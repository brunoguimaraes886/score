import re
from datetime import date

from requests.exceptions import RequestException

from connectors.rest_connector import RestConnector
from constants import BCB_API_TIMEOUT, BCB_API_URL
from errors import CdiUnavailable


# COF-17: o caminho da série 12 do SGS (CDI diário), o mesmo no Banco
# Central e no Mockserver que faz o papel dele (ARQ-07, ARQ-12).
CDI_SERIES_PATH = "/dados/serie/bcdata.sgs.12/dados"

# A taxa vem em texto, em % ao dia, com ponto decimal ("0.054266").
CDI_RATE_PATTERN = re.compile(r"^[0-9]+\.[0-9]+$")


class BcbConnector(RestConnector):
    """Fala com o Banco Central: a taxa do CDI de um dia (ARQ-07, COF-17).

    Quem responde é o Mockserver do compose, carregado com 10 anos de CDI
    real (ARQ-12). O endereço e o timeout vêm do ambiente (PRD-01, PRD-03).
    O Banco Central não pede token: internal_token None deixa o cabeçalho
    INTERNAL-TOKEN de fora (o requests descarta cabeçalho com valor None).
    """

    def __init__(self) -> None:
        super().__init__(
            class_name=__name__,
            base_url=BCB_API_URL,
            timeout=BCB_API_TIMEOUT,
            internal_token=None,
        )

    def get_cdi_rate(self, accounting_date: date) -> str:
        """A taxa do CDI do dia, em texto e em % ao dia ("0.054266"); None quando o dia não tem taxa (COF-16).

        Resposta esperada: 200 com uma lista JSON. Lista vazia: o dia não
        tem taxa (fim de semana ou feriado). Lista com um item {"data":
        "DD/MM/AAAA", "valor": "0.054266"} do mesmo dia: a taxa. Qualquer
        outra coisa (timeout, erro de conexão, outro status, outro corpo)
        levanta CdiUnavailable: 503 QIT001031, e a virada não grava nada
        (COF-20).
        """
        day = accounting_date.strftime("%d/%m/%Y")
        endpoint = f"{CDI_SERIES_PATH}?formato=json&dataInicial={day}&dataFinal={day}"

        try:
            response = self.send(endpoint=endpoint, method="GET")
        except RequestException:
            raise CdiUnavailable(accounting_date.isoformat()) from None

        if response.status != 200 or not isinstance(response.json, list) or len(response.json) > 1:
            raise CdiUnavailable(accounting_date.isoformat())

        if len(response.json) == 0:
            return None

        rate = response.json[0]

        if not isinstance(rate, dict) or rate.get("data") != day or not isinstance(rate.get("valor"), str):
            raise CdiUnavailable(accounting_date.isoformat())

        if CDI_RATE_PATTERN.fullmatch(rate["valor"]) is None:
            raise CdiUnavailable(accounting_date.isoformat())

        return rate["valor"]
