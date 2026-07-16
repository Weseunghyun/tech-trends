"""기사 본문 추출 — 상세 한글 요약의 입력을 풍부하게 하기 위함.

RSS가 제목만 줄 때(예: Anthropic) 실제 페이지를 열어 본문/메타설명을 확보한다.
stdlib만 사용(의존성 추가 없음, YAGNI). SPA처럼 본문이 비면 메타 설명이라도 반환한다.
요약은 에이전트가 수행하므로 완벽한 추출이 아니어도 된다(노이즈는 에이전트가 무시).
실패는 호출측에서 격리한다(빈 문자열로 처리).
"""

from __future__ import annotations

import html
import re

from scripts.config import ARTICLE_MAX_BYTES, ARTICLE_TEXT_MAX
from scripts.http import get_bytes

_SCRIPT_STYLE = re.compile(r"<(script|style|noscript|svg|template)\b[^>]*>.*?</\1>", re.I | re.S)
_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")
_META_DESC = re.compile(
    r'<meta[^>]+(?:name|property)=["\'](?:description|og:description)["\'][^>]*'
    r'content=["\'](.*?)["\']',
    re.I | re.S,
)
_META_DESC_REV = re.compile(
    r'<meta[^>]+content=["\'](.*?)["\'][^>]*(?:name|property)=["\'](?:description|og:description)["\']',
    re.I | re.S,
)


def _meta_description(html_text: str) -> str:
    for rx in (_META_DESC, _META_DESC_REV):
        m = rx.search(html_text)
        if m:
            return _WS.sub(" ", html.unescape(m.group(1))).strip()
    return ""


def _body_text(html_text: str) -> str:
    cleaned = _SCRIPT_STYLE.sub(" ", html_text)
    cleaned = _TAG.sub(" ", cleaned)
    return _WS.sub(" ", html.unescape(cleaned)).strip()


def fetch_article_text(url: str) -> str:
    """기사 URL의 메타 설명 + 본문 텍스트를 합쳐 반환(컷). 실패/비HTML은 ""."""
    try:
        # 임의 외부 URL — 크기 상한을 더 엄격하게(SSRF·크기 통제는 http 계층이 담당)
        raw = get_bytes(url, max_bytes=ARTICLE_MAX_BYTES)
    except Exception:  # noqa: BLE001 — 본문 확보 실패는 격리(요약은 raw_summary로 폴백)
        return ""
    try:
        text = raw.decode("utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        return ""
    if "<html" not in text.lower() and "<meta" not in text.lower() and "<p" not in text.lower():
        return ""  # HTML로 보이지 않으면 포기
    meta = _meta_description(text)
    body = _body_text(text)
    combined = (meta + "\n\n" + body).strip() if meta else body
    return combined[:ARTICLE_TEXT_MAX]
