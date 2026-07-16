"""공통 HTTP — SEC-04 준수(verify=True 유지·timeout 명시·raise_for_status).

임의 외부 URL(HN 제출 링크 등)을 fetch하는 유일한 관문이므로 목적지 통제를 여기서 강제한다:
① 공개 IP만 허용 — 사설/루프백/링크로컬/예약 대역 거부(SSRF, 로컬 실행 시 홈 LAN 보호)
② 리다이렉트 자동 추종 금지 — 홉마다 목적지를 재검증(302로 내부망 우회 차단)
③ 응답 크기 상한 — 스트리밍 누적 컷(무제한 다운로드로 인한 메모리 소진 방지)
검증은 연결 직전 getaddrinfo 기준이다(DNS rebinding TOCTOU는 위협 모델 밖 — 개인용
저가치 자산, requests 재해석 간 격차 수용).

feedparser에는 URL이 아닌 bytes를 전달한다(feedparser 자체 fetch는 timeout/verify를
우회하므로 금지, research R4). 시크릿·URL 토큰을 출력 경로로 내보내지 않는다(SEC-01/02).
"""

from __future__ import annotations

import ipaddress
import json
import socket
import time
from typing import Any
from urllib.parse import urljoin, urlsplit

import requests

from scripts.config import (
    HTTP_BACKOFF,
    HTTP_MAX_BYTES,
    HTTP_MAX_REDIRECTS,
    HTTP_RETRIES,
    HTTP_TIMEOUT,
    USER_AGENT,
)

_SESSION = requests.Session()
_SESSION.headers.update({"User-Agent": USER_AGENT})

# 재시도할 일시적 상태 코드(429 rate-limit, 5xx). 영구 오류(403/404)는 재시도 안 함.
_RETRY_STATUS = {429, 500, 502, 503, 504}
_REDIRECT_STATUS = {301, 302, 303, 307, 308}


def assert_public_http_url(url: str) -> None:
    """http(s) + 공개 IP 목적지만 허용. 위반 시 ValueError(SSRF 차단, SEC-04)."""
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https"):
        raise ValueError("non-http(s) URL blocked")
    host = parts.hostname
    if not host:
        raise ValueError("hostless URL blocked")
    port = parts.port or (443 if parts.scheme == "https" else 80)
    infos = socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
    if not infos:
        raise ValueError("unresolvable host blocked")
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if not ip.is_global:
            raise ValueError("non-public host blocked")


def _fetch_once(url: str, timeout: int) -> requests.Response:
    """단일 URL을 예의 있는 재시도(backoff)로 fetch. 우회 아님 — verify=True 유지.

    일시적 오류(타임아웃·연결오류·429/5xx)만 재시도한다. 403/404 등 영구 거부는 즉시 raise.
    3xx는 재검증을 위해 호출측(_get)이 처리하므로 그대로 반환한다.
    """
    for attempt in range(HTTP_RETRIES + 1):
        try:
            resp = _SESSION.get(  # verify=True 기본 — override 금지
                url, timeout=timeout, stream=True, allow_redirects=False
            )
            if resp.status_code in _RETRY_STATUS and attempt < HTTP_RETRIES:
                resp.close()
                time.sleep(HTTP_BACKOFF * (attempt + 1))
                continue
            if resp.status_code in _REDIRECT_STATUS:
                return resp
            resp.raise_for_status()
            return resp
        except (requests.Timeout, requests.ConnectionError):
            if attempt < HTTP_RETRIES:
                time.sleep(HTTP_BACKOFF * (attempt + 1))
                continue
            raise
    raise AssertionError("unreachable")  # 루프는 항상 return/raise로 끝남


def _get(url: str, timeout: int) -> requests.Response:
    """홉마다 목적지를 검증하며 리다이렉트를 따라간 최종 2xx 응답 반환."""
    current = url
    for _ in range(HTTP_MAX_REDIRECTS + 1):
        assert_public_http_url(current)
        resp = _fetch_once(current, timeout)
        if resp.status_code in _REDIRECT_STATUS:
            location = resp.headers.get("Location")
            resp.close()
            if not location:
                raise ValueError("redirect without Location")
            current = urljoin(current, location)
            continue
        return resp
    raise ValueError("too many redirects")


def _read_capped(resp: requests.Response, max_bytes: int) -> bytes:
    """응답 본문을 상한까지만 스트리밍으로 읽음. 초과 시 ValueError."""
    length = resp.headers.get("Content-Length", "")
    if length.isdigit() and int(length) > max_bytes:
        resp.close()
        raise ValueError("response too large")
    chunks: list[bytes] = []
    total = 0
    try:
        for chunk in resp.iter_content(chunk_size=65536):
            total += len(chunk)
            if total > max_bytes:
                raise ValueError("response too large")
            chunks.append(chunk)
    finally:
        resp.close()
    return b"".join(chunks)


def get_bytes(url: str, timeout: int = HTTP_TIMEOUT, max_bytes: int = HTTP_MAX_BYTES) -> bytes:
    """URL 본문을 bytes로 반환. 공개 IP 검증·홉별 재검증·크기 상한 적용."""
    return _read_capped(_get(url, timeout), max_bytes)


def get_json(url: str, timeout: int = HTTP_TIMEOUT, max_bytes: int = HTTP_MAX_BYTES) -> Any:
    """JSON 엔드포인트(HN Algolia 등)를 파싱해 반환(get_bytes와 동일 통제)."""
    return json.loads(get_bytes(url, timeout, max_bytes).decode("utf-8"))
