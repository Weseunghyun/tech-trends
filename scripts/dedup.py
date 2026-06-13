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
    """이전 일자에 본 항목만 걸러내고 신규/당일 항목은 통과시킨다(FR-011).

    - 이전 일자(today 이전)에 본 URL → 제외(일자 간 중복 누적 방지).
    - 당일 최초 등장 또는 같은 날 재실행 항목 → 통과(같은 날 재실행 시 스냅샷이 비지 않음).
    - 같은 실행 내 동일 URL 중복 → 1회만 통과.
    통과 항목은 원장에 최초 발견일로 등록한다(기존 일자 보존).
    """
    today_str = today.isoformat()
    fresh: list[dict] = []
    run_seen: set[str] = set()
    for it in items:
        norm = normalize_url(it["url"])
        if norm in run_seen:
            continue  # 같은 실행 내 중복
        prior = ledger.get(norm)
        if prior is not None and prior < today_str:
            continue  # 이전 일자에 이미 노출 → 일자 간 중복 제거
        run_seen.add(norm)
        ledger.setdefault(norm, today_str)
        fresh.append(it)
    return fresh
