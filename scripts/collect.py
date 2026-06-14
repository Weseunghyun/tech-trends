"""수집 오케스트레이션 진입점 — python -m scripts.collect.

흐름(2패스):
  1) `collect`          : 수집·검증·중복제거·점수 → 표시 항목 본문 fetch →
                          가벼운 latest.json + 요약용 summary_input.json(gitignore) 작성
  2) `collect --summaries S.json` : 재수집 없이 기존 당일 스냅샷에 한글 요약만 주입(가벼움)

시크릿·자격증명을 어떤 출력 경로로도 내보내지 않는다(SEC-01/02).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path

from scripts.config import (
    CONTENT_CATEGORIES,
    KST,
    PER_CATEGORY,
    RAW_SUMMARY_MAX,
    SOURCES,
    SUMMARY_MAX,
)
from scripts.dedup import filter_new_items, load_ledger, prune, save_ledger
from scripts.fetch_article import fetch_article_text
from scripts.normalize import clip, item_id, normalize_url, valid_url
from scripts.render import build_snapshot, prune_files, refresh_pointers, write_snapshot
from scripts.score import compute_hot_topics
from scripts.sources.hackernews import fetch_hn
from scripts.sources.rss import fetch_rss

SUMMARY_INPUT_NAME = "summary_input.json"

# 커밋되는 스냅샷에서 제외할 무거운/요약 입력 전용 필드(대시보드 불필요)
_HEAVY_FIELDS = ("raw_summary", "article_text")


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
        "summary_ko": clip(raw.get("summary_ko"), SUMMARY_MAX),
        "raw_summary": clip(raw.get("raw_summary"), RAW_SUMMARY_MAX),
        "article_text": "",  # 표시 항목에 한해 이후 본문 fetch로 채움(요약 입력용)
        "lang": raw.get("lang") or "unknown",
        "published_at": raw.get("published_at"),
        "collected_at": collected_at,
        "metrics": raw.get("metrics"),
    }


def _lean(item: dict) -> dict:
    """커밋용 가벼운 item — 요약 입력 전용 필드 제거."""
    return {k: v for k, v in item.items() if k not in _HEAVY_FIELDS}


def _lean_snapshot(snapshot: dict) -> dict:
    """스냅샷의 모든 item(카테고리·핫토픽 근거)을 가볍게."""
    out = dict(snapshot)
    out["categories"] = {c: [_lean(it) for it in lst] for c, lst in snapshot["categories"].items()}
    out["hot_topics"] = [
        {**t, "items": [_lean(it) for it in t["items"]]} for t in snapshot["hot_topics"]
    ]
    return out


def _displayed_items(snapshot: dict) -> list[dict]:
    """카테고리 + 핫토픽 근거의 고유 item(같은 dict 참조) 목록."""
    seen: set[str] = set()
    out: list[dict] = []
    groups = list(snapshot["categories"].values()) + [t["items"] for t in snapshot["hot_topics"]]
    for lst in groups:
        for it in lst:
            if it["id"] not in seen:
                seen.add(it["id"])
                out.append(it)
    return out


def _enrich_article_text(items: list[dict]) -> None:
    """표시 항목에 한해 기사 본문을 fetch해 article_text 채움(실패는 격리, "" 유지)."""
    for it in items:
        text = fetch_article_text(it["url"])
        if text:
            it["article_text"] = text


def _write_summary_input(out: Path, items: list[dict]) -> None:
    """에이전트 요약 입력 파일(gitignore) — id별 제목·출처·원문설명·본문."""
    payload = {
        it["id"]: {
            "title": it["title"],
            "url": it["url"],
            "source": it["source"],
            "category": it["category"],
            "raw_summary": it["raw_summary"],
            "article_text": it["article_text"],
        }
        for it in items
    }
    (out / SUMMARY_INPUT_NAME).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def _load_summaries(path: str) -> dict[str, str]:
    """에이전트가 채운 {item_id: 한글요약} JSON 로드."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return {str(k): str(v) for k, v in data.items()}


def inject_summaries(out: Path, date_str: str, summaries_path: str) -> dict:
    """재수집 없이 기존 당일 스냅샷에 한글 요약만 주입하고 재기록."""
    day_file = out / f"{date_str}.json"
    if not day_file.exists():
        raise FileNotFoundError(f"{day_file} 없음 — 먼저 collect를 실행하세요")
    snapshot = json.loads(day_file.read_text(encoding="utf-8"))
    summaries = _load_summaries(summaries_path)

    def _apply(it: dict) -> None:
        if it["id"] in summaries:
            it["summary_ko"] = clip(summaries[it["id"]], SUMMARY_MAX)

    for lst in snapshot["categories"].values():
        for it in lst:
            _apply(it)
    for t in snapshot["hot_topics"]:
        for it in t["items"]:
            _apply(it)

    write_snapshot(snapshot, out)
    refresh_pointers(out, day_file, snapshot["generated_at"])
    return snapshot


def collect(date_str: str, out: Path, *, dry_run: bool = False) -> dict:
    """수집 파이프라인 실행(1패스). 산출 스냅샷 dict 반환."""
    now = datetime.now(KST)
    generated_at = now.isoformat(timespec="seconds")

    items: list[dict] = []
    sources_status: list[dict] = []

    for source in SOURCES:
        try:
            raws = _dispatch(source)
            finalized = [it for r in raws if (it := _finalize_item(r, generated_at))]
            items.extend(finalized)
            sources_status.append(
                {"source": source["id"], "ok": True, "item_count": len(finalized),
                 "error_type": None, "feed_built_at": None}
            )
        except Exception as e:  # noqa: BLE001 — 개별 소스 실패 격리(FR-009)
            print(f"  {source['id']} 수집 실패: {type(e).__name__}", file=sys.stderr)
            sources_status.append(
                {"source": source["id"], "ok": False, "item_count": 0,
                 "error_type": type(e).__name__, "feed_built_at": None}
            )

    # 일자 간 중복 제거(FR-011)
    today = date.fromisoformat(date_str)
    ledger = prune(load_ledger(out), today)
    items = filter_new_items(items, ledger, today)

    categories = _group_by_category(items)
    hot_topics = compute_hot_topics(items)
    snapshot = build_snapshot(
        date_str=date_str, generated_at=generated_at,
        categories=categories, hot_topics=hot_topics, sources=sources_status,
    )

    ok_count = sum(1 for s in sources_status if s["ok"])
    if dry_run:
        _print_dry_run(snapshot, ok_count)
        return snapshot

    if ok_count == 0:
        print("전 소스 실패 — 산출물 미갱신", file=sys.stderr)
        return snapshot

    # 표시 항목에 한해 본문 fetch(요약 입력 강화) → 요약 입력 파일 작성
    displayed = _displayed_items(snapshot)
    _enrich_article_text(displayed)
    _write_summary_input(out, displayed)

    # 커밋 파일은 가볍게(본문·원문설명 제외)
    lean = _lean_snapshot(snapshot)
    day_file = write_snapshot(lean, out)
    refresh_pointers(out, day_file, generated_at)
    prune_files(out, now.date())
    save_ledger(out, ledger)
    return snapshot


def _group_by_category(items: list[dict]) -> dict[str, list[dict]]:
    """콘텐츠 카테고리별로 묶고 카테고리당 PER_CATEGORY개로 컷(FR-017)."""
    by_cat: dict[str, list[dict]] = {c: [] for c in CONTENT_CATEGORIES}
    for it in items:
        if it["category"] in by_cat:
            by_cat[it["category"]].append(it)
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
        "--summaries", default=None,
        help="에이전트가 채운 {item_id: 한글요약} JSON 경로(주입 전용, 재수집 안 함)",
    )
    args = parser.parse_args(argv)

    date_str = args.date or datetime.now(KST).date().isoformat()
    out = Path(args.out)

    if args.summaries:
        # 주입 전용 패스(재수집·재fetch 없음)
        snapshot = inject_summaries(out, date_str, args.summaries)
        return 0

    snapshot = collect(date_str, out, dry_run=args.dry_run)
    ok_count = sum(1 for s in snapshot["sources"] if s["ok"])
    return 0 if ok_count > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
