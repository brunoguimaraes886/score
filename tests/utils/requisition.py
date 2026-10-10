import json
from requests import request, Response
from requests.exceptions import ConnectionError as RequestsConnectionError
from os import environ


API_OFFLINE = (
    "Não consegui falar com a API em {base_url}.\n"
    "Ela precisa estar de pé pros testes rodarem. Suba com:  docker compose up"
)

# R3, TST-08: somente os 503 previstos para dependência lenta ou fora do ar:
# timeout do banco, banco indisponível e falha do CDI.
ACCEPTED_SERVER_ERROR_CODES = ("QIT000503", "QIT000504", "QIT001031")


class ClientRequisition:
    # Cada resposta da API recebida no teste em andamento, como (método,
    # caminho, status, code). É da classe, e não do objeto: as threads dos
    # testes de concorrência gravam na mesma lista. Quem a esvazia antes de
    # cada teste e a confere depois é a fixture no_server_errors, em
    # tests/conftest.py.
    received_responses = []

    @staticmethod
    def send(
        method,
        endpoint,
        payload=None,
        headers=None,
        data=None,
        cert=None,
        query_params=None,
        verify=True,
    ):

        if headers is None:
            headers = dict()

        api_host = environ.get("SERVER_LOCALHOST", "127.0.0.1")
        api_port = environ.get("API_PORT", "3000")
        base_url = f"http://{api_host}:{api_port}"

        url = f"{base_url}{endpoint}"

        try:
            response = request(
                method.upper(),
                url,
                headers=headers,
                json=payload,
                data=data,
                cert=cert,
                verify=verify,
                params=query_params,
                timeout=30,
            )
        except RequestsConnectionError:
            raise RuntimeError(API_OFFLINE.format(base_url=base_url)) from None

        base_response = BaseConnectorResponse(
            endpoint=endpoint,
            method=method,
            payload=payload,
            headers=headers,
            response=response,
        )

        ClientRequisition.record(method, endpoint, base_response.response_status, base_response.response_json)

        return base_response

    @staticmethod
    def start_test() -> None:
        """Esvazia a lista de respostas: a fixture no_server_errors chama antes de cada teste."""
        ClientRequisition.received_responses.clear()

    @staticmethod
    def record(method: str, endpoint: str, status: int, response_json) -> None:
        """Guarda uma resposta da API: método, caminho, status e o campo code do corpo (None quando o corpo não é um objeto JSON com code)."""
        code = None

        if isinstance(response_json, dict):
            code = response_json.get("code")

        ClientRequisition.received_responses.append((method.upper(), endpoint, status, code))

    @staticmethod
    def server_errors() -> list:
        """As respostas 5xx do teste em andamento, menos o 503 com um código de ACCEPTED_SERVER_ERROR_CODES (R3)."""
        errors = []

        for method, endpoint, status, code in list(ClientRequisition.received_responses):
            if status < 500:
                continue

            if status == 503 and code in ACCEPTED_SERVER_ERROR_CODES:
                continue

            errors.append((method, endpoint, status, code))

        return errors


class BaseConnectorResponse:
    def __init__(
        self,
        response: Response,
        endpoint: str,
        method: str,
        headers: dict,
        payload: dict,
    ) -> None:
        self.endpoint = endpoint
        self.method = method
        self.payload = payload
        self.headers = headers
        self.response = response
        self.response_content = response.content
        self.response_status = response.status_code

        self.response_json = None
        try:
            self.response_json = json.loads(self.response_content)
        except Exception as ex:
            print(ex)
            ...
            # logger warning
