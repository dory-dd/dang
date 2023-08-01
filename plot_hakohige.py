from db_thread_detail_data import execute_sql_query
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import mannwhitneyu
import pandas as pd
from ydata_profiling import ProfileReport as pdp
PATH = "/mnt/d/Pictures/image/df_ProfileReport/"


def plot_boxplot(table_name, thread_key):
    # データの取得
    sql = f"SELECT COUNT(*) FROM {table_name} GROUP BY post_id"
    post_count_list = [count[0] for count in execute_sql_query(sql) if isinstance(count[0], int)]
    sql2 = f"SELECT COUNT(*) FROM {table_name} WHERE thread_key = '{thread_key}' GROUP BY post_id"
    thread_post_count_list = [count[0] for count in execute_sql_query(sql2) if isinstance(count[0], int)]
    
    # Mann-Whitney Uテストの実行
    statistic, pvalue = mannwhitneyu(post_count_list, thread_post_count_list)

    # プロットの設定
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.boxplot(x=thread_post_count_list, ax=ax, whis=[2.5, 97.5]) # 95%信頼区間を指定
    ax.set_xscale('log')
    ax.set_yscale('log')

    # タイトルやラベルの設定
    ax.set_title(f"Mann-Whitney U test for thread {thread_key}", fontsize=16)
    ax.set_xlabel("Thread Post Count", fontsize=12)
    ax.set_ylabel("Post Count Distribution", fontsize=12)

    # 結果の表示
    ax.text(0.05, 0.9, f"Mann-Whitney U test result:\nstatistic={statistic:.2f}, p-value={pvalue:.4f}",
            transform=ax.transAxes, fontsize=12, bbox=dict(facecolor='gray', alpha=0.2))

    # x軸とy軸の範囲を設定
    ax.set_ylim(bottom=min(post_count_list+thread_post_count_list)/2)
    ax.set_xlim(right=max(post_count_list+thread_post_count_list)*1.1)

    # グラフの保存
    plt.savefig(f"/mnt/d/Pictures/image/hakohige/{thread_key}_figure.png")


def get_ids_without_idchange(table_name):
    # データの取得
    sql = f"""
        SELECT DISTINCT post_id FROM {table_name}
        WHERE post_id NOT IN (
            SELECT post_id
            FROM {table_name}
            WHERE thread_key IN (
                SELECT thread_key
                FROM {table_name}
                WHERE comment LIKE '%!idchange%'
            )
        )
    """
    return execute_sql_query(sql)


def analyze_ids(ids):
    result = {}
    for id in ids:
        id_str = id[0]  # idはタプルで格納されているので、文字列に変換する必要があります
        if len(id_str) == 9:
            carrier = id_str[-1]
        elif len(id_str) == 10:
            carrier = id_str[-2]
        else:
            print(id)

        carrier_names = {
            "0": "固定回線",
            "d": "docomo",
            "a": "au",
            "r": "softbank_ipv4",
            "p": "softbank_ipv6",
            "M": "MVNO",
            "H": "no_reverse_lookup",
            "8": "VPN"
        }

        carrier_name = carrier_names.get(carrier)
        if carrier_name:
            result[carrier_name] = result.get(carrier_name, 0) + 1

    total_count = sum(result.values())
    for key, value in result.items():
        percentage = (value / total_count) * 100
        percentage
        print(f"{key}: {value} ({percentage:.2f}%)")

    return result


def carrier_name_master():
    table_name = "carrier_name_master"
    sql = f"""
        CREATE TABLE IF NOT EXISTS carrier_name_master (
        carrier_code CHAR(1) PRIMARY KEY,
        carrier_name VARCHAR(20) NOT NULL
        );
        """

    insert_sql = """
        INSERT INTO carrier_name_master (carrier_code, carrier_name)
        VALUES
        ('0', '固定回線'),
        ('d', 'docomo'),
        ('a', 'au'),
        ('r', 'softbank_ipv4'),
        ('p', 'softbank_ipv6'),
        ('M', 'MVNO'),
        ('H', 'no_reverse_lookup'),
        ('8', 'VPN');
    """
    if execute_sql_query(sql) is None:
        print("carrier_name_master was created!")
        return execute_sql_query(insert_sql)


def create_view_daily_carrier_counts_with_percent(table_name):
    sql = f"""
        CREATE VIEW IF NOT EXISTS create_view_daily_carrier_counts_with_percent AS
        SELECT
            strftime('%Y-%m-%d', comment_time) AS date,
            cn.carrier_name AS carrier,
            COUNT(*) AS count,
            ROUND(COUNT(*) * 1.0 / SUM(COUNT(*)) OVER (PARTITION BY strftime('%Y-%m-%d', comment_time)) * 100, 2) AS percentage
        FROM (
            SELECT
                post_id,
                CASE
                WHEN LENGTH(post_id) = 9 THEN SUBSTR(post_id, -1, 1)
                WHEN LENGTH(post_id) = 10 THEN SUBSTR(post_id, -2, 1)
                ELSE NULL
                END AS carrier_code,
                comment_time
            FROM {table_name}
            WHERE post_id IN (
                SELECT DISTINCT post_id FROM {table_name}
                WHERE post_id NOT IN (
                    SELECT post_id
                    FROM {table_name}
                    WHERE thread_key IN (
                        SELECT thread_key
                        FROM {table_name}
                        WHERE comment LIKE '%!idchange%'
                    )
                )
            )
        ) AS sub
        JOIN carrier_name_master AS cn ON sub.carrier_code = cn.carrier_code
        GROUP BY strftime('%Y-%m-%d', comment_time), cn.carrier_name, sub.carrier_code
        ORDER BY date DESC, count DESC;
    """
    return execute_sql_query(sql)


if __name__ == "__main__":
    table_name = "bbs_threads_test"
    id_view = "daily_unique_id_percentage"
    sum_day_view = "daily_comment_count"
    sum_hour_view = "hourly_comment_count"

    #plot_boxplot(table_name, 1678988403)
    #ids = get_ids_without_idchange(table_name)
    #result = analyze_ids(ids)
    #result = carrier_name_master()
    result = create_view_daily_carrier_counts_with_percent(table_name)
    print(result)