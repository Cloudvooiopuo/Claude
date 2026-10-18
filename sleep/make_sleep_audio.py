"""睡眠用のオリジナル音（著作権の心配がない）を作る。継ぎ目なしでループできる1本を書き出す。

使い方: python3 make_sleep_audio.py <out.wav> [秒数=600] [type=rain_pad] [seed=1]
type:
  rain_pad   … 雨音＋ゆっくり動くやわらかい和音
  rain       … 雨音だけ
  brown      … ブラウンノイズ（低いザーという音）
  pad        … 和音だけ（ゆっくり、打楽器なし）
  waves      … 波の音（ゆっくり寄せて返す）＋和音
  sunny      … 晴れ：遠くの鳥のさえずり＋そよ風＋明るい和音
"""
import sys
import wave

import numpy as np
from scipy.signal import lfilter

SR = 44100


def brown(n, rng):
    x = np.cumsum(rng.standard_normal(n))
    # ゆっくり流れないように、ゆるく中央へ戻す
    x -= np.convolve(x, np.ones(SR) / SR, mode="same")
    return x / (np.abs(x).max() + 1e-9)


def lowpass(x, a):
    # 1次のローパス（a が小さいほど丸い音）
    return lfilter([a], [1, a - 1], x)


def rain(n, rng):
    w = rng.standard_normal(n)
    hiss = lowpass(w, 0.25) - lowpass(w, 0.02)          # サーという雨の地
    drops = np.zeros(n)
    k = rng.integers(0, n, n // 900)                      # ぽつぽつ
    drops[k] = rng.uniform(0.3, 1.0, len(k)) * rng.choice([-1, 1], len(k))
    drops = lowpass(drops, 0.35)
    body = lowpass(w, 0.004)                              # 遠くの低い雨
    x = 0.55 * hiss + 0.25 * drops + 0.9 * body / (np.abs(body).max() + 1e-9) * 0.3
    return x / (np.abs(x).max() + 1e-9)


def hz(m):
    return 440 * 2 ** ((m - 69) / 12)


def pad(n, rng):
    t = np.arange(n) / SR
    roots = [48, 45, 41, 43]                              # C Am F G（低め）
    seg = 20.0                                            # 1つの和音を20秒
    out = np.zeros(n)
    for i, r in enumerate(roots * int(np.ceil(n / SR / seg / 4) + 1)):
        s, e = int(i * seg * SR), int((i + 1.5) * seg * SR)
        if s >= n:
            break
        e = min(e, n)
        tt = t[s:e] - t[s]
        env = np.sin(np.pi * np.clip(tt / (seg * 1.5), 0, 1)) ** 2
        chord = [r, r + 7, r + 12, r + 16] if i % 2 == 0 else [r, r + 3 + 4, r + 12, r + 15]
        sig = sum(np.sin(2 * np.pi * hz(m) * tt * (1 + 0.0007 * j)) / (1 + j * 0.6) for j, m in enumerate(chord))
        out[s:e] += env * sig
    lfo = 0.85 + 0.15 * np.sin(2 * np.pi * t / 37)
    out *= lfo
    return out / (np.abs(out).max() + 1e-9)


def waves(n, rng):
    t = np.arange(n) / SR
    w = lowpass(rng.standard_normal(n), 0.08)
    swell = (0.5 + 0.5 * np.sin(2 * np.pi * t / 9.5 + 0.6 * np.sin(2 * np.pi * t / 41))) ** 2
    x = w * swell
    return x / (np.abs(x).max() + 1e-9)


def wind(n, rng):
    t = np.arange(n) / SR
    w = lowpass(rng.standard_normal(n), 0.03)
    gust = 0.55 + 0.45 * np.sin(2 * np.pi * t / 23 + 1.3 * np.sin(2 * np.pi * t / 71))
    x = w * gust
    return x / (np.abs(x).max() + 1e-9)


def birds(n, rng):
    """遠くの小鳥。数秒おきに短いさえずり（高さが上下する音）を2〜5回。"""
    out = np.zeros(n)
    pos = int(rng.uniform(1, 4) * SR)
    while pos < n:
        base = rng.uniform(2600, 4200)
        for _ in range(rng.integers(2, 6)):
            if pos >= n:
                break
            d = rng.uniform(0.06, 0.16)
            tt = np.arange(int(d * SR)) / SR
            sweep = base * (1 + rng.uniform(-0.25, 0.35) * tt / d)
            ph = 2 * np.pi * np.cumsum(sweep) / SR
            env = np.sin(np.pi * tt / d) ** 2
            seg = np.sin(ph + 0.4 * np.sin(2 * np.pi * 38 * tt)) * env * rng.uniform(0.3, 1.0)
            e = min(n, pos + len(seg))
            out[pos:e] += seg[: e - pos]
            pos += len(seg) + int(rng.uniform(0.04, 0.12) * SR)
        pos += int(rng.uniform(2.5, 9) * SR)
    out = lowpass(out, 0.5)                               # 遠くで鳴っている感じに丸める
    return out / (np.abs(out).max() + 1e-9)


def pad_bright(n, rng):
    t = np.arange(n) / SR
    roots = [53, 48, 50, 55]                              # F C Dm G（明るめ、少し高め）
    seg = 18.0
    out = np.zeros(n)
    for i, r in enumerate(roots * int(np.ceil(n / SR / seg / 4) + 1)):
        s, e = int(i * seg * SR), int((i + 1.5) * seg * SR)
        if s >= n:
            break
        e = min(e, n)
        tt = t[s:e] - t[s]
        env = np.sin(np.pi * np.clip(tt / (seg * 1.5), 0, 1)) ** 2
        minor = (i % 4 == 2)
        chord = [r, r + (3 if minor else 4), r + 7, r + 12, r + 14]
        sig = sum(np.sin(2 * np.pi * hz(m) * tt * (1 + 0.0006 * j)) / (1 + j * 0.7) for j, m in enumerate(chord))
        out[s:e] += env * sig
    out *= 0.85 + 0.15 * np.sin(2 * np.pi * t / 29)
    return out / (np.abs(out).max() + 1e-9)


MIX = {
    "rain_pad": [("rain", 0.55), ("pad", 0.35)],
    "rain": [("rain", 0.8)],
    "brown": [("brown", 0.7)],
    "pad": [("pad", 0.6)],
    "waves": [("waves", 0.6), ("pad", 0.25)],
    "sunny": [("pad_bright", 0.45), ("wind", 0.22), ("birds", 0.12)],
}
GEN = {"rain": rain, "brown": brown, "pad": pad, "waves": waves,
       "wind": wind, "birds": birds, "pad_bright": pad_bright}


def make(sec, kind, seed):
    rng = np.random.default_rng(seed)
    fade = 8 * SR
    n = int(sec * SR) + fade
    x = sum(g * GEN[name](n, rng) for name, g in MIX[kind])
    # 最後の8秒を最初に重ねて、ループの継ぎ目を消す
    ramp = np.linspace(0, 1, fade)
    head = x[:fade] * ramp + x[-fade:] * (1 - ramp)
    x = np.concatenate([head, x[fade:-fade]])
    x = x / (np.abs(x).max() + 1e-9) * 0.5             # 寝る時用に小さめ
    return x


def write(path, x):
    st = np.stack([x, np.roll(x, 331)], axis=1)          # ほんの少し左右に広げる
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((st * 32767).astype(np.int16).tobytes())


if __name__ == "__main__":
    out = sys.argv[1]
    sec = float(sys.argv[2]) if len(sys.argv) > 2 else 600
    kind = sys.argv[3] if len(sys.argv) > 3 else "rain_pad"
    seed = int(sys.argv[4]) if len(sys.argv) > 4 else 1
    write(out, make(sec, kind, seed))
    print("done", out, sec, kind, seed)
