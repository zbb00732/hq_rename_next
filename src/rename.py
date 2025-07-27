import os
import sys
import re
import datetime
import calendar
from tkinter import filedialog
from typing import List, Tuple


class TimestampReplacer:
    """
    タイムスタンプおよび対戦プレイヤー情報を含むファイルを読み取り、
    Player1 / Player2 を実際のプレイヤー名に置換して、
    Youtube概要欄に記載する文面のファイルを英語・日本語で出力するクラス。
    """

    def __init__(self):
        """コンストラクタ：変数宣言"""
        self.replace_info: List[Tuple[str, str]] = []
        self.match_result: dict[str, Tuple[str, str]] = {}
        self.date: datetime.date = None

        self.players_name_en: List[str] = []
        self.players_name_jp: List[str] = []

        self.output_lines: List[str] = []


    def load_replace_info(self, replace_info_file) -> List[Tuple[str, str]]:
        """replace_info.txt を読み込み、置換用の配列に変換

        Args:
            replace_info_file (str): 置換情報ファイル名

        Returns:
            List[Tuple[str, str]]: (日本語名, 英語名)のリスト
        """
        info = []
        with open(replace_info_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split(',')
                if len(parts) == 2:
                    info.append(tuple(parts))

        # 大和田→Oowada、和田→Wada といった組合せがあった場合に誤って置換しないよう日本語文字列が長い順にソートする
        replace_info_sorted = sorted(info, key=lambda x: len(x[0]), reverse=True)
        return replace_info_sorted


    def extract_date_from_filename(self, filename: str) -> datetime.date:
        """ファイル名から日付情報を抽出

        Args:
            filename (str): 対戦resultファイル名

        Returns:
            datetime.date: ファイル名から抽出した日付
        """
        base = os.path.basename(filename)[:8]
        return datetime.date(int(base[:4]), int(base[4:6]), int(base[6:8]))


    def convert_to_display_names(self, normalized_names: List[str]) -> List[str]:
        """対戦プレイヤー名（英語）の配列を、「日本語名 (英語名)」の配列に変換

        Args:
            normalized_names (List[str]): 対戦プレイヤー名（英語）の配列

        Returns:
            List[str]: 「日本語名 (英語名)」の配列
        """
        # self.replace_info (日本語名, 英語名) の配列を {英語名: 日本語名} の dict 形式に変換
        replace_dict = {en: jp for jp, en in self.replace_info}
        display_list = []
        for name in normalized_names:
            original = replace_dict.get(name, name)
            if original == name:
                display_list.append(f"{name}")
            else:
                display_list.append(f"{original} ({name})")

        return display_list


    def parse_result_file(self, result_file: str) -> dict[str, Tuple[str, str]]:
        """resultファイルを読み込み、{ 試合番号: (プレイヤー1, プレイヤー2) }の辞書を返す。
           また、参加者のリスト（英語・日本語）をクラス変数に格納する。
        Args:
            result_file (str): 対戦resultファイル名

        Returns:
            dict[str, Tuple[str, str]]: { 試合番号: (プレイヤー1, プレイヤー2) }の辞書
        """
        replace_dict = dict(self.replace_info)
        result_dict = {}
        player_set = set()

        with open(result_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                match = re.match(r'(M\d+):\s*(.*?)\s+vs\s+(.*)', line)
                if match:
                    matchno, raw_p1, raw_p2 = match.groups()
                    player1 = replace_dict.get(raw_p1.strip(), raw_p1.strip())
                    player2 = replace_dict.get(raw_p2.strip(), raw_p2.strip())
                    result_dict[matchno] = (player1, player2)
                    player_set.add(player1)
                    player_set.add(player2)

        self.players_name_en = sorted(player_set)
        self.players_name_jp = self.convert_to_display_names(self.players_name_en)

        return result_dict


    def replace_timestamps_playername(self, timestamp_file: str) -> List[str]:
        """timestampファイルを読み込み、Player1・Player2 を置換した結果を str の配列として返す
        Args:
            timestamp_file (str): 対戦timestampファイル名

        Returns:
            List[str]: 置換後の文字列のリスト
        """

        output_lines = []
        match_dict = self.match_result

        with open(timestamp_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        current_matchno = None  # 直前の M番号を保持

        for line in lines:
            stripped = line.strip()

            # 試合行: 0:00:22 M01: Player1 - X vs Player2 - Y
            match = re.match(r'(\d+:\d+:\d+)\s+(M\d+):\s+Player1\s+-\s+(.*?)\s+vs\s+Player2\s+-\s+(.*)', stripped)
            if match:
                timecode, matchno, p1_suffix, p2_suffix = match.groups()
                current_matchno = matchno  # 次の勝敗行のために保持

                real_p1, real_p2 = match_dict.get(matchno, ("Player1", "Player2"))
                new_line = f"{timecode} {matchno}: {real_p1} - {p1_suffix} vs {real_p2} - {p2_suffix}"
                output_lines.append(new_line)
                continue

            # 勝敗行: Player1 win by X:X または Player2 win by X:X
            win_match = re.match(r'(Player[12])\s+win\s+by\s+(\d+:\d+)', stripped)
            if win_match and current_matchno:
                winner, score = win_match.groups()
                real_p1, real_p2 = match_dict.get(current_matchno, ("Player1", "Player2"))
                winner_name = real_p1 if winner == "Player1" else real_p2
                new_line = f"{winner_name} win by {score}"
                output_lines.append(new_line)
                continue

            # その他の行（例：Settingsなど）
            output_lines.append(stripped)

        return output_lines


    def write_header(self, output_file: str, title: str, comment: str, player_names: List[str]) -> None:
        """Youtube動画概要欄のヘッダー情報（タイトル・コメント・プレイヤー一覧）を出力ファイルに書き込む

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


    def write_body(self, output_file: str, output_lines: List[str]) -> None:
        """Youtube動画概要欄の内容（タイムスタンプ、ハッシュタグ）を出力ファイルに書き込む

        Args:
            output_file (str): 出力ファイルパス
            output_lines (List[str]): プレイヤー名置換後のタイムスタンプ文字列
        """
        with open(output_file, 'a', encoding='utf-8') as f:
            for line in output_lines:
                f.write(f"{line}\n")
            f.write('\n#hellishquart\n')


    def process(self) -> None:
        """メイン処理実行"""
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            base_dir = os.path.abspath(os.path.join(current_dir, os.pardir))

        replace_info_file    = os.path.join(base_dir, "replace_info.txt")
        youtube_comment_file = os.path.join(base_dir, "youtube_comment.txt")

        if not os.path.isfile(replace_info_file):
            print(f"置換ファイルが見つかりません: {replace_info_file}")
            sys.exit()
        if not os.path.isfile(youtube_comment_file):
            print(f"コメントファイルが見つかりません: {youtube_comment_file}")
            sys.exit()

        timestamp_file = filedialog.askopenfilename(title="対戦timestampsファイルを選択")
        if not timestamp_file:
            print('タイムスタンプファイルが選択されていません。')
            sys.exit()

        result_file = filedialog.askopenfilename(title="対戦resultファイルを選択")
        if not result_file:
            print('対戦結果ファイルが選択されていません。')
            sys.exit()

        self.replace_info = self.load_replace_info(replace_info_file)

        self.match_result = self.parse_result_file(result_file)
        self.date = self.extract_date_from_filename(result_file)

        self.output_lines = self.replace_timestamps_playername(timestamp_file)

        with open(youtube_comment_file, 'r', encoding='utf-8') as f:
            comments = [line.strip().replace('\\n', '\n').replace('@n', '\n') for line in f]

        weekday = self.date.weekday()
        is_saturday = weekday == 5

        title_en = f"[Hellish Quart PvP] {calendar.month_abbr[self.date.month]}-{self.date.day:02d}-{self.date.year}"
        title_jp = f"[Hellish Quart PvP] {self.date.year}-{self.date.month:02d}-{self.date.day:02d}"

        if is_saturday:
            title_en += " Weekly Sparring"
            title_jp += " 週例オンライン対戦会"
            comment_en = comments[0]
            comment_jp = comments[1]
        else:
            title_en += " Sparring"
            title_jp += " 道場マッチ"
            comment_en = comments[2]
            comment_jp = comments[3]

        date_str = self.date.strftime('%Y%m%d')
        output_file_en = f'{date_str}_youtube_description_en.txt'
        output_file_jp = f'{date_str}_youtube_description_jp.txt'

        self.write_header(output_file_en, title_en, comment_en, self.players_name_en)
        self.write_header(output_file_jp, title_jp, comment_jp, self.players_name_jp)
        self.write_body(output_file_en, self.output_lines)
        self.write_body(output_file_jp, self.output_lines)


def main():
    replacer = TimestampReplacer()
    replacer.process()


if __name__ == '__main__':
    main()
