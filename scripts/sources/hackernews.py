"""Hacker News 어댑터 — Algolia 공개 JSON API(T013).

무키. points·num_comments를 metrics로 수집해 트렌드 점수(R2)의 근거로 쓴다.
외부 URL이 없는 텍스트 글(Ask HN 등)은 HN item URL을 폴백 키로 사용한다.
"""

from __future__ import annotations

from datetime import datetime

from scripts.config import KST
from scripts.http import get_json

_HN_ITEM = "https://news.ycombinator.com/item?id={}"


def _created_iso(hit: dict) -> str | None:
    ts = hit.get("created_at_i")
    if not ts:
        return None
    try:
        return datetime.fromtimestamp(int(ts), tz=KST).isoformat(timespec="seconds")
    except (ValueError, OverflowError, OSError):
        return None


def fetch_hn(source: dict) -> list[dict]:
    """front_page 검색 결과를 raw 항목으로 변환."""
    items: list[dict] = []
    for url in source["urls"]:
        data = get_json(url)
        for hit in data.get("hits", []):
            title = hit.get("title") or ""
            if not title:
                continue
            object_id = hit.get("objectID")
            link = hit.get("url") or (_HN_ITEM.format(object_id) if object_id else "")
            if not link:
                continue
            points = hit.get("points")
            comments = hit.get("num_comments")
            metrics = None
            if isinstance(points, int) or isinstance(comments, int):
                metrics = {
                    "points": points if isinstance(points, int) and points >= 0 else 0,
                    "comments": comments if isinstance(comments, int) and comments >= 0 else 0,
                }
            items.append(
                {
                    "title": title,
                    "url": link,
                    "source": source["id"],
                    "category": source["category"],
                    "summary_ko": "",
                    "raw_summary": "",  # HN은 본문 없음(토론 링크). 점수·제목으로 충분
                    "lang": "en",
                    "published_at": _created_iso(hit),
                    "metrics": metrics,
                }
            )
    return items
