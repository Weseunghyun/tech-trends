"""공통 HTTP — SEC-04 준수(verify=True 유지·timeout 명시·raise_for_status).

feedparser에는 URL이 아닌 bytes를 전달한다(feedparser 자체 fetch는 timeout/verify를
우회하므로 금지, research R4). 시크릿·URL 토큰을 출력 경로로 내보내지 않는다(SEC-01/02).
"""

from __future__ import annotations

import time
from typing import Any

import requests

from scripts.config import HTTP_BACKOFF, HTTP_RETRIES, HTTP_TIMEOUT, USER_AGENT

_SESSION = requests.Session()
_SESSION.headers.update({"User-Agent": USER_AGENT})

# 재시도할 일시적 상태 코드(429 rate-limit, 5xx). 영구 오류(403/404)는 재시도 안 함.
_RETRY_STATUS = {429, 500, 502, 503, 504}


def _get(url: str, timeout: int) -> requests.Response:
    """예의 있는 재시도(backoff) 후 2xx 응답 반환. 우회 아님 — verify=True 유지.

    일시적 오류(타임아웃·연결오류·429/5xx)만 재시도한다. 403/404 등 영구 거부는 즉시 raise.
    """
    last_exc: Exception | None = None
    for attempt in range(HTTP_RETRIES + 1):
        try:
            resp = _SESSION.get(url, timeout=timeout)  # verify=True 기본 — override 금지
            if resp.status_code in _RETRY_STATUS and attempt < HTTP_RETRIES:
                time.sleep(HTTP_BACKOFF * (attempt + 1))
                continue
            resp.raise_for_status()
            return resp
        except (requests.Timeout, requests.ConnectionError) as e:
            last_exc = e
            if attempt < HTTP_RETRIES:
                time.sleep(HTTP_BACKOFF * (attempt + 1))
                continue
            raise
    # 429/5xx로 재시도 소진 시: 마지막 응답으로 raise_for_status
    if last_exc:
        raise last_exc
    resp.raise_for_status()
    return resp


def get_bytes(url: str, timeout: int = HTTP_TIMEOUT) -> bytes:
    """URL 본문을 bytes로 반환. verify=True(기본 유지), raise_for_status() 후 2xx만 반환."""
    return _get(url, timeout).content


def get_json(url: str, timeout: int = HTTP_TIMEOUT) -> Any:
    """JSON 엔드포인트(HN Algolia 등)를 파싱해 반환."""
    return _get(url, timeout).json()
