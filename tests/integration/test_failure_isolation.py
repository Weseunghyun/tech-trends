"""US3 통합 — 소스 실패 격리(FR-009) + 일자 간 중복 제거(FR-011)."""

from __future__ import annotations

import json

from scripts import collect as collect_mod


def _make_dispatch(fail_source: str):
    def _dispatch(source):
        if source["id"] == fail_source:
            raise TimeoutError("boom")
        return [
            {"title": f"{source['id']} 글", "url": f"https://example.com/{source['id']}",
             "source": source["id"], "category": source["category"], "summary_ko": "",
             "lang": "en", "published_at": None, "metrics": None},
        ]
    return _dispatch


def test_one_source_failure_isolated(monkeypatch, tmp_path):
    monkeypatch.setattr(collect_mod, "_dispatch", _make_dispatch("hackernews"))
    snap = collect_mod.collect("2026-06-13", tmp_path)

    statuses = {s["source"]: s for s in snap["sources"]}
    # 실패 소스는 ok=False, error_type 타입명만(SEC-02)
    assert statuses["hackernews"]["ok"] is False
    assert statuses["hackernews"]["error_type"] == "TimeoutError"
    assert statuses["hackernews"]["item_count"] == 0
    # 나머지 소스는 정상 적재 → latest.json 생성됨(전체 중단 없음)
    assert (tmp_path / "latest.json").exists()
    assert sum(1 for s in snap["sources"] if s["ok"]) >= 1


def test_all_sources_fail_does_not_overwrite(monkeypatch, tmp_path):
    # 직전 성공분 latest.json 배치
    (tmp_path / "latest.json").write_text('{"date":"prev"}', encoding="utf-8")

    def _all_fail(source):
        raise ConnectionError("down")

    monkeypatch.setattr(collect_mod, "_dispatch", _all_fail)
    snap = collect_mod.collect("2026-06-13", tmp_path)

    assert all(not s["ok"] for s in snap["sources"])
    # 전 소스 실패 → 직전 latest.json 미덮어쓰기(엣지 케이스 정책)
    assert json.loads((tmp_path / "latest.json").read_text(encoding="utf-8"))["date"] == "prev"


def test_exit_code_partial_vs_total_failure(monkeypatch, tmp_path):
    monkeypatch.setattr(collect_mod, "_dispatch", _make_dispatch("hackernews"))
    assert collect_mod.main(["--date", "2026-06-13", "--out", str(tmp_path)]) == 0

    def _all_fail(source):
        raise ConnectionError("down")

    monkeypatch.setattr(collect_mod, "_dispatch", _all_fail)
    assert collect_mod.main(["--date", "2026-06-13", "--out", str(tmp_path)]) == 1


def test_cross_day_dedup(monkeypatch, tmp_path):
    monkeypatch.setattr(collect_mod, "_dispatch", _make_dispatch("none"))
    # 1일차: 모든 항목 신규
    snap1 = collect_mod.collect("2026-06-13", tmp_path)
    day1_items = [it for lst in snap1["categories"].values() for it in lst]
    assert day1_items, "1일차 항목 존재"
    assert (tmp_path / "seen_urls.json").exists()

    # 2일차: 동일 URL 재수집 → 중복 제거되어 0건
    snap2 = collect_mod.collect("2026-06-14", tmp_path)
    day2_items = [it for lst in snap2["categories"].values() for it in lst]
    assert day2_items == [], "동일 URL은 일자 간 1회만 노출(FR-011)"
