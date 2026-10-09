from fastapi import FastAPI, Request
from fastapi.concurrency import run_in_threadpool
from starlette.routing import Match

from constants import ACCOUNT_TOKEN_HEADER
from controllers.base_controller import BaseController
from controllers.customer_controller import CustomerController
from errors import InvalidSchema, QIException
from errors.handlers import qi_exception_to_response


BODY_ROUTES = {
    ("POST", "/customers"),
    ("POST", "/accounts/{account_key}/deposits"),
    ("POST", "/accounts/{account_key}/withdrawals"),
    ("POST", "/accounts/{account_key}/transfers"),
    ("POST", "/accounts/{account_key}/savings"),
    ("POST", "/accounts/{account_key}/redemptions"),
    ("POST", "/accounts/{account_key}/point_applications"),
    ("POST", "/accounts/{account_key}/categories"),
    ("POST", "/internal/accounts/{account_key}/blocks"),
    ("POST", "/internal/day_closings"),
}
QUERY_ROUTES = {
    ("GET", "/accounts/{account_key}/entries"),
    ("GET", "/accounts/{account_key}/piggy_bank_entries"),
    ("GET", "/accounts/{account_key}/categories"),
}


def check_owner(method, path, params, account_token):
    if path.startswith("/internal/"):
        return
    if "account_key" in params and (method, path) != ("POST", "/accounts/{account_key}/deposits"):
        BaseController(__name__).get_owned_account(params["account_key"], account_token)
    elif method == "GET" and path == "/customers/{customer_key}":
        CustomerController().get_by_key(params["customer_key"], account_token)


def register_input_contract_middleware(application: FastAPI) -> None:
    @application.middleware("http")
    async def check_input_contract(request: Request, call_next):
        selected = None
        params = {}
        for route in application.router.routes:
            match, scope = route.matches(request.scope)
            if match == Match.FULL:
                selected = route
                params = scope.get("path_params", {})
                break
        if selected is None:
            return await call_next(request)
        route_key = (request.method, selected.path)
        unexpected_query = route_key not in QUERY_ROUTES and len(request.query_params) > 0
        unexpected_body = route_key not in BODY_ROUTES and len(await request.body()) > 0
        if unexpected_query or unexpected_body:
            try:
                await run_in_threadpool(check_owner, request.method, selected.path, params,
                                        request.headers.get(ACCOUNT_TOKEN_HEADER))
            except QIException as error:
                return qi_exception_to_response(error)
            return qi_exception_to_response(InvalidSchema("Unexpected request body or query parameter."))
        return await call_next(request)
