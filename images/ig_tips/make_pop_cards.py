"""絵の入ったInstagram用の画像（1080x1350）を作る。色の背景に大きなイラスト（絵文字）をシールのように置き、
白いカードに見出しと手順（手順ごとに小さな絵）を載せる。

使い方: python3 make_pop_cards.py <pop.json> <出力フォルダ>
pop.json の各要素: {"file","tag","title","hero":[大1,小,小],"steps":[[絵,文],...] か "body":"..","ask"(任意),"accent"(任意)}
"photo"（リポジトリの一番上からの相対パス）があれば、上半分を写真にして、絵は小さなシール1つだけにする。
"""
import json
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1350
GOTHIC = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
INK = "#2B2B2B"
SOFT = "#6B6B6B"
ACCENTS = ["#FF8A5B", "#2EC4B6", "#5B8DEF", "#F25F8E", "#7BC67B", "#F2B134", "#9B6BDF"]


def font(size):
    return ImageFont.truetype(GOTHIC, size)


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mix(c, k):
    """k=0 で白、k=1 で元の色"""
    return tuple(int(255 - (255 - v) * k) for v in rgb(c))


def emoji(ch, size):
    im = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((80, 80), ch, font=ImageFont.truetype(EMOJI, 109), embedded_color=True, anchor="mm")
    im = im.crop(im.getbbox())
    s = size / max(im.size)
    return im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)


def sticker(ch, size, angle=0):
    """白いふちと影の付いたシール"""
    e = emoji(ch, size)
    pad = 26
    base = Image.new("RGBA", (e.width + pad * 2, e.height + pad * 2), (0, 0, 0, 0))
    base.alpha_composite(e, (pad, pad))
    alpha = base.getchannel("A").filter(ImageFilter.MaxFilter(25))
    white = Image.new("RGBA", base.size, (255, 255, 255, 255))
    white.putalpha(alpha)
    shadow = Image.new("RGBA", base.size, (0, 0, 0, 70))
    shadow.putalpha(alpha.point(lambda v: int(v * 0.3)).filter(ImageFilter.GaussianBlur(10)))
    out = Image.new("RGBA", (base.width + 20, base.height + 20), (0, 0, 0, 0))
    out.alpha_composite(shadow, (14, 18))
    out.alpha_composite(white, (0, 0))
    out.alpha_composite(base, (0, 0))
    return out.rotate(angle, resample=Image.BICUBIC, expand=True)


def put(img, im, cx, cy):
    img.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))


def fit(d, text, size, min_size, max_w):
    while size > min_size and d.textlength(text, font=font(size)) > max_w:
        size -= 2
    return size


def card(tip, accent, seed):
    rnd = random.Random(seed)
    img = Image.new("RGBA", (W, H), rgb(accent) + (255,))
    d = ImageDraw.Draw(img)
    if tip.get("photo"):
        photo_top(img, tip, accent, rnd)
    else:
        hero_top(img, d, tip, accent, rnd)
    return bottom_card(img, tip, accent)


def photo_top(img, tip, accent, rnd):
    """上半分（0〜700px）を写真にして、タグと小さなシールを載せる"""
    ph = Image.open(ROOT / tip["photo"]).convert("RGB")
    th = 700
    s = max(W / ph.width, th / ph.height)
    ph = ph.resize((int(ph.width * s) + 1, int(ph.height * s) + 1), Image.LANCZOS)
    x, y = (ph.width - W) // 2, int((ph.height - th) * tip.get("photo_y", 0.5))
    img.paste(ph.crop((x, y, x + W, y + th)), (0, 0))
    d = ImageDraw.Draw(img)
    tag = tip["tag"]
    tw = d.textlength(tag, font=font(40))
    d.rounded_rectangle([60, 60, 60 + tw + 64, 132], 36, fill=(255, 255, 255, 235))
    d.text((92, 96), tag, font=font(40), fill=accent, anchor="lm")
    put(img, sticker(tip["hero"][0], 130, rnd.uniform(-12, 12)), W - 150, 560)


def hero_top(img, d, tip, accent, rnd):
    # 背景の水玉と斜めの帯
    for _ in range(14):
        r = rnd.randint(30, 120)
        x, y = rnd.randint(-50, W + 50), rnd.randint(-50, 620)
        d.ellipse([x - r, y - r, x + r, y + r], fill=mix(accent, 0.75) + (255,))
    for i in range(-3, 8):
        x = i * 180
        d.polygon([(x, 0), (x + 60, 0), (x - 340, 620), (x - 400, 620)], fill=mix(accent, 0.88) + (255,))
    # タグ
    tag = tip["tag"]
    tw = d.textlength(tag, font=font(40))
    d.rounded_rectangle([60, 60, 60 + tw + 64, 132], 36, fill=(255, 255, 255, 255))
    d.text((92, 96), tag, font=font(40), fill=accent, anchor="lm")
    # 大きなイラスト
    hero = tip["hero"]
    put(img, sticker(hero[0], 300, rnd.uniform(-8, 8)), W / 2, 360)
    if len(hero) > 1:
        put(img, sticker(hero[1], 140, rnd.uniform(-20, 20)), W / 2 - 300, 300)
    if len(hero) > 2:
        put(img, sticker(hero[2], 140, rnd.uniform(-20, 20)), W / 2 + 300, 430)


def bottom_card(img, tip, accent):
    # 白いカード
    top = 640
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([50, top + 14, W - 50, H - 36], 48, fill=(0, 0, 0, 60))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(12)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([50, top, W - 50, H - 50], 48, fill=(255, 255, 255, 255))
    title = tip["title"].replace("\n", "")
    ts = fit(d, title, 72, 50, W - 200)
    lines = [title]
    if ts < 60:  # 小さくなりすぎる見出しは2行に分ける（title の改行の位置、無ければ読点か真ん中）
        if "\n" in tip["title"]:
            lines = tip["title"].split("\n")
        else:
            cut = title.find("、") + 1 or len(title) // 2
            lines = [title[:cut], title[cut:]]
        ts = min(fit(d, ln, 64, 50, W - 200) for ln in lines)
    ty = top + 80
    for ln in lines:
        d.text((W / 2, ty), ln, font=font(ts), fill=INK, anchor="mm")
        ty += int(ts * 1.25)
    d.rounded_rectangle([W / 2 - 50, ty - 20, W / 2 + 50, ty - 10], 5, fill=accent)
    y = ty + 45
    if tip.get("steps"):
        for i, (ch, text) in enumerate(tip["steps"]):
            d.rounded_rectangle([110, y - 8, W - 110, y + 92], 30, fill=mix(accent, 0.12) + (255,))
            put(img, emoji(ch, 66), 175, y + 42)
            d = ImageDraw.Draw(img)
            fs = fit(d, text, 46, 34, W - 360)
            d.text((235, y + 42), text, font=font(fs), fill=INK, anchor="lm")
            y += 118
    else:
        for ln in tip["body"].split("\n"):
            fs = fit(d, ln, 44, 32, W - 220)
            d.text((W / 2, y + 30), ln, font=font(fs), fill=INK, anchor="mm")
            y += 70
        y += 20
    if tip.get("ask") and y + 30 < H - 160:  # 入りきらない時は画像には載せない（本文に書く）
        d.text((W / 2, y + 30), tip["ask"], font=font(42), fill=accent, anchor="mm")
    d.text((W / 2, H - 100), "保存して後で見返してね", font=font(34), fill=SOFT, anchor="mm")
    put(img, emoji("🔖", 40), W / 2 + 230, H - 100)
    return img.convert("RGB")


def main(src, out_dir):
    tips = json.loads(Path(src).read_text())
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for i, t in enumerate(tips):
        card(t, t.get("accent", ACCENTS[i % len(ACCENTS)]), i).save(out / f"{t['file']}.jpg", quality=92)
        print(t["file"])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
