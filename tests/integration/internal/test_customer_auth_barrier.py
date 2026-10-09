from uuid import uuid4

from tests.utils import DbUtils, ObjectGenerator, RequestGenerator


class TestCustomerAuthBarrier:
    def test_customer_and_account_share_the_account_ip_counter(self):
        DbUtils.rollback()
        account = ObjectGenerator.create_account()
        other = ObjectGenerator.create_account()
        for _ in range(5):
            status, response = RequestGenerator.GET_customer(account["customer_key"], "wrong")
            assert (status, response["code"]) == (404, "QIT001008")
        for _ in range(5):
            status, response = RequestGenerator.GET_account(account["account_key"], "wrong")
            assert (status, response["code"]) == (404, "QIT001010")
        for send, key in [(RequestGenerator.GET_customer, account["customer_key"]),
                          (RequestGenerator.GET_account, account["account_key"])]:
            status, response = send(key, account["account_token"])
            assert (status, response["code"]) == (429, "QIT000429")
        assert RequestGenerator.GET_account(other["account_key"], other["account_token"])[0] == 200

    def test_unknown_customer_has_a_normalized_fallback_counter(self):
        DbUtils.rollback()
        key = str(uuid4())
        for _ in range(5):
            for spelling in [key, key.upper()]:
                status, response = RequestGenerator.GET_customer(spelling, "wrong")
                assert (status, response["code"]) == (404, "QIT001008")
        status, response = RequestGenerator.GET_customer(key, "wrong")
        assert (status, response["code"]) == (429, "QIT000429")
