/* ============================================================
   策展页交互层
   原则：只改渲染出来的 DOM，不动语义；状态一律走 aria-live。
   ============================================================ */
(function () {
  "use strict";

  var DATA = window.A11Y_DATA;
  if (!DATA) return;

  /* --- 六点制盲文字母表：分类标记用真实点字，不是装饰 --- */
  var BRAILLE = {
    a: [1],
    b: [1, 2],
    c: [1, 4],
    d: [1, 4, 5],
    e: [1, 5],
    f: [1, 2, 4],
    g: [1, 2, 4, 5],
    h: [1, 2, 5],
    i: [2, 4],
    j: [2, 4, 5]
  };

  var SNAPSHOT = new Date(DATA.generated + "T00:00:00");
  var NEW_DAYS = 30;
  var STALE_DAYS = 365;

  /* --- 小工具 --- */
  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }

  function brailleCell(letter) {
    var on = BRAILLE[letter] || [];
    var cell = el("span", "cell");
    cell.setAttribute("aria-hidden", "true");
    for (var i = 1; i <= 6; i++) {
      var d = el("i");
      if (on.indexOf(i) !== -1) d.setAttribute("data-on", "");
      cell.appendChild(d);
    }
    return cell;
  }

  function daysSince(iso) {
    if (!iso || iso === "?") return Infinity;
    var t = Date.parse(iso + "T00:00:00Z");
    if (isNaN(t)) return Infinity;
    return Math.round((SNAPSHOT - t) / 86400000);
  }

  function isNew(p) { return daysSince(p.pushed) <= NEW_DAYS; }
  function isStale(p) { return p.archived === true || daysSince(p.pushed) > STALE_DAYS; }

  function fmtStars(n) {
    if (typeof n !== "number") return "?";
    return n.toLocaleString("zh-CN");
  }

  function repoUrl(p) {
    return p.url || ("https://github.com/" + p.repo);
  }

  function label(p) {
    var s = [p.name];
    if (p.repo) s.push("（" + p.repo + "）");
    return s.join("");
  }

  /* --- 拍平数据，给每个项目挂上它所属的分类 --- */
  var ALL = [];
  var CATS = [];
  (DATA.categories || []).forEach(function (cat, ci) {
    var letter = String.fromCharCode(97 + (ci % 10));
    var c = {
      id: "cat-" + ci,
      letter: letter,
      name: cat.name,
      blurb: cat.blurb || "",
      count: 0
    };
    CATS.push(c);
    (cat.projects || []).forEach(function (p) {
      ALL.push(Object.assign({}, p, { cat: c }));
      c.count++;
    });
  });

  /* ============================================================
     1. 页头计数
     ============================================================ */
  var heroCount = document.getElementById("hero-count");
  if (heroCount) heroCount.textContent = String(ALL.length);

  /* ============================================================
     2. 环境信号台 — 读真实的系统无障碍偏好
     ============================================================ */
  (function console_() {
    var host = document.getElementById("sig");
    if (!host || !window.matchMedia) return;

    var input = "键盘 / 指针未使用";
    var rows = {};

    function row(key, name) {
      var r = el("div", "sig__row");
      var k = el("dt", "sig__k", name);
      var v = el("dd", "sig__v");
      var dot = el("span", "dot");
      v.appendChild(dot);
      var txt = el("span");
      v.appendChild(txt);
      r.appendChild(k); r.appendChild(v);
      host.appendChild(r);
      rows[key] = { dot: dot, txt: txt };
      return rows[key];
    }

    function set(key, on, text) {
      var r = rows[key];
      if (!r) return;
      r.dot.setAttribute("data-on", on ? "yes" : "no");
      r.txt.textContent = text;
    }

    function bind(query, cb) {
      if (!window.matchMedia) { cb(null); return; }
      var mq = window.matchMedia(query);
      var fire = function () { cb(mq.matches); };
      fire();
      // 新旧两种监听 API 都兼容
      if (mq.addEventListener) mq.addEventListener("change", fire);
      else if (mq.addListener) mq.addListener(fire);
    }

    row("scheme", "配色");
    row("motion", "动效");
    row("contrast", "对比度");
    row("forced", "强制颜色");
    row("pointer", "指针");
    row("modality", "当前输入");

    bind("(prefers-color-scheme: dark)", function (dark) {
      set("scheme", dark, dark ? "深色" : "浅色");
    });

    bind("(prefers-reduced-motion: reduce)", function (reduce) {
      set("motion", reduce, reduce ? "已减弱 · 过渡已关闭" : "标准 · 保留轻量过渡");
    });

    bind("(prefers-contrast: more)", function (more) {
      set("contrast", more, more ? "更高 · 边框与文字已加重" : "标准");
    });

    bind("(forced-colors: active)", function (fc) {
      set("forced", fc, fc ? "已启用 · 本页改用系统颜色" : "未启用");
    });

    bind("(pointer: coarse)", function (coarse) {
      set("pointer", coarse, coarse ? "触摸 · 目标已放大到 44px" : "鼠标 / 触控板");
    });

    function showInput() {
      var name = input.split(" ")[0];
      set("modality", name === "键盘", input);
    }
    showInput();

    document.addEventListener("keydown", function (e) {
      if (e.key === "Tab" || e.key === "Shift") {
        input = "键盘 · 焦点环已加粗";
        showInput();
      }
    }, true);

    ["pointerdown", "touchstart"].forEach(function (ev) {
      document.addEventListener(ev, function () {
        input = ev === "touchstart" ? "触摸" : "指针 / 鼠标";
        showInput();
      }, true);
    });
  })();

  /* ============================================================
     3. 侧栏图例
     ============================================================ */
  (function key_() {
    var list = document.getElementById("key-list");
    if (!list) return;
    CATS.forEach(function (c) {
      var li = el("li");
      li.appendChild(brailleCell(c.letter));
      li.appendChild(el("span", null, c.name));
      list.appendChild(li);
    });
  })();

  /* ============================================================
     4. 卡片渲染
     ============================================================ */
  function buildCard(p) {
    var li = el("li", "card");
    li.style.borderLeftColor = p.pick ? "var(--yellow)" : "var(--line)";

    var top = el("div", "card__top");
    var cellWrap = el("span", "card__cell");
    cellWrap.appendChild(brailleCell(p.cat.letter));
    top.appendChild(cellWrap);

    var h = el("h3", "card__h");
    var a = el("a", null, p.name);
    a.href = repoUrl(p);
    if (!p.repo) a.target = "_blank";
    if (p.repo) a.target = "_blank";
    a.rel = "noopener noreferrer";
    a.appendChild(el("span", "vh", " — 在新标签页打开" + (p.repo ? " GitHub 仓库" : "官网")));
    h.appendChild(a);
    top.appendChild(h);
    li.appendChild(top);

    if (p.desc) li.appendChild(el("p", "card__desc", p.desc));
    if (p.why) li.appendChild(el("p", "card__why", p.why));

    var meta = el("p", "card__meta");

    function bit(name, value) {
      var s = el("span");
      var b = el("b", null, value);
      s.appendChild(el("span", "vh", name + "："));
      s.appendChild(b);
      return s;
    }

    if (typeof p.stars === "number" && p.stars > 0) meta.appendChild(bit("星标", fmtStars(p.stars)));
    if (p.lang && p.lang !== "?") meta.appendChild(bit("语言", p.lang));
    if (p.license && p.license !== "?") meta.appendChild(bit("许可证", p.license));
    if (p.pushed && p.pushed !== "?") {
      var when = el("span");
      when.appendChild(el("span", "vh", "最近推送："));
      when.appendChild(el("b", null, p.pushed));
      meta.appendChild(when);
    }

    if (p.pick) {
      var rec = el("span", "tag tag--rec", "推荐");
      rec.appendChild(el("span", "vh", "—— 编辑部推荐"));
      meta.appendChild(rec);
    }
    if (isNew(p) && !isStale(p)) {
      var tag = el("span", "tag tag--new", "新");
      tag.appendChild(el("span", "vh", "—— 近 30 天内有推送"));
      meta.appendChild(tag);
    }
    if (isStale(p)) {
      var old = el("span", "tag tag--stale", "停更");
      old.appendChild(el("span", "vh", "—— 超过一年未推送或已归档"));
      meta.appendChild(old);
    }
    if (p.repo) {
      var r = el("span");
      r.appendChild(el("span", "vh", "仓库："));
      r.appendChild(document.createTextNode(p.repo));
      meta.appendChild(r);
    }
    if (p.url && p.repo) {
      var s2 = el("span");
      var u = el("a", null, "官网");
      u.href = p.url;
      u.target = "_blank";
      u.rel = "noopener noreferrer";
      u.appendChild(el("span", "vh", " — 在新标签页打开"));
      s2.appendChild(u);
      meta.appendChild(s2);
    }

    li.appendChild(meta);
    return li;
  }

  /* ============================================================
     5. 筛选 / 搜索 / 排序
     ============================================================ */
  var grid = document.getElementById("grid");
  var empty = document.getElementById("empty");
  var status = document.getElementById("status");
  var chipsHost = document.getElementById("chips");
  var qInput = document.getElementById("q");
  var sortSel = document.getElementById("sort");
  var resetBtn = document.getElementById("reset");
  var pickOnly = document.getElementById("pick-only");

  var active = new Set(CATS.map(function (c) { return c.id; }));

  function render() {
    if (!grid) return;

    var q = (qInput && qInput.value || "").trim().toLowerCase();
    var sort = sortSel ? sortSel.value : "stars";
    var onlyPicks = Boolean(pickOnly && pickOnly.checked);

    var shown = ALL.filter(function (p) {
      if (!active.has(p.cat.id)) return false;
      if (onlyPicks && !p.pick) return false;
      if (!q) return true;
      var hay = [p.name, p.repo, p.lang, p.license, p.desc, p.why, p.cat.name]
        .filter(Boolean).join(" ").toLowerCase();
      return hay.indexOf(q) !== -1;
    });

    shown.sort(function (a, b) {
      if (sort === "name") return String(a.name).localeCompare(String(b.name), "zh-Hans-CN");
      if (sort === "pushed") return String(b.pushed || "").localeCompare(String(a.pushed || ""));
      return (b.stars || 0) - (a.stars || 0);
    });

    grid.textContent = "";
    var frag = document.createDocumentFragment();
    shown.forEach(function (p) { frag.appendChild(buildCard(p)); });
    grid.appendChild(frag);

    if (empty) empty.hidden = shown.length !== 0;

    if (status) {
      status.textContent = "";
      var b = el("b", null, String(shown.length));
      status.appendChild(document.createTextNode("显示 "));
      status.appendChild(b);
      status.appendChild(document.createTextNode(
        " / " + ALL.length + " 个项目"
        + (active.size < CATS.length
            ? " · 已筛选 " + active.size + " 个分类"
            : " · 全部分类")
        + (onlyPicks ? " · 仅推荐" : "")
        + (q ? " · 搜索“" + q + "”" : "")
      ));
    }
  }

  function buildChips() {
    if (!chipsHost) return;

    function chip(id, name, count, letter) {
      var b = el("button", "chip");
      b.type = "button";
      b.setAttribute("aria-pressed", String(active.has(id)));
      if (letter) b.appendChild(brailleCell(letter));
      b.appendChild(el("span", null, name));
      b.appendChild(el("span", "chip__n", String(count)));
      b.setAttribute("aria-label",
        name + "，" + count + " 个项目" +
        (active.has(id) ? "，已选中，按下可取消筛选" : "，未选中，按下可筛选"));
      b.addEventListener("click", function () {
        if (active.has(id)) active.delete(id); else active.add(id);
        refreshChips();
        render();
      });
      return b;
    }

    function refreshChips() {
      Array.prototype.forEach.call(chipsHost.children, function (btn) {
        var id = btn.getAttribute("data-id");
        var on = active.has(id);
        btn.setAttribute("aria-pressed", String(on));
        var name = btn.getAttribute("data-name");
        var count = btn.getAttribute("data-count");
        btn.setAttribute("aria-label",
          name + "，" + count + " 个项目" +
          (on ? "，已选中，按下可取消筛选" : "，未选中，按下可筛选"));
      });
    }

    chipsHost.textContent = "";
    CATS.forEach(function (c) {
      var b = chip(c.id, c.name, c.count, c.letter);
      b.setAttribute("data-id", c.id);
      b.setAttribute("data-name", c.name);
      b.setAttribute("data-count", String(c.count));
      chipsHost.appendChild(b);
    });
  }

  if (chipsHost) buildChips();
  if (qInput) qInput.addEventListener("input", render);
  if (sortSel) sortSel.addEventListener("change", render);
  if (pickOnly) pickOnly.addEventListener("change", render);
  if (resetBtn) {
    resetBtn.addEventListener("click", function () {
      active = new Set(CATS.map(function (c) { return c.id; }));
      if (qInput) qInput.value = "";
      if (sortSel) sortSel.value = "stars";
      if (pickOnly) pickOnly.checked = false;
      if (chipsHost) buildChips();
      render();
      if (qInput) qInput.focus();
    });
  }

  render();
})();
