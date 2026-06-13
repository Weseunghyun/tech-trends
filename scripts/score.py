"""토픽 그룹핑 + 트렌드 점수 — research R2.

실측 수치(교차 출현 수 + HN engagement)만으로 0~1 점수를 산출한다. 임의 부스트·
소스별 권위 가중치 없음(헌법 III). 데이터 결측 항은 정직하게 0으로 둔다.
"""

from __future__ import annotations

import math
import re

from scripts.config import COMMENT_RATIO, HOT_TOPICS_MAX, JACCARD, W_HN, W_SRC
from scripts.normalize import normalize_url

_STOP = {
    "the", "a", "an", "of", "to", "for", "and", "or", "in", "on", "with", "is", "are",
    "show", "hn", "ask", "how", "why", "new", "using", "use", "release", "released",
    "from", "by", "at", "as", "your", "you", "we", "our",
}


def topic_key(title: str) -> frozenset[str]:
    """제목 → 유의어 토큰 집합(stopword·짧은 토큰 제거)."""
    words = re.findall(r"[a-z0-9]+", title.lower())
    return frozenset(w for w in words if len(w) > 2 and w not in _STOP)


def _jaccard(a: frozenset[str], b: frozenset[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def group_topics(items: list[dict]) -> list[dict]:
    """그리디 단일 패스 클러스터링(O(n²), 일 수십~수백 항목이라 충분).

    제목 토큰셋 Jaccard ≥ JACCARD 이거나 정규화 URL 동일이면 같은 토픽.
    반환 토픽 dict: title, items, sources(set), hn_points, hn_comments.
    """
    clusters: list[dict] = []
    for it in items:
        key = topic_key(it["title"])
        norm = normalize_url(it["url"])
        placed = False
        for c in clusters:
            same_url = norm in c["_urls"]
            if same_url or _jaccard(key, c["_key"]) >= JACCARD:
                _add_to_cluster(c, it, key, norm)
                placed = True
                break
        if not placed:
            clusters.append(_new_cluster(it, key, norm))
    return clusters


def _new_cluster(it: dict, key: frozenset[str], norm: str) -> dict:
    c = {
        "title": it["title"],
        "items": [],
        "sources": set(),
        "hn_points": 0,
        "hn_comments": 0,
        "_key": key,
        "_urls": set(),
        "_top_eng": -1,
    }
    _add_to_cluster(c, it, key, norm)
    return c


def _add_to_cluster(c: dict, it: dict, key: frozenset[str], norm: str) -> None:
    c["items"].append(it)
    c["sources"].add(it["source"])
    c["_urls"].add(norm)
    c["_key"] = c["_key"] | key  # 토픽 키는 누적 합집합
    m = it.get("metrics") or {}
    pts = m.get("points") or 0
    cmts = m.get("comments") or 0
    if it["source"] == "hackernews":
        c["hn_points"] += pts
        c["hn_comments"] += cmts
    # 표시 제목 = 최고 engagement 멤버
    eng = pts + cmts
    if eng > c["_top_eng"]:
        c["_top_eng"] = eng
        c["title"] = it["title"]


def _minmax(values: list[float]) -> list[float]:
    if not values:
        return []
    lo, hi = min(values), max(values)
    if hi - lo < 1e-9:
        return [0.0 for _ in values]
    return [(v - lo) / (hi - lo) for v in values]


def score_topics(topics: list[dict], top_n: int = HOT_TOPICS_MAX) -> list[dict]:
    """토픽들에 트렌드 점수를 부여하고 내림차순 상위 top_n HotTopic 반환.

    norm_src_count·norm_hn_engagement(log1p+minmax)의 가중합. 실측만 사용.
    """
    if not topics:
        return []

    src_counts = [float(len(t["sources"])) for t in topics]
    hn_raw = [
        math.log1p(t["hn_points"]) + COMMENT_RATIO * math.log1p(t["hn_comments"]) for t in topics
    ]
    norm_src = _minmax(src_counts)
    norm_hn = _minmax(hn_raw)

    scored: list[dict] = []
    for t, ns, nh in zip(topics, norm_src, norm_hn, strict=True):
        score = W_SRC * ns + W_HN * nh
        hn = None
        if t["hn_points"] or t["hn_comments"]:
            hn = {"points": t["hn_points"], "comments": t["hn_comments"]}
        scored.append(
            {
                "topic": t["title"],
                "trend_score": round(score, 4),
                "src_count": len(t["sources"]),
                "hn": hn,
                "items": t["items"],
            }
        )

    scored.sort(key=lambda x: x["trend_score"], reverse=True)
    return scored[:top_n]


def compute_hot_topics(items: list[dict], top_n: int = HOT_TOPICS_MAX) -> list[dict]:
    """수집 항목 → 그룹핑 → 점수 → 상위 HotTopic[] (collect 통합용)."""
    return score_topics(group_topics(items), top_n)
