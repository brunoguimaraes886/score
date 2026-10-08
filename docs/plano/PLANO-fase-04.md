> **Git local — Bruno, 08/10/2026:** durante a produção, branches, commits, merges e tags ficam locais. Não executar push, pull ou fetch nem exigir acesso ao GitHub. O envio completo será feito pelo Bruno somente no final, quando tudo estiver pronto. As verificações de commits e dependências são locais.

# PLANO — Fase 04 — esqueleto

**Branch:** `fase/04-esqueleto` · **Depende de:** fase 3
**Objetivo:** os middlewares de segurança e de log (estado da requisição, token de administração, registro em `request_log`, barreira contra chute de token), o timeout do banco e as funções de teste que montam os dados por HTTP.

Regras de execução: `AGENTS.md`. Nomes obrigatórios: `docs/plano/PLANO-00-indice.md`, `docs/plano/PLANO-fase-02.md` (tabela `request_log`, model `RequestLog`) e `docs/plano/PLANO-fase-03.md` (`docs/rotas.md`, catálogo de erros, schemas). Um passo por vez, na ordem: 4.1 a 4.8 e, por último, 4.fim.

Esta fase não cria rota de negócio, controller nem tabela. Rota nova nenhuma: os testes usam caminhos que nunca vão existir (`/nao_existe`, `/internal/nao_existe`), cuja resposta com os tokens certos é sempre o 404 `QIT000404`.

Contagem de testes da suíte: `72 passed` nos passos 4.1 e 4.2; `76 passed` de 4.3 a 4.5; `82 passed` de 4.6 até o fim.

Comandos usados nesta fase que não estão na seção 3 do `AGENTS.md`:

| Quero | Comando |
|---|---|
| Rodar uma linha de Python no `.venv` | `./.venv/Scripts/python.exe -c "<código>"` |
| Rodar uma linha de Python dentro do container da API | `docker compose exec -T api python -c "<código>"` |
| O mesmo, com uma variável de ambiente trocada só nesse comando | `docker compose exec -T -e <NOME>=<valor> api python -c "<código>"` |
| Rodar SQL no banco | `docker compose exec -T db psql -U bootcamp -d bootcamp -t -A -c "<SQL>"` |
| Requisição à mão, vendo status e cabeçalhos | `curl.exe -s -i <opções> <url>` |
| Parar e religar só o banco | `docker compose stop db` e `docker compose start db` |
| Procurar texto nos arquivos do Git | `git grep <opções> -- <pastas>` |

O `-T` desliga o terminal interativo, que o Git Bash não oferece. O `-t -A` do `psql` tira cabeçalho, rodapé e alinhamento: colunas separadas por `|`, valor nulo vazio. O `git grep` termina com código 1 quando não acha nada: nos itens em que o esperado é "nenhuma linha", esse código 1 sem linha impressa é o resultado certo.

Todas as saídas esperadas abaixo valem sem `.env` na raiz do repositório (ARQ-04). Existe um `.env`: PARE.

## Cobertura das regras desta fase (TST-02)

| Regra | O que fica vermelho se a regra deixar de valer |
|---|---|
| API-04 — `INTERNAL-TOKEN` em toda rota | `test_healthcheck.py::test_no_token` (base) e `test_admin_token.py::test_internal_path_without_admin_token` |
| PRD-07, PRD-13, API-13 — token de administração em `/internal` | `tests/integration/security/test_admin_token.py` (4 testes) |
| PRD-10 — barreira | `tests/integration/security/test_auth_barrier.py` (6 testes) |
| PRD-06, PRD-14 — uma linha por requisição, com `auth_failure` | `test_auth_barrier.py` (a barreira só conta o que o `request_log_writer` gravou) e as conferências L1 a L5 do passo 4.5 |
| PRD-04 — nada de estado na memória | `test_auth_barrier.py::test_one_failure_below_the_limit_does_not_block`: o teste anterior deixa 10 erros; se a contagem morasse na memória, o `DbUtils.rollback()` não a zeraria e o primeiro 404 viraria 429 |
| PRD-08 — timeout no banco | conferências T1 a T5 do passo 4.4 (sem teste black box: ver "Divergências", item 3) |
| PRD-12 — log sem CPF, CNPJ nem token | conferência L6 do passo 4.5 |
| PRD-02 — health check sem banco | conferência L7 do passo 4.5 |
| PRD-01, ARQ-04 — configuração no ambiente | conferências C1 e C2 do passo 4.2 |

Dos "Testes previstos" do `09 - Plano de trabalho`, caem nesta fase: "sem `INTERNAL-TOKEN` → 403" (Cliente) e "`/health_check` sem tocar no banco → 204" (Conferências à mão).

---

### Passo 4.1 — Estado da requisição
**Branch:** fase/04-esqueleto · **Depende de:** fase 3 (merge `feat(contrato): fase 03 com rotas, catálogo de erros e schemas` e commit `docs(plano): roteiros auditados`, os dois na `main`; tag `fase-03`)
**Objetivo:** criar o `RequestState` (o que cada requisição deixa para a linha de `request_log`), abri-lo no middleware `request_context` e preenchê-lo no `qi_exception_to_response` (`error_code`) e no `internal_token` (`auth_failure = "INTERNAL"`).
**Decisões:** PRD-06 — log de toda requisição · PRD-14 — colunas do log · API-04 — `INTERNAL-TOKEN` em toda rota
**Arquivos:**
- `src/utils/request_context.py` (editar): o conteúdo inteiro passa a ser:

```python
import re
import uuid
from contextvars import ContextVar
from typing import Optional


# O nome do cabeçalho que carrega o identificador da requisição.
#
# "X-Request-ID" não é invenção deste projeto: é a convenção que
# balanceadores de carga, proxies e ferramentas de log já sabem ler.
REQUEST_ID_HEADER = "X-Request-ID"

# O que aceitamos quando quem chama manda o identificador dele: letras,
# números, hífen e sublinhado, no máximo 64 caracteres. O porquê dessa
# desconfiança está em build_request_id, logo abaixo.
SAFE_REQUEST_ID = re.compile(r"[A-Za-z0-9_-]{1,64}")

# Fora de uma requisição (a API subindo), o log escreve isto no lugar do
# identificador.
NO_REQUEST_ID = "-"


# Este arquivo mora em utils/, e não em middlewares/, porque quem mais
# precisa dele é o logger: middlewares/ importa errors/, errors/ importa
# utils/logger.py, e o logger fecharia o ciclo.
#
# ContextVar, e não variável comum: ele guarda um valor separado por
# requisição em andamento. Com uma variável comum, duas requisições ao
# mesmo tempo sobrescreveriam o valor uma da outra.
_request_id: ContextVar[str] = ContextVar("request_id", default=NO_REQUEST_ID)


def get_request_id() -> str:
    """Devolve o identificador da requisição que está sendo atendida agora."""
    return _request_id.get()


def set_request_id(request_id: str) -> None:
    """Guarda o identificador desta requisição. Quem chama é o middleware."""
    _request_id.set(request_id)


def build_request_id(received_request_id: str = None) -> str:
    """Aproveita o identificador que veio de fora, ou inventa um novo.

    O valor veio de FORA e vai parar no log: quem mandasse uma quebra de
    linha escreveria uma linha de log inventada (log injection). Quem
    manda algo fora do formato ganha um identificador novo.

    `fullmatch`, e não `match`: o `match` se contenta com um começo certo
    e deixa passar o lixo que vier depois.
    """
    if received_request_id is not None and SAFE_REQUEST_ID.fullmatch(received_request_id):
        return received_request_id

    return str(uuid.uuid4())


class RequestState:
    """O que a requisição deixa para a linha de request_log (PRD-06, PRD-14).

    - `request_id`: o mesmo identificador do log da saída padrão.
    - `error_code`: o código do erro respondido; quem grava é o
      qi_exception_to_response (src/errors/handlers.py).
    - `auth_failure`: qual token falhou (INTERNAL, ADMIN ou ACCOUNT); quem
      grava são os middlewares de token e, na fase 5, a checagem de dono.
    - `account_key`: a key da conta que está no caminho; quem grava é o
      middleware request_log_writer.

    É um objeto MUTÁVEL guardado num ContextVar, pelo mesmo motivo do
    Context de src/database.py: quem roda mais para dentro muda um
    atributo, e o middleware de fora lê o mesmo objeto. Um `.set()` feito
    lá dentro seria invisível aqui fora.
    """

    def __init__(self, request_id: str) -> None:
        self.request_id = request_id
        self.error_code = None
        self.auth_failure = None
        self.account_key = None


_request_state: ContextVar[Optional[RequestState]] = ContextVar("request_state", default=None)


def start_request_state(request_id: str) -> RequestState:
    """Cria o estado desta requisição e o deixa no contexto. Quem chama é o middleware request_context."""
    request_state = RequestState(request_id)
    _request_state.set(request_state)

    return request_state


def get_request_state() -> Optional[RequestState]:
    """Devolve o estado da requisição em andamento; None fora de uma requisição."""
    return _request_state.get()
```

- `src/middlewares/request_context.py` (editar): o conteúdo inteiro passa a ser:

```python
from fastapi import FastAPI, Request

from utils.request_context import REQUEST_ID_HEADER, build_request_id, set_request_id, start_request_state


def register_request_context_middleware(application: FastAPI) -> None:
    """Dá um nome próprio a cada requisição e abre o estado dela.

    É o middleware mais de fora, e não pula rota nenhuma: não existe
    requisição que não mereça um nome.

    • O identificador vai para o ContextVar que o logger lê: toda linha de
      log da mesma requisição sai com o mesmo nome.
    • O identificador volta no cabeçalho X-Request-ID da resposta: quem
      chamou pode citá-lo ao abrir um chamado.
    • O RequestState nasce aqui. As camadas de dentro o preenchem, e o
      middleware request_log_writer o grava em request_log (PRD-06).
    """

    @application.middleware("http")
    async def create_request_context(request: Request, call_next):
        request_id = build_request_id(request.headers.get(REQUEST_ID_HEADER))
        set_request_id(request_id)
        start_request_state(request_id)

        response = await call_next(request)

        response.headers[REQUEST_ID_HEADER] = request_id

        return response
```

- `src/errors/handlers.py` (editar): o conteúdo inteiro passa a ser:

```python
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from errors.base_error import (
    QIException,
    InternalError,
    InvalidParameter,
    InvalidSchema,
    MethodNotAllowed,
    NotFoundResource,
)
from utils.logger import get_logger
from utils.request_context import get_request_state


logger = get_logger(__name__)


def qi_exception_to_response(exception: QIException) -> JSONResponse:
    """Traduz um erro nosso para a resposta JSON que o cliente recebe.

    Este é o único lugar do projeto que sabe como um erro vira HTTP. Ele
    também anota o código do erro no estado da requisição: é de lá que o
    middleware request_log_writer o grava em request_log (PRD-14).
    """
    request_state = get_request_state()
    if request_state is not None:
        request_state.error_code = exception.code

    body = {
        "title": exception.title,
        "description": exception.description,
        "translation": exception.translation,
        "code": exception.code,
    }
    return JSONResponse(status_code=exception.http_status, content=body)


def describe_validation_error(error: dict) -> str:
    location = []
    for part in error.get("loc", []):
        if part not in ("body", "query"):
            location.append(str(part))

    message = error.get("msg", "invalid value")

    if location:
        return f"{message} in {'.'.join(location)}"

    return message


def register_error_handlers(application: FastAPI) -> None:
    """Ensina a aplicação a responder cada tipo de erro."""

    @application.exception_handler(QIException)
    def handle_qi_exception(request: Request, exception: QIException) -> JSONResponse:
        return qi_exception_to_response(exception)

    @application.exception_handler(StarletteHTTPException)
    def handle_http_exception(request: Request, exception: StarletteHTTPException) -> JSONResponse:
        if exception.status_code == 404:
            return qi_exception_to_response(NotFoundResource())

        if exception.status_code == 405:
            return qi_exception_to_response(MethodNotAllowed())

        logger.error(f"HTTP {exception.status_code} em {request.url.path}: {exception.detail}")
        return qi_exception_to_response(InternalError())

    @application.exception_handler(RequestValidationError)
    def handle_validation_error(request: Request, exception: RequestValidationError) -> JSONResponse:
        errors = exception.errors()

        if errors:
            first_error = errors[0]
        else:
            first_error = {}

        description = describe_validation_error(first_error)
        origin = first_error.get("loc", [""])[0]

        # Hoje este ramo não é alcançado: corpo e query string são julgados
        # pelo JSON Schema (utils/schema_handler.py), e os parâmetros de
        # caminho são todos `str`. Ele fica para a rota que declarar um
        # parâmetro tipado.
        if origin in ("query", "path"):
            return qi_exception_to_response(InvalidParameter(description))

        return qi_exception_to_response(InvalidSchema(description))

    @application.exception_handler(Exception)
    def handle_unexpected_error(request: Request, exception: Exception) -> JSONResponse:
        logger.exception(f"Erro inesperado em {request.method} {request.url.path}")
        return qi_exception_to_response(InternalError())
```

- `src/middlewares/internal_token.py` (editar): o conteúdo inteiro passa a ser:

```python
from fastapi import FastAPI, Request

from constants import BYPASS_ENDPOINTS, INTERNAL_TOKEN
from errors.base_error import ForbiddenNotInternal
from errors.handlers import qi_exception_to_response
from models import RequestLog
from utils.request_context import get_request_state


def register_internal_token_middleware(application: FastAPI) -> None:
    """Deixa passar só quem manda o header INTERNAL-TOKEN com o valor certo (API-04).

    O valor certo vem da variável de ambiente INTERNAL_TOKEN, nunca do
    código. As rotas de BYPASS_ENDPOINTS (raiz e health check) são públicas.

    Errou o token: anota `auth_failure = INTERNAL` no estado da requisição
    (vai para request_log e alimenta a barreira da PRD-10) e responde 403
    QIT000002.

    Dentro de middleware, a resposta de erro é DEVOLVIDA, não levantada:
    quem traduz exceção são os exception handlers, que rodam mais para
    dentro. Levantar aqui viraria um 500.
    """

    @application.middleware("http")
    async def check_internal_token(request: Request, call_next):
        is_public = request.url.path in BYPASS_ENDPOINTS

        if request.method == "OPTIONS" or is_public:
            return await call_next(request)

        if request.headers.get("INTERNAL-TOKEN") != INTERNAL_TOKEN:
            request_state = get_request_state()
            if request_state is not None:
                request_state.auth_failure = RequestLog.INTERNAL
            return qi_exception_to_response(ForbiddenNotInternal())

        return await call_next(request)
```

**Passo a passo:**
1. Abra a fase (AGENTS.md, seção 7): `git status --short` → saída vazia; depois, um por vez:
   ```
   git switch main
   git switch -c fase/04-esqueleto
   ```
2. `git log --oneline` → mostra `docs(plano): roteiros auditados` e `feat(contrato): fase 03 com rotas, catálogo de erros e schemas`. `git tag --list fase-03` → `fase-03`.
3. Edite `src/utils/request_context.py` com o conteúdo do campo **Arquivos**.
4. Edite `src/middlewares/request_context.py` com o conteúdo do campo **Arquivos**.
5. Edite `src/errors/handlers.py` com o conteúdo do campo **Arquivos**.
6. Edite `src/middlewares/internal_token.py` com o conteúdo do campo **Arquivos**.
7. `docker compose up -d --build --wait` → termina sem erro.
8. Rode as conferências RS1, RS2 e RS3 do **Verificar**.
9. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `72 passed`.
10. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
11. Feche o passo (AGENTS.md, seção 7), um comando por vez:
    ```
    git add -- src/utils/request_context.py src/middlewares/request_context.py src/errors/handlers.py src/middlewares/internal_token.py
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "feat(log): estado da requisição para o registro em request_log"
    git log -1 --format=%B
    ```

**Testes:** nenhum teste novo. O passo é de camada de baixo: o `RequestState` só fica visível por HTTP quando o `request_log_writer` (4.5) o grava, e quem o prova é a barreira (4.6). Aqui, a prova são as conferências RS1 a RS3 e os 72 testes que já existiam.
**Verificar:**
- RS1 (um comando, numa linha só):
  ```
  docker compose exec -T api python -c "from utils.request_context import start_request_state, get_request_state; s = start_request_state('abc'); print(get_request_state() is s, s.request_id, s.error_code, s.auth_failure, s.account_key)"
  ```
  → `True abc None None None`
- RS2 (um comando, numa linha só):
  ```
  docker compose exec -T api python -c "from utils.request_context import start_request_state; from errors import ForbiddenNotInternal, qi_exception_to_response; s = start_request_state('abc'); r = qi_exception_to_response(ForbiddenNotInternal()); print(r.status_code, s.error_code)"
  ```
  → `403 QIT000002`
- RS3: `curl.exe -s -i http://127.0.0.1:3000/nao_existe` → a primeira linha é `HTTP/1.1 403 Forbidden`; há uma linha que começa com `x-request-id:`; o corpo contém `QIT000002`.
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `72 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/errors/handlers.py
  src/middlewares/internal_token.py
  src/middlewares/request_context.py
  src/utils/request_context.py
  ```
- `git log -1 --format=%B` → `feat(log): estado da requisição para o registro em request_log`

**Pronto quando:**
- [ ] `RequestState`, `start_request_state` e `get_request_state` existem em `src/utils/request_context.py`; `get_request_id`, `set_request_id` e `build_request_id` continuam lá, com o mesmo comportamento.
- [ ] RS1, RS2 e RS3 dão a saída esperada.
- [ ] Suíte com `72 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/04-esqueleto`.

**Commit:** `feat(log): estado da requisição para o registro em request_log`
**Pare se:**
- O item 2 não mostrar as duas mensagens ou a tag `fase-03`: a fase 03 não chegou à `main`.
- `docker compose up -d --build --wait` falhar: rode `docker compose logs --tail 100 api` e traga a saída (um `ImportError` com `circular import` no texto diz qual arquivo).
- RS1, RS2 ou RS3 derem outra saída depois de 3 tentativas de conferir os quatro arquivos contra o plano.
- A suíte não terminar com `72 passed`.

---

### Passo 4.2 — Configuração nova
**Branch:** fase/04-esqueleto · **Depende de:** 4.1
**Objetivo:** as constantes novas em `src/constants.py`, as variáveis novas no `docker-compose.yml` (com padrão) e no `.env.example` (com valor de mentirinha), e `ADMIN_TOKEN` entre as variáveis obrigatórias.
**Decisões:** PRD-01 — segredo no ambiente · PRD-07 — dois tokens internos · PRD-08 — timeout no banco · PRD-10 — barreira · PRD-13 — token de administração · API-16 — token da conta · ARQ-04 — sobe sem `.env`
**Arquivos:**
- `src/constants.py` (editar): o conteúdo inteiro passa a ser:

```python
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

# A API de boletos: o serviço de fora que este projeto chama pra emitir
# uma cobrança (veja src/connectors/). O endereço vem do ambiente, como
# tudo aqui — na sua máquina ele aponta pro mock server do sábado 4; em
# produção, apontaria pro serviço de verdade. O código não sabe a
# diferença, e esse é o ponto.
BANKSLIP_API_URL = os.environ.get("BANKSLIP_API_URL", "http://localhost:8080")
BANKSLIP_API_INTERNAL_TOKEN = os.environ.get("BANKSLIP_API_INTERNAL_TOKEN", "default_token")

# Quantos segundos esperar pelo serviço de boletos antes de desistir.
# Todo connector TEM um timeout — o porquê está em
# src/connectors/rest_connector.py.
BANKSLIP_API_TIMEOUT = int(os.environ.get("BANKSLIP_API_TIMEOUT", "5"))

# Rotas públicas: não exigem o header INTERNAL-TOKEN. São as duas que
# precisam responder pra quem ainda não tem token nenhum: a raiz, que
# diz quem é este serviço, e o health check, que o Docker consulta pra
# saber se a API já está de pé.
BYPASS_ENDPOINTS = [
    "/",
    "/health_check",
]

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
```

- `docker-compose.yml` (editar): o conteúdo inteiro passa a ser:

```yaml
# O docker compose sobe a aplicacao e o banco juntos, com um comando so:
#
#     docker compose up
#
# Os testes rodam na sua maquina, contra a API que subiu aqui:
#
#     pip install -r requirements-dev.txt
#     pytest
#
# Nao precisa criar arquivo nenhum antes: cada configuracao abaixo tem um
# valor padrao, escrito no proprio ${VARIAVEL:-padrao}. Le-se assim:
# "use o que estiver na variavel VARIAVEL; se ela nao existir, use padrao".
#
# O .env continua valendo, e agora e OPCIONAL: se voce criar um (copiando
# o .env.example), o compose le esse arquivo e o que estiver la ganha do
# padrao. E o jeito de trocar uma porta ocupada ou o token, sem editar
# este arquivo.

services:
  api:
    build:
      context: .
      target: api
    ports:
      # Se a porta 3000 ja estiver ocupada na sua maquina, coloque
      # API_PORT=3001 (ou outra livre) no seu .env.
      - "${API_PORT:-3000}:3000"
    environment:
      # Dentro do compose, o banco atende pelo nome "db" — nao por localhost.
      # Por isso esta linha nao tem padrao pra sobrescrever: aqui dentro o
      # endereco do banco e sempre este.
      DATABASE_URL: postgresql+psycopg2://bootcamp:bootcamp@db:5432/bootcamp
      APP_ENV: ${APP_ENV:-local}
      SERVICE_NAME: ${SERVICE_NAME:-bootcamp-api}
      # A senha que protege os endpoints internos. O padrao vale pra
      # estudar; num sistema de verdade, isso nunca teria valor padrao.
      INTERNAL_TOKEN: ${INTERNAL_TOKEN:-default_token}
      # O segundo token das rotas /internal (PRD-13). Mesmo aviso do de
      # cima sobre o valor padrao.
      ADMIN_TOKEN: ${ADMIN_TOKEN:-default_admin_token}
      # Barreira contra chute de token (PRD-10): quantos erros de token do
      # mesmo IP, dentro de quantos minutos, antes do 429.
      AUTH_FAILURE_LIMIT: ${AUTH_FAILURE_LIMIT:-10}
      AUTH_FAILURE_WINDOW_MINUTES: ${AUTH_FAILURE_WINDOW_MINUTES:-15}
      # Timeout do banco (PRD-08), em milissegundos: esperando trava e
      # rodando um comando. Passou, a API responde 503.
      DB_LOCK_TIMEOUT_MS: ${DB_LOCK_TIMEOUT_MS:-5000}
      DB_STATEMENT_TIMEOUT_MS: ${DB_STATEMENT_TIMEOUT_MS:-5000}
      # A API de boletos (assunto do sabado 4). Variavel que nao esta
      # nesta lista NAO CHEGA no container: o compose repassa o que
      # esta escrito aqui, e mais nada. Sem estas tres linhas, mexer
      # nos BANKSLIP_* do .env nao teria efeito nenhum aqui dentro.
      BANKSLIP_API_URL: ${BANKSLIP_API_URL:-http://localhost:8080}
      BANKSLIP_API_INTERNAL_TOKEN: ${BANKSLIP_API_INTERNAL_TOKEN:-default_token}
      BANKSLIP_API_TIMEOUT: ${BANKSLIP_API_TIMEOUT:-5}
    volumes:
      # Monta o codigo pra dentro do container: salvou o arquivo,
      # a API recarrega sozinha (o --reload ali embaixo).
      - ./src:/app
    # --reload: salvou o arquivo, a API reinicia sozinha.
    command: uvicorn app:app --host 0.0.0.0 --port 3000 --no-server-header --reload
    healthcheck:
      # "Subiu" nao e a mesma coisa que "ja responde". E esta checagem
      # que diz quando a API passa a atender de verdade — espere ela
      # ficar (healthy) antes de rodar o pytest, ou o primeiro teste
      # bate numa porta que ainda nao responde.
      test: ["CMD-SHELL", "python -c 'import urllib.request; urllib.request.urlopen(\"http://localhost:3000/health_check\")'"]
      interval: 3s
      timeout: 5s
      retries: 20
      start_period: 5s
    depends_on:
      db:
        condition: service_healthy

  db:
    build: ./database/.
    environment:
      POSTGRES_USER: bootcamp
      POSTGRES_PASSWORD: bootcamp
      POSTGRES_DB: bootcamp
    ports:
      # Mesma ideia: DB_PORT=5433 no .env se a 5432 estiver ocupada.
      - "${DB_PORT:-5432}:5432"
    healthcheck:
      # A API so sobe depois que o banco responder de verdade.
      test: ["CMD-SHELL", "pg_isready -U bootcamp -d bootcamp"]
      interval: 3s
      timeout: 3s
      retries: 20
```

- `.env.example` (editar): o conteúdo inteiro passa a ser:

```bash
# ─────────────────────────────────────────────────────────────
# Exemplo de configuração — Bootcamp QI Tech
#
# VOCÊ NÃO PRECISA DISTO PRA COMEÇAR. O "docker compose up" sobe
# com todos os valores abaixo já preenchidos, sem criar arquivo
# nenhum.
#
# Este arquivo serve pra quando você quiser TROCAR alguma coisa —
# uma porta ocupada, o token, o banco. Aí sim:
#   cp .env.example .env
# e edite o .env. O que estiver nele ganha do valor padrão.
#
# O arquivo .env é SEU, fica só na sua máquina e nunca vai pro Git
# (olha lá no .gitignore). Este .env.example, sim, vai pro Git —
# por isso ele só tem valor de mentirinha, nunca senha de verdade.
#
# Essa é a regra nº 1 de configuração: senha não mora no código.
# Ela mora no ambiente, e o código só pergunta "qual é?".
# ─────────────────────────────────────────────────────────────

# Em qual ambiente a aplicação acha que está rodando.
# Vale "local", "test" ou "production" — muda o NÍVEL do log: em
# "local" e "test" as linhas de DEBUG aparecem; em "production", só
# de INFO pra cima. O formato da linha é o mesmo nos três.
APP_ENV=local

# Nome do serviço. Aparece no log e na rota raiz da API.
SERVICE_NAME=bootcamp-api

# Endereço completo do banco, no formato:
#   postgresql+psycopg2://USUARIO:SENHA@HOST:PORTA/NOME_DO_BANCO
#
# Rodando com "docker compose up", o compose troca o HOST por "db"
# automaticamente (é o nome do serviço do Postgres) — ou seja, esta
# linha aqui NÃO vale lá dentro.
# Ela vale pra quem roda alguma coisa direto na própria máquina.
DATABASE_URL=postgresql+psycopg2://bootcamp:bootcamp@localhost:5432/bootcamp

# Senha simples que protege os endpoints internos da API.
# Quem chama precisa mandar o header:  INTERNAL-TOKEN: default_token
INTERNAL_TOKEN=default_token

# Senha das rotas /internal (virada do dia, bloquear e desbloquear
# conta). Elas pedem o INTERNAL-TOKEN e mais o header:
#   ADMIN-TOKEN: default_admin_token
ADMIN_TOKEN=default_admin_token

# Barreira contra chute de token: quantos erros de INTERNAL-TOKEN ou
# ADMIN-TOKEN do mesmo IP, dentro de quantos minutos, fazem a API
# responder 429 a toda requisição desse IP.
AUTH_FAILURE_LIMIT=10
AUTH_FAILURE_WINDOW_MINUTES=15

# Timeout do banco, em milissegundos: quanto esperar por uma trava
# (lock_timeout) e por um comando (statement_timeout). Passou, a API
# desfaz a transação e responde 503.
DB_LOCK_TIMEOUT_MS=5000
DB_STATEMENT_TIMEOUT_MS=5000

# Onde os testes procuram a API, quando rodados fora do Docker.
SERVER_LOCALHOST=127.0.0.1

# ─────────────────────────────────────────────────────────────
# A API de boletos (o connector)
#
# É o serviço de FORA que este projeto chama pra emitir cobrança —
# veja src/connectors/. Não existe uma API de boletos rodando na sua
# máquina, e tudo bem: quem faz o papel dela é um mock server (assunto
# do sábado 4). Estes valores dizem ao connector onde ela "está".
# ─────────────────────────────────────────────────────────────

# Onde a API de boletos atende. Troque pra apontar pro seu mock.
#
# ATENÇÃO: "localhost" aqui é o localhost DE DENTRO do container da
# API, que não é o da sua máquina. Se o seu mock roda na sua máquina,
# o endereço que o container enxerga é http://host.docker.internal:8080
# (no Linux, o IP do gateway do compose).
BANKSLIP_API_URL=http://localhost:8080

# O token que ELA exige — mesma ideia do INTERNAL_TOKEN lá em cima,
# só que na outra direção: lá conferimos quem nos chama, aqui nos
# apresentamos pra quem chamamos.
BANKSLIP_API_INTERNAL_TOKEN=default_token

# Quantos segundos esperar por ela antes de desistir.
BANKSLIP_API_TIMEOUT=5

# ─────────────────────────────────────────────────────────────
# Portas — mexa aqui se alguma já estiver ocupada na sua máquina
#
# "port is already allocated" na hora do "docker compose up" quer
# dizer que outro programa já está usando aquela porta. Não precisa
# descobrir qual: escolha outra e siga a vida.
#
# Tire o "#" da frente e troque o número:
# ─────────────────────────────────────────────────────────────

# Em qual porta da SUA máquina a API vai atender (http://localhost:3000).
#API_PORT=3001

# Em qual porta da SUA máquina o banco vai atender.
# Se mudar aqui, mude também a porta lá na DATABASE_URL acima —
# senão o acesso direto ao banco procura no lugar errado.
#DB_PORT=5433
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/04-esqueleto`; `git log --oneline` mostra `feat(log): estado da requisição para o registro em request_log`.
2. Edite `src/constants.py` com o conteúdo do campo **Arquivos**.
3. Edite `docker-compose.yml` com o conteúdo do campo **Arquivos**.
4. Edite `.env.example` com o conteúdo do campo **Arquivos**.
5. `docker compose up -d --build --wait` → termina sem erro (o compose recria o container da API, porque o `environment` mudou).
6. Rode as conferências C1 e C2 do **Verificar**.
7. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `72 passed`.
8. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
9. Feche o passo (AGENTS.md, seção 7), um comando por vez:
   ```
   git add -- src/constants.py docker-compose.yml .env.example
   git diff --cached --name-only
   git diff --name-only
   git ls-files --others --exclude-standard
   git commit -m "chore(config): token de administração, barreira e timeout do banco no ambiente"
   git log -1 --format=%B
   ```

**Testes:** nenhum teste novo. Configuração não tem regra própria: quem a usa são os passos 4.3 (token de administração), 4.4 (timeout) e 4.6 (barreira), e os testes deles quebram se o valor não chegar. Aqui, a prova são C1 (o valor chega ao container) e C2 (sem `ADMIN_TOKEN`, a API não sobe).
**Verificar:**
- C1 (um comando, numa linha só):
  ```
  docker compose exec -T api python -c "import constants as c; print(c.ADMIN_TOKEN, c.AUTH_FAILURE_LIMIT, c.AUTH_FAILURE_WINDOW_MINUTES, c.DB_LOCK_TIMEOUT_MS, c.DB_STATEMENT_TIMEOUT_MS, c.INTERNAL_TOKEN_HEADER, c.ACCOUNT_TOKEN_HEADER, c.ADMIN_TOKEN_HEADER, c.INTERNAL_PREFIX, c.REQUIRED_VARIABLES)"
  ```
  → `default_admin_token 10 15 5000 5000 INTERNAL-TOKEN ACCOUNT-TOKEN ADMIN-TOKEN /internal ['DATABASE_URL', 'INTERNAL_TOKEN', 'ADMIN_TOKEN']`
- C2 (um comando, numa linha só; o código de saída 1 é o esperado):
  ```
  docker compose exec -T -e ADMIN_TOKEN= api python -c "import constants; constants.check_variables()"
  ```
  → a última linha começa com `OSError: Faltam variáveis de ambiente: ADMIN_TOKEN.`
- `git grep -n -e "default_admin_token" -- src` → nenhuma linha (o padrão mora no compose, nunca no código).
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `72 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  .env.example
  docker-compose.yml
  src/constants.py
  ```
- `git log -1 --format=%B` → `chore(config): token de administração, barreira e timeout do banco no ambiente`

**Pronto quando:**
- [ ] As 9 constantes novas existem em `src/constants.py`; `ADMIN_TOKEN` está em `REQUIRED_VARIABLES`.
- [ ] O compose passa as 5 variáveis novas à API, cada uma com padrão; o `.env.example` tem as 5, com valor de mentirinha.
- [ ] C1 e C2 dão a saída esperada.
- [ ] Suíte com `72 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/04-esqueleto`.

**Commit:** `chore(config): token de administração, barreira e timeout do banco no ambiente`
**Pare se:**
- `docker compose up -d --build --wait` falhar: rode `docker compose logs --tail 100 api` e traga a saída.
- C1 der outro valor: o container não recebeu a variável (confira se existe `.env` na raiz).
- C2 não terminar com a linha `OSError: Faltam variáveis de ambiente: ADMIN_TOKEN.`
- A suíte não terminar com `72 passed`.

---

### Passo 4.3 — Token de administração
**Branch:** fase/04-esqueleto · **Depende de:** 4.2
**Objetivo:** `register_admin_token_middleware`: caminho `/internal` ou abaixo de `/internal/` sem o `ADMIN-TOKEN` certo responde 403 `QIT000003` e grava `auth_failure = "ADMIN"`.
**Decisões:** PRD-07 — dois tokens internos · PRD-13 — token de administração · API-13 — rotas `/internal` · API-04 — `INTERNAL-TOKEN` em toda rota · TST-01 — black box e TDD · TST-02 — o que barra tem teste
**Arquivos:**
- `src/middlewares/admin_token.py` (criar): o conteúdo inteiro é:

```python
from fastapi import FastAPI, Request

from constants import ADMIN_TOKEN, ADMIN_TOKEN_HEADER, INTERNAL_PREFIX
from errors.base_error import ForbiddenNotAdmin
from errors.handlers import qi_exception_to_response
from models import RequestLog
from utils.request_context import get_request_state


def is_internal_path(path: str) -> bool:
    """True para /internal e para tudo abaixo de /internal/; /internalx não conta."""
    return path == INTERNAL_PREFIX or path.startswith(INTERNAL_PREFIX + "/")


def register_admin_token_middleware(application: FastAPI) -> None:
    """O segundo cadeado das rotas /internal (PRD-07, PRD-13, API-13).

    Roda por dentro do internal_token: quem chega aqui já mandou o
    INTERNAL-TOKEN certo. Nos caminhos /internal, falta ou erro do
    ADMIN-TOKEN anota `auth_failure = ADMIN` no estado da requisição (vai
    para request_log e alimenta a barreira da PRD-10) e responde 403
    QIT000003. Os outros caminhos passam direto.
    """

    @application.middleware("http")
    async def check_admin_token(request: Request, call_next):
        if request.method == "OPTIONS" or not is_internal_path(request.url.path):
            return await call_next(request)

        if request.headers.get(ADMIN_TOKEN_HEADER) != ADMIN_TOKEN:
            request_state = get_request_state()
            if request_state is not None:
                request_state.auth_failure = RequestLog.ADMIN
            return qi_exception_to_response(ForbiddenNotAdmin())

        return await call_next(request)
```

- `src/middlewares/__init__.py` (editar): o conteúdo inteiro passa a ser:

```python
from middlewares.admin_token import register_admin_token_middleware
from middlewares.internal_token import register_internal_token_middleware
from middlewares.request_context import register_request_context_middleware
from middlewares.request_logger import register_request_logger_middleware
from middlewares.session_manager import register_session_manager_middleware
```

- `src/app.py` (editar): o conteúdo inteiro passa a ser:

```python
from fastapi import FastAPI

from constants import check_variables
from errors import register_error_handlers
from errors.base_error import error_verification
from middlewares import (
    register_admin_token_middleware,
    register_internal_token_middleware,
    register_request_context_middleware,
    register_request_logger_middleware,
    register_session_manager_middleware,
)
from resources import HealthCheckResource
from utils.logger import setup_logging


def create_app() -> FastAPI:
    """Monta a aplicação: os middlewares, as rotas e os error handlers."""
    # Os três None desligam a documentação automática (ARQ-09).
    application = FastAPI(
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )

    # ────────────────────────────────────────────────────────────────
    # Os middlewares. O ÚLTIMO registrado é o PRIMEIRO a rodar: leia as
    # linhas de baixo para cima e a requisição atravessa assim, de fora
    # para dentro:
    #
    #     request_context   nome da requisição e RequestState
    #     request_logger    ENTROU / SAIU na saída padrão
    #     internal_token    403 sem o INTERNAL-TOKEN certo (API-04)
    #     admin_token       403 em /internal sem o ADMIN-TOKEN (PRD-13)
    #     session_manager   sessão de banco; o mais interno de todos
    #
    # A ordem inteira, com os porquês: docs/plano/PLANO-00-indice.md,
    # seção "Middlewares".
    # ────────────────────────────────────────────────────────────────
    register_session_manager_middleware(application)
    register_admin_token_middleware(application)
    register_internal_token_middleware(application)
    register_request_logger_middleware(application)
    register_request_context_middleware(application)

    # ────────────────────────────────────────────────────────────────
    # As rotas: uma linha por endereço e verbo. O status de sucesso sai
    # de dentro do resource (API-02).
    # ────────────────────────────────────────────────────────────────
    health_check_resource = HealthCheckResource()

    application.add_api_route("/", health_check_resource.on_get_home, methods=["GET"])
    application.add_api_route(
        "/health_check",
        health_check_resource.on_get_health_check,
        methods=["GET"]
    )

    register_error_handlers(application)

    return application


def main() -> FastAPI:
    # Não deixa a API subir com configuração faltando: é melhor falhar
    # agora, na hora de ligar, do que na cara do cliente mais tarde.
    check_variables()
    error_verification()
    setup_logging()

    return create_app()


app = main()
```

- `tests/integration/security/test_admin_token.py` (criar): o conteúdo inteiro é:

```python
"""Token de administração nas rotas /internal (PRD-07, PRD-13, API-13).

Todo teste daqui erra um token de propósito e por isso começa com
DbUtils.rollback(): a barreira contra chute de token (PRD-10) conta os
erros de token do IP em request_log.
"""

from os import environ

from tests.utils import INTERNAL_TOKEN, DbUtils
from tests.utils.requisition import ClientRequisition


ADMIN_TOKEN = environ.get("ADMIN_TOKEN", "default_admin_token")

# Caminho sob /internal que nunca vira rota: com os dois tokens certos, a
# resposta é o 404 do caminho que não existe.
INTERNAL_PATH = "/internal/nao_existe"

FORBIDDEN_ADMIN_TRANSLATION = "Requisição precisa do token de administração"


class TestAdminToken:
    def test_internal_path_without_admin_token(self):
        DbUtils.rollback()

        response = ClientRequisition.send("POST", INTERNAL_PATH)
        assert response.response_status == 403
        assert response.response_json["code"] == "QIT000002"

        response = ClientRequisition.send("POST", INTERNAL_PATH, headers={"ADMIN-TOKEN": ADMIN_TOKEN})
        assert response.response_status == 403
        assert response.response_json["code"] == "QIT000002"

        response = ClientRequisition.send("POST", INTERNAL_PATH, headers={"INTERNAL-TOKEN": INTERNAL_TOKEN})
        assert response.response_status == 403
        assert response.response_json["code"] == "QIT000003"
        assert response.response_json["translation"] == FORBIDDEN_ADMIN_TRANSLATION

    def test_internal_path_with_wrong_admin_token(self):
        DbUtils.rollback()

        response = ClientRequisition.send(
            "POST",
            INTERNAL_PATH,
            headers={"INTERNAL-TOKEN": INTERNAL_TOKEN, "ADMIN-TOKEN": "token_errado"},
        )
        assert response.response_status == 403
        assert response.response_json["code"] == "QIT000003"

        response = ClientRequisition.send(
            "POST",
            INTERNAL_PATH,
            headers={"INTERNAL-TOKEN": INTERNAL_TOKEN, "ADMIN-TOKEN": INTERNAL_TOKEN},
        )
        assert response.response_status == 403
        assert response.response_json["code"] == "QIT000003"

    def test_internal_path_with_both_tokens(self):
        DbUtils.rollback()

        response = ClientRequisition.send("POST", INTERNAL_PATH, headers={"INTERNAL-TOKEN": INTERNAL_TOKEN})
        assert response.response_status == 403
        assert response.response_json["code"] == "QIT000003"

        response = ClientRequisition.send(
            "POST",
            INTERNAL_PATH,
            headers={"INTERNAL-TOKEN": INTERNAL_TOKEN, "ADMIN-TOKEN": ADMIN_TOKEN},
        )
        assert response.response_status == 404
        assert response.response_json["code"] == "QIT000404"

    def test_admin_token_only_under_internal_prefix(self):
        DbUtils.rollback()

        for path in ["/internal", "/internal/"]:
            response = ClientRequisition.send("GET", path, headers={"INTERNAL-TOKEN": INTERNAL_TOKEN})
            assert response.response_status == 403
            assert response.response_json["code"] == "QIT000003"

        for path in ["/internalx", "/nao_existe/internal"]:
            response = ClientRequisition.send("GET", path, headers={"INTERNAL-TOKEN": INTERNAL_TOKEN})
            assert response.response_status == 404
            assert response.response_json["code"] == "QIT000404"
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/04-esqueleto`; `git log --oneline` mostra `chore(config): token de administração, barreira e timeout do banco no ambiente`.
2. Crie `tests/integration/security/test_admin_token.py` com o conteúdo do campo **Arquivos** (a pasta `tests/integration/security/` é nova e fica sem `__init__.py`, como `tests/integration/`).
3. `docker compose up -d --build --wait`.
4. `./.venv/Scripts/python.exe -m pytest -v tests/integration/security/test_admin_token.py` → a última linha tem `4 failed` e não tem `passed`. Os 4 falham por asserção de status: hoje `/internal/nao_existe` com só o `INTERNAL-TOKEN` responde 404.
5. Crie `src/middlewares/admin_token.py` com o conteúdo do campo **Arquivos**.
6. Edite `src/middlewares/__init__.py` com o conteúdo do campo **Arquivos**.
7. Edite `src/app.py` com o conteúdo do campo **Arquivos**.
8. `docker compose up -d --build --wait`.
9. `./.venv/Scripts/python.exe -m pytest -v tests/integration/security/test_admin_token.py` → a última linha tem `4 passed`.
10. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `76 passed`.
11. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
12. Feche o passo (AGENTS.md, seção 7), um comando por vez:
    ```
    git add -- src/middlewares/admin_token.py src/middlewares/__init__.py src/app.py tests/integration/security/test_admin_token.py
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "feat(seguranca): token de administração nas rotas /internal"
    git log -1 --format=%B
    ```

**Testes:** `tests/integration/security/test_admin_token.py`. Nenhum teste toca no banco além do `DbUtils.rollback()` da primeira linha.

| Função de teste | Entrada | Esperado |
|---|---|---|
| `test_internal_path_without_admin_token` | `POST /internal/nao_existe` (a) sem cabeçalho; (b) só `ADMIN-TOKEN` certo; (c) só `INTERNAL-TOKEN` certo | (a) 403 `QIT000002`; (b) 403 `QIT000002` (o `INTERNAL-TOKEN` é conferido antes); (c) 403 `QIT000003`, `translation` = `Requisição precisa do token de administração`. Banco: só linhas de `request_log` (a partir do 4.5) |
| `test_internal_path_with_wrong_admin_token` | `POST /internal/nao_existe` com `INTERNAL-TOKEN` certo e (a) `ADMIN-TOKEN: token_errado`; (b) `ADMIN-TOKEN` igual ao `INTERNAL-TOKEN` | (a) e (b): 403 `QIT000003` (os dois tokens são diferentes, PRD-07) |
| `test_internal_path_with_both_tokens` | `POST /internal/nao_existe` (a) só `INTERNAL-TOKEN`; (b) os dois certos | (a) 403 `QIT000003`; (b) 404 `QIT000404`: o middleware deixou passar, e o caminho não existe |
| `test_admin_token_only_under_internal_prefix` | `GET` com só o `INTERNAL-TOKEN` em `/internal`, `/internal/`, `/internalx`, `/nao_existe/internal` | os dois primeiros: 403 `QIT000003`; os dois últimos: 404 `QIT000404` (não são caminhos `/internal`) |

**Verificar:**
- `./.venv/Scripts/python.exe -m pytest -v tests/integration/security/test_admin_token.py` → `4 passed`.
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `76 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/app.py
  src/middlewares/__init__.py
  src/middlewares/admin_token.py
  tests/integration/security/test_admin_token.py
  ```
- `git log -1 --format=%B` → `feat(seguranca): token de administração nas rotas /internal`

**Pronto quando:**
- [ ] Os 4 testes falharam antes do código (item 4) e passam depois (item 9).
- [ ] No `src/app.py`, `register_admin_token_middleware` está registrado entre `register_session_manager_middleware` e `register_internal_token_middleware`.
- [ ] Suíte com `76 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/04-esqueleto`.

**Commit:** `feat(seguranca): token de administração nas rotas /internal`
**Pare se:**
- O item 4 não terminar com `4 failed` (um teste passou antes do código, ou falhou com `SyntaxError`, `NameError` ou `IndentationError` depois de 3 tentativas de conferir o arquivo contra o plano).
- O item 9 der `QIT000002` onde o esperado é `QIT000003`: a ordem dos registros no `src/app.py` não é a do plano.
- A suíte não terminar com `76 passed`.

---

### Passo 4.4 — Timeout no banco
**Branch:** fase/04-esqueleto · **Depende de:** 4.3
**Objetivo:** toda conexão nasce com `lock_timeout = DB_LOCK_TIMEOUT_MS` e `statement_timeout = DB_STATEMENT_TIMEOUT_MS`; o `OperationalError` de timeout que sai de uma rota responde 503 `QIT000503`.
**Decisões:** PRD-08 — timeout no banco · R3 — código de erro próprio · API-11 — status de erro
**Arquivos:**
- `src/database.py` (editar): duas trocas, e nada mais. A docstring e os outros comentários ficam como estão.
  1. Troque a linha
     ```python
     from constants import DATABASE_URL
     ```
     por
     ```python
     from constants import DATABASE_URL, DB_LOCK_TIMEOUT_MS, DB_STATEMENT_TIMEOUT_MS
     ```
  2. Troque a linha
     ```python
     engine = create_engine(DATABASE_URL, pool_size=5, pool_recycle=600, pool_pre_ping=True)
     ```
     por estas linhas (o nome `DB_TIMEOUT_OPTIONS` é novo):
     ```python
     # PRD-08: toda conexão nasce com lock_timeout e statement_timeout, em
     # milissegundos. Passou do tempo, o PostgreSQL desiste do comando, a
     # transação é desfeita e a API responde 503 QIT000503
     # (src/errors/handlers.py).
     DB_TIMEOUT_OPTIONS = f"-c lock_timeout={DB_LOCK_TIMEOUT_MS} -c statement_timeout={DB_STATEMENT_TIMEOUT_MS}"

     engine = create_engine(
         DATABASE_URL,
         pool_size=5,
         pool_recycle=600,
         pool_pre_ping=True,
         connect_args={"options": DB_TIMEOUT_OPTIONS},
         hide_parameters=True,
     )
     ```
- `src/errors/handlers.py` (editar): o conteúdo inteiro passa a ser:

```python
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from psycopg2 import errors as psycopg2_errors
from sqlalchemy.exc import OperationalError
from starlette.exceptions import HTTPException as StarletteHTTPException

from errors.base_error import (
    QIException,
    DatabaseTimeout,
    InternalError,
    InvalidParameter,
    InvalidSchema,
    MethodNotAllowed,
    NotFoundResource,
)
from utils.logger import get_logger
from utils.request_context import get_request_state


logger = get_logger(__name__)


def qi_exception_to_response(exception: QIException) -> JSONResponse:
    """Traduz um erro nosso para a resposta JSON que o cliente recebe.

    Este é o único lugar do projeto que sabe como um erro vira HTTP. Ele
    também anota o código do erro no estado da requisição: é de lá que o
    middleware request_log_writer o grava em request_log (PRD-14).
    """
    request_state = get_request_state()
    if request_state is not None:
        request_state.error_code = exception.code

    body = {
        "title": exception.title,
        "description": exception.description,
        "translation": exception.translation,
        "code": exception.code,
    }
    return JSONResponse(status_code=exception.http_status, content=body)


def is_database_timeout(exception: Exception) -> bool:
    """True quando o PostgreSQL desistiu por tempo (PRD-08).

    `LockNotAvailable` (SQLSTATE 55P03): passou do lock_timeout esperando
    uma trava. `QueryCanceled` (SQLSTATE 57014): passou do
    statement_timeout rodando o comando. O SQLAlchemy embrulha o erro do
    psycopg2 num OperationalError e guarda o original em `.orig`.
    """
    original = getattr(exception, "orig", None)
    return isinstance(original, (psycopg2_errors.LockNotAvailable, psycopg2_errors.QueryCanceled))


def describe_validation_error(error: dict) -> str:
    location = []
    for part in error.get("loc", []):
        if part not in ("body", "query"):
            location.append(str(part))

    message = error.get("msg", "invalid value")

    if location:
        return f"{message} in {'.'.join(location)}"

    return message


def register_error_handlers(application: FastAPI) -> None:
    """Ensina a aplicação a responder cada tipo de erro."""

    @application.exception_handler(QIException)
    def handle_qi_exception(request: Request, exception: QIException) -> JSONResponse:
        return qi_exception_to_response(exception)

    @application.exception_handler(StarletteHTTPException)
    def handle_http_exception(request: Request, exception: StarletteHTTPException) -> JSONResponse:
        if exception.status_code == 404:
            return qi_exception_to_response(NotFoundResource())

        if exception.status_code == 405:
            return qi_exception_to_response(MethodNotAllowed())

        logger.error(f"HTTP {exception.status_code} em {request.url.path}: {exception.detail}")
        return qi_exception_to_response(InternalError())

    @application.exception_handler(RequestValidationError)
    def handle_validation_error(request: Request, exception: RequestValidationError) -> JSONResponse:
        errors = exception.errors()

        if errors:
            first_error = errors[0]
        else:
            first_error = {}

        description = describe_validation_error(first_error)
        origin = first_error.get("loc", [""])[0]

        # Hoje este ramo não é alcançado: corpo e query string são julgados
        # pelo JSON Schema (utils/schema_handler.py), e os parâmetros de
        # caminho são todos `str`. Ele fica para a rota que declarar um
        # parâmetro tipado.
        if origin in ("query", "path"):
            return qi_exception_to_response(InvalidParameter(description))

        return qi_exception_to_response(InvalidSchema(description))

    @application.exception_handler(OperationalError)
    def handle_operational_error(request: Request, exception: OperationalError) -> JSONResponse:
        # A sessão da rota fica com a transação abortada; o session_manager
        # a fecha, e fechar desfaz tudo: nada é gravado (PRD-08).
        if is_database_timeout(exception):
            logger.warning(f"Timeout do banco em {request.method} {request.url.path}")
            return qi_exception_to_response(DatabaseTimeout())

        logger.exception(f"Erro do banco em {request.method} {request.url.path}")
        return qi_exception_to_response(InternalError())

    @application.exception_handler(Exception)
    def handle_unexpected_error(request: Request, exception: Exception) -> JSONResponse:
        logger.exception(f"Erro inesperado em {request.method} {request.url.path}")
        return qi_exception_to_response(InternalError())
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/04-esqueleto`; `git log --oneline` mostra `feat(seguranca): token de administração nas rotas /internal`.
2. Faça as duas trocas em `src/database.py`.
3. Edite `src/errors/handlers.py` com o conteúdo do campo **Arquivos**.
4. `docker compose up -d --build --wait` → termina sem erro.
5. Rode as conferências T1 a T5 do **Verificar**, na ordem. T2 leva uns 5 segundos.
6. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `76 passed`.
7. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
8. Feche o passo (AGENTS.md, seção 7), um comando por vez:
   ```
   git add -- src/database.py src/errors/handlers.py
   git diff --cached --name-only
   git diff --name-only
   git ls-files --others --exclude-standard
   git commit -m "feat(banco): lock_timeout e statement_timeout com resposta 503"
   git log -1 --format=%B
   ```

**Testes:** nenhum teste novo. Um teste black box do 503 precisaria de uma rota segurando uma trava por mais de 5 segundos, e nenhuma rota faz isso; o teste de integração só toca no banco pelo `DbUtils.rollback()` (TST-01). A prova é feita dentro do container: T1 (a conexão nasce com os dois tempos), T2 (`statement_timeout` de verdade), T3 (`lock_timeout` de verdade, com duas conexões disputando a linha do `bank_clock`), T4 (o que não é timeout continua não sendo) e T5 (o handler está registrado).
**Verificar:**
- T1 (um comando, numa linha só):
  ```
  docker compose exec -T api python -c "from sqlalchemy import text; from database import engine; c = engine.connect(); print(c.execute(text('SHOW lock_timeout')).scalar(), c.execute(text('SHOW statement_timeout')).scalar()); c.close()"
  ```
  → `5s 5s`
- T2 (um comando, numa linha só; leva uns 5 segundos):
  ```
  docker compose exec -T api python -c "from concurrent.futures import ThreadPoolExecutor; from sqlalchemy import text; from database import engine; from errors.handlers import is_database_timeout; c = engine.connect(); e = ThreadPoolExecutor().submit(c.execute, text('SELECT pg_sleep(6)')).exception(); print(type(e).__name__, type(e.orig).__name__, is_database_timeout(e))"
  ```
  → `OperationalError QueryCanceled True`
- T3 (um comando, numa linha só; o `-e` baixa o `lock_timeout` para 1 segundo só neste comando, para que ele vença o `statement_timeout`):
  ```
  docker compose exec -T -e DB_LOCK_TIMEOUT_MS=1000 api python -c "from concurrent.futures import ThreadPoolExecutor; from sqlalchemy import text; from database import engine; from errors.handlers import is_database_timeout; c1 = engine.connect(); c1.execute(text('SELECT id FROM bank_clock FOR UPDATE')); c2 = engine.connect(); e = ThreadPoolExecutor().submit(c2.execute, text('SELECT id FROM bank_clock FOR UPDATE')).exception(); print(type(e).__name__, type(e.orig).__name__, is_database_timeout(e))"
  ```
  → `OperationalError LockNotAvailable True`
- T4 (um comando, numa linha só):
  ```
  docker compose exec -T api python -c "from sqlalchemy.exc import OperationalError; from errors.handlers import is_database_timeout; print(is_database_timeout(OperationalError('SELECT 1', {}, Exception('x'))), is_database_timeout(ValueError('x')))"
  ```
  → `False False`
- T5 (um comando, numa linha só):
  ```
  docker compose exec -T api python -c "from sqlalchemy.exc import OperationalError; from app import app; print(OperationalError in app.exception_handlers)"
  ```
  → a última linha é `True`.
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `76 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/database.py
  src/errors/handlers.py
  ```
- `git log -1 --format=%B` → `feat(banco): lock_timeout e statement_timeout com resposta 503`

**Pronto quando:**
- [ ] T1 a T5 dão a saída esperada.
- [ ] `is_database_timeout` existe em `src/errors/handlers.py` e o handler de `OperationalError` responde `DatabaseTimeout` (503 `QIT000503`) no timeout e `InternalError` no resto.
- [ ] Suíte com `76 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/04-esqueleto`.

**Commit:** `feat(banco): lock_timeout e statement_timeout com resposta 503`
**Pare se:**
- Alguma linha citada nas trocas de `src/database.py` não for encontrada igual.
- T1 mostrar `0` em algum dos dois valores: o `connect_args` não chegou à conexão.
- T2 ou T3 terminarem com `AttributeError: 'NoneType' object has no attribute 'orig'`: o comando terminou sem timeout.
- T2, T3, T4 ou T5 derem outra saída depois de 3 tentativas de conferir os dois arquivos contra o plano.
- A suíte não terminar com `76 passed`.

---

### Passo 4.5 — Registro de toda requisição
**Branch:** fase/04-esqueleto · **Depende de:** 4.4
**Objetivo:** `RequestLogRepository` (`create`, `count_auth_failures`) com sessão própria e `register_request_log_writer_middleware`, que grava uma linha em `request_log` por requisição, fora da transação da regra, menos as de `BYPASS_ENDPOINTS`; o `account_key` sai do caminho.
**Decisões:** PRD-06 — log de toda requisição · PRD-14 — colunas do log · PRD-12 — log sem CPF, CNPJ nem token · PRD-02 — health check sem banco · DAD-13 — pedido barrado só deixa o log · R5 — o `id` interno nunca sai
**Arquivos:**
- `src/repositories/request_log_repository.py` (criar): o conteúdo inteiro é:

```python
from datetime import timedelta
from uuid import uuid4

from sqlalchemy import func

from database import SessionLocal
from models import RequestLog


class RequestLogRepository:
    """Grava e conta as linhas de request_log (PRD-06, PRD-14), com sessão própria.

    É o único repository que não recebe o contexto da requisição: cada
    método abre uma sessão, faz o trabalho e fecha. Assim a linha do log
    fica fora da transação da regra, e o pedido barrado, cuja transação é
    desfeita, deixa a linha dele gravada (DAD-13). Quem chama são os
    middlewares request_log_writer e auth_barrier, nunca um controller.
    """

    def create(
        self,
        request_id: str,
        method: str,
        path: str,
        status: int,
        error_code: str,
        client_ip: str,
        account_key: str,
        auth_failure: str,
    ) -> None:
        request_log = RequestLog()
        request_log.request_log_key = str(uuid4())
        request_log.request_id = request_id
        request_log.method = method
        request_log.path = path
        request_log.status = status
        request_log.error_code = error_code
        request_log.client_ip = client_ip
        request_log.account_key = account_key
        request_log.auth_failure = auth_failure

        with SessionLocal() as session:
            session.add(request_log)
            session.commit()

    def count_auth_failures(
        self,
        client_ip: str,
        auth_failures: list,
        window_minutes: int,
        account_key: str = None,
    ) -> int:
        """Quantas linhas deste IP falharam num dos tokens de `auth_failures` nos últimos `window_minutes` minutos.

        Com `account_key`, conta só as linhas dessa conta (a barreira do
        token da conta, passo 5.9). A janela é medida pelo relógio do
        banco (`now()`), o mesmo que preenche o `created_at`.
        """
        with SessionLocal() as session:
            query = session.query(func.count(RequestLog.id)).filter(
                RequestLog.client_ip == client_ip,
                RequestLog.auth_failure.in_(auth_failures),
                RequestLog.created_at >= func.now() - timedelta(minutes=window_minutes),
            )

            if account_key is not None:
                query = query.filter(RequestLog.account_key == account_key)

            return query.scalar()
```

- `src/repositories/__init__.py` (editar): o conteúdo inteiro passa a ser:

```python
from repositories.request_log_repository import RequestLogRepository
```

- `src/middlewares/request_log_writer.py` (criar): o conteúdo inteiro é:

```python
import re

from fastapi import FastAPI, Request
from fastapi.concurrency import run_in_threadpool

from constants import BYPASS_ENDPOINTS
from errors.base_error import InternalError
from repositories import RequestLogRepository
from utils.logger import get_logger
from utils.request_context import RequestState, get_request_state


logger = get_logger(__name__)

# /accounts/{account_key}... e /internal/accounts/{account_key}...: a key é
# o segmento logo depois de "accounts/", com os 36 caracteres de um UUID.
ACCOUNT_KEY_IN_PATH = re.compile(r"^/(?:internal/)?accounts/([0-9a-f-]{36})(?:/|$)")


def get_client_ip(request: Request):
    """O IP de quem chamou, como o servidor o vê; None quando o servidor não sabe."""
    if request.client is None:
        return None

    return request.client.host


def account_key_from_path(path: str):
    """A key da conta que está no caminho; None quando o caminho não é de uma conta."""
    match = ACCOUNT_KEY_IN_PATH.match(path)
    if match is None:
        return None

    return match.group(1)


async def save_request_log(request: Request, request_state: RequestState, status: int, error_code) -> None:
    """Grava a linha de request_log desta requisição.

    Grava só as colunas da PRD-14. Nunca cabeçalho, corpo nem parâmetros
    do endereço: é por lá que viajam token, CPF e CNPJ (PRD-12). A
    gravação roda fora do laço de eventos (run_in_threadpool), para não
    parar as outras requisições. Se ela falhar, a resposta segue para o
    cliente e a falha vai para o log da saída padrão.
    """
    try:
        await run_in_threadpool(
            RequestLogRepository().create,
            request_state.request_id,
            request.method,
            request.url.path,
            status,
            error_code,
            get_client_ip(request),
            request_state.account_key,
            request_state.auth_failure,
        )
    except Exception:
        logger.exception("Não consegui gravar a linha de request_log")


def register_request_log_writer_middleware(application: FastAPI) -> None:
    """Uma linha em request_log por requisição, deu certo ou não (PRD-06).

    Fica por fora da barreira e dos tokens: o 403 e o 429 também são
    gravados, e são as falhas de token gravadas aqui que a barreira conta
    (PRD-10). As rotas de BYPASS_ENDPOINTS não são gravadas: o health
    check não toca no banco (PRD-02).

    Antes de seguir, anota no estado da requisição a key da conta que
    está no caminho, para as camadas de dentro e para a linha do log.
    """

    @application.middleware("http")
    async def write_request_log(request: Request, call_next):
        if request.url.path in BYPASS_ENDPOINTS:
            return await call_next(request)

        request_state = get_request_state()
        request_state.account_key = account_key_from_path(request.url.path)

        try:
            response = await call_next(request)
        except Exception:
            # Erro inesperado: quem responde o 500 é o handler mais de
            # fora, depois daqui. A linha sai com o status e o código dele.
            await save_request_log(request, request_state, 500, InternalError.code)
            raise

        await save_request_log(request, request_state, response.status_code, request_state.error_code)

        return response
```

- `src/middlewares/__init__.py` (editar): o conteúdo inteiro passa a ser:

```python
from middlewares.admin_token import register_admin_token_middleware
from middlewares.internal_token import register_internal_token_middleware
from middlewares.request_context import register_request_context_middleware
from middlewares.request_log_writer import register_request_log_writer_middleware
from middlewares.request_logger import register_request_logger_middleware
from middlewares.session_manager import register_session_manager_middleware
```

- `src/app.py` (editar): o conteúdo inteiro passa a ser:

```python
from fastapi import FastAPI

from constants import check_variables
from errors import register_error_handlers
from errors.base_error import error_verification
from middlewares import (
    register_admin_token_middleware,
    register_internal_token_middleware,
    register_request_context_middleware,
    register_request_log_writer_middleware,
    register_request_logger_middleware,
    register_session_manager_middleware,
)
from resources import HealthCheckResource
from utils.logger import setup_logging


def create_app() -> FastAPI:
    """Monta a aplicação: os middlewares, as rotas e os error handlers."""
    # Os três None desligam a documentação automática (ARQ-09).
    application = FastAPI(
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )

    # ────────────────────────────────────────────────────────────────
    # Os middlewares. O ÚLTIMO registrado é o PRIMEIRO a rodar: leia as
    # linhas de baixo para cima e a requisição atravessa assim, de fora
    # para dentro:
    #
    #     request_context      nome da requisição e RequestState
    #     request_logger       ENTROU / SAIU na saída padrão
    #     request_log_writer   uma linha em request_log (PRD-06)
    #     internal_token       403 sem o INTERNAL-TOKEN certo (API-04)
    #     admin_token          403 em /internal sem o ADMIN-TOKEN (PRD-13)
    #     session_manager      sessão de banco; o mais interno de todos
    #
    # A ordem inteira, com os porquês: docs/plano/PLANO-00-indice.md,
    # seção "Middlewares".
    # ────────────────────────────────────────────────────────────────
    register_session_manager_middleware(application)
    register_admin_token_middleware(application)
    register_internal_token_middleware(application)
    register_request_log_writer_middleware(application)
    register_request_logger_middleware(application)
    register_request_context_middleware(application)

    # ────────────────────────────────────────────────────────────────
    # As rotas: uma linha por endereço e verbo. O status de sucesso sai
    # de dentro do resource (API-02).
    # ────────────────────────────────────────────────────────────────
    health_check_resource = HealthCheckResource()

    application.add_api_route("/", health_check_resource.on_get_home, methods=["GET"])
    application.add_api_route(
        "/health_check",
        health_check_resource.on_get_health_check,
        methods=["GET"]
    )

    register_error_handlers(application)

    return application


def main() -> FastAPI:
    # Não deixa a API subir com configuração faltando: é melhor falhar
    # agora, na hora de ligar, do que na cara do cliente mais tarde.
    check_variables()
    error_verification()
    setup_logging()

    return create_app()


app = main()
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/04-esqueleto`; `git log --oneline` mostra `feat(banco): lock_timeout e statement_timeout com resposta 503`.
2. Crie `src/repositories/request_log_repository.py` com o conteúdo do campo **Arquivos**.
3. Edite `src/repositories/__init__.py` com o conteúdo do campo **Arquivos**.
4. Crie `src/middlewares/request_log_writer.py` com o conteúdo do campo **Arquivos**.
5. Edite `src/middlewares/__init__.py` com o conteúdo do campo **Arquivos**.
6. Edite `src/app.py` com o conteúdo do campo **Arquivos**.
7. `docker compose up -d --build --wait` → termina sem erro.
8. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `76 passed`.
9. Rode as conferências L1 a L7 do **Verificar**, na ordem, cada uma depois da anterior. A L7 para e religa o banco.
10. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
11. Feche o passo (AGENTS.md, seção 7), um comando por vez:
    ```
    git add -- src/repositories/request_log_repository.py src/repositories/__init__.py src/middlewares/request_log_writer.py src/middlewares/__init__.py src/app.py
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "feat(log): uma linha em request_log por requisição"
    git log -1 --format=%B
    ```

**Testes:** nenhum teste novo. O teste black box só fala por HTTP, e nenhuma rota devolve o `request_log`: quem prova a gravação por HTTP é a barreira do 4.6, que só bloqueia se as falhas de token estiverem gravadas. Aqui, a prova são as conferências L1 a L7.
**Verificar:**
- L1: `curl.exe -s -i -H "INTERNAL-TOKEN: token_errado" http://127.0.0.1:3000/accounts/6f1c2a9e-8b3d-4c7a-9e21-5d4b3a2f1e0c/entries` → a primeira linha é `HTTP/1.1 403 Forbidden`.
- L2 (um comando, numa linha só):
  ```
  docker compose exec -T db psql -U bootcamp -d bootcamp -t -A -c "SELECT method, path, status, error_code, auth_failure, account_key FROM request_log ORDER BY id DESC LIMIT 1"
  ```
  → `GET|/accounts/6f1c2a9e-8b3d-4c7a-9e21-5d4b3a2f1e0c/entries|403|QIT000002|INTERNAL|6f1c2a9e-8b3d-4c7a-9e21-5d4b3a2f1e0c`
- L3: `curl.exe -s -i -H "INTERNAL-TOKEN: default_token" http://127.0.0.1:3000/nao_existe` → a primeira linha é `HTTP/1.1 404 Not Found`.
- L4: o mesmo comando da L2 → `GET|/nao_existe|404|QIT000404||`
- L5 (um comando, numa linha só):
  ```
  docker compose exec -T db psql -U bootcamp -d bootcamp -t -A -c "SELECT count(*) FROM request_log WHERE path IN ('/', '/health_check')"
  ```
  → `0` (o Docker consulta o `/health_check` a cada 3 segundos, e nenhuma dessas chamadas vira linha).
- L6 (PRD-12): `git grep -n -e "request.headers" -e "request.body" -e "request.json" -e "url.query" -- src/middlewares/request_log_writer.py src/repositories/request_log_repository.py` → nenhuma linha.
- L7 (PRD-02), um comando por vez:
  1. `docker compose stop db`
  2. `curl.exe -s -i http://127.0.0.1:3000/health_check` → a primeira linha é `HTTP/1.1 204 No Content`.
  3. `curl.exe -s -i http://127.0.0.1:3000/` → a primeira linha é `HTTP/1.1 200 OK`.
  4. `docker compose start db`
  5. `docker compose up -d --build --wait` → termina sem erro.
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `76 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/app.py
  src/middlewares/__init__.py
  src/middlewares/request_log_writer.py
  src/repositories/__init__.py
  src/repositories/request_log_repository.py
  ```
- `git log -1 --format=%B` → `feat(log): uma linha em request_log por requisição`

**Pronto quando:**
- [ ] L1 a L7 dão a saída esperada.
- [ ] No `src/app.py`, `register_request_log_writer_middleware` está registrado entre `register_internal_token_middleware` e `register_request_logger_middleware`.
- [ ] Suíte com `76 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/04-esqueleto`.

**Commit:** `feat(log): uma linha em request_log por requisição`
**Pare se:**
- `docker compose up -d --build --wait` falhar: rode `docker compose logs --tail 100 api` e traga a saída.
- L2 ou L4 vierem vazias ou diferentes: rode `docker compose logs --tail 100 api` e procure `Não consegui gravar a linha de request_log`; traga a saída.
- L5 der número diferente de `0`.
- L7, item 2 ou 3, der outra primeira linha: a API depende do banco para o health check.
- A suíte não terminar com `76 passed`.

---

### Passo 4.6 — Barreira dos tokens internos
**Branch:** fase/04-esqueleto · **Depende de:** 4.5
**Objetivo:** `register_auth_barrier_middleware`: `AUTH_FAILURE_LIMIT` falhas de `INTERNAL` ou `ADMIN` do mesmo IP em `AUTH_FAILURE_WINDOW_MINUTES` fazem toda requisição desse IP responder 429 `QIT000429`, antes de conferir token; os testes de `test_healthcheck.py` que erram token passam a começar com `DbUtils.rollback()`.
**Decisões:** PRD-10 — barreira · PRD-04 — sem estado na memória · PRD-06 — o log alimenta a barreira · PRD-02 — health check sem banco · PRD-08 — timeout também na barreira · TST-01 — black box e TDD · TST-02 — o que barra tem teste
**Arquivos:**
- `src/middlewares/auth_barrier.py` (criar): o conteúdo inteiro é:

```python
from fastapi import FastAPI, Request
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.exc import OperationalError

from constants import AUTH_FAILURE_LIMIT, AUTH_FAILURE_WINDOW_MINUTES, BYPASS_ENDPOINTS
from errors.base_error import DatabaseTimeout, TooManyAuthFailures
from errors.handlers import is_database_timeout, qi_exception_to_response
from middlewares.request_log_writer import get_client_ip
from models import RequestLog
from repositories import RequestLogRepository


# As falhas que esta barreira conta: as dos dois tokens internos, por IP.
INTERNAL_AUTH_FAILURES = [RequestLog.INTERNAL, RequestLog.ADMIN]


def register_auth_barrier_middleware(application: FastAPI) -> None:
    """Barreira contra chute de token (PRD-10).

    AUTH_FAILURE_LIMIT falhas de INTERNAL-TOKEN ou ADMIN-TOKEN do mesmo IP
    nos últimos AUTH_FAILURE_WINDOW_MINUTES minutos: toda requisição desse
    IP responde 429 QIT000429, antes de conferir token nenhum, até as
    falhas antigas saírem da janela. O 429 não conta como falha.

    A contagem mora em request_log, no banco, e não na memória do
    processo (PRD-04): vale para todas as cópias da API. As rotas de
    BYPASS_ENDPOINTS passam direto: o health check não toca no banco
    (PRD-02).
    """

    @application.middleware("http")
    async def check_auth_barrier(request: Request, call_next):
        if request.method == "OPTIONS" or request.url.path in BYPASS_ENDPOINTS:
            return await call_next(request)

        try:
            failures = await run_in_threadpool(
                RequestLogRepository().count_auth_failures,
                get_client_ip(request),
                INTERNAL_AUTH_FAILURES,
                AUTH_FAILURE_WINDOW_MINUTES,
            )
        except OperationalError as error:
            if is_database_timeout(error):
                return qi_exception_to_response(DatabaseTimeout())
            raise

        if failures >= AUTH_FAILURE_LIMIT:
            return qi_exception_to_response(TooManyAuthFailures())

        return await call_next(request)
```

- `src/middlewares/__init__.py` (editar): o conteúdo inteiro passa a ser:

```python
from middlewares.admin_token import register_admin_token_middleware
from middlewares.auth_barrier import register_auth_barrier_middleware
from middlewares.internal_token import register_internal_token_middleware
from middlewares.request_context import register_request_context_middleware
from middlewares.request_log_writer import register_request_log_writer_middleware
from middlewares.request_logger import register_request_logger_middleware
from middlewares.session_manager import register_session_manager_middleware
```

- `src/app.py` (editar): o conteúdo inteiro passa a ser:

```python
from fastapi import FastAPI

from constants import check_variables
from errors import register_error_handlers
from errors.base_error import error_verification
from middlewares import (
    register_admin_token_middleware,
    register_auth_barrier_middleware,
    register_internal_token_middleware,
    register_request_context_middleware,
    register_request_log_writer_middleware,
    register_request_logger_middleware,
    register_session_manager_middleware,
)
from resources import HealthCheckResource
from utils.logger import setup_logging


def create_app() -> FastAPI:
    """Monta a aplicação: os middlewares, as rotas e os error handlers."""
    # Os três None desligam a documentação automática (ARQ-09).
    application = FastAPI(
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )

    # ────────────────────────────────────────────────────────────────
    # Os middlewares. O ÚLTIMO registrado é o PRIMEIRO a rodar: leia as
    # linhas de baixo para cima e a requisição atravessa assim, de fora
    # para dentro:
    #
    #     request_context      nome da requisição e RequestState
    #     request_logger       ENTROU / SAIU na saída padrão
    #     request_log_writer   uma linha em request_log (PRD-06)
    #     auth_barrier         429 para o IP que errou token demais (PRD-10)
    #     internal_token       403 sem o INTERNAL-TOKEN certo (API-04)
    #     admin_token          403 em /internal sem o ADMIN-TOKEN (PRD-13)
    #     session_manager      sessão de banco; o mais interno de todos
    #
    # O log vem antes da barreira e dos tokens para gravar também o 403 e
    # o 429; a barreira vem antes dos tokens para responder sem conferir
    # token nenhum. A ordem inteira, com os porquês:
    # docs/plano/PLANO-00-indice.md, seção "Middlewares".
    # ────────────────────────────────────────────────────────────────
    register_session_manager_middleware(application)
    register_admin_token_middleware(application)
    register_internal_token_middleware(application)
    register_auth_barrier_middleware(application)
    register_request_log_writer_middleware(application)
    register_request_logger_middleware(application)
    register_request_context_middleware(application)

    # ────────────────────────────────────────────────────────────────
    # As rotas: uma linha por endereço e verbo. O status de sucesso sai
    # de dentro do resource (API-02).
    # ────────────────────────────────────────────────────────────────
    health_check_resource = HealthCheckResource()

    application.add_api_route("/", health_check_resource.on_get_home, methods=["GET"])
    application.add_api_route(
        "/health_check",
        health_check_resource.on_get_health_check,
        methods=["GET"]
    )

    register_error_handlers(application)

    return application


def main() -> FastAPI:
    # Não deixa a API subir com configuração faltando: é melhor falhar
    # agora, na hora de ligar, do que na cara do cliente mais tarde.
    check_variables()
    error_verification()
    setup_logging()

    return create_app()


app = main()
```

- `tests/integration/security/test_auth_barrier.py` (criar): o conteúdo inteiro é:

```python
"""Barreira contra chute dos tokens internos (PRD-10, PRD-04).

AUTH_FAILURE_LIMIT erros de INTERNAL-TOKEN ou ADMIN-TOKEN do mesmo IP
fazem toda requisição desse IP responder 429 QIT000429, antes de
conferir token. A contagem mora em request_log (PRD-04): cada teste
começa e termina com DbUtils.rollback(). Sem a limpeza do fim, o IP dos
testes ficaria barrado para o resto da suíte.

A janela de AUTH_FAILURE_WINDOW_MINUTES minutos não é testada aqui: o
teste teria de esperar a janela passar.
"""

from os import environ

from tests.utils import INTERNAL_TOKEN, DbUtils
from tests.utils.requisition import ClientRequisition


ADMIN_TOKEN = environ.get("ADMIN_TOKEN", "default_admin_token")
AUTH_FAILURE_LIMIT = int(environ.get("AUTH_FAILURE_LIMIT", "10"))

WRONG_TOKEN = "token_errado"
UNKNOWN_PATH = "/nao_existe"
INTERNAL_PATH = "/internal/nao_existe"
TOO_MANY_TRANSLATION = "Tentativas demais com token errado. Tente de novo mais tarde."


def fail_internal_token(times: int) -> None:
    for _ in range(times):
        response = ClientRequisition.send("GET", UNKNOWN_PATH, headers={"INTERNAL-TOKEN": WRONG_TOKEN})
        assert response.response_status == 403
        assert response.response_json["code"] == "QIT000002"


def fail_admin_token(times: int) -> None:
    for _ in range(times):
        response = ClientRequisition.send(
            "GET",
            INTERNAL_PATH,
            headers={"INTERNAL-TOKEN": INTERNAL_TOKEN, "ADMIN-TOKEN": WRONG_TOKEN},
        )
        assert response.response_status == 403
        assert response.response_json["code"] == "QIT000003"


def send_with_internal_token():
    return ClientRequisition.send("GET", UNKNOWN_PATH, headers={"INTERNAL-TOKEN": INTERNAL_TOKEN})


def assert_not_blocked() -> None:
    response = send_with_internal_token()
    assert response.response_status == 404
    assert response.response_json["code"] == "QIT000404"


def assert_blocked() -> None:
    response = send_with_internal_token()
    assert response.response_status == 429
    assert response.response_json["code"] == "QIT000429"
    assert response.response_json["translation"] == TOO_MANY_TRANSLATION


class TestAuthBarrier:
    def test_limit_of_internal_failures_blocks_the_ip(self):
        DbUtils.rollback()
        try:
            fail_internal_token(AUTH_FAILURE_LIMIT)

            assert_blocked()

            response = ClientRequisition.send("GET", UNKNOWN_PATH)
            assert response.response_status == 429
            assert response.response_json["code"] == "QIT000429"

            response = ClientRequisition.send(
                "POST",
                INTERNAL_PATH,
                headers={"INTERNAL-TOKEN": INTERNAL_TOKEN, "ADMIN-TOKEN": ADMIN_TOKEN},
            )
            assert response.response_status == 429
            assert response.response_json["code"] == "QIT000429"
        finally:
            DbUtils.rollback()

    def test_one_failure_below_the_limit_does_not_block(self):
        DbUtils.rollback()
        try:
            fail_internal_token(AUTH_FAILURE_LIMIT - 1)

            assert_not_blocked()

            fail_internal_token(1)

            assert_blocked()
        finally:
            DbUtils.rollback()

    def test_limit_of_admin_failures_blocks_the_ip(self):
        DbUtils.rollback()
        try:
            fail_admin_token(AUTH_FAILURE_LIMIT)

            assert_blocked()
        finally:
            DbUtils.rollback()

    def test_internal_and_admin_failures_add_up(self):
        DbUtils.rollback()
        try:
            fail_internal_token(AUTH_FAILURE_LIMIT // 2)
            fail_admin_token(AUTH_FAILURE_LIMIT - AUTH_FAILURE_LIMIT // 2)

            assert_blocked()
        finally:
            DbUtils.rollback()

    def test_successful_requests_do_not_count(self):
        DbUtils.rollback()
        try:
            for _ in range(2 * AUTH_FAILURE_LIMIT):
                assert_not_blocked()

            fail_internal_token(AUTH_FAILURE_LIMIT - 1)

            assert_not_blocked()

            fail_internal_token(1)

            assert_blocked()
        finally:
            DbUtils.rollback()

    def test_public_routes_skip_the_barrier(self):
        DbUtils.rollback()
        try:
            fail_internal_token(AUTH_FAILURE_LIMIT)

            response = ClientRequisition.send("GET", "/")
            assert response.response_status == 200

            response = ClientRequisition.send("GET", "/health_check")
            assert response.response_status == 204

            assert_blocked()
        finally:
            DbUtils.rollback()
```

- `tests/integration/test_healthcheck.py` (editar): três trocas, e nada mais. Os comentários e as docstrings ficam como estão.
  1. Troque a linha
     ```python
     from tests.utils import INTERNAL_TOKEN
     ```
     por
     ```python
     from tests.utils import INTERNAL_TOKEN, DbUtils
     ```
  2. Troque as duas linhas
     ```python
         def test_no_token(self):
             response = ClientRequisition.send("PUT", "/sample")
     ```
     por
     ```python
         def test_no_token(self):
             DbUtils.rollback()

             response = ClientRequisition.send("PUT", "/sample")
     ```
  3. Em `test_error_translation_keeps_accents`, troque as duas linhas que fecham a docstring e abrem o corpo
     ```python
             """
             response = ClientRequisition.send("PUT", "/sample")
     ```
     por
     ```python
             """
             DbUtils.rollback()

             response = ClientRequisition.send("PUT", "/sample")
     ```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/04-esqueleto`; `git log --oneline` mostra `feat(log): uma linha em request_log por requisição`.
2. Crie `tests/integration/security/test_auth_barrier.py` com o conteúdo do campo **Arquivos**.
3. Faça as três trocas em `tests/integration/test_healthcheck.py`.
4. `docker compose up -d --build --wait`.
5. `./.venv/Scripts/python.exe -m pytest -v tests/integration/security/test_auth_barrier.py` → a última linha tem `6 failed` e não tem `passed`. Os 6 falham por asserção de status: o 429 esperado volta 404.
6. `./.venv/Scripts/python.exe -m pytest -v tests/integration/test_healthcheck.py` → a última linha tem `6 passed` (as trocas só acrescentam a limpeza).
7. Crie `src/middlewares/auth_barrier.py` com o conteúdo do campo **Arquivos**.
8. Edite `src/middlewares/__init__.py` com o conteúdo do campo **Arquivos**.
9. Edite `src/app.py` com o conteúdo do campo **Arquivos**.
10. `docker compose up -d --build --wait`.
11. `./.venv/Scripts/python.exe -m pytest -v tests/integration/security/test_auth_barrier.py` → a última linha tem `6 passed`.
12. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `82 passed`.
13. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
14. Feche o passo (AGENTS.md, seção 7), um comando por vez:
    ```
    git add -- src/middlewares/auth_barrier.py src/middlewares/__init__.py src/app.py tests/integration/security/test_auth_barrier.py tests/integration/test_healthcheck.py
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "feat(seguranca): barreira contra chute dos tokens internos"
    git log -1 --format=%B
    ```

**Testes:** `tests/integration/security/test_auth_barrier.py`. `LIMIT` = `AUTH_FAILURE_LIMIT` (10 sem `.env`). "Falha interna" = `GET /nao_existe` com `INTERNAL-TOKEN: token_errado` → 403 `QIT000002`. "Falha de admin" = `GET /internal/nao_existe` com `INTERNAL-TOKEN` certo e `ADMIN-TOKEN: token_errado` → 403 `QIT000003`. "Requisição certa" = `GET /nao_existe` com `INTERNAL-TOKEN` certo. Efeito no banco: só linhas de `request_log`, apagadas pelo `DbUtils.rollback()` do começo e do fim de cada teste.

| Função de teste | Entrada | Esperado |
|---|---|---|
| `test_limit_of_internal_failures_blocks_the_ip` | `LIMIT` falhas internas; depois (a) requisição certa; (b) `GET /nao_existe` sem token nenhum; (c) `POST /internal/nao_existe` com os dois tokens certos | (a) 429 `QIT000429`, `translation` = `Tentativas demais com token errado. Tente de novo mais tarde.`; (b) 429 `QIT000429`, não 403: a barreira responde antes de conferir token; (c) 429 `QIT000429`: barra toda rota |
| `test_one_failure_below_the_limit_does_not_block` | `LIMIT - 1` falhas internas; requisição certa; mais 1 falha; requisição certa | a primeira certa: 404 `QIT000404` (passa); a segunda: 429 `QIT000429` (barrada no limite exato) |
| `test_limit_of_admin_failures_blocks_the_ip` | `LIMIT` falhas de admin; requisição certa | 429 `QIT000429`: falha do `ADMIN-TOKEN` também conta |
| `test_internal_and_admin_failures_add_up` | `LIMIT // 2` falhas internas e `LIMIT - LIMIT // 2` de admin; requisição certa | 429 `QIT000429`: as duas somam no mesmo limite |
| `test_successful_requests_do_not_count` | `2 × LIMIT` requisições certas; `LIMIT - 1` falhas internas; requisição certa; 1 falha; requisição certa | as certas do começo: 404; a do meio: 404 (sucesso não conta); a última: 429 |
| `test_public_routes_skip_the_barrier` | `LIMIT` falhas internas; `GET /`; `GET /health_check`; requisição certa | 200; 204 (o IP barrado ainda vê as rotas públicas, que não tocam no banco); 429 `QIT000429` |

`tests/integration/test_healthcheck.py`: `test_no_token` e `test_error_translation_keeps_accents` passam a começar com `DbUtils.rollback()` (PRD-10: teste que erra token de propósito limpa a contagem). Entradas e resultados esperados não mudam.

**Verificar:**
- `./.venv/Scripts/python.exe -m pytest -v tests/integration/security/test_auth_barrier.py` → `6 passed`.
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `82 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m pytest` de novo → `82 passed` (a barreira não deixa resto de uma rodada para a outra).
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/app.py
  src/middlewares/__init__.py
  src/middlewares/auth_barrier.py
  tests/integration/security/test_auth_barrier.py
  tests/integration/test_healthcheck.py
  ```
- `git log -1 --format=%B` → `feat(seguranca): barreira contra chute dos tokens internos`

**Pronto quando:**
- [ ] Os 6 testes falharam antes do código (item 5) e passam depois (item 11).
- [ ] No `src/app.py`, `register_auth_barrier_middleware` está registrado entre `register_internal_token_middleware` e `register_request_log_writer_middleware`.
- [ ] Suíte com `82 passed`, duas vezes seguidas; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/04-esqueleto`.

**Commit:** `feat(seguranca): barreira contra chute dos tokens internos`
**Pare se:**
- O item 5 não terminar com `6 failed`.
- O item 6 não terminar com `6 passed`.
- Um teste fora de `test_auth_barrier.py` receber 429: algum teste que erra token não limpa a contagem.
- O item 11 der 403 onde o esperado é 429: a ordem dos registros no `src/app.py` não é a do plano.
- A suíte não terminar com `82 passed`.

---

### Passo 4.7 — Funções de teste: requisições
**Branch:** fase/04-esqueleto · **Depende de:** 4.6
**Objetivo:** `RequestGenerator` reescrito, com um método por rota do registro do `PLANO-00-indice.md`, e as constantes `INTERNAL_TOKEN` e `ADMIN_TOKEN`.
**Decisões:** TST-01 — black box (os testes falam com a API só por HTTP, pelas funções de `tests/utils/`) · API-04 — `INTERNAL-TOKEN` · API-16 — `ACCOUNT-TOKEN` · PRD-13 — `ADMIN-TOKEN`
**Arquivos:**
- `tests/utils/request_generator.py` (editar): o conteúdo inteiro passa a ser:

```python
from os import environ

from tests.utils.requisition import ClientRequisition


INTERNAL_TOKEN = environ.get("INTERNAL_TOKEN", "default_token")
ADMIN_TOKEN = environ.get("ADMIN_TOKEN", "default_admin_token")


def _headers(internal_token: str = None, account_token: str = None, admin_token: str = None) -> dict:
    """Os cabeçalhos de token da requisição. Valor None deixa o cabeçalho de fora."""
    headers = {}

    if internal_token is not None:
        headers["INTERNAL-TOKEN"] = internal_token

    if account_token is not None:
        headers["ACCOUNT-TOKEN"] = account_token

    if admin_token is not None:
        headers["ADMIN-TOKEN"] = admin_token

    return headers


def _send(method: str, endpoint: str, headers: dict, payload: dict = None, query_params: dict = None) -> tuple:
    """Manda a requisição e devolve (status, corpo JSON ou None)."""
    response = ClientRequisition.send(method, endpoint, payload=payload, headers=headers, query_params=query_params)

    return response.response_status, response.response_json


class RequestGenerator:
    """Um método por rota de docs/rotas.md; cada um devolve (status, corpo).

    Os tokens têm padrão: o INTERNAL_TOKEN e o ADMIN_TOKEN certos. O
    `account_token` é sempre pedido, porque cada conta tem o seu. Para
    testar token errado, passe outro valor; para testar token faltando,
    passe None.
    """

    @staticmethod
    def POST_customer(payload: dict, internal_token: str = INTERNAL_TOKEN) -> tuple:
        return _send("POST", "/customers", _headers(internal_token), payload=payload)

    @staticmethod
    def GET_customer(customer_key: str, account_token: str, internal_token: str = INTERNAL_TOKEN) -> tuple:
        return _send("GET", f"/customers/{customer_key}", _headers(internal_token, account_token))

    @staticmethod
    def POST_account(customer_key: str, internal_token: str = INTERNAL_TOKEN) -> tuple:
        return _send("POST", f"/customers/{customer_key}/accounts", _headers(internal_token))

    @staticmethod
    def GET_account(account_key: str, account_token: str, internal_token: str = INTERNAL_TOKEN) -> tuple:
        return _send("GET", f"/accounts/{account_key}", _headers(internal_token, account_token))

    @staticmethod
    def DELETE_account(account_key: str, account_token: str, internal_token: str = INTERNAL_TOKEN) -> tuple:
        return _send("DELETE", f"/accounts/{account_key}", _headers(internal_token, account_token))

    @staticmethod
    def POST_deposit(account_key: str, payload: dict, internal_token: str = INTERNAL_TOKEN) -> tuple:
        return _send("POST", f"/accounts/{account_key}/deposits", _headers(internal_token), payload=payload)

    @staticmethod
    def POST_withdrawal(account_key: str, account_token: str, payload: dict, internal_token: str = INTERNAL_TOKEN) -> tuple:
        return _send("POST", f"/accounts/{account_key}/withdrawals", _headers(internal_token, account_token), payload=payload)

    @staticmethod
    def POST_transfer(account_key: str, account_token: str, payload: dict, internal_token: str = INTERNAL_TOKEN) -> tuple:
        return _send("POST", f"/accounts/{account_key}/transfers", _headers(internal_token, account_token), payload=payload)

    @staticmethod
    def GET_transaction(account_key: str, account_token: str, transaction_key: str, internal_token: str = INTERNAL_TOKEN) -> tuple:
        return _send("GET", f"/accounts/{account_key}/transactions/{transaction_key}", _headers(internal_token, account_token))

    @staticmethod
    def GET_entries(account_key: str, account_token: str, params: dict = None, internal_token: str = INTERNAL_TOKEN) -> tuple:
        return _send("GET", f"/accounts/{account_key}/entries", _headers(internal_token, account_token), query_params=params)

    @staticmethod
    def GET_gamification(account_key: str, account_token: str, internal_token: str = INTERNAL_TOKEN) -> tuple:
        return _send("GET", f"/accounts/{account_key}/gamification", _headers(internal_token, account_token))

    @staticmethod
    def POST_point_application(account_key: str, account_token: str, payload: dict, internal_token: str = INTERNAL_TOKEN) -> tuple:
        return _send("POST", f"/accounts/{account_key}/point_applications", _headers(internal_token, account_token), payload=payload)

    @staticmethod
    def POST_point_reset(account_key: str, account_token: str, internal_token: str = INTERNAL_TOKEN) -> tuple:
        return _send("POST", f"/accounts/{account_key}/point_resets", _headers(internal_token, account_token))

    @staticmethod
    def POST_saving(account_key: str, account_token: str, payload: dict, internal_token: str = INTERNAL_TOKEN) -> tuple:
        return _send("POST", f"/accounts/{account_key}/savings", _headers(internal_token, account_token), payload=payload)

    @staticmethod
    def POST_redemption(account_key: str, account_token: str, payload: dict, internal_token: str = INTERNAL_TOKEN) -> tuple:
        return _send("POST", f"/accounts/{account_key}/redemptions", _headers(internal_token, account_token), payload=payload)

    @staticmethod
    def GET_piggy_bank_entries(account_key: str, account_token: str, params: dict = None, internal_token: str = INTERNAL_TOKEN) -> tuple:
        return _send("GET", f"/accounts/{account_key}/piggy_bank_entries", _headers(internal_token, account_token), query_params=params)

    @staticmethod
    def POST_category(account_key: str, account_token: str, payload: dict, internal_token: str = INTERNAL_TOKEN) -> tuple:
        return _send("POST", f"/accounts/{account_key}/categories", _headers(internal_token, account_token), payload=payload)

    @staticmethod
    def GET_categories(account_key: str, account_token: str, params: dict = None, internal_token: str = INTERNAL_TOKEN) -> tuple:
        return _send("GET", f"/accounts/{account_key}/categories", _headers(internal_token, account_token), query_params=params)

    @staticmethod
    def GET_category(account_key: str, account_token: str, category_key: str, internal_token: str = INTERNAL_TOKEN) -> tuple:
        return _send("GET", f"/accounts/{account_key}/categories/{category_key}", _headers(internal_token, account_token))

    @staticmethod
    def DELETE_category(account_key: str, account_token: str, category_key: str, internal_token: str = INTERNAL_TOKEN) -> tuple:
        return _send("DELETE", f"/accounts/{account_key}/categories/{category_key}", _headers(internal_token, account_token))

    @staticmethod
    def POST_block(account_key: str, payload: dict, internal_token: str = INTERNAL_TOKEN, admin_token: str = ADMIN_TOKEN) -> tuple:
        return _send("POST", f"/internal/accounts/{account_key}/blocks", _headers(internal_token, admin_token=admin_token), payload=payload)

    @staticmethod
    def POST_unblock(account_key: str, internal_token: str = INTERNAL_TOKEN, admin_token: str = ADMIN_TOKEN) -> tuple:
        return _send("POST", f"/internal/accounts/{account_key}/unblocks", _headers(internal_token, admin_token=admin_token))

    @staticmethod
    def POST_day_closing(payload: dict, internal_token: str = INTERNAL_TOKEN, admin_token: str = ADMIN_TOKEN) -> tuple:
        return _send("POST", "/internal/day_closings", _headers(internal_token, admin_token=admin_token), payload=payload)
```

- `tests/utils/__init__.py` (editar): o conteúdo inteiro passa a ser:

```python
from tests.utils.db_utils import DbUtils
from tests.utils.random_generator import RandomGenerator
from tests.utils.object_generator import ObjectGenerator
from tests.utils.payload_generator import PayloadGenerator
from tests.utils.request_generator import RequestGenerator, INTERNAL_TOKEN, ADMIN_TOKEN
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/04-esqueleto`; `git log --oneline` mostra `feat(seguranca): barreira contra chute dos tokens internos`.
2. Edite `tests/utils/request_generator.py` com o conteúdo do campo **Arquivos**.
3. Edite `tests/utils/__init__.py` com o conteúdo do campo **Arquivos**.
4. Rode a conferência G1 do **Verificar**.
5. `docker compose up -d --build --wait`.
6. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `82 passed`.
7. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
8. Feche o passo (AGENTS.md, seção 7), um comando por vez:
   ```
   git add -- tests/utils/request_generator.py tests/utils/__init__.py
   git diff --cached --name-only
   git diff --name-only
   git ls-files --others --exclude-standard
   git commit -m "test(utils): RequestGenerator com um método por rota"
   git log -1 --format=%B
   ```

**Testes:** nenhum teste novo. As 23 rotas nascem nas fases 5 a 9; um teste que as chamasse agora receberia 404 e quebraria quando cada rota nascesse. A prova é a G1: troca o `ClientRequisition.send` por um gravador, chama os 23 métodos e confere método HTTP, caminho, cabeçalhos com os valores, corpo e query string de cada um, sem falar com a API.
**Verificar:**
- G1 (um comando, numa linha só):
  ```
  ./.venv/Scripts/python.exe -c "import types; from tests.utils.requisition import ClientRequisition; calls = []; ClientRequisition.send = staticmethod(lambda method, endpoint, payload=None, headers=None, query_params=None: calls.append('|'.join([method, endpoint, ','.join(k + '=' + v for k, v in sorted(headers.items())), '-' if payload is None else 'body', '-' if query_params is None else 'query'])) or types.SimpleNamespace(response_status=0, response_json=None)); from tests.utils import RequestGenerator as R; R.POST_customer({}); R.GET_customer('ck', 'tk'); R.POST_account('ck'); R.GET_account('ak', 'tk'); R.DELETE_account('ak', 'tk'); R.POST_deposit('ak', {}); R.POST_withdrawal('ak', 'tk', {}); R.POST_transfer('ak', 'tk', {}); R.GET_transaction('ak', 'tk', 'xk'); R.GET_entries('ak', 'tk', {'limit': '1'}); R.GET_gamification('ak', 'tk'); R.POST_point_application('ak', 'tk', {}); R.POST_point_reset('ak', 'tk'); R.POST_saving('ak', 'tk', {}); R.POST_redemption('ak', 'tk', {}); R.GET_piggy_bank_entries('ak', 'tk', {'limit': '1'}); R.POST_category('ak', 'tk', {}); R.GET_categories('ak', 'tk', {'limit': '1'}); R.GET_category('ak', 'tk', 'gk'); R.DELETE_category('ak', 'tk', 'gk'); R.POST_block('ak', {}); R.POST_unblock('ak'); R.POST_day_closing({}); R.GET_account('ak', None, internal_token=None); print(len(calls)); print(chr(10).join(calls))"
  ```
  → exatamente estas 25 linhas:
  ```
  24
  POST|/customers|INTERNAL-TOKEN=default_token|body|-
  GET|/customers/ck|ACCOUNT-TOKEN=tk,INTERNAL-TOKEN=default_token|-|-
  POST|/customers/ck/accounts|INTERNAL-TOKEN=default_token|-|-
  GET|/accounts/ak|ACCOUNT-TOKEN=tk,INTERNAL-TOKEN=default_token|-|-
  DELETE|/accounts/ak|ACCOUNT-TOKEN=tk,INTERNAL-TOKEN=default_token|-|-
  POST|/accounts/ak/deposits|INTERNAL-TOKEN=default_token|body|-
  POST|/accounts/ak/withdrawals|ACCOUNT-TOKEN=tk,INTERNAL-TOKEN=default_token|body|-
  POST|/accounts/ak/transfers|ACCOUNT-TOKEN=tk,INTERNAL-TOKEN=default_token|body|-
  GET|/accounts/ak/transactions/xk|ACCOUNT-TOKEN=tk,INTERNAL-TOKEN=default_token|-|-
  GET|/accounts/ak/entries|ACCOUNT-TOKEN=tk,INTERNAL-TOKEN=default_token|-|query
  GET|/accounts/ak/gamification|ACCOUNT-TOKEN=tk,INTERNAL-TOKEN=default_token|-|-
  POST|/accounts/ak/point_applications|ACCOUNT-TOKEN=tk,INTERNAL-TOKEN=default_token|body|-
  POST|/accounts/ak/point_resets|ACCOUNT-TOKEN=tk,INTERNAL-TOKEN=default_token|-|-
  POST|/accounts/ak/savings|ACCOUNT-TOKEN=tk,INTERNAL-TOKEN=default_token|body|-
  POST|/accounts/ak/redemptions|ACCOUNT-TOKEN=tk,INTERNAL-TOKEN=default_token|body|-
  GET|/accounts/ak/piggy_bank_entries|ACCOUNT-TOKEN=tk,INTERNAL-TOKEN=default_token|-|query
  POST|/accounts/ak/categories|ACCOUNT-TOKEN=tk,INTERNAL-TOKEN=default_token|body|-
  GET|/accounts/ak/categories|ACCOUNT-TOKEN=tk,INTERNAL-TOKEN=default_token|-|query
  GET|/accounts/ak/categories/gk|ACCOUNT-TOKEN=tk,INTERNAL-TOKEN=default_token|-|-
  DELETE|/accounts/ak/categories/gk|ACCOUNT-TOKEN=tk,INTERNAL-TOKEN=default_token|-|-
  POST|/internal/accounts/ak/blocks|ADMIN-TOKEN=default_admin_token,INTERNAL-TOKEN=default_token|body|-
  POST|/internal/accounts/ak/unblocks|ADMIN-TOKEN=default_admin_token,INTERNAL-TOKEN=default_token|-|-
  POST|/internal/day_closings|ADMIN-TOKEN=default_admin_token,INTERNAL-TOKEN=default_token|body|-
  GET|/accounts/ak||-|-
  ```
- `git grep -n -i "sample" -- tests/utils/request_generator.py` → nenhuma linha.
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `82 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  tests/utils/__init__.py
  tests/utils/request_generator.py
  ```
- `git log -1 --format=%B` → `test(utils): RequestGenerator com um método por rota`

**Pronto quando:**
- [ ] A G1 dá exatamente as 25 linhas do **Verificar**.
- [ ] `ADMIN_TOKEN` sai de `tests.utils`.
- [ ] Suíte com `82 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/04-esqueleto`.

**Commit:** `test(utils): RequestGenerator com um método por rota`
**Pare se:**
- A G1 terminar com `Traceback` ou der outra saída depois de 3 tentativas de conferir o arquivo contra o plano.
- A suíte não terminar com `82 passed`.

---

### Passo 4.8 — Funções de teste: corpos e objetos
**Branch:** fase/04-esqueleto · **Depende de:** 4.7
**Objetivo:** `PayloadGenerator` (um corpo válido por schema de entrada) e `ObjectGenerator` (`create_customer`, `create_account`, `create_funded_account`), sem nada do `sample_entity` em `tests/utils/`; os exemplos da docstring de `src/utils/schema_handler.py` deixam de citar o `sample_entity`.
**Decisões:** TST-01 — black box (dados montados pelas rotas) · R6 — sem float · DAD-08 — centavos inteiros · API-03 — schema fechado · ARQ-11 — pode mudar o base
**Arquivos:**
- `tests/utils/payload_generator.py` (editar): o conteúdo inteiro passa a ser:

```python
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
```

- `tests/utils/object_generator.py` (editar): o conteúdo inteiro passa a ser:

```python
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
```

- `tests/utils/__init__.py` (editar): o conteúdo inteiro passa a ser (a mesma lista, na ordem em que cada arquivo depende do anterior):

```python
from tests.utils.db_utils import DbUtils
from tests.utils.random_generator import RandomGenerator
from tests.utils.payload_generator import PayloadGenerator
from tests.utils.request_generator import RequestGenerator, INTERNAL_TOKEN, ADMIN_TOKEN
from tests.utils.object_generator import ObjectGenerator
```

- `src/utils/schema_handler.py` (editar): só a docstring dos dois decorators; o código não muda. Cinco trocas, e nada mais:
  1. A linha `                @SchemaHandler.validate("post_sample_entity.json")` vira `                @SchemaHandler.validate("post_customers.json")`.
  2. A linha `        "/sample_entity" a este método é o src/app.py, e é de propósito:` vira `        "/customers" a este método é o src/app.py, e é de propósito:`.
  3. A linha `                @SchemaHandler.validate_query_params("get_sample_entities.json")` vira `                @SchemaHandler.validate_query_params("get_entries.json")`.
  4. A linha `                def on_get_list(self, request: Request) -> JSONResponse:` vira `                def on_get_entries(self, request: Request) -> JSONResponse:`.
  5. A linha `            class SampleEntityResource:` aparece duas vezes. A primeira (logo acima da linha da troca 1) vira `            class CustomerResource:`; a segunda (logo acima da linha da troca 3) vira `            class TransactionResource:`.

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/04-esqueleto`; `git log --oneline` mostra `test(utils): RequestGenerator com um método por rota`.
2. Edite `tests/utils/payload_generator.py` com o conteúdo do campo **Arquivos**.
3. Edite `tests/utils/object_generator.py` com o conteúdo do campo **Arquivos**.
4. Edite `tests/utils/__init__.py` com o conteúdo do campo **Arquivos**.
5. Faça as cinco trocas em `src/utils/schema_handler.py`.
6. Rode as conferências P1 e P2 do **Verificar**.
7. `docker compose up -d --build --wait`.
8. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `82 passed`.
9. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
10. Feche o passo (AGENTS.md, seção 7), um comando por vez:
    ```
    git add -- tests/utils/payload_generator.py tests/utils/object_generator.py tests/utils/__init__.py src/utils/schema_handler.py
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "test(utils): PayloadGenerator e ObjectGenerator do projeto"
    git log -1 --format=%B
    ```

**Testes:** nenhum teste novo. O `ObjectGenerator` chama rotas que nascem nas fases 5 e 6, e o primeiro uso dele é o teste da rota (5.3 em diante). A prova é a P1 (os nomes existem) e a P2 (cada corpo do `PayloadGenerator` passa no schema da sua rota, com `"additionalProperties": false` e dinheiro inteiro).
**Verificar:**
- P1 (um comando, numa linha só):
  ```
  ./.venv/Scripts/python.exe -c "from tests.utils import ObjectGenerator as O, PayloadGenerator as P; print(sorted(n for n in vars(O) if not n.startswith('_'))); print(sorted(n for n in vars(P) if not n.startswith('_')))"
  ```
  → exatamente:
  ```
  ['create_account', 'create_customer', 'create_funded_account']
  ['block', 'category', 'customer', 'day_closing', 'deposit', 'point_application', 'redemption', 'saving', 'transfer', 'withdrawal']
  ```
- P2 (um comando, numa linha só):
  ```
  ./.venv/Scripts/python.exe -c "import json, uuid, jsonschema; from tests.utils import PayloadGenerator as P, RandomGenerator; k = str(uuid.uuid4()); pairs = [('post_customers.json', P.customer()), ('post_deposits.json', P.deposit()), ('post_deposits.json', P.deposit(depositor_document=RandomGenerator.generate_cnpj())), ('post_withdrawals.json', P.withdrawal()), ('post_transfers.json', P.transfer(k)), ('post_savings.json', P.saving()), ('post_savings.json', P.saving(category_key=k)), ('post_redemptions.json', P.redemption()), ('post_redemptions.json', P.redemption(category_key=k)), ('post_categories.json', P.category()), ('post_point_applications.json', P.point_application()), ('post_day_closings.json', P.day_closing('2026-06-01')), ('post_blocks.json', P.block())]; [jsonschema.validate(p, json.load(open('src/schemas/' + f, encoding='utf-8'))) for f, p in pairs]; print(len(pairs), 'ok')"
  ```
  → `13 ok`
- `git grep -n -e SampleEntity -e sample_entity -- src/controllers src/repositories src/resources src/models src/schemas tests/utils/object_generator.py tests/utils/payload_generator.py tests/utils/request_generator.py` → nenhuma linha. Docstrings e comentários de utilitários herdados não são símbolos executáveis; não ampliar esta busca para eles.
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `82 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/utils/schema_handler.py
  tests/utils/__init__.py
  tests/utils/object_generator.py
  tests/utils/payload_generator.py
  ```
- `git log -1 --format=%B` → `test(utils): PayloadGenerator e ObjectGenerator do projeto`

**Pronto quando:**
- [ ] P1 e P2 dão a saída esperada.
- [ ] Nenhum `SampleEntity` nem `sample_entity` em `src/` e em `tests/utils/`.
- [ ] Suíte com `82 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/04-esqueleto`.

**Commit:** `test(utils): PayloadGenerator e ObjectGenerator do projeto`
**Pare se:**
- Alguma linha citada nas trocas de `src/utils/schema_handler.py` não for encontrada igual.
- A P2 terminar com `jsonschema.exceptions.ValidationError`: um corpo do `PayloadGenerator` não bate com o schema da fase 03; traga a saída inteira.
- O `git grep` de `SampleEntity` mostrar alguma linha.
- A suíte não terminar com `82 passed`.

---

### Passo 4.fim — Fechar a fase
**Branch:** fase/04-esqueleto · **Depende de:** 4.1 a 4.8
**Objetivo:** provar a fase com o banco recriado do zero e levá-la para a `main` com a tag `fase-04`.
**Decisões:** TIM-04 — git por fase · TIM-08 — git automático · ARQ-03 — SQL só com o banco vazio · ARQ-04 — sobe sem `.env`
**Arquivos:** nenhum. O passo não cria, não edita e não apaga arquivo.
**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/04-esqueleto`.
2. `git log --oneline -n 10` → tem as 8 mensagens dos passos 4.1 a 4.8, cada uma uma vez:
   ```
   feat(log): estado da requisição para o registro em request_log
   chore(config): token de administração, barreira e timeout do banco no ambiente
   feat(seguranca): token de administração nas rotas /internal
   feat(banco): lock_timeout e statement_timeout com resposta 503
   feat(log): uma linha em request_log por requisição
   feat(seguranca): barreira contra chute dos tokens internos
   test(utils): RequestGenerator com um método por rota
   test(utils): PayloadGenerator e ObjectGenerator do projeto
   ```
3. Recrie o banco do zero e suba tudo, um comando por vez:
   ```
   docker compose down -v
   docker compose up -d --build --wait
   ```
4. Rode a conferência T1 (passo 4.4) → `5s 5s`.
5. Rode a conferência C1 (passo 4.2) → a linha do **Verificar** do passo 4.2.
6. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `82 passed`.
7. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
8. `git status --short` → saída vazia.
9. Leve a fase para a `main`, um comando por vez:
   ```
   git switch main
   git merge --no-ff --no-edit -m "feat(esqueleto): fase 04 com middlewares de segurança e log, timeout do banco e funções de teste" fase/04-esqueleto
   git tag fase-04
   ```
10. Rode o **Verificar**.

**Testes:** nenhum teste novo. A suíte inteira (16 de integração + 66 unitários) roda com o banco recriado do zero (item 6).
**Verificar:**
- O `git status --short` antes do merge não mostra alterações.
- `git branch --show-current` → `main`.
- `git log -1 --format=%B` → `feat(esqueleto): fase 04 com middlewares de segurança e log, timeout do banco e funções de teste`.
- `git log -1 --format=%P` → dois hashes separados por um espaço (é um merge).
- `git tag --list fase-04` → `fase-04`.
- `git status --short` → saída vazia.

**Pronto quando:**
- [ ] T1 e C1 dão o esperado com o banco recriado do zero.
- [ ] Suíte com `82 passed`; lint sem saída.
- [ ] Merge `--no-ff` na `main` com a mensagem exata; tag `fase-04` criada localmente; merge local na `main`.

**Commit:** nenhum commit de passo. Mensagem do merge: `feat(esqueleto): fase 04 com middlewares de segurança e log, timeout do banco e funções de teste`
**Pare se:**
- Faltar uma das 8 mensagens do item 2.
- `docker compose up -d --build --wait` falhar: rode `docker compose logs --tail 100 db` e `docker compose logs --tail 100 api` e traga as duas saídas.
- T1 ou C1 derem outra saída.
- A suíte não terminar com `82 passed` ou o lint imprimir qualquer linha.
- O merge local der conflito (AGENTS.md, seção 8, item 9).

---

## Divergências encontradas

Seção para o Bruno; o agente não executa nada daqui.

| # | Onde | O que foi feito |
|---|---|---|
| 1 | `PLANO-fase-03.md`, passo 3.2, item 11: "`src/utils/schema_handler.py` (sai na fase 4)". O índice não põe esse arquivo em nenhum passo da fase 4. | Entrou no 4.8 (só docstring). Acrescentar `src/utils/schema_handler.py` (editar) aos arquivos do 4.8 no PLANO-00. |
| 2 | PLANO-00, passo 4.8: `tests/utils/__init__.py` (editar), sem nome novo para exportar. | A edição põe os imports na ordem de dependência; a lista exportada não muda. |
| 3 | TST-02 para a PRD-08: o 503 `QIT000503` não tem teste black box. Nenhuma rota segura trava por mais de 5 s, e o teste de integração só toca no banco pelo `DbUtils.rollback()`. | Prova por conferência no container (T1 a T5 do 4.4). A janela de 15 minutos da PRD-10 também fica sem teste (o teste teria de esperar); o limite exato, a soma `INTERNAL` + `ADMIN` e o "antes de conferir token" têm teste. |
| 4 | `ADMIN_TOKEN` nos testes de 4.3 e 4.6: o `tests.utils` só o exporta no 4.7. | Os dois arquivos de teste leem `ADMIN_TOKEN` do ambiente por conta própria, com o mesmo padrão. |
| 5 | `AGENTS.md`, seção 8, item 7 (teste novo que passa antes do código → PARE). | Cada função de teste nova tem pelo menos uma asserção que falha antes do código; o lado "passa" de cada `if` (TST-01) mora na mesma função, depois dela. |

## Nomes novos da fase 04 (registrar no PLANO-00)

Seção para o Bruno; o agente não executa nada daqui.

| Onde | Nomes |
|---|---|
| `src/middlewares/admin_token.py` | `is_internal_path(path)` |
| `src/middlewares/request_log_writer.py` | `ACCOUNT_KEY_IN_PATH`, `get_client_ip(request)`, `account_key_from_path(path)`, `save_request_log(request, request_state, status, error_code)` |
| `src/middlewares/auth_barrier.py` | `INTERNAL_AUTH_FAILURES` |
| `src/errors/handlers.py` | `is_database_timeout(exception)`; handler de `OperationalError` (timeout → 503 `QIT000503`; o resto → 500 `QIT000500`) |
| `src/database.py` | `DB_TIMEOUT_OPTIONS` |
| `RequestLogRepository` | `create(request_id, method, path, status, error_code, client_ip, account_key, auth_failure)`; `count_auth_failures(client_ip, auth_failures, window_minutes, account_key=None)` (o 5.9 usa o `account_key`) |
| `RequestState` | `account_key` é preenchido pelo `request_log_writer` antes da rota; a checagem de dono (5.5) grava `auth_failure = "ACCOUNT"` no mesmo objeto |
| `tests/utils/request_generator.py` | `_headers`, `_send`; parâmetros `internal_token` (todas) e `admin_token` (as 3 internas), com padrão; `account_token` obrigatório nas rotas "conta"; `params` nas 3 listas; valor `None` tira o cabeçalho |
| `PayloadGenerator` | assinaturas do passo 4.8; padrões: `deposit` 100000 centavos, os outros valores 1000; `saving` e `redemption` sem `category_key` quando ele é `None` |
| `ObjectGenerator` | `create_customer` devolve a `customer_key`; `create_account` e `create_funded_account` devolvem `{"customer_key", "account_key", "account_token"}` |
| Testes | pasta `tests/integration/security/`; caminhos `/nao_existe` e `/internal/nao_existe` (nunca viram rota) |
