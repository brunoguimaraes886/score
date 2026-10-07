# PLANO-00 — índice

Índice do plano do protótipo bancário do Bootcamp QI Tech 2026. Os nomes deste arquivo são obrigatórios em todas as fases: tabelas, models, rotas, schemas, erros, classes, funções, arquivos, variáveis de ambiente e cabeçalhos. Os passos completos ficam em `docs/plano/PLANO-fase-NN.md`; as regras de execução, no `AGENTS.md`.

## Como ler

- Os códigos (`MOV-12`) são as decisões de `docs/decisoes.md`.
- Cada arquivo de um passo vem com o que o passo faz com ele: criar, editar ou apagar. Apagar é sempre com `git rm`.
- Passo de camada de baixo (repository, DTO, controller) não tem teste novo; o teste vem no passo da rota, que fica vermelho antes do código.
- Os passos da fase 11 são de prova: o teste confere o que já existe.
- A fase 0 e a seção "(c) Feito à mão" são do Bruno, não do agente.

## Ordem das fases

| Ordem | Fase | Branch | Depende de |
|---|---|---|---|
| 1 | 0 — preparação [HUMANO] | `main` | — |
| 2 | 2 — banco | `fase/02-banco` | 0 |
| 3 | 3 — contrato | `fase/03-contrato` | 2 |
| 4 | 4 — esqueleto | `fase/04-esqueleto` | 3 |
| 5 | 5 — cliente e conta | `fase/05-cliente-conta` | 4 |
| 6 | 6 — depósito, transferência e extrato | `fase/06-dinheiro` | 5 |
| 7 | 8 — XP, nível e pontos | `fase/08-xp-pontos` | 6 |
| 8 | 7 — cofrinho, virada do dia, ranque e carência | `fase/07-cofrinho` | 8 |
| 9 | 9 — categorias, IR/IOF e chance de não debitar | `fase/09-categorias-impostos-sorteio` | 7 |
| 10 | 11 — provas extras | `fase/11-provas-extras` | 9 |

Uma fase por vez, nesta ordem. As etapas 1, 10, 12 e 13 do plano de trabalho não são do agente.

Duas diferenças em relação ao plano de trabalho:

- **A fase 8 roda antes da 7.** Guardar no cofrinho e virar o dia dão XP de recorde (GAM-04, GAM-19, GAM-25), e quem soma XP e sobe nível é a fase 8 (`GamificationController.award_record_xp`).
- **Lotes e a categoria "economias" entram na fase 7.** O rendimento é contado por lote (DIA-03, COF-13, COF-15, COF-23): o primeiro guardar já cria lote, e o primeiro resgate já tira do lote mais antigo. A fase 9 fica com as categorias criadas pelo dono, o IR e o IOF e a chance de não debitar.

Se o tempo apertar, a fase 11 fica só com os passos 11.1 e 11.2 (TST-08 — provas extras).

## Registro de nomes

### Cabeçalhos e variáveis de ambiente

| Nome | Tipo | Padrão no `docker-compose.yml` | Passo |
|---|---|---|---|
| `INTERNAL-TOKEN` | cabeçalho | — | base |
| `ACCOUNT-TOKEN` | cabeçalho (token da conta, API-16) | — | 4.2 |
| `ADMIN-TOKEN` | cabeçalho (rotas `/internal`, PRD-13) | — | 4.2 |
| `INTERNAL_TOKEN` | variável | `default_token` | base |
| `ADMIN_TOKEN` | variável | `default_admin_token` | 4.2 |
| `AUTH_FAILURE_LIMIT` | variável | `10` | 4.2 |
| `AUTH_FAILURE_WINDOW_MINUTES` | variável | `15` | 4.2 |
| `DB_LOCK_TIMEOUT_MS` | variável | `5000` | 4.2 |
| `DB_STATEMENT_TIMEOUT_MS` | variável | `5000` | 4.2 |
| `BCB_API_URL` | variável | `http://mockserver:1080` | 7.8 e 7.10 |
| `BCB_API_TIMEOUT` | variável | `5` | 7.8 e 7.10 |
| `MOCKSERVER_PORT` | variável (porta da máquina) | `1080` | 7.10 |
| `MOCKSERVER_URL` | variável dos testes | `http://127.0.0.1:1080` (padrão no código do teste) | 7.10 |

Saem no 7.8 e no 7.10: `BANKSLIP_API_URL`, `BANKSLIP_API_INTERNAL_TOKEN`, `BANKSLIP_API_TIMEOUT`.

Constantes novas em `src/constants.py` (4.2): `ADMIN_TOKEN`, `AUTH_FAILURE_LIMIT`, `AUTH_FAILURE_WINDOW_MINUTES`, `DB_LOCK_TIMEOUT_MS`, `DB_STATEMENT_TIMEOUT_MS`, `INTERNAL_TOKEN_HEADER = "INTERNAL-TOKEN"`, `ACCOUNT_TOKEN_HEADER = "ACCOUNT-TOKEN"`, `ADMIN_TOKEN_HEADER = "ADMIN-TOKEN"`, `INTERNAL_PREFIX = "/internal"`. Em 7.8: `BCB_API_URL`, `BCB_API_TIMEOUT`.

### Tabelas e models

Uma tabela por model, em `src/models/`, listado em `src/models/__init__.py` na ordem dos passos.

| Tabela | Model | Arquivo | Passo |
|---|---|---|---|
| `account_type` | `AccountType` | `account_type.py` | 2.8 |
| `account_status` | `AccountStatus` | `account_status.py` | 2.8 |
| `block_reason` | `BlockReason` | `block_reason.py` | 2.8 |
| `transaction_type` | `TransactionType` | `transaction_type.py` | 2.8 |
| `entry_type` | `EntryType` | `entry_type.py` | 2.9 |
| `category_status` | `CategoryStatus` | `category_status.py` | 2.9 |
| `piggy_rank` | `PiggyRank` | `piggy_rank.py` | 2.9 |
| `customer` | `Customer` | `customer.py` | 2.9 |
| `bank_clock` | `BankClock` | `bank_clock.py` | 2.10 |
| `request_log` | `RequestLog` | `request_log.py` | 2.10 |
| `account` | `Account` | `account.py` | 2.10 |
| `account_status_event` | `AccountStatusEvent` | `account_status_event.py` | 2.10 |
| `transaction` | `Transaction` | `transaction.py` | 2.11 |
| `deposits` | `Deposit` | `deposit.py` | 2.11 |
| `category` | `Category` | `category.py` | 2.11 |
| `category_status_event` | `CategoryStatusEvent` | `category_status_event.py` | 2.11 |
| `entry` | `Entry` | `entry.py` | 2.12 |
| `lot` | `Lot` | `lot.py` | 2.12 |
| `xp_event` | `XpEvent` | `xp_event.py` | 2.12 |
| `level_event` | `LevelEvent` | `level_event.py` | 2.12 |
| `rank_event` | `RankEvent` | `rank_event.py` | 2.13 |
| `points_event` | `PointsEvent` | `points_event.py` | 2.13 |

Colunas, tipos fixos, restrições e dados iniciais: os de `10 - Banco de dados`, com uma troca: a tabela de quem depositou se chama `deposits`, como na MOV-16 (o 10 propunha `deposit`; vale o 04).

### Rotas

Toda rota pede `INTERNAL-TOKEN`, menos `/` e `/health_check`. "Conta" = também `ACCOUNT-TOKEN`; "Admin" = também `ADMIN-TOKEN`.

| Método e caminho | Tokens | Schema | Resource e método | Passo |
|---|---|---|---|---|
| `GET /` | nenhum | — | `HealthCheckResource.on_get_home` | base |
| `GET /health_check` | nenhum | — | `HealthCheckResource.on_get_health_check` | base |
| `POST /customers` | interno | `post_customers.json` | `CustomerResource.on_post` | 5.3 |
| `GET /customers/{customer_key}` | conta | — | `CustomerResource.on_get_by_key` | 5.8 |
| `POST /customers/{customer_key}/accounts` | interno | — | `AccountResource.on_post_account` | 5.6 |
| `GET /accounts/{account_key}` | conta | — | `AccountResource.on_get_by_key` | 5.7 |
| `DELETE /accounts/{account_key}` | conta | — | `AccountResource.on_delete_by_key` | 5.11 |
| `POST /accounts/{account_key}/deposits` | interno | `post_deposits.json` | `TransactionResource.on_post_deposit` | 6.5 |
| `POST /accounts/{account_key}/withdrawals` | conta | `post_withdrawals.json` | `TransactionResource.on_post_withdrawal` | 6.6 |
| `POST /accounts/{account_key}/transfers` | conta | `post_transfers.json` | `TransactionResource.on_post_transfer` | 6.8 |
| `GET /accounts/{account_key}/transactions/{transaction_key}` | conta | — | `TransactionResource.on_get_transaction` | 6.10 |
| `GET /accounts/{account_key}/entries` | conta | `get_entries.json` | `TransactionResource.on_get_entries` | 6.11 |
| `GET /accounts/{account_key}/gamification` | conta | — | `GamificationResource.on_get` | 8.4 |
| `POST /accounts/{account_key}/point_applications` | conta | `post_point_applications.json` | `GamificationResource.on_post_point_application` | 8.6 |
| `POST /accounts/{account_key}/point_resets` | conta | — | `GamificationResource.on_post_point_reset` | 8.6 |
| `POST /accounts/{account_key}/savings` | conta | `post_savings.json` | `PiggyBankResource.on_post_saving` | 7.5 |
| `POST /accounts/{account_key}/redemptions` | conta | `post_redemptions.json` | `PiggyBankResource.on_post_redemption` | 7.6 |
| `GET /accounts/{account_key}/piggy_bank_entries` | conta | `get_piggy_bank_entries.json` | `PiggyBankResource.on_get_piggy_bank_entries` | 7.7 |
| `POST /accounts/{account_key}/categories` | conta | `post_categories.json` | `CategoryResource.on_post` | 9.4 |
| `GET /accounts/{account_key}/categories` | conta | `get_categories.json` | `CategoryResource.on_get_list` | 9.4 |
| `GET /accounts/{account_key}/categories/{category_key}` | conta | — | `CategoryResource.on_get_by_key` | 9.5 |
| `DELETE /accounts/{account_key}/categories/{category_key}` | conta | — | `CategoryResource.on_delete_by_key` | 9.5 |
| `POST /internal/accounts/{account_key}/blocks` | admin | `post_blocks.json` | `InternalResource.on_post_block` | 5.10 |
| `POST /internal/accounts/{account_key}/unblocks` | admin | — | `InternalResource.on_post_unblock` | 5.10 |
| `POST /internal/day_closings` | admin | `post_day_closings.json` | `InternalResource.on_post_day_closing` | 7.11 |

Arquivos dos resources, em `src/resources/`: `customer.py`, `account.py`, `transaction.py`, `gamification.py`, `piggy_bank.py`, `category.py`, `internal.py`. Status de sucesso, corpo de cada resposta e erros de cada rota: `docs/rotas.md` (3.1).

### Schemas de entrada

Em `src/schemas/`, todos com `"additionalProperties": false`; todo campo de dinheiro com `"type": "integer"` e `"minimum": 1`.

| Arquivo | Campos | Passo |
|---|---|---|
| `post_customers.json` | `name`, `document_number`, `email`, `birthdate` | 3.3 |
| `post_deposits.json` | `depositor_name`, `depositor_document`, `amount`, `request_control_key` | 3.3 |
| `post_withdrawals.json` | `amount`, `request_control_key` | 3.3 |
| `post_transfers.json` | `destination_account_key`, `amount`, `request_control_key` | 3.4 |
| `get_entries.json` | `limit`, `page` | 3.4 |
| `get_categories.json` | `limit`, `page` | 3.4 |
| `get_piggy_bank_entries.json` | `limit`, `page`, `category_key` | 3.4 |
| `post_savings.json` | `amount`, `request_control_key`, `category_key` (opcional) | 3.5 |
| `post_redemptions.json` | `amount`, `request_control_key`, `category_key` (opcional) | 3.5 |
| `post_categories.json` | `name` | 3.5 |
| `post_point_applications.json` | `benefit` (`FEE` ou `CHANCE`), `points` | 3.5 |
| `post_day_closings.json` | `accounting_date` | 3.6 |
| `post_blocks.json` | `reason` (`SUSPICIOUS_ACTIVITY`, `JUDICIAL_ORDER`, `CUSTOMER_REQUEST`, `MANUAL_REVIEW`) | 3.6 |

### Catálogo de erros

Criado inteiro no passo 3.2. Os genéricos ficam em `src/errors/base_error.py`; os do projeto, em `src/errors/custom_errors.py`. `QIT001001` e `QIT001002` (do `sample_entity`) saem e não voltam.

| Código | Classe | Status | Quando |
|---|---|---|---|
| `QIT000003` | `ForbiddenNotAdmin` | 403 | rota `/internal` sem o `ADMIN-TOKEN` certo |
| `QIT000429` | `TooManyAuthFailures` | 429 | a barreira contra chute de token disparou |
| `QIT000503` | `DatabaseTimeout` | 503 | estourou `lock_timeout` ou `statement_timeout` |
| `QIT001003` | `InvalidDocumentNumber` | 422 | CPF ou CNPJ com dígito verificador errado |
| `QIT001004` | `DuplicatedDocumentNumber` | 409 | CPF já cadastrado |
| `QIT001005` | `DuplicatedEmail` | 409 | e-mail já cadastrado |
| `QIT001006` | `UnderageCustomer` | 422 | menos de 18 anos |
| `QIT001007` | `InvalidBirthdate` | 422 | data de nascimento que não existe |
| `QIT001008` | `CustomerNotFound` | 404 | cliente não existe, ou o token não é da conta aberta dele |
| `QIT001009` | `CustomerAlreadyHasAccount` | 409 | o cliente já tem conta não encerrada |
| `QIT001010` | `AccountNotFound` | 404 | conta não existe, não é de cliente, ou o token não é dela |
| `QIT001011` | `AccountNotActive` | 409 | a conta está bloqueada ou encerrada |
| `QIT001012` | `AccountNotEmpty` | 409 | encerrar com saldo ou cofrinho diferente de zero |
| `QIT001013` | `AccountNotBlocked` | 409 | desbloquear conta que não está bloqueada |
| `QIT001014` | `IdempotencyKeyConflict` | 409 | mesma `request_control_key` com outro corpo |
| `QIT001015` | `InsufficientBalance` | 422 | o saldo não cobre o valor (mais a tarifa, na transferência) |
| `QIT001016` | `SameAccountTransfer` | 422 | origem igual ao destino |
| `QIT001017` | `DestinationAccountNotFound` | 404 | conta de destino não existe ou não é de cliente |
| `QIT001018` | `DestinationAccountNotActive` | 409 | conta de destino bloqueada ou encerrada |
| `QIT001019` | `DailyTransferLimitReached` | 422 | a 11ª transferência enviada no dia contábil |
| `QIT001020` | `TransactionNotFound` | 404 | operação que não existe ou não é desta conta |
| `QIT001021` | `CategoryNotFound` | 404 | categoria que não existe neste cofrinho |
| `QIT001022` | `CategoryDeleted` | 409 | guardar, resgatar ou excluir em categoria excluída |
| `QIT001023` | `InsufficientCategoryBalance` | 422 | resgate maior que o saldo da categoria |
| `QIT001024` | `DuplicatedCategoryName` | 409 | nome repetido entre as categorias ativas |
| `QIT001025` | `DefaultCategoryCannotBeDeleted` | 409 | excluir "economias" |
| `QIT001026` | `CategoryNotEmpty` | 409 | excluir categoria com dinheiro |
| `QIT001027` | `NotEnoughFreePoints` | 422 | aplicar mais pontos do que os livres |
| `QIT001028` | `DayAlreadyClosed` | 409 | virada de uma data já fechada |
| `QIT001029` | `FutureAccountingDate` | 422 | virada de uma data depois do relógio |
| `QIT001030` | `InvalidAccountingDate` | 422 | data da virada que não existe no calendário |
| `QIT001031` | `CdiUnavailable` | 503 | o Banco Central (Mockserver) não respondeu a tempo |

### Middlewares

Ordem de execução, de fora para dentro. No `src/app.py` o registro é o inverso desta lista.

1. `register_request_context_middleware` (base; no 4.1 passa a criar o `RequestState`)
2. `register_request_logger_middleware` (base)
3. `register_request_log_writer_middleware` (`src/middlewares/request_log_writer.py`, 4.5)
4. `register_auth_barrier_middleware` (`src/middlewares/auth_barrier.py`, 4.6 e 5.9)
5. `register_internal_token_middleware` (base; no 4.1 grava a falha no `RequestState`)
6. `register_admin_token_middleware` (`src/middlewares/admin_token.py`, 4.3)
7. `register_session_manager_middleware` (base)

Os middlewares 3 e 4 não atendem `BYPASS_ENDPOINTS`: o health check continua sem tocar no banco (PRD-02).

### Contas puras

Em `src/calculations/`, exportadas por `src/calculations/__init__.py`. Só biblioteca padrão, `constants` e arquivos da própria pasta.

| Arquivo | Nomes | Passo |
|---|---|---|
| `fee.py` | `calculate_fee(amount_cents, fee_points)` | 6.3 |
| `xp.py` | `MAX_LEVEL`, `level_cost(next_level)`, `next_level_n(level)`, `record_whole_reais(new_balance_cents, record_cents)`, `gain_transfer_xp(level, xp, amount_cents)`, `gain_record_xp(level, xp, whole_reais)`, `XpGain` | 8.1 |
| `ranks.py` | `RANK_ORDER`, `RANK_MINIMUM_CENTS`, `RANK_CDI_PERCENT`, `GRACE_DAYS`, `rank_for_balance(balance_cents)` | 7.1 |
| `lots.py` | `split_redemption(principal_remaining, yield_remaining, amount_cents)` | 7.1 |
| `piggy_yield.py` | `daily_rate(cdi_daily_percent, rank_cdi_percent)`, `lot_yield(lot_balance_cents, residue, rate)` | 7.2 |
| `taxes.py` | `ir_percent(days)`, `iof_percent(days)`, `redemption_taxes(yield_parts)` | 9.1 |
| `lottery.py` | `PRIZE_LIMIT_CENTS`, `is_eligible_for_prize(amount_cents)`, `draw_prize(chance_points, rng)` | 9.7 |

### Camadas e peças de apoio

| Peça | Arquivo | Nomes (passo em que nasce cada um) |
|---|---|---|
| `RequestState` | `src/utils/request_context.py` | `RequestState` (`request_id`, `error_code`, `auth_failure`, `account_key`), `start_request_state`, `get_request_state` (4.1) |
| Token da conta | `src/utils/account_token.py` | `generate_account_token`, `hash_account_token`, `account_token_matches` (5.4) |
| Hash do corpo | `src/utils/request_hash.py` | `hash_request_body` (6.4) |
| Documento | `src/utils/document_number.py` | `is_valid_cnpj`, `mask_document_number` (6.2) |
| `CustomerRepository` | `src/repositories/customer_repository.py` | `create`, `get_by_key`, `get_by_document_number`, `get_by_email` (5.1) |
| `AccountRepository` | `src/repositories/account_repository.py` | `create_customer_account`, `get_by_key`, `get_customer_account`, `get_open_account_by_customer`, `get_piggy_bank`, `get_system_account`, `lock_accounts`, `change_status` (5.4) |
| `CategoryRepository` | `src/repositories/category_repository.py` | `create_default`, `get_default` (5.4); `get_balance` (7.3); `create`, `get_by_key`, `list_active_page`, `delete` (9.3) |
| `TransactionRepository` | `src/repositories/transaction_repository.py` | `create`, `get_by_request_control_key`, `get_by_key_for_account` (6.1); `count_transfers_sent` (6.9) |
| `EntryRepository` | `src/repositories/entry_repository.py` | `create` (6.1); `list_page` (6.11); `list_piggy_bank_page` (7.7) |
| `DepositRepository` | `src/repositories/deposit_repository.py` | `create` (6.1) |
| `BankClockRepository` | `src/repositories/bank_clock_repository.py` | `get_accounting_date`, `lock`, `advance` (6.1) |
| `LotRepository` | `src/repositories/lot_repository.py` | `create`, `list_open_for_update` (7.3); `list_open_by_piggy_bank_for_update` (7.12) |
| `GamificationRepository` | `src/repositories/gamification_repository.py` | `create_xp_event`, `create_level_event`, `create_points_event`, `create_rank_event` (8.2) |
| `RequestLogRepository` | `src/repositories/request_log_repository.py` | `create`, `count_auth_failures` (4.5) |
| `BaseController` | `src/controllers/base_controller.py` | `get_owned_account(account_key, account_token)` (5.5) |
| `CustomerController` | `src/controllers/customer_controller.py` | `create` (5.2); `get_by_key` (5.8) |
| `AccountController` | `src/controllers/account_controller.py` | `open_account`, `get_account` (5.5); `block_account`, `unblock_account` (5.10); `close_account` (5.11; regras somadas em 6.12 e 7.15) |
| `TransactionController` | `src/controllers/transaction_controller.py` | `deposit` (6.4); `withdraw` (6.6); `transfer` (6.7; somas em 6.9, 8.5, 8.7, 9.8); `get_transaction` (6.10); `list_entries` (6.11) |
| `GamificationController` | `src/controllers/gamification_controller.py` | `get_gamification`, `award_transfer_xp`, `award_record_xp` (8.3); `apply_points`, `reset_points` (8.6) |
| `PiggyBankController` | `src/controllers/piggy_bank_controller.py` | `save`, `redeem` (7.4; somas em 9.2 e 9.6); `list_piggy_bank_entries` (7.7) |
| `DayClosingController` | `src/controllers/day_closing_controller.py` | `close_day` (7.11; somas em 7.12, 7.13, 7.14) |
| `CategoryController` | `src/controllers/category_controller.py` | `create_category`, `list_categories`, `get_category`, `delete_category` (9.3) |
| DTOs | `src/dtos/` | `CustomerDTO` (5.1), `AccountDTO` (5.5), `TransactionDTO` (6.2; resgate bruto e líquido no 7.4), `EntryDTO` (6.2), `GamificationDTO` (8.2), `CategoryDTO` (9.3) |
| `BcbConnector` | `src/connectors/bcb_connector.py` | `get_cdi_rate(accounting_date)` (7.8) |
| Testes: requisições | `tests/utils/request_generator.py` | `RequestGenerator`, `INTERNAL_TOKEN`, `ADMIN_TOKEN` (4.7) |
| Testes: corpos e objetos | `tests/utils/payload_generator.py`, `tests/utils/object_generator.py` | `PayloadGenerator`, `ObjectGenerator` (4.8) |
| Testes: Mockserver | `tests/utils/mock_generator.py` | `MockGenerator.set_cdi_rate`, `set_cdi_delay`, `clear_cdi` (7.10) |
| Script do CDI | `scripts/download_cdi.py` | grava `mockserver/cdi_expectations.json` (7.9) |
| Imagem do Mockserver | `mockserver/Dockerfile` | serviço `mockserver` no compose (7.10) |
| Tabela de rotas | `docs/rotas.md` | 3.1 |

## Fase 0 — preparação [HUMANO]

**Branch:** `main` · **Depende de:** nada
**Objetivo:** o repositório `score` com o base, o `AGENTS.md`, o `CLAUDE.md`, o plano e o espelho das decisões, publicado na `main`.

Tudo no PowerShell. Antes do primeiro comando, troque os três caminhos pelos da sua máquina.

```powershell
$repo = "C:\Users\bruno\Desktop\Life\QI Tech\bootcamp QITech\score"
$base = "C:\Users\bruno\Desktop\Life\QI Tech\bootcamp QITech\bootcamp-base-api"
$decisoes = "C:\Users\bruno\Desktop\Life\QI Tech\bootcamp QITech\_contexto"
```

**0.1 — Conferir o repositório (TIM-04 — repositório novo e privado)**

```powershell
Set-Location $repo
git remote -v
git status
```

- `git remote -v` mostra `origin` apontando para `https://github.com/brunoguimaraes886/score` (fetch e push).
- `git status` não mostra arquivo modificado.
- Abra `https://github.com/brunoguimaraes886/score` numa janela anônima: tem de dar 404 (privado).

**0.2 — Copiar o base sem `.git` (ARQ-11 — pode mudar o base)**

```powershell
robocopy $base $repo /E /XD .venv .pytest_cache __pycache__ .git /XF .env
Get-ChildItem $repo -Force -Name
```

- O `robocopy` termina com código 1 (arquivos copiados); de 0 a 7 não é erro.
- A lista mostra `.env.example`, `.flake8`, `.gitignore`, `database`, `docker-compose.yml`, `Dockerfile`, `docs`, `LICENSE`, `README.md`, `requirements-dev.txt`, `requirements.txt`, `src`, `tests` e `.git`; não mostra `.venv` nem `.env`.

**0.3 — Colocar `AGENTS.md`, `CLAUDE.md`, plano e decisões (TIM-07 — espelho das decisões)**

1. Salve o `AGENTS.md` deste chat em `$repo`.
2. Rode:

```powershell
[System.IO.File]::WriteAllText("$repo\CLAUDE.md", "@AGENTS.md`n")
New-Item -ItemType Directory -Force -Path "$repo\docs\plano"
Copy-Item -LiteralPath $decisoes -Destination "$repo\docs\decisoes.md"
```

3. Salve o `PLANO-00-indice.md` em `$repo\docs\plano\`.

**0.4 — Primeiro commit e push na `main` (TIM-04)**

```powershell
git add -A
git status --short
git commit -m "chore: base do bootcamp, AGENTS.md e plano"
git branch -M main
git push -u origin main
```

- Antes do commit, a lista do `git status --short` não tem `.env` (só `.env.example`) nem `.venv`.
- Se o push for recusado porque o GitHub já tem um commit: `git pull origin main --allow-unrelated-histories --no-edit` e, depois, `git push -u origin main`.

**0.5 — Só se for usar o Claude Code: commit sem assinatura**

```powershell
New-Item -ItemType Directory -Force -Path "$repo\.claude"
[System.IO.File]::WriteAllText("$repo\.claude\settings.local.json", '{"attribution": {"commit": "", "pr": ""}}')
```

A pasta `.claude/` está no `.gitignore` do base: o arquivo nunca vai para o Git.

## Fase 2 — banco

**Branch:** `fase/02-banco` · **Depende de:** fase 0
**Objetivo:** o `database.sql` com as 22 tabelas e um model por tabela, sem nada do `sample_entity`.

**2.1 — Preparar o ambiente**
- Entrega: `.venv` com o `requirements-dev.txt` instalado; `flake8==7.1.1` no `requirements-dev.txt`; `pytest.ini` com `pythonpath = src`; padrão do `SERVER_LOCALHOST` trocado de `0.0.0.0` para `127.0.0.1` nos testes e no `.env.example`.
- Decisões: TST-05 — unitários em pasta separada; ARQ-04 — sobe sem `.env`.
- Arquivos: `requirements-dev.txt` (editar) · `pytest.ini` (criar) · `tests/conftest.py` (editar) · `tests/utils/requisition.py` (editar) · `.env.example` (editar)

**2.2 — Apagar os testes do sample_entity**
- Entrega: `tests/integration/` só com `test_healthcheck.py`.
- Decisões: ARQ-11 — pode apagar o `sample_entity`.
- Arquivos: `tests/integration/sample_entity/test_sample_entities.py` (apagar) · `tests/integration/sample_entity/test_sample_entity_create.py` (apagar) · `tests/integration/sample_entity/test_sample_entity_get.py` (apagar) · `tests/integration/sample_entity/test_sample_entity_update.py` (apagar)

**2.3 — Apagar as rotas do sample_entity**
- Entrega: `src/app.py` só com `/` e `/health_check`; `src/resources/__init__.py` só com `HealthCheckResource`.
- Decisões: ARQ-11 — pode apagar o `sample_entity`.
- Arquivos: `src/app.py` (editar) · `src/resources/sample_entity.py` (apagar) · `src/resources/__init__.py` (editar)

**2.4 — Apagar controller e repository do sample_entity**
- Entrega: `src/controllers/__init__.py` e `src/repositories/__init__.py` vazios; `BaseController` intacto.
- Decisões: ARQ-11 — pode apagar o `sample_entity`.
- Arquivos: `src/controllers/sample_entity_controller.py` (apagar) · `src/controllers/__init__.py` (editar) · `src/repositories/sample_entity_repository.py` (apagar) · `src/repositories/__init__.py` (editar)

**2.5 — Apagar DTO e schemas do sample_entity**
- Entrega: `src/dtos/__init__.py` vazio; nenhum schema em `src/schemas/`.
- Decisões: ARQ-11 — pode apagar o `sample_entity`.
- Arquivos: `src/dtos/sample_entity_dto.py` (apagar) · `src/dtos/__init__.py` (editar) · `src/schemas/post_sample_entity.json` (apagar) · `src/schemas/put_sample_entity.json` (apagar) · `src/schemas/get_sample_entities.json` (apagar)

**2.6 — Apagar os models do sample_entity**
- Entrega: `src/models/` só com `base.py` e o `__init__.py` vazio.
- Decisões: ARQ-11 — pode apagar o `sample_entity`.
- Arquivos: `src/models/sample_entity.py` (apagar) · `src/models/sample_entity_status.py` (apagar) · `src/models/sample_entity_status_event.py` (apagar) · `src/models/__init__.py` (editar)

**2.7 — O `database.sql` completo**
- Entrega: as 22 tabelas do registro, com chaves, `UNIQUE`, `CHECK` e índices da seção "Restrições" do 10; dados iniciais: os 7 tipos fixos, a conta `BANK` e a conta `OUTSIDE_WORLD` e o relógio em `2026-06-01`.
- Decisões: DAD-01 — id e key; DAD-05 — entidades; DAD-06 — tabela de operações; DAD-07 — saldo em dois lugares; DAD-08 — centavos em `BIGINT`; DAD-09 — contas do sistema; DAD-10 — só o sistema fica negativo; DAD-14 — gamificação em eventos e colunas; DAD-15 — banco nasce inteiro; DAD-17 — duas datas; CLI-04 — uma conta aberta; COF-14 — cofrinho é conta; COF-15 — fração de centavo; COF-18 — nome único; COF-23 — colunas do lote; COF-25 — imposto para o banco; DIA-04 — começa em 01/06/2026; MOV-12 — idempotência; MOV-16 — tabela `deposits`; PRD-14 — colunas do log; R4 — append-only.
- Arquivos: `database/database.sql` (editar)

**2.8 — Models dos tipos fixos (1 de 2)**
- Entrega: `AccountType`, `AccountStatus`, `BlockReason`, `TransactionType`.
- Decisões: DAD-04 — entidade, estado, relação; CLI-05 — estados da conta; DAD-06 — tipos de operação.
- Arquivos: `src/models/account_type.py` (criar) · `src/models/account_status.py` (criar) · `src/models/block_reason.py` (criar) · `src/models/transaction_type.py` (criar) · `src/models/__init__.py` (editar)

**2.9 — Models dos tipos fixos (2 de 2) e do cliente**
- Entrega: `EntryType`, `CategoryStatus`, `PiggyRank`, `Customer`.
- Decisões: DAD-16 — tipos de lançamento; GAM-12 — ranques; CLI-02 — dados do cliente.
- Arquivos: `src/models/entry_type.py` (criar) · `src/models/category_status.py` (criar) · `src/models/piggy_rank.py` (criar) · `src/models/customer.py` (criar) · `src/models/__init__.py` (editar)

**2.10 — Models do relógio, do log e da conta**
- Entrega: `BankClock`, `RequestLog`, `Account`, `AccountStatusEvent`.
- Decisões: DIA-01 — relógio do banco; PRD-06 — log de toda requisição; COF-14 — cofrinho é conta; CLI-05 — estados da conta.
- Arquivos: `src/models/bank_clock.py` (criar) · `src/models/request_log.py` (criar) · `src/models/account.py` (criar) · `src/models/account_status_event.py` (criar) · `src/models/__init__.py` (editar)

**2.11 — Models da operação, do depósito e da categoria**
- Entrega: `Transaction`, `Deposit` (tabela `deposits`), `Category`, `CategoryStatusEvent`.
- Decisões: DAD-06 — tabela de operações; MOV-16 — tabela `deposits`; COF-03 — categorias; API-15 — excluir categoria.
- Arquivos: `src/models/transaction.py` (criar) · `src/models/deposit.py` (criar) · `src/models/category.py` (criar) · `src/models/category_status_event.py` (criar) · `src/models/__init__.py` (editar)

**2.12 — Models do lançamento, do lote e dos eventos de XP e nível**
- Entrega: `Entry`, `Lot`, `XpEvent`, `LevelEvent`.
- Decisões: DAD-05 — entidades; COF-06 — lotes; DAD-14 — gamificação em eventos e colunas.
- Arquivos: `src/models/entry.py` (criar) · `src/models/lot.py` (criar) · `src/models/xp_event.py` (criar) · `src/models/level_event.py` (criar) · `src/models/__init__.py` (editar)

**2.13 — Models dos eventos de ranque e de pontos**
- Entrega: `RankEvent`, `PointsEvent`; os 22 models batem com as 22 tabelas.
- Decisões: DAD-14 — gamificação em eventos e colunas; GAM-14 — carência; GAM-21 — aplicar e zerar.
- Arquivos: `src/models/rank_event.py` (criar) · `src/models/points_event.py` (criar) · `src/models/__init__.py` (editar)

**2.fim — Fechar a fase** (AGENTS.md, seção 7).

## Fase 3 — contrato

**Branch:** `fase/03-contrato` · **Depende de:** fase 2
**Objetivo:** a tabela de rotas, o catálogo de erros inteiro e os 13 schemas de entrada.

**3.1 — Tabela de rotas**
- Entrega: `docs/rotas.md` com uma linha por rota do registro: método, caminho, tokens, schema, status e corpo de sucesso, erros (código e status) e se é idempotente, com o porquê. A convenção de nomes vem no topo.
- Decisões: API-05 — tabela de rotas; API-06 — convenção REST; API-07 — inglês e plural; API-08 — rotas aninhadas; API-10 — resposta de sucesso; API-13 — rotas `/internal`.
- Arquivos: `docs/rotas.md` (criar)

**3.2 — Catálogo de erros**
- Entrega: as 32 classes do catálogo; `QIT001001` e `QIT001002` saem; `UnderageSampleEntity` vira `UnderageCustomer`.
- Decisões: API-01 — formato de erro; API-11 — status de erro; API-12 — catálogo; R3 — código de erro próprio.
- Arquivos: `src/errors/base_error.py` (editar) · `src/errors/custom_errors.py` (editar)

**3.3 — Schemas do cliente, do depósito e do saque**
- Entrega: `tests/unit/test_schema_files.py` (confere, para cada schema, JSON válido, `"additionalProperties": false` e dinheiro inteiro a partir de 1); `post_customers.json`, `post_deposits.json`, `post_withdrawals.json`.
- Decisões: API-03 — schema fechado; API-18 — valor inteiro ≥ 1; CLI-02 — dados do cliente; MOV-12 — idempotência; MOV-16 — corpo do depósito; R6 — sem float.
- Arquivos: `tests/unit/__init__.py` (criar) · `tests/unit/test_schema_files.py` (criar) · `src/schemas/post_customers.json` (criar) · `src/schemas/post_deposits.json` (criar) · `src/schemas/post_withdrawals.json` (criar)

**3.4 — Schemas da transferência e das listas**
- Entrega: `post_transfers.json`, `get_entries.json`, `get_categories.json`, `get_piggy_bank_entries.json`; `limit` de 1 a 100 (o regex do base aceitava 0).
- Decisões: MOV-04 — envelope do extrato; MOV-12 — idempotência; API-03 — schema fechado; API-18 — valor inteiro ≥ 1.
- Arquivos: `tests/unit/test_schema_files.py` (editar) · `src/schemas/post_transfers.json` (criar) · `src/schemas/get_entries.json` (criar) · `src/schemas/get_categories.json` (criar) · `src/schemas/get_piggy_bank_entries.json` (criar)

**3.5 — Schemas do cofrinho, das categorias e dos pontos**
- Entrega: `post_savings.json`, `post_redemptions.json`, `post_categories.json`, `post_point_applications.json`.
- Decisões: COF-03 — categorias; COF-10 — guardar e resgatar; GAM-21 — aplicar e zerar; MOV-12 — idempotência; API-18 — valor inteiro ≥ 1.
- Arquivos: `tests/unit/test_schema_files.py` (editar) · `src/schemas/post_savings.json` (criar) · `src/schemas/post_redemptions.json` (criar) · `src/schemas/post_categories.json` (criar) · `src/schemas/post_point_applications.json` (criar)

**3.6 — Schemas das rotas internas**
- Entrega: `post_day_closings.json`, `post_blocks.json`.
- Decisões: DIA-05 — data da virada; CLI-05 — estados da conta; CLI-08 — motivos do bloqueio; API-13 — rotas `/internal`.
- Arquivos: `tests/unit/test_schema_files.py` (editar) · `src/schemas/post_day_closings.json` (criar) · `src/schemas/post_blocks.json` (criar)

**3.fim — Fechar a fase** (AGENTS.md, seção 7).

## Fase 4 — esqueleto

**Branch:** `fase/04-esqueleto` · **Depende de:** fase 3
**Objetivo:** os middlewares de segurança e de log, o timeout do banco e as funções de teste que montam os dados por HTTP.

**4.1 — Estado da requisição**
- Entrega: `RequestState`, `start_request_state`, `get_request_state`; o middleware `request_context` cria o estado; `qi_exception_to_response` grava `error_code`; o `internal_token` grava `auth_failure = "INTERNAL"`.
- Decisões: PRD-06 — log de toda requisição; PRD-14 — colunas do log.
- Arquivos: `src/utils/request_context.py` (editar) · `src/middlewares/request_context.py` (editar) · `src/errors/handlers.py` (editar) · `src/middlewares/internal_token.py` (editar)

**4.2 — Configuração nova**
- Entrega: as constantes novas de `src/constants.py` (registro); as variáveis no `docker-compose.yml`, com padrão, e no `.env.example`, com valor de mentirinha; `ADMIN_TOKEN` em `REQUIRED_VARIABLES`.
- Decisões: PRD-01 — segredo no ambiente; PRD-07 — dois tokens internos; PRD-08 — timeout no banco; PRD-10 — barreira; PRD-13 — token de administração; API-16 — token da conta; ARQ-04 — sobe sem `.env`.
- Arquivos: `src/constants.py` (editar) · `docker-compose.yml` (editar) · `.env.example` (editar)

**4.3 — Token de administração**
- Entrega: `register_admin_token_middleware`: caminho que começa em `/internal` sem o `ADMIN-TOKEN` certo responde 403 `QIT000003` e grava `auth_failure = "ADMIN"`.
- Decisões: PRD-07 — dois tokens internos; PRD-13 — token de administração; API-13 — rotas `/internal`.
- Arquivos: `src/middlewares/admin_token.py` (criar) · `src/middlewares/__init__.py` (editar) · `src/app.py` (editar) · `tests/integration/security/test_admin_token.py` (criar)

**4.4 — Timeout no banco**
- Entrega: toda conexão com `lock_timeout` e `statement_timeout` de `DB_LOCK_TIMEOUT_MS` e `DB_STATEMENT_TIMEOUT_MS`; `OperationalError` de timeout responde 503 `QIT000503`.
- Decisões: PRD-08 — timeout no banco; R3 — código de erro próprio.
- Arquivos: `src/database.py` (editar) · `src/errors/handlers.py` (editar)

**4.5 — Registro de toda requisição**
- Entrega: `RequestLogRepository` (`create`, `count_auth_failures`), com sessão própria; `register_request_log_writer_middleware` grava uma linha em `request_log` por requisição, fora da transação da regra, menos as de `BYPASS_ENDPOINTS`; o `account_key` sai do caminho.
- Decisões: PRD-06 — log de toda requisição; PRD-14 — colunas do log; PRD-12 — log sem CPF, CNPJ nem token; PRD-02 — health check sem banco.
- Arquivos: `src/repositories/request_log_repository.py` (criar) · `src/repositories/__init__.py` (editar) · `src/middlewares/request_log_writer.py` (criar) · `src/middlewares/__init__.py` (editar) · `src/app.py` (editar)

**4.6 — Barreira dos tokens internos**
- Entrega: `register_auth_barrier_middleware`: `AUTH_FAILURE_LIMIT` falhas de `INTERNAL` ou `ADMIN` do mesmo IP em `AUTH_FAILURE_WINDOW_MINUTES` fazem toda requisição desse IP responder 429 `QIT000429`, antes de conferir token; `test_healthcheck.py` com `DbUtils.rollback()` nos testes que erram token.
- Decisões: PRD-10 — barreira; PRD-04 — sem estado na memória.
- Arquivos: `src/middlewares/auth_barrier.py` (criar) · `src/middlewares/__init__.py` (editar) · `src/app.py` (editar) · `tests/integration/security/test_auth_barrier.py` (criar) · `tests/integration/test_healthcheck.py` (editar)

**4.7 — Funções de teste: requisições**
- Entrega: `RequestGenerator` reescrito, um método por rota do registro: `POST_customer`, `GET_customer`, `POST_account`, `GET_account`, `DELETE_account`, `POST_deposit`, `POST_withdrawal`, `POST_transfer`, `GET_transaction`, `GET_entries`, `GET_gamification`, `POST_point_application`, `POST_point_reset`, `POST_saving`, `POST_redemption`, `GET_piggy_bank_entries`, `POST_category`, `GET_categories`, `GET_category`, `DELETE_category`, `POST_block`, `POST_unblock`, `POST_day_closing`; constantes `INTERNAL_TOKEN` e `ADMIN_TOKEN`.
- Decisões: TST-01 — black box.
- Arquivos: `tests/utils/request_generator.py` (editar) · `tests/utils/__init__.py` (editar)

**4.8 — Funções de teste: corpos e objetos**
- Entrega: `PayloadGenerator` (`customer`, `deposit`, `withdrawal`, `transfer`, `saving`, `redemption`, `category`, `point_application`, `day_closing`, `block`); `ObjectGenerator` (`create_customer`, `create_account`, `create_funded_account`).
- Decisões: TST-01 — black box; R6 — sem float.
- Arquivos: `tests/utils/payload_generator.py` (editar) · `tests/utils/object_generator.py` (editar) · `tests/utils/__init__.py` (editar)

**4.fim — Fechar a fase** (AGENTS.md, seção 7).

## Fase 5 — cliente e conta

**Branch:** `fase/05-cliente-conta` · **Depende de:** fase 4
**Objetivo:** cadastrar e consultar cliente; abrir, consultar, bloquear, desbloquear e encerrar conta, com o token da conta.

**5.1 — Cliente: repository e DTO**
- Entrega: `CustomerRepository`; `CustomerDTO` (`obj_to_dict`, `only_obj_key`).
- Decisões: CLI-02 — dados do cliente; DAD-12 — UUID no repository; R5 — id nunca sai.
- Arquivos: `src/repositories/customer_repository.py` (criar) · `src/repositories/__init__.py` (editar) · `src/dtos/customer_dto.py` (criar) · `src/dtos/__init__.py` (editar)

**5.2 — Cliente: controller**
- Entrega: `CustomerController.create`: CPF válido → CPF único → e-mail único → idade, antes de gravar; `IntegrityError` vira o 409 do campo repetido.
- Decisões: CLI-02 — dados do cliente; CLI-03 — idade mínima; R3 — código de erro próprio.
- Arquivos: `src/controllers/customer_controller.py` (criar) · `src/controllers/__init__.py` (editar)

**5.3 — `POST /customers`**
- Entrega: a rota.
- Decisões: TST-03 — CPF único; API-02 — status de sucesso; API-03 — schema fechado; API-04 — `INTERNAL-TOKEN`.
- Arquivos: `src/resources/customer.py` (criar) · `src/resources/__init__.py` (editar) · `src/app.py` (editar) · `tests/integration/customers/test_create_customer.py` (criar)

**5.4 — Conta: token e repositories**
- Entrega: `generate_account_token`, `hash_account_token`, `account_token_matches`; `AccountRepository` (abre a conta, o cofrinho ligado a ela e grava só o hash do token); `CategoryRepository.create_default` e `get_default` ("economias", nascida com a conta).
- Decisões: API-16 — token da conta; COF-14 — cofrinho é conta; COF-03 — categoria padrão; CLI-04 — uma conta aberta; DAD-09 — contas do sistema; DAD-12 — UUID no repository.
- Arquivos: `src/utils/account_token.py` (criar) · `src/repositories/account_repository.py` (criar) · `src/repositories/category_repository.py` (criar) · `src/repositories/__init__.py` (editar)

**5.5 — Conta: DTO, controller e checagem de dono**
- Entrega: `AccountDTO`; `AccountController.open_account` e `get_account`; `BaseController.get_owned_account`: conta de cliente cuja chave e token batem, ou 404 `QIT001010` com `auth_failure = "ACCOUNT"`.
- Decisões: API-08 — rotas aninhadas; API-09 — dono pelo token; R8 — outro dono → 404; API-16 — token da conta; CLI-04 — uma conta aberta.
- Arquivos: `src/dtos/account_dto.py` (criar) · `src/dtos/__init__.py` (editar) · `src/controllers/account_controller.py` (criar) · `src/controllers/base_controller.py` (editar) · `src/controllers/__init__.py` (editar)

**5.6 — `POST /customers/{customer_key}/accounts`**
- Entrega: a rota; a resposta traz o token uma vez só.
- Decisões: CLI-01 — conta só com cliente; CLI-04 — uma conta aberta; TST-03 — conta só com cliente; API-16 — token da conta.
- Arquivos: `src/resources/account.py` (criar) · `src/resources/__init__.py` (editar) · `src/app.py` (editar) · `tests/integration/accounts/test_open_account.py` (criar)

**5.7 — `GET /accounts/{account_key}`**
- Entrega: a rota, com saldo e saldo total do cofrinho.
- Decisões: R8 — outro dono → 404; API-09 — dono pelo token; R5 — id nunca sai; DAD-08 — centavos.
- Arquivos: `src/resources/account.py` (editar) · `src/app.py` (editar) · `tests/integration/accounts/test_get_account.py` (criar)

**5.8 — `GET /customers/{customer_key}`**
- Entrega: `CustomerController.get_by_key` e a rota; só com o token da conta não encerrada do cliente.
- Decisões: API-17 — consultar cliente; R8 — outro dono → 404.
- Arquivos: `src/controllers/customer_controller.py` (editar) · `src/resources/customer.py` (editar) · `src/app.py` (editar) · `tests/integration/customers/test_get_customer.py` (criar)

**5.9 — Barreira do token da conta**
- Entrega: a barreira passa a contar também `ACCOUNT` por conta e IP.
- Decisões: PRD-10 — barreira.
- Arquivos: `src/middlewares/auth_barrier.py` (editar) · `tests/integration/security/test_account_auth_barrier.py` (criar)

**5.10 — Bloquear e desbloquear**
- Entrega: `AccountController.block_account` e `unblock_account`; `InternalResource`; as duas rotas `/internal/accounts/...`; evento com origem `MANUAL` e motivo no bloqueio.
- Decisões: CLI-05 — estados da conta; API-13 — rotas `/internal`; PRD-13 — token de administração; R4 — append-only.
- Arquivos: `src/controllers/account_controller.py` (editar) · `src/resources/internal.py` (criar) · `src/resources/__init__.py` (editar) · `src/app.py` (editar) · `tests/integration/internal/test_block_account.py` (criar)

**5.11 — `DELETE /accounts/{account_key}`**
- Entrega: `AccountController.close_account` (só conta ativa) e a rota; depois de encerrar, o cliente abre outra conta.
- Decisões: CLI-04 — uma conta aberta; CLI-05 — estados da conta; CLI-06 — encerrar zerada (parte do estado).
- Arquivos: `src/controllers/account_controller.py` (editar) · `src/resources/account.py` (editar) · `src/app.py` (editar) · `tests/integration/accounts/test_close_account.py` (criar)

**5.fim — Fechar a fase** (AGENTS.md, seção 7).

## Fase 6 — depósito, transferência e extrato

**Branch:** `fase/06-dinheiro` · **Depende de:** fase 5
**Objetivo:** depósito, saque e transferência com tarifa, idempotência e travas; consulta de operação e extrato paginado.

**6.1 — Repositories do dinheiro**
- Entrega: `TransactionRepository` (`create`, `get_by_request_control_key`, `get_by_key_for_account`); `EntryRepository.create` (atualiza `balance` e grava `balance_after`; nas contas do sistema, os dois ficam nulos); `DepositRepository.create`; `BankClockRepository` (`get_accounting_date`, `lock`, `advance`).
- Decisões: DAD-05 — entidades; DAD-06 — tabela de operações; DAD-07 — saldo em dois lugares; DAD-09 — contas do sistema; DAD-17 — duas datas; DIA-01 — relógio do banco; MOV-19 — idempotência na prática; DAD-11 — nada apaga movimentação.
- Arquivos: `src/repositories/transaction_repository.py` (criar) · `src/repositories/entry_repository.py` (criar) · `src/repositories/deposit_repository.py` (criar) · `src/repositories/bank_clock_repository.py` (criar) · `src/repositories/__init__.py` (editar)

**6.2 — DTOs do dinheiro e documento mascarado**
- Entrega: `TransactionDTO`; `EntryDTO` (outra ponta e as duas datas); `is_valid_cnpj`; `mask_document_number`.
- Decisões: MOV-16 — CPF ou CNPJ de quem deposita; MOV-17 — outra ponta no extrato; MOV-18 — duas datas no extrato; PRD-12 — dado sensível mascarado.
- Arquivos: `src/dtos/transaction_dto.py` (criar) · `src/dtos/entry_dto.py` (criar) · `src/dtos/__init__.py` (editar) · `src/utils/document_number.py` (editar)

**6.3 — Tarifa (unitário)**
- Entrega: `calculate_fee(amount_cents, fee_points)`: `ceil(amount_cents × (10 − fee_points) / 1000)` em inteiros.
- Decisões: MOV-06 — tarifa de 1%; MOV-10 — arredonda para cima; GAM-09 — ponto em tarifa; TST-05 — unitários.
- Arquivos: `tests/unit/test_fee.py` (criar) · `src/calculations/__init__.py` (criar) · `src/calculations/fee.py` (criar)

**6.4 — Depósito: controller**
- Entrega: `hash_request_body`; `TransactionController.deposit`: repetição pela `request_control_key` (mesmo corpo → a resposta da primeira vez; outro corpo → 409 `QIT001014`; `IntegrityError` tratado como repetição); conta de cliente ativa; documento válido; operação `DEPOSIT` com dois lançamentos (`OUTSIDE_WORLD` − e conta +) e a linha em `deposits`.
- Decisões: MOV-07 — operações; MOV-09 — depósito sem tarifa; MOV-12 — idempotência; MOV-15 — quem deposita; MOV-16 — rota e dados do depósito; MOV-19 — idempotência na prática; CLI-09 — bloqueada não mexe em dinheiro; DAD-13 — operação síncrona.
- Arquivos: `src/utils/request_hash.py` (criar) · `src/controllers/transaction_controller.py` (criar) · `src/controllers/__init__.py` (editar)

**6.5 — `POST /accounts/{account_key}/deposits`**
- Entrega: a rota; a resposta traz só a key da operação.
- Decisões: MOV-15 — quem deposita; MOV-16 — rota e dados do depósito; API-18 — valor inteiro ≥ 1.
- Arquivos: `src/resources/transaction.py` (criar) · `src/resources/__init__.py` (editar) · `src/app.py` (editar) · `tests/integration/transactions/test_deposit.py` (criar)

**6.6 — Saque**
- Entrega: `TransactionController.withdraw` e `POST /accounts/{account_key}/withdrawals`: só o dono, conta ativa, saldo suficiente, operação `WITHDRAWAL` (conta − e `OUTSIDE_WORLD` +).
- Decisões: MOV-07 — operações; MOV-08 — o que barra; MOV-15 — só o dono saca; MOV-12 — idempotência.
- Arquivos: `src/controllers/transaction_controller.py` (editar) · `src/resources/transaction.py` (editar) · `src/app.py` (editar) · `tests/integration/transactions/test_withdrawal.py` (criar)

**6.7 — Transferência: controller**
- Entrega: `TransactionController.transfer`: dono → repetição → origem ativa → origem diferente do destino → destino existe → destino ativo → trava das duas contas na ordem do `id` → saldo cobre valor + tarifa; operação `TRANSFER` com os quatro lançamentos; usa `calculate_fee(amount_cents, 0)` (os pontos entram no 8.7).
- Decisões: MOV-01 — sem saldo barra; MOV-02 — valor + tarifa; MOV-03 — toda transferência tem tarifa; MOV-05 — trava no saldo; MOV-08 — o que barra; MOV-09 — quem envia paga; MOV-10 — tarifa zero sem lançamento; MOV-11 — ordem das travas; DAD-16 — tarifa como lançamento; CLI-09 — bloqueada não mexe em dinheiro.
- Arquivos: `src/controllers/transaction_controller.py` (editar)

**6.8 — `POST /accounts/{account_key}/transfers`**
- Entrega: a rota; a resposta traz a key da operação e o saldo novo.
- Decisões: TST-03 — sem saldo e tarifa; API-10 — resposta de sucesso; MOV-12 — idempotência.
- Arquivos: `src/resources/transaction.py` (editar) · `src/app.py` (editar) · `tests/integration/transactions/test_transfer.py` (criar)

**6.9 — Limite diário e bloqueio automático**
- Entrega: `TransactionRepository.count_transfers_sent(account, accounting_date, since)`; a 11ª transferência enviada no dia contábil, contada desde o último desbloqueio, responde 422 `QIT001019` e bloqueia a conta na mesma requisição (`SUSPICIOUS_ACTIVITY`, origem `AUTOMATIC`).
- Decisões: CLI-08 — bloqueio automático; DAD-13 — a única gravação de pedido barrado.
- Arquivos: `src/controllers/transaction_controller.py` (editar) · `src/repositories/transaction_repository.py` (editar) · `tests/integration/transactions/test_daily_transfer_limit.py` (criar)

**6.10 — `GET /accounts/{account_key}/transactions/{transaction_key}`**
- Entrega: `TransactionController.get_transaction` e a rota.
- Decisões: R8 — outro dono → 404; API-10 — resposta de sucesso.
- Arquivos: `src/controllers/transaction_controller.py` (editar) · `src/resources/transaction.py` (editar) · `src/app.py` (editar) · `tests/integration/transactions/test_get_transaction.py` (criar)

**6.11 — `GET /accounts/{account_key}/entries` (extrato)**
- Entrega: `EntryRepository.list_page` (`created_at` decrescente, desempate por `id`, pede `limit + 1`); `TransactionController.list_entries` e a rota, no envelope do base.
- Decisões: MOV-04 — envelope do extrato; MOV-14 — ordem do extrato; MOV-17 — outra ponta; MOV-18 — duas datas; TST-03 — extrato paginado.
- Arquivos: `src/controllers/transaction_controller.py` (editar) · `src/repositories/entry_repository.py` (editar) · `src/resources/transaction.py` (editar) · `src/app.py` (editar) · `tests/integration/transactions/test_entries.py` (criar)

**6.12 — Encerrar só com saldo zero**
- Entrega: `close_account` recusa saldo diferente de zero com 409 `QIT001012`.
- Decisões: CLI-06 — encerrar zerada.
- Arquivos: `src/controllers/account_controller.py` (editar) · `tests/integration/accounts/test_close_account_with_balance.py` (criar)

**6.fim — Fechar a fase** (AGENTS.md, seção 7).

## Fase 8 — XP, nível e pontos

**Branch:** `fase/08-xp-pontos` · **Depende de:** fase 6
**Objetivo:** XP por transferência, níveis, pontos e a tarifa menor; a rota que mostra a gamificação.

**8.1 — XP e nível (unitário)**
- Entrega: os nomes de `xp.py` no registro. `XpGain` tem `level`, `xp`, `xp_gained` e `levels_gained`; ao cruzar um nível, o resto do valor rende com o `n` novo.
- Decisões: GAM-05 — nível não cai; GAM-15 — 10 níveis; GAM-16 — fórmulas de XP; GAM-18 — XP inteiro; GAM-24 — custo do nível; GAM-25 — XP do recorde em reais; TST-05 — unitários.
- Arquivos: `tests/unit/test_xp.py` (criar) · `src/calculations/xp.py` (criar) · `src/calculations/__init__.py` (editar)

**8.2 — Gamificação: repository e DTO**
- Entrega: `GamificationRepository`; `GamificationDTO` (XP, nível e XP que falta; pontos livres, em tarifa e em chance; tarifa e chance atuais; ranque, % do CDI, recorde e fim da carência).
- Decisões: DAD-14 — gamificação em eventos e colunas; API-14 — rota da gamificação.
- Arquivos: `src/repositories/gamification_repository.py` (criar) · `src/repositories/__init__.py` (editar) · `src/dtos/gamification_dto.py` (criar) · `src/dtos/__init__.py` (editar)

**8.3 — Gamificação: controller**
- Entrega: `GamificationController.get_gamification`, `award_transfer_xp(account, amount_cents, source, transaction, accounting_date)` e `award_record_xp(account, transaction, accounting_date)` (usado pela fase 7); cada nível novo grava `level_event` e soma 1 ponto livre.
- Decisões: GAM-02 — as peças; GAM-04 — XP de recorde; GAM-06 — pontos livres.
- Arquivos: `src/controllers/gamification_controller.py` (criar) · `src/controllers/__init__.py` (editar)

**8.4 — `GET /accounts/{account_key}/gamification`**
- Entrega: `GamificationResource` e a rota; conta aberta depois de encerrar outra começa do zero.
- Decisões: API-14 — rota da gamificação; GAM-01 — gamificação por conta.
- Arquivos: `src/resources/gamification.py` (criar) · `src/resources/__init__.py` (editar) · `src/app.py` (editar) · `tests/integration/gamification/test_get_gamification.py` (criar)

**8.5 — XP na transferência**
- Entrega: `transfer` chama `award_transfer_xp` para quem envia (`TRANSFER_SENT`) e para quem recebe (`TRANSFER_RECEIVED`), cada um com o seu `n`.
- Decisões: GAM-16 — fórmulas de XP; GAM-17 — XP dos dois lados; GAM-18 — XP inteiro; GAM-24 — custo do nível.
- Arquivos: `src/controllers/transaction_controller.py` (editar) · `tests/integration/gamification/test_transfer_xp.py` (criar)

**8.6 — Aplicar e zerar pontos**
- Entrega: `apply_points` e `reset_points`; `POST .../point_applications` e `POST .../point_resets`; cada mudança grava `points_event`.
- Decisões: GAM-06 — pontos livres; GAM-07 — redistribuir; GAM-21 — aplicar e zerar; CLI-09 — bloqueada mexe em pontos.
- Arquivos: `src/controllers/gamification_controller.py` (editar) · `src/resources/gamification.py` (editar) · `src/app.py` (editar) · `tests/integration/gamification/test_points.py` (criar)

**8.7 — Tarifa menor com pontos**
- Entrega: `transfer` passa `points_fee` da conta de origem para `calculate_fee`.
- Decisões: GAM-09 — ponto em tarifa; MOV-10 — tarifa zero sem lançamento.
- Arquivos: `src/controllers/transaction_controller.py` (editar) · `tests/integration/gamification/test_fee_with_points.py` (criar)

**8.fim — Fechar a fase** (AGENTS.md, seção 7).

## Fase 7 — cofrinho, virada do dia, ranque e carência

**Branch:** `fase/07-cofrinho` · **Depende de:** fase 8
**Objetivo:** guardar e resgatar na categoria "economias", com lotes; o connector do CDI e o Mockserver; a virada do dia com rendimento, XP de recorde, ranque e carência.

**7.1 — Ranques e lotes (unitário)**
- Entrega: os nomes de `ranks.py` e de `lots.py` no registro.
- Decisões: GAM-12 — ranque pelo cofrinho; GAM-13 — mínimos; COF-02 — % do CDI por ranque; COF-24 — resgate proporcional; TST-05 — unitários.
- Arquivos: `tests/unit/test_ranks.py` (criar) · `src/calculations/ranks.py` (criar) · `tests/unit/test_lots.py` (criar) · `src/calculations/lots.py` (criar) · `src/calculations/__init__.py` (editar)

**7.2 — Rendimento (unitário)**
- Entrega: `daily_rate` (taxa diária com 8 casas) e `lot_yield` (centavos inteiros e o resíduo com 8 casas, em `Decimal`).
- Decisões: COF-02 — % do CDI por ranque; COF-13 — rendimento por lote; COF-15 — fração de centavo; TST-05 — unitários.
- Arquivos: `tests/unit/test_piggy_yield.py` (criar) · `src/calculations/piggy_yield.py` (criar) · `src/calculations/__init__.py` (editar)

**7.3 — Lotes: repository**
- Entrega: `LotRepository` (`create`, `list_open_for_update`, do mais antigo para o mais novo); `CategoryRepository.get_balance`.
- Decisões: COF-06 — lotes; COF-23 — colunas do lote.
- Arquivos: `src/repositories/lot_repository.py` (criar) · `src/repositories/category_repository.py` (editar) · `src/repositories/__init__.py` (editar)

**7.4 — Guardar e resgatar: controller**
- Entrega: `PiggyBankController.save` (operação `SAVE`, lote novo, ranque sobe na hora, XP de recorde por `award_record_xp`) e `redeem` (operação `REDEEM`, do lote mais antigo, principal e rendimento na proporção do lote); os dois aceitam só a categoria padrão: outra `category_key` responde 404 `QIT001021` (a escolha entra no 9.6); `TransactionDTO` com bruto e líquido do resgate.
- Decisões: COF-01 — um cofrinho por conta; COF-06 — lotes; COF-07 — resgate maior que a categoria; COF-08 — bruto e líquido; COF-10 — guardar e resgatar livres; COF-11 — sem limite; COF-23 — colunas do lote; COF-24 — resgate proporcional; MOV-09 — sem tarifa; MOV-12 — idempotência; GAM-04 — XP de recorde; GAM-19 — ranque sobe na hora; CLI-09 — bloqueada não mexe em dinheiro.
- Arquivos: `src/controllers/piggy_bank_controller.py` (criar) · `src/controllers/__init__.py` (editar) · `src/dtos/transaction_dto.py` (editar)

**7.5 — `POST /accounts/{account_key}/savings`**
- Entrega: `PiggyBankResource` e a rota.
- Decisões: COF-10 — guardar livre; COF-11 — sem limite; GAM-04 — XP de recorde; GAM-19 — ranque sobe na hora.
- Arquivos: `src/resources/piggy_bank.py` (criar) · `src/resources/__init__.py` (editar) · `src/app.py` (editar) · `tests/integration/piggy_bank/test_save.py` (criar)

**7.6 — `POST /accounts/{account_key}/redemptions`**
- Entrega: a rota.
- Decisões: COF-06 — lote mais antigo primeiro; COF-07 — resgate maior que a categoria; COF-10 — resgate livre; COF-24 — resgate proporcional.
- Arquivos: `src/resources/piggy_bank.py` (editar) · `src/app.py` (editar) · `tests/integration/piggy_bank/test_redeem.py` (criar)

**7.7 — `GET /accounts/{account_key}/piggy_bank_entries`**
- Entrega: `EntryRepository.list_piggy_bank_page` (filtro opcional por categoria); `list_piggy_bank_entries` e a rota.
- Decisões: COF-05 — saldo e extrato do cofrinho; MOV-04 — envelope do extrato.
- Arquivos: `src/controllers/piggy_bank_controller.py` (editar) · `src/repositories/entry_repository.py` (editar) · `src/resources/piggy_bank.py` (editar) · `src/app.py` (editar) · `tests/integration/piggy_bank/test_piggy_bank_entries.py` (criar)

**7.8 — Connector do Banco Central**
- Entrega: `BcbConnector.get_cdi_rate(accounting_date)`: a taxa do dia em texto, `None` quando o dia não tem taxa, e `CdiUnavailable` (503) em timeout ou erro; `BCB_API_URL` e `BCB_API_TIMEOUT`; o connector de boletos sai.
- Decisões: ARQ-07 — CDI por connector; COF-17 — CDI real, série 12; COF-20 — Banco Central fora → 503; PRD-03 — timeout no connector.
- Arquivos: `src/connectors/bcb_connector.py` (criar) · `src/connectors/__init__.py` (editar) · `src/connectors/bankslip_connector.py` (apagar) · `src/constants.py` (editar)

**7.9 — Script que baixa o CDI**
- Entrega: `scripts/download_cdi.py`: baixa 10 anos da série 12 do SGS e grava `mockserver/cdi_expectations.json`; o agente escreve, não roda.
- Decisões: ARQ-12 — Banco Central só no download; COF-17 — CDI real.
- Arquivos: `scripts/download_cdi.py` (criar)

Entre o 7.9 e o 7.10, o Bruno roda o script e faz o commit do arquivo de dados (seção "(c) Feito à mão").

**7.10 — Mockserver no compose**
- Entrega: serviço `mockserver` (imagem de `mockserver/Dockerfile`, com o arquivo de dados dentro; porta `${MOCKSERVER_PORT:-1080}`); `BCB_API_URL` e `BCB_API_TIMEOUT` na API; `BANKSLIP_*` saem; `MockGenerator` (`set_cdi_rate`, `set_cdi_delay`, `clear_cdi`) para os testes programarem o Mockserver.
- Decisões: ARQ-05 — serviço novo no compose; ARQ-06 — três peças; ARQ-08 — ambiente de entrega; ARQ-04 — sobe sem `.env`.
- Arquivos: `docker-compose.yml` (editar) · `.env.example` (editar) · `mockserver/Dockerfile` (criar) · `tests/utils/mock_generator.py` (criar) · `tests/utils/__init__.py` (editar)

**7.11 — Virada do dia: data, CDI e relógio**
- Entrega: `DayClosingController.close_day` e `POST /internal/day_closings`: data igual ao relógio → pede a taxa e avança um dia; já fechada → 409; no futuro → 422; inexistente → 422; Banco Central fora → 503 e o dia não avança.
- Decisões: DIA-01 — relógio do banco; DIA-02 — virada por rota; DIA-05 — data da virada; COF-20 — Banco Central fora → 503.
- Arquivos: `src/controllers/day_closing_controller.py` (criar) · `src/controllers/__init__.py` (editar) · `src/resources/internal.py` (editar) · `src/app.py` (editar) · `tests/integration/internal/test_day_closing.py` (criar)

**7.12 — Rendimento na virada**
- Entrega: `LotRepository.list_open_by_piggy_bank_for_update`; rendimento de cada lote pelo ranque que rende no dia, um lançamento `YIELD` por categoria (banco − e cofrinho +), resíduo guardado no lote; dia sem taxa não rende; conta bloqueada rende.
- Decisões: COF-02 — % do CDI por ranque; COF-13 — rendimento por lote; COF-15 — fração de centavo; COF-16 — só dias com taxa; COF-22 — rende o dia inteiro; COF-23 — colunas do lote; DIA-03 — ordem da virada; CLI-07 — bloqueada segue na virada; GAM-19 — rende o ranque do início do dia.
- Arquivos: `src/controllers/day_closing_controller.py` (editar) · `src/repositories/lot_repository.py` (editar) · `tests/integration/internal/test_day_closing_yield.py` (criar)

**7.13 — XP do recorde na virada**
- Entrega: depois do rendimento, `award_record_xp` em cada cofrinho que passou do recorde.
- Decisões: GAM-04 — XP de recorde; GAM-19 — XP de recorde na virada; GAM-25 — XP do recorde em reais; CLI-07 — bloqueada segue na virada.
- Arquivos: `src/controllers/day_closing_controller.py` (editar) · `tests/integration/internal/test_day_closing_record_xp.py` (criar)

**7.14 — Ranque e carência na virada**
- Entrega: sobe, abre carência (`grace_until` = data + 30 dias), encerra carência, cai; grava `rank_event` (`UP`, `GRACE_START`, `GRACE_END`, `DOWN`) e o `yield_rank_id` de amanhã.
- Decisões: GAM-12 — ranque pelo cofrinho; GAM-14 — carência; GAM-19 — queda só na virada; COF-02 — % do CDI por ranque; CLI-07 — bloqueada segue na virada.
- Arquivos: `src/controllers/day_closing_controller.py` (editar) · `tests/integration/internal/test_day_closing_rank.py` (criar)

**7.15 — Encerrar só com cofrinho zerado**
- Entrega: `close_account` recusa cofrinho diferente de zero com 409 `QIT001012`.
- Decisões: CLI-06 — encerrar zerada.
- Arquivos: `src/controllers/account_controller.py` (editar) · `tests/integration/accounts/test_close_account_with_piggy.py` (criar)

**7.fim — Fechar a fase** (AGENTS.md, seção 7).

## Fase 9 — categorias, IR/IOF e chance de não debitar

**Branch:** `fase/09-categorias-impostos-sorteio` · **Depende de:** fase 7
**Objetivo:** impostos no resgate, categorias criadas pelo dono e o sorteio que devolve a transferência.

**9.1 — Impostos (unitário)**
- Entrega: `ir_percent`, `iof_percent` (tabela regressiva real, até 29 dias) e `redemption_taxes` (IOF e IR do resgate, arredondados uma vez, para cima).
- Decisões: COF-12 — IR e IOF reais; TST-05 — unitários.
- Arquivos: `tests/unit/test_taxes.py` (criar) · `src/calculations/taxes.py` (criar) · `src/calculations/__init__.py` (editar)

**9.2 — IR e IOF no resgate**
- Entrega: `redeem` desconta os impostos sobre a parte de rendimento, em lançamentos `IOF` e `IR` a crédito da conta do banco.
- Decisões: COF-08 — bruto e líquido; COF-12 — IR e IOF reais; COF-24 — imposto só sobre o rendimento; COF-25 — imposto para o banco.
- Arquivos: `src/controllers/piggy_bank_controller.py` (editar) · `tests/integration/piggy_bank/test_redeem_taxes.py` (criar)

**9.3 — Categorias: repository, DTO e controller**
- Entrega: `CategoryRepository` (`create`, `get_by_key`, `list_active_page`, `delete`, que muda o estado e grava o evento); `CategoryDTO`; `CategoryController`.
- Decisões: COF-03 — categorias; COF-04 — excluir categoria; COF-18 — nome único; API-15 — excluir categoria; R4 — append-only.
- Arquivos: `src/repositories/category_repository.py` (editar) · `src/dtos/category_dto.py` (criar) · `src/dtos/__init__.py` (editar) · `src/controllers/category_controller.py` (criar) · `src/controllers/__init__.py` (editar)

**9.4 — Criar e listar categorias**
- Entrega: `CategoryResource`; `POST` e `GET .../categories` (só as ativas, com saldo).
- Decisões: COF-03 — categorias; COF-05 — saldo por categoria; COF-18 — nome único; CLI-09 — bloqueada mexe em categoria.
- Arquivos: `src/resources/category.py` (criar) · `src/resources/__init__.py` (editar) · `src/app.py` (editar) · `tests/integration/categories/test_create_and_list_categories.py` (criar)

**9.5 — Consultar e excluir categoria**
- Entrega: `GET` e `DELETE .../categories/{category_key}`; excluída aparece com `status: deleted`.
- Decisões: COF-04 — excluir categoria; API-15 — excluir categoria.
- Arquivos: `src/resources/category.py` (editar) · `src/app.py` (editar) · `tests/integration/categories/test_get_and_delete_category.py` (criar)

**9.6 — Guardar e resgatar por categoria**
- Entrega: `save` e `redeem` usam a `category_key` do corpo (sem ela, "economias"); categoria excluída → 409 `QIT001022`; resgate maior que a categoria → 422 `QIT001023`.
- Decisões: COF-03 — categorias; COF-06 — lotes por categoria; COF-07 — resgate maior que a categoria; COF-19 — sem mover entre categorias; API-15 — guardar em excluída.
- Arquivos: `src/controllers/piggy_bank_controller.py` (editar) · `tests/integration/piggy_bank/test_category_money.py` (criar)

**9.7 — Sorteio (unitário)**
- Entrega: `PRIZE_LIMIT_CENTS = 10000`, `is_eligible_for_prize`, `draw_prize(chance_points, rng)` (`rng.randrange(1000) < chance_points`).
- Decisões: GAM-10 — chance de não debitar; GAM-11 — ponto vale igual; GAM-22 — sorteio até R$ 100; TST-06 — sorteio injetável.
- Arquivos: `tests/unit/test_lottery.py` (criar) · `src/calculations/lottery.py` (criar) · `src/calculations/__init__.py` (editar)

**9.8 — Chance de não debitar**
- Entrega: depois de conferir o saldo, `transfer` sorteia; quando sai, a conta do banco devolve valor + tarifa num lançamento `PRIZE`, sem XP.
- Decisões: GAM-10 — chance de não debitar; GAM-22 — sorteio até R$ 100; GAM-23 — prêmio sem XP; TST-06 — sorteio injetável.
- Arquivos: `src/controllers/transaction_controller.py` (editar) · `tests/integration/gamification/test_chance.py` (criar)

**9.fim — Fechar a fase** (AGENTS.md, seção 7).

## Fase 11 — provas extras

**Branch:** `fase/11-provas-extras` · **Depende de:** fase 9
**Objetivo:** provar concorrência, idempotência, reconciliação e ausência de erro 500. Todos os passos são de prova.

**11.1 — Duas transferências ao mesmo tempo**
- Entrega: o saldo cobre só uma; passa exatamente uma; saldo nunca negativo.
- Decisões: TST-08 — provas extras; MOV-01 — sem saldo barra; MOV-05 — trava no saldo.
- Arquivos: `tests/integration/extras/test_concurrent_transfers.py` (criar)

**11.2 — Mesma chave de idempotência ao mesmo tempo**
- Entrega: uma operação só; as duas respostas iguais.
- Decisões: TST-08 — provas extras; MOV-12 — idempotência; MOV-19 — idempotência na prática.
- Arquivos: `tests/integration/extras/test_idempotency_race.py` (criar)

**11.3 — A paga B e B paga A ao mesmo tempo**
- Entrega: sem deadlock e sem 500.
- Decisões: TST-08 — provas extras; MOV-11 — ordem das travas.
- Arquivos: `tests/integration/extras/test_crossed_transfers.py` (criar)

**11.4 — Reconciliação**
- Entrega: em cada conta criada no teste, a soma do extrato é o saldo.
- Decisões: TST-08 — provas extras; DAD-07 — saldo em dois lugares.
- Arquivos: `tests/integration/extras/test_reconciliation.py` (criar)

**11.5 — Nenhum erro 500 na suíte**
- Entrega: uma fixture automática em `tests/conftest.py` reprova o teste que receber 500, ou 503 com código diferente de `QIT001031` e `QIT000503`; `ClientRequisition` guarda os status de cada teste.
- Decisões: TST-08 — provas extras; R3 — nunca 500 por regra.
- Arquivos: `tests/conftest.py` (editar) · `tests/utils/requisition.py` (editar)

**11.fim — Fechar a fase** (AGENTS.md, seção 7).

## (a) Cobertura das decisões

Formato: número da decisão → passo. "todas" = vale em todo passo, pelo `AGENTS.md`; "base" = o base já faz e nenhum passo desfaz.

- **R:** 1→todas (integração só por HTTP; 4.7) · 2→7.10 · 3→3.2, 4.4, 5.2, 11.5 · 4→2.7, 5.10, 9.3 · 5→2.7, 5.1, 5.5 · 6→2.7, 3.3–3.6, 6.3 · 8→5.5, 5.7
- **ESC:** 01→5.3, 5.6, 6.5, 6.8, 6.11 · 05→fases 8, 7 e 9
- **ARQ:** 01→base · 02→todas · 03→2.7 · 04→4.2, 7.10 · 05→7.10 · 06→7.10 · 07→7.8, 7.10 · 08→7.10 · 09→base · 11→2.2–2.6 · 12→7.9
- **DAD:** 01→2.7 · 04→2.7–2.13 · 05→2.7–2.13 · 06→2.7, 6.1 · 07→2.7, 6.1, 11.4 · 08→2.7, 3.3–3.6 · 09→2.7, 5.4 · 10→2.7 · 11→6.1 · 12→5.1, 5.4 · 13→6.4, 6.9 · 14→2.7, 8.2 · 15→2.7 · 16→6.7 · 17→2.7, 6.1, 6.11
- **CLI:** 01→5.6 · 02→5.2, 5.3 · 03→5.2 · 04→2.7, 5.5, 5.6, 5.11 · 05→5.10, 5.11 · 06→5.11, 6.12, 7.15 · 07→7.12–7.14 · 08→6.9 · 09→6.4, 6.6, 6.7, 7.4, 8.6, 9.4
- **MOV:** 01→6.7, 11.1 · 02→6.7 · 03→6.7 · 04→3.4, 6.11, 7.7 · 05→6.7, 11.1 · 06→6.3 · 07→6.4, 6.6 · 08→6.6, 6.7 · 09→6.4, 6.7, 7.4 · 10→6.3, 8.7 · 11→6.7, 11.3 · 12→2.7, 6.4, 6.6, 6.8, 7.4, 11.2 · 14→6.11 · 15→6.4, 6.6 · 16→2.7, 3.3, 6.4, 6.5 · 17→6.2, 6.11 · 18→6.2, 6.11 · 19→6.1, 6.4, 11.2
- **COF:** 01→5.4, 7.4 · 02→7.1, 7.2, 7.12, 7.14 · 03→5.4, 9.3, 9.6 · 04→9.3, 9.5 · 05→7.7, 9.4 · 06→7.3, 7.4, 9.6 · 07→7.4, 9.6 · 08→7.4, 9.2 · 10→7.4–7.6 · 11→7.4, 7.5 · 12→9.1, 9.2 · 13→7.2, 7.12 · 14→2.7, 5.4 · 15→2.7, 7.2, 7.12 · 16→7.12 · 17→7.8, 7.9 · 18→2.7, 9.3, 9.4 · 19→9.6 · 20→7.8, 7.11 · 21→2.7 · 22→7.12 · 23→2.7, 7.3, 7.12 · 24→7.1, 7.4, 9.2 · 25→2.7, 9.2
- **GAM:** 01→8.4 · 02→8.3 · 04→8.3, 7.4, 7.13 · 05→8.1 · 06→8.3, 8.6 · 07→8.6 · 09→6.3, 8.7 · 10→9.7, 9.8 · 11→9.7 · 12→7.1, 7.14 · 13→7.1 · 14→7.14 · 15→8.1 · 16→8.1, 8.5 · 17→8.5 · 18→8.1, 8.5 · 19→7.4, 7.12–7.14 · 21→8.6 · 22→9.7, 9.8 · 23→9.8 · 24→8.1, 8.5 · 25→8.1, 7.13
- **DIA:** 01→2.7, 6.1, 7.11 · 02→7.11 · 03→7.11–7.14 · 04→2.7 · 05→3.6, 7.11
- **API:** 01→3.2 · 02→3.1 e cada passo de rota · 03→3.3–3.6 · 04→base, 4.6 · 05→3.1 · 06→3.1 · 07→3.1 · 08→3.1, 5.5 · 09→5.5, 5.7 · 10→3.1, 6.8, 6.10 · 11→3.2 · 12→3.2 · 13→3.1, 4.3, 5.10 · 14→8.2, 8.4 · 15→2.7, 9.3, 9.5 · 16→4.2, 5.4–5.6 · 17→5.8 · 18→3.3–3.5, 6.5
- **PRD:** 01→4.2 · 02→base, 4.5 · 03→7.8 · 04→4.6 · 06→2.7, 4.1, 4.5 · 07→4.2, 4.3 · 08→4.2, 4.4 · 10→4.6, 5.9 · 12→4.5, 6.2 · 13→4.3 · 14→2.7, 4.1, 4.5
- **TST:** 01→todas · 02→todas · 03→5.3, 5.6, 6.8, 6.11 · 05→2.1, 6.3, 8.1, 7.1, 7.2, 9.1, 9.7 · 06→9.7, 9.8 · 07→todas · 08→11.1–11.5

**Não viram código:** R7 · ESC-02, ESC-03, ESC-04, ESC-06, ESC-08 · TIM-01 a TIM-08 (TIM-03, TIM-04 e TIM-08 regem o `AGENTS.md`; TIM-07 é a fase 0) · ARQ-10 · MOV-13 · PRD-05, PRD-09, PRD-11 · RFC-01 a RFC-07 · as partes "se sobrar tempo": o gatilho da DAD-11 e o nginx da ARQ-06 e da PRD-10. A decidir, sem efeito no código: ESC-07, RFC-06.

## (b) Requisitos do desafio → passo

| Requisito (02 - O desafio) | Passo |
|---|---|
| Cadastro de cliente com dados válidos; recusa CPF inválido, CPF repetido e menor de idade | 5.2, 5.3 |
| Conta vinculada a um cliente que existe | 5.5, 5.6 |
| Depósito | 6.4, 6.5 |
| Transferência que nunca deixa o saldo negativo | 6.7, 6.8 |
| …nem com pedidos simultâneos | 6.7, 11.1, 11.3 |
| …nem com pedidos repetidos | 6.4, 6.8, 11.2 |
| Tarifa cobrada na transferência, registrada e incluída na conferência de saldo | 6.3, 6.7, 6.8, 6.11 |
| Extrato paginado, com ordem definida e `is_last_page` | 6.11 |
| Testes mínimos da Aula 3: CPF único · conta só com cliente · sem saldo · tarifa · extrato paginado | 5.3 · 5.6 · 6.8 · 6.8 · 6.11 |
| Funcionalidade extra: a gamificação 2.1 | fases 8, 7 e 9 |
| `docker compose up` sobe tudo, sem arquivo extra | 4.2, 7.10; conferência na etapa 12 |
| `pytest` roda contra a API do compose | todas as fases; conferência na etapa 12 |
| Repositório público, sem segredo, com README que explica como rodar | (c), itens 7 e 9 |
| PDF com lógica de RFC | (c), item 8 |

## (c) Feito à mão

1. **Agora — fase 0.** Os comandos estão na seção "Fase 0".
2. **Antes de cada fase — o plano da fase na `main`.** Só depois do merge da fase anterior. Salve o `PLANO-fase-NN.md` em `docs\plano\` e rode:

   ```powershell
   git switch main
   git pull --ff-only origin main
   git add -- docs/plano/PLANO-fase-NN.md
   git commit -m "docs(plano): fase NN"
   git push origin main
   ```

   Depois, peça ao agente: `Execute os passos N.1 a N.fim de docs/plano/PLANO-fase-NN.md`.
3. **Enquanto o agente roda.** Docker Desktop ligado. Quando ele parar, traga o relatório (PASSO / O QUE FIZ / ONDE PAREI / ERRO / ARQUIVOS ALTERADOS) para o chat; a correção vira um passo novo no plano.
4. **Na fase 7, entre o 7.9 e o 7.10 — os dados do CDI.** Na pasta do repositório, na branch `fase/07-cofrinho`:

   ```powershell
   ./.venv/Scripts/python.exe scripts/download_cdi.py
   git status --short
   git add -- mockserver/cdi_expectations.json
   git commit -m "chore(cdi): dados do CDI para o mockserver"
   git push origin fase/07-cofrinho
   ```

   O `git status --short` mostra só `?? mockserver/cdi_expectations.json`. Antes do commit, abra o arquivo e confira três datas contra o site do Banco Central (ARQ-12).
5. **Quando o `04 - Decisões.md` mudar.** Entre duas fases, copie de novo para `docs/decisoes.md` e faça o commit na `main` com a mensagem `docs(decisoes): espelho do 04` (TIM-07).
6. **Se usar o Claude Code.** Passo 0.5, antes da primeira sessão.
7. **Depois da fase 11 — README.** O `README.md` e o `docs/como-o-projeto-e-organizado.md` do base falam do `sample_entity`. Reescrever o README (como subir, como rodar os testes, as rotas) com o Claude Cowork e decidir o destino do outro arquivo; commit na `main`.
8. **Etapa 10 (09–10/10) — RFC.** Com o Claude Cowork, a partir do `docs/rotas.md` e do diagrama do 10; PDF de 2 a 4 páginas.
9. **Etapa 12 (11/10) — teste de fogo e publicação.** Checklist da máquina limpa no GitHub Codespaces (ARQ-10); repositório público até a noite (RFC-07).
10. **Etapa 13 (12/10, até 10h) — entrega.** PDF e link; guardar o comprovante.
