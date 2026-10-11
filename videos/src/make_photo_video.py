"""写真が動く背景の縦型動画（1080x1920）を作る。場面ごとに CC0・パブリックドメインの写真を
ゆっくり寄せながら流し（ケン・バーンズ）、下に字幕、声は VOICEVOX、BGM は make_bgm.py。

使い方: python3 make_photo_video.py <spec.json> <out.mp4>
spec.json は videos/src/motion/*.json と同じ形に、次を足す:
  "photos": {"hook": "photos/w6/xxx.jpg", "items": {"3": "...", "2": "...", "1": "..."}, "cta": "..."}
     （"photos/w6/xxx.jpg#0.3" で横のどこを見せるかを指定できる）
  "photo_note": true  … 商品紹介の回。実物ではない似た写真なので、画面に「※写真はイメージです」を出す
写真のパスはリポジトリの一番上からの相対パス。出典は photos/credits.json。
"""
import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
import make_bgm  # noqa: E402
from make_narrated_video import SR, resample, speak  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
W, H, FPS = 1080, 1920, 30
FONT = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
FADE = 0.4  # 場面の切り替えの重ね時間（秒）
_fonts = {}


def font(size):
    if size not in _fonts:
        _fonts[size] = ImageFont.truetype(FONT, size)
    return _fonts[size]


def ease_out(t):
    t = min(max(t, 0.0), 1.0)
    return 1 - (1 - t) ** 3


def cover(path, scale=1.18):
    """画面より少し大きく切り抜いておく（寄り・横移動の余白）。
    "photos/x.jpg#0.3" のように # の後に 0〜1 を書くと、横長の写真のどこを見せるか（左0・右1）を決められる"""
    path, _, fx = path.partition("#")
    im = Image.open(ROOT / path).convert("RGB")
    tw, th = int(W * scale), int(H * scale)
    s = max(tw / im.width, th / im.height)
    im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)
    x, y = int((im.width - tw) * float(fx or 0.5)), (im.height - th) // 2
    return im.crop((x, y, x + tw, y + th))


def kenburns(base, p, k):
    """p=0→1 で少しずつ寄る。k で寄る向き（場面ごとに変える）"""
    z = 1.0 + 0.12 * p
    cw, ch = base.width / (1.18 / 1.0) / z * 1.0, base.height / 1.18 / z
    dx = (base.width - cw) * (0.5 + 0.35 * math.cos(k * 2.1) * (p - 0.5))
    dy = (base.height - ch) * (0.5 + 0.35 * math.sin(k * 1.7) * (p - 0.5))
    return base.resize((W, H), Image.BILINEAR, box=(dx, dy, dx + cw, dy + ch))


def shade():
    """字幕を読みやすくする下の暗いグラデーションと、上の薄い影"""
    a = np.zeros((H, 1), dtype=np.float32)
    y = np.arange(H, dtype=np.float32)
    a[:, 0] = np.clip((y - H * 0.42) / (H * 0.5), 0, 1) ** 1.3 * 200 + np.clip((260 - y) / 260, 0, 1) * 90
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    img.putalpha(Image.fromarray(np.repeat(a, W, axis=1).astype(np.uint8)))
    return img


def fit(text, size, min_size, max_w=960):
    d = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    while size > min_size and d.textlength(text, font=font(size)) > max_w:
        size -= 2
    return size


def text_layer(text, size, color="white", max_w=960, stroke=None):
    """白い文字に黒いふち。収まらなければ小さくし、それでも長ければ折り返す"""
    size = fit(text, size, int(size * 0.65), max_w)
    fnt = font(size)
    d = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    lines, line = [], ""
    for ch in text:
        if d.textlength(line + ch, font=fnt) > max_w and line:
            lines.append(line)
            line = ch
        else:
            line += ch
    lines.append(line)
    sw = stroke if stroke is not None else max(3, size // 14)
    lh = int(size * 1.3)
    layer = Image.new("RGBA", (W, lh * len(lines) + 20), (0, 0, 0, 0))
    dd = ImageDraw.Draw(layer)
    for i, ln in enumerate(lines):
        dd.text((W / 2, 10 + i * lh), ln, font=fnt, fill=color, anchor="ma", stroke_width=sw, stroke_fill=(20, 20, 20))
    soft = layer.filter(ImageFilter.GaussianBlur(6))
    out = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    out.alpha_composite(Image.merge("RGBA", (*Image.new("RGB", layer.size, (0, 0, 0)).split(),
                                             soft.getchannel("A").point(lambda v: v * 0.6))), (0, 6))
    out.alpha_composite(layer)
    return out


def pill(text, size, fill):
    fnt = font(size)
    tw = ImageDraw.Draw(Image.new("RGB", (1, 1))).textlength(text, font=fnt)
    im = Image.new("RGBA", (int(tw + size * 1.2), int(size * 1.6)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, im.width - 1, im.height - 1], radius=im.height // 2, fill=fill)
    d.text((im.width / 2, im.height / 2), text, font=fnt, fill="white", anchor="mm")
    return im


def put(img, im, cx, top, alpha=1.0, dy=0.0):
    if alpha <= 0.01:
        return
    if alpha < 1:
        im = im.copy()
        im.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
    img.alpha_composite(im, (int(cx - im.width / 2), int(top + dy)))


class Scene:
    def __init__(self, kind, item, photo, k):
        self.kind, self.item, self.base, self.k = kind, item, cover(photo), k
        self.layers = None


def build_layers(spec, sc, n_items, credit):
    acc = spec["accent"]
    if sc.kind == "hook":
        hook = [text_layer(ln, 104) for ln in spec["hook"]]
        return {"hook": hook, "sub": text_layer(spec["sub"], 46, color="#F2F2F2")}
    if sc.kind == "item":
        it = sc.item
        return {"label": pill(it["label"], 64, acc), "name": text_layer(it["name"], 84),
                "note": text_layer(it.get("note", ""), 48, color="#F2F2F2") if it.get("note") else None}
    lines = [text_layer(ln, 82) for ln in spec["cta"]]
    return {"cta": lines, "foot": text_layer(spec["foot"], 38, color="#EEEEEE") if spec.get("foot") else None,
            "credit": text_layer(credit, 30, color="#DDDDDD", stroke=2) if credit else None}


def draw_scene(spec, sc, lt, dur, gt, n_items, shade_img, marks):
    img = kenburns(sc.base, min(lt / max(dur, 0.1), 1.0), sc.k).convert("RGBA")
    img.alpha_composite(shade_img)
    L = sc.layers
    if sc.kind == "hook":
        y = 1080
        for i, layer in enumerate(L["hook"]):
            p = ease_out((lt - 0.1 - i * 0.18) / 0.4)
            put(img, layer, W / 2, y, p, (1 - p) * 60)
            y += layer.height - 6
        p = ease_out((lt - 0.7) / 0.4)
        put(img, L["sub"], W / 2, y + 30, p)
    elif sc.kind == "item":
        p = ease_out(lt / 0.45)
        put(img, L["label"], W / 2 - (1 - p) * W, 1150)
        p2 = ease_out((lt - 0.3) / 0.4)
        y = 1150 + L["label"].height + 30
        put(img, L["name"], W / 2, y, p2, (1 - p2) * 60)
        if L["note"]:
            put(img, L["note"], W / 2, y + L["name"].height + 10, ease_out((lt - 0.55) / 0.4))
        k = n_items - sc.item["rank"] + 1
        d = ImageDraw.Draw(img)
        bw, x0 = 600, (W - 600) / 2
        d.rounded_rectangle([x0, 1720, x0 + bw, 1736], radius=8, fill=(255, 255, 255, 110))
        d.rounded_rectangle([x0, 1720, x0 + bw * (k - 1 + ease_out(lt / 0.8)) / n_items, 1736], radius=8,
                            fill=spec["accent"])
        d.text((W / 2, 1775), f"{k} / {n_items}", font=font(34), fill="white", anchor="mm",
               stroke_width=2, stroke_fill=(20, 20, 20))
    else:
        y = 1040
        for i, layer in enumerate(L["cta"]):
            p = ease_out((lt - 0.15 - i * 0.15) / 0.35)
            put(img, layer, W / 2, y, p, (1 - p) * 40)
            y += layer.height - 4
        if L["foot"]:
            put(img, L["foot"], W / 2, y + 30)
        if L["credit"]:
            put(img, L["credit"], W / 2, H - 120)
    for m in marks:
        img.alpha_composite(m[0], m[1])
    return img


def main(spec_path, out_path):
    spec = json.loads(Path(spec_path).read_text())
    slots = json.loads((Path(__file__).parent / "rotation.json").read_text())["slots"]
    slot = slots[spec["slot"] % len(slots)]
    say = spec["say"]
    credit = f"VOICEVOX:{slot['voice']}" if slot["voice"] else ""
    ph = spec["photos"]
    items = sorted(spec["items"], key=lambda x: -x["rank"])
    scenes = [Scene("hook", None, ph["hook"], 0)]
    scenes += [Scene("item", it, ph["items"][str(it["rank"])], i + 1) for i, it in enumerate(items)]
    scenes.append(Scene("cta", None, ph["cta"], 5))
    texts = [say["hook"]] + [say["items"][str(it["rank"])] for it in items] + [say["cta"]]
    for sc in scenes:
        sc.layers = build_layers(spec, sc, len(items), credit)

    if slot["speaker"] is None:
        durs = [3.0] * (len(scenes) - 1) + [3.5]
        voice = np.zeros(int(SR * sum(durs)))
    else:
        parts, durs = [], []
        for text in texts:
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

    # 画面の隅にずっと出す表示（#PR・写真はイメージ）
    marks = []
    if spec.get("pr", True):
        marks.append((pill("#PR", 36, (30, 30, 30, 170)), (50, 60)))
    if spec.get("photo_note"):
        note = pill("※写真はイメージです", 30, (30, 30, 30, 150))
        marks.append((note, (W - note.width - 50, 64)))
    shade_img = shade()

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
        first = None
        for f in range(int(total * FPS)):
            gt = f / FPS
            i = int(np.searchsorted(starts, gt, side="right") - 1)
            fr = draw_scene(spec, scenes[i], gt - starts[i], durs[i] + FADE, gt, len(items), shade_img, marks)
            # 次の場面へ写真を重ねて切り替える
            if i + 1 < len(scenes) and gt > starts[i + 1] - FADE:
                a = (gt - (starts[i + 1] - FADE)) / FADE
                nxt = kenburns(scenes[i + 1].base, 0.0, scenes[i + 1].k).convert("RGBA")
                nxt.alpha_composite(shade_img)
                for m in marks:
                    nxt.alpha_composite(m[0], m[1])
                fr = Image.blend(fr, nxt, a)
            fr = fr.convert("RGB")
            if f == int(1.5 * FPS):
                first = fr
            proc.stdin.write(fr.tobytes())
        proc.stdin.close()
        proc.wait()
        (first or fr).save(Path(out_path).with_suffix(".jpg"), quality=90)
    print(f"{out_path}: slot {spec['slot']} {slot['voice'] or '声なし'} / {slot['music']} / {total:.1f}s")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
