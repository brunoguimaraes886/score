from fastapi import FastAPI, Request

from constants import ADMIN_TOKEN, ADMIN_TOKEN_HEADER, INTERNAL_PREFIX
from errors.base_error import ForbiddenNotAdmin
from errors.handlers import qi_exception_to_response
from models import RequestLog
from utils.request_context import get_request_state


def is_internal_path(path: str) -> bool:
    """True para /internal e para tudo abaixo de /internal/; /internalx não conta."""
    return path == INTERNAL_PREFIX or path.startswith(INTERNAL_PREFIX + "/")


def register_admin_token_middleware(application: FastAPI) -> None:
    """O segundo cadeado das rotas /internal (PRD-07, PRD-13, API-13).

    Roda por dentro do internal_token: quem chega aqui já mandou o
    INTERNAL-TOKEN certo. Nos caminhos /internal, falta ou erro do
    ADMIN-TOKEN anota `auth_failure = ADMIN` no estado da requisição (vai
    para request_log e alimenta a barreira da PRD-10) e responde 403
    QIT000003. Os outros caminhos passam direto.
    """

    @application.middleware("http")
    async def check_admin_token(request: Request, call_next):
        if request.method == "OPTIONS" or not is_internal_path(request.url.path):
            return await call_next(request)

        if request.headers.get(ADMIN_TOKEN_HEADER) != ADMIN_TOKEN:
            request_state = get_request_state()
            if request_state is not None:
                request_state.auth_failure = RequestLog.ADMIN
            return qi_exception_to_response(ForbiddenNotAdmin())

        return await call_next(request)
