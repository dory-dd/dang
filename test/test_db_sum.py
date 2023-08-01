from datetime import datetime, date
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from my_tables import create_tables, drop_tables, Thread, DailyTotal, MonthlyTotal, YearlyTotal
from my_functions import save_daily_total, save_monthly_total, save_yearly_total, save_total_by_date

# テスト用データベースの作成
engine = create_engine('sqlite:///:memory:', echo=False)
create_tables(engine)
Session = sessionmaker(bind=engine)

# テスト用データの作成
thread_data = [
    {'thread_id': '1', 'thread_date': datetime(2022, 2, 20), 'res_number': 5},
    {'thread_id': '1', 'thread_date': datetime(2022, 2, 20), 'res_number': 3},
    {'thread_id': '1', 'thread_date': datetime(2022, 2, 21), 'res_number': 2},
    {'thread_id': '2', 'thread_date': datetime(2022, 2, 21), 'res_number': 4},
    {'thread_id': '2', 'thread_date': datetime(2022, 2, 22), 'res_number': 6},
]
daily_total_data = [
    {'date': date(2022, 2, 20), 'total_res': 8},
    {'date': date(2022, 2, 21), 'total_res': 6},
    {'date': date(2022, 2, 22), 'total_res': 6},
]
monthly_total_data = [
    {'month': '202202', 'total_res': 20},
]
yearly_total_data = [
    {'year': '2022', 'total_res': 20},
]

@pytest.fixture
def session():
    # テスト用データの追加
    with Session() as session:
        session.add_all([Thread(**d) for d in thread_data])
        session.add_all([DailyTotal(**d) for d in daily_total_data])
        session.add_all([MonthlyTotal(**d) for d in monthly_total_data])
        session.add_all([YearlyTotal(**d) for d in yearly_total_data])
        session.commit()
    yield session
    # テスト用データの削除
    with Session() as session:
        session.query(Thread).delete()
        session.query(DailyTotal).delete()
        session.query(MonthlyTotal).delete()
        session.query(YearlyTotal).delete()
        session.commit()
    drop_tables(engine)

def test_save_daily_total(session):
    save_daily_total(engine, session)
    # daily_total_tableに正しく保存されたかをチェック
    with Session() as session:
        daily_totals = session.query(DailyTotal).order_by(DailyTotal.date).all()
        assert len(daily_totals) == 3
        assert daily_totals[0].date == date(2022, 2, 20)
        assert daily_totals[0].total_res == 8
        assert daily_totals[1].date == date(2022, 2, 21)
        assert daily_totals[1].total_res == 6
        assert daily_totals[2].date == date.today()
        assert daily_totals[2.].total_res == 0


def test_save_monthly_total(session):
    save_monthly_total(engine, session)
    # monthly_total_tableに正しく保存されたかをチェック
    with Session() as session:
        monthly_totals = session.query(MonthlyTotal).all()
        assert len(monthly_totals) == 1
        assert monthly_totals[0].month == '202202'
        assert monthly_totals[0].total_res == 20


def test_save_yearly_total(session):
    save_yearly_total(engine, session)
    # yearly_total_tableに正しく保存されたかをチェック
    with Session() as session:
        yearly_totals = session.query(YearlyTotal).all()
        assert len(yearly_totals) == 1
        assert yearly_totals[0].year == '2022'
        assert yearly_totals[0].total_res == 20


def test_save_total_by_date(session):
    save_total_by_date(engine, session, 'daily_total')
    # daily_total_tableに正しく保存されたかをチェック
    with Session() as session:
        daily_totals = session.query(DailyTotal).order_by(DailyTotal.date).all()
        assert len(daily_totals) == 3
        assert daily_totals[0].date == date(2022, 2, 20)
        assert daily_totals[0].total_res == 8
        assert daily_totals[1].date == date(2022, 2, 21)
        assert daily_totals[1].total_res == 6
        assert daily_totals[2].date == date.today()
        assert daily_totals[2].total_res == 0


save_total_by_date(engine, session, 'monthly_total')
# monthly_total_tableに正しく保存されたかをチェック
with Session() as session:
    monthly_totals = session.query(MonthlyTotal).all()
    assert len(monthly_totals) == 1
    assert monthly_totals[0].month == '202202'
    assert monthly_totals[0].total_res == 20

save_total_by_date(engine, session, 'yearly_total')
# yearly_total_tableに正しく保存されたかをチェック
with Session() as session:
    yearly_totals = session.query(YearlyTotal).all()
    assert len(yearly_totals) == 1
    assert yearly_totals[0].year == '2022'
    assert yearly_totals[0].total_res == 20