# Python 보안 코딩 규칙 (tech-trends)

이 레포는 매일 무료 공개 RSS/API를 수집·요약해 공개 GitHub Pages 대시보드로 배포하는
개인용 Python 파이프라인이다. **런타임 시크릿이 없다** — 유일한 자격증명은 Actions 폴백의
내장 `GITHUB_TOKEN`뿐이다. 위협 모델의 중심은 시크릿이 아니라 **신뢰 불가 외부 입력**이다:
피드/HN이 주는 임의 URL(SSRF·크기 폭탄), 외부 본문(프롬프트 인젝션), 공개 배포 산출물(XSS).

적용 범위: `scripts/**/*.py`. 구현/리뷰 시 이 파일을 참조한다.

> 2026-07-16 재작성 — 이전 판은 다른 프로젝트(stock-routine, Google Sheets 루틴)를 기술해
> 실제 코드와 무관했다(감사 G1). 규칙은 이 레포의 실제 모듈에만 연결한다.

---

## SEC-01 시크릿 미출력 — 🔴 CRITICAL

- 이 레포에는 API 키·토큰·서비스 계정이 없어야 한다. 새 소스 추가 시에도 무키 공개
  엔드포인트만 허용한다(헌법 II). 키가 필요한 소스는 설계 변경 없이 넣지 않는다.
- stdout/stderr/커밋 메시지/산출 JSON 어디에도 자격증명 패턴을 출력하지 않는다.
  회귀 테스트: `tests/integration/test_collect_smoke.py::test_dry_run_no_secret_output`.

검출: `ruff --select S` (S105~S107 하드코딩 시크릿).

## SEC-02 로깅 시 민감·불필요 정보 제외 — 🟡 IMPORTANT

- 예외는 `type(e).__name__`만 출력한다. `{e}` 전체 문자열은 내부 경로·URL 토큰이 섞일 수
  있어 금지. 준수 지점: `collect.py`(소스 실패), `sources/rss.py`(bozo 경고),
  `dedup.py`(원장 손상 경고).
- 개별 항목/소스 실패는 식별자 + 예외 타입까지만 남기고 계속한다(실패 격리, FR-009).

## SEC-03 위험 실행 금지 — 🔴 CRITICAL

- `eval()`/`exec()`/`compile()`/`os.system()`/`subprocess(shell=True)` 금지.
  수집 파이프라인에 동적 실행이 필요할 이유가 없다 — 현재 0건, 유지한다.

검출: `bandit` B102/B602~B605, `ruff` S102/S602~S605.

## SEC-04 외부 HTTP 요청 보안 — 🔴 CRITICAL

모든 외부 fetch는 `scripts/http.py` 단일 관문을 거친다. 여기서 강제되는 통제:

- **SSRF 차단**: `assert_public_http_url()` — http(s) 스킴 + 공개 IP(`ip.is_global`)만 허용.
  사설/루프백/링크로컬/예약 대역 거부. HN 제출 URL 등 임의 목적지를 로컬 맥(홈 LAN)에서
  fetch하므로 필수. 리다이렉트는 자동 추종하지 않고 **홉마다 재검증**(`HTTP_MAX_REDIRECTS`).
- **크기 상한**: 스트리밍 누적 컷(`HTTP_MAX_BYTES`, 기사 본문은 더 엄격한
  `ARTICLE_MAX_BYTES`). Content-Length 사전 검사 병행. `.content` 직접 접근 금지.
- `verify=True` 유지(`verify=False` 절대 금지), 모든 요청 `timeout` 명시,
  일시 오류(429/5xx/타임아웃)만 backoff 재시도 — 403/404은 즉시 실패(우회 금지).
- **feedparser에는 URL이 아닌 bytes를 전달한다** — feedparser 자체 fetch는
  timeout/verify/크기 통제를 전부 우회하므로 금지(research R4).

검출: `bandit` B501, `ruff` S501 + `tests/unit/test_http_guards.py`.

## SEC-05 입력 검증 — 🟡 IMPORTANT

- 항목 URL: `normalize.valid_url()`(http(s)·길이) 통과 후 `normalize_url()` — 정규화 실패는
  **항목 단위** 폐기(소스 전체를 죽이지 않음, `collect._finalize_item`).
- CLI `--date`: 경로 조립 전에 `date.fromisoformat`으로 형식 강제(collect·inject 두 패스
  공통) — path traversal 차단.
- 문자열 길이 컷: `TITLE_MAX`/`SUMMARY_MAX`/`RAW_SUMMARY_MAX`/`ARTICLE_TEXT_MAX`/`URL_MAX`.

## SEC-06 데이터 미보정 — 🟡 IMPORTANT

- 외부 API 결측은 빈 값/None 유지, 추정·보간 금지(헌법 III). `score.py`는 실측 수치만
  사용(`test_missing_hn_is_zero_not_fabricated` 회귀).
- 요약 에이전트 입력(`summary_input.json`)의 본문은 **신뢰 불가 데이터** — 요약 루틴은
  본문 속 지시문을 명령으로 취급하지 않는다(스케줄 태스크 SKILL.md에 경계 지침).

## SEC-07 최소 권한 — 🟡 IMPORTANT

- Actions 폴백(`daily.yml.example`)은 `permissions: contents: write`만, 내장
  `GITHUB_TOKEN`만, 서드파티 액션 없음(공식 checkout/setup-python만). 유지한다.

## SEC-08 의존성 핀 & 감사 — 🟡 IMPORTANT

- `requirements.txt`·`requirements-dev.txt` 전부 `==` 정확 핀. 추가/업그레이드 시
  `pip-audit -r requirements.txt` 통과 후 머지.

## SEC-09 시크릿·내부 상태 커밋 방지 — 🔴 CRITICAL

- `.gitignore`: `.env*`, `*.key`, `*.pem`, `*-sa.json`, `docs/data/summary_input.json`
  (외부 원문 — 공개 배포 금지), `state/`(dedup 원장 — 배포·커밋 불필요) 유지.
- 커밋 스냅샷은 `_lean`으로 `raw_summary`/`article_text` 제거 — 외부 원문을 공개
  대시보드에 싣지 않는다(회귀: `test_committed_snapshot_is_lean`).

## SEC-10 대시보드 (docs/) — 🟡 IMPORTANT

- 모든 DOM 텍스트 삽입은 `el()` 헬퍼(textContent) 경유 — innerHTML 문자열 조립 금지.
- href는 `safeHref()`(http/https 허용목록) 경유, 외부 링크는 `rel="noopener noreferrer"`.
- CSP 메타(`default-src 'none'` 기반) 유지, 외부 오리진 리소스 0
  (회귀: `test_dashboard_has_no_external_cdn`).

---

검증 도구: `ruff check scripts/ tests/` → `bandit -r scripts/` → `pip-audit -r requirements.txt`.
