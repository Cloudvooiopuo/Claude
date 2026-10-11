# SNSに毎日投稿する回し方（手順書）

Addnessのゴール「TikTok・Instagram・Threadsに毎日出し続ける仕組みを作る」で使う手順です。
新しい会話のAIでも、これを読めば次の2週間分の投稿を作って予約できるように書いています。
同じ内容をAddnessのナレッジ「SNSの投稿を2週間分作って予約する」にも置いています。

## 1. 決まり（必ず守る）

| 項目 | 決まり |
| --- | --- |
| 投稿の時間 | 毎日 **12時**：Instagram画像（1枚）／**18時**：動画かレターのどちらか ＋ Threads（文字） |
| 動画とレター | だいたい半々にする。動画は TikTok・Instagramリール・YouTubeショート、レターは Instagram（めくる投稿）と TikTok（写真投稿）に出す。YouTubeには出さない |
| アフィリエイト | **SNSごとに5本に1本だけ**。商品紹介の回はキャプションの先頭に `#PR` を付け、「紹介した物はプロフィールのリンクから」で締める。ほかの4本は暮らし・メディア・レジャーの話で、商品・リンク・#PRは付けない |
| 商品紹介の言い方 | 「売れてる」「レビューでこう言われてる」で話す。「使ってみた」「私はこう感じた」は言わない。順位はスクショを撮った日付を「（9/29時点）」のように書く |
| 薬機法・景表法 | 美容・健康の物は効果を言い切らない（「伸びる」「消える」「永久」などは使わない） |
| リンク先 | 投稿には楽天かAmazonかを書かない。こちら側の記録（ゴール本文の表）にだけ「リンク先」の列を付ける。今の商品紹介はAmazonだけ |
| 写真 | **本人の写真や個人情報は出さない**。写真は Wikimedia Commons の **CC0・パブリックドメインの物だけ**。出典は `photos/credits.json` に足す。商品紹介で似た写真を使う時は「※写真はイメージです」と入れる。ロゴや商品名が読める他社の写真は使わない |
| 声 | VOICEVOX。`videos/src/rotation.json` の slot を動画ごとに1つずつ進める（声なしの回もある）。キャプションに「ナレーション：VOICEVOX:<声の名前>」を書く |
| TikTok | `isAigc: true`。商品紹介の回は `commercialContentThirdParty: true` も付ける |
| 予約の前 | **本人のOKをもらってから予約する** |

## 2. 1回分（2週間）の流れ

1. **今の状況を読む**：Addnessのゴールで `get_goal_context` と `list_goal_memories` を読む。ゴール本文の先頭に、最新の予約状況（どこまで埋まっているか、次の slot 番号、次の商品紹介の日）がある
2. **穴を探す**：Metricool（brandId `7070916`、タイムゾーン `Asia/Tokyo`）の `getScheduledPosts` で、今日から14日先までの12時・18時を確かめる
3. **反応を見る**：`getAnalyticsDataByMetrics` で先週の表示・保存・いいねを見て、伸びたテーマを次の2週間に多めに入れる
4. **ネタを決める**：14日分の表を作る（日・12時の画像・18時の形（動画かレター）・種類（暮らし／メディア／レジャー／商品紹介）・内容・リンク先）。商品紹介は5日に1回。季節に合わせる
5. **作る**（下の「3. 作り方」）
6. **本人に見せてOKをもらう**：表と、見本を数本送る
7. **予約する**：Metricool の `createScheduledPost` で1件ずつ予約する。画像と動画は、このブランチをpushしてから `https://raw.githubusercontent.com/Cloudvooiopuo/Claude/claude/addness-daily-sns-posting-d9kgj2/<ファイルの場所>` を渡す（Metricoolが自分の保存先へコピーするので、後でファイルを動かしても予約は壊れない）
8. **記録する**：ゴール本文の先頭の「予約の状況」を書き換え、予約した物を表（日・形・内容・リンク先・Metricool ID）で足す。`append_goal_memory` に要点（どこまで埋まったか、次の slot、次の商品紹介の日）を残す

## 3. 作り方（プログラムの場所）

すべてブランチ `claude/addness-daily-sns-posting-d9kgj2` にあります。

| 作る物 | プログラム | 使い方 | 設定の見本 |
| --- | --- | --- | --- |
| 写真が動く動画（今の主な型） | `videos/src/make_photo_video.py` | `python3 make_photo_video.py <spec.json> <out.mp4>` | `videos/src/w6/*.json` |
| 絵文字が動く動画 | `videos/src/make_motion_video.py` | `python3 make_motion_video.py <spec.json> <out.mp4>` | `videos/src/motion/*.json` |
| 文字の動画（古い型、声だけ版も作れる） | `videos/src/make_narrated_video.py` | `<spec> <out> [--voice-only]` | `videos/src/w4/*.json` |
| BGM | `videos/src/make_bgm.py` | 動画のプログラムが中で使う | — |
| レター（5枚） | `images/letters/make_letter_cards.py` | `python3 make_letter_cards.py <spec.json> <出力フォルダ>` | `images/letters/` の各フォルダ |
| Instagram画像 | `images/ig_tips/make_tip_cards.py` | `python3 make_tip_cards.py <内容.json>` | `images/ig_tips/photo_1031_1113.json` |
| 写真を探す | `photos/src/commons_search.py` | 候補：`"<検索語>" <候補フォルダ> [件数]`／使う：`--take <候補.jpg> <保存先.jpg>` | 出典 `photos/credits.json` |
| 予約用の一覧 | `posts/posts_<期間>.json` | 1件＝date・form・kind・affiliate・link・title・text・media・networks | `posts/posts_1031_1113.json` |
| プロフィール画像 | `profile/` | — | — |

### 準備（新しい環境で1回）

- Python の道具：`pip install pillow "numpy<2" pyopenjtalk-prebuilt imageio-ffmpeg`
- VOICEVOX：`dockerd` を起動してから
  `docker pull voicevox/voicevox_engine:cpu-latest` → `docker run -d -p 50021:50021 voicevox/voicevox_engine:cpu-latest`（localhost:50021。プロキシは通さない）
- ネットワーク：環境の許可ドメインに `commons.wikimedia.org`・`upload.wikimedia.org`・`raw.githubusercontent.com` が要る。Commons の `api.php` は混雑で429になりやすいので、`commons_search.py` は検索ページ→ファイルページでライセンス確認→縮小版を取る方法にしてある

## 4. 定期実行（この会話に届く）

| いつ | 何をする |
| --- | --- |
| 毎日 12:20・18:20 | 投稿のお知らせ（🟢投稿済み／🟡待ち／🔴失敗、リンクつき） |
| 毎週日曜 19:48 | スクショの日：本人にAmazon売れ筋のスクショを頼む（商品紹介の回に使う） |
| 毎週月曜 7:52 | マーケの振り返り：先週の数字と次の寄せ方を報告する |
| 毎週月曜 8:56 | 予約の補充：振り返りの結論を使い、上の「2. 1回分の流れ」を行って本人のOKを待つ |

## 5. 困った時

- 投稿が 🔴 になった：`getScheduledPosts` の `detailedStatus` を見る。直す前に本人に確認する
- Amazon・楽天の商品画像のサーバーはこの環境から取れない（使わない決まり）
- 会話が長くなって止まった：新しい会話で「HANDBOOK.md とゴール本文の先頭を読んで、続きをやって」と頼む。定期実行の届け先も新しい会話に作り直す
