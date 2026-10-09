from datetime import date

from sqlalchemy.exc import IntegrityError

from controllers.base_controller import BaseController
from dtos import CustomerDTO
from errors import (
    DuplicatedDocumentNumber,
    DuplicatedEmail,
    InvalidBirthdate,
    InvalidDocumentNumber,
    UnderageCustomer,
)
from repositories import CustomerRepository
from utils.document_number import is_valid_cpf


# CLI-03: idade mínima para o cadastro, sem idade máxima.
MINIMUM_AGE = 18


class CustomerController(BaseController):
    """As regras do cliente (CLI-02, CLI-03)."""

    def __init__(self) -> None:
        super().__init__(__name__)
        self.customer_repository = CustomerRepository(self.context)

    def create(self, customer_data: dict) -> dict:
        """Cadastra o cliente. As regras, nesta ordem, antes de gravar:

        1. CPF válido (422 QIT001003);
        2. CPF único (409 QIT001004);
        3. e-mail único (409 QIT001005);
        4. data de nascimento que existe no calendário (422 QIT001007);
        5. pelo menos MINIMUM_AGE anos, contados na data de hoje (422 QIT001006).

        O formato de cada campo já passou pelo schema post_customers.json.
        Dois cadastros iguais ao mesmo tempo passam juntos pelas perguntas
        2 e 3; o UNIQUE do banco barra o segundo no commit. Esse
        IntegrityError vira o 409 do campo repetido, nunca 500 (R3).
        """
        document_number = customer_data["document_number"]
        email = customer_data["email"]

        if not is_valid_cpf(document_number):
            raise InvalidDocumentNumber()

        if self.customer_repository.get_by_document_number(document_number) is not None:
            raise DuplicatedDocumentNumber()

        if self.customer_repository.get_by_email(email) is not None:
            raise DuplicatedEmail(email)

        birthdate = self._parse_birthdate(customer_data["birthdate"])
        age = self._age_in_years(birthdate)

        if age < MINIMUM_AGE:
            raise UnderageCustomer(age, MINIMUM_AGE)

        customer = self.customer_repository.create(customer_data["name"], document_number, email, birthdate)
        customer_dto = CustomerDTO.only_obj_key(customer)

        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()

            if self.customer_repository.get_by_document_number(document_number) is not None:
                raise DuplicatedDocumentNumber()

            if self.customer_repository.get_by_email(email) is not None:
                raise DuplicatedEmail(email)

            raise

        return customer_dto

    def _parse_birthdate(self, raw_birthdate: str) -> date:
        """Converte a data, ou recusa com 422 em vez de 500.

        O schema garantiu o formato; ele não sabe quantos dias tem
        fevereiro: "2025-02-30" chega aqui e para aqui.
        """
        try:
            return date.fromisoformat(raw_birthdate)
        except ValueError:
            raise InvalidBirthdate(raw_birthdate)

    def _age_in_years(self, birthdate: date) -> int:
        today = date.today()
        age = today.year - birthdate.year

        # Quem ainda não fez aniversário este ano tem um ano a menos.
        if (today.month, today.day) < (birthdate.month, birthdate.day):
            age = age - 1

        return age
