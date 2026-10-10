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

O [catálogo completo de erros](erros.md) reúne os 40 códigos definidos pela
API, agrupados por categoria, com status HTTP e mensagens. Este documento
lista os erros comuns abaixo e os específicos junto de cada rota.

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
| `QIT000504` | 503 | conexão com o banco recusada, perdida ou indisponível; nenhuma movimentação parcial é confirmada |

`QIT000504` (`DatabaseUnavailable`): `title` = `Service Unavailable`,
`description` = `The database is unavailable.`,
`translation` = `O banco de dados está indisponível.`.
`QIT000503` continua reservado ao timeout de trava/comando.

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
      "status": "ACTIVE",
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
      "status": "ACTIVE",
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

Tokens: conta. Uma categoria do cofrinho, ativa ou excluída. Excluída sai com `"status": "DELETED"` (API-15).

COF-28 (9.9): gross_yield/net_yield são rendimento em centavos, sem principal/resíduo; líquido estima resgate total desta categoria na yield_accounting_date, com COF-27.

Sucesso: 200

```json
{
  "category_key": "a7d2e9f6-8b4c-4d3a-be7f-6c5b4a3f2d10",
  "name": "carro",
  "is_default": false,
  "status": "DELETED",
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
