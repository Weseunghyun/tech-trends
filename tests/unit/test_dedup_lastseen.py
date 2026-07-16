"""scripts.dedup — last-seen 원장(seen_urls.json) 행동 스펙 테스트.

구현 비열람(blind) 작성: 스펙 브리프에 선언된 공개 계약만 사용한다.
  - prune(ledger, today, days=30): '마지막 목격일'이 today 기준 days '초과'인 항목만 제거
  - mark_seen(url, ledger, today): 마지막 목격일을 today로 갱신하되 과거로는 되돌리지 않음
  - filter_new_items(items, ledger, today):
      * 원장에 없거나 당일 기록 URL -> 통과
      * 이전 일자 기록 URL -> 제외 + last-seen을 today로 touch (좀비 재노출 방지, 핵심 신규 스펙)
      * 미래 일자 기록 URL -> 제외, touch 없음 (과거 백필 시나리오)
      * 통과(신규) 항목 -> 원장 미등록 (등록은 표시 확정 후 mark_seen의 몫)

원장 키는 '정규화 URL'이므로 내부 정규화 규칙에 의존하지 않도록
공개 API인 mark_seen을 프로브로 사용해 키를 역산한다.
날짜는 datetime.now(KST) 기준 상대값만 사용한다(하드코딩 금지 규칙).
"""

import sys
from datetime import date, datetime, timedelta
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
for _p in (_ROOT, _ROOT / "src"):
    if _p.exists() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from scripts.config import KST
from scripts.dedup import filter_new_items, mark_seen, prune


def _today() -> date:
    """KST 기준 오늘."""
    return datetime.now(KST).date()


def _as_date(value) -> date:
    """원장 값(ISO 문자열 등)을 date로 파싱 — date/datetime 포맷 양쪽에 관대하게."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return datetime.fromisoformat(str(value)).date()


def _key(url: str) -> str:
    """공개 API(mark_seen)만으로 URL의 정규화 원장 키를 역산."""
    probe: dict = {}
    mark_seen(url, probe, _today())
    assert len(probe) == 1, "mark_seen이 원장에 키 1개를 등록해야 함"
    return next(iter(probe))


def _item(url: str) -> dict:
    """filter_new_items 최소 요구 형태({'url': str}) + 식별용 title."""
    return {"url": url, "title": "테스트 항목"}


def test_zombie_reexposure_prevented_by_lastseen_touch():
    """케이스 1(핵심 신규 스펙 — 좀비 재노출 방지):
    원장에 32일 전 날짜로 기록된 URL은 filter_new_items가 제외하면서
    원장 날짜를 오늘로 touch -> 이어지는 prune(기본 30일)에도 만료되지 않는다.
    (구 스펙이라면 '최초 발견일' 기준으로 만료돼 다음 수집 때 재노출됐을 시나리오)"""
    today = _today()
    url = "https://example.com/zombie-article"
    ledger: dict = {}
    mark_seen(url, ledger, today - timedelta(days=32))  # 마지막 목격 = 32일 전
    key = _key(url)
    assert key in ledger

    # 대조 확인: touch 없이 바로 prune 했다면 32 > 30 이므로 만료 대상이었다
    assert key not in prune(dict(ledger), today)

    # 이전 일자 기록 URL -> 제외되면서 last-seen이 today로 갱신(touch)
    assert filter_new_items([_item(url)], ledger, today) == []
    assert _as_date(ledger[key]) == today

    # touch 덕분에 prune에서 살아남는다 -> 좀비 재노출 없음
    assert key in prune(ledger, today)


def test_disappeared_url_expires_after_window():
    """케이스 2: 피드에서 사라져 31일간 touch가 없던 URL은 prune으로 만료된다.
    경계 확인: 정확히 30일은 '초과'가 아니므로 유지된다."""
    today = _today()
    gone_url = "https://example.com/gone-article"
    edge_url = "https://example.com/edge-article"
    ledger: dict = {}
    mark_seen(gone_url, ledger, today - timedelta(days=31))  # 31일 무목격 -> 만료
    mark_seen(edge_url, ledger, today - timedelta(days=30))  # 정확히 30일 -> 유지

    pruned = prune(ledger, today)
    assert _key(gone_url) not in pruned
    assert _key(edge_url) in pruned


def test_passing_new_items_are_not_registered():
    """케이스 3: filter_new_items 통과(신규) 항목은 원장에 등록되지 않는다.
    (등록은 표시 확정 후 mark_seen의 몫)"""
    today = _today()
    url = "https://example.com/fresh-article"
    ledger: dict = {}

    result = filter_new_items([_item(url)], ledger, today)

    assert len(result) == 1  # 원장에 없는 URL -> 통과
    assert ledger == {}  # 통과했어도 원장에는 아무 키도 생기지 않음


def test_mark_seen_moves_date_forward_only():
    """케이스 4: mark_seen은 날짜를 앞으로만 이동 —
    오늘로 기록한 뒤 어제 날짜로 다시 호출해도 오늘이 유지된다."""
    today = _today()
    url = "https://example.com/forward-only"
    ledger: dict = {}
    mark_seen(url, ledger, today)
    mark_seen(url, ledger, today - timedelta(days=1))  # 과거로 되돌리기 시도

    assert len(ledger) == 1
    assert _as_date(ledger[_key(url)]) == today


def test_backfill_future_dated_entry_excluded_without_touch():
    """케이스 5(과거 백필): 원장에 오늘 날짜로 기록된 URL을 today=어제로 filter
    -> 제외되고, 원장 날짜는 오늘 그대로 유지(미래 기록은 touch하지 않음)."""
    today = _today()
    yesterday = today - timedelta(days=1)
    url = "https://example.com/backfill-article"
    ledger: dict = {}
    mark_seen(url, ledger, today)  # 백필 실행 시점(어제) 기준으로는 '미래' 기록

    assert filter_new_items([_item(url)], ledger, yesterday) == []
    assert _as_date(ledger[_key(url)]) == today  # 날짜 변경 없음
