---
title: "Contract: data.json 스키마 (대시보드 ↔ 데이터)"
type: contract
project: "tech-trends"
feature: "daily-trends-dashboard"
branch: "feature/daily-trends-dashboard"
status: Draft
created: 2026-06-13
updated: 2026-06-13
tags:
  - sdd
  - sdd/contract
---

# Contract: `data/latest.json` 및 `data/YYYY-MM-DD.json`

정적 대시보드(HTML/JS)와 수집기 사이의 단일 계약. 대시보드는 이 구조만 가정하고, 수집기는 이 구조를 보장한다. 동일 출처 fetch(키·CORS 불필요).

## 최상위 (DashboardSnapshot)

```json
{
  "schema_version": 1,
  "generated_at": "2026-06-13T08:05:12+09:00",
  "date": "2026-06-13",
  "categories": {
    "ai_labs": [ /* TrendItem[] ~10 */ ],
    "github_trending": [ /* TrendItem[] ~10 */ ],
    "codex": [ /* TrendItem[] ~10 */ ],
    "eng_blogs": [ /* TrendItem[] ~10 (phase 1엔 비거나 ai_labs 공유) */ ]
  },
  "hot_topics": [ /* HotTopic[] 점수 내림차순, 상위 10 */ ],
  "sources": [ /* SourceStatus[] */ ]
}
```

**주의(단일 출처)**: `hot_topics`는 **최상위 배열로만** 존재한다. `categories` 객체 안에는 `hot_topics` 키를 두지 않는다(이중 정의·중복 렌더 방지). `categories`는 콘텐츠 4탭(`ai_labs`,`github_trending`,`codex`,`eng_blogs`)만, 핫토픽 탭은 최상위 `hot_topics`를 렌더한다.

## TrendItem

```json
{
  "id": "9b1c…(sha1-hex)",
  "title": "addyosmani/agent-skills",
  "url": "https://github.com/addyosmani/agent-skills",
  "source": "github_trending",
  "category": "github_trending",
  "summary_ko": "에이전트 스킬 모음 레포. …",
  "lang": "en",
  "published_at": "2026-06-12T00:00:00+09:00",
  "collected_at": "2026-06-13T08:05:00+09:00",
  "metrics": { "stars_added": 320 }
}
```

- 필수: `id`,`title`,`url`,`source`,`category`,`summary_ko`,`lang`,`collected_at`.
- `published_at` 없으면 `null`. `metrics` 없으면 `null`. `summary_ko` 생성 실패 시 `""`.
- `url`은 항상 `https?://`로 시작(검증 통과분만 적재).

## HotTopic

```json
{
  "topic": "Claude Opus tool use",
  "trend_score": 0.96,
  "src_count": 3,
  "hn": { "points": 420, "comments": 180 },
  "items": [ /* TrendItem[] 근거 항목 */ ]
}
```

- `trend_score` ∈ [0.0, 1.0]. `hn`은 HN 멤버 없으면 `null`.

## SourceStatus

```json
{ "source": "openai", "ok": false, "item_count": 0, "error_type": "Timeout", "feed_built_at": null }
```

- 실패 소스도 배열에 포함(부분 성공 가시화, FR-009). `error_type`은 **예외 타입명만**(값·자격증명·URL 토큰 금지, SEC-02).

## 대시보드(소비자) 계약

- 로드 시 **`data/latest.json`만** fetch(상대경로 + `?v=<ts>`, `cache:"no-store"`).
- 카테고리 탭 = `categories` 키. 핫토픽 탭 = `hot_topics`(점수·src_count 배지 표시).
- 각 항목은 `title`(→ `url` 링크) + `summary_ko` 렌더. 빈 카테고리는 "항목 없음" 표시(오류 아님).
- `generated_at` 표시(신선도). `sources` 중 `ok:false`는 "수집 실패" 표시 가능.
- 모르는 추가 필드는 무시(전방 호환). `schema_version` 증가 시 대시보드가 분기 처리.

## 보조 파일 계약

- `data/index.json`: `{ "dates": ["YYYY-MM-DD", …(≤30)], "generated_at": "ISO8601" }`.
- `data/seen_urls.json`: `{ "<normalized_url>": "YYYY-MM-DD", … }` — 수집기 전용(대시보드는 읽지 않음).
