import os


SERVICE_ROOT = os.path.abspath(os.path.dirname(__file__))

# Onde moram os arquivos de schema — os .json que descrevem o formato
# que cada requisicao precisa ter. Quem le essa pasta e o
# src/utils/schema_handler.py.
SCHEMA_PATH = os.path.join(SERVICE_ROOT, "schemas")

APP_ENV = os.environ.get("APP_ENV", "local")
SERVICE_NAME = os.environ.get("SERVICE_NAME", "bootcamp-api")

DATABASE_URL = os.environ.get("DATABASE_URL")
INTERNAL_TOKEN = os.environ.get("INTERNAL_TOKEN")

# PRD-07, PRD-13: o segundo token das rotas /internal (virada do dia,
# bloquear e desbloquear conta). Sem padrão aqui, como o INTERNAL_TOKEN:
# o padrão de estudo mora no docker-compose.yml.
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN")

# Os nomes dos cabeçalhos de token (API-04, API-16, PRD-13).
INTERNAL_TOKEN_HEADER = "INTERNAL-TOKEN"
ACCOUNT_TOKEN_HEADER = "ACCOUNT-TOKEN"
ADMIN_TOKEN_HEADER = "ADMIN-TOKEN"

# API-13: todo caminho que começa aqui pede também o ADMIN-TOKEN.
INTERNAL_PREFIX = "/internal"

# PRD-10: AUTH_FAILURE_LIMIT erros de token do mesmo IP dentro de
# AUTH_FAILURE_WINDOW_MINUTES minutos fazem a API responder 429.
AUTH_FAILURE_LIMIT = int(os.environ.get("AUTH_FAILURE_LIMIT", "10"))
AUTH_FAILURE_WINDOW_MINUTES = int(os.environ.get("AUTH_FAILURE_WINDOW_MINUTES", "15"))

# PRD-08: quanto o banco espera, em milissegundos, por uma trava
# (lock_timeout) e por um comando (statement_timeout) antes de desistir.
DB_LOCK_TIMEOUT_MS = int(os.environ.get("DB_LOCK_TIMEOUT_MS", "5000"))
DB_STATEMENT_TIMEOUT_MS = int(os.environ.get("DB_STATEMENT_TIMEOUT_MS", "5000"))

# ARQ-07, COF-17: o Banco Central, de onde vem a taxa do CDI (série 12 do
# SGS). Na entrega e nos testes, quem responde é o Mockserver do compose
# (ARQ-12): a API nunca fala com o Banco Central de verdade.
BCB_API_URL = os.environ.get("BCB_API_URL", "http://mockserver:1080")

# PRD-03, COF-20: quantos segundos esperar pela taxa antes de desistir.
# Passou, a virada responde 503 e o dia não avança.
BCB_API_TIMEOUT = int(os.environ.get("BCB_API_TIMEOUT", "5"))

# Rotas públicas: não exigem o header INTERNAL-TOKEN. São as duas que
# precisam responder pra quem ainda não tem token nenhum: a raiz, que
# diz quem é este serviço, e o health check, que o Docker consulta pra
# saber se a API já está de pé.
BYPASS_ENDPOINTS = [
    "/",
    "/health_check",
]

DAILY_TRANSFER_LIMIT = int(os.environ.get("DAILY_TRANSFER_LIMIT", "10"))

REQUIRED_VARIABLES = ["DATABASE_URL", "INTERNAL_TOKEN", "ADMIN_TOKEN"]


def check_variables():
    missing = []
    for name in REQUIRED_VARIABLES:
        if not globals().get(name):
            missing.append(name)

    if missing:
        raise EnvironmentError(
            f"Faltam variáveis de ambiente: {', '.join(missing)}. "
            "Rodando com 'docker compose up' elas já vêm preenchidas. "
            "Fora do Docker, copie o .env.example para .env."
        )
