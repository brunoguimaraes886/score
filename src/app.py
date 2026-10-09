from fastapi import FastAPI

from constants import check_variables
from errors import register_error_handlers
from errors.base_error import error_verification
from middlewares import (
    register_admin_token_middleware,
    register_auth_barrier_middleware,
    register_internal_token_middleware,
    register_request_context_middleware,
    register_request_log_writer_middleware,
    register_request_logger_middleware,
    register_session_manager_middleware,
)
from resources import AccountResource, CustomerResource, HealthCheckResource, InternalResource, TransactionResource
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
    #     auth_barrier         429 para o IP que errou token demais (PRD-10)
    #     internal_token       403 sem o INTERNAL-TOKEN certo (API-04)
    #     admin_token          403 em /internal sem o ADMIN-TOKEN (PRD-13)
    #     session_manager      sessão de banco; o mais interno de todos
    #
    # O log vem antes da barreira e dos tokens para gravar também o 403 e
    # o 429; a barreira vem antes dos tokens para responder sem conferir
    # token nenhum. A ordem inteira, com os porquês:
    # docs/plano/PLANO-00-indice.md, seção "Middlewares".
    # ────────────────────────────────────────────────────────────────
    register_session_manager_middleware(application)
    register_admin_token_middleware(application)
    register_internal_token_middleware(application)
    register_auth_barrier_middleware(application)
    register_request_log_writer_middleware(application)
    register_request_logger_middleware(application)
    register_request_context_middleware(application)

    # ────────────────────────────────────────────────────────────────
    # As rotas: uma linha por endereço e verbo. O status de sucesso sai
    # de dentro do resource (API-02).
    # ────────────────────────────────────────────────────────────────
    health_check_resource = HealthCheckResource()
    customer_resource = CustomerResource()
    account_resource = AccountResource()
    internal_resource = InternalResource()
    transaction_resource = TransactionResource()

    application.add_api_route("/", health_check_resource.on_get_home, methods=["GET"])
    application.add_api_route(
        "/health_check",
        health_check_resource.on_get_health_check,
        methods=["GET"]
    )

    # Cliente
    application.add_api_route("/customers", customer_resource.on_post, methods=["POST"])
    application.add_api_route("/customers/{customer_key}", customer_resource.on_get_by_key, methods=["GET"])

    # Conta
    application.add_api_route("/customers/{customer_key}/accounts", account_resource.on_post_account, methods=["POST"])
    application.add_api_route("/accounts/{account_key}", account_resource.on_get_by_key, methods=["GET"])
    application.add_api_route("/accounts/{account_key}", account_resource.on_delete_by_key, methods=["DELETE"])

    # Dinheiro
    application.add_api_route("/accounts/{account_key}/deposits", transaction_resource.on_post_deposit, methods=["POST"])
    application.add_api_route("/accounts/{account_key}/withdrawals", transaction_resource.on_post_withdrawal, methods=["POST"])
    application.add_api_route("/accounts/{account_key}/transfers", transaction_resource.on_post_transfer, methods=["POST"])

    # Rotas internas (API-13): INTERNAL-TOKEN e ADMIN-TOKEN
    application.add_api_route("/internal/accounts/{account_key}/blocks", internal_resource.on_post_block, methods=["POST"])
    application.add_api_route("/internal/accounts/{account_key}/unblocks", internal_resource.on_post_unblock, methods=["POST"])

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
