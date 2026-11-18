"""12時のInstagramカルーセル（4枚）を content.py から作る。

使い方: python3 build_carousel.py [日付...]   → images/carousel/<日付>/1〜4.jpg
1枚目＝写真の表紙、2枚目＝やること3つ、3枚目＝ポイント、4枚目＝保存・フォローのお願い。
1枚目の写真は photos.py の6番目（無い日は1枚目を飛ばす）。
"""
import sys
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "images/ig_tips"))
sys.path.insert(0, str(HERE))
import make_pop_cards as pop  # noqa: E402
from content import DAYS  # noqa: E402


def pages(day):
    c = day["car"]
    from photos import P
    cover = P[day["d"]][5]
    out = []
    if (ROOT / cover).exists():
        out.append(dict(tag=c["tag"], title=c["title"], body=c["body"], hero=[c["hero"]], photo=cover))
    out.append(dict(tag=c["tag"], title="やることは3つ", hero=[c["hero"], c["steps"][0][0], c["steps"][2][0]], steps=c["steps"]))
    out.append(dict(tag="ポイント", title=c["title"], hero=["💡"], body=c["point"], ask=c.get("ask", "")))
    out.append(dict(tag="毎日更新中", title="保存して見返してね", hero=["🔖", "❄️", "🏠"],
                    body="冬の暮らしのコツを\n毎日投稿しています\nフォローして待っててね"))
    return out


def main(dates):
    for i, day in enumerate(DAYS):
        if dates and day["d"] not in dates:
            continue
        accent = pop.ACCENTS[i % len(pop.ACCENTS)]
        out = ROOT / "images/carousel" / day["d"]
        out.mkdir(parents=True, exist_ok=True)
        for f in out.glob("*.jpg"):
            f.unlink()
        for n, t in enumerate(pages(day), 1):
            pop.card(t, accent, i * 10 + n).save(out / f"{n}.jpg", quality=92)
        print(day["d"], len(list(out.glob("*.jpg"))))


if __name__ == "__main__":
    main(sys.argv[1:])
