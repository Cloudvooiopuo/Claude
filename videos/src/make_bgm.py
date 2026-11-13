"""著作権の心配がないオリジナルのBGMを作る。style と seed で毎回違う曲になる。

使い方: python3 make_bgm.py <out.wav> [秒数] [style] [seed]
style: calm（やわらかい）/ pop（明るくテンポが速い）
"""
import sys
import wave

import numpy as np

SR = 44100

STYLES = {
    # bpm, コード進行（ルートからの半音）, メロディの密度, キックの間隔
    "calm": {"bpm": 96, "prog": [[0, 4, 7], [-3, 0, 4], [-7, -3, 0], [-5, -1, 2]], "mel_every": 2, "kick_every": 2},
    "pop": {"bpm": 124, "prog": [[0, 4, 7], [-5, -1, 2], [-3, 0, 4], [-7, -3, 0]], "mel_every": 1, "kick_every": 1},
}
SCALE = [0, 2, 4, 7, 9, 12, 14, 16]  # ペンタトニック


def note(freq, dur, amp=0.2):
    t = np.arange(int(SR * dur)) / SR
    tone = np.sin(2 * np.pi * freq * t) + 0.3 * np.sin(4 * np.pi * freq * t)
    env = np.minimum(1, t / 0.02) * np.exp(-t * 2.5)
    return amp * tone * env


def kick(dur):
    t = np.arange(int(SR * dur)) / SR
    return 0.5 * np.sin(2 * np.pi * (110 * np.exp(-t * 20) + 45) * t) * np.exp(-t * 12)


def hat(dur, rng):
    t = np.arange(int(SR * dur)) / SR
    return 0.05 * rng.standard_normal(len(t)) * np.exp(-t * 60)


def hz(midi):
    return 440 * 2 ** ((midi - 69) / 12)


def make(seconds=15.0, style="calm", seed=0):
    st = STYLES[style]
    rng = np.random.default_rng(seed)
    key = 60 + int(rng.integers(-3, 4))
    beat = 60 / st["bpm"]
    n = int(SR * seconds)
    mix = np.zeros(n + SR)
    chords = [[key + x for x in c] for c in st["prog"]]
    melody = [key + 12 + SCALE[i] for i in rng.integers(0, len(SCALE), 16)]
    pos, i = 0, 0
    while pos < n:
        chord = chords[(i // 4) % 4]
        start = pos
        for m in chord:
            seg = note(hz(m), beat * 1.5, 0.08)
            mix[start:start + len(seg)] += seg
        seg = note(hz(chord[0] - 12), beat, 0.12)
        mix[start:start + len(seg)] += seg
        if i % st["mel_every"] == 0:
            seg = note(hz(melody[(i // st["mel_every"]) % len(melody)]), beat, 0.07)
            mix[start:start + len(seg)] += seg
        seg = kick(0.3) if i % (2 * st["kick_every"]) < st["kick_every"] else hat(0.1, rng) * 2
        mix[start:start + len(seg)] += seg
        half = start + int(SR * beat / 2)
        seg = hat(0.08, rng)
        mix[half:half + len(seg)] += seg
        pos += int(SR * beat)
        i += 1
    mix = mix[:n]
    fade = int(SR * 1.0)
    mix[:int(SR * 0.3)] *= np.linspace(0, 1, int(SR * 0.3))
    mix[-fade:] *= np.linspace(1, 0, fade)
    return mix / np.max(np.abs(mix)) * 0.5


def write_wav(out, data, sr=SR):
    pcm = (np.clip(data, -1, 1) * 32767).astype(np.int16)
    with wave.open(out, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def main(out, seconds=15.0, style="calm", seed=0):
    write_wav(out, make(seconds, style, seed))


if __name__ == "__main__":
    a = sys.argv
    main(a[1], float(a[2]) if len(a) > 2 else 15.0, a[3] if len(a) > 3 else "calm", int(a[4]) if len(a) > 4 else 0)
