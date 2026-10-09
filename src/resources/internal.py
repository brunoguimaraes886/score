from fastapi import Response
from fastapi import status as http_status

from controllers import AccountController
from utils.schema_handler import SchemaHandler


class InternalResource:
    """As rotas da operação do banco, sob /internal (API-13)."""

    @SchemaHandler.validate("post_blocks.json")
    def on_post_block(self, account_key: str, payload: dict) -> Response:
        controller = AccountController()
        controller.block_account(account_key, payload["reason"])
        return Response(status_code=http_status.HTTP_204_NO_CONTENT)

    def on_post_unblock(self, account_key: str) -> Response:
        controller = AccountController()
        controller.unblock_account(account_key)
        return Response(status_code=http_status.HTTP_204_NO_CONTENT)
