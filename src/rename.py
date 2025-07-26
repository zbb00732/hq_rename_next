import os
import sys
import datetime
import calendar
from tkinter import filedialog
from typing import List, Tuple


class TimestampReplacer:
    """
    プレイヤー情報を含むタイムスタンプファイルを読み取り、
    Player1 / Player2 を実際のプレイヤー名に置換して、
    英語・日本語両方の形式でファイルを出力するクラス。
    """

    def __init__(self):
        """コンストラクタ：必要ファイルの読み込み"""
        self.input_file = filedialog.askopenfilename(title="対戦timestampsファイルを選択")
        if not self.input_file:
            print('タイムスタンプファイルが選択されていません。')
            sys.exit()

        self.player_file = filedialog.askopenfilename(title="対戦resultファイルを選択")
        if not self.player_file:
            print('対戦結果ファイルが選択されていません。')
            sys.exit()

        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            base_dir = os.path.abspath(os.path.join(current_dir, os.pardir))

        self.replace_info_file = os.path.join(base_dir, "replace_info.txt")
        self.comment_file = os.path.join(base_dir, "youtube_comment.txt")

        # ファイル存在チェック
        if not os.path.isfile(self.replace_info_file):
            print(f"置換ファイルが見つかりません: {self.replace_info_file}")
            sys.exit()
        if not os.path.isfile(self.comment_file):
            print(f"コメントファイルが見つかりません: {self.comment_file}")
            sys.exit()

        self.output_file_en = 'timestamps_rename_en.txt'
        self.output_file_jp = 'timestamps_rename_jp.txt'

        self.players_list = []
        self.players_name_en = []
        self.players_name_jp = []

        self.date = self.extract_date_from_filename(self.player_file)

    def extract_date_from_filename(self, filename: str) -> datetime.date:
        """ファイル名から日付情報を抽出

        Args:
            filename (str): プレイヤーファイル名

        Returns:
            datetime.date: ファイル名から抽出した日付
        """
        base = os.path.basename(filename)[:8]
        return datetime.date(int(base[:4]), int(base[4:6]), int(base[6:8]))

    def load_replace_info(self) -> List[Tuple[str, str]]:
        """replace_info.txt を読み込み、置換用辞書に変換

        Returns:
            List[Tuple[str, str]]: (日本語名, 英語名)のリスト
        """
        info = []
        with open(self.replace_info_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split(',')
                if len(parts) == 2:
                    info.append(tuple(parts))
        return info

    def parse_player_list(self, replace_info: List[Tuple[str, str]]) -> None:
        """プレイヤーファイルを読み込み、置換とリスト作成を行う

        Args:
            replace_info (List[Tuple[str, str]]): プレイヤー名置換リスト
        """
        with open(self.player_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # 長い日本語順に並べ替え
        replace_info_sorted = sorted(replace_info, key=lambda x: len(x[0]), reverse=True)

        for line in lines:
            for jp, en in replace_info_sorted:
                line = line.replace(jp, en)
            parts = line.strip().split()
            if len(parts) < 4:
                continue
            p1, p2 = parts[1], parts[3]
            self.players_list.append([p1, p2])

            for player in [p1, p2]:
                if player not in self.players_name_en:
                    self.players_name_en.append(player)
                    jp_name = next((f"{jp}({player})" for jp, en in replace_info if en == player), player)
                    self.players_name_jp.append(jp_name)

        # 英語名と日本語表示名のペアでソート（英語名のアルファベット順、大文字小文字無視）
        paired_names = sorted(zip(self.players_name_en, self.players_name_jp), key=lambda x: x[0].lower())
        # ソート済みペアを分離
        self.players_name_en = [en for en, _ in paired_names]
        self.players_name_jp = [jp for _, jp in paired_names]

    def replace_players(self, output_file: str, is_append: bool = False) -> None:
        """タイムスタンプファイル内のPlayer1/Player2をプレイヤー名に置換

        Args:
            output_file (str): 出力ファイルパス
            is_append (bool): 追記モードかどうか
        """
        with open(self.input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        mode = 'a' if is_append else 'w'
        with open(output_file, mode, encoding='utf-8') as f:
            index = 0
            for i in range(0, len(lines) - 1, 2):
                if index >= len(self.players_list):
                    break
                p1, p2 = self.players_list[index]
                lines[i] = lines[i].replace('Player1', p1).replace('Player2', p2)
                lines[i + 1] = lines[i + 1].replace('Player1', p1).replace('Player2', p2)
                f.write(lines[i])
                f.write(lines[i + 1])
                index += 1
            f.write('\n#hellishquart\n')

    def write_header(self, output_file: str, title: str, comment: str, player_names: List[str]) -> None:
        """ヘッダー情報（タイトル・コメント・プレイヤー一覧）を出力ファイルに書き込む

        Args:
            output_file (str): 出力ファイルパス
            title (str): ヘッダータイトル
            comment (str): 説明コメント（複数行含む）
            player_names (List[str]): プレイヤー名一覧
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"{title}\n\n")
            f.write(comment.replace('@n', '\n'))
            f.write('\n')
            for name in player_names:
                f.write(f" - {name}\n")
            f.write('\n')

    def process(self) -> None:
        """メイン処理実行"""
        with open(self.player_file, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()

        if first_line.startswith('M01:'):
            # 自動生成用
            replace_info = self.load_replace_info()
            self.parse_player_list(replace_info)

            with open(self.comment_file, 'r', encoding='utf-8') as f:
                comments = [line.strip().replace('\\n', '\n').replace('@n', '\n') for line in f]

            weekday = self.date.weekday()
            is_saturday = weekday == 5

            title_en = f"[Hellish Quart PvP] {calendar.month_abbr[self.date.month]}-{self.date.day:02d}-{self.date.year}"
            title_en += " Weekly Sparring" if is_saturday else " Sparring"

            title_jp = f"[Hellish Quart PvP] {self.date.year}-{self.date.month:02d}-{self.date.day:02d}"
            title_jp += " 週例オンライン対戦会" if is_saturday else " 道場マッチ"

            comment_en = comments[0] if is_saturday else comments[2]
            comment_jp = comments[1] if is_saturday else comments[3]

            self.write_header(self.output_file_en, title_en, comment_en, self.players_name_en)
            self.write_header(self.output_file_jp, title_jp, comment_jp, self.players_name_jp)

            self.replace_players(self.output_file_en, is_append=True)
            self.replace_players(self.output_file_jp, is_append=True)
        else:
            # 手動生成用：replace_infoやコメントファイルは不要
            print("手動生成モードとして実行中：プレイヤー情報は埋め込まれません")
            self.replace_players(self.output_file_en, is_append=False)


def main():
    replacer = TimestampReplacer()
    replacer.process()


if __name__ == '__main__':
    main()
