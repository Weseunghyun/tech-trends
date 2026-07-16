"""산출물 작성 — 스냅샷 JSON·포인터(latest/index) 갱신 (data-model / R5·R7).

한국어 보존을 위해 ensure_ascii=False. 모든 쓰기는 원자적(tmp + os.replace) —
중단 시 잘린 JSON이 커밋되는 것을 방지한다(감사 F-04).

일자 아카이브는 영구 보관한다(2026-07-16 결정): 파일이 하루 15~43KB로 연 ~12MB 수준이라
GitHub Pages에 부담이 없고, "지난 트렌드 다시 둘러보기" 용도에 30일 삭제가 정면으로
반한다. 30일 만료는 dedup 원장(last-seen)에만 적용된다.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from scripts.config import SCHEMA_VERSION

_DATE_GLOB = "20*-*.json"


def _write_text_atomic(path: Path, text: str) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def _write_json(path: Path, obj: object) -> None:
    _write_text_atomic(path, json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


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
    _write_text_atomic(out / "latest.json", day_file.read_text(encoding="utf-8"))

    dates = sorted(p.stem for p in out.glob(_DATE_GLOB))
    _write_json(out / "index.json", {"dates": dates, "generated_at": generated_at})
