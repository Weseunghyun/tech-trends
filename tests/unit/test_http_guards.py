"""http 계층 보안 통제 단위 테스트 — SSRF 차단·리다이렉트 재검증·응답 크기 상한 (SEC-04).

네트워크 비의존: socket.getaddrinfo와 세션을 모킹한다.
"""

from __future__ import annotations

import socket

import pytest
from scripts import http as http_mod

# 호스트명 → 해석될 IP (테스트 전용 가짜 DNS)
_FAKE_DNS = {
    "public.example": "93.184.216.34",
    "evil-internal.example": "192.168.1.10",
    "metadata.example": "169.254.169.254",
    "localhost": "127.0.0.1",
}


def _fake_getaddrinfo(host, port, *args, **kwargs):
    ip = _FAKE_DNS.get(host, host)  # IP 리터럴은 그대로
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, port or 80))]


@pytest.fixture(autouse=True)
def _no_real_dns(monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", _fake_getaddrinfo)


class _FakeResponse:
    def __init__(self, status=200, headers=None, chunks=(b"ok",), url=""):
        self.status_code = status
        self.headers = headers or {}
        self._chunks = list(chunks)
        self.url = url
        self.closed = False

    def iter_content(self, chunk_size=65536):
        yield from self._chunks

    def raise_for_status(self):
        if self.status_code >= 400:
            raise http_mod.requests.HTTPError(f"HTTP {self.status_code}")

    def close(self):
        self.closed = True


class _FakeSession:
    """URL별 준비된 응답을 돌려주는 세션 스텁."""

    def __init__(self, responses: dict[str, _FakeResponse]):
        self._responses = responses
        self.calls: list[str] = []

    def get(self, url, **kwargs):
        self.calls.append(url)
        if url not in self._responses:
            raise AssertionError(f"unexpected fetch: {url}")
        return self._responses[url]


# --- assert_public_http_url -------------------------------------------------

@pytest.mark.parametrize("url", [
    "http://127.0.0.1/x",
    "http://localhost/x",
    "http://192.168.1.10/x",
    "http://10.0.0.5/x",
    "http://169.254.169.254/latest/meta-data/",
    "http://evil-internal.example/x",  # 공개처럼 보이는 호스트명이 사설 IP로 해석
    "http://metadata.example/x",
    "ftp://public.example/x",
    "javascript:alert(1)",
])
def test_non_public_or_non_http_blocked(url):
    with pytest.raises(ValueError):
        http_mod.assert_public_http_url(url)


def test_public_host_allowed():
    http_mod.assert_public_http_url("https://public.example/article")


# --- 리다이렉트 재검증 -------------------------------------------------------

def test_redirect_to_private_ip_blocked(monkeypatch):
    session = _FakeSession({
        "https://public.example/a": _FakeResponse(
            status=302, headers={"Location": "http://192.168.1.10/steal"}
        ),
    })
    monkeypatch.setattr(http_mod, "_SESSION", session)
    with pytest.raises(ValueError, match="non-public"):
        http_mod.get_bytes("https://public.example/a")


def test_redirect_to_public_followed(monkeypatch):
    session = _FakeSession({
        "https://public.example/a": _FakeResponse(
            status=301, headers={"Location": "https://public.example/b"}
        ),
        "https://public.example/b": _FakeResponse(chunks=(b"hello",)),
    })
    monkeypatch.setattr(http_mod, "_SESSION", session)
    assert http_mod.get_bytes("https://public.example/a") == b"hello"
    assert session.calls == ["https://public.example/a", "https://public.example/b"]


def test_too_many_redirects(monkeypatch):
    responses = {
        f"https://public.example/{i}": _FakeResponse(
            status=302, headers={"Location": f"https://public.example/{i + 1}"}
        )
        for i in range(http_mod.HTTP_MAX_REDIRECTS + 2)
    }
    session = _FakeSession(responses)
    monkeypatch.setattr(http_mod, "_SESSION", session)
    with pytest.raises(ValueError, match="too many redirects"):
        http_mod.get_bytes("https://public.example/0")


# --- 응답 크기 상한 -----------------------------------------------------------

def test_content_length_precheck(monkeypatch):
    session = _FakeSession({
        "https://public.example/big": _FakeResponse(headers={"Content-Length": "999999999"}),
    })
    monkeypatch.setattr(http_mod, "_SESSION", session)
    with pytest.raises(ValueError, match="too large"):
        http_mod.get_bytes("https://public.example/big", max_bytes=1024)


def test_streamed_body_capped(monkeypatch):
    # Content-Length 없이 무한/대용량 스트림 — 누적 컷이 막아야 함
    session = _FakeSession({
        "https://public.example/stream": _FakeResponse(chunks=[b"x" * 65536] * 50),
    })
    monkeypatch.setattr(http_mod, "_SESSION", session)
    with pytest.raises(ValueError, match="too large"):
        http_mod.get_bytes("https://public.example/stream", max_bytes=100_000)


def test_body_within_cap_ok(monkeypatch):
    session = _FakeSession({
        "https://public.example/ok": _FakeResponse(chunks=(b"a" * 10, b"b" * 10)),
    })
    monkeypatch.setattr(http_mod, "_SESSION", session)
    assert http_mod.get_bytes("https://public.example/ok", max_bytes=100) == b"a" * 10 + b"b" * 10
