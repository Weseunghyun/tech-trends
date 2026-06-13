# Python 보안 코딩 규칙 (stock-routine)

이 레포는 매일 시세/스크리너를 수집해 Google Sheets에 적재하는 개인용 Python 루틴이다.
민감 자산은 두 환경변수뿐이다: `GCP_SA_KEY_JSON`(service account JSON 본문)과 `SHEET_ID`.
아래 규칙은 이 레포의 실제 코드(`scripts/sheets_client.py`, `scripts/fetch_us_screener.py`, `scripts/fetch_kr.py` 등)에 직접 연결된다.

적용 범위: `scripts/**/*.py`. 구현/리뷰 시 이 파일을 참조하고, `impl-python-validate` 스킬이 자동 검출한다.

---

## SEC-01 시크릿 미출력 (Secret Non-Disclosure) — 🔴 CRITICAL

근거: CLAUDE.md "절대 하지 말 것" — API 키/service account JSON을 stdout에 출력 금지.

- `GCP_SA_KEY_JSON`, `GCP_SA_KEY_PATH`, `SHEET_ID` 값을 `print()`, `logging.*`, `sys.stdout.write()` 등 어떤 출력 경로로도 내보내지 않는다.
- `sheets_client.get_client()`의 `json.loads(key_json)` 결과(`info` dict, 특히 `private_key`/`client_email`)를 출력하거나 예외 메시지에 포함하지 않는다.
- 인증 오류 메시지에는 환경변수 **이름**만 적는다. 현재 `sheets_client.py`의 `RuntimeError("환경변수 GCP_SA_KEY_JSON 또는 ...")`는 값이 아닌 이름만 노출하므로 준수 상태 — 이 패턴을 유지한다.
- 예외 출력은 `type(e).__name__`을 우선한다. `fetch_us_screener.py`의 `fetch_fundamentals`가 이미 `print(f"  {ticker} 실패: {type(e).__name__}", file=sys.stderr)`로 이 패턴을 따른다 — 신규 코드도 동일하게.

검출: `ruff` S105/S106/S107(하드코딩 시크릿).

## SEC-02 로깅 시 민감 정보 제외 (Log Sanitization) — 🟡 IMPORTANT

근거: `fetch_kr.py`의 `except Exception as e: print(f"  {ticker}: 실패 — {e}", file=sys.stderr)`는 `{e}` 안에 자격증명/내부 변수가 섞일 수 있다.

- stderr 출력 시 `{e}` 전체 대신 `{type(e).__name__}` 또는 `{type(e).__name__}: {e}` 형식을 쓰되, 인증·시트 접근 경로 예외는 `{e}` 노출을 피한다.
- `sheets_client.py`의 인증 단계 예외는 `raise RuntimeError("인증 실패") from None`으로 원인 체인을 끊어 내부 토큰/경로 누출을 막는 것을 권장한다.
- 개별 종목 실패는 ticker 식별자 + 예외 타입까지만 남긴다(CLAUDE.md "개별 실패는 stderr 기록 후 계속" 정책 유지).

## SEC-03 위험 실행 금지 (Dangerous Execution Ban) — 🔴 CRITICAL

근거: 데이터 수집 파이프라인이라 동적 코드 실행/셸 호출이 전혀 필요 없다. 현재 어떤 스크립트에도 없다 — 이 상태를 유지한다.

- `eval()`, `exec()`, `compile()`, `os.system()`, `os.popen()` 사용 금지.
- 불가피하게 `subprocess`를 쓸 경우 `shell=False` + 인자 리스트만 허용. `shell=True` 금지.

검출: `bandit` B102/B103/B602/B603/B604/B605, `ruff` S102/S602/S603/S604/S605.

## SEC-04 외부 HTTP 요청 보안 (External Request Security) — 🔴 CRITICAL

근거: `fetch_us_screener.py`의 `get_sp500_list()`가 `requests.get(url, headers=..., timeout=10)`로 GitHub raw CSV를 받는다.

- `verify=False` 절대 금지(기본 `verify=True` 유지) — MITM 노출.
- 모든 `requests.get/post`에 `timeout`을 명시한다(현재 `timeout=10` 준수). fx/us/kr는 yfinance/pykrx 내부 호출이라 직접 `requests`가 없음 — 직접 호출을 새로 추가하면 동일 규칙 적용.
- 응답 파싱 전 `response.raise_for_status()`를 호출한다(현재 준수). `pd.read_csv(StringIO(response.text))`는 그 뒤에만.
- yfinance/pykrx가 반환한 값은 신뢰하지 말고 None/타입 체크 후 사용한다(현재 `info.get(...)` + `pd.notna` 패턴 유지).

검출: `bandit` B501/B502/B503, `ruff` S501.

## SEC-05 입력 검증 (Input Validation) — 🟡 IMPORTANT

근거: holdings 시트의 `ticker`가 yfinance/pykrx에 그대로 전달된다(`fetch_kr.py` `to_pykrx_code`, `fetch_us_screener.py` `yf.Ticker(ticker)`).

- ticker는 `^[A-Za-z0-9.\-]{1,12}$` 형태만 허용하고, 위반 시 stderr에 형식 오류를 남기고 `continue`로 건너뛴다.
  ```python
  import re
  _TICKER_RE = re.compile(r"^[A-Za-z0-9.\-]{1,12}$")
  if not _TICKER_RE.match(ticker):
      print(f"  {ticker}: 유효하지 않은 티커 형식, skip", file=sys.stderr)
      continue
  ```
- `SHEET_ID`는 빈 문자열 체크에 더해 `^[A-Za-z0-9_-]{20,}$` 패턴 검증을 권장한다.
- 시트에 적재하는 문자열 길이를 제한한다(`fetch_us_screener.py`의 summary 1500자 컷 유지).

## SEC-06 데이터 미보정 (No Data Fabrication) — 🟡 IMPORTANT

근거: CLAUDE.md "절대 하지 말 것" — 임의 데이터 보정/추측값 채우기 금지.

- 외부 API가 None/결측을 주면 빈 값(`""`)이나 명시적 기본값으로 두고, 추정·보간으로 채우지 않는다(현재 `pd.notna(...)` 분기 후 `""` 처리 패턴 유지).
- holdings 시트 데이터는 읽기 전용으로만 다룬다. 수정/upsert 대상은 `prices`/`screener_us` 등 산출 시트에 한정한다.

## SEC-07 최소 권한 원칙 (Least Privilege) — 🟡 IMPORTANT

근거: `sheets_client.py`의 `SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]`는 Sheets 읽기+쓰기만 요청 — 올바름.

- `SCOPES`에 `drive`, `drive.file`, `cloud-platform` 등을 추가하지 않는다.
- GCP service account IAM 역할은 대상 스프레드시트 접근에 필요한 최소 수준으로 제한하고, 키는 주기적으로(권장 90일) 교체한다.

## SEC-08 의존성 핀 & 감사 (Dependency Pinning & Audit) — 🟡 IMPORTANT

근거: `requirements.txt`가 모든 패키지를 `==`로 핀(yfinance==0.2.66 등) — 준수.

- 패키지 추가/업그레이드 시 머지 전 `pip-audit -r requirements.txt`로 CVE 스캔.
- `==` 정확 버전 핀을 유지한다. 선택적 강화로 `--require-hashes`(SHA256 고정)를 검토한다.

검출: `pip-audit --requirement requirements.txt`.

## SEC-09 시크릿 커밋 방지 (Secret Leak Prevention) — 🔴 CRITICAL

근거: 로컬 테스트 시 `GCP_SA_KEY_PATH`가 가리키는 sa.json이나 `.env`가 실수로 커밋될 수 있다.

- `.gitignore`에 `.env`, `*.key`, sa-key용 JSON 패턴을 유지/추가한다(레포 루트의 `*.json` SA 키를 추적하지 않도록).
- service account JSON 파일을 레포 안에 두지 않는다. 로컬 테스트는 레포 밖 경로를 `GCP_SA_KEY_PATH`로 지정한다.

---

검증 도구는 `impl-python-validate` 스킬이 일괄 실행한다(ruff → bandit → pip-audit, 미설치 시 graceful skip).