"""BOOTHで売る手帳（印刷・書き込み用のPDF）を作る。

使い方: python3 make_techo.py <spec.json> <出力フォルダ>
  <file>.pdf … A4縦（150dpi）の複数ページのPDF
  preview/01.jpg〜 … 商品ページ用の見本画像（1080x1350、表紙と中身の数ページ）

spec.json の pages は次の種類を並べる:
  {"type":"cover"}                                    表紙（title, sub, photo）
  {"type":"text","head":..,"lines":[..]}              説明のページ
  {"type":"table","head":..,"cols":[..],"widths":[..],"rows":N,"labels":[..],"note":..}
  {"type":"check","head":..,"items":[..],"note":..}   チェックリスト
  {"type":"lines","head":..,"rows":N}                 罫線だけのメモ
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
GOTHIC = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
MINCHO = "/usr/share/fonts/opentype/ipafont-mincho/ipam.ttf"
INK, SOFT = "#3A3330", "#8A7F78"
SIGN = "カフェと旅と売れ筋メモ"
W, H = 1240, 1754
M = 90


def font(path, size):
    return ImageFont.truetype(path, size)


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def tint(c, k):
    return tuple(int(255 - (255 - v) * k) for v in rgb(c))


def photo(path, w, h):
    im = Image.open(ROOT / path).convert("RGB")
    s = max(w / im.width, h / im.height)
    im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((x, y, x + w, y + h))


def wrap(d, text, fnt, max_w):
    out, line = [], ""
    for ch in text:
        if d.textlength(line + ch, font=fnt) > max_w and line:
            out.append(line)
            line = ch
        else:
            line += ch
    return out + ([line] if line else [])


def base(s, n, total, head):
    pg = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(pg)
    d.rectangle([0, 0, W, 14], fill=s["accent"])
    d.text((M, 70), head, font=font(MINCHO, 56), fill=INK)
    d.line([M, 150, M + 140, 150], fill=s["accent"], width=6)
    d.text((W / 2, H - 50), f"{s['name']}　{n} / {total}　{SIGN}", font=font(GOTHIC, 22), fill=SOFT, anchor="mm")
    return pg, d


def cover(s, total):
    pg = Image.new("RGB", (W, H), tint(s["accent"], 0.18))
    pg.paste(photo(s["photo"], W, 980), (0, 0))
    d = ImageDraw.Draw(pg)
    d.rounded_rectangle([90, 860, W - 90, H - 120], 40, fill="#FFFDF7")
    y = 960
    for ln in s["title"]:
        d.text((W / 2, y), ln, font=font(MINCHO, 96), fill=INK, anchor="ma")
        y += 124
    d.line([W / 2 - 80, y + 20, W / 2 + 80, y + 20], fill=s["accent"], width=6)
    d.text((W / 2, y + 70), s["sub"], font=font(GOTHIC, 36), fill=SOFT, anchor="ma")
    d.text((W / 2, H - 230), f"印刷して使えるA4 {total}ページ", font=font(GOTHIC, 34), fill=s["accent"], anchor="mm")
    d.text((W / 2, H - 170), SIGN, font=font(GOTHIC, 28), fill=SOFT, anchor="mm")
    return pg


def page_text(s, p, n, total):
    pg, d = base(s, n, total, p["head"])
    y = 220
    for ln in p["lines"]:
        if ln.startswith("■"):
            y += 20
            d.text((M, y), ln, font=font(GOTHIC, 38), fill=s["accent"])
            y += 64
            continue
        for w in wrap(d, ln, font(GOTHIC, 32), W - 2 * M):
            d.text((M, y), w, font=font(GOTHIC, 32), fill=INK)
            y += 52
    return pg


def page_table(s, p, n, total):
    pg, d = base(s, n, total, p["head"])
    y = 210
    if p.get("note"):
        for w in wrap(d, p["note"], font(GOTHIC, 28), W - 2 * M):
            d.text((M, y), w, font=font(GOTHIC, 28), fill=SOFT)
            y += 44
        y += 16
    cols, widths = p["cols"], p.get("widths") or [1] * len(p["cols"])
    xs = [M]
    for k in widths:
        xs.append(xs[-1] + (W - 2 * M) * k / sum(widths))
    rows = p["rows"]
    rh = min(84, (H - 140 - y) // (rows + 1))
    d.rectangle([M, y, W - M, y + rh], fill=tint(s["accent"], 0.3))
    for i, c in enumerate(cols):
        d.text(((xs[i] + xs[i + 1]) / 2, y + rh / 2), c, font=font(GOTHIC, 28), fill=INK, anchor="mm")
    for r in range(rows + 1):
        d.line([M, y + rh * (r + 1), W - M, y + rh * (r + 1)], fill=tint(s["accent"], 0.5), width=2)
    for xx in xs:
        d.line([xx, y, xx, y + rh * (rows + 1)], fill=tint(s["accent"], 0.5), width=2)
    for r, lab in enumerate(p.get("labels", [])[:rows]):
        d.text(((xs[0] + xs[1]) / 2, y + rh * (r + 1.5)), lab, font=font(GOTHIC, 26), fill=INK, anchor="mm")
    return pg


def page_check(s, p, n, total):
    pg, d = base(s, n, total, p["head"])
    y = 220
    if p.get("note"):
        for w in wrap(d, p["note"], font(GOTHIC, 28), W - 2 * M):
            d.text((M, y), w, font=font(GOTHIC, 28), fill=SOFT)
            y += 44
        y += 20
    for it in p["items"]:
        d.rounded_rectangle([M, y + 4, M + 40, y + 44], 8, outline=s["accent"], width=4)
        for k, w in enumerate(wrap(d, it, font(GOTHIC, 32), W - 2 * M - 70)):
            d.text((M + 66, y + k * 48), w, font=font(GOTHIC, 32), fill=INK)
        y += 48 * max(1, len(wrap(d, it, font(GOTHIC, 32), W - 2 * M - 70))) + 30
    return pg


def page_lines(s, p, n, total):
    pg, d = base(s, n, total, p["head"])
    y = 230
    for _ in range(p.get("rows", 20)):
        y += 64
        d.line([M, y, W - M, y], fill=tint(s["accent"], 0.4), width=2)
    return pg


def main():
    s = json.loads(Path(sys.argv[1]).read_text())
    out = Path(sys.argv[2])
    (out / "preview").mkdir(parents=True, exist_ok=True)
    total = len(s["pages"])
    pages = []
    for n, p in enumerate(s["pages"], start=1):
        f = {"cover": lambda *a: cover(s, total), "text": page_text, "table": page_table,
             "check": page_check, "lines": page_lines}[p["type"]]
        pages.append(f(s, p, n, total) if p["type"] != "cover" else f())
    pages[0].save(out / f"{s['file']}.pdf", "PDF", resolution=150, save_all=True, append_images=pages[1:])
    for k, i in enumerate(s.get("preview", [1, 3, 5, 7]), start=1):
        im = pages[i - 1].copy()
        im.thumbnail((1080, 1350))
        bg = Image.new("RGB", (1080, 1350), tint(s["accent"], 0.18))
        bg.paste(im, ((1080 - im.width) // 2, (1350 - im.height) // 2))
        bg.save(out / "preview" / f"0{k}.jpg", quality=92)
    print("done", total, "pages")


if __name__ == "__main__":
    main()
