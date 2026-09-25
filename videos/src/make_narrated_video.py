"""ナレーション（AI音声）＋BGMつきの縦型ランキング動画を作る。

使い方: python3 make_narrated_video.py <spec.json> <out.mp4>
spec.json は make_ranking_video.py と同じ形に、次を足す:
  "say": {"hook": "..", "items": {"3": "..", ...}, "cta": ".."}  読み上げる文（英字はカタカナで書く）
  "music": {"style": "calm" | "pop", "seed": 整数}  動画ごとに変えると毎回違う曲になる
音声: HTS Voice "Mei"（名古屋工業大学, CC BY 3.0）。動画の最後の画面に表記を入れる。
"""
import json
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

import imageio_ffmpeg
import numpy as np
import pyopenjtalk
from pyopenjtalk.htsengine import HTSEngine

sys.path.insert(0, str(Path(__file__).parent))
import make_bgm  # noqa: E402
from make_ranking_video import FPS, MUTED, base, draw_block, font, frame_hook, frame_item, FG  # noqa: E402

SR = 48000
VOICE_ZIP = "https://downloads.sourceforge.net/project/mmdagent/MMDAgent_Example/MMDAgent_Example-1.8/MMDAgent_Example-1.8.zip"
VOICE_DIR = Path.home() / ".cache" / "mei_voice"
CREDIT = "音声：HTS Voice Mei（名古屋工業大学 CC BY 3.0）"


def voice_path(mood="happy"):
    path = VOICE_DIR / f"mei_{mood}.htsvoice"
    if not path.exists():
        VOICE_DIR.mkdir(parents=True, exist_ok=True)
        z = VOICE_DIR / "mmd.zip"
        urllib.request.urlretrieve(VOICE_ZIP, z)
        with zipfile.ZipFile(z) as zf:
            for name in zf.namelist():
                if name.startswith("MMDAgent_Example-1.8/Voice/mei/") and name.endswith(".htsvoice"):
                    (VOICE_DIR / Path(name).name).write_bytes(zf.read(name))
        z.unlink()
    return path


def speak(engine, text):
    x = engine.synthesize(pyopenjtalk.extract_fullcontext(text))
    return x / np.max(np.abs(x)) * 0.9


def resample(x, src, dst):
    n = int(len(x) * dst / src)
    return np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x)


def frame_cta(spec):
    img, d = base(spec["accent"])
    draw_block(d, [(t, 76, FG) for t in spec["cta"]] + [(spec.get("foot", ""), 40, MUTED)], 700)
    fnt = font(28)
    w = d.textlength(CREDIT, font=fnt)
    d.text(((1080 - w) / 2, 1920 - 90), CREDIT, font=fnt, fill=MUTED)
    return img


def main(spec_path, out_path):
    spec = json.loads(Path(spec_path).read_text())
    say = spec["say"]
    engine = HTSEngine(str(voice_path()).encode())
    engine.set_speed(1.15)

    items = sorted(spec["items"], key=lambda x: -x["rank"])
    slides = [(frame_hook(spec), say["hook"])]
    slides += [(frame_item(spec, it), say["items"][str(it["rank"])]) for it in items]
    slides.append((frame_cta(spec), say["cta"]))

    gap = 0.35
    voice, durs = [], []
    for _, text in slides:
        v = speak(engine, text)
        seg = np.concatenate([np.zeros(int(SR * 0.15)), v, np.zeros(int(SR * gap))])
        voice.append(seg)
        durs.append(len(seg) / SR)
    durs[-1] += 1.0
    voice.append(np.zeros(int(SR * 1.0)))
    voice = np.concatenate(voice)
    total = len(voice) / SR

    music = spec.get("music", {})
    bgm = make_bgm.make(total, music.get("style", "calm"), music.get("seed", 0))
    bgm = resample(bgm, make_bgm.SR, SR)[: len(voice)]
    mix = voice + 0.22 * np.pad(bgm, (0, len(voice) - len(bgm)))
    mix = mix / max(1.0, np.max(np.abs(mix)))

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    with tempfile.TemporaryDirectory() as tmp:
        wav = str(Path(tmp) / "audio.wav")
        make_bgm.write_wav(wav, mix, SR)
        lst = Path(tmp) / "list.txt"
        entries = []
        for i, ((img, _), dur) in enumerate(zip(slides, durs)):
            p = Path(tmp) / f"f{i}.png"
            img.save(p)
            entries.append(f"file '{p}'\nduration {dur:.3f}")
        entries.append(f"file '{Path(tmp) / f'f{len(slides) - 1}.png'}'")
        lst.write_text("\n".join(entries) + "\n")
        subprocess.run([
            ffmpeg, "-y", "-loglevel", "error",
            "-f", "concat", "-safe", "0", "-i", str(lst),
            "-i", wav,
            "-vf", f"fps={FPS},format=yuv420p",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart",
            out_path,
        ], check=True)
        slides[0][0].save(Path(out_path).with_suffix(".jpg"), quality=90)
    print(f"{out_path}: {total:.1f}s")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
