"""手紙ふうの画像（1080x1350）を数枚作る。Instagramのカルーセル・TikTokの写真投稿用。

使い方: python3 make_letter_cards.py <spec.json> <出力フォルダ>
spec.json は videos/src/motion/*.json と同じ形（hook / sub / items / emoji / accent）。
表紙 → コツ1〜3 → 締め の5枚を 01.jpg〜05.jpg で書き出す。
"photos"（make_photo_video.py と同じ形）があれば、絵文字の代わりに写真をテープで貼った形にする。
"photo_note": true なら写真の下に「※写真はイメージです」を出す（商品紹介の回）。
"""
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1350
MINCHO = "/usr/share/fonts/opentype/ipafont-mincho/ipam.ttf"
GOTHIC = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
INK = "#3A3330"
SOFT = "#8A7F78"
PAPER = "#FFFDF7"
SIGN = "カフェと旅と売れ筋メモ"
PX, PY = 90, 120          # 紙の外側の余白
TEXT_W = W - 2 * PX - 120  # 紙の中の文字幅


def font(path, size):
    return ImageFont.truetype(path, size)


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def tint(c, k):
    return tuple(int(255 - (255 - v) * k) for v in rgb(c))


def emoji(ch, size):
    im = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((80, 80), ch, font=font(EMOJI, 109), embedded_color=True, anchor="mm")
    im = im.crop(im.getbbox())
    s = size / max(im.size)
    return im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)


def wrap(d, text, fnt, max_w):
    lines, line = [], ""
    for ch in text:
        if d.textlength(line + ch, font=fnt) > max_w and line:
            lines.append(line)
            line = ch
        else:
            line += ch
    return lines + [line] if line else lines


def fit_size(d, text, path, size, min_size, max_w):
    while size > min_size and d.textlength(text, font=font(path, size)) > max_w:
        size -= 2
    return size


def block(d, y, text, path, size, color, min_size=None, gap=1.5):
    size = fit_size(d, text, path, size, min_size or int(size * 0.7), TEXT_W)
    fnt = font(path, size)
    for ln in wrap(d, text, fnt, TEXT_W):
        d.text((W / 2, y), ln, font=fnt, fill=color, anchor="ma")
        y += int(size * gap)
    return y


def paper(accent, page, total, seed):
    bg = Image.new("RGB", (W, H), tint(accent, 0.22))
    # 紙の影
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([PX + 10, PY + 16, W - PX + 10, H - PY + 16], 18, fill=(0, 0, 0, 60))
    bg.paste(sh.filter(ImageFilter.GaussianBlur(14)), (0, 0), sh.filter(ImageFilter.GaussianBlur(14)))
    d = ImageDraw.Draw(bg)
    d.rounded_rectangle([PX, PY, W - PX, H - PY], 18, fill=PAPER)
    # 罫線
    for y in range(PY + 150, H - PY - 60, 72):
        d.line([PX + 50, y, W - PX - 50, y], fill=tint(accent, 0.18), width=2)
    # マスキングテープ
    tape = Image.new("RGBA", (300, 70), tint(accent, 0.55) + (190,))
    tape = tape.rotate(-6 if seed % 2 else 5, expand=True, resample=Image.BICUBIC)
    bg.paste(tape, (int(W / 2 - tape.width / 2), PY - 40), tape)
    # ページ
    d.text((W / 2, H - PY - 50), f"{page} / {total}", font=font(GOTHIC, 30), fill=SOFT, anchor="mm")
    return bg, d


def stamp(bg, accent, ch):
    d = ImageDraw.Draw(bg)
    x0, y0 = W - PX - 170, PY + 40
    d.rounded_rectangle([x0, y0, x0 + 120, y0 + 140], 10, fill=tint(accent, 0.35), outline=accent, width=4)
    e = emoji(ch, 84)
    bg.paste(e, (int(x0 + 60 - e.width / 2), int(y0 + 70 - e.height / 2)), e)


def snapshot(bg, accent, path, w, h, cy, angle, note=False):
    """写真を白いふち付きで少し傾け、上にマスキングテープを貼る。写真の下の端の y を返す"""
    path, _, fx = path.partition("#")
    im = Image.open(ROOT / path).convert("RGB")
    s = max(w / im.width, h / im.height)
    im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)
    x, y = int((im.width - w) * float(fx or 0.5)), (im.height - h) // 2
    im = im.crop((x, y, x + w, y + h))
    b = 18
    card = Image.new("RGBA", (w + 2 * b, h + 2 * b), (255, 255, 255, 255))
    card.paste(im, (b, b))
    tape = Image.new("RGBA", (200, 56), tint(accent, 0.55) + (200,))
    sh = Image.new("RGBA", (card.width + 40, card.height + 40), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle([20, 26, card.width + 20, card.height + 26], fill=(0, 0, 0, 70))
    sh = sh.filter(ImageFilter.GaussianBlur(10))
    sh.alpha_composite(card, (20, 20))
    sh = sh.rotate(angle, resample=Image.BICUBIC, expand=True)
    bg.paste(sh, (int(W / 2 - sh.width / 2), int(cy - sh.height / 2)), sh)
    t = tape.rotate(-angle * 3, expand=True, resample=Image.BICUBIC)
    bg.paste(t, (int(W / 2 - t.width / 2), int(cy - sh.height / 2) + 4), t)
    bottom = cy + sh.height / 2
    if note:
        ImageDraw.Draw(bg).text((W / 2, bottom - 6), "※写真はイメージです", font=font(GOTHIC, 26), fill=SOFT,
                                anchor="ma")
        bottom += 26
    return bottom


def main(spec_path, out_dir):
    s = json.loads(Path(spec_path).read_text())
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    acc = s["accent"]
    em = s.get("emoji", {})
    tag, _, sub = s["sub"].partition("｜")
    items = sorted(s["items"], key=lambda x: -x["rank"])
    total = len(items) + 2

    # 表紙
    ph = s.get("photos")
    note = s.get("photo_note", False)
    bg, d = paper(acc, 1, total, 0)
    if ph:
        d.text((PX + 70, PY + 60), f"{tag}のレター", font=font(GOTHIC, 34), fill=acc)
        if s.get("pr", True):
            d.text((W - PX - 70, PY + 60), "#PR", font=font(GOTHIC, 34), fill=SOFT, anchor="ra")
        y = snapshot(bg, acc, ph["hook"], 600, 290, PY + 300, -3, note) + 40
        for ln in s["hook"]:
            y = block(d, y, ln, MINCHO, 66, INK, gap=1.35)
    else:
        stamp(bg, acc, em.get("hook", "✉️"))
        d.text((PX + 70, PY + 90), f"{tag}のレター", font=font(GOTHIC, 38), fill=acc)
        y = PY + 330
        for ln in s["hook"]:
            y = block(d, y, ln, MINCHO, 96, INK, gap=1.4)
    y = block(d, y + (20 if ph else 50), sub or "コツを3つ書きました", MINCHO, 44 if ph else 48, SOFT)
    d.text((W / 2, y + (30 if ph else 70)), "めくってね  →", font=font(MINCHO, 42 if ph else 44), fill=acc, anchor="ma")
    bg.save(out / "01.jpg", quality=92)

    # コツ
    for i, it in enumerate(items):
        bg, d = paper(acc, i + 2, total, i + 1)
        if ph:
            d.text((W / 2, PY + 70), f"その{i + 1}", font=font(MINCHO, 76), fill=acc, anchor="ma")
            y = snapshot(bg, acc, ph["items"][str(it["rank"])], 660, 400, PY + 420, (-2.5, 2, -1.5)[i % 3], note)
            y = block(d, y + 40, it["name"], MINCHO, 64, INK, min_size=46)
        else:
            d.text((W / 2, PY + 150), f"その{i + 1}", font=font(MINCHO, 84), fill=acc, anchor="ma")
            e = emoji(em.get("items", {}).get(str(it["rank"]), "✅"), 230)
            bg.paste(e, (int(W / 2 - e.width / 2), PY + 300), e)
            y = block(d, PY + 600, it["name"], MINCHO, 70, INK, min_size=50)
        if it.get("note"):
            block(d, y + 30, it["note"], MINCHO, 44, SOFT, min_size=34)
        bg.save(out / f"{i + 2:02d}.jpg", quality=92)

    # 締め
    bg, d = paper(acc, total, total, 9)
    if ph:
        y = snapshot(bg, acc, ph["cta"], 560, 300, PY + 260, 2, False) + 50
    else:
        e = emoji(em.get("cta", "🔖"), 200)
        bg.paste(e, (int(W / 2 - e.width / 2), PY + 220), e)
        y = PY + 520
    y = block(d, y, "読んでくれてありがとう", MINCHO, 66, INK)
    y = block(d, y + 20, "保存して、後で見返してね", MINCHO, 56, INK)
    if s.get("pr", True):
        y = block(d, y + 20, "紹介した物はプロフィールのリンクから", MINCHO, 42, SOFT)
    d.text((W - PX - 70, H - PY - 130), f"— {SIGN}", font=font(MINCHO, 42), fill=SOFT, anchor="ra")
    bg.save(out / f"{total:02d}.jpg", quality=92)
    print(out, total)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
