"""제네릭 RSS/Atom 어댑터 — github_trending·ai_labs·codex 공통(T010~T012).

http.get_bytes로 받은 bytes를 feedparser에 전달한다(URL 직접 fetch 금지, R4).
요약(summary_ko)은 에이전트가 인라인으로 채우므로 여기서는 빈 문자열로 둔다(FR-004).
"""

from __future__ import annotations

import html
import re
import sys
from calendar import timegm
from datetime import datetime

import feedparser

from scripts.config import KST, RAW_SUMMARY_MAX
from scripts.http import get_bytes

_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(text: str) -> str:
    """피드 description의 HTML 태그 제거 + 엔티티 디코드 + 공백 정리(요약 입력용)."""
    if not text:
        return ""
    cleaned = html.unescape(_TAG_RE.sub(" ", text))
    return re.sub(r"\s+", " ", cleaned).strip()[:RAW_SUMMARY_MAX]


def _published_iso(entry: feedparser.FeedParserDict) -> str | None:
    """published_parsed(struct_time, UTC)를 KST ISO8601로. 없으면 None(추정 금지)."""
    st = entry.get("published_parsed") or entry.get("updated_parsed")
    if not st:
        return None
    try:
        dt = datetime.fromtimestamp(timegm(st), tz=KST)
        return dt.isoformat(timespec="seconds")
    except (ValueError, OverflowError, OSError):
        return None


def _lang_of(title: str) -> str:
    """제목에 한글이 있으면 ko, 아니면 en(대부분 영문 소스)."""
    return "ko" if any("가" <= ch <= "힣" for ch in title) else "en"


def fetch_rss(source: dict) -> list[dict]:
    """소스의 모든 피드 URL을 파싱해 raw 항목 리스트 반환.

    한 소스에 여러 url이 있으면 합친다. 개별 url 파싱 경고는 stderr에 타입만 남기고 계속.
    """
    items: list[dict] = []
    for url in source["urls"]:
        raw = get_bytes(url)
        parsed = feedparser.parse(raw)
        if parsed.bozo and not parsed.entries:
            # malformed + 항목 0 → 이 url은 건너뜀(SEC-02: 타입만)
            exc = getattr(parsed, "bozo_exception", None)
            print(
                f"  feed 경고: {source['id']} ({type(exc).__name__ if exc else 'bozo'})",
                file=sys.stderr,
            )
            continue
        for entry in parsed.entries:
            link = entry.get("link") or ""
            title = entry.get("title") or ""
            if not link or not title:
                continue
            raw_summary = _strip_html(entry.get("summary") or entry.get("description") or "")
            items.append(
                {
                    "title": title,
                    "url": link,
                    "source": source["id"],
                    "category": source["category"],
                    "summary_ko": "",
                    "raw_summary": raw_summary,
                    "lang": _lang_of(title),
                    "published_at": _published_iso(entry),
                    "metrics": None,
                }
            )
    return items
