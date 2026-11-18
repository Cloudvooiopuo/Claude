"""Openverse（CC0・パブリックドメインの画像をまとめて探せる公開サービス）から写真を探す。
Wikimedia Commons が混んでいる時の代わり。今は Flickr の画像だけを使う（live.staticflickr.com）。

使い方:
  候補を見る:     python3 openverse_search.py "<検索語>" <候補フォルダ> [件数]
  使う写真を保存: python3 openverse_search.py --take <候補フォルダ>/<候補名>.jpg <保存先.jpg>
出典（ページURL・作者・ライセンス）は 候補フォルダ/credits.json と photos/credits.json に書く。
"""
import io
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image

API = "https://api.openverse.org/v1/images/"
UA = "SoranoneBGM/1.0 (CC0 photo search)"


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60).read()


def main(q, out_dir, n=8):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    cp = out / "credits.json"
    credits = json.loads(cp.read_text()) if cp.exists() else {}
    url = API + "?" + urllib.parse.urlencode({"q": q, "license": "cc0,pdm", "source": "flickr",
                                               "size": "large", "page_size": 20, "mature": "false"})
    got = 0
    for r in json.loads(get(url))["results"]:
        if got >= int(n):
            break
        if (r.get("width") or 0) < 1600 or r.get("license") not in ("cc0", "pdm"):
            continue
        fn = f"{re.sub(r'[^a-z0-9]+', '_', q.lower()).strip('_')}_{got:02d}.jpg"
        try:
            im = Image.open(io.BytesIO(get(r["url"]))).convert("RGB")
        except Exception as e:  # noqa: BLE001
            print("skip", r["url"], e)
            continue
        full = out / ("full_" + fn)
        im.thumbnail((1920, 1920))
        im.save(full, quality=90)
        im.thumbnail((500, 500))
        im.save(out / fn, quality=85)
        credits[fn] = {"title": r.get("title", ""), "page": r.get("foreign_landing_url", ""),
                       "license": r["license"].upper(), "artist": r.get("creator", "") or "", "full": str(full)}
        got += 1
        print(fn, r["license"], r.get("title", "")[:60], flush=True)
        cp.write_text(json.dumps(credits, ensure_ascii=False, indent=1))


def take(cand, dest):
    cand, dest = Path(cand), Path(dest)
    r = json.loads((cand.parent / "credits.json").read_text())[cand.name]
    dest.parent.mkdir(parents=True, exist_ok=True)
    Image.open(r["full"]).save(dest, quality=90)
    root = Path(__file__).resolve().parents[2]
    p = root / "photos" / "credits.json"
    credits = json.loads(p.read_text()) if p.exists() else {}
    credits[str(dest.resolve().relative_to(root))] = {k: r[k] for k in ("title", "page", "license", "artist")}
    p.write_text(json.dumps(credits, ensure_ascii=False, indent=1, sort_keys=True))
    print(dest, r["license"], r["title"])


if __name__ == "__main__":
    if sys.argv[1] == "--take":
        take(sys.argv[2], sys.argv[3])
    else:
        main(*sys.argv[1:])
