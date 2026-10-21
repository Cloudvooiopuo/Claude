"""arc of light のチャンネルアイコン（800×800）とバナー（2560×1440）を作る。

使い方: python3 make_brand_images.py
- 背景は夜空の紺から紫へのグラデーション、やわらかい虹の弧（ぼかして光らせる）、星のきらめき
- 文字は Inter Display Light の小文字、字間を広めにしてやわらかく見せる
- バナーの文字と弧は、どの画面でも切れない中央の範囲（1546×423）に入れる
"""
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = Path(__file__).parent
FONT = "/usr/share/fonts/opentype/inter/InterDisplay-Light.otf"
FONT_THIN = "/usr/share/fonts/opentype/inter/InterDisplay-ExtraLight.otf"
TOP, BOTTOM = (14, 16, 48), (58, 34, 92)
RAINBOW = [(255, 170, 190), (255, 205, 160), (255, 240, 170), (170, 240, 205), (160, 205, 255), (200, 175, 255)]


def gradient(w, h):
    im = Image.new("RGB", (w, h))
    px = im.load()
    for y in range(h):
        t = y / (h - 1)
        c = tuple(int(TOP[i] + (BOTTOM[i] - TOP[i]) * t) for i in range(3))
        for x in range(w):
            px[x, y] = c
    return im


def arc(size, cx, cy, r, width):
    # 虹の弧：色ごとに少しずつ半径をずらして描き、ぼかして光らせる
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    band = width / len(RAINBOW)
    for i, c in enumerate(RAINBOW):
        rr = r - i * band
        d.arc([cx - rr, cy - rr, cx + rr, cy + rr], 180, 360, fill=c + (230,), width=max(2, int(band)))
    glow = layer.filter(ImageFilter.GaussianBlur(width * 0.9))
    soft = layer.filter(ImageFilter.GaussianBlur(width * 0.12))
    out = Image.new("RGBA", size, (0, 0, 0, 0))
    out.alpha_composite(glow)
    out.alpha_composite(glow)
    out.alpha_composite(soft)
    return out


def star(d, x, y, s, a):
    # 4つの先がとがった星
    pts = []
    for k in range(8):
        ang = math.pi / 4 * k - math.pi / 2
        rr = s if k % 2 == 0 else s * 0.22
        pts.append((x + rr * math.cos(ang), y + rr * math.sin(ang)))
    d.polygon(pts, fill=(255, 255, 255, a))


def sparkles(size, n, seed, big=4, region=None, avoid=None):
    rng = random.Random(seed)
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    w, h = size
    x0, y0, x1, y1 = region or (0, 0, w, h)
    for _ in range(n):
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        r = rng.choice([1, 1, 1.5, 2, 2.5])
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, rng.randint(90, 220)))
    placed = 0
    while placed < big:
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        if avoid and avoid[0] < x < avoid[2] and avoid[1] < y < avoid[3]:
            continue
        placed += 1
        star(d, x, y, rng.uniform(w * 0.008, w * 0.016), rng.randint(180, 240))
    glow = layer.filter(ImageFilter.GaussianBlur(2))
    out = Image.new("RGBA", size, (0, 0, 0, 0))
    out.alpha_composite(glow)
    out.alpha_composite(layer)
    return out


def text(im, s, font, cx, cy, spacing, fill=(255, 255, 255, 245)):
    # 字間を広げて1文字ずつ置き、ほんのり光らせる
    d = ImageDraw.Draw(im)
    widths = [d.textlength(ch, font=font) for ch in s]
    total = sum(widths) + spacing * (len(s) - 1)
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    x = cx - total / 2
    asc, desc = font.getmetrics()
    y = cy - (asc + desc) / 2
    for ch, wch in zip(s, widths):
        ld.text((x, y), ch, font=font, fill=fill)
        x += wch + spacing
    im.alpha_composite(layer.filter(ImageFilter.GaussianBlur(font.size * 0.12)))
    im.alpha_composite(layer)


def icon():
    w = h = 800
    im = gradient(w, h).convert("RGBA")
    im.alpha_composite(sparkles((w, h), 70, 3, big=5, avoid=(150, 520, 650, 650)))
    im.alpha_composite(arc((w, h), w / 2, h * 0.60, 250, 90))
    star(ImageDraw.Draw(im), w * 0.72, h * 0.30, 26, 250)
    text(im, "arc of light", ImageFont.truetype(FONT, 74), w / 2, h * 0.73, 6)
    im.convert("RGB").save(OUT / "icon_800.png")


def banner():
    w, h = 2560, 1440
    im = gradient(w, h).convert("RGBA")
    sx0, sy0 = (w - 1546) / 2, (h - 423) / 2
    im.alpha_composite(sparkles((w, h), 420, 7, big=14, avoid=(sx0 - 60, sy0 - 60, sx0 + 1606, sy0 + 483)))
    im.alpha_composite(arc((w, h), w / 2, sy0 + 330, 300, 70))
    text(im, "arc of light", ImageFont.truetype(FONT, 120), w / 2, sy0 + 265, 12)
    text(im, "pop  ·  chill  ·  ballad  ·  bgm", ImageFont.truetype(FONT_THIN, 40), w / 2, sy0 + 372, 10, fill=(235, 230, 255, 225))
    im.convert("RGB").save(OUT / "banner_2560x1440.png")
    # 確認用：スマホで見える中央の範囲を枠で示した版
    chk = im.copy()
    ImageDraw.Draw(chk).rectangle([sx0, sy0, sx0 + 1546, sy0 + 423], outline=(255, 80, 80, 255), width=4)
    chk.convert("RGB").resize((1280, 720)).save(OUT / "banner_safe_area_check.png")


if __name__ == "__main__":
    icon()
    banner()
    print("done")
