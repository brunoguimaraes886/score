from concurrent.futures import ThreadPoolExecutor, TimeoutError
from datetime import date
from os import environ
from threading import Event
from unittest.mock import Mock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from tests.utils import DbUtils, MockGenerator, ObjectGenerator, PayloadGenerator, RequestGenerator

environ.setdefault("DATABASE_URL", DbUtils.database_url())


def run_waiting_closing(started, resume, cdi_available=True):
    import database
    from controllers import DayClosingController
    from errors import CdiUnavailable

    context = database.open_context()
    try:
        controller = DayClosingController()

        def get_cdi_rate(accounting_date):
            assert accounting_date == date(2026, 6, 1)
            started.set()
            assert resume.wait(20), "a consulta do CDI não foi liberada"
            if not cdi_available:
                raise CdiUnavailable(accounting_date.isoformat())
            return None

        controller.bcb_connector.get_cdi_rate = get_cdi_rate
        return controller.close_day({"accounting_date": "2026-06-01"})
    finally:
        if context.db_session is not None:
            context.db_session.rollback()
            context.db_session.close()
        database.clear_context()


def test_deposit_finishes_while_day_closing_waits_for_cdi_without_holding_connection(monkeypatch):
    DbUtils.rollback()
    import database

    engine = create_engine(DbUtils.database_url())
    monkeypatch.setattr(database, "SessionLocal", sessionmaker(bind=engine, autoflush=False))
    account = ObjectGenerator.create_account()
    started, resume = Event(), Event()
    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            closing = executor.submit(run_waiting_closing, started, resume)
            try:
                assert started.wait(10), "a virada não chegou à consulta do CDI"
                deposit = executor.submit(RequestGenerator.POST_deposit, account["account_key"], PayloadGenerator.deposit(amount=100))
                try:
                    status, body = deposit.result(timeout=3)
                except TimeoutError:
                    raise AssertionError("o depósito ficou esperando a consulta do CDI") from None
                assert status == 201, body
                assert not closing.done()
                assert engine.pool.checkedout() == 0
                status, transaction = RequestGenerator.GET_transaction(account["account_key"], account["account_token"], body["transaction_key"])
                assert status == 200, transaction
                assert transaction["accounting_date"] == "2026-06-01"
            finally:
                resume.set()
            assert closing.result(timeout=10) == {"closed_date": "2026-06-01", "accounting_date": "2026-06-02"}
        status, summary = RequestGenerator.GET_account(account["account_key"], account["account_token"])
        assert status == 200, summary
        assert summary["balance"] == 100
    finally:
        engine.dispose()


@pytest.mark.parametrize("cdi_available", [True, False])
def test_day_closed_during_cdi_query_is_revalidated_even_if_cdi_fails(monkeypatch, cdi_available):
    DbUtils.rollback()
    import database
    from controllers import DayClosingController
    from errors import DayAlreadyClosed, FutureAccountingDate

    engine = create_engine(DbUtils.database_url())
    monkeypatch.setattr(database, "SessionLocal", sessionmaker(bind=engine, autoflush=False))
    started, resume = Event(), Event()
    MockGenerator.set_cdi_rate("2026-06-01")
    try:
        context = database.open_context()
        try:
            controller = DayClosingController()
            controller.bcb_connector.get_cdi_rate = Mock(side_effect=AssertionError("data inválida não deve consultar o CDI"))
            for accounting_date, error_class in [("2026-05-31", DayAlreadyClosed), ("2026-06-02", FutureAccountingDate)]:
                with pytest.raises(error_class):
                    controller.close_day({"accounting_date": accounting_date})
                controller.session.rollback()
            controller.bcb_connector.get_cdi_rate.assert_not_called()
        finally:
            if context.db_session is not None:
                context.db_session.close()
            database.clear_context()

        with ThreadPoolExecutor(max_workers=2) as executor:
            waiting = executor.submit(run_waiting_closing, started, resume, cdi_available)
            try:
                assert started.wait(10), "a primeira virada não chegou à consulta do CDI"
                completing = executor.submit(RequestGenerator.POST_day_closing, PayloadGenerator.day_closing("2026-06-01"))
                try:
                    status, body = completing.result(timeout=3)
                except TimeoutError:
                    raise AssertionError("a segunda virada ficou esperando a consulta do CDI da primeira") from None
                assert status == 200, body
                assert body == {"closed_date": "2026-06-01", "accounting_date": "2026-06-02"}
                assert not waiting.done()
            finally:
                resume.set()
            with pytest.raises(DayAlreadyClosed) as error:
                waiting.result(timeout=10)
            assert error.value.code == "QIT001028"

        account = ObjectGenerator.create_account()
        status, body = RequestGenerator.POST_deposit(account["account_key"], PayloadGenerator.deposit(amount=100))
        assert status == 201, body
        status, transaction = RequestGenerator.GET_transaction(account["account_key"], account["account_token"], body["transaction_key"])
        assert status == 200, transaction
        assert transaction["accounting_date"] == "2026-06-02"
    finally:
        MockGenerator.clear_cdi("2026-06-01")
        engine.dispose()
