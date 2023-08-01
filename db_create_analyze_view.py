from datetime import datetime
from time import sleep

from db_thread_detail_data import execute_sql_query
from db_thread_detail_data import create_view_daily_comment_count
from db_thread_detail_data import create_view_daily_unique_id_percentage
from db_thread_detail_data import create_view_hourly_comment_count
from helper import calc_similarity, measure_time

# 板の名前
NANG = "livegalileo"
NANU = "liveuranus"
KENMO = "news1"

def create_views(board):
    table_name = "db_" + board
    view_name = "view_" + board
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        create_view_daily_comment_count(table_name, view_name)
        create_view_hourly_comment_count(table_name, view_name)
        create_view_daily_unique_id_percentage(table_name, view_name)

    except Exception as e:
        print(f"{now}[ERROR]: {e}")


def main():
    try:
        return create_views(KENMO)
    except Exception as e:
        print(f"[ERROR]: {e}")
    
if __name__ == "__main__":
    board = KENMO
    view_name = "view_" + board
    day = f"{view_name}_daily_comment_count"
    hour = f"{view_name}_hourly_comment_count"
    id = f"{view_name}_daily_unique_id_percentage"
    
    main()
    sql = f'select * from {day}'
    
    result = execute_sql_query(sql)
    print(result)