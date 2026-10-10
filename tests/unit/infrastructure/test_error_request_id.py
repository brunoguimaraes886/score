import asyncio
from os import environ
from types import SimpleNamespace

from starlette.exceptions import HTTPException

environ.setdefault("DATABASE_URL", "postgresql+psycopg2://bootcamp:bootcamp@localhost:5432/bootcamp")

from errors.base_error import InvalidSchema
from errors.handlers import qi_exception_to_response, register_error_handlers
from middlewares.request_context import register_request_context_middleware


class Application:
    def __init__(self):
        self.handlers = {}
        self.middleware_callback = None

    def exception_handler(self, error_class):
        def save(handler):
            self.handlers[error_class] = handler
            return handler
        return save

    def middleware(self, protocol):
        def save(handler):
            self.middleware_callback = handler
            return handler
        return save


def test_outer_error_handler_reuses_request_id_after_context_is_lost(monkeypatch):
    monkeypatch.setattr("errors.handlers.get_request_state", lambda: None)
    application = Application()
    register_error_handlers(application)
    request = SimpleNamespace(method="GET", url=SimpleNamespace(path="/probe"),
                              state=SimpleNamespace(request_id="existing-id"))
    response = application.handlers[Exception](request, RuntimeError("probe"))
    assert response.status_code == 500
    assert response.headers["X-Request-ID"] == "existing-id"
    response = application.handlers[HTTPException](request, HTTPException(404))
    assert response.status_code == 404
    assert response.headers["X-Request-ID"] == "existing-id"


def test_converter_preserves_the_id_of_the_current_request(monkeypatch):
    state = SimpleNamespace(request_id="current-id", error_code=None)
    monkeypatch.setattr("errors.handlers.get_request_state", lambda: state)
    response = qi_exception_to_response(InvalidSchema("Invalid input."))
    assert response.headers["X-Request-ID"] == "current-id"
    assert state.error_code == "QIT000001"


def test_request_context_keeps_id_on_request_even_if_inner_layer_fails():
    application = Application()
    register_request_context_middleware(application)
    request = SimpleNamespace(headers={"X-Request-ID": "existing-id"}, state=SimpleNamespace())

    async def call_next(request):
        raise RuntimeError("probe")

    try:
        asyncio.run(application.middleware_callback(request, call_next))
    except RuntimeError:
        pass
    else:
        raise AssertionError("A falha deve continuar até o handler de erros.")
    assert request.state.request_id == "existing-id"
