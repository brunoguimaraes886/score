> **Git local — Bruno, 08/10/2026:** durante a produção, branches, commits, merges e tags ficam locais. Não executar push, pull ou fetch nem exigir acesso ao GitHub. O envio completo será feito pelo Bruno somente no final, quando tudo estiver pronto. As verificações de commits e dependências são locais.

# PLANO — Fase 03 — contrato

**Branch:** `fase/03-contrato` · **Depende de:** fase 2
**Objetivo:** a tabela de rotas (`docs/rotas.md`), o catálogo de erros inteiro (`src/errors/`) e os 13 schemas de entrada (`src/schemas/`).

Regras de execução: `AGENTS.md`. Nomes obrigatórios: `docs/plano/PLANO-00-indice.md`. Um passo por vez, na ordem: 3.1 a 3.6 e, por último, 3.fim.

Esta fase não cria rota, controller nem tabela. O que ela escreve é o contrato que as fases 4 a 11 seguem: os nomes de campo, os corpos de resposta e os códigos de erro saem daqui.

Contagem de testes da suíte: `6 passed` nos passos 3.1 e 3.2 (nenhum teste novo); os passos 3.3 a 3.6 trazem a contagem deles.

Comandos usados nesta fase que não estão na seção 3 do `AGENTS.md` (são os da fase 02):

| Quero | Comando |
|---|---|
| Rodar uma linha de Python no `.venv` | `./.venv/Scripts/python.exe -c "<código>"` |
| Rodar uma linha de Python dentro do container da API (o `src/` montado, com as dependências da API) | `docker compose exec -T api python -c "<código>"` |
| Procurar texto nos arquivos do Git | `git grep <opções> -- <pasta>` |

O `git grep` termina com código de saída 1 quando não acha nada. Nos itens em que o esperado é "nenhuma linha", esse código 1 sem nenhuma linha impressa é o resultado certo, não erro.

---

### Passo 3.1 — Tabela de rotas
**Branch:** fase/03-contrato · **Depende de:** fase 2 (merge `feat(banco): fase 02 com as 22 tabelas e os 22 models` e commit `docs(plano): roteiros auditados`, os dois na `main`; tag `fase-02`)
**Objetivo:** `docs/rotas.md` com a convenção de nomes, os formatos, a autenticação, os erros comuns, a idempotência, o resumo das 25 rotas e o detalhe de cada uma.
**Decisões:** API-05 — tabela de rotas · API-06 — convenção REST · API-07 — inglês e plural · API-08 — rotas aninhadas · API-02 — status de sucesso · API-10 — resposta de sucesso · API-13 — rotas `/internal` · API-09 — dono pelo token · API-16 — token da conta · API-17 — consultar cliente · API-14 — rota da gamificação · API-15 — excluir categoria · MOV-04 — envelope do extrato · MOV-12 — idempotência · MOV-14 — ordem do extrato · MOV-17 — outra ponta · MOV-18 — duas datas · COF-08 — bruto e líquido · PRD-12 — documento mascarado · R5 — id nunca sai · R6 — sem float · R8 — outro dono → 404
**Arquivos:**
- `docs/rotas.md` (criar): o conteúdo inteiro é o bloco abaixo, da linha `# Tabela de rotas` até a linha que começa com `Idempotente: não. Fechar a mesma data`. A linha que abre o bloco (quatro crases e a palavra `markdown`) e a que o fecha (quatro crases) não entram no arquivo.

````markdown
# Tabela de rotas

O contrato da API: cada rota, quem pode chamar, o que entra, o que sai e os erros. Os formatos de entrada estão nos schemas de `src/schemas/`; os erros, em `src/errors/`. Os códigos entre parênteses (`MOV-12`) são as decisões de `docs/decisoes.md`.

## Convenção de nomes (API-06, API-07, API-08)

- Rotas, campos e valores em inglês; recurso sempre no plural (`/customers`, `/accounts`); nomes em `snake_case`.
- Tudo o que é da conta fica aninhado sob `/accounts/{account_key}`: a checagem de dono é uma regra só, "a conta da URL é a conta do token".
- Ação que não vira recurso usa o substantivo da ação, no plural, como recurso criado por `POST`: `deposits`, `withdrawals`, `transfers`, `savings`, `redemptions`, `point_applications`, `point_resets`, `blocks`, `unblocks`, `day_closings`. Cada `POST` desses registra um fato novo.
- Encerrar conta e excluir categoria são `DELETE` no próprio recurso: só mudam o estado e gravam o evento; nada é apagado (R4, API-15).
- Rotas da operação do banco ficam sob `/internal` (API-13).

## Formatos

- Key: UUID v4 em texto (`"6f1c2a9e-8b3d-4c7a-9e21-5d4b3a2f1e0c"`). Key mal formada no caminho responde o mesmo 404 da key que não existe. O `id` interno nunca sai (R5).
- Dinheiro: centavos, número inteiro (`5050` = R$ 50,50). Entrada de dinheiro: inteiro a partir de 1 (API-18). Nunca número com ponto (R6, DAD-08).
- Data: `"YYYY-MM-DD"` (`"2026-06-01"`). Data e hora: ISO 8601 sem fuso, como gravada no banco (`"2026-10-07T14:03:12.123456"`).
- `accounting_date`: o dia do relógio do banco (DIA-01); `created_at`: a data e hora reais (DAD-17).
- Valores fixos: em maiúsculas, como no banco (`"ACTIVE"`, `"DELETED"`, `"TRANSFER"`, `"FEE"`).
- Percentual: texto com ponto decimal, nunca número (`"0.9"` = 0,9%; `"102.5"` = 102,5% do CDI).
- Documento de outra pessoa sai mascarado (PRD-12): CPF `"***.456.789-**"`; CNPJ `"**.222.333/****-**"`. O dono vê o próprio CPF inteiro (API-17).
- Token da conta: 43 caracteres de letras, números, `-` e `_` (`secrets.token_urlsafe(32)`). Sai uma vez só, na resposta da abertura da conta (API-16).

## Cabeçalhos e autenticação (API-04, API-09, API-16, PRD-07, PRD-13)

| Na coluna Tokens | Cabeçalhos que a rota pede |
|---|---|
| nenhum | nenhum |
| interno | `INTERNAL-TOKEN` |
| conta | `INTERNAL-TOKEN` e `ACCOUNT-TOKEN` (o token da conta da URL) |
| admin | `INTERNAL-TOKEN` e `ADMIN-TOKEN` |

`ACCOUNT-TOKEN` que falta ou que é de outra conta responde 404, nunca 403 (R8).

## Erro

Todo erro tem o mesmo corpo (API-01), com o `translation` em português:

```json
{
  "title": "Account not Found",
  "description": "Account with key b2e7f4a1-3c9d-4e8b-a6f2-1d0c9b8a7e65 was not found.",
  "translation": "A conta com chave b2e7f4a1-3c9d-4e8b-a6f2-1d0c9b8a7e65 não foi encontrada.",
  "code": "QIT001010"
}
```

Erros que valem para todas as rotas (cada rota, mais abaixo, lista só os seus):

| Código | Status | Quando |
|---|---|---|
| `QIT000001` | 400 | corpo/query fora do schema ou não previstos, incluindo {} em rota sem corpo (API-19; guarda em 9.11) |
| `QIT000002` | 403 | falta o `INTERNAL-TOKEN` ou ele está errado (toda rota menos `/` e `/health_check`) |
| `QIT000003` | 403 | rota `/internal` sem o `ADMIN-TOKEN` certo |
| `QIT000404` | 404 | caminho que não existe |
| `QIT000405` | 405 | método que o caminho não aceita |
| `QIT000429` | 429 | barreira contra chute de token (PRD-10): erros de token demais do mesmo IP, ou da mesma conta e IP, na janela; responde antes de conferir o token (toda rota menos `/` e `/health_check`) |
| `QIT001032` | 422 | acumulador ultrapassaria BIGINT; operação/virada integralmente desfeita (DAD-19; guarda em 9.10) |
| `QIT000503` | 503 | o banco passou do `lock_timeout` ou do `statement_timeout` (PRD-08); nada é gravado |

`QIT000500` (500) não é resposta de regra: é bug (R3).

## Idempotência (MOV-12, MOV-19)

Depósito, saque, transferência, guardar e resgatar levam `request_control_key` (UUID) no corpo.

- Mesma chave e mesmo pedido (a mesma `account_key` da URL e o mesmo corpo): a API não cria outra operação e responde o status e o corpo da primeira vez.
- Mesma chave e outro pedido: 409 `QIT001014`.
- Pedido barrado não guarda a chave: a mesma chave pode ser usada de novo.

## Resumo

| Método e caminho | Tokens | Schema | Sucesso | Erros da rota | Idempotente |
|---|---|---|---|---|---|
| GET / | nenhum | — | 200 | — | sim: só lê |
| GET /health_check | nenhum | — | 204 | — | sim: só lê |
| POST /customers | interno | `post_customers.json` | 201 | 422 `QIT001003` · 409 `QIT001004` · 409 `QIT001005` · 422 `QIT001006` · 422 `QIT001007` | não: repetir dá 409 `QIT001004` |
| GET /customers/{customer_key} | conta | — | 200 | 404 `QIT001008` | sim: só lê |
| POST /customers/{customer_key}/accounts | interno | — | 201 | 404 `QIT001008` · 409 `QIT001009` | não: repetir dá 409 `QIT001009` |
| GET /accounts/{account_key} | conta | — | 200 | 404 `QIT001010` | sim: só lê |
| DELETE /accounts/{account_key} | conta | — | 204 | 404 `QIT001010` · 409 `QIT001011` · 409 `QIT001012` | não: repetir dá 409 `QIT001011` |
| POST /accounts/{account_key}/deposits | interno | `post_deposits.json` | 201 | 404 `QIT001010` · 409 `QIT001011` · 422 `QIT001003` · 409 `QIT001014` | sim: `request_control_key` |
| POST /accounts/{account_key}/withdrawals | conta | `post_withdrawals.json` | 201 | 404 `QIT001010` · 409 `QIT001011` · 422 `QIT001015` · 409 `QIT001014` | sim: `request_control_key` |
| POST /accounts/{account_key}/transfers | conta | `post_transfers.json` | 201 | 404 `QIT001010` · 409 `QIT001011` · 422 `QIT001016` · 404 `QIT001017` · 409 `QIT001018` · 422 `QIT001015` · 422 `QIT001019` · 409 `QIT001014` | sim: `request_control_key` |
| GET /accounts/{account_key}/transactions/{transaction_key} | conta | — | 200 | 404 `QIT001010` · 404 `QIT001020` | sim: só lê |
| GET /accounts/{account_key}/entries | conta | `get_entries.json` | 200 | 404 `QIT001010` | sim: só lê |
| GET /accounts/{account_key}/gamification | conta | — | 200 | 404 `QIT001010` | sim: só lê |
| POST /accounts/{account_key}/point_applications | conta | `post_point_applications.json` | 200 | 404 `QIT001010` · 409 `QIT001011` · 422 `QIT001027` | não: cada pedido soma os pontos de novo |
| POST /accounts/{account_key}/point_resets | conta | — | 200 | 404 `QIT001010` · 409 `QIT001011` | sim: zerar de novo deixa tudo igual |
| POST /accounts/{account_key}/savings | conta | `post_savings.json` | 201 | 404 `QIT001010` · 409 `QIT001011` · 404 `QIT001021` · 409 `QIT001022` · 422 `QIT001015` · 409 `QIT001014` | sim: `request_control_key` |
| POST /accounts/{account_key}/redemptions | conta | `post_redemptions.json` | 201 | 404 `QIT001010` · 409 `QIT001011` · 404 `QIT001021` · 409 `QIT001022` · 422 `QIT001023` · 409 `QIT001014` | sim: `request_control_key` |
| GET /accounts/{account_key}/piggy_bank_entries | conta | `get_piggy_bank_entries.json` | 200 | 404 `QIT001010` · 404 `QIT001021` | sim: só lê |
| POST /accounts/{account_key}/categories | conta | `post_categories.json` | 201 | 404 `QIT001010` · 409 `QIT001011` · 409 `QIT001024` | não: repetir o nome dá 409 `QIT001024` |
| GET /accounts/{account_key}/categories | conta | `get_categories.json` | 200 | 404 `QIT001010` | sim: só lê |
| GET /accounts/{account_key}/categories/{category_key} | conta | — | 200 | 404 `QIT001010` · 404 `QIT001021` | sim: só lê |
| DELETE /accounts/{account_key}/categories/{category_key} | conta | — | 204 | 404 `QIT001010` · 409 `QIT001011` · 404 `QIT001021` · 409 `QIT001022` · 409 `QIT001025` · 409 `QIT001026` | não: repetir dá 409 `QIT001022` |
| POST /internal/accounts/{account_key}/blocks | admin | `post_blocks.json` | 204 | 404 `QIT001010` · 409 `QIT001011` | não: repetir dá 409 `QIT001011` |
| POST /internal/accounts/{account_key}/unblocks | admin | — | 204 | 404 `QIT001010` · 409 `QIT001013` | não: repetir dá 409 `QIT001013` |
| POST /internal/day_closings | admin | `post_day_closings.json` | 200 | 422 `QIT001030` · 409 `QIT001028` · 422 `QIT001029` · 503 `QIT001031` | não: a mesma data de novo dá 409 `QIT001028` e não paga duas vezes (DIA-02) |

"Não" quer dizer: a segunda chamada igual não repete o efeito, e responde um erro que diz por quê.

## Cliente e conta

### GET /

Tokens: nenhum. A rota do base: quem é o serviço. O `id` aqui é o número do processo da API no sistema operacional, não um `id` do banco.

Sucesso: 200

```json
{
  "service": "bootcamp-api",
  "id": "1"
}
```

### GET /health_check

Tokens: nenhum. Não toca no banco (PRD-02).

Sucesso: 204, sem corpo.

### POST /customers

Tokens: interno. Schema: `post_customers.json`. Cadastra o cliente (CLI-02, CLI-03).

Corpo:

```json
{
  "name": "Ana Lima",
  "document_number": "123.456.789-09",
  "email": "ana.lima@example.com",
  "birthdate": "1995-04-12"
}
```

Sucesso: 201

```json
{
  "customer_key": "6f1c2a9e-8b3d-4c7a-9e21-5d4b3a2f1e0c"
}
```

| Código | Status | Quando |
|---|---|---|
| `QIT001003` | 422 | CPF com dígito verificador errado |
| `QIT001004` | 409 | CPF já cadastrado |
| `QIT001005` | 409 | e-mail já cadastrado |
| `QIT001006` | 422 | menos de 18 anos |
| `QIT001007` | 422 | data de nascimento que não existe no calendário |

Idempotente: não. Repetir o mesmo cadastro responde 409 `QIT001004`; o CPF é único.

### GET /customers/{customer_key}

Tokens: conta (o token da conta não encerrada do cliente). O CPF sai inteiro: é o dono vendo o próprio dado (API-17).

Sucesso: 200

```json
{
  "customer_key": "6f1c2a9e-8b3d-4c7a-9e21-5d4b3a2f1e0c",
  "name": "Ana Lima",
  "document_number": "123.456.789-09",
  "email": "ana.lima@example.com",
  "birthdate": "1995-04-12"
}
```

| Código | Status | Quando |
|---|---|---|
| `QIT001008` | 404 | cliente não existe; ou o `ACCOUNT-TOKEN` falta ou não é o da conta não encerrada dele |

Idempotente: sim, só lê.

### POST /customers/{customer_key}/accounts

Tokens: interno. Sem corpo. Abre a conta, o cofrinho dela e a categoria "economias" (CLI-04, COF-14). O token sai só nesta resposta (API-16).

Sucesso: 201

```json
{
  "account_key": "b2e7f4a1-3c9d-4e8b-a6f2-1d0c9b8a7e65",
  "account_token": "kX9vQ2mN7pL4rT8wZ1yB6cF3hJ5dS0aE2gU7iO9nM4q"
}
```

| Código | Status | Quando |
|---|---|---|
| `QIT001008` | 404 | cliente não existe; nenhuma conta é criada (CLI-01) |
| `QIT001009` | 409 | o cliente já tem conta não encerrada |

Idempotente: não. A segunda abertura responde 409 `QIT001009`.

### GET /accounts/{account_key}

Tokens: conta. Lê também conta bloqueada ou encerrada (CLI-05).

Sucesso: 200

```json
{
  "account_key": "b2e7f4a1-3c9d-4e8b-a6f2-1d0c9b8a7e65",
  "customer_key": "6f1c2a9e-8b3d-4c7a-9e21-5d4b3a2f1e0c",
  "status": "ACTIVE",
  "balance": 39900,
  "piggy_bank_balance": 10000,
  "piggy_bank_gross_yield": 0,
  "piggy_bank_net_yield": 0,
  "yield_accounting_date": "2026-10-07",
  "created_at": "2026-10-07T14:03:12.123456"
}
```

Campos de rendimento implementados em 9.9 (COF-28): centavos inteiros disponíveis, sem principal/resíduo; líquido simula resgate total na data contábil indicada. A conta soma a estimativa separada de cada categoria com COF-27.

`status`: `ACTIVE`, `BLOCKED` ou `CLOSED`. `piggy_bank_balance`: o saldo total do cofrinho.

| Código | Status | Quando |
|---|---|---|
| `QIT001010` | 404 | conta não existe ou não é de cliente; ou o `ACCOUNT-TOKEN` falta ou não é dela |

Idempotente: sim, só lê.

### DELETE /accounts/{account_key}

Tokens: conta. Encerra a conta: muda o estado para `CLOSED` e grava o evento (CLI-05, CLI-06).

Sucesso: 204, sem corpo.

| Código | Status | Quando |
|---|---|---|
| `QIT001010` | 404 | conta não existe ou não é de cliente; ou o `ACCOUNT-TOKEN` falta ou não é dela |
| `QIT001011` | 409 | a conta está bloqueada ou já encerrada |
| `QIT001012` | 409 | saldo ou cofrinho diferente de zero |

Idempotente: não. Encerrar de novo responde 409 `QIT001011`.

## Dinheiro

### POST /accounts/{account_key}/deposits

Tokens: interno. Schema: `post_deposits.json`. Qualquer um com o `INTERNAL-TOKEN` deposita em qualquer conta (MOV-15, MOV-16). O dinheiro sai da conta "mundo de fora". Sem tarifa e sem XP. A resposta não traz saldo.

Corpo (`depositor_document`: CPF `000.000.000-00` ou CNPJ `00.000.000/0000-00`):

```json
{
  "depositor_name": "Carlos Souza",
  "depositor_document": "11.222.333/0001-81",
  "amount": 50000,
  "request_control_key": "1b2c3d4e-5f6a-4b7c-8d9e-0f1a2b3c4d5e"
}
```

Sucesso: 201

```json
{
  "transaction_key": "d4a9b6c3-5e1f-4a0d-8b4c-3f2e1d0c9a87"
}
```

| Código | Status | Quando |
|---|---|---|
| `QIT001010` | 404 | conta não existe ou não é de cliente |
| `QIT001011` | 409 | a conta está bloqueada ou encerrada |
| `QIT001003` | 422 | CPF ou CNPJ de quem deposita com dígito verificador errado |
| `QIT001014` | 409 | mesma `request_control_key` com outro pedido |

Idempotente: sim, pela `request_control_key`.

### POST /accounts/{account_key}/withdrawals

Tokens: conta. Schema: `post_withdrawals.json`. Só o dono saca (MOV-15). O dinheiro vai para a conta "mundo de fora". Sem tarifa e sem XP.

Corpo:

```json
{
  "amount": 10000,
  "request_control_key": "1b2c3d4e-5f6a-4b7c-8d9e-0f1a2b3c4d5e"
}
```

Sucesso: 201. `balance`: o saldo da conta depois do saque.

```json
{
  "transaction_key": "d4a9b6c3-5e1f-4a0d-8b4c-3f2e1d0c9a87",
  "balance": 40000
}
```

| Código | Status | Quando |
|---|---|---|
| `QIT001010` | 404 | conta não existe ou não é de cliente; ou o `ACCOUNT-TOKEN` falta ou não é dela |
| `QIT001011` | 409 | a conta está bloqueada ou encerrada |
| `QIT001015` | 422 | o saldo não cobre o valor |
| `QIT001014` | 409 | mesma `request_control_key` com outro pedido |

Idempotente: sim, pela `request_control_key`.

### POST /accounts/{account_key}/transfers

Tokens: conta. Schema: `post_transfers.json`. A conta da URL envia; quem envia paga a tarifa, num lançamento próprio (MOV-06, MOV-09, MOV-10, DAD-16). Dá XP para os dois lados (GAM-17). Até R$ 100,00, concorre ao sorteio (GAM-10, GAM-22).

Corpo:

```json
{
  "destination_account_key": "c3f8a5b2-4d0e-4f9c-b7a3-2e1d0c9b8f76",
  "amount": 10000,
  "request_control_key": "1b2c3d4e-5f6a-4b7c-8d9e-0f1a2b3c4d5e"
}
```

Sucesso: 201. `balance`: o saldo da conta de origem depois da transferência, já com a tarifa e com o prêmio, se saiu (API-10).

```json
{
  "transaction_key": "d4a9b6c3-5e1f-4a0d-8b4c-3f2e1d0c9a87",
  "balance": 39900
}
```

| Código | Status | Quando |
|---|---|---|
| `QIT001010` | 404 | conta de origem não existe ou não é de cliente; ou o `ACCOUNT-TOKEN` falta ou não é dela |
| `QIT001011` | 409 | a conta de origem está bloqueada ou encerrada |
| `QIT001016` | 422 | origem igual ao destino |
| `QIT001017` | 404 | conta de destino não existe ou não é de cliente |
| `QIT001018` | 409 | conta de destino bloqueada ou encerrada |
| `QIT001015` | 422 | o saldo não cobre valor + tarifa; os dois saldos ficam como estavam |
| `QIT001019` | 422 | a 11ª transferência enviada no dia contábil; a conta fica bloqueada (CLI-08) |
| `QIT001014` | 409 | mesma `request_control_key` com outro pedido |

Idempotente: sim, pela `request_control_key`. O duplo clique não debita duas vezes.

### GET /accounts/{account_key}/transactions/{transaction_key}

Tokens: conta. Uma operação que tem lançamento nesta conta ou no cofrinho dela. `entries`: os lançamentos desta conta e do cofrinho dela, na ordem em que foram gravados; cada um no formato do extrato.

Sucesso: 200

```json
{
  "transaction_key": "d4a9b6c3-5e1f-4a0d-8b4c-3f2e1d0c9a87",
  "type": "TRANSFER",
  "accounting_date": "2026-06-01",
  "created_at": "2026-10-07T14:03:12.123456",
  "entries": [
    {
      "entry_key": "9f4a1b8c-0d6e-4f5c-9a91-8e7d6c5b4f32",
      "transaction_key": "d4a9b6c3-5e1f-4a0d-8b4c-3f2e1d0c9a87",
      "transaction_type": "TRANSFER",
      "entry_type": "AMOUNT",
      "amount": -10000,
      "balance_after": 40000,
      "category": null,
      "counterparty": {
        "type": "CUSTOMER",
        "name": "Bruno Alves",
        "document_number": "***.654.321-**"
      },
      "accounting_date": "2026-06-01",
      "created_at": "2026-10-07T14:03:12.123456"
    },
    {
      "entry_key": "e5b0c7d4-6f2a-4b1e-9c5d-4a3f2e1d0b98",
      "transaction_key": "d4a9b6c3-5e1f-4a0d-8b4c-3f2e1d0c9a87",
      "transaction_type": "TRANSFER",
      "entry_type": "FEE",
      "amount": -100,
      "balance_after": 39900,
      "category": null,
      "counterparty": {
        "type": "BANK"
      },
      "accounting_date": "2026-06-01",
      "created_at": "2026-10-07T14:03:12.123456"
    }
  ]
}
```

`type`: `DEPOSIT`, `WITHDRAWAL`, `TRANSFER`, `SAVE`, `REDEEM` ou `YIELD`. Quando `type` é `REDEEM`, o objeto traz também `gross_amount`, `iof`, `ir` e `net_amount`, como na resposta de `POST .../redemptions`.

| Código | Status | Quando |
|---|---|---|
| `QIT001010` | 404 | conta não existe ou não é de cliente; ou o `ACCOUNT-TOKEN` falta ou não é dela |
| `QIT001020` | 404 | operação que não existe ou não tem lançamento nesta conta nem no cofrinho dela |

Idempotente: sim, só lê.

### GET /accounts/{account_key}/entries

Tokens: conta. Schema: `get_entries.json` (query string). O extrato da conta principal: mais recentes primeiro (`created_at` decrescente, desempate pelo mais novo), com o saldo depois de cada lançamento (MOV-04, MOV-14, MOV-17, MOV-18).

Query: `limit` de 1 a 100 (padrão 10) e `page` a partir de 0 (padrão 0). Exemplo: `/accounts/b2e7f4a1-3c9d-4e8b-a6f2-1d0c9b8a7e65/entries?limit=10&page=0`.

Sucesso: 200

```json
{
  "data": [
    {
      "entry_key": "e5b0c7d4-6f2a-4b1e-9c5d-4a3f2e1d0b98",
      "transaction_key": "d4a9b6c3-5e1f-4a0d-8b4c-3f2e1d0c9a87",
      "transaction_type": "TRANSFER",
      "entry_type": "FEE",
      "amount": -100,
      "balance_after": 39900,
      "category": null,
      "counterparty": {
        "type": "BANK"
      },
      "accounting_date": "2026-06-01",
      "created_at": "2026-10-07T14:03:12.123456"
    },
    {
      "entry_key": "9f4a1b8c-0d6e-4f5c-9a91-8e7d6c5b4f32",
      "transaction_key": "d4a9b6c3-5e1f-4a0d-8b4c-3f2e1d0c9a87",
      "transaction_type": "TRANSFER",
      "entry_type": "AMOUNT",
      "amount": -10000,
      "balance_after": 40000,
      "category": null,
      "counterparty": {
        "type": "CUSTOMER",
        "name": "Bruno Alves",
        "document_number": "***.654.321-**"
      },
      "accounting_date": "2026-06-01",
      "created_at": "2026-10-07T14:03:12.123456"
    },
    {
      "entry_key": "0a5b2c9d-1e7f-4a6d-ab02-9f8e7d6c5a43",
      "transaction_key": "8e3f0a7b-9c5d-4e4b-8f80-7d6c5b4a3e21",
      "transaction_type": "DEPOSIT",
      "entry_type": "AMOUNT",
      "amount": 50000,
      "balance_after": 50000,
      "category": null,
      "counterparty": {
        "type": "DEPOSITOR",
        "name": "Carlos Souza",
        "document_number": "**.222.333/****-**"
      },
      "accounting_date": "2026-06-01",
      "created_at": "2026-10-07T14:01:05.654321"
    }
  ],
  "limit": 10,
  "page": 0,
  "is_last_page": true
}
```

Item do extrato:

| Campo | O que é |
|---|---|
| `entry_key` | key do lançamento |
| `transaction_key` | key da operação |
| `transaction_type` | `DEPOSIT`, `WITHDRAWAL`, `TRANSFER`, `SAVE`, `REDEEM` ou `YIELD` |
| `entry_type` | `AMOUNT` (o valor), `FEE` (tarifa), `PRIZE` (prêmio do sorteio), `YIELD` (rendimento), `IOF` ou `IR` |
| `amount` | centavos com sinal: negativo sai, positivo entra |
| `balance_after` | saldo da conta depois do lançamento; no cofrinho, o saldo total do cofrinho |
| `category` | `null` na conta principal; no cofrinho, `{"category_key", "name"}` da categoria do lançamento |
| `counterparty` | a outra ponta (MOV-17), na tabela abaixo |
| `accounting_date` | dia do banco em que contou |
| `created_at` | quando aconteceu |

`counterparty` (MOV-17):

| Lançamento | `counterparty` |
|---|---|
| transferência (`AMOUNT`) | `{"type": "CUSTOMER", "name", "document_number"}`: o outro cliente, com o CPF mascarado |
| depósito (`AMOUNT`) | `{"type": "DEPOSITOR", "name", "document_number"}`: quem depositou, com o CPF ou CNPJ mascarado |
| tarifa, prêmio e rendimento | `{"type": "BANK"}` |
| guardar e resgatar, na conta principal | `{"type": "PIGGY_BANK", "category_key", "name"}`: o cofrinho e a categoria |
| guardar e resgatar, no cofrinho | `{"type": "ACCOUNT"}`: a conta principal |
| saque | `null` |

COF-25: IOF e IR ficam somente no ledger da BANK, sem linhas no extrato do cliente. O resgate mostra o bruto no cofrinho e somente o líquido na conta; líquido zero não gera lançamento na conta.

| Código | Status | Quando |
|---|---|---|
| `QIT001010` | 404 | conta não existe ou não é de cliente; ou o `ACCOUNT-TOKEN` falta ou não é dela |

Idempotente: sim, só lê.

## Gamificação

### GET /accounts/{account_key}/gamification

Tokens: conta. A gamificação da conta (API-14, GAM-01).

Sucesso: 200

```json
{
  "level": 1,
  "xp": 250,
  "xp_to_next_level": 3750,
  "points_free": 0,
  "points_fee": 1,
  "points_chance": 0,
  "fee_percent": "0.9",
  "chance_percent": "0",
  "rank": "DEFAULT",
  "cdi_percent": "100",
  "piggy_record": 0,
  "grace_until": null
}
```

| Campo | O que é |
|---|---|
| `level` | nível atual, de 0 a 10 |
| `xp` | XP dentro do nível atual |
| `xp_to_next_level` | XP que falta para o próximo nível; `null` no nível 10 |
| `points_free`, `points_fee`, `points_chance` | pontos livres, aplicados em tarifa e aplicados em chance |
| `fee_percent` | tarifa atual da transferência, em % (`"1"` sem pontos; `"0"` com 10 pontos) |
| `chance_percent` | chance atual de não debitar, em % |
| `rank` | `DEFAULT`, `BRONZE`, `SILVER`, `GOLD`, `PLATINUM` ou `DIAMOND` |
| `cdi_percent` | quanto o cofrinho rende, em % do CDI (`"100"`, `"102.5"`, `"105"`, `"110"`, `"115"`, `"120"`) |
| `piggy_record` | maior saldo que o cofrinho já teve, em centavos |
| `grace_until` | último dia da carência; `null` fora da carência |

| Código | Status | Quando |
|---|---|---|
| `QIT001010` | 404 | conta não existe ou não é de cliente; ou o `ACCOUNT-TOKEN` falta ou não é dela |

Idempotente: sim, só lê.

### POST /accounts/{account_key}/point_applications

Tokens: conta. Schema: `post_point_applications.json`. Soma pontos livres a um benefício (GAM-21). Conta bloqueada aplica (CLI-09).

Corpo (`benefit`: `FEE` ou `CHANCE`):

```json
{
  "benefit": "FEE",
  "points": 1
}
```

Sucesso: 200, com o corpo de `GET /accounts/{account_key}/gamification` já atualizado.

```json
{
  "level": 1,
  "xp": 250,
  "xp_to_next_level": 3750,
  "points_free": 0,
  "points_fee": 1,
  "points_chance": 0,
  "fee_percent": "0.9",
  "chance_percent": "0",
  "rank": "DEFAULT",
  "cdi_percent": "100",
  "piggy_record": 0,
  "grace_until": null
}
```

| Código | Status | Quando |
|---|---|---|
| `QIT001010` | 404 | conta não existe ou não é de cliente; ou o `ACCOUNT-TOKEN` falta ou não é dela |
| `QIT001011` | 409 | a conta está encerrada |
| `QIT001027` | 422 | mais pontos do que os livres |

Idempotente: não. Sem chave (GAM-21): cada pedido aplica os pontos de novo, enquanto houver pontos livres.

### POST /accounts/{account_key}/point_resets

Tokens: conta. Sem corpo. Todos os pontos voltam a livres (GAM-21). Conta bloqueada zera (CLI-09).

Sucesso: 200, com o corpo de `GET /accounts/{account_key}/gamification` já atualizado.

```json
{
  "level": 1,
  "xp": 250,
  "xp_to_next_level": 3750,
  "points_free": 1,
  "points_fee": 0,
  "points_chance": 0,
  "fee_percent": "1",
  "chance_percent": "0",
  "rank": "DEFAULT",
  "cdi_percent": "100",
  "piggy_record": 0,
  "grace_until": null
}
```

| Código | Status | Quando |
|---|---|---|
| `QIT001010` | 404 | conta não existe ou não é de cliente; ou o `ACCOUNT-TOKEN` falta ou não é dela |
| `QIT001011` | 409 | a conta está encerrada |

Idempotente: sim. Zerar de novo deixa os pontos como estão.

## Cofrinho

### POST /accounts/{account_key}/savings

Tokens: conta. Schema: `post_savings.json`. Leva dinheiro da conta para uma categoria do cofrinho; sem `category_key`, vai para "economias" (COF-03, COF-10). Sem tarifa.

Corpo:

```json
{
  "amount": 10000,
  "request_control_key": "1b2c3d4e-5f6a-4b7c-8d9e-0f1a2b3c4d5e",
  "category_key": "a7d2e9f6-8b4c-4d3a-be7f-6c5b4a3f2d10"
}
```

Sucesso: 201. `balance`: saldo da conta; `piggy_bank_balance`: saldo total do cofrinho, os dois depois de guardar.

```json
{
  "transaction_key": "d4a9b6c3-5e1f-4a0d-8b4c-3f2e1d0c9a87",
  "balance": 29900,
  "piggy_bank_balance": 10000
}
```

| Código | Status | Quando |
|---|---|---|
| `QIT001010` | 404 | conta não existe ou não é de cliente; ou o `ACCOUNT-TOKEN` falta ou não é dela |
| `QIT001011` | 409 | a conta está bloqueada ou encerrada |
| `QIT001021` | 404 | categoria que não existe neste cofrinho |
| `QIT001022` | 409 | categoria excluída |
| `QIT001015` | 422 | o saldo da conta não cobre o valor |
| `QIT001014` | 409 | mesma `request_control_key` com outro pedido |

Idempotente: sim, pela `request_control_key`.

### POST /accounts/{account_key}/redemptions

Tokens: conta. Schema: `post_redemptions.json`. Traz dinheiro de uma categoria do cofrinho para a conta; sem `category_key`, sai de "economias". Sai do lote mais antigo da categoria, e o IOF e o IR são descontados do rendimento (COF-06, COF-08, COF-12, COF-24).

Corpo:

```json
{
  "amount": 5000,
  "request_control_key": "1b2c3d4e-5f6a-4b7c-8d9e-0f1a2b3c4d5e"
}
```

Sucesso: 201. `gross_amount`: o valor que saiu do cofrinho; `iof` e `ir`: os impostos; `net_amount`: o que entrou na conta (`gross_amount - iof - ir`); `balance` e `piggy_bank_balance` depois do resgate.

```json
{
  "transaction_key": "d4a9b6c3-5e1f-4a0d-8b4c-3f2e1d0c9a87",
  "balance": 34900,
  "piggy_bank_balance": 5000,
  "gross_amount": 5000,
  "iof": 0,
  "ir": 0,
  "net_amount": 5000
}
```

| Código | Status | Quando |
|---|---|---|
| `QIT001010` | 404 | conta não existe ou não é de cliente; ou o `ACCOUNT-TOKEN` falta ou não é dela |
| `QIT001011` | 409 | a conta está bloqueada ou encerrada |
| `QIT001021` | 404 | categoria que não existe neste cofrinho |
| `QIT001022` | 409 | categoria excluída |
| `QIT001023` | 422 | resgate maior que o saldo da categoria (COF-07) |
| `QIT001014` | 409 | mesma `request_control_key` com outro pedido |

Idempotente: sim, pela `request_control_key`.

### GET /accounts/{account_key}/piggy_bank_entries

Tokens: conta. Schema: `get_piggy_bank_entries.json` (query string). O extrato do cofrinho, no envelope e na ordem do extrato da conta (COF-05). `category_key` filtra uma categoria, ativa ou excluída.

Query: `limit` de 1 a 100 (padrão 10), `page` a partir de 0 (padrão 0) e `category_key` (opcional). Exemplo: `/accounts/b2e7f4a1-3c9d-4e8b-a6f2-1d0c9b8a7e65/piggy_bank_entries?limit=10&page=0`.

Sucesso: 200

```json
{
  "data": [
    {
      "entry_key": "e5b0c7d4-6f2a-4b1e-9c5d-4a3f2e1d0b98",
      "transaction_key": "d4a9b6c3-5e1f-4a0d-8b4c-3f2e1d0c9a87",
      "transaction_type": "SAVE",
      "entry_type": "AMOUNT",
      "amount": 10000,
      "balance_after": 10000,
      "category": {
        "category_key": "f6c1d8e5-7a3b-4c2f-ad6e-5b4a3f2e1c09",
        "name": "economias"
      },
      "counterparty": {
        "type": "ACCOUNT"
      },
      "accounting_date": "2026-06-01",
      "created_at": "2026-10-07T14:05:40.111111"
    }
  ],
  "limit": 10,
  "page": 0,
  "is_last_page": true
}
```

| Código | Status | Quando |
|---|---|---|
| `QIT001010` | 404 | conta não existe ou não é de cliente; ou o `ACCOUNT-TOKEN` falta ou não é dela |
| `QIT001021` | 404 | `category_key` que não existe neste cofrinho |

Idempotente: sim, só lê.

### POST /accounts/{account_key}/categories

Tokens: conta. Schema: `post_categories.json`. Cria uma categoria no cofrinho (COF-03, COF-18). Conta bloqueada cria (CLI-09).

Corpo:

```json
{
  "name": "carro"
}
```

Sucesso: 201

```json
{
  "category_key": "a7d2e9f6-8b4c-4d3a-be7f-6c5b4a3f2d10"
}
```

| Código | Status | Quando |
|---|---|---|
| `QIT001010` | 404 | conta não existe ou não é de cliente; ou o `ACCOUNT-TOKEN` falta ou não é dela |
| `QIT001011` | 409 | a conta está encerrada |
| `QIT001024` | 409 | nome repetido entre as categorias ativas do cofrinho |

Idempotente: não. Repetir o nome responde 409 `QIT001024`.

### GET /accounts/{account_key}/categories

Tokens: conta. Schema: `get_categories.json` (query string). Só as categorias ativas, com o saldo de cada uma (COF-05, API-15), na ordem em que foram criadas.

Query: `limit` de 1 a 100 (padrão 10) e `page` a partir de 0 (padrão 0).

COF-28 (9.9): gross_yield/net_yield são rendimento em centavos, sem principal/resíduo; líquido estima resgate total desta categoria na yield_accounting_date, com COF-27.

Sucesso: 200

```json
{
  "data": [
    {
      "category_key": "f6c1d8e5-7a3b-4c2f-ad6e-5b4a3f2e1c09",
      "name": "economias",
      "is_default": true,
      "status": "active",
      "balance": 10000,
      "gross_yield": 0,
      "net_yield": 0,
      "yield_accounting_date": "2026-10-07",
      "created_at": "2026-10-07T14:02:00.000001"
    },
    {
      "category_key": "a7d2e9f6-8b4c-4d3a-be7f-6c5b4a3f2d10",
      "name": "carro",
      "is_default": false,
      "status": "active",
      "balance": 0,
      "gross_yield": 0,
      "net_yield": 0,
      "yield_accounting_date": "2026-10-07",
      "created_at": "2026-10-07T14:06:30.222222"
    }
  ],
  "limit": 10,
  "page": 0,
  "is_last_page": true
}
```

| Código | Status | Quando |
|---|---|---|
| `QIT001010` | 404 | conta não existe ou não é de cliente; ou o `ACCOUNT-TOKEN` falta ou não é dela |

Idempotente: sim, só lê.

### GET /accounts/{account_key}/categories/{category_key}

Tokens: conta. Uma categoria do cofrinho, ativa ou excluída. Excluída sai com `"status": "deleted"` (API-15).

COF-28 (9.9): gross_yield/net_yield são rendimento em centavos, sem principal/resíduo; líquido estima resgate total desta categoria na yield_accounting_date, com COF-27.

Sucesso: 200

```json
{
  "category_key": "a7d2e9f6-8b4c-4d3a-be7f-6c5b4a3f2d10",
  "name": "carro",
  "is_default": false,
  "status": "deleted",
  "balance": 0,
  "gross_yield": 0,
  "net_yield": 0,
  "yield_accounting_date": "2026-10-07",
  "created_at": "2026-10-07T14:06:30.222222"
}
```

| Código | Status | Quando |
|---|---|---|
| `QIT001010` | 404 | conta não existe ou não é de cliente; ou o `ACCOUNT-TOKEN` falta ou não é dela |
| `QIT001021` | 404 | categoria que não existe neste cofrinho |

Idempotente: sim, só lê.

### DELETE /accounts/{account_key}/categories/{category_key}

Tokens: conta. Exclui a categoria: muda o estado para `DELETED` e grava o evento (COF-04, API-15). Conta bloqueada exclui (CLI-09).

Sucesso: 204, sem corpo.

| Código | Status | Quando |
|---|---|---|
| `QIT001010` | 404 | conta não existe ou não é de cliente; ou o `ACCOUNT-TOKEN` falta ou não é dela |
| `QIT001011` | 409 | a conta está encerrada |
| `QIT001021` | 404 | categoria que não existe neste cofrinho |
| `QIT001022` | 409 | categoria já excluída |
| `QIT001025` | 409 | a categoria é "economias" |
| `QIT001026` | 409 | categoria com dinheiro |

Idempotente: não. Excluir de novo responde 409 `QIT001022`.

## Rotas internas (API-13)

### POST /internal/accounts/{account_key}/blocks

Tokens: admin. Schema: `post_blocks.json`. O banco bloqueia a conta, com motivo; o evento grava a origem `MANUAL` (CLI-05).

Corpo (`reason`: `SUSPICIOUS_ACTIVITY`, `JUDICIAL_ORDER`, `CUSTOMER_REQUEST` ou `MANUAL_REVIEW`):

```json
{
  "reason": "JUDICIAL_ORDER"
}
```

Sucesso: 204, sem corpo.

| Código | Status | Quando |
|---|---|---|
| `QIT001010` | 404 | conta não existe ou não é de cliente |
| `QIT001011` | 409 | a conta já está bloqueada ou encerrada |

Idempotente: não. Bloquear de novo responde 409 `QIT001011`.

### POST /internal/accounts/{account_key}/unblocks

Tokens: admin. Sem corpo. A conta volta a `ACTIVE`; o evento grava a origem `MANUAL` (CLI-05).

Sucesso: 204, sem corpo.

| Código | Status | Quando |
|---|---|---|
| `QIT001010` | 404 | conta não existe ou não é de cliente |
| `QIT001013` | 409 | a conta não está bloqueada |

Idempotente: não. Desbloquear de novo responde 409 `QIT001013`.

### POST /internal/day_closings

Tokens: admin. Schema: `post_day_closings.json`. Fecha o dia do relógio do banco, numa transação só: taxa do CDI, rendimento, XP de recorde, ranques e carência; depois avança a data (DIA-02, DIA-03, DIA-05).

Corpo:

```json
{
  "accounting_date": "2026-06-01"
}
```

Sucesso: 200. `closed_date`: o dia fechado; `accounting_date`: o novo dia do relógio.

```json
{
  "closed_date": "2026-06-01",
  "accounting_date": "2026-06-02"
}
```

| Código | Status | Quando |
|---|---|---|
| `QIT001030` | 422 | data que não existe no calendário |
| `QIT001028` | 409 | data já fechada (antes do relógio) |
| `QIT001029` | 422 | data depois do relógio |
| `QIT001031` | 503 | o Banco Central (Mockserver) não respondeu a tempo; nada é gravado e o dia não avança (COF-20) |

Idempotente: não. Fechar a mesma data de novo responde 409 `QIT001028` e não paga duas vezes (DIA-02).
````

**Passo a passo:**
1. Abra a fase (AGENTS.md, seção 7): `git status --short` → saída vazia; depois, um por vez:
   ```
   git switch main
   git switch -c fase/03-contrato
   ```
2. `git log --oneline` → mostra `docs(plano): roteiros auditados` e `feat(banco): fase 02 com as 22 tabelas e os 22 models`. `git tag --list fase-02` → `fase-02`.
3. Crie `docs/rotas.md` com o conteúdo do campo **Arquivos**.
4. Rode a conferência R1 (abaixo) → `25 25 31 0 1`.
5. `docker compose up -d --build --wait`.
6. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `6 passed`.
7. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
8. Feche o passo (AGENTS.md, seção 7), um comando por vez:
   ```
   git add -- docs/rotas.md
   git diff --cached --name-only
   git diff --name-only
   git ls-files --others --exclude-standard
   git commit -m "docs(contrato): tabela de rotas com tokens, respostas, erros e idempotência"
   git log -1 --format=%B
   ```

Conferência R1 (um comando, numa linha só):

```
./.venv/Scripts/python.exe -c "import re, json; f = chr(96) * 3; q = chr(34); t = open('docs/rotas.md', encoding='utf-8').read(); b = re.findall(f + 'json\n(.*?)' + f, t, re.S); [json.loads(x) for x in b]; print(len(re.findall(r'^### (GET|POST|DELETE) /', t, re.M)), len(re.findall(r'^\| (GET|POST|DELETE) /', t, re.M)), len(b), len(re.findall(q + r'\s*:\s*-?\d+\.\d+', t)), len(re.findall(q + r'(id|\w+_id)' + q, t)))"
```

A saída tem 5 números: títulos de rota (`### GET /...`), linhas de rota no resumo, blocos JSON (todos precisam abrir no `json.loads`), números com ponto decimal em campo JSON e campos `"id"` ou terminados em `_id"`. Esperado: `25 25 31 0 1`. O único `"id"` é o do `GET /`, que é o número do processo, não do banco. Se sair `Traceback` com `JSONDecodeError`, um bloco JSON foi copiado errado.

**Testes:** nenhum teste novo. A suíte continua com os 6 testes do `test_healthcheck.py`; as respostas descritas aqui ganham teste nos passos de cada rota.
**Verificar:**
- Conferência R1 → `25 25 31 0 1`.
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `6 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente `docs/rotas.md`.
- `git log -1 --format=%B` → `docs(contrato): tabela de rotas com tokens, respostas, erros e idempotência`

**Pronto quando:**
- [ ] `docs/rotas.md` existe, em UTF-8 sem BOM, igual ao bloco do plano.
- [ ] A R1 dá `25 25 31 0 1`.
- [ ] Suíte com `6 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/03-contrato`.

**Commit:** `docs(contrato): tabela de rotas com tokens, respostas, erros e idempotência`
**Pare se:**
- O item 2 não mostrar as duas mensagens ou a tag `fase-02`: a fase 02 não chegou à `main`.
- A R1 der qualquer saída diferente de `25 25 31 0 1` depois de 3 tentativas de conferir o arquivo contra o plano.
- A suíte não terminar com `6 passed`.

---

### Passo 3.2 — Catálogo de erros
**Branch:** fase/03-contrato · **Depende de:** 3.1
**Objetivo:** os 3 erros genéricos novos em `src/errors/base_error.py` e os 30 do projeto em `src/errors/custom_errors.py`; `QIT001001` e `QIT001002` saem; `UnderageSampleEntity` vira `UnderageCustomer`.
**Decisões:** API-01 — formato de erro · API-11 — status de erro · API-12 — catálogo · R3 — código de erro próprio · R8 — outro dono → 404 · PRD-12 — documento fora da mensagem · ARQ-11 — pode apagar o `sample_entity` · CLI-03 — idade mínima · MOV-12 — idempotência · CLI-08 — bloqueio automático · COF-20 — Banco Central fora → 503 · PRD-08 — timeout no banco · PRD-10 — barreira · PRD-13 — token de administração
**Arquivos:**

O catálogo inteiro. A coluna **Parâmetros** é a assinatura do `__init__` (sem o `self`): as fases seguintes levantam cada erro com esses argumentos, nessa ordem. `status` (em `AccountNotActive` e `AccountNotBlocked`) é o `enumerator` do estado atual da conta. O `title` e a `description` (em inglês) estão no código abaixo.

| Código | Classe | Arquivo | Status | Parâmetros | `translation` | Quando sai |
|---|---|---|---|---|---|---|
| `QIT000001` | `InvalidSchema` | base (já existe) | 400 | `description` | Payload Inválido | corpo ou query string fora do schema |
| `QIT000002` | `ForbiddenNotInternal` | base (já existe) | 403 | — | Requisição precisa ser interna | sem o `INTERNAL-TOKEN` certo |
| `QIT000003` | `ForbiddenNotAdmin` | `base_error.py` (novo) | 403 | — | Requisição precisa do token de administração | rota `/internal` sem o `ADMIN-TOKEN` certo |
| `QIT000010` | `InvalidParameter` | base (já existe) | 400 | `description` | Parâmetros inválidos foram fornecidos na requisição. | parâmetro de caminho tipado inválido (nenhuma rota do projeto usa) |
| `QIT000404` | `NotFoundResource` | base (já existe) | 404 | — | O resource solicitado não pode ser encontrado, mas pode estar disponível no futuro. Requests subsequentes do cliente são permitidos. | caminho que não existe |
| `QIT000405` | `MethodNotAllowed` | base (já existe) | 405 | — | O método desejado não foi encontrado para esse recurso. | método que o caminho não aceita |
| `QIT000429` | `TooManyAuthFailures` | `base_error.py` (novo) | 429 | — | Tentativas demais com token errado. Tente de novo mais tarde. | a barreira contra chute de token disparou |
| `QIT000500` | `InternalError` | base (já existe) | 500 | — | Um erro interno aconteceu e está sendo investigado. | erro inesperado; nunca por regra |
| `QIT000503` | `DatabaseTimeout` | `base_error.py` (novo) | 503 | — | O banco de dados demorou demais para responder. | estourou `lock_timeout` ou `statement_timeout` |
| `QIT001003` | `InvalidDocumentNumber` | `custom_errors.py` (muda) | 422 | — | O CPF ou CNPJ informado não é válido. | CPF do cliente, ou CPF ou CNPJ de quem deposita, com dígito verificador errado |
| `QIT001004` | `DuplicatedDocumentNumber` | `custom_errors.py` (muda) | 409 | — | Já existe um cadastro com este CPF. | CPF já cadastrado |
| `QIT001005` | `DuplicatedEmail` | `custom_errors.py` (muda) | 409 | `email` | Já existe um cadastro com este e-mail. | e-mail já cadastrado |
| `QIT001006` | `UnderageCustomer` | `custom_errors.py` (renomeada) | 422 | `age, minimum_age` | É preciso ter pelo menos {minimum_age} anos. | menos de 18 anos |
| `QIT001007` | `InvalidBirthdate` | `custom_errors.py` (fica) | 422 | `birthdate` | A data de nascimento informada não existe. | data de nascimento que não existe |
| `QIT001008` | `CustomerNotFound` | `custom_errors.py` (novo) | 404 | `customer_key` | O cliente com chave {customer_key} não foi encontrado. | cliente não existe, ou o token não é da conta aberta dele |
| `QIT001009` | `CustomerAlreadyHasAccount` | `custom_errors.py` (novo) | 409 | `customer_key` | O cliente já tem uma conta que não foi encerrada. | o cliente já tem conta não encerrada |
| `QIT001010` | `AccountNotFound` | `custom_errors.py` (novo) | 404 | `account_key` | A conta com chave {account_key} não foi encontrada. | conta não existe, não é de cliente, ou o token não é dela |
| `QIT001011` | `AccountNotActive` | `custom_errors.py` (novo) | 409 | `account_key, status` | A conta não está ativa: está bloqueada ou encerrada. | a conta está bloqueada ou encerrada |
| `QIT001012` | `AccountNotEmpty` | `custom_errors.py` (novo) | 409 | `account_key` | A conta só pode ser encerrada com o saldo e o cofrinho zerados. | encerrar com saldo ou cofrinho diferente de zero |
| `QIT001013` | `AccountNotBlocked` | `custom_errors.py` (novo) | 409 | `account_key, status` | Só uma conta bloqueada pode ser desbloqueada. | desbloquear conta que não está bloqueada |
| `QIT001014` | `IdempotencyKeyConflict` | `custom_errors.py` (novo) | 409 | `request_control_key` | Esta chave de idempotência já foi usada com outro pedido. | mesma `request_control_key` com outro pedido |
| `QIT001015` | `InsufficientBalance` | `custom_errors.py` (novo) | 422 | `account_key` | O saldo não cobre o valor da operação (e a tarifa, na transferência). | o saldo não cobre o valor (mais a tarifa, na transferência) |
| `QIT001016` | `SameAccountTransfer` | `custom_errors.py` (novo) | 422 | — | A conta de destino precisa ser diferente da conta de origem. | origem igual ao destino |
| `QIT001017` | `DestinationAccountNotFound` | `custom_errors.py` (novo) | 404 | `account_key` | A conta de destino não foi encontrada. | conta de destino não existe ou não é de cliente |
| `QIT001018` | `DestinationAccountNotActive` | `custom_errors.py` (novo) | 409 | `account_key` | A conta de destino não está ativa: está bloqueada ou encerrada. | conta de destino bloqueada ou encerrada |
| `QIT001019` | `DailyTransferLimitReached` | `custom_errors.py` (novo) | 422 | `account_key` | O limite diário de transferências foi atingido, e a conta foi bloqueada. | a 11ª transferência enviada no dia contábil |
| `QIT001020` | `TransactionNotFound` | `custom_errors.py` (novo) | 404 | `transaction_key` | A operação com chave {transaction_key} não foi encontrada. | operação que não existe ou não é desta conta |
| `QIT001021` | `CategoryNotFound` | `custom_errors.py` (novo) | 404 | `category_key` | A categoria com chave {category_key} não foi encontrada neste cofrinho. | categoria que não existe neste cofrinho |
| `QIT001022` | `CategoryDeleted` | `custom_errors.py` (novo) | 409 | `category_key` | A categoria foi excluída. | guardar, resgatar ou excluir em categoria excluída |
| `QIT001023` | `InsufficientCategoryBalance` | `custom_errors.py` (novo) | 422 | `category_key` | O saldo da categoria não cobre o resgate. | resgate maior que o saldo da categoria |
| `QIT001024` | `DuplicatedCategoryName` | `custom_errors.py` (novo) | 409 | `name` | Já existe uma categoria ativa com este nome. | nome repetido entre as categorias ativas |
| `QIT001025` | `DefaultCategoryCannotBeDeleted` | `custom_errors.py` (novo) | 409 | `category_key` | A categoria padrão (economias) não pode ser excluída. | excluir "economias" |
| `QIT001026` | `CategoryNotEmpty` | `custom_errors.py` (novo) | 409 | `category_key` | Só uma categoria zerada pode ser excluída. | excluir categoria com dinheiro |
| `QIT001027` | `NotEnoughFreePoints` | `custom_errors.py` (novo) | 422 | `requested, free` | Pontos livres insuficientes: pedidos {requested}, livres {free}. | aplicar mais pontos do que os livres |
| `QIT001028` | `DayAlreadyClosed` | `custom_errors.py` (novo) | 409 | `accounting_date` | O dia {accounting_date} já foi fechado. | virada de uma data já fechada |
| `QIT001029` | `FutureAccountingDate` | `custom_errors.py` (novo) | 422 | `accounting_date, current_date` | O dia {accounting_date} ainda não chegou: o banco está em {current_date}. | virada de uma data depois do relógio |
| `QIT001030` | `InvalidAccountingDate` | `custom_errors.py` (novo) | 422 | `accounting_date` | A data informada não existe no calendário. | data da virada que não existe no calendário |
| `QIT001031` | `CdiUnavailable` | `custom_errors.py` (novo) | 503 | `accounting_date` | O Banco Central não respondeu a taxa do CDI a tempo. | o Banco Central (Mockserver) não respondeu a tempo |
| `QIT001032` | `NumericLimitExceeded` | `custom_errors.py` (novo) | 422 | — | Um valor acumulado excede o limite numérico permitido. | acumulador acima de BIGINT; rollback integral (DAD-19), guarda no passo 9.10 |

Saem do catálogo: `QIT001001` (`NotFoundSampleEntity`) e `QIT001002` (`SampleEntityFinalStatus`). Esses dois códigos não voltam.

- `src/errors/base_error.py` (editar): o conteúdo inteiro passa a ser o bloco abaixo. As 95 primeiras linhas são as do base, sem mudança; as três classes do fim são novas.

```python
import sys
import inspect


def error_verification():
    clsmembers = inspect.getmembers(sys.modules["errors"], inspect.isclass)

    errors_dict = dict()
    for _class in clsmembers:
        class_name = _class[0]
        class_type = _class[1]
        is_custom_exception = False
        if issubclass(class_type, QIException) and class_name != "QIException":
            is_custom_exception = True

        if is_custom_exception:
            code = class_type.code
            if errors_dict.get(code) is not None:
                used_class_name = errors_dict[code]
                raise Exception(f"The code {code} is being used twice: In {class_name} and {used_class_name}")
            errors_dict[code] = class_name
    return


class QIException(Exception):
    def __init__(self, title, code, http_status, description, translation) -> None:
        self.title = title
        self.description = description
        self.translation = translation
        self.code = code
        self.http_status = http_status


class MethodNotAllowed(QIException):
    code = "QIT000405"

    def __init__(self) -> None:
        title = "Method not allowed"
        http_status = 405
        description = "The requested method is forbidden for this resource."
        translation = "O método desejado não foi encontrado para esse recurso."
        super().__init__(title, self.code, http_status, description, translation)


class InternalError(QIException):
    code = "QIT000500"

    def __init__(self) -> None:
        title = "Internal Error"
        http_status = 500
        description = "An internal error has occurred and its being investigated."
        translation = "Um erro interno aconteceu e está sendo investigado."
        super().__init__(title, self.code, http_status, description, translation)


class NotFoundResource(QIException):
    code = "QIT000404"

    def __init__(self) -> None:
        title = "Resource not Found"
        http_status = 404
        description = "The requested resource could not be found but may be available in the future. Subsequent requests by the client are permissible."
        translation = "O resource solicitado não pode ser encontrado, mas pode estar disponível no futuro. Requests subsequentes do cliente são permitidos."
        super().__init__(title, self.code, http_status, description, translation)


class InvalidSchema(QIException):
    code = "QIT000001"

    def __init__(self, __description) -> None:
        title = "Bad Request"
        http_status = 400
        description = __description
        translation = "Payload Inválido"
        super().__init__(title, self.code, http_status, description, translation)


class ForbiddenNotInternal(QIException):
    code = "QIT000002"

    def __init__(self) -> None:
        title = "Forbidden"
        http_status = 403
        description = "Request must be internal"
        translation = "Requisição precisa ser interna"
        super().__init__(title, self.code, http_status, description, translation)


class InvalidParameter(QIException):
    code = "QIT000010"

    def __init__(self, description) -> None:
        title = "Invalid Parameter"
        http_status = 400
        translation = "Parâmetros inválidos foram fornecidos na requisição."
        super().__init__(title, self.code, http_status, description, translation)


class ForbiddenNotAdmin(QIException):
    """Rota /internal sem o ADMIN-TOKEN certo (PRD-13).

    O INTERNAL-TOKEN já passou: este é o segundo cadeado, só das rotas
    da operação do banco. Quem responde é o middleware do admin token.
    """

    code = "QIT000003"

    def __init__(self) -> None:
        title = "Forbidden"
        http_status = 403
        description = "Request must carry a valid admin token"
        translation = "Requisição precisa do token de administração"
        super().__init__(title, self.code, http_status, description, translation)


class TooManyAuthFailures(QIException):
    """A barreira contra chute de token disparou (PRD-10).

    Responde antes de conferir qualquer token: quem errou demais na
    janela espera, mesmo que agora mande o token certo.
    """

    code = "QIT000429"

    def __init__(self) -> None:
        title = "Too Many Requests"
        http_status = 429
        description = "Too many failed token attempts from this client. Try again later."
        translation = "Tentativas demais com token errado. Tente de novo mais tarde."
        super().__init__(title, self.code, http_status, description, translation)


class DatabaseTimeout(QIException):
    """O banco passou do lock_timeout ou do statement_timeout (PRD-08).

    503, e não 500: a API está certa, quem demorou foi a dependência. A
    transação é desfeita e nada é gravado.
    """

    code = "QIT000503"

    def __init__(self) -> None:
        title = "Service Unavailable"
        http_status = 503
        description = "The database took too long to answer."
        translation = "O banco de dados demorou demais para responder."
        super().__init__(title, self.code, http_status, description, translation)
```

- `src/errors/custom_errors.py` (editar): o conteúdo inteiro passa a ser:

```python
from errors import QIException


# ────────────────────────────────────────────────────────────────
# Cliente
# ────────────────────────────────────────────────────────────────


class InvalidDocumentNumber(QIException):
    """O CPF ou o CNPJ tem o formato certo e não existe.

    422, e não 400, de propósito: 400 quer dizer "não consegui ler o seu
    pedido". Aqui a API leu, entendeu, e o valor é que não pode existir —
    os dígitos verificadores não batem com a conta. Vale para o CPF do
    cliente e para o CPF ou CNPJ de quem deposita. O número não volta na
    mensagem (PRD-12).
    """

    code = "QIT001003"

    def __init__(self) -> None:
        title = "Invalid Document Number"
        http_status = 422
        description = "The document number is not a valid CPF or CNPJ."
        translation = "O CPF ou CNPJ informado não é válido."
        super().__init__(title, self.code, http_status, description, translation)


class DuplicatedDocumentNumber(QIException):
    """Já existe um cliente com este CPF.

    409 Conflict: o pedido está correto em si, e o que impede é o que já
    está no banco.
    """

    code = "QIT001004"

    def __init__(self) -> None:
        title = "Document Number already registered"
        http_status = 409
        description = "There is already a customer with this document number."
        translation = "Já existe um cadastro com este CPF."
        super().__init__(title, self.code, http_status, description, translation)


class DuplicatedEmail(QIException):
    code = "QIT001005"

    def __init__(self, email) -> None:
        title = "Email already registered"
        http_status = 409
        description = f"There is already a customer with the email {email}."
        translation = "Já existe um cadastro com este e-mail."
        super().__init__(title, self.code, http_status, description, translation)


class UnderageCustomer(QIException):
    code = "QIT001006"

    def __init__(self, age, minimum_age) -> None:
        title = "Customer is underage"
        http_status = 422
        description = f"The customer is {age} years old, and the minimum is {minimum_age}."
        translation = f"É preciso ter pelo menos {minimum_age} anos."
        super().__init__(title, self.code, http_status, description, translation)


class InvalidBirthdate(QIException):
    """A data tem o formato certo e não existe no calendário.

    O `pattern` do schema sabe contar dígitos, não dias: "2025-02-30"
    passa pelo regex e morre no `date.fromisoformat`. Sem esta classe,
    esse ValueError virava 500.
    """

    code = "QIT001007"

    def __init__(self, birthdate) -> None:
        title = "Invalid Birthdate"
        http_status = 422
        description = f"The birthdate {birthdate} is not a real date."
        translation = "A data de nascimento informada não existe."
        super().__init__(title, self.code, http_status, description, translation)


class CustomerNotFound(QIException):
    """O cliente não existe, ou o token não é o da conta aberta dele.

    Os dois casos respondem igual (R8): quem não é o dono não descobre
    se o cliente existe.
    """

    code = "QIT001008"

    def __init__(self, customer_key) -> None:
        title = "Customer not Found"
        http_status = 404
        description = f"Customer with key {customer_key} was not found."
        translation = f"O cliente com chave {customer_key} não foi encontrado."
        super().__init__(title, self.code, http_status, description, translation)


# ────────────────────────────────────────────────────────────────
# Conta
# ────────────────────────────────────────────────────────────────


class CustomerAlreadyHasAccount(QIException):
    code = "QIT001009"

    def __init__(self, customer_key) -> None:
        title = "Customer already has an account"
        http_status = 409
        description = f"Customer with key {customer_key} already has an account that is not closed."
        translation = "O cliente já tem uma conta que não foi encerrada."
        super().__init__(title, self.code, http_status, description, translation)


class AccountNotFound(QIException):
    """A conta não existe, não é de cliente, ou o token não é dela.

    Os três casos respondem igual (R8, API-09): recurso de outro dono é
    404, nunca 403.
    """

    code = "QIT001010"

    def __init__(self, account_key) -> None:
        title = "Account not Found"
        http_status = 404
        description = f"Account with key {account_key} was not found."
        translation = f"A conta com chave {account_key} não foi encontrada."
        super().__init__(title, self.code, http_status, description, translation)


class AccountNotActive(QIException):
    code = "QIT001011"

    def __init__(self, account_key, status) -> None:
        title = "Account is not active"
        http_status = 409
        description = f"Account with key {account_key} is {status} and cannot do this operation."
        translation = "A conta não está ativa: está bloqueada ou encerrada."
        super().__init__(title, self.code, http_status, description, translation)


class AccountNotEmpty(QIException):
    code = "QIT001012"

    def __init__(self, account_key) -> None:
        title = "Account is not empty"
        http_status = 409
        description = f"Account with key {account_key} has money in its balance or in its piggy bank."
        translation = "A conta só pode ser encerrada com o saldo e o cofrinho zerados."
        super().__init__(title, self.code, http_status, description, translation)


class AccountNotBlocked(QIException):
    code = "QIT001013"

    def __init__(self, account_key, status) -> None:
        title = "Account is not blocked"
        http_status = 409
        description = f"Account with key {account_key} is {status}, not BLOCKED."
        translation = "Só uma conta bloqueada pode ser desbloqueada."
        super().__init__(title, self.code, http_status, description, translation)


# ────────────────────────────────────────────────────────────────
# Dinheiro
# ────────────────────────────────────────────────────────────────


class IdempotencyKeyConflict(QIException):
    """A mesma request_control_key chegou com outro pedido (MOV-12).

    Mesma chave e mesmo pedido não é erro: é a resposta da primeira vez.
    """

    code = "QIT001014"

    def __init__(self, request_control_key) -> None:
        title = "Idempotency key conflict"
        http_status = 409
        description = f"The request_control_key {request_control_key} was already used with a different request."
        translation = "Esta chave de idempotência já foi usada com outro pedido."
        super().__init__(title, self.code, http_status, description, translation)


class InsufficientBalance(QIException):
    code = "QIT001015"

    def __init__(self, account_key) -> None:
        title = "Insufficient balance"
        http_status = 422
        description = f"The balance of account {account_key} does not cover this operation."
        translation = "O saldo não cobre o valor da operação (e a tarifa, na transferência)."
        super().__init__(title, self.code, http_status, description, translation)


class SameAccountTransfer(QIException):
    code = "QIT001016"

    def __init__(self) -> None:
        title = "Same account transfer"
        http_status = 422
        description = "The destination account must be different from the origin account."
        translation = "A conta de destino precisa ser diferente da conta de origem."
        super().__init__(title, self.code, http_status, description, translation)


class DestinationAccountNotFound(QIException):
    code = "QIT001017"

    def __init__(self, account_key) -> None:
        title = "Destination account not Found"
        http_status = 404
        description = f"Destination account with key {account_key} was not found."
        translation = "A conta de destino não foi encontrada."
        super().__init__(title, self.code, http_status, description, translation)


class DestinationAccountNotActive(QIException):
    code = "QIT001018"

    def __init__(self, account_key) -> None:
        title = "Destination account is not active"
        http_status = 409
        description = f"Destination account with key {account_key} cannot receive money."
        translation = "A conta de destino não está ativa: está bloqueada ou encerrada."
        super().__init__(title, self.code, http_status, description, translation)


class DailyTransferLimitReached(QIException):
    """A 11ª transferência enviada no dia contábil (CLI-08).

    É a única recusa que grava alguma coisa: a conta fica bloqueada na
    mesma requisição (DAD-13).
    """

    code = "QIT001019"

    def __init__(self, account_key) -> None:
        title = "Daily transfer limit reached"
        http_status = 422
        description = f"Account {account_key} reached the daily limit of transfers and was blocked."
        translation = "O limite diário de transferências foi atingido, e a conta foi bloqueada."
        super().__init__(title, self.code, http_status, description, translation)


class TransactionNotFound(QIException):
    code = "QIT001020"

    def __init__(self, transaction_key) -> None:
        title = "Transaction not Found"
        http_status = 404
        description = f"Transaction with key {transaction_key} was not found."
        translation = f"A operação com chave {transaction_key} não foi encontrada."
        super().__init__(title, self.code, http_status, description, translation)


# ────────────────────────────────────────────────────────────────
# Cofrinho e categorias
# ────────────────────────────────────────────────────────────────


class CategoryNotFound(QIException):
    code = "QIT001021"

    def __init__(self, category_key) -> None:
        title = "Category not Found"
        http_status = 404
        description = f"Category with key {category_key} was not found in this piggy bank."
        translation = f"A categoria com chave {category_key} não foi encontrada neste cofrinho."
        super().__init__(title, self.code, http_status, description, translation)


class CategoryDeleted(QIException):
    code = "QIT001022"

    def __init__(self, category_key) -> None:
        title = "Category is deleted"
        http_status = 409
        description = f"Category with key {category_key} is deleted."
        translation = "A categoria foi excluída."
        super().__init__(title, self.code, http_status, description, translation)


class InsufficientCategoryBalance(QIException):
    code = "QIT001023"

    def __init__(self, category_key) -> None:
        title = "Insufficient category balance"
        http_status = 422
        description = f"The balance of category {category_key} does not cover this redemption."
        translation = "O saldo da categoria não cobre o resgate."
        super().__init__(title, self.code, http_status, description, translation)


class DuplicatedCategoryName(QIException):
    code = "QIT001024"

    def __init__(self, name) -> None:
        title = "Category name already registered"
        http_status = 409
        description = f"There is already an active category named {name}."
        translation = "Já existe uma categoria ativa com este nome."
        super().__init__(title, self.code, http_status, description, translation)


class DefaultCategoryCannotBeDeleted(QIException):
    code = "QIT001025"

    def __init__(self, category_key) -> None:
        title = "Default category cannot be deleted"
        http_status = 409
        description = f"Category with key {category_key} is the default category."
        translation = "A categoria padrão (economias) não pode ser excluída."
        super().__init__(title, self.code, http_status, description, translation)


class CategoryNotEmpty(QIException):
    code = "QIT001026"

    def __init__(self, category_key) -> None:
        title = "Category is not empty"
        http_status = 409
        description = f"Category with key {category_key} has money."
        translation = "Só uma categoria zerada pode ser excluída."
        super().__init__(title, self.code, http_status, description, translation)


# ────────────────────────────────────────────────────────────────
# Gamificação
# ────────────────────────────────────────────────────────────────


class NotEnoughFreePoints(QIException):
    code = "QIT001027"

    def __init__(self, requested, free) -> None:
        title = "Not enough free points"
        http_status = 422
        description = f"Requested {requested} points, but only {free} are free."
        translation = f"Pontos livres insuficientes: pedidos {requested}, livres {free}."
        super().__init__(title, self.code, http_status, description, translation)


# ────────────────────────────────────────────────────────────────
# Virada do dia
# ────────────────────────────────────────────────────────────────


class DayAlreadyClosed(QIException):
    code = "QIT001028"

    def __init__(self, accounting_date) -> None:
        title = "Day already closed"
        http_status = 409
        description = f"The day {accounting_date} is already closed."
        translation = f"O dia {accounting_date} já foi fechado."
        super().__init__(title, self.code, http_status, description, translation)


class FutureAccountingDate(QIException):
    code = "QIT001029"

    def __init__(self, accounting_date, current_date) -> None:
        title = "Future accounting date"
        http_status = 422
        description = f"The day {accounting_date} is after the bank date {current_date}."
        translation = f"O dia {accounting_date} ainda não chegou: o banco está em {current_date}."
        super().__init__(title, self.code, http_status, description, translation)


class InvalidAccountingDate(QIException):
    """A data tem o formato certo e não existe no calendário.

    Mesma ideia do InvalidBirthdate: o schema confere o formato, e
    "2026-02-30" só morre no `date.fromisoformat`.
    """

    code = "QIT001030"

    def __init__(self, accounting_date) -> None:
        title = "Invalid accounting date"
        http_status = 422
        description = f"The accounting date {accounting_date} is not a real date."
        translation = "A data informada não existe no calendário."
        super().__init__(title, self.code, http_status, description, translation)


class CdiUnavailable(QIException):
    """O Banco Central (o Mockserver) não respondeu a tempo (COF-20).

    503: a dependência está fora do ar ou lenta. A virada é desfeita
    inteira, e o dia não avança.
    """

    code = "QIT001031"

    def __init__(self, accounting_date) -> None:
        title = "CDI rate unavailable"
        http_status = 503
        description = f"The Central Bank did not answer the CDI rate for {accounting_date} in time."
        translation = "O Banco Central não respondeu a taxa do CDI a tempo."
        super().__init__(title, self.code, http_status, description, translation)

class NumericLimitExceeded(QIException):
    code = "QIT001032"

    def __init__(self) -> None:
        super().__init__("Numeric Limit Exceeded", self.code, 422,
                         "An accumulated value exceeds the BIGINT limit.",
                         "Um valor acumulado excede o limite numérico permitido.")

```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/03-contrato`; `git log --oneline -n 3` → mostra `docs(contrato): tabela de rotas com tokens, respostas, erros e idempotência`.
2. `docker compose up -d --build --wait`.
3. Rode a conferência E1 (abaixo), antes do código → exatamente:
   ```
   QIT000001:400 QIT000002:403 QIT000010:400 QIT000404:404 QIT000405:405 QIT000500:500 QIT001001:404 QIT001002:409 QIT001003:422 QIT001004:409 QIT001005:409 QIT001006:422 QIT001007:422
   ```
4. Edite `src/errors/base_error.py` com o conteúdo do campo **Arquivos**.
5. Edite `src/errors/custom_errors.py` com o conteúdo do campo **Arquivos**.
6. Rode a E1 de novo → exatamente a linha do **Verificar**.
7. `docker compose up -d --build --wait` → termina sem erro. Na subida, a API roda o `error_verification`, que derruba a aplicação se um código aparecer duas vezes.
8. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `6 passed`.
9. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
10. `git grep -n -e QIT001001 -e QIT001002 -e SampleEntity -- src/errors` → nenhuma linha.
11. `git grep -l SampleEntity -- src` → exatamente `src/utils/schema_handler.py` (sai na fase 4).
12. Feche o passo (AGENTS.md, seção 7), um comando por vez:
    ```
    git add -- src/errors/base_error.py src/errors/custom_errors.py
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "feat(erros): catálogo de erros do projeto"
    git log -1 --format=%B
    ```

Conferência E1 (um comando, numa linha só). Roda dentro do container da API: carrega o pacote `errors`, cria cada erro com `"x"` em cada parâmetro e imprime `código:status` de todos, em ordem:

```
docker compose exec -T api python -c "import errors, inspect; from errors.base_error import QIException; ks = [k for n, k in inspect.getmembers(errors, inspect.isclass) if issubclass(k, QIException) and k is not QIException]; print(' '.join(sorted(k.code + ':' + str(k(*['x'] * (len(inspect.signature(k.__init__).parameters) - 1)).http_status) for k in ks)))"
```

**Testes:** nenhum teste novo. Um erro só sai por uma rota, e as rotas nascem nas fases 4 a 9: cada código ganha o seu teste black box no passo da rota que o levanta (TST-02). Aqui, a prova é a E1 (cada classe nasce com o código e o status do catálogo) e a subida da API (nenhum código repetido).
**Verificar:**
- E1 → exatamente esta linha:
  ```
  QIT000001:400 QIT000002:403 QIT000003:403 QIT000010:400 QIT000404:404 QIT000405:405 QIT000429:429 QIT000500:500 QIT000503:503 QIT001003:422 QIT001004:409 QIT001005:409 QIT001006:422 QIT001007:422 QIT001008:404 QIT001009:409 QIT001010:404 QIT001011:409 QIT001012:409 QIT001013:409 QIT001014:409 QIT001015:422 QIT001016:422 QIT001017:404 QIT001018:409 QIT001019:422 QIT001020:404 QIT001021:404 QIT001022:409 QIT001023:422 QIT001024:409 QIT001025:409 QIT001026:409 QIT001027:422 QIT001028:409 QIT001029:422 QIT001030:422 QIT001031:503 QIT001032:422
  ```
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `6 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/errors/base_error.py
  src/errors/custom_errors.py
  ```
- `git log -1 --format=%B` → `feat(erros): catálogo de erros do projeto`

**Pronto quando:**
- [ ] A E1 dá os 39 códigos com os status do catálogo; nenhum `QIT001001` nem `QIT001002`.
- [ ] A API sobe com `docker compose up -d --build --wait`.
- [ ] `git grep` não acha `SampleEntity` em `src/errors/`.
- [ ] Suíte com `6 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/03-contrato`.

**Commit:** `feat(erros): catálogo de erros do projeto`
**Pare se:**
- A E1 do item 3 der outra linha: o catálogo do base não é o que o plano espera.
- A E1 do item 6 der outra linha depois de 3 tentativas de conferir os dois arquivos contra o plano.
- `docker compose up -d --build --wait` falhar: rode `docker compose logs --tail 100 api` e traga a saída (a frase `is being used twice` diz qual código se repetiu).
- O item 11 mostrar outro arquivo além de `src/utils/schema_handler.py`: algum código ainda usa um erro do `sample_entity`.
- A suíte não terminar com `6 passed`.

---

### Passo 3.3 — Schemas do cliente, do depósito e do saque
**Branch:** fase/03-contrato · **Depende de:** 3.2
**Objetivo:** o teste que confere os arquivos de schema e os 3 primeiros schemas: `post_customers.json`, `post_deposits.json` e `post_withdrawals.json`.
**Decisões:** API-03 — schema fechado · API-18 — valor inteiro ≥ 1 · R6 — sem float · DAD-08 — centavos em `BIGINT` · CLI-02 — dados do cliente · MOV-12 — idempotência · MOV-15 — quem deposita · MOV-16 — corpo do depósito · TST-05 — unitários em pasta separada
**Arquivos:**

Regras de todos os schemas desta fase (os passos 3.4 a 3.6 seguem as mesmas):

- `"$schema": "http://json-schema.org/draft-04/schema#"` na primeira linha. O `jsonschema==4.17.3` do `requirements.txt` escolhe o validador por essa chave; sem ela, usa o draft 2020-12, em que `5050.0` conta como `integer`. No draft 4, `integer` recusa número com ponto: `5050.0` → 400 `QIT000001` (API-18, R6).
- `"additionalProperties": false` em todo schema (API-03).
- Dinheiro (`amount`): `"type": "integer"`, `"minimum": 1` e `"maximum": 9223372036854775807`. O máximo é o limite do `BIGINT` (DAD-08), não regra de negócio: acima dele, o banco recusaria a gravação e a API responderia 500.
- Key no corpo ou na query (`request_control_key`, `destination_account_key`, `category_key`): UUID com letras minúsculas, exatamente 36 caracteres, como `str(uuid4())`.
- Dígitos com `[0-9]`, nunca `\d`: no Python, `\d` aceita dígitos de outros alfabetos (`١٢٣`).
- Campo de formato fixo (CPF, CNPJ, data, key) tem `minLength` e `maxLength` iguais ao tamanho certo. No Python, o `$` do `pattern` aceita uma quebra de linha no fim (`"2026-06-01\n"`); o tamanho fechado a recusa.
- Formatos de texto do base mantidos: `name` de 1 a 255 caracteres; o `pattern` do `email` (CLI-02 — dados do cliente, como no `sample_entity`).

- `tests/unit/__init__.py` (criar): vazio, 0 bytes.
- `tests/unit/test_schema_files.py` (criar): o conteúdo inteiro é:

```python
"""Confere os arquivos de src/schemas/ como texto: cada um é o contrato de entrada de uma rota.

O teste não importa nada de src/: abre o JSON do disco e compara com o que
o plano define. Que a API responde 400 para o corpo fora do schema, cada
rota prova no teste black box dela.
"""

import json
from pathlib import Path

import pytest


SCHEMA_DIR = Path(__file__).resolve().parents[2] / "src" / "schemas"

# Draft 4: nele, o tipo "integer" recusa 5050.0. A partir do draft 6, o
# jsonschema aceita número com ponto e parte decimal zero como inteiro (R6).
DRAFT_04 = "http://json-schema.org/draft-04/schema#"

CPF_PATTERN = "^[0-9]{3}\\.[0-9]{3}\\.[0-9]{3}-[0-9]{2}$"
CNPJ_PATTERN = "^[0-9]{2}\\.[0-9]{3}\\.[0-9]{3}/[0-9]{4}-[0-9]{2}$"
DATE_PATTERN = "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
UUID_PATTERN = "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"

# O maior valor que cabe num BIGINT do PostgreSQL (DAD-08).
BIGINT_MAX = 9223372036854775807

TEXT_FIELD = {"type": "string", "minLength": 1, "maxLength": 255}
DATE_FIELD = {"type": "string", "minLength": 10, "maxLength": 10, "pattern": DATE_PATTERN}
UUID_FIELD = {"type": "string", "minLength": 36, "maxLength": 36, "pattern": UUID_PATTERN}
MONEY_FIELD = {"type": "integer", "minimum": 1, "maximum": BIGINT_MAX}

# O formato de cada campo, igual em todo schema que o usa.
FIELD_RULES = {
    "name": TEXT_FIELD,
    "depositor_name": TEXT_FIELD,
    "document_number": {"type": "string", "minLength": 14, "maxLength": 14, "pattern": CPF_PATTERN},
    "depositor_document": {
        "type": "string",
        "anyOf": [
            {"minLength": 14, "maxLength": 14, "pattern": CPF_PATTERN},
            {"minLength": 18, "maxLength": 18, "pattern": CNPJ_PATTERN},
        ],
    },
    "email": {"type": "string", "maxLength": 255, "pattern": "^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$"},
    "birthdate": DATE_FIELD,
    "accounting_date": DATE_FIELD,
    "amount": MONEY_FIELD,
    "request_control_key": UUID_FIELD,
    "destination_account_key": UUID_FIELD,
    "category_key": UUID_FIELD,
    "limit": {"type": "string", "pattern": "^(100|[1-9][0-9]?)$"},
    "page": {"type": "string", "pattern": "^[0-9]{1,9}$"},
    "points": {"type": "integer", "minimum": 1},
    "benefit": {"type": "string", "enum": ["FEE", "CHANCE"]},
    "reason": {
        "type": "string",
        "enum": ["SUSPICIOUS_ACTIVITY", "JUDICIAL_ORDER", "CUSTOMER_REQUEST", "MANUAL_REVIEW"],
    },
}

# Um item por arquivo de src/schemas/: o title, os campos e os obrigatórios.
# Lista de obrigatórios vazia = o schema não tem a chave "required".
EXPECTED_SCHEMAS = {
    "post_customers.json": {
        "title": "PostCustomers",
        "fields": ["name", "document_number", "email", "birthdate"],
        "required": ["name", "document_number", "email", "birthdate"],
    },
    "post_deposits.json": {
        "title": "PostDeposits",
        "fields": ["depositor_name", "depositor_document", "amount", "request_control_key"],
        "required": ["depositor_name", "depositor_document", "amount", "request_control_key"],
    },
    "post_withdrawals.json": {
        "title": "PostWithdrawals",
        "fields": ["amount", "request_control_key"],
        "required": ["amount", "request_control_key"],
    },
}  # fim de EXPECTED_SCHEMAS

SCHEMA_NAMES = sorted(EXPECTED_SCHEMAS)


def load_schema(name):
    path = SCHEMA_DIR / name
    assert path.is_file(), f"Falta o schema {name} em src/schemas/"
    return json.loads(path.read_text(encoding="utf-8"))


def test_schema_folder_has_exactly_the_expected_files():
    found = sorted(path.name for path in SCHEMA_DIR.glob("*.json"))
    assert found == SCHEMA_NAMES


@pytest.mark.parametrize("name", SCHEMA_NAMES)
def test_schema_header(name):
    schema = load_schema(name)
    assert schema["$schema"] == DRAFT_04
    assert schema["title"] == EXPECTED_SCHEMAS[name]["title"]
    assert schema["type"] == "object"


@pytest.mark.parametrize("name", SCHEMA_NAMES)
def test_schema_is_closed(name):
    schema = load_schema(name)
    assert schema["additionalProperties"] is False


@pytest.mark.parametrize("name", SCHEMA_NAMES)
def test_schema_fields_and_required(name):
    schema = load_schema(name)
    expected = EXPECTED_SCHEMAS[name]
    assert sorted(schema["properties"]) == sorted(expected["fields"])

    if expected["required"]:
        assert sorted(schema["required"]) == sorted(expected["required"])
    else:
        assert "required" not in schema


@pytest.mark.parametrize("name", SCHEMA_NAMES)
def test_schema_field_formats(name):
    schema = load_schema(name)
    for field, rule in schema["properties"].items():
        assert field in FIELD_RULES, f"Campo {field} sem regra no teste"
        assert rule == FIELD_RULES[field], f"Formato errado em {name}: {field}"


@pytest.mark.parametrize("name", SCHEMA_NAMES)
def test_schema_has_no_float_type(name):
    load_schema(name)
    text = (SCHEMA_DIR / name).read_text(encoding="utf-8")
    assert '"number"' not in text
```

- `src/schemas/post_customers.json` (criar): o conteúdo inteiro é:

```json
{
  "$schema": "http://json-schema.org/draft-04/schema#",
  "title": "PostCustomers",
  "type": "object",
  "properties": {
    "name": {
      "type": "string",
      "minLength": 1,
      "maxLength": 255
    },
    "document_number": {
      "type": "string",
      "minLength": 14,
      "maxLength": 14,
      "pattern": "^[0-9]{3}\\.[0-9]{3}\\.[0-9]{3}-[0-9]{2}$"
    },
    "email": {
      "type": "string",
      "maxLength": 255,
      "pattern": "^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$"
    },
    "birthdate": {
      "type": "string",
      "minLength": 10,
      "maxLength": 10,
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    }
  },
  "required": [
    "name",
    "document_number",
    "email",
    "birthdate"
  ],
  "additionalProperties": false
}
```

- `src/schemas/post_deposits.json` (criar): o conteúdo inteiro é:

```json
{
  "$schema": "http://json-schema.org/draft-04/schema#",
  "title": "PostDeposits",
  "type": "object",
  "properties": {
    "depositor_name": {
      "type": "string",
      "minLength": 1,
      "maxLength": 255
    },
    "depositor_document": {
      "type": "string",
      "anyOf": [
        {
          "minLength": 14,
          "maxLength": 14,
          "pattern": "^[0-9]{3}\\.[0-9]{3}\\.[0-9]{3}-[0-9]{2}$"
        },
        {
          "minLength": 18,
          "maxLength": 18,
          "pattern": "^[0-9]{2}\\.[0-9]{3}\\.[0-9]{3}/[0-9]{4}-[0-9]{2}$"
        }
      ]
    },
    "amount": {
      "type": "integer",
      "minimum": 1,
      "maximum": 9223372036854775807
    },
    "request_control_key": {
      "type": "string",
      "minLength": 36,
      "maxLength": 36,
      "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    }
  },
  "required": [
    "depositor_name",
    "depositor_document",
    "amount",
    "request_control_key"
  ],
  "additionalProperties": false
}
```

- `src/schemas/post_withdrawals.json` (criar): o conteúdo inteiro é:

```json
{
  "$schema": "http://json-schema.org/draft-04/schema#",
  "title": "PostWithdrawals",
  "type": "object",
  "properties": {
    "amount": {
      "type": "integer",
      "minimum": 1,
      "maximum": 9223372036854775807
    },
    "request_control_key": {
      "type": "string",
      "minLength": 36,
      "maxLength": 36,
      "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    }
  },
  "required": [
    "amount",
    "request_control_key"
  ],
  "additionalProperties": false
}
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/03-contrato`; `git log --oneline -n 3` → mostra `feat(erros): catálogo de erros do projeto`.
2. Crie `tests/unit/__init__.py` (vazio) e `tests/unit/test_schema_files.py` com o conteúdo do campo **Arquivos**.
3. `./.venv/Scripts/python.exe -m pytest -v tests/unit/test_schema_files.py` → a última linha tem `16 failed`; cada falha é `AssertionError` (`Falta o schema ...` ou a lista vazia de `test_schema_folder_has_exactly_the_expected_files`).
4. Crie os 3 schemas com o conteúdo do campo **Arquivos**.
5. `./.venv/Scripts/python.exe -m pytest -v tests/unit/test_schema_files.py` → a última linha tem `16 passed`.
6. `docker compose up -d --build --wait`.
7. Rode a conferência S3 (abaixo) → a saída do **Verificar**.
8. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `22 passed`.
9. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
10. Feche o passo (AGENTS.md, seção 7), um comando por vez:
    ```
    git add -- tests/unit/__init__.py tests/unit/test_schema_files.py src/schemas/post_customers.json src/schemas/post_deposits.json src/schemas/post_withdrawals.json
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "feat(schemas): cliente, depósito e saque, com o teste dos arquivos de schema"
    git log -1 --format=%B
    ```

Conferência S3 (um comando, numa linha só). Roda dentro do container da API, com o mesmo `jsonschema` que valida as requisições: confere cada schema contra o meta-schema dele (`check_schema`) e diz, para cada corpo de teste, se o schema aceita (`True`) ou recusa (`False`):

```
docker compose exec -T api python -c "import os, json; from constants import SCHEMA_PATH; from jsonschema.validators import validator_for; ld = lambda n: json.load(open(os.path.join(SCHEMA_PATH, n), encoding='utf-8')); c = lambda n, xs: (lambda s: (validator_for(s).check_schema(s), [validator_for(s)(s).is_valid(x) for x in xs])[1])(ld(n)); k = '1b2c3d4e-5f6a-4b7c-8d9e-0f1a2b3c4d5e'; b = {'depositor_name': 'Carlos Souza', 'amount': 5050, 'request_control_key': k}; cu = {'name': 'Ana Lima', 'document_number': '123.456.789-09', 'email': 'ana.lima@example.com', 'birthdate': '1995-04-12'}; print(validator_for(ld('post_withdrawals.json')).__name__, c('post_withdrawals.json', [{'amount': 5050, 'request_control_key': k}, {'amount': 5050.0, 'request_control_key': k}, {'amount': 0, 'request_control_key': k}, {'amount': '5050', 'request_control_key': k}, {'amount': True, 'request_control_key': k}, {'amount': 5050, 'request_control_key': k, 'extra': 1}, {'amount': 5050}, {'amount': 5050, 'request_control_key': k.upper()}]), c('post_deposits.json', [dict(b, depositor_document=x) for x in ['123.456.789-09', '11.222.333/0001-81', '123.456.789-09\n', '12345678909', '11.222.333/0001-8']]), c('post_customers.json', [cu, dict(cu, document_number='123.456.789-09\n'), dict(cu, birthdate='1995-4-12'), dict(cu, email='ana.lima'), dict(cu, name='')]))"
```

Os corpos, na ordem: saque válido; `amount` `5050.0`; `amount` `0`; `amount` em texto; `amount` `true`; campo a mais; sem `request_control_key`; chave em maiúsculas · depósito com CPF; com CNPJ; CPF com quebra de linha no fim; CPF sem pontuação; CNPJ com um dígito a menos · cliente válido; CPF com quebra de linha no fim; data sem zero à esquerda; e-mail sem `@`; nome vazio.

**Testes:** `tests/unit/test_schema_files.py` (unitário; lê os arquivos de `src/schemas/` como texto, não importa nada de `src/`).

O arquivo tem 1 teste solto e 5 testes com `@pytest.mark.parametrize`, que rodam uma vez para cada nome de `EXPECTED_SCHEMAS`:

| Teste | Entrada | Esperado |
|---|---|---|
| `test_schema_folder_has_exactly_the_expected_files` | os nomes dos `*.json` de `src/schemas/` | a lista em ordem é igual às chaves de `EXPECTED_SCHEMAS` em ordem: nem schema a mais, nem a menos |
| `test_schema_header[<arquivo>]` | o arquivo | existe; abre com `json.loads`; `$schema` = `http://json-schema.org/draft-04/schema#`; `title` = o do `EXPECTED_SCHEMAS`; `type` = `object` |
| `test_schema_is_closed[<arquivo>]` | o arquivo | `additionalProperties` é `false` (API-03) |
| `test_schema_fields_and_required[<arquivo>]` | o arquivo | os campos de `properties` são exatamente os `fields`; `required` é exatamente a lista `required` ou, se ela é vazia, o schema não tem `required` |
| `test_schema_field_formats[<arquivo>]` | cada campo de `properties` | igual à regra do campo em `FIELD_RULES`: dinheiro `{"type": "integer", "minimum": 1, "maximum": 9223372036854775807}` (API-18, R6); key `{"type": "string", "minLength": 36, "maxLength": 36, "pattern": <UUID minúsculo>}`; os outros como no dicionário |
| `test_schema_has_no_float_type[<arquivo>]` | o texto do arquivo | não tem `"number"` (R6) |

Arquivo que ainda não existe falha em todos os testes dele com `AssertionError: Falta o schema <arquivo> em src/schemas/`.

Neste passo, `EXPECTED_SCHEMAS` tem 3 arquivos: 1 + 5 × 3 = 16 testes. Antes dos schemas: `16 failed`. Depois: `16 passed`. Suíte: 6 + 16 = 22.

Que a API responde 400 `QIT000001` para o corpo recusado fica provado no teste black box de cada rota (5.3, 6.5, 6.6).
**Verificar:**
- S3 → exatamente:
  ```
  Draft4Validator [True, False, False, False, False, False, False, False] [True, True, False, False, False] [True, False, False, False, False]
  ```
- `./.venv/Scripts/python.exe -m pytest tests/unit` → a última linha tem `16 passed`.
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `22 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/schemas/post_customers.json
  src/schemas/post_deposits.json
  src/schemas/post_withdrawals.json
  tests/unit/__init__.py
  tests/unit/test_schema_files.py
  ```
- `git log -1 --format=%B` → `feat(schemas): cliente, depósito e saque, com o teste dos arquivos de schema`

**Pronto quando:**
- [ ] `tests/unit/` existe, com `__init__.py` vazio e `test_schema_files.py`.
- [ ] Os 16 testes falharam antes dos schemas e passam depois.
- [ ] A S3 dá a linha do **Verificar**.
- [ ] Suíte com `22 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/03-contrato`.

**Commit:** `feat(schemas): cliente, depósito e saque, com o teste dos arquivos de schema`
**Pare se:**
- O item 3 não terminar com `16 failed`, ou alguma falha não for `AssertionError`.
- A S3 começar com outro nome que não `Draft4Validator`, ou terminar com `Traceback` (`SchemaError` = um schema não vale no draft 4).
- A S3 der outra lista depois de 3 tentativas de conferir os arquivos contra o plano.
- A suíte não terminar com `22 passed`.

---
### Passo 3.4 — Schemas da transferência e das listas
**Branch:** fase/03-contrato · **Depende de:** 3.3
**Objetivo:** `post_transfers.json`, `get_entries.json`, `get_categories.json` e `get_piggy_bank_entries.json`; `limit` de 1 a 100 (o `pattern` do base aceitava `0`).
**Decisões:** MOV-04 — envelope do extrato (`limit` padrão 10 e máximo 100; `page` a partir de 0) · MOV-12 — idempotência · API-03 — schema fechado · API-18 — valor inteiro ≥ 1 · COF-05 — extrato do cofrinho por categoria
**Arquivos:**

Os schemas de query string (`get_*`) têm todo campo em `"type": "string"`, como o `get_sample_entities.json` do base: a query string chega como texto, e o resource converte com `int()` depois da validação. Sem `required`: `limit` e `page` têm padrão (10 e 0), e `category_key` é filtro opcional.

- `tests/unit/test_schema_files.py` (editar): uma troca só, no fim do dicionário `EXPECTED_SCHEMAS`.
  - Antes (uma linha):

```python
}  # fim de EXPECTED_SCHEMAS
```

  - Depois (as linhas novas e, por último, a mesma linha de antes):

```python
    "post_transfers.json": {
        "title": "PostTransfers",
        "fields": ["destination_account_key", "amount", "request_control_key"],
        "required": ["destination_account_key", "amount", "request_control_key"],
    },
    "get_entries.json": {
        "title": "GetEntries",
        "fields": ["limit", "page"],
        "required": [],
    },
    "get_categories.json": {
        "title": "GetCategories",
        "fields": ["limit", "page"],
        "required": [],
    },
    "get_piggy_bank_entries.json": {
        "title": "GetPiggyBankEntries",
        "fields": ["limit", "page", "category_key"],
        "required": [],
    },
}  # fim de EXPECTED_SCHEMAS
```

- `src/schemas/post_transfers.json` (criar): o conteúdo inteiro é:

```json
{
  "$schema": "http://json-schema.org/draft-04/schema#",
  "title": "PostTransfers",
  "type": "object",
  "properties": {
    "destination_account_key": {
      "type": "string",
      "minLength": 36,
      "maxLength": 36,
      "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    },
    "amount": {
      "type": "integer",
      "minimum": 1,
      "maximum": 9223372036854775807
    },
    "request_control_key": {
      "type": "string",
      "minLength": 36,
      "maxLength": 36,
      "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    }
  },
  "required": [
    "destination_account_key",
    "amount",
    "request_control_key"
  ],
  "additionalProperties": false
}
```

- `src/schemas/get_entries.json` (criar): o conteúdo inteiro é:

```json
{
  "$schema": "http://json-schema.org/draft-04/schema#",
  "title": "GetEntries",
  "type": "object",
  "properties": {
    "limit": {
      "type": "string",
      "pattern": "^(100|[1-9][0-9]?)$"
    },
    "page": {
      "type": "string",
      "pattern": "^[0-9]{1,9}$"
    }
  },
  "additionalProperties": false
}
```

- `src/schemas/get_categories.json` (criar): o conteúdo inteiro é:

```json
{
  "$schema": "http://json-schema.org/draft-04/schema#",
  "title": "GetCategories",
  "type": "object",
  "properties": {
    "limit": {
      "type": "string",
      "pattern": "^(100|[1-9][0-9]?)$"
    },
    "page": {
      "type": "string",
      "pattern": "^[0-9]{1,9}$"
    }
  },
  "additionalProperties": false
}
```

- `src/schemas/get_piggy_bank_entries.json` (criar): o conteúdo inteiro é:

```json
{
  "$schema": "http://json-schema.org/draft-04/schema#",
  "title": "GetPiggyBankEntries",
  "type": "object",
  "properties": {
    "limit": {
      "type": "string",
      "pattern": "^(100|[1-9][0-9]?)$"
    },
    "page": {
      "type": "string",
      "pattern": "^[0-9]{1,9}$"
    },
    "category_key": {
      "type": "string",
      "minLength": 36,
      "maxLength": 36,
      "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    }
  },
  "additionalProperties": false
}
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/03-contrato`; `git log --oneline -n 3` → mostra `feat(schemas): cliente, depósito e saque, com o teste dos arquivos de schema`.
2. Edite `tests/unit/test_schema_files.py` como no campo **Arquivos**.
3. `./.venv/Scripts/python.exe -m pytest -v tests/unit/test_schema_files.py` → a última linha tem `21 failed` e `15 passed`; as falhas são `AssertionError` dos 4 arquivos novos e de `test_schema_folder_has_exactly_the_expected_files`.
4. Crie os 4 schemas com o conteúdo do campo **Arquivos**.
5. `./.venv/Scripts/python.exe -m pytest -v tests/unit/test_schema_files.py` → a última linha tem `36 passed`.
6. `docker compose up -d --build --wait`.
7. Rode a conferência S4 (abaixo) → a saída do **Verificar**.
8. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `42 passed`.
9. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
10. Feche o passo (AGENTS.md, seção 7), um comando por vez:
    ```
    git add -- tests/unit/test_schema_files.py src/schemas/post_transfers.json src/schemas/get_entries.json src/schemas/get_categories.json src/schemas/get_piggy_bank_entries.json
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "feat(schemas): transferência e listas paginadas"
    git log -1 --format=%B
    ```

Conferência S4 (um comando, numa linha só; mesma ideia da S3):

```
docker compose exec -T api python -c "import os, json; from constants import SCHEMA_PATH; from jsonschema.validators import validator_for; ld = lambda n: json.load(open(os.path.join(SCHEMA_PATH, n), encoding='utf-8')); c = lambda n, xs: (lambda s: (validator_for(s).check_schema(s), [validator_for(s)(s).is_valid(x) for x in xs])[1])(ld(n)); k = '1b2c3d4e-5f6a-4b7c-8d9e-0f1a2b3c4d5e'; print(c('get_entries.json', [{}, {'limit': '1', 'page': '0'}, {'limit': '100'}, {'limit': '0'}, {'limit': '101'}, {'limit': '-1'}, {'limit': 'abc'}, {'page': '-3'}, {'size': '10'}]), c('get_categories.json', [{'limit': '100'}, {'limit': '0'}]), c('get_piggy_bank_entries.json', [{'category_key': k}, {'category_key': 'economias'}]), c('post_transfers.json', [{'destination_account_key': k, 'amount': 1, 'request_control_key': k}, {'destination_account_key': k, 'amount': 1}]))"
```

Os casos, na ordem: extrato sem query; `limit=1&page=0`; `limit=100`; `limit=0`; `limit=101`; `limit=-1`; `limit=abc`; `page=-3`; campo `size` · categorias com `limit=100`; com `limit=0` · extrato do cofrinho com `category_key` UUID; com `category_key=economias` · transferência válida; sem `request_control_key`.

**Testes:** `tests/unit/test_schema_files.py`, os mesmos 6 testes do passo 3.3 (tabela de lá). `EXPECTED_SCHEMAS` passa a ter 7 arquivos: 1 + 5 × 7 = 36 testes. Antes dos schemas: `21 failed` (o teste da pasta e os 5 de cada arquivo novo) e `15 passed`. Depois: `36 passed`. Suíte: 6 + 36 = 42.
**Verificar:**
- S4 → exatamente:
  ```
  [True, True, True, False, False, False, False, False, False] [True, False] [True, False] [True, False]
  ```
- `./.venv/Scripts/python.exe -m pytest tests/unit` → a última linha tem `36 passed`.
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `42 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/schemas/get_categories.json
  src/schemas/get_entries.json
  src/schemas/get_piggy_bank_entries.json
  src/schemas/post_transfers.json
  tests/unit/test_schema_files.py
  ```
- `git log -1 --format=%B` → `feat(schemas): transferência e listas paginadas`

**Pronto quando:**
- [ ] Os 4 schemas existem, iguais ao plano.
- [ ] Os testes novos falharam antes dos schemas e passam depois.
- [ ] A S4 dá a linha do **Verificar**.
- [ ] Suíte com `42 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/03-contrato`.

**Commit:** `feat(schemas): transferência e listas paginadas`
**Pare se:**
- O item 3 não terminar com `21 failed` e `15 passed`.
- A S4 der outra lista depois de 3 tentativas de conferir os arquivos contra o plano, ou terminar com `Traceback`.
- A suíte não terminar com `42 passed`.

---
### Passo 3.5 — Schemas do cofrinho, das categorias e dos pontos
**Branch:** fase/03-contrato · **Depende de:** 3.4
**Objetivo:** `post_savings.json`, `post_redemptions.json`, `post_categories.json` e `post_point_applications.json`.
**Decisões:** COF-03 — categorias (sem `category_key`, vale "economias") · COF-10 — guardar e resgatar · COF-18 — nome da categoria · GAM-21 — aplicar e zerar (sem chave de idempotência) · MOV-12 — idempotência · API-18 — valor inteiro ≥ 1 · R6 — sem float
**Arquivos:**

`points` é `"type": "integer"` e `"minimum": 1`, sem máximo: pedir mais pontos do que os livres é regra de negócio, 422 `QIT001027` no controller (fase 8). `benefit` aceita só `FEE` e `CHANCE`, em maiúsculas, como os valores do banco.

- `tests/unit/test_schema_files.py` (editar): uma troca só, no fim do dicionário `EXPECTED_SCHEMAS`.
  - Antes (uma linha):

```python
}  # fim de EXPECTED_SCHEMAS
```

  - Depois (as linhas novas e, por último, a mesma linha de antes):

```python
    "post_savings.json": {
        "title": "PostSavings",
        "fields": ["amount", "request_control_key", "category_key"],
        "required": ["amount", "request_control_key"],
    },
    "post_redemptions.json": {
        "title": "PostRedemptions",
        "fields": ["amount", "request_control_key", "category_key"],
        "required": ["amount", "request_control_key"],
    },
    "post_categories.json": {
        "title": "PostCategories",
        "fields": ["name"],
        "required": ["name"],
    },
    "post_point_applications.json": {
        "title": "PostPointApplications",
        "fields": ["benefit", "points"],
        "required": ["benefit", "points"],
    },
}  # fim de EXPECTED_SCHEMAS
```

- `src/schemas/post_savings.json` (criar): o conteúdo inteiro é:

```json
{
  "$schema": "http://json-schema.org/draft-04/schema#",
  "title": "PostSavings",
  "type": "object",
  "properties": {
    "amount": {
      "type": "integer",
      "minimum": 1,
      "maximum": 9223372036854775807
    },
    "request_control_key": {
      "type": "string",
      "minLength": 36,
      "maxLength": 36,
      "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    },
    "category_key": {
      "type": "string",
      "minLength": 36,
      "maxLength": 36,
      "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    }
  },
  "required": [
    "amount",
    "request_control_key"
  ],
  "additionalProperties": false
}
```

- `src/schemas/post_redemptions.json` (criar): o conteúdo inteiro é:

```json
{
  "$schema": "http://json-schema.org/draft-04/schema#",
  "title": "PostRedemptions",
  "type": "object",
  "properties": {
    "amount": {
      "type": "integer",
      "minimum": 1,
      "maximum": 9223372036854775807
    },
    "request_control_key": {
      "type": "string",
      "minLength": 36,
      "maxLength": 36,
      "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    },
    "category_key": {
      "type": "string",
      "minLength": 36,
      "maxLength": 36,
      "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    }
  },
  "required": [
    "amount",
    "request_control_key"
  ],
  "additionalProperties": false
}
```

- `src/schemas/post_categories.json` (criar): o conteúdo inteiro é:

```json
{
  "$schema": "http://json-schema.org/draft-04/schema#",
  "title": "PostCategories",
  "type": "object",
  "properties": {
    "name": {
      "type": "string",
      "minLength": 1,
      "maxLength": 255
    }
  },
  "required": [
    "name"
  ],
  "additionalProperties": false
}
```

- `src/schemas/post_point_applications.json` (criar): o conteúdo inteiro é:

```json
{
  "$schema": "http://json-schema.org/draft-04/schema#",
  "title": "PostPointApplications",
  "type": "object",
  "properties": {
    "benefit": {
      "type": "string",
      "enum": [
        "FEE",
        "CHANCE"
      ]
    },
    "points": {
      "type": "integer",
      "minimum": 1
    }
  },
  "required": [
    "benefit",
    "points"
  ],
  "additionalProperties": false
}
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/03-contrato`; `git log --oneline -n 3` → mostra `feat(schemas): transferência e listas paginadas`.
2. Edite `tests/unit/test_schema_files.py` como no campo **Arquivos**.
3. `./.venv/Scripts/python.exe -m pytest -v tests/unit/test_schema_files.py` → a última linha tem `21 failed` e `35 passed`; as falhas são `AssertionError` dos 4 arquivos novos e de `test_schema_folder_has_exactly_the_expected_files`.
4. Crie os 4 schemas com o conteúdo do campo **Arquivos**.
5. `./.venv/Scripts/python.exe -m pytest -v tests/unit/test_schema_files.py` → a última linha tem `56 passed`.
6. `docker compose up -d --build --wait`.
7. Rode a conferência S5 (abaixo) → a saída do **Verificar**.
8. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `62 passed`.
9. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
10. Feche o passo (AGENTS.md, seção 7), um comando por vez:
    ```
    git add -- tests/unit/test_schema_files.py src/schemas/post_savings.json src/schemas/post_redemptions.json src/schemas/post_categories.json src/schemas/post_point_applications.json
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "feat(schemas): cofrinho, categorias e pontos"
    git log -1 --format=%B
    ```

Conferência S5 (um comando, numa linha só; mesma ideia da S3):

```
docker compose exec -T api python -c "import os, json; from constants import SCHEMA_PATH; from jsonschema.validators import validator_for; ld = lambda n: json.load(open(os.path.join(SCHEMA_PATH, n), encoding='utf-8')); c = lambda n, xs: (lambda s: (validator_for(s).check_schema(s), [validator_for(s)(s).is_valid(x) for x in xs])[1])(ld(n)); k = '1b2c3d4e-5f6a-4b7c-8d9e-0f1a2b3c4d5e'; print(c('post_savings.json', [{'amount': 100, 'request_control_key': k}, {'amount': 100, 'request_control_key': k, 'category_key': k}, {'amount': 100, 'request_control_key': k, 'category_key': 'economias'}]), c('post_redemptions.json', [{'amount': 100, 'request_control_key': k}, {'amount': 1.5, 'request_control_key': k}]), c('post_categories.json', [{'name': 'carro'}, {'name': ''}, {}]), c('post_point_applications.json', [{'benefit': 'FEE', 'points': 1}, {'benefit': 'fee', 'points': 1}, {'benefit': 'CHANCE', 'points': 0}, {'benefit': 'CHANCE', 'points': 1.0}, {'benefit': 'CHANCE'}]))"
```

Os casos, na ordem: guardar sem categoria; com `category_key` UUID; com `category_key=economias` · resgatar válido; `amount` `1.5` · categoria `carro`; nome vazio; sem `name` · `FEE` com 1 ponto; `fee` minúsculo; `CHANCE` com 0; `points` `1.0`; sem `points`.

**Testes:** `tests/unit/test_schema_files.py`, os mesmos 6 testes do passo 3.3. `EXPECTED_SCHEMAS` passa a ter 11 arquivos: 1 + 5 × 11 = 56 testes. Antes dos schemas: `21 failed` e `35 passed`. Depois: `56 passed`. Suíte: 6 + 56 = 62.
**Verificar:**
- S5 → exatamente:
  ```
  [True, True, False] [True, False] [True, False, False] [True, False, False, False, False]
  ```
- `./.venv/Scripts/python.exe -m pytest tests/unit` → a última linha tem `56 passed`.
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `62 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/schemas/post_categories.json
  src/schemas/post_point_applications.json
  src/schemas/post_redemptions.json
  src/schemas/post_savings.json
  tests/unit/test_schema_files.py
  ```
- `git log -1 --format=%B` → `feat(schemas): cofrinho, categorias e pontos`

**Pronto quando:**
- [ ] Os 4 schemas existem, iguais ao plano.
- [ ] Os testes novos falharam antes dos schemas e passam depois.
- [ ] A S5 dá a linha do **Verificar**.
- [ ] Suíte com `62 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/03-contrato`.

**Commit:** `feat(schemas): cofrinho, categorias e pontos`
**Pare se:**
- O item 3 não terminar com `21 failed` e `35 passed`.
- A S5 der outra lista depois de 3 tentativas de conferir os arquivos contra o plano, ou terminar com `Traceback`.
- A suíte não terminar com `62 passed`.

---
### Passo 3.6 — Schemas das rotas internas
**Branch:** fase/03-contrato · **Depende de:** 3.5
**Objetivo:** `post_day_closings.json` e `post_blocks.json`; com eles, os 13 schemas do registro.
**Decisões:** DIA-05 — data da virada · CLI-05 — estados da conta · CLI-08 — motivos do bloqueio · API-13 — rotas `/internal` · API-03 — schema fechado
**Arquivos:**

`accounting_date` confere só o formato: data que não existe no calendário (`2026-02-30`) passa no schema e sai como 422 `QIT001030` no controller (fase 7). `reason` aceita só os 4 valores de `block_reason`.

- `tests/unit/test_schema_files.py` (editar): uma troca só, no fim do dicionário `EXPECTED_SCHEMAS`.
  - Antes (uma linha):

```python
}  # fim de EXPECTED_SCHEMAS
```

  - Depois (as linhas novas e, por último, a mesma linha de antes):

```python
    "post_day_closings.json": {
        "title": "PostDayClosings",
        "fields": ["accounting_date"],
        "required": ["accounting_date"],
    },
    "post_blocks.json": {
        "title": "PostBlocks",
        "fields": ["reason"],
        "required": ["reason"],
    },
}  # fim de EXPECTED_SCHEMAS
```

- `src/schemas/post_day_closings.json` (criar): o conteúdo inteiro é:

```json
{
  "$schema": "http://json-schema.org/draft-04/schema#",
  "title": "PostDayClosings",
  "type": "object",
  "properties": {
    "accounting_date": {
      "type": "string",
      "minLength": 10,
      "maxLength": 10,
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    }
  },
  "required": [
    "accounting_date"
  ],
  "additionalProperties": false
}
```

- `src/schemas/post_blocks.json` (criar): o conteúdo inteiro é:

```json
{
  "$schema": "http://json-schema.org/draft-04/schema#",
  "title": "PostBlocks",
  "type": "object",
  "properties": {
    "reason": {
      "type": "string",
      "enum": [
        "SUSPICIOUS_ACTIVITY",
        "JUDICIAL_ORDER",
        "CUSTOMER_REQUEST",
        "MANUAL_REVIEW"
      ]
    }
  },
  "required": [
    "reason"
  ],
  "additionalProperties": false
}
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/03-contrato`; `git log --oneline -n 3` → mostra `feat(schemas): cofrinho, categorias e pontos`.
2. Edite `tests/unit/test_schema_files.py` como no campo **Arquivos**.
3. `./.venv/Scripts/python.exe -m pytest -v tests/unit/test_schema_files.py` → a última linha tem `11 failed` e `55 passed`; as falhas são `AssertionError` dos 2 arquivos novos e de `test_schema_folder_has_exactly_the_expected_files`.
4. Crie os 2 schemas com o conteúdo do campo **Arquivos**.
5. `./.venv/Scripts/python.exe -m pytest -v tests/unit/test_schema_files.py` → a última linha tem `66 passed`.
6. `docker compose up -d --build --wait`.
7. Rode a conferência S6 (abaixo) → a saída do **Verificar**.
8. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `72 passed`.
9. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
10. Feche o passo (AGENTS.md, seção 7), um comando por vez:
    ```
    git add -- tests/unit/test_schema_files.py src/schemas/post_day_closings.json src/schemas/post_blocks.json
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "feat(schemas): rotas internas de bloqueio e virada do dia"
    git log -1 --format=%B
    ```

Conferência S6 (um comando, numa linha só; mesma ideia da S3):

```
docker compose exec -T api python -c "import os, json; from constants import SCHEMA_PATH; from jsonschema.validators import validator_for; ld = lambda n: json.load(open(os.path.join(SCHEMA_PATH, n), encoding='utf-8')); c = lambda n, xs: (lambda s: (validator_for(s).check_schema(s), [validator_for(s)(s).is_valid(x) for x in xs])[1])(ld(n)); k = '1b2c3d4e-5f6a-4b7c-8d9e-0f1a2b3c4d5e'; print(c('post_day_closings.json', [{'accounting_date': '2026-06-01'}, {'accounting_date': '2026-6-1'}, {'accounting_date': '2026-06-01\n'}, {}]), c('post_blocks.json', [{'reason': 'JUDICIAL_ORDER'}, {'reason': 'OTHER'}, {}]))"
```

Os casos, na ordem: virada de `2026-06-01`; `2026-6-1`; `2026-06-01` com quebra de linha no fim; sem `accounting_date` · bloqueio por `JUDICIAL_ORDER`; por `OTHER`; sem `reason`.

**Testes:** `tests/unit/test_schema_files.py`, os mesmos 6 testes do passo 3.3. `EXPECTED_SCHEMAS` passa a ter os 13 arquivos: 1 + 5 × 13 = 66 testes. Antes dos schemas: `11 failed` e `55 passed`. Depois: `66 passed`. Suíte: 6 + 66 = 72.
**Verificar:**
- S6 → exatamente:
  ```
  [True, False, False, False] [True, False, False]
  ```
- `./.venv/Scripts/python.exe -m pytest tests/unit` → a última linha tem `66 passed`.
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `72 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/schemas/post_blocks.json
  src/schemas/post_day_closings.json
  tests/unit/test_schema_files.py
  ```
- `git ls-files src/schemas` (depois do commit) → exatamente:
  ```
  src/schemas/get_categories.json
  src/schemas/get_entries.json
  src/schemas/get_piggy_bank_entries.json
  src/schemas/post_blocks.json
  src/schemas/post_categories.json
  src/schemas/post_customers.json
  src/schemas/post_day_closings.json
  src/schemas/post_deposits.json
  src/schemas/post_point_applications.json
  src/schemas/post_redemptions.json
  src/schemas/post_savings.json
  src/schemas/post_transfers.json
  src/schemas/post_withdrawals.json
  ```
- `git log -1 --format=%B` → `feat(schemas): rotas internas de bloqueio e virada do dia`

**Pronto quando:**
- [ ] Os 13 schemas do registro existem, iguais ao plano.
- [ ] Os testes novos falharam antes dos schemas e passam depois.
- [ ] A S6 dá a linha do **Verificar**.
- [ ] Suíte com `72 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/03-contrato`.

**Commit:** `feat(schemas): rotas internas de bloqueio e virada do dia`
**Pare se:**
- O item 3 não terminar com `11 failed` e `55 passed`.
- A S6 der outra lista depois de 3 tentativas de conferir os arquivos contra o plano, ou terminar com `Traceback`.
- A suíte não terminar com `72 passed`.

---
### Passo 3.fim — Fechar a fase
**Branch:** fase/03-contrato · **Depende de:** 3.1 a 3.6
**Objetivo:** provar a fase com o banco recriado do zero e levá-la para a `main` com a tag `fase-03`.
**Decisões:** TIM-04 — git por fase · TIM-08 — git automático · ARQ-03 — SQL só com o banco vazio · API-12 — catálogo fecha com o contrato
**Arquivos:** nenhum. O passo não cria, não edita e não apaga arquivo.
**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/03-contrato`.
2. `git log --oneline -n 10` → tem as 6 mensagens dos passos 3.1 a 3.6, cada uma uma vez:
   ```
   docs(contrato): tabela de rotas com tokens, respostas, erros e idempotência
   feat(erros): catálogo de erros do projeto
   feat(schemas): cliente, depósito e saque, com o teste dos arquivos de schema
   feat(schemas): transferência e listas paginadas
   feat(schemas): cofrinho, categorias e pontos
   feat(schemas): rotas internas de bloqueio e virada do dia
   ```
3. Recrie o banco do zero e suba tudo, um comando por vez:
   ```
   docker compose down -v
   docker compose up -d --build --wait
   ```
4. Rode a conferência R1 (passo 3.1) → `25 25 31 0 1`.
5. Rode a conferência E1 (passo 3.2) → a linha de 39 códigos do **Verificar** do passo 3.2.
6. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `72 passed`.
7. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
8. `git status --short` → saída vazia.
9. Leve a fase para a `main`, um comando por vez:
   ```
   git switch main
   git merge --no-ff --no-edit -m "feat(contrato): fase 03 com rotas, catálogo de erros e schemas" fase/03-contrato
   git tag fase-03
   ```
10. Rode o **Verificar**.

**Testes:** nenhum teste novo. A suíte inteira (6 de integração + 66 unitários) roda com o banco recriado do zero (item 6).
**Verificar:**
- O `git status --short` antes do merge não mostra alterações.
- `git branch --show-current` → `main`.
- `git log -1 --format=%B` → `feat(contrato): fase 03 com rotas, catálogo de erros e schemas`.
- `git log -1 --format=%P` → dois hashes separados por um espaço (é um merge).
- `git tag --list fase-03` → `fase-03`.
- `git status --short` → saída vazia.

**Pronto quando:**
- [ ] R1 e E1 dão o esperado com o banco recriado do zero.
- [ ] Suíte com `72 passed`; lint sem saída.
- [ ] Merge `--no-ff` na `main` com a mensagem exata; tag `fase-03` criada localmente; merge local na `main`.

**Commit:** nenhum commit de passo. Mensagem do merge: `feat(contrato): fase 03 com rotas, catálogo de erros e schemas`
**Pare se:**
- Faltar uma das 6 mensagens do item 2.
- `docker compose up -d --build --wait` falhar: rode `docker compose logs --tail 100 db` e `docker compose logs --tail 100 api` e traga as duas saídas.
- A R1 ou a E1 der outra saída.
- A suíte não terminar com `72 passed` ou o lint imprimir qualquer linha.
- O merge local der conflito (AGENTS.md, seção 8, item 9).

---

## Nomes novos da fase 03 (registrar no PLANO-00)

Seção para o Bruno; o agente não executa nada daqui.

| Onde | Nomes |
|---|---|
| Campos de resposta (`docs/rotas.md`) | `account_token` · `piggy_bank_balance`, `piggy_bank_gross_yield`, `piggy_bank_net_yield`, `yield_accounting_date` (9.9) · categoria: `gross_yield`, `net_yield`, `yield_accounting_date` (9.9) · `gross_amount`, `iof`, `ir`, `net_amount` (resgate e `GET` de operação `REDEEM`) · `entries` (no `GET` da operação) · item do extrato: `entry_key`, `transaction_key`, `transaction_type`, `entry_type`, `amount`, `balance_after`, `category`, `counterparty`, `accounting_date`, `created_at` · gamificação: `level`, `xp`, `xp_to_next_level`, `points_free`, `points_fee`, `points_chance`, `fee_percent`, `chance_percent`, `rank`, `cdi_percent`, `piggy_record`, `grace_until` · categoria: `category_key`, `name`, `is_default`, `status`, `balance`, `created_at` · virada: `closed_date`, `accounting_date` |
| `counterparty.type` | `CUSTOMER`, `DEPOSITOR`, `BANK`, `PIGGY_BANK`, `ACCOUNT` (saque: `counterparty` nulo) |
| Formatos | CNPJ mascarado `**.222.333/****-**` (6.2) · token da conta `secrets.token_urlsafe(32)` (5.4) · percentuais em texto (`"0.9"`) · valores fixos em maiúsculas na resposta |
| Idempotência | "mesmo pedido" = mesma `account_key` da URL e mesmo corpo: `hash_request_body` (6.4) recebe a `account_key` e o corpo |
| Erros | parâmetros do `__init__` de cada classe: tabela do passo 3.2 · `InvalidDocumentNumber()` e `DuplicatedDocumentNumber()` sem parâmetro |
| Schemas | `"$schema": "http://json-schema.org/draft-04/schema#"` em todos · `amount` com `"maximum": 9223372036854775807` · keys só em minúsculas, 36 caracteres |
| Teste | `tests/unit/test_schema_files.py`: `EXPECTED_SCHEMAS`, `FIELD_RULES` (schema novo em fase futura entra nos dois) |
