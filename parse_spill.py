# -*- coding: utf-8 -*-
"""从 web_fetch 截断的 spill 文件里尽量抽出 GitHub 仓库记录（原始 API 数据）。"""
import json, sys, pathlib

dec = json.JSONDecoder()

def load(path):
    txt = pathlib.Path(path).read_text(encoding="utf-8", errors="replace")
    out = []
    # 逐条扫描 '{"id":' 起点，容错解析；截断处自然失败即停止
    pos = 0
    while True:
        i = txt.find('{"id":', pos)
        if i < 0:
            break
        try:
            obj, end = dec.raw_decode(txt[i:])
        except Exception:
            pos = i + 6
            continue
        pos = i + end
        if not isinstance(obj, dict) or "full_name" not in obj:
            continue
        lic = obj.get("license") or {}
        out.append(dict(
            full_name=obj.get("full_name"),
            stars=obj.get("stargazers_count"),
            lang=obj.get("language"),
            license=(lic.get("spdx_id") if isinstance(lic, dict) else None),
            pushed=(obj.get("pushed_at") or "")[:10],
            archived=bool(obj.get("archived")),
            desc=(obj.get("description") or "").strip(),
            topics=obj.get("topics") or [],
            homepage=obj.get("homepage") or "",
        ))
    return out

allr, seen = [], set()
for f in sys.argv[1:]:
    got = load(f)
    print(f"  {pathlib.Path(f).name}: +{len(got)}")
    for r in got:
        if r["full_name"] not in seen:
            seen.add(r["full_name"]); allr.append(r)

allr.sort(key=lambda r: -(r["stars"] or 0))
print(f"\n共 {len(allr)} 个唯一仓库\n")
for r in allr:
    flag = " [归档]" if r["archived"] else ""
    print(f'{r["stars"]:>7}  {r["full_name"]:<48} {r["lang"] or "-":<11} {r["license"] or "-":<13} {r["pushed"]}{flag}')

pathlib.Path("github_raw.json").write_text(
    json.dumps(allr, ensure_ascii=False, indent=2), encoding="utf-8")
print("\n-> github_raw.json")
