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


def test_worked_example_r2():
    # R2: Claude(src3, 420/180) > Rust(src2, 950/240) > DeepMind(src1, 0/0)
    topics = [
        _topic("Claude Opus tool use", ["anthropic", "hackernews", "github_trending"], 420, 180),
        _topic("new Rust web framework", ["github_trending", "hackernews"], 950, 240),
        _topic("DeepMind weather model", ["deepmind"], 0, 0),
    ]
    result = score_topics(topics)

    assert [r["topic"] for r in result] == [
        "Claude Opus tool use",
        "new Rust web framework",
        "DeepMind weather model",
    ]
    assert round(result[0]["trend_score"], 2) == 0.96
    assert round(result[1]["trend_score"], 2) == 0.70
    assert round(result[2]["trend_score"], 2) == 0.00
    # 내림차순
    scores = [r["trend_score"] for r in result]
    assert scores == sorted(scores, reverse=True)


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
