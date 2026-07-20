"use strict";

// Tech Trends 대시보드 v2 — 동일 출처 fetch(FR-006), 외부 CDN/키 없음.
// 카테고리 5탭 + 핫토픽 + 주간 몰아보기, 전체 히스토리 페이징.
// 훑기 도구: 검색(당일/전체 기간), 읽음 흐림(localStorage), 긴 요약 접기, 복귀 힌트.
// 접근성: WAI-ARIA 탭 패턴, 카드 제목 h2, 상태는 role=status. 보안: textContent·safeHref·CSP.
// 히트바 폭 등 동적 스타일은 CSSOM(style 프로퍼티)로만 — CSP style-src 'self' 유지.

var CATEGORY_LABELS = {
  hot_topics: "핫토픽/화두",
  ai_labs: "AI 랩 동향",
  community: "커뮤니티",
  github_trending: "GitHub Trending",
  codex: "OpenAI Codex",
  eng_blogs: "엔지니어링/기술 블로그",
  weekly: "주간 몰아보기",
};
var CONTENT_ORDER = [
  "hot_topics", "ai_labs", "community", "github_trending", "codex", "eng_blogs", "weekly",
];
var CONTENT_TABS = ["ai_labs", "community", "github_trending", "codex", "eng_blogs"];
var WEEKLY_DAYS = 7;
var WEEKLY_MAX_TOPICS = 15;
var SEARCH_MAX_RESULTS = 100;
var VISITED_MAX = 3000;

var state = { dates: [], idx: 0, data: null, activeTab: "hot_topics", query: "", searchAll: false };
var cache = Object.create(null); // 세션 내 날짜별 스냅샷 메모 — 과거 파일은 불변
var nav = { newer: null, older: null, label: null }; // 1회 생성 — 포커스 소실 방지

function el(tag, cls, text) {
  var e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text != null) e.textContent = text;
  return e;
}

// 외부 데이터 URL은 http(s)만 허용 — javascript: 등 스킴 차단(상류 검증의 2차 방어선)
function safeHref(url) {
  try {
    var u = new URL(String(url == null ? "" : url), window.location.href);
    if (u.protocol === "http:" || u.protocol === "https:") return u.href;
  } catch (e) { /* 무효 URL → 아래 폴백 */ }
  return "#";
}

function hostnameOf(url) {
  try { return new URL(String(url)).hostname; } catch (e) { return "(링크)"; }
}

// ---------- 읽음(방문) 기록 — localStorage ----------

var visited = (function () {
  try {
    var raw = JSON.parse(localStorage.getItem("tt_visited") || "[]");
    return new Set(Array.isArray(raw) ? raw : []);
  } catch (e) { return new Set(); }
})();

function saveVisited() {
  try {
    var arr = Array.from(visited);
    if (arr.length > VISITED_MAX) arr = arr.slice(arr.length - VISITED_MAX);
    localStorage.setItem("tt_visited", JSON.stringify(arr));
  } catch (e) { /* 사파리 프라이빗 모드 등 — 기록 실패는 무해 */ }
}

function markVisited(id, dimTarget) {
  if (!id) return;
  visited.add(id);
  saveVisited();
  if (dimTarget) dimTarget.classList.add("visited");
}

function extLink(cls, text, url, lang) {
  var a = el("a", cls, text);
  a.href = safeHref(url);
  a.target = "_blank";
  a.rel = "noopener noreferrer";
  if (lang && lang !== "unknown") a.lang = lang;
  return a;
}

function metricsBadge(points, comments) {
  var b = el("span", "badge", "▲ " + (points || 0) + " · 💬 " + (comments || 0));
  b.setAttribute("aria-label", "포인트 " + (points || 0) + ", 댓글 " + (comments || 0));
  return b;
}

// ---------- 카드 ----------

function summaryEl(text) {
  var p = el("p", "summary clamp", text);
  return p;
}

// 렌더 후 실측으로 잘린 요약에만 '더보기' 버튼 부착
function addExpanders(container) {
  var clamped = container.querySelectorAll(".summary.clamp");
  for (var i = 0; i < clamped.length; i++) {
    (function (p) {
      if (p.scrollHeight <= p.clientHeight + 4) { p.classList.remove("clamp"); return; }
      var btn = el("button", "morebtn", "더보기");
      btn.setAttribute("aria-expanded", "false");
      btn.addEventListener("click", function () {
        var expanded = p.classList.toggle("clamp") === false;
        btn.textContent = expanded ? "접기" : "더보기";
        btn.setAttribute("aria-expanded", expanded ? "true" : "false");
      });
      p.insertAdjacentElement("afterend", btn);
    })(clamped[i]);
  }
}

function itemCard(item, extraBadges) {
  var card = el("div", "card");
  if (item.id && visited.has(item.id)) card.classList.add("visited");
  var h = el("h2", "card-title");
  var a = extLink("title", item.title || "(제목 없음)", item.url, item.lang);
  a.addEventListener("click", function () { markVisited(item.id, card); });
  h.appendChild(a);
  card.appendChild(h);
  if (item.summary_ko) card.appendChild(summaryEl(item.summary_ko));
  var row = el("div", "row");
  if (item.source) row.appendChild(el("span", "badge", item.source));
  if (item.metrics && (item.metrics.points || item.metrics.comments)) {
    row.appendChild(metricsBadge(item.metrics.points, item.metrics.comments));
  }
  if (item.published_at) row.appendChild(el("span", "badge", item.published_at.slice(0, 10)));
  (extraBadges || []).forEach(function (b) { row.appendChild(b); });
  card.appendChild(row);
  return card;
}

function hotTopicCard(topic, dateTags) {
  var card = el("div", "card");

  // 히트바 — 화제도(0~1)를 폭으로. CSP-safe: style 프로퍼티만 사용.
  var score = Number(topic.trend_score || 0);
  var bar = el("div", "heatbar");
  var fill = el("span");
  fill.style.width = Math.max(4, Math.round(score * 100)) + "%";
  bar.appendChild(fill);
  bar.setAttribute("aria-hidden", "true");
  card.appendChild(bar);

  card.appendChild(el("h2", "card-title title", topic.topic || "(주제)"));
  var row = el("div", "row");
  var scoreBadge = el("span", "badge score", "🔥 " + score.toFixed(2));
  scoreBadge.setAttribute("aria-label", "화제도 점수 " + score.toFixed(2));
  row.appendChild(scoreBadge);
  row.appendChild(el("span", "badge src", "소스 " + (topic.src_count || 0) + "곳"));
  if (topic.hn && (topic.hn.points || topic.hn.comments)) {
    row.appendChild(metricsBadge(topic.hn.points, topic.hn.comments));
  }
  (dateTags || []).forEach(function (d) {
    row.appendChild(el("span", "badge", d.slice(5)));
  });
  card.appendChild(row);

  (topic.items || []).forEach(function (it) {
    var sub = el("div", "hot-item");
    if (it.id && visited.has(it.id)) sub.classList.add("visited");
    var head = el("div", "hot-item-head");
    var label = it.title || hostnameOf(it.url);
    var a = extLink("hot-item-title", label, it.url, it.lang);
    a.addEventListener("click", function () { markVisited(it.id, sub); });
    head.appendChild(a);
    var catLabel = CONTENT_TABS.indexOf(it.category) >= 0 ? CATEGORY_LABELS[it.category] : it.source;
    var tag = el("span", "hot-item-cat", catLabel);
    tag.title = "‘" + catLabel + "’ 탭의 글";
    head.appendChild(tag);
    sub.appendChild(head);
    if (it.summary_ko) sub.appendChild(summaryEl(it.summary_ko));
    card.appendChild(sub);
  });
  return card;
}

// ---------- 데이터 로드 (세션 캐시 + 신선도 구분) ----------

function fetchJSON(path, fresh) {
  var url = fresh ? path + "?v=" + Date.now() : path;
  return fetch(url, fresh ? { cache: "no-store" } : undefined).then(function (r) {
    if (!r.ok) throw new Error("HTTP " + r.status);
    return r.json();
  });
}

function loadData(dateStr) {
  if (cache[dateStr]) return Promise.resolve(cache[dateStr]);
  var isNewest = dateStr === state.dates[0];
  return fetchJSON("data/" + dateStr + ".json", isNewest).then(function (data) {
    if (!isNewest) cache[dateStr] = data;
    return data;
  });
}

// ---------- 검색 ----------

function matcher(query) {
  var q = query.trim().toLowerCase();
  if (!q) return null;
  return function (text) { return String(text || "").toLowerCase().indexOf(q) >= 0; };
}

function itemMatches(m, it) {
  return m(it.title) || m(it.summary_ko);
}

function topicMatches(m, t) {
  if (m(t.topic)) return true;
  return (t.items || []).some(function (it) { return itemMatches(m, it); });
}

// ---------- 렌더 ----------

function panelsEl() { return document.getElementById("panels"); }

function renderError(message) {
  var panels = panelsEl();
  panels.textContent = "";
  panels.appendChild(el("p", "empty", message));
}

function renderPanel(key) {
  if (state.searchAll && state.query.trim()) { renderSearchAll(); return; }
  if (key === "weekly") { renderWeekly(); return; }
  var data = state.data;
  var panels = panelsEl();
  panels.textContent = "";
  if (!data) { panels.appendChild(el("p", "empty", "데이터 없음")); return; }
  var m = matcher(state.query);
  var list = key === "hot_topics" ? (data.hot_topics || []) : ((data.categories || {})[key] || []);
  if (m) {
    list = key === "hot_topics"
      ? list.filter(function (t) { return topicMatches(m, t); })
      : list.filter(function (it) { return itemMatches(m, it); });
  }
  if (!list.length) {
    panels.appendChild(el("p", "empty", m ? "검색 결과 없음" : "항목 없음"));
    return;
  }
  list.forEach(function (entry) {
    panels.appendChild(key === "hot_topics" ? hotTopicCard(entry) : itemCard(entry));
  });
  addExpanders(panels);
}

// 전체 기간 검색 — 아카이브 전 날짜에서 제목·요약 매칭(항목 단위, 최신순)
function renderSearchAll() {
  var m = matcher(state.query);
  var panels = panelsEl();
  if (!m) { renderPanel(state.activeTab); return; }
  panels.textContent = "";
  panels.appendChild(el("p", "search-note", "전체 " + state.dates.length + "일에서 검색 중…"));

  var q = state.query;
  Promise.all(state.dates.map(function (d) {
    return loadData(d).then(
      function (data) { return { date: d, data: data }; },
      function () { return null; }
    );
  })).then(function (results) {
    if (!(state.searchAll && state.query === q)) return; // 조건이 바뀌었으면 무시
    var byId = Object.create(null);
    results.forEach(function (r) {
      if (!r) return;
      var buckets = [];
      var cats = r.data.categories || {};
      Object.keys(cats).forEach(function (c) { buckets.push(cats[c]); });
      (r.data.hot_topics || []).forEach(function (t) { buckets.push(t.items || []); });
      buckets.forEach(function (lst) {
        lst.forEach(function (it) {
          if (!it || !it.id || byId[it.id]) return; // 최신 날짜(정렬상 앞)가 우선
          if (itemMatches(m, it)) byId[it.id] = { item: it, date: r.date };
        });
      });
    });
    var hits = Object.keys(byId).map(function (k) { return byId[k]; });
    hits.sort(function (a, b) { return a.date < b.date ? 1 : -1; });
    var total = hits.length;
    hits = hits.slice(0, SEARCH_MAX_RESULTS);

    panels.textContent = "";
    if (!total) { panels.appendChild(el("p", "empty", "전체 기간에서 결과 없음")); return; }
    panels.appendChild(el("p", "search-note",
      "전체 " + state.dates.length + "일 · " + total + "건" +
      (total > SEARCH_MAX_RESULTS ? " (상위 " + SEARCH_MAX_RESULTS + "건 표시)" : "")));
    hits.forEach(function (h) {
      panels.appendChild(itemCard(h.item, [el("span", "badge", h.date)]));
    });
    addExpanders(panels);
  });
}

// 주간 몰아보기 — 최근 7일 핫토픽 합산(며칠 쉬고 복귀하는 용도)
function renderWeekly() {
  var days = state.dates.slice(0, WEEKLY_DAYS);
  var panels = panelsEl();
  panels.textContent = "";
  panels.appendChild(el("p", "empty", "최근 " + days.length + "일 데이터를 모으는 중…"));

  Promise.all(days.map(function (d) {
    return loadData(d).then(
      function (data) { return { date: d, data: data }; },
      function () { return null; }
    );
  })).then(function (results) {
    if (state.activeTab !== "weekly" || (state.searchAll && state.query.trim())) return;
    var byKey = Object.create(null);
    results.forEach(function (r) {
      if (!r) return;
      (r.data.hot_topics || []).forEach(function (t) {
        var key = (t.items && t.items[0] && t.items[0].id) || t.topic || "";
        if (!key) return;
        if (!byKey[key]) byKey[key] = { topic: t, dates: [] };
        if (Number(t.trend_score || 0) > Number(byKey[key].topic.trend_score || 0)) {
          byKey[key].topic = t;
        }
        byKey[key].dates.push(r.date);
      });
    });
    var m = matcher(state.query);
    var merged = Object.keys(byKey).map(function (k) { return byKey[k]; });
    if (m) merged = merged.filter(function (x) { return topicMatches(m, x.topic); });
    merged.sort(function (a, b) {
      return Number(b.topic.trend_score || 0) - Number(a.topic.trend_score || 0);
    });
    merged = merged.slice(0, WEEKLY_MAX_TOPICS);

    panels.textContent = "";
    if (!merged.length) {
      panels.appendChild(el("p", "empty", m ? "검색 결과 없음" : "항목 없음"));
      return;
    }
    panels.appendChild(el("p", "weekly-note",
      "최근 " + days.length + "일 핫토픽 합산 · 화제도순 상위 " + merged.length + "건"));
    merged.forEach(function (x) {
      panels.appendChild(hotTopicCard(x.topic, x.dates.sort()));
    });
    addExpanders(panels);
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

// ---------- 탭 (WAI-ARIA 탭 패턴) ----------

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

// ---------- 검색 UI 배선 ----------

function buildSearch() {
  var input = document.getElementById("search");
  var scope = document.getElementById("scopebtn");
  var timer = null;
  input.addEventListener("input", function () {
    if (timer) clearTimeout(timer);
    timer = setTimeout(function () {
      state.query = input.value;
      renderPanel(state.activeTab);
    }, 160);
  });
  scope.addEventListener("click", function () {
    state.searchAll = !state.searchAll;
    scope.setAttribute("aria-pressed", state.searchAll ? "true" : "false");
    renderPanel(state.activeTab);
    if (state.searchAll) input.focus();
  });
}

// ---------- 복귀 힌트 ----------

function buildCatchup() {
  var slot = document.getElementById("catchup-slot");
  var prev = null;
  try { prev = localStorage.getItem("tt_last_visit"); } catch (e) { /* 무시 */ }
  var missed = prev ? state.dates.filter(function (d) { return d > prev; }).length : 0;
  if (prev && missed >= 2) {
    var chip = el("button", "catchup",
      "마지막 방문(" + prev.slice(5) + ") 이후 " + missed + "일치 쌓임 — 주간 몰아보기 →");
    chip.addEventListener("click", function () {
      selectTab("weekly", true);
      slot.textContent = "";
    });
    slot.appendChild(chip);
  }
  try { localStorage.setItem("tt_last_visit", state.dates[0]); } catch (e) { /* 무시 */ }
}

// ---------- 헤더·날짜 네비게이션 ----------

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
  nav.label.textContent = "";
  nav.label.appendChild(document.createTextNode((data.date || "") + " "));
  nav.label.appendChild(el("span", "pos", "(" + (state.idx + 1) + "/" + state.dates.length + ")"));
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

// ---------- 초기화: index + latest 병렬 로드 ----------

function init() {
  var pIndex = fetchJSON("data/index.json", true).catch(function () { return null; });
  var pLatest = fetchJSON("data/latest.json", true).catch(function () { return null; });
  Promise.all([pIndex, pLatest]).then(function (res) {
    var idx = res[0], latest = res[1];
    if (idx && idx.dates && idx.dates.length) {
      state.dates = idx.dates.slice().sort().reverse(); // 최신순
    } else if (latest && latest.date) {
      state.dates = [latest.date];
    } else {
      renderError("데이터를 불러오지 못했습니다.");
      return;
    }
    buildTabs();
    buildDatenav();
    buildSearch();
    buildCatchup();
    if (latest && latest.date === state.dates[0]) cache[latest.date] = latest;
    go(0);
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
