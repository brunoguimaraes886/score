from os import environ

from tests.utils.requisition import ClientRequisition


INTERNAL_TOKEN = environ.get("INTERNAL_TOKEN", "default_token")
ADMIN_TOKEN = environ.get("ADMIN_TOKEN", "default_admin_token")


def _headers(internal_token: str = None, account_token: str = None, admin_token: str = None) -> dict:
    """Os cabeçalhos de token da requisição. Valor None deixa o cabeçalho de fora."""
    headers = {}

    if internal_token is not None:
        headers["INTERNAL-TOKEN"] = internal_token

    if account_token is not None:
        headers["ACCOUNT-TOKEN"] = account_token

    if admin_token is not None:
        headers["ADMIN-TOKEN"] = admin_token

    return headers


def _send(method: str, endpoint: str, headers: dict, payload: dict = None, query_params: dict = None) -> tuple:
    """Manda a requisição e devolve (status, corpo JSON ou None)."""
    response = ClientRequisition.send(method, endpoint, payload=payload, headers=headers, query_params=query_params)

    return response.response_status, response.response_json


class RequestGenerator:
    """Um método por rota de docs/rotas.md; cada um devolve (status, corpo).

    Os tokens têm padrão: o INTERNAL_TOKEN e o ADMIN_TOKEN certos. O
    `account_token` é sempre pedido, porque cada conta tem o seu. Para
    testar token errado, passe outro valor; para testar token faltando,
    passe None.
    """

    @staticmethod
    def POST_customer(payload: dict, internal_token: str = INTERNAL_TOKEN) -> tuple:
        return _send("POST", "/customers", _headers(internal_token), payload=payload)

    @staticmethod
    def GET_customer(customer_key: str, account_token: str, internal_token: str = INTERNAL_TOKEN) -> tuple:
        return _send("GET", f"/customers/{customer_key}", _headers(internal_token, account_token))

    @staticmethod
    def POST_account(customer_key: str, internal_token: str = INTERNAL_TOKEN) -> tuple:
        return _send("POST", f"/customers/{customer_key}/accounts", _headers(internal_token))

    @staticmethod
    def GET_account(account_key: str, account_token: str, internal_token: str = INTERNAL_TOKEN) -> tuple:
        return _send("GET", f"/accounts/{account_key}", _headers(internal_token, account_token))

    @staticmethod
    def DELETE_account(account_key: str, account_token: str, internal_token: str = INTERNAL_TOKEN) -> tuple:
        return _send("DELETE", f"/accounts/{account_key}", _headers(internal_token, account_token))

    @staticmethod
    def POST_deposit(account_key: str, payload: dict, internal_token: str = INTERNAL_TOKEN) -> tuple:
        return _send("POST", f"/accounts/{account_key}/deposits", _headers(internal_token), payload=payload)

    @staticmethod
    def POST_withdrawal(account_key: str, account_token: str, payload: dict, internal_token: str = INTERNAL_TOKEN) -> tuple:
        return _send("POST", f"/accounts/{account_key}/withdrawals", _headers(internal_token, account_token), payload=payload)

    @staticmethod
    def POST_transfer(account_key: str, account_token: str, payload: dict, internal_token: str = INTERNAL_TOKEN) -> tuple:
        return _send("POST", f"/accounts/{account_key}/transfers", _headers(internal_token, account_token), payload=payload)

    @staticmethod
    def GET_transaction(account_key: str, account_token: str, transaction_key: str, internal_token: str = INTERNAL_TOKEN) -> tuple:
        return _send("GET", f"/accounts/{account_key}/transactions/{transaction_key}", _headers(internal_token, account_token))

    @staticmethod
    def GET_entries(account_key: str, account_token: str, params: dict = None, internal_token: str = INTERNAL_TOKEN) -> tuple:
        return _send("GET", f"/accounts/{account_key}/entries", _headers(internal_token, account_token), query_params=params)

    @staticmethod
    def GET_gamification(account_key: str, account_token: str, internal_token: str = INTERNAL_TOKEN) -> tuple:
        return _send("GET", f"/accounts/{account_key}/gamification", _headers(internal_token, account_token))

    @staticmethod
    def POST_point_application(account_key: str, account_token: str, payload: dict, internal_token: str = INTERNAL_TOKEN) -> tuple:
        return _send("POST", f"/accounts/{account_key}/point_applications", _headers(internal_token, account_token), payload=payload)

    @staticmethod
    def POST_point_reset(account_key: str, account_token: str, internal_token: str = INTERNAL_TOKEN) -> tuple:
        return _send("POST", f"/accounts/{account_key}/point_resets", _headers(internal_token, account_token))

    @staticmethod
    def POST_saving(account_key: str, account_token: str, payload: dict, internal_token: str = INTERNAL_TOKEN) -> tuple:
        return _send("POST", f"/accounts/{account_key}/savings", _headers(internal_token, account_token), payload=payload)

    @staticmethod
    def POST_redemption(account_key: str, account_token: str, payload: dict, internal_token: str = INTERNAL_TOKEN) -> tuple:
        return _send("POST", f"/accounts/{account_key}/redemptions", _headers(internal_token, account_token), payload=payload)

    @staticmethod
    def GET_piggy_bank_entries(account_key: str, account_token: str, params: dict = None, internal_token: str = INTERNAL_TOKEN) -> tuple:
        return _send("GET", f"/accounts/{account_key}/piggy_bank_entries", _headers(internal_token, account_token), query_params=params)

    @staticmethod
    def POST_category(account_key: str, account_token: str, payload: dict, internal_token: str = INTERNAL_TOKEN) -> tuple:
        return _send("POST", f"/accounts/{account_key}/categories", _headers(internal_token, account_token), payload=payload)

    @staticmethod
    def GET_categories(account_key: str, account_token: str, params: dict = None, internal_token: str = INTERNAL_TOKEN) -> tuple:
        return _send("GET", f"/accounts/{account_key}/categories", _headers(internal_token, account_token), query_params=params)

    @staticmethod
    def GET_category(account_key: str, account_token: str, category_key: str, internal_token: str = INTERNAL_TOKEN) -> tuple:
        return _send("GET", f"/accounts/{account_key}/categories/{category_key}", _headers(internal_token, account_token))

    @staticmethod
    def DELETE_category(account_key: str, account_token: str, category_key: str, internal_token: str = INTERNAL_TOKEN) -> tuple:
        return _send("DELETE", f"/accounts/{account_key}/categories/{category_key}", _headers(internal_token, account_token))

    @staticmethod
    def POST_block(account_key: str, payload: dict, internal_token: str = INTERNAL_TOKEN, admin_token: str = ADMIN_TOKEN) -> tuple:
        return _send("POST", f"/internal/accounts/{account_key}/blocks", _headers(internal_token, admin_token=admin_token), payload=payload)

    @staticmethod
    def POST_unblock(account_key: str, internal_token: str = INTERNAL_TOKEN, admin_token: str = ADMIN_TOKEN) -> tuple:
        return _send("POST", f"/internal/accounts/{account_key}/unblocks", _headers(internal_token, admin_token=admin_token))

    @staticmethod
    def POST_day_closing(payload: dict, internal_token: str = INTERNAL_TOKEN, admin_token: str = ADMIN_TOKEN) -> tuple:
        return _send("POST", "/internal/day_closings", _headers(internal_token, admin_token=admin_token), payload=payload)
