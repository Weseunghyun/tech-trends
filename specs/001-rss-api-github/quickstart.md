---
title: "Quickstart: AI·개발/기술 트렌드 종합 대시보드"
type: quickstart
project: "tech-trends"
feature: "daily-trends-dashboard"
branch: "feature/daily-trends-dashboard"
status: Draft
created: 2026-06-13
updated: 2026-06-13
tags:
  - sdd
  - sdd/quickstart
---

# Quickstart: 로컬 실행 & 검증

전제: Python 3.11+, 공개 GitHub repo(이미 보유), `feature/daily-trends-dashboard` 브랜치.

## 1. 의존성

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt   # feedparser==6.0.11, requests==2.33.0
```

## 2. 수집 dry-run (네트워크만, 쓰기 없음)

```bash
python -m scripts.collect --dry-run
```

기대: 소스별 수집 항목 수·성공/실패 통계가 stdout에 출력(시크릿 미출력). 1개 이상 소스 실패해도 종료코드 0(부분 성공). 전 소스 실패 시에만 1.

## 3. 실제 산출물 생성 (로컬)

```bash
python -m scripts.collect --date 2026-06-13 --out docs/data
ls docs/data/   # latest.json, 2026-06-13.json, index.json, seen_urls.json
```

기대: `latest.json`이 당일 스냅샷과 동일, `index.json.dates`에 당일 포함, 30일 초과 파일 없음.

## 4. 대시보드 로컬 미리보기 (동일 출처)

```bash
cd docs && python -m http.server 8080
# 브라우저: http://localhost:8080/  → data/latest.json 로드 확인
```

기대: 카테고리 탭(AI 랩 동향/GitHub Trending/엔지니어링·기술 블로그/OpenAI Codex/핫토픽)에 항목·한글 요약·출처 링크 표시. 핫토픽은 점수 내림차순. 모바일 폭(≈375px)에서 가로 스크롤 없음. 빈 카테고리는 "항목 없음".

## 5. 검증 게이트

```bash
# 파이썬 보안/품질 (SEC-01~09)
#  ruff → bandit → pip-audit
ruff check scripts/ && bandit -q -r scripts/ && pip-audit -r requirements.txt
```

(미설치 도구는 graceful skip — `impl-python-validate` 스킬이 일괄 실행)

수동 검증 항목:
- [ ] 표시 항목 100%가 클릭 가능한 출처 링크 보유(SC-002)
- [ ] 한 소스 강제 실패(잘못된 URL) 시 나머지로 갱신·실패 격리(US3)
- [ ] 산출물/로그에 토큰·키 평문 없음(SC-006)
- [ ] 영문 항목 요약이 한글, 원문 제목·링크 보존(SC-007)
- [ ] 동일 URL 항목이 일자에 걸쳐 1회만 노출(SC-008)

## 6. 배포 (GitHub Pages)

1. Settings → Pages → Source: Deploy from a branch, Branch: `main`, Folder: `/docs`.
2. 스케줄 루틴이 매일 KST 08:00경 수집→요약→`docs/data` 커밋·푸시.
3. 공개 URL: `https://<id>.github.io/<repo>/`.

## 7. 스케줄 등록

- 1차: claude.ai/code 스케줄 루틴(에이전트 인라인 요약, 별도 LLM 키 없음).
- 폴백: `.github/workflows`의 cron `0 23 * * *`(=08:00 KST), 내장 `GITHUB_TOKEN`로 push.
