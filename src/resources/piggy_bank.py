from fastapi import Request
from fastapi import status as http_status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from constants import ACCOUNT_TOKEN_HEADER
from controllers import PiggyBankController
from utils.schema_handler import SchemaHandler


# MOV-04: o extrato do cofrinho começa na página 0, com 10 itens, quando a query string não diz.
DEFAULT_LIMIT = 10
DEFAULT_PAGE = 0


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

    @SchemaHandler.validate("post_redemptions.json")
    def on_post_redemption(self, account_key: str, payload: dict, request: Request) -> JSONResponse:
        controller = PiggyBankController()
        transaction = controller.redeem(account_key, request.headers.get(ACCOUNT_TOKEN_HEADER), payload)

        return JSONResponse(
            content=jsonable_encoder(transaction),
            status_code=http_status.HTTP_201_CREATED,
        )

    @SchemaHandler.validate_query_params("get_piggy_bank_entries.json")
    def on_get_piggy_bank_entries(self, account_key: str, request: Request) -> JSONResponse:
        """Uma página do extrato do cofrinho. O schema get_piggy_bank_entries.json já garantiu limit, page e category_key."""
        controller = PiggyBankController()

        query_params = request.query_params
        limit = int(query_params.get("limit", DEFAULT_LIMIT))
        page = int(query_params.get("page", DEFAULT_PAGE))
        offset = page * limit

        entries_page = controller.list_piggy_bank_entries(
            account_key,
            request.headers.get(ACCOUNT_TOKEN_HEADER),
            limit,
            offset,
            query_params.get("category_key"),
        )

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
