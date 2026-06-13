---
title: "Tech Trends Constitution"
type: constitution
feature: project-wide
branch: ""
status: Active
created: 2026-06-13
updated: 2026-06-13
tags:
  - sdd
  - sdd/constitution
---

# Tech Trends Constitution

이 문서는 tech-trends 프로젝트의 **비가역 원칙**을 정의한다. 모든 SDD 단계(specify→clarify→plan→tasks→analyze→implement)는 이를 고정 컨텍스트로 참조하며, 어떤 기능 요구도 이 원칙을 위반할 수 없다. 충돌 시 본 헌법이 우선한다.

프로젝트 성격: 혼자 보는 **AI·개발/기술 트렌드 종합 대시보드**. 매일 정해진 시각에 무료 공개 소스(RSS·공개 API)에서 최신 동향·화제 주제를 모아 요약하고, **공개 GitHub Pages 정적 대시보드**로 폰·아무 브라우저에서 본다. 개인정보·민감 데이터는 다루지 않는다.

## Core Principles

### I. 공개·정적 우선, 시크릿 미노출 (Public-Static First) — NON-NEGOTIABLE
대시보드는 공개되어도 무방한 데이터만 다룬다(개인정보 없음). 산출물은 정적 파일(JSON/HTML)로 공개 repo + GitHub Pages에 둔다. **API 키·토큰(GitHub PAT, 향후 X 키 등)은 repo·산출물·로그·stdout 어디에도 노출하지 않는다** — 환경변수/스케줄러 시크릿으로만 주입한다. 위험 실행(`eval`/`exec`/`os.system`/`shell=True`) 금지. 외부 HTTP는 `verify=True`·`timeout`·`raise_for_status()`.

### II. 클라우드 가용 소스만 자동화 (Cloud-Reachable Automation)
자동(무인) 파이프라인은 **클라우드/해외 IP에서도 동작하는 소스만** 사용한다. 데이터센터 IP를 차단하거나 로그인이 필요한 소스(예: X 로그인 세션 크롤링, 네이버·KRX류 비공식 API)는 자동 경로에서 제외한다. 비공식 소스를 쓸 땐 반드시 클라우드 가용 폴백을 함께 둔다. (근거: stock-routine에서 네이버 API가 클라우드 IP 차단으로 전 종목 실패한 사례.)

### III. 데이터 무결성·출처 명시 (No Fabrication, Always Attribute)
수집 항목은 **원문 출처 링크를 반드시 포함**한다. 요약·트렌드 점수는 실제 수집 데이터에 근거하며, 없는 사실·추측·환각을 만들지 않는다. 소스가 결측/실패하면 빈 값 또는 "데이터 없음"으로 두고 추정으로 채우지 않는다.

### IV. 외부 소스 실패 격리 (Failure Isolation)
개별 소스(RSS·API) 하나의 실패가 전체 빌드를 중단시키지 않는다. 호출은 예외를 잡아 건너뛰고 부분 성공 결과로 대시보드를 갱신한다. 외부에서 받은 값(URL·제목 등)은 사용 전 형식·길이를 검증한다.

### V. ToS·예의 준수 (Respect ToS & robots)
공개 RSS·공식 API·문서화된 공개 엔드포인트만 자동 수집한다. 로그인 세션을 이용한 자동 스크래핑, robots/ToS가 금지하는 크롤링은 하지 않는다(개인 계정 정지 위험). X 등 제약 소스는 수동/대화형 또는 유료 공식 API로만 다룬다.

### VI. 최소주의 (Simplicity / YAGNI)
혼자 보는 일일 대시보드다. 서버·DB·인증·결제 등 요청되지 않은 인프라를 추가하지 않는다. 정적 사이트(GitHub Pages) + 스케줄 수집으로 충분하다. 의존성은 핀 고정하고 추가 시 취약점 점검한다.

## 기술 제약 (Technical Constraints)

- 수집·요약 실행 단위: 스케줄 자동화(예: claude.ai/code 루틴 또는 GitHub Actions cron). 요약은 가능하면 루틴의 에이전트 LLM이 직접 수행해 별도 LLM API 키 의존을 피한다.
- 산출물: `data.json`(수집·요약 결과) + 정적 대시보드(HTML/JS). 공개 repo에 커밋 → GitHub Pages 서빙. 대시보드는 같은 출처의 JSON을 fetch(키·CORS 불필요).
- 소스 1단계(무료·무키): GitHub Trending(비공식 RSS), AI 랩 블로그(공개/생성 RSS), OpenAI Codex 공식 RSS, Hacker News(Algolia 공개 API). X는 phase 2.

## 개발 워크플로우 (Development Workflow)

- SDD 산출물은 로컬 `specs/<feature-slug>/`에 둔다.
- 브랜치는 `feature/<slug>` 기본. 커밋은 `commit-rule` 스킬 형식(외부 이슈 트래커 꼬리말 없음, Claude 꼬리말 금지).
- 개인 프로젝트이므로 커밋 후 push까지 수행 가능(사용자 승인됨).
- Python 코드 구현 시 `impl-python-validate`로 보안/품질 검증(`.claude/rules/python-security.md` SEC-01~09). JS/정적 산출물은 해당 시 별도 점검.

## Governance

본 헌법은 다른 모든 관행에 우선한다. 원칙 변경은 명시적 개정과 버전 갱신을 거친다. 특히 원칙 I(시크릿 미노출)·V(ToS 준수)는 협상 불가다.

**Version**: 1.0.0 | **Ratified**: 2026-06-13 | **Last Amended**: 2026-06-13
