from datetime import timedelta
from uuid import uuid4

from sqlalchemy import func

from database import SessionLocal
from models import RequestLog


class RequestLogRepository:
    """Grava e conta as linhas de request_log (PRD-06, PRD-14), com sessão própria.

    É o único repository que não recebe o contexto da requisição: cada
    método abre uma sessão, faz o trabalho e fecha. Assim a linha do log
    fica fora da transação da regra, e o pedido barrado, cuja transação é
    desfeita, deixa a linha dele gravada (DAD-13). Quem chama são os
    middlewares request_log_writer e auth_barrier, nunca um controller.
    """

    def create(
        self,
        request_id: str,
        method: str,
        path: str,
        status: int,
        error_code: str,
        client_ip: str,
        account_key: str,
        auth_failure: str,
    ) -> None:
        request_log = RequestLog()
        request_log.request_log_key = str(uuid4())
        request_log.request_id = request_id
        request_log.method = method
        request_log.path = path
        request_log.status = status
        request_log.error_code = error_code
        request_log.client_ip = client_ip
        request_log.account_key = account_key
        request_log.auth_failure = auth_failure

        with SessionLocal() as session:
            session.add(request_log)
            session.commit()

    def count_auth_failures(
        self,
        client_ip: str,
        auth_failures: list,
        window_minutes: int,
        account_key: str = None,
    ) -> int:
        """Quantas linhas deste IP falharam num dos tokens de `auth_failures` nos últimos `window_minutes` minutos.

        Com `account_key`, conta só as linhas dessa conta (a barreira do
        token da conta, passo 5.9). A janela é medida pelo relógio do
        banco (`now()`), o mesmo que preenche o `created_at`.
        """
        with SessionLocal() as session:
            query = session.query(func.count(RequestLog.id)).filter(
                RequestLog.client_ip == client_ip,
                RequestLog.auth_failure.in_(auth_failures),
                RequestLog.created_at >= func.now() - timedelta(minutes=window_minutes),
            )

            if account_key is not None:
                query = query.filter(RequestLog.account_key == account_key)

            return query.scalar()
