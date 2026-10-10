import asyncio
from os import environ
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from starlette.requests import Request

environ.setdefault("DATABASE_URL", "postgresql+psycopg2://bootcamp:bootcamp@localhost:5432/bootcamp")

from middlewares.request_logger import register_request_logger_middleware


def test_request_log_omits_arbitrary_query_and_headers(monkeypatch):
    callbacks = []
    application = SimpleNamespace(middleware=lambda protocol: callbacks.append)
    logger = Mock()
    monkeypatch.setattr("middlewares.request_logger.logger", logger)
    register_request_logger_middleware(application)
    request = Request({"type": "http", "method": "GET", "scheme": "http", "server": ("localhost", 3000),
                       "path": "/customers", "query_string": b"token=PRIVATE_QUERY_MARKER&document=PRIVATE_DOCUMENT",
                       "headers": [(b"internal-token", b"PRIVATE_HEADER")]})
    response = SimpleNamespace(status_code=405)

    async def call_next(request):
        return response

    assert asyncio.run(callbacks[0](request, call_next)) is response
    messages = [entry.args[0] for entry in logger.info.call_args_list]
    assert messages[0] == "ENTROU GET /customers"
    assert messages[1].startswith("SAIU 405 GET /customers - ")
    assert messages[1].endswith(" ms")
    assert "PRIVATE" not in " ".join(messages)


def test_both_uvicorn_launches_disable_access_log():
    root = Path(__file__).resolve().parents[3]
    for filename, prefix in [("Dockerfile", "CMD uvicorn"), ("docker-compose.yml", "command: uvicorn")]:
        lines = (root / filename).read_text(encoding="utf-8").splitlines()
        launches = [line for line in lines if line.strip().startswith(prefix)]
        assert len(launches) == 1
        assert "--no-access-log" in launches[0]
