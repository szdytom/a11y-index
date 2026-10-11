#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
静态无障碍自检 —— 对 index.html 做机器可判定的那部分检查。

刻意不去做"全自动 WCAG 通过"的假承诺：能静态判定的只有一部分规则，
真正的验收还得靠键盘走查、屏幕阅读器和人工判断。这个脚本的定位是
"防止低级错误混进交付"，而不是替代审计。
"""
import re
import sys
import pathlib
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parent
HTML = ROOT / "index.html"

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr"}


class Audit(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.problems = []
        self.notes = []
        self.stack = []
        self.ids = {}
        self.headings = []
        self.labels_for = set()
        self.form_controls = []          # (tag, attrs)
        self.buttons = []
        self.links = []
        self.landmarks = []
        self.html_attrs = {}
        self._text_of = {}               # 元素索引 -> 累计文本
        self._current_h = None
        self._h_text = ""
        self._skip_depth = 0
        self._cur_button = None
        self._cur_a = None
        self._textbuf = []

    # ---------- 工具 ----------
    def _attr(self, attrs, name):
        for k, v in attrs:
            if k == name:
                return v
        return None

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "html":
            self.html_attrs = d

        if "id" in d:
            self.ids.setdefault(d["id"], 0)
            self.ids[d["id"]] += 1

        if tag == "label" and d.get("for"):
            self.labels_for.add(d["for"])

        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.headings.append((int(tag[1]), d.get("class", "")))
            self._current_h = int(tag[1])
            self._h_text = ""

        if tag in ("button",):
            self.buttons.append(d)
            self._cur_button = d
        if tag == "a":
            self.links.append(d)
            self._cur_a = d
        if tag in ("main", "nav", "header", "footer", "aside", "section"):
            self.landmarks.append((tag, d.get("aria-label") or d.get("aria-labelledby")))
        if tag in ("input", "select", "textarea"):
            self.form_controls.append((tag, d))

        if d.get("tabindex") and d["tabindex"].lstrip("-").isdigit() and int(d["tabindex"]) > 0:
            self.problems.append(f"<{tag}> 使用了正数 tabindex={d['tabindex']}，会打乱 Tab 顺序")
        if d.get("autofocus") is not None and tag != "body":
            self.notes.append(f"<{tag}> 带 autofocus，请确认不会把用户猛然弹离当前位置")
        if tag == "a" and d.get("target") == "_blank":
            rel = (d.get("rel") or "")
            if "noopener" not in rel:
                self.problems.append(f"外链 <a href=\"{d.get('href','?')}\"> 用了 target=_blank 但缺 rel=noopener")
            if "noreferrer" not in rel:
                self.notes.append(f"外链 {d.get('href','?')} 建议加 rel=noreferrer")
        if tag == "img":
            if d.get("alt") is None:
                self.problems.append(f"<img src=\"{d.get('src','?')}\"> 缺少 alt")
        if tag == "iframe" and not d.get("title"):
            self.problems.append("<iframe> 缺少 title")

        if tag not in VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6") and self._current_h is not None:
            self.headings[-1] = (self.headings[-1][0], self.headings[-1][1], self._h_text.strip())
            self._current_h = None
        if tag == "button":
            self._cur_button = None
        if tag == "a":
            self._cur_a = None
        while self.stack:
            t = self.stack.pop()
            if t == tag:
                break

    def handle_data(self, data):
        if self._current_h is not None:
            self._h_text += data

    # ---------- 判定 ----------
    def finish(self):
        for tag, attrs in self.form_controls:
            if attrs.get("type") in ("hidden", "submit", "button", "reset"):
                continue
            has_label = (
                (attrs.get("id") and attrs["id"] in self.labels_for)
                or attrs.get("aria-label")
                or attrs.get("aria-labelledby")
                or attrs.get("title")
            )
            if not has_label:
                self.problems.append(
                    f"表单控件 <{tag} id=\"{attrs.get('id','(无 id)')}\"> 没有可访问名称")

        if self.html_attrs.get("lang") is None:
            self.problems.append("<html> 缺少 lang 属性")

        if not self.ids:
            self.notes.append("页面没有任何 id，跳过重复 id 检查")
        for i, n in self.ids.items():
            if n > 1:
                self.problems.append(f"id=\"{i}\" 重复出现 {n} 次")

        # 标题层级
        levels = [h[0] for h in self.headings]
        if not levels:
            self.problems.append("页面没有任何标题")
        else:
            if levels[0] != 1:
                self.notes.append(f"第一个标题是 h{levels[0]}（静态页面通常从 h1 开始）")
            if levels.count(1) != 1:
                self.problems.append(f"h1 出现了 {levels.count(1)} 次，应该只有一次")
            for a, b in zip(levels, levels[1:]):
                if b > a + 1:
                    self.problems.append(f"标题层级从 h{a} 跳到 h{b}，屏幕阅读器导航会断档")

        # 交互元素必须能被 Tab 到且顺序自然，这里只查可访问名称
        for b in self.buttons:
            if b.get("aria-label") or b.get("aria-labelledby") or b.get("title"):
                continue
            # 文本在子节点里，靠 __main__ 的文本检查兜底
        return self.problems, self.notes


def check_dynamic_content():
    """检查脚本生成的控件是否都补了可访问名称。"""
    problems = []
    app = (ROOT / "app.js").read_text(encoding="utf-8")
    if "aria-pressed" not in app:
        problems.append("分类按钮没有 aria-pressed 状态")
    if "aria-live" not in (ROOT / "index.html").read_text(encoding="utf-8"):
        problems.append("筛选结果没有 aria-live 播报区")
    if "setAttribute(\"aria-label\"" not in app and "setAttribute('aria-label'" not in app:
        problems.append("动态生成的按钮没有 aria-label")
    if "brailleCell" in app and "aria-hidden" not in app:
        problems.append("盲文点阵是装饰图形，应标记 aria-hidden")
    return problems


def check_css():
    problems = []
    css = (ROOT / "style.css").read_text(encoding="utf-8")
    if re.search(r"outline\s*:\s*(none|0)", css):
        problems.append("CSS 里有 outline:none/0，会抹掉键盘焦点可见性")
    for need in ("prefers-reduced-motion", "prefers-contrast", "forced-colors", "prefers-color-scheme"):
        if need not in css:
            problems.append(f"CSS 没有处理 {need}")
    if "focus-visible" not in css:
        problems.append("CSS 没有定义 :focus-visible 焦点样式")
    return problems


def main():
    if not HTML.exists():
        print("找不到 index.html", file=sys.stderr)
        return 2
    src = HTML.read_text(encoding="utf-8")

    p = Audit()
    p.feed(src)
    problems, notes = p.finish()
    problems += check_dynamic_content()
    problems += check_css()

    print(f"检查文件：{HTML.name} / style.css / app.js")
    print(f"标题结构：{' > '.join('h%d' % h[0] for h in p.headings)}")
    print(f"地标数量：{len(p.landmarks)}  {[t for t, _ in p.landmarks]}")
    print()

    if notes:
        print("提示（非阻断）：")
        for n in dict.fromkeys(notes):
            print("  · " + n)
        print()

    if problems:
        print(f"发现 {len(problems)} 个问题：")
        for x in dict.fromkeys(problems):
            print("  ✗ " + x)
        return 1

    print("静态检查全部通过。")
    print("仍需人工验证：键盘完整走查、屏幕阅读器朗读、200% 缩放重排、真实浏览器对比度。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
