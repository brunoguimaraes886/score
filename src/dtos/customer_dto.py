from models import Customer


class CustomerDTO:
    """O cliente que a API devolve: a key pública, nunca o id (R5).

    O CPF sai inteiro: só o dono consulta o próprio cliente (API-17).
    """

    @staticmethod
    def obj_to_dict(customer: Customer) -> dict:
        return {
            "customer_key": customer.customer_key,
            "name": customer.name,
            "document_number": customer.document_number,
            "email": customer.email,
            "birthdate": customer.birthdate.isoformat(),
        }

    @staticmethod
    def only_obj_key(customer: Customer) -> dict:
        return {"customer_key": customer.customer_key}
