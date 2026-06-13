"""산출물 작성 — 스냅샷 JSON·포인터(latest/index) 갱신·30일 prune (data-model / R5·R7).

한국어 보존을 위해 ensure_ascii=False. 대시보드는 latest.json만 읽는다(동일 출처).
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

from scripts.config import RETENTION_DAYS, SCHEMA_VERSION

_DATE_GLOB = "20*-*.json"


def _write_json(path: Path, obj: object) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_snapshot(
    *,
    date_str: str,
    generated_at: str,
    categories: dict[str, list[dict]],
    hot_topics: list[dict],
    sources: list[dict],
) -> dict:
    """DashboardSnapshot 최상위 구조 생성(contracts/data-json-schema)."""
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "date": date_str,
        "categories": categories,
        "hot_topics": hot_topics,
        "sources": sources,
    }


def write_snapshot(snapshot: dict, out: Path) -> Path:
    """당일 스냅샷을 docs/data/YYYY-MM-DD.json으로 기록."""
    out.mkdir(parents=True, exist_ok=True)
    day_file = out / f"{snapshot['date']}.json"
    _write_json(day_file, snapshot)
    return day_file


def refresh_pointers(out: Path, day_file: Path, generated_at: str) -> None:
    """latest.json(당일 복사본)·index.json(매니페스트) 갱신."""
    latest = out / "latest.json"
    latest.write_text(day_file.read_text(encoding="utf-8"), encoding="utf-8")

    dates = sorted(p.stem for p in out.glob(_DATE_GLOB))
    _write_json(out / "index.json", {"dates": dates, "generated_at": generated_at})


def prune_files(out: Path, today: date, days: int = RETENTION_DAYS) -> list[str]:
    """days(기본 30)를 초과한 일자 파일 삭제. 삭제된 일자 목록 반환."""
    keep_from = today - timedelta(days=days - 1)  # today 포함 days개
    removed: list[str] = []
    for f in out.glob(_DATE_GLOB):
        try:
            d = date.fromisoformat(f.stem)
        except ValueError:
            continue
        if d < keep_from:
            f.unlink()
            removed.append(f.stem)
    return removed
