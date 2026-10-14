"""10/15〜10/30 の絵文字版（videos/src/motion/*.json）を写真版に作り直す。

使い方: python3 build_w8.py <キー> [<キー> ...]
  PLAN に書いた候補写真を photos/w8/ に --take で落とし（出典は photos/credits.json）、
  videos/src/w8/<キー>.json を書いて、動画なら videos/w8/<キー>.mp4、
  レターなら images/letters/photo/<キー>/01〜05.jpg を作る。
候補写真はスクラッチの検索フォルダ（環境変数 CAND）か、photos/ の中の既存の写真（"photos/..." で始まる）。
"""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CAND = Path(os.environ.get("CAND", "."))
ROLES = ["hook", "3", "2", "1", "cta"]

# キー: (元の絵文字版, 日付, 形, 種類, PR, 写真5枚 hook/3/2/1/cta)
PLAN = {
    "1016_bgm": ("1016_bgm", "2026-10-16", "letter", "メディア", False,
                 ["c2/1016a/headphones_02.jpg", "c4/piano_keys/piano_keys_05.jpg", "c2/1016a/headphones_00.jpg", "c2/1016a/headphones_01.jpg", "c4/piano_keys/piano_keys_04.jpg"]),
    "1020_rain_car": ("c2_rain_car", "2026-10-20", "video", "アフィリエイト", True,
                      ["c2/1020a/rain_on_windshield_00.jpg", "c2/1020a/rain_on_windshield_01.jpg", "c2/1020b/car_wiper_01.jpg", "c2/1020a/rain_on_windshield_03.jpg", "c2/1020a/rain_on_windshield_02.jpg"]),
    "1021_cafe": ("1021_cafe", "2026-10-21", "letter", "レジャー", False,
                  ["c2/1021a/latte_01.jpg", "c2/1021b/cafe_interior_01.jpg", "c2/1021a/latte_00.jpg", "c2/1021a/latte_02.jpg", "c2/1021a/latte_01.jpg"]),
    "1024_daytrip": ("1024_daytrip", "2026-10-24", "video", "レジャー", False,
                     ["c2/1024b/countryside_road_autumn_00.jpg", "c2/1024a/train_window_view_00.jpg", "c2/1024b/countryside_road_autumn_01.jpg", "c2/1024b/countryside_road_autumn_02.jpg", "c2/1024b/countryside_road_autumn_00.jpg"]),
    "1025_cable": ("t4_cable", "2026-10-25", "video", "アフィリエイト", True,
                   ["c2/1025a/usb_cable_00.jpg", "c2/1025a/usb_cable_01.jpg", "c2/1025a/usb_cable_02.jpg", "c2/1025a/usb_cable_03.jpg", "c2/1025a/usb_cable_00.jpg"]),
    "1029_night": ("1029_night", "2026-10-29", "letter", "レジャー", False,
                   ["c2/1029a/city_lights_night_00.jpg", "c2/1029b/lantern_night_02.jpg", "c2/1029a/city_lights_night_01.jpg", "c2/1029b/lantern_night_00.jpg", "c2/1029a/city_lights_night_00.jpg"]),
    "1030_desk_cable": ("t7_desk_cable", "2026-10-30", "video", "アフィリエイト", True,
                        ["c2/1030a/desk_setup_01.jpg", "c2/1030a/desk_setup_00.jpg", "c2/1030a/desk_setup_02.jpg", "c2/1025a/usb_cable_01.jpg", "c2/1030a/desk_setup_01.jpg"]),
}


def take(src, dst):
    if dst.exists():
        return
    if src.startswith("photos/"):
        dst.write_bytes((ROOT / src).read_bytes())
        return
    subprocess.run([sys.executable, "commons_search.py", "--take", str(CAND / src), str(dst)],
                   cwd=ROOT / "photos/src", check=True)


def build(key):
    motion, date, form, kind, pr, srcs = PLAN[key]
    m = json.loads((ROOT / f"videos/src/motion/{motion}.json").read_text())
    done = {}
    paths = {}
    for role, src in zip(ROLES, srcs):
        if src in done:
            paths[role] = done[src]
            continue
        rel = f"photos/w8/{key}_{role}.jpg" if not src.startswith("photos/") else src
        if not src.startswith("photos/"):
            take(src, ROOT / rel)
        done[src] = rel
        paths[role] = rel
    spec = {"date": date, "form": form, "kind": kind, "accent": m["accent"], "pr": pr, "photo_note": pr,
            "hook": m["hook"], "sub": m["sub"], "items": m["items"], "cta": m["cta"], "foot": m.get("foot", ""),
            "photos": {"hook": paths["hook"], "items": {"3": paths["3"], "2": paths["2"], "1": paths["1"]},
                       "cta": paths["cta"]},
            "slot": m["slot"], "say": m["say"]}
    out = ROOT / f"videos/src/w8/{key}.json"
    out.write_text(json.dumps(spec, ensure_ascii=False, indent=2))
    if form == "video":
        subprocess.run([sys.executable, "make_photo_video.py", f"w8/{key}.json", f"../w8/{key}.mp4"],
                       cwd=ROOT / "videos/src", check=True)
    else:
        subprocess.run([sys.executable, "make_letter_cards.py", str(out), str(ROOT / f"images/letters/photo/{key}")],
                       cwd=ROOT / "images/letters", check=True)
    print("BUILT", key, flush=True)


if __name__ == "__main__":
    for k in sys.argv[1:]:
        build(k)
