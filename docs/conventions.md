<!-- Cladding · Tier C · derived from observed code · Refreshed by: clad init --scan -->

# Project conventions

_Mode: deterministic (no LLM polish). Re-run `clad scan` without `--no-llm` for prose._

## Observed style

| key | value |
|---|---|
| indent | four-space |
| quote | double |
| semicolon | mixed |
| naming (exports) | mixed |
| naming (constants) | mixed |
| docblock ratio | 0.58 |
| import order | unknown |
| export pattern | unknown |
| error handling | throw-primary |
| type def location | inline |
| test location | none |
| file header | (none) |

## Doc tag frequency

- `@param`: 0
- `@returns`: 0
- `@throws`: 0
- `@example`: 0
- `@see`: 0
- `@deprecated`: 0

## Representative modules

### scripts · scripts/collect.py

```
"""수집 오케스트레이션 진입점 — python -m scripts.collect.

흐름(2패스):
  1) `collect`          : 수집·검증·중복제거·점수 → 표시 항목 본문 fetch →
                          가벼운 latest.json + 요약용 summary_input.json(gitignore) 작성
  2) `collect --summaries S.json` : 재수집 없이 기존 당일 스냅샷에 한글 요약만 주입(가벼움)

시크릿·자격증명을 어떤 출력 경로로도 내보내지 않는다(SEC-01/02).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path

from scripts.config import (
    CONTENT_CATEGORIES,
    KST,
    PER_CATEGORY,
    RAW_SUMMARY_MAX,
    SOURCES,
    SUMMARY_MAX,
)
from scripts.dedup import filter_new_items, load_ledger, prune, save_ledger
from scripts.fetch_article import fetch_article_text
from scripts.normalize import clip, item_id, normalize_url, valid_url
from scripts.render import build_snapshot, prune_files, refresh_pointers, write_snapshot
from scripts.score import compute_hot_topics
from scripts.sources.hackernews import fetch_hn
from scripts.sources.rss import fetch_rss

SUMMARY_INPUT_NAME = "summary_input.json"

# 커밋되는 스냅샷에서 제외할 무거운/요약 입력 전용 필드(대시보드 불필요)
_HEAVY_FIELDS = ("raw_summary", "article_text")


def _dispatch(source: dict) -> list[dict]:
    """소스 kind에 맞는 어댑터 호출."""
    if source["kind"] == "rss":
        return fetch_rss(source)
    if source["kind"] == "hn":
        return fetch_hn(source)
    raise ValueError(f"unknown source kind: {source['kind']}")


def _finalize_item(raw: dict, collected_at: str) -> dict | None:
    """raw 항목을 검증·정규화해 TrendItem dict로. 부적합 시 None(폐기, FR-003/010)."""
    url = (raw.get("url") or "").strip()
    if not valid_url(url):
        return None
    title = clip(raw.get("title"))
    if not title:
        return None
    return {
        "id": item_id(url),
        "title": title,
        "url": normalize_url(url),
        "source": raw["source"],
        "category": raw["category"],
        "summary_ko": clip(raw.get("summary_ko"), SUMMARY_MAX),
        "raw_summary": clip(raw.get("raw_summary"), RAW_SUMMARY_MAX),
        "article_text": "",  # 표시 항목에 한해 이후 본문 fetch로 채움(요약 입력용)
        "lang": raw.get("lang") or "unknown",
        "published_at": raw.get("published_at"),
        "collected_at": collected_at,
        "metrics": raw.get("metrics"),
    }


def _lean(item: dict) -> dict:
    """커밋용 가벼운 item — 요약 입력 전용 필드 제거."""
    return {k: v for k, v in item.items() if k not in _HEAVY_FIELDS}


def _lean_snapshot(snapshot: dict) -> dict:
    """스냅샷의 모든 item(카테고리·핫토픽 근거)을 가볍게."""
```