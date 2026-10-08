> **Git local — Bruno, 08/10/2026:** durante a produção, branches, commits, merges e tags ficam locais. Não executar push, pull ou fetch nem exigir acesso ao GitHub. O envio completo será feito pelo Bruno somente no final, quando tudo estiver pronto. As verificações de commits e dependências são locais.

# PLANO — Fase 05 — cliente e conta

**Branch:** `fase/05-cliente-conta` · **Depende de:** fase 4
**Objetivo:** cadastrar e consultar cliente; abrir, consultar, bloquear, desbloquear e encerrar conta, com o token da conta e a barreira contra chute desse token.

Regras de execução: `AGENTS.md`. Nomes obrigatórios: `docs/plano/PLANO-00-indice.md`, `docs/plano/PLANO-fase-02.md` (tabelas, models, constantes dos models e ids dos tipos fixos), `docs/plano/PLANO-fase-03.md` (`docs/rotas.md`, catálogo de erros, schemas) e `docs/plano/PLANO-fase-04.md` (`RequestState`, `RequestLogRepository`, `RequestGenerator`, `PayloadGenerator`, `ObjectGenerator`). Um passo por vez, na ordem: 5.1 a 5.11 e, por último, 5.fim.

Contagem de testes da suíte: `82 passed` em 5.1 e 5.2; `94 passed` de 5.3 a 5.5; `99 passed` em 5.6; `104 passed` em 5.7; `109 passed` em 5.8; `114 passed` em 5.9; `122 passed` em 5.10; `129 passed` em 5.11 e no 5.fim (82 de antes + 47 novos, todos de integração).

Comandos usados nesta fase que não estão na seção 3 do `AGENTS.md`:

| Quero | Comando |
|---|---|
| Rodar uma linha de Python no `.venv` (a raiz do repositório no caminho de import) | `./.venv/Scripts/python.exe -c "<código>"` |
| Rodar uma linha de Python dentro do container da API | `docker compose exec -T api python -c "<código>"` |
| Rodar SQL no banco | `docker compose exec -T db psql -U bootcamp -d bootcamp -t -A -c "<SQL>"` |
| Requisição à mão, vendo status e cabeçalhos | `curl.exe -s -i <opções> <url>` |
| Procurar texto nos arquivos do Git | `git grep <opções> -- <pastas>` |

O `-T` desliga o terminal interativo, que o Git Bash não oferece. O `-t -A` do `psql` tira cabeçalho, rodapé e alinhamento: colunas separadas por `|`, valor nulo vazio. O `git grep` termina com código 1 quando não acha nada: nos itens em que o esperado é "nenhuma linha", esse código 1 sem linha impressa é o resultado certo.

Nas conferências com `./.venv/Scripts/python.exe -c`, as rotas de resposta 204 fazem o `tests/utils/requisition.py` imprimir a linha `Expecting value: line 1 column 1 (char 0)` (corpo vazio não é JSON). Essa linha não é erro; a saída esperada diz onde ela aparece.

Todas as saídas esperadas abaixo valem sem `.env` na raiz do repositório (ARQ-04). Existe um `.env`: PARE.

## Cobertura das regras desta fase (TST-02)

| Regra | O que fica vermelho se a regra deixar de valer |
|---|---|
| CLI-02 — CPF válido | `test_create_customer.py::test_refuses_invalid_document_number`, `test_checks_rules_in_order` |
| CLI-02, TST-03 — CPF único | `test_create_customer.py::test_refuses_duplicated_document_number`, `test_concurrent_same_document_number` |
| CLI-02 — e-mail único | `test_create_customer.py::test_refuses_duplicated_email`, `test_concurrent_same_email` |
| CLI-03 — 18 anos, sem máximo | `test_create_customer.py::test_refuses_underage`, `test_accepts_minimum_age_and_has_no_maximum` |
| R3 — data que não existe vira 422, nunca 500 | `test_create_customer.py::test_refuses_impossible_birthdate` |
| API-03 — schema fechado | `test_create_customer.py::test_refuses_body_out_of_schema`, `test_block_account.py::test_refuses_body_out_of_schema` |
| API-04 — `INTERNAL-TOKEN` | `test_requires_internal_token` em `test_create_customer.py`, `test_open_account.py` e `test_get_account.py` |
| CLI-01, TST-03 — conta só com cliente | `test_open_account.py::test_refuses_unknown_customer` e a conferência A2 do 5.6 |
| CLI-04 — uma conta não encerrada | `test_open_account.py::test_refuses_second_open_account`, `test_concurrent_openings`; `test_close_account.py::test_customer_opens_new_account_after_closing` |
| API-16 — token da conta | `test_open_account.py::test_opens_account` (formato, um por conta); `test_get_account.py::test_gets_new_account` (não volta); conferências K1 (5.4) e A1 (5.6): só o hash SHA-256 no banco |
| R8, API-09 — outro dono → 404 | `test_other_account_token_is_404` e `test_missing_or_wrong_token_is_404` em `test_get_account.py`, `test_get_customer.py` e `test_close_account.py` |
| API-17 — consultar cliente | `test_get_customer.py` (5 testes); `test_close_account.py::test_customer_opens_new_account_after_closing` |
| R5 — o `id` nunca sai | `assert_no_internal_id` em `test_create_customer.py`, `test_open_account.py`, `test_get_account.py` e `test_get_customer.py` |
| DAD-08 — centavos inteiros | `test_get_account.py::test_gets_new_account` (`balance` e `piggy_bank_balance` são `int` e valem 0) |
| CLI-05 — estados da conta | `test_block_account.py` (8 testes); `test_close_account.py` (7 testes) |
| CLI-06 — encerrar só conta ativa (parte do estado) | `test_close_account.py::test_closed_account_cannot_be_closed_again`, `test_blocked_account_cannot_be_closed` |
| CLI-09 — bloqueada não encerra; leitura liberada | `test_close_account.py::test_blocked_account_cannot_be_closed`; `test_block_account.py::test_blocked_account_still_reads` |
| PRD-07, PRD-13, API-13 — `ADMIN-TOKEN` nas rotas `/internal` | `test_block_account.py::test_requires_admin_token` |
| PRD-10 — barreira do token da conta, por conta + IP | `tests/integration/security/test_account_auth_barrier.py` (5 testes) |
| PRD-14 — `auth_failure = ACCOUNT` em `request_log` | conferências G1 e G2 do 5.7; a barreira do 5.9 só bloqueia se a falha estiver gravada |
| R4 — toda mudança de estado grava evento | conferências K1 (5.4), A1 (5.6), B1 (5.10) e E1 (5.11) |
| COF-14, COF-03 — o cofrinho e a categoria "economias" nascem com a conta | conferências K1 (5.4) e A1 (5.6) |

Dos "Testes previstos" do `09 - Plano de trabalho`, caem nesta fase:

| Cenário do 09 | Teste |
|---|---|
| Cliente: cadastro válido | `test_create_customer.py::test_creates_customer` |
| Cliente: CPF inválido | `test_create_customer.py::test_refuses_invalid_document_number` |
| Cliente: CPF já cadastrado (Aula 3) | `test_create_customer.py::test_refuses_duplicated_document_number` |
| Cliente: e-mail já cadastrado | `test_create_customer.py::test_refuses_duplicated_email` |
| Cliente: menor de idade · data que não existe | `test_refuses_underage` · `test_refuses_impossible_birthdate` |
| Cliente: campo a mais ou de tipo errado · obrigatório faltando | `test_create_customer.py::test_refuses_body_out_of_schema` |
| Cliente: consultar cliente que não existe | `test_get_customer.py::test_unknown_customer_is_404` |
| Cliente: sem `INTERNAL-TOKEN` | `test_create_customer.py::test_requires_internal_token` |
| Conta: abrir para cliente que existe; saldo 0 | `test_open_account.py::test_opens_account`; `test_get_account.py::test_gets_new_account` |
| Conta: abrir para cliente que não existe (Aula 3) | `test_open_account.py::test_refuses_unknown_customer` e conferência A2 |
| Conta: cliente em estado que não permite | não se aplica: o cliente não tem estado (CLI-05); o único 409 da abertura é o `QIT001009` (ver "Divergências", item 3) |
| Conta: segunda conta | `test_open_account.py::test_refuses_second_open_account` |
| Conta: conta de outro cliente pelo caminho do primeiro | `test_get_account.py::test_other_account_token_is_404` |
| Conta: saldo inicial 0, inteiro | `test_get_account.py::test_gets_new_account` |
| Transação: conta bloqueada ou encerrada → 409 | nesta fase, só o que a conta faz consigo: encerrar e bloquear (`test_close_account.py`, `test_block_account.py`); o dinheiro entra na fase 6 |

---

### Passo 5.1 — Cliente: repository e DTO
**Branch:** fase/05-cliente-conta · **Depende de:** fase 4 (merge `feat(esqueleto): fase 04 com middlewares de segurança e log, timeout do banco e funções de teste` e commit `docs(plano): roteiros auditados`, os dois na `main`; tag `fase-04`)
**Objetivo:** `CustomerRepository` (`create`, `get_by_key`, `get_by_id`, `get_by_document_number`, `get_by_email`) e `CustomerDTO` (`obj_to_dict`, `only_obj_key`).
**Decisões:** CLI-02 — dados do cliente · DAD-12 — UUID no repository · R5 — o `id` nunca sai · API-17 — o dono vê o CPF inteiro
**Arquivos:**
- `src/repositories/customer_repository.py` (criar): o conteúdo inteiro é:

```python
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
```

- `src/repositories/__init__.py` (editar): o conteúdo inteiro passa a ser:

```python
from repositories.request_log_repository import RequestLogRepository
from repositories.customer_repository import CustomerRepository
```

- `src/dtos/customer_dto.py` (criar): o conteúdo inteiro é:

```python
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
```

- `src/dtos/__init__.py` (editar): o conteúdo inteiro passa a ser:

```python
from dtos.customer_dto import CustomerDTO
```

**Passo a passo:**
1. Abra a fase (AGENTS.md, seção 7): `git status --short` → saída vazia; depois, um por vez:
   ```
   git switch main
   git switch -c fase/05-cliente-conta
   ```
2. `git log --oneline` → mostra `docs(plano): roteiros auditados` e `feat(esqueleto): fase 04 com middlewares de segurança e log, timeout do banco e funções de teste`. `git tag --list fase-04` → `fase-04`.
3. Crie `src/repositories/customer_repository.py` com o conteúdo do campo **Arquivos**.
4. Edite `src/repositories/__init__.py` com o conteúdo do campo **Arquivos**.
5. Crie `src/dtos/customer_dto.py` com o conteúdo do campo **Arquivos**.
6. Edite `src/dtos/__init__.py` com o conteúdo do campo **Arquivos**.
7. `docker compose up -d --build --wait` → termina sem erro.
8. Rode a conferência U1 do **Verificar**.
9. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `82 passed`.
10. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
11. Feche o passo (AGENTS.md, seção 7), um comando por vez:
    ```
    git add -- src/repositories/customer_repository.py src/repositories/__init__.py src/dtos/customer_dto.py src/dtos/__init__.py
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "feat(cliente): repository e DTO do cliente"
    git log -1 --format=%B
    ```

**Testes:** nenhum teste novo. O passo é de camada de baixo: quem prova o repository e o DTO por HTTP é a rota do 5.3. Aqui, a prova é a U1, que grava um cliente numa transação, lê de volta pelas quatro buscas, monta os dois DTOs e desfaz tudo (`rollback`): o banco fica como estava.
**Verificar:**
- U1 (um comando, numa linha só):
  ```
  docker compose exec -T api python -c "from datetime import date; from database import open_context; from repositories import CustomerRepository; from dtos import CustomerDTO; c = open_context(); s = c.get_or_create_session(); r = CustomerRepository(c); x = r.create('Ana Lima', '123.456.789-09', 'ana.conferencia.u1@example.com', date(1995, 4, 12)); s.flush(); d = CustomerDTO.obj_to_dict(x); print(sorted(d), d['document_number'], d['birthdate'], len(d['customer_key'])); print(r.get_by_key(x.customer_key) is x, r.get_by_id(x.id) is x, r.get_by_document_number('123.456.789-09') is x, r.get_by_email('ana.conferencia.u1@example.com') is x, CustomerDTO.only_obj_key(x) == {'customer_key': x.customer_key}); s.rollback()"
  ```
  → exatamente:
  ```
  ['birthdate', 'customer_key', 'document_number', 'email', 'name'] 123.456.789-09 1995-04-12 36
  True True True True True
  ```
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `82 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/dtos/__init__.py
  src/dtos/customer_dto.py
  src/repositories/__init__.py
  src/repositories/customer_repository.py
  ```
- `git log -1 --format=%B` → `feat(cliente): repository e DTO do cliente`

**Pronto quando:**
- [ ] Os dois arquivos novos e os dois `__init__.py` têm exatamente o conteúdo do campo **Arquivos**.
- [ ] A U1 dá as duas linhas esperadas.
- [ ] Suíte com `82 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/05-cliente-conta`.

**Commit:** `feat(cliente): repository e DTO do cliente`
**Pare se:**
- O item 2 não mostrar as duas mensagens ou a tag `fase-04`: a fase 04 não chegou à `main`.
- `docker compose up -d --build --wait` falhar: rode `docker compose logs --tail 100 api` e traga a saída.
- A U1 terminar com `Traceback` ou der outra saída depois de 3 tentativas de conferir os quatro arquivos contra o plano. Um `IntegrityError` com `customer_document_number_key` ou `customer_email_key` quer dizer que o CPF ou o e-mail da U1 já está no banco: rode `docker compose down -v`, `docker compose up -d --build --wait` e a U1 de novo.
- A suíte não terminar com `82 passed`.

---

### Passo 5.2 — Cliente: controller
**Branch:** fase/05-cliente-conta · **Depende de:** 5.1
**Objetivo:** `CustomerController.create`: CPF válido → CPF único → e-mail único → data que existe → idade mínima, antes de gravar; o `IntegrityError` do commit vira o 409 do campo repetido.
**Decisões:** CLI-02 — dados do cliente · CLI-03 — idade mínima · R3 — código de erro próprio, nunca 500 · MOV-19 — `IntegrityError` tratado, nunca 500 · ARQ-02 — commit por último
**Arquivos:**
- `src/controllers/customer_controller.py` (criar): o conteúdo inteiro é:

```python
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
```

- `src/controllers/__init__.py` (editar): o conteúdo inteiro passa a ser:

```python
from controllers.customer_controller import CustomerController
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/05-cliente-conta`; `git log --oneline` mostra `feat(cliente): repository e DTO do cliente`.
2. Crie `src/controllers/customer_controller.py` com o conteúdo do campo **Arquivos**.
3. Edite `src/controllers/__init__.py` com o conteúdo do campo **Arquivos**.
4. `docker compose up -d --build --wait` → termina sem erro.
5. Rode a conferência U2 do **Verificar**.
6. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `82 passed`.
7. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
8. Feche o passo (AGENTS.md, seção 7), um comando por vez:
   ```
   git add -- src/controllers/customer_controller.py src/controllers/__init__.py
   git diff --cached --name-only
   git diff --name-only
   git ls-files --others --exclude-standard
   git commit -m "feat(cliente): controller com as regras do cadastro"
   git log -1 --format=%B
   ```

**Testes:** nenhum teste novo. Cada regra do `create` ganha o seu teste black box no 5.3, que fica vermelho antes da rota. Aqui, a prova é a U2: o controller carrega, com a idade mínima do plano, e a API sobe com ele.
**Verificar:**
- U2 (um comando, numa linha só):
  ```
  docker compose exec -T api python -c "from controllers import CustomerController; from controllers.customer_controller import MINIMUM_AGE; print(CustomerController.__name__, MINIMUM_AGE, sorted(n for n in vars(CustomerController) if not n.startswith('__')))"
  ```
  → `CustomerController 18 ['_abc_impl', '_age_in_years', '_parse_birthdate', 'create']` (o `_abc_impl` vem do `ABCMeta` do `BaseController`)
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `82 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/controllers/__init__.py
  src/controllers/customer_controller.py
  ```
- `git log -1 --format=%B` → `feat(cliente): controller com as regras do cadastro`

**Pronto quando:**
- [ ] `src/controllers/customer_controller.py` e `src/controllers/__init__.py` têm exatamente o conteúdo do campo **Arquivos**.
- [ ] A U2 dá a linha esperada.
- [ ] Suíte com `82 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/05-cliente-conta`.

**Commit:** `feat(cliente): controller com as regras do cadastro`
**Pare se:**
- A U2 terminar com `ImportError` ou `Traceback` depois de 3 tentativas de conferir os dois arquivos contra o plano (um erro do catálogo com outro nome quer dizer que a fase 03 não é a do plano).
- A suíte não terminar com `82 passed`.

---

### Passo 5.3 — `POST /customers`
**Branch:** fase/05-cliente-conta · **Depende de:** 5.2
**Objetivo:** `CustomerResource.on_post` e a rota `POST /customers` (tokens: interno; schema `post_customers.json`): 201 com `{"customer_key"}`; erros 422 `QIT001003`, 409 `QIT001004`, 409 `QIT001005`, 422 `QIT001006`, 422 `QIT001007`, 400 `QIT000001`, 403 `QIT000002`.
**Decisões:** CLI-02 — dados do cliente · CLI-03 — idade mínima · TST-03 — CPF único · API-02 — status de sucesso · API-03 — schema fechado · API-04 — `INTERNAL-TOKEN` · API-10 — criação devolve a key · R5 — o `id` nunca sai · TST-01 — black box e TDD
**Arquivos:**
- `src/resources/customer.py` (criar): o conteúdo inteiro é:

```python
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
```

- `src/resources/__init__.py` (editar): o conteúdo inteiro passa a ser:

```python
from resources.health_check import HealthCheckResource
from resources.customer import CustomerResource
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
from resources import CustomerResource, HealthCheckResource
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
    # de dentro do resource (API-02). Tokens, corpos e erros de cada uma:
    # docs/rotas.md.
    # ────────────────────────────────────────────────────────────────
    health_check_resource = HealthCheckResource()
    customer_resource = CustomerResource()

    application.add_api_route("/", health_check_resource.on_get_home, methods=["GET"])
    application.add_api_route(
        "/health_check",
        health_check_resource.on_get_health_check,
        methods=["GET"]
    )

    # Cliente
    application.add_api_route("/customers", customer_resource.on_post, methods=["POST"])

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

- `tests/integration/customers/test_create_customer.py` (criar; a pasta `tests/integration/customers/` é nova e fica sem `__init__.py`, como `tests/integration/`): o conteúdo inteiro é:

```python
"""Cadastro de cliente: POST /customers (CLI-02, CLI-03, TST-03, API-03, API-04).

O controller confere, nesta ordem: CPF válido (422 QIT001003), CPF único
(409 QIT001004), e-mail único (409 QIT001005), data que existe (422
QIT001007) e idade mínima de 18 anos (422 QIT001006). O formato de cada
campo é do schema post_customers.json (400 QIT000001).
"""

import re
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta

from tests.utils import DbUtils, PayloadGenerator, RandomGenerator, RequestGenerator


UUID_V4 = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")
PARALLEL_REQUESTS = 8
INVALID_CPF = "111.222.333-44"
DUPLICATED_DOCUMENT_TRANSLATION = "Já existe um cadastro com este CPF."
UNDERAGE_TRANSLATION = "É preciso ter pelo menos 18 anos."


def birthdate_for_age(age_in_years: int) -> str:
    """A data de nascimento de quem faz essa idade hoje; num 29/02, a de 28/02."""
    today = date.today()

    if today.month == 2 and today.day == 29:
        return date(today.year - age_in_years, 2, 28).isoformat()

    return date(today.year - age_in_years, today.month, today.day).isoformat()


def birthdate_turning_age_in_two_days(age_in_years: int) -> str:
    """A data de nascimento de quem faz essa idade daqui a dois dias.

    Dois dias, e não um: o container da API roda em UTC e pode estar um
    dia à frente da máquina que roda os testes. Um 29/02 vira 01/03.
    """
    birthday = date.today() + timedelta(days=2)

    if birthday.month == 2 and birthday.day == 29:
        birthday = birthday + timedelta(days=1)

    return date(birthday.year - age_in_years, birthday.month, birthday.day).isoformat()


def assert_no_internal_id(body: dict) -> None:
    """R5: nenhum campo id nem terminado em _id na resposta."""
    for field in body:
        assert field != "id", field
        assert not field.endswith("_id"), field


def post_customers_in_parallel(payloads: list) -> list:
    with ThreadPoolExecutor(max_workers=len(payloads)) as executor:
        return list(executor.map(RequestGenerator.POST_customer, payloads))


def assert_one_created_and_the_rest_refused(results: list, error_code: str) -> None:
    statuses = sorted(status for status, _response in results)
    assert statuses == [201] + [409] * (len(results) - 1), results

    codes = [response["code"] for status, response in results if status == 409]
    assert codes == [error_code] * (len(results) - 1), codes


class TestCreateCustomer:
    def test_creates_customer(self):
        payload = PayloadGenerator.customer()

        status, response = RequestGenerator.POST_customer(payload)

        assert status == 201, response
        assert list(response) == ["customer_key"]
        assert UUID_V4.match(response["customer_key"])
        assert_no_internal_id(response)

    def test_refuses_invalid_document_number(self):
        for document_number in [INVALID_CPF, "111.111.111-11"]:
            payload = PayloadGenerator.customer(document_number=document_number)

            status, response = RequestGenerator.POST_customer(payload)

            assert status == 422, (document_number, response)
            assert response["code"] == "QIT001003"

    def test_refuses_duplicated_document_number(self):
        first = PayloadGenerator.customer()
        status, response = RequestGenerator.POST_customer(first)
        assert status == 201, response

        second = PayloadGenerator.customer(document_number=first["document_number"])
        status, response = RequestGenerator.POST_customer(second)

        assert status == 409, response
        assert response["code"] == "QIT001004"
        assert response["translation"] == DUPLICATED_DOCUMENT_TRANSLATION

    def test_refuses_duplicated_email(self):
        first = PayloadGenerator.customer()
        status, response = RequestGenerator.POST_customer(first)
        assert status == 201, response

        second = PayloadGenerator.customer(email=first["email"])
        status, response = RequestGenerator.POST_customer(second)

        assert status == 409, response
        assert response["code"] == "QIT001005"

    def test_refuses_underage(self):
        for birthdate in [birthdate_for_age(17), birthdate_turning_age_in_two_days(18)]:
            payload = PayloadGenerator.customer(birthdate=birthdate)

            status, response = RequestGenerator.POST_customer(payload)

            assert status == 422, (birthdate, response)
            assert response["code"] == "QIT001006"
            assert response["translation"] == UNDERAGE_TRANSLATION

    def test_accepts_minimum_age_and_has_no_maximum(self):
        for birthdate in [birthdate_for_age(18), "1900-01-01"]:
            payload = PayloadGenerator.customer(birthdate=birthdate)

            status, response = RequestGenerator.POST_customer(payload)

            assert status == 201, (birthdate, response)

    def test_refuses_impossible_birthdate(self):
        for birthdate in ["2025-02-30", "9999-99-99"]:
            payload = PayloadGenerator.customer(birthdate=birthdate)

            status, response = RequestGenerator.POST_customer(payload)

            assert status == 422, (birthdate, response)
            assert response["code"] == "QIT001007"

    def test_checks_rules_in_order(self):
        existing = PayloadGenerator.customer()
        status, response = RequestGenerator.POST_customer(existing)
        assert status == 201, response

        underage = birthdate_for_age(17)
        cases = [
            (PayloadGenerator.customer(document_number=INVALID_CPF, email=existing["email"], birthdate=underage), "QIT001003"),
            (
                PayloadGenerator.customer(document_number=existing["document_number"], email=existing["email"], birthdate=underage),
                "QIT001004",
            ),
            (PayloadGenerator.customer(email=existing["email"], birthdate="2025-02-30"), "QIT001005"),
        ]

        for payload, error_code in cases:
            status, response = RequestGenerator.POST_customer(payload)

            assert response["code"] == error_code, (payload, response)

    def test_refuses_body_out_of_schema(self):
        payloads = []

        payload = PayloadGenerator.customer()
        payload["extra"] = 1
        payloads.append(payload)

        for field in ["name", "document_number", "email", "birthdate"]:
            payload = PayloadGenerator.customer()
            del payload[field]
            payloads.append(payload)

        wrong_values = [
            ("name", 123),
            ("name", ""),
            ("document_number", "12345678909"),
            ("email", "ana.lima"),
            ("birthdate", "17/05/1990"),
        ]

        for field, wrong_value in wrong_values:
            payload = PayloadGenerator.customer()
            payload[field] = wrong_value
            payloads.append(payload)

        payloads.append({})

        for payload in payloads:
            status, response = RequestGenerator.POST_customer(payload)

            assert status == 400, (payload, response)
            assert response["code"] == "QIT000001"

    def test_requires_internal_token(self):
        DbUtils.rollback()

        status, response = RequestGenerator.POST_customer(PayloadGenerator.customer())
        assert status == 201, response

        for internal_token in [None, "token_errado"]:
            status, response = RequestGenerator.POST_customer(PayloadGenerator.customer(), internal_token=internal_token)

            assert status == 403, (internal_token, response)
            assert response["code"] == "QIT000002"

    def test_concurrent_same_document_number(self):
        document_number = RandomGenerator.generate_cpf()
        payloads = [PayloadGenerator.customer(document_number=document_number) for _ in range(PARALLEL_REQUESTS)]

        results = post_customers_in_parallel(payloads)

        assert_one_created_and_the_rest_refused(results, "QIT001004")

    def test_concurrent_same_email(self):
        email = PayloadGenerator.customer()["email"]
        payloads = [PayloadGenerator.customer(email=email) for _ in range(PARALLEL_REQUESTS)]

        results = post_customers_in_parallel(payloads)

        assert_one_created_and_the_rest_refused(results, "QIT001005")
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/05-cliente-conta`; `git log --oneline` mostra `feat(cliente): controller com as regras do cadastro`.
2. Crie `tests/integration/customers/test_create_customer.py` com o conteúdo do campo **Arquivos**.
3. `docker compose up -d --build --wait`.
4. `./.venv/Scripts/python.exe -m pytest -v tests/integration/customers/test_create_customer.py` → a última linha tem `12 failed` e não tem `passed`. Os 12 falham por asserção de status: hoje `POST /customers` responde 404 `QIT000404`.
5. Crie `src/resources/customer.py` com o conteúdo do campo **Arquivos**.
6. Edite `src/resources/__init__.py` com o conteúdo do campo **Arquivos**.
7. Edite `src/app.py` com o conteúdo do campo **Arquivos**.
8. `docker compose up -d --build --wait`.
9. `./.venv/Scripts/python.exe -m pytest -v tests/integration/customers/test_create_customer.py` → a última linha tem `12 passed`.
10. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `94 passed`.
11. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
12. Feche o passo (AGENTS.md, seção 7), um comando por vez:
    ```
    git add -- src/resources/customer.py src/resources/__init__.py src/app.py tests/integration/customers/test_create_customer.py
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "feat(cliente): rota de cadastro de cliente"
    git log -1 --format=%B
    ```

**Testes:** `tests/integration/customers/test_create_customer.py`. Efeito no banco: cada 201 grava uma linha em `customer`; nenhuma recusa grava cliente (só a linha de `request_log`).

| Função de teste | Entrada | Esperado |
|---|---|---|
| `test_creates_customer` | `POST /customers` com `PayloadGenerator.customer()` | 201; o corpo tem só `customer_key`, UUID v4 em minúsculas; nenhum campo `id` nem `*_id` |
| `test_refuses_invalid_document_number` | CPF `111.222.333-44` (dígito errado) e `111.111.111-11` (dígitos iguais) | 422 `QIT001003` nos dois |
| `test_refuses_duplicated_document_number` | cliente cadastrado; outro com o mesmo CPF e outro e-mail | o primeiro 201; o segundo 409 `QIT001004`, `translation` = `Já existe um cadastro com este CPF.` |
| `test_refuses_duplicated_email` | cliente cadastrado; outro com o mesmo e-mail e outro CPF | o primeiro 201; o segundo 409 `QIT001005` |
| `test_refuses_underage` | nascido há exatamente 17 anos; e quem faz 18 daqui a 2 dias | 422 `QIT001006`, `translation` = `É preciso ter pelo menos 18 anos.` nos dois |
| `test_accepts_minimum_age_and_has_no_maximum` | quem faz 18 hoje; nascido em `1900-01-01` | 201 nos dois (CLI-03: sem idade máxima) |
| `test_refuses_impossible_birthdate` | `2025-02-30` e `9999-99-99` (passam no `pattern`) | 422 `QIT001007` nos dois, nunca 500 |
| `test_checks_rules_in_order` | cliente cadastrado; (a) CPF inválido + e-mail repetido + 17 anos; (b) CPF repetido + e-mail repetido + 17 anos; (c) e-mail repetido + data `2025-02-30` | (a) `QIT001003`; (b) `QIT001004`; (c) `QIT001005`: a ordem do controller |
| `test_refuses_body_out_of_schema` | campo `extra`; cada um dos 4 campos faltando; `name` = `123`; `name` vazio; CPF sem pontuação; e-mail sem `@`; data `17/05/1990`; corpo `{}` | 400 `QIT000001` em todos (12 corpos) |
| `test_requires_internal_token` | começa com `DbUtils.rollback()`; cadastro com o token; depois sem `INTERNAL-TOKEN` e com `INTERNAL-TOKEN: token_errado` | 201; depois 403 `QIT000002` nos dois. Banco: 2 linhas de falha `INTERNAL` em `request_log` |
| `test_concurrent_same_document_number` | 8 cadastros ao mesmo tempo, mesmo CPF, e-mails diferentes | exatamente um 201 e sete 409 `QIT001004`; nenhum 500 (o `IntegrityError` do commit vira 409) |
| `test_concurrent_same_email` | 8 cadastros ao mesmo tempo, mesmo e-mail, CPFs diferentes | exatamente um 201 e sete 409 `QIT001005` |

**Verificar:**
- `./.venv/Scripts/python.exe -m pytest -v tests/integration/customers/test_create_customer.py` → `12 passed`.
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `94 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/app.py
  src/resources/__init__.py
  src/resources/customer.py
  tests/integration/customers/test_create_customer.py
  ```
- `git log -1 --format=%B` → `feat(cliente): rota de cadastro de cliente`

**Pronto quando:**
- [ ] Os 12 testes falharam antes do código (item 4) e passam depois (item 9).
- [ ] Suíte com `94 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/05-cliente-conta`.

**Commit:** `feat(cliente): rota de cadastro de cliente`
**Pare se:**
- O item 4 não terminar com `12 failed`, ou alguma falha for `SyntaxError`, `NameError`, `IndentationError` ou `ImportError` depois de 3 tentativas de conferir o arquivo de teste contra o plano.
- Um teste receber 500 (`QIT000500`): rode `docker compose logs --tail 100 api` e traga a saída.
- `test_concurrent_same_document_number` ou `test_concurrent_same_email` falhar em uma de três rodadas seguidas do item 9.
- A suíte não terminar com `94 passed`.

---

### Passo 5.4 — Conta: token e repositories
**Branch:** fase/05-cliente-conta · **Depende de:** 5.3
**Objetivo:** o token da conta (`generate_account_token`, `hash_account_token`, `account_token_matches`); `AccountRepository` (abre a conta e o cofrinho, grava só o hash do token, busca, trava e muda o estado com evento); `CategoryRepository.create_default` e `get_default` ("economias", nascida com o cofrinho).
**Decisões:** API-16 — token da conta · COF-14 — cofrinho é conta · COF-01 — um cofrinho por conta · COF-03 — categoria padrão · CLI-04 — uma conta aberta · CLI-05 — estados da conta · DAD-09 — contas do sistema · DAD-12 — UUID no repository · GAM-13 — ranque padrão a partir de R$ 0 · MOV-05, MOV-11 — trava na ordem do `id` · R4 — append-only
**Arquivos:**
- `src/utils/account_token.py` (criar): o conteúdo inteiro é:

```python
import hashlib
import hmac
import secrets


# 32 bytes aleatórios viram 43 caracteres de letras, números, - e _
# (docs/rotas.md, "Formatos").
ACCOUNT_TOKEN_BYTES = 32


def generate_account_token() -> str:
    """Um token novo para uma conta nova (API-16). Sai uma vez só, na resposta 201."""
    return secrets.token_urlsafe(ACCOUNT_TOKEN_BYTES)


def hash_account_token(account_token: str) -> str:
    """O SHA-256 do token, em 64 caracteres hexadecimais: é só isto que o banco guarda (API-16)."""
    return hashlib.sha256(account_token.encode("utf-8")).hexdigest()


def account_token_matches(account_token, token_hash) -> bool:
    """True quando o token recebido é o da conta.

    Token que falta (None) ou conta sem hash (cofrinho, contas do
    sistema) nunca bate. A comparação de tempo constante
    (hmac.compare_digest) não deixa o tempo da resposta contar quantos
    caracteres acertaram.
    """
    if account_token is None or token_hash is None:
        return False

    return hmac.compare_digest(hash_account_token(account_token), token_hash)
```

- `src/repositories/account_repository.py` (criar): o conteúdo inteiro é:

```python
from datetime import datetime
from uuid import uuid4

from database import Context
from models import Account, AccountStatus, AccountStatusEvent, AccountType, BlockReason, Customer, PiggyRank


class AccountRepository:
    """Consulta e grava contas: de cliente, cofrinho e do sistema (COF-14, DAD-09).

    Nenhuma regra de negócio mora aqui. A key nasce aqui, com uuid4
    (DAD-12). Toda mudança de estado grava o evento na mesma transação
    (CLI-05, R4).
    """

    def __init__(self, context: Context) -> None:
        self.session = context.db_session

    def create_customer_account(self, customer: Customer, token_hash: str) -> Account:
        """Abre a conta do cliente, o cofrinho ligado a ela e o evento ACTIVE da conta.

        A conta nasce ACTIVE, com saldo 0, só o hash do token (API-16) e o
        ranque DEFAULT, o atual e o que rende (GAM-13). O cofrinho é outra
        linha de account, do tipo PIGGY_BANK, ACTIVE, do mesmo cliente,
        com parent_account_id = id da conta, saldo 0 e sem token (COF-14).

        O primeiro flush dá o id da conta ao cofrinho e ao evento. Uma
        segunda conta não encerrada do mesmo cliente é barrada aqui, pelo
        índice account_one_open_per_customer_idx, como IntegrityError.
        """
        active = self._get_fixed_type(AccountStatus, AccountStatus.ACTIVE)
        default_rank = self._get_fixed_type(PiggyRank, PiggyRank.DEFAULT)

        account = Account()
        account.account_key = str(uuid4())
        account.account_type = self._get_fixed_type(AccountType, AccountType.CUSTOMER)
        account.status = active
        account.customer_id = customer.id
        account.balance = 0
        account.token_hash = token_hash
        account.rank = default_rank
        account.yield_rank = default_rank

        self.session.add(account)
        self.session.flush()

        piggy_bank = Account()
        piggy_bank.account_key = str(uuid4())
        piggy_bank.account_type = self._get_fixed_type(AccountType, AccountType.PIGGY_BANK)
        piggy_bank.status = active
        piggy_bank.customer_id = customer.id
        piggy_bank.parent_account_id = account.id
        piggy_bank.balance = 0

        self.session.add(piggy_bank)
        self._add_status_event(account, active, None, None)
        self.session.flush()

        return account

    def get_by_key(self, account_key: str) -> Account:
        """A conta com esta key, de qualquer tipo; None quando não existe."""
        return self.session.query(Account).filter(Account.account_key == account_key).first()

    def get_customer_account(self, account_key: str) -> Account:
        """A conta de cliente com esta key; None para key que não existe, cofrinho ou conta do sistema."""
        account = self.get_by_key(account_key)

        if account is None or account.account_type.enumerator != AccountType.CUSTOMER:
            return None

        return account

    def get_open_account_by_customer(self, customer: Customer) -> Account:
        """A conta de cliente não encerrada (ACTIVE ou BLOCKED) do cliente; None quando ele não tem (CLI-04)."""
        return (
            self.session.query(Account)
            .join(Account.account_type)
            .join(Account.status)
            .filter(
                Account.customer_id == customer.id,
                AccountType.enumerator == AccountType.CUSTOMER,
                AccountStatus.enumerator != AccountStatus.CLOSED,
            )
            .first()
        )

    def get_piggy_bank(self, account: Account) -> Account:
        """O cofrinho da conta: a conta cujo parent_account_id é o id dela (COF-14)."""
        return self.session.query(Account).filter(Account.parent_account_id == account.id).first()

    def get_system_account(self, account_type_enumerator: str) -> Account:
        """A conta BANK ou a OUTSIDE_WORLD, criadas pelo database.sql (DAD-09)."""
        return (
            self.session.query(Account)
            .join(Account.account_type)
            .filter(AccountType.enumerator == account_type_enumerator)
            .one()
        )

    def lock_accounts(self, accounts: list) -> list:
        """Trava as linhas das contas com SELECT ... FOR UPDATE, na ordem do id, menor primeiro (MOV-05, MOV-11).

        Devolve as mesmas contas, na ordem do id, com os valores relidos do
        banco depois da trava (populate_existing): o que outra transação
        gravou antes de soltar a trava aparece aqui.
        """
        account_ids = sorted(account.id for account in accounts)

        return (
            self.session.query(Account)
            .filter(Account.id.in_(account_ids))
            .order_by(Account.id)
            .with_for_update()
            .populate_existing()
            .all()
        )

    def change_status(
        self,
        account: Account,
        status_enumerator: str,
        source: str = None,
        block_reason_enumerator: str = None,
    ) -> None:
        """Muda o estado da conta e grava o evento, na mesma transação (CLI-05, R4).

        `source`: AccountStatusEvent.MANUAL (rota interna) ou
        AccountStatusEvent.AUTOMATIC (bloqueio automático, passo 6.9);
        None quando quem muda é o dono (encerrar). `block_reason_enumerator`
        só no bloqueio.
        """
        status = self._get_fixed_type(AccountStatus, status_enumerator)

        block_reason = None
        if block_reason_enumerator is not None:
            block_reason = self._get_fixed_type(BlockReason, block_reason_enumerator)

        account.status = status
        self._add_status_event(account, status, source, block_reason)

    def _add_status_event(self, account: Account, status: AccountStatus, source: str, block_reason: BlockReason) -> None:
        status_event = AccountStatusEvent()
        status_event.account_id = account.id
        status_event.status = status
        status_event.block_reason = block_reason
        status_event.source = source
        status_event.event_datetime = datetime.now()

        self.session.add(status_event)

    def _get_fixed_type(self, model, enumerator: str):
        """A linha de uma tabela de tipos fixos (account_type, account_status, block_reason, piggy_rank) pelo enumerator."""
        return self.session.query(model).filter(model.enumerator == enumerator).one()
```

- `src/repositories/category_repository.py` (criar): o conteúdo inteiro é:

```python
from datetime import datetime
from uuid import uuid4

from database import Context
from models import Account, Category, CategoryStatus, CategoryStatusEvent


# COF-03: o nome da categoria padrão, que nasce com o cofrinho.
DEFAULT_CATEGORY_NAME = "economias"


class CategoryRepository:
    """Consulta e grava as categorias do cofrinho (COF-03). Nenhuma regra de negócio mora aqui."""

    def __init__(self, context: Context) -> None:
        self.session = context.db_session

    def create_default(self, piggy_bank: Account) -> Category:
        """Cria a categoria "economias" do cofrinho, ACTIVE, e grava o evento do estado (R4).

        O flush dá o id da categoria ao evento. O índice
        category_one_default_idx garante uma padrão por cofrinho.
        """
        active = self.session.query(CategoryStatus).filter(CategoryStatus.enumerator == CategoryStatus.ACTIVE).one()

        category = Category()
        category.category_key = str(uuid4())
        category.account_id = piggy_bank.id
        category.status = active
        category.name = DEFAULT_CATEGORY_NAME
        category.is_default = True

        self.session.add(category)
        self.session.flush()

        status_event = CategoryStatusEvent()
        status_event.category_id = category.id
        status_event.status = active
        status_event.event_datetime = datetime.now()

        self.session.add(status_event)

        return category

    def get_default(self, piggy_bank: Account) -> Category:
        """A categoria "economias" do cofrinho."""
        return (
            self.session.query(Category)
            .filter(Category.account_id == piggy_bank.id, Category.is_default.is_(True))
            .first()
        )
```

- `src/repositories/__init__.py` (editar): o conteúdo inteiro passa a ser:

```python
from repositories.request_log_repository import RequestLogRepository
from repositories.customer_repository import CustomerRepository
from repositories.account_repository import AccountRepository
from repositories.category_repository import CategoryRepository
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/05-cliente-conta`; `git log --oneline` mostra `feat(cliente): rota de cadastro de cliente`.
2. Crie `src/utils/account_token.py` com o conteúdo do campo **Arquivos** (a pasta `src/utils/` não tem `__init__.py`, e continua sem).
3. Crie `src/repositories/account_repository.py` com o conteúdo do campo **Arquivos**.
4. Crie `src/repositories/category_repository.py` com o conteúdo do campo **Arquivos**.
5. Edite `src/repositories/__init__.py` com o conteúdo do campo **Arquivos**.
6. `docker compose up -d --build --wait` → termina sem erro.
7. Rode a conferência K1 do **Verificar**.
8. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `94 passed`.
9. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
10. Feche o passo (AGENTS.md, seção 7), um comando por vez:
    ```
    git add -- src/utils/account_token.py src/repositories/account_repository.py src/repositories/category_repository.py src/repositories/__init__.py
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "feat(conta): token da conta e repositories da conta e da categoria padrão"
    git log -1 --format=%B
    ```

**Testes:** nenhum teste novo. O passo é de camada de baixo; as rotas dos passos 5.6 a 5.11 usam estas peças por HTTP. Aqui, a prova é a K1: numa transação só, cadastra um cliente, abre a conta, confere o token, o cofrinho, a categoria padrão, as buscas, a trava e as mudanças de estado, e desfaz tudo (`rollback`).
**Verificar:**
- K1 (um comando, numa linha só):
  ```
  docker compose exec -T api python -c "from datetime import date; from database import open_context; from repositories import AccountRepository, CategoryRepository, CustomerRepository; from utils.account_token import account_token_matches, generate_account_token, hash_account_token; c = open_context(); s = c.get_or_create_session(); t = generate_account_token(); h = hash_account_token(t); x = CustomerRepository(c).create('Ana Lima', '529.982.247-25', 'ana.conferencia.k1@example.com', date(1995, 4, 12)); s.flush(); r = AccountRepository(c); a = r.create_customer_account(x, h); p = r.get_piggy_bank(a); g = CategoryRepository(c).create_default(p); print(len(t), len(h), account_token_matches(t, h), account_token_matches('outro', h), account_token_matches(None, h), t in h); print(a.account_type.enumerator, a.status.enumerator, a.balance, a.token_hash == h, a.rank.enumerator, a.yield_rank.enumerator); print(p.account_type.enumerator, p.status.enumerator, p.parent_account_id == a.id, p.customer_id == x.id, p.balance, p.token_hash); print(g.name, g.is_default, g.status.enumerator, CategoryRepository(c).get_default(p) is g); print(r.get_customer_account(a.account_key) is a, r.get_customer_account(p.account_key), r.get_by_key(p.account_key) is p, r.get_open_account_by_customer(x) is a, r.get_system_account('BANK').account_type.enumerator, r.get_system_account('OUTSIDE_WORLD').balance); print(r.lock_accounts([a]) == [a]); r.change_status(a, 'BLOCKED', 'MANUAL', 'JUDICIAL_ORDER'); s.flush(); print(a.status.enumerator, r.get_open_account_by_customer(x) is a); r.change_status(a, 'CLOSED'); s.flush(); print(a.status.enumerator, r.get_open_account_by_customer(x)); s.rollback()"
  ```
  → exatamente:
  ```
  43 64 True False False False
  CUSTOMER ACTIVE 0 True DEFAULT DEFAULT
  PIGGY_BANK ACTIVE True True 0 None
  economias True ACTIVE True
  True None True True BANK None
  True
  BLOCKED True
  CLOSED None
  ```
- `git grep -n -e "token_urlsafe" -e "sha256" -- src` → exatamente as duas linhas de `src/utils/account_token.py` (o token só nasce e só vira hash ali).
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `94 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/repositories/__init__.py
  src/repositories/account_repository.py
  src/repositories/category_repository.py
  src/utils/account_token.py
  ```
- `git log -1 --format=%B` → `feat(conta): token da conta e repositories da conta e da categoria padrão`

**Pronto quando:**
- [ ] Os três arquivos novos e o `src/repositories/__init__.py` têm exatamente o conteúdo do campo **Arquivos**.
- [ ] A K1 dá as 8 linhas esperadas.
- [ ] Suíte com `94 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/05-cliente-conta`.

**Commit:** `feat(conta): token da conta e repositories da conta e da categoria padrão`
**Pare se:**
- A K1 terminar com `Traceback` ou der outra saída depois de 3 tentativas de conferir os quatro arquivos contra o plano. Um `IntegrityError` com `customer_document_number_key` ou `customer_email_key` quer dizer que o CPF ou o e-mail da K1 já está no banco: rode `docker compose down -v`, `docker compose up -d --build --wait` e a K1 de novo.
- O `git grep` mostrar `token_urlsafe` ou `sha256` em outro arquivo.
- A suíte não terminar com `94 passed`.

---

### Passo 5.5 — Conta: DTO, controller e checagem de dono
**Branch:** fase/05-cliente-conta · **Depende de:** 5.4
**Objetivo:** `AccountDTO`; `AccountController.open_account` e `get_account`; `BaseController.get_owned_account` (conta de cliente cuja key e token batem, ou 404 `QIT001010` com `auth_failure = "ACCOUNT"`) e `BaseController.mark_account_auth_failure`.
**Decisões:** API-08 — rotas aninhadas, uma checagem de dono · API-09 — dono pelo token da conta · R8 — outro dono → 404 · API-16 — token da conta · CLI-01 — conta só com cliente · CLI-04 — uma conta aberta · PRD-14 — `auth_failure` · R3, MOV-19 — `IntegrityError` vira 409 · R5 — o `id` nunca sai
**Arquivos:**
- `src/dtos/account_dto.py` (criar): o conteúdo inteiro é:

```python
from models import Account, Customer


class AccountDTO:
    """A conta que a API devolve: keys públicas, nunca id nem token_hash (R5, API-16)."""

    @staticmethod
    def obj_to_dict(account: Account, customer: Customer, piggy_bank: Account) -> dict:
        """A conta para o dono (GET /accounts/{account_key}): saldo e saldo total do cofrinho, em centavos (DAD-08)."""
        return {
            "account_key": account.account_key,
            "customer_key": customer.customer_key,
            "status": account.status.enumerator,
            "balance": account.balance,
            "piggy_bank_balance": piggy_bank.balance,
            "created_at": account.created_at.isoformat(),
        }

    @staticmethod
    def open_account_to_dict(account: Account, account_token: str) -> dict:
        """A resposta da abertura: a key e o token, que só sai aqui, uma vez (API-16)."""
        return {
            "account_key": account.account_key,
            "account_token": account_token,
        }
```

- `src/dtos/__init__.py` (editar): o conteúdo inteiro passa a ser:

```python
from dtos.customer_dto import CustomerDTO
from dtos.account_dto import AccountDTO
```

- `src/controllers/base_controller.py` (editar): o conteúdo inteiro passa a ser:

```python
from abc import ABCMeta

from database import get_context
from errors import AccountNotFound
from models import Account, RequestLog
from repositories import AccountRepository
from utils.account_token import account_token_matches
from utils.logger import get_logger
from utils.request_context import get_request_state


class BaseController(metaclass=ABCMeta):
    """O que todo controller tem em comum: a conexão com o banco, o log e a checagem de dono.

    Nada chega por parâmetro: o controller pega o CONTEXTO da requisição
    em que está rodando. Quem preparou esse contexto foi o middleware.

    Guardar o `self.context`, e não só a sessão, é o que permite o
    repository receber `context` em vez de `db`: o contexto é a coisa que
    viaja entre as camadas, e a sessão é só o que ele carrega hoje.

    É aqui que a sessão nasce, no `get_or_create_session` — construir um
    controller é a mesma coisa que dizer "eu uso banco".
    """

    def __init__(self, class_name: str) -> None:
        self.context = get_context()
        self.session = self.context.get_or_create_session()
        self.logger = get_logger(class_name)

    def mark_account_auth_failure(self) -> None:
        """Anota no estado da requisição que o token da conta falhou (PRD-14).

        O middleware request_log_writer grava `auth_failure = ACCOUNT` em
        request_log, e a barreira da PRD-10 conta essas linhas (passo 5.9).
        """
        request_state = get_request_state()
        if request_state is not None:
            request_state.auth_failure = RequestLog.ACCOUNT

    def get_owned_account(self, account_key: str, account_token: str) -> Account:
        """A conta de cliente da URL, se o ACCOUNT-TOKEN é o dela (API-08, API-09).

        Conta que não existe, que não é de cliente (cofrinho, contas do
        sistema), token que falta e token de outra conta respondem o mesmo
        404 QIT001010, nunca 403 (R8): quem não é o dono não descobre se a
        conta existe. Toda recusa daqui anota a falha do token da conta.
        """
        account = AccountRepository(self.context).get_customer_account(account_key)

        if account is None or not account_token_matches(account_token, account.token_hash):
            self.mark_account_auth_failure()
            raise AccountNotFound(account_key)

        return account
```

- `src/controllers/account_controller.py` (criar): o conteúdo inteiro é:

```python
from sqlalchemy.exc import IntegrityError

from controllers.base_controller import BaseController
from dtos import AccountDTO
from errors import CustomerAlreadyHasAccount, CustomerNotFound
from repositories import AccountRepository, CategoryRepository, CustomerRepository
from utils.account_token import generate_account_token, hash_account_token


class AccountController(BaseController):
    """As regras da conta (CLI-01, CLI-04, CLI-05, API-16)."""

    def __init__(self) -> None:
        super().__init__(__name__)
        self.account_repository = AccountRepository(self.context)
        self.category_repository = CategoryRepository(self.context)
        self.customer_repository = CustomerRepository(self.context)

    def open_account(self, customer_key: str) -> dict:
        """Abre a conta do cliente. As regras, nesta ordem, antes de gravar:

        1. o cliente existe (404 QIT001008; nenhuma conta é criada, CLI-01);
        2. o cliente não tem conta não encerrada (409 QIT001009, CLI-04).

        Depois: a conta ACTIVE com saldo 0 e o hash do token, o cofrinho e
        a categoria "economias" (COF-14, COF-03), numa transação só. Duas
        aberturas ao mesmo tempo passam juntas pela pergunta 2; o índice
        account_one_open_per_customer_idx barra a segunda, e esse
        IntegrityError vira o mesmo 409 QIT001009, nunca 500 (R3).
        """
        customer = self.customer_repository.get_by_key(customer_key)

        if customer is None:
            raise CustomerNotFound(customer_key)

        if self.account_repository.get_open_account_by_customer(customer) is not None:
            raise CustomerAlreadyHasAccount(customer_key)

        account_token = generate_account_token()

        try:
            account = self.account_repository.create_customer_account(customer, hash_account_token(account_token))
            piggy_bank = self.account_repository.get_piggy_bank(account)
            self.category_repository.create_default(piggy_bank)

            account_dto = AccountDTO.open_account_to_dict(account, account_token)
            self.session.commit()
        except IntegrityError:
            self.session.rollback()

            if self.account_repository.get_open_account_by_customer(customer) is not None:
                raise CustomerAlreadyHasAccount(customer_key)

            raise

        return account_dto

    def get_account(self, account_key: str, account_token: str) -> dict:
        """A conta, só para o dono; também bloqueada ou encerrada (CLI-05). Não grava nada."""
        account = self.get_owned_account(account_key, account_token)
        customer = self.customer_repository.get_by_id(account.customer_id)
        piggy_bank = self.account_repository.get_piggy_bank(account)

        return AccountDTO.obj_to_dict(account, customer, piggy_bank)
```

- `src/controllers/__init__.py` (editar): o conteúdo inteiro passa a ser:

```python
from controllers.customer_controller import CustomerController
from controllers.account_controller import AccountController
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/05-cliente-conta`; `git log --oneline` mostra `feat(conta): token da conta e repositories da conta e da categoria padrão`.
2. Crie `src/dtos/account_dto.py` com o conteúdo do campo **Arquivos**.
3. Edite `src/dtos/__init__.py` com o conteúdo do campo **Arquivos**.
4. Edite `src/controllers/base_controller.py` com o conteúdo do campo **Arquivos**.
5. Crie `src/controllers/account_controller.py` com o conteúdo do campo **Arquivos**.
6. Edite `src/controllers/__init__.py` com o conteúdo do campo **Arquivos**.
7. `docker compose up -d --build --wait` → termina sem erro.
8. Rode a conferência S1 do **Verificar**.
9. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `94 passed`.
10. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
11. Feche o passo (AGENTS.md, seção 7), um comando por vez:
    ```
    git add -- src/dtos/account_dto.py src/dtos/__init__.py src/controllers/base_controller.py src/controllers/account_controller.py src/controllers/__init__.py
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "feat(conta): DTO, controller e checagem de dono da conta"
    git log -1 --format=%B
    ```

**Testes:** nenhum teste novo. As rotas que usam estas peças nascem nos passos 5.6 (abrir) e 5.7 (consultar, com a checagem de dono), com os testes que ficam vermelhos antes delas. Aqui, a prova é a S1: os nomes do plano existem e a API sobe com eles.
**Verificar:**
- S1 (um comando, numa linha só):
  ```
  docker compose exec -T api python -c "from controllers import AccountController, CustomerController; from controllers.base_controller import BaseController; from dtos import AccountDTO; print(sorted(n for n in vars(AccountController) if not n.startswith('_'))); print(sorted(n for n in vars(BaseController) if not n.startswith('_'))); print(sorted(n for n in vars(AccountDTO) if not n.startswith('_'))); print(issubclass(CustomerController, BaseController), issubclass(AccountController, BaseController))"
  ```
  → exatamente:
  ```
  ['get_account', 'open_account']
  ['get_owned_account', 'mark_account_auth_failure']
  ['obj_to_dict', 'open_account_to_dict']
  True True
  ```
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `94 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/controllers/__init__.py
  src/controllers/account_controller.py
  src/controllers/base_controller.py
  src/dtos/__init__.py
  src/dtos/account_dto.py
  ```
- `git log -1 --format=%B` → `feat(conta): DTO, controller e checagem de dono da conta`

**Pronto quando:**
- [ ] Os cinco arquivos têm exatamente o conteúdo do campo **Arquivos**.
- [ ] A S1 dá as 4 linhas esperadas.
- [ ] Suíte com `94 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/05-cliente-conta`.

**Commit:** `feat(conta): DTO, controller e checagem de dono da conta`
**Pare se:**
- `docker compose up -d --build --wait` falhar com `ImportError` ou `circular import` no `docker compose logs --tail 100 api`: traga a saída.
- A S1 der outra saída depois de 3 tentativas de conferir os cinco arquivos contra o plano.
- A suíte não terminar com `94 passed`.

---

### Passo 5.6 — `POST /customers/{customer_key}/accounts`
**Branch:** fase/05-cliente-conta · **Depende de:** 5.5
**Objetivo:** `AccountResource.on_post_account` e a rota `POST /customers/{customer_key}/accounts` (tokens: interno; sem corpo): 201 com `{"account_key", "account_token"}`; 404 `QIT001008`; 409 `QIT001009`; 403 `QIT000002`.
**Decisões:** CLI-01 — conta só com cliente · CLI-04 — uma conta aberta · TST-03 — conta só com cliente · API-16 — token da conta · COF-14 — cofrinho é conta · COF-03 — "economias" · API-02 — 201 na criação · API-10 — criação devolve key e poucos campos · R3, MOV-19 — `IntegrityError` vira 409 · R4 — evento do estado · TST-01 — black box e TDD
**Arquivos:**
- `src/resources/account.py` (criar): o conteúdo inteiro é:

```python
from fastapi import status as http_status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from controllers import AccountController


class AccountResource:
    """A porta HTTP da conta. Sem regra de negócio, sem SQL e sem nada guardado no self (ARQ-02).

    O token da conta chega no cabeçalho ACCOUNT-TOKEN (API-16); quem o
    confere é o controller (BaseController.get_owned_account).
    """

    def on_post_account(self, customer_key: str) -> JSONResponse:
        controller = AccountController()
        account = controller.open_account(customer_key)

        return JSONResponse(
            content=jsonable_encoder(account),
            status_code=http_status.HTTP_201_CREATED,
        )
```

- `src/resources/__init__.py` (editar): o conteúdo inteiro passa a ser:

```python
from resources.health_check import HealthCheckResource
from resources.customer import CustomerResource
from resources.account import AccountResource
```

- `src/app.py` (editar): o conteúdo inteiro passa a ser o do passo 5.3, com três trocas, e nada mais:
  1. A linha
     ```python
     from resources import CustomerResource, HealthCheckResource
     ```
     vira
     ```python
     from resources import AccountResource, CustomerResource, HealthCheckResource
     ```
  2. A linha
     ```python
         customer_resource = CustomerResource()
     ```
     vira as duas linhas
     ```python
         customer_resource = CustomerResource()
         account_resource = AccountResource()
     ```
  3. A linha
     ```python
         application.add_api_route("/customers", customer_resource.on_post, methods=["POST"])
     ```
     vira as quatro linhas
     ```python
         application.add_api_route("/customers", customer_resource.on_post, methods=["POST"])

         # Conta
         application.add_api_route("/customers/{customer_key}/accounts", account_resource.on_post_account, methods=["POST"])
     ```
  O bloco das rotas fica exatamente assim (de `health_check_resource = HealthCheckResource()` até `register_error_handlers(application)`):
  ```python
      health_check_resource = HealthCheckResource()
      customer_resource = CustomerResource()
      account_resource = AccountResource()

      application.add_api_route("/", health_check_resource.on_get_home, methods=["GET"])
      application.add_api_route(
          "/health_check",
          health_check_resource.on_get_health_check,
          methods=["GET"]
      )

      # Cliente
      application.add_api_route("/customers", customer_resource.on_post, methods=["POST"])

      # Conta
      application.add_api_route("/customers/{customer_key}/accounts", account_resource.on_post_account, methods=["POST"])

      register_error_handlers(application)
  ```

- `tests/integration/accounts/test_open_account.py` (criar; a pasta `tests/integration/accounts/` é nova e fica sem `__init__.py`): o conteúdo inteiro é:

```python
"""Abertura de conta: POST /customers/{customer_key}/accounts (CLI-01, CLI-04, API-16, TST-03).

A conta só nasce para cliente que existe (404 QIT001008) e que não tem
conta não encerrada (409 QIT001009). O token da conta sai uma vez só,
nesta resposta.
"""

import re
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

from tests.utils import DbUtils, ObjectGenerator, RequestGenerator


UUID_V4 = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")
ACCOUNT_TOKEN = re.compile(r"^[A-Za-z0-9_-]{43}$")
PARALLEL_REQUESTS = 8


def assert_no_internal_id(body: dict) -> None:
    """R5: nenhum campo id nem terminado em _id na resposta."""
    for field in body:
        assert field != "id", field
        assert not field.endswith("_id"), field


class TestOpenAccount:
    def test_opens_account(self):
        customer_key = ObjectGenerator.create_customer()

        status, response = RequestGenerator.POST_account(customer_key)

        assert status == 201, response
        assert sorted(response) == ["account_key", "account_token"]
        assert UUID_V4.match(response["account_key"])
        assert ACCOUNT_TOKEN.match(response["account_token"])
        assert_no_internal_id(response)

        other_account = ObjectGenerator.create_account()
        assert other_account["account_key"] != response["account_key"]
        assert other_account["account_token"] != response["account_token"]

    def test_refuses_unknown_customer(self):
        for customer_key in [str(uuid4()), "nao-e-uma-key"]:
            status, response = RequestGenerator.POST_account(customer_key)

            assert status == 404, (customer_key, response)
            assert response["code"] == "QIT001008"
            assert "account_key" not in response
            assert "account_token" not in response

    def test_refuses_second_open_account(self):
        account = ObjectGenerator.create_account()

        status, response = RequestGenerator.POST_account(account["customer_key"])

        assert status == 409, response
        assert response["code"] == "QIT001009"

    def test_requires_internal_token(self):
        DbUtils.rollback()

        status, response = RequestGenerator.POST_account(ObjectGenerator.create_customer())
        assert status == 201, response

        customer_key = ObjectGenerator.create_customer()

        for internal_token in [None, "token_errado"]:
            status, response = RequestGenerator.POST_account(customer_key, internal_token=internal_token)

            assert status == 403, (internal_token, response)
            assert response["code"] == "QIT000002"

        status, response = RequestGenerator.POST_account(customer_key)
        assert status == 201, response

    def test_concurrent_openings(self):
        customer_key = ObjectGenerator.create_customer()

        with ThreadPoolExecutor(max_workers=PARALLEL_REQUESTS) as executor:
            results = list(executor.map(RequestGenerator.POST_account, [customer_key] * PARALLEL_REQUESTS))

        statuses = sorted(status for status, _response in results)
        assert statuses == [201] + [409] * (PARALLEL_REQUESTS - 1), results

        codes = [response["code"] for status, response in results if status == 409]
        assert codes == ["QIT001009"] * (PARALLEL_REQUESTS - 1), codes
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/05-cliente-conta`; `git log --oneline` mostra `feat(conta): DTO, controller e checagem de dono da conta`.
2. Crie `tests/integration/accounts/test_open_account.py` com o conteúdo do campo **Arquivos**.
3. `docker compose up -d --build --wait`.
4. `./.venv/Scripts/python.exe -m pytest -v tests/integration/accounts/test_open_account.py` → a última linha tem `5 failed` e não tem `passed`. Os 5 falham por asserção: hoje a rota responde 404 `QIT000404` (no `ObjectGenerator.create_account`, a asserção `status == 201` dele).
5. Crie `src/resources/account.py` com o conteúdo do campo **Arquivos**.
6. Edite `src/resources/__init__.py` com o conteúdo do campo **Arquivos**.
7. Faça as três trocas em `src/app.py` e confira o bloco das rotas contra o do campo **Arquivos**.
8. `docker compose up -d --build --wait`.
9. `./.venv/Scripts/python.exe -m pytest -v tests/integration/accounts/test_open_account.py` → a última linha tem `5 passed`.
10. Rode as conferências A1 e A2 do **Verificar**.
11. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `99 passed`.
12. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
13. Feche o passo (AGENTS.md, seção 7), um comando por vez:
    ```
    git add -- src/resources/account.py src/resources/__init__.py src/app.py tests/integration/accounts/test_open_account.py
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "feat(conta): rota de abertura de conta"
    git log -1 --format=%B
    ```

**Testes:** `tests/integration/accounts/test_open_account.py`. Efeito no banco de cada 201: uma conta `CUSTOMER` `ACTIVE` com saldo 0 e o hash do token, um cofrinho `PIGGY_BANK`, a categoria "economias" e os dois eventos `ACTIVE` (conta e categoria); o 404 e o 409 não gravam nada além da linha de `request_log`.

| Função de teste | Entrada | Esperado |
|---|---|---|
| `test_opens_account` | cliente novo; `POST /customers/{customer_key}/accounts`; depois outra conta, de outro cliente | 201; o corpo tem exatamente `account_key` (UUID v4) e `account_token` (43 caracteres de `A-Z a-z 0-9 - _`); nenhum `id`; a outra conta tem key e token diferentes |
| `test_refuses_unknown_customer` | `customer_key` UUID que não existe; e `nao-e-uma-key` | 404 `QIT001008` nos dois, sem `account_key` nem `account_token` no corpo (CLI-01; a conferência A2 prova que nenhuma conta é criada) |
| `test_refuses_second_open_account` | segunda abertura para o mesmo cliente | 409 `QIT001009` |
| `test_requires_internal_token` | começa com `DbUtils.rollback()`; abertura com o token; para outro cliente, sem `INTERNAL-TOKEN` e com `token_errado`; depois com o token certo | 201; 403 `QIT000002` nos dois; 201 (as recusas não abriram conta) |
| `test_concurrent_openings` | 8 aberturas ao mesmo tempo para o mesmo cliente | exatamente um 201 e sete 409 `QIT001009`; nenhum 500 |

**Verificar:**
- `./.venv/Scripts/python.exe -m pytest -v tests/integration/accounts/test_open_account.py` → `5 passed`.
- A1 — o que a abertura grava (API-16, COF-14, COF-03, R4, GAM-13). Um comando, numa linha só:
  ```
  ./.venv/Scripts/python.exe -c "import hashlib; from sqlalchemy import create_engine, text; from tests.utils import DbUtils, ObjectGenerator; a = ObjectGenerator.create_account(); c = create_engine(DbUtils.database_url()).connect(); k = {'k': a['account_key']}; h = c.execute(text('SELECT token_hash FROM account WHERE account_key = :k'), k).scalar(); print(len(a['account_token']), h == hashlib.sha256(a['account_token'].encode()).hexdigest(), a['account_token'] in h); print(c.execute(text('SELECT m.balance, r.enumerator, y.enumerator FROM account m JOIN piggy_rank r ON r.id = m.rank_id JOIN piggy_rank y ON y.id = m.yield_rank_id WHERE m.account_key = :k'), k).fetchall()); print(c.execute(text('SELECT t.enumerator, s.enumerator, p.balance, p.token_hash IS NULL, p.customer_id = m.customer_id FROM account m JOIN account p ON p.parent_account_id = m.id JOIN account_type t ON t.id = p.account_type_id JOIN account_status s ON s.id = p.status_id WHERE m.account_key = :k'), k).fetchall()); print(c.execute(text('SELECT g.name, g.is_default, cs.enumerator, (SELECT count(*) FROM category_status_event e WHERE e.category_id = g.id) FROM category g JOIN account p ON p.id = g.account_id JOIN account m ON m.id = p.parent_account_id JOIN category_status cs ON cs.id = g.status_id WHERE m.account_key = :k'), k).fetchall()); print(c.execute(text('SELECT s.enumerator, e.source, e.block_reason_id FROM account_status_event e JOIN account m ON m.id = e.account_id JOIN account_status s ON s.id = e.status_id WHERE m.account_key = :k'), k).fetchall())"
  ```
  → exatamente:
  ```
  43 True False
  [(0, 'DEFAULT', 'DEFAULT')]
  [('PIGGY_BANK', 'ACTIVE', 0, True, True)]
  [('economias', True, 'ACTIVE', 1)]
  [('ACTIVE', None, None)]
  ```
- A2 — cliente que não existe não abre conta (CLI-01). Um comando, numa linha só:
  ```
  ./.venv/Scripts/python.exe -c "import uuid; from sqlalchemy import create_engine, text; from tests.utils import DbUtils, RequestGenerator; c = create_engine(DbUtils.database_url(), isolation_level='AUTOCOMMIT').connect(); n = c.execute(text('SELECT count(*) FROM account')).scalar(); s = RequestGenerator.POST_account(str(uuid.uuid4())); print(s[0], s[1]['code'], c.execute(text('SELECT count(*) FROM account')).scalar() - n)"
  ```
  → `404 QIT001008 0`
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `99 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/app.py
  src/resources/__init__.py
  src/resources/account.py
  tests/integration/accounts/test_open_account.py
  ```
- `git log -1 --format=%B` → `feat(conta): rota de abertura de conta`

**Pronto quando:**
- [ ] Os 5 testes falharam antes do código (item 4) e passam depois (item 9).
- [ ] A1 e A2 dão a saída esperada.
- [ ] Suíte com `99 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/05-cliente-conta`.

**Commit:** `feat(conta): rota de abertura de conta`
**Pare se:**
- O item 4 não terminar com `5 failed`.
- Um teste receber 500 (`QIT000500`): rode `docker compose logs --tail 100 api` e traga a saída.
- `test_concurrent_openings` falhar em uma de três rodadas seguidas do item 9.
- A1 ou A2 derem outra saída depois de 3 tentativas de conferir os arquivos do passo contra o plano.
- A suíte não terminar com `99 passed`.

---

### Passo 5.7 — `GET /accounts/{account_key}`
**Branch:** fase/05-cliente-conta · **Depende de:** 5.6
**Objetivo:** `AccountResource.on_get_by_key` e a rota `GET /accounts/{account_key}` (tokens: conta): 200 com `account_key`, `customer_key`, `status`, `balance`, `piggy_bank_balance` e `created_at`; 404 `QIT001010` com `auth_failure = "ACCOUNT"` para conta que não existe, que não é de cliente, token que falta e token de outra conta.
**Decisões:** R8 — outro dono → 404 · API-09 — dono pelo token · API-16 — o token não volta · R5 — o `id` nunca sai · DAD-08 — centavos inteiros · API-10 — consulta devolve o objeto pelo DTO · CLI-05 — encerrada e bloqueada só leem · PRD-14 — `auth_failure` · TST-01 — black box e TDD
**Arquivos:**
- `src/resources/account.py` (editar): o conteúdo inteiro passa a ser:

```python
from fastapi import Request
from fastapi import status as http_status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from constants import ACCOUNT_TOKEN_HEADER
from controllers import AccountController


class AccountResource:
    """A porta HTTP da conta. Sem regra de negócio, sem SQL e sem nada guardado no self (ARQ-02).

    O token da conta chega no cabeçalho ACCOUNT-TOKEN (API-16); quem o
    confere é o controller (BaseController.get_owned_account).
    """

    def on_post_account(self, customer_key: str) -> JSONResponse:
        controller = AccountController()
        account = controller.open_account(customer_key)

        return JSONResponse(
            content=jsonable_encoder(account),
            status_code=http_status.HTTP_201_CREATED,
        )

    def on_get_by_key(self, account_key: str, request: Request) -> JSONResponse:
        controller = AccountController()
        account = controller.get_account(account_key, request.headers.get(ACCOUNT_TOKEN_HEADER))

        return JSONResponse(
            content=jsonable_encoder(account),
            status_code=http_status.HTTP_200_OK,
        )
```

- `src/app.py` (editar): uma troca, e nada mais. A linha
  ```python
      application.add_api_route("/customers/{customer_key}/accounts", account_resource.on_post_account, methods=["POST"])
  ```
  vira as duas linhas
  ```python
      application.add_api_route("/customers/{customer_key}/accounts", account_resource.on_post_account, methods=["POST"])
      application.add_api_route("/accounts/{account_key}", account_resource.on_get_by_key, methods=["GET"])
  ```

- `tests/integration/accounts/test_get_account.py` (criar): o conteúdo inteiro é:

```python
"""Consulta da conta: GET /accounts/{account_key} (R8, API-09, API-16, R5, DAD-08).

Só com o ACCOUNT-TOKEN da própria conta. Conta que não existe, token que
falta, token errado ou de outra conta: o mesmo 404 QIT001010, nunca 403.
Os testes que erram o token começam com DbUtils.rollback() (PRD-10).
"""

from datetime import datetime
from uuid import uuid4

from tests.utils import DbUtils, ObjectGenerator, RequestGenerator


ACCOUNT_FIELDS = ["account_key", "balance", "created_at", "customer_key", "piggy_bank_balance", "status"]


def assert_no_internal_id(body: dict) -> None:
    """R5: nenhum campo id nem terminado em _id na resposta."""
    for field in body:
        assert field != "id", field
        assert not field.endswith("_id"), field


def assert_account_not_found(status: int, response: dict) -> None:
    assert status == 404, response
    assert response["code"] == "QIT001010"


def assert_owner_reads(account: dict) -> None:
    status, response = RequestGenerator.GET_account(account["account_key"], account["account_token"])
    assert status == 200, response


class TestGetAccount:
    def test_gets_new_account(self):
        account = ObjectGenerator.create_account()

        status, response = RequestGenerator.GET_account(account["account_key"], account["account_token"])

        assert status == 200, response
        assert sorted(response) == ACCOUNT_FIELDS
        assert response["account_key"] == account["account_key"]
        assert response["customer_key"] == account["customer_key"]
        assert response["status"] == "ACTIVE"
        assert type(response["balance"]) is int
        assert response["balance"] == 0
        assert type(response["piggy_bank_balance"]) is int
        assert response["piggy_bank_balance"] == 0
        datetime.fromisoformat(response["created_at"])
        assert account["account_token"] not in str(response)
        assert_no_internal_id(response)

    def test_other_account_token_is_404(self):
        DbUtils.rollback()
        first = ObjectGenerator.create_account()
        second = ObjectGenerator.create_account()

        assert_owner_reads(first)

        status, response = RequestGenerator.GET_account(first["account_key"], second["account_token"])
        assert_account_not_found(status, response)

        status, response = RequestGenerator.GET_account(second["account_key"], first["account_token"])
        assert_account_not_found(status, response)

    def test_missing_or_wrong_token_is_404(self):
        DbUtils.rollback()
        account = ObjectGenerator.create_account()

        assert_owner_reads(account)

        for account_token in [None, "token_errado", account["account_key"]]:
            status, response = RequestGenerator.GET_account(account["account_key"], account_token)
            assert_account_not_found(status, response)

    def test_unknown_account_is_404(self):
        DbUtils.rollback()
        account = ObjectGenerator.create_account()

        assert_owner_reads(account)

        for account_key in [str(uuid4()), "nao-e-uma-key"]:
            status, response = RequestGenerator.GET_account(account_key, account["account_token"])
            assert_account_not_found(status, response)

    def test_requires_internal_token(self):
        DbUtils.rollback()
        account = ObjectGenerator.create_account()

        assert_owner_reads(account)

        status, response = RequestGenerator.GET_account(account["account_key"], account["account_token"], internal_token=None)

        assert status == 403, response
        assert response["code"] == "QIT000002"
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/05-cliente-conta`; `git log --oneline` mostra `feat(conta): rota de abertura de conta`.
2. Crie `tests/integration/accounts/test_get_account.py` com o conteúdo do campo **Arquivos**.
3. `docker compose up -d --build --wait`.
4. `./.venv/Scripts/python.exe -m pytest -v tests/integration/accounts/test_get_account.py` → a última linha tem `5 failed` e não tem `passed`. Os 5 falham por asserção: hoje `GET /accounts/{account_key}` responde 404 `QIT000404` onde o teste espera 200.
5. Edite `src/resources/account.py` com o conteúdo do campo **Arquivos**.
6. Faça a troca em `src/app.py`.
7. `docker compose up -d --build --wait`.
8. `./.venv/Scripts/python.exe -m pytest -v tests/integration/accounts/test_get_account.py` → a última linha tem `5 passed`.
9. Rode as conferências G1 e G2 do **Verificar**, nessa ordem, uma logo depois da outra.
10. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `104 passed`.
11. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
12. Feche o passo (AGENTS.md, seção 7), um comando por vez:
    ```
    git add -- src/resources/account.py src/app.py tests/integration/accounts/test_get_account.py
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "feat(conta): rota de consulta da conta com checagem de dono"
    git log -1 --format=%B
    ```

**Testes:** `tests/integration/accounts/test_get_account.py`. Nenhum teste grava além das contas que cria e das linhas de `request_log`; as recusas gravam `auth_failure = ACCOUNT` (conferência G2).

| Função de teste | Entrada | Esperado |
|---|---|---|
| `test_gets_new_account` | conta nova; `GET /accounts/{account_key}` com o token dela | 200; campos exatamente `account_key`, `balance`, `created_at`, `customer_key`, `piggy_bank_balance`, `status`; `status` `ACTIVE`; `balance` e `piggy_bank_balance` = `0`, tipo `int`; `created_at` em ISO 8601; o token não aparece; nenhum `id` |
| `test_other_account_token_is_404` | começa com `DbUtils.rollback()`; contas A e B; A com o token de A; A com o token de B; B com o token de A | 200; 404 `QIT001010`; 404 `QIT001010` (R8: nunca 403) |
| `test_missing_or_wrong_token_is_404` | começa com `DbUtils.rollback()`; conta A com o token certo; depois sem `ACCOUNT-TOKEN`, com `token_errado` e com a própria `account_key` no lugar do token | 200; 404 `QIT001010` nos três |
| `test_unknown_account_is_404` | começa com `DbUtils.rollback()`; conta A com o token certo; depois key UUID que não existe e `nao-e-uma-key`, com o token de A | 200; 404 `QIT001010` nos dois |
| `test_requires_internal_token` | começa com `DbUtils.rollback()`; conta A com os dois tokens; depois sem `INTERNAL-TOKEN` | 200; 403 `QIT000002` |

**Verificar:**
- `./.venv/Scripts/python.exe -m pytest -v tests/integration/accounts/test_get_account.py` → `5 passed`.
- G1: `curl.exe -s -i -H "INTERNAL-TOKEN: default_token" -H "ACCOUNT-TOKEN: token_errado" http://127.0.0.1:3000/accounts/6f1c2a9e-8b3d-4c7a-9e21-5d4b3a2f1e0c` → a primeira linha é `HTTP/1.1 404 Not Found`; o corpo contém `QIT001010`.
- G2 (um comando, numa linha só):
  ```
  docker compose exec -T db psql -U bootcamp -d bootcamp -t -A -c "SELECT method, path, status, error_code, auth_failure, account_key FROM request_log ORDER BY id DESC LIMIT 1"
  ```
  → `GET|/accounts/6f1c2a9e-8b3d-4c7a-9e21-5d4b3a2f1e0c|404|QIT001010|ACCOUNT|6f1c2a9e-8b3d-4c7a-9e21-5d4b3a2f1e0c`
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `104 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/app.py
  src/resources/account.py
  tests/integration/accounts/test_get_account.py
  ```
- `git log -1 --format=%B` → `feat(conta): rota de consulta da conta com checagem de dono`

**Pronto quando:**
- [ ] Os 5 testes falharam antes do código (item 4) e passam depois (item 8).
- [ ] G1 e G2 dão a saída esperada.
- [ ] Suíte com `104 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/05-cliente-conta`.

**Commit:** `feat(conta): rota de consulta da conta com checagem de dono`
**Pare se:**
- O item 4 não terminar com `5 failed`.
- Um teste receber 403 onde o plano espera 404 (a checagem de dono respondeu 403: R8).
- A G2 mostrar a coluna `auth_failure` vazia: a checagem de dono não anotou a falha.
- A suíte não terminar com `104 passed`.

---

### Passo 5.8 — `GET /customers/{customer_key}`
**Branch:** fase/05-cliente-conta · **Depende de:** 5.7
**Objetivo:** `CustomerController.get_by_key` e a rota `GET /customers/{customer_key}` (tokens: conta, o da conta não encerrada do cliente): 200 com os dados do cliente e o CPF inteiro; 404 `QIT001008` em todo outro caso.
**Decisões:** API-17 — consultar cliente · R8 — outro dono → 404 · API-09 — dono pelo token · R5 — o `id` nunca sai · PRD-14 — `auth_failure` · TST-01 — black box e TDD
**Arquivos:**
- `src/controllers/customer_controller.py` (editar): o conteúdo inteiro passa a ser:

```python
from datetime import date

from sqlalchemy.exc import IntegrityError

from controllers.base_controller import BaseController
from dtos import CustomerDTO
from errors import (
    CustomerNotFound,
    DuplicatedDocumentNumber,
    DuplicatedEmail,
    InvalidBirthdate,
    InvalidDocumentNumber,
    UnderageCustomer,
)
from repositories import AccountRepository, CustomerRepository
from utils.account_token import account_token_matches
from utils.document_number import is_valid_cpf


# CLI-03: idade mínima para o cadastro, sem idade máxima.
MINIMUM_AGE = 18


class CustomerController(BaseController):
    """As regras do cliente (CLI-02, CLI-03, API-17)."""

    def __init__(self) -> None:
        super().__init__(__name__)
        self.customer_repository = CustomerRepository(self.context)
        self.account_repository = AccountRepository(self.context)

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

    def get_by_key(self, customer_key: str, account_token: str) -> dict:
        """O cliente, só para o dono (API-17). Não grava nada.

        Confere, nesta ordem: o cliente existe; ele tem conta não
        encerrada (ACTIVE ou BLOCKED); o ACCOUNT-TOKEN é o dessa conta.
        Qualquer falha responde o mesmo 404 QIT001008 e anota a falha do
        token da conta (PRD-14): quem não é o dono não descobre se o
        cliente existe (R8).
        """
        customer = self.customer_repository.get_by_key(customer_key)

        account = None
        if customer is not None:
            account = self.account_repository.get_open_account_by_customer(customer)

        if account is None or not account_token_matches(account_token, account.token_hash):
            self.mark_account_auth_failure()
            raise CustomerNotFound(customer_key)

        return CustomerDTO.obj_to_dict(customer)

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
```

- `src/resources/customer.py` (editar): o conteúdo inteiro passa a ser:

```python
from fastapi import Request
from fastapi import status as http_status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from constants import ACCOUNT_TOKEN_HEADER
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

    def on_get_by_key(self, customer_key: str, request: Request) -> JSONResponse:
        controller = CustomerController()
        customer = controller.get_by_key(customer_key, request.headers.get(ACCOUNT_TOKEN_HEADER))

        return JSONResponse(
            content=jsonable_encoder(customer),
            status_code=http_status.HTTP_200_OK,
        )
```

- `src/app.py` (editar): uma troca, e nada mais. A linha
  ```python
      application.add_api_route("/customers", customer_resource.on_post, methods=["POST"])
  ```
  vira as duas linhas
  ```python
      application.add_api_route("/customers", customer_resource.on_post, methods=["POST"])
      application.add_api_route("/customers/{customer_key}", customer_resource.on_get_by_key, methods=["GET"])
  ```

- `tests/integration/customers/test_get_customer.py` (criar): o conteúdo inteiro é:

```python
"""Consulta do cliente: GET /customers/{customer_key} (API-17, R8, R5).

Só com o ACCOUNT-TOKEN da conta não encerrada do cliente; o CPF sai
inteiro. Qualquer outro caso responde o mesmo 404 QIT001008. Os testes
que erram o token começam com DbUtils.rollback() (PRD-10).
"""

from uuid import uuid4

from tests.utils import DbUtils, ObjectGenerator, PayloadGenerator, RequestGenerator


def assert_no_internal_id(body: dict) -> None:
    """R5: nenhum campo id nem terminado em _id na resposta."""
    for field in body:
        assert field != "id", field
        assert not field.endswith("_id"), field


def assert_customer_not_found(status: int, response: dict) -> None:
    assert status == 404, response
    assert response["code"] == "QIT001008"


def assert_owner_reads_customer(account: dict) -> None:
    status, response = RequestGenerator.GET_customer(account["customer_key"], account["account_token"])
    assert status == 200, response


class TestGetCustomer:
    def test_owner_gets_customer(self):
        payload = PayloadGenerator.customer()
        status, response = RequestGenerator.POST_customer(payload)
        assert status == 201, response

        customer_key = response["customer_key"]
        account = ObjectGenerator.create_account(customer_key)

        status, response = RequestGenerator.GET_customer(customer_key, account["account_token"])

        assert status == 200, response
        assert response == {
            "customer_key": customer_key,
            "name": payload["name"],
            "document_number": payload["document_number"],
            "email": payload["email"],
            "birthdate": payload["birthdate"],
        }
        assert_no_internal_id(response)

    def test_other_account_token_is_404(self):
        DbUtils.rollback()
        first = ObjectGenerator.create_account()
        second = ObjectGenerator.create_account()

        assert_owner_reads_customer(first)

        status, response = RequestGenerator.GET_customer(first["customer_key"], second["account_token"])
        assert_customer_not_found(status, response)

        status, response = RequestGenerator.GET_customer(second["customer_key"], first["account_token"])
        assert_customer_not_found(status, response)

    def test_missing_or_wrong_token_is_404(self):
        DbUtils.rollback()
        account = ObjectGenerator.create_account()

        assert_owner_reads_customer(account)

        for account_token in [None, "token_errado"]:
            status, response = RequestGenerator.GET_customer(account["customer_key"], account_token)
            assert_customer_not_found(status, response)

    def test_unknown_customer_is_404(self):
        DbUtils.rollback()
        account = ObjectGenerator.create_account()

        assert_owner_reads_customer(account)

        for customer_key in [str(uuid4()), "nao-e-uma-key"]:
            status, response = RequestGenerator.GET_customer(customer_key, account["account_token"])
            assert_customer_not_found(status, response)

    def test_customer_without_account_is_404(self):
        DbUtils.rollback()
        account = ObjectGenerator.create_account()
        customer_key = ObjectGenerator.create_customer()

        assert_owner_reads_customer(account)

        for account_token in [account["account_token"], None]:
            status, response = RequestGenerator.GET_customer(customer_key, account_token)
            assert_customer_not_found(status, response)
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/05-cliente-conta`; `git log --oneline` mostra `feat(conta): rota de consulta da conta com checagem de dono`.
2. Crie `tests/integration/customers/test_get_customer.py` com o conteúdo do campo **Arquivos**.
3. `docker compose up -d --build --wait`.
4. `./.venv/Scripts/python.exe -m pytest -v tests/integration/customers/test_get_customer.py` → a última linha tem `5 failed` e não tem `passed`. Os 5 falham por asserção: hoje `GET /customers/{customer_key}` responde 404 `QIT000404` (caminho sem rota) onde o teste espera 200.
5. Edite `src/controllers/customer_controller.py` com o conteúdo do campo **Arquivos**.
6. Edite `src/resources/customer.py` com o conteúdo do campo **Arquivos**.
7. Faça a troca em `src/app.py`.
8. `docker compose up -d --build --wait`.
9. `./.venv/Scripts/python.exe -m pytest -v tests/integration/customers/test_get_customer.py` → a última linha tem `5 passed`.
10. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `109 passed`.
11. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
12. Feche o passo (AGENTS.md, seção 7), um comando por vez:
    ```
    git add -- src/controllers/customer_controller.py src/resources/customer.py src/app.py tests/integration/customers/test_get_customer.py
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "feat(cliente): rota de consulta do cliente pelo dono"
    git log -1 --format=%B
    ```

**Testes:** `tests/integration/customers/test_get_customer.py`. Nenhum teste grava além dos clientes e contas que cria e das linhas de `request_log`.

| Função de teste | Entrada | Esperado |
|---|---|---|
| `test_owner_gets_customer` | cliente cadastrado com um corpo conhecido; conta aberta; `GET /customers/{customer_key}` com o token da conta | 200; o corpo é exatamente `customer_key`, `name`, `document_number` (CPF inteiro), `email` e `birthdate` do cadastro; nenhum `id` |
| `test_other_account_token_is_404` | começa com `DbUtils.rollback()`; contas A e B; cliente de A com o token de A; cliente de A com o token de B; cliente de B com o token de A | 200; 404 `QIT001008`; 404 `QIT001008` |
| `test_missing_or_wrong_token_is_404` | começa com `DbUtils.rollback()`; cliente de A com o token de A; depois sem `ACCOUNT-TOKEN` e com `token_errado` | 200; 404 `QIT001008` nos dois |
| `test_unknown_customer_is_404` | começa com `DbUtils.rollback()`; cliente de A com o token de A; depois `customer_key` UUID que não existe e `nao-e-uma-key`, com o token de A | 200; 404 `QIT001008` nos dois |
| `test_customer_without_account_is_404` | começa com `DbUtils.rollback()`; conta A; cliente C sem conta; cliente de A com o token de A; cliente C com o token de A e sem token | 200; 404 `QIT001008` nos dois |

**Verificar:**
- `./.venv/Scripts/python.exe -m pytest -v tests/integration/customers/test_get_customer.py` → `5 passed`.
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `109 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/app.py
  src/controllers/customer_controller.py
  src/resources/customer.py
  tests/integration/customers/test_get_customer.py
  ```
- `git log -1 --format=%B` → `feat(cliente): rota de consulta do cliente pelo dono`

**Pronto quando:**
- [ ] Os 5 testes falharam antes do código (item 4) e passam depois (item 9).
- [ ] Suíte com `109 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/05-cliente-conta`.

**Commit:** `feat(cliente): rota de consulta do cliente pelo dono`
**Pare se:**
- O item 4 não terminar com `5 failed`.
- Um teste de `test_create_customer.py` ficar vermelho: o `create` mudou além do plano.
- A suíte não terminar com `109 passed`.

---

### Passo 5.9 — Barreira do token da conta
**Branch:** fase/05-cliente-conta · **Depende de:** 5.8
**Objetivo:** a barreira do 4.6 passa a contar também as falhas `ACCOUNT` por conta + IP: `AUTH_FAILURE_LIMIT` falhas do token de uma conta, do mesmo IP, em `AUTH_FAILURE_WINDOW_MINUTES` fazem toda requisição desse IP com essa conta no caminho responder 429 `QIT000429`, antes de conferir token.
**Decisões:** PRD-10 — barreira (por conta + IP no token da conta) · PRD-04 — sem estado na memória · PRD-06, PRD-14 — o log alimenta a barreira · PRD-08 — timeout também na barreira · TST-01 — black box e TDD · TST-02 — o que barra tem teste
**Arquivos:**
- `src/repositories/request_log_repository.py` (editar): trocar `from uuid import uuid4` por `from uuid import NAMESPACE_URL, uuid4, uuid5`; trocar `from models import RequestLog` por `from models import Account, Customer, RequestLog`; acrescentar ao fim da classe o método completo abaixo. IDs 1 CUSTOMER e 3 CLOSED são os da fase 2. O fallback uuid5 usa a customer_key normalizada, sem token nem nova coluna:

```python
    def resolve_customer_auth_key(self, customer_key: str) -> str:
        """PRD-15: conta aberta do cliente; sem conta, sujeito estavel de 36 caracteres."""
        normalized = customer_key.lower()
        with SessionLocal() as session:
            account_key = (session.query(Account.account_key)
                           .join(Customer, Customer.id == Account.customer_id)
                           .filter(Customer.customer_key == normalized,
                                   Account.account_type_id == 1,
                                   Account.status_id != 3)
                           .scalar())
        if account_key is not None:
            return account_key
        return str(uuid5(NAMESPACE_URL, "customer:" + normalized))
```

- `src/middlewares/auth_barrier.py` (editar): o conteúdo inteiro passa a ser:

```python
import re

from fastapi import FastAPI, Request
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.exc import OperationalError

from constants import AUTH_FAILURE_LIMIT, AUTH_FAILURE_WINDOW_MINUTES, BYPASS_ENDPOINTS
from errors.base_error import DatabaseTimeout, TooManyAuthFailures
from errors.handlers import is_database_timeout, qi_exception_to_response
from middlewares.request_log_writer import get_client_ip
from models import RequestLog
from repositories import RequestLogRepository
from utils.request_context import get_request_state


# As falhas dos dois tokens internos, contadas por IP.
INTERNAL_AUTH_FAILURES = [RequestLog.INTERNAL, RequestLog.ADMIN]

# As falhas do token da conta, contadas por conta + IP.
ACCOUNT_AUTH_FAILURES = [RequestLog.ACCOUNT]


def count_failures(client_ip: str, account_key: str) -> tuple:
    """(falhas dos tokens internos deste IP, falhas do token desta conta neste IP).

    Sem conta no caminho (`account_key` None), a segunda conta é 0 e nem
    vai ao banco.
    """
    repository = RequestLogRepository()

    internal_failures = repository.count_auth_failures(client_ip, INTERNAL_AUTH_FAILURES, AUTH_FAILURE_WINDOW_MINUTES)

    account_failures = 0
    if account_key is not None:
        account_failures = repository.count_auth_failures(
            client_ip,
            ACCOUNT_AUTH_FAILURES,
            AUTH_FAILURE_WINDOW_MINUTES,
            account_key,
        )

    return internal_failures, account_failures


def register_auth_barrier_middleware(application: FastAPI) -> None:
    """Barreira contra chute de token (PRD-10).

    • AUTH_FAILURE_LIMIT falhas de INTERNAL-TOKEN ou ADMIN-TOKEN do mesmo
      IP nos últimos AUTH_FAILURE_WINDOW_MINUTES minutos: toda requisição
      desse IP responde 429 QIT000429.
    • AUTH_FAILURE_LIMIT falhas do ACCOUNT-TOKEN de uma conta, do mesmo IP,
      na mesma janela: toda requisição desse IP com essa conta no caminho
      responde 429 QIT000429. As outras contas e as rotas sem conta no
      caminho seguem atendidas.

    Responde antes de conferir token nenhum, até as falhas antigas saírem
    da janela. O 429 não conta como falha. A key da conta no caminho já
    está no estado da requisição: quem a anota é o request_log_writer,
    que roda por fora desta barreira.

    A contagem mora em request_log, no banco, e não na memória do
    processo (PRD-04): vale para todas as cópias da API. As rotas de
    BYPASS_ENDPOINTS passam direto: o health check não toca no banco
    (PRD-02).
    """

    @application.middleware("http")
    async def check_auth_barrier(request: Request, call_next):
        if request.method == "OPTIONS" or request.url.path in BYPASS_ENDPOINTS:
            return await call_next(request)

        request_state = get_request_state()

        try:
            customer_path = re.fullmatch(r"/customers/([^/]+)", request.url.path)
            if request.method == "GET" and customer_path is not None:
                request_state.account_key = await run_in_threadpool(
                    RequestLogRepository().resolve_customer_auth_key, customer_path.group(1),
                )

            internal_failures, account_failures = await run_in_threadpool(
                count_failures,
                get_client_ip(request),
                request_state.account_key,
            )
        except OperationalError as error:
            if is_database_timeout(error):
                return qi_exception_to_response(DatabaseTimeout())
            raise

        if internal_failures >= AUTH_FAILURE_LIMIT or account_failures >= AUTH_FAILURE_LIMIT:
            return qi_exception_to_response(TooManyAuthFailures())

        return await call_next(request)
```

- `tests/integration/security/test_account_auth_barrier.py` (criar): o conteúdo inteiro é:

```python
"""Barreira contra chute do token da conta (PRD-10, PRD-04).

AUTH_FAILURE_LIMIT erros do ACCOUNT-TOKEN de uma conta, do mesmo IP,
fazem toda requisição desse IP com essa conta no caminho responder 429
QIT000429, antes de conferir token. A contagem mora em request_log
(PRD-04): cada teste começa e termina com DbUtils.rollback().

A janela de AUTH_FAILURE_WINDOW_MINUTES minutos não é testada aqui: o
teste teria de esperar a janela passar.
"""

from os import environ

from tests.utils import DbUtils, ObjectGenerator, PayloadGenerator, RequestGenerator


AUTH_FAILURE_LIMIT = int(environ.get("AUTH_FAILURE_LIMIT", "10"))

WRONG_TOKEN = "token_errado"
TOO_MANY_TRANSLATION = "Tentativas demais com token errado. Tente de novo mais tarde."


def fail_account_token(account: dict, times: int, account_token: str = WRONG_TOKEN) -> None:
    for _ in range(times):
        status, response = RequestGenerator.GET_account(account["account_key"], account_token)
        assert status == 404, response
        assert response["code"] == "QIT001010"


def assert_not_blocked(account: dict) -> None:
    status, response = RequestGenerator.GET_account(account["account_key"], account["account_token"])
    assert status == 200, response


def assert_blocked(account: dict) -> None:
    status, response = RequestGenerator.GET_account(account["account_key"], account["account_token"])
    assert status == 429, response
    assert response["code"] == "QIT000429"
    assert response["translation"] == TOO_MANY_TRANSLATION


class TestAccountAuthBarrier:
    def test_limit_of_account_failures_blocks_the_account(self):
        DbUtils.rollback()
        try:
            account = ObjectGenerator.create_account()

            fail_account_token(account, AUTH_FAILURE_LIMIT)

            assert_blocked(account)

            status, response = RequestGenerator.DELETE_account(account["account_key"], account["account_token"])
            assert status == 429, response
            assert response["code"] == "QIT000429"

            status, response = RequestGenerator.POST_block(account["account_key"], PayloadGenerator.block())
            assert status == 429, response
            assert response["code"] == "QIT000429"
        finally:
            DbUtils.rollback()

    def test_one_failure_below_the_limit_does_not_block(self):
        DbUtils.rollback()
        try:
            account = ObjectGenerator.create_account()

            fail_account_token(account, AUTH_FAILURE_LIMIT - 1)

            assert_not_blocked(account)

            fail_account_token(account, 1)

            assert_blocked(account)
        finally:
            DbUtils.rollback()

    def test_missing_token_counts_as_failure(self):
        DbUtils.rollback()
        try:
            account = ObjectGenerator.create_account()

            fail_account_token(account, AUTH_FAILURE_LIMIT, account_token=None)

            assert_blocked(account)
        finally:
            DbUtils.rollback()

    def test_barrier_is_per_account(self):
        DbUtils.rollback()
        try:
            blocked_account = ObjectGenerator.create_account()
            other_account = ObjectGenerator.create_account()

            fail_account_token(blocked_account, AUTH_FAILURE_LIMIT)

            assert_blocked(blocked_account)
            assert_not_blocked(other_account)

            status, response = RequestGenerator.POST_customer(PayloadGenerator.customer())
            assert status == 201, response
        finally:
            DbUtils.rollback()

    def test_successful_requests_do_not_count(self):
        DbUtils.rollback()
        try:
            account = ObjectGenerator.create_account()

            for _ in range(2 * AUTH_FAILURE_LIMIT):
                assert_not_blocked(account)

            fail_account_token(account, AUTH_FAILURE_LIMIT - 1)

            assert_not_blocked(account)

            fail_account_token(account, 1)

            assert_blocked(account)
        finally:
            DbUtils.rollback()
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/05-cliente-conta`; `git log --oneline` mostra `feat(cliente): rota de consulta do cliente pelo dono`.
2. Crie `tests/integration/security/test_account_auth_barrier.py` com o conteúdo do campo **Arquivos**.
3. `docker compose up -d --build --wait`.
4. `./.venv/Scripts/python.exe -m pytest -v tests/integration/security/test_account_auth_barrier.py` → a última linha tem `5 failed` e não tem `passed`. Os 5 falham por asserção de status: o 429 esperado volta 200.
5. Edite `src/middlewares/auth_barrier.py` com o conteúdo do campo **Arquivos**.
6. `docker compose up -d --build --wait`.
7. `./.venv/Scripts/python.exe -m pytest -v tests/integration/security/test_account_auth_barrier.py` → a última linha tem `5 passed`.
8. `./.venv/Scripts/python.exe -m pytest -v tests/integration/security/test_auth_barrier.py` → a última linha tem `6 passed` (a barreira dos tokens internos não mudou).
9. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `114 passed`.
10. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
11. Feche o passo (AGENTS.md, seção 7), um comando por vez:
    ```
    git add -- src/repositories/request_log_repository.py src/middlewares/auth_barrier.py tests/integration/security/test_account_auth_barrier.py
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "feat(seguranca): barreira contra chute do token da conta"
    git log -1 --format=%B
    ```

**Testes:** `tests/integration/security/test_account_auth_barrier.py`. `LIMIT` = `AUTH_FAILURE_LIMIT` (10 sem `.env`). "Falha" = `GET /accounts/{account_key}` com `ACCOUNT-TOKEN: token_errado` → 404 `QIT001010`. "Leitura do dono" = o mesmo `GET` com o token certo. Efeito no banco: contas criadas no teste e linhas de `request_log`, apagadas pelo `DbUtils.rollback()` do começo e do fim de cada teste.

| Função de teste | Entrada | Esperado |
|---|---|---|
| `test_limit_of_account_failures_blocks_the_account` | `LIMIT` falhas na conta A; depois (a) leitura do dono; (b) `DELETE /accounts/{A}` com o token certo; (c) `POST /internal/accounts/{A}/blocks` com os tokens certos | (a) 429 `QIT000429`, `translation` = `Tentativas demais com token errado. Tente de novo mais tarde.`; (b) e (c) 429 `QIT000429`: barra toda rota com A no caminho, antes de existir a rota |
| `test_one_failure_below_the_limit_does_not_block` | `LIMIT - 1` falhas; leitura do dono; mais 1 falha; leitura do dono | 200; depois 429 `QIT000429` (barrada no limite exato) |
| `test_missing_token_counts_as_failure` | `LIMIT` leituras de A sem `ACCOUNT-TOKEN`; leitura do dono | 404 `QIT001010` em cada uma; depois 429 |
| `test_barrier_is_per_account` | `LIMIT` falhas na conta A; leitura de A; leitura da conta B pelo dono; `POST /customers` | 429; 200 (a contagem é por conta); 201 (falha do token da conta não barra o IP nas rotas sem conta) |
| `test_successful_requests_do_not_count` | `2 × LIMIT` leituras do dono; `LIMIT - 1` falhas; leitura; 1 falha; leitura | as do começo e a do meio: 200; a última: 429 |

**Verificar:**
- `./.venv/Scripts/python.exe -m pytest -v tests/integration/security/test_account_auth_barrier.py` → `5 passed`.
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `114 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m pytest` de novo → `114 passed` (a barreira não deixa resto de uma rodada para a outra).
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/middlewares/auth_barrier.py
  src/repositories/request_log_repository.py
  tests/integration/security/test_account_auth_barrier.py
  ```
- `git log -1 --format=%B` → `feat(seguranca): barreira contra chute do token da conta`

**Pronto quando:**
- [ ] Os 5 testes falharam antes do código (item 4) e passam depois (item 7).
- [ ] Os 6 testes de `test_auth_barrier.py` continuam verdes.
- [ ] Suíte com `114 passed`, duas vezes seguidas; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/05-cliente-conta`.

**Commit:** `feat(seguranca): barreira contra chute do token da conta`
**Pare se:**
- O item 4 não terminar com `5 failed`.
- Um teste fora de `test_account_auth_barrier.py` e `test_auth_barrier.py` receber 429: algum teste que erra token não limpa a contagem.
- O item 8 não terminar com `6 passed`.
- A suíte não terminar com `114 passed`.

---


PRD-15 também vale para GET /customers/{customer_key}: resolver a conta antes de contar ACCOUNT; writer grava a mesma key resolvida. Sem conta, uuid5 da customer_key normalizada identifica o contador fallback na coluna existente. O controlador continua dando 404; ao atingir o limite, a barreira dá 429. Expiração e compartilhamento entre cliente/conta têm provas no passo 11.6.

### Passo 5.10 — Bloquear e desbloquear
**Branch:** fase/05-cliente-conta · **Depende de:** 5.9
**Objetivo:** `AccountController.block_account` e `unblock_account`; `InternalResource` (`on_post_block`, `on_post_unblock`); as rotas `POST /internal/accounts/{account_key}/blocks` (schema `post_blocks.json`) e `POST /internal/accounts/{account_key}/unblocks`, tokens: admin; 204 sem corpo; evento com origem `MANUAL` e, no bloqueio, o motivo.
**Decisões:** CLI-05 — estados da conta (só o banco bloqueia, com motivo) · CLI-09 — bloqueada continua lendo · API-13 — rotas `/internal` · PRD-07, PRD-13 — token de administração · API-02 — 204 pronto e sem corpo · API-03 — schema fechado · R4 — append-only · MOV-05, MOV-11 — trava antes de conferir o estado · TST-01 — black box e TDD
**Arquivos:**
- `src/controllers/account_controller.py` (editar): o conteúdo inteiro passa a ser:

```python
from sqlalchemy.exc import IntegrityError

from controllers.base_controller import BaseController
from dtos import AccountDTO
from errors import (
    AccountNotActive,
    AccountNotBlocked,
    AccountNotFound,
    CustomerAlreadyHasAccount,
    CustomerNotFound,
)
from models import Account, AccountStatus, AccountStatusEvent
from repositories import AccountRepository, CategoryRepository, CustomerRepository
from utils.account_token import generate_account_token, hash_account_token


class AccountController(BaseController):
    """As regras da conta (CLI-01, CLI-04, CLI-05, API-16)."""

    def __init__(self) -> None:
        super().__init__(__name__)
        self.account_repository = AccountRepository(self.context)
        self.category_repository = CategoryRepository(self.context)
        self.customer_repository = CustomerRepository(self.context)

    def open_account(self, customer_key: str) -> dict:
        """Abre a conta do cliente. As regras, nesta ordem, antes de gravar:

        1. o cliente existe (404 QIT001008; nenhuma conta é criada, CLI-01);
        2. o cliente não tem conta não encerrada (409 QIT001009, CLI-04).

        Depois: a conta ACTIVE com saldo 0 e o hash do token, o cofrinho e
        a categoria "economias" (COF-14, COF-03), numa transação só. Duas
        aberturas ao mesmo tempo passam juntas pela pergunta 2; o índice
        account_one_open_per_customer_idx barra a segunda, e esse
        IntegrityError vira o mesmo 409 QIT001009, nunca 500 (R3).
        """
        customer = self.customer_repository.get_by_key(customer_key)

        if customer is None:
            raise CustomerNotFound(customer_key)

        if self.account_repository.get_open_account_by_customer(customer) is not None:
            raise CustomerAlreadyHasAccount(customer_key)

        account_token = generate_account_token()

        try:
            account = self.account_repository.create_customer_account(customer, hash_account_token(account_token))
            piggy_bank = self.account_repository.get_piggy_bank(account)
            self.category_repository.create_default(piggy_bank)

            account_dto = AccountDTO.open_account_to_dict(account, account_token)
            self.session.commit()
        except IntegrityError:
            self.session.rollback()

            if self.account_repository.get_open_account_by_customer(customer) is not None:
                raise CustomerAlreadyHasAccount(customer_key)

            raise

        return account_dto

    def get_account(self, account_key: str, account_token: str) -> dict:
        """A conta, só para o dono; também bloqueada ou encerrada (CLI-05). Não grava nada."""
        account = self.get_owned_account(account_key, account_token)
        customer = self.customer_repository.get_by_id(account.customer_id)
        piggy_bank = self.account_repository.get_piggy_bank(account)

        return AccountDTO.obj_to_dict(account, customer, piggy_bank)

    def block_account(self, account_key: str, reason: str) -> None:
        """O banco bloqueia a conta, com motivo (CLI-05). As regras, nesta ordem:

        1. a conta existe e é de cliente (404 QIT001010);
        2. trava a linha da conta (o estado é relido depois da trava);
        3. a conta está ACTIVE (409 QIT001011).

        Depois: estado BLOCKED e o evento com origem MANUAL e o motivo.
        """
        account = self._get_locked_customer_account(account_key)

        if account.status.enumerator != AccountStatus.ACTIVE:
            raise AccountNotActive(account_key, account.status.enumerator)

        self.account_repository.change_status(account, AccountStatus.BLOCKED, AccountStatusEvent.MANUAL, reason)

        self.session.commit()

    def unblock_account(self, account_key: str) -> None:
        """O banco desbloqueia a conta (CLI-05). As regras, nesta ordem:

        1. a conta existe e é de cliente (404 QIT001010);
        2. trava a linha da conta (o estado é relido depois da trava);
        3. a conta está BLOCKED (409 QIT001013).

        Depois: estado ACTIVE e o evento com origem MANUAL, sem motivo.
        """
        account = self._get_locked_customer_account(account_key)

        if account.status.enumerator != AccountStatus.BLOCKED:
            raise AccountNotBlocked(account_key, account.status.enumerator)

        self.account_repository.change_status(account, AccountStatus.ACTIVE, AccountStatusEvent.MANUAL)

        self.session.commit()

    def _get_locked_customer_account(self, account_key: str) -> Account:
        """A conta de cliente da key, travada (rotas /internal: sem token de conta)."""
        account = self.account_repository.get_customer_account(account_key)

        if account is None:
            raise AccountNotFound(account_key)

        return self.account_repository.lock_accounts([account])[0]
```

- `src/resources/internal.py` (criar): o conteúdo inteiro é:

```python
from fastapi import Response
from fastapi import status as http_status

from controllers import AccountController
from utils.schema_handler import SchemaHandler


class InternalResource:
    """As rotas da operação do banco, sob /internal (API-13).

    Pedem o INTERNAL-TOKEN e o ADMIN-TOKEN: quem confere são os
    middlewares internal_token e admin_token, antes daqui (PRD-07,
    PRD-13). Sem regra de negócio, sem SQL e sem nada guardado no self.
    """

    @SchemaHandler.validate("post_blocks.json")
    def on_post_block(self, account_key: str, payload: dict) -> Response:
        controller = AccountController()
        controller.block_account(account_key, payload["reason"])

        return Response(status_code=http_status.HTTP_204_NO_CONTENT)

    def on_post_unblock(self, account_key: str) -> Response:
        controller = AccountController()
        controller.unblock_account(account_key)

        return Response(status_code=http_status.HTTP_204_NO_CONTENT)
```

- `src/resources/__init__.py` (editar): o conteúdo inteiro passa a ser:

```python
from resources.health_check import HealthCheckResource
from resources.customer import CustomerResource
from resources.account import AccountResource
from resources.internal import InternalResource
```

- `src/app.py` (editar): três trocas, e nada mais.
  1. A linha
     ```python
     from resources import AccountResource, CustomerResource, HealthCheckResource
     ```
     vira
     ```python
     from resources import AccountResource, CustomerResource, HealthCheckResource, InternalResource
     ```
  2. A linha
     ```python
         account_resource = AccountResource()
     ```
     vira as duas linhas
     ```python
         account_resource = AccountResource()
         internal_resource = InternalResource()
     ```
  3. A linha
     ```python
         application.add_api_route("/accounts/{account_key}", account_resource.on_get_by_key, methods=["GET"])
     ```
     vira as cinco linhas
     ```python
         application.add_api_route("/accounts/{account_key}", account_resource.on_get_by_key, methods=["GET"])

         # Rotas internas (API-13): INTERNAL-TOKEN e ADMIN-TOKEN
         application.add_api_route("/internal/accounts/{account_key}/blocks", internal_resource.on_post_block, methods=["POST"])
         application.add_api_route("/internal/accounts/{account_key}/unblocks", internal_resource.on_post_unblock, methods=["POST"])
     ```
  O bloco das rotas fica exatamente assim (de `health_check_resource = HealthCheckResource()` até `register_error_handlers(application)`):
  ```python
      health_check_resource = HealthCheckResource()
      customer_resource = CustomerResource()
      account_resource = AccountResource()
      internal_resource = InternalResource()

      application.add_api_route("/", health_check_resource.on_get_home, methods=["GET"])
      application.add_api_route(
          "/health_check",
          health_check_resource.on_get_health_check,
          methods=["GET"]
      )

      # Cliente
      application.add_api_route("/customers", customer_resource.on_post, methods=["POST"])
      application.add_api_route("/customers/{customer_key}", customer_resource.on_get_by_key, methods=["GET"])

      # Conta
      application.add_api_route("/customers/{customer_key}/accounts", account_resource.on_post_account, methods=["POST"])
      application.add_api_route("/accounts/{account_key}", account_resource.on_get_by_key, methods=["GET"])

      # Rotas internas (API-13): INTERNAL-TOKEN e ADMIN-TOKEN
      application.add_api_route("/internal/accounts/{account_key}/blocks", internal_resource.on_post_block, methods=["POST"])
      application.add_api_route("/internal/accounts/{account_key}/unblocks", internal_resource.on_post_unblock, methods=["POST"])

      register_error_handlers(application)
  ```

- `tests/integration/internal/test_block_account.py` (criar; a pasta `tests/integration/internal/` é nova e fica sem `__init__.py`): o conteúdo inteiro é:

```python
"""Bloquear e desbloquear conta: POST /internal/accounts/{account_key}/blocks e /unblocks.

CLI-05: ACTIVE vira BLOCKED e volta; só o banco bloqueia (rota interna,
com motivo). CLI-09: a bloqueada continua lendo. PRD-07, PRD-13: as rotas
/internal pedem também o ADMIN-TOKEN. Sucesso: 204, sem corpo.
"""

from uuid import uuid4

from tests.utils import DbUtils, ObjectGenerator, PayloadGenerator, RequestGenerator


BLOCK_REASONS = ["SUSPICIOUS_ACTIVITY", "JUDICIAL_ORDER", "CUSTOMER_REQUEST", "MANUAL_REVIEW"]


def account_status(account: dict) -> str:
    status, response = RequestGenerator.GET_account(account["account_key"], account["account_token"])
    assert status == 200, response

    return response["status"]


def block(account: dict) -> None:
    status, response = RequestGenerator.POST_block(account["account_key"], PayloadGenerator.block())
    assert status == 204, response
    assert response is None


class TestBlockAccount:
    def test_blocks_and_unblocks(self):
        account = ObjectGenerator.create_account()

        status, response = RequestGenerator.POST_block(account["account_key"], PayloadGenerator.block("JUDICIAL_ORDER"))
        assert status == 204, response
        assert response is None
        assert account_status(account) == "BLOCKED"

        status, response = RequestGenerator.POST_unblock(account["account_key"])
        assert status == 204, response
        assert response is None
        assert account_status(account) == "ACTIVE"

    def test_accepts_every_reason(self):
        for reason in BLOCK_REASONS:
            account = ObjectGenerator.create_account()

            status, response = RequestGenerator.POST_block(account["account_key"], PayloadGenerator.block(reason))

            assert status == 204, (reason, response)
            assert account_status(account) == "BLOCKED"

    def test_block_requires_active_account(self):
        account = ObjectGenerator.create_account()
        block(account)

        status, response = RequestGenerator.POST_block(account["account_key"], PayloadGenerator.block())

        assert status == 409, response
        assert response["code"] == "QIT001011"
        assert account_status(account) == "BLOCKED"

    def test_unblock_requires_blocked_account(self):
        account = ObjectGenerator.create_account()

        status, response = RequestGenerator.POST_unblock(account["account_key"])

        assert status == 409, response
        assert response["code"] == "QIT001013"
        assert account_status(account) == "ACTIVE"

    def test_unknown_account_is_404(self):
        for account_key in [str(uuid4()), "nao-e-uma-key"]:
            status, response = RequestGenerator.POST_block(account_key, PayloadGenerator.block())
            assert status == 404, (account_key, response)
            assert response["code"] == "QIT001010"

            status, response = RequestGenerator.POST_unblock(account_key)
            assert status == 404, (account_key, response)
            assert response["code"] == "QIT001010"

    def test_requires_admin_token(self):
        DbUtils.rollback()
        blocked_account = ObjectGenerator.create_account()
        active_account = ObjectGenerator.create_account()

        block(blocked_account)

        for admin_token in [None, "token_errado"]:
            status, response = RequestGenerator.POST_block(active_account["account_key"], PayloadGenerator.block(), admin_token=admin_token)
            assert status == 403, (admin_token, response)
            assert response["code"] == "QIT000003"

            status, response = RequestGenerator.POST_unblock(blocked_account["account_key"], admin_token=admin_token)
            assert status == 403, (admin_token, response)
            assert response["code"] == "QIT000003"

        assert account_status(active_account) == "ACTIVE"
        assert account_status(blocked_account) == "BLOCKED"

    def test_refuses_body_out_of_schema(self):
        account = ObjectGenerator.create_account()
        payloads = [
            {"reason": "OUTRO_MOTIVO"},
            {"reason": "manual_review"},
            {"reason": "MANUAL_REVIEW", "extra": 1},
            {},
        ]

        for payload in payloads:
            status, response = RequestGenerator.POST_block(account["account_key"], payload)

            assert status == 400, (payload, response)
            assert response["code"] == "QIT000001"

        assert account_status(account) == "ACTIVE"

    def test_blocked_account_still_reads(self):
        account = ObjectGenerator.create_account()
        block(account)

        status, response = RequestGenerator.GET_account(account["account_key"], account["account_token"])
        assert status == 200, response
        assert response["status"] == "BLOCKED"
        assert response["balance"] == 0

        status, response = RequestGenerator.GET_customer(account["customer_key"], account["account_token"])
        assert status == 200, response
        assert response["customer_key"] == account["customer_key"]
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/05-cliente-conta`; `git log --oneline` mostra `feat(seguranca): barreira contra chute do token da conta`.
2. Crie `tests/integration/internal/test_block_account.py` com o conteúdo do campo **Arquivos**.
3. `docker compose up -d --build --wait`.
4. `./.venv/Scripts/python.exe -m pytest -v tests/integration/internal/test_block_account.py` → a última linha tem `8 failed` e não tem `passed`. Os 8 falham por asserção: hoje as rotas `/internal/accounts/...` respondem 404 `QIT000404`.
5. Edite `src/controllers/account_controller.py` com o conteúdo do campo **Arquivos**.
6. Crie `src/resources/internal.py` com o conteúdo do campo **Arquivos**.
7. Edite `src/resources/__init__.py` com o conteúdo do campo **Arquivos**.
8. Faça as três trocas em `src/app.py` e confira o bloco das rotas contra o do campo **Arquivos**.
9. `docker compose up -d --build --wait`.
10. `./.venv/Scripts/python.exe -m pytest -v tests/integration/internal/test_block_account.py` → a última linha tem `8 passed`.
11. Rode a conferência B1 do **Verificar**.
12. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `122 passed`.
13. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
14. Feche o passo (AGENTS.md, seção 7), um comando por vez:
    ```
    git add -- src/controllers/account_controller.py src/resources/internal.py src/resources/__init__.py src/app.py tests/integration/internal/test_block_account.py
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "feat(conta): bloquear e desbloquear conta pelas rotas internas"
    git log -1 --format=%B
    ```

**Testes:** `tests/integration/internal/test_block_account.py`. Efeito no banco de cada 204: o estado da conta muda e uma linha nova em `account_status_event` (conferência B1); as recusas não gravam nada além da linha de `request_log`.

| Função de teste | Entrada | Esperado |
|---|---|---|
| `test_blocks_and_unblocks` | conta nova; bloqueio com `JUDICIAL_ORDER`; leitura; desbloqueio; leitura | 204 sem corpo; `status` `BLOCKED`; 204 sem corpo; `status` `ACTIVE` |
| `test_accepts_every_reason` | uma conta nova para cada um dos 4 motivos | 204 e `BLOCKED` nas quatro |
| `test_block_requires_active_account` | conta bloqueada; bloqueio de novo | 409 `QIT001011`; continua `BLOCKED` |
| `test_unblock_requires_blocked_account` | conta `ACTIVE`; desbloqueio | 409 `QIT001013`; continua `ACTIVE` |
| `test_unknown_account_is_404` | bloqueio e desbloqueio com key UUID que não existe e com `nao-e-uma-key` | 404 `QIT001010` nos quatro |
| `test_requires_admin_token` | começa com `DbUtils.rollback()`; conta X bloqueada (com os tokens certos) e conta Y ativa; bloqueio de Y e desbloqueio de X sem `ADMIN-TOKEN` e com `ADMIN-TOKEN: token_errado` | 204 no bloqueio de X; 403 `QIT000003` nas quatro tentativas; Y continua `ACTIVE` e X continua `BLOCKED` |
| `test_refuses_body_out_of_schema` | `reason` `OUTRO_MOTIVO`; `reason` em minúsculas; campo `extra`; corpo `{}` | 400 `QIT000001` nos quatro; a conta continua `ACTIVE` |
| `test_blocked_account_still_reads` | conta bloqueada; `GET /accounts/{account_key}` e `GET /customers/{customer_key}` com o token dela | 200 com `status` `BLOCKED` e `balance` 0; 200 com o cliente (CLI-05: lê; API-17: conta não encerrada) |

**Verificar:**
- `./.venv/Scripts/python.exe -m pytest -v tests/integration/internal/test_block_account.py` → `8 passed`.
- B1 — os eventos de estado (R4, CLI-05). Um comando, numa linha só:
  ```
  ./.venv/Scripts/python.exe -c "from sqlalchemy import create_engine, text; from tests.utils import DbUtils, ObjectGenerator, PayloadGenerator, RequestGenerator; a = ObjectGenerator.create_account(); k = a['account_key']; b = RequestGenerator.POST_block(k, PayloadGenerator.block('JUDICIAL_ORDER'))[0]; u = RequestGenerator.POST_unblock(k)[0]; c = create_engine(DbUtils.database_url()).connect(); print(b, u, c.execute(text('SELECT s.enumerator, r.enumerator, e.source FROM account_status_event e JOIN account m ON m.id = e.account_id JOIN account_status s ON s.id = e.status_id LEFT JOIN block_reason r ON r.id = e.block_reason_id WHERE m.account_key = :k ORDER BY e.id'), {'k': k}).fetchall())"
  ```
  → as duas primeiras linhas são `Expecting value: line 1 column 1 (char 0)` (as duas respostas 204); a última linha é exatamente:
  ```
  204 204 [('ACTIVE', None, None), ('BLOCKED', 'JUDICIAL_ORDER', 'MANUAL'), ('ACTIVE', None, 'MANUAL')]
  ```
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `122 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/app.py
  src/controllers/account_controller.py
  src/resources/__init__.py
  src/resources/internal.py
  tests/integration/internal/test_block_account.py
  ```
- `git log -1 --format=%B` → `feat(conta): bloquear e desbloquear conta pelas rotas internas`

**Pronto quando:**
- [ ] Os 8 testes falharam antes do código (item 4) e passam depois (item 10).
- [ ] A B1 dá a linha esperada.
- [ ] Suíte com `122 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/05-cliente-conta`.

**Commit:** `feat(conta): bloquear e desbloquear conta pelas rotas internas`
**Pare se:**
- O item 4 não terminar com `8 failed`.
- `test_requires_admin_token` receber `QIT000002` onde o plano espera `QIT000003`: o `INTERNAL-TOKEN` não está chegando (confira o `RequestGenerator` do 4.7, sem mudá-lo).
- A B1 mostrar outra lista de eventos depois de 3 tentativas de conferir os arquivos do passo contra o plano.
- A suíte não terminar com `122 passed`.

---

### Passo 5.11 — `DELETE /accounts/{account_key}`
**Branch:** fase/05-cliente-conta · **Depende de:** 5.10
**Objetivo:** `AccountController.close_account` (só o dono, só conta `ACTIVE`) e a rota `DELETE /accounts/{account_key}` (tokens: conta): 204 sem corpo; 404 `QIT001010`; 409 `QIT001011`. Depois de encerrar, a conta só lê e o cliente abre outra.
**Decisões:** CLI-04 — uma conta aberta, depois de encerrar abre outra · CLI-05 — estados da conta (`CLOSED` é final; só o dono encerra) · CLI-06 — encerrar zerada (parte do estado; saldo no 6.12, cofrinho no 7.15) · CLI-09 — bloqueada não encerra · API-17 — encerrada não consulta o cliente · R8 — outro dono → 404 · API-02 — 204 · R4 — append-only · MOV-05, MOV-11 — trava antes de conferir o estado · TST-01 — black box e TDD
**Arquivos:**
- `src/controllers/account_controller.py` (editar): o conteúdo inteiro passa a ser o do passo 5.10, com um método novo, `close_account`, escrito logo depois de `unblock_account` e antes de `_get_locked_customer_account`. O método inteiro (com a linha em branco antes dele, como os outros):

```python
    def close_account(self, account_key: str, account_token: str) -> None:
        """O dono encerra a conta (CLI-05, CLI-06). As regras, nesta ordem:

        1. a conta é do dono do token (404 QIT001010, R8);
        2. trava a linha da conta (o estado é relido depois da trava);
        3. a conta está ACTIVE (409 QIT001011): bloqueada precisa ser
           desbloqueada antes, e encerrada é final.

        O saldo zero entra no passo 6.12 e o cofrinho zerado, no 7.15,
        entre a regra 3 e a gravação. Depois: estado CLOSED e o evento,
        sem origem e sem motivo (quem muda é o dono).
        """
        account = self.get_owned_account(account_key, account_token)
        account = self.account_repository.lock_accounts([account])[0]

        if account.status.enumerator != AccountStatus.ACTIVE:
            raise AccountNotActive(account_key, account.status.enumerator)

        self.account_repository.change_status(account, AccountStatus.CLOSED)

        self.session.commit()
```

  Os imports não mudam: `AccountNotActive` e `AccountStatus` já estão no arquivo.

- `src/resources/account.py` (editar): o conteúdo inteiro passa a ser:

```python
from fastapi import Request, Response
from fastapi import status as http_status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from constants import ACCOUNT_TOKEN_HEADER
from controllers import AccountController


class AccountResource:
    """A porta HTTP da conta. Sem regra de negócio, sem SQL e sem nada guardado no self (ARQ-02).

    O token da conta chega no cabeçalho ACCOUNT-TOKEN (API-16); quem o
    confere é o controller (BaseController.get_owned_account).
    """

    def on_post_account(self, customer_key: str) -> JSONResponse:
        controller = AccountController()
        account = controller.open_account(customer_key)

        return JSONResponse(
            content=jsonable_encoder(account),
            status_code=http_status.HTTP_201_CREATED,
        )

    def on_get_by_key(self, account_key: str, request: Request) -> JSONResponse:
        controller = AccountController()
        account = controller.get_account(account_key, request.headers.get(ACCOUNT_TOKEN_HEADER))

        return JSONResponse(
            content=jsonable_encoder(account),
            status_code=http_status.HTTP_200_OK,
        )

    def on_delete_by_key(self, account_key: str, request: Request) -> Response:
        controller = AccountController()
        controller.close_account(account_key, request.headers.get(ACCOUNT_TOKEN_HEADER))

        return Response(status_code=http_status.HTTP_204_NO_CONTENT)
```

- `src/app.py` (editar): uma troca, e nada mais. A linha
  ```python
      application.add_api_route("/accounts/{account_key}", account_resource.on_get_by_key, methods=["GET"])
  ```
  vira as duas linhas
  ```python
      application.add_api_route("/accounts/{account_key}", account_resource.on_get_by_key, methods=["GET"])
      application.add_api_route("/accounts/{account_key}", account_resource.on_delete_by_key, methods=["DELETE"])
  ```

- `tests/integration/accounts/test_close_account.py` (criar): o conteúdo inteiro é:

```python
"""Encerrar conta: DELETE /accounts/{account_key} (CLI-04, CLI-05, CLI-06, CLI-09, API-17, R8).

Só o dono encerra (404 QIT001010 para os outros), e só conta ACTIVE (409
QIT001011). Encerrada é final e só lê; depois dela, o cliente abre outra
conta. Saldo e cofrinho zerados entram nos passos 6.12 e 7.15. Os testes
que erram o token começam com DbUtils.rollback() (PRD-10).
"""

from tests.utils import DbUtils, ObjectGenerator, PayloadGenerator, RequestGenerator


def account_status(account: dict) -> str:
    status, response = RequestGenerator.GET_account(account["account_key"], account["account_token"])
    assert status == 200, response

    return response["status"]


def close(account: dict) -> None:
    status, response = RequestGenerator.DELETE_account(account["account_key"], account["account_token"])
    assert status == 204, response
    assert response is None


def assert_not_active(status: int, response: dict) -> None:
    assert status == 409, response
    assert response["code"] == "QIT001011"


def assert_account_not_found(status: int, response: dict) -> None:
    assert status == 404, response
    assert response["code"] == "QIT001010"


class TestCloseAccount:
    def test_closes_account(self):
        account = ObjectGenerator.create_account()

        close(account)

        status, response = RequestGenerator.GET_account(account["account_key"], account["account_token"])
        assert status == 200, response
        assert response["status"] == "CLOSED"
        assert response["balance"] == 0

    def test_closed_account_cannot_be_closed_again(self):
        account = ObjectGenerator.create_account()
        close(account)

        status, response = RequestGenerator.DELETE_account(account["account_key"], account["account_token"])

        assert_not_active(status, response)
        assert account_status(account) == "CLOSED"

    def test_blocked_account_cannot_be_closed(self):
        account = ObjectGenerator.create_account()

        status, response = RequestGenerator.POST_block(account["account_key"], PayloadGenerator.block())
        assert status == 204, response

        status, response = RequestGenerator.DELETE_account(account["account_key"], account["account_token"])
        assert_not_active(status, response)
        assert account_status(account) == "BLOCKED"

        status, response = RequestGenerator.POST_unblock(account["account_key"])
        assert status == 204, response

        close(account)
        assert account_status(account) == "CLOSED"

    def test_customer_opens_new_account_after_closing(self):
        old_account = ObjectGenerator.create_account()
        close(old_account)

        status, response = RequestGenerator.POST_account(old_account["customer_key"])
        assert status == 201, response
        new_account = {
            "customer_key": old_account["customer_key"],
            "account_key": response["account_key"],
            "account_token": response["account_token"],
        }
        assert new_account["account_key"] != old_account["account_key"]
        assert new_account["account_token"] != old_account["account_token"]

        status, response = RequestGenerator.GET_account(new_account["account_key"], new_account["account_token"])
        assert status == 200, response
        assert response["status"] == "ACTIVE"
        assert response["balance"] == 0

        assert account_status(old_account) == "CLOSED"

        status, response = RequestGenerator.GET_customer(old_account["customer_key"], old_account["account_token"])
        assert status == 404, response
        assert response["code"] == "QIT001008"

        status, response = RequestGenerator.GET_customer(new_account["customer_key"], new_account["account_token"])
        assert status == 200, response

        status, response = RequestGenerator.POST_account(old_account["customer_key"])
        assert status == 409, response
        assert response["code"] == "QIT001009"

    def test_closed_account_cannot_be_blocked_or_unblocked(self):
        account = ObjectGenerator.create_account()
        close(account)

        status, response = RequestGenerator.POST_block(account["account_key"], PayloadGenerator.block())
        assert_not_active(status, response)

        status, response = RequestGenerator.POST_unblock(account["account_key"])
        assert status == 409, response
        assert response["code"] == "QIT001013"

        assert account_status(account) == "CLOSED"

    def test_other_account_token_is_404(self):
        DbUtils.rollback()
        first = ObjectGenerator.create_account()
        second = ObjectGenerator.create_account()

        status, response = RequestGenerator.DELETE_account(first["account_key"], second["account_token"])
        assert_account_not_found(status, response)
        assert account_status(first) == "ACTIVE"

        close(first)

    def test_missing_or_wrong_token_is_404(self):
        DbUtils.rollback()
        account = ObjectGenerator.create_account()

        for account_token in [None, "token_errado"]:
            status, response = RequestGenerator.DELETE_account(account["account_key"], account_token)
            assert_account_not_found(status, response)

        assert account_status(account) == "ACTIVE"
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/05-cliente-conta`; `git log --oneline` mostra `feat(conta): bloquear e desbloquear conta pelas rotas internas`.
2. Crie `tests/integration/accounts/test_close_account.py` com o conteúdo do campo **Arquivos**.
3. `docker compose up -d --build --wait`.
4. `./.venv/Scripts/python.exe -m pytest -v tests/integration/accounts/test_close_account.py` → a última linha tem `7 failed` e não tem `passed`. Os 7 falham por asserção de status: hoje `DELETE /accounts/{account_key}` responde 405 `QIT000405` (o caminho existe só com `GET`).
5. Edite `src/controllers/account_controller.py`: acrescente o método `close_account` do campo **Arquivos** entre `unblock_account` e `_get_locked_customer_account`.
6. Edite `src/resources/account.py` com o conteúdo do campo **Arquivos**.
7. Faça a troca em `src/app.py`.
8. `docker compose up -d --build --wait`.
9. `./.venv/Scripts/python.exe -m pytest -v tests/integration/accounts/test_close_account.py` → a última linha tem `7 passed`.
10. Rode a conferência E1 do **Verificar**.
11. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `129 passed`.
12. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
13. Feche o passo (AGENTS.md, seção 7), um comando por vez:
    ```
    git add -- src/controllers/account_controller.py src/resources/account.py src/app.py tests/integration/accounts/test_close_account.py
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "feat(conta): rota de encerramento da conta pelo dono"
    git log -1 --format=%B
    ```

**Testes:** `tests/integration/accounts/test_close_account.py`. Efeito no banco de cada 204: a conta fica `CLOSED` e uma linha nova em `account_status_event` (conferência E1); as recusas não gravam nada além da linha de `request_log`.

| Função de teste | Entrada | Esperado |
|---|---|---|
| `test_closes_account` | conta nova; `DELETE /accounts/{account_key}` com o token dela; leitura | 204 sem corpo; 200 com `status` `CLOSED` e `balance` 0 (encerrada só lê) |
| `test_closed_account_cannot_be_closed_again` | conta encerrada; `DELETE` de novo | 409 `QIT001011`; continua `CLOSED` |
| `test_blocked_account_cannot_be_closed` | conta bloqueada; `DELETE`; desbloqueio; `DELETE` | 409 `QIT001011` e continua `BLOCKED`; 204; 204 e `CLOSED` |
| `test_customer_opens_new_account_after_closing` | conta encerrada; nova abertura para o mesmo cliente; leituras; `GET /customers/{customer_key}` com o token velho e com o novo; terceira abertura | 201 com key e token novos; a nova `ACTIVE` com `balance` 0; a velha `CLOSED`; 404 `QIT001008` com o token velho e 200 com o novo (API-17); 409 `QIT001009` (CLI-04) |
| `test_closed_account_cannot_be_blocked_or_unblocked` | conta encerrada; bloqueio; desbloqueio | 409 `QIT001011`; 409 `QIT001013`; continua `CLOSED` |
| `test_other_account_token_is_404` | começa com `DbUtils.rollback()`; contas A e B; `DELETE` de A com o token de B; leitura de A; `DELETE` de A com o token de A | 404 `QIT001010`; A continua `ACTIVE`; 204 |
| `test_missing_or_wrong_token_is_404` | começa com `DbUtils.rollback()`; `DELETE` de A sem `ACCOUNT-TOKEN` e com `token_errado` | 404 `QIT001010` nos dois; A continua `ACTIVE` |

**Verificar:**
- `./.venv/Scripts/python.exe -m pytest -v tests/integration/accounts/test_close_account.py` → `7 passed`.
- E1 — o evento do encerramento (R4, CLI-05). Um comando, numa linha só:
  ```
  ./.venv/Scripts/python.exe -c "from sqlalchemy import create_engine, text; from tests.utils import DbUtils, ObjectGenerator, RequestGenerator; a = ObjectGenerator.create_account(); k = a['account_key']; d = RequestGenerator.DELETE_account(k, a['account_token'])[0]; c = create_engine(DbUtils.database_url()).connect(); print(d, c.execute(text('SELECT s.enumerator, e.block_reason_id, e.source FROM account_status_event e JOIN account m ON m.id = e.account_id JOIN account_status s ON s.id = e.status_id WHERE m.account_key = :k ORDER BY e.id'), {'k': k}).fetchall())"
  ```
  → a primeira linha é `Expecting value: line 1 column 1 (char 0)` (a resposta 204); a última linha é exatamente:
  ```
  204 [('ACTIVE', None, None), ('CLOSED', None, None)]
  ```
- `git grep -n -e "session.delete" -e "\.delete(" -- src` → nenhuma linha (R4: nada é apagado; encerrar muda o estado).
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `129 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/app.py
  src/controllers/account_controller.py
  src/resources/account.py
  tests/integration/accounts/test_close_account.py
  ```
- `git log -1 --format=%B` → `feat(conta): rota de encerramento da conta pelo dono`

**Pronto quando:**
- [ ] Os 7 testes falharam antes do código (item 4) e passam depois (item 9).
- [ ] A E1 dá a linha esperada; o `git grep` não acha `delete`.
- [ ] Suíte com `129 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/05-cliente-conta`.

**Commit:** `feat(conta): rota de encerramento da conta pelo dono`
**Pare se:**
- O item 4 não terminar com `7 failed`.
- `test_customer_opens_new_account_after_closing` receber 409 `QIT001009` na nova abertura: a conta encerrada ainda conta como aberta.
- A E1 mostrar outra lista de eventos depois de 3 tentativas de conferir os arquivos do passo contra o plano.
- A suíte não terminar com `129 passed`.

---

### Passo 5.fim — Fechar a fase
**Branch:** fase/05-cliente-conta · **Depende de:** 5.1 a 5.11
**Objetivo:** provar a fase com o banco recriado do zero e levá-la para a `main` com a tag `fase-05`.
**Decisões:** TIM-04 — git por fase · TIM-08 — git automático · ARQ-03 — SQL só com o banco vazio · ARQ-04 — sobe sem `.env` · TST-01 — suíte inteira verde
**Arquivos:** nenhum. O passo não cria, não edita e não apaga arquivo.
**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/05-cliente-conta`.
2. `git log --oneline -n 12` → tem as 11 mensagens dos passos 5.1 a 5.11, cada uma uma vez:
   ```
   feat(cliente): repository e DTO do cliente
   feat(cliente): controller com as regras do cadastro
   feat(cliente): rota de cadastro de cliente
   feat(conta): token da conta e repositories da conta e da categoria padrão
   feat(conta): DTO, controller e checagem de dono da conta
   feat(conta): rota de abertura de conta
   feat(conta): rota de consulta da conta com checagem de dono
   feat(cliente): rota de consulta do cliente pelo dono
   feat(seguranca): barreira contra chute do token da conta
   feat(conta): bloquear e desbloquear conta pelas rotas internas
   feat(conta): rota de encerramento da conta pelo dono
   ```
3. Recrie o banco do zero e suba tudo, um comando por vez:
   ```
   docker compose down -v
   docker compose up -d --build --wait
   ```
4. Rode a conferência A1 (passo 5.6) → as 5 linhas do **Verificar** do passo 5.6.
5. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `129 passed`.
6. `./.venv/Scripts/python.exe -m pytest` de novo → a última linha tem `129 passed` (nada intermitente).
7. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
8. `git status --short` → saída vazia.
9. Leve a fase para a `main`, um comando por vez:
   ```
   git switch main
   git merge --no-ff --no-edit -m "feat(cliente-conta): fase 05 com cadastro de cliente, conta com token, bloqueio e encerramento" fase/05-cliente-conta
   git tag fase-05
   ```
10. Rode o **Verificar**.

**Testes:** nenhum teste novo. A suíte inteira (63 de integração + 66 unitários) roda duas vezes com o banco recriado do zero (itens 5 e 6).
**Verificar:**
- O `git status --short` antes do merge não mostra alterações.
- `git branch --show-current` → `main`.
- `git log -1 --format=%B` → `feat(cliente-conta): fase 05 com cadastro de cliente, conta com token, bloqueio e encerramento`.
- `git log -1 --format=%P` → dois hashes separados por um espaço (é um merge).
- `git tag --list fase-05` → `fase-05`.
- `git status --short` → saída vazia.

**Pronto quando:**
- [ ] A A1 dá o esperado com o banco recriado do zero.
- [ ] Suíte com `129 passed`, duas vezes seguidas; lint sem saída.
- [ ] Merge `--no-ff` na `main` com a mensagem exata; tag `fase-05` criada localmente; merge local na `main`.

**Commit:** nenhum commit de passo. Mensagem do merge: `feat(cliente-conta): fase 05 com cadastro de cliente, conta com token, bloqueio e encerramento`
**Pare se:**
- Faltar uma das 11 mensagens do item 2.
- `docker compose up -d --build --wait` falhar: rode `docker compose logs --tail 100 db` e `docker compose logs --tail 100 api` e traga as duas saídas.
- A A1 der outra saída.
- A suíte não terminar com `129 passed` nas duas rodadas, ou o lint imprimir qualquer linha.
- O merge local der conflito (AGENTS.md, seção 8, item 9).

---

## Divergências encontradas

Seção para o Bruno; o agente não executa nada daqui.

| # | Onde | O que foi feito |
|---|---|---|
| 1 | PLANO-00, passo 5.2: "CPF válido → CPF único → e-mail único → idade". A data que não existe (`QIT001007`) não tem lugar na ordem; o base a conferia primeiro. | Entra logo antes da idade: CPF válido → CPF único → e-mail único → data que existe → idade. `test_checks_rules_in_order` prova a ordem. |
| 2 | CLI-03 não diz se a idade conta pela data real ou pelo relógio do banco (DIA-01 lista o que usa o relógio: rendimento, recorde, carência, limite diário). | Data real (`date.today()`), como o base. O container roda em UTC: o teste do "faz 18 anos" usa uma folga de 2 dias para não falhar entre 21h e 24h no horário de Brasília. |
| 3 | 09, "Conta: cliente em estado que não permite → 409". CLI-05: o cliente não tem estado. | Sem teste próprio; o único 409 da abertura é o `QIT001009`, testado. Tirar a linha do 09. |
| 4 | 09, "abrir conta para cliente que não existe → 404, e nenhuma conta criada". TST-01 proíbe o teste de ler o banco. | O teste prova o 404 e o corpo sem `account_key`; a contagem de linhas fica na conferência A2 do 5.6. |
| 5 | PLANO-00, passos 5.10 e 5.11: não citam `lock_accounts`. | Bloquear, desbloquear e encerrar travam a linha da conta antes de conferir o estado (o mesmo `with_for_update` da MOV-05), para dois pedidos ao mesmo tempo não decidirem pelo estado velho. |
| 6 | PRD-10 conta o token da conta "por conta + IP", e `GET /customers/{customer_key}` não tem conta no caminho. | PRD-15: a fase 5.9 resolve a conta aberta antes da barreira e compartilha conta + IP; sem conta, usa o fallback da customer_key normalizada. Provas no passo 11.6. |
| 7 | AGENTS.md, seção 6: teste que erra token começa com `DbUtils.rollback()`. A falha do token da conta é contada por conta, e cada teste cria a sua. | Seguido assim mesmo, em todo teste que erra `INTERNAL-TOKEN`, `ADMIN-TOKEN` ou `ACCOUNT-TOKEN`. |
| 8 | Nenhuma decisão diz o estado do cofrinho quando a conta é bloqueada ou encerrada, nem se a abertura grava evento. | O cofrinho nasce `ACTIVE` e não muda: quem manda é o estado da conta principal. A abertura grava o evento `ACTIVE` da conta (origem vazia) e o evento `ACTIVE` da categoria "economias"; o encerramento grava `CLOSED` com origem vazia. Na fase 9, a categoria criada pelo dono deve gravar o evento `ACTIVE` também, pelo mesmo motivo. |
| 9 | `rank_id` e `yield_rank_id` aceitam nulo, e nenhuma decisão diz o valor inicial. | A conta nasce com os dois em `DEFAULT` (GAM-13: padrão a partir de R$ 0). As fases 7 e 8 podem contar com eles preenchidos. |

## Nomes novos da fase 05 (registrar no PLANO-00)

Seção para o Bruno; o agente não executa nada daqui.

| Onde | Nomes |
|---|---|
| `CustomerRepository` | `get_by_id(customer_id)` (para o `customer_key` no `GET` da conta); assinatura `create(name, document_number, email, birthdate)` |
| `CustomerController` | constante `MINIMUM_AGE = 18`; `create(customer_data)`; `get_by_key(customer_key, account_token)`; `_parse_birthdate`, `_age_in_years` |
| `CustomerDTO` | `obj_to_dict(customer)`, `only_obj_key(customer)` |
| `src/utils/account_token.py` | `ACCOUNT_TOKEN_BYTES = 32`; `account_token_matches(account_token, token_hash)` aceita `None` nos dois e devolve `False` |
| `AccountRepository` | `create_customer_account(customer, token_hash)` (cria a conta, o cofrinho e o evento `ACTIVE`; ranque `DEFAULT`); `get_by_key(account_key)`; `get_customer_account(account_key)`; `get_open_account_by_customer(customer)`; `get_piggy_bank(account)`; `get_system_account(account_type_enumerator)`; `lock_accounts(accounts)` (devolve a lista travada, na ordem do `id`); `change_status(account, status_enumerator, source=None, block_reason_enumerator=None)`; `_add_status_event`, `_get_fixed_type` |
| `CategoryRepository` | constante `DEFAULT_CATEGORY_NAME = "economias"`; `create_default(piggy_bank)` (grava o evento `ACTIVE`); `get_default(piggy_bank)` |
| `AccountDTO` | `obj_to_dict(account, customer, piggy_bank)`; `open_account_to_dict(account, account_token)` |
| `BaseController` | `mark_account_auth_failure()`; `get_owned_account(account_key, account_token)` |
| `AccountController` | `open_account(customer_key)`; `get_account(account_key, account_token)`; `block_account(account_key, reason)`; `unblock_account(account_key)`; `close_account(account_key, account_token)`; `_get_locked_customer_account(account_key)` |
| Resources | `CustomerResource.on_post`, `on_get_by_key(customer_key, request)`; `AccountResource.on_post_account(customer_key)`, `on_get_by_key(account_key, request)`, `on_delete_by_key(account_key, request)`; `InternalResource.on_post_block(account_key, payload)`, `on_post_unblock(account_key)`. O `ACCOUNT-TOKEN` é lido no resource por `request.headers.get(ACCOUNT_TOKEN_HEADER)` |
| `src/middlewares/auth_barrier.py` | `ACCOUNT_AUTH_FAILURES`; `count_failures(client_ip, account_key)` |
| Testes | pastas `tests/integration/customers/`, `tests/integration/accounts/`, `tests/integration/internal/`; ajudantes locais `assert_no_internal_id`, `birthdate_for_age`, `birthdate_turning_age_in_two_days`, `account_status`; chave malformada de teste `nao-e-uma-key` |
| Comportamento | o fechamento da conta (6.12, 7.15) entra entre a regra 3 do `close_account` e o `change_status`; o bloqueio automático (6.9) usa `change_status(account, AccountStatus.BLOCKED, AccountStatusEvent.AUTOMATIC, BlockReason.SUSPICIOUS_ACTIVITY)` |
