# tech-trends — 프로젝트 브리프 (새 세션 시작점)

> 이 파일은 stock-routine 작업 세션에서 넘어온 **인수인계 문서**다. 새 Claude 세션은 이 폴더를 열고 이 브리프를 읽은 뒤 `/sdd-design`으로 시작한다. (연구·결정이 채팅이 아니라 이 파일에 보존됨.)

## 목표

혼자 보는 **AI·개발/기술 트렌드 종합 대시보드**. 매일 자동으로 최신 동향·새 소식·"뜨겁게 화두인 주제"를 모아 요약하고, **공개 GitHub Pages 정적 대시보드**로 폰·아무 브라우저에서 본다. (주식 루틴과 같은 성격이되 데이터·소스만 다름.)

## 왜 새 구조인가 (기존 주식 루틴 대비)

주식 대시보드는 Google Sheets → Cowork/Apps Script로 봤는데 3가지 단점이 있었다:
1. Cowork는 클로드 앱에서만 보임 (앱 종속)
2. Apps Script는 구글 계정 권한 마찰 (여러 계정 쓰면 접근 불편)
3. 루틴/프라이빗 레포 방식은 무난

→ tech-trends는 **개인정보가 없어 공개 OK**라, 시트·Apps Script·Cowork를 거칠 이유가 없다. **"스케줄 수집·요약 → 공개 repo에 JSON 커밋 → GitHub Pages 정적 대시보드"** 가 세 단점을 한 번에 없앤다.

## 확정 아키텍처

```
[스케줄 루틴(매일)]  ─ 무료 RSS/공개 API 수집 → 에이전트 LLM이 "오늘의 화두" 요약
        │                                     (별도 LLM 키 불필요 — 루틴 Claude가 직접)
        ▼  data.json + index.html 커밋
[공개 GitHub repo] ── GitHub Pages ──▶ https://<id>.github.io/tech-trends
                                        (폰·웹·공유 OK, 키·로그인·CORS 불필요)
```

- 대시보드 HTML은 같은 repo의 `data.json`을 fetch(동일 출처). 주식 대시보드 HTML(카드·탭·차트, 외부 CDN 0)을 이식해 룩앤필 재사용 가능.
- 수집·요약 실행은 claude.ai/code 루틴 권장(요약을 에이전트가 직접). 대안: GitHub Actions cron(LLM 요약 시 키 필요).

## 대시보드 범위 (탭/카테고리) — AI에 가두지 말 것

1. **AI 랩 동향**: Anthropic·OpenAI·DeepMind·Meta·Mistral·xAI 블로그 + OpenAI Codex 체인지로그
2. **GitHub Trending**: 전 언어 (AI뿐 아니라 개발 전반)
3. **엔지니어링/기술 블로그**: 대기업 eng blog RSS 모음
4. **핫토픽/화두**: Hacker News 포인트·댓글 + 소스 교차 출현으로 트렌드 점수화
5. *(phase 2)* X 인플루언서 (Karpathy 등) — 아래 참조

## 소스별 수집 가능성 (2026-06 리서치, 핵심은 직접 재확인 ✔)

| 소스 | 방법 | 키/비용 | 비고 |
|---|---|---|---|
| GitHub Trending | [GitHubTrendingRSS](https://github.com/mshibanami/GitHubTrendingRSS) 언어별 RSS (GitHub Actions→Pages, 활성) | 없음/무료 ✔ | 공식 API 없음 |
| AI 랩 블로그 | [Olshansk/rss-feeds](https://github.com/Olshansk/rss-feeds) — Anthropic·OpenAI·DeepMind·Meta·Mistral·xAI·Cohere, 시간당 갱신 static XML(raw.githubusercontent) | 없음/무료 ✔ | 12.7k 커밋, 매우 활성 |
| OpenAI Codex | 공식 RSS `https://developers.openai.com/codex/changelog/rss.xml` (최신 2026-06-11) | 없음/무료 ✔ | |
| 핫토픽 | [Hacker News Algolia API](https://hn.algolia.com/api) (포인트·댓글) + GitHub REST(스타 증가) | 없음(HN)/GitHub 토큰 권장 | 무료 |
| 기술블로그 집계 | techblogposts.com API 불명확 → kilimchoi engineering-blogs RSS 목록 + 위 Olshansk 대체 | 없음/무료 | |
| **X/트위터** | **2026 무료 사실상 폐지.** 종량제 읽기 $0.005/포스트(2026-02-06~), 핵심 5명 ≈ 월 $15. 무료 우회(Nitter 등) 거의 죽음 | **유료·키 필요** | **phase 2** |

## 결정 사항

- **phase 1 = X 제외**, 무료·무키 소스로 자동 MVP부터. X는 키 생기면 phase 2로 추가.
- X 수동 보강 옵션: 필요 시 사용자가 Claude in Chrome으로 로그인된 X 피드를 **대화형으로** 요약(자동 아님, 무료, ToS·계정 안전). 자동 일일에는 미포함.
- 요약 엔진: 루틴의 에이전트 LLM이 직접 → 별도 LLM API 키 불필요.
- 공개 대시보드(링크 공유 OK).

## ⏭️ Phase 2 — 약속된 후속 작업 (MVP 완성 후)

**"X 우회법 매우 상세 검색"** — 사용자가 명시 요청. MVP가 돌아간 뒤, X(트위터) 인플루언서를 자동으로 따라가는 현실적 방법(공식 종량제 vs 비공식 third-party API[twitterapi.io/getxapi 등]의 2026 현재 비용·ToS·합법성·안정성)을 deep-research로 상세 조사한다. 그 전엔 X는 phase 1에서 빼고, 수동 보강만.

## 기존 유사 솔루션 (재발명 방지·벤치마크)

- [smol.ai / AINews](https://smol.ai/) — 매일 AI 뉴스를 X·Discord·Reddit에서 모아 요약하는 뉴스레터. 구상과 거의 동일 → 벤치마크/부분 구독 가치. 단 "커스텀 대시보드+화제도 점수"는 기성품이 안 맞아 직접 만들 가치 있음.
- [readless.app AI RSS 목록](https://www.readless.app/blog/best-ai-news-rss-feeds-2026), FreshRSS/Miniflux(셀프호스트 리더 — 우리 용도와 다름).

## 작업 스타일 (stock-routine에서 이어옴)

- **SDD 파이프라인**: specify→clarify→plan→tasks→analyze→implement. `.specify`·sdd 스킬·헌법 이미 이 repo에 복사됨.
- **커밋**: `commit-rule` 형식(제목 + 1.기능추가/2.버그수정/3.개발환경변경). **Co-Authored-By/Claude 꼬리말 절대 금지.**
- **푸시**: 개인 프로젝트라 커밋 후 push까지 자동 OK.
- **검증**: 매 단계 테스트 + dry-run + (Python이면) ruff/bandit. 미보정·실패격리·시크릿 미노출.
- **교훈**: 클라우드 IP에서 비공식/로그인 소스는 차단됨 → 자동 경로엔 클라우드 가용 소스만(헌법 II).

## 새 세션 시작 방법

이 폴더(`tech-trends`)에서 새 Claude 세션을 열고:

```
/sdd-design AI·개발/기술 트렌드 종합 대시보드. 무료 공개 RSS·API(GitHub Trending·AI랩 블로그·OpenAI Codex·Hacker News)를 매일 수집·요약해 공개 GitHub Pages 정적 대시보드로 보여준다. X는 phase 2(유료/수동). 자세한 결정·소스·아키텍처는 PROJECT_BRIEF.md 참조.
```
