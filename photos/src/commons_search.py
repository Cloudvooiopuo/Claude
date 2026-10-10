"""Wikimedia Commons から CC0・パブリックドメインの写真だけを探して落とす。

使い方:
  候補を見る:   python3 commons_search.py "<検索語>" <候補フォルダ> [件数]      … 500px の小さい版で落とす
  使う写真を落とす: python3 commons_search.py --take <候補フォルダ>/<候補名>.jpg <保存先.jpg>
                                         … 1920px か 1280px の版で落とし、photos/credits.json に出典を書く

この環境では commons の api.php が出口の共有で 429 になり、thumb.wikimedia.org は止まっているので、
① 画像検索のページ（Special:MediaSearch、構造化データで CC0 / パブリックドメインに絞る）からファイル名を拾い、
② 各ファイルページの「ライセンスの短い表示（licensetpl_short）」を読んで CC0・Public domain 以外は捨て、
③ upload.wikimedia.org の 1920px 版（元画像は 429 になりやすい）を落として 1800px に縮める。
出典（ファイルページURL・作者・ライセンス）は <出力フォルダ>/credits.json に追記する。
"""
import html
import io
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image

BASE = "https://commons.wikimedia.org"
UA = "CafeTabiMemoBot/1.0 (https://github.com/cloudvooiopuo/claude)"
FILTER = "haswbstatement:P275=Q6938433|P6216=Q19652"  # ライセンス=CC0 か 著作権の状態=パブリックドメイン


def get(url, tries=6):
    for i in range(tries):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=90).read()
        except urllib.error.HTTPError as e:
            if e.code != 429 or i == tries - 1:
                raise
            time.sleep(int(e.headers.get("retry-after", 30)) + 5)


def file_names(q):
    """検索ページに埋め込まれた結果（JSON）から、ファイル名・大きさ・元画像URLを拾う"""
    url = f"{BASE}/w/index.php?" + urllib.parse.urlencode(
        {"search": f"{q} {FILTER}", "title": "Special:MediaSearch", "type": "image"})
    page = get(url).decode()
    hits, seen = [], set()
    for seg in page.split('{"pageid":')[1:]:  # 結果1件ずつに分けてから読む（隣の結果と混ざらないように）
        t = re.search(r'"title":"(File:(?:[^"\\]|\\.)+)"', seg)
        ii = re.search(r'"imageinfo":\[\{"size":\d+,"width":(\d+),"height":(\d+)', seg)
        u = re.search(r'"url":"(https://upload\.wikimedia\.org/[^"?]+)', seg)
        if not (t and ii and u):
            continue
        name = json.loads(f'"{t.group(1)}"')
        if name in seen or not name.lower().endswith((".jpg", ".jpeg", ".png")):
            continue
        seen.add(name)
        hits.append({"title": name, "w": int(ii.group(1)), "h": int(ii.group(2)), "url": u.group(1)})
    return hits


def check(hit):
    """ファイルページの「ライセンスの短い表示」を読む。全部が CC0／パブリックドメインの時だけ出典を返す"""
    page = f"{BASE}/wiki/{urllib.parse.quote(hit['title'].replace(' ', '_'))}"
    h = get(page).decode()
    lic = [" ".join(html.unescape(re.sub("<[^>]+>", "", x)).split())
           for x in re.findall(r'class="licensetpl(?:_|&#95;)short"[^>]*>(.*?)</span>', h, re.S)]
    if not lic or not all(l.lower().startswith(("cc0", "public domain", "pd")) for l in lic):
        return None
    a = re.search(r'id="fileinfotpl_aut"[^>]*>.*?</td>\s*<td[^>]*>(.*?)</td>', h, re.S)
    artist = " ".join(html.unescape(re.sub("<[^>]+>", "", a.group(1))).split())[:120] if a else ""
    return dict(hit, page=page, license=lic[0], artist=artist)


def thumb(url, w, size=None):
    """元画像は 429 になりやすいので、upload.wikimedia.org の決まった幅（500・1280・1920px）の縮小版を使う"""
    size = size or (1920 if w > 1920 else 1280 if w > 1280 else None)
    if not size:
        return url
    head, name = url.rsplit("/", 1)
    return head.replace("/commons/", "/commons/thumb/") + f"/{name}/{size}px-{name}"


def main(q, out_dir, n=8):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    cred_path = out / "credits.json"
    credits = json.loads(cred_path.read_text()) if cred_path.exists() else {}
    got = 0
    for hit in file_names(q):
        if got >= int(n):
            break
        if hit["w"] < 1200 or hit["h"] < 900 or hit["w"] * hit["h"] > 60e6:
            continue
        time.sleep(1)
        r = check(hit)
        if not r:
            continue
        fn = f"{re.sub(r'[^a-z0-9]+', '_', q.lower()).strip('_')}_{got:02d}.jpg"
        Image.open(io.BytesIO(get(thumb(r["url"], r["w"], 500)))).convert("RGB").save(out / fn, quality=85)
        credits[fn] = r
        got += 1
        print(fn, r["license"], r["title"], flush=True)
    cred_path.write_text(json.dumps(credits, ensure_ascii=False, indent=1))


def take(cand, dest):
    """候補の中から使う1枚を大きい版で落とし、リポジトリの photos/credits.json に出典を足す"""
    cand, dest = Path(cand), Path(dest)
    r = json.loads((cand.parent / "credits.json").read_text())[cand.name]
    im = Image.open(io.BytesIO(get(thumb(r["url"], r["w"])))).convert("RGB")
    im.thumbnail((1920, 1920))
    dest.parent.mkdir(parents=True, exist_ok=True)
    im.save(dest, quality=90)
    root = Path(__file__).resolve().parents[2]
    cp = root / "photos" / "credits.json"
    credits = json.loads(cp.read_text()) if cp.exists() else {}
    credits[str(dest.resolve().relative_to(root))] = {k: r[k] for k in ("title", "page", "license", "artist")}
    cp.write_text(json.dumps(credits, ensure_ascii=False, indent=1, sort_keys=True))
    print(dest, r["license"], r["title"])


if __name__ == "__main__":
    if sys.argv[1] == "--take":
        take(sys.argv[2], sys.argv[3])
    else:
        main(*sys.argv[1:])
