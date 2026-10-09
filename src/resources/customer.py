from fastapi import status as http_status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from controllers import CustomerController
from utils.schema_handler import SchemaHandler


class CustomerResource:
    """A porta HTTP do cliente: confere o corpo, chama o controller e devolve o status.

    Sem regra de negócio, sem SQL e sem nada guardado no self: o mesmo
    resource atende todas as requisições (ARQ-02).
    """

    @SchemaHandler.validate("post_customers.json")
    def on_post(self, payload: dict) -> JSONResponse:
        controller = CustomerController()
        customer = controller.create(payload)

        return JSONResponse(
            content=jsonable_encoder(customer),
            status_code=http_status.HTTP_201_CREATED,
        )
