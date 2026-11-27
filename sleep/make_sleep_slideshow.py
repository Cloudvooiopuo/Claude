"""写真を何枚か順番に切り替える長い睡眠BGM動画を作る（ゆっくり重ねて切り替え）。

使い方: python3 make_sleep_slideshow.py <audio.wav> <時間(時間単位)> <out.mp4> "<タイトル1>" "<タイトル2>" <写真1> <写真2> ...
- 1枚目にだけタイトルを入れる（最初の画面とサムネイル用）。2枚目からは写真だけ
- 写真は時間を均等に分けて表示し、切り替えは12秒かけてゆっくり重ねる
- 画面は2コマ/秒。止まっている間はほとんどデータが増えないので、ファイルは小さいまま
"""
import os
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT = "/usr/share/fonts/opentype/ipafont-mincho/ipam.ttf"
W, H = 1920, 1080
FPS = 2
FADE = 12


def prep(path, t1=None, t2=None):
    im = Image.open(path).convert("RGB")
    s = max(W / im.width, H / im.height)
    im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)
    x, y = (im.width - W) // 2, (im.height - H) // 2
    im = im.crop((x, y, x + W, y + H))
    im = Image.blend(im, Image.new("RGB", (W, H), (8, 10, 24)), 0.30 if t1 is None else 0.45)
    if t1:
        im = im.filter(ImageFilter.GaussianBlur(1.2))
        d = ImageDraw.Draw(im)
        d.text((W / 2, H / 2 - 50), t1, font=ImageFont.truetype(FONT, 96), fill=(240, 236, 228), anchor="mm")
        d.text((W / 2, H / 2 + 70), t2, font=ImageFont.truetype(FONT, 48), fill=(200, 196, 210), anchor="mm")
    return np.asarray(im, dtype=np.float32)


def main(wav, hours, out, t1, t2, *photos):
    total = int(float(hours) * 3600)
    frames = [prep(photos[0], t1, t2)] + [prep(p) for p in photos[1:]]
    Image.fromarray(frames[0].astype(np.uint8)).save(str(Path(out).with_suffix(".jpg")), quality=92)
    seg = total / len(frames)
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    proc = subprocess.Popen([
        ff, "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-i", wav, "-t", str(total),
        "-c:v", "libx264", "-tune", "stillimage", "-preset", "veryfast", "-crf", "28", "-pix_fmt", "yuv420p",
        "-g", str(FPS * 60),
        "-af", f"afade=t=in:d=10,afade=t=out:st={max(0, total - 600)}:d={min(600, total)}",
        "-c:a", "aac", "-b:a", os.environ.get("ABR", "96k"), "-shortest", "-movflags", "+faststart", out,
    ], stdin=subprocess.PIPE)
    cache = {}
    for f in range(total * FPS):
        t = f / FPS
        i = min(int(t // seg), len(frames) - 1)
        into = t - i * seg
        if i + 1 < len(frames) and into > seg - FADE:
            a = round((into - (seg - FADE)) / FADE, 2)
            key = (i, a)
            if key not in cache:
                cache = {key: (frames[i] * (1 - a) + frames[i + 1] * a).astype(np.uint8).tobytes()}
            buf = cache[key]
        else:
            key = (i, 0)
            if key not in cache:
                cache = {key: frames[i].astype(np.uint8).tobytes()}
            buf = cache[key]
        proc.stdin.write(buf)
    proc.stdin.close()
    proc.wait()
    print("done", out, Path(out).stat().st_size // 1_000_000, "MB")


if __name__ == "__main__":
    main(*sys.argv[1:])
