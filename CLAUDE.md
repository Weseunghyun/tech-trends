# tech-trends Development Guidelines

Last updated: 2026-07-16 (감사 후 placeholder 제거·실제 구조 반영)

## Active Technologies

- Python 3.11+ (수집기), HTML5 + Vanilla JS/CSS (대시보드, 빌드 스텝·프레임워크·외부 CDN 없음)
- 런타임 의존성: `feedparser==6.0.11`, `requests==2.33.0` (LLM SDK 없음 — 요약은 에이전트 인라인)
- 개발 의존성: `requirements-dev.txt` (pytest·ruff·bandit·pip-audit, 정확 버전 핀)

## Project Structure

```text
scripts/          # 수집기 — config·http·normalize·dedup·score·render·fetch_article·collect, sources/(rss·hn)
docs/             # 정적 대시보드(index.html·app.js·styles.css) + data/(날짜별 JSON·latest·index)
state/            # 파이프라인 내부 상태(dedup 원장 seen_urls.json) — gitignore, 공개 배포 제외
tests/            # unit(normalize·dedup·score·http) + integration(수집 스모크·실패 격리·가드)
specs/            # SDD 산출물(001-rss-api-github), spec/ + spec.yaml — cladding SSoT
```

## Commands

```bash
source .venv/bin/activate
python -m scripts.collect --dry-run        # 네트워크 수집만(쓰기 없음)
python -m scripts.collect --out docs/data  # 실제 산출(1패스). --summaries <json>은 2패스 주입
pytest tests/ -q                           # 전체 테스트
ruff check scripts/ tests/                 # 린트(보안 S룰 포함)
bandit -r scripts/ -q                      # 보안 정적 분석
clad check                                 # cladding 게이트(드리프트·아키텍처·시크릿·테스트)
```

## Code Style

- Python: ruff 설정(pyproject.toml) 준수 — E·F·I·B·SIM·S. 모듈 docstring에 Why와 FR/SEC/research 역참조.
- 예외 로그는 `type(e).__name__`만(SEC-02). 결측은 빈 값 유지, 추정·보간 금지(헌법 III).
- JS: vanilla ES5 스타일(var·function), 모든 DOM 텍스트는 textContent 경유(el 헬퍼), href는 safeHref.

## 파이프라인 불변식 (감사 2026-07-16 반영)

- dedup 원장은 **last-seen** 의미론 — 피드에서 30일간 안 보인 URL만 만료. 원장 등록은 **표시된 항목만**.
- 산출물 쓰기는 원자적(tmp + os.replace). 일자 아카이브는 영구 보관(30일 삭제 없음).
- 외부 fetch는 `scripts/http.py` 단일 관문 — 공개 IP 검증·리다이렉트 홉별 재검증·크기 상한.
- 성공 소스 과반 미달이면 산출물 미갱신 + exit 1 (빈약 데이터 덮어쓰기 방지).

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->

## cladding

**Spec is SSoT** — `spec.yaml` is authoritative; code must satisfy its
`features[]` and `acceptance_criteria`. Run `clad check --strict` before commit.

**Persona separation** — planner writes spec, reviewer audits, developer
implements; whoever authors a unit must not sign off on it (anti-self-cert).

**Feature cycle — one at a time** — One feature end-to-end before the next:
author its shard (`acceptance_criteria` + `modules`) → implement → author tests
in a separate context → `clad done <featureId>` (sets `status: done` only when
`clad check --tier=pre-push --strict` is GREEN). Never author shards ahead of
their code, or hand-write `status: done`. See `docs/feature-cycle.md`.

**Hash-based IDs** — Never hand-author `F-NNN` filenames; use the `clad` CLI
(or `/cladding:init`). Model in `docs/spec-ids-multi-dev.md`.

**Drift detectors** — `clad check --strict` runs them all; don't suppress
findings — fix them or update spec. (알려진 예외: CONVENTION_DRIFT의
"file-header comment" 경고는 Python을 인식 못 하는 플러그인 0.8.1 오탐 —
docstring이 이미 충족하므로 dismiss가 정답.)
