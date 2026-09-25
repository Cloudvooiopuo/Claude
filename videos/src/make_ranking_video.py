"""縦型（1080x1920）の文字だけのランキング動画を作る。

使い方: python3 make_ranking_video.py <spec.json> <out.mp4>
spec.json: {"hook": [..], "sub": "..", "items": [{"rank":3,"name":"..","note":".."}], "cta": [..], "accent": "#RRGGBB"}
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
FONT = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
BG = "#FFF8F0"
FG = "#222222"
MUTED = "#777777"
FPS = 30


def font(size):
    return ImageFont.truetype(FONT, size)


def wrap(draw, text, fnt, max_w):
    lines, line = [], ""
    for ch in text:
        if draw.textlength(line + ch, font=fnt) > max_w and line:
            lines.append(line)
            line = ch
        else:
            line += ch
    if line:
        lines.append(line)
    return lines


def draw_block(draw, lines_spec, top, max_w=920):
    y = top
    for text, size, color in lines_spec:
        fnt = font(size)
        for ln in wrap(draw, text, fnt, max_w):
            w = draw.textlength(ln, font=fnt)
            draw.text(((W - w) / 2, y), ln, font=fnt, fill=color)
            y += int(size * 1.35)
        y += int(size * 0.4)
    return y


def base(accent):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 24], fill=accent)
    d.rectangle([0, H - 24, W, H], fill=accent)
    d.text((60, 70), "#PR", font=font(40), fill=MUTED)
    return img, d


def frame_hook(spec):
    img, d = base(spec["accent"])
    lines = [(t, 92, FG) for t in spec["hook"]]
    lines.append((spec["sub"], 46, MUTED))
    draw_block(d, lines, 640)
    return img


def frame_item(spec, item):
    img, d = base(spec["accent"])
    r = item["rank"]
    fnt = font(260)
    label = f"{r}位"
    w = d.textlength(label, font=fnt)
    d.text(((W - w) / 2, 430), label, font=fnt, fill=spec["accent"])
    draw_block(d, [(item["name"], 70, FG), (item.get("note", ""), 46, MUTED)], 820)
    return img


def frame_cta(spec):
    img, d = base(spec["accent"])
    draw_block(d, [(t, 76, FG) for t in spec["cta"]] + [(spec.get("foot", ""), 40, MUTED)], 700)
    return img


def main(spec_path, out_path):
    spec = json.loads(Path(spec_path).read_text())
    frames = [(frame_hook(spec), 3.0)]
    for it in sorted(spec["items"], key=lambda x: -x["rank"]):
        frames.append((frame_item(spec, it), 3.0))
    frames.append((frame_cta(spec), 3.5))

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    with tempfile.TemporaryDirectory() as tmp:
        lst = Path(tmp) / "list.txt"
        entries = []
        for i, (img, dur) in enumerate(frames):
            p = Path(tmp) / f"f{i}.png"
            img.save(p)
            entries.append(f"file '{p}'\nduration {dur}")
        entries.append(f"file '{Path(tmp) / f'f{len(frames) - 1}.png'}'")
        lst.write_text("\n".join(entries) + "\n")
        # 無音の音声トラックを付ける（無音トラックが無いと弾くSNSがあるため）
        subprocess.run([
            ffmpeg, "-y", "-loglevel", "error",
            "-f", "concat", "-safe", "0", "-i", str(lst),
            "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
            "-vf", f"fps={FPS},format=yuv420p",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-c:a", "aac", "-shortest", "-movflags", "+faststart",
            out_path,
        ], check=True)
        frames[0][0].save(Path(out_path).with_suffix(".jpg"), quality=90)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
