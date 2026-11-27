"""18時の写真動画の spec を content.py と photos.py から作り、make_photo_video.py で動画にする。

使い方: python3 build_videos.py [日付...]   → videos/src/w10/<日付>_<key>.json と videos/w10/<日付>_<key>.mp4
slot は 64 から1本ずつ進める（videos/src/rotation.json）。
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
from content import DAYS  # noqa: E402
from photos import P  # noqa: E402

ACC = ["#5E548E", "#E76F51", "#2A9D8F", "#457B9D", "#B5838D", "#6A994E", "#D4A373"]
FIRST_SLOT = 64


def spec(i, day):
    v, ph = day["video"], P[day["d"]]
    items = [dict(rank=3 - k, label=lab, name=name, note=note) for k, (lab, name, note, _) in enumerate(v["items"])]
    return {
        "date": f"2026-11-{day['d'][2:]}", "form": "video", "kind": day["kind"], "accent": ACC[i % len(ACC)],
        "pr": day["pr"], "photo_note": day["pr"], "hook": v["hook"], "sub": v["sub"], "items": items,
        "cta": ["使う物は", "プロフィールのリンクから"] if day["pr"] else ["保存して", "後で見返してね"],
        "foot": "",
        "photos": {"hook": ph[0], "items": {"3": ph[1], "2": ph[2], "1": ph[3]}, "cta": ph[4]},
        "slot": FIRST_SLOT + i,
        "say": {"hook": "、".join(v["hook"]) + "。",
                "items": {str(3 - k): say for k, (_, _, _, say) in enumerate(v["items"])},
                "cta": "使う物は、プロフィールのリンクから。" if day["pr"] else "保存して、あとで見返してね。"},
    }


def main(dates):
    (ROOT / "videos/src/w10").mkdir(parents=True, exist_ok=True)
    (ROOT / "videos/w10").mkdir(parents=True, exist_ok=True)
    for i, day in enumerate(DAYS):
        if dates and day["d"] not in dates:
            continue
        name = f"{day['d']}_{day['key']}"
        sp = ROOT / f"videos/src/w10/{name}.json"
        sp.write_text(json.dumps(spec(i, day), ensure_ascii=False, indent=2))
        out = ROOT / f"videos/w10/{name}.mp4"
        r = subprocess.run([sys.executable, str(ROOT / "videos/src/make_photo_video.py"), str(sp), str(out)],
                           capture_output=True, text=True, cwd=ROOT)
        print(name, r.returncode, (r.stdout + r.stderr).strip().splitlines()[-1:] if r.returncode else "ok")


if __name__ == "__main__":
    main(sys.argv[1:])
