# Catálogo de erros

Os 40 códigos definidos pela API Score, organizados por categoria. Cada entrada
informa o status HTTP, a condição de recusa e os textos de `title`,
`description` e `translation`. Para saber quais erros se aplicam a cada
requisição, consulte o [contrato de rotas](rotas.md#resumo).

Os nomes das classes e as mensagens correspondem à implementação em
[`base_error.py`](../src/errors/base_error.py) e
[`custom_errors.py`](../src/errors/custom_errors.py).
Marcadores entre chaves, como `{account_key}`, são substituídos pelos valores
da requisição ou do estado consultado. Em `QIT000001` e `QIT000010`,
`{description}` é o texto produzido pela validação, sem uma frase única fixa.

## Formato da resposta

O status HTTP vem na resposta; o corpo contém estes quatro campos:

```json
{
  "title": "Same account transfer",
  "description": "The destination account must be different from the origin account.",
  "translation": "A conta de destino precisa ser diferente da conta de origem.",
  "code": "QIT001016"
}
```

Ao tratar uma falha, use o código e o status HTTP. Mensagens com parâmetros
variam de uma requisição para outra.

## Consulta por status HTTP

| Status | Significado no Score |
|---|---|
| 400 | Formato ou parâmetros inválidos |
| 403 | Token interno ou administrativo inválido/ausente |
| 404 | Rota ou recurso inexistente; nas rotas do titular, também ausência de acesso |
| 405 | Método HTTP não aceito pela rota |
| 409 | Duplicidade, conflito de idempotência ou estado que impede a ação |
| 422 | Regra de negócio, data/documento inválido ou limite numérico |
| 429 | Tentativas de autenticação demais na janela configurada |
| 500 | Erro inesperado da aplicação |
| 503 | Banco ou CDI indisponível/lento |

O token da conta ausente ou de outro dono responde 404, com o código do
recurso consultado, para não revelar sua existência. O `QIT000010` está
incluído para completar o catálogo herdado do base; não é uma resposta
esperada das rotas atuais.

## Categorias

| Categoria | Códigos |
|---|---|
| [Formato e roteamento](#formato-e-roteamento) | 4 |
| [Autenticação e proteção contra tentativas](#autenticacao-e-protecao-contra-tentativas) | 3 |
| [Infraestrutura e limites numéricos](#infraestrutura-e-limites-numericos) | 4 |
| [Clientes](#clientes) | 6 |
| [Contas](#contas) | 5 |
| [Movimentações e idempotência](#movimentacoes-e-idempotencia) | 7 |
| [Cofrinho e categorias](#cofrinho-e-categorias) | 6 |
| [Gamificação](#gamificacao) | 1 |
| [Fechamento do dia](#fechamento-do-dia) | 4 |

<a id="formato-e-roteamento"></a>

## Formato e roteamento

### QIT000001 — InvalidSchema

**HTTP 400.** Corpo ou query string fora do contrato: schema inválido, campos extras, JSON inválido ou corpo em rota que não aceita corpo.

- `title`: `Bad Request`
- `description`: `{description}`
- `translation`: `Payload Inválido`

### QIT000010 — InvalidParameter

**HTTP 400.** Validação de parâmetro tipado do caminho ou da query pelo FastAPI. Erro herdado do base; o ramo não é alcançado pelas rotas atuais, que usam caminhos em texto e JSON Schema.

- `title`: `Invalid Parameter`
- `description`: `{description}`
- `translation`: `Parâmetros inválidos foram fornecidos na requisição.`

### QIT000404 — NotFoundResource

**HTTP 404.** Caminho solicitado não corresponde a uma rota registrada.

- `title`: `Resource not Found`
- `description`: `The requested resource could not be found but may be available in the future. Subsequent requests by the client are permissible.`
- `translation`: `O resource solicitado não pode ser encontrado, mas pode estar disponível no futuro. Requests subsequentes do cliente são permitidos.`

### QIT000405 — MethodNotAllowed

**HTTP 405.** O caminho existe, mas não aceita o método HTTP utilizado.

- `title`: `Method not allowed`
- `description`: `The requested method is forbidden for this resource.`
- `translation`: `O método desejado não foi encontrado para esse recurso.`

<a id="autenticacao-e-protecao-contra-tentativas"></a>

## Autenticação e proteção contra tentativas

### QIT000002 — ForbiddenNotInternal

**HTTP 403.** INTERNAL-TOKEN ausente ou incorreto. Não se aplica a GET / nem a GET /health_check.

- `title`: `Forbidden`
- `description`: `Request must be internal`
- `translation`: `Requisição precisa ser interna`

### QIT000003 — ForbiddenNotAdmin

**HTTP 403.** ADMIN-TOKEN ausente ou incorreto em uma rota /internal, após a conferência do token interno.

- `title`: `Forbidden`
- `description`: `Request must carry a valid admin token`
- `translation`: `Requisição precisa do token de administração`

### QIT000429 — TooManyAuthFailures

**HTTP 429.** Limite de falhas de autenticação atingido na janela configurada. A barreira responde antes de conferir os tokens, mesmo que a tentativa atual use um token correto.

- `title`: `Too Many Requests`
- `description`: `Too many failed token attempts from this client. Try again later.`
- `translation`: `Tentativas demais com token errado. Tente de novo mais tarde.`

<a id="infraestrutura-e-limites-numericos"></a>

## Infraestrutura e limites numéricos

### QIT000500 — InternalError

**HTTP 500.** Erro inesperado da aplicação. Não representa uma recusa prevista de regra de negócio.

- `title`: `Internal Error`
- `description`: `An internal error has occurred and its being investigated.`
- `translation`: `Um erro interno aconteceu e está sendo investigado.`

### QIT000503 — DatabaseTimeout

**HTTP 503.** PostgreSQL excedeu o tempo de espera por trava ou de execução do comando (lock_timeout ou statement_timeout). A transação é desfeita.

- `title`: `Service Unavailable`
- `description`: `The database took too long to answer.`
- `translation`: `O banco de dados demorou demais para responder.`

### QIT000504 — DatabaseUnavailable

**HTTP 503.** Conexão com PostgreSQL recusada, perdida ou indisponível. Nenhuma movimentação parcial é confirmada.

- `title`: `Service Unavailable`
- `description`: `The database is unavailable.`
- `translation`: `O banco de dados está indisponível.`

### QIT001032 — NumericLimitExceeded

**HTTP 422.** Um valor acumulado ultrapassaria o limite de BIGINT. A operação ou virada é integralmente desfeita.

- `title`: `Numeric Limit Exceeded`
- `description`: `An accumulated value exceeds the BIGINT limit.`
- `translation`: `Um valor acumulado excede o limite numérico permitido.`

<a id="clientes"></a>

## Clientes

### QIT001003 — InvalidDocumentNumber

**HTTP 422.** CPF ou CNPJ com dígitos verificadores inválidos. Usado no cadastro do cliente e na validação do documento de quem deposita.

- `title`: `Invalid Document Number`
- `description`: `The document number is not a valid CPF or CNPJ.`
- `translation`: `O CPF ou CNPJ informado não é válido.`

### QIT001004 — DuplicatedDocumentNumber

**HTTP 409.** Já existe cliente com o CPF informado.

- `title`: `Document Number already registered`
- `description`: `There is already a customer with this document number.`
- `translation`: `Já existe um cadastro com este CPF.`

### QIT001005 — DuplicatedEmail

**HTTP 409.** Já existe cliente com o e-mail informado.

- `title`: `Email already registered`
- `description`: `There is already a customer with the email {email}.`
- `translation`: `Já existe um cadastro com este e-mail.`

### QIT001006 — UnderageCustomer

**HTTP 422.** Cliente não atingiu a idade mínima exigida (18 anos).

- `title`: `Customer is underage`
- `description`: `The customer is {age} years old, and the minimum is {minimum_age}.`
- `translation`: `É preciso ter pelo menos {minimum_age} anos.`

### QIT001007 — InvalidBirthdate

**HTTP 422.** Data de nascimento tem o formato esperado, mas não existe no calendário.

- `title`: `Invalid Birthdate`
- `description`: `The birthdate {birthdate} is not a real date.`
- `translation`: `A data de nascimento informada não existe.`

### QIT001008 — CustomerNotFound

**HTTP 404.** Cliente não encontrado. Na consulta, também responde quando o token da conta está ausente ou não dá acesso ao cliente.

- `title`: `Customer not Found`
- `description`: `Customer with key {customer_key} was not found.`
- `translation`: `O cliente com chave {customer_key} não foi encontrado.`

<a id="contas"></a>

## Contas

### QIT001009 — CustomerAlreadyHasAccount

**HTTP 409.** Cliente já possui uma conta que não está encerrada.

- `title`: `Customer already has an account`
- `description`: `Customer with key {customer_key} already has an account that is not closed.`
- `translation`: `O cliente já tem uma conta que não foi encerrada.`

### QIT001010 — AccountNotFound

**HTTP 404.** Conta não encontrada ou não pertencente a cliente. Nas rotas do titular, também responde quando o token está ausente ou não pertence à conta da URL.

- `title`: `Account not Found`
- `description`: `Account with key {account_key} was not found.`
- `translation`: `A conta com chave {account_key} não foi encontrada.`

### QIT001011 — AccountNotActive

**HTTP 409.** Estado da conta impede a ação. Movimentações recusam conta bloqueada ou encerrada; pontos e criação/exclusão de categorias recusam conta encerrada. Bloquear novamente ou encerrar conta inativa também usa este código.

- `title`: `Account is not active`
- `description`: `Account with key {account_key} is {status} and cannot do this operation.`
- `translation`: `A conta não está ativa: está bloqueada ou encerrada.`

### QIT001012 — AccountNotEmpty

**HTTP 409.** Encerramento solicitado com dinheiro no saldo da conta ou no cofrinho.

- `title`: `Account is not empty`
- `description`: `Account with key {account_key} has money in its balance or in its piggy bank.`
- `translation`: `A conta só pode ser encerrada com o saldo e o cofrinho zerados.`

### QIT001013 — AccountNotBlocked

**HTTP 409.** Desbloqueio solicitado para conta que não está bloqueada.

- `title`: `Account is not blocked`
- `description`: `Account with key {account_key} is {status}, not BLOCKED.`
- `translation`: `Só uma conta bloqueada pode ser desbloqueada.`

<a id="movimentacoes-e-idempotencia"></a>

## Movimentações e idempotência

### QIT001014 — IdempotencyKeyConflict

**HTTP 409.** A mesma request_control_key já foi usada com outro pedido. Vale para depósito, saque, transferência, guardar e resgatar.

- `title`: `Idempotency key conflict`
- `description`: `The request_control_key {request_control_key} was already used with a different request.`
- `translation`: `Esta chave de idempotência já foi usada com outro pedido.`

### QIT001015 — InsufficientBalance

**HTTP 422.** Saldo da conta insuficiente para saque, transferência ou aplicação no cofrinho. Na transferência, deve cobrir o valor e a tarifa.

- `title`: `Insufficient balance`
- `description`: `The balance of account {account_key} does not cover this operation.`
- `translation`: `O saldo não cobre o valor da operação (e a tarifa, na transferência).`

### QIT001016 — SameAccountTransfer

**HTTP 422.** Conta de destino é a mesma conta de origem.

- `title`: `Same account transfer`
- `description`: `The destination account must be different from the origin account.`
- `translation`: `A conta de destino precisa ser diferente da conta de origem.`

### QIT001017 — DestinationAccountNotFound

**HTTP 404.** Conta de destino não encontrada ou não pertencente a cliente.

- `title`: `Destination account not Found`
- `description`: `Destination account with key {account_key} was not found.`
- `translation`: `A conta de destino não foi encontrada.`

### QIT001018 — DestinationAccountNotActive

**HTTP 409.** Conta de destino bloqueada ou encerrada.

- `title`: `Destination account is not active`
- `description`: `Destination account with key {account_key} cannot receive money.`
- `translation`: `A conta de destino não está ativa: está bloqueada ou encerrada.`

### QIT001019 — DailyTransferLimitReached

**HTTP 422.** Limite diário de transferências enviadas atingido: a 11ª tentativa bloqueia a conta. O bloqueio é confirmado antes da resposta de recusa.

- `title`: `Daily transfer limit reached`
- `description`: `Account {account_key} reached the daily limit of transfers and was blocked.`
- `translation`: `O limite diário de transferências foi atingido, e a conta foi bloqueada.`

### QIT001020 — TransactionNotFound

**HTTP 404.** Operação não encontrada ou sem lançamento na conta indicada nem no cofrinho dela.

- `title`: `Transaction not Found`
- `description`: `Transaction with key {transaction_key} was not found.`
- `translation`: `A operação com chave {transaction_key} não foi encontrada.`

<a id="cofrinho-e-categorias"></a>

## Cofrinho e categorias

### QIT001021 — CategoryNotFound

**HTTP 404.** Categoria não encontrada no cofrinho da conta indicada.

- `title`: `Category not Found`
- `description`: `Category with key {category_key} was not found in this piggy bank.`
- `translation`: `A categoria com chave {category_key} não foi encontrada neste cofrinho.`

### QIT001022 — CategoryDeleted

**HTTP 409.** A categoria está excluída; não permite a ação solicitada.

- `title`: `Category is deleted`
- `description`: `Category with key {category_key} is deleted.`
- `translation`: `A categoria foi excluída.`

### QIT001023 — InsufficientCategoryBalance

**HTTP 422.** Valor do resgate ultrapassa o saldo da categoria.

- `title`: `Insufficient category balance`
- `description`: `The balance of category {category_key} does not cover this redemption.`
- `translation`: `O saldo da categoria não cobre o resgate.`

### QIT001024 — DuplicatedCategoryName

**HTTP 409.** Já existe categoria ativa com o mesmo nome no cofrinho.

- `title`: `Category name already registered`
- `description`: `There is already an active category named {name}.`
- `translation`: `Já existe uma categoria ativa com este nome.`

### QIT001025 — DefaultCategoryCannotBeDeleted

**HTTP 409.** Tentativa de excluir a categoria padrão economias.

- `title`: `Default category cannot be deleted`
- `description`: `Category with key {category_key} is the default category.`
- `translation`: `A categoria padrão (economias) não pode ser excluída.`

### QIT001026 — CategoryNotEmpty

**HTTP 409.** Tentativa de excluir categoria que ainda possui dinheiro.

- `title`: `Category is not empty`
- `description`: `Category with key {category_key} has money.`
- `translation`: `Só uma categoria zerada pode ser excluída.`

<a id="gamificacao"></a>

## Gamificação

### QIT001027 — NotEnoughFreePoints

**HTTP 422.** Quantidade de pontos solicitada ultrapassa os pontos livres.

- `title`: `Not enough free points`
- `description`: `Requested {requested} points, but only {free} are free.`
- `translation`: `Pontos livres insuficientes: pedidos {requested}, livres {free}.`

<a id="fechamento-do-dia"></a>

## Fechamento do dia

### QIT001028 — DayAlreadyClosed

**HTTP 409.** O dia contábil solicitado já foi fechado; o rendimento não é pago novamente.

- `title`: `Day already closed`
- `description`: `The day {accounting_date} is already closed.`
- `translation`: `O dia {accounting_date} já foi fechado.`

### QIT001029 — FutureAccountingDate

**HTTP 422.** Data solicitada está depois da data atual do relógio do banco.

- `title`: `Future accounting date`
- `description`: `The day {accounting_date} is after the bank date {current_date}.`
- `translation`: `O dia {accounting_date} ainda não chegou: o banco está em {current_date}.`

### QIT001030 — InvalidAccountingDate

**HTTP 422.** Data contábil tem o formato esperado, mas não existe no calendário.

- `title`: `Invalid accounting date`
- `description`: `The accounting date {accounting_date} is not a real date.`
- `translation`: `A data informada não existe no calendário.`

### QIT001031 — CdiUnavailable

**HTTP 503.** Taxa do CDI indisponível no serviço do Banco Central, representado pelo Mockserver na entrega e nos testes. A virada é desfeita e o dia não avança.

- `title`: `CDI rate unavailable`
- `description`: `The Central Bank did not answer the CDI rate for {accounting_date} in time.`
- `translation`: `O Banco Central não respondeu a taxa do CDI a tempo.`
