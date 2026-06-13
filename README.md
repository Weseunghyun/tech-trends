# tech-trends

AI·개발/기술 트렌드 종합 대시보드. 매일 KST 08:00경 무료 공개 소스(GitHub Trending·AI 랩 블로그·OpenAI Codex·Hacker News)에서
최신 동향·화제 주제를 모아 한글로 요약하고, 공개 GitHub Pages 정적 대시보드로 본다. 폰·아무 브라우저에서 로그인·키 없이 본다.

## 아키텍처

```
[스케줄 루틴(매일 KST 08:00)]
  └ 파이썬 수집기(scripts/) — 무료 RSS/API 수집 → 정규화·검증 → 30일 중복 제거 → 트렌드 점수
  └ 에이전트 LLM이 한글 요약(인라인, 별도 LLM 키 불필요)
  └ docs/data/latest.json 커밋·푸시
        ▼
[공개 GitHub repo] ── GitHub Pages(/docs) ──▶ https://<id>.github.io/tech-trends
                                              (정적 HTML/JS가 같은 출처 JSON fetch)
```

## 구조

- `scripts/` — 수집기(Python 3.11+). `config`(소스 9개·점수 상수), `http`/`normalize`/`dedup`/`score`/`render`, `sources/`(RSS·HN 어댑터), `collect`(오케스트레이션).
- `docs/` — 정적 대시보드(외부 CDN 0, 모바일 반응형). `index.html`/`app.js`/`styles.css` + `data/`(`latest.json`·일자 아카이브·`index.json`·`seen_urls.json`).
- `tests/` — 단위(normalize/dedup/score)·통합(수집 스모크·실패 격리).
- `specs/001-rss-api-github/` — SDD 산출물(spec·plan·research·data-model·contracts·tasks).

## 로컬 실행

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt          # feedparser==6.0.11, requests==2.33.0

python -m scripts.collect --dry-run      # 네트워크 수집만(쓰기 없음), 통계 출력
python -m scripts.collect --out docs/data  # 실제 산출물 생성
python -m pytest tests/ -q               # 테스트

cd docs && python -m http.server 8080    # http://localhost:8080 미리보기
```

수집기 옵션: `--dry-run`, `--date YYYY-MM-DD`, `--out <dir>`, `--summaries <json>`(에이전트가 채운 `{item_id: 한글요약}`).

## 배포 (GitHub Pages)

1. Settings → Pages → Source: **Deploy from a branch**, Branch: 기본 브랜치, Folder: **`/docs`**.
2. 공개 URL: `https://<id>.github.io/tech-trends/`.

## 스케줄

- **1차(권장)**: claude.ai/code 스케줄 루틴 — 수집 + 한글 요약을 에이전트가 인라인으로 수행하고 커밋·푸시(별도 LLM 키 없음).
- **폴백**: `.github/workflows/daily.yml` cron `0 23 * * *`(=KST 08:00). LLM 키가 없어 요약은 빈 값으로 커밋되고(추정 금지), 내장 `GITHUB_TOKEN`로 push. cron 타이밍은 비보장.

## 원칙·보안

- 불변 원칙: [.specify/memory/constitution.md](.specify/memory/constitution.md) — 공개·정적·시크릿 미노출, 클라우드 가용 소스만, 출처 필수·무결성, 실패 격리, ToS 준수, YAGNI.
- 파이썬 보안 규칙: [.claude/rules/python-security.md](.claude/rules/python-security.md)(SEC-01~09). 검증: `ruff` / `bandit` / `pip-audit`.
- 설계·결정 배경: [PROJECT_BRIEF.md](PROJECT_BRIEF.md). X(트위터)는 phase 2(유료/수동).
