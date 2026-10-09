from fastapi import Request
from fastapi import status as http_status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from constants import ACCOUNT_TOKEN_HEADER
from controllers import TransactionController
from utils.schema_handler import SchemaHandler


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
