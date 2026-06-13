"""중복 제거·원장 단위 테스트 — research R3 / FR-011 / FR-018."""

from __future__ import annotations

from datetime import date

from scripts.dedup import filter_new_items, is_new, load_ledger, mark_seen, prune, save_ledger
from scripts.normalize import normalize_url


def test_normalized_url_dedup_equivalence():
    led: dict[str, str] = {}
    mark_seen("https://Example.com/Post/?utm_source=x", led, date(2026, 6, 13))
    # www·http·trailing slash·추적 파라미터 차이는 동일 항목으로 간주
    assert not is_new("http://www.example.com/Post", led)
    assert not is_new("https://example.com/Post/?utm_source=y&utm_medium=z", led)
    # 경로 대소문자는 보존 → 다른 자원
    assert is_new("https://example.com/post", led)


def test_fragment_distinguishes_items():
    # Codex changelog는 fragment로 항목 구분 — fragment가 다르면 별개 자원
    led: dict[str, str] = {}
    mark_seen("https://developers.openai.com/codex/changelog/#codex-2026-06-11", led, date(2026, 6, 13))
    assert is_new("https://developers.openai.com/codex/changelog/#codex-2026-06-09", led)
    assert not is_new("https://developers.openai.com/codex/changelog/#codex-2026-06-11", led)


def test_prune_drops_over_30_days():
    led = {
        "https://a.com/1": "2026-05-01",  # 43일 전 → 제거
        "https://b.com/2": "2026-06-01",  # 12일 전 → 유지
    }
    kept = prune(led, date(2026, 6, 13), days=30)
    assert normalize_url("https://a.com/1") in led  # 원본 보존
    assert "https://a.com/1" not in kept
    assert "https://b.com/2" in kept


def test_filter_new_items_dedups_within_run():
    led: dict[str, str] = {}
    items = [
        {"url": "https://x.com/1", "title": "a"},
        {"url": "https://x.com/1?utm_source=feed", "title": "a dup"},  # 같은 자원
        {"url": "https://y.com/2", "title": "b"},
    ]
    fresh = filter_new_items(items, led, date(2026, 6, 13))
    assert len(fresh) == 2  # 동일 URL은 1회만


def test_ledger_roundtrip(tmp_path):
    led = {"https://a.com/1": "2026-06-13"}
    save_ledger(tmp_path, led)
    assert load_ledger(tmp_path) == led


def test_load_ledger_missing_is_empty(tmp_path):
    assert load_ledger(tmp_path) == {}
