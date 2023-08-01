from db_thread_detail_data import execute_sql_query
from datetime import datetime, timedelta
from scipy.stats import mannwhitneyu
from pprint import pprint


def count_sections(last_hours=24, sql_query='', output_format='{hour} : {count}'):
    now = datetime.now()
    date_range = [(now - timedelta(hours=i)).strftime('%Y-%m-%d %H:%M')
                  for i in range(last_hours)]
    for i in range(len(date_range)-1):
        start_str = date_range[i]
        end_str = date_range[i+1]
        query = f"{sql_query} WHERE comment_time >= '{end_str}' AND comment_time <= '{start_str}'"
        section_count = execute_sql_query(query)[0][0]
        hour = i+1
        if section_count == 0:
            print(f"{hour}時間前 - データなし")
        else:
            print(output_format.format(
                hour=f"{end_str} - {start_str}", count=section_count))


def calc_similarity(table_name):
    # SQLを定義する
    sql = f"SELECT COUNT(*) FROM {table_name}"
    # SQLを実行して結果を代入する
    result = execute_sql_query(sql)[0][0]
    # metadetaをスクレイピングし、レス数の合計をint形式で取得する
    correct_number = sum_res_numbers_from_url(
        "https://hayabusa4.3chan.jp/livegalileo/subject.txt")
    # 一致率を計算する
    similarity = 100 * min(result, correct_number) / \
        max(result, correct_number)
    # 結果を表示する
    print(
        "======================================\n"
        f"{table_name}の登録レコードは: {result}\n"
        # f"正しいレコード数は:{correct_number}\n"
        f"一致率は:         {int(similarity)}%\n"
        "======================================"
    )

    return int(similarity), correct_number


def make_3ch_urls(thread_keys):
    urls = []
    for thread_key in thread_keys:
        urls.append(
            f"https://hayabusa4.3chan.jp/test/read.cgi/livegalileo/{thread_key[0]}/")
    return urls


def search_insect_threads(table_name):
    sql = f'''
        SELECT thread_key
        FROM {table_name}
        WHERE post_id IN 
            (SELECT post_id
            FROM {table_name}
            WHERE res_num = 1
            GROUP BY  post_id
            HAVING COUNT(post_id) = 1 )
                AND comment NOT LIKE '%!idchange%'
                AND post_id NOT LIKE '%0'
                AND comment LIKE (thread_title LIKE '%wwww%'
                OR thread_title LIKE '%←%'
                OR thread_title LIKE '%弱者%'
                OR thread_title LIKE '%チー牛%')
        GROUP BY  thread_key;
    '''
    thread_keys = execute_sql_query(sql)
    # urls = make_3ch_urls(thread_keys)

    return thread_keys


def toukei(table_name, thread_key):
    # 全体のポスト数を集計
    sql = f"SELECT COUNT(*) FROM {table_name} GROUP BY post_id"
    post_count_list = execute_sql_query(sql)
    # IDなしのカウントを削除する
    if len(str(post_count_list[0])) >= 4:
        print(f"{post_count_list[0]} deleted!")
        del post_count_list[0]
    # 数値以外の要素を削除する
    post_count_list = [count[0] for count in post_count_list if isinstance(count[0], int)]
    # post_count_listの要素数を取得する
    all_post = len(post_count_list)    
    
    # threadのポスト数を集計
    sql2 = f"SELECT COUNT(*) FROM {table_name} WHERE thread_key = '{thread_key}' GROUP BY post_id"
    # 数値以外の要素を削除する
    thread_post_count_list = [count[0] for count in execute_sql_query(sql2) if isinstance(count[0], int)]
    # thread_post_count_listの要素数を取得する
    thread_post = len(thread_post_count_list) 

    # Mann-Whitney Uテストを実行する
    if all_post == 0 or thread_post == 0:
        print("データ数が0なので、Mann-Whitney Uテストは実行できません")
    else:
        statistic, pvalue = mannwhitneyu(post_count_list, thread_post_count_list)
    
    return thread_key,statistic,pvalue


def get_topid_from_keyword(table_name, target_colum, keywords, date=""):
    or_conditions = " OR ".join([f"{target_colum} LIKE '%{kw}%'" for kw in keywords])
    if or_conditions:
        or_conditions = "WHERE " + or_conditions
    if date:
        date_condition = f"AND comment_time LIKE '%{date}%'"
    else:
        date_condition = ""
    sql = f'''
        SELECT res_num, thread_key, comment
        FROM {table_name}
        {or_conditions}
        AND thread_key = "1679099922"
        AND res_num >= "820"
        {date_condition}
        -- GROUP BY post_id
        -- ORDER BY cnt DESC
    '''
    fax_comments = execute_sql_query(sql)
    fax_comments = list(fax_comments)
    fax_comments.append("\n")  # 末尾に改行コードを追加
    #with open("fax_comment.txt", "w") as f:
    #    f.write("".join(str(comment) for comment in fax_comments)) 
    return fax_comments


def get_idetc_from_keyword_list(table_name, target_column, keywords_list, date=""):
    placeholders = ','.join(['?' for _ in keywords_list])
    sql = f'''
        SELECT post_id, thread_title, comment
        FROM {table_name}
        WHERE comment_time = ?
        AND {target_column} IN ({placeholders})
     '''
    # values = [f'%{date}%', *keywords_list]
    # results = execute_sql_query(sql, values, many=True)
    results = execute_sql_query(sql, [keywords_list], many=True)
    return results


def read_file(filename):
    """
    テキストファイルを読み込み、各列をリストに格納する関数。
    """
    with open(filename, 'r') as f:
        # ファイルの各行をリストに格納する
        lines = f.readlines()

    # 各列をリストに格納するための空のリストを用意する
    columns = [[] for _ in range(len(lines[0].split()))]

    # 各行をタブ(\t)で分割し、各列のリストに要素を格納する
    for line in lines:
        values = line.split("\n")
        for i, value in enumerate(values):
            columns[i].append(value)
    return columns[0]


if __name__ == "__main__":
    NANG = "livegalileo"
    NANU = "liveuranus"
    
    board = NANU
    
    table_name = "db_" + board
    id_view = "daily_unique_id_percentage"
    sum_day_view = "daily_comment_count"
    sum_hour_view = "hourly_comment_count"

    result = execute_sql_query(f"select thread_title, res_num, comment from {table_name} where post_id like '%EAfVPoIO0%'")
    # section = count_sections(last_hours=48, sql_query=f"select count(*) from {table_name}")
    # result = calculate_unique_post_id_ratio(table_name, , '2023-03-14 23:59')
    # insect = search_insect_threads(table_name)
    # result = create_view_daily_unique_id_percentage(table_name)
    #result = create_view_hourly_comment_count(table_name)
    #sql = f'SELECT thread_title FROM {table_name} WHERE thread_title LIKE "%要注意%" and comment_time LIKE "%2023-03-18%"'
    #result = execute_sql_query(sql)
    # result = make_3ch_urls(result)
    #result = toukei(table_name, 1678983587)
    #result = best_anker_100(table_name)

    #tikutiku = ["アフィ","あふぃ","アフィリエイト","対立煽り","FAX","ちび","ちびび","過疎","キッモ","キッモ","キモ","きも","つまらん","死ね","氏ね","しね","あっそ","だから","きもちわり","逃亡","帰れ","かえれ","つまんね","つまんない"]
    #fax_word = ["酸妄","在る","在るな","下民", "折れ","マンカス","だからな","どうする？","である","FAX時代","FAX氏","ノレカス","鼻ゴミ","障害者共","知恵遅れ"]
    #fax_word = read_file(f"{memo_path}fax_shine.txt")
    #fax_word =[""]
    #date = '2023-03-18'
    #result = get_topid_from_keyword(table_name, "res_num", fax_word)
    print(result)
    #print(execute_sql_query(f"select comment from {table_name} where post_id = 'UV2WEPZv0B'"))