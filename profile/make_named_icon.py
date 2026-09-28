"""A案のイラストに名前「カフェと旅と売れ筋メモ」を入れたアイコンを作る。
丸く切り抜かれても文字が欠けないよう、円の内側だけに置く。"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).parent
FONT = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
INK, BG = "#264653", "#FBEFE3"


def main():
    art = Image.open(OUT / "hobby_icon_a_warm.jpg").resize((700, 700), Image.LANCZOS)
    img = Image.new("RGB", (1080, 1080), BG)
    img.paste(art, (190, 60))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([150, 760, 930, 960], radius=100, fill="#FFFFFF")
    for text, size, y in [("カフェと旅と", 80, 780), ("売れ筋メモ", 92, 865)]:
        f = ImageFont.truetype(FONT, size)
        w = d.textlength(text, font=f)
        d.text(((1080 - w) / 2, y), text, font=f, fill=INK)
    img.save(OUT / "icon_final_named.jpg", quality=92)


if __name__ == "__main__":
    main()
