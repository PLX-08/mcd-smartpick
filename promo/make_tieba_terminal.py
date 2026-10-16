# -*- coding: utf-8 -*-
"""贴吧配图 1200x900：终端窗口风格，展示 --demo 真实运行输出"""
import os
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "tieba_demo_terminal_1200x900.png")

W, H = 1200, 900
GOLD = (255, 199, 44)
RED = (235, 90, 80)
GREEN = (120, 220, 150)
WHITE = (240, 240, 245)
GRAY = (160, 168, 180)
DIM = (110, 118, 130)
BG = (11, 13, 16)
WIN = (13, 16, 20)
BAR = (24, 28, 34)

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
gd.ellipse((620, -320, 1420, 320), fill=(255, 199, 44, 18))
img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")
d = ImageDraw.Draw(img)

# ---------- 终端窗口 ----------
WX0, WY0, WX1, WY1 = 60, 56, 1140, 846
rrect(d, (WX0, WY0, WX1, WY1), 18, fill=WIN, outline=(60, 66, 76), width=2)

# 标题栏
rrect(d, (WX0, WY0, WX1, WY0 + 52), 18, fill=BAR)
d.rectangle((WX0, WY0 + 34, WX1, WY0 + 52), fill=BAR)
d.line([(WX0, WY0 + 52), (WX1, WY0 + 52)], fill=(52, 58, 68), width=1)

for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
    d.ellipse((WX0 + 24 + i * 26, WY0 + 21, WX0 + 38 + i * 26, WY0 + 35), fill=c)

d.text((WX0 + 118, WY0 + 16), "McSmartPick · 实测输出", font=f(FR, 20), fill=GRAY)

# 右上标签
lab = "python scripts/mcsmart.py --demo"
lw = tw(d, lab, f(FR, 19))
rrect(d, (WX1 - lw - 46, WY0 + 13, WX1 - 20, WY0 + 39), 13, fill=(38, 44, 52), outline=(70, 78, 90), width=1)
d.text((WX1 - lw - 33, WY0 + 17), lab, font=f(FR, 19), fill=GREEN)

# ---------- 内容 ----------
X = WX0 + 34
y = WY0 + 84
LH = 28

# (text, color, size, bold)
blocks = [
    [("【目标：省钱 ｜ 预算 ¥30】", GOLD, 22, True),
     ("  推荐搭配：麦香鸡 + 猪柳麦满分", WHITE, 22, False),
     ("  原价 ¥27.00，使用「全场9折」立减 ¥2.70", GRAY, 22, False),
     ("  👉 实付 ¥24.30，共省 ¥2.70（约 10%）", GOLD, 24, True),
     ("  营养参考：720.0 kcal ｜ 蛋白 34.0g ｜ 脂肪 38.0g ｜ 碳水 62.0g", DIM, 21, False)],
    [("【目标：增肌高蛋白 ｜ 预算 ¥35】", GOLD, 22, True),
     ("  推荐搭配：板烧鸡腿堡 + 猪柳麦满分", WHITE, 22, False),
     ("  原价 ¥35.00，使用「满30减8」立减 ¥8.00", GRAY, 22, False),
     ("  👉 实付 ¥27.00，共省 ¥8.00（约 23%）", GOLD, 24, True),
     ("  营养参考：750.0 kcal ｜ 蛋白 44.0g ｜ 脂肪 34.0g ｜ 碳水 68.0g", DIM, 21, False)],
    [("【目标：低卡控糖 ｜ 预算 ¥30】", GOLD, 22, True),
     ("  推荐搭配：田园脆鸡沙拉", WHITE, 22, False),
     ("  原价 ¥18.00，使用「全场9折」立减 ¥1.80", GRAY, 22, False),
     ("  👉 实付 ¥16.20，共省 ¥1.80（约 10%）", GOLD, 24, True),
     ("  营养参考：180.0 kcal ｜ 蛋白 12.0g ｜ 脂肪 8.0g ｜ 碳水 14.0g", DIM, 21, False)],
    [("【目标：解馋满足 ｜ 预算 ¥25】", GOLD, 22, True),
     ("  推荐搭配：薯条(大) + 苹果派 + 圆筒冰淇淋", WHITE, 22, False),
     ("  原价 ¥24.00，使用「甜品满15减5」立减 ¥5.00", GRAY, 22, False),
     ("  👉 实付 ¥19.00，共省 ¥5.00（约 21%）", GOLD, 24, True),
     ("  营养参考：900.0 kcal ｜ 蛋白 12.0g ｜ 脂肪 40.0g ｜ 碳水 124.0g", DIM, 21, False)],
]

d.text((X, y), "$ python scripts/mcsmart.py --demo", font=f(FB, 21), fill=GREEN)
y += LH + 10

for bi, blk in enumerate(blocks):
    for (t, c, sz, bd) in blk:
        d.text((X, y), t, font=f(FB if bd else FR, sz), fill=c)
        y += LH + (2 if sz == 24 else 0)
    y += 10

# ---------- 底部说明 ----------
note = "以上为真实运行输出，无需 Token 即可复现 · 价格与优惠以麦当劳官方实时结果为准"
d.text(((W - tw(d, note, f(FR, 21))) / 2, 866), note, font=f(FR, 21), fill=DIM)

img.save(OUT, quality=95)
print("saved:", OUT, "end_y:", y)
