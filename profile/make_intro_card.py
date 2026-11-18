"""Instagramに固定する自己紹介の画像（1080x1350）を作る。"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).parent
FONT = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
BG, INK, ACCENT = "#FBEFE3", "#264653", "#E76F51"


def font(n):
    return ImageFont.truetype(FONT, n)


def main():
    img = Image.new("RGB", (1080, 1350), BG)
    d = ImageDraw.Draw(img)
    icon = Image.open(OUT / "hobby_icon_a_warm.jpg").resize((360, 360))
    mask = Image.new("L", (360, 360), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, 359, 359], fill=255)
    img.paste(icon, (360, 110), mask)
    y = 530
    for text, size, col in [
        ("はじめまして", 84, INK),
        ("カフェ巡り・旅行・コスメ・料理", 48, INK),
        ("音楽とアートが好きです", 48, INK),
        ("", 30, INK),
        ("Amazon・楽天で", 56, ACCENT),
        ("今売れてる物を", 56, ACCENT),
        ("30秒のTOP3で毎日紹介", 56, ACCENT),
        ("", 30, INK),
        ("知りたいジャンルはコメントで教えてね", 40, "#6B705C"),
    ]:
        if text:
            w = d.textlength(text, font=font(size))
            d.text(((1080 - w) / 2, y), text, font=font(size), fill=col)
        y += int(size * 1.45)
    img.save(OUT / "intro_card_instagram.jpg", quality=92)


if __name__ == "__main__":
    main()
