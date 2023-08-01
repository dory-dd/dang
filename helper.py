import time
from datetime import datetime
import re
from db_thread_detail_data import execute_sql_query
from scraper import get_http_from_url


def sum_res_numbers_from_url(url: str) -> int:
    """
    タイトル一覧ページからレスの数のみを合計する
    """
    metadata = get_http_from_url(url)
    total = 0
    for item in metadata:
        # 正規表現を使って、()内の数字の部分だけを抽出する
        match = re.search(r'\((\d+)\)', item)
        if match:
            # 抽出した数字をint型に変換して、totalに足し合わせる
            total += int(match.group(1))
    return total


def measure_time(func, *args, **kwargs):
    """
    関数の実行時間を計算する
    """
    def format_elapsed_time(elapsed_time):
        """
        実行時間を分や時間に変換してフォーマットする
        """
        if elapsed_time < 60:
            return f"実行時間は {round(elapsed_time, 2)} 秒です"
        elif elapsed_time < 3600:
            minutes = int(elapsed_time / 60)
            seconds = elapsed_time % 60
            return f"実行時間は {minutes} 分 {round(seconds, 2)} 秒です"
        else:
            hours = int(elapsed_time / 3600)
            minutes = int((elapsed_time % 3600) / 60)
            seconds = elapsed_time % 60
            return f"実行時間は {hours} 時間 {minutes} 分 {round(seconds, 2)} 秒です"

    start_time = time.time()
    result = func(*args, **kwargs)
    end_time = time.time()
    elapsed_time = end_time - start_time
    return format_elapsed_time(elapsed_time)



def get_max_res_num(table_name, thread_key):
    max_res_num_query = 'SELECT MAX(res_num) FROM {table_name} WHERE thread_key = ?;'
    max_res_num = execute_sql_query(max_res_num_query.format(table_name=table_name), (thread_key,))[0][0]
    return max_res_num


def calc_similarity(table_name, subject_url):
    """
    初期構築時の検証用
    sum_res_numbers_from_urlとDBのレコード数を照合して、一致率を計算する
    """
    # SQLを定義する
    sql = f"SELECT COUNT(*) FROM {table_name}"
    # SQLを実行して結果を代入する
    result = execute_sql_query(sql)[0][0]
    # metadetaをスクレイピングし、レス数の合計をint形式で取得する
    correct_number = sum_res_numbers_from_url(subject_url)
    # 一致率を計算する
    similarity = 100 * min(result, correct_number) / max(result, correct_number)
    # 結果を表示する
    print(f"{table_name}の登録レコードは: {result}\n subject.txt合計値は: {correct_number}\n 一致率は:{similarity}%")

    return int(similarity), correct_number


def calculate_unique_post_id_ratio(table_name):
    """
    単発ID率を計算する
    """
    sql = f'''
        SELECT (COUNT(DISTINCT 
            CASE WHEN comment LIKE '%!idchange%' THEN NULL ELSE post_id END)*1.0
            /COUNT(CASE WHEN comment LIKE '%!idchange%' THEN NULL ELSE post_id END))*100.0
            AS unique_percentage 
        FROM {table_name};

    '''
    return execute_sql_query(sql)[0][0]


def count_records_between_dates(table_name, start_date, end_date):
    """
    from YYYYMMDD TO YYYYMMDD形式でレコードを抽出する
    """
    # 日時をパースして、DB認識できるフォーマットに変換する
    start_datetime = datetime.strptime(start_date, '%Y%m%d %H:%M')
    end_datetime = datetime.strptime(end_date, '%Y%m%d %H:%M')
    start_str = start_datetime.strftime('%Y-%m-%d %H:%M:%S')
    end_str = end_datetime.strftime('%Y-%m-%d %H:%M:%S')

    # SQLクエリを実行して結果を取得する
    sql = f"SELECT COUNT(*) FROM {table_name} WHERE comment_time >= ? AND comment_time <= ?"
    params = (start_str, end_str)

    return execute_sql_query(sql, params)[0][0]
