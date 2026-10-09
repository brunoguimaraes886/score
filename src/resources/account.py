from fastapi import Request
from fastapi import status as http_status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from constants import ACCOUNT_TOKEN_HEADER
from controllers import AccountController


class AccountResource:
    """A porta HTTP da conta. Sem regra de negócio, sem SQL e sem nada guardado no self (ARQ-02)."""

    def on_post_account(self, customer_key: str) -> JSONResponse:
        controller = AccountController()
        account = controller.open_account(customer_key)
        return JSONResponse(content=jsonable_encoder(account), status_code=http_status.HTTP_201_CREATED)

    def on_get_by_key(self, account_key: str, request: Request) -> JSONResponse:
        controller = AccountController()
        account = controller.get_account(account_key, request.headers.get(ACCOUNT_TOKEN_HEADER))
        return JSONResponse(content=jsonable_encoder(account), status_code=http_status.HTTP_200_OK)
