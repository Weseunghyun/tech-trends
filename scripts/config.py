"""수집기 설정 — 소스 목록·카테고리 매핑·점수 상수·한계값.

모든 소스는 무료·무키 공개 엔드포인트이며 클라우드/해외 IP에서 도달 가능하고
로그인이 필요 없다(헌법 II, FR-015). X/Twitter는 phase 1에서 제외한다(FR-016).
구체 엔드포인트 근거는 specs/001-rss-api-github/research.md R1.
"""

from __future__ import annotations

from pathlib import Path
from zoneinfo import ZoneInfo

# 기준 시간대 — "당일" 판정 및 타임스탬프(FR-001)
KST = ZoneInfo("Asia/Seoul")

# 파이프라인 내부 상태(dedup 원장 등) — 공개 배포되는 docs/ 밖, repo 루트 기준(cwd 무관).
# gitignore 대상: 매 실행 last-seen 갱신으로 diff가 커서 커밋 부적합 + 대시보드가 안 씀.
STATE_DIR = Path(__file__).resolve().parents[1] / "state"

# HTTP (SEC-04)
HTTP_TIMEOUT = 15  # connect+read 초
USER_AGENT = "tech-trends/1.0 (personal dashboard)"
HTTP_RETRIES = 2  # 실패 시 추가 재시도 횟수(예의 있는 backoff, 우회 아님)
HTTP_BACKOFF = 1.5  # 재시도 간 대기 배수(초)
HTTP_MAX_REDIRECTS = 5  # 홉마다 목적지 재검증(SSRF 우회 방지)
HTTP_MAX_BYTES = 10_000_000  # 응답 크기 상한 — 무제한 다운로드로 인한 메모리 소진 방지
ARTICLE_MAX_BYTES = 2_000_000  # 기사 본문 fetch 상한(임의 외부 URL이라 더 엄격)

# 카테고리 코드 → 표시명 (FR-007)
CATEGORY_NAMES = {
    "ai_labs": "AI 랩 동향",
    "community": "커뮤니티",
    "github_trending": "GitHub Trending",
    "codex": "OpenAI Codex",
    "eng_blogs": "엔지니어링/기술 블로그",
    "hot_topics": "핫토픽/화두",
}

# 콘텐츠 탭(개별 항목 렌더). hot_topics는 최상위 HotTopic 집계로 별도 렌더.
CONTENT_CATEGORIES = ["ai_labs", "community", "github_trending", "codex", "eng_blogs"]

# 소스 정의 — 닫힌 식별자 목록(현재 16개).
# kind: "rss"(feedparser) | "hn"(Algolia JSON). category: 항목이 귀속될 카테고리 코드.
# 모든 url은 https(verify=True)·클라우드 도달·로그인 불필요.
SOURCES = [
    {
        "id": "github_trending",
        "kind": "rss",
        "category": "github_trending",
        "urls": ["https://mshibanami.github.io/GitHubTrendingRSS/daily/all.xml"],
    },
    {
        "id": "anthropic",
        "kind": "rss",
        "category": "ai_labs",
        "urls": [
            "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_news.xml"
        ],
    },
    {
        "id": "openai",
        "kind": "rss",
        "category": "ai_labs",
        # Olshansk 미수록 → 공식 RSS(research R1). 개편·봇필터 위험 → 실패 격리로 보호.
        "urls": [
            "https://openai.com/news/engineering/rss.xml",
            "https://openai.com/blog/rss.xml",
        ],
    },
    {
        "id": "deepmind",
        "kind": "rss",
        "category": "ai_labs",
        # Olshansk 미수록 → 공식 RSS(research R1)
        "urls": ["https://deepmind.google/blog/rss.xml"],
    },
    {
        "id": "meta_ai",
        "kind": "rss",
        "category": "ai_labs",
        "urls": [
            "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_meta_ai.xml"
        ],
    },
    {
        "id": "mistral",
        "kind": "rss",
        "category": "ai_labs",
        "urls": ["https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_mistral.xml"],
    },
    {
        "id": "xai",
        "kind": "rss",
        "category": "ai_labs",
        "urls": ["https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_xainews.xml"],
    },
    {
        "id": "openai_codex",
        "kind": "rss",
        "category": "codex",
        "urls": ["https://developers.openai.com/codex/changelog/rss.xml"],
    },
    # 엔지니어링/기술 블로그(대기업 eng blog 공식 RSS) — 모두 클라우드/로컬 도달 확인
    {"id": "cloudflare", "kind": "rss", "category": "eng_blogs",
     "urls": ["https://blog.cloudflare.com/rss/"]},
    {"id": "github_blog", "kind": "rss", "category": "eng_blogs",
     "urls": ["https://github.blog/feed/"]},
    {"id": "aws", "kind": "rss", "category": "eng_blogs",
     "urls": ["https://aws.amazon.com/blogs/aws/feed/"]},
    {"id": "stripe", "kind": "rss", "category": "eng_blogs",
     "urls": ["https://stripe.com/blog/feed.rss"]},
    {"id": "meta_eng", "kind": "rss", "category": "eng_blogs",
     "urls": ["https://engineering.fb.com/feed/"]},
    # 커뮤니티 (2026-07-20 추가 — 로컬 도달 확인, 실패 격리로 보호)
    {"id": "reddit_localllama", "kind": "rss", "category": "community",
     "urls": ["https://www.reddit.com/r/LocalLLaMA/.rss"]},
    # HF 블로그는 랩 동향 성격 (모델 릴리스·기법 발표의 주요 진원지)
    {"id": "hf_blog", "kind": "rss", "category": "ai_labs",
     "urls": ["https://huggingface.co/blog/feed.xml"]},
    {
        "id": "hackernews",
        "kind": "hn",
        "category": "hot_topics",
        "urls": ["https://hn.algolia.com/api/v1/search?tags=front_page"],
    },
]

# 닫힌 소스 식별자 enum (data-model과 일치)
SOURCE_IDS = [s["id"] for s in SOURCES]

# 트렌드 점수 상수 — 실측 수치만 사용, 임의 보정 없음(헌법 III)
# raw_score = hn_engagement + SRC_BONUS*(소스수-1) + ITEM_BONUS*log1p(항목수-1)
# 이후 그날 최댓값으로 나눠 0~1로 표시(연속 분포 → 점수가 변별됨).
COMMENT_RATIO = 0.5  # HN 댓글 대 포인트 구조 비율(점수 부스트 아님)
SRC_BONUS = 3.0  # 교차 출현 1개 추가당 가산(중간 화제의 HN 글 수준)
ITEM_BONUS = 0.4  # 토픽 내 항목 수 가산(많이 회자될수록)
JACCARD = 0.5  # 토픽 그룹핑 제목 토큰셋 유사도 임계

# 한계값
PER_CATEGORY = 10  # 카테고리당 표시 항목 상한 (FR-017)
HOT_TOPICS_MAX = 10  # 핫토픽 상위 N (FR-008)
TITLE_MAX = 300  # 제목 길이 컷 (SEC-05)
SUMMARY_MAX = 2500  # 한글 상세 요약 길이 컷(번역·정리·전문용어 설명 포함)
RAW_SUMMARY_MAX = 1000  # 요약 입력용 원문 description 컷
ARTICLE_TEXT_MAX = 5000  # 요약 입력용 본문 추출 텍스트 컷
URL_MAX = 2048
RETENTION_DAYS = 30  # dedup 원장(last-seen) 만료 기준. 일자 아카이브 파일은 영구 보관.
MIN_OK_RATIO = 0.5  # 성공 소스 비율 미달 시 산출물 미갱신(빈약 데이터 덮어쓰기 방지)

SCHEMA_VERSION = 1

# FR-016 가드: 자동 소스에 X/Twitter 엔드포인트가 없어야 한다(assert는 -O에서 제거되므로 raise).
_FORBIDDEN_HOSTS = ("twitter.com", "x.com", "nitter")


def _assert_no_x_sources() -> None:
    for s in SOURCES:
        for u in s["urls"]:
            if any(h in u.lower() for h in _FORBIDDEN_HOSTS):
                raise RuntimeError(f"X/Twitter 소스는 phase 1에서 금지(FR-016): {s['id']}")


_assert_no_x_sources()
