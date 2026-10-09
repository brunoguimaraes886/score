from fastapi import status as http_status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from controllers import AccountController


class AccountResource:
    """A porta HTTP da conta. Sem regra de negócio, sem SQL e sem nada guardado no self (ARQ-02)."""

    def on_post_account(self, customer_key: str) -> JSONResponse:
        controller = AccountController()
        account = controller.open_account(customer_key)
        return JSONResponse(content=jsonable_encoder(account), status_code=http_status.HTTP_201_CREATED)
