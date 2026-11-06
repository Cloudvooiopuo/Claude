"""予約用の一覧 posts/posts_1114_1127.json を作る（1件＝date・form・kind・affiliate・link・title・text・media・networks）。"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
from build_videos import FIRST_SLOT  # noqa: E402
from content import DAYS  # noqa: E402

SLOTS = json.loads((ROOT / "videos/src/rotation.json").read_text())["slots"]
CREDIT = "写真：Wikimedia Commons（CC0／パブリックドメイン）"
out = []
for i, day in enumerate(DAYS):
    d, c, v = day["d"], day["car"], day["video"]
    date = f"2026-11-{d[2:]}"
    steps = "\n".join(f"{k + 1}. {s[1]}" for k, s in enumerate(c["steps"]))
    cap = f"{c['title']}\n\n{c['body'].replace(chr(10), '')}\n\n{steps}\n\n{c['point'].replace(chr(10), '')}\n"
    if c.get("ask"):
        cap += f"\n{c['ask']}\n"
    cap += f"\nめくって読んでね。保存して後で見返してね\n\n{c['tags']}\n\n{CREDIT}"
    imgs = sorted((ROOT / "images/carousel" / d).glob("*.jpg"))
    out.append(dict(date=f"{date}T12:00:00", form="carousel", kind="暮らし・メディア・レジャー", affiliate=False, link="リンクなし",
                    title=c["title"], text=cap, media=[str(p.relative_to(ROOT)) for p in imgs], networks=["instagram"]))
    out.append(dict(date=f"{date}T18:00:00", form="threads", kind="暮らし・メディア・レジャー", affiliate=False, link="リンクなし",
                    title=c["title"], text=day["threads"], media=[], networks=["threads"]))
    slot = SLOTS[(FIRST_SLOT + i) % len(SLOTS)]
    title = "、".join(v["hook"])
    lines = "\n".join(f"{lab} {name}" for lab, name, _, _ in v["items"])
    head = f"#PR {title}" if day["pr"] else title
    body = f"{head}\n\n{lines}\n"
    if day["pr"]:
        body += f"（使うなら：{v['products']}）\n"
    body += "\n保存して後で見返してね\n"
    if day["pr"]:
        body += "使う物はプロフィールのリンクから\n※写真はイメージです\n"
    if slot["voice"]:
        body += f"ナレーション：VOICEVOX:{slot['voice']}\n"
    body += f"{CREDIT}\n\n{v['tags']}"
    out.append(dict(date=f"{date}T18:00:00", form="video", kind=day["kind"], affiliate=day["pr"],
                    link="Amazon（リンク待ち）" if day["pr"] else "リンクなし", title=title, text=body,
                    media=[f"videos/w10/{d}_{day['key']}.mp4"], networks=["instagram", "tiktok", "youtube"],
                    youtube_title=v["ytitle"], youtube_tags=v["yttags"]))
(ROOT / "posts/posts_1114_1127.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
print(len(out))
