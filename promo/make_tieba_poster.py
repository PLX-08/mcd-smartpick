# -*- coding: utf-8 -*-
"""贴吧宣传主海报 1200x900：深色底 + 麦当劳黄红，左栏卖点右栏实测案例"""
import os
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "tieba_poster_1200x900.png")

W, H = 1200, 900
GOLD = (255, 199, 44)
RED = (218, 41, 28)
WHITE = (255, 255, 255)
GRAY = (178, 178, 188)
DIM = (138, 138, 150)
CODE_DIM = (150, 150, 162)
BG = (14, 13, 17)
CARD = (26, 24, 30)

FB = "C:/Windows/Fonts/msyhbd.ttc"
FR = "C:/Windows/Fonts/msyh.ttc"


def f(p, s):
    return ImageFont.truetype(p, s)


def tw(d, s, font):
    return d.textbbox((0, 0), s, font=font)[2]


def rrect(d, box, r, fill=None, outline=None, width=2):
    d.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)


img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)

glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
gd = ImageDraw.Draw(glow)
gd.ellipse((-260, -300, 520, 300), fill=(255, 199, 44, 26))
gd.ellipse((760, 560, 1480, 1160), fill=(218, 41, 28, 20))
img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")
d = ImageDraw.Draw(img)

d.rectangle((0, 0, W, 5), fill=GOLD)

# ================= 左栏 =================
LX = 62

f_tag = f(FR, 26)
tag = "AI 点餐神器 · 已对接麦当劳官方 MCP"
twt = tw(d, tag, f_tag)
rrect(d, (LX, 46, LX + twt + 44, 96), 25, fill=(255, 199, 44, 40), outline=(255, 199, 44, 190), width=2)
d.text((LX + 22, 56), tag, font=f_tag, fill=GOLD)

d.text((LX - 4, 126), "麦门聪明点", font=f(FB, 96), fill=GOLD)
d.text((LX, 252), "M c S m a r t P i c k", font=f(FR, 34), fill=GRAY)

# 标语（手动两行，避免 wrap 把单字挤成一行）
d.text((LX, 306), "说一句目标 + 预算，", font=f(FB, 46), fill=WHITE)
d.text((LX, 366), "AI 帮你算出最划算的那一份", font=f(FB, 46), fill=WHITE)

d.text((LX, 428), "取数交给官方 · 算账交给代码 · 结论讲人话", font=f(FR, 28), fill=DIM)

# 四档目标 2x2
gy, cw, chh, gap = 486, 286, 58, 14
goals = [("省钱吃饱", "save"), ("增肌高蛋白", "protein"), ("低卡控糖", "lowcal"), ("解馋满足", "crave")]
for i, (g, c) in enumerate(goals):
    r, cc = divmod(i, 2)
    bx = LX + cc * (cw + gap)
    by = gy + r * (chh + gap)
    rrect(d, (bx, by, bx + cw, by + chh), 16, fill=CARD, outline=(255, 199, 44, 110), width=2)
    d.text((bx + 22, by + 12), g, font=f(FB, 29), fill=GOLD)
    d.text((bx + cw - tw(d, c, f(FR, 20)) - 20, by + 21), c, font=f(FR, 20), fill=CODE_DIM)

# 三个亮点（置于 CTA 上方，避免遮挡）
py = 636
feats = ["54 项测试全绿", "官方接口实跑留证", "零依赖 · 开源免费"]
fx = LX
for t in feats:
    d.ellipse((fx, py + 9, fx + 9, py + 18), fill=GOLD)
    d.text((fx + 20, py), t, font=f(FR, 25), fill=GRAY)
    fx += tw(d, t, f(FR, 25)) + 48

# ================= 右栏：实测案例卡 =================
RX, RW = 700, 438
rrect(d, (RX, 118, RX + RW, 640), 26, fill=CARD, outline=(255, 199, 44, 90), width=2)

d.text((RX + 30, 146), "实测 · 目标「省钱」· 预算 ¥30", font=f(FR, 25), fill=DIM)
d.text((RX + 30, 196), "麦香鸡 + 猪柳麦满分", font=f(FB, 44), fill=WHITE)
d.text((RX + 30, 258), "麦当劳菜单中的最优组合", font=f(FR, 24), fill=DIM)

d.text((RX + 30, 322), "原价 ¥27.00", font=f(FR, 34), fill=(150, 150, 160))
mx = RX + 30 + tw(d, "原价 ¥27.00", f(FR, 34)) + 16
d.line([(mx, 340), (mx + 104, 340)], fill=(150, 150, 160), width=3)

d.text((RX + 30, 434), "实付", font=f(FR, 28), fill=GRAY)
d.text((RX + 104, 380), "¥24.30", font=f(FB, 76), fill=GOLD)

d.line([(RX + 30, 500), (RX + RW - 30, 500)], fill=(70, 70, 80), width=1)
d.text((RX + 30, 524), "立减 ¥2.70", font=f(FB, 34), fill=RED)
d.text((RX + 30, 572), "营养参考：720 kcal ｜ 蛋白 34g", font=f(FR, 24), fill=DIM)
d.text((RX + 30, 606), "数据来自真实运行输出，非估算", font=f(FR, 21), fill=(105, 105, 118))

# ================= 底部 CTA =================
cta = "GitHub 搜  McSmartPick  ·  点个 Star 帮我冲榜"
fcta = f(FB, 40)
twc = tw(d, cta, fcta)
cx0 = (W - twc) / 2 - 52
rrect(d, (cx0, 690, cx0 + twc + 104, 774), 42, fill=RED)
d.text(((W - twc) / 2, 706), cta, font=fcta, fill=WHITE)

line1 = "麦当劳 1024 程序员节大赛 · 榜单按 GitHub Star 排名"
line2 = "参赛作品 · 非麦当劳官方产品 · 价格以官方实时结果为准"
d.text(((W - tw(d, line1, f(FR, 26))) / 2, 800), line1, font=f(FR, 26), fill=GRAY)
d.text(((W - tw(d, line2, f(FR, 22))) / 2, 846), line2, font=f(FR, 22), fill=(115, 115, 128))

img.save(OUT, quality=95)
print("saved:", OUT)
