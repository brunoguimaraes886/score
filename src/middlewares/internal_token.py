from fastapi import FastAPI, Request

from constants import BYPASS_ENDPOINTS, INTERNAL_TOKEN
from errors.base_error import ForbiddenNotInternal
from errors.handlers import qi_exception_to_response
from models import RequestLog
from utils.request_context import get_request_state


def register_internal_token_middleware(application: FastAPI) -> None:
    """Deixa passar só quem manda o header INTERNAL-TOKEN com o valor certo (API-04).

    O valor certo vem da variável de ambiente INTERNAL_TOKEN, nunca do
    código. As rotas de BYPASS_ENDPOINTS (raiz e health check) são públicas.

    Errou o token: anota `auth_failure = INTERNAL` no estado da requisição
    (vai para request_log e alimenta a barreira da PRD-10) e responde 403
    QIT000002.

    Dentro de middleware, a resposta de erro é DEVOLVIDA, não levantada:
    quem traduz exceção são os exception handlers, que rodam mais para
    dentro. Levantar aqui viraria um 500.
    """

    @application.middleware("http")
    async def check_internal_token(request: Request, call_next):
        is_public = request.url.path in BYPASS_ENDPOINTS

        if request.method == "OPTIONS" or is_public:
            return await call_next(request)

        if request.headers.get("INTERNAL-TOKEN") != INTERNAL_TOKEN:
            request_state = get_request_state()
            if request_state is not None:
                request_state.auth_failure = RequestLog.INTERNAL
            return qi_exception_to_response(ForbiddenNotInternal())

        return await call_next(request)
