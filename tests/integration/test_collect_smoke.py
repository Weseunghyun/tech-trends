"""US1 통합 스모크 — 수집 파이프라인이 검증된 항목·출처 링크·카테고리 컷을 산출하는지.

네트워크 비의존: _dispatch를 모킹한다. SC-002(출처 링크 100%)·FR-017(카테고리 컷)·
SC-006(시크릿 미출력) 회귀.
"""

from __future__ import annotations

import json
from pathlib import Path

from scripts import collect as collect_mod


def _fake_dispatch(source):
    # 소스마다 항목 2개 + 무효 URL 1개(폐기되어야 함)
    return [
        {"title": f"{source['id']} 글1", "url": f"https://example.com/{source['id']}/1",
         "source": source["id"], "category": source["category"], "summary_ko": "",
         "lang": "en", "published_at": None, "metrics": None},
        {"title": f"{source['id']} 글2", "url": f"https://example.com/{source['id']}/2?utm_source=x",
         "source": source["id"], "category": source["category"], "summary_ko": "",
         "lang": "en", "published_at": None, "metrics": None},
        {"title": "무효", "url": "not-a-url", "source": source["id"],
         "category": source["category"], "summary_ko": "", "lang": "en",
         "published_at": None, "metrics": None},
    ]


def test_collect_produces_valid_items(monkeypatch, tmp_path):
    monkeypatch.setattr(collect_mod, "_dispatch", _fake_dispatch)
    snap = collect_mod.collect("2026-06-13", tmp_path)

    # 모든 항목이 valid http(s) url 보유 (SC-002)
    all_items = [it for lst in snap["categories"].values() for it in lst]
    assert all_items, "항목이 생성되어야 함"
    for it in all_items:
        assert it["url"].startswith("https://"), it["url"]
        assert it["id"]
        # utm_ 추적 파라미터는 정규화로 제거됨
        assert "utm_" not in it["url"]

    # 카테고리당 PER_CATEGORY 이하 (FR-017)
    for lst in snap["categories"].values():
        assert len(lst) <= collect_mod.PER_CATEGORY

    # 무효 URL 항목은 폐기됨 (소스당 3개 중 2개만)
    assert snap["sources"][0]["item_count"] == 2

    # latest.json 산출 (FR-005)
    latest = json.loads((tmp_path / "latest.json").read_text(encoding="utf-8"))
    assert latest["date"] == "2026-06-13"
    assert (tmp_path / "index.json").exists()


def test_summary_injection(monkeypatch, tmp_path):
    monkeypatch.setattr(collect_mod, "_dispatch", _fake_dispatch)
    # 먼저 id를 알아내기 위해 1회 수집
    snap = collect_mod.collect("2026-06-13", tmp_path, dry_run=True)
    first = next(it for lst in snap["categories"].values() for it in lst)
    sfile = tmp_path / "summaries.json"
    sfile.write_text(json.dumps({first["id"]: "주입된 한글 요약"}), encoding="utf-8")

    snap2 = collect_mod.collect("2026-06-13", tmp_path, dry_run=True, summaries_path=str(sfile))
    injected = [
        it for lst in snap2["categories"].values() for it in lst if it["id"] == first["id"]
    ]
    assert injected and injected[0]["summary_ko"] == "주입된 한글 요약"


def test_dry_run_no_secret_output(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(collect_mod, "_dispatch", _fake_dispatch)
    collect_mod.collect("2026-06-13", tmp_path / "nowrite", dry_run=True)
    out = capsys.readouterr()
    combined = out.out + out.err
    # 토큰/키스러운 패턴이 출력에 없어야 함 (SEC-01)
    for needle in ["BEGIN PRIVATE KEY", "Authorization", "secret", "token="]:
        assert needle not in combined


def test_dashboard_has_no_external_cdn():
    html = Path("docs/index.html").read_text(encoding="utf-8")
    # script/link가 외부 절대 URL을 참조하지 않아야 함 (SC-001 외부 CDN 0)
    assert "src=\"http" not in html
    assert "href=\"http" not in html
