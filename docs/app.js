"use strict";

// Tech Trends 대시보드 — data/latest.json을 동일 출처로 fetch해 렌더(FR-006).
// 외부 CDN/키/CORS 불필요. 카테고리 4탭 + 핫토픽 1탭.

var CATEGORY_LABELS = {
  ai_labs: "AI 랩 동향",
  github_trending: "GitHub Trending",
  codex: "OpenAI Codex",
  eng_blogs: "엔지니어링/기술 블로그",
  hot_topics: "핫토픽/화두",
};
var CONTENT_ORDER = ["hot_topics", "ai_labs", "github_trending", "codex", "eng_blogs"];

function el(tag, cls, text) {
  var e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text != null) e.textContent = text;
  return e;
}

function escapeAttr(s) {
  return String(s == null ? "" : s);
}

// 안전한 외부 링크 카드
function itemCard(item) {
  var card = el("div", "card");
  var a = el("a", "title", item.title || "(제목 없음)");
  a.href = escapeAttr(item.url);
  a.target = "_blank";
  a.rel = "noopener noreferrer";
  card.appendChild(a);

  if (item.summary_ko) {
    card.appendChild(el("p", "summary", item.summary_ko));
  }

  var row = el("div", "row");
  if (item.source) row.appendChild(el("span", "badge", item.source));
  if (item.metrics && (item.metrics.points || item.metrics.comments)) {
    row.appendChild(
      el("span", "badge", "▲ " + (item.metrics.points || 0) + " · 💬 " + (item.metrics.comments || 0))
    );
  }
  if (item.published_at) {
    row.appendChild(el("span", "badge", item.published_at.slice(0, 10)));
  }
  card.appendChild(row);
  return card;
}

function hotTopicCard(topic) {
  var card = el("div", "card");
  card.appendChild(el("span", "title", topic.topic || "(주제)"));

  var row = el("div", "row");
  row.appendChild(el("span", "badge score", "🔥 " + Number(topic.trend_score || 0).toFixed(2)));
  row.appendChild(el("span", "badge src", "소스 " + (topic.src_count || 0)));
  if (topic.hn && (topic.hn.points || topic.hn.comments)) {
    row.appendChild(el("span", "badge", "HN ▲" + (topic.hn.points || 0) + " 💬" + (topic.hn.comments || 0)));
  }
  card.appendChild(row);

  if (topic.items && topic.items.length) {
    // 연관 글: 제목(출처 링크) + 상세 한글 요약을 바로 펼쳐 보여준다
    topic.items.forEach(function (it) {
      var sub = el("div", "hot-item");
      var a = el("a", "hot-item-title", it.title || it.url);
      a.href = escapeAttr(it.url);
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      sub.appendChild(a);
      var src = el("span", "hot-item-src", " · " + (it.source || ""));
      sub.appendChild(src);
      if (it.summary_ko) {
        sub.appendChild(el("p", "summary", it.summary_ko));
      }
      card.appendChild(sub);
    });
  }
  return card;
}

function renderPanel(key, data) {
  var panels = document.getElementById("panels");
  panels.innerHTML = "";
  var list, render;
  if (key === "hot_topics") {
    list = data.hot_topics || [];
    render = hotTopicCard;
  } else {
    list = (data.categories && data.categories[key]) || [];
    render = itemCard;
  }
  if (!list.length) {
    panels.appendChild(el("p", "empty", "항목 없음"));
    return;
  }
  list.forEach(function (entry) {
    panels.appendChild(render(entry));
  });
}

function countFor(key, data) {
  if (key === "hot_topics") return (data.hot_topics || []).length;
  return ((data.categories && data.categories[key]) || []).length;
}

function buildTabs(data) {
  var tabs = document.getElementById("tabs");
  tabs.innerHTML = "";
  var first = true;
  CONTENT_ORDER.forEach(function (key) {
    var btn = el("button", "tab");
    btn.setAttribute("role", "tab");
    btn.setAttribute("aria-selected", first ? "true" : "false");
    btn.innerHTML = "";
    btn.appendChild(document.createTextNode(CATEGORY_LABELS[key] || key));
    var c = el("span", "count", "(" + countFor(key, data) + ")");
    btn.appendChild(c);
    btn.addEventListener("click", function () {
      var all = tabs.querySelectorAll(".tab");
      for (var i = 0; i < all.length; i++) all[i].setAttribute("aria-selected", "false");
      btn.setAttribute("aria-selected", "true");
      renderPanel(key, data);
    });
    tabs.appendChild(btn);
    if (first) {
      renderPanel(key, data);
      first = false;
    }
  });
}

function renderFreshness(data) {
  var f = document.getElementById("freshness");
  var when = data.generated_at ? data.generated_at.replace("T", " ").slice(0, 16) : data.date || "";
  f.textContent = "갱신: " + when + " (KST)";

  var failed = (data.sources || []).filter(function (s) { return !s.ok; });
  if (failed.length) {
    var span = el("span", "src-fail", " · 수집 실패: " + failed.map(function (s) { return s.source; }).join(", "));
    document.getElementById("meta").appendChild(span);
  }
}

function init() {
  // 상대 경로 + 캐시 버스팅(FR-012 신선도). project-pages 서브패스 호환.
  fetch("data/latest.json?v=" + Date.now(), { cache: "no-store" })
    .then(function (res) {
      if (!res.ok) throw new Error("HTTP " + res.status);
      return res.json();
    })
    .then(function (data) {
      document.getElementById("placeholder").remove();
      renderFreshness(data);
      buildTabs(data);
    })
    .catch(function (err) {
      var p = document.getElementById("placeholder");
      if (p) p.textContent = "데이터를 불러오지 못했습니다 (" + err.message + ").";
    });
}

document.addEventListener("DOMContentLoaded", init);
