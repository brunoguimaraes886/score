import re
import uuid
from contextvars import ContextVar
from typing import Optional


# O nome do cabeçalho que carrega o identificador da requisição.
#
# "X-Request-ID" não é invenção deste projeto: é a convenção que
# balanceadores de carga, proxies e ferramentas de log já sabem ler.
REQUEST_ID_HEADER = "X-Request-ID"

# O que aceitamos quando quem chama manda o identificador dele: letras,
# números, hífen e sublinhado, no máximo 64 caracteres. O porquê dessa
# desconfiança está em build_request_id, logo abaixo.
SAFE_REQUEST_ID = re.compile(r"[A-Za-z0-9_-]{1,64}")

# Fora de uma requisição (a API subindo), o log escreve isto no lugar do
# identificador.
NO_REQUEST_ID = "-"


# Este arquivo mora em utils/, e não em middlewares/, porque quem mais
# precisa dele é o logger: middlewares/ importa errors/, errors/ importa
# utils/logger.py, e o logger fecharia o ciclo.
#
# ContextVar, e não variável comum: ele guarda um valor separado por
# requisição em andamento. Com uma variável comum, duas requisições ao
# mesmo tempo sobrescreveriam o valor uma da outra.
_request_id: ContextVar[str] = ContextVar("request_id", default=NO_REQUEST_ID)


def get_request_id() -> str:
    """Devolve o identificador da requisição que está sendo atendida agora."""
    return _request_id.get()


def set_request_id(request_id: str) -> None:
    """Guarda o identificador desta requisição. Quem chama é o middleware."""
    _request_id.set(request_id)


def build_request_id(received_request_id: str = None) -> str:
    """Aproveita o identificador que veio de fora, ou inventa um novo.

    O valor veio de FORA e vai parar no log: quem mandasse uma quebra de
    linha escreveria uma linha de log inventada (log injection). Quem
    manda algo fora do formato ganha um identificador novo.

    `fullmatch`, e não `match`: o `match` se contenta com um começo certo
    e deixa passar o lixo que vier depois.
    """
    if received_request_id is not None and SAFE_REQUEST_ID.fullmatch(received_request_id):
        return received_request_id

    return str(uuid.uuid4())


class RequestState:
    """O que a requisição deixa para a linha de request_log (PRD-06, PRD-14).

    - `request_id`: o mesmo identificador do log da saída padrão.
    - `error_code`: o código do erro respondido; quem grava é o
      qi_exception_to_response (src/errors/handlers.py).
    - `auth_failure`: qual token falhou (INTERNAL, ADMIN ou ACCOUNT); quem
      grava são os middlewares de token e, na fase 5, a checagem de dono.
    - `account_key`: a key da conta que está no caminho; quem grava é o
      middleware request_log_writer.

    É um objeto MUTÁVEL guardado num ContextVar, pelo mesmo motivo do
    Context de src/database.py: quem roda mais para dentro muda um
    atributo, e o middleware de fora lê o mesmo objeto. Um `.set()` feito
    lá dentro seria invisível aqui fora.
    """

    def __init__(self, request_id: str) -> None:
        self.request_id = request_id
        self.error_code = None
        self.auth_failure = None
        self.account_key = None


_request_state: ContextVar[Optional[RequestState]] = ContextVar("request_state", default=None)


def start_request_state(request_id: str) -> RequestState:
    """Cria o estado desta requisição e o deixa no contexto. Quem chama é o middleware request_context."""
    request_state = RequestState(request_id)
    _request_state.set(request_state)

    return request_state


def get_request_state() -> Optional[RequestState]:
    """Devolve o estado da requisição em andamento; None fora de uma requisição."""
    return _request_state.get()
