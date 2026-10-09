from pathlib import Path
from os import path, environ

import pytest

root = Path(__file__).resolve().parents[1]

if not environ.get("APP_ENV") or environ.get("APP_ENV") == "local":
    from dotenv import load_dotenv

    load_dotenv(path.join(str(root), ".env"))

    if environ.get("SERVER_LOCALHOST") is None:
        environ["SERVER_LOCALHOST"] = "127.0.0.1"


@pytest.fixture(autouse=True)
def no_server_errors():
    """R3, TST-08: reprova o teste que recebeu da API um 5xx fora dos 503 de dependência.

    Antes de cada teste, esvazia a lista de respostas do ClientRequisition;
    depois dele, confere a lista. Os únicos 5xx aceitos são o 503 QIT000503
    (o banco passou do timeout, PRD-08), o 503 QIT000504 (banco indisponível)
    e o 503 QIT001031 (o Banco Central
    não respondeu, COF-20). Qualquer outro 5xx vira erro na desmontagem do
    teste, com as respostas na mensagem.

    O import fica aqui dentro, e não no topo: o tests.utils lê o
    INTERNAL_TOKEN do ambiente quando é importado, e o .env tem de ser lido
    antes disso.
    """
    from tests.utils.requisition import ClientRequisition

    ClientRequisition.start_test()

    yield

    server_errors = ClientRequisition.server_errors()
    assert server_errors == [], f"Resposta 5xx da API neste teste (R3): {server_errors}"
