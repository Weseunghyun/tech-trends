---
title: "Data Model: AI·개발/기술 트렌드 종합 대시보드"
type: data-model
project: "tech-trends"
feature: "daily-trends-dashboard"
branch: "feature/daily-trends-dashboard"
status: Draft
created: 2026-06-13
updated: 2026-06-13
tags:
  - sdd
  - sdd/data-model
---

# Data Model: AI·개발/기술 트렌드 종합 대시보드

spec의 Key Entities를 구현 가능한 스키마로 구체화한다. 산출물은 정적 JSON(`docs/data/*.json`)이며 DB는 없다(헌법 VI). 외부에서 받는 모든 입력 필드는 사용 전 검증한다(SEC-05).

## 엔티티

### TrendItem (트렌드 항목)

한 소스에서 수집된 단일 항목.

| 필드 | 타입 | 필수 | 설명 / 검증 |
|---|---|---|---|
| `id` | string | ✔ | 정규화 URL의 SHA-1 16진. 중복 제거·dedup 키 |
| `title` | string | ✔ | 항목 제목. 1~300자로 trim·길이 컷. 빈 제목이면 항목 폐기 |
| `url` | string | ✔ | **정규화된 원문 URL**(R3). `^https?://` 형식 검증, 미충족 시 폐기. 출처 없으면 표시 안 함(FR-003) |
| `source` | string | ✔ | 소스 식별자(enum): `github_trending`,`anthropic`,`openai`,`deepmind`,`meta_ai`,`mistral`,`xai`,`openai_codex`,`hackernews` |
| `category` | string | ✔ | 카테고리 enum(아래 Category). 소스→카테고리 매핑으로 결정 |
| `summary_ko` | string | ✔ | 한글 요약(에이전트 생성). 0~600자 컷. 생성 실패 시 빈 문자열("")(추정 금지, 헌법 III) |
| `lang` | string | ✔ | 원문 언어 코드(`en`/`ko`/…). 미상이면 `"unknown"` |
| `published_at` | string\|null | | 발행 일시 ISO 8601(KST). 피드에 없으면 null(추정 금지) |
| `collected_at` | string | ✔ | 수집 일시 ISO 8601(KST) |
| `metrics` | object\|null | | 소스별 지표. HN: `{points:int, comments:int}`. GitHub: `{stars_added:int}`(가능 시). 없으면 null |

검증 규칙(SEC-05): `url`은 `^https?://[^\s]{1,2048}$`; `title`·`summary_ko`는 길이 컷; `metrics` 정수는 `>=0` 아니면 무시. 결측은 null/""로 두고 보간하지 않는다.

### HotTopic (핫토픽)

여러 TrendItem을 묶어 도출한 화제 주제(R2).

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `topic` | string | ✔ | 표시 제목 = 최고 engagement 멤버 제목 |
| `trend_score` | number | ✔ | 0.0~1.0. `0.6*norm_src_count + 0.4*norm_hn_engagement`(실측만) |
| `src_count` | int | ✔ | 출현한 서로 다른 소스 수(≥1) |
| `items` | TrendItem[] | ✔ | 근거 항목들(각자 출처 링크 포함, FR-003) |
| `hn` | object\|null | | `{points:int, comments:int}` 합. HN 멤버 없으면 null |

정렬: `trend_score` 내림차순, 상위 10(FR-008/FR-017).

### Category (카테고리)

대시보드 탭/섹션. enum 고정(FR-007):

| 코드 | 표시명 | 소속 소스(TrendItem.category) | 탭 렌더 대상 |
|---|---|---|---|
| `ai_labs` | AI 랩 동향 | anthropic, openai, deepmind, meta_ai, mistral, xai | TrendItem[] |
| `github_trending` | GitHub Trending | github_trending | TrendItem[] |
| `codex` | OpenAI Codex | openai_codex | TrendItem[] |
| `eng_blogs` | 엔지니어링/기술 블로그 | (AI 랩 외 eng blog RSS; phase 1은 비거나 ai_labs와 공유 가능) | TrendItem[] |
| `hot_topics` | 핫토픽/화두 | hackernews (HN 원천 TrendItem의 category) | **HotTopic[]** (전 소스 집계, `categories`가 아닌 최상위 `hot_topics`에 저장) |

- `categories` 객체에는 콘텐츠 4탭(`ai_labs`,`github_trending`,`codex`,`eng_blogs`)의 TrendItem[]만 담는다. `hot_topics` 탭은 최상위 `hot_topics` 배열(HotTopic[])을 렌더한다 — `categories`에 `hot_topics` 키를 두지 않는다(contracts 단일 출처 규칙).
- HN 원천 TrendItem은 `category="hot_topics"`로 태깅되어 HotTopic 집계의 근거가 된다(개별 콘텐츠 탭으로 직접 렌더되지는 않음).
- 콘텐츠 4탭은 각각 항목 약 10개 상한(FR-017), 핫토픽은 상위 10 HotTopic.

### DashboardSnapshot (대시보드 스냅샷) — 일자 산출물 루트

`docs/data/YYYY-MM-DD.json` 및 `latest.json`의 최상위 구조.

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `schema_version` | int | ✔ | 스키마 버전(시작 1) |
| `generated_at` | string | ✔ | 수집 기준 일시 ISO 8601(KST). 신선도 표시(FR-012) |
| `date` | string | ✔ | 기준 일자 `YYYY-MM-DD`(KST) |
| `categories` | object | ✔ | 카테고리 코드 → TrendItem[] (각 ~10개) |
| `hot_topics` | HotTopic[] | ✔ | 상위 핫토픽(점수 내림차순) |
| `sources` | SourceStatus[] | ✔ | 소스별 수집 성공/실패(FR-009) |

### SourceStatus (소스 상태)

부분 성공·실패 격리 가시화(FR-009, US3).

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `source` | string | ✔ | 소스 식별자 |
| `ok` | bool | ✔ | 수집 성공 여부 |
| `item_count` | int | ✔ | 수집 항목 수(실패 시 0) |
| `error_type` | string\|null | | 실패 시 예외 타입명만(값·자격증명 금지, SEC-02). 성공 시 null |
| `feed_built_at` | string\|null | | RSS `lastBuildDate` 등 신선도 단서 |

## 보조 영속 데이터

### SeenLedger — `docs/data/seen_urls.json` (R3)

```json
{ "<normalized_url>": "YYYY-MM-DD", ... }
```

정규화 URL → 최초 발견일. 30일 초과 항목 prune. 일자 간 중복 제거(FR-011)의 단일 출처.

### Manifest — `docs/data/index.json`

```json
{ "dates": ["2026-06-13", "..."], "generated_at": "2026-06-13T08:05:00+09:00" }
```

최근(≤30) 일자 목록. 수집기가 중복 제거 윈도를 O(30)로 읽는 매니페스트.

## 라이프사이클 / 상태 전이

1. **수집**: 소스별 fetch → 항목 정규화·검증 → 실패 소스는 `SourceStatus.ok=false`로 격리(전체 중단 없음, FR-009).
2. **중복 제거**: `seen_urls.json` 로드·prune → 정규화 URL로 신규만 통과(FR-011).
3. **요약**: 신규 항목에 에이전트가 `summary_ko` 부여(영문→한글, FR-004). 실패 시 "".
4. **점수**: 그룹핑→정규화→가중합으로 HotTopic 산출(FR-008).
5. **산출**: `YYYY-MM-DD.json` 작성 → `latest.json` 복사 → `index.json` 갱신 → 30일 prune → `seen_urls.json` 갱신.
6. **커밋**: `docs/data` 단일 커밋 add(+delete) → push.

모든 단계에서 결측/실패는 빈 값·"데이터 없음"으로 두고 추정으로 채우지 않는다(헌법 III, FR-010).

## 불변식

- 표시되는 모든 TrendItem은 `url`(정규화·검증 통과)을 가진다 — 출처 없는 항목 0건(SC-002).
- `trend_score`는 실측 수치만의 함수 — 임의 보정 0건(SC-004).
- working tree의 `data/YYYY-MM-DD.json`은 항상 ≤30개(R7).
- 어떤 산출물·로그에도 시크릿 평문 없음(SC-006, SEC-01).
