"""공통 HTTP — SEC-04 준수(verify=True 유지·timeout 명시·raise_for_status).

feedparser에는 URL이 아닌 bytes를 전달한다(feedparser 자체 fetch는 timeout/verify를
우회하므로 금지, research R4). 시크릿·URL 토큰을 출력 경로로 내보내지 않는다(SEC-01/02).
"""

from __future__ import annotations

from typing import Any

import requests

from scripts.config import HTTP_TIMEOUT, USER_AGENT

_SESSION = requests.Session()
_SESSION.headers.update({"User-Agent": USER_AGENT})


def get_bytes(url: str, timeout: int = HTTP_TIMEOUT) -> bytes:
    """URL 본문을 bytes로 반환. verify=True(기본 유지), raise_for_status() 후 2xx만 반환."""
    resp = _SESSION.get(url, timeout=timeout)  # verify=True 기본 — 절대 override 금지
    resp.raise_for_status()
    return resp.content


def get_json(url: str, timeout: int = HTTP_TIMEOUT) -> Any:
    """JSON 엔드포인트(HN Algolia 등)를 파싱해 반환."""
    resp = _SESSION.get(url, timeout=timeout)
    resp.raise_for_status()
    return resp.json()
