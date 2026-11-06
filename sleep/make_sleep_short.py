"""睡眠BGMの長い動画から、ショート用の縦動画（1080×1920・約35秒）を作る。

使い方: python3 make_sleep_short.py <元の動画.mp4> <開始秒> <写真.jpg> <out.mp4> "<題名1>" "<題名2>"
- 音は元の動画の <開始秒> から35秒を切り出し、最初と最後をふんわり出し入れする
- 映像は写真を縦に切り抜き、ゆっくり寄っていく。上に題名、下に「フル版はチャンネルで」
"""
import subprocess
import sys

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT = "/usr/share/fonts/opentype/ipafont-mincho/ipam.ttf"
W, H = 1080, 1920
SEC = 35
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()


def frame(photo, t1, t2, path):
    # ズームの余白ぶん大きめに作る
    bw, bh = int(W * 1.12), int(H * 1.12)
    im = Image.open(photo).convert("RGB")
    s = max(bw / im.width, bh / im.height)
    im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)
    x, y = (im.width - bw) // 2, (im.height - bh) // 2
    im = im.crop((x, y, x + bw, y + bh))
    im = Image.blend(im, Image.new("RGB", im.size, (8, 10, 24)), 0.35)
    d = ImageDraw.Draw(im)
    cx = bw / 2
    # 文字のうしろを少し暗くして読みやすく
    shade = Image.new("L", im.size, 0)
    sd = ImageDraw.Draw(shade)
    sd.rectangle([0, bh * 0.16, bw, bh * 0.36], fill=110)
    sd.rectangle([0, bh * 0.80, bw, bh * 0.90], fill=90)
    shade = shade.filter(ImageFilter.GaussianBlur(60))
    im = Image.composite(Image.new("RGB", im.size, (0, 0, 0)), im, shade)
    d = ImageDraw.Draw(im)
    d.text((cx, bh * 0.23), t1, font=ImageFont.truetype(FONT, 92), fill=(242, 238, 230), anchor="mm")
    d.text((cx, bh * 0.30), t2, font=ImageFont.truetype(FONT, 58), fill=(214, 210, 224), anchor="mm")
    d.text((cx, bh * 0.85), "フル版（1時間）はチャンネルで", font=ImageFont.truetype(FONT, 46), fill=(230, 226, 236), anchor="mm")
    im.save(path, quality=92)


def main(src, start, photo, out, t1, t2):
    img = out + ".jpg"
    frame(photo, t1, t2, img)
    n = SEC * 30
    subprocess.run([FFMPEG, "-nostdin", "-y", "-loglevel", "error",
                    "-loop", "1", "-i", img,
                    "-ss", str(start), "-t", str(SEC), "-i", src,
                    "-filter_complex",
                    f"[0:v]zoompan=z='1.12-0.12*on/{n}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={n}:s={W}x{H}:fps=30,format=yuv420p[v];"
                    f"[1:a]afade=t=in:d=2,afade=t=out:st={SEC - 3}:d=3[a]",
                    "-map", "[v]", "-map", "[a]", "-t", str(SEC),
                    "-c:v", "libx264", "-preset", "medium", "-crf", "23",
                    "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", out], check=True)
    import os
    os.remove(img)
    print("done", out, flush=True)


if __name__ == "__main__":
    main(*sys.argv[1:])
