import requests
import re
from datetime import datetime
from typing import List, Tuple
from time import sleep

BASE_URL = "https://sannan.nl"
KAKO_URL = "https://kako.sannan.nl"


def main(board, kako=False):
    """
    メイン処理。アクセス間隔を調整してクラウドフレアによるDDoS攻撃として認識されないようにする。
    """
    if kako:
        subject_url = f"{KAKO_URL}/{board}/subject.txt"
    else:
        subject_url = f"{BASE_URL}/{board}/subject.txt"

    result = []
    try:
        thread_lines = get_http_from_url(subject_url)
        each_line = extract_thread_info_from_lines(thread_lines)

        for keys in each_line:
            if kako:
                thread_url = f"{KAKO_URL}/{board}/dat/{keys[0]}.dat"
            else:
                thread_url = f"{BASE_URL}/{board}/dat/{keys[0]}.dat"

            try:
                res_list = get_http_from_url(thread_url)
                if res_list is None:
                    raise requests.exceptions.HTTPError

                key = keys[0]
                thread_title = keys[1]

                for i, res in enumerate(res_list):
                    res_num = i + 1
                    thread_data = list(extract_thread_content_from_dat(res)) # 連結のためにリストに変換
                    result.append([key, res_num] + thread_data + [thread_title])

                sleep(2) # アクセス間隔を設定

            except requests.exceptions.HTTPError as e:
                print(f"HTTPエラーが発生しました KEY {keys}: {e}")
                continue

    except Exception as e:
        raise e

    return result


def get_http_from_url(url: str) -> List[str]:
    """指定されたURLからデータを取得する"""
    try:
        response = requests.get(url)
        response.encoding = "sjis"  # 文字コードを明示的に指定する
        response.raise_for_status()  # ステータスコードが200以外の場合に例外を発生させる
        # レスポンスの文字列を改行区切りのリストに変換する
        lines = response.text.splitlines()
        return lines
    except requests.exceptions.HTTPError as e:
        print(f"==================={datetime.now()}===================\n")
        print("HTTPエラーが発生しました:", e)
    except requests.exceptions.ConnectionError as e:
        print(f"==================={datetime.now()}===================\n")
        print("接続エラーが発生しました:", e)
    except requests.exceptions.Timeout as e:
        print(f"==================={datetime.now()}===================\n")
        print("タイムアウトエラーが発生しました:", e)
    except requests.exceptions.RequestException as e:
        print(f"==================={datetime.now()}===================\n")
        print("その他のエラーが発生しました:", e)



def extract_thread_info_from_lines(lines):
    def extract_thread_data_from_metadata(line: str) -> Tuple[str, str, str]:
        """1行のデータからthread_key, thread_title, res_numberを抽出する"""
        pattern = r"^(.+?)\.dat<>\s*([^<>]+?)\s+\((\d+)\)$"
        match = re.match(pattern, line)
        if not match:
            # パターンにマッチしない行は無視する
            return None
        thread_key, thread_title, res_number = match.groups()
        return thread_key, thread_title.strip(), res_number


    """複数行のデータからthread_key, thread_title, res_numberを抽出する"""
    results = []
    for line in lines:
        parsed = extract_thread_data_from_metadata(line)
        if parsed is not None:
            results.append(parsed)
    return results


def extract_thread_content_from_dat(data):

    def parse_name_and_wacchoi(s):
        # 名前とwacchoiをパースするヘルパー関数
        if "</b>(" in s:  # </b>( が含まれている場合
            name, wacchoi = s.split("</b>(")
            return name, wacchoi.replace(")<b>", "")
        else:
            # 管理人の書き込みを無視する
            if "★" in s:
                raise Exception
            else:
                return s, ""

    # データを分割して必要な情報を抜き出す
    try:
        lst = data.split("<>")
        name, wacchoi = parse_name_and_wacchoi(lst[0])
        mail = lst[1]
        date, id_num = lst[2].replace("???", "").split("ID:")
        # 特殊文字と改行を削除
        remove_schar = r"(&#\d+;)|(\u3000+)"
        comment = re.sub(remove_schar, "", lst[3].replace("<br>", "").rstrip())
        return name.rstrip(), wacchoi, mail, date.rstrip(), id_num, comment
    except Exception:
        name = "invild data"
        wacchoi = "12345"
        mail = "sage"
        date = "1900/1/1(日) 00:00:00.00"
        id_num = "abcdefg"
        comment = "invild data comment"
        return name.rstrip(), wacchoi, mail, date.rstrip(), id_num, comment