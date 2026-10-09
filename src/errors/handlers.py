from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from psycopg2 import errors as psycopg2_errors
from sqlalchemy.exc import OperationalError
from starlette.exceptions import HTTPException as StarletteHTTPException

from errors.base_error import (
    QIException,
    DatabaseTimeout,
    InternalError,
    InvalidParameter,
    InvalidSchema,
    MethodNotAllowed,
    NotFoundResource,
)
from utils.logger import get_logger
from utils.request_context import REQUEST_ID_HEADER, get_request_state


logger = get_logger(__name__)


def qi_exception_to_response(exception: QIException, request: Request = None) -> JSONResponse:
    """Traduz um erro nosso para a resposta JSON que o cliente recebe.

    Este é o único lugar do projeto que sabe como um erro vira HTTP. Ele
    também anota o código do erro no estado da requisição: é de lá que o
    middleware request_log_writer o grava em request_log (PRD-14).
    """
    request_state = get_request_state()
    request_id = getattr(getattr(request, "state", None), "request_id", None)
    if request_state is not None:
        request_state.error_code = exception.code
        request_id = request_id or request_state.request_id

    body = {
        "title": exception.title,
        "description": exception.description,
        "translation": exception.translation,
        "code": exception.code,
    }
    headers = {REQUEST_ID_HEADER: request_id} if request_id is not None else None
    return JSONResponse(status_code=exception.http_status, content=body, headers=headers)


def is_database_timeout(exception: Exception) -> bool:
    """True quando o PostgreSQL desistiu por tempo (PRD-08).

    `LockNotAvailable` (SQLSTATE 55P03): passou do lock_timeout esperando
    uma trava. `QueryCanceled` (SQLSTATE 57014): passou do
    statement_timeout rodando o comando. O SQLAlchemy embrulha o erro do
    psycopg2 num OperationalError e guarda o original em `.orig`.
    """
    original = getattr(exception, "orig", None)
    return isinstance(original, (psycopg2_errors.LockNotAvailable, psycopg2_errors.QueryCanceled))


def describe_validation_error(error: dict) -> str:
    location = []
    for part in error.get("loc", []):
        if part not in ("body", "query"):
            location.append(str(part))

    message = error.get("msg", "invalid value")

    if location:
        return f"{message} in {'.'.join(location)}"

    return message


def register_error_handlers(application: FastAPI) -> None:
    """Ensina a aplicação a responder cada tipo de erro."""

    @application.exception_handler(QIException)
    def handle_qi_exception(request: Request, exception: QIException) -> JSONResponse:
        return qi_exception_to_response(exception, request)

    @application.exception_handler(StarletteHTTPException)
    def handle_http_exception(request: Request, exception: StarletteHTTPException) -> JSONResponse:
        if exception.status_code == 400:
            return qi_exception_to_response(InvalidSchema("Invalid JSON request body."), request)

        if exception.status_code == 404:
            return qi_exception_to_response(NotFoundResource(), request)

        if exception.status_code == 405:
            return qi_exception_to_response(MethodNotAllowed(), request)

        logger.error(f"HTTP {exception.status_code} em {request.url.path}: {exception.detail}")
        return qi_exception_to_response(InternalError(), request)

    @application.exception_handler(RequestValidationError)
    def handle_validation_error(request: Request, exception: RequestValidationError) -> JSONResponse:
        errors = exception.errors()

        if errors:
            first_error = errors[0]
        else:
            first_error = {}

        description = describe_validation_error(first_error)
        origin = first_error.get("loc", [""])[0]

        # Hoje este ramo não é alcançado: corpo e query string são julgados
        # pelo JSON Schema (utils/schema_handler.py), e os parâmetros de
        # caminho são todos `str`. Ele fica para a rota que declarar um
        # parâmetro tipado.
        if origin in ("query", "path"):
            return qi_exception_to_response(InvalidParameter(description), request)

        return qi_exception_to_response(InvalidSchema(description), request)

    @application.exception_handler(OperationalError)
    def handle_operational_error(request: Request, exception: OperationalError) -> JSONResponse:
        # A sessão da rota fica com a transação abortada; o session_manager
        # a fecha, e fechar desfaz tudo: nada é gravado (PRD-08).
        if is_database_timeout(exception):
            logger.warning(f"Timeout do banco em {request.method} {request.url.path}")
            return qi_exception_to_response(DatabaseTimeout(), request)

        logger.exception(f"Erro do banco em {request.method} {request.url.path}")
        return qi_exception_to_response(InternalError(), request)

    @application.exception_handler(Exception)
    def handle_unexpected_error(request: Request, exception: Exception) -> JSONResponse:
        logger.exception(f"Erro inesperado em {request.method} {request.url.path}")
        return qi_exception_to_response(InternalError(), request)
