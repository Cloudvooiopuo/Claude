"""プロフィール用の画像（アイコン3案・YouTubeバナー）を作る。

使い方: python3 make_profile_images.py
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
OUT = Path(__file__).parent
NAME = ["まいにち", "売れ筋メモ"]


def font(size):
    return ImageFont.truetype(FONT, size)


def centered(d, y, text, size, fill, w=1080):
    f = font(size)
    tw = d.textlength(text, font=f)
    d.text(((w - tw) / 2, y), text, font=f, fill=fill)


def icon(bg, fg, sub, name):
    img = Image.new("RGB", (1080, 1080), bg)
    d = ImageDraw.Draw(img)
    # 丸く切り抜かれても文字が欠けないよう、中央の円の内側だけに描く
    d.ellipse([90, 90, 990, 990], outline=sub, width=14)
    centered(d, 330, NAME[0], 120, fg)
    centered(d, 490, NAME[1], 150, fg)
    centered(d, 700, "TOP3で紹介", 64, sub)
    img.save(OUT / name, quality=92)


def banner():
    # YouTubeバナー 2560x1440。どの端末でも見える中央 1546x423 に文字を収める
    img = Image.new("RGB", (2560, 1440), "#FFF8F0")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 2560, 40], fill="#E8833A")
    d.rectangle([0, 1400, 2560, 1440], fill="#E8833A")
    centered(d, 560, "まいにち売れ筋メモ", 150, "#222222", 2560)
    centered(d, 750, "Amazon・楽天で今売れてる物を、30秒のTOP3で。", 64, "#777777", 2560)
    img.save(OUT / "youtube_banner.jpg", quality=92)


if __name__ == "__main__":
    icon("#E8833A", "#FFFFFF", "#FFE3CC", "icon_a_orange.jpg")
    icon("#FFF8F0", "#222222", "#E8833A", "icon_b_cream.jpg")
    icon("#222222", "#FFFFFF", "#E8833A", "icon_c_black.jpg")
    banner()
