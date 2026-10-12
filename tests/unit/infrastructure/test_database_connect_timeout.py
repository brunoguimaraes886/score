import os
from pathlib import Path
import socket
import subprocess
import sys
from threading import Event, Thread


PROBE = """
from sqlalchemy.exc import OperationalError

from database import engine
from errors.handlers import is_database_unavailable

try:
    with engine.connect():
        raise AssertionError("a conexão não deveria ser estabelecida")
except OperationalError as error:
    assert is_database_unavailable(error)
    assert "timeout" in str(error.orig).lower()
    print("database unavailable")
finally:
    engine.dispose()
"""


def test_database_connection_timeout_when_server_accepts_tcp_but_does_not_respond():
    finished = Event()
    accepted = Event()
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        listener.settimeout(10)
        port = listener.getsockname()[1]

        def stalled_server():
            connection, _ = listener.accept()
            with connection:
                accepted.set()
                finished.wait(12)

        worker = Thread(target=stalled_server, daemon=True)
        worker.start()
        environment = os.environ.copy()
        environment["DATABASE_URL"] = f"postgresql+psycopg2://probe:probe@127.0.0.1:{port}/probe"
        environment["DB_CONNECT_TIMEOUT_SECONDS"] = "2"
        environment["PYTHONPATH"] = str(Path(__file__).resolve().parents[3] / "src")
        environment["PYTHONUTF8"] = "1"
        try:
            try:
                result = subprocess.run(
                    [sys.executable, "-c", PROBE], env=environment,
                    capture_output=True, text=True, timeout=8,
                )
            except subprocess.TimeoutExpired:
                raise AssertionError("a conexão não respeitou o timeout configurado") from None
            assert accepted.is_set()
            assert result.returncode == 0, result.stderr
            assert result.stdout.strip() == "database unavailable"
        finally:
            finished.set()
            worker.join(timeout=2)
