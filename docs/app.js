"use strict";

// Tech Trends 대시보드 — 동일 출처 fetch(FR-006), 외부 CDN/키 없음.
// 카테고리 4탭 + 핫토픽 1탭, 최근 30일 히스토리 페이징.

var CATEGORY_LABELS = {
  ai_labs: "AI 랩 동향",
  github_trending: "GitHub Trending",
  codex: "OpenAI Codex",
  eng_blogs: "엔지니어링/기술 블로그",
  hot_topics: "핫토픽/화두",
};
var CONTENT_ORDER = ["hot_topics", "ai_labs", "github_trending", "codex", "eng_blogs"];
var CONTENT_TABS = ["ai_labs", "github_trending", "codex", "eng_blogs"];

var state = { dates: [], idx: 0, data: null, activeTab: "hot_topics" };

function el(tag, cls, text) {
  var e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text != null) e.textContent = text;
  return e;
}
function safe(s) { return String(s == null ? "" : s); }

function extLink(cls, text, url) {
  var a = el("a", cls, text);
  a.href = safe(url);
  a.target = "_blank";
  a.rel = "noopener noreferrer";
  return a;
}

function itemCard(item) {
  var card = el("div", "card");
  card.appendChild(extLink("title", item.title || "(제목 없음)", item.url));
  if (item.summary_ko) card.appendChild(el("p", "summary", item.summary_ko));
  var row = el("div", "row");
  if (item.source) row.appendChild(el("span", "badge", item.source));
  if (item.metrics && (item.metrics.points || item.metrics.comments)) {
    row.appendChild(el("span", "badge",
      "▲ " + (item.metrics.points || 0) + " · 💬 " + (item.metrics.comments || 0)));
  }
  if (item.published_at) row.appendChild(el("span", "badge", item.published_at.slice(0, 10)));
  card.appendChild(row);
  return card;
}

function hotTopicCard(topic) {
  var card = el("div", "card");
  card.appendChild(el("span", "title", topic.topic || "(주제)"));
  var row = el("div", "row");
  row.appendChild(el("span", "badge score", "🔥 " + Number(topic.trend_score || 0).toFixed(2)));
  row.appendChild(el("span", "badge src", "소스 " + (topic.src_count || 0) + "곳"));
  if (topic.hn && (topic.hn.points || topic.hn.comments)) {
    row.appendChild(el("span", "badge",
      "HN ▲" + (topic.hn.points || 0) + " 💬" + (topic.hn.comments || 0)));
  }
  card.appendChild(row);

  (topic.items || []).forEach(function (it) {
    var sub = el("div", "hot-item");
    var head = el("div", "hot-item-head");
    head.appendChild(extLink("hot-item-title", it.title || it.url, it.url));
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

function renderPanel(key) {
  var data = state.data;
  var panels = document.getElementById("panels");
  panels.innerHTML = "";
  var list = key === "hot_topics" ? (data.hot_topics || []) : ((data.categories || {})[key] || []);
  var render = key === "hot_topics" ? hotTopicCard : itemCard;
  if (!list.length) { panels.appendChild(el("p", "empty", "항목 없음")); return; }
  list.forEach(function (entry) { panels.appendChild(render(entry)); });
}

function countFor(key) {
  var data = state.data;
  return key === "hot_topics"
    ? (data.hot_topics || []).length
    : ((data.categories || {})[key] || []).length;
}

function buildTabs() {
  var tabs = document.getElementById("tabs");
  tabs.innerHTML = "";
  CONTENT_ORDER.forEach(function (key) {
    var btn = el("button", "tab");
    btn.setAttribute("role", "tab");
    btn.setAttribute("aria-selected", key === state.activeTab ? "true" : "false");
    btn.appendChild(document.createTextNode(CATEGORY_LABELS[key] || key));
    btn.appendChild(el("span", "count", "(" + countFor(key) + ")"));
    btn.addEventListener("click", function () {
      state.activeTab = key;
      var all = tabs.querySelectorAll(".tab");
      for (var i = 0; i < all.length; i++) all[i].setAttribute("aria-selected", "false");
      btn.setAttribute("aria-selected", "true");
      renderPanel(key);
    });
    tabs.appendChild(btn);
  });
  renderPanel(state.activeTab);
}

function renderHeader() {
  var data = state.data;
  var when = data.generated_at ? data.generated_at.replace("T", " ").slice(0, 16) : data.date || "";
  document.getElementById("freshness").textContent = "갱신: " + when + " (KST)";

  // 날짜 네비게이션(히스토리 페이징)
  var nav = document.getElementById("datenav");
  nav.innerHTML = "";
  var newer = el("button", "navbtn", "◀ 다음날");
  newer.disabled = state.idx <= 0;
  newer.addEventListener("click", function () { go(state.idx - 1); });
  var label = el("span", "datelabel",
    (data.date || "") + "  (" + (state.idx + 1) + "/" + state.dates.length + ")");
  var older = el("button", "navbtn", "이전날 ▶");
  older.disabled = state.idx >= state.dates.length - 1;
  older.addEventListener("click", function () { go(state.idx + 1); });
  nav.appendChild(newer); nav.appendChild(label); nav.appendChild(older);

  var meta = document.getElementById("meta-extra");
  meta.innerHTML = "";
  var failed = (data.sources || []).filter(function (s) { return !s.ok; });
  if (failed.length) {
    meta.appendChild(el("span", "src-fail",
      "수집 실패: " + failed.map(function (s) { return s.source; }).join(", ")));
  }
}

function go(idx) {
  if (idx < 0 || idx >= state.dates.length) return;
  state.idx = idx;
  loadDate(state.dates[idx]);
}

function loadDate(dateStr) {
  fetch("data/" + dateStr + ".json?v=" + Date.now(), { cache: "no-store" })
    .then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
    .then(function (data) {
      state.data = data;
      renderHeader();
      buildTabs();
    })
    .catch(function (err) {
      document.getElementById("panels").innerHTML =
        "<p class='empty'>" + dateStr + " 데이터를 불러오지 못했습니다 (" + err.message + ").</p>";
    });
}

function init() {
  // 최근 날짜 목록(매니페스트) → 히스토리 페이징. 실패 시 latest.json 단독.
  fetch("data/index.json?v=" + Date.now(), { cache: "no-store" })
    .then(function (r) { if (!r.ok) throw new Error("no index"); return r.json(); })
    .then(function (idx) {
      var dates = (idx.dates || []).slice().sort().reverse(); // 최신순
      if (!dates.length) throw new Error("empty");
      state.dates = dates;
      state.idx = 0;
      loadDate(dates[0]);
    })
    .catch(function () {
      fetch("data/latest.json?v=" + Date.now(), { cache: "no-store" })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          state.dates = [data.date]; state.idx = 0; state.data = data;
          renderHeader(); buildTabs();
        })
        .catch(function (err) {
          document.getElementById("panels").innerHTML =
            "<p class='empty'>데이터를 불러오지 못했습니다 (" + err.message + ").</p>";
        });
    });
}

// 동적 로드 시 DOMContentLoaded가 이미 지났을 수 있으므로 상태를 확인해 init 호출
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
