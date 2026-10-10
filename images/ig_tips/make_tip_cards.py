"""Instagram用の暮らしのコツ画像（1080x1350）を tips.json から作る。

使い方: python3 make_tip_cards.py   → 同じフォルダに <file>.jpg を書き出す
"""
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1350
FONT = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
BG = "#FFF8F0"
FG = "#222222"
MUTED = "#777777"
ACCENTS = ["#E76F51", "#2A9D8F", "#457B9D", "#B5838D", "#6A994E", "#D4A373", "#5E548E"]
HERE = Path(__file__).parent


def font(size):
    return ImageFont.truetype(FONT, size)


def centered(d, y, text, size, color, gap=1.4):
    fnt = font(size)
    for ln in text.split("\n"):
        w = d.textlength(ln, font=fnt)
        d.text(((W - w) / 2, y), ln, font=fnt, fill=color)
        y += int(size * gap)
    return y


def card(tip, accent):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 20], fill=accent)
    d.rectangle([0, H - 20, W, H], fill=accent)
    tag = font(40)
    tw = d.textlength(tip["tag"], font=tag)
    d.rounded_rectangle([(W - tw) / 2 - 36, 200, (W + tw) / 2 + 36, 280], radius=40, fill=accent)
    d.text(((W - tw) / 2, 218), tip["tag"], font=tag, fill="#FFFFFF")
    y = centered(d, 400, tip["title"], 84, FG)
    d.line([(W / 2 - 60, y + 30), (W / 2 + 60, y + 30)], fill=accent, width=6)
    y = centered(d, y + 100, tip["body"], 46, FG, 1.6)
    if tip.get("ask"):
        centered(d, y + 60, tip["ask"], 46, accent)
    centered(d, H - 110, "保存して後で見返してね", 34, MUTED)
    return img


def main():
    tips = json.loads((HERE / "tips.json").read_text())
    for i, tip in enumerate(tips):
        card(tip, ACCENTS[i % len(ACCENTS)]).save(HERE / f"{tip['file']}.jpg", quality=92)
        print(tip["file"])


if __name__ == "__main__":
    main()
