from abc import ABCMeta

from database import get_context
from errors import AccountNotFound
from models import Account, RequestLog
from repositories import AccountRepository
from utils.account_token import account_token_matches
from utils.logger import get_logger
from utils.request_context import get_request_state


class BaseController(metaclass=ABCMeta):
    """O que todo controller tem em comum: a conexão com o banco, o log e a checagem de dono.

    Nada chega por parâmetro: o controller pega o CONTEXTO da requisição
    em que está rodando. Quem preparou esse contexto foi o middleware.

    Guardar o `self.context`, e não só a sessão, é o que permite o
    repository receber `context` em vez de `db`: o contexto é a coisa que
    viaja entre as camadas, e a sessão é só o que ele carrega hoje.

    É aqui que a sessão nasce, no `get_or_create_session` — construir um
    controller é a mesma coisa que dizer "eu uso banco".
    """

    def __init__(self, class_name: str) -> None:
        self.context = get_context()
        self.session = self.context.get_or_create_session()
        self.logger = get_logger(class_name)

    def mark_account_auth_failure(self) -> None:
        """Anota no estado da requisição que o token da conta falhou (PRD-14)."""
        request_state = get_request_state()
        if request_state is not None:
            request_state.auth_failure = RequestLog.ACCOUNT

    def get_owned_account(self, account_key: str, account_token: str) -> Account:
        """A conta de cliente da URL, se o ACCOUNT-TOKEN é o dela (API-08, API-09)."""
        account = AccountRepository(self.context).get_customer_account(account_key)
        if account is None or not account_token_matches(account_token, account.token_hash):
            self.mark_account_auth_failure()
            raise AccountNotFound(account_key)
        return account
