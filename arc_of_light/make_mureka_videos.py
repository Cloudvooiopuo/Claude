"""Murekaの「映像音楽」にアップロードする、曲ごとの短い動画（12秒・1280×720）を作る。

使い方: python3 make_mureka_videos.py
- 背景は make_brand_images.py の絵や写真を、文字なしで使う
- ゆっくり寄る・横に流れる動き（ズームとパン）をつけ、曲ごとに動きと切り取り方を変える
- 出力: mureka_videos/<番号>_<曲名>.mp4
"""
import math
import subprocess
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

import make_brand_images as m

OUT = Path(__file__).parent / "mureka_videos"
W, H = 2560, 1440
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()


def sky_day():
    im = m.gradient(W, H, m.DAY_TOP, m.DAY_BOTTOM).convert("RGBA")
    im.alpha_composite(m.clouds((W, H), 21, 9))
    im.alpha_composite(m.sparkles((W, H), 120, 4, big=8))
    return im


def sky_day_arc():
    im = sky_day()
    im.alpha_composite(m.arc((W, H), W / 2, H * 0.75, 700, 40, m.LIGHT_ARC))
    m.flare(im, W / 2 + 700 * math.cos(math.radians(-50)), H * 0.75 + 700 * math.sin(math.radians(-50)), 40)
    return im


def sky_night():
    im = m.gradient(W, H).convert("RGBA")
    im.alpha_composite(m.sparkles((W, H), 700, 13, big=20))
    return im


def photo(name, warm=1.0, soften=4):
    im = m.photo_bg(m.OUT / name, W, H, bright=1.0, soften=soften).convert("RGB")
    if warm != 1.0:
        r, g, b = im.split()
        r = r.point(lambda v: min(255, int(v * warm)))
        b = b.point(lambda v: int(v / warm))
        im = Image.merge("RGB", (r, g, b))
    return im.convert("RGBA")


def sky_golden():
    # 夕方の金色の空と、低い太陽の光
    im = m.gradient(W, H, (255, 160, 120), (255, 226, 170)).convert("RGBA")
    im.alpha_composite(m.clouds((W, H), 31, 7))
    m.flare(im, W * 0.7, H * 0.62, 120)
    im.alpha_composite(m.sparkles((W, H), 80, 6, big=4))
    return im


def sky_lemon():
    # レモン色からミントへの、明るくさわやかな空
    im = m.gradient(W, H, (255, 244, 180), (196, 240, 220)).convert("RGBA")
    im.alpha_composite(m.clouds((W, H), 41, 8))
    im.alpha_composite(m.sparkles((W, H), 140, 8, big=10))
    return im


def cg_night_arc():
    return m.cg_scene(W, H, True, seed=5)


SONGS = [
    ("01", "Brand_New_Sky", sky_day_arc, "in"),
    ("02", "Neon_Hearts", lambda: m.cg_scene(W, H, True, seed=2), "in"),
    ("03", "Golden_Hour", sky_golden, "right"),
    ("04", "Wild_and_Free", lambda: photo("live_1.jpg", soften=3), "in"),
    ("05", "Coffee_and_Sunshine", lambda: photo("records_1.jpg", warm=1.08, soften=3), "left"),
    ("06", "Midnight_Drive", lambda: photo("neon_1.jpg", soften=24), "right"),
    ("07", "Higher_Than_the_Stars", sky_night, "out"),
    ("08", "Weekend_Vibes", lambda: m.cg_scene(W, H, False, seed=3), "in"),
    ("09", "ソーダ色のサマーデイ", sky_day, "left"),
    ("10", "ミッドナイト・ネオン", lambda: photo("neon_1.jpg", soften=24), "out"),
    ("11", "スタートライン", lambda: photo("live_1.jpg", soften=5), "right"),
    ("12", "アーク・オブ・ライト", cg_night_arc, "out"),
    ("13", "レモネード・ウィークエンド", sky_lemon, "left"),
]


def render(num, title, make_bg, move, sec=12, fps=30):
    src = OUT / f"_{num}.png"
    make_bg().convert("RGB").save(src)
    n = sec * fps
    # zoompan：in=ゆっくり寄る、out=ゆっくり引く、left/right=少し寄ったまま横に流れる
    if move == "in":
        z, x, y = f"1+0.15*on/{n}", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    elif move == "out":
        z, x, y = f"1.15-0.15*on/{n}", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    elif move == "left":
        z, x, y = "1.15", f"(iw-iw/zoom)*(1-on/{n})", "ih/2-(ih/zoom/2)"
    else:
        z, x, y = "1.15", f"(iw-iw/zoom)*on/{n}", "ih/2-(ih/zoom/2)"
    out = OUT / f"{num}_{title}.mp4"
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-loop", "1", "-i", str(src),
                    "-vf", f"zoompan=z='{z}':x='{x}':y='{y}':d={n}:s=1280x720:fps={fps},format=yuv420p",
                    "-t", str(sec), "-c:v", "libx264", "-preset", "medium", "-crf", "24",
                    "-movflags", "+faststart", str(out)], check=True)
    src.unlink()
    print(out.name, round(out.stat().st_size / 1e6, 1), "MB", flush=True)


if __name__ == "__main__":
    import sys
    only = set(sys.argv[1:])
    for s in SONGS:
        if not only or s[0] in only:
            render(*s)
