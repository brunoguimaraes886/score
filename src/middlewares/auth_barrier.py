from fastapi import FastAPI, Request
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.exc import OperationalError

from constants import AUTH_FAILURE_LIMIT, AUTH_FAILURE_WINDOW_MINUTES, BYPASS_ENDPOINTS
from errors.base_error import DatabaseTimeout, TooManyAuthFailures
from errors.handlers import is_database_timeout, qi_exception_to_response
from middlewares.request_log_writer import get_client_ip
from models import RequestLog
from repositories import RequestLogRepository


# As falhas que esta barreira conta: as dos dois tokens internos, por IP.
INTERNAL_AUTH_FAILURES = [RequestLog.INTERNAL, RequestLog.ADMIN]


def register_auth_barrier_middleware(application: FastAPI) -> None:
    """Barreira contra chute de token (PRD-10).

    AUTH_FAILURE_LIMIT falhas de INTERNAL-TOKEN ou ADMIN-TOKEN do mesmo IP
    nos últimos AUTH_FAILURE_WINDOW_MINUTES minutos: toda requisição desse
    IP responde 429 QIT000429, antes de conferir token nenhum, até as
    falhas antigas saírem da janela. O 429 não conta como falha.

    A contagem mora em request_log, no banco, e não na memória do
    processo (PRD-04): vale para todas as cópias da API. As rotas de
    BYPASS_ENDPOINTS passam direto: o health check não toca no banco
    (PRD-02).
    """

    @application.middleware("http")
    async def check_auth_barrier(request: Request, call_next):
        if request.method == "OPTIONS" or request.url.path in BYPASS_ENDPOINTS:
            return await call_next(request)

        try:
            failures = await run_in_threadpool(
                RequestLogRepository().count_auth_failures,
                get_client_ip(request),
                INTERNAL_AUTH_FAILURES,
                AUTH_FAILURE_WINDOW_MINUTES,
            )
        except OperationalError as error:
            if is_database_timeout(error):
                return qi_exception_to_response(DatabaseTimeout())
            raise

        if failures >= AUTH_FAILURE_LIMIT:
            return qi_exception_to_response(TooManyAuthFailures())

        return await call_next(request)
