import json
from datetime import date
from os import environ
from types import SimpleNamespace
from unittest.mock import Mock, call

import pytest
from psycopg2.errors import LockNotAvailable, QueryCanceled
from requests.exceptions import Timeout
from sqlalchemy.exc import OperationalError

environ.setdefault("DATABASE_URL", "postgresql+psycopg2://bootcamp:bootcamp@localhost:5432/bootcamp")

from connectors import BcbConnector
from controllers.gamification_controller import GamificationController
from controllers.piggy_bank_controller import PiggyBankController
from controllers.transaction_controller import TransactionController
from errors import CdiUnavailable
from errors.handlers import register_error_handlers
from models import Account, AccountStatus
from repositories import AccountRepository
from tests.utils.requisition import ClientRequisition


def test_idempotency_is_rechecked_after_waiting_before_state_and_balance():
    account = SimpleNamespace(id=1, account_key="a", status=SimpleNamespace(enumerator=AccountStatus.BLOCKED), balance=0)
    piggy = SimpleNamespace(id=2, balance=0)
    first = SimpleNamespace(transaction_key="first")
    for method, response_method in [("save", "_saving_response"), ("redeem", "_redemption_response")]:
        controller = PiggyBankController.__new__(PiggyBankController)
        controller.get_owned_account = Mock(return_value=account)
        controller._find_repeated = Mock(side_effect=[None, first])
        controller.bank_clock_repository = Mock()
        controller._lock_account_and_piggy_bank = Mock(return_value=(account, piggy))
        setattr(controller, response_method, Mock(return_value={"transaction_key": "first", "balance": 7}))
        result = getattr(controller, method)("a", "token", {"request_control_key": "key", "amount": 1})
        assert result == {"transaction_key": "first", "balance": 7}
        assert controller._find_repeated.call_count == 2
    controller = TransactionController.__new__(TransactionController)
    controller.get_owned_account = Mock(return_value=account)
    controller._find_repeated = Mock(side_effect=[None, first])
    controller.bank_clock_repository = Mock()
    controller.account_repository = Mock()
    controller.account_repository.get_customer_account.return_value = None
    controller.account_repository.lock_accounts.return_value = [account]
    controller._balance_after = Mock(return_value=7)
    controller.rng = Mock()
    assert controller.transfer("a", "token", {"request_control_key": "key", "amount": 1, "destination_account_key": "b"}) == {"transaction_key": "first", "balance": 7}
    assert controller._find_repeated.call_count == 2
    assert controller.rng.mock_calls == []


def test_lock_accounts_orders_by_internal_id_before_for_update():
    repository = AccountRepository.__new__(AccountRepository)
    repository.session = Mock()
    query = Mock()
    repository.session.query.return_value = query
    for name in ["filter", "order_by", "with_for_update", "populate_existing"]:
        getattr(query, name).return_value = query
    query.all.return_value = ["locked"]
    assert repository.lock_accounts([SimpleNamespace(id=9), SimpleNamespace(id=2)]) == ["locked"]
    query.order_by.assert_called_once_with(Account.id)
    query.with_for_update.assert_called_once_with()
    assert query.method_calls.index(call.order_by(Account.id)) < query.method_calls.index(call.with_for_update())
    assert query.filter.call_args.args[0].right.value == [2, 9]


def test_rank_upgrade_ends_previous_grace_before_up():
    controller = GamificationController.__new__(GamificationController)
    controller.gamification_repository = Mock()
    account = SimpleNamespace(rank=SimpleNamespace(enumerator="BRONZE"), grace_until=date(2026, 7, 1))
    day = date(2026, 6, 2)
    assert controller.raise_rank(account, SimpleNamespace(balance=500000), day) is True
    assert controller.gamification_repository.create_rank_event.call_args_list == [
        call(account, "BRONZE", "GRACE_END", day), call(account, "SILVER", "UP", day)]
    controller.gamification_repository.reset_mock()
    account.grace_until = None
    assert controller.raise_rank(account, SimpleNamespace(balance=500000), day) is True
    controller.gamification_repository.create_rank_event.assert_called_once_with(account, "SILVER", "UP", day)
    controller.gamification_repository.reset_mock()
    assert controller.raise_rank(account, SimpleNamespace(balance=100000), day) is False
    assert controller.gamification_repository.mock_calls == []


def test_every_unexpected_5xx_is_reported_and_clear_resets():
    ClientRequisition.start_test()
    try:
        for status, code in [(200, None), (503, "QIT001031"), (503, "QIT000503"),
                             (500, "QIT000500"), (503, "other"), (502, None), (504, None)]:
            ClientRequisition.record("get", "/probe", status, {"code": code})
        assert [(status, code) for _, _, status, code in ClientRequisition.server_errors()] == [
            (500, "QIT000500"), (503, "other"), (502, None), (504, None)]
    finally:
        ClientRequisition.start_test()
    assert ClientRequisition.server_errors() == []


def test_database_timeouts_map_to_the_specific_503_without_waiting():
    class Application:
        def __init__(self):
            self.handlers = {}

        def exception_handler(self, error_class):
            def save(handler):
                self.handlers[error_class] = handler
                return handler
            return save

    application = Application()
    register_error_handlers(application)
    request = SimpleNamespace(method="POST", url=SimpleNamespace(path="/probe"))
    for original in [LockNotAvailable(), QueryCanceled()]:
        response = application.handlers[OperationalError](request, OperationalError("probe", {}, original))
        assert response.status_code == 503
        assert json.loads(response.body)["code"] == "QIT000503"


def test_cdi_timeout_is_a_project_503_without_network_or_waiting():
    connector = BcbConnector()
    connector.send = Mock(side_effect=Timeout())
    with pytest.raises(CdiUnavailable) as result:
        connector.get_cdi_rate(date(2026, 6, 1))
    assert (result.value.http_status, result.value.code) == (503, "QIT001031")


def test_transfer_prize_uses_injected_generator_and_normal_xp_only():
    origin = SimpleNamespace(id=1, account_key="a", balance=10100,
                             status=SimpleNamespace(enumerator="ACTIVE"), points_fee=0, points_chance=10)
    destination = SimpleNamespace(id=2, account_key="b", balance=0, status=SimpleNamespace(enumerator="ACTIVE"))
    bank = SimpleNamespace(id=3, balance=None)
    controller = TransactionController.__new__(TransactionController)
    controller.get_owned_account = Mock(return_value=origin)
    controller._find_repeated = Mock(return_value=None)
    controller.bank_clock_repository = Mock()
    controller.bank_clock_repository.get_accounting_date.return_value = date(2026, 6, 1)
    controller.account_repository = Mock()
    controller.account_repository.get_customer_account.return_value = destination
    controller.account_repository.lock_accounts.return_value = [origin, destination]
    controller.account_repository.get_system_account.return_value = bank
    controller.transaction_repository = Mock()
    controller.transaction_repository.count_transfers_sent.return_value = 0
    controller.transaction_repository.create.return_value = SimpleNamespace(transaction_key="first")
    controller.entry_repository = Mock()
    created = []

    def create(transaction, account, kind, amount):
        created.append((account.id, kind, amount))
        if account.balance is not None:
            account.balance += amount

    controller.entry_repository.create.side_effect = create
    controller.gamification_controller = Mock()
    controller.rng = Mock()
    controller.rng.randrange.return_value = 0
    controller.session = Mock()
    controller.logger = Mock()
    result = controller.transfer("a", "token", {"request_control_key": "key", "amount": 10000, "destination_account_key": "b"})
    assert result == {"transaction_key": "first", "balance": 10100}
    assert destination.balance == 10000
    assert created == [(1, "AMOUNT", -10000), (1, "FEE", -100), (2, "AMOUNT", 10000),
                       (3, "FEE", 100), (3, "PRIZE", -10100), (1, "PRIZE", 10100)]
    controller.rng.randrange.assert_called_once_with(1000)
    assert [c.args[1:3] for c in controller.gamification_controller.award_transfer_xp.call_args_list] == [
        (10000, "TRANSFER_SENT"), (10000, "TRANSFER_RECEIVED")]
    controller.session.commit.assert_called_once_with()
