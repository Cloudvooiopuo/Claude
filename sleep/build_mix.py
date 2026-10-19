"""曲（オーディオライブラリー）と自作の自然音を重ねて、長い1本の音（wav）を作る。

使い方: python3 build_mix.py <out.wav> <分> <曲1.mp3> [曲2.mp3 ...]
- 曲は順番に流し、曲と曲の間に20〜40秒の「自然音だけ」の時間を入れる（くり返しが目立たないように）
- 自然音（環境変数 AMB=sunny/waves/rain/night/fire/city、既定は sunny＝そよ風・小鳥）は10分ごとに違う番号で作ってつなぐので、同じ音のくり返しにならない
- 最後の10分は少しずつ小さくする
"""
import os
import subprocess
import sys
import wave

import imageio_ffmpeg
import numpy as np

import make_sleep_audio as m

SR = m.SR


def load(path):
    raw = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-loglevel", "error", "-i", path,
                          "-f", "s16le", "-ac", "2", "-ar", str(SR), "-"], capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.int16).reshape(-1, 2).astype(np.float32) / 32768
    return x / (np.sqrt(np.mean(x ** 2)) + 1e-9)


AMB = os.environ.get("AMB", "sunny")


def ambience(sec, seed):
    rng = np.random.default_rng(seed)
    n = int(sec * SR)
    if AMB == "waves":
        a = 0.8 * m.waves(n, rng) + 0.2 * m.wind(n, rng)
    elif AMB == "night":
        a = 0.7 * m.wind(n, rng) + 0.3 * m.brown(n, rng)
    elif AMB == "city":
        a = 0.75 * m.city(n, rng) + 0.25 * m.wind(n, rng)
    elif AMB == "fire":
        a = 0.85 * m.fire(n, rng) + 0.15 * m.brown(n, rng)
    elif AMB == "rain":
        a = m.rain(n, rng)
    else:
        a = 0.6 * m.wind(n, rng) + 0.25 * m.birds(n, rng)
    a = a / (np.sqrt(np.mean(a ** 2)) + 1e-9)
    return np.stack([a, np.roll(a, 331)], 1).astype(np.float32)


def main(out, minutes, songs):
    total = int(float(minutes) * 60 * SR)
    tracks = [load(s) for s in songs]
    rng = np.random.default_rng(len(songs) * 101 + int(float(minutes)))
    w = wave.open(out, "wb")
    w.setnchannels(2), w.setsampwidth(2), w.setframerate(SR)
    chunk = 600 * SR
    music = np.zeros((0, 2), np.float32)
    i = 0
    pos = 0
    seed = 1
    while pos < total:
        n = min(chunk, total - pos)
        amb = ambience(n / SR, seed)
        seed += 1
        # この区間に足りるだけ曲を並べる（曲の間に自然音だけの時間）
        while len(music) < n:
            gap = np.zeros((int(rng.uniform(20, 40) * SR), 2), np.float32)
            t = tracks[i % len(tracks)]
            i += 1
            fade = np.minimum(1, np.minimum(np.arange(len(t)), np.arange(len(t))[::-1]) / (3 * SR))[:, None]
            music = np.concatenate([music, gap, t * fade])
        seg, music = music[:n], music[n:]
        mix = 0.12 * seg + float(os.environ.get("AMBGAIN", "0.05")) * amb
        # 区間のつなぎ目は自然音同士をなめらかに（先頭0.5秒）
        t0 = np.arange(n) + pos
        fade_out = np.clip((total - t0) / (600 * SR), 0, 1)[:, None]
        fade_in = np.clip(t0 / (10 * SR), 0, 1)[:, None]
        mix = mix * fade_out * fade_in
        w.writeframes((np.tanh(mix * 1.2) * 32767).astype(np.int16).tobytes())
        pos += n
        print(f"{pos / SR / 60:.0f}/{float(minutes):.0f} min", flush=True)
    w.close()


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3:])
