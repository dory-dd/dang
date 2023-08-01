from datetime import datetime
from time import sleep
from scraper import main as scraper_main
from db_thread_detail_data import execute_sql_query
from db_thread_detail_data import create_table_if_not_exists
from db_thread_detail_data import insert_to_table
from helper import calc_similarity, measure_time

# 板の名前
NANG = "livegalileo"
NANU = "liveuranus"
KENMO = "news1"

# 巡回リスト
CRONING_BOARD = [NANG, NANU]

def cronning_board(board, kako=False):
    table_name = "db_" + board
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        scraped_data =  scraper_main(board,kako)
        create_table_if_not_exists(table_name)
        insert_to_table(table_name, scraped_data)
        
        record_count = execute_sql_query(f"select count(*) from {table_name}")[0][0]
        invild_count = execute_sql_query(f"select count(*) from {table_name} where name = 'invild data'")[0][0]
        
        print(f"{now}: {board} [OK]: Record count: {record_count} Invild count: {invild_count}")

    except Exception as e:
        print(f"{now}[ERROR]: {e}")


def main():
    # cronning_board(NANG)
    # sleep(5)
    # cronning_board(NANU)
    # sleep(5)
    cronning_board(NANG, kako=True)
    
if __name__ == "__main__":
    print(measure_time(main))