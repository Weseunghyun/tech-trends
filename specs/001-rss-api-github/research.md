---
title: "Research: AI·개발/기술 트렌드 종합 대시보드"
type: research
project: "tech-trends"
feature: "daily-trends-dashboard"
branch: "feature/daily-trends-dashboard"
status: Draft
created: 2026-06-13
updated: 2026-06-13
tags:
  - sdd
  - sdd/research
---

# Research: AI·개발/기술 트렌드 종합 대시보드

0단계 리서치. 기술 컨텍스트의 불명확 항목과 외부 소스 가용성을 해소한다. 모든 소스는 2026-06-13에 직접 재확인(헌법 II·III 근거).

## R1. 소스 가용성 (직접 재확인)

**결정**: 아래 4계열 소스를 1단계 자동 수집 대상으로 확정. 모두 무료·무키이며 클라우드/데이터센터 IP에서 도달 가능(GitHub Pages/Fastly, raw.githubusercontent, Algolia CDN, OpenAI/Cloudflare).

| 소스 | 엔드포인트(확정) | 형식 | 비고 |
|---|---|---|---|
| GitHub Trending(전 언어, 일간) | `https://mshibanami.github.io/GitHubTrendingRSS/daily/all.xml` | RSS 2.0 | 언어별: `.../daily/{language}.xml`. 일간 all은 항목 ~8개로 적음. `lastBuildDate`로 신선도 확인 |
| AI 랩 — Anthropic | `https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_news.xml` (+ research/engineering/red) | RSS 2.0 | 시간당 생성. 신선 확인 |
| AI 랩 — Meta AI | `.../feeds/feed_meta_ai.xml` | RSS 2.0 | |
| AI 랩 — Mistral | `.../feeds/feed_mistral.xml` | RSS 2.0 | 발행 빈도 낮음(정상) |
| AI 랩 — xAI | `.../feeds/feed_xainews.xml` | RSS 2.0 | 발행 빈도 낮음(정상) |
| AI 랩 — OpenAI | `https://openai.com/news/engineering/rss.xml`, `https://openai.com/blog/rss.xml` | RSS 2.0 | **Olshansk 미수록** → 1차 공식 RSS. 사이트 개편·봇 필터 위험 |
| AI 랩 — DeepMind | `https://deepmind.google/blog/rss.xml` | RSS 2.0 | **Olshansk 미수록** → 1차 공식 RSS |
| OpenAI Codex 체인지로그 | `https://developers.openai.com/codex/changelog/rss.xml` | RSS 2.0 | 최신 2026-06-11 확인. 릴리스마다 갱신 |
| Hacker News | `https://hn.algolia.com/api/v1/search?tags=front_page`, `.../search_by_date?tags=story` | JSON | 무키. `points`·`num_comments`·`created_at_i` 제공. ~10k req/h/IP, 429 백오프 |

**근거**: 헌법 II(클라우드 가용)·V(공개 공식 엔드포인트만)에 부합. HN은 가장 클라우드 친화적. RSS 계열은 스크레이퍼 백엔드라 200이어도 staleness 가능 → 항상 `lastBuildDate`/최신 `pubDate` 확인.

**고려된 대안**: GitHub Trending 웹페이지 직접 스크래핑(항목 더 많음) → ToS/안정성·클라우드 차단 위험으로 제외(헌법 II·V). Olshansk에 OpenAI/DeepMind 위탁 → 미수록이라 불가, 공식 RSS로 대체.

**실패 모드 대응**: 개별 소스 200 응답이라도 staleness 가능 → 신선도 점검. OpenAI/DeepMind 1차 RSS는 봇 챌린지 가능 → 정상 User-Agent, 낮은 빈도. 모든 소스는 실패 격리(헌법 IV)로 건너뜀.

## R2. 트렌드 점수 산식 (핫토픽)

**결정**: 토픽 그룹핑 후 **실측 수치 2개만의 정규화 가중합**으로 0~1 점수 산출. 임의 부스트·소스별 권위 가중치 없음(헌법 III).

- **그룹핑**: 제목 토큰 집합(stopword 제거)으로 Jaccard 유사도 ≥ 0.5이거나 정규화 URL 동일 시 같은 토픽. 그리디 단일 패스 O(n²)(일 수십~수백 항목이라 충분). 표시 제목 = 최고 engagement 멤버 제목. 임베딩/NLP 클러스터링은 YAGNI로 제외.
- **원시 신호**: `src_count`(토픽이 출현한 **서로 다른 소스 수**), `hn_points`·`hn_comments`(토픽의 HN 멤버 합; 없으면 0).
- **정규화**: HN은 heavy-tail → `log1p` 압축 후 그날 토픽들에 대해 min-max. `hn_engagement_raw = log1p(points) + 0.5*log1p(comments)`(댓글 0.5는 두 HN 필드 간 구조적 비율, 점수 부스트 아님). `src_count`도 min-max.
- **최종 점수**: `trend_score = 0.6*norm_src_count + 0.4*norm_hn_engagement`. 내림차순 정렬 후 상위 N(=10) 표시.
- **설정 상수**: `W_SRC=0.6`, `W_HN=0.4`, `COMMENT_RATIO=0.5`, `JACCARD=0.5` — 모듈 상단에 명시, 첫 며칠 결과 보고 조정.

**근거**: 교차 출현(0.6)이 "화두"의 가장 견고한 신호. 데이터 결측 시 해당 항은 정직하게 0(백필 없음 → 헌법 III). log+min-max는 upvote/comment heavy-tail의 표준 처리.

**고려된 대안**: HN gravity 시간감쇠(일 1회 스냅샷이라 무의미), z-score(안정 평균 필요), 임베딩 클러스터링(불투명·의존성), 소스별 권위 가중치(임의 부스트=헌법 위반) → 모두 제외.

## R3. 중복 제거 (정규화 URL + 30일 원장)

**결정**: 고정된 안전·멱등 변환으로 URL 정규화 후 중복 판정. 일자 간 중복은 커밋되는 `seen_urls.json` 원장으로 기억.

- **정규화 변환(안전)**: ① scheme 소문자 + http→https 통일, ② host 소문자 + 선행 `www.` 제거(비기본 포트는 보존), ③ 경로 끝 `/` 1개 제거(루트 제외), ④ `utm_*` 및 큐레이트된 추적 파라미터(fbclid, gclid, ref, mc_cid 등) 제거 후 나머지 정렬, ⑤ **fragment 보존**.
- **건드리지 않음(불안전)**: 경로 대소문자(서버 case-sensitive), 비추적 쿼리(`id`,`page`,`v` 등) — 자원을 바꾸므로 보존.
- **⚠️ fragment 보존(구현 중 보정)**: 초기 설계는 fragment를 제거하려 했으나, **OpenAI Codex changelog가 fragment(`#codex-2026-06-11-app`)로 개별 항목을 구분**한다(94개 항목이 동일 경로 + 다른 fragment). 제거 시 전 항목이 1개로 병합되므로 fragment를 보존한다. 비용: `#top` 류 무의미 fragment가 false 구분을 만들 수 있으나, 현 소스에선 항목 병합 손실이 더 큰 위험이라 보존이 옳다.
- **엣지**: HN 텍스트 글(외부 URL 없음)은 `https://news.ycombinator.com/item?id={objectID}`를 키로. 동일 기사·다른 도메인(신디케이션)은 URL로 못 잡음 → R2 제목 그룹핑이 토픽 레이어에서 처리(2계층 분리).
- **30일 원장**: `seen_urls.json`(정규화 URL → 최초 발견일). 매 실행: 로드 → 30일 초과 prune → 신규 항목 정규화 후 원장에 있으면 drop, 없으면 today로 추가·유지 → 저장·커밋. 외부 저장소 불필요.

**근거**: 정확 URL 중복(결정적·안전)과 퍼지 토픽 그룹핑(best-effort)을 분리해 각각 단순·디버그 가능. stdlib `urllib.parse`로 ~60줄 명시 로직(감사 가능) → `w3lib.canonicalize_url`보다 의존성·불필요 변환 적음.

**고려된 대안**: 제목 해시 중복(제목 수정됨), 무한 이력 보관(원장 무한 증가) → 제외.

## R4. 파이썬 라이브러리 (RSS 파싱 + HTTP)

**결정**:

| 용도 | 라이브러리 | 핀 버전(2026-06) | 근거 |
|---|---|---|---|
| RSS+Atom 파싱 | feedparser | `feedparser==6.0.11` | RSS 1.0/2.0·Atom·RDF·malformed 모두 처리, 날짜 정규화. 이 프로젝트의 이종 피드에 적합 |
| HTTP | requests | `requests==2.33.0` | 성숙, SEC-04(timeout·verify=True·raise_for_status)에 정합. stock-routine과 동일 |
| HTML 정리(필요 시) | stdlib `html`/`html.parser` | — | 피드 본문 HTML 제거. 필요시에만 beautifulsoup4 추가 |

- **LLM SDK 없음**: 요약/번역은 오케스트레이팅 에이전트가 직접 → `anthropic`/`openai` 패키지 미포함(requirements.txt에서 의도적 부재).
- **패턴**: `requests`로 fetch(timeout=15, verify 기본, raise_for_status) → **bytes를 feedparser.parse에 전달**(feedparser가 URL 직접 fetch하면 timeout/verify 우회 → 금지). `bozo` 플래그 시 예외 타입만 stderr 기록(SEC-02). HN은 RSS 없음 → 동일 fetch 패턴 + `resp.json()`.

**근거**: feedparser는 이종·malformed 피드 현실을 graceful하게 처리(KISS). requests는 기존 레포 도구이자 SEC-04에 매핑. async(httpx)는 일 1회 수십 피드엔 조기 최적화.

**고려된 대안**: httpx(비동기 불필요), atoma(malformed에 엄격), lxml 수작업(다이얼렉트·날짜 재구현) → 제외. 추가 시 `pip-audit`(SEC-08).

## R5. 정적 대시보드 + 데이터 레이아웃 (GitHub Pages)

**결정**: 단일 repo, 기본 브랜치 `/docs` 퍼블리시. 하이브리드 레이아웃 — `latest.json`(대시보드가 로드 시 읽는 단일 빠른 경로) + `data/YYYY-MM-DD.json`(30일 윈도, 수집기 중복 제거용) + `index.json`(매니페스트).

```text
docs/
  index.html        # 단일 페이지, 외부 CDN 0, 모바일 반응형, 탭/카드
  app.js            # fetch + 렌더
  styles.css
  data/
    latest.json     # 오늘 파일 복사본 — 페이지가 로드 시 읽는 유일 파일
    2026-06-13.json # 일자 아카이브(오늘+직전 29일)
    ...
    index.json      # {"dates":[...], "generated_at":"..."}
```

- **로드(빠른 경로)**: `index.html`이 `data/latest.json`만 fetch(상대경로, `?v=<ts>` + `cache:"no-store"`로 캐시 버스팅). 30일 아카이브는 런타임에 안 읽음.
- **동일 출처**: 같은 repo `/docs` → `https://<id>.github.io/<repo>/`에서 same-origin. 상대경로 사용(`data/latest.json`, 선행 `/` 금지)해 project-pages 서브패스에서 동작. CORS·키 불필요.
- **서빙**: Settings→Pages, Source=Deploy from a branch, Branch=`main`(또는 배포 브랜치), Folder=`/docs`. 수집 코드·requirements는 사이트에서 제외됨.

**근거**: 단일 fetch = 모바일 빠른 첫 페인트, 30일 이력은 수집기 관심사. 상대 same-origin으로 CORS/키 제거.

**고려된 대안**: 단일 롤링 data.json(30일 전체 다운로드=느림), 일자 파일만(프론트가 today 추정→타임존 버그·404), gh-pages 브랜치(기계장치 과다) → 제외.

## R6. 스케줄링 (매일 ~08:00 KST)

**결정**: **1차 = claude.ai/code 스케줄 루틴**이 파이썬 수집기 실행 + 한글 요약을 **에이전트가 인라인** 수행 + 공개 repo에 JSON 커밋·푸시(별도 LLM 키 불필요). **GitHub Actions cron은 폴백**으로 문서화.

루틴 1회 작업: 수집(fetch RSS/API) → 최근 `data/*.json` 윈도로 일자 간 중복 제거 → 에이전트 한글 요약/큐레이션 → `data/YYYY-MM-DD.json` 작성·`latest.json` 복사·`index.json` 갱신·30일 prune → `git add docs/data && commit && push`.

- **1차 근거**: 별도 LLM 키 관리 불필요(에이전트가 요약자). 단일 소유자·일 1회 repo write엔 충분.
- **폴백(GH Actions cron)**: cron은 UTC → 08:00 KST = `cron: "0 23 * * *"`. **타이밍 비보장**(수십 분 지연·고부하 시 silent skip 가능) → "08시경"으로 취급. 60일 무커밋 시 스케줄 자동 비활성(일일 커밋이 유지). 푸시는 `permissions: contents: write`의 내장 `GITHUB_TOKEN`로 충분(PAT 불필요). LLM 키 사용 시 Actions Secret으로만, 커밋·출력 금지(SEC-01/09).

**근거**: LLM 인라인 + 추가 자격증명 0 + 이동부품 최소. 폴백 문서화로 루틴 장애 시에도 "Actions+키" 또는 "Actions+원시데이터"로 degrade.

**고려된 대안**: Actions+LLM키 1차(유료 의존·시크릿 회전), 셀프호스트 cron(인프라 소유) → 폴백/제외.

## R7. 30일 롤링 보관 메커니즘

**결정**: 매 실행 끝에 30일 초과 일자 파일 삭제 → `latest.json`·`index.json` 갱신 → 한 커밋으로 add+delete 반영. 중복 제거는 윈도 내 파일(또는 `index.json`)만 스캔(O(30), 저렴).

- **git 이력 트레이드오프(명시)**: working tree에서 삭제해도 **git 이력엔 잔존** → `.git`이 일 1파일씩 증가. 단일 소유자·소형 JSON이라 수년간 무시 가능, 디버깅에 유용. **이력 재작성 금지**(filter-repo/squash는 공개 클론 깨고 순오버헤드). 규모 문제 시(현 규모엔 없음)에만 squash/별도 데이터 브랜치 — 지금은 범위 밖(YAGNI).

**근거**: prune-in-place + 단일 커밋으로 working tree 정확히 30파일 유지(중복 제거 빠름·Pages 페이로드 예측 가능), 이력 증가는 무해.

**고려된 대안**: 이력 재작성(공개 클론 깨짐), orphan 데이터 브랜치(브랜치 관리 오버헤드), 아카이브 없이 단일 롤링 파일(전체 파싱) → 제외.

## 미해결/주의

- 모든 "명확화 필요" 해소됨(spec Clarifications + 본 리서치).
- 운영 주의: GitHub Trending all 일간 항목 수가 적음 → 언어별 피드(예 `python.xml`,`javascript.xml`) 추가 고려는 구현 시 옵션. OpenAI/DeepMind 1차 RSS는 주기적 재확인 대상.
