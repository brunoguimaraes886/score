> **Git local — Bruno, 08/10/2026:** durante a produção, branches, commits, merges e tags ficam locais. Não executar push, pull ou fetch nem exigir acesso ao GitHub. O envio completo será feito pelo Bruno somente no final, quando tudo estiver pronto. As verificações de commits e dependências são locais.

# PLANO — Fase 02 — banco

**Branch:** `fase/02-banco` · **Depende de:** fase 0
**Objetivo:** preparar o ambiente de teste, apagar o `sample_entity`, escrever o `database/database.sql` com as 22 tabelas e criar um model por tabela.

Regras de execução: `AGENTS.md`. Nomes obrigatórios: `docs/plano/PLANO-00-indice.md`. Um passo por vez, na ordem: 2.1 a 2.13 e, por último, 2.fim.

Nos passos que apagam arquivo, o `git rm` acontece no item do **Passo a passo** que o manda, antes dos testes, para a suíte rodar sem o arquivo. No fim desses passos, o `git rm` da seção 7 do `AGENTS.md` não se repete: o arquivo já está fora.

Contagem de testes da suíte nesta fase: 35 no base (29 do `sample_entity` + 6 do `test_healthcheck.py`); 6 a partir do passo 2.2.

Comandos novos nesta fase (não estão na seção 3 do `AGENTS.md`):

| Quero | Comando |
|---|---|
| Rodar uma consulta no banco do compose | `docker compose exec -T db psql -U bootcamp -d bootcamp -t -A -c "<consulta>"` |
| Rodar uma linha de Python no `.venv` | `./.venv/Scripts/python.exe -c "<código>"` |
| Listar os arquivos de uma pasta no Git | `git ls-files <pasta>` |

O `-T` desliga o terminal interativo, que o Git Bash não oferece. O `-t -A` tira cabeçalho, rodapé e alinhamento da saída do `psql`.

---

### Passo 2.1 — Preparar o ambiente
**Branch:** fase/02-banco · **Depende de:** fase 0 (commit `chore: base do bootcamp, AGENTS.md e plano` e commit `docs(plano): roteiros auditados`, os dois na `main`)
**Objetivo:** `.venv` com as dependências e o `flake8`, `pytest.ini` com `pythonpath = src` e os testes apontando para `127.0.0.1`.
**Decisões:** TST-05 — unitários em pasta separada (o `pytest.ini` deixa o import achar `src/`); ARQ-04 — sobe sem `.env`; ARQ-01 — stack do base.
**Arquivos:**
- `requirements-dev.txt` (editar): o conteúdo inteiro passa a ser:

```text
# Dependencias que so o desenvolvedor precisa (rodar teste, ler .env).
# Nao vao para dentro da imagem que sobe em producao.

-r requirements.txt

pytest==7.4.4
pytest-cov==4.1.0
python-dotenv==1.0.1
flake8==7.1.1
```

- `pytest.ini` (criar, na raiz do repositório): o conteúdo inteiro é:

```ini
[pytest]
pythonpath = src
```

- `tests/conftest.py` (editar): o conteúdo inteiro passa a ser:

```python
from pathlib import Path
from os import path, environ

root = Path(__file__).resolve().parents[1]

if not environ.get("APP_ENV") or environ.get("APP_ENV") == "local":
    from dotenv import load_dotenv

    load_dotenv(path.join(str(root), ".env"))

    if environ.get("SERVER_LOCALHOST") is None:
        environ["SERVER_LOCALHOST"] = "127.0.0.1"
```

- `tests/utils/requisition.py` (editar): troque o host e limite a espera HTTP dos testes.
  - Antes: `        api_host = environ.get("SERVER_LOCALHOST", "0.0.0.0")`
  - Depois: `        api_host = environ.get("SERVER_LOCALHOST", "127.0.0.1")`
  - Na chamada `request(...)`, logo depois de `params=query_params,`, acrescente `timeout=30,`. Sem resposta por 30 segundos, o teste falha com timeout em vez de ficar preso, inclusive nas provas de concorrência.
- `.env.example` (editar): troque uma linha só.
  - Antes: `SERVER_LOCALHOST=0.0.0.0`
  - Depois: `SERVER_LOCALHOST=127.0.0.1`

**Passo a passo:**
1. Abra a fase (AGENTS.md, seção 7): `git status --short` → saída vazia; depois, um por vez:
   ```
   git switch main
   git switch -c fase/02-banco
   ```
2. `git log --oneline` → mostra `docs(plano): roteiros auditados` e `chore: base do bootcamp, AGENTS.md e plano`.
3. Crie o ambiente virtual: `python -m venv .venv`.
4. `./.venv/Scripts/python.exe --version` → uma linha que começa com `Python 3.11.`.
5. Edite `requirements-dev.txt` com o conteúdo do campo **Arquivos**.
6. `./.venv/Scripts/python.exe -m pip install -r requirements-dev.txt` → termina com código 0, sem `ERROR`; uma instalação já satisfeita (`Requirement already satisfied`) também passa.
7. Crie `pytest.ini` com o conteúdo do campo **Arquivos**.
8. Edite `tests/conftest.py`, `tests/utils/requisition.py` e `.env.example` como no campo **Arquivos**.
9. `docker compose up -d --build --wait`.
10. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `35 passed`.
11. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
12. Feche o passo (AGENTS.md, seção 7), um comando por vez:
    ```
    git add -- requirements-dev.txt pytest.ini tests/conftest.py tests/utils/requisition.py .env.example
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "chore(ambiente): venv com flake8, pytest.ini e testes em 127.0.0.1"
    git log -1 --format=%B
    ```

**Testes:** nenhum teste novo. A suíte do base (35 testes) é a prova de que nada quebrou.
**Verificar:**
- `./.venv/Scripts/python.exe -m flake8 --version` → a primeira palavra é `7.1.1`.
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `35 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente estas 5 linhas, nesta ordem:
  ```
  .env.example
  pytest.ini
  requirements-dev.txt
  tests/conftest.py
  tests/utils/requisition.py
  ```
- `git log -1 --format=%B` → `chore(ambiente): venv com flake8, pytest.ini e testes em 127.0.0.1`

**Pronto quando:**
- [ ] `.venv` existe e tem o `flake8` 7.1.1.
- [ ] `pytest.ini` na raiz, com as 2 linhas do plano.
- [ ] Nenhum `0.0.0.0` em `tests/conftest.py`, `tests/utils/requisition.py` e `.env.example`.
- [ ] Suíte com `35 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/02-banco`.

**Commit:** `chore(ambiente): venv com flake8, pytest.ini e testes em 127.0.0.1`
**Pare se:**
- `python -m venv .venv` falha ou o comando `python` não existe.
- O `pip install` mostra `ERROR`.
- O lint imprime qualquer linha. Os arquivos do base não se corrigem neste passo: traga a saída no relatório.
- A suíte não termina com `35 passed`.

---

### Passo 2.2 — Apagar os testes do sample_entity
**Branch:** fase/02-banco · **Depende de:** 2.1
**Objetivo:** `tests/integration/` só com `test_healthcheck.py`.
**Decisões:** ARQ-11 — pode apagar o `sample_entity`.
**Arquivos:**
- `tests/integration/sample_entity/test_sample_entities.py` (apagar)
- `tests/integration/sample_entity/test_sample_entity_create.py` (apagar)
- `tests/integration/sample_entity/test_sample_entity_get.py` (apagar)
- `tests/integration/sample_entity/test_sample_entity_update.py` (apagar)

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/02-banco`; `git log --oneline` mostra `chore(ambiente): venv com flake8, pytest.ini e testes em 127.0.0.1`.
2. Apague os 4 arquivos, num comando:
   ```
   git rm -- tests/integration/sample_entity/test_sample_entities.py tests/integration/sample_entity/test_sample_entity_create.py tests/integration/sample_entity/test_sample_entity_get.py tests/integration/sample_entity/test_sample_entity_update.py
   ```
3. `docker compose up -d --build --wait`.
4. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `6 passed`.
5. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
6. Feche o passo, um comando por vez (sem `git add` e sem `git rm`: nada foi criado nem editado, e o `git rm` foi o item 2):
   ```
   git diff --cached --name-only
   git diff --name-only
   git ls-files --others --exclude-standard
   git commit -m "test: remove os testes do sample_entity"
   git log -1 --format=%B
   ```

**Testes:** nenhum teste novo. O passo apaga 29 testes do `sample_entity`, por ordem deste plano (ARQ-11); a suíte fica com os 6 de `tests/integration/test_healthcheck.py`.
**Verificar:**
- `git ls-files tests/integration` → uma linha só: `tests/integration/test_healthcheck.py`
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `6 passed`.
- `git diff --cached --name-only` (antes do commit) → exatamente as 4 linhas:
  ```
  tests/integration/sample_entity/test_sample_entities.py
  tests/integration/sample_entity/test_sample_entity_create.py
  tests/integration/sample_entity/test_sample_entity_get.py
  tests/integration/sample_entity/test_sample_entity_update.py
  ```

**Pronto quando:**
- [ ] `git ls-files tests/integration/sample_entity` não imprime arquivos; `__pycache__` ignorado pode continuar no disco.
- [ ] Suíte com `6 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata.

**Commit:** `test: remove os testes do sample_entity`
**Pare se:**
- O `git rm` responde `did not match any files`.
- A suíte não termina com `6 passed`.
- Sobra qualquer arquivo em `tests/integration/sample_entity/`.

---

### Passo 2.3 — Apagar as rotas do sample_entity
**Branch:** fase/02-banco · **Depende de:** 2.2
**Objetivo:** `src/app.py` só com `/` e `/health_check`; `src/resources/__init__.py` só com `HealthCheckResource`.
**Decisões:** ARQ-11 — pode apagar o `sample_entity`.
**Arquivos:**
- `src/resources/sample_entity.py` (apagar)
- `src/resources/__init__.py` (editar): o conteúdo inteiro passa a ser:

```python
from resources.health_check import HealthCheckResource
```

- `src/app.py` (editar): três trocas, e nada mais. Os comentários do arquivo ficam como estão.
  1. Troque a linha
     ```python
     from resources import HealthCheckResource, SampleEntityResource
     ```
     por
     ```python
     from resources import HealthCheckResource
     ```
  2. Apague a linha
     ```python
         sample_entity_resource = SampleEntityResource()
     ```
     A linha `    health_check_resource = HealthCheckResource()`, logo acima dela, fica.
  3. Apague o bloco inteiro abaixo (as 5 rotas do `sample_entity` e a linha em branco que vem antes dele), que fica entre o fecha-parêntese da rota `/health_check` e a linha `    register_error_handlers(application)`:
     ```python

         application.add_api_route(
             "/sample_entity",
             sample_entity_resource.on_post,
             methods=["POST"],
         )
         application.add_api_route(
             "/sample_entity/{sample_entity_key}",
             sample_entity_resource.on_get_by_key,
             methods=["GET"],
         )
         application.add_api_route(
             "/sample_entity/{sample_entity_key}",
             sample_entity_resource.on_put_by_key,
             methods=["PUT"],
         )
         application.add_api_route(
             "/webhook/sample_entity/{sample_entity_key}/increment_counter",
             sample_entity_resource.on_put_increment_counter,
             methods=["PUT"],
         )
         application.add_api_route(
             "/sample_entities",
             sample_entity_resource.on_get_list,
             methods=["GET"],
         )
     ```
     Depois da troca, o trecho fica exatamente assim:
     ```python
         health_check_resource = HealthCheckResource()

         application.add_api_route("/", health_check_resource.on_get_home, methods=["GET"])
         application.add_api_route(
             "/health_check",
             health_check_resource.on_get_health_check,
             methods=["GET"]
         )

         register_error_handlers(application)

         return application
     ```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → vazio; `git branch --show-current` → `fase/02-banco`; `git log --oneline` mostra `test: remove os testes do sample_entity`.
2. `git rm -- src/resources/sample_entity.py`
3. Edite `src/resources/__init__.py` como no campo **Arquivos**.
4. Faça as três trocas em `src/app.py`.
5. `docker compose up -d --build --wait`.
6. Rode os comandos do **Verificar**, na ordem.
7. Feche o passo, um comando por vez:
   ```
   git add -- src/app.py src/resources/__init__.py
   git diff --cached --name-only
   git diff --name-only
   git ls-files --others --exclude-standard
   git commit -m "refactor(api): remove as rotas do sample_entity"
   git log -1 --format=%B
   ```

**Testes:** nenhum teste novo. A rota que sumiu é conferida pelo `curl.exe` do **Verificar**; os 6 testes de `test_healthcheck.py` provam que a API sobe sem o resource.
**Verificar:**
- `curl.exe -s -i -H "INTERNAL-TOKEN: default_token" http://127.0.0.1:3000/sample_entities` → a primeira linha é `HTTP/1.1 404 Not Found` e o corpo contém `QIT000404`.
- `docker compose exec -T api python -c "from app import app; print(sorted(r.path for r in app.routes if 'sample' in r.path))"` → `[]`. Comentários preservados do base não contam como rota ativa.
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `6 passed`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/app.py
  src/resources/__init__.py
  src/resources/sample_entity.py
  ```

**Pronto quando:**
- [ ] `src/app.py` registra só `/` e `/health_check`.
- [ ] `src/resources/` tem só `__init__.py` e `health_check.py`.
- [ ] `GET /sample_entities` responde 404 `QIT000404`.
- [ ] Suíte com `6 passed`; lint sem saída; commit local feito.

**Commit:** `refactor(api): remove as rotas do sample_entity`
**Pare se:**
- `docker compose up -d --build --wait` falha (rode `docker compose logs --tail 100 api` e traga a saída).
- O `curl.exe` responde outro status.
- Algum trecho de `src/app.py` citado no campo **Arquivos** não é encontrado igual.

---

### Passo 2.4 — Apagar controller e repository do sample_entity
**Branch:** fase/02-banco · **Depende de:** 2.3
**Objetivo:** `src/controllers/__init__.py` e `src/repositories/__init__.py` vazios; `BaseController` intacto.
**Decisões:** ARQ-11 — pode apagar o `sample_entity`.
**Arquivos:**
- `src/controllers/sample_entity_controller.py` (apagar)
- `src/repositories/sample_entity_repository.py` (apagar)
- `src/controllers/__init__.py` (editar): apague a única linha (`from controllers.sample_entity_controller import SampleEntityController`). O arquivo fica vazio: 0 bytes.
- `src/repositories/__init__.py` (editar): apague a única linha (`from repositories.sample_entity_repository import SampleEntityRepository`). O arquivo fica vazio: 0 bytes.

`src/controllers/base_controller.py` não muda.

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → vazio; `git branch --show-current` → `fase/02-banco`; `git log --oneline` mostra `refactor(api): remove as rotas do sample_entity`.
2. `git rm -- src/controllers/sample_entity_controller.py src/repositories/sample_entity_repository.py`
3. Esvazie `src/controllers/__init__.py` e `src/repositories/__init__.py`.
4. `docker compose up -d --build --wait`.
5. Rode os comandos do **Verificar**, na ordem.
6. Feche o passo, um comando por vez:
   ```
   git add -- src/controllers/__init__.py src/repositories/__init__.py
   git diff --cached --name-only
   git diff --name-only
   git ls-files --others --exclude-standard
   git commit -m "refactor: remove controller e repository do sample_entity"
   git log -1 --format=%B
   ```

**Testes:** nenhum teste novo.
**Verificar:**
- `git ls-files src/controllers src/repositories` → exatamente:
  ```
  src/controllers/__init__.py
  src/controllers/base_controller.py
  src/repositories/__init__.py
  ```
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `6 passed`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/controllers/__init__.py
  src/controllers/sample_entity_controller.py
  src/repositories/__init__.py
  src/repositories/sample_entity_repository.py
  ```

**Pronto quando:**
- [ ] Os dois `__init__.py` estão vazios.
- [ ] `src/controllers/base_controller.py` sem nenhuma mudança (`git diff main -- src/controllers/base_controller.py` sem saída).
- [ ] Suíte com `6 passed`; lint sem saída; commit local feito.

**Commit:** `refactor: remove controller e repository do sample_entity`
**Pare se:**
- `docker compose up -d --build --wait` falha.
- A suíte não termina com `6 passed`.

---

### Passo 2.5 — Apagar DTO e schemas do sample_entity
**Branch:** fase/02-banco · **Depende de:** 2.4
**Objetivo:** `src/dtos/__init__.py` vazio; nenhum schema em `src/schemas/`.
**Decisões:** ARQ-11 — pode apagar o `sample_entity`.
**Arquivos:**
- `src/dtos/sample_entity_dto.py` (apagar)
- `src/schemas/post_sample_entity.json` (apagar)
- `src/schemas/put_sample_entity.json` (apagar)
- `src/schemas/get_sample_entities.json` (apagar)
- `src/dtos/__init__.py` (editar): apague a única linha (`from dtos.sample_entity_dto import SampleEntityDTO`). O arquivo fica vazio: 0 bytes.

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → vazio; `git branch --show-current` → `fase/02-banco`; `git log --oneline` mostra `refactor: remove controller e repository do sample_entity`.
2. `git rm -- src/dtos/sample_entity_dto.py src/schemas/post_sample_entity.json src/schemas/put_sample_entity.json src/schemas/get_sample_entities.json`
3. Esvazie `src/dtos/__init__.py`.
4. `docker compose up -d --build --wait`.
5. Rode os comandos do **Verificar**, na ordem.
6. Feche o passo, um comando por vez:
   ```
   git add -- src/dtos/__init__.py
   git diff --cached --name-only
   git diff --name-only
   git ls-files --others --exclude-standard
   git commit -m "refactor: remove DTO e schemas do sample_entity"
   git log -1 --format=%B
   ```

**Testes:** nenhum teste novo.
**Verificar:**
- `git ls-files src/dtos src/schemas` → uma linha só: `src/dtos/__init__.py`
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `6 passed`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/dtos/__init__.py
  src/dtos/sample_entity_dto.py
  src/schemas/get_sample_entities.json
  src/schemas/post_sample_entity.json
  src/schemas/put_sample_entity.json
  ```

**Pronto quando:**
- [ ] `src/dtos/__init__.py` vazio; nenhum arquivo em `src/schemas/` no Git.
- [ ] Suíte com `6 passed`; lint sem saída; commit local feito.

**Commit:** `refactor: remove DTO e schemas do sample_entity`
**Pare se:**
- `docker compose up -d --build --wait` falha.
- A suíte não termina com `6 passed`.

---

### Passo 2.6 — Apagar os models do sample_entity
**Branch:** fase/02-banco · **Depende de:** 2.5
**Objetivo:** `src/models/` só com `base.py` e o `__init__.py` vazio.
**Decisões:** ARQ-11 — pode apagar o `sample_entity`.
**Arquivos:**
- `src/models/sample_entity.py` (apagar)
- `src/models/sample_entity_status.py` (apagar)
- `src/models/sample_entity_status_event.py` (apagar)
- `src/models/__init__.py` (editar): apague as 3 linhas. O arquivo fica vazio: 0 bytes.

`src/models/base.py` não muda.

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → vazio; `git branch --show-current` → `fase/02-banco`; `git log --oneline` mostra `refactor: remove DTO e schemas do sample_entity`.
2. `git rm -- src/models/sample_entity.py src/models/sample_entity_status.py src/models/sample_entity_status_event.py`
3. Esvazie `src/models/__init__.py`.
4. `docker compose up -d --build --wait`.
5. Rode os comandos do **Verificar**, na ordem.
6. Feche o passo, um comando por vez:
   ```
   git add -- src/models/__init__.py
   git diff --cached --name-only
   git diff --name-only
   git ls-files --others --exclude-standard
   git commit -m "refactor(models): remove os models do sample_entity"
   git log -1 --format=%B
   ```

**Testes:** nenhum teste novo.
**Verificar:**
- `git ls-files src/models` → exatamente:
  ```
  src/models/__init__.py
  src/models/base.py
  ```
- `git grep -l "SampleEntity" -- src` → exatamente estas 2 linhas (as duas saem nas fases 3 e 4; ficam de propósito):
  ```
  src/errors/custom_errors.py
  src/utils/schema_handler.py
  ```
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `6 passed`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/models/__init__.py
  src/models/sample_entity.py
  src/models/sample_entity_status.py
  src/models/sample_entity_status_event.py
  ```

**Pronto quando:**
- [ ] `src/models/` com `__init__.py` (vazio) e `base.py`.
- [ ] O `git grep` dá só as 2 linhas do **Verificar**.
- [ ] Suíte com `6 passed`; lint sem saída; commit local feito.

**Commit:** `refactor(models): remove os models do sample_entity`
**Pare se:**
- `docker compose up -d --build --wait` falha.
- O `git grep` mostra um arquivo além dos 2 esperados.
- A suíte não termina com `6 passed`.

---

### Passo 2.7 — O `database.sql` completo
**Branch:** fase/02-banco · **Depende de:** 2.6
**Objetivo:** `database/database.sql` com as 22 tabelas, as restrições, os índices e os dados iniciais (7 tipos fixos, conta `BANK`, conta `OUTSIDE_WORLD` e relógio em `2026-06-01`).
**Decisões:** DAD-01 — id e key; DAD-04 — entidade, estado, relação; DAD-05 — entidades; DAD-06 — tabela de operações; DAD-07 — saldo em dois lugares; DAD-08 — centavos em `BIGINT`; DAD-09 — contas do sistema; DAD-10 — só o sistema fica negativo; DAD-14 — gamificação em eventos e colunas; DAD-15 — banco nasce inteiro; DAD-16 — tipos de lançamento; DAD-17 — duas datas; CLI-04 — uma conta aberta; CLI-05 — estados da conta; CLI-08 — motivos do bloqueio; COF-03 — categoria padrão; COF-14 — cofrinho é conta; COF-15 — fração de centavo; COF-18 — nome único; COF-23 — colunas do lote; COF-25 — imposto para o banco; GAM-12 — ranques; GAM-14 — carência; GAM-15 — 10 níveis; GAM-16 — fórmulas de XP; GAM-21 — aplicar e zerar; DIA-01 — relógio do banco; DIA-04 — começa em 01/06/2026; MOV-10 — tarifa zero sem lançamento; MOV-12 — idempotência; MOV-14 — ordem do extrato; MOV-16 — tabela `deposits`; MOV-19 — idempotência na prática; API-16 — token da conta; PRD-06 — log de toda requisição; PRD-10 — barreira; PRD-14 — colunas do log; R4 — append-only; R6 — sem float.
**Arquivos:**
- `database/database.sql` (editar): apague todo o conteúdo atual (as 3 tabelas do `sample_entity`) e grave exatamente o conteúdo abaixo, caractere por caractere. O arquivo só tem caracteres ASCII e nenhum sinal de porcentagem: o `DbUtils.rollback()` lê o arquivo com a codificação padrão do Windows e o executa pelo psycopg2.

```sql
-- Banco do prototipo bancario do Bootcamp QI Tech 2026 (DAD-15: nasce inteiro).
--
-- Roda quando o volume do banco nasce (database/Dockerfile) e a cada
-- DbUtils.rollback() dos testes. Mudou este arquivo: docker compose down -v.
--
-- Regras de escrita deste arquivo:
-- * so caracteres ASCII, sem acento: o DbUtils le o arquivo no Windows;
-- * nenhum sinal de porcentagem: o DbUtils executa o texto pelo psycopg2;
-- * dinheiro em centavos inteiros, BIGINT (DAD-08);
-- * id interno SERIAL e key publica CHAR(36), UUID v4 (DAD-01, DAD-12).

-- ============================================================
-- Tipos fixos
-- Os ids saem da ordem dos INSERT (o banco nasce vazio). Os indices
-- parciais mais abaixo usam esses ids.
-- ============================================================

CREATE TABLE account_type(
    id                              SERIAL PRIMARY KEY,
    enumerator                      VARCHAR(50) NOT NULL,
    created_at                      TIMESTAMP NOT NULL DEFAULT(NOW()),
    UNIQUE(enumerator)
);

INSERT INTO account_type (enumerator) VALUES
('CUSTOMER'),
('PIGGY_BANK'),
('BANK'),
('OUTSIDE_WORLD');

CREATE TABLE account_status(
    id                              SERIAL PRIMARY KEY,
    enumerator                      VARCHAR(50) NOT NULL,
    created_at                      TIMESTAMP NOT NULL DEFAULT(NOW()),
    UNIQUE(enumerator)
);

INSERT INTO account_status (enumerator) VALUES
('ACTIVE'),
('BLOCKED'),
('CLOSED');

CREATE TABLE block_reason(
    id                              SERIAL PRIMARY KEY,
    enumerator                      VARCHAR(50) NOT NULL,
    created_at                      TIMESTAMP NOT NULL DEFAULT(NOW()),
    UNIQUE(enumerator)
);

INSERT INTO block_reason (enumerator) VALUES
('SUSPICIOUS_ACTIVITY'),
('JUDICIAL_ORDER'),
('CUSTOMER_REQUEST'),
('MANUAL_REVIEW');

CREATE TABLE transaction_type(
    id                              SERIAL PRIMARY KEY,
    enumerator                      VARCHAR(50) NOT NULL,
    created_at                      TIMESTAMP NOT NULL DEFAULT(NOW()),
    UNIQUE(enumerator)
);

INSERT INTO transaction_type (enumerator) VALUES
('DEPOSIT'),
('WITHDRAWAL'),
('TRANSFER'),
('SAVE'),
('REDEEM'),
('YIELD');

CREATE TABLE entry_type(
    id                              SERIAL PRIMARY KEY,
    enumerator                      VARCHAR(50) NOT NULL,
    created_at                      TIMESTAMP NOT NULL DEFAULT(NOW()),
    UNIQUE(enumerator)
);

INSERT INTO entry_type (enumerator) VALUES
('AMOUNT'),
('FEE'),
('PRIZE'),
('YIELD'),
('IOF'),
('IR');

CREATE TABLE category_status(
    id                              SERIAL PRIMARY KEY,
    enumerator                      VARCHAR(50) NOT NULL,
    created_at                      TIMESTAMP NOT NULL DEFAULT(NOW()),
    UNIQUE(enumerator)
);

INSERT INTO category_status (enumerator) VALUES
('ACTIVE'),
('DELETED');

CREATE TABLE piggy_rank(
    id                              SERIAL PRIMARY KEY,
    enumerator                      VARCHAR(50) NOT NULL,
    created_at                      TIMESTAMP NOT NULL DEFAULT(NOW()),
    UNIQUE(enumerator)
);

INSERT INTO piggy_rank (enumerator) VALUES
('DEFAULT'),
('BRONZE'),
('SILVER'),
('GOLD'),
('PLATINUM'),
('DIAMOND');

-- ============================================================
-- Quem: cliente
-- ============================================================

CREATE TABLE customer(
    id                              SERIAL PRIMARY KEY,
    customer_key                    CHAR(36) NOT NULL,
    name                            VARCHAR(255) NOT NULL,
    document_number                 CHAR(14) NOT NULL,
    email                           VARCHAR(255) NOT NULL,
    birthdate                       DATE NOT NULL,
    created_at                      TIMESTAMP NOT NULL DEFAULT(NOW()),
    UNIQUE(customer_key),
    UNIQUE(document_number),
    UNIQUE(email)
);

-- ============================================================
-- Soltas: relogio do banco e registro de requisicoes
-- ============================================================

-- DIA-01: uma linha so, com o hoje do banco. DIA-04: comeca em 2026-06-01.
CREATE TABLE bank_clock(
    id                              SERIAL PRIMARY KEY,
    bank_clock_key                  CHAR(36) NOT NULL,
    accounting_date                 DATE NOT NULL,
    updated_at                      TIMESTAMP NOT NULL DEFAULT(NOW()),
    UNIQUE(bank_clock_key),
    CHECK (id = 1)
);

INSERT INTO bank_clock (bank_clock_key, accounting_date) VALUES
(gen_random_uuid()::text, '2026-06-01');

-- PRD-06, PRD-14: uma linha por requisicao, gravada fora da transacao da
-- regra. Sem chave estrangeira de proposito. Nunca guarda CPF, CNPJ,
-- token nem corpo (PRD-12).
CREATE TABLE request_log(
    id                              SERIAL PRIMARY KEY,
    request_log_key                 CHAR(36) NOT NULL,
    request_id                      VARCHAR(64) NOT NULL,
    method                          VARCHAR NOT NULL,
    path                            VARCHAR NOT NULL,
    status                          INTEGER NOT NULL,
    error_code                      VARCHAR(20),
    client_ip                       VARCHAR(45),
    account_key                     VARCHAR,
    auth_failure                    VARCHAR(20),
    created_at                      TIMESTAMP NOT NULL DEFAULT(NOW()),
    UNIQUE(request_log_key),
    CHECK (auth_failure IN ('INTERNAL', 'ADMIN', 'ACCOUNT'))
);

-- PRD-10: a barreira conta falhas de token por IP e por conta + IP.
CREATE INDEX request_log_client_ip_created_at_idx
    ON request_log (client_ip, created_at);

CREATE INDEX request_log_account_key_client_ip_created_at_idx
    ON request_log (account_key, client_ip, created_at);

-- ============================================================
-- Quem: conta (de cliente, cofrinho, do banco e mundo de fora)
-- ============================================================

-- Conta de cliente: customer_id preenchido, balance e token_hash preenchidos.
-- Cofrinho (COF-14): customer_id e parent_account_id preenchidos, balance
-- preenchido, token_hash nulo.
-- Contas do sistema (DAD-09): customer_id, parent_account_id, balance e
-- token_hash nulos; o saldo delas e a soma dos lancamentos.
-- Gamificacao (DAD-14, GAM-01): valores atuais nas colunas da conta de cliente.
CREATE TABLE account(
    id                              SERIAL PRIMARY KEY,
    account_key                     CHAR(36) NOT NULL,
    account_type_id                 INTEGER NOT NULL REFERENCES account_type(id),
    status_id                       INTEGER NOT NULL REFERENCES account_status(id),
    customer_id                     INTEGER REFERENCES customer(id),
    parent_account_id               INTEGER REFERENCES account(id),
    balance                         BIGINT,
    token_hash                      CHAR(64),
    xp                              BIGINT NOT NULL DEFAULT(0),
    level                           INTEGER NOT NULL DEFAULT(0),
    points_free                     INTEGER NOT NULL DEFAULT(0),
    points_fee                      INTEGER NOT NULL DEFAULT(0),
    points_chance                   INTEGER NOT NULL DEFAULT(0),
    rank_id                         INTEGER REFERENCES piggy_rank(id),
    yield_rank_id                   INTEGER REFERENCES piggy_rank(id),
    piggy_record                    BIGINT NOT NULL DEFAULT(0),
    grace_until                     DATE,
    created_at                      TIMESTAMP NOT NULL DEFAULT(NOW()),
    UNIQUE(account_key),
    UNIQUE(parent_account_id),
    CHECK (balance >= 0),
    CHECK (xp >= 0),
    CHECK (level >= 0),
    CHECK (points_free >= 0),
    CHECK (points_fee >= 0),
    CHECK (points_chance >= 0),
    CHECK (piggy_record >= 0)
);

-- CLI-04: uma conta nao encerrada por cliente.
-- account_type CUSTOMER = 1; account_status CLOSED = 3.
CREATE UNIQUE INDEX account_one_open_per_customer_idx
    ON account (customer_id)
    WHERE account_type_id = 1 AND status_id <> 3;

-- DAD-09: a conta do banco e a conta mundo de fora.
INSERT INTO account (account_key, account_type_id, status_id) VALUES
(
    gen_random_uuid()::text,
    (SELECT id FROM account_type WHERE enumerator = 'BANK'),
    (SELECT id FROM account_status WHERE enumerator = 'ACTIVE')
),
(
    gen_random_uuid()::text,
    (SELECT id FROM account_type WHERE enumerator = 'OUTSIDE_WORLD'),
    (SELECT id FROM account_status WHERE enumerator = 'ACTIVE')
);

-- CLI-05, CLI-08, R4: historico do estado da conta.
-- block_reason_id so no bloqueio; source: MANUAL (rota interna) ou
-- AUTOMATIC (bloqueio automatico).
CREATE TABLE account_status_event(
    id                              SERIAL PRIMARY KEY,
    account_id                      INTEGER NOT NULL REFERENCES account(id),
    status_id                       INTEGER NOT NULL REFERENCES account_status(id),
    block_reason_id                 INTEGER REFERENCES block_reason(id),
    source                          VARCHAR(20),
    event_datetime                  TIMESTAMP NOT NULL,
    created_at                      TIMESTAMP NOT NULL DEFAULT(clock_timestamp()),
    CHECK (source IN ('MANUAL', 'AUTOMATIC'))
);

-- ============================================================
-- Dinheiro: operacao, deposito e lancamento
-- ============================================================

-- DAD-06, DAD-17, MOV-12, MOV-19: uma linha por pedido.
-- request_control_key e request_hash nulos so no rendimento (YIELD).
CREATE TABLE transaction(
    id                              SERIAL PRIMARY KEY,
    transaction_key                 CHAR(36) NOT NULL,
    transaction_type_id             INTEGER NOT NULL REFERENCES transaction_type(id),
    request_control_key             CHAR(36),
    request_hash                    CHAR(64),
    accounting_date                 DATE NOT NULL,
    created_at                      TIMESTAMP NOT NULL DEFAULT(clock_timestamp()),
    UNIQUE(transaction_key),
    UNIQUE(request_control_key)
);

-- MOV-15, MOV-16: quem depositou. CPF (14) ou CNPJ (18) formatado.
CREATE TABLE deposits(
    id                              SERIAL PRIMARY KEY,
    deposit_key                     CHAR(36) NOT NULL,
    transaction_id                  INTEGER NOT NULL REFERENCES transaction(id),
    depositor_name                  VARCHAR(255) NOT NULL,
    depositor_document              VARCHAR(18) NOT NULL,
    created_at                      TIMESTAMP NOT NULL DEFAULT(NOW()),
    UNIQUE(deposit_key),
    UNIQUE(transaction_id)
);

-- ============================================================
-- Cofrinho: categorias
-- ============================================================

-- COF-03, COF-14: account_id e o cofrinho. is_default marca economias.
CREATE TABLE category(
    id                              SERIAL PRIMARY KEY,
    category_key                    CHAR(36) NOT NULL,
    account_id                      INTEGER NOT NULL REFERENCES account(id),
    status_id                       INTEGER NOT NULL REFERENCES category_status(id),
    name                            VARCHAR(255) NOT NULL,
    is_default                      BOOLEAN NOT NULL DEFAULT(FALSE),
    created_at                      TIMESTAMP NOT NULL DEFAULT(NOW()),
    UNIQUE(category_key)
);

-- COF-18: nome unico entre as categorias ativas do cofrinho.
-- category_status ACTIVE = 1.
CREATE UNIQUE INDEX category_active_name_idx
    ON category (account_id, name)
    WHERE status_id = 1;

-- COF-03: uma categoria padrao por cofrinho.
CREATE UNIQUE INDEX category_one_default_idx
    ON category (account_id)
    WHERE is_default;

-- API-15, R4: historico do estado da categoria.
CREATE TABLE category_status_event(
    id                              SERIAL PRIMARY KEY,
    category_id                     INTEGER NOT NULL REFERENCES category(id),
    status_id                       INTEGER NOT NULL REFERENCES category_status(id),
    event_datetime                  TIMESTAMP NOT NULL,
    created_at                      TIMESTAMP NOT NULL DEFAULT(NOW())
);

-- DAD-05, DAD-16, MOV-19: uma linha por conta afetada; a soma da operacao
-- e zero. category_id so nos lancamentos do cofrinho. balance_after nulo
-- nas contas do sistema.
CREATE TABLE entry(
    id                              SERIAL PRIMARY KEY,
    entry_key                       CHAR(36) NOT NULL,
    transaction_id                  INTEGER NOT NULL REFERENCES transaction(id),
    account_id                      INTEGER NOT NULL REFERENCES account(id),
    entry_type_id                   INTEGER NOT NULL REFERENCES entry_type(id),
    category_id                     INTEGER REFERENCES category(id),
    amount                          BIGINT NOT NULL,
    balance_after                   BIGINT,
    created_at                      TIMESTAMP NOT NULL DEFAULT(clock_timestamp()),
    UNIQUE(entry_key),
    CHECK (amount <> 0),
    CHECK (balance_after >= 0)
);

-- MOV-14: extrato da conta, mais recente primeiro, desempate por id.
CREATE INDEX entry_account_created_at_id_idx
    ON entry (account_id, created_at DESC, id DESC);

-- ============================================================
-- Cofrinho: lotes
-- ============================================================

-- COF-06, COF-13, COF-15, COF-23: um lote por guardar.
-- residue: fracao de centavo do rendimento, 8 casas.
CREATE TABLE lot(
    id                              SERIAL PRIMARY KEY,
    lot_key                         CHAR(36) NOT NULL,
    category_id                     INTEGER NOT NULL REFERENCES category(id),
    transaction_id                  INTEGER NOT NULL REFERENCES transaction(id),
    accounting_date                 DATE NOT NULL,
    principal_remaining             BIGINT NOT NULL,
    yield_remaining                 BIGINT NOT NULL DEFAULT(0),
    residue                         NUMERIC(9, 8) NOT NULL DEFAULT(0),
    created_at                      TIMESTAMP NOT NULL DEFAULT(clock_timestamp()),
    UNIQUE(lot_key),
    CHECK (principal_remaining >= 0),
    CHECK (yield_remaining >= 0),
    CHECK (residue >= 0 AND residue < 1)
);

-- ============================================================
-- Gamificacao: eventos (DAD-14)
-- ============================================================

-- GAM-04, GAM-16, GAM-17, GAM-19: transaction_id nulo no XP da virada.
CREATE TABLE xp_event(
    id                              SERIAL PRIMARY KEY,
    xp_event_key                    CHAR(36) NOT NULL,
    account_id                      INTEGER NOT NULL REFERENCES account(id),
    transaction_id                  INTEGER REFERENCES transaction(id),
    source                          VARCHAR(20) NOT NULL,
    xp                              BIGINT NOT NULL,
    accounting_date                 DATE NOT NULL,
    created_at                      TIMESTAMP NOT NULL DEFAULT(NOW()),
    UNIQUE(xp_event_key),
    CHECK (source IN ('TRANSFER_SENT', 'TRANSFER_RECEIVED', 'PIGGY_RECORD')),
    CHECK (xp >= 0)
);

-- GAM-05, GAM-06, GAM-15: nivel alcancado (cada um vale 1 ponto livre).
CREATE TABLE level_event(
    id                              SERIAL PRIMARY KEY,
    level_event_key                 CHAR(36) NOT NULL,
    account_id                      INTEGER NOT NULL REFERENCES account(id),
    level                           INTEGER NOT NULL,
    accounting_date                 DATE NOT NULL,
    created_at                      TIMESTAMP NOT NULL DEFAULT(NOW()),
    UNIQUE(level_event_key),
    CHECK (level >= 1)
);

-- GAM-12, GAM-14, GAM-19: subiu, abriu carencia, saiu da carencia, caiu.
CREATE TABLE rank_event(
    id                              SERIAL PRIMARY KEY,
    rank_event_key                  CHAR(36) NOT NULL,
    account_id                      INTEGER NOT NULL REFERENCES account(id),
    rank_id                         INTEGER NOT NULL REFERENCES piggy_rank(id),
    kind                            VARCHAR(20) NOT NULL,
    accounting_date                 DATE NOT NULL,
    created_at                      TIMESTAMP NOT NULL DEFAULT(NOW()),
    UNIQUE(rank_event_key),
    CHECK (kind IN ('UP', 'GRACE_START', 'GRACE_END', 'DOWN'))
);

-- GAM-07, GAM-21: aplicar +Y pontos num beneficio, ou zerar tudo.
-- benefit nulo no RESET.
CREATE TABLE points_event(
    id                              SERIAL PRIMARY KEY,
    points_event_key                CHAR(36) NOT NULL,
    account_id                      INTEGER NOT NULL REFERENCES account(id),
    action                          VARCHAR(10) NOT NULL,
    benefit                         VARCHAR(10),
    points                          INTEGER NOT NULL,
    created_at                      TIMESTAMP NOT NULL DEFAULT(NOW()),
    UNIQUE(points_event_key),
    CHECK (action IN ('APPLY', 'RESET')),
    CHECK (benefit IN ('FEE', 'CHANCE')),
    CHECK ((action = 'APPLY' AND benefit IS NOT NULL) OR (action = 'RESET' AND benefit IS NULL)),
    CHECK (points >= 0)
);
```

Ids dos tipos fixos, na ordem dos `INSERT` (os índices parciais e os passos dos models usam estes valores):

| Tabela | Ids |
|---|---|
| `account_type` | 1 `CUSTOMER` · 2 `PIGGY_BANK` · 3 `BANK` · 4 `OUTSIDE_WORLD` |
| `account_status` | 1 `ACTIVE` · 2 `BLOCKED` · 3 `CLOSED` |
| `block_reason` | 1 `SUSPICIOUS_ACTIVITY` · 2 `JUDICIAL_ORDER` · 3 `CUSTOMER_REQUEST` · 4 `MANUAL_REVIEW` |
| `transaction_type` | 1 `DEPOSIT` · 2 `WITHDRAWAL` · 3 `TRANSFER` · 4 `SAVE` · 5 `REDEEM` · 6 `YIELD` |
| `entry_type` | 1 `AMOUNT` · 2 `FEE` · 3 `PRIZE` · 4 `YIELD` · 5 `IOF` · 6 `IR` |
| `category_status` | 1 `ACTIVE` · 2 `DELETED` |
| `piggy_rank` | 1 `DEFAULT` · 2 `BRONZE` · 3 `SILVER` · 4 `GOLD` · 5 `PLATINUM` · 6 `DIAMOND` |

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → vazio; `git branch --show-current` → `fase/02-banco`; `git log --oneline` mostra `refactor(models): remove os models do sample_entity`.
2. Substitua o conteúdo inteiro de `database/database.sql` pelo bloco SQL do campo **Arquivos**.
3. `./.venv/Scripts/python.exe -c "t = open('database/database.sql', encoding='ascii').read(); print('%' in t, 'sample' in t)"` → `False False`.
4. Recrie o banco do zero, um comando por vez:
   ```
   docker compose down -v
   docker compose up -d --build --wait
   ```
5. Rode as consultas do **Verificar**, na ordem, e compare cada saída com a esperada.
6. `./.venv/Scripts/python.exe -c "from tests.utils import DbUtils; DbUtils.rollback(); print('ok')"` → `ok`.
7. Repita as consultas V1 e V10 do **Verificar**: as saídas são as mesmas.
8. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `6 passed`.
9. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
10. Feche o passo, um comando por vez:
    ```
    git add -- database/database.sql
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "feat(banco): database.sql com as 22 tabelas e os dados iniciais"
    git log -1 --format=%B
    ```

**Testes:** nenhum teste novo. Teste de integração não lê o banco (TST-01); as tabelas são provadas pelas consultas do **Verificar** e, depois, pelos testes de rota das fases 5 a 9.
**Verificar:** cada consulta é um comando numa linha só. `-t -A` tira cabeçalho e alinhamento: a saída é só o valor.

- V1 — quantas tabelas:
  ```
  docker compose exec -T db psql -U bootcamp -d bootcamp -t -A -c "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"
  ```
  Saída: `22`
- V2 — os nomes:
  ```
  docker compose exec -T db psql -U bootcamp -d bootcamp -t -A -c "SELECT string_agg(table_name, ',' ORDER BY table_name) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"
  ```
  Saída: `account,account_status,account_status_event,account_type,bank_clock,block_reason,category,category_status,category_status_event,customer,deposits,entry,entry_type,level_event,lot,piggy_rank,points_event,rank_event,request_log,transaction,transaction_type,xp_event`
- V3 a V9 — os tipos fixos e os ids. Um comando por tabela; troque só o nome da tabela no fim:
  ```
  docker compose exec -T db psql -U bootcamp -d bootcamp -t -A -c "SELECT string_agg(id || ':' || enumerator, ',' ORDER BY id) FROM account_type"
  ```
  Saídas:
  - V3 `account_type` → `1:CUSTOMER,2:PIGGY_BANK,3:BANK,4:OUTSIDE_WORLD`
  - V4 `account_status` → `1:ACTIVE,2:BLOCKED,3:CLOSED`
  - V5 `block_reason` → `1:SUSPICIOUS_ACTIVITY,2:JUDICIAL_ORDER,3:CUSTOMER_REQUEST,4:MANUAL_REVIEW`
  - V6 `transaction_type` → `1:DEPOSIT,2:WITHDRAWAL,3:TRANSFER,4:SAVE,5:REDEEM,6:YIELD`
  - V7 `entry_type` → `1:AMOUNT,2:FEE,3:PRIZE,4:YIELD,5:IOF,6:IR`
  - V8 `category_status` → `1:ACTIVE,2:DELETED`
  - V9 `piggy_rank` → `1:DEFAULT,2:BRONZE,3:SILVER,4:GOLD,5:PLATINUM,6:DIAMOND`
- V10 — as contas do sistema (DAD-09):
  ```
  docker compose exec -T db psql -U bootcamp -d bootcamp -t -A -c "SELECT t.enumerator || ':' || s.enumerator || ':' || coalesce(a.balance::text, 'null') || ':' || length(a.account_key) FROM account a JOIN account_type t ON t.id = a.account_type_id JOIN account_status s ON s.id = a.status_id ORDER BY a.id"
  ```
  Saída, 2 linhas:
  ```
  BANK:ACTIVE:null:36
  OUTSIDE_WORLD:ACTIVE:null:36
  ```
- V11 — o relógio (DIA-04):
  ```
  docker compose exec -T db psql -U bootcamp -d bootcamp -t -A -c "SELECT accounting_date || ':' || length(bank_clock_key) FROM bank_clock"
  ```
  Saída: `2026-06-01:36`
- V12 — as restrições, por tipo (c = CHECK, f = chave estrangeira, p = chave primária, u = UNIQUE):
  ```
  docker compose exec -T db psql -U bootcamp -d bootcamp -t -A -c "SELECT contype || ':' || count(*) FROM pg_constraint WHERE connamespace = 'public'::regnamespace GROUP BY contype ORDER BY contype"
  ```
  Saída, 4 linhas:
  ```
  c:23
  f:27
  p:22
  u:25
  ```
- V13 — os índices criados à mão:
  ```
  docker compose exec -T db psql -U bootcamp -d bootcamp -t -A -c "SELECT string_agg(indexname, ',' ORDER BY indexname) FROM pg_indexes WHERE schemaname = 'public' AND right(indexname, 4) = '_idx'"
  ```
  Saída: `account_one_open_per_customer_idx,category_active_name_idx,category_one_default_idx,entry_account_created_at_id_idx,request_log_account_key_client_ip_created_at_idx,request_log_client_ip_created_at_idx`
- `git diff --cached --name-only` (antes do commit) → uma linha só: `database/database.sql`

**Pronto quando:**
- [ ] `database/database.sql` é o bloco do plano, sem nenhuma diferença.
- [ ] O banco sobe do zero (`down -v` e `up`) e as saídas de V1 a V13 batem.
- [ ] `DbUtils.rollback()` roda o arquivo sem erro (item 6).
- [ ] Suíte com `6 passed`; lint sem saída; commit local feito.
- [ ] Nenhum model criado neste passo: `git ls-files src/models` continua com `src/models/__init__.py` e `src/models/base.py`.

**Commit:** `feat(banco): database.sql com as 22 tabelas e os dados iniciais`
**Pare se:**
- O item 3 não imprime `False False` ou levanta `UnicodeDecodeError`.
- `docker compose up -d --build --wait` falha: rode `docker compose logs --tail 100 db` e `docker compose logs --tail 100 api` e traga as duas saídas. O SQL é dado inteiro pelo plano e não se corrige no passo.
- Qualquer saída de V1 a V13 é diferente da esperada.
- O item 6 não imprime `ok`.

---

## Como os models são feitos

- Um arquivo por tabela em `src/models/`, no padrão de `src/models/base.py` e dos models do base: `Column` com o tipo da coluna, `nullable` sempre escrito, `server_default` onde o `database.sql` tem `DEFAULT`, `UniqueConstraint` para cada `UNIQUE` da tabela.
- O `database/database.sql` é a fonte. Os `CHECK` e os índices parciais (`CREATE UNIQUE INDEX ... WHERE`) ficam só nele; os models não os repetem.
- Chave estrangeira para um model já carregado: `ForeignKey(<Model>.id)`, com o model importado de `models`, como o `SampleEntity` do base. Para a própria tabela (`account.parent_account_id`): `ForeignKey("account.id")`.
- `relationship` só para as tabelas de tipos fixos, com `lazy="selectin"`, como o `status` do base. Entre tabelas de dados, só a coluna `_id`.
- Os valores fixos viram constantes da classe, como `SampleEntityStatus.CREATED` no base: o enumerator nas tabelas de tipos fixos e os valores de cada `CHECK ... IN (...)` nas outras.
- `src/models/__init__.py` importa os models na ordem dos passos: cada um depois daqueles de que depende. O conteúdo inteiro do arquivo vem em cada passo.
- Nenhum código do projeto importa `models` nesta fase: a API sobe sem eles. A prova de cada passo é a conferência C1.

## Conferência C1 (comando novo)

Roda dentro do container da API, que tem o `src/` montado em `/app` e a `DATABASE_URL` do compose. Carrega todos os models, monta os relacionamentos (`configure_mappers`) e compara cada model com a tabela do banco: nome, nulo e tipo de cada coluna, e as chaves estrangeiras. Um comando numa linha só:

```
docker compose exec -T api python -c "import models; from models.base import Base; from database import engine; from sqlalchemy import inspect; from sqlalchemy.orm import configure_mappers; configure_mappers(); d = engine.dialect; db = inspect(engine); cols = lambda n, t: (sorted((c.name, c.nullable, c.type.compile(dialect=d)) for c in t.columns), sorted((c['name'], c['nullable'], c['type'].compile(dialect=d)) for c in db.get_columns(n))); fks = lambda n, t: (sorted((f.parent.name, f.column.table.name) for f in t.foreign_keys), sorted((f['constrained_columns'][0], f['referred_table']) for f in db.get_foreign_keys(n))); print(len(Base.metadata.tables), [n for n, t in Base.metadata.tables.items() if cols(n, t)[0] != cols(n, t)[1] or fks(n, t)[0] != fks(n, t)[1]])"
```

Saída: o número de models carregados, um espaço e a lista das tabelas que não batem. Esperado em cada passo: o número do passo e `[]`.

| Passo | Antes do código | Depois do código |
|---|---|---|
| 2.8 | `0 []` | `4 []` |
| 2.9 | `4 []` | `8 []` |
| 2.10 | `8 []` | `12 []` |
| 2.11 | `12 []` | `16 []` |
| 2.12 | `16 []` | `20 []` |
| 2.13 | `20 []` | `22 []` |

Se a C1 terminar com `Traceback`, a última linha diz o arquivo e o motivo.

---

### Passo 2.8 — Models dos tipos fixos (1 de 2)
**Branch:** fase/02-banco · **Depende de:** 2.7
**Objetivo:** criar os models `AccountType`, `AccountStatus`, `BlockReason` e `TransactionType`.
**Decisões:** DAD-04 — entidade, estado, relação · CLI-05 — estados da conta · CLI-08 — motivos do bloqueio · DAD-06 — tabela de operações
**Arquivos:**
- `src/models/account_type.py` (criar). Conteúdo inteiro:

```python
from sqlalchemy import Column, DateTime, Integer, String, UniqueConstraint, func
from models.base import Base


class AccountType(Base):
    __tablename__ = "account_type"

    id = Column(Integer, primary_key=True)
    enumerator = Column(String(50), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (UniqueConstraint("enumerator"),)

    CUSTOMER = "CUSTOMER"
    PIGGY_BANK = "PIGGY_BANK"
    BANK = "BANK"
    OUTSIDE_WORLD = "OUTSIDE_WORLD"
```

- `src/models/account_status.py` (criar). Conteúdo inteiro:

```python
from sqlalchemy import Column, DateTime, Integer, String, UniqueConstraint, func
from models.base import Base


class AccountStatus(Base):
    __tablename__ = "account_status"

    id = Column(Integer, primary_key=True)
    enumerator = Column(String(50), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (UniqueConstraint("enumerator"),)

    ACTIVE = "ACTIVE"
    BLOCKED = "BLOCKED"
    CLOSED = "CLOSED"
```

- `src/models/block_reason.py` (criar). Conteúdo inteiro:

```python
from sqlalchemy import Column, DateTime, Integer, String, UniqueConstraint, func
from models.base import Base


class BlockReason(Base):
    __tablename__ = "block_reason"

    id = Column(Integer, primary_key=True)
    enumerator = Column(String(50), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (UniqueConstraint("enumerator"),)

    SUSPICIOUS_ACTIVITY = "SUSPICIOUS_ACTIVITY"
    JUDICIAL_ORDER = "JUDICIAL_ORDER"
    CUSTOMER_REQUEST = "CUSTOMER_REQUEST"
    MANUAL_REVIEW = "MANUAL_REVIEW"
```

- `src/models/transaction_type.py` (criar). Conteúdo inteiro:

```python
from sqlalchemy import Column, DateTime, Integer, String, UniqueConstraint, func
from models.base import Base


class TransactionType(Base):
    __tablename__ = "transaction_type"

    id = Column(Integer, primary_key=True)
    enumerator = Column(String(50), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (UniqueConstraint("enumerator"),)

    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    TRANSFER = "TRANSFER"
    SAVE = "SAVE"
    REDEEM = "REDEEM"
    YIELD = "YIELD"
```

- `src/models/__init__.py` (editar). Conteúdo inteiro, 4 linhas:

```python
from models.account_type import AccountType
from models.account_status import AccountStatus
from models.block_reason import BlockReason
from models.transaction_type import TransactionType
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/02-banco`; `git log --oneline` mostra `feat(banco): database.sql com as 22 tabelas e os dados iniciais`.
2. `docker compose up -d --build --wait`
3. Antes do código: rode a C1 → `0 []`.
4. Crie os arquivos `src/models/account_type.py`, `src/models/account_status.py`, `src/models/block_reason.py`, `src/models/transaction_type.py` com o conteúdo do campo **Arquivos**.
5. Grave o conteúdo inteiro de `src/models/__init__.py` do campo **Arquivos**.
6. `docker compose up -d --build --wait`
7. Rode a C1 → `4 []`.
8. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `6 passed`.
9. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
10. Rode o **Verificar**.
11. Fim do passo, um comando por vez:
    ```
    git add -- src/models/account_type.py src/models/account_status.py src/models/block_reason.py src/models/transaction_type.py src/models/__init__.py
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "feat(models): account_type, account_status, block_reason e transaction_type"
    git log -1 --format=%B
    ```

**Testes:** nenhum teste novo. Teste de integração não importa de `src/` (TST-01) e model não é conta pura (TST-05). A prova é a C1, que sai de `0 []` (item 3) para `4 []` (item 7); as rotas das fases 5 a 9 usam estes models por HTTP.
**Verificar:**
- C1 → `4 []`.
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `6 passed`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/models/__init__.py
  src/models/account_status.py
  src/models/account_type.py
  src/models/block_reason.py
  src/models/transaction_type.py
  ```

**Pronto quando:**
- [ ] Os arquivos novos têm exatamente o conteúdo do campo **Arquivos**.
- [ ] `src/models/__init__.py` tem as 4 linhas do campo **Arquivos**, nesta ordem.
- [ ] C1 com `4 []`; suíte com `6 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata feito.

**Commit:** `feat(models): account_type, account_status, block_reason e transaction_type`
**Pare se:**
- A C1 do item 3 não der `0 []`.
- A C1 do item 7 terminar com `Traceback` ou listar uma tabela entre os colchetes: o model e o `database.sql` não batem, e o `database.sql` não muda neste passo.
- `docker compose up -d --build --wait` falhar: rode `docker compose logs --tail 100 api` e traga a saída.
- A suíte não terminar com `6 passed`.

---

### Passo 2.9 — Models dos tipos fixos (2 de 2) e do cliente
**Branch:** fase/02-banco · **Depende de:** 2.8
**Objetivo:** criar os models `EntryType`, `CategoryStatus`, `PiggyRank` e `Customer`.
**Decisões:** DAD-16 — tipos de lançamento · COF-25 — imposto para o banco · API-15 — excluir categoria · GAM-12 — ranques · CLI-02 — dados do cliente · DAD-01 — id e key
**Arquivos:**
- `src/models/entry_type.py` (criar). Conteúdo inteiro:

```python
from sqlalchemy import Column, DateTime, Integer, String, UniqueConstraint, func
from models.base import Base


class EntryType(Base):
    __tablename__ = "entry_type"

    id = Column(Integer, primary_key=True)
    enumerator = Column(String(50), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (UniqueConstraint("enumerator"),)

    AMOUNT = "AMOUNT"
    FEE = "FEE"
    PRIZE = "PRIZE"
    YIELD = "YIELD"
    IOF = "IOF"
    IR = "IR"
```

- `src/models/category_status.py` (criar). Conteúdo inteiro:

```python
from sqlalchemy import Column, DateTime, Integer, String, UniqueConstraint, func
from models.base import Base


class CategoryStatus(Base):
    __tablename__ = "category_status"

    id = Column(Integer, primary_key=True)
    enumerator = Column(String(50), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (UniqueConstraint("enumerator"),)

    ACTIVE = "ACTIVE"
    DELETED = "DELETED"
```

- `src/models/piggy_rank.py` (criar). Conteúdo inteiro:

```python
from sqlalchemy import Column, DateTime, Integer, String, UniqueConstraint, func
from models.base import Base


class PiggyRank(Base):
    __tablename__ = "piggy_rank"

    id = Column(Integer, primary_key=True)
    enumerator = Column(String(50), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (UniqueConstraint("enumerator"),)

    DEFAULT = "DEFAULT"
    BRONZE = "BRONZE"
    SILVER = "SILVER"
    GOLD = "GOLD"
    PLATINUM = "PLATINUM"
    DIAMOND = "DIAMOND"
```

- `src/models/customer.py` (criar). Conteúdo inteiro:

```python
from sqlalchemy import CHAR, Column, Date, DateTime, Integer, String, UniqueConstraint, func
from models.base import Base


class Customer(Base):
    __tablename__ = "customer"

    id = Column(Integer, primary_key=True)
    customer_key = Column(CHAR(36), nullable=False)
    name = Column(String(255), nullable=False)
    document_number = Column(CHAR(14), nullable=False)
    email = Column(String(255), nullable=False)
    birthdate = Column(Date, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("customer_key"),
        UniqueConstraint("document_number"),
        UniqueConstraint("email"),
    )
```

- `src/models/__init__.py` (editar). Conteúdo inteiro, 8 linhas:

```python
from models.account_type import AccountType
from models.account_status import AccountStatus
from models.block_reason import BlockReason
from models.transaction_type import TransactionType
from models.entry_type import EntryType
from models.category_status import CategoryStatus
from models.piggy_rank import PiggyRank
from models.customer import Customer
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/02-banco`; `git log --oneline` mostra `feat(models): account_type, account_status, block_reason e transaction_type`.
2. `docker compose up -d --build --wait`
3. Antes do código: rode a C1 → `4 []`.
4. Crie os arquivos `src/models/entry_type.py`, `src/models/category_status.py`, `src/models/piggy_rank.py`, `src/models/customer.py` com o conteúdo do campo **Arquivos**.
5. Grave o conteúdo inteiro de `src/models/__init__.py` do campo **Arquivos**.
6. `docker compose up -d --build --wait`
7. Rode a C1 → `8 []`.
8. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `6 passed`.
9. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
10. Rode o **Verificar**.
11. Fim do passo, um comando por vez:
    ```
    git add -- src/models/entry_type.py src/models/category_status.py src/models/piggy_rank.py src/models/customer.py src/models/__init__.py
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "feat(models): entry_type, category_status, piggy_rank e customer"
    git log -1 --format=%B
    ```

**Testes:** nenhum teste novo. Teste de integração não importa de `src/` (TST-01) e model não é conta pura (TST-05). A prova é a C1, que sai de `4 []` (item 3) para `8 []` (item 7); as rotas das fases 5 a 9 usam estes models por HTTP.
**Verificar:**
- C1 → `8 []`.
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `6 passed`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/models/__init__.py
  src/models/category_status.py
  src/models/customer.py
  src/models/entry_type.py
  src/models/piggy_rank.py
  ```

**Pronto quando:**
- [ ] Os arquivos novos têm exatamente o conteúdo do campo **Arquivos**.
- [ ] `src/models/__init__.py` tem as 8 linhas do campo **Arquivos**, nesta ordem.
- [ ] C1 com `8 []`; suíte com `6 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata feito.

**Commit:** `feat(models): entry_type, category_status, piggy_rank e customer`
**Pare se:**
- A C1 do item 3 não der `4 []`.
- A C1 do item 7 terminar com `Traceback` ou listar uma tabela entre os colchetes: o model e o `database.sql` não batem, e o `database.sql` não muda neste passo.
- `docker compose up -d --build --wait` falhar: rode `docker compose logs --tail 100 api` e traga a saída.
- A suíte não terminar com `6 passed`.

---

### Passo 2.10 — Models do relógio, do log e da conta
**Branch:** fase/02-banco · **Depende de:** 2.9
**Objetivo:** criar os models `BankClock`, `RequestLog`, `Account` e `AccountStatusEvent`.
**Decisões:** DIA-01 — relógio do banco · PRD-06 — log de toda requisição · PRD-14 — colunas do log · COF-14 — cofrinho é conta · DAD-09 — contas do sistema · DAD-14 — gamificação em eventos e colunas · API-16 — token da conta · CLI-05 — estados da conta · CLI-08 — bloqueio automático
**Arquivos:**
- `src/models/bank_clock.py` (criar). Conteúdo inteiro:

```python
from sqlalchemy import CHAR, Column, Date, DateTime, Integer, UniqueConstraint, func
from models.base import Base


class BankClock(Base):
    __tablename__ = "bank_clock"

    id = Column(Integer, primary_key=True)
    bank_clock_key = Column(CHAR(36), nullable=False)
    accounting_date = Column(Date, nullable=False)
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (UniqueConstraint("bank_clock_key"),)
```

- `src/models/request_log.py` (criar). Conteúdo inteiro:

```python
from sqlalchemy import CHAR, Column, DateTime, Integer, String, UniqueConstraint, func
from models.base import Base


class RequestLog(Base):
    __tablename__ = "request_log"

    id = Column(Integer, primary_key=True)
    request_log_key = Column(CHAR(36), nullable=False)
    request_id = Column(String(64), nullable=False)
    method = Column(String, nullable=False)
    path = Column(String, nullable=False)
    status = Column(Integer, nullable=False)
    error_code = Column(String(20), nullable=True)
    client_ip = Column(String(45), nullable=True)
    account_key = Column(String, nullable=True)
    auth_failure = Column(String(20), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (UniqueConstraint("request_log_key"),)

    INTERNAL = "INTERNAL"
    ADMIN = "ADMIN"
    ACCOUNT = "ACCOUNT"
```

- `src/models/account.py` (criar). Conteúdo inteiro:

```python
from sqlalchemy import CHAR, BigInteger, Column, Date, DateTime, ForeignKey, Integer, UniqueConstraint, func, text
from sqlalchemy.orm import relationship
from models.base import Base
from models import AccountStatus, AccountType, Customer, PiggyRank


class Account(Base):
    __tablename__ = "account"

    id = Column(Integer, primary_key=True)
    account_key = Column(CHAR(36), nullable=False)
    account_type_id = Column(Integer, ForeignKey(AccountType.id), nullable=False)
    status_id = Column(Integer, ForeignKey(AccountStatus.id), nullable=False)
    customer_id = Column(Integer, ForeignKey(Customer.id), nullable=True)
    parent_account_id = Column(Integer, ForeignKey("account.id"), nullable=True)
    balance = Column(BigInteger, nullable=True)
    token_hash = Column(CHAR(64), nullable=True)
    xp = Column(BigInteger, nullable=False, server_default=text("0"))
    level = Column(Integer, nullable=False, server_default=text("0"))
    points_free = Column(Integer, nullable=False, server_default=text("0"))
    points_fee = Column(Integer, nullable=False, server_default=text("0"))
    points_chance = Column(Integer, nullable=False, server_default=text("0"))
    rank_id = Column(Integer, ForeignKey(PiggyRank.id), nullable=True)
    yield_rank_id = Column(Integer, ForeignKey(PiggyRank.id), nullable=True)
    piggy_record = Column(BigInteger, nullable=False, server_default=text("0"))
    grace_until = Column(Date, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("account_key"),
        UniqueConstraint("parent_account_id"),
    )

    account_type = relationship("AccountType", foreign_keys=[account_type_id], lazy="selectin")
    status = relationship("AccountStatus", foreign_keys=[status_id], lazy="selectin")
    rank = relationship("PiggyRank", foreign_keys=[rank_id], lazy="selectin")
    yield_rank = relationship("PiggyRank", foreign_keys=[yield_rank_id], lazy="selectin")
```

- `src/models/account_status_event.py` (criar). Conteúdo inteiro:

```python
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship
from models.base import Base
from models import Account, AccountStatus, BlockReason


class AccountStatusEvent(Base):
    __tablename__ = "account_status_event"

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey(Account.id), nullable=False)
    status_id = Column(Integer, ForeignKey(AccountStatus.id), nullable=False)
    block_reason_id = Column(Integer, ForeignKey(BlockReason.id), nullable=True)
    source = Column(String(20), nullable=True)
    event_datetime = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.clock_timestamp())

    status = relationship("AccountStatus", foreign_keys=[status_id], lazy="selectin")
    block_reason = relationship("BlockReason", foreign_keys=[block_reason_id], lazy="selectin")

    MANUAL = "MANUAL"
    AUTOMATIC = "AUTOMATIC"
```

- `src/models/__init__.py` (editar). Conteúdo inteiro, 12 linhas:

```python
from models.account_type import AccountType
from models.account_status import AccountStatus
from models.block_reason import BlockReason
from models.transaction_type import TransactionType
from models.entry_type import EntryType
from models.category_status import CategoryStatus
from models.piggy_rank import PiggyRank
from models.customer import Customer
from models.bank_clock import BankClock
from models.request_log import RequestLog
from models.account import Account
from models.account_status_event import AccountStatusEvent
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/02-banco`; `git log --oneline` mostra `feat(models): entry_type, category_status, piggy_rank e customer`.
2. `docker compose up -d --build --wait`
3. Antes do código: rode a C1 → `8 []`.
4. Crie os arquivos `src/models/bank_clock.py`, `src/models/request_log.py`, `src/models/account.py`, `src/models/account_status_event.py` com o conteúdo do campo **Arquivos**.
5. Grave o conteúdo inteiro de `src/models/__init__.py` do campo **Arquivos**.
6. `docker compose up -d --build --wait`
7. Rode a C1 → `12 []`.
8. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `6 passed`.
9. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
10. Rode o **Verificar**.
11. Fim do passo, um comando por vez:
    ```
    git add -- src/models/bank_clock.py src/models/request_log.py src/models/account.py src/models/account_status_event.py src/models/__init__.py
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "feat(models): bank_clock, request_log, account e account_status_event"
    git log -1 --format=%B
    ```

**Testes:** nenhum teste novo. Teste de integração não importa de `src/` (TST-01) e model não é conta pura (TST-05). A prova é a C1, que sai de `8 []` (item 3) para `12 []` (item 7); as rotas das fases 5 a 9 usam estes models por HTTP.
**Verificar:**
- C1 → `12 []`.
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `6 passed`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/models/__init__.py
  src/models/account.py
  src/models/account_status_event.py
  src/models/bank_clock.py
  src/models/request_log.py
  ```

**Pronto quando:**
- [ ] Os arquivos novos têm exatamente o conteúdo do campo **Arquivos**.
- [ ] `src/models/__init__.py` tem as 12 linhas do campo **Arquivos**, nesta ordem.
- [ ] C1 com `12 []`; suíte com `6 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata feito.

**Commit:** `feat(models): bank_clock, request_log, account e account_status_event`
**Pare se:**
- A C1 do item 3 não der `8 []`.
- A C1 do item 7 terminar com `Traceback` ou listar uma tabela entre os colchetes: o model e o `database.sql` não batem, e o `database.sql` não muda neste passo.
- `docker compose up -d --build --wait` falhar: rode `docker compose logs --tail 100 api` e traga a saída.
- A suíte não terminar com `6 passed`.

---

### Passo 2.11 — Models da operação, do depósito e da categoria
**Branch:** fase/02-banco · **Depende de:** 2.10
**Objetivo:** criar os models `Transaction`, `Deposit` (tabela `deposits`), `Category` e `CategoryStatusEvent`.
**Decisões:** DAD-06 — tabela de operações · DAD-17 — duas datas · MOV-12 — idempotência · MOV-16 — tabela `deposits` · MOV-19 — idempotência na prática · COF-03 — categorias · API-15 — excluir categoria
**Arquivos:**
- `src/models/transaction.py` (criar). Conteúdo inteiro:

```python
from sqlalchemy import CHAR, Column, Date, DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import relationship
from models.base import Base
from models import TransactionType


class Transaction(Base):
    __tablename__ = "transaction"

    id = Column(Integer, primary_key=True)
    transaction_key = Column(CHAR(36), nullable=False)
    transaction_type_id = Column(Integer, ForeignKey(TransactionType.id), nullable=False)
    request_control_key = Column(CHAR(36), nullable=True)
    request_hash = Column(CHAR(64), nullable=True)
    accounting_date = Column(Date, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.clock_timestamp())

    __table_args__ = (
        UniqueConstraint("transaction_key"),
        UniqueConstraint("request_control_key"),
    )

    transaction_type = relationship("TransactionType", foreign_keys=[transaction_type_id], lazy="selectin")
```

- `src/models/deposit.py` (criar). Conteúdo inteiro:

```python
from sqlalchemy import CHAR, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from models.base import Base
from models import Transaction


class Deposit(Base):
    __tablename__ = "deposits"

    id = Column(Integer, primary_key=True)
    deposit_key = Column(CHAR(36), nullable=False)
    transaction_id = Column(Integer, ForeignKey(Transaction.id), nullable=False)
    depositor_name = Column(String(255), nullable=False)
    depositor_document = Column(String(18), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("deposit_key"),
        UniqueConstraint("transaction_id"),
    )
```

- `src/models/category.py` (criar). Conteúdo inteiro:

```python
from sqlalchemy import CHAR, Boolean, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint, func, text
from sqlalchemy.orm import relationship
from models.base import Base
from models import Account, CategoryStatus


class Category(Base):
    __tablename__ = "category"

    id = Column(Integer, primary_key=True)
    category_key = Column(CHAR(36), nullable=False)
    account_id = Column(Integer, ForeignKey(Account.id), nullable=False)
    status_id = Column(Integer, ForeignKey(CategoryStatus.id), nullable=False)
    name = Column(String(255), nullable=False)
    is_default = Column(Boolean, nullable=False, server_default=text("false"))
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (UniqueConstraint("category_key"),)

    status = relationship("CategoryStatus", foreign_keys=[status_id], lazy="selectin")
```

- `src/models/category_status_event.py` (criar). Conteúdo inteiro:

```python
from sqlalchemy import Column, DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import relationship
from models.base import Base
from models import Category, CategoryStatus


class CategoryStatusEvent(Base):
    __tablename__ = "category_status_event"

    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey(Category.id), nullable=False)
    status_id = Column(Integer, ForeignKey(CategoryStatus.id), nullable=False)
    event_datetime = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    status = relationship("CategoryStatus", foreign_keys=[status_id], lazy="selectin")
```

- `src/models/__init__.py` (editar). Conteúdo inteiro, 16 linhas:

```python
from models.account_type import AccountType
from models.account_status import AccountStatus
from models.block_reason import BlockReason
from models.transaction_type import TransactionType
from models.entry_type import EntryType
from models.category_status import CategoryStatus
from models.piggy_rank import PiggyRank
from models.customer import Customer
from models.bank_clock import BankClock
from models.request_log import RequestLog
from models.account import Account
from models.account_status_event import AccountStatusEvent
from models.transaction import Transaction
from models.deposit import Deposit
from models.category import Category
from models.category_status_event import CategoryStatusEvent
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/02-banco`; `git log --oneline` mostra `feat(models): bank_clock, request_log, account e account_status_event`.
2. `docker compose up -d --build --wait`
3. Antes do código: rode a C1 → `12 []`.
4. Crie os arquivos `src/models/transaction.py`, `src/models/deposit.py`, `src/models/category.py`, `src/models/category_status_event.py` com o conteúdo do campo **Arquivos**.
5. Grave o conteúdo inteiro de `src/models/__init__.py` do campo **Arquivos**.
6. `docker compose up -d --build --wait`
7. Rode a C1 → `16 []`.
8. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `6 passed`.
9. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
10. Rode o **Verificar**.
11. Fim do passo, um comando por vez:
    ```
    git add -- src/models/transaction.py src/models/deposit.py src/models/category.py src/models/category_status_event.py src/models/__init__.py
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "feat(models): transaction, deposits, category e category_status_event"
    git log -1 --format=%B
    ```

**Testes:** nenhum teste novo. Teste de integração não importa de `src/` (TST-01) e model não é conta pura (TST-05). A prova é a C1, que sai de `12 []` (item 3) para `16 []` (item 7); as rotas das fases 5 a 9 usam estes models por HTTP.
**Verificar:**
- C1 → `16 []`.
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `6 passed`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/models/__init__.py
  src/models/category.py
  src/models/category_status_event.py
  src/models/deposit.py
  src/models/transaction.py
  ```

**Pronto quando:**
- [ ] Os arquivos novos têm exatamente o conteúdo do campo **Arquivos**.
- [ ] `src/models/__init__.py` tem as 16 linhas do campo **Arquivos**, nesta ordem.
- [ ] C1 com `16 []`; suíte com `6 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata feito.

**Commit:** `feat(models): transaction, deposits, category e category_status_event`
**Pare se:**
- A C1 do item 3 não der `12 []`.
- A C1 do item 7 terminar com `Traceback` ou listar uma tabela entre os colchetes: o model e o `database.sql` não batem, e o `database.sql` não muda neste passo.
- `docker compose up -d --build --wait` falhar: rode `docker compose logs --tail 100 api` e traga a saída.
- A suíte não terminar com `6 passed`.

---

### Passo 2.12 — Models do lançamento, do lote e dos eventos de XP e nível
**Branch:** fase/02-banco · **Depende de:** 2.11
**Objetivo:** criar os models `Entry`, `Lot`, `XpEvent` e `LevelEvent`.
**Decisões:** DAD-05 — entidades · DAD-16 — tarifa é lançamento · COF-06 — lotes · COF-15 — fração de centavo · COF-23 — colunas do lote · DAD-14 — gamificação em eventos e colunas · GAM-16 — fórmulas de XP · GAM-17 — XP de quem envia e de quem recebe
**Arquivos:**
- `src/models/entry.py` (criar). Conteúdo inteiro:

```python
from sqlalchemy import CHAR, BigInteger, Column, DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import relationship
from models.base import Base
from models import Account, Category, EntryType, Transaction


class Entry(Base):
    __tablename__ = "entry"

    id = Column(Integer, primary_key=True)
    entry_key = Column(CHAR(36), nullable=False)
    transaction_id = Column(Integer, ForeignKey(Transaction.id), nullable=False)
    account_id = Column(Integer, ForeignKey(Account.id), nullable=False)
    entry_type_id = Column(Integer, ForeignKey(EntryType.id), nullable=False)
    category_id = Column(Integer, ForeignKey(Category.id), nullable=True)
    amount = Column(BigInteger, nullable=False)
    balance_after = Column(BigInteger, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.clock_timestamp())

    __table_args__ = (UniqueConstraint("entry_key"),)

    entry_type = relationship("EntryType", foreign_keys=[entry_type_id], lazy="selectin")
```

- `src/models/lot.py` (criar). Conteúdo inteiro:

```python
from sqlalchemy import CHAR, BigInteger, Column, Date, DateTime, ForeignKey, Integer, Numeric, UniqueConstraint, func, text
from models.base import Base
from models import Category, Transaction


class Lot(Base):
    __tablename__ = "lot"

    id = Column(Integer, primary_key=True)
    lot_key = Column(CHAR(36), nullable=False)
    category_id = Column(Integer, ForeignKey(Category.id), nullable=False)
    transaction_id = Column(Integer, ForeignKey(Transaction.id), nullable=False)
    accounting_date = Column(Date, nullable=False)
    principal_remaining = Column(BigInteger, nullable=False)
    yield_remaining = Column(BigInteger, nullable=False, server_default=text("0"))
    residue = Column(Numeric(9, 8), nullable=False, server_default=text("0"))
    created_at = Column(DateTime, nullable=False, server_default=func.clock_timestamp())

    __table_args__ = (UniqueConstraint("lot_key"),)
```

- `src/models/xp_event.py` (criar). Conteúdo inteiro:

```python
from sqlalchemy import CHAR, BigInteger, Column, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from models.base import Base
from models import Account, Transaction


class XpEvent(Base):
    __tablename__ = "xp_event"

    id = Column(Integer, primary_key=True)
    xp_event_key = Column(CHAR(36), nullable=False)
    account_id = Column(Integer, ForeignKey(Account.id), nullable=False)
    transaction_id = Column(Integer, ForeignKey(Transaction.id), nullable=True)
    source = Column(String(20), nullable=False)
    xp = Column(BigInteger, nullable=False)
    accounting_date = Column(Date, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (UniqueConstraint("xp_event_key"),)

    TRANSFER_SENT = "TRANSFER_SENT"
    TRANSFER_RECEIVED = "TRANSFER_RECEIVED"
    PIGGY_RECORD = "PIGGY_RECORD"
```

- `src/models/level_event.py` (criar). Conteúdo inteiro:

```python
from sqlalchemy import CHAR, Column, Date, DateTime, ForeignKey, Integer, UniqueConstraint, func
from models.base import Base
from models import Account


class LevelEvent(Base):
    __tablename__ = "level_event"

    id = Column(Integer, primary_key=True)
    level_event_key = Column(CHAR(36), nullable=False)
    account_id = Column(Integer, ForeignKey(Account.id), nullable=False)
    level = Column(Integer, nullable=False)
    accounting_date = Column(Date, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (UniqueConstraint("level_event_key"),)
```

- `src/models/__init__.py` (editar). Conteúdo inteiro, 20 linhas:

```python
from models.account_type import AccountType
from models.account_status import AccountStatus
from models.block_reason import BlockReason
from models.transaction_type import TransactionType
from models.entry_type import EntryType
from models.category_status import CategoryStatus
from models.piggy_rank import PiggyRank
from models.customer import Customer
from models.bank_clock import BankClock
from models.request_log import RequestLog
from models.account import Account
from models.account_status_event import AccountStatusEvent
from models.transaction import Transaction
from models.deposit import Deposit
from models.category import Category
from models.category_status_event import CategoryStatusEvent
from models.entry import Entry
from models.lot import Lot
from models.xp_event import XpEvent
from models.level_event import LevelEvent
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/02-banco`; `git log --oneline` mostra `feat(models): transaction, deposits, category e category_status_event`.
2. `docker compose up -d --build --wait`
3. Antes do código: rode a C1 → `16 []`.
4. Crie os arquivos `src/models/entry.py`, `src/models/lot.py`, `src/models/xp_event.py`, `src/models/level_event.py` com o conteúdo do campo **Arquivos**.
5. Grave o conteúdo inteiro de `src/models/__init__.py` do campo **Arquivos**.
6. `docker compose up -d --build --wait`
7. Rode a C1 → `20 []`.
8. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `6 passed`.
9. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
10. Rode o **Verificar**.
11. Fim do passo, um comando por vez:
    ```
    git add -- src/models/entry.py src/models/lot.py src/models/xp_event.py src/models/level_event.py src/models/__init__.py
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "feat(models): entry, lot, xp_event e level_event"
    git log -1 --format=%B
    ```

**Testes:** nenhum teste novo. Teste de integração não importa de `src/` (TST-01) e model não é conta pura (TST-05). A prova é a C1, que sai de `16 []` (item 3) para `20 []` (item 7); as rotas das fases 5 a 9 usam estes models por HTTP.
**Verificar:**
- C1 → `20 []`.
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `6 passed`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/models/__init__.py
  src/models/entry.py
  src/models/level_event.py
  src/models/lot.py
  src/models/xp_event.py
  ```

**Pronto quando:**
- [ ] Os arquivos novos têm exatamente o conteúdo do campo **Arquivos**.
- [ ] `src/models/__init__.py` tem as 20 linhas do campo **Arquivos**, nesta ordem.
- [ ] C1 com `20 []`; suíte com `6 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata feito.

**Commit:** `feat(models): entry, lot, xp_event e level_event`
**Pare se:**
- A C1 do item 3 não der `16 []`.
- A C1 do item 7 terminar com `Traceback` ou listar uma tabela entre os colchetes: o model e o `database.sql` não batem, e o `database.sql` não muda neste passo.
- `docker compose up -d --build --wait` falhar: rode `docker compose logs --tail 100 api` e traga a saída.
- A suíte não terminar com `6 passed`.

---

### Passo 2.13 — Models dos eventos de ranque e de pontos
**Branch:** fase/02-banco · **Depende de:** 2.12
**Objetivo:** criar os models `RankEvent` e `PointsEvent`; os 22 models batem com as 22 tabelas.
**Decisões:** DAD-14 — gamificação em eventos e colunas · GAM-14 — carência · GAM-19 — ranque na virada · GAM-21 — aplicar e zerar
**Arquivos:**
- `src/models/rank_event.py` (criar). Conteúdo inteiro:

```python
from sqlalchemy import CHAR, Column, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import relationship
from models.base import Base
from models import Account, PiggyRank


class RankEvent(Base):
    __tablename__ = "rank_event"

    id = Column(Integer, primary_key=True)
    rank_event_key = Column(CHAR(36), nullable=False)
    account_id = Column(Integer, ForeignKey(Account.id), nullable=False)
    rank_id = Column(Integer, ForeignKey(PiggyRank.id), nullable=False)
    kind = Column(String(20), nullable=False)
    accounting_date = Column(Date, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (UniqueConstraint("rank_event_key"),)

    rank = relationship("PiggyRank", foreign_keys=[rank_id], lazy="selectin")

    UP = "UP"
    GRACE_START = "GRACE_START"
    GRACE_END = "GRACE_END"
    DOWN = "DOWN"
```

- `src/models/points_event.py` (criar). Conteúdo inteiro:

```python
from sqlalchemy import CHAR, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from models.base import Base
from models import Account


class PointsEvent(Base):
    __tablename__ = "points_event"

    id = Column(Integer, primary_key=True)
    points_event_key = Column(CHAR(36), nullable=False)
    account_id = Column(Integer, ForeignKey(Account.id), nullable=False)
    action = Column(String(10), nullable=False)
    benefit = Column(String(10), nullable=True)
    points = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (UniqueConstraint("points_event_key"),)

    APPLY = "APPLY"
    RESET = "RESET"
    FEE = "FEE"
    CHANCE = "CHANCE"
```

- `src/models/__init__.py` (editar). Conteúdo inteiro, 22 linhas:

```python
from models.account_type import AccountType
from models.account_status import AccountStatus
from models.block_reason import BlockReason
from models.transaction_type import TransactionType
from models.entry_type import EntryType
from models.category_status import CategoryStatus
from models.piggy_rank import PiggyRank
from models.customer import Customer
from models.bank_clock import BankClock
from models.request_log import RequestLog
from models.account import Account
from models.account_status_event import AccountStatusEvent
from models.transaction import Transaction
from models.deposit import Deposit
from models.category import Category
from models.category_status_event import CategoryStatusEvent
from models.entry import Entry
from models.lot import Lot
from models.xp_event import XpEvent
from models.level_event import LevelEvent
from models.rank_event import RankEvent
from models.points_event import PointsEvent
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/02-banco`; `git log --oneline` mostra `feat(models): entry, lot, xp_event e level_event`.
2. `docker compose up -d --build --wait`
3. Antes do código: rode a C1 → `20 []`.
4. Crie os arquivos `src/models/rank_event.py`, `src/models/points_event.py` com o conteúdo do campo **Arquivos**.
5. Grave o conteúdo inteiro de `src/models/__init__.py` do campo **Arquivos**.
6. `docker compose up -d --build --wait`
7. Rode a C1 → `22 []`.
8. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `6 passed`.
9. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
10. Rode o **Verificar**.
11. Fim do passo, um comando por vez:
    ```
    git add -- src/models/rank_event.py src/models/points_event.py src/models/__init__.py
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "feat(models): rank_event e points_event"
    git log -1 --format=%B
    ```

**Testes:** nenhum teste novo. Teste de integração não importa de `src/` (TST-01) e model não é conta pura (TST-05). A prova é a C1, que sai de `20 []` (item 3) para `22 []` (item 7); as rotas das fases 5 a 9 usam estes models por HTTP.
**Verificar:**
- C1 → `22 []`.
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `6 passed`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/models/__init__.py
  src/models/points_event.py
  src/models/rank_event.py
  ```

**Pronto quando:**
- [ ] Os arquivos novos têm exatamente o conteúdo do campo **Arquivos**.
- [ ] `src/models/__init__.py` tem as 22 linhas do campo **Arquivos**, nesta ordem.
- [ ] C1 com `22 []`; suíte com `6 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata feito.

**Commit:** `feat(models): rank_event e points_event`
**Pare se:**
- A C1 do item 3 não der `20 []`.
- A C1 do item 7 terminar com `Traceback` ou listar uma tabela entre os colchetes: o model e o `database.sql` não batem, e o `database.sql` não muda neste passo.
- `docker compose up -d --build --wait` falhar: rode `docker compose logs --tail 100 api` e traga a saída.
- A suíte não terminar com `6 passed`.

---

### Passo 2.fim — Fechar a fase
**Branch:** fase/02-banco · **Depende de:** 2.1 a 2.13
**Objetivo:** provar a fase com o banco recriado do zero e levá-la para a `main` com a tag `fase-02`.
**Decisões:** TIM-04 — git por fase · TIM-08 — git automático · ARQ-03 — SQL só com o banco vazio · DAD-15 — banco nasce inteiro
**Arquivos:** nenhum. O passo não cria, não edita e não apaga arquivo.
**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/02-banco`.
2. `git log --oneline -n 20` → tem as 13 mensagens dos passos 2.1 a 2.13, cada uma uma vez:
   ```
   chore(ambiente): venv com flake8, pytest.ini e testes em 127.0.0.1
   test: remove os testes do sample_entity
   refactor(api): remove as rotas do sample_entity
   refactor: remove controller e repository do sample_entity
   refactor: remove DTO e schemas do sample_entity
   refactor(models): remove os models do sample_entity
   feat(banco): database.sql com as 22 tabelas e os dados iniciais
   feat(models): account_type, account_status, block_reason e transaction_type
   feat(models): entry_type, category_status, piggy_rank e customer
   feat(models): bank_clock, request_log, account e account_status_event
   feat(models): transaction, deposits, category e category_status_event
   feat(models): entry, lot, xp_event e level_event
   feat(models): rank_event e points_event
   ```
3. Recrie o banco do zero e suba tudo, um comando por vez:
   ```
   docker compose down -v
   docker compose up -d --build --wait
   ```
4. `docker compose exec -T db psql -U bootcamp -d bootcamp -t -A -c "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"` → `22`.
5. Rode a C1 → `22 []`.
6. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `6 passed`.
7. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
8. `git status --short` → saída vazia.
9. Leve a fase para a `main`, um comando por vez:
   ```
   git switch main
   git merge --no-ff --no-edit -m "feat(banco): fase 02 com as 22 tabelas e os 22 models" fase/02-banco
   git tag fase-02
   ```
10. Rode o **Verificar**.

**Testes:** nenhum teste novo. A suíte inteira roda com o banco recriado do zero (item 6).
**Verificar:**
- O `git status --short` antes do merge não mostra alterações.
- `git branch --show-current` → `main`.
- `git log -1 --format=%B` → `feat(banco): fase 02 com as 22 tabelas e os 22 models`.
- `git log -1 --format=%P` → dois hashes separados por um espaço (é um merge).
- `git tag --list fase-02` → `fase-02`.
- `git status --short` → saída vazia.

**Pronto quando:**
- [ ] O banco recriado do zero tem 22 tabelas e a C1 dá `22 []`.
- [ ] Suíte com `6 passed`; lint sem saída.
- [ ] Merge `--no-ff` na `main` com a mensagem exata; tag `fase-02` criada localmente; merge local na `main`.

**Commit:** nenhum commit de passo. Mensagem do merge: `feat(banco): fase 02 com as 22 tabelas e os 22 models`
**Pare se:**
- Faltar uma das 13 mensagens do item 2.
- `docker compose up -d --build --wait` falhar: rode `docker compose logs --tail 100 db` e `docker compose logs --tail 100 api` e traga as duas saídas.
- O item 4 não der `22` ou a C1 não der `22 []`.
- A suíte não terminar com `6 passed` ou o lint imprimir qualquer linha.
- O merge local der conflito (AGENTS.md, seção 8, item 9).

---

## Divergências encontradas

Seção para o Bruno; o agente não executa nada daqui. Registro para corrigir as notas. O `database.sql` do passo 2.7 já segue a coluna "Vale".

### `10 - Banco de dados` contra `04 - Decisões` (vale o 04)

| # | No 10 | No 04 | Vale (no `database.sql`) |
|---|---|---|---|
| 1 | Tabela `deposit`, no singular. | MOV-16 — quem depositou fica na tabela `deposits`. | `deposits`, com `deposit_key` e model `Deposit` (já no PLANO-00). |
| 2 | `bank_clock` sem key pública. | DAD-01 — toda tabela tem `id` e `<entidade>_key` (UUID), única; DAD-05 põe o relógio entre as entidades. | Coluna nova `bank_clock_key CHAR(36) NOT NULL`, `UNIQUE`. |
| 3 | `request_log` sem key pública (só `request_id`). | DAD-01, DAD-05 (os logs estão entre as entidades). | Coluna nova `request_log_key CHAR(36) NOT NULL`, `UNIQUE`. |
| 4 | Caixa "A confirmar": para onde vão IOF e IR. | COF-25 — decidida: lançamentos `IOF` e `IR` a crédito da conta do banco. | Sem efeito em coluna; a caixa do 10 está velha. |
| 5 | `account.level` "0 a 10". | GAM-15 — 10 níveis, e todos os números da gamificação são constantes ajustáveis. | Só o piso: `CHECK (level >= 0)` na conta e `CHECK (level >= 1)` no `level_event`. O teto de 10 mora na constante `MAX_LEVEL` (`src/calculations/xp.py`, passo 8.1), não no banco. |
| 6 | `category_status` com o valor `DELETED`. | API-15 — a consulta da categoria excluída devolve `status: deleted`, em minúsculas. | `DELETED` no banco, como todos os tipos fixos. No DTO (passo 9.3), usar `category.status.enumerator.lower()`: `active` ou `deleted`, conforme API-15 e o contrato da fase 3. Não há decisão pendente aqui. |

As 7 tabelas de tipos fixos e as 2 de eventos de estado (`account_status_event`, `category_status_event`) ficaram sem key, como no base, pela DAD-05 ("as tabelas de estado e de eventos de estado, como no base"). A DAD-01 diz "toda tabela": a nota 04 tem as duas frases.

### `10 - Banco de dados` contra o `codebase.md` (aviso)

| # | No 10 | No base | No `database.sql` |
|---|---|---|---|
| 7 | Keys e `request_control_key` com tipo `uuid`. | `database/database.sql` guarda a key em `CHAR(36)`; o repository gera com `uuid4()`. | `CHAR(36)`, como o base. |
| 8 | `request_log.request_id` com tipo `uuid`. | `build_request_id` (`src/utils/request_context.py`) aceita o `X-Request-ID` de quem chama: letras, números, `-` e `_`, até 64 caracteres. | `VARCHAR(64)`, sem `UNIQUE` (quem chama pode repetir o identificador). |
| 9 | Tabelas de tipos fixos só com `id` e `enumerator`. | `sample_entity_status` tem `created_at`. | Com `created_at`, como o base. |

### `PLANO-00-indice.md`

| # | Linha | Correção |
|---|---|---|
| 10 | "Colunas, tipos fixos, restrições e dados iniciais: os de `10 - Banco de dados`, com uma troca: `deposits`" | Passam a ser as trocas 1, 2, 3, 5, 7, 8 e 9 desta lista. |
| 11 | Registro de nomes (falta) | Nomes novos desta fase, obrigatórios nas próximas: os valores `INTERNAL`, `ADMIN` e `ACCOUNT` de `request_log.auth_failure` (o 4.1 grava `INTERNAL`; o 4.3, `ADMIN`; o 5.9, `ACCOUNT`); os índices `account_one_open_per_customer_idx`, `category_active_name_idx`, `category_one_default_idx`, `entry_account_created_at_id_idx`, `request_log_client_ip_created_at_idx` e `request_log_account_key_client_ip_created_at_idx`; os ids dos tipos fixos da tabela do passo 2.7. |

### Nomes novos dos models (registrar no PLANO-00)

| Onde | Nomes |
|---|---|
| Relacionamentos | `Account.account_type`, `Account.status`, `Account.rank`, `Account.yield_rank` · `AccountStatusEvent.status`, `AccountStatusEvent.block_reason` · `Transaction.transaction_type` · `Category.status` · `CategoryStatusEvent.status` · `Entry.entry_type` · `RankEvent.rank` |
| Constantes dos tipos fixos | `AccountType`: `CUSTOMER`, `PIGGY_BANK`, `BANK`, `OUTSIDE_WORLD` · `AccountStatus`: `ACTIVE`, `BLOCKED`, `CLOSED` · `BlockReason`: `SUSPICIOUS_ACTIVITY`, `JUDICIAL_ORDER`, `CUSTOMER_REQUEST`, `MANUAL_REVIEW` · `TransactionType`: `DEPOSIT`, `WITHDRAWAL`, `TRANSFER`, `SAVE`, `REDEEM`, `YIELD` · `EntryType`: `AMOUNT`, `FEE`, `PRIZE`, `YIELD`, `IOF`, `IR` · `CategoryStatus`: `ACTIVE`, `DELETED` · `PiggyRank`: `DEFAULT`, `BRONZE`, `SILVER`, `GOLD`, `PLATINUM`, `DIAMOND` |
| Constantes das colunas com `CHECK` | `RequestLog`: `INTERNAL`, `ADMIN`, `ACCOUNT` · `AccountStatusEvent`: `MANUAL`, `AUTOMATIC` · `XpEvent`: `TRANSFER_SENT`, `TRANSFER_RECEIVED`, `PIGGY_RECORD` · `RankEvent`: `UP`, `GRACE_START`, `GRACE_END`, `DOWN` · `PointsEvent`: `APPLY`, `RESET`, `FEE`, `CHANCE` |
| Comando | a conferência C1 (`docker compose exec -T api python -c ...`) |


## Correções da auditoria de 08/10

`created_at` de `transaction`, `entry`, `lot` e `account_status_event` usa `clock_timestamp()` no SQL e no model: `NOW()` marca o começo da transação, anterior à espera pela trava, e poderia inverter a ordem real dos lançamentos e a contagem desde o desbloqueio. Não mudar tipos de coluna. DAD-18 e DAD-19 continuam pendentes; não considerar o banco liberado até Bruno resolver essas divergências.
