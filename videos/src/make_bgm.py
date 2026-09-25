"""著作権の心配がないオリジナルのBGM（やわらかいコード進行＋軽いリズム）を作る。

使い方: python3 make_bgm.py <out.wav> [秒数]
"""
import sys
import wave

import numpy as np

SR = 44100
BPM = 96


def note(freq, dur, amp=0.2):
    t = np.arange(int(SR * dur)) / SR
    tone = np.sin(2 * np.pi * freq * t) + 0.3 * np.sin(4 * np.pi * freq * t)
    env = np.minimum(1, t / 0.02) * np.exp(-t * 2.5)
    return amp * tone * env


def kick(dur):
    t = np.arange(int(SR * dur)) / SR
    return 0.5 * np.sin(2 * np.pi * (110 * np.exp(-t * 20) + 45) * t) * np.exp(-t * 12)


def hat(dur):
    t = np.arange(int(SR * dur)) / SR
    return 0.05 * np.random.default_rng(0).standard_normal(len(t)) * np.exp(-t * 60)


def hz(midi):
    return 440 * 2 ** ((midi - 69) / 12)


def main(out, seconds=15.0):
    beat = 60 / BPM
    n = int(SR * seconds)
    mix = np.zeros(n + SR)
    # C - Am - F - G（明るく落ち着いた進行）
    chords = [[60, 64, 67], [57, 60, 64], [53, 57, 60], [55, 59, 62]]
    melody = [72, 71, 69, 67, 69, 72, 74, 72]
    pos, i = 0, 0
    while pos < n:
        chord = chords[(i // 4) % 4]
        start = pos
        for m in chord:
            seg = note(hz(m), beat * 1.5, 0.08)
            mix[start:start + len(seg)] += seg
        seg = note(hz(chord[0] - 12), beat, 0.12)
        mix[start:start + len(seg)] += seg
        if i % 2 == 0:
            seg = note(hz(melody[(i // 2) % len(melody)]), beat, 0.07)
            mix[start:start + len(seg)] += seg
        seg = kick(0.3) if i % 2 == 0 else hat(0.1)
        mix[start:start + len(seg)] += seg
        half = start + int(SR * beat / 2)
        seg = hat(0.08)
        mix[half:half + len(seg)] += seg
        pos += int(SR * beat)
        i += 1
    mix = mix[:n]
    fade = int(SR * 1.0)
    mix[:int(SR * 0.3)] *= np.linspace(0, 1, int(SR * 0.3))
    mix[-fade:] *= np.linspace(1, 0, fade)
    mix = mix / np.max(np.abs(mix)) * 0.5
    data = (mix * 32767).astype(np.int16)
    with wave.open(out, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())


if __name__ == "__main__":
    main(sys.argv[1], float(sys.argv[2]) if len(sys.argv) > 2 else 15.0)
