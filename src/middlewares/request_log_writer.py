import re

from fastapi import FastAPI, Request
from fastapi.concurrency import run_in_threadpool

from constants import BYPASS_ENDPOINTS
from errors.base_error import InternalError
from repositories import RequestLogRepository
from utils.logger import get_logger
from utils.request_context import RequestState, get_request_state


logger = get_logger(__name__)

# /accounts/{account_key}... e /internal/accounts/{account_key}...: a key é
# o segmento logo depois de "accounts/", com os 36 caracteres de um UUID.
ACCOUNT_KEY_IN_PATH = re.compile(r"^/(?:internal/)?accounts/([0-9a-f-]{36})(?:/|$)")


def get_client_ip(request: Request):
    """O IP de quem chamou, como o servidor o vê; None quando o servidor não sabe."""
    if request.client is None:
        return None

    return request.client.host


def account_key_from_path(path: str):
    """A key da conta que está no caminho; None quando o caminho não é de uma conta."""
    match = ACCOUNT_KEY_IN_PATH.match(path)
    if match is None:
        return None

    return match.group(1)


async def save_request_log(request: Request, request_state: RequestState, status: int, error_code) -> None:
    """Grava a linha de request_log desta requisição.

    Grava só as colunas da PRD-14. Nunca cabeçalho, corpo nem parâmetros
    do endereço: é por lá que viajam token, CPF e CNPJ (PRD-12). A
    gravação roda fora do laço de eventos (run_in_threadpool), para não
    parar as outras requisições. Se ela falhar, a resposta segue para o
    cliente e a falha vai para o log da saída padrão.
    """
    try:
        await run_in_threadpool(
            RequestLogRepository().create,
            request_state.request_id,
            request.method,
            request.url.path,
            status,
            error_code,
            get_client_ip(request),
            request_state.account_key,
            request_state.auth_failure,
        )
    except Exception:
        logger.exception("Não consegui gravar a linha de request_log")


def register_request_log_writer_middleware(application: FastAPI) -> None:
    """Uma linha em request_log por requisição, deu certo ou não (PRD-06).

    Fica por fora da barreira e dos tokens: o 403 e o 429 também são
    gravados, e são as falhas de token gravadas aqui que a barreira conta
    (PRD-10). As rotas de BYPASS_ENDPOINTS não são gravadas: o health
    check não toca no banco (PRD-02).

    Antes de seguir, anota no estado da requisição a key da conta que
    está no caminho, para as camadas de dentro e para a linha do log.
    """

    @application.middleware("http")
    async def write_request_log(request: Request, call_next):
        if request.url.path in BYPASS_ENDPOINTS:
            return await call_next(request)

        request_state = get_request_state()
        request_state.account_key = account_key_from_path(request.url.path)

        try:
            response = await call_next(request)
        except Exception:
            # Erro inesperado: quem responde o 500 é o handler mais de
            # fora, depois daqui. A linha sai com o status e o código dele.
            await save_request_log(request, request_state, 500, InternalError.code)
            raise

        await save_request_log(request, request_state, response.status_code, request_state.error_code)

        return response
