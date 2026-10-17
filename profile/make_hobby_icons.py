"""趣味（カフェ・旅行・コスメ・料理・音楽・アート）を描いたアート風アイコンを作る。

使い方: python3 make_hobby_icons.py
4倍の大きさで描いてから縮めて、線をなめらかにする。
"""
import math
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).parent
S = 4
W = 1080 * S


def p(*v):
    return [x * S for x in v]


def coffee(d, cx, cy, r, c, steam):
    d.rounded_rectangle(p(cx - r, cy - r * .5, cx + r * .8, cy + r), radius=r * .25 * S, fill=c)
    d.arc(p(cx + r * .45, cy - r * .2, cx + r * 1.25, cy + r * .55), -90, 90, fill=c, width=int(r * .18 * S))
    for dx in (-.4, .1):
        x = cx + r * dx
        d.line([((x + r * .12 * math.sin(t / 3)) * S, (cy - r * .7 - t * r * .09) * S) for t in range(8)], fill=steam, width=int(r * .1 * S))


def lipstick(d, cx, cy, r, body, tip):
    d.rectangle(p(cx - r * .35, cy, cx + r * .35, cy + r * 1.1), fill=body)
    d.rectangle(p(cx - r * .25, cy - r * .45, cx + r * .25, cy), fill="#E9C46A")
    d.polygon(p(cx - r * .25, cy - r * .45, cx + r * .25, cy - r * .45, cx + r * .25, cy - r * 1.1, cx - r * .25, cy - r * .8), fill=tip)


def note(d, cx, cy, r, c):
    d.ellipse(p(cx - r * .9, cy + r * .4, cx - r * .1, cy + r * 1.0), fill=c)
    d.ellipse(p(cx + r * .3, cy + r * .2, cx + r * 1.1, cy + r * .8), fill=c)
    d.rectangle(p(cx - r * .25, cy - r * .9, cx - r * .1, cy + r * .7), fill=c)
    d.rectangle(p(cx + r * .95, cy - r * 1.1, cx + r * 1.1, cy + r * .5), fill=c)
    d.polygon(p(cx - r * .25, cy - r * .9, cx + r * 1.1, cy - r * 1.1, cx + r * 1.1, cy - r * .75, cx - r * .25, cy - r * .55), fill=c)


def plane(img, cx, cy, r, c):
    # 上向きの飛行機を別の層に描いて、斜めに回してから貼る
    n = int(r * 2.4 * S)
    layer = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    m, u = n / 2, r * S
    d.rounded_rectangle([m - u * .14, m - u, m + u * .14, m + u], radius=u * .14, fill=c)  # 胴体
    d.polygon([(m - u * .1, m - u * .15), (m - u, m + u * .25), (m - u, m + u * .4), (m + u, m + u * .4), (m + u, m + u * .25), (m + u * .1, m - u * .15)], fill=c)  # 主翼
    d.polygon([(m - u * .08, m + u * .65), (m - u * .42, m + u * .9), (m - u * .42, m + u), (m + u * .42, m + u), (m + u * .42, m + u * .9), (m + u * .08, m + u * .65)], fill=c)  # 尾翼
    layer = layer.rotate(-40, resample=Image.BICUBIC)
    img.paste(layer, (int(cx * S - n / 2), int(cy * S - n / 2)), layer)


def palette(d, cx, cy, r, c, dots):
    d.ellipse(p(cx - r, cy - r * .8, cx + r, cy + r * .8), fill=c)
    d.ellipse(p(cx + r * .2, cy + r * .15, cx + r * .6, cy + r * .5), fill="#00000000")
    for (dx, dy), col in zip([(-.5, -.3), (-.05, -.45), (.4, -.25), (-.55, .2)], dots):
        d.ellipse(p(cx + r * dx - r * .17, cy + r * dy - r * .17, cx + r * dx + r * .17, cy + r * dy + r * .17), fill=col)


def pan(d, cx, cy, r, c, egg):
    d.ellipse(p(cx - r, cy - r * .75, cx + r * .6, cy + r * .75), fill=c)
    d.rounded_rectangle(p(cx + r * .45, cy - r * .12, cx + r * 1.4, cy + r * .12), radius=int(r * .1 * S), fill=c)
    d.ellipse(p(cx - r * .6, cy - r * .45, cx + r * .2, cy + r * .4), fill="#FFFFFF")
    d.ellipse(p(cx - r * .35, cy - r * .2, cx - r * .02, cy + r * .12), fill=egg)


def blobs(d, cols):
    # マティスの切り絵のような、やわらかい形を背景に置く
    shapes = [(250, 260, 190), (830, 300, 150), (260, 840, 160), (820, 820, 200), (540, 540, 120)]
    for (x, y, r), col in zip(shapes, cols):
        pts = []
        for i in range(24):
            a = 2 * math.pi * i / 24
            rr = r * (1 + .18 * math.sin(3 * a + x) + .1 * math.cos(5 * a + y))
            pts += p(x + rr * math.cos(a), y + rr * math.sin(a))
        d.polygon(pts, fill=col)


def make(name, bg, blob_cols, ink, accent):
    img = Image.new("RGB", (W, W), bg)
    d = ImageDraw.Draw(img, "RGBA")
    blobs(d, blob_cols)
    coffee(d, 300, 300, 95, ink, ink)
    note(d, 780, 280, 85, ink)
    lipstick(d, 300, 790, 110, ink, accent)
    plane(img, 800, 780, 120, ink)
    palette(d, 540, 560, 120, "#FFFFFF", [accent, "#2A9D8F", "#E9C46A", "#264653"])
    pan(d, 540, 870, 80, ink, "#F4A261")
    img = img.resize((1080, 1080), Image.LANCZOS)
    img.save(OUT / name, quality=92)


DRAW = {
    "coffee": lambda img, d, x, y, r, ink, acc: coffee(d, x, y, r, ink, ink),
    "note": lambda img, d, x, y, r, ink, acc: note(d, x, y, r * .9, ink),
    "lipstick": lambda img, d, x, y, r, ink, acc: lipstick(d, x, y, r, ink, acc),
    "plane": lambda img, d, x, y, r, ink, acc: plane(img, x, y, r, ink),
    "palette": lambda img, d, x, y, r, ink, acc: palette(d, x, y, r, "#FFFFFF", [acc, "#2A9D8F", "#E9C46A", "#264653"]),
    "pan": lambda img, d, x, y, r, ink, acc: pan(d, x - r * .2, y, r * .8, ink, "#F4A261"),
}


def make_hero(name, hero, others, bg="#FBEFE3", ink="#264653", accent="#E63946",
              cols=("#F4A261cc", "#E76F51aa", "#E9C46Acc", "#2A9D8F99", "#F2CC8Fcc")):
    """A案の色で、SNSごとに主役の絵を1つ大きく真ん中に置く。"""
    img = Image.new("RGB", (W, W), bg)
    d = ImageDraw.Draw(img, "RGBA")
    blob = [(540, 520, 300)] + [(540 + 330 * math.cos(a), 540 + 330 * math.sin(a), 95) for a in [math.radians(v) for v in (-150, -30, 90)]]
    for (x, y, r), col in zip(blob, cols):
        pts = []
        for i in range(24):
            t = 2 * math.pi * i / 24
            rr = r * (1 + .15 * math.sin(3 * t + x) + .08 * math.cos(5 * t + y))
            pts += p(x + rr * math.cos(t), y + rr * math.sin(t))
        d.polygon(pts, fill=col)
    DRAW[hero](img, d, 540, 520, 190, ink, accent)
    for (x, y, _), o in zip(blob[1:], others):
        DRAW[o](img, d, x, y, 70, ink, accent)
    img = img.resize((1080, 1080), Image.LANCZOS)
    img.save(OUT / name, quality=92)


if __name__ == "__main__":
    make_hero("sns_icon_tiktok.jpg", "note", ["lipstick", "coffee", "plane"])
    make_hero("sns_icon_instagram.jpg", "lipstick", ["coffee", "note", "palette"])
    make_hero("sns_icon_threads.jpg", "coffee", ["pan", "note", "plane"])
    make_hero("sns_icon_youtube.jpg", "plane", ["palette", "coffee", "lipstick"])
    make("hobby_icon_a_warm.jpg", "#FBEFE3", ["#F4A261cc", "#E76F51aa", "#E9C46Acc", "#2A9D8F99", "#F2CC8Fcc"], "#264653", "#E63946")
    make("hobby_icon_b_pastel.jpg", "#F6F1FA", ["#CDB4DBcc", "#FFC8DDcc", "#BDE0FEcc", "#A2D2FFcc", "#FFAFCCcc"], "#3D315B", "#E5383B")
    make("hobby_icon_c_night.jpg", "#1D2D44", ["#3E5C76cc", "#748CABaa", "#F0EBD833", "#E0A45877", "#F4A26155"], "#F0EBD8", "#FF6B6B")
