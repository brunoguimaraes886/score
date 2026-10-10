import asyncio
import json
from os import environ
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from psycopg2 import InterfaceError as PgInterfaceError, OperationalError as PgOperationalError
from psycopg2.errors import LockNotAvailable, QueryCanceled
from sqlalchemy.exc import DBAPIError, InterfaceError, OperationalError

environ.setdefault("DATABASE_URL", "postgresql+psycopg2://bootcamp:bootcamp@localhost:5432/bootcamp")

from errors.handlers import register_error_handlers
from middlewares.auth_barrier import register_auth_barrier_middleware
from middlewares.session_manager import register_session_manager_middleware
from tests.utils.requisition import ClientRequisition


class Application:
    def __init__(self):
        self.handlers = {}
        self.callback = None

    def exception_handler(self, error_class):
        def save(handler):
            self.handlers[error_class] = handler
            return handler
        return save

    def middleware(self, protocol):
        def save(handler):
            self.callback = handler
            return handler
        return save


def database_error(sqlstate=None):
    class Original(PgOperationalError):
        @property
        def pgcode(self):
            return sqlstate
    return OperationalError("probe", {}, Original("connection unavailable"))


def request_for(path="/accounts/probe"):
    return SimpleNamespace(method="GET", url=SimpleNamespace(path=path), client=SimpleNamespace(host="127.0.0.1"),
                           state=SimpleNamespace(request_id="database-outage"))


def assert_unavailable(response):
    assert response.status_code == 503
    assert json.loads(response.body) == {
        "title": "Service Unavailable", "description": "The database is unavailable.",
        "translation": "O banco de dados está indisponível.", "code": "QIT000504",
    }
    assert response.headers["X-Request-ID"] == "database-outage"


@pytest.mark.parametrize("sqlstate", [None, "08001", "08006", "57P01", "57P02", "57P03"])
def test_handler_translates_connection_failures_to_the_authorized_503(sqlstate):
    application = Application()
    register_error_handlers(application)
    assert_unavailable(application.handlers[OperationalError](request_for(), database_error(sqlstate)))


def test_handler_translates_invalidated_connections_without_hiding_other_errors():
    application = Application()
    register_error_handlers(application)
    error = InterfaceError("probe", {}, PgInterfaceError("closed connection"), connection_invalidated=True)
    assert_unavailable(application.handlers[DBAPIError](request_for(), error))
    response = application.handlers[OperationalError](request_for(), database_error("53100"))
    assert response.status_code == 500
    assert json.loads(response.body)["code"] == "QIT000500"
    for original in [LockNotAvailable(), QueryCanceled()]:
        response = application.handlers[OperationalError](request_for(), OperationalError("probe", {}, original))
        assert response.status_code == 503
        assert json.loads(response.body)["code"] == "QIT000503"


@pytest.mark.parametrize("path", ["/accounts/probe", "/customers/probe"])
def test_auth_barrier_translates_outage_before_route_execution(monkeypatch, path):
    application = Application()
    register_auth_barrier_middleware(application)
    monkeypatch.setattr("middlewares.auth_barrier.get_request_state", lambda: SimpleNamespace(account_key=None))
    monkeypatch.setattr("middlewares.auth_barrier.count_failures", Mock(side_effect=database_error()))
    monkeypatch.setattr("middlewares.auth_barrier.RequestLogRepository", lambda: SimpleNamespace(
        resolve_customer_auth_key=Mock(side_effect=database_error())))
    route = Mock()
    assert_unavailable(asyncio.run(application.callback(request_for(path), route)))
    route.assert_not_called()


def test_session_is_rolled_back_and_closed_when_connection_fails(monkeypatch):
    application = Application()
    register_session_manager_middleware(application)
    session = Mock()
    clear = Mock()
    monkeypatch.setattr("middlewares.session_manager.open_context", lambda: SimpleNamespace(db_session=session))
    monkeypatch.setattr("middlewares.session_manager.clear_context", clear)

    async def route(request):
        raise database_error()

    with pytest.raises(OperationalError):
        asyncio.run(application.callback(request_for(), route))
    session.rollback.assert_called_once_with()
    session.close.assert_called_once_with()
    clear.assert_called_once_with()


def test_auth_barrier_preserves_timeout_and_propagates_unexpected_database_errors(monkeypatch):
    application = Application()
    register_auth_barrier_middleware(application)
    monkeypatch.setattr("middlewares.auth_barrier.get_request_state", lambda: SimpleNamespace(account_key=None))
    route = Mock()
    for original in [LockNotAvailable(), QueryCanceled()]:
        error = OperationalError("probe", {}, original)
        monkeypatch.setattr("middlewares.auth_barrier.count_failures", Mock(side_effect=error))
        response = asyncio.run(application.callback(request_for(), route))
        assert response.status_code == 503
        assert json.loads(response.body)["code"] == "QIT000503"
        assert response.headers["X-Request-ID"] == "database-outage"
    error = InterfaceError("probe", {}, PgInterfaceError("closed connection"), connection_invalidated=True)
    monkeypatch.setattr("middlewares.auth_barrier.count_failures", Mock(side_effect=error))
    assert_unavailable(asyncio.run(application.callback(request_for(), route)))
    monkeypatch.setattr("middlewares.auth_barrier.count_failures", Mock(side_effect=database_error("53100")))
    with pytest.raises(OperationalError):
        asyncio.run(application.callback(request_for(), route))
    route.assert_not_called()


def test_server_error_guard_accepts_only_the_authorized_unavailability_status():
    for status in [503, 500]:
        ClientRequisition.start_test()
        ClientRequisition.record("GET", "/probe", status, {"code": "QIT000504"})
        assert bool(ClientRequisition.server_errors()) == (status != 503)
    ClientRequisition.start_test()
