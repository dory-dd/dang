import os
from datetime import datetime, timedelta
import sqlite3

# データベースファイルのパスを指定
DB_FILE = "/mnt/d/database/test_db.db"


def create_connection():
    """データベースに接続する"""
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        print(f"successful connection with sqlite version {sqlite3.version}")
        return conn
    except sqlite3.Error as e:
        print(e)
        return conn


def create_total_table(table_name):
    """テーブルを作成する"""
    with create_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                f"CREATE TABLE IF NOT EXISTS {table_name} "
                "(timestamp TIMESTAMP PRIMARY KEY, total_res INTEGER)"
            )
            print(f"{table_name} table created successfully")
        except sqlite3.Error as e:
            print(e)


def save_total_records(table_name, date_string):
    """指定された日/月/年のres_numの合計を求め、指定されたテーブルに保存する。"""
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            # f"INSERT INTO {table_name} (timestamp, total_res) "
            # "SELECT ? AS timestamp, SUM(res_num) AS total_res "
            # "FROM thread_table WHERE DATE(timestamp) = ? "
            # "ON CONFLICT(timestamp) DO UPDATE SET total_res = excluded.total_res",
            # (datetime.strptime(date_string, "%Y-%m-%d"), date_string)
            f"INSERT INTO {table_name} (timestamp, total_res) "
                "SELECT DATE(timestamp) AS timestamp, SUM(res_num) AS total_res "
                "FROM thread_table WHERE DATE(timestamp) = ? "
                "GROUP BY DATE(timestamp) "
                "ON CONFLICT (timestamp) DO UPDATE SET total_res = excluded.total_res",
                (date_string,)
        )
        conn.commit()
        print(f"Records saved to {table_name} table successfully")
    except sqlite3.Error as e:
        print(e)
    finally:
        cursor.close()
        conn.close()


def load_data(database_name: str, table_name: str):
    """データベースからデータを読み込む"""
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(f"SELECT * FROM {table_name} ORDER BY timestamp DESC")
        result = cursor.fetchall()
        print(f"Contents of {table_name} table:")
        for row in result:
            print(row)
        return result
    except Error as e:
        print(e)
    finally:
        cursor.close()
        conn.close()


def get_date(offset):
    today = datetime.today()
    new_date = today + timedelta(days=offset)
    return new_date.strftime('%Y-%m-%d')


# テスト
# create_total_table("daily_total")
# create_total_table("monthly_total")
# create_total_table("yearly_total")

save_total_records("daily_total", get_date(0))
save_total_records("daily_total", get_date(-1))

load_data(DB_FILE, "daily_total")