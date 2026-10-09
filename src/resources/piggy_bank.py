from fastapi import Request
from fastapi import status as http_status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from constants import ACCOUNT_TOKEN_HEADER
from controllers import PiggyBankController
from utils.schema_handler import SchemaHandler


class PiggyBankResource:
    """A porta HTTP do cofrinho: guardar, resgatar e o extrato do cofrinho.

    Sem regra de negócio, sem SQL e sem nada guardado no self (ARQ-02). O
    token da conta chega no cabeçalho ACCOUNT-TOKEN (API-16); quem o
    confere é o controller.
    """

    @SchemaHandler.validate("post_savings.json")
    def on_post_saving(self, account_key: str, payload: dict, request: Request) -> JSONResponse:
        controller = PiggyBankController()
        transaction = controller.save(account_key, request.headers.get(ACCOUNT_TOKEN_HEADER), payload)

        return JSONResponse(
            content=jsonable_encoder(transaction),
            status_code=http_status.HTTP_201_CREATED,
        )
