"""URL 정규화·검증·항목 ID — research R3 / SEC-05.

정규화는 안전·멱등 변환만 적용한다(자원을 바꾸지 않음). 두 번 적용해도 같은 문자열이
나오므로 dedup 키로 안정적이다.
"""

from __future__ import annotations

import hashlib
import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from scripts.config import TITLE_MAX, URL_MAX

_URL_RE = re.compile(r"^https?://[^\s]{1,%d}$" % URL_MAX)

# 추적 파라미터 — 접두 일치
_TRACKING_PREFIXES = ("utm_",)
# 추적 파라미터 — 정확 일치
_TRACKING_EXACT = {
    "fbclid", "gclid", "gbraid", "wbraid", "msclkid", "mc_cid", "mc_eid",
    "igshid", "ref", "ref_src", "ref_url", "source", "cmpid", "spm",
    "yclid", "_hsenc", "_hsmi", "vero_id", "oly_enc_id", "oly_anon_id",
}


def valid_url(url: str) -> bool:
    """http(s) URL 형식·길이 검증(SEC-05)."""
    return bool(url) and bool(_URL_RE.match(url.strip()))


def normalize_url(raw: str) -> str:
    """안전·멱등 변환으로 URL 정규화(research R3).

    ① scheme 소문자 + http→https  ② host 소문자 + 선행 www. 제거(비기본 포트 보존)
    ③ 경로 끝 슬래시 제거(루트 제외)  ④ utm_/추적 파라미터 제거 후 나머지 정렬
    ⑤ fragment 보존(OpenAI Codex changelog 등은 fragment로 개별 항목을 구분 —
       제거하면 전 항목이 하나로 병합됨). 경로 대소문자·비추적 쿼리도 보존(자원 변경 방지).
    """
    parts = urlsplit(raw.strip())

    scheme = "https" if parts.scheme.lower() in ("http", "https", "") else parts.scheme.lower()

    host = parts.hostname.lower() if parts.hostname else ""
    if host.startswith("www."):
        host = host[4:]
    netloc = f"{host}:{parts.port}" if parts.port and parts.port not in (80, 443) else host

    path = parts.path
    if len(path) > 1 and path.endswith("/"):
        path = path.rstrip("/")

    kept = [
        (k, v)
        for (k, v) in parse_qsl(parts.query, keep_blank_values=True)
        if not (k.lower().startswith(_TRACKING_PREFIXES) or k.lower() in _TRACKING_EXACT)
    ]
    query = urlencode(sorted(kept))

    return urlunsplit((scheme, netloc, path, query, parts.fragment))


def item_id(url: str) -> str:
    """정규화 URL의 SHA-1 16진 — dedup·중복 제거 키(보안용 아님)."""
    return hashlib.sha1(
        normalize_url(url).encode("utf-8"), usedforsecurity=False
    ).hexdigest()


def clip(text: str | None, limit: int = TITLE_MAX) -> str:
    """문자열 trim + 길이 컷(SEC-05). None은 ""."""
    if not text:
        return ""
    t = text.strip()
    return t[:limit]
