<!-- Cladding · Tier B · SSoT — LLM-refined · Refreshed by: clad init / clad clarify -->

# tech-trends — Project Context

## 1. Why does this project exist?

AI·개발 기술 동향은 소스가 분산되어(각 랩 블로그, GitHub Trending, Hacker News) 매일 직접 훑는 비용이 크다. 기존 주식 루틴(Google Sheets + Apps Script + Cowork)은 앱 종속·계정 권한 마찰이 있었다. tech-trends는 개인정보가 없어 공개 가능하다는 점을 활용해 **"스케줄 수집·요약 → 공개 repo에 JSON 커밋 → GitHub Pages 정적 대시보드"** 구조로 그 마찰을 제거한다.

## 2. What problem does it solve?

- 매일 여러 소스를 수동으로 확인하는 시간 비용 → 하루 1회 자동 수집·한국어 요약.
- 뉴스 나열이 아니라 **화제도 스코어링**(HN 지표 + 소스 교차 출현)으로 "지금 뜨거운 주제"를 우선 노출.
- 어떤 기기·브라우저에서도 로그인 없이 접근 (앱/계정 종속 제거).

## 3. What is its purpose?

혼자 보는 AI·개발/기술 트렌드 종합 대시보드. 설계 원칙:

- **무키·무로그인**: 클라우드에서 접근 가능한 무료 공개 소스만 자동 경로에 포함 (X 등 쿠키 필요 소스는 로컬 보강/phase 2).
- **무빌드·무CDN**: 대시보드는 vanilla HTML/JS/CSS, 데이터는 동일 출처 JSON fetch.
- **실패 격리·미보정**: 소스 하나가 죽어도 나머지는 산출, 결측은 추정으로 채우지 않음.
- **요약은 에이전트 인라인**: 별도 LLM API 키 없이 루틴 에이전트가 직접 요약.

## See also

- `PROJECT_BRIEF.md` — 인수인계 브리프 (아키텍처 결정·소스 리서치·phase 2 계획)
- `specs/001-rss-api-github/` — SDD 산출물 (spec/plan/tasks/research)
- `docs/conventions.md` — observed code conventions
- `spec/architecture.yaml` — observed layers
- `spec/capabilities.yaml` — capability inventory
- `spec.yaml` — feature registry
