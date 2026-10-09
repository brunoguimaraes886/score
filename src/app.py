from fastapi import FastAPI

from constants import check_variables
from errors import register_error_handlers
from errors.base_error import error_verification
from middlewares import (
    register_admin_token_middleware,
    register_internal_token_middleware,
    register_request_context_middleware,
    register_request_log_writer_middleware,
    register_request_logger_middleware,
    register_session_manager_middleware,
)
from resources import HealthCheckResource
from utils.logger import setup_logging


def create_app() -> FastAPI:
    """Monta a aplicação: os middlewares, as rotas e os error handlers."""
    # Os três None desligam a documentação automática (ARQ-09).
    application = FastAPI(
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )

    # ────────────────────────────────────────────────────────────────
    # Os middlewares. O ÚLTIMO registrado é o PRIMEIRO a rodar: leia as
    # linhas de baixo para cima e a requisição atravessa assim, de fora
    # para dentro:
    #
    #     request_context      nome da requisição e RequestState
    #     request_logger       ENTROU / SAIU na saída padrão
    #     request_log_writer   uma linha em request_log (PRD-06)
    #     internal_token       403 sem o INTERNAL-TOKEN certo (API-04)
    #     admin_token          403 em /internal sem o ADMIN-TOKEN (PRD-13)
    #     session_manager      sessão de banco; o mais interno de todos
    #
    # A ordem inteira, com os porquês: docs/plano/PLANO-00-indice.md,
    # seção "Middlewares".
    # ────────────────────────────────────────────────────────────────
    register_session_manager_middleware(application)
    register_admin_token_middleware(application)
    register_internal_token_middleware(application)
    register_request_log_writer_middleware(application)
    register_request_logger_middleware(application)
    register_request_context_middleware(application)

    # ────────────────────────────────────────────────────────────────
    # As rotas: uma linha por endereço e verbo. O status de sucesso sai
    # de dentro do resource (API-02).
    # ────────────────────────────────────────────────────────────────
    health_check_resource = HealthCheckResource()

    application.add_api_route("/", health_check_resource.on_get_home, methods=["GET"])
    application.add_api_route(
        "/health_check",
        health_check_resource.on_get_health_check,
        methods=["GET"]
    )

    register_error_handlers(application)

    return application


def main() -> FastAPI:
    # Não deixa a API subir com configuração faltando: é melhor falhar
    # agora, na hora de ligar, do que na cara do cliente mais tarde.
    check_variables()
    error_verification()
    setup_logging()

    return create_app()


app = main()
