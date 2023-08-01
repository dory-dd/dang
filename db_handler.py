import sqlite3
from typing import List, Tuple
from datetime import datetime
import re
from scraper import scrape_data


def trans_unixtime_to_datestr(thread_key):
    # Unix時間をdatetime形式に変換する
    thread_key = datetime.fromtimestamp(int(thread_key))
    # datetime形式の日付を文字列に変換するためのフォーマットを指定する
    date_format = "%Y-%m-%d %H:%M:%S"
    # 文字列に変換する
    return thread_key.strftime(date_format)


def create_database(database_name: str, table_name: str) -> None:
    """データベースを作成する"""
    conn = sqlite3.connect(f'{database_name}.db')
    c = conn.cursor()
    c.execute(f'CREATE TABLE IF NOT EXISTS {table_name} (timestamp TIMESTAMP PRIMARY KEY, title TEXT, res_num INTEGER)')
    conn.commit()
    conn.close()


def save_data(database_name: str, table_name: str, data: List[Tuple[str, str, str]]) -> None:
    """リストのデータをデータベースに保存し、すでに重複している場合はres_numberをupdateする"""
    # 除外スレタイリスト
    exclude_titles = ["^★\s３ちゃんねる", "^■\s規制情報\s■"]
    conn = sqlite3.connect(f'{database_name}.db')
    c = conn.cursor()

    for item in data:
        timestamp, title, res_num = item
        str_timestamp = trans_unixtime_to_datestr(timestamp)
        # タイトルが除外対象の正規表現に一致する場合、データを保存しない
        if any([re.search(regex, title) for regex in exclude_titles]):
            continue
        c.execute(
            f'INSERT INTO {table_name} (timestamp, title, res_num) VALUES (?, ?, ?) '
            f'ON CONFLICT(timestamp) DO UPDATE SET res_num = ?',
            (str_timestamp, title, res_num, res_num),
        )

    conn.commit()
    conn.close()


def load_data(database_name: str, table_name: str) -> List[Tuple[str, str, int]]:
    """データベースからデータを読み込む"""
    conn = sqlite3.connect(f'{database_name}.db')
    c = conn.cursor()
    c.execute(f'SELECT COUNT(*) FROM {table_name}')
    data = c.fetchone()
    conn.close()
    return data[0]


# テスト
if __name__ == "__main__":
    dt_now = datetime.now()
    today = dt_now.strftime('%Y-%m-%d-%H:%S')

    database_name = "/mnt/d/database/test_db.db"
    table_name = "thread_table"

    create_database(database_name, table_name)
    data = scrape_data()
    save_data(database_name, table_name, data)
    loaded_data = load_data(database_name, table_name)
    print(f"{today} thread count: {loaded_data}")
