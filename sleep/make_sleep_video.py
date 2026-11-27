"""睡眠BGMの長い動画を作る（静止画1枚＋ループする音）。9時間でも数分で書き出せる。

使い方: python3 make_sleep_video.py <背景.jpg> <loop.wav> <時間(時間単位)> <out.mp4> "<タイトル1行目>" "<2行目>"
- 画面はほぼ動かないので、映像は1秒1コマ・低いビットレートにしてファイルを小さくする
- 最後の10分は音を少しずつ小さくする（寝ている人を起こさない）
"""
import os
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT = "/usr/share/fonts/opentype/ipafont-mincho/ipam.ttf"
W, H = 1920, 1080


def thumb(bg, t1, t2, out):
    im = Image.open(bg).convert("RGB")
    s = max(W / im.width, H / im.height)
    im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)
    x, y = (im.width - W) // 2, (im.height - H) // 2
    im = im.crop((x, y, x + W, y + H)).filter(ImageFilter.GaussianBlur(1.2))
    dark = Image.new("RGB", (W, H), (8, 10, 24))
    im = Image.blend(im, dark, 0.45)
    d = ImageDraw.Draw(im)
    d.text((W / 2, H / 2 - 50), t1, font=ImageFont.truetype(FONT, 96), fill=(240, 236, 228), anchor="mm")
    d.text((W / 2, H / 2 + 70), t2, font=ImageFont.truetype(FONT, 48), fill=(200, 196, 210), anchor="mm")
    im.save(out, quality=92)


def main(bg, wav, hours, out, t1, t2):
    img = str(Path(out).with_suffix(".jpg"))
    thumb(bg, t1, t2, img)
    total = float(hours) * 3600
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    fade_st = max(0, total - 600)
    subprocess.run([
        ff, "-y", "-loglevel", "error",
        "-loop", "1", "-framerate", "1", "-i", img,
        "-stream_loop", "-1", "-i", wav,
        "-t", str(total),
        "-c:v", "libx264", "-tune", "stillimage", "-preset", "veryfast", "-r", "1", "-pix_fmt", "yuv420p", "-crf", "28",
        "-af", f"afade=t=in:d=10,afade=t=out:st={fade_st}:d={min(600, total)}",
        "-c:a", "aac", "-b:a", os.environ.get("ABR", "128k"), "-movflags", "+faststart", out,
    ], check=True)
    print("done", out, Path(out).stat().st_size // 1_000_000, "MB")


if __name__ == "__main__":
    main(*sys.argv[1:7])
