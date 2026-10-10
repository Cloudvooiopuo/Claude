"""動きのある縦型動画（1080x1920）を作る。文字だけのスライドの代わりに、
色が動く背景・大きな絵文字のイラスト・弾む／すべり込む文字・進み具合のバーを付ける。

使い方: python3 make_motion_video.py <spec.json> <out.mp4>
spec.json は make_narrated_video.py と同じ形に、次を足す:
  "emoji": {"hook": "🏠", "items": {"3": "📦", "2": "🛋️", "1": "🎨"}, "cta": "🔖"}
声は VOICEVOX（localhost:50021）、BGM は make_bgm.py。声と BGM の扱いは make_narrated_video.py と同じ。
"""
import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
import make_bgm  # noqa: E402
from make_narrated_video import SR, resample, speak  # noqa: E402

W, H, FPS = 1080, 1920, 30
FONT = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
EMOJI_FONT = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
FG = "#222222"
MUTED = "#666666"
_fonts, _emoji = {}, {}


def font(size):
    if size not in _fonts:
        _fonts[size] = ImageFont.truetype(FONT, size)
    return _fonts[size]


def emoji_img(ch, size):
    """カラー絵文字を size px の正方形画像にする（Noto Color Emoji は 109px 固定なので拡大縮小）"""
    key = (ch, size)
    if key not in _emoji:
        f = ImageFont.truetype(EMOJI_FONT, 109)
        im = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((80, 80), ch, font=f, embedded_color=True, anchor="mm")
        im = im.crop(im.getbbox()) if im.getbbox() else im
        s = size / max(im.size)
        _emoji[key] = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    return _emoji[key]


def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def ease_out_back(t):
    t = min(max(t, 0.0), 1.0)
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


def ease_out(t):
    t = min(max(t, 0.0), 1.0)
    return 1 - (1 - t) ** 3


def background(accent, t):
    """やわらかいグラデーションの上を、薄い丸がゆっくり流れる"""
    a = np.array(hex2rgb(accent), dtype=np.float32)
    base = np.array([255, 248, 240], dtype=np.float32)
    y = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    mix = 0.10 + 0.08 * (0.5 + 0.5 * np.sin(2 * math.pi * (y + t * 0.08)))
    rows = base * (1 - mix) + a * mix
    img = Image.fromarray(np.repeat(rows[:, None, :], W, axis=1).reshape(H, W, 3).astype(np.uint8))
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for i in range(6):
        r = 90 + 40 * (i % 3)
        cx = (i * 211 + t * (30 + i * 8)) % (W + 2 * r) - r
        cy = (i * 337 + t * (18 + i * 5)) % (H + 2 * r) - r
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=tuple(a.astype(int).tolist()) + (28,))
    img = img.convert("RGBA")
    img.alpha_composite(ov)
    return img


def text_center(d, y, text, size, color, max_w=940):
    fnt = font(size)
    lines, line = [], ""
    for ch in text:
        if d.textlength(line + ch, font=fnt) > max_w and line:
            lines.append(line)
            line = ch
        else:
            line += ch
    lines.append(line)
    for ln in lines:
        w = d.textlength(ln, font=fnt)
        d.text(((W - w) / 2, y), ln, font=fnt, fill=color)
        y += int(size * 1.35)
    return y


def fit(text, size, min_size, max_w=940):
    """1行に収まるまで文字を小さくする（min_size より小さくはしない。収まらなければ折り返す）"""
    d = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    while size > min_size and d.textlength(text, font=font(size)) > max_w:
        size -= 2
    return size


def text_layer(text, size, color, max_w=940):
    """折り返し込みで文字を描き、使った高さで切り抜いた透明画像を返す"""
    size = fit(text, size, int(size * 0.65), max_w)
    layer = Image.new("RGBA", (W, size * 6), (0, 0, 0, 0))
    y = text_center(ImageDraw.Draw(layer), 10, text, size, color, max_w)
    return layer.crop((0, 0, W, int(y + size * 0.1)))


def paste_center(img, im, cx, cy, scale=1.0, angle=0.0, alpha=1.0):
    if scale <= 0.01 or alpha <= 0.01:
        return
    im2 = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.LANCZOS)
    if angle:
        im2 = im2.rotate(angle, resample=Image.BICUBIC, expand=True)
    if alpha < 1:
        a = im2.getchannel("A").point(lambda v: int(v * alpha))
        im2.putalpha(a)
    img.alpha_composite(im2, (int(cx - im2.width / 2), int(cy - im2.height / 2)))


def draw_frame(spec, kind, idx, lt, gt, n_items, credit):
    """kind: hook / item / cta。lt はその場面の中の経過秒、gt は動画全体の経過秒"""
    acc = spec["accent"]
    img = background(acc, gt)
    d = ImageDraw.Draw(img)
    if spec.get("pr", True):
        d.text((60, 70), "#PR", font=font(40), fill=MUTED)
    em = spec.get("emoji", {})
    bob = math.sin(gt * 2.2) * 14
    if kind == "hook":
        s = ease_out_back(lt / 0.6)
        paste_center(img, emoji_img(em.get("hook", "✨"), 360), W / 2, 560 + bob, s, math.sin(gt * 1.5) * 4)
        y = 860
        for i, ln in enumerate(spec["hook"]):
            layer = text_layer(ln, 96, FG)
            p = ease_out((lt - 0.15 - i * 0.18) / 0.35)
            if p > 0:
                paste_center(img, layer, W / 2, y + layer.height / 2 + (1 - p) * 60, 1.0, 0, p)
            y += layer.height
        p = ease_out((lt - 0.8) / 0.4)
        if p > 0:
            layer = text_layer(spec["sub"], 46, MUTED)
            paste_center(img, layer, W / 2, y + 30 + layer.height / 2, 1.0, 0, p)
    elif kind == "item":
        it = idx
        # 「コツ1」が左からすべり込む
        p = ease_out(lt / 0.45)
        lab = Image.new("RGBA", (W, 260), (0, 0, 0, 0))
        ImageDraw.Draw(lab).text((W / 2, 130), it["label"], font=font(200), fill=acc, anchor="mm")
        paste_center(img, lab, W / 2 - (1 - p) * W, 360)
        # 絵文字がポンと出て、ゆらゆら
        s = ease_out_back((lt - 0.2) / 0.5)
        paste_center(img, emoji_img(em.get("items", {}).get(str(it["rank"]), "✅"), 300), W / 2, 780 + bob, s,
                     math.sin(gt * 3) * 6)
        # 文字が下から出る
        p2 = ease_out((lt - 0.45) / 0.4)
        if p2 > 0:
            layer = Image.new("RGBA", (W, 520), (0, 0, 0, 0))
            dd = ImageDraw.Draw(layer)
            y = text_center(dd, 10, it["name"], fit(it["name"], 74, 52), FG)
            y = text_center(dd, y + 14, it.get("note", ""), fit(it.get("note", ""), 46, 34), MUTED)
            layer = layer.crop((0, 0, W, int(y + 10)))
            paste_center(img, layer, W / 2, 1060 + layer.height / 2 + (1 - p2) * 70, 1.0, 0, p2)
        # 進み具合のバー
        k = n_items - it["rank"] + 1
        bw = 600
        x0 = (W - bw) / 2
        d.rounded_rectangle([x0, 1560, x0 + bw, 1580], radius=10, fill=(225, 220, 215))
        prog = (k - 1 + ease_out(lt / 0.8)) / n_items
        d.rounded_rectangle([x0, 1560, x0 + bw * prog, 1580], radius=10, fill=acc)
        d.text((W / 2, 1625), f"{k} / {n_items}", font=font(36), fill=MUTED, anchor="mm")
    else:
        pulse = 1 + 0.06 * math.sin(gt * 6)
        s = ease_out_back(lt / 0.5) * pulse
        paste_center(img, emoji_img(em.get("cta", "🔖"), 300), W / 2, 620, s)
        y = 880
        for i, ln in enumerate(spec["cta"]):
            layer = text_layer(ln, 80, FG)
            p = ease_out((lt - 0.2 - i * 0.15) / 0.35)
            if p > 0:
                paste_center(img, layer, W / 2, y + layer.height / 2 + (1 - p) * 40, 1.0, 0, p)
            y += layer.height
        if spec.get("foot"):
            text_center(d, y + 40, spec["foot"], 40, MUTED)
        if credit:
            d.text((W / 2, H - 90), credit, font=font(30), fill=MUTED, anchor="mm")
    d.rectangle([0, 0, W, 18], fill=acc)
    d.rectangle([0, H - 18, W, H], fill=acc)
    return img.convert("RGB")


def main(spec_path, out_path):
    spec = json.loads(Path(spec_path).read_text())
    slots = json.loads((Path(__file__).parent / "rotation.json").read_text())["slots"]
    slot = slots[spec["slot"] % len(slots)]
    say = spec["say"]
    credit = f"VOICEVOX:{slot['voice']}" if slot["voice"] else ""
    items = sorted(spec["items"], key=lambda x: -x["rank"])
    scenes = [("hook", None, say["hook"])] + [("item", it, say["items"][str(it["rank"])]) for it in items]
    scenes.append(("cta", None, say["cta"]))

    if slot["speaker"] is None:
        durs = [3.0] * (len(scenes) - 1) + [3.5]
        voice = np.zeros(int(SR * sum(durs)))
    else:
        parts, durs = [], []
        for _, _, text in scenes:
            seg = np.concatenate([np.zeros(int(SR * 0.15)), speak(text, slot["speaker"]), np.zeros(int(SR * 0.35))])
            parts.append(seg)
            durs.append(len(seg) / SR)
        durs[-1] += 1.0
        parts.append(np.zeros(SR))
        voice = np.concatenate(parts)
    total = len(voice) / SR
    bgm = make_bgm.make(total, slot["music"], spec["slot"] * 7 + 3)
    bgm = resample(bgm, make_bgm.SR, SR)[: len(voice)]
    level = 0.22 if slot["speaker"] is not None else 0.8
    mix = voice + level * np.pad(bgm, (0, len(voice) - len(bgm)))
    mix = mix / max(1.0, np.max(np.abs(mix)))

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    with tempfile.TemporaryDirectory() as tmp:
        wav = str(Path(tmp) / "audio.wav")
        make_bgm.write_wav(wav, mix, SR)
        proc = subprocess.Popen([
            ffmpeg, "-y", "-loglevel", "error",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
            "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out_path,
        ], stdin=subprocess.PIPE)
        starts = np.cumsum([0] + durs[:-1])
        n_frames = int(total * FPS)
        first = None
        for f in range(n_frames):
            gt = f / FPS
            i = int(np.searchsorted(starts, gt, side="right") - 1)
            kind, it, _ = scenes[i]
            fr = draw_frame(spec, kind, it, gt - starts[i], gt, len(items), credit)
            if f == int(1.2 * FPS):
                first = fr
            proc.stdin.write(fr.tobytes())
        proc.stdin.close()
        proc.wait()
        (first or fr).save(Path(out_path).with_suffix(".jpg"), quality=90)
    print(f"{out_path}: slot {spec['slot']} {slot['voice'] or '声なし'} / {slot['music']} / {total:.1f}s")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
