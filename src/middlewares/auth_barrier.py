import re

from fastapi import FastAPI, Request
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.exc import OperationalError

from constants import AUTH_FAILURE_LIMIT, AUTH_FAILURE_WINDOW_MINUTES, BYPASS_ENDPOINTS
from errors.base_error import DatabaseTimeout, TooManyAuthFailures
from errors.handlers import is_database_timeout, qi_exception_to_response
from middlewares.request_log_writer import get_client_ip
from models import RequestLog
from repositories import RequestLogRepository
from utils.request_context import get_request_state


INTERNAL_AUTH_FAILURES = [RequestLog.INTERNAL, RequestLog.ADMIN]
ACCOUNT_AUTH_FAILURES = [RequestLog.ACCOUNT]


def count_failures(client_ip: str, account_key: str) -> tuple:
    repository = RequestLogRepository()
    internal_failures = repository.count_auth_failures(client_ip, INTERNAL_AUTH_FAILURES, AUTH_FAILURE_WINDOW_MINUTES)
    account_failures = 0
    if account_key is not None:
        account_failures = repository.count_auth_failures(
            client_ip, ACCOUNT_AUTH_FAILURES, AUTH_FAILURE_WINDOW_MINUTES, account_key,
        )
    return internal_failures, account_failures


def register_auth_barrier_middleware(application: FastAPI) -> None:
    """Aplica limites de falhas de autenticação por IP e conta, com contagem no banco."""

    @application.middleware("http")
    async def check_auth_barrier(request: Request, call_next):
        if request.method == "OPTIONS" or request.url.path in BYPASS_ENDPOINTS:
            return await call_next(request)
        request_state = get_request_state()
        try:
            customer_path = re.fullmatch(r"/customers/([^/]+)", request.url.path)
            if request.method == "GET" and customer_path is not None:
                request_state.account_key = await run_in_threadpool(
                    RequestLogRepository().resolve_customer_auth_key, customer_path.group(1),
                )
            internal_failures, account_failures = await run_in_threadpool(
                count_failures, get_client_ip(request), request_state.account_key,
            )
        except OperationalError as error:
            if is_database_timeout(error):
                return qi_exception_to_response(DatabaseTimeout())
            raise
        if internal_failures >= AUTH_FAILURE_LIMIT or account_failures >= AUTH_FAILURE_LIMIT:
            return qi_exception_to_response(TooManyAuthFailures())
        return await call_next(request)
