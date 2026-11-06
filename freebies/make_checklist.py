"""無料プレゼント（チェックリスト・記入表）を作る。

使い方: python3 make_checklist.py <spec.json> <出力フォルダ>
  スマホ用の画像（1080x1350）: 01.jpg＝表紙、02.jpg〜＝リスト
  印刷用のPDF（A4 縦1枚）: <file>.pdf

spec.json:
  file, title（行のリスト）, sub, accent, photo（リポジトリの一番上からの相対パス）,
  sections: [{"head": "見出し", "items": ["項目", ...]}]  … チェックリスト
  か table: {"cols": ["列名", ...], "rows": 8, "tips": ["一言", ...]}  … 書き込む表
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
GOTHIC = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
MINCHO = "/usr/share/fonts/opentype/ipafont-mincho/ipam.ttf"
INK, SOFT, PAPER = "#3A3330", "#8A7F78", "#FFFDF7"
SIGN = "カフェと旅と売れ筋メモ"


def font(path, size):
    return ImageFont.truetype(path, size)


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def tint(c, k):
    return tuple(int(255 - (255 - v) * k) for v in rgb(c))


def cover_photo(path, w, h):
    im = Image.open(ROOT / path).convert("RGB")
    s = max(w / im.width, h / im.height)
    im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((x, y, x + w, y + h))


def check(d, x, y, size, accent):
    d.rounded_rectangle([x, y, x + size, y + size], int(size * 0.2), outline=accent, width=max(3, size // 12), fill="white")


def phone_cover(s, out):
    W, H = 1080, 1350
    bg = Image.new("RGB", (W, H), tint(s["accent"], 0.2))
    bg.paste(cover_photo(s["photo"], W, 760), (0, 0))
    d = ImageDraw.Draw(bg)
    d.rounded_rectangle([60, 640, W - 60, H - 70], 36, fill=PAPER)
    d.rounded_rectangle([W / 2 - 170, 600, W / 2 + 170, 680], 40, fill=s["accent"])
    d.text((W / 2, 640), "無料プレゼント", font=font(GOTHIC, 44), fill="white", anchor="mm")
    y = 740
    for ln in s["title"]:
        d.text((W / 2, y), ln, font=font(MINCHO, 76), fill=INK, anchor="ma")
        y += 100
    d.text((W / 2, y + 20), s["sub"], font=font(GOTHIC, 36), fill=SOFT, anchor="ma")
    d.text((W / 2, H - 170), "保存して使ってね📌".replace("📌", ""), font=font(GOTHIC, 40), fill=s["accent"], anchor="mm")
    d.text((W / 2, H - 110), SIGN, font=font(GOTHIC, 30), fill=SOFT, anchor="mm")
    bg.save(out, quality=92)


def draw_sections(d, s, x, y, w, scale, accent):
    for sec in s["sections"]:
        d.text((x, y), "■ " + sec["head"], font=font(GOTHIC, int(42 * scale)), fill=accent)
        y += int(66 * scale)
        for it in sec["items"]:
            check(d, x + int(8 * scale), y + int(4 * scale), int(38 * scale), accent)
            d.text((x + int(66 * scale), y), it, font=font(GOTHIC, int(36 * scale)), fill=INK)
            y += int(58 * scale)
        y += int(22 * scale)
    return y


def draw_table(d, s, x, y, w, scale, accent, rows):
    cols = s["table"]["cols"]
    widths = s["table"].get("widths") or [1] * len(cols)
    tot = sum(widths)
    xs = [x]
    for k in widths:
        xs.append(xs[-1] + w * k / tot)
    rh = int(78 * scale)
    d.rectangle([x, y, x + w, y + rh], fill=tint(accent, 0.3))
    for i, c in enumerate(cols):
        d.text(((xs[i] + xs[i + 1]) / 2, y + rh / 2), c, font=font(GOTHIC, int(30 * scale)), fill=INK, anchor="mm")
    for r in range(rows + 1):
        d.line([x, y + rh * (r + 1), x + w, y + rh * (r + 1)], fill=tint(accent, 0.5), width=2)
    for r, lab in enumerate(s["table"].get("labels", [])[:rows]):
        d.text(((xs[0] + xs[1]) / 2, y + rh * (r + 1.5)), lab, font=font(GOTHIC, int(32 * scale)), fill=INK, anchor="mm")
    for xx in xs:
        d.line([xx, y, xx, y + rh * (rows + 1)], fill=tint(accent, 0.5), width=2)
    y += rh * (rows + 1) + int(40 * scale)
    for t in s["table"].get("tips", []):
        d.text((x, y), "・" + t, font=font(GOTHIC, int(32 * scale)), fill=INK)
        y += int(52 * scale)
    return y


def phone_pages(s, outdir):
    W, H = 1080, 1350
    pages = []
    if "sections" in s:
        # 見出しごとに区切って、1枚に入るだけ並べる
        groups, cur, h = [], [], 0
        for sec in s["sections"]:
            need = 66 + 58 * len(sec["items"]) + 22
            if cur and h + need > 1060:
                groups.append(cur)
                cur, h = [], 0
            cur.append(sec)
            h += need
        groups.append(cur)
        for g in groups:
            pages.append({"sections": g})
    else:
        pages.append({"table": s["table"]})
    n = len(pages) + 1
    for i, p in enumerate(pages, start=2):
        bg = Image.new("RGB", (W, H), tint(s["accent"], 0.2))
        d = ImageDraw.Draw(bg)
        d.rounded_rectangle([50, 60, W - 50, H - 60], 30, fill=PAPER)
        d.text((W / 2, 130), " ".join(s["title"]), font=font(MINCHO, 48), fill=INK, anchor="mm")
        d.line([W / 2 - 60, 180, W / 2 + 60, 180], fill=s["accent"], width=6)
        if "sections" in p:
            draw_sections(d, {"sections": p["sections"]}, 110, 230, W - 220, 1.0, s["accent"])
        else:
            draw_table(d, {"table": p["table"]}, 90, 230, W - 180, 1.0, s["accent"], p["table"].get("rows", 8))
        d.text((W / 2, H - 100), f"{SIGN}　{i} / {n}", font=font(GOTHIC, 28), fill=SOFT, anchor="mm")
        bg.save(outdir / f"0{i}.jpg", quality=92)


def pdf(s, out):
    W, H = 1240, 1754  # A4 150dpi
    pg = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(pg)
    d.rectangle([0, 0, W, 16], fill=s["accent"])
    d.text((W / 2, 90), " ".join(s["title"]), font=font(MINCHO, 60), fill=INK, anchor="mm")
    d.text((W / 2, 160), s["sub"], font=font(GOTHIC, 30), fill=SOFT, anchor="mm")
    if "sections" in s:
        draw_sections(d, s, 140, 250, W - 280, 1.3, s["accent"])
    else:
        draw_table(d, s, 80, 240, W - 160, 1.0, s["accent"], s["table"].get("rows_pdf", 14))
    d.text((W / 2, H - 60), SIGN, font=font(GOTHIC, 26), fill=SOFT, anchor="mm")
    pg.save(out, "PDF", resolution=150)


def main():
    s = json.loads(Path(sys.argv[1]).read_text())
    outdir = Path(sys.argv[2])
    outdir.mkdir(parents=True, exist_ok=True)
    phone_cover(s, outdir / "01.jpg")
    phone_pages(s, outdir)
    pdf(s, outdir / f"{s['file']}.pdf")
    print("done", outdir)


if __name__ == "__main__":
    main()
