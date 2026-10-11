#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
data.json  ->  data.js

单个 HTML 用 file:// 直接打开时无法 fetch 本地 JSON（CORS），
所以构建期把同一份数据再产出一份 JS 变量。data.json 始终是唯一数据源。
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
SRC = ROOT / "data.json"
DST = ROOT / "data.js"


def main() -> int:
    raw = SRC.read_text(encoding="utf-8")
    data = json.loads(raw)

    # 基本健全性检查：宁可构建失败，也不要把脏数据发到页面
    cats = data.get("categories")
    if not isinstance(cats, list) or not cats:
        print("错误：data.json 里没有 categories", file=sys.stderr)
        return 1

    total = 0
    seen = {}
    for ci, cat in enumerate(cats):
        if not cat.get("name"):
            print(f"错误：第 {ci} 个分类缺少 name", file=sys.stderr)
            return 1
        if ci >= 10:
            print("错误：分类超过 10 个，盲文字母表 a-j 不够用", file=sys.stderr)
            return 1
        for p in cat.get("projects", []):
            total += 1
            name = p.get("name", "")
            if not name:
                print(f"错误：分类「{cat['name']}」下有项目缺少 name", file=sys.stderr)
                return 1
            if not (p.get("repo") or p.get("url")):
                print(f"警告：{name} 既没有 repo 也没有 url", file=sys.stderr)
            if name in seen:
                print(f"错误：项目重复出现：{name}", file=sys.stderr)
                return 1
            seen[name] = cat["name"]

    payload = json.dumps(data, ensure_ascii=False, indent=2)
    DST.write_text(
        "/* 由 build.py 从 data.json 生成，请勿手改。 */\n"
        "window.A11Y_DATA = " + payload + ";\n",
        encoding="utf-8",
    )
    print(f"OK  {len(cats)} 个分类 / {total} 个项目  ->  {DST.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
