from fastapi import Request, Response
from fastapi import status as http_status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from constants import ACCOUNT_TOKEN_HEADER
from controllers import CategoryController
from utils.schema_handler import SchemaHandler


# MOV-04: a lista de categorias começa na página 0, com 10 itens, quando a query string não diz.
DEFAULT_LIMIT = 10
DEFAULT_PAGE = 0


class CategoryResource:
    """A porta HTTP das categorias do cofrinho: criar, listar, consultar e excluir.

    Sem regra de negócio, sem SQL e sem nada guardado no self (ARQ-02). O
    token da conta chega no cabeçalho ACCOUNT-TOKEN (API-16); quem o
    confere é o controller.
    """

    @SchemaHandler.validate("post_categories.json")
    def on_post(self, account_key: str, payload: dict, request: Request) -> JSONResponse:
        controller = CategoryController()
        category = controller.create_category(account_key, request.headers.get(ACCOUNT_TOKEN_HEADER), payload)

        return JSONResponse(
            content=jsonable_encoder(category),
            status_code=http_status.HTTP_201_CREATED,
        )

    @SchemaHandler.validate_query_params("get_categories.json")
    def on_get_list(self, account_key: str, request: Request) -> JSONResponse:
        """Uma página das categorias ativas. O schema get_categories.json já garantiu limit e page."""
        controller = CategoryController()

        query_params = request.query_params
        limit = int(query_params.get("limit", DEFAULT_LIMIT))
        page = int(query_params.get("page", DEFAULT_PAGE))
        offset = page * limit

        categories_page = controller.list_categories(account_key, request.headers.get(ACCOUNT_TOKEN_HEADER), limit, offset)

        # O envelope da página fala de limit e page, vocabulário de HTTP: quem o monta é o resource, como no base.
        page_envelope = {
            "data": categories_page["categories_list_dto"],
            "limit": limit,
            "page": page,
            "is_last_page": categories_page["is_last_page"],
        }

        return JSONResponse(
            content=jsonable_encoder(page_envelope),
            status_code=http_status.HTTP_200_OK,
        )

    def on_get_by_key(self, account_key: str, category_key: str, request: Request) -> JSONResponse:
        controller = CategoryController()
        category = controller.get_category(account_key, request.headers.get(ACCOUNT_TOKEN_HEADER), category_key)

        return JSONResponse(
            content=jsonable_encoder(category),
            status_code=http_status.HTTP_200_OK,
        )

    def on_delete_by_key(self, account_key: str, category_key: str, request: Request) -> Response:
        controller = CategoryController()
        controller.delete_category(account_key, request.headers.get(ACCOUNT_TOKEN_HEADER), category_key)

        return Response(status_code=http_status.HTTP_204_NO_CONTENT)
