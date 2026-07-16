"use strict";

// Tech Trends 대시보드 — 동일 출처 fetch(FR-006), 외부 CDN/키 없음.
// 카테고리 4탭 + 핫토픽 + 주간 몰아보기, 전체 히스토리 페이징.
// 접근성: WAI-ARIA 탭 패턴(로빙 탭인덱스·화살표 탐색), 카드 제목은 h2, 상태는 role=status.
// 보안: 모든 텍스트는 textContent, href는 http(s) 허용목록(safeHref), CSP는 index.html.

var CATEGORY_LABELS = {
  hot_topics: "핫토픽/화두",
  ai_labs: "AI 랩 동향",
  github_trending: "GitHub Trending",
  codex: "OpenAI Codex",
  eng_blogs: "엔지니어링/기술 블로그",
  weekly: "주간 몰아보기",
};
var CONTENT_ORDER = ["hot_topics", "ai_labs", "github_trending", "codex", "eng_blogs", "weekly"];
var CONTENT_TABS = ["ai_labs", "github_trending", "codex", "eng_blogs"];
var WEEKLY_DAYS = 7;
var WEEKLY_MAX_TOPICS = 15;

var state = { dates: [], idx: 0, data: null, activeTab: "hot_topics" };
var cache = Object.create(null); // 세션 내 날짜별 스냅샷 메모 — 과거 파일은 불변(감사 E2)
var nav = { newer: null, older: null, label: null }; // 1회 생성 — 포커스 소실 방지(감사 A3)

function el(tag, cls, text) {
  var e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text != null) e.textContent = text;
  return e;
}

// 외부 데이터 URL은 http(s)만 허용 — javascript: 등 스킴 차단(상류 검증의 2차 방어선, 감사 S3)
function safeHref(url) {
  try {
    var u = new URL(String(url == null ? "" : url), window.location.href);
    if (u.protocol === "http:" || u.protocol === "https:") return u.href;
  } catch (e) { /* 무효 URL → 아래 폴백 */ }
  return "#";
}

function extLink(cls, text, url, lang) {
  var a = el("a", cls, text);
  a.href = safeHref(url);
  a.target = "_blank";
  a.rel = "noopener noreferrer";
  if (lang && lang !== "unknown") a.lang = lang; // 한국어 TTS의 영어 제목 오낭독 방지(WCAG 3.1.2)
  return a;
}

function metricsBadge(points, comments) {
  var b = el("span", "badge", "▲ " + (points || 0) + " · 💬 " + (comments || 0));
  b.setAttribute("aria-label", "HN 포인트 " + (points || 0) + ", 댓글 " + (comments || 0));
  return b;
}

function itemCard(item) {
  var card = el("div", "card");
  var h = el("h2", "card-title");
  h.appendChild(extLink("title", item.title || "(제목 없음)", item.url, item.lang));
  card.appendChild(h);
  if (item.summary_ko) card.appendChild(el("p", "summary", item.summary_ko));
  var row = el("div", "row");
  if (item.source) row.appendChild(el("span", "badge", item.source));
  if (item.metrics && (item.metrics.points || item.metrics.comments)) {
    row.appendChild(metricsBadge(item.metrics.points, item.metrics.comments));
  }
  if (item.published_at) row.appendChild(el("span", "badge", item.published_at.slice(0, 10)));
  card.appendChild(row);
  return card;
}

function hotTopicCard(topic, dateTags) {
  var card = el("div", "card");
  card.appendChild(el("h2", "card-title title", topic.topic || "(주제)"));
  var row = el("div", "row");
  var score = el("span", "badge score", "🔥 " + Number(topic.trend_score || 0).toFixed(2));
  score.setAttribute("aria-label", "화제도 점수 " + Number(topic.trend_score || 0).toFixed(2));
  row.appendChild(score);
  row.appendChild(el("span", "badge src", "소스 " + (topic.src_count || 0) + "곳"));
  if (topic.hn && (topic.hn.points || topic.hn.comments)) {
    row.appendChild(metricsBadge(topic.hn.points, topic.hn.comments));
  }
  (dateTags || []).forEach(function (d) {
    row.appendChild(el("span", "badge", d.slice(5))); // 주간 뷰: 등장일 MM-DD
  });
  card.appendChild(row);

  (topic.items || []).forEach(function (it) {
    var sub = el("div", "hot-item");
    var head = el("div", "hot-item-head");
    var label = it.title || hostnameOf(it.url); // URL 원문 노출 대신 도메인 축약(감사 D2)
    head.appendChild(extLink("hot-item-title", label, it.url, it.lang));
    // 교차탭 연결: 이 글이 어느 카테고리 탭에 있는지 표시
    var catLabel = CONTENT_TABS.indexOf(it.category) >= 0 ? CATEGORY_LABELS[it.category] : it.source;
    var tag = el("span", "hot-item-cat", catLabel);
    tag.title = "‘" + catLabel + "’ 탭의 글";
    head.appendChild(tag);
    sub.appendChild(head);
    if (it.summary_ko) sub.appendChild(el("p", "summary", it.summary_ko));
    card.appendChild(sub);
  });
  return card;
}

function hostnameOf(url) {
  try { return new URL(String(url)).hostname; } catch (e) { return "(링크)"; }
}

// ---------- 데이터 로드 (세션 캐시 + 신선도 구분) ----------

function fetchJSON(path, fresh) {
  // 신선도가 필요한 파일(index/latest/최신일)만 캐시버스팅 — 과거 날짜 파일은 불변이라
  // 브라우저 HTTP 캐시(GitHub Pages max-age=600)를 그대로 활용한다(감사 E2).
  var url = fresh ? path + "?v=" + Date.now() : path;
  return fetch(url, fresh ? { cache: "no-store" } : undefined).then(function (r) {
    if (!r.ok) throw new Error("HTTP " + r.status);
    return r.json();
  });
}

function loadData(dateStr) {
  if (cache[dateStr]) return Promise.resolve(cache[dateStr]);
  var isNewest = dateStr === state.dates[0]; // 최신일은 요약 주입으로 갱신될 수 있음
  return fetchJSON("data/" + dateStr + ".json", isNewest).then(function (data) {
    if (!isNewest) cache[dateStr] = data;
    return data;
  });
}

// ---------- 렌더 ----------

function panelsEl() { return document.getElementById("panels"); }

function renderError(message) {
  var panels = panelsEl();
  panels.textContent = "";
  panels.appendChild(el("p", "empty", message));
}

function renderPanel(key) {
  if (key === "weekly") { renderWeekly(); return; }
  var data = state.data;
  var panels = panelsEl();
  panels.textContent = "";
  if (!data) { panels.appendChild(el("p", "empty", "데이터 없음")); return; }
  var list = key === "hot_topics" ? (data.hot_topics || []) : ((data.categories || {})[key] || []);
  if (!list.length) { panels.appendChild(el("p", "empty", "항목 없음")); return; }
  list.forEach(function (entry) {
    panels.appendChild(key === "hot_topics" ? hotTopicCard(entry) : itemCard(entry));
  });
}

// 주간 몰아보기 — 최근 7일 스냅샷을 합산해 핫토픽 top을 한 화면에(며칠 쉬고 복귀하는 용도)
function renderWeekly() {
  var days = state.dates.slice(0, WEEKLY_DAYS);
  var panels = panelsEl();
  panels.textContent = "";
  panels.appendChild(el("p", "empty", "최근 " + days.length + "일 데이터를 모으는 중…"));

  Promise.all(days.map(function (d) {
    return loadData(d).then(
      function (data) { return { date: d, data: data }; },
      function () { return null; } // 하루 실패는 건너뜀(격리)
    );
  })).then(function (results) {
    if (state.activeTab !== "weekly") return; // 기다리는 동안 탭이 바뀌었으면 무시
    var byKey = Object.create(null);
    results.forEach(function (r) {
      if (!r) return;
      (r.data.hot_topics || []).forEach(function (t) {
        var key = (t.items && t.items[0] && t.items[0].id) || t.topic || "";
        if (!key) return;
        if (!byKey[key]) byKey[key] = { topic: t, dates: [] };
        if (Number(t.trend_score || 0) > Number(byKey[key].topic.trend_score || 0)) {
          byKey[key].topic = t; // 가장 뜨거웠던 날의 스냅샷을 대표로
        }
        byKey[key].dates.push(r.date);
      });
    });
    var merged = Object.keys(byKey).map(function (k) { return byKey[k]; });
    merged.sort(function (a, b) {
      return Number(b.topic.trend_score || 0) - Number(a.topic.trend_score || 0);
    });
    merged = merged.slice(0, WEEKLY_MAX_TOPICS);

    panels.textContent = "";
    if (!merged.length) { panels.appendChild(el("p", "empty", "항목 없음")); return; }
    panels.appendChild(el("p", "weekly-note",
      "최근 " + days.length + "일 핫토픽 합산 · 화제도순 상위 " + merged.length + "건"));
    merged.forEach(function (m) {
      panels.appendChild(hotTopicCard(m.topic, m.dates.sort()));
    });
  });
}

function countFor(key) {
  if (key === "weekly") return Math.min(WEEKLY_DAYS, state.dates.length) + "일";
  var data = state.data;
  if (!data) return "0";
  var n = key === "hot_topics"
    ? (data.hot_topics || []).length
    : ((data.categories || {})[key] || []).length;
  return String(n);
}

// ---------- 탭 (WAI-ARIA 탭 패턴: 1회 생성·로빙 탭인덱스·화살표 탐색) ----------

function buildTabs() {
  var tabs = document.getElementById("tabs");
  tabs.textContent = "";
  CONTENT_ORDER.forEach(function (key) {
    var btn = el("button", "tab");
    btn.id = "tab-" + key;
    btn.setAttribute("role", "tab");
    btn.setAttribute("aria-controls", "panels");
    btn.appendChild(document.createTextNode(CATEGORY_LABELS[key] || key));
    btn.appendChild(el("span", "count", ""));
    btn.addEventListener("click", function () { selectTab(key, false); });
    btn.addEventListener("keydown", onTabKeydown);
    tabs.appendChild(btn);
  });
  syncTabState();
}

function tabButtons() {
  return Array.prototype.slice.call(document.querySelectorAll("#tabs .tab"));
}

function syncTabState() {
  tabButtons().forEach(function (btn) {
    var selected = btn.id === "tab-" + state.activeTab;
    btn.setAttribute("aria-selected", selected ? "true" : "false");
    btn.tabIndex = selected ? 0 : -1;
  });
  panelsEl().setAttribute("aria-labelledby", "tab-" + state.activeTab);
}

function selectTab(key, focus) {
  state.activeTab = key;
  syncTabState();
  if (focus) document.getElementById("tab-" + key).focus();
  renderPanel(key);
}

function onTabKeydown(e) {
  var keys = { ArrowRight: 1, ArrowLeft: -1, Home: 0, End: 0 };
  if (!(e.key in keys)) return;
  e.preventDefault();
  var order = CONTENT_ORDER;
  var i = order.indexOf(state.activeTab);
  var next = e.key === "Home" ? 0
    : e.key === "End" ? order.length - 1
    : (i + keys[e.key] + order.length) % order.length;
  selectTab(order[next], true);
}

function updateTabCounts() {
  tabButtons().forEach(function (btn) {
    var key = btn.id.replace("tab-", "");
    btn.querySelector(".count").textContent = "(" + countFor(key) + ")";
  });
}

// ---------- 헤더·날짜 네비게이션 (1회 생성 — 포커스 유지) ----------

function buildDatenav() {
  var wrap = document.getElementById("datenav");
  wrap.textContent = "";
  nav.newer = el("button", "navbtn", "◀ 다음날");
  nav.newer.addEventListener("click", function () { go(state.idx - 1); });
  nav.label = el("span", "datelabel", "");
  nav.older = el("button", "navbtn", "이전날 ▶");
  nav.older.addEventListener("click", function () { go(state.idx + 1); });
  wrap.appendChild(nav.newer); wrap.appendChild(nav.label); wrap.appendChild(nav.older);
}

function renderHeader() {
  var data = state.data;
  var when = data.generated_at ? data.generated_at.replace("T", " ").slice(0, 16) : data.date || "";
  document.getElementById("freshness").textContent = "갱신: " + when + " (KST)";

  nav.newer.disabled = state.idx <= 0;
  nav.older.disabled = state.idx >= state.dates.length - 1;
  nav.label.textContent = (data.date || "") + "  (" + (state.idx + 1) + "/" + state.dates.length + ")";
  // 방금 누른 버튼이 끝에 닿아 비활성화되면 반대쪽으로 포커스 이동(키보드 연속 탐색 유지)
  if (document.activeElement === nav.newer && nav.newer.disabled) nav.older.focus();
  if (document.activeElement === nav.older && nav.older.disabled) nav.newer.focus();

  var meta = document.getElementById("meta-extra");
  meta.textContent = "";
  var failed = (data.sources || []).filter(function (s) { return !s.ok; });
  if (failed.length) {
    meta.appendChild(el("span", "src-fail",
      "수집 실패: " + failed.map(function (s) { return s.source; }).join(", ")));
  }
  if (data.summaries_injected === false) {
    meta.appendChild(el("span", "src-fail", "한글 요약 주입 전 — 원문 제목만 표시될 수 있음"));
  }
}

function go(idx) {
  if (idx < 0 || idx >= state.dates.length) return;
  state.idx = idx;
  var dateStr = state.dates[idx];
  loadData(dateStr).then(function (data) {
    state.data = data;
    renderHeader();
    updateTabCounts();
    renderPanel(state.activeTab);
  }).catch(function (err) {
    renderError(dateStr + " 데이터를 불러오지 못했습니다 (" + err.message + ").");
  });
}

// ---------- 초기화: index + latest 병렬 로드(직렬 2 RTT 제거, 감사 E3) ----------

function init() {
  var pIndex = fetchJSON("data/index.json", true).catch(function () { return null; });
  var pLatest = fetchJSON("data/latest.json", true).catch(function () { return null; });
  Promise.all([pIndex, pLatest]).then(function (res) {
    var idx = res[0], latest = res[1];
    if (idx && idx.dates && idx.dates.length) {
      state.dates = idx.dates.slice().sort().reverse(); // 최신순
    } else if (latest && latest.date) {
      state.dates = [latest.date]; // index 실패 → latest 단독 폴백
    } else {
      renderError("데이터를 불러오지 못했습니다.");
      return;
    }
    buildTabs();
    buildDatenav();
    if (latest && latest.date === state.dates[0]) cache[latest.date] = latest; // 재요청 절약
    go(0);
  });
}

// 동적 로드 시 DOMContentLoaded가 이미 지났을 수 있으므로 상태를 확인해 init 호출
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
