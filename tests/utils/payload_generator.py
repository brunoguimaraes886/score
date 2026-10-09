from uuid import uuid4

from tests.utils.random_generator import RandomGenerator


class PayloadGenerator:
    """Um corpo válido para cada rota com corpo, com qualquer campo trocado a pedido.

    Sem argumento, o que precisa ser único sai aleatório: CPF, e-mail,
    request_control_key e nome de categoria. Dinheiro sempre em centavos,
    número inteiro (R6, DAD-08). Para testar campo faltando, apague a
    chave do dicionário devolvido.
    """

    @staticmethod
    def customer(name: str = None, document_number: str = None, email: str = None, birthdate: str = None) -> dict:
        if name is None:
            name = "Maria da Silva"

        if document_number is None:
            document_number = RandomGenerator.generate_cpf()

        if email is None:
            email = f"maria.silva.{uuid4()}@exemplo.com.br"

        if birthdate is None:
            birthdate = "1990-05-17"

        return {
            "name": name,
            "document_number": document_number,
            "email": email,
            "birthdate": birthdate,
        }

    @staticmethod
    def deposit(
        amount: int = 100000,
        depositor_name: str = None,
        depositor_document: str = None,
        request_control_key: str = None,
    ) -> dict:
        if depositor_name is None:
            depositor_name = "Carlos Souza"

        if depositor_document is None:
            depositor_document = RandomGenerator.generate_cpf()

        if request_control_key is None:
            request_control_key = str(uuid4())

        return {
            "depositor_name": depositor_name,
            "depositor_document": depositor_document,
            "amount": amount,
            "request_control_key": request_control_key,
        }

    @staticmethod
    def withdrawal(amount: int = 1000, request_control_key: str = None) -> dict:
        if request_control_key is None:
            request_control_key = str(uuid4())

        return {"amount": amount, "request_control_key": request_control_key}

    @staticmethod
    def transfer(destination_account_key: str, amount: int = 1000, request_control_key: str = None) -> dict:
        if request_control_key is None:
            request_control_key = str(uuid4())

        return {
            "destination_account_key": destination_account_key,
            "amount": amount,
            "request_control_key": request_control_key,
        }

    @staticmethod
    def saving(amount: int = 1000, request_control_key: str = None, category_key: str = None) -> dict:
        """Sem `category_key`, o campo fica de fora e o dinheiro vai para "economias"."""
        if request_control_key is None:
            request_control_key = str(uuid4())

        payload = {"amount": amount, "request_control_key": request_control_key}

        if category_key is not None:
            payload["category_key"] = category_key

        return payload

    @staticmethod
    def redemption(amount: int = 1000, request_control_key: str = None, category_key: str = None) -> dict:
        """Sem `category_key`, o campo fica de fora e o dinheiro sai de "economias"."""
        if request_control_key is None:
            request_control_key = str(uuid4())

        payload = {"amount": amount, "request_control_key": request_control_key}

        if category_key is not None:
            payload["category_key"] = category_key

        return payload

    @staticmethod
    def category(name: str = None) -> dict:
        if name is None:
            name = f"Categoria {uuid4()}"

        return {"name": name}

    @staticmethod
    def point_application(benefit: str = "FEE", points: int = 1) -> dict:
        return {"benefit": benefit, "points": points}

    @staticmethod
    def day_closing(accounting_date: str) -> dict:
        return {"accounting_date": accounting_date}

    @staticmethod
    def block(reason: str = "MANUAL_REVIEW") -> dict:
        return {"reason": reason}
