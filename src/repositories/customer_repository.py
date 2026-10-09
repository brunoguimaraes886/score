from datetime import date
from uuid import uuid4

from database import Context
from models import Customer


class CustomerRepository:
    """Consulta e grava clientes (CLI-02). Nenhuma regra de negócio mora aqui.

    A key nasce aqui, com uuid4 (DAD-12). Quem confere CPF, e-mail e idade
    é o CustomerController, antes de chamar o create.
    """

    def __init__(self, context: Context) -> None:
        self.session = context.db_session

    def create(self, name: str, document_number: str, email: str, birthdate: date) -> Customer:
        customer = Customer()
        customer.customer_key = str(uuid4())
        customer.name = name
        customer.document_number = document_number
        customer.email = email
        customer.birthdate = birthdate

        self.session.add(customer)
        return customer

    def get_by_key(self, customer_key: str) -> Customer:
        return self.session.query(Customer).filter(Customer.customer_key == customer_key).first()

    def get_by_id(self, customer_id: int) -> Customer:
        return self.session.query(Customer).filter(Customer.id == customer_id).first()

    def get_by_document_number(self, document_number: str) -> Customer:
        return self.session.query(Customer).filter(Customer.document_number == document_number).first()

    def get_by_email(self, email: str) -> Customer:
        return self.session.query(Customer).filter(Customer.email == email).first()
