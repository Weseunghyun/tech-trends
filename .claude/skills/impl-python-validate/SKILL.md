---
name: impl-python-validate
description: Python 구현을 완료한 뒤 태스크를 [X]로 표시하기 전에 보안/품질 검증을 수행한다. ruff, bandit, pip-audit를 설치된 경우에만 실행하고 미설치 시 건너뛴다. stock-routine의 시크릿(GCP_SA_KEY_JSON/SHEET_ID) 미노출과 외부 API/HTTP 취급을 점검할 때 사용한다.
argument-hint: "[검증할 경로(기본 scripts/)]"
disable-model-invocation: true
---

# Python 구현 후 보안/품질 검증

SDD 태스크 구현이 끝나면 `[X]` 표시 **전에** 아래 단계를 순서대로 수행한다.
이 레포의 보안 규칙은 `.claude/rules/python-security.md`에 정의돼 있으며, 검증은 그 규칙을 기계적으로 확인하는 게이트다.

대상 경로 인자가 없으면 `scripts/`를 기본으로 한다.

## Step 1: 보안 린트 (ruff S-그룹)

`ruff`가 설치돼 있으면 실행한다. 없으면 `[SKIP]`을 출력하고 다음 단계로 넘어간다.

```bash
if command -v ruff >/dev/null 2>&1; then
  echo "[ruff] 보안 룰(S-그룹) + 기본 검사"
  ruff check scripts --select S,E,W,F --output-format concise
else
  echo "[SKIP] ruff 미설치 — pip install ruff"
fi
```

- S102/S602~S605: `eval`/`exec`/`shell=True` 검출 (SEC-03)
- S501: SSL 검증 비활성화 검출 (SEC-04)
- S105/S106/S107: 하드코딩 시크릿 검출 (SEC-01)
- 위반이 있으면 수정 후 재실행한다. 우회/무시(noqa 남발) 금지.

## Step 2: 보안 스캔 (bandit)

`bandit`이 설치돼 있으면 실행한다. 없으면 `[SKIP]`.

```bash
if command -v bandit >/dev/null 2>&1; then
  echo "[bandit] 전체 보안 스캔 (medium 이상)"
  bandit -r scripts -ll --quiet
else
  echo "[SKIP] bandit 미설치 — pip install bandit"
fi
```

- ruff S-그룹이 못 잡는 B301/B302(역직렬화), B501~B503(SSL), B602~B605(셸)까지 커버.
- `test_*.py`의 `assert`(B101)는 테스트 특성상 허용한다.
- High 심각도 발견은 반드시 수정한다.

## Step 3: 의존성 CVE 감사 (pip-audit)

`pip-audit`이 설치돼 있고 `requirements.txt`가 바뀐 태스크일 때 실행한다. 없으면 `[SKIP]`.

```bash
if command -v pip-audit >/dev/null 2>&1; then
  echo "[pip-audit] requirements.txt CVE 스캔"
  pip-audit --requirement requirements.txt
else
  echo "[SKIP] pip-audit 미설치 — pip install pip-audit"
fi
```

- 알려진 CVE가 나오면 핀 버전을 안전한 버전으로 올리고 Step 3을 재실행한다 (SEC-08).
- 모든 의존성은 `==` 정확 버전 핀을 유지한다.

## Step 4: 시크릿/규칙 수동 체크리스트

자동 도구가 없거나 통과했더라도 아래를 직접 확인한다 (`.claude/rules/python-security.md` 대조):

- [ ] 변경 코드에 `GCP_SA_KEY_JSON`/`GCP_SA_KEY_PATH`/`SHEET_ID` 값을 출력하는 경로가 없는가 (SEC-01)
- [ ] 예외 출력이 `{e}` 전체가 아닌 `type(e).__name__` 기반인가, 인증 예외에 자격증명이 섞이지 않는가 (SEC-02)
- [ ] 새 `requests` 호출에 `timeout` 명시 + `verify=False` 없음 + `raise_for_status()` 호출 (SEC-04)
- [ ] 외부에서 받은 ticker를 API에 넘기기 전 형식 검증(`^[A-Za-z0-9.\-]{1,12}$`)하는가 (SEC-05)
- [ ] 결측값을 추정/보간으로 채우지 않고 빈 값/명시 기본값으로 두는가, holdings는 읽기 전용인가 (SEC-06)
- [ ] `SCOPES`에 spreadsheets 외 스코프를 추가하지 않았는가 (SEC-07)
- [ ] SA 키 파일/`.env`를 레포에 커밋하지 않는가 (SEC-09)

## 결과 판정

- 실행한 도구가 모두 통과하고 체크리스트에 미해결 항목이 없으면 태스크를 `[X]`로 표시한다.
- 도구 미설치로 `[SKIP]`된 단계는 Step 4 수동 체크리스트로 대체 검증한다.
- 실패가 하나라도 있으면 `[X]` 표시 없이 수정 후 재검증한다 (RULES: 검증 우회 금지).