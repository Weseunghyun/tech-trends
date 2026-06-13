"""정규화 URL 기반 일자 간 중복 제거 + 30일 원장 — research R3 / FR-011.

seen_urls.json: {정규화 URL: 최초 발견일(YYYY-MM-DD)}. 매 실행마다 30일 초과분을
prune하고, 이미 본 URL은 신규에서 제외한다. 외부 저장소 없이 커밋 메커니즘 재사용.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from scripts.config import RETENTION_DAYS
from scripts.normalize import normalize_url

LEDGER_NAME = "seen_urls.json"


def load_ledger(out: Path) -> dict[str, str]:
    """seen_urls.json 로드. 없으면 빈 dict(day-one 안전)."""
    path = out / LEDGER_NAME
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return {str(k): str(v) for k, v in data.items()} if isinstance(data, dict) else {}


def prune(ledger: dict[str, str], today: date, days: int = RETENTION_DAYS) -> dict[str, str]:
    """today 기준 days(기본 30)를 초과한 항목 제거한 새 원장 반환."""
    kept: dict[str, str] = {}
    for url, seen in ledger.items():
        try:
            d = date.fromisoformat(seen)
        except ValueError:
            continue
        if (today - d).days <= days:
            kept[url] = seen
    return kept


def is_new(url: str, ledger: dict[str, str]) -> bool:
    """정규화 URL이 원장에 없으면 신규(True)."""
    return normalize_url(url) not in ledger


def mark_seen(url: str, ledger: dict[str, str], today: date) -> None:
    """신규 URL을 today로 원장에 등록(기존 항목은 최초 발견일 보존)."""
    norm = normalize_url(url)
    ledger.setdefault(norm, today.isoformat())


def save_ledger(out: Path, ledger: dict[str, str]) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / LEDGER_NAME).write_text(
        json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def filter_new_items(items: list[dict], ledger: dict[str, str], today: date) -> list[dict]:
    """원장에 없는 신규 항목만 통과시키고, 통과 항목을 원장에 등록(FR-011).

    같은 실행 내 동일 URL 중복도 1회만 통과한다.
    """
    fresh: list[dict] = []
    for it in items:
        url = it["url"]
        if is_new(url, ledger):
            fresh.append(it)
            mark_seen(url, ledger, today)
    return fresh
