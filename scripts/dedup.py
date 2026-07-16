"""정규화 URL 기반 일자 간 중복 제거 + last-seen 원장 — research R3 / FR-011.

seen_urls.json: {정규화 URL: 마지막 목격일(YYYY-MM-DD)}. 소스 피드가 전체 아카이브를
반환하므로 "최초 발견일 + 30일" 만료는 만료 즉시 전 아카이브가 신규로 재통과하는
좀비 재노출을 일으킨다(2026-07-16 실측). 그래서 원장은 **마지막으로 피드에서 목격한
날**을 기록하고, 피드에서 30일간 사라진 URL만 만료한다 — 재등장하면 그때는 실제로
다시 화제가 된 것이므로 신규 취급이 옳다.

등록 시점: 수집 통과 시점이 아니라 **스냅샷에 실제 표시된 항목만** mark_seen으로
등록한다(카테고리 컷에 잘린 항목이 "본 적 없는데 seen 처리"되어 영구 유실되는 것을
방지). filter_new_items는 중복 판정과 last-seen 갱신만 담당한다.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import date
from pathlib import Path

from scripts.config import RETENTION_DAYS
from scripts.normalize import normalize_url

LEDGER_NAME = "seen_urls.json"


def load_ledger(state_dir: Path) -> dict[str, str]:
    """seen_urls.json 로드. 없으면 빈 dict(day-one 안전).

    손상된 원장은 빈 dict로 폴백하되 stderr에 남긴다 — 무증상 전체 재노출 방지(감사 F-04).
    """
    path = state_dir / LEDGER_NAME
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        print(f"  seen_urls 원장 손상 — 빈 원장으로 시작 ({type(e).__name__})", file=sys.stderr)
        return {}
    return {str(k): str(v) for k, v in data.items()} if isinstance(data, dict) else {}


def prune(ledger: dict[str, str], today: date, days: int = RETENTION_DAYS) -> dict[str, str]:
    """마지막 목격일이 today 기준 days(기본 30)를 초과한 항목을 제거한 새 원장 반환."""
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
    """URL의 마지막 목격일을 today로 갱신(과거로는 되돌리지 않음 — 백필 안전)."""
    norm = normalize_url(url)
    today_str = today.isoformat()
    if ledger.get(norm, "") < today_str:
        ledger[norm] = today_str


def save_ledger(state_dir: Path, ledger: dict[str, str]) -> None:
    """원장 원자적 기록(tmp + os.replace) — 중단 시 잘린 JSON 방지(감사 F-04)."""
    state_dir.mkdir(parents=True, exist_ok=True)
    path = state_dir / LEDGER_NAME
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(
        json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    os.replace(tmp, path)


def filter_new_items(items: list[dict], ledger: dict[str, str], today: date) -> list[dict]:
    """이전 일자에 목격한 항목을 걸러내고 신규/당일 항목만 통과시킨다(FR-011).

    - 이전 일자에 목격한 URL → 제외 + **last-seen을 today로 갱신**(피드에 아직 있으므로
      만료되지 않게 — 좀비 재노출 방지의 핵심).
    - 미래 일자로 기록된 URL(과거 날짜 백필 중) → 제외, 원장은 건드리지 않음.
    - 원장에 없거나 당일 기록 → 통과(같은 날 재실행 시 스냅샷이 비지 않음).
    - 같은 실행 내 동일 URL 중복 → 1회만 통과.
    통과 항목의 원장 등록은 여기서 하지 않는다 — 표시 확정 후 mark_seen으로(모듈 docstring).
    """
    today_str = today.isoformat()
    fresh: list[dict] = []
    run_seen: set[str] = set()
    for it in items:
        norm = normalize_url(it["url"])
        if norm in run_seen:
            continue  # 같은 실행 내 중복
        prior = ledger.get(norm)
        if prior is not None and prior != today_str:
            if prior < today_str:
                ledger[norm] = today_str  # 피드에 여전히 존재 → 만료 시계 리셋
            continue  # 다른 일자에 이미 목격 → 일자 간 중복 제거
        run_seen.add(norm)
        fresh.append(it)
    return fresh
