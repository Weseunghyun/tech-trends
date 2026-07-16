# tech-trends

AI·개발/기술 트렌드 종합 대시보드. 매일 KST 08:00경 무료 공개 소스(GitHub Trending·AI 랩 블로그·OpenAI Codex·Hacker News)에서
최신 동향·화제 주제를 모아 한글로 요약하고, 공개 GitHub Pages 정적 대시보드로 본다. 폰·아무 브라우저에서 로그인·키 없이 본다.

## 아키텍처

```
[스케줄 루틴(매일 KST 08:00)]
  └ 파이썬 수집기(scripts/) — 무료 RSS/API 수집 → 정규화·검증 → 중복 제거(last-seen 원장) → 트렌드 점수
  └ 에이전트 LLM이 한글 요약(인라인, 별도 LLM 키 불필요)
  └ docs/data/latest.json 커밋·푸시
        ▼
[공개 GitHub repo] ── GitHub Pages(/docs) ──▶ https://<id>.github.io/tech-trends
                                              (정적 HTML/JS가 같은 출처 JSON fetch)
```

## 구조

- `scripts/` — 수집기(Python 3.11+). `config`(소스·점수 상수), `http`(공개 IP 검증·리다이렉트 재검증·크기 상한의 단일 fetch 관문), `normalize`/`dedup`/`score`/`render`, `sources/`(RSS·HN 어댑터), `collect`(오케스트레이션).
- `docs/` — 정적 대시보드(외부 CDN 0, CSP, 모바일 반응형). `index.html`/`app.js`/`styles.css` + `data/`(`latest.json`·일자 아카이브(영구 보관)·`index.json`).
- `state/` — 파이프라인 내부 상태(dedup 원장 `seen_urls.json`). **gitignore** — 공개 배포·커밋 대상 아님. 새 클론/새 머신의 첫 실행은 원장이 비어 있어 하루치 대량 노출이 있을 수 있다(1회성, 이후 자동 안정).
- `tests/` — 단위(dedup·score·http 가드)·통합(수집 스모크·실패 격리·파이프라인 가드).
- `specs/001-rss-api-github/` — SDD 산출물. `spec.yaml`·`spec/` — cladding SSoT.

## 로컬 실행

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt          # 런타임: feedparser==6.0.11, requests==2.33.0
pip install -r requirements-dev.txt      # 개발: pytest, ruff, bandit, pip-audit

python -m scripts.collect --dry-run      # 네트워크 수집만(쓰기 없음), 통계 출력
python -m scripts.collect --out docs/data  # 실제 산출물 생성 (원장은 state/에 기록)
pytest tests/ -q                         # 테스트
ruff check scripts/ tests/ && bandit -r scripts/ -q   # 린트·보안 정적 분석

cd docs && python -m http.server 8080    # http://localhost:8080 미리보기
```

수집기 옵션: `--dry-run`, `--date YYYY-MM-DD`, `--out <dir>`, `--state <dir>`(원장 위치, 기본 `<repo>/state`), `--summaries <json>`(에이전트가 채운 `{item_id: 한글요약}` 주입).

종료 코드: 성공 소스가 **과반 미만이면 1** — 빈약한 부분 데이터로 직전 산출물을 덮어쓰지 않고 스케줄 루틴이 push를 생략한다.

## 대시보드

- 탭: 핫토픽/화두 · AI 랩 동향 · GitHub Trending · OpenAI Codex · 엔지니어링 블로그 · **주간 몰아보기**(최근 7일 핫토픽 합산 — 며칠 쉬고 복귀할 때).
- 날짜 페이징으로 전체 아카이브 열람(영구 보관). 과거 날짜 파일은 불변이라 브라우저 캐시를 활용하고, 최신 데이터만 매번 신선하게 받는다.

## 배포 (GitHub Pages)

1. Settings → Pages → Source: **Deploy from a branch**, Branch: 기본 브랜치, Folder: **`/docs`**.
2. 공개 URL: `https://<id>.github.io/tech-trends/`.

## 스케줄

- **1차(운영 중)**: 로컬 스케줄 루틴(`tt-daily-local`, 매일 07:36 KST) — 수집 + 한글 요약을 에이전트가 인라인 수행하고 커밋·푸시. 맥이 꺼진 날은 건너뛴다(공백일은 대시보드에서 자연히 표시되지 않음 — HN/트렌딩은 소급 불가, 랩 블로그는 다음 실행이 따라잡음).
- **폴백**: `.github/daily.yml.example`를 `.github/workflows/daily.yml`로 옮기면 활성화. 단 ① 요약 없음(LLM 키 없음) ② `state/` 원장이 러너에 없어 일자 간 중복 제거가 동작하지 않음(캐시/아티팩트 배선 필요) — 임시 대체용으로만.

## 원칙·보안

- 불변 원칙: [.specify/memory/constitution.md](.specify/memory/constitution.md) — 공개·정적·시크릿 미노출, 클라우드 가용 소스만, 출처 필수·무결성, 실패 격리, ToS 준수, YAGNI.
- 파이썬 보안 규칙: [.claude/rules/python-security.md](.claude/rules/python-security.md)(SEC-01~10) — SSRF 차단·크기 상한·리다이렉트 재검증은 `scripts/http.py`가 강제. 검증: `ruff` / `bandit` / `pip-audit`.
- 설계·결정 배경: [PROJECT_BRIEF.md](PROJECT_BRIEF.md). X(트위터)는 phase 2(유료/수동).
