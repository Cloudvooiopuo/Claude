"""arc of light のチャンネルアイコン（800×800）とバナー（2560×1440）を、夜の版と昼の版で作る。

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
# 昼の版：青空から、やわらかい桃色へ。文字は濃い紺で読みやすく
DAY_TOP, DAY_BOTTOM = (120, 196, 255), (255, 214, 226)
INK = (34, 40, 96, 250)
RAINBOW = [(255, 170, 190), (255, 205, 160), (255, 240, 170), (170, 240, 205), (160, 205, 255), (200, 175, 255)]


def blur(layer, radius):
    # 透明な所の黒がにじまないよう、色に不透明度を掛けてからぼかし、あとで割り戻す
    import numpy as np
    a = np.asarray(layer, dtype=np.float32) / 255
    pm = np.dstack([a[..., :3] * a[..., 3:4], a[..., 3:4]])
    pm_im = [Image.fromarray((pm[..., i] * 255).astype("uint8")).filter(ImageFilter.GaussianBlur(radius)) for i in range(4)]
    b = np.dstack([np.asarray(c, dtype=np.float32) / 255 for c in pm_im])
    alpha = b[..., 3:4]
    rgb = np.where(alpha > 1e-4, b[..., :3] / np.maximum(alpha, 1e-4), 0)
    out = np.dstack([np.clip(rgb, 0, 1), alpha]) * 255
    return Image.fromarray(out.astype("uint8"), "RGBA")


def gradient(w, h, top=TOP, bottom=BOTTOM):
    TOP_, BOTTOM_ = top, bottom
    im = Image.new("RGB", (w, h))
    px = im.load()
    for y in range(h):
        t = y / (h - 1)
        c = tuple(int(TOP_[i] + (BOTTOM_[i] - TOP_[i]) * t) for i in range(3))
        for x in range(w):
            px[x, y] = c
    return im


def arc(size, cx, cy, r, width, colors=None):
    # 虹の弧：色ごとに少しずつ半径をずらして描き、ぼかして光らせる
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    colors = colors or RAINBOW
    band = width / len(colors)
    for i, c in enumerate(colors):
        rr = r - i * band
        d.arc([cx - rr, cy - rr, cx + rr, cy + rr], 180, 360, fill=c + (230,), width=max(2, int(band)))
    glow = blur(layer, width * 0.9)
    soft = blur(layer, width * 0.12)
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
    glow = blur(layer, 2)
    out = Image.new("RGBA", size, (0, 0, 0, 0))
    out.alpha_composite(glow)
    out.alpha_composite(layer)
    return out


def text(im, s, font, cx, cy, spacing, fill=(255, 255, 255, 245), glow=True):
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
    if glow:
        im.alpha_composite(blur(layer, font.size * 0.12))
    im.alpha_composite(layer)


# 昼の版は虹ではなく「光の弧」：白から淡い金色の細い弧を、明るく光らせる
LIGHT_ARC = [(255, 255, 255), (255, 247, 220), (255, 232, 170)]


def flare(im, x, y, s):
    # 弧の先に置く光の粒（大きなきらめき＋やわらかい光の輪）
    layer = Image.new("RGBA", im.size, (255, 255, 255, 0))
    d = ImageDraw.Draw(layer)
    d.ellipse([x - s, y - s, x + s, y + s], fill=(255, 250, 225, 200))
    im.alpha_composite(blur(layer, s * 0.9))
    star(ImageDraw.Draw(im), x, y, s * 1.6, 255)


def clouds(size, seed, n, avoid=None):
    # ふんわりした白い雲（円を重ねてぼかす）
    rng = random.Random(seed)
    w, h = size
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    placed = 0
    while placed < n:
        cx, cy = rng.uniform(0, w), rng.uniform(h * 0.05, h * 0.95)
        if avoid and avoid[0] < cx < avoid[2] and avoid[1] < cy < avoid[3]:
            continue
        placed += 1
        s = rng.uniform(w * 0.04, w * 0.08)
        for _ in range(6):
            ox, oy, r = rng.uniform(-1.6, 1.6) * s, rng.uniform(-0.3, 0.3) * s, rng.uniform(0.5, 0.9) * s
            d.ellipse([cx + ox - r, cy + oy - r * 0.7, cx + ox + r, cy + oy + r * 0.7], fill=(255, 255, 255, 150))
    return blur(layer, w * 0.012)


def icon_day():
    w = h = 800
    im = gradient(w, h, DAY_TOP, DAY_BOTTOM).convert("RGBA")
    im.alpha_composite(clouds((w, h), 2, 4, avoid=(120, 180, 680, 680)))
    im.alpha_composite(sparkles((w, h), 40, 5, big=5, avoid=(150, 520, 650, 650)))
    im.alpha_composite(arc((w, h), w / 2, h * 0.60, 250, 22, LIGHT_ARC))
    im.alpha_composite(arc((w, h), w / 2, h * 0.60, 244, 8, [(255, 255, 255)]))
    flare(im, w / 2 + 250 * math.cos(math.radians(-50)), h * 0.60 + 250 * math.sin(math.radians(-50)), 22)
    text(im, "arc of light", ImageFont.truetype(FONT, 74), w / 2, h * 0.73, 6, fill=INK, glow=False)
    im.convert("RGB").save(OUT / "icon_day_800.png")


def banner_day():
    w, h = 2560, 1440
    im = gradient(w, h, DAY_TOP, DAY_BOTTOM).convert("RGBA")
    sx0, sy0 = (w - 1546) / 2, (h - 423) / 2
    im.alpha_composite(clouds((w, h), 9, 9, avoid=(sx0 - 100, sy0 - 80, sx0 + 1646, sy0 + 503)))
    im.alpha_composite(sparkles((w, h), 160, 11, big=12, avoid=(sx0 - 60, sy0 - 60, sx0 + 1606, sy0 + 483)))
    im.alpha_composite(arc((w, h), w / 2, sy0 + 330, 300, 24, LIGHT_ARC))
    im.alpha_composite(arc((w, h), w / 2, sy0 + 330, 294, 8, [(255, 255, 255)]))
    flare(im, w / 2 + 300 * math.cos(math.radians(-50)), sy0 + 330 + 300 * math.sin(math.radians(-50)), 26)
    text(im, "arc of light", ImageFont.truetype(FONT, 120), w / 2, sy0 + 265, 12, fill=INK, glow=False)
    text(im, "pop  ·  chill  ·  ballad  ·  bgm", ImageFont.truetype(FONT, 40), w / 2, sy0 + 372, 10, fill=(60, 64, 120, 230), glow=False)
    im.convert("RGB").save(OUT / "banner_day_2560x1440.png")
    chk = im.copy()
    ImageDraw.Draw(chk).rectangle([sx0, sy0, sx0 + 1546, sy0 + 423], outline=(255, 80, 80, 255), width=4)
    chk.convert("RGB").resize((1280, 720)).save(OUT / "banner_day_safe_area_check.png")


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


def all_old():
    icon()
    banner()
    icon_day()
    banner_day()
    print("done")


def photo_bg(path, w, h, bright=1.08, soften=0):
    # 写真を枠いっぱいに切り抜き、少し明るく、やわらかくする
    from PIL import ImageEnhance
    p = Image.open(path).convert("RGB")
    s = max(w / p.width, h / p.height)
    p = p.resize((int(p.width * s) + 1, int(p.height * s) + 1), Image.LANCZOS)
    x, y = (p.width - w) // 2, (p.height - h) // 2
    p = p.crop((x, y, x + w, y + h))
    p = ImageEnhance.Brightness(p).enhance(bright)
    p = ImageEnhance.Color(p).enhance(1.1)
    if soften:
        # ぼかして、写真の中の看板や文字を読めなくし、ロゴの文字を引き立てる
        p = p.filter(ImageFilter.GaussianBlur(soften))
    return p.convert("RGBA")


def veil(size, box, a=120):
    # 文字の後ろだけ白くかすませて読みやすくする
    layer = Image.new("RGBA", size, (255, 255, 255, 0))
    ImageDraw.Draw(layer).rounded_rectangle(box, radius=(box[3] - box[1]) / 2, fill=(255, 255, 255, a))
    return blur(layer, (box[3] - box[1]) * 0.18)


def plaza_icon():
    w = h = 800
    im = photo_bg(OUT / "plaza_1.jpg", w, h, soften=7)
    im.alpha_composite(veil((w, h), (90, 480, 710, 650), 200))
    im.alpha_composite(arc((w, h), w / 2, h * 0.70, 230, 20, LIGHT_ARC))
    im.alpha_composite(arc((w, h), w / 2, h * 0.70, 225, 7, [(255, 255, 255)]))
    flare(im, w / 2 + 230 * math.cos(math.radians(-50)), h * 0.70 + 230 * math.sin(math.radians(-50)), 20)
    text(im, "arc of light", ImageFont.truetype(FONT, 76), w / 2, h * 0.70, 6, fill=INK, glow=False)
    im.convert("RGB").save(OUT / "icon_plaza_800.png")


def plaza_banner():
    w, h = 2560, 1440
    im = photo_bg(OUT / "plaza_1.jpg", w, h, soften=14)
    sx0, sy0 = (w - 1546) / 2, (h - 423) / 2
    im.alpha_composite(veil((w, h), (sx0 + 260, sy0 + 175, sx0 + 1286, sy0 + 410), 205))
    im.alpha_composite(arc((w, h), w / 2, sy0 + 330, 300, 24, LIGHT_ARC))
    im.alpha_composite(arc((w, h), w / 2, sy0 + 330, 294, 8, [(255, 255, 255)]))
    flare(im, w / 2 + 300 * math.cos(math.radians(-50)), sy0 + 330 + 300 * math.sin(math.radians(-50)), 26)
    text(im, "arc of light", ImageFont.truetype(FONT, 120), w / 2, sy0 + 265, 12, fill=INK, glow=False)
    text(im, "pop  ·  chill  ·  ballad  ·  bgm", ImageFont.truetype(FONT, 40), w / 2, sy0 + 372, 10, fill=(60, 64, 120, 235), glow=False)
    im.convert("RGB").save(OUT / "banner_plaza_2560x1440.png")
    chk = im.copy()
    ImageDraw.Draw(chk).rectangle([sx0, sy0, sx0 + 1546, sy0 + 423], outline=(255, 80, 80, 255), width=4)
    chk.convert("RGB").resize((1280, 720)).save(OUT / "banner_plaza_safe_area_check.png")


def plaza():
    plaza_icon()
    plaza_banner()


def photo_version(name, photo, soften_icon, soften_banner, dark=True):
    # 写真の版（レコード店・ライブ・ネオンの街など）。暗い写真は白い文字、明るい写真は紺の文字
    ink = (255, 255, 255, 250) if dark else INK
    sub = (235, 232, 255, 235) if dark else (60, 64, 120, 235)
    vcol = (10, 12, 30) if dark else (255, 255, 255)

    def veil_c(size, box, a):
        layer = Image.new("RGBA", size, vcol + (0,))
        ImageDraw.Draw(layer).rounded_rectangle(box, radius=(box[3] - box[1]) / 2, fill=vcol + (a,))
        return blur(layer, (box[3] - box[1]) * 0.18)

    w = h = 800
    im = photo_bg(OUT / photo, w, h, bright=1.0 if dark else 1.08, soften=soften_icon)
    im.alpha_composite(veil_c((w, h), (90, 480, 710, 650), 150 if dark else 200))
    im.alpha_composite(arc((w, h), w / 2, h * 0.70, 230, 20, LIGHT_ARC))
    im.alpha_composite(arc((w, h), w / 2, h * 0.70, 225, 7, [(255, 255, 255)]))
    flare(im, w / 2 + 230 * math.cos(math.radians(-50)), h * 0.70 + 230 * math.sin(math.radians(-50)), 20)
    text(im, "arc of light", ImageFont.truetype(FONT, 76), w / 2, h * 0.70, 6, fill=ink, glow=dark)
    im.convert("RGB").save(OUT / f"icon_{name}_800.png")

    w, h = 2560, 1440
    im = photo_bg(OUT / photo, w, h, bright=1.0 if dark else 1.08, soften=soften_banner)
    sx0, sy0 = (w - 1546) / 2, (h - 423) / 2
    im.alpha_composite(veil_c((w, h), (sx0 + 260, sy0 + 175, sx0 + 1286, sy0 + 410), 150 if dark else 205))
    im.alpha_composite(arc((w, h), w / 2, sy0 + 330, 300, 24, LIGHT_ARC))
    im.alpha_composite(arc((w, h), w / 2, sy0 + 330, 294, 8, [(255, 255, 255)]))
    flare(im, w / 2 + 300 * math.cos(math.radians(-50)), sy0 + 330 + 300 * math.sin(math.radians(-50)), 26)
    text(im, "arc of light", ImageFont.truetype(FONT, 120), w / 2, sy0 + 265, 12, fill=ink, glow=dark)
    text(im, "pop  ·  chill  ·  ballad  ·  bgm", ImageFont.truetype(FONT, 40), w / 2, sy0 + 372, 10, fill=sub, glow=False)
    im.convert("RGB").save(OUT / f"banner_{name}_2560x1440.png")
    im.convert("RGB").resize((1280, 720)).save(OUT / f"preview_{name}.jpg")


if __name__ == "__main__":
    photo_version("records", "records_1.jpg", 4, 8)
    photo_version("live", "live_1.jpg", 3, 6)
    photo_version("neon", "neon_1.jpg", 14, 26)
