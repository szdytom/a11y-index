# -*- coding: utf-8 -*-
"""校验本页配色方案的 WCAG 2.2 对比度。"""
def srgb(c):
    c = c/255.0
    return c/12.92 if c <= 0.04045 else ((c+0.055)/1.055)**2.4

def lum(hexstr):
    h = hexstr.lstrip('#')
    r,g,b = (int(h[i:i+2],16) for i in (0,2,4))
    return 0.2126*srgb(r) + 0.7152*srgb(g) + 0.0722*srgb(b)

def ratio(a,b):
    la,lb = lum(a), lum(b)
    hi,lo = max(la,lb), min(la,lb)
    return (hi+0.05)/(lo+0.05)

LIGHT = dict(paper='#FAF9F5', card='#FFFFFF', ink='#171B1D', graphite='#565D60',
             yellow='#E9A800', amber='#7A5900', green='#0F4F48',
             green_soft='#E2EDEA', line='#D9D6CC')
DARK  = dict(paper='#0E1113', card='#181D20', ink='#F1F0EB', graphite='#A8AFAF',
             yellow='#E9A800', amber='#F0BE4E', green='#6FD3C4',
             green_soft='#14201F', line='#333B3F')

def check(name, pal, pairs):
    print(f"\n=== {name} ===")
    worst = 99
    for fg, bg, need, label in pairs:
        r = ratio(pal[fg], pal[bg])
        ok = "PASS" if r >= need else "**FAIL**"
        worst = min(worst, r/need)
        print(f"  {ok:8} {r:5.2f}:1  (需 {need})  {label}")
    return worst

P = []
# 正文类：AA 正文 4.5，AAA 正文 7
P.append(('ink','paper',7,'正文 墨/纸'))
P.append(('ink','card',7,'正文 墨/卡'))
P.append(('graphite','paper',4.5,'次级文字 石墨/纸'))
P.append(('graphite','card',4.5,'次级文字 石墨/卡'))
P.append(('ink','yellow',4.5,'h1 强调 墨/盲道黄'))
P.append(('amber','paper',4.5,'eyebrow+图例 琥珀/纸'))
P.append(('amber','card',4.5,'卡片盲文点 琥珀/卡'))
P.append(('green','paper',4.5,'链接 墨绿/纸'))
P.append(('green','card',4.5,'链接 墨绿/卡'))
P.append(('green','green_soft',4.5,'方法区链接 墨绿/浅绿底'))
P.append(('ink','green_soft',7,'方法区正文 墨/浅绿底'))
P.append(('graphite','green_soft',4.5,'方法区次级 石墨/浅绿底'))
P.append(('paper','ink',4.5,'按钮/控制台头 纸/墨'))
P.append(('yellow','ink',3,'焦点环/装饰 黄/墨'))
P.append(('line','card',1.2,'卡片描边 线/卡'))  # 装饰性，仅记录

w1 = check("浅色", LIGHT, P)

D = []
D.append(('ink','paper',7,'正文 墨/纸'))
D.append(('ink','card',7,'正文 墨/卡'))
D.append(('graphite','paper',4.5,'次级文字/纸'))
D.append(('graphite','card',4.5,'次级文字/卡'))
D.append(('amber','paper',4.5,'eyebrow 琥珀/纸'))
D.append(('amber','card',4.5,'盲文点 琥珀/卡'))
D.append(('green','paper',4.5,'链接 亮绿/纸'))
D.append(('green','card',4.5,'链接 亮绿/卡'))
D.append(('ink','green_soft',4.5,'方法区正文/深绿底'))
D.append(('green','green_soft',3,'方法区链接/深绿底'))
D.append(('paper','yellow',4.5,'深色按钮 纸/黄'))
w2 = check("深色", DARK, D)

print("\n--- 结论 ---")
print("浅色最差余量 %.2fx，深色最差余量 %.2fx（>=1.00 表示全部达标）" % (w1, w2))
