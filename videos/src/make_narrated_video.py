"""ナレーション（VOICEVOX）＋BGMつきの縦型ランキング動画を作る。

使い方: python3 make_narrated_video.py <spec.json> <out.mp4>
spec.json は make_ranking_video.py と同じ形に、次を足す:
  "slot": 整数  rotation.json の何番目の声・曲を使うか（動画ごとに1つずつ進める）
  "say": {"hook": "..", "items": {"3": "..", ...}, "cta": ".."}  読み上げる文（英字はカタカナで書く）
声は VOICEVOX エンジン（localhost:50021）で作る。起動方法:
  dockerd &  →  docker run -d --rm -p 50021:50021 voicevox/voicevox_engine:cpu-latest
声のある回は最後の画面に「VOICEVOX:名前」を入れる（利用規約の表記）。
"""
import io
import json
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
import wave
from pathlib import Path

import imageio_ffmpeg
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import make_bgm  # noqa: E402
from make_ranking_video import FG, FPS, MUTED, base, draw_block, font, frame_hook, frame_item  # noqa: E402

SR = 24000
ENGINE = "http://localhost:50021"
_open = urllib.request.build_opener(urllib.request.ProxyHandler({})).open


def speak(text, speaker):
    q = json.loads(_open(urllib.request.Request(
        f"{ENGINE}/audio_query?text={urllib.parse.quote(text)}&speaker={speaker}", method="POST")).read())
    q.update(speedScale=1.1, intonationScale=1.15, outputSamplingRate=SR, outputStereo=False)
    wav = _open(urllib.request.Request(
        f"{ENGINE}/synthesis?speaker={speaker}", data=json.dumps(q).encode(),
        headers={"Content-Type": "application/json"})).read()
    with wave.open(io.BytesIO(wav)) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768
    return x / np.max(np.abs(x)) * 0.9


def resample(x, src, dst):
    n = int(len(x) * dst / src)
    return np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x)


def frame_cta(spec, credit):
    img, d = base(spec["accent"])
    draw_block(d, [(t, 76, FG) for t in spec["cta"]] + [(spec.get("foot", ""), 40, MUTED)], 700)
    if credit:
        fnt = font(30)
        w = d.textlength(credit, font=fnt)
        d.text(((1080 - w) / 2, 1920 - 90), credit, font=fnt, fill=MUTED)
    return img


def main(spec_path, out_path):
    spec = json.loads(Path(spec_path).read_text())
    slots = json.loads((Path(__file__).parent / "rotation.json").read_text())["slots"]
    slot = slots[spec["slot"] % len(slots)]
    say = spec["say"]
    credit = f"VOICEVOX:{slot['voice']}" if slot["voice"] else ""

    items = sorted(spec["items"], key=lambda x: -x["rank"])
    slides = [(frame_hook(spec), say["hook"])]
    slides += [(frame_item(spec, it), say["items"][str(it["rank"])]) for it in items]
    slides.append((frame_cta(spec, credit), say["cta"]))

    if slot["speaker"] is None:
        durs = [3.0] * (len(slides) - 1) + [3.5]
        voice = np.zeros(int(SR * sum(durs)))
    else:
        parts, durs = [], []
        for _, text in slides:
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
    print(f"{out_path}: slot {spec['slot']} {slot['voice'] or '声なし'} / {slot['music']} / {total:.1f}s")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
