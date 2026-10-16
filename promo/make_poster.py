# -*- coding: utf-8 -*-
"""生成抖音竖版宣传海报 1080x1920：AI 背景图 + 中文文字层"""
import os
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))
BG = os.path.join(BASE, "Vertical_mobile_poster_backgro_2026-10-14T23-11-41.png")
OUT = os.path.join(BASE, "douyin_poster_1080x1920.png")

W, H = 1080, 1920
GOLD = (255, 199, 44)
RED = (218, 41, 28)
WHITE = (255, 255, 255)
GRAY = (198, 198, 204)

FB = "C:/Windows/Fonts/msyhbd.ttc"
FR = "C:/Windows/Fonts/msyh.ttc"


def f(path, size):
    return ImageFont.truetype(path, size)


def tw(d, s, font):
    return d.textbbox((0, 0), s, font=font)[2]


def center_text(d, y, s, font, fill):
    d.text(((W - tw(d, s, font)) / 2, y), s, font=font, fill=fill)


def rrect(d, box, r, fill=None, outline=None, width=2):
    d.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)


def wrap(d, s, font, max_w):
    lines, cur = [], ""
    for ch in s:
        if tw(d, cur + ch, font) > max_w and cur:
            lines.append(cur)
            cur = ch
        else:
            cur += ch
    if cur:
        lines.append(cur)
    return lines


# ---------- 背景 ----------
base = Image.open(BG).convert("RGB")
bw, bh = base.size
sc = max(W / bw, H / bh)
base = base.resize((int(bw * sc), int(bh * sc)), Image.LANCZOS)
nw, nh = base.size
base = base.crop(((nw - W) / 2, (nh - H) / 2 - 60, (nw - W) / 2 + W, (nh - H) / 2 - 60 + H))
base = Image.blend(base, Image.new("RGB", (W, H), (8, 8, 12)), 0.42)

# 上下渐变遮罩
grad = Image.new("L", (W, H), 0)
gd = ImageDraw.Draw(grad)
for y in range(760):
    gd.line([(0, y), (W, y)], fill=int(215 * (1 - y / 760) ** 1.3))
for y in range(1330, H):
    gd.line([(0, y), (W, y)], fill=int(245 * ((y - 1330) / (H - 1330)) ** 1.4))
base = Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), base, grad)

img = base.convert("RGBA")
d = ImageDraw.Draw(img)

# ---------- 顶部 ----------
f_tag, f_title, f_en, f_slogan = f(FR, 34), f(FB, 132), f(FR, 44), f(FB, 50)
tag = "AI 点餐神器 · 已对接麦当劳官方 MCP"
twt = tw(d, tag, f_tag)
rrect(d, (W / 2 - twt / 2 - 34, 148, W / 2 + twt / 2 + 34, 214), 33,
      fill=(255, 199, 44, 38), outline=(255, 199, 44, 210), width=2)
center_text(d, 159, tag, f_tag, (30, 22, 10))

center_text(d, 268, "麦门聪明点", f(FB, 132), GOLD)
center_text(d, 432, "M c S m a r t P i c k", f(FR, 42), (235, 235, 240))

# 标语
y = 520
for ln in wrap(d, "说一句目标 + 预算，AI 帮你算出最划算的那一份", f(FB, 50), W - 140):
    center_text(d, y, ln, f(FB, 50), WHITE)
    y += 72

# 副标语
center_text(d, y + 16, "取数交给官方 · 算账交给代码 · 结论讲人话", f(FR, 32), GRAY)

# ---------- 四档目标 ----------
goals = ["省钱吃饱", "增肌高蛋白", "低卡控糖", "解馋满足"]
codes = ["save", "protein", "lowcal", "crave"]
gy = 1180
cw, chh, gap = 232, 140, 24
x0 = (W - (cw * 2 + gap)) / 2
for i, (g, c) in enumerate(zip(goals, codes)):
    r, c_ = divmod(i, 2)
    bx = x0 + c_ * (cw + gap)
    by = gy + r * (chh + gap)
    rrect(d, (bx, by, bx + cw, by + chh), 26, fill=(24, 22, 26, 205), outline=(255, 199, 44, 120), width=2)
    d.text(((bx + cw / 2 - tw(d, g, f(FB, 40)) / 2), by + 30), g, font=f(FB, 40), fill=GOLD)
    d.text(((bx + cw / 2 - tw(d, c, f(FR, 26)) / 2), by + 86), c, font=f(FR, 26), fill=GRAY)

# ---------- 真实案例卡片 ----------
cy = 1544
rrect(d, (74, cy, W - 74, cy + 214), 30, fill=(16, 15, 18, 225), outline=(255, 199, 44, 90), width=2)
d.text((112, cy + 30), "实测 · 预算 ¥35", font=f(FR, 30), fill=GRAY)
d.text((112, cy + 76), "双层吉士堡 + 猪柳麦满分", font=f(FB, 42), fill=WHITE)
d.text((112, cy + 140), "原价 ¥32.00", font=f(FR, 32), fill=(150, 150, 158))
mid = 112 + tw(d, "原价 ¥32.00", f(FR, 32)) + 18
d.line([(mid, cy + 148), (mid + 96, cy + 148)], fill=(150, 150, 158), width=3)
d.text((mid + 116, cy + 116), "实付 ¥24.00", font=f(FB, 44), fill=GOLD)
d.text((112 + 0, cy + 0), "", font=f(FR, 20))
d.text((W - 112 - tw(d, "省 ¥8 · 蛋白 42g", f(FB, 34)), cy + 34), "省 ¥8 · 蛋白 42g", font=f(FB, 34), fill=RED)

# ---------- 底部 CTA ----------
cta = "GitHub 搜 McSmartPick · 点个 Star ★"
fcta = f(FB, 44)
twc = tw(d, cta, fcta)
rrect(d, (W / 2 - twc / 2 - 46, 1796, W / 2 + twc / 2 + 46, 1876), 40, fill=(218, 41, 28, 245))
center_text(d, 1810, cta, fcta, WHITE)

center_text(d, 1894, "参赛作品 · 非麦当劳官方产品 · 价格以官方实时结果为准", f(FR, 24), (140, 140, 148))

img.convert("RGB").save(OUT, quality=95)
print("saved:", OUT)
