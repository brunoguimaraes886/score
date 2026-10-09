"""Baixa o CDI diário do Banco Central e grava as respostas do Mockserver (ARQ-07, ARQ-12, COF-16, COF-17).

Roda uma vez, à mão, no desenvolvimento, e nunca na suíte nem no compose:
na entrega, o Mockserver já sobe com o arquivo gerado aqui, e nem a API
nem os testes falam com o Banco Central (ARQ-12).

Da raiz do repositório:

    ./.venv/Scripts/python.exe scripts/download_cdi.py

O que faz:
1. pede ao Banco Central a série 12 do SGS (CDI, em % ao dia) de
   START_DATE a END_DATE, numa chamada só (o SGS entrega até 10 anos);
2. confere cada linha: data dentro do período, sem repetição, taxa em
   texto com ponto decimal;
3. grava mockserver/cdi_expectations.json: uma expectativa do Mockserver
   por dia de calendário do período. Dia com taxa responde a lista com a
   taxa, como o Banco Central; dia sem taxa (fim de semana e feriado)
   responde a lista vazia (COF-16).

Depois, confira as três datas que o script mostra contra o site do Banco
Central antes do commit (ARQ-12).
"""

import json
import re
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path


SERIES_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados"

# O caminho que o BcbConnector chama no Mockserver: o mesmo do Banco Central.
CDI_SERIES_PATH = "/dados/serie/bcdata.sgs.12/dados"

# O período: 10 anos menos um dia, dentro do limite de uma chamada do SGS.
START_DATE = date(2016, 10, 1)
END_DATE = date(2026, 9, 30)

DOWNLOAD_TIMEOUT_SECONDS = 120
CDI_RATE_PATTERN = re.compile(r"^[0-9]+\.[0-9]+$")
OUTPUT_FILE = Path(__file__).resolve().parents[1] / "mockserver" / "cdi_expectations.json"

# As três datas que o script mostra no fim, para conferir no site do Banco Central.
CHECK_DATES = [date(2026, 6, 1), date(2026, 6, 2), date(2026, 6, 3)]


def brazilian_date(day: date) -> str:
    """2026-06-01 → "01/06/2026", o formato do SGS."""
    return day.strftime("%d/%m/%Y")


def download_rates() -> dict:
    """{data: taxa em texto} dos dias com taxa publicada no período."""
    query = f"?formato=json&dataInicial={brazilian_date(START_DATE)}&dataFinal={brazilian_date(END_DATE)}"
    request = urllib.request.Request(SERIES_URL + query, headers={"Accept": "application/json"})

    with urllib.request.urlopen(request, timeout=DOWNLOAD_TIMEOUT_SECONDS) as response:
        rows = json.loads(response.read().decode("utf-8"))

    rates = {}
    for row in rows:
        day = datetime.strptime(row["data"], "%d/%m/%Y").date()
        rate = row["valor"]

        if day < START_DATE or day > END_DATE:
            raise ValueError(f"o SGS mandou uma data fora do período: {row['data']}")

        if day in rates:
            raise ValueError(f"o SGS mandou a mesma data duas vezes: {row['data']}")

        if not isinstance(rate, str) or CDI_RATE_PATTERN.fullmatch(rate) is None:
            raise ValueError(f"taxa fora do formato em {row['data']}: {rate!r}")

        rates[day] = rate

    return rates


def build_expectation(day: date, rate: str) -> dict:
    """A expectativa do Mockserver para um dia: a lista com a taxa, ou a lista vazia quando rate é None."""
    body = []
    if rate is not None:
        body = [{"data": brazilian_date(day), "valor": rate}]

    return {
        "httpRequest": {
            "method": "GET",
            "path": CDI_SERIES_PATH,
            "queryStringParameters": {
                "formato": ["json"],
                "dataInicial": [brazilian_date(day)],
                "dataFinal": [brazilian_date(day)],
            },
        },
        "httpResponse": {
            "statusCode": 200,
            "headers": {"Content-Type": ["application/json"]},
            "body": json.dumps(body),
        },
        "times": {"unlimited": True},
    }


def main() -> None:
    rates = download_rates()

    expectations = []
    day = START_DATE
    while day <= END_DATE:
        expectations.append(build_expectation(day, rates.get(day)))
        day = day + timedelta(days=1)

    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8", newline="\n") as output:
        json.dump(expectations, output, ensure_ascii=True, indent=2)
        output.write("\n")

    print(f"{len(expectations)} dias, {len(rates)} com taxa, de {START_DATE.isoformat()} a {END_DATE.isoformat()}")
    for check_date in CHECK_DATES:
        print(check_date.isoformat(), rates.get(check_date))
    print(f"gravado em {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
