# Score — Bootcamp QI Tech 2026

Protótipo bancário do time João, Ana e Bruno Guimarães Duarte: cadastro de
clientes, abertura de contas, depósitos, saques, transferências com tarifa
e extratos paginados. A gamificação acrescenta XP, níveis, pontos e um
cofrinho com categorias, ranques e rendimento pelo CDI.

A API usa Python 3.11, FastAPI, SQLAlchemy 2 e PostgreSQL 16. Dinheiro é
representado em **centavos inteiros**: `5050` significa R$ 50,50.
Operações financeiras e seus lançamentos são gravados na mesma transação;
contas são travadas antes de atualizar o saldo, que nunca pode ficar negativo.

## Subir o projeto

No Windows, instale Docker Desktop com suporte a containers Linux. Para
rodar os testes localmente, tenha também Python 3.11. Execute os comandos
abaixo no PowerShell, na raiz do repositório.

```powershell
docker compose up -d --build --wait
```

O Compose fornece os valores padrão e **não exige `.env`**. O comando
reconstrói as imagens e espera os health checks antes de terminar.

| Serviço | Endereço local padrão | Papel |
|---|---|---|
| API | `http://127.0.0.1:3000` | Rotas bancárias |
| PostgreSQL | `127.0.0.1:5432` | Estado, saldos, operações, eventos e logs |
| Mockserver | `http://127.0.0.1:1080` | CDI histórico, incluído na imagem |

Na execução da entrega e da suíte, o CDI vem do Mockserver. Não é necessário
acesso ao Banco Central. O script de atualização dos dados em `scripts/`
é uma operação separada e não roda no Compose nem nos testes.

Confira a API:

```powershell
docker compose ps
curl.exe -i http://127.0.0.1:3000/health_check
```

O health check responde **204, sem corpo**, e não consulta o banco. Ele
mede se a API está de pé; não certifica a disponibilidade do PostgreSQL.

## Testes e lint

Prepare o ambiente de testes uma vez:

```powershell
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -r requirements-dev.txt
```

Antes de testar, ponha a imagem da API em dia e aguarde sua disponibilidade:

```powershell
docker compose up -d --build --wait
./.venv/Scripts/python.exe -m pytest
./.venv/Scripts/python.exe -m flake8 src tests
```

Todos os comandos são executados um por vez. A suíte usa
`http://127.0.0.1:3000` por padrão. Os testes de integração chamam a API
por HTTP; os unitários verificam cálculos e infraestrutura. Alguns cenários
limpam os dados pelo `DbUtils.rollback()`: use um banco de desenvolvimento
ou teste, sem dados que precisem ser preservados.

Para executar apenas um arquivo ou os testes unitários:

```powershell
./.venv/Scripts/python.exe -m pytest -v tests/integration/transactions/test_transfer.py
./.venv/Scripts/python.exe -m pytest tests/unit
```

Há provas de concorrência, idempotência e reconciliação em
`tests/integration/extras/`. Elas verificam disputas de saldo, transferências
cruzadas, pedidos repetidos e a correspondência entre extrato e saldo.

## Autenticação

| Cabeçalho | Uso |
|---|---|
| `INTERNAL-TOKEN` | Todas as rotas, exceto `/` e `/health_check`; padrão de estudo: `default_token` |
| `ACCOUNT-TOKEN` | Consulta e operações do titular; token da conta indicada na URL |
| `ADMIN-TOKEN` | Segundo token das rotas `/internal`; padrão de estudo: `default_admin_token` |

Cadastro, abertura de conta e depósito exigem apenas o token interno.
O token da conta sai **uma única vez**, na resposta de abertura; guarde-o
para as próximas chamadas. No banco fica somente seu hash SHA-256.
Token da conta ausente ou de outro dono retorna 404. Token interno ou
administrativo incorreto retorna 403; falhas repetidas podem levar a 429.

Tokens devem viajar nos cabeçalhos. Os logs próprios registram método,
caminho, status, duração e identificador, sem corpo, cabeçalhos ou query
string. O access log do Uvicorn está desativado nas duas inicializações.
Envie um `X-Request-ID` com até 64 letras, números, hífens ou sublinhados
para relacionar resposta e logs; valores fora desse formato são substituídos.

## Fluxo bancário: cliente → conta → depósito → transferência → extrato

As entradas e respostas completas estão no [contrato de rotas](docs/rotas.md#resumo).
Use dados fictícios e os campos descritos nos schemas.

| Ordem | Requisição | Entrada e resultado |
|---|---|---|
| 1 | `POST /customers` | Corpo com `name`, CPF formatado em `document_number`, `email` e `birthdate` (`YYYY-MM-DD`). Retorna 201 com `customer_key`. CPF e e-mail são únicos; idade mínima de 18 anos. |
| 2 | `POST /customers/{customer_key}/accounts` | Sem corpo. Retorna 201 com `account_key` e `account_token`. Cria também cofrinho e categoria “economias”. Repita 1 e 2 para criar o destinatário. |
| 3 | `POST /accounts/{account_key}/deposits` | Corpo com `amount`, `depositor_name`, `depositor_document` (CPF/CNPJ formatado válido) e `request_control_key`. Retorna 201 com `transaction_key`; não cobra tarifa. |
| 4 | `POST /accounts/{account_key}/transfers` | URL da origem e seu `ACCOUNT-TOKEN`. Corpo com `destination_account_key`, `amount` e `request_control_key`. Retorna 201 com `transaction_key` e `balance`. O saldo deve cobrir valor e tarifa; sem pontos, a tarifa é 1%, arredondada para cima em centavos. |
| 5 | `GET /accounts/{account_key}/entries?limit=10&page=0` | Token do titular. Retorna 200 com `data`, `limit`, `page` e `is_last_page`. Consulte origem e destino; avance `page` até a última página. |

Cada `request_control_key` é um UUID v4 novo para uma nova intenção.
A mesma chave com o mesmo pedido repete a resposta original sem movimentar
novamente. A mesma chave com outro pedido retorna 409 `QIT001014`.
Pedidos recusados não consomem a chave.

Valores monetários de entrada são inteiros positivos. Corpo e query string
têm schemas fechados: campos extras, JSON inválido, NUL e Unicode inválido
retornam 400 `QIT000001`. Acentos, apóstrofos e emojis válidos são aceitos.
O extrato começa na página 0, aceita `limit` de 1 a 100 e mascara documentos
de outras pessoas.

Para consultar uma conta com as chaves e o token obtidos na abertura:

```powershell
curl.exe -i "http://127.0.0.1:3000/accounts/CHAVE_DA_CONTA" -H "INTERNAL-TOKEN: default_token" -H "ACCOUNT-TOKEN: TOKEN_DA_CONTA"
```

Substitua os dois marcadores pelos valores da sua conta. As requisições
com corpo e os cenários de recusa estão demonstrados nos testes de
[clientes](tests/integration/customers/test_create_customer.py),
[contas](tests/integration/accounts/test_open_account.py),
[depósitos](tests/integration/transactions/test_deposit.py),
[transferências](tests/integration/transactions/test_transfer.py) e
[extratos](tests/integration/transactions/test_entries.py).

Outras rotas permitem saques, consulta de operações, aplicação e liberação
de pontos, categorias, guardar e resgatar. As rotas administrativas bloqueiam,
desbloqueiam e fecham o dia contábil. Consulte os contratos e regras de cada
uma em [docs/rotas.md](docs/rotas.md).

## Erros

Toda recusa responde com `title`, `description`, `translation` em português
e `code`. O status faz parte do contrato: 400 para formato, 403 para token
interno/admin, 404 para recurso ausente ou sem acesso, 409 para duplicidade
ou estado incompatível e 422 para regra de negócio.

O timeout de trava/comando do banco retorna 503 `QIT000503`; conexão com
o banco indisponível retorna 503 `QIT000504`; falha do CDI retorna
503 `QIT001031`. `QIT000500` representa erro inesperado.
O catálogo e os erros específicos estão em [docs/rotas.md](docs/rotas.md#erro)
e `src/errors/`.

## Configuração e diagnóstico

As configurações são lidas do ambiente por `src/constants.py`. Os padrões
do Compose permitem executar o projeto sem preparar arquivos. Consulte
[.env.example](.env.example) para as opções; valores de estudo não são
credenciais de produção. Nunca versione segredos ou o `.env`.

Se alterar portas, mantenha coerentes `API_PORT`, `DB_PORT`,
`DATABASE_URL`, `MOCKSERVER_PORT` e `MOCKSERVER_URL` para os testes locais.
Dentro do Compose, a API acessa o banco por `db:5432`.

Para investigar falha de inicialização ou conexão:

```powershell
docker compose ps
docker compose logs --tail 100 api
docker compose logs --tail 100 db
```

Se o Docker não responder, abra o Docker Desktop e aguarde a inicialização.
Uma porta ocupada exige liberar a porta ou configurar outra.
Uma alteração em `database/database.sql` só é aplicada na criação do banco.
Para recriar exclusivamente os dados descartáveis deste projeto:

```powershell
docker compose down -v
docker compose up -d --build --wait
```

**O primeiro comando apaga o banco deste projeto.** Para apenas desligar
os serviços preservando os dados, use `docker compose stop`.

## Organização e documentação de entrega

`src/app.py` registra as rotas e os middlewares. Os schemas validam a entrada,
os resources traduzem HTTP, os controllers aplicam as regras, os repositories
acessam o banco e os DTOs montam respostas sem identificadores internos.
Cálculos puros ficam em `src/calculations/`; o SQL de criação,
em `database/database.sql`.

- [Rotas, campos, respostas e erros](docs/rotas.md).
- [Como o projeto é organizado](docs/como-o-projeto-e-organizado.md).
- [Decisões de negócio e arquitetura](docs/decisoes.md).
- [Plano de implementação](docs/plano/PLANO-00-indice.md).

O PDF/RFC final da equipe ainda precisa ser incluído no repositório para
compor a entrega. Os documentos acima descrevem o contrato e as decisões
disponíveis nesta árvore.

Licença [MIT](LICENSE).
