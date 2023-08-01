import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import japanize_matplotlib
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db_thread_detail_data import execute_sql_query
import numpy as np
import seaborn as sns


id_view = "daily_unique_id_percentage"
sum_view = "view_{board}_daily_comment_count"
TABLE_NAME = "bbs_threads_test"


def count_posts_with_isolation_rate(board):
    sql = f"""
        SELECT view_{board}_daily_comment_count.date, view_{board}_daily_comment_count.sum_comment, daily_unique_id_percentage.percentage
        FROM view_{board}_daily_comment_count 
        JOIN daily_unique_id_percentage ON view_{board}_daily_comment_count.date = daily_unique_id_percentage.date
        WHERE view_{board}_daily_comment_count.date >= '2000-01-01';
    """
    sns.set(font=['IPAexGothic'])
    data = execute_sql_query(sql)
    df = pd.DataFrame(data, columns=['date', 'sum_comment', 'daily_unique_id_percentage'])
    fig, ax1 = plt.subplots(figsize=(10,6))

    # 書き込み件数の棒グラフを描画する
    ax1.bar(df['date'], df['sum_comment'], color='tab:blue', label='書き込み回数')
    ax1.set_xlabel('日付')
    ax1.set_ylabel('書き込み回数')

    # ユニークIDパーセンテージの折れ線グラフを描画する
    ax2 = ax1.twinx()
    ax2.plot(df['date'], df['daily_unique_id_percentage'], color='tab:red', label='単発ID率[%]')
    ax2.set_ylabel('単発ID率[%]')

    # グラフのタイトルと凡例を設定する
    ax1.set_title('書き込み回数と単発ID率[%]')
    ax1.legend(loc='upper left', prop={'size': 10})
    ax2.legend(loc='upper right', prop={'size': 10})
    ax2.set_ylim([0, 50])

    st.pyplot(fig)


def plot_carrier_percentage():
    # SQLクエリの実行
    sql = "SELECT date, carrier, percentage FROM create_view_daily_carrier_counts_with_percent WHERE date >= '2023-03-13'"
    data = execute_sql_query(sql)

    # タプルからDataFrameに変換
    df = pd.DataFrame(data, columns=['date', 'carrier', 'percentage'])

    # 日付をdatetime型に変換
    df['date'] = pd.to_datetime(df['date'])

    # グラフの描画
    sns.set(style="darkgrid", font=['IPAexGothic'])
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.lineplot(x='date', y='percentage', hue='carrier', data=df, ax=ax)

    # グラフの設定
    ax.set(xlabel='Date', ylabel='Percentage')
    ax.set_title('キャリアごとの書き込み[%]')
    plt.xticks(rotation=45)

    # グラフの表示
    st.pyplot(fig)



def plot_histogram():
    sql = f"SELECT COUNT(*) AS count FROM {TABLE_NAME} GROUP BY post_id ORDER BY count DESC"
    post_count_list = execute_sql_query(sql)
    # IDなしのカウントを削除する
    if len(str(post_count_list[0])) >= 4:
        del post_count_list[0]

    # 数値以外の要素を削除する
    post_count_list = np.array([count[0] for count in execute_sql_query(sql) if isinstance(count[0], int)])
    

    # 平均、中央値、標準偏差を計算
    mean_value = np.mean(post_count_list)
    median_value = np.median(post_count_list)
    std_value = np.std(post_count_list)

    # 対数軸のKDEプロットを作成
    fig, ax = plt.subplots()
    sns.kdeplot(x=post_count_list, ax=ax, log_scale=True, color='steelblue', linewidth=3, alpha=0.7, fill=True, facecolor='lightblue')
    ax.set_xlim(1, 100)
    ax.set_ylim(0.001, 3.5)
    ax.set_title('ID別書き込み回数のヒストグラム')
    ax.set_xlabel('書き込み回数')
    ax.set_ylabel('頻度 (log scale)')

    # 平均、中央値、標準偏差をグラフに追加
    ax.axvline(mean_value, color='red', linestyle='dashed', label=f'平均: {mean_value:.2f}')
    ax.axvline(median_value, color='green', linestyle='dashed', label=f'中央値: {median_value:.2f}')
    ax.axvline(std_value, color='orange', linestyle='dashed', label=f'標準偏差: {std_value:.2f}')

    # 凡例を表示
    plt.legend(fontsize=10)

    # Seabornのスタイルを変更
    sns.set_style("whitegrid", font=['IPAexGothic'])
    sns.set_palette("husl")

    # Streamlitに表示
    st.pyplot(fig)


def plot_hourly_comment_counts():
    # hourly_comment_countビューからデータを取得する
    sql = "SELECT * FROM hourly_comment_count"
    hourly_comment_counts = execute_sql_query(sql)

    
    # データフレームを作成する
    hourly_comment_counts = pd.DataFrame(hourly_comment_counts, columns=["date_hour", "count"])

    # 移動平均を計算する
    hourly_comment_counts["moving_average"] = hourly_comment_counts["count"].rolling(window=12).mean()

    # グラフを作成する
    fig, ax = plt.subplots(figsize=(10, 6))

    # 日付のフォーマットを変換し、yyyymmddのみを抽出
    # hourly_comment_counts['date'] = pd.to_datetime(hourly_comment_counts['date_hour'], format='%Y-%m-%d %H:%M:%S').dt.strftime('%Y%m%d')
    # print(hourly_comment_counts['date'].dtypes)
    # hourly_comment_counts = hourly_comment_counts.drop(columns=['date_hour'])

    # 日付でグループ化して件数を集計
    # view_{board}_daily_comment_counts = hourly_comment_counts.groupby('date').sum()

    # 棒グラフで書き込み数を表示する
    sns.barplot(x='date_hour', y='count', data=hourly_comment_counts, color='steelblue', ax=ax)

    # 移動平均を折れ線グラフで表示する
    sns.lineplot(x=hourly_comment_counts['date_hour'], y=hourly_comment_counts["moving_average"], color='orange', linewidth=2, label='移動平均', ax=ax)

    # 軸のラベルとタイトルのフォントサイズを大きくする
    ax.tick_params(labelsize=14)
    ax.set_title("時間別コメント数", fontsize=18)
    ax.set_xlabel("時間", fontsize=14)
    ax.set_ylabel("コメント数", fontsize=14)

    # 凡例を表示する
    ax.legend(fontsize=14)

    # Seabornのテーマを適用する
    sns.set_style('whitegrid')
    sns.set_palette('husl')


    # Streamlitにグラフを表示する
    st.pyplot(fig)

    

def show_data():
    # 書き込み回数と孤立ID率のグラフを作成
    count_posts_with_isolation_rate()
    
    # キャリア別の書き込み率を作成
    plot_carrier_percentage()
    
    # 時間別の書き込み数グラフを作成
    plot_hourly_comment_counts()



# メインのStreamlitアプリケーション
def main():
    st.title('3G 書き込み数推移')
    show_data()


if __name__ == '__main__':
    main()
