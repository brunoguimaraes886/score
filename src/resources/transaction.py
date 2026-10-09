from fastapi import Request
from fastapi import status as http_status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from constants import ACCOUNT_TOKEN_HEADER
from controllers import TransactionController
from utils.schema_handler import SchemaHandler


# MOV-04: o extrato começa na página 0, com 10 itens, quando a query string não diz.
DEFAULT_LIMIT = 10
DEFAULT_PAGE = 0


class TransactionResource:
    """A porta HTTP do dinheiro: depósito, saque, transferência, consulta e extrato.

    Sem regra de negócio, sem SQL e sem nada guardado no self (ARQ-02). O
    token da conta chega no cabeçalho ACCOUNT-TOKEN (API-16); quem o
    confere é o controller.
    """

    @SchemaHandler.validate("post_deposits.json")
    def on_post_deposit(self, account_key: str, payload: dict) -> JSONResponse:
        controller = TransactionController()
        transaction = controller.deposit(account_key, payload)

        return JSONResponse(
            content=jsonable_encoder(transaction),
            status_code=http_status.HTTP_201_CREATED,
        )

    @SchemaHandler.validate("post_withdrawals.json")
    def on_post_withdrawal(self, account_key: str, payload: dict, request: Request) -> JSONResponse:
        controller = TransactionController()
        transaction = controller.withdraw(account_key, request.headers.get(ACCOUNT_TOKEN_HEADER), payload)

        return JSONResponse(
            content=jsonable_encoder(transaction),
            status_code=http_status.HTTP_201_CREATED,
        )

    @SchemaHandler.validate("post_transfers.json")
    def on_post_transfer(self, account_key: str, payload: dict, request: Request) -> JSONResponse:
        controller = TransactionController()
        transaction = controller.transfer(account_key, request.headers.get(ACCOUNT_TOKEN_HEADER), payload)

        return JSONResponse(
            content=jsonable_encoder(transaction),
            status_code=http_status.HTTP_201_CREATED,
        )

    def on_get_transaction(self, account_key: str, transaction_key: str, request: Request) -> JSONResponse:
        controller = TransactionController()
        transaction = controller.get_transaction(account_key, request.headers.get(ACCOUNT_TOKEN_HEADER), transaction_key)

        return JSONResponse(
            content=jsonable_encoder(transaction),
            status_code=http_status.HTTP_200_OK,
        )

    @SchemaHandler.validate_query_params("get_entries.json")
    def on_get_entries(self, account_key: str, request: Request) -> JSONResponse:
        """Uma página do extrato. O schema get_entries.json já garantiu que limit e page são dígitos."""
        controller = TransactionController()

        query_params = request.query_params
        limit = int(query_params.get("limit", DEFAULT_LIMIT))
        page = int(query_params.get("page", DEFAULT_PAGE))
        offset = page * limit

        entries_page = controller.list_entries(account_key, request.headers.get(ACCOUNT_TOKEN_HEADER), limit, offset)

        # O envelope da página fala de limit e page, vocabulário de HTTP: quem o monta é o resource, como no base.
        page_envelope = {
            "data": entries_page["entries_list_dto"],
            "limit": limit,
            "page": page,
            "is_last_page": entries_page["is_last_page"],
        }

        return JSONResponse(
            content=jsonable_encoder(page_envelope),
            status_code=http_status.HTTP_200_OK,
        )
