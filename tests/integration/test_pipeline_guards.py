"""collect 파이프라인 가드 — 행동 스펙 테스트 (구현 비열람 blind 작성).

스펙 브리프에 선언된 공개 계약만 사용한다:
  - scripts.collect: collect(date_str, out, *, state_dir, dry_run),
    inject_summaries(out, date_str, summaries_path), main(argv)
  - 테스트 심: scripts.collect._dispatch(source) -> raw 항목 리스트,
    scripts.collect._enrich_article_text (네트워크 차단용)
  - scripts.config: SOURCES(16개, 2026-07-20 확장), PER_CATEGORY=10, KST, MIN_OK_RATIO=0.5
  - scripts.dedup: load_ledger, mark_seen(정규화 키 역산 프로브)

검증 케이스:
  1. 표시(스냅샷 채택) 항목만 원장 등록 + 컷 항목은 다음날 재노출(영구 유실 없음)
  2. 카테고리 컷은 published_at 내림차순 상위 PER_CATEGORY개
  3. --date 형식 위반("../../evil") -> SystemExit(code 2)
  4. 소스 성공 비율 < MIN_OK_RATIO -> latest.json 미작성(기존 보존) + main()==1
  5. 과거 날짜 inject_summaries가 latest.json의 date를 역행시키지 않음
  6. summaries_injected 필드: collect 직후 false, inject 후 해당 날짜 파일 true

규칙: 날짜는 datetime.now(KST) 기준 상대값만 사용, 네트워크는 심 모킹으로 차단.
스냅샷 JSON 내부 구조는 브리프에 명세돼 있지 않으므로 구조 비의존 헬퍼로 탐색한다.
"""

import json
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest
from scripts import collect as collect_mod
from scripts.collect import collect, inject_summaries, main
from scripts.config import KST, MIN_OK_RATIO, PER_CATEGORY, SOURCES
from scripts.dedup import load_ledger, mark_seen

TARGET = SOURCES[0]  # 같은 카테고리 항목 15개를 쏟아낼 타깃 소스


# ---------- 날짜/항목/심 헬퍼 ----------


def _today() -> date:
    return datetime.now(KST).date()


def _raw(source: dict, url: str, published_at, title: str) -> dict:
    """브리프가 정의한 _dispatch raw 항목 형태 그대로."""
    return {
        "title": title,
        "url": url,
        "source": source["id"],
        "category": source["category"],
        "summary_ko": "",
        "lang": "en",
        "published_at": published_at,
        "metrics": None,
    }


def _install_seams(monkeypatch, dispatch) -> None:
    """브리프 지정 심 2곳 모킹 — 네트워크 접근 차단(필수 규칙)."""
    monkeypatch.setattr(collect_mod, "_dispatch", dispatch)
    monkeypatch.setattr(collect_mod, "_enrich_article_text", lambda items: None)


def _ledger_key(url: str) -> str:
    """내부 정규화 규칙에 의존하지 않고 공개 API(mark_seen)로 원장 키를 역산."""
    probe: dict = {}
    mark_seen(url, probe, _today())
    assert len(probe) == 1
    return next(iter(probe))


# ---------- 스냅샷 구조 비의존 탐색 헬퍼 ----------


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _latest_file(out: Path) -> Path:
    direct = out / "latest.json"
    if direct.exists():
        return direct
    cands = list(out.rglob("latest.json"))
    assert len(cands) == 1, f"latest.json 파일을 특정하지 못함: {cands}"
    return cands[0]


def _find_dated_file(out: Path, date_str: str) -> Path:
    """파일명에 date_str이 들어간 날짜 스냅샷 파일을 탐색(위치·명명 규칙 비의존)."""
    cands = [p for p in out.rglob("*.json") if date_str in p.name and p.name != "latest.json"]
    assert len(cands) == 1, (
        f"'{date_str}' 날짜 스냅샷 파일을 하나로 특정하지 못함. 후보: "
        f"{[str(p) for p in cands]} / 전체 json: {[p.name for p in out.rglob('*.json')]}"
    )
    return cands[0]


def _all_items(node) -> list[dict]:
    """스냅샷 JSON 어디에 있든 표시 항목(url+title 보유 dict)을 전부 수집."""
    found: list[dict] = []
    if isinstance(node, dict):
        if "url" in node and "title" in node:
            found.append(node)
        else:
            for v in node.values():
                found.extend(_all_items(v))
    elif isinstance(node, list):
        for v in node:
            found.extend(_all_items(v))
    return found


def _category_urls(snap: dict, category: str) -> list[str]:
    """카테고리별 표시 항목 url 목록 — 그룹핑 구조를 모르므로 여러 형태를 순차 시도."""
    cats = snap.get("categories")
    if isinstance(cats, dict) and category in cats:
        return [i["url"] for i in _all_items(cats[category])]
    if isinstance(cats, list):
        for entry in cats:
            if isinstance(entry, dict) and category in (
                entry.get("category"),
                entry.get("id"),
                entry.get("name"),
            ):
                return [i["url"] for i in _all_items(entry)]
    items = snap.get("items")
    if isinstance(items, dict) and category in items:
        return [i["url"] for i in _all_items(items[category])]
    # 평면 리스트 + 항목별 category 필드 형태
    flat = [i for i in _all_items(snap) if i.get("category") == category]
    if flat:
        return [i["url"] for i in flat]
    raise AssertionError(
        f"스냅샷에서 카테고리 '{category}' 항목을 찾지 못함 — 최상위 키: {sorted(snap.keys())}"
    )


# ---------- 공통 시나리오 ----------


def _make_scenario():
    """타깃 소스 = 같은 카테고리 15개(published_at 각기 다름),
    나머지 13개 소스 = 훨씬 오래된 필러 1개씩(수집 성공 유지 + 게이트 통과용)."""
    now = datetime.now(KST).replace(minute=0, second=0, microsecond=0)
    target_items = [
        _raw(
            TARGET,
            f"https://target-feed.example.org/item-{k:02d}",
            (now - timedelta(hours=k)).isoformat(),  # k가 클수록 오래된 글
            f"타깃 항목 {k:02d}",
        )
        for k in range(PER_CATEGORY + 5)  # 15개
    ]
    filler_ts = (now - timedelta(days=10)).isoformat()  # 타깃 15개보다 항상 오래됨
    filler_urls = {
        s["id"]: f"https://filler-feed.example.org/src-{i}" for i, s in enumerate(SOURCES)
    }

    def dispatch(source, *args, **kwargs):
        if source["id"] == TARGET["id"]:
            return [dict(it) for it in target_items]  # 호출마다 사본(수집기 측 변형 격리)
        return [_raw(source, filler_urls[source["id"]], filler_ts, f"필러 {source['id']}")]

    top10 = {it["url"] for it in target_items[:PER_CATEGORY]}  # published_at 최신 10개
    cut5 = {it["url"] for it in target_items[PER_CATEGORY:]}  # 컷으로 잘릴 5개
    return dispatch, top10, cut5


# ---------- 테스트 케이스 ----------


def test_only_displayed_items_enter_ledger_and_cut_items_reappear_next_day(tmp_path, monkeypatch):
    """[스펙 1] 표시 항목만 원장 등록:
    15개 중 PER_CATEGORY(10)개만 표시 -> 원장에는 '표시된 항목 수만큼만' 키 존재,
    컷된 5개는 미등록 -> 다음날 재수집 시 컷됐던 항목이 표시 목록에 등장(영구 유실 없음)."""
    dispatch, top10, cut5 = _make_scenario()
    _install_seams(monkeypatch, dispatch)
    today = _today()

    collect(today.isoformat(), tmp_path, state_dir=tmp_path)

    snap1 = _load_json(_latest_file(tmp_path))
    cat_urls_d1 = _category_urls(snap1, TARGET["category"])
    assert PER_CATEGORY == 10  # 스펙 명시값 확인
    assert len(cat_urls_d1) == PER_CATEGORY  # 카테고리당 10개만 표시

    # 원장에는 표시된 '고유' 항목 수만큼만 정규화 URL이 존재해야 한다
    # (같은 항목이 카테고리와 핫토픽 양쪽에 나타나도 원장 등록은 1회 — url 기준 dedupe)
    displayed_total = len({it["url"] for it in _all_items(snap1)})
    ledger = load_ledger(tmp_path)
    assert len(ledger) == displayed_total

    # 표시된 타깃 URL은 등록, 컷된 URL은 미등록
    for u in cat_urls_d1:
        assert _ledger_key(u) in ledger, f"표시 항목이 원장에 없음: {u}"
    for u in cut5:
        assert _ledger_key(u) not in ledger, f"컷된(미표시) 항목이 원장에 등록됨: {u}"

    # 다음날 동일 피드 재수집 -> 컷됐던 5개가 표시되고, 전날 표시분은 재노출되지 않는다
    day2 = today + timedelta(days=1)
    collect(day2.isoformat(), tmp_path, state_dir=tmp_path)
    snap2 = _load_json(_latest_file(tmp_path))
    cat_urls_d2 = set(_category_urls(snap2, TARGET["category"]))
    assert cut5 <= cat_urls_d2, "전날 컷으로 잘렸던 항목이 다음날 표시 목록에 없음(영구 유실)"
    assert cat_urls_d2.isdisjoint(top10), "전날 표시된 항목이 다음날 중복 재노출됨"


def test_category_cut_keeps_most_recent_published_at(tmp_path, monkeypatch):
    """[스펙 2] published_at 내림차순 컷:
    표시된 10개는 15개 중 published_at이 가장 최신인 10개여야 한다."""
    dispatch, top10, _cut5 = _make_scenario()
    _install_seams(monkeypatch, dispatch)

    collect(_today().isoformat(), tmp_path, state_dir=tmp_path)

    snap = _load_json(_latest_file(tmp_path))
    assert set(_category_urls(snap, TARGET["category"])) == top10


def test_main_rejects_malformed_date_with_exit_code_2(tmp_path, monkeypatch):
    """[스펙 3] --date 형식 검증: 경로조작 문자열 '../../evil' -> SystemExit(code=2)."""
    dispatch, _top10, _cut5 = _make_scenario()
    _install_seams(monkeypatch, dispatch)  # 검증 이전/이후 어느 시점에도 네트워크 차단

    with pytest.raises(SystemExit) as excinfo:
        main(["--date", "../../evil", "--out", str(tmp_path), "--state", str(tmp_path)])
    assert excinfo.value.code == 2


def test_majority_failure_gate_preserves_latest_and_returns_1(tmp_path, monkeypatch):
    """[스펙 4] 과반 임계 게이트: 과반 이상 소스 실패(성공 비율 < MIN_OK_RATIO=0.5)
    -> latest.json 미작성(기존 파일 보존), main()이 1을 반환."""
    assert len(SOURCES) == 16  # 스펙 명시값 (2026-07-20 reddit_localllama·hf_blog 추가로 14→16)
    assert MIN_OK_RATIO == 0.5  # 스펙 명시값

    n_fail = len(SOURCES) // 2 + 1  # 과반 실패 -> 성공 비율이 임계 미만이 되도록
    failing_ids = {s["id"] for s in SOURCES[:n_fail]}
    now_iso = datetime.now(KST).isoformat()
    ok_urls = {s["id"]: f"https://ok-feed.example.org/src-{i}" for i, s in enumerate(SOURCES)}

    def dispatch(source, *args, **kwargs):
        if source["id"] in failing_ids:
            raise RuntimeError("모킹된 수집 실패")
        return [_raw(source, ok_urls[source["id"]], now_iso, f"성공 항목 {source['id']}")]

    _install_seams(monkeypatch, dispatch)

    # 기존 latest.json(센티널) — 게이트 발동 시 그대로 보존되어야 한다
    sentinel = {"date": (_today() - timedelta(days=5)).isoformat(), "sentinel": "게이트 보존 확인"}
    latest_path = tmp_path / "latest.json"
    latest_path.write_text(json.dumps(sentinel, ensure_ascii=False), encoding="utf-8")

    rc = main(["--date", _today().isoformat(), "--out", str(tmp_path), "--state", str(tmp_path)])

    assert rc == 1  # 과반 미달 -> 실패 종료 코드
    assert json.loads(latest_path.read_text(encoding="utf-8")) == sentinel  # latest.json 보존


def test_inject_with_past_date_does_not_regress_latest(tmp_path, monkeypatch):
    """[스펙 5] inject 과거 날짜 latest 역행 방지:
    오늘 스냅샷 생성 후 어제 날짜 파일을 수작업으로 만들어 inject_summaries(어제)를 호출해도
    latest.json의 date는 여전히 오늘이어야 한다."""
    dispatch, _top10, _cut5 = _make_scenario()
    _install_seams(monkeypatch, dispatch)
    today_s = _today().isoformat()
    yest_s = (_today() - timedelta(days=1)).isoformat()

    collect(today_s, tmp_path, state_dir=tmp_path)
    today_file = _find_dated_file(tmp_path, today_s)

    # 어제 날짜 스냅샷 파일 수작업 생성: 오늘 스냅샷 JSON에서 date만 어제로 치환
    data = _load_json(today_file)
    data["date"] = yest_s
    yest_file = today_file.parent / today_file.name.replace(today_s, yest_s)
    yest_file.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    # 요약 파일: {url: 요약} 매핑으로 작성
    summaries = {it["url"]: "주입 테스트 요약" for it in _all_items(data)}
    spath = tmp_path / "summaries.json"
    spath.write_text(json.dumps(summaries, ensure_ascii=False), encoding="utf-8")

    result = inject_summaries(tmp_path, yest_s, str(spath))
    assert isinstance(result, dict)  # 선언 시그니처: dict 반환

    # 핵심: 과거 날짜 inject가 latest.json을 역행시키지 않는다
    assert _load_json(_latest_file(tmp_path))["date"] == today_s


def test_snapshot_summaries_injected_flag(tmp_path, monkeypatch):
    """[스펙 6] 스냅샷 신규 필드: collect 산출 latest.json에 summaries_injected=false,
    inject_summaries 후 해당 날짜 파일에 true."""
    dispatch, _top10, _cut5 = _make_scenario()
    _install_seams(monkeypatch, dispatch)
    today_s = _today().isoformat()

    collect(today_s, tmp_path, state_dir=tmp_path)
    latest = _load_json(_latest_file(tmp_path))
    assert latest.get("summaries_injected") is False  # collect 직후에는 false

    summaries = {it["url"]: "주입 테스트 요약" for it in _all_items(latest)}
    spath = tmp_path / "summaries.json"
    spath.write_text(json.dumps(summaries, ensure_ascii=False), encoding="utf-8")

    inject_summaries(tmp_path, today_s, str(spath))

    dated = _load_json(_find_dated_file(tmp_path, today_s))
    assert dated.get("summaries_injected") is True  # inject 후 해당 날짜 파일은 true
