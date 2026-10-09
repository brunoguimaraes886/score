from tests.utils.payload_generator import PayloadGenerator
from tests.utils.request_generator import RequestGenerator


class ObjectGenerator:
    """Monta os dados de um teste pelas rotas, como um cliente faria (TST-01).

    Cada função confere o status de sucesso da rota que chama: se a
    montagem falha, o teste para ali, com a resposta na mensagem do assert.
    """

    @staticmethod
    def create_customer(name: str = None, document_number: str = None, email: str = None, birthdate: str = None) -> str:
        """Cadastra um cliente e devolve a customer_key."""
        payload = PayloadGenerator.customer(name=name, document_number=document_number, email=email, birthdate=birthdate)

        status, response = RequestGenerator.POST_customer(payload)
        assert status == 201, response

        return response["customer_key"]

    @staticmethod
    def create_account(customer_key: str = None) -> dict:
        """Abre uma conta e devolve customer_key, account_key e account_token.

        Sem `customer_key`, cadastra um cliente novo antes.
        """
        if customer_key is None:
            customer_key = ObjectGenerator.create_customer()

        status, response = RequestGenerator.POST_account(customer_key)
        assert status == 201, response

        return {
            "customer_key": customer_key,
            "account_key": response["account_key"],
            "account_token": response["account_token"],
        }

    @staticmethod
    def create_funded_account(amount: int = 100000) -> dict:
        """Abre uma conta, deposita `amount` centavos nela e devolve o mesmo dicionário do create_account."""
        account = ObjectGenerator.create_account()

        status, response = RequestGenerator.POST_deposit(account["account_key"], PayloadGenerator.deposit(amount=amount))
        assert status == 201, response

        return account
