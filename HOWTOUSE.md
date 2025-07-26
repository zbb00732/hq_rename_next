# rename.exe ：timestamps.txt に記録されたプレイヤー名をリネームし、Youtube概要欄向けのテキストを生成するツール

## 概要

timestamps.txt に記録されたプレイヤー名をリネームし、Youtube概要欄向けのテキストを生成するツールです。

## 使い方

1. rename.exe を起動
2. timestamp.exe で生成したタイムスタンプファイルを選択
3. BOT から出力された result ファイルを選択
4. 以下のファイルが生成されます：

   - `timestamps_rename_en.txt`（英語）
   - `timestamps_rename_jp.txt`（日本語）

## 注意事項

- result ファイルにはプレイヤーの Discord アカウント名が記載されています。

- Discord アカウント名と Youtube 用プレイヤー名との対応表は `replace_info.txt` に記述します。

- Youtube 概要欄の文章は、対戦結果ファイルの日付から曜日を取得し、週例対戦会か道場かを自動判別します。

- 概要欄テンプレートは `youtube_comment.txt` に以下の順で記載されています：

  -- 英文（週例対戦会）
  -- 日本語（週例対戦会）
  -- 英文（道場）
  -- 日本語（道場）

以上
