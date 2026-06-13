"""수집 오케스트레이션 진입점 — python -m scripts.collect.

단계: 소스 수집(실패 격리) → 정규화·검증 → (중복 제거) → (요약 주입) → (점수) → 산출물.
중복 제거·점수·요약 주입은 각 사용자 스토리 단계에서 통합된다.
시크릿·자격증명을 어떤 출력 경로로도 내보내지 않는다(SEC-01/02).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path

from scripts.config import CONTENT_CATEGORIES, KST, PER_CATEGORY, SOURCES
from scripts.dedup import filter_new_items, load_ledger, prune, save_ledger
from scripts.normalize import clip, item_id, normalize_url, valid_url
from scripts.render import build_snapshot, prune_files, refresh_pointers, write_snapshot
from scripts.score import compute_hot_topics
from scripts.sources.hackernews import fetch_hn
from scripts.sources.rss import fetch_rss


def _dispatch(source: dict) -> list[dict]:
    """소스 kind에 맞는 어댑터 호출."""
    if source["kind"] == "rss":
        return fetch_rss(source)
    if source["kind"] == "hn":
        return fetch_hn(source)
    raise ValueError(f"unknown source kind: {source['kind']}")


def _finalize_item(raw: dict, collected_at: str) -> dict | None:
    """raw 항목을 검증·정규화해 TrendItem dict로. 부적합 시 None(폐기, FR-003/010)."""
    url = (raw.get("url") or "").strip()
    if not valid_url(url):
        return None
    title = clip(raw.get("title"))
    if not title:
        return None
    return {
        "id": item_id(url),
        "title": title,
        "url": normalize_url(url),
        "source": raw["source"],
        "category": raw["category"],
        "summary_ko": clip(raw.get("summary_ko"), 600),
        "lang": raw.get("lang") or "unknown",
        "published_at": raw.get("published_at"),
        "collected_at": collected_at,
        "metrics": raw.get("metrics"),
    }


def _load_summaries(path: str | None) -> dict[str, str]:
    """에이전트가 채운 {item_id: 한글요약} JSON 로드. 없으면 빈 매핑(요약 "" 유지)."""
    if not path:
        return {}
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return {str(k): str(v) for k, v in data.items()}


def collect(
    date_str: str, out: Path, *, dry_run: bool = False, summaries_path: str | None = None
) -> dict:
    """수집 파이프라인 실행. 산출 스냅샷 dict 반환."""
    now = datetime.now(KST)
    generated_at = now.isoformat(timespec="seconds")
    summaries = _load_summaries(summaries_path)

    items: list[dict] = []
    sources_status: list[dict] = []

    for source in SOURCES:
        try:
            raws = _dispatch(source)
            finalized = [it for r in raws if (it := _finalize_item(r, generated_at))]
            # 에이전트가 채운 한글 요약 주입(FR-004). 없으면 "" 유지(추정 금지)
            for it in finalized:
                if it["id"] in summaries:
                    it["summary_ko"] = clip(summaries[it["id"]], 600)
            items.extend(finalized)
            sources_status.append(
                {
                    "source": source["id"],
                    "ok": True,
                    "item_count": len(finalized),
                    "error_type": None,
                    "feed_built_at": None,
                }
            )
        except Exception as e:  # noqa: BLE001 — 개별 소스 실패 격리(FR-009)
            # 예외 타입명만 기록 — 값/자격증명 미노출(SEC-02)
            print(f"  {source['id']} 수집 실패: {type(e).__name__}", file=sys.stderr)
            sources_status.append(
                {
                    "source": source["id"],
                    "ok": False,
                    "item_count": 0,
                    "error_type": type(e).__name__,
                    "feed_built_at": None,
                }
            )

    # 일자 간 중복 제거(FR-011): 정규화 URL 원장으로 신규 항목만 통과
    today = date.fromisoformat(date_str)
    ledger = prune(load_ledger(out), today)
    items = filter_new_items(items, ledger, today)

    categories = _group_by_category(items)
    hot_topics = compute_hot_topics(items)
    snapshot = build_snapshot(
        date_str=date_str,
        generated_at=generated_at,
        categories=categories,
        hot_topics=hot_topics,
        sources=sources_status,
    )

    ok_count = sum(1 for s in sources_status if s["ok"])
    if dry_run:
        _print_dry_run(snapshot, ok_count)
        return snapshot

    if ok_count == 0:
        # 전 소스 실패 → 직전 latest.json 미덮어쓰기(엣지 케이스 정책)
        print("전 소스 실패 — 산출물 미갱신", file=sys.stderr)
        return snapshot

    day_file = write_snapshot(snapshot, out)
    refresh_pointers(out, day_file, generated_at)
    prune_files(out, now.date())
    save_ledger(out, ledger)  # 신규 등록·prune 반영된 원장 저장(FR-011)
    return snapshot


def _group_by_category(items: list[dict]) -> dict[str, list[dict]]:
    """콘텐츠 카테고리별로 묶고 카테고리당 PER_CATEGORY개로 컷(FR-017)."""
    by_cat: dict[str, list[dict]] = {c: [] for c in CONTENT_CATEGORIES}
    for it in items:
        cat = it["category"]
        if cat in by_cat:
            by_cat[cat].append(it)
    return {c: lst[:PER_CATEGORY] for c, lst in by_cat.items()}


def _print_dry_run(snapshot: dict, ok_count: int) -> None:
    """dry-run 통계 출력(시크릿 미포함)."""
    print(f"[dry-run] date={snapshot['date']} 소스 성공 {ok_count}/{len(snapshot['sources'])}")
    for s in snapshot["sources"]:
        mark = "ok" if s["ok"] else f"FAIL({s['error_type']})"
        print(f"  - {s['source']}: {s['item_count']}건 {mark}")
    for cat, lst in snapshot["categories"].items():
        print(f"  [{cat}] {len(lst)}건")
    print(f"  [hot_topics] {len(snapshot['hot_topics'])}건")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="scripts.collect", description="tech-trends 수집기")
    parser.add_argument("--dry-run", action="store_true", help="수집만, 파일 미작성")
    parser.add_argument("--date", default=None, help="기준 일자 YYYY-MM-DD(KST), 기본 오늘")
    parser.add_argument("--out", default="docs/data", help="산출 디렉토리")
    parser.add_argument(
        "--summaries", default=None, help="에이전트가 채운 {item_id: 한글요약} JSON 경로"
    )
    args = parser.parse_args(argv)

    date_str = args.date or datetime.now(KST).date().isoformat()
    snapshot = collect(
        date_str, Path(args.out), dry_run=args.dry_run, summaries_path=args.summaries
    )

    ok_count = sum(1 for s in snapshot["sources"] if s["ok"])
    return 0 if ok_count > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
