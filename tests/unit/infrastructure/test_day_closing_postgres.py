from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from os import environ
from threading import Event
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

from sqlalchemy import create_engine, func, literal, text
from sqlalchemy.orm import sessionmaker

from tests.utils import DbUtils, ObjectGenerator, PayloadGenerator, RequestGenerator

environ.setdefault("DATABASE_URL", DbUtils.database_url())


def test_account_closed_between_listing_and_lock_is_not_processed(monkeypatch):
    DbUtils.rollback()
    import database
    from controllers import AccountController, DayClosingController

    engine = create_engine(DbUtils.database_url())
    monkeypatch.setattr(database, "SessionLocal", sessionmaker(bind=engine, autoflush=False))
    account = ObjectGenerator.create_funded_account(200000)
    key, token = account["account_key"], account["account_token"]
    assert RequestGenerator.POST_saving(key, token, PayloadGenerator.saving(amount=200000))[0] == 201
    assert RequestGenerator.POST_redemption(key, token, PayloadGenerator.redemption(amount=200000))[0] == 201
    assert RequestGenerator.POST_withdrawal(key, token, PayloadGenerator.withdrawal(amount=200000))[0] == 201

    def snapshot():
        with engine.connect() as connection:
            values = connection.execute(text("SELECT xp, rank_id, yield_rank_id, piggy_record, grace_until FROM account WHERE account_key=:key"), {"key": key}).one()
            events = connection.execute(text("SELECT count(*) FROM rank_event e JOIN account a ON a.id=e.account_id WHERE a.account_key=:key"), {"key": key}).scalar()
            return tuple(values), events

    before = snapshot()
    listed, resume = Event(), Event()

    def run_closing():
        context = database.open_context()
        try:
            controller = DayClosingController()
            original = controller.account_repository.list_open_customer_accounts

            def pause_after_listing():
                rows = original()
                listed.set()
                assert resume.wait(30), "encerramento nao liberou a virada"
                return rows

            controller.account_repository.list_open_customer_accounts = pause_after_listing
            controller.bcb_connector.get_cdi_rate = Mock(return_value=None)
            controller.gamification_controller.award_record_xp = Mock(wraps=controller.gamification_controller.award_record_xp)
            result = controller.close_day({"accounting_date": "2026-06-01"})
            assert controller.gamification_controller.award_record_xp.call_count == 0
            return result
        finally:
            if context.db_session is not None:
                context.db_session.close()
            database.clear_context()

    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(run_closing)
            try:
                assert listed.wait(30), "virada nao chegou a listagem"
                context = database.open_context()
                try:
                    AccountController().close_account(key, token)
                finally:
                    if context.db_session is not None:
                        context.db_session.close()
                    database.clear_context()
            finally:
                resume.set()
            assert future.result(timeout=30) == {"closed_date": "2026-06-01", "accounting_date": "2026-06-02"}
        assert RequestGenerator.GET_account(key, token)[1]["status"] == "CLOSED"
        assert snapshot() == before
    finally:
        engine.dispose()


def test_auth_failure_window_boundary_and_expiration_without_sleep(monkeypatch):
    DbUtils.rollback()
    from models import RequestLog
    from repositories import RequestLogRepository
    from repositories import request_log_repository as module

    engine = create_engine(DbUtils.database_url())
    factory = sessionmaker(bind=engine)
    monkeypatch.setattr(module, "SessionLocal", factory)
    now = [datetime(2026, 10, 8, 12)]
    monkeypatch.setattr(module, "func", SimpleNamespace(count=func.count, now=lambda: literal(now[0])))
    account_key = str(uuid4())
    with factory() as session:
        for age in [timedelta(minutes=15, microseconds=1), timedelta(minutes=15), timedelta(0)]:
            session.add(RequestLog(request_log_key=str(uuid4()), request_id=str(uuid4()),
                                   created_at=now[0] - age, method="GET", path="/probe", status=404,
                                   error_code="QIT001010", client_ip="127.0.0.1", account_key=account_key,
                                   auth_failure="ACCOUNT"))
        session.commit()
    repository = RequestLogRepository()
    try:
        assert repository.count_auth_failures("127.0.0.1", ["ACCOUNT"], 15, account_key) == 2
        assert repository.count_auth_failures("127.0.0.1", ["ACCOUNT"], 15, str(uuid4())) == 0
        now[0] += timedelta(minutes=15)
        assert repository.count_auth_failures("127.0.0.1", ["ACCOUNT"], 15, account_key) == 1
        now[0] += timedelta(microseconds=1)
        assert repository.count_auth_failures("127.0.0.1", ["ACCOUNT"], 15, account_key) == 0
    finally:
        engine.dispose()


def test_zeroed_lot_keeps_its_fraction_and_new_saving_creates_an_independent_lot():
    from decimal import Decimal
    from tests.utils import DbUtils, MockGenerator, ObjectGenerator, PayloadGenerator, RequestGenerator
    from database import DATABASE_URL
    from sqlalchemy import create_engine, text

    DbUtils.rollback()
    engine = create_engine(DATABASE_URL)
    account = ObjectGenerator.create_funded_account(1000)
    key, token = account["account_key"], account["account_token"]

    def lots():
        with engine.connect() as connection:
            return connection.execute(text("SELECT l.id, l.principal_remaining, l.yield_remaining, l.residue FROM lot l JOIN category c ON c.id = l.category_id JOIN account p ON p.id = c.account_id JOIN account a ON a.id = p.parent_account_id WHERE a.account_key = :key ORDER BY l.id"), {"key": key}).all()

    try:
        assert RequestGenerator.POST_saving(key, token, PayloadGenerator.saving(amount=1000))[0] == 201
        MockGenerator.set_cdi_rate("2026-06-01", "0.054266")
        assert RequestGenerator.POST_day_closing(PayloadGenerator.day_closing("2026-06-01"))[0] == 200
        old_id = lots()[0].id
        assert lots()[0][1:] == (1000, 0, Decimal("0.54266000"))
        assert RequestGenerator.POST_redemption(key, token, PayloadGenerator.redemption(amount=1000))[0] == 201
        assert lots()[0][1:] == (0, 0, Decimal("0.54266000"))
        assert RequestGenerator.POST_saving(key, token, PayloadGenerator.saving(amount=1000))[0] == 201
        assert len(lots()) == 2 and lots()[1].id != old_id
        assert lots()[1][1:] == (1000, 0, Decimal("0.00000000"))
        for day, expected_yield, expected_residue in [("2026-06-02", 0, "0.54266000"),
                                                      ("2026-06-03", 1, "0.08532000")]:
            MockGenerator.set_cdi_rate(day, "0.054266")
            assert RequestGenerator.POST_day_closing(PayloadGenerator.day_closing(day))[0] == 200
            assert lots()[0][1:] == (0, 0, Decimal("0.54266000"))
            assert lots()[1][1:] == (1000, expected_yield, Decimal(expected_residue))
            status, summary = RequestGenerator.GET_account(key, token)
            assert status == 200, summary
            assert (summary["piggy_bank_balance"], summary["piggy_bank_gross_yield"]) == (1000 + expected_yield, expected_yield)
    finally:
        for day in ["2026-06-01", "2026-06-02", "2026-06-03"]:
            MockGenerator.clear_cdi(day)
        engine.dispose()
