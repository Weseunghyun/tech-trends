"""트렌드 점수 단위 테스트 — research R2 worked example 재현 + 헌법 III(결측 0)."""

from __future__ import annotations

from scripts.score import compute_hot_topics, group_topics, score_topics


def _topic(title, sources, points=0, comments=0, items=None):
    return {
        "title": title,
        "items": items or [],
        "sources": set(sources),
        "hn_points": points,
        "hn_comments": comments,
    }


def test_scoring_orders_and_spreads():
    # 교차출현↑·HN engagement↑ 토픽이 상위; 단일·무HN은 0
    topics = [
        _topic("Claude tool use", ["anthropic", "hackernews", "github_trending"], 420, 180),
        _topic("Rust web framework", ["github_trending", "hackernews"], 950, 240),
        _topic("DeepMind weather", ["deepmind"], 0, 0),
    ]
    result = score_topics(topics)
    assert result[0]["topic"] == "Claude tool use"  # 3소스+HN → 최상위
    assert result[-1]["topic"] == "DeepMind weather"  # 단일소스·무HN → 최하
    assert result[0]["trend_score"] == 1.0  # 최댓값 = 1.0로 정규화
    assert result[-1]["trend_score"] == 0.0
    scores = [r["trend_score"] for r in result]
    assert scores == sorted(scores, reverse=True)
    # 점수가 서로 달라야 함(변별)
    assert len(set(scores)) == 3


def test_hn_only_topics_differentiate_by_points():
    # HN 단일 소스라도 포인트가 다르면 점수가 달라야 한다(전부 동일 금지)
    topics = [
        _topic("big story", ["hackernews"], 1500, 400),
        _topic("small story", ["hackernews"], 50, 5),
    ]
    result = score_topics(topics)
    scores = {r["topic"]: r["trend_score"] for r in result}
    assert scores["big story"] > scores["small story"]
    assert scores["big story"] != scores["small story"]


def test_missing_hn_is_zero_not_fabricated():
    # HN 멤버 없는 토픽은 hn=None, hn 기여 0 (헌법 III)
    topics = [_topic("only blog", ["anthropic"], 0, 0)]
    result = score_topics(topics)
    assert result[0]["hn"] is None
    # 단일 토픽 → minmax 스프레드 0 → score 0
    assert result[0]["trend_score"] == 0.0


def test_group_merges_same_url_and_similar_titles():
    items = [
        {"title": "GPT-5 released by OpenAI", "url": "https://a.com/x", "source": "openai",
         "category": "ai_labs", "metrics": None},
        {"title": "OpenAI released GPT-5", "url": "https://b.com/y", "source": "hackernews",
         "category": "hot_topics", "metrics": {"points": 500, "comments": 100}},
        {"title": "Totally unrelated kernel patch", "url": "https://c.com/z",
         "source": "github_trending", "category": "github_trending", "metrics": None},
    ]
    clusters = group_topics(items)
    # 유사 제목 2개는 한 토픽, 무관한 1개는 별도 → 2 클러스터
    assert len(clusters) == 2
    merged = max(clusters, key=lambda c: len(c["sources"]))
    assert merged["sources"] == {"openai", "hackernews"}
    assert merged["hn_points"] == 500


def test_compute_hot_topics_end_to_end():
    items = [
        {"title": "alpha topic", "url": "https://x.com/1", "source": "anthropic",
         "category": "ai_labs", "metrics": None},
        {"title": "beta story", "url": "https://y.com/2", "source": "hackernews",
         "category": "hot_topics", "metrics": {"points": 300, "comments": 50}},
    ]
    hot = compute_hot_topics(items)
    assert len(hot) == 2
    for h in hot:
        assert 0.0 <= h["trend_score"] <= 1.0
        assert h["src_count"] >= 1
