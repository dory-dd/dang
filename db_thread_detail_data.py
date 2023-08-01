import sqlite3
import re
from datetime import datetime
import locale
import traceback

DATABASE = '/mnt/d/database/test_db.db'
locale.setlocale(locale.LC_TIME, 'ja_JP.UTF-8')


def execute_sql_query(query, params=None, many=False):
    """
    SQLクエリを実行してその結果を返す。

    Args:
        query (str): 実行するSQL文
        params (list): プレースホルダの値を指定する場合に使用する。デフォルトはNone。
        many (bool): executemanyを使用する場合にTrueに設定する。デフォルトはFalse。

    Returns:
        list: 実行結果の取得に成功した場合は、取得したレコードのリストを返す。エラーが発生した場合は、Noneを返す。
    """
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            if params is None:
                cursor.execute(query)
            else:
                if many:
                    cursor.executemany(query, params)
                else:
                    cursor.execute(query, params)
            conn.commit()
            result = cursor.fetchall()
            return result
    except Exception as e:
        # エラーが発生した場合
        t = list(traceback.TracebackException.from_exception(e).format())
        print(f"Error executing SQL query: {query}")
        print(f"Error message: {str(t)}")
        print(f"Values causing the error: {params}")
        # with open("params.txt", "w") as f:
        #     pprint.pprint(params, stream=f)
        raise e


def insert_to_table(table_name, data_list):
    pattern = re.compile(r'<[^>]*?>')

    # プレースホルダーを使用してSQLクエリを構築する
    sql = f"""
        INSERT INTO {table_name} (thread_key, res_num, name, watcchoi, email, comment_time, post_id, comment, thread_title)
        SELECT 
            ? AS thread_key,
            ? AS res_num,
            ? AS name,
            ? AS watcchoi,
            ? AS email,
            ? AS comment_time,
            ? AS post_id,
            ? AS comment,
            ? AS thread_title
        WHERE NOT EXISTS (
            SELECT 1
            FROM {table_name}
            WHERE thread_key = ?
            AND res_num = ?
        )
    """
    # パラメーターリストを生成する
    params_list = []
    for thread_data in data_list:
        try:
            values = []
            thread_key = thread_data[0]
            res_num = thread_data[1]
            name = str(thread_data[2])
            watcchoi = str(thread_data[3])
            email = str(thread_data[4])
            comment_time_str = thread_data[5]
            comment_time_str_without_owner = comment_time_str
            date_obj = datetime.strptime(comment_time_str_without_owner, '%Y/%m/%d(%a) %H:%M:%S.%f')
            comment_time = date_obj.strftime('%Y-%m-%d %H:%M:%S.%f')
            post_id = str(thread_data[6].replace("主", "").strip())
            comment = str(thread_data[7])
            thread_title = thread_data[8]
        except ValueError as e:
            print(f"error:{e}")
            continue

        # プレースホルダーに値を追加する
        values.extend([thread_key, res_num, name, watcchoi, email, comment_time, post_id, comment, thread_title, thread_key, res_num])
        params_list.append(values)

    # SQLを実行する
    execute_sql_query(sql, params_list, many=True)


def create_table_if_not_exists(table_name):
    sql = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        thread_key CHAR(11) NOT NULL,
        res_num INTEGER NOT NULL,
        name varchar(20),
        watcchoi varchar(30),
        email varchar(50),
        comment_time TIMESTAMP NOT NULL,
        post_id varchar(255),
        comment TEXT NOT NULL,
        thread_title varchar(100),
        PRIMARY KEY (thread_key, res_num)
    );
"""
    return execute_sql_query(sql)


def create_view_daily_comment_count(table_name, view_name):
    sql = f'''
        CREATE VIEW IF NOT EXISTS {view_name}_daily_comment_count AS
        SELECT strftime('%Y-%m-%d', comment_time) AS date, COUNT(*) AS sum_comment
        FROM {table_name}
        GROUP BY date
        ORDER BY date;
    '''
    return execute_sql_query(sql)


def create_view_hourly_comment_count(table_name, view_name):
    sql = f'''
        CREATE VIEW IF NOT EXISTS {view_name}_hourly_comment_count AS
        SELECT strftime('%Y-%m-%d %H:00:00.00', comment_time) AS date_hour, COUNT(*) AS comment_count
        FROM {table_name}
        GROUP BY date_hour
        ORDER BY date_hour;
    '''
    return execute_sql_query(sql)


def create_view_daily_unique_id_percentage(table_name, view_name):
    sql = f"""
        CREATE VIEW IF NOT EXISTS {view_name}_daily_unique_id_percentage AS
        WITH t1 AS (
            SELECT date(comment_time) AS date, COUNT(*) AS count
            FROM (
                SELECT post_id, COUNT(*) AS cnt, comment_time
                FROM {table_name}
                GROUP BY post_id
                HAVING cnt = 1
            ) t
        GROUP BY date(comment_time)
        ), t2 AS (
            SELECT date(comment_time) AS date, COUNT(*) AS count
            FROM {table_name}
            GROUP BY date(comment_time)
        ), t3 AS (
            SELECT date(comment_time) AS date, COUNT(post_id) AS count
            FROM {table_name}
            WHERE thread_key IN (SELECT thread_key FROM {table_name} WHERE comment LIKE '%!idchange%')
            GROUP BY date(comment_time)
        )
        SELECT date(t1.date) AS date, ROUND(CAST(t1.count AS REAL) / (CAST(t2.count AS REAL) - CAST(t3.count AS REAL)) * 100, 2) AS percentage
        FROM t1
        INNER JOIN t2 ON t1.date = t2.date
        INNER JOIN t3 ON t1.date = t3.date;
    """
    return execute_sql_query(sql)
