> **Git local — Bruno, 08/10/2026:** durante a produção, branches, commits, merges e tags ficam locais. Não executar push, pull ou fetch nem exigir acesso ao GitHub. O envio completo será feito pelo Bruno somente no final, quando tudo estiver pronto. As verificações de commits e dependências são locais.

# PLANO — Fase 06 — depósito, transferência e extrato

**Branch:** `fase/06-dinheiro` · **Depende de:** fase 5
**Objetivo:** depósito, saque e transferência com tarifa, idempotência e travas; limite diário com bloqueio automático; consulta da operação e extrato paginado; encerrar a conta só com saldo zero.

Regras de execução: `AGENTS.md`. Nomes obrigatórios: `docs/plano/PLANO-00-indice.md`, `docs/plano/PLANO-fase-02.md` (tabelas, models, constantes dos models e ids dos tipos fixos), `docs/plano/PLANO-fase-03.md` (`docs/rotas.md`, catálogo de erros, schemas), `docs/plano/PLANO-fase-04.md` (`RequestGenerator`, `PayloadGenerator`, `ObjectGenerator`, `INTERNAL_TOKEN`) e `docs/plano/PLANO-fase-05.md` (`AccountRepository`, `CustomerRepository`, `BaseController.get_owned_account`, `AccountController`). Um passo por vez, na ordem: 6.1 a 6.12 e, por último, 6.fim.

Contagem de testes da suíte (última linha do pytest): `129 passed` em 6.1 e 6.2; `138 passed` em 6.3 e 6.4; `149 passed` em 6.5; `159 passed` em 6.6 e 6.7; `174 passed` em 6.8; `179 passed` em 6.9; `186 passed` em 6.10; `195 passed` em 6.11; `197 passed` em 6.12 e no 6.fim (129 de antes + 9 unitários + 59 de integração).

Comandos usados nesta fase que não estão na seção 3 do `AGENTS.md`:

| Quero | Comando |
|---|---|
| Rodar uma linha de Python no `.venv` (a raiz do repositório no caminho de import) | `./.venv/Scripts/python.exe -c "<código>"` |
| Rodar uma linha de Python dentro do container da API | `docker compose exec -T api python -c "<código>"` |
| Procurar texto nos arquivos do Git | `git grep <opções> -- <pastas>` |

O `-T` desliga o terminal interativo, que o Git Bash não oferece. O `git grep` termina com código 1 quando não acha nada: nos itens em que o esperado é "nenhuma linha", esse código 1 sem linha impressa é o resultado certo.

Nas conferências que rodam dentro do container (`docker compose exec -T api python -c`), o código de `src/` é importado direto, sem HTTP, e tudo termina em `s.rollback()`: nada fica gravado.

Todas as saídas esperadas abaixo valem sem `.env` na raiz do repositório (ARQ-04). Existe um `.env`: PARE.

## Cobertura das regras desta fase (TST-02)

| Regra | O que fica vermelho se a regra deixar de valer |
|---|---|
| MOV-01, TST-03 — sem saldo barra, os dois saldos ficam | `test_transfer.py::test_refuses_insufficient_balance` |
| MOV-02 — o saldo cobre valor + tarifa | `test_transfer.py::test_refuses_insufficient_balance` (valor coberto, tarifa não), `test_balance_exactly_covers_amount_plus_fee` |
| MOV-03, MOV-06, TST-03 — toda transferência paga 1% | `test_transfer.py::test_transfers_with_fee`, `test_fee_rounds_up_to_the_cent`; `tests/unit/test_fee.py` |
| MOV-10 — arredonda para cima | `test_fee.py::test_rounds_up_to_the_cent`, `test_splitting_never_costs_less`; `test_transfer.py::test_fee_rounds_up_to_the_cent` |
| MOV-10 — tarifa zero sem lançamento | `test_fee.py::test_ten_fee_points_make_the_fee_zero` (a conta); o lado black box só existe com pontos, no passo 8.7 (ver "Divergências", item 6) |
| GAM-09 — cada ponto tira 0,1 p.p. | `test_fee.py::test_each_fee_point_removes_a_tenth_of_a_percentage_point` |
| MOV-09 — quem envia paga; depósito e saque sem tarifa | `test_transfer.py::test_transfers_with_fee` (o destino recebe o valor exato); `test_deposit.py::test_deposits_into_account`; `test_withdrawal.py::test_withdraws`; `test_get_transaction.py::test_gets_transfer_from_the_destination` (sem lançamento de tarifa no destino) |
| DAD-16 — uma operação, quatro lançamentos, soma zero | conferência T1 do 6.8 |
| MOV-05 — trava no saldo | `test_withdrawal.py::test_concurrent_withdrawals_never_go_negative`; `test_transfer.py::test_concurrent_transfers_never_go_negative` |
| MOV-11 — ordem das travas | `test_transfer.py::test_crossed_transfers_do_not_deadlock` |
| MOV-07, MOV-15 — depósito por qualquer um; saque só do dono | `test_deposit.py::test_deposits_into_account` (sem `ACCOUNT-TOKEN`); `test_withdrawal.py::test_other_account_token_is_404` |
| MOV-08, API-18 — o que barra | `test_refuses_body_out_of_schema` em `test_deposit.py`, `test_withdrawal.py` e `test_transfer.py` (400); `test_refuses_insufficient_balance` (422); `test_refuses_same_account` (422); os testes de conta bloqueada ou encerrada (409) |
| MOV-12 — idempotência | `test_repeated_request_returns_first_response`, `test_same_key_with_other_request_is_409` em `test_deposit.py`, `test_withdrawal.py` e `test_transfer.py`; `test_deposit.py::test_refused_request_does_not_keep_the_key` |
| MOV-19 — resposta remontada; corrida com a mesma chave | `test_withdrawal.py::test_repeated_request_returns_first_response` (o saldo da primeira vez, depois de outro saque); `test_deposit.py::test_concurrent_same_key` |
| MOV-16 — dígito verificador errado → 422; quem depositou fica em `deposits` | `test_deposit.py::test_refuses_invalid_document`, `test_deposits_with_cnpj`; conferência D2 do 6.5 |
| CLI-09 — bloqueada ou encerrada não mexe em dinheiro | `test_blocked_or_closed_account_refuses_deposit`, `test_blocked_or_closed_account_refuses_withdrawal`, `test_inactive_origin_is_409`, `test_inactive_destination_is_409`; `test_close_account_with_balance.py::test_closes_after_the_balance_reaches_zero` |
| CLI-08 — bloqueio automático na 11ª | `tests/integration/transactions/test_daily_transfer_limit.py` (5 testes); conferência B1 do 6.9 |
| CLI-06 — encerrar só com saldo zero | `tests/integration/accounts/test_close_account_with_balance.py` (2 testes) |
| R8, API-08, API-09 — outro dono → 404 | `test_other_account_token_is_404` e `test_missing_or_wrong_token_is_404` em `test_withdrawal.py` e `test_transfer.py`; `test_other_account_token_is_404` em `test_get_transaction.py` e `test_entries.py`; `test_get_transaction.py::test_transaction_of_other_account_is_404` |
| MOV-04, MOV-14, TST-03 — envelope, ordem, paginação | `test_entries.py::test_empty_statement`, `test_pagination`, `test_default_and_maximum_limit`, `test_most_recent_first_with_stable_tiebreak`, `test_refuses_query_out_of_schema` |
| MOV-17, PRD-12 — outra ponta, documento mascarado | `test_get_transaction.py` (4 testes de leitura); `test_entries.py::test_shows_every_operation_with_counterparty_and_dates` |
| MOV-18, DAD-17 — duas datas | `test_get_transaction.py::assert_transaction`; `test_entries.py::test_shows_every_operation_with_counterparty_and_dates`; conferência D2 do 6.5 (a data contábil é a do relógio) |
| DAD-07 — saldo em dois lugares | `test_entries.py::test_statement_reconciles_with_balance` |
| DAD-09 — contas do sistema sem saldo em coluna | conferências D2 (6.5) e T1 (6.8) |
| DAD-13 — regra que falha não grava | `test_entries.py::test_refused_requests_leave_no_entry`; os testes de recusa conferem os saldos |
| R5 — o `id` nunca sai | `assert_no_internal_id` (em todos os níveis da resposta) em `test_get_transaction.py` e `test_entries.py` |
| R6, DAD-08 — centavos inteiros | `type(...) is int` em `balance`, `amount` e `balance_after`; `test_fee.py::test_returns_int_never_float` |
| API-04 — `INTERNAL-TOKEN` | `test_deposit.py::test_requires_internal_token` |

Dos "Testes previstos" do `09 - Plano de trabalho`, caem nesta fase:

| Cenário do 09 | Teste |
|---|---|
| Transação: depósito válido | `test_deposit.py::test_deposits_into_account` |
| Transação: transferência válida (Aula 3) | `test_transfer.py::test_transfers_with_fee` |
| Transação: saldo insuficiente (Aula 3) | `test_transfer.py::test_refuses_insufficient_balance` |
| Transação: saldo exatamente igual a valor + tarifa | `test_transfer.py::test_balance_exactly_covers_amount_plus_fee` |
| Transação: valor zero, negativo, decimal ou float | `test_refuses_body_out_of_schema` nos três arquivos (400 `QIT000001`, API-18) |
| Transação: origem igual ao destino | `test_transfer.py::test_refuses_same_account` |
| Transação: origem ou destino que não existe | `test_transfer.py::test_unknown_destination_is_404`; `test_missing_or_wrong_token_is_404` (a origem não é do token); `test_deposit.py::test_unknown_account_is_404` |
| Transação: conta bloqueada ou encerrada | `test_inactive_origin_is_409`, `test_inactive_destination_is_409` e os de depósito e saque |
| Transação: 10 passam, a 11ª é recusada, conta `BLOCKED`, a 12ª dá 409 | `test_daily_transfer_limit.py::test_eleventh_transfer_is_refused_and_blocks_the_account`; "a 11ª não aparece no extrato": `test_entries.py::test_refused_requests_leave_no_entry` |
| Transação: desbloqueio e nova transferência no mesmo dia | `test_daily_transfer_limit.py::test_unblock_restarts_the_count` |
| Transação: bloqueio automático e virada do dia | fase 7: a virada nasce no passo 7.11 |
| Transação: a tarifa aparece no extrato (MOV-09) | `test_entries.py::test_most_recent_first_with_stable_tiebreak` |
| Transação: consultar a transação por conta que não é a dela | `test_get_transaction.py::test_transaction_of_other_account_is_404` |
| Transação: PUT, PATCH ou DELETE numa transação | `test_get_transaction.py::test_put_patch_and_delete_are_405` |
| Transação: varrer as respostas atrás de `id` | `assert_no_internal_id` em `test_get_transaction.py` e `test_entries.py` |
| Extrato: conta sem movimento | `test_entries.py::test_empty_statement` |
| Extrato: N+1 movimentos com `limit` = N (Aula 3) | `test_entries.py::test_pagination` |
| Extrato: ordem | `test_entries.py::test_most_recent_first_with_stable_tiebreak` |
| Extrato: `limit` zero, negativo, acima de 100 ou texto | `test_entries.py::test_refuses_query_out_of_schema` |
| Extrato: de conta de outro cliente | `test_entries.py::test_other_account_token_is_404` |
| Extrato: depósito + transferência + tarifa | `test_entries.py::test_shows_every_operation_with_counterparty_and_dates` |
| Provas extras: duas transferências ao mesmo tempo; A paga B e B paga A; mesma chave duas vezes; mesma chave com outro corpo; soma do extrato = saldo | adiantadas aqui (`test_concurrent_transfers_never_go_negative`, `test_crossed_transfers_do_not_deadlock`, `test_concurrent_same_key`, `test_same_key_with_other_request_is_409`, `test_statement_reconciles_with_balance`); a fase 11 repete com 10 rodadas |

---

### Passo 6.1 — Repositories do dinheiro
**Branch:** fase/06-dinheiro · **Depende de:** fase 5 (merge `feat(cliente-conta): fase 05 com cadastro de cliente, conta com token, bloqueio e encerramento` e commit `docs(plano): roteiros auditados`, os dois na `main`; tag `fase-05`)
**Objetivo:** `TransactionRepository` (`create`, `get_by_request_control_key`, `get_by_key_for_account`), `EntryRepository` (`create`, `list_by_transaction`, `get_transfer_counterparty_customer`), `DepositRepository` (`create`, `get_by_transaction`) e `BankClockRepository` (`get_accounting_date`, `lock`, `advance`).
**Decisões:** DAD-05 — entidades · DAD-06 — tabela de operações · DAD-07 — saldo em dois lugares · DAD-09 — contas do sistema · DAD-12 — UUID no repository · DAD-16 — tarifa como lançamento · DAD-17 — duas datas · DIA-01 — relógio do banco · MOV-12, MOV-19 — idempotência · MOV-14 — ordem por `id` no empate · MOV-17 — outra ponta · R4, DAD-11 — nada apaga movimentação
**Arquivos:**
- `src/repositories/transaction_repository.py` (criar): o conteúdo inteiro é:

```python
from datetime import date
from uuid import uuid4

from database import Context
from models import Entry, Transaction, TransactionType


class TransactionRepository:
    """Consulta e grava as operações (DAD-06). Nenhuma regra de negócio mora aqui.

    A key nasce aqui, com uuid4 (DAD-12). Operação não se altera nem se
    apaga (R4, DAD-11): este repository só cria e consulta.
    """

    def __init__(self, context: Context) -> None:
        self.session = context.db_session

    def create(self, transaction_type_enumerator: str, request_control_key: str, request_hash: str, accounting_date: date) -> Transaction:
        """Cria a operação com as duas datas (DAD-17): accounting_date vem do relógio do banco; created_at, do NOW() do banco.

        O flush manda o INSERT na hora: dá o id aos lançamentos e, se a
        request_control_key já existe, levanta o IntegrityError do UNIQUE
        aqui, antes de qualquer lançamento (MOV-19). Se outra transação
        acabou de gravar a mesma chave e ainda não fez commit, o INSERT
        espera por ela.
        """
        transaction = Transaction()
        transaction.transaction_key = str(uuid4())
        transaction.transaction_type = (
            self.session.query(TransactionType).filter(TransactionType.enumerator == transaction_type_enumerator).one()
        )
        transaction.request_control_key = request_control_key
        transaction.request_hash = request_hash
        transaction.accounting_date = accounting_date

        self.session.add(transaction)
        self.session.flush()

        return transaction

    def get_by_request_control_key(self, request_control_key: str) -> Transaction:
        """A operação gravada com esta chave de idempotência; None quando não existe (MOV-12)."""
        return self.session.query(Transaction).filter(Transaction.request_control_key == request_control_key).first()

    def get_by_key_for_account(self, transaction_key: str, account_ids: list) -> Transaction:
        """A operação com esta key, se ela tem pelo menos um lançamento numa das contas de account_ids; None nos outros casos (R8)."""
        return (
            self.session.query(Transaction)
            .join(Entry, Entry.transaction_id == Transaction.id)
            .filter(Transaction.transaction_key == transaction_key, Entry.account_id.in_(account_ids))
            .first()
        )
```

- `src/repositories/entry_repository.py` (criar): o conteúdo inteiro é:

```python
from uuid import uuid4

from database import Context
from models import Account, Category, Customer, Entry, EntryType, Transaction


class EntryRepository:
    """Consulta e grava os lançamentos: as pernas de cada operação (DAD-05, DAD-16).

    Nenhuma regra de negócio mora aqui. A key nasce aqui, com uuid4
    (DAD-12). Lançamento não se altera nem se apaga (R4, DAD-11).
    """

    def __init__(self, context: Context) -> None:
        self.session = context.db_session

    def create(
        self,
        transaction: Transaction,
        account: Account,
        entry_type_enumerator: str,
        amount: int,
        category: Category = None,
    ) -> Entry:
        """Grava um lançamento de `amount` centavos (negativo sai, positivo entra) na conta.

        Conta com saldo em coluna (de cliente e cofrinho): soma o amount ao
        balance e grava o saldo novo em balance_after (DAD-07, MOV-19).
        Contas do sistema (BANK e OUTSIDE_WORLD) têm balance nulo: os dois
        ficam nulos, e o saldo delas é a soma dos lançamentos (DAD-09).

        Quem chama já travou a conta de cliente (MOV-05). O flush grava na
        ordem das chamadas: o id dos lançamentos de uma operação cresce
        nessa ordem, e o extrato desempata por ele (MOV-14).
        """
        entry = Entry()
        entry.entry_key = str(uuid4())
        entry.transaction_id = transaction.id
        entry.account_id = account.id
        entry.entry_type = self.session.query(EntryType).filter(EntryType.enumerator == entry_type_enumerator).one()
        entry.amount = amount

        if category is not None:
            entry.category_id = category.id

        if account.balance is not None:
            account.balance = account.balance + amount
            entry.balance_after = account.balance

        self.session.add(entry)
        self.session.flush()

        return entry

    def list_by_transaction(self, transaction: Transaction, account_ids: list) -> list:
        """Os lançamentos da operação nas contas de account_ids, na ordem em que foram gravados (id crescente)."""
        return (
            self.session.query(Entry)
            .filter(Entry.transaction_id == transaction.id, Entry.account_id.in_(account_ids))
            .order_by(Entry.id)
            .all()
        )

    def get_transfer_counterparty_customer(self, entry: Entry) -> Customer:
        """O cliente da outra ponta de um lançamento AMOUNT de transferência (MOV-17).

        É o dono da conta do outro lançamento AMOUNT da mesma operação: na
        transferência, os dois AMOUNT são o de quem envia e o de quem recebe.
        """
        return (
            self.session.query(Customer)
            .join(Account, Account.customer_id == Customer.id)
            .join(Entry, Entry.account_id == Account.id)
            .join(EntryType, EntryType.id == Entry.entry_type_id)
            .filter(
                Entry.transaction_id == entry.transaction_id,
                Entry.id != entry.id,
                EntryType.enumerator == EntryType.AMOUNT,
            )
            .one()
        )
```

- `src/repositories/deposit_repository.py` (criar): o conteúdo inteiro é:

```python
from uuid import uuid4

from database import Context
from models import Deposit, Transaction


class DepositRepository:
    """Consulta e grava quem depositou (MOV-15, MOV-16), na tabela deposits. Nenhuma regra de negócio mora aqui."""

    def __init__(self, context: Context) -> None:
        self.session = context.db_session

    def create(self, transaction: Transaction, depositor_name: str, depositor_document: str) -> Deposit:
        """Grava o nome e o CPF ou CNPJ formatado de quem depositou, ligados à operação DEPOSIT.

        O documento inteiro fica só aqui, no banco (PRD-12): para fora, só
        sai mascarado.
        """
        deposit = Deposit()
        deposit.deposit_key = str(uuid4())
        deposit.transaction_id = transaction.id
        deposit.depositor_name = depositor_name
        deposit.depositor_document = depositor_document

        self.session.add(deposit)
        self.session.flush()

        return deposit

    def get_by_transaction(self, transaction: Transaction) -> Deposit:
        """Quem fez o depósito desta operação; None quando a operação não é um depósito."""
        return self.session.query(Deposit).filter(Deposit.transaction_id == transaction.id).first()
```

- `src/repositories/bank_clock_repository.py` (criar): o conteúdo inteiro é:

```python
from datetime import date, timedelta

from database import Context
from models import BankClock


class BankClockRepository:
    """O relógio do banco: a data contábil, numa tabela de uma linha só (DIA-01, DIA-04).

    Nenhuma regra de negócio mora aqui. Toda operação de dinheiro lê a
    data por get_accounting_date antes de travar qualquer conta; a virada
    do dia (fase 7) trava a linha por lock e muda a data por advance.
    """

    def __init__(self, context: Context) -> None:
        self.session = context.db_session

    def get_accounting_date(self) -> date:
        """O "hoje" do banco, lido com SELECT ... FOR SHARE.

        A trava compartilhada deixa várias operações lerem a data ao mesmo
        tempo e segura a virada do dia (lock, FOR UPDATE) até elas
        terminarem: nenhuma operação grava uma data que a virada já fechou.
        """
        return self.session.query(BankClock).with_for_update(read=True).one().accounting_date

    def lock(self) -> BankClock:
        """A linha do relógio, travada com SELECT ... FOR UPDATE, com os valores relidos do banco."""
        return self.session.query(BankClock).with_for_update().populate_existing().one()

    def advance(self, bank_clock: BankClock) -> date:
        """Passa o relógio travado para o dia seguinte do calendário e devolve a data nova (DIA-01)."""
        bank_clock.accounting_date = bank_clock.accounting_date + timedelta(days=1)

        return bank_clock.accounting_date
```

- `src/repositories/__init__.py` (editar): o conteúdo inteiro passa a ser:

```python
from repositories.request_log_repository import RequestLogRepository
from repositories.customer_repository import CustomerRepository
from repositories.account_repository import AccountRepository
from repositories.category_repository import CategoryRepository
from repositories.transaction_repository import TransactionRepository
from repositories.entry_repository import EntryRepository
from repositories.deposit_repository import DepositRepository
from repositories.bank_clock_repository import BankClockRepository
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia.
2. Abra a fase, um comando por vez:
   ```
   git switch main
   git log --oneline -n 3
   git tag --list fase-05
   git switch -c fase/06-dinheiro
   ```
   O `git log` mostra `docs(plano): roteiros auditados` e `feat(cliente-conta): fase 05 com cadastro de cliente, conta com token, bloqueio e encerramento`; o `git tag` mostra `fase-05`.
3. Crie `src/repositories/transaction_repository.py`, `src/repositories/entry_repository.py`, `src/repositories/deposit_repository.py` e `src/repositories/bank_clock_repository.py` com o conteúdo do campo **Arquivos**.
4. Edite `src/repositories/__init__.py` com o conteúdo do campo **Arquivos**.
5. `docker compose up -d --build --wait` → termina sem erro.
6. Rode a conferência R1 do **Verificar**.
7. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `129 passed`.
8. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
9. Feche o passo (AGENTS.md, seção 7), um comando por vez:
   ```
   git add -- src/repositories/transaction_repository.py src/repositories/entry_repository.py src/repositories/deposit_repository.py src/repositories/bank_clock_repository.py src/repositories/__init__.py
   git diff --cached --name-only
   git diff --name-only
   git ls-files --others --exclude-standard
   git commit -m "feat(dinheiro): repositories da operação, do lançamento, do depósito e do relógio"
   git log -1 --format=%B
   ```

**Testes:** nenhum teste novo. O passo é de camada de baixo; as rotas dos passos 6.5 a 6.11 usam estas peças por HTTP. A prova é a R1: numa transação só, cadastra dois clientes, abre as duas contas, grava um depósito e uma transferência pelos repositories, confere saldos, buscas, a outra ponta e o relógio, e desfaz tudo (`rollback`).
**Verificar:**
- R1 (um comando, numa linha só):
  ```
  docker compose exec -T api python -c "from datetime import date; from database import open_context; from models import AccountType, EntryType, TransactionType; from repositories import AccountRepository, BankClockRepository, CustomerRepository, DepositRepository, EntryRepository, TransactionRepository; c = open_context(); s = c.get_or_create_session(); r = AccountRepository(c); x = CustomerRepository(c).create('Ana Lima', '529.982.247-25', 'ana.conferencia.r1@example.com', date(1995, 4, 12)); y = CustomerRepository(c).create('Bruno Alves', '111.444.777-35', 'bruno.conferencia.r1@example.com', date(1990, 1, 20)); s.flush(); a = r.create_customer_account(x, '0' * 64); b = r.create_customer_account(y, '1' * 64); o = r.get_system_account(AccountType.OUTSIDE_WORLD); k = BankClockRepository(c); d = k.get_accounting_date(); t = TransactionRepository(c); e = EntryRepository(c); q = DepositRepository(c); t1 = t.create(TransactionType.DEPOSIT, '0f0f0f0f-0f0f-4f0f-8f0f-0f0f0f0f0f0f', 'a' * 64, d); e1 = e.create(t1, o, EntryType.AMOUNT, -5050); e2 = e.create(t1, a, EntryType.AMOUNT, 5050); dp = q.create(t1, 'Carlos Souza', '11.222.333/0001-81'); t2 = t.create(TransactionType.TRANSFER, '1f1f1f1f-1f1f-4f1f-8f1f-1f1f1f1f1f1f', 'b' * 64, d); e3 = e.create(t2, a, EntryType.AMOUNT, -1000); e4 = e.create(t2, b, EntryType.AMOUNT, 1000); print(d, len(t1.transaction_key), t1.transaction_type.enumerator, t1.accounting_date == d, t1.request_hash == 'a' * 64); print(e1.balance_after, o.balance, e2.balance_after, e3.balance_after, a.balance, e4.balance_after, b.balance, e1.entry_type.enumerator); print(t.get_by_request_control_key('0f0f0f0f-0f0f-4f0f-8f0f-0f0f0f0f0f0f') is t1, t.get_by_request_control_key('2f2f2f2f-2f2f-4f2f-8f2f-2f2f2f2f2f2f'), t.get_by_key_for_account(t1.transaction_key, [a.id]) is t1, t.get_by_key_for_account(t1.transaction_key, [b.id])); print(e.list_by_transaction(t2, [a.id, b.id]) == [e3, e4], e.list_by_transaction(t2, [b.id]) == [e4], e.get_transfer_counterparty_customer(e3) is y, e.get_transfer_counterparty_customer(e4) is x); print(len(dp.deposit_key), dp.depositor_document, q.get_by_transaction(t1) is dp, q.get_by_transaction(t2)); w = k.lock(); print(k.advance(w), w.accounting_date); s.rollback()"
  ```
  → exatamente (o relógio ainda está em 2026-06-01: só a virada da fase 7 o move):
  ```
  2026-06-01 36 DEPOSIT True True
  None None 5050 4050 4050 1000 1000 AMOUNT
  True None True None
  True True True True
  36 11.222.333/0001-81 True None
  2026-06-02 2026-06-02
  ```
- `git grep -n -e "session.delete" -e "\.delete(" -e "\.update(" -- src/repositories/transaction_repository.py src/repositories/entry_repository.py src/repositories/deposit_repository.py` → nenhuma linha (R4: operação, lançamento e depósito só se criam e se consultam).
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `129 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/repositories/__init__.py
  src/repositories/bank_clock_repository.py
  src/repositories/deposit_repository.py
  src/repositories/entry_repository.py
  src/repositories/transaction_repository.py
  ```
- `git log -1 --format=%B` → `feat(dinheiro): repositories da operação, do lançamento, do depósito e do relógio`

**Pronto quando:**
- [ ] A branch `fase/06-dinheiro` nasceu da `main` com o merge da fase 5.
- [ ] Os quatro arquivos novos e o `src/repositories/__init__.py` têm exatamente o conteúdo do campo **Arquivos**.
- [ ] A R1 dá as 6 linhas esperadas; o `git grep` não acha nada.
- [ ] Suíte com `129 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/06-dinheiro`.

**Commit:** `feat(dinheiro): repositories da operação, do lançamento, do depósito e do relógio`
**Pare se:**
- O `git log` do item 2 não mostrar as duas mensagens, ou o `git tag` não mostrar `fase-05`.
- A R1 terminar com `Traceback` ou der outra saída depois de 3 tentativas de conferir os cinco arquivos contra o plano. Um `IntegrityError` com `customer_document_number_key` ou `customer_email_key` quer dizer que o CPF ou o e-mail da R1 já está no banco: rode `docker compose down -v`, `docker compose up -d --build --wait` e a R1 de novo.
- A primeira linha da R1 não começar com `2026-06-01`.
- A suíte não terminar com `129 passed`.

---

### Passo 6.2 — DTOs do dinheiro e documento mascarado
**Branch:** fase/06-dinheiro · **Depende de:** 6.1
**Objetivo:** `TransactionDTO` (`only_obj_key`, `with_balance`, `obj_to_dict`); `EntryDTO` (`obj_to_dict` e as três formas da outra ponta); `is_valid_cnpj` e `mask_document_number` em `src/utils/document_number.py`.
**Decisões:** MOV-16 — CPF ou CNPJ de quem deposita · MOV-17 — outra ponta no extrato · MOV-18 — duas datas no extrato · PRD-12 — dado sensível mascarado · API-10 — resposta de sucesso · R5 — o `id` nunca sai · DAD-08 — centavos inteiros
**Arquivos:**
- `src/utils/document_number.py` (editar): o conteúdo inteiro passa a ser o bloco abaixo. `is_valid_cpf` não muda de comportamento; a docstring passa a citar `post_customers.json`.

```python
CPF_LENGTH = 11

CHECK_DIGIT_POSITIONS = [9, 10]

CNPJ_LENGTH = 14

# Pesos dos dois dígitos verificadores do CNPJ, da esquerda para a direita:
# o primeiro dígito usa os 12 primeiros dígitos; o segundo, os 13.
CNPJ_FIRST_WEIGHTS = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
CNPJ_SECOND_WEIGHTS = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]

# Tamanho do documento formatado: CPF 000.000.000-00; CNPJ 00.000.000/0000-00.
FORMATTED_CPF_LENGTH = 14
FORMATTED_CNPJ_LENGTH = 18


def is_valid_cpf(document_number: str) -> bool:
    """Diz se um CPF existe de verdade — não se ele tem a cara certa.

    O schema em src/schemas/post_customers.json já cobrou o formato:
    três pontos, um hífen, onze dígitos. Isto aqui é outra pergunta, e a
    diferença entre as duas é a lição deste arquivo.

    Os dois últimos dígitos de um CPF não são escolhidos: eles são o
    RESULTADO de uma conta feita sobre os nove primeiros. Por isso um
    número pode ter o formato perfeito e não existir — "111.222.333-44"
    passa no schema e não passa aqui.

    É o mesmo motivo pelo qual a resposta dessa recusa é 422 e não 400:
    não é que a API não conseguiu ler o pedido; ela leu, entendeu, e o
    valor não pode existir.

    A conta, para cada um dos dois dígitos: multiplica cada dígito
    anterior por um peso que decresce, soma tudo, tira o resto da divisão
    por 11. Resto menor que 2 vira dígito 0; nos outros casos, o dígito é
    11 menos o resto.
    """
    digits = []
    for character in document_number:
        if character.isdigit():
            digits.append(int(character))

    if len(digits) != CPF_LENGTH:
        return False

    # Um CPF de dígitos todos iguais ("111.111.111-11") passa na conta
    # dos dígitos verificadores e mesmo assim não vale. São onze números
    # conhecidos, e a Receita não emite nenhum deles.
    all_digits_are_equal = True
    for digit in digits:
        if digit != digits[0]:
            all_digits_are_equal = False
            break

    if all_digits_are_equal:
        return False

    for position in CHECK_DIGIT_POSITIONS:
        total = 0
        first_weight = position + 1

        for index in range(position):
            total = total + digits[index] * (first_weight - index)

        remainder = total % 11

        if remainder < 2:
            expected_digit = 0
        else:
            expected_digit = 11 - remainder

        if digits[position] != expected_digit:
            return False

    return True


def is_valid_cnpj(document_number: str) -> bool:
    """Diz se um CNPJ existe de verdade (MOV-16): a mesma pergunta do is_valid_cpf, com outros pesos.

    O schema post_deposits.json já cobrou o formato 00.000.000/0000-00.
    Aqui a conta: cada dígito verificador é o resto da soma dos dígitos
    anteriores multiplicados pelos pesos (CNPJ_FIRST_WEIGHTS e
    CNPJ_SECOND_WEIGHTS), dividida por 11. Resto menor que 2 vira 0; nos
    outros casos, o dígito é 11 menos o resto. CNPJ de dígitos todos
    iguais não vale.
    """
    digits = []
    for character in document_number:
        if character.isdigit():
            digits.append(int(character))

    if len(digits) != CNPJ_LENGTH:
        return False

    if len(set(digits)) == 1:
        return False

    for weights in [CNPJ_FIRST_WEIGHTS, CNPJ_SECOND_WEIGHTS]:
        position = len(weights)
        total = 0

        for index in range(position):
            total = total + digits[index] * weights[index]

        remainder = total % 11

        if remainder < 2:
            expected_digit = 0
        else:
            expected_digit = 11 - remainder

        if digits[position] != expected_digit:
            return False

    return True


def mask_document_number(document_number: str) -> str:
    """O CPF ou o CNPJ de outra pessoa, mascarado (PRD-12, MOV-17).

    CPF 123.456.789-09 → ***.456.789-**: somem os 3 primeiros dígitos e
    os 2 verificadores. CNPJ 11.222.333/0001-81 → **.222.333/****-**:
    somem os 2 primeiros, a filial e os 2 verificadores. O documento
    chega formatado, como o banco o guarda; outro tamanho é erro de
    programa (ValueError), nunca dado de cliente.
    """
    if len(document_number) == FORMATTED_CPF_LENGTH:
        return "***" + document_number[3:12] + "**"

    if len(document_number) == FORMATTED_CNPJ_LENGTH:
        return "**" + document_number[2:11] + "****-**"

    raise ValueError(f"documento com {len(document_number)} caracteres não é CPF nem CNPJ formatado")
```

- `src/dtos/transaction_dto.py` (criar): o conteúdo inteiro é:

```python
from models import Transaction


class TransactionDTO:
    """A operação que a API devolve: a key pública, nunca o id nem a request_control_key (R5)."""

    @staticmethod
    def only_obj_key(transaction: Transaction) -> dict:
        """A resposta do depósito: só a key da operação (MOV-16)."""
        return {"transaction_key": transaction.transaction_key}

    @staticmethod
    def with_balance(transaction: Transaction, balance: int) -> dict:
        """A resposta do saque e da transferência: a key e o saldo da conta depois da operação, em centavos (API-10)."""
        return {
            "transaction_key": transaction.transaction_key,
            "balance": balance,
        }

    @staticmethod
    def obj_to_dict(transaction: Transaction, entries: list) -> dict:
        """A operação para o dono (GET .../transactions/{transaction_key}), com os lançamentos já no formato do extrato."""
        return {
            "transaction_key": transaction.transaction_key,
            "type": transaction.transaction_type.enumerator,
            "accounting_date": transaction.accounting_date.isoformat(),
            "created_at": transaction.created_at.isoformat(),
            "entries": entries,
        }
```

- `src/dtos/entry_dto.py` (criar): o conteúdo inteiro é:

```python
from models import Category, Customer, Deposit, Entry, Transaction
from utils.document_number import mask_document_number


class EntryDTO:
    """Um item do extrato (MOV-14, MOV-17, MOV-18): keys públicas, dinheiro em centavos, nunca id (R5).

    A outra ponta (`counterparty`) chega pronta do controller, montada por
    um dos três métodos de baixo; o CPF e o CNPJ de outra pessoa só saem
    mascarados (PRD-12).
    """

    @staticmethod
    def obj_to_dict(entry: Entry, transaction: Transaction, counterparty: dict, category: Category = None) -> dict:
        category_dict = None
        if category is not None:
            category_dict = {
                "category_key": category.category_key,
                "name": category.name,
            }

        return {
            "entry_key": entry.entry_key,
            "transaction_key": transaction.transaction_key,
            "transaction_type": transaction.transaction_type.enumerator,
            "entry_type": entry.entry_type.enumerator,
            "amount": entry.amount,
            "balance_after": entry.balance_after,
            "category": category_dict,
            "counterparty": counterparty,
            "accounting_date": transaction.accounting_date.isoformat(),
            "created_at": entry.created_at.isoformat(),
        }

    @staticmethod
    def customer_counterparty(customer: Customer) -> dict:
        """Na transferência: o outro cliente, com o CPF mascarado."""
        return {
            "type": "CUSTOMER",
            "name": customer.name,
            "document_number": mask_document_number(customer.document_number),
        }

    @staticmethod
    def depositor_counterparty(deposit: Deposit) -> dict:
        """No depósito: quem depositou, com o CPF ou o CNPJ mascarado."""
        return {
            "type": "DEPOSITOR",
            "name": deposit.depositor_name,
            "document_number": mask_document_number(deposit.depositor_document),
        }

    @staticmethod
    def bank_counterparty() -> dict:
        """Na tarifa, no prêmio, no rendimento, no IOF e no IR: o banco."""
        return {"type": "BANK"}
```

- `src/dtos/__init__.py` (editar): o conteúdo inteiro passa a ser:

```python
from dtos.customer_dto import CustomerDTO
from dtos.account_dto import AccountDTO
from dtos.transaction_dto import TransactionDTO
from dtos.entry_dto import EntryDTO
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/06-dinheiro`; `git log --oneline` mostra `feat(dinheiro): repositories da operação, do lançamento, do depósito e do relógio`.
2. Edite `src/utils/document_number.py` com o conteúdo do campo **Arquivos**.
3. Crie `src/dtos/transaction_dto.py` e `src/dtos/entry_dto.py` com o conteúdo do campo **Arquivos**.
4. Edite `src/dtos/__init__.py` com o conteúdo do campo **Arquivos**.
5. `docker compose up -d --build --wait` → termina sem erro.
6. Rode a conferência D1 do **Verificar**.
7. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `129 passed`.
8. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
9. Feche o passo (AGENTS.md, seção 7), um comando por vez:
   ```
   git add -- src/utils/document_number.py src/dtos/transaction_dto.py src/dtos/entry_dto.py src/dtos/__init__.py
   git diff --cached --name-only
   git diff --name-only
   git ls-files --others --exclude-standard
   git commit -m "feat(dinheiro): DTOs da operação e do extrato, CNPJ e documento mascarado"
   git log -1 --format=%B
   ```

**Testes:** nenhum teste novo. `src/utils/` e `src/dtos/` não são contas puras (TST-05), e o teste de integração não importa de `src/` (TST-01). O CNPJ errado é provado por HTTP no 6.5 (`test_refuses_invalid_document`) e a máscara, no 6.10 e no 6.11. Aqui, a prova é a D1, com objetos de mentira no lugar dos models.
**Verificar:**
- D1 (um comando, numa linha só):
  ```
  docker compose exec -T api python -c "from datetime import date, datetime; from types import SimpleNamespace as N; from dtos import EntryDTO, TransactionDTO; from utils.document_number import is_valid_cnpj, is_valid_cpf, mask_document_number; t = N(transaction_key='tk', transaction_type=N(enumerator='TRANSFER'), accounting_date=date(2026, 6, 1), created_at=datetime(2026, 10, 7, 14, 3, 12, 123456)); e = N(entry_key='ek', entry_type=N(enumerator='FEE'), amount=-100, balance_after=39900, created_at=datetime(2026, 10, 7, 14, 3, 12, 123456)); print(is_valid_cnpj('11.222.333/0001-81'), is_valid_cnpj('11.222.333/0001-80'), is_valid_cnpj('11.111.111/1111-11'), is_valid_cnpj('11.222.333/0001-8'), is_valid_cpf('529.982.247-25')); print(mask_document_number('529.982.247-25'), mask_document_number('11.222.333/0001-81')); print(EntryDTO.obj_to_dict(e, t, EntryDTO.bank_counterparty())); print(EntryDTO.customer_counterparty(N(name='Bruno Alves', document_number='529.982.247-25'))); print(EntryDTO.depositor_counterparty(N(depositor_name='Carlos Souza', depositor_document='11.222.333/0001-81'))); print(TransactionDTO.only_obj_key(t), TransactionDTO.with_balance(t, 39900)); print(TransactionDTO.obj_to_dict(t, []))"
  ```
  → exatamente:
  ```
  True False False False True
  ***.982.247-** **.222.333/****-**
  {'entry_key': 'ek', 'transaction_key': 'tk', 'transaction_type': 'TRANSFER', 'entry_type': 'FEE', 'amount': -100, 'balance_after': 39900, 'category': None, 'counterparty': {'type': 'BANK'}, 'accounting_date': '2026-06-01', 'created_at': '2026-10-07T14:03:12.123456'}
  {'type': 'CUSTOMER', 'name': 'Bruno Alves', 'document_number': '***.982.247-**'}
  {'type': 'DEPOSITOR', 'name': 'Carlos Souza', 'document_number': '**.222.333/****-**'}
  {'transaction_key': 'tk'} {'transaction_key': 'tk', 'balance': 39900}
  {'transaction_key': 'tk', 'type': 'TRANSFER', 'accounting_date': '2026-06-01', 'created_at': '2026-10-07T14:03:12.123456', 'entries': []}
  ```
- `git grep -n -e SampleEntity -e sample_entity -- src/utils/document_number.py` → nenhuma linha.
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `129 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/dtos/__init__.py
  src/dtos/entry_dto.py
  src/dtos/transaction_dto.py
  src/utils/document_number.py
  ```
- `git log -1 --format=%B` → `feat(dinheiro): DTOs da operação e do extrato, CNPJ e documento mascarado`

**Pronto quando:**
- [ ] Os quatro arquivos têm exatamente o conteúdo do campo **Arquivos**.
- [ ] A D1 dá as 7 linhas esperadas.
- [ ] Suíte com `129 passed` (o cadastro de cliente continua validando CPF igual); lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/06-dinheiro`.

**Commit:** `feat(dinheiro): DTOs da operação e do extrato, CNPJ e documento mascarado`
**Pare se:**
- `docker compose up -d --build --wait` falhar com `ImportError` no `docker compose logs --tail 100 api`: traga a saída.
- A D1 der outra saída depois de 3 tentativas de conferir os quatro arquivos contra o plano.
- Um teste de `tests/integration/customers/` falhar: o `is_valid_cpf` mudou de comportamento.

---

### Passo 6.3 — Tarifa (unitário)
**Branch:** fase/06-dinheiro · **Depende de:** 6.2
**Objetivo:** `calculate_fee(amount_cents, fee_points)` = `teto(amount_cents × (10 − fee_points) / 1000)`, só com inteiros, em `src/calculations/fee.py`, com o teste unitário escrito antes.
**Decisões:** MOV-06 — tarifa de 1% · MOV-10 — arredonda para cima · GAM-09 — ponto em tarifa · GAM-15 — 10 pontos no máximo · TST-05 — unitários em pasta separada, escritos primeiro · R6, DAD-08 — sem float
**Arquivos:**
- `tests/unit/test_fee.py` (criar): o conteúdo inteiro é:

```python
"""Tarifa da transferência: calculate_fee (MOV-06, MOV-10, GAM-09, TST-05).

Unitário: importa só de calculations, da biblioteca padrão e do pytest.
O pytest.ini põe src/ no caminho de import.
"""

import pytest

from calculations import calculate_fee


class TestCalculateFee:
    def test_one_percent_of_the_amount(self):
        assert calculate_fee(10000, 0) == 100
        assert calculate_fee(100, 0) == 1
        assert calculate_fee(1200, 0) == 12
        assert calculate_fee(100000, 0) == 1000

    def test_rounds_up_to_the_cent(self):
        assert calculate_fee(1234, 0) == 13
        assert calculate_fee(101, 0) == 2
        assert calculate_fee(99, 0) == 1
        assert calculate_fee(1, 0) == 1
        assert calculate_fee(1000, 9) == 1
        assert calculate_fee(1, 9) == 1

    def test_splitting_never_costs_less(self):
        for first in range(1, 301, 7):
            for second in range(1, 301, 11):
                assert calculate_fee(first, 0) + calculate_fee(second, 0) >= calculate_fee(first + second, 0), (first, second)

    def test_each_fee_point_removes_a_tenth_of_a_percentage_point(self):
        for fee_points in range(0, 11):
            assert calculate_fee(10000, fee_points) == 100 - 10 * fee_points, fee_points

    def test_ten_fee_points_make_the_fee_zero(self):
        assert calculate_fee(1, 10) == 0
        assert calculate_fee(1000000000000, 10) == 0

    def test_returns_int_never_float(self):
        for amount_cents, fee_points in [(1, 0), (1234, 0), (10000, 3), (1, 10)]:
            assert type(calculate_fee(amount_cents, fee_points)) is int, (amount_cents, fee_points)

    def test_exact_for_the_largest_bigint(self):
        assert calculate_fee(9223372036854775807, 0) == 92233720368547759

    def test_refuses_points_out_of_range(self):
        for fee_points in [-1, 11]:
            with pytest.raises(ValueError):
                calculate_fee(10000, fee_points)

    def test_refuses_amount_below_one_cent(self):
        for amount_cents in [0, -1]:
            with pytest.raises(ValueError):
                calculate_fee(amount_cents, 0)
```

- `src/calculations/__init__.py` (criar; a pasta `src/calculations/` é nova): o conteúdo inteiro é:

```python
from calculations.fee import calculate_fee
```

- `src/calculations/fee.py` (criar): o conteúdo inteiro é:

```python
"""Tarifa da transferência (MOV-06, MOV-10, GAM-09). Conta pura: só inteiros, sem banco e sem HTTP."""


# MOV-06: a tarifa cheia é 1% = 10 décimos de ponto percentual.
FULL_FEE_TENTHS_OF_PERCENT = 10

# GAM-09, GAM-15: cada ponto em tarifa tira 1 décimo de ponto percentual;
# com os 10 pontos, a tarifa é 0%.
MAX_FEE_POINTS = 10

# Um décimo de ponto percentual é 1/1000 do valor.
TENTHS_OF_PERCENT_DIVISOR = 1000


def calculate_fee(amount_cents: int, fee_points: int) -> int:
    """A tarifa da transferência, em centavos inteiros.

    tarifa = teto(amount_cents × (10 − fee_points) / 1000)

    Arredonda para cima ao centavo (MOV-10): 1% de R$ 12,34 = 12,34
    centavos → 13. Assim, dividir uma transferência em duas nunca sai mais
    barato. A conta é feita só com inteiros: somar o divisor menos 1 antes
    da divisão inteira (//) é o teto sem passar por float (R6, DAD-08).

    Recusa com ValueError o que nenhuma regra permite: valor abaixo de 1
    centavo (API-18) e pontos fora de 0 a 10 (GAM-09).
    """
    if amount_cents < 1:
        raise ValueError(f"amount_cents precisa ser pelo menos 1, veio {amount_cents}")

    if fee_points < 0 or fee_points > MAX_FEE_POINTS:
        raise ValueError(f"fee_points precisa estar entre 0 e {MAX_FEE_POINTS}, veio {fee_points}")

    tenths_of_percent = FULL_FEE_TENTHS_OF_PERCENT - fee_points

    return (amount_cents * tenths_of_percent + TENTHS_OF_PERCENT_DIVISOR - 1) // TENTHS_OF_PERCENT_DIVISOR
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/06-dinheiro`; `git log --oneline` mostra `feat(dinheiro): DTOs da operação e do extrato, CNPJ e documento mascarado`.
2. Crie `tests/unit/test_fee.py` com o conteúdo do campo **Arquivos**.
3. `./.venv/Scripts/python.exe -m pytest -v tests/unit/test_fee.py` → a saída tem `ModuleNotFoundError: No module named 'calculations'` e a última linha tem `1 error`. É o motivo certo (AGENTS.md, seção 6): a pasta `src/calculations/` ainda não existe.
4. Crie `src/calculations/__init__.py` e `src/calculations/fee.py` com o conteúdo do campo **Arquivos**.
5. `./.venv/Scripts/python.exe -m pytest -v tests/unit/test_fee.py` → a última linha tem `9 passed`.
6. `docker compose up -d --build --wait` → termina sem erro.
7. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `138 passed`.
8. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
9. Rode o **Verificar**.
10. Feche o passo (AGENTS.md, seção 7), um comando por vez:
    ```
    git add -- tests/unit/test_fee.py src/calculations/__init__.py src/calculations/fee.py
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "feat(tarifa): calculate_fee com teste unitário"
    git log -1 --format=%B
    ```

**Testes:** `tests/unit/test_fee.py` (TST-05). Não toca na API nem no banco.

| Função de teste | Entrada | Esperado |
|---|---|---|
| `test_one_percent_of_the_amount` | 10000, 100, 1200, 100000 centavos; 0 pontos | 100, 1, 12, 1000 |
| `test_rounds_up_to_the_cent` | 1234, 101, 99, 1 com 0 pontos; 1000 e 1 com 9 pontos | 13, 2, 1, 1; 1 e 1 (MOV-10) |
| `test_splitting_never_costs_less` | pares de valores de 1 a 300 | tarifa(a) + tarifa(b) ≥ tarifa(a + b) |
| `test_each_fee_point_removes_a_tenth_of_a_percentage_point` | 10000 com 0 a 10 pontos | 100 − 10 × pontos (GAM-09) |
| `test_ten_fee_points_make_the_fee_zero` | 1 e 1.000.000.000.000 com 10 pontos | 0 |
| `test_returns_int_never_float` | quatro combinações | `type(...) is int` (R6) |
| `test_exact_for_the_largest_bigint` | 9223372036854775807, 0 pontos | 92233720368547759 (sem perder dígito) |
| `test_refuses_points_out_of_range` | −1 e 11 pontos | `ValueError` |
| `test_refuses_amount_below_one_cent` | 0 e −1 centavos | `ValueError` |

**Verificar:**
- `./.venv/Scripts/python.exe -m pytest -v tests/unit/test_fee.py` → `9 passed`.
- `git grep -n -e "import" -- src/calculations/fee.py` → nenhuma linha (a conta pura não importa nada).
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `138 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/calculations/__init__.py
  src/calculations/fee.py
  tests/unit/test_fee.py
  ```
- `git log -1 --format=%B` → `feat(tarifa): calculate_fee com teste unitário`

**Pronto quando:**
- [ ] O teste falhou antes do código com `ModuleNotFoundError` (item 3) e passa depois (item 5).
- [ ] Os três arquivos têm exatamente o conteúdo do campo **Arquivos**.
- [ ] O `git grep` não acha nada.
- [ ] Suíte com `138 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/06-dinheiro`.

**Commit:** `feat(tarifa): calculate_fee com teste unitário`
**Pare se:**
- O item 3 não mostrar `ModuleNotFoundError: No module named 'calculations'` (outro erro, ou algum teste rodou).
- O item 5 não terminar com `9 passed` depois de 3 tentativas de conferir `src/calculations/fee.py` contra o plano.
- A suíte não terminar com `138 passed`.

---

### Passo 6.4 — Depósito: controller
**Branch:** fase/06-dinheiro · **Depende de:** 6.3
**Objetivo:** `hash_request_body` e `TransactionController.deposit`: conta de cliente que existe → repetição pela `request_control_key` (mesmo pedido → a resposta da primeira vez; outro pedido → 409 `QIT001014`; `IntegrityError` tratado como repetição) → trava → conta `ACTIVE` → documento válido; operação `DEPOSIT` com dois lançamentos (`OUTSIDE_WORLD` − e conta +) e a linha em `deposits`.
**Decisões:** MOV-07 — operações · MOV-09 — depósito sem tarifa · MOV-12 — idempotência · MOV-15 — quem deposita · MOV-16 — rota e dados do depósito · MOV-19 — idempotência na prática · MOV-05 — trava no saldo · CLI-09 — bloqueada não mexe em dinheiro · DAD-09 — mundo de fora · DAD-13 — operação síncrona · DIA-01 — data contábil · R3 — `IntegrityError` nunca vira 500
**Arquivos:**
- `src/utils/request_hash.py` (criar): o conteúdo inteiro é:

```python
import hashlib
import json


def hash_request_body(transaction_type: str, account_key: str, payload: dict) -> str:
    """O SHA-256 do pedido, em 64 caracteres hexadecimais (MOV-12, MOV-19).

    É o que a operação guarda em request_hash. O mesmo pedido é a mesma
    operação (DEPOSIT, WITHDRAWAL ou TRANSFER), na mesma conta da URL,
    com o mesmo corpo: os três entram no hash. A mesma
    request_control_key com outro hash é outro pedido (409 QIT001014).

    O texto que vira hash é o JSON com as chaves em ordem alfabética e sem
    espaços: o mesmo corpo com os campos em outra ordem dá o mesmo hash.
    """
    request = {
        "transaction_type": transaction_type,
        "account_key": account_key,
        "payload": payload,
    }
    canonical_text = json.dumps(request, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    return hashlib.sha256(canonical_text.encode("utf-8")).hexdigest()
```

- `src/controllers/transaction_controller.py` (criar): o conteúdo inteiro é:

```python
from sqlalchemy.exc import IntegrityError

from controllers.base_controller import BaseController
from dtos import TransactionDTO
from errors import (
    AccountNotActive,
    AccountNotFound,
    IdempotencyKeyConflict,
    InvalidDocumentNumber,
)
from models import AccountStatus, AccountType, EntryType, Transaction, TransactionType
from repositories import AccountRepository, BankClockRepository, DepositRepository, EntryRepository, TransactionRepository
from utils.document_number import FORMATTED_CPF_LENGTH, is_valid_cnpj, is_valid_cpf
from utils.request_hash import hash_request_body


class TransactionController(BaseController):
    """As regras do dinheiro em movimento: depósito, saque, transferência, consulta e extrato (MOV).

    Toda operação de dinheiro segue o mesmo desenho:

    1. confere quem pede e repete a resposta de um pedido já feito (MOV-12);
    2. lê a data contábil (DIA-01) e trava as contas de cliente, na ordem
       do id (MOV-05, MOV-11); as regras são conferidas depois da trava,
       com o estado e o saldo relidos do banco;
    3. grava a operação e os lançamentos, que somam zero (DAD-16), e faz o
       commit; regra que falha não grava nada (DAD-13).
    """

    def __init__(self) -> None:
        super().__init__(__name__)
        self.account_repository = AccountRepository(self.context)
        self.bank_clock_repository = BankClockRepository(self.context)
        self.deposit_repository = DepositRepository(self.context)
        self.entry_repository = EntryRepository(self.context)
        self.transaction_repository = TransactionRepository(self.context)

    def deposit(self, account_key: str, deposit_data: dict) -> dict:
        """Depósito: o dinheiro vem da conta OUTSIDE_WORLD (MOV-07, MOV-15, MOV-16). As regras, nesta ordem:

        1. a conta existe e é de cliente (404 QIT001010); o depósito não
           pede token de conta, e esta recusa não conta como falha de token;
        2. a mesma request_control_key com o mesmo pedido devolve a resposta
           da primeira vez; com outro pedido, 409 QIT001014 (MOV-12);
        3. trava a conta (MOV-05);
        4. a conta está ACTIVE (409 QIT001011, CLI-09);
        5. o CPF ou o CNPJ de quem deposita existe (422 QIT001003, MOV-16).

        Depois: a operação DEPOSIT, o lançamento AMOUNT −valor na
        OUTSIDE_WORLD, o AMOUNT +valor na conta e a linha em deposits. Sem
        tarifa (MOV-09). A resposta traz só a key da operação.
        """
        account = self.account_repository.get_customer_account(account_key)

        if account is None:
            raise AccountNotFound(account_key)

        request_control_key = deposit_data["request_control_key"]
        request_hash = hash_request_body(TransactionType.DEPOSIT, account_key, deposit_data)

        repeated_transaction = self._find_repeated(request_control_key, request_hash)
        if repeated_transaction is not None:
            return TransactionDTO.only_obj_key(repeated_transaction)

        accounting_date = self.bank_clock_repository.get_accounting_date()
        account = self.account_repository.lock_accounts([account])[0]

        # Uma chamada com a mesma chave pode ter concluído enquanto esta esperava a trava.
        repeated_transaction = self._find_repeated(request_control_key, request_hash)
        if repeated_transaction is not None:
            return TransactionDTO.only_obj_key(repeated_transaction)

        if account.status.enumerator != AccountStatus.ACTIVE:
            raise AccountNotActive(account_key, account.status.enumerator)

        if not self._is_valid_depositor_document(deposit_data["depositor_document"]):
            raise InvalidDocumentNumber()

        outside_world = self.account_repository.get_system_account(AccountType.OUTSIDE_WORLD)
        amount = deposit_data["amount"]

        try:
            transaction = self.transaction_repository.create(TransactionType.DEPOSIT, request_control_key, request_hash, accounting_date)
            self.entry_repository.create(transaction, outside_world, EntryType.AMOUNT, -amount)
            self.entry_repository.create(transaction, account, EntryType.AMOUNT, amount)
            self.deposit_repository.create(transaction, deposit_data["depositor_name"], deposit_data["depositor_document"])

            transaction_dto = TransactionDTO.only_obj_key(transaction)
            self.logger.info("operation_ready_to_commit transaction_key=%s", transaction.transaction_key)
            self.session.commit()
        except IntegrityError:
            self.session.rollback()

            repeated_transaction = self._find_repeated(request_control_key, request_hash)
            if repeated_transaction is None:
                raise

            return TransactionDTO.only_obj_key(repeated_transaction)

        return transaction_dto

    def _find_repeated(self, request_control_key: str, request_hash: str) -> Transaction:
        """A operação já gravada com esta chave e o mesmo pedido; None quando a chave é nova (MOV-12, MOV-19).

        A chave já usada com outro pedido (outro hash) responde 409
        QIT001014.
        """
        transaction = self.transaction_repository.get_by_request_control_key(request_control_key)

        if transaction is None:
            return None

        if transaction.request_hash != request_hash:
            raise IdempotencyKeyConflict(request_control_key)

        return transaction

    def _is_valid_depositor_document(self, depositor_document: str) -> bool:
        """CPF (14 caracteres formatado) ou CNPJ (18): o schema já garantiu um dos dois formatos (MOV-16)."""
        if len(depositor_document) == FORMATTED_CPF_LENGTH:
            return is_valid_cpf(depositor_document)

        return is_valid_cnpj(depositor_document)
```

- `src/controllers/__init__.py` (editar): o conteúdo inteiro passa a ser:

```python
from controllers.customer_controller import CustomerController
from controllers.account_controller import AccountController
from controllers.transaction_controller import TransactionController
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/06-dinheiro`; `git log --oneline` mostra `feat(tarifa): calculate_fee com teste unitário`.
2. Crie `src/utils/request_hash.py` com o conteúdo do campo **Arquivos** (a pasta `src/utils/` não tem `__init__.py`, e continua sem).
3. Crie `src/controllers/transaction_controller.py` com o conteúdo do campo **Arquivos**.
4. Edite `src/controllers/__init__.py` com o conteúdo do campo **Arquivos**.
5. `docker compose up -d --build --wait` → termina sem erro.
6. Rode a conferência S1 do **Verificar**.
7. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `138 passed`.
8. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
9. Feche o passo (AGENTS.md, seção 7), um comando por vez:
   ```
   git add -- src/utils/request_hash.py src/controllers/transaction_controller.py src/controllers/__init__.py
   git diff --cached --name-only
   git diff --name-only
   git ls-files --others --exclude-standard
   git commit -m "feat(deposito): controller do depósito com idempotência"
   git log -1 --format=%B
   ```

**Testes:** nenhum teste novo. A rota que usa o controller nasce no 6.5, com os testes que ficam vermelhos antes dela. Aqui, a prova é a S1: os nomes do plano existem, a API sobe com eles, e o hash muda quando muda a operação ou a conta, mas não quando muda a ordem dos campos.
**Verificar:**
- S1 (um comando, numa linha só):
  ```
  docker compose exec -T api python -c "from controllers import TransactionController; from controllers.base_controller import BaseController; from utils.request_hash import hash_request_body; print(sorted(n for n in vars(TransactionController) if not n.startswith('__'))); print(issubclass(TransactionController, BaseController)); h = hash_request_body('DEPOSIT', 'k', {'a': 1, 'b': 2}); print(len(h), h == hash_request_body('DEPOSIT', 'k', {'b': 2, 'a': 1}), h == hash_request_body('WITHDRAWAL', 'k', {'a': 1, 'b': 2}), h == hash_request_body('DEPOSIT', 'outra', {'a': 1, 'b': 2}))"
  ```
  → exatamente:
  ```
  ['_find_repeated', '_is_valid_depositor_document', 'deposit']
  True
  64 True False False
  ```
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `138 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/controllers/__init__.py
  src/controllers/transaction_controller.py
  src/utils/request_hash.py
  ```
- `git log -1 --format=%B` → `feat(deposito): controller do depósito com idempotência`

**Pronto quando:**
- [ ] Os três arquivos têm exatamente o conteúdo do campo **Arquivos**.
- [ ] A S1 dá as 3 linhas esperadas.
- [ ] Suíte com `138 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/06-dinheiro`.

**Commit:** `feat(deposito): controller do depósito com idempotência`
**Pare se:**
- `docker compose up -d --build --wait` falhar com `ImportError` ou `circular import` no `docker compose logs --tail 100 api`: traga a saída.
- A S1 der outra saída depois de 3 tentativas de conferir os três arquivos contra o plano.
- A suíte não terminar com `138 passed`.

---

### Passo 6.5 — `POST /accounts/{account_key}/deposits`
**Branch:** fase/06-dinheiro · **Depende de:** 6.4
**Objetivo:** `TransactionResource.on_post_deposit` e a rota `POST /accounts/{account_key}/deposits` (tokens: interno; schema `post_deposits.json`): 201 com `{"transaction_key"}`; 404 `QIT001010`; 409 `QIT001011`; 422 `QIT001003`; 409 `QIT001014`; 400 `QIT000001`; 403 `QIT000002`.
**Decisões:** MOV-15 — quem deposita · MOV-16 — rota e dados do depósito · MOV-09 — sem tarifa · MOV-12, MOV-19 — idempotência · API-18 — valor inteiro ≥ 1 · API-02 — 201 na criação · API-03 — schema fechado · API-04 — `INTERNAL-TOKEN` · CLI-09 — bloqueada ou encerrada → 409 · TST-01 — black box e TDD
**Arquivos:**
- `src/resources/transaction.py` (criar): o conteúdo inteiro é:

```python
from fastapi import status as http_status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from controllers import TransactionController
from utils.schema_handler import SchemaHandler


class TransactionResource:
    """A porta HTTP do dinheiro: depósito, saque, transferência, consulta e extrato.

    Sem regra de negócio, sem SQL e sem nada guardado no self (ARQ-02). O
    token da conta chega no cabeçalho ACCOUNT-TOKEN (API-16); quem o
    confere é o controller.
    """

    @SchemaHandler.validate("post_deposits.json")
    def on_post_deposit(self, account_key: str, payload: dict) -> JSONResponse:
        controller = TransactionController()
        transaction = controller.deposit(account_key, payload)

        return JSONResponse(
            content=jsonable_encoder(transaction),
            status_code=http_status.HTTP_201_CREATED,
        )
```

- `src/resources/__init__.py` (editar): o conteúdo inteiro passa a ser:

```python
from resources.health_check import HealthCheckResource
from resources.customer import CustomerResource
from resources.account import AccountResource
from resources.internal import InternalResource
from resources.transaction import TransactionResource
```

- `src/app.py` (editar): três trocas, e nada mais.
  1. A linha
     ```python
     from resources import AccountResource, CustomerResource, HealthCheckResource, InternalResource
     ```
     vira
     ```python
     from resources import AccountResource, CustomerResource, HealthCheckResource, InternalResource, TransactionResource
     ```
  2. A linha
     ```python
         internal_resource = InternalResource()
     ```
     vira as duas linhas
     ```python
         internal_resource = InternalResource()
         transaction_resource = TransactionResource()
     ```
  3. A linha
     ```python
         application.add_api_route("/accounts/{account_key}", account_resource.on_delete_by_key, methods=["DELETE"])
     ```
     vira as quatro linhas
     ```python
         application.add_api_route("/accounts/{account_key}", account_resource.on_delete_by_key, methods=["DELETE"])

         # Dinheiro
         application.add_api_route("/accounts/{account_key}/deposits", transaction_resource.on_post_deposit, methods=["POST"])
     ```
  O bloco das rotas fica exatamente assim (de `health_check_resource = HealthCheckResource()` até `register_error_handlers(application)`):
  ```python
      health_check_resource = HealthCheckResource()
      customer_resource = CustomerResource()
      account_resource = AccountResource()
      internal_resource = InternalResource()
      transaction_resource = TransactionResource()

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
      application.add_api_route("/accounts/{account_key}", account_resource.on_delete_by_key, methods=["DELETE"])

      # Dinheiro
      application.add_api_route("/accounts/{account_key}/deposits", transaction_resource.on_post_deposit, methods=["POST"])

      # Rotas internas (API-13): INTERNAL-TOKEN e ADMIN-TOKEN
      application.add_api_route("/internal/accounts/{account_key}/blocks", internal_resource.on_post_block, methods=["POST"])
      application.add_api_route("/internal/accounts/{account_key}/unblocks", internal_resource.on_post_unblock, methods=["POST"])

      register_error_handlers(application)
  ```

- `tests/integration/transactions/test_deposit.py` (criar; a pasta `tests/integration/transactions/` é nova e fica sem `__init__.py`): o conteúdo inteiro é:

```python
"""Depósito: POST /accounts/{account_key}/deposits (MOV-07, MOV-09, MOV-12, MOV-15, MOV-16, MOV-19, CLI-09).

Qualquer um com o INTERNAL-TOKEN deposita em qualquer conta de cliente,
informando nome e CPF ou CNPJ de quem deposita; não pede ACCOUNT-TOKEN.
O saldo sobe exatamente o valor, sem tarifa. A resposta traz só a key da
operação. Os testes que erram o token começam com DbUtils.rollback() (PRD-10).
"""

import re
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

from tests.utils import DbUtils, ObjectGenerator, PayloadGenerator, RandomGenerator, RequestGenerator


UUID_V4 = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")
PARALLEL_REQUESTS = 8


def balance_of(account: dict) -> int:
    status, response = RequestGenerator.GET_account(account["account_key"], account["account_token"])
    assert status == 200, response
    assert type(response["balance"]) is int, response

    return response["balance"]


def deposit(account: dict, payload: dict) -> tuple:
    return RequestGenerator.POST_deposit(account["account_key"], payload)


class TestDeposit:
    def test_deposits_into_account(self):
        account = ObjectGenerator.create_account()

        status, response = deposit(account, PayloadGenerator.deposit(amount=50000))

        assert status == 201, response
        assert sorted(response) == ["transaction_key"]
        assert UUID_V4.match(response["transaction_key"])
        assert balance_of(account) == 50000

        status, response = deposit(account, PayloadGenerator.deposit(amount=2550))

        assert status == 201, response
        assert balance_of(account) == 52550

    def test_deposits_with_cnpj(self):
        account = ObjectGenerator.create_account()

        status, response = deposit(account, PayloadGenerator.deposit(amount=1, depositor_document=RandomGenerator.generate_cnpj()))

        assert status == 201, response
        assert balance_of(account) == 1

    def test_refuses_invalid_document(self):
        account = ObjectGenerator.create_account()

        for depositor_document in ["123.456.789-00", "111.111.111-11", "11.222.333/0001-80", "11.111.111/1111-11"]:
            status, response = deposit(account, PayloadGenerator.deposit(depositor_document=depositor_document))

            assert status == 422, (depositor_document, response)
            assert response["code"] == "QIT001003"

        assert balance_of(account) == 0

    def test_refuses_body_out_of_schema(self):
        account = ObjectGenerator.create_account()
        bodies = []

        for amount in [0, -1, 50.5, 5050.0, "5050", True, None]:
            bodies.append(PayloadGenerator.deposit(amount=amount))

        for field in ["depositor_name", "depositor_document", "amount", "request_control_key"]:
            body = PayloadGenerator.deposit()
            del body[field]
            bodies.append(body)

        bodies.append(dict(PayloadGenerator.deposit(), extra=1))
        bodies.append(PayloadGenerator.deposit(request_control_key=str(uuid4()).upper()))
        bodies.append(PayloadGenerator.deposit(depositor_document="12345678909"))
        bodies.append(PayloadGenerator.deposit(depositor_name=""))

        for body in bodies:
            status, response = deposit(account, body)

            assert status == 400, (body, response)
            assert response["code"] == "QIT000001"

        assert balance_of(account) == 0

    def test_unknown_account_is_404(self):
        for account_key in [str(uuid4()), "nao-e-uma-key"]:
            status, response = RequestGenerator.POST_deposit(account_key, PayloadGenerator.deposit())

            assert status == 404, (account_key, response)
            assert response["code"] == "QIT001010"

    def test_blocked_or_closed_account_refuses_deposit(self):
        account = ObjectGenerator.create_account()

        status, response = RequestGenerator.POST_block(account["account_key"], PayloadGenerator.block())
        assert status == 204, response

        status, response = deposit(account, PayloadGenerator.deposit(amount=1000))
        assert status == 409, response
        assert response["code"] == "QIT001011"

        status, response = RequestGenerator.POST_unblock(account["account_key"])
        assert status == 204, response

        status, response = deposit(account, PayloadGenerator.deposit(amount=1000))
        assert status == 201, response
        assert balance_of(account) == 1000

        closed_account = ObjectGenerator.create_account()
        status, response = RequestGenerator.DELETE_account(closed_account["account_key"], closed_account["account_token"])
        assert status == 204, response

        status, response = deposit(closed_account, PayloadGenerator.deposit(amount=1000))
        assert status == 409, response
        assert response["code"] == "QIT001011"
        assert balance_of(closed_account) == 0

    def test_repeated_request_returns_first_response(self):
        account = ObjectGenerator.create_account()
        payload = PayloadGenerator.deposit(amount=3000)

        first_status, first_response = deposit(account, payload)
        second_status, second_response = deposit(account, payload)

        assert first_status == 201, first_response
        assert second_status == 201, second_response
        assert second_response == first_response
        assert balance_of(account) == 3000

    def test_same_key_with_other_request_is_409(self):
        account = ObjectGenerator.create_account()
        other_account = ObjectGenerator.create_account()
        payload = PayloadGenerator.deposit(amount=3000)

        status, response = deposit(account, payload)
        assert status == 201, response

        for target, body in [(account, dict(payload, amount=3001)), (other_account, payload)]:
            status, response = deposit(target, body)

            assert status == 409, (body, response)
            assert response["code"] == "QIT001014"

        assert balance_of(account) == 3000
        assert balance_of(other_account) == 0

    def test_refused_request_does_not_keep_the_key(self):
        account = ObjectGenerator.create_account()
        request_control_key = str(uuid4())

        status, response = deposit(account, PayloadGenerator.deposit(depositor_document="123.456.789-00", request_control_key=request_control_key))
        assert status == 422, response

        status, response = deposit(account, PayloadGenerator.deposit(amount=700, request_control_key=request_control_key))
        assert status == 201, response
        assert balance_of(account) == 700

    def test_requires_internal_token(self):
        DbUtils.rollback()
        account = ObjectGenerator.create_account()

        for internal_token in [None, "token_errado"]:
            status, response = RequestGenerator.POST_deposit(account["account_key"], PayloadGenerator.deposit(), internal_token=internal_token)

            assert status == 403, (internal_token, response)
            assert response["code"] == "QIT000002"

        status, response = deposit(account, PayloadGenerator.deposit(amount=100))
        assert status == 201, response
        assert balance_of(account) == 100

    def test_concurrent_same_key(self):
        account = ObjectGenerator.create_account()
        payload = PayloadGenerator.deposit(amount=4000)

        with ThreadPoolExecutor(max_workers=PARALLEL_REQUESTS) as executor:
            results = list(executor.map(lambda _index: deposit(account, payload), range(PARALLEL_REQUESTS)))

        assert [status for status, _response in results] == [201] * PARALLEL_REQUESTS, results
        assert len({response["transaction_key"] for _status, response in results}) == 1, results
        assert balance_of(account) == 4000
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/06-dinheiro`; `git log --oneline` mostra `feat(deposito): controller do depósito com idempotência`.
2. Crie `tests/integration/transactions/test_deposit.py` com o conteúdo do campo **Arquivos**.
3. `docker compose up -d --build --wait`.
4. `./.venv/Scripts/python.exe -m pytest -v tests/integration/transactions/test_deposit.py` → a última linha tem `11 failed` e não tem `passed`. Os 11 falham por asserção: hoje o caminho `/accounts/{account_key}/deposits` não existe e responde 404 `QIT000404` (em `test_requires_internal_token`, os dois 403 passam e a falha é o depósito com o token certo).
5. Crie `src/resources/transaction.py` com o conteúdo do campo **Arquivos**.
6. Edite `src/resources/__init__.py` com o conteúdo do campo **Arquivos**.
7. Faça as três trocas em `src/app.py` e confira o bloco das rotas contra o do campo **Arquivos**.
8. `docker compose up -d --build --wait`.
9. `./.venv/Scripts/python.exe -m pytest -v tests/integration/transactions/test_deposit.py` → a última linha tem `11 passed`.
10. Rode a conferência D2 do **Verificar**.
11. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `149 passed`.
12. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
13. Feche o passo (AGENTS.md, seção 7), um comando por vez:
    ```
    git add -- src/resources/transaction.py src/resources/__init__.py src/app.py tests/integration/transactions/test_deposit.py
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "feat(deposito): rota de depósito"
    git log -1 --format=%B
    ```

**Testes:** `tests/integration/transactions/test_deposit.py`. Efeito no banco de cada 201: uma linha em `transaction` (`DEPOSIT`, com a `request_control_key`, o `request_hash` e a data do relógio), dois lançamentos (`OUTSIDE_WORLD` −valor com `balance_after` nulo; a conta +valor com o saldo novo), uma linha em `deposits` e o `balance` da conta somado; as recusas não gravam nada além da linha de `request_log`.

| Função de teste | Entrada | Esperado |
|---|---|---|
| `test_deposits_into_account` | conta nova; depósito de 50000 com CPF, sem `ACCOUNT-TOKEN`; depois 2550 | 201; o corpo tem exatamente `transaction_key` (UUID v4); saldo 50000 e depois 52550, inteiro (MOV-09: sem tarifa) |
| `test_deposits_with_cnpj` | depósito de 1 centavo com CNPJ válido | 201; saldo 1 |
| `test_refuses_invalid_document` | `123.456.789-00`, `111.111.111-11`, `11.222.333/0001-80`, `11.111.111/1111-11` | 422 `QIT001003` nos quatro; saldo 0 |
| `test_refuses_body_out_of_schema` | `amount` 0, −1, 50.5, 5050.0, `"5050"`, `true`, `null`; cada um dos 4 campos faltando; campo `extra`; `request_control_key` em maiúsculas; documento sem pontos; nome vazio | 400 `QIT000001` nos 15; saldo 0 (API-18) |
| `test_unknown_account_is_404` | key UUID que não existe; `nao-e-uma-key` | 404 `QIT001010` nos dois |
| `test_blocked_or_closed_account_refuses_deposit` | conta bloqueada; desbloqueio; conta encerrada | 409 `QIT001011`; 201 e saldo 1000; 409 `QIT001011` e saldo 0 (CLI-09) |
| `test_repeated_request_returns_first_response` | o mesmo corpo duas vezes | 201 duas vezes, corpos iguais; saldo 3000, uma vez só (MOV-12) |
| `test_same_key_with_other_request_is_409` | a mesma chave com outro `amount`; a mesma chave e o mesmo corpo em outra conta | 409 `QIT001014` nos dois; saldos 3000 e 0 |
| `test_refused_request_does_not_keep_the_key` | chave K com CPF errado; depois K num depósito válido | 422; depois 201 e saldo 700 (MOV-12: pedido barrado não guarda a chave) |
| `test_requires_internal_token` | começa com `DbUtils.rollback()`; sem `INTERNAL-TOKEN` e com `token_errado`; depois com o token certo | 403 `QIT000002` nos dois; 201 e saldo 100 |
| `test_concurrent_same_key` | 8 depósitos iguais ao mesmo tempo | oito 201 com a mesma `transaction_key`; saldo 4000 (MOV-19: o `IntegrityError` vira repetição, nunca 500) |

**Verificar:**
- `./.venv/Scripts/python.exe -m pytest -v tests/integration/transactions/test_deposit.py` → `11 passed`.
- D2 — o que o depósito grava (MOV-16, DAD-09, DAD-17, MOV-19). Um comando, numa linha só:
  ```
  ./.venv/Scripts/python.exe -c "from sqlalchemy import create_engine, text; from tests.utils import DbUtils, ObjectGenerator, PayloadGenerator, RequestGenerator; a = ObjectGenerator.create_account(); p = PayloadGenerator.deposit(amount=5050, depositor_name='Carlos Souza', depositor_document='11.222.333/0001-81'); s, r = RequestGenerator.POST_deposit(a['account_key'], p); print(s, sorted(r)); c = create_engine(DbUtils.database_url()).connect(); k = {'t': r['transaction_key'], 'r': p['request_control_key']}; print(c.execute(text('SELECT y.enumerator, x.accounting_date = b.accounting_date, length(x.request_hash), x.request_control_key = :r FROM transaction x JOIN transaction_type y ON y.id = x.transaction_type_id CROSS JOIN bank_clock b WHERE x.transaction_key = :t'), k).fetchall()); print(c.execute(text('SELECT t.enumerator, y.enumerator, e.amount, e.balance_after FROM entry e JOIN transaction x ON x.id = e.transaction_id JOIN account m ON m.id = e.account_id JOIN account_type t ON t.id = m.account_type_id JOIN entry_type y ON y.id = e.entry_type_id WHERE x.transaction_key = :t ORDER BY e.id'), k).fetchall()); print(c.execute(text('SELECT d.depositor_name, d.depositor_document, length(d.deposit_key) FROM deposits d JOIN transaction x ON x.id = d.transaction_id WHERE x.transaction_key = :t'), k).fetchall()); print(c.execute(text('SELECT balance FROM account WHERE account_type_id IN (3, 4) ORDER BY id')).fetchall())"
  ```
  → exatamente:
  ```
  201 ['transaction_key']
  [('DEPOSIT', True, 64, True)]
  [('OUTSIDE_WORLD', 'AMOUNT', -5050, None), ('CUSTOMER', 'AMOUNT', 5050, 5050)]
  [('Carlos Souza', '11.222.333/0001-81', 36)]
  [(None,), (None,)]
  ```
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `149 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/app.py
  src/resources/__init__.py
  src/resources/transaction.py
  tests/integration/transactions/test_deposit.py
  ```
- `git log -1 --format=%B` → `feat(deposito): rota de depósito`

**Pronto quando:**
- [ ] Os 11 testes falharam antes do código (item 4) e passam depois (item 9).
- [ ] A D2 dá as 5 linhas esperadas.
- [ ] Suíte com `149 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/06-dinheiro`.

**Commit:** `feat(deposito): rota de depósito`
**Pare se:**
- O item 4 não terminar com `11 failed`.
- Um teste receber 500 (`QIT000500`): rode `docker compose logs --tail 100 api` e traga a saída.
- `test_concurrent_same_key` falhar em uma de três rodadas seguidas do item 9.
- A D2 der outra saída depois de 3 tentativas de conferir os arquivos do passo contra o plano.
- A suíte não terminar com `149 passed`.

---

### Passo 6.6 — Saque
**Branch:** fase/06-dinheiro · **Depende de:** 6.5
**Objetivo:** `TransactionController.withdraw` e a rota `POST /accounts/{account_key}/withdrawals` (tokens: conta; schema `post_withdrawals.json`): só o dono, repetição, trava, conta `ACTIVE`, saldo suficiente; operação `WITHDRAWAL` (conta − e `OUTSIDE_WORLD` +); 201 com `{"transaction_key", "balance"}`; 404 `QIT001010`; 409 `QIT001011`; 422 `QIT001015`; 409 `QIT001014`; 400 `QIT000001`.
**Decisões:** MOV-07 — operações · MOV-08 — o que barra · MOV-09 — saque sem tarifa · MOV-15 — só o dono saca · MOV-05 — trava no saldo · MOV-12, MOV-19 — idempotência e resposta remontada · CLI-09 — bloqueada ou encerrada → 409 · R8 — outro dono → 404 · API-10 — key e saldo novo · TST-01 — black box e TDD
**Arquivos:**
- `src/controllers/transaction_controller.py` (editar): três mudanças, e nada mais.
  1. Tudo o que vem antes da linha `class TransactionController(BaseController):` passa a ser exatamente o bloco abaixo (seguido de duas linhas em branco antes do `class`):

```python
from sqlalchemy.exc import IntegrityError

from controllers.base_controller import BaseController
from dtos import TransactionDTO
from errors import (
    AccountNotActive,
    AccountNotFound,
    IdempotencyKeyConflict,
    InsufficientBalance,
    InvalidDocumentNumber,
)
from models import Account, AccountStatus, AccountType, EntryType, Transaction, TransactionType
from repositories import AccountRepository, BankClockRepository, DepositRepository, EntryRepository, TransactionRepository
from utils.document_number import FORMATTED_CPF_LENGTH, is_valid_cnpj, is_valid_cpf
from utils.request_hash import hash_request_body
```

  2. O método `withdraw` abaixo entra logo depois do método `deposit` e antes de `_find_repeated`, com uma linha em branco antes dele:

```python
    def withdraw(self, account_key: str, account_token: str, withdrawal_data: dict) -> dict:
        """Saque: o dinheiro vai para a conta OUTSIDE_WORLD (MOV-07, MOV-15). As regras, nesta ordem:

        1. a conta é do dono do token (404 QIT001010, R8): só o dono saca;
        2. a mesma request_control_key com o mesmo pedido devolve a resposta
           da primeira vez, com o saldo de depois daquele saque (MOV-19);
           com outro pedido, 409 QIT001014 (MOV-12);
        3. trava a conta (MOV-05);
        4. a conta está ACTIVE (409 QIT001011, CLI-09);
        5. o saldo cobre o valor (422 QIT001015, MOV-08).

        Depois: a operação WITHDRAWAL, o AMOUNT −valor na conta e o AMOUNT
        +valor na OUTSIDE_WORLD. Sem tarifa (MOV-09). A resposta traz a key
        e o saldo novo.
        """
        account = self.get_owned_account(account_key, account_token)

        request_control_key = withdrawal_data["request_control_key"]
        request_hash = hash_request_body(TransactionType.WITHDRAWAL, account_key, withdrawal_data)

        repeated_transaction = self._find_repeated(request_control_key, request_hash)
        if repeated_transaction is not None:
            return TransactionDTO.with_balance(repeated_transaction, self._balance_after(repeated_transaction, account))

        accounting_date = self.bank_clock_repository.get_accounting_date()
        account = self.account_repository.lock_accounts([account])[0]

        # Uma chamada com a mesma chave pode ter concluído enquanto esta esperava a trava.
        repeated_transaction = self._find_repeated(request_control_key, request_hash)
        if repeated_transaction is not None:
            return TransactionDTO.with_balance(repeated_transaction, self._balance_after(repeated_transaction, account))

        if account.status.enumerator != AccountStatus.ACTIVE:
            raise AccountNotActive(account_key, account.status.enumerator)

        amount = withdrawal_data["amount"]

        if account.balance < amount:
            raise InsufficientBalance(account_key)

        outside_world = self.account_repository.get_system_account(AccountType.OUTSIDE_WORLD)

        try:
            transaction = self.transaction_repository.create(TransactionType.WITHDRAWAL, request_control_key, request_hash, accounting_date)
            self.entry_repository.create(transaction, account, EntryType.AMOUNT, -amount)
            self.entry_repository.create(transaction, outside_world, EntryType.AMOUNT, amount)

            transaction_dto = TransactionDTO.with_balance(transaction, account.balance)
            self.logger.info("operation_ready_to_commit transaction_key=%s", transaction.transaction_key)
            self.session.commit()
        except IntegrityError:
            self.session.rollback()

            repeated_transaction = self._find_repeated(request_control_key, request_hash)
            if repeated_transaction is None:
                raise

            return TransactionDTO.with_balance(repeated_transaction, self._balance_after(repeated_transaction, account))

        return transaction_dto
```

  3. O método `_balance_after` abaixo entra no fim da classe, logo depois de `_is_valid_depositor_document`, com uma linha em branco antes dele:

```python
    def _balance_after(self, transaction: Transaction, account: Account) -> int:
        """O saldo da conta logo depois da operação: o balance_after do último lançamento dela na operação (MOV-19)."""
        entries = self.entry_repository.list_by_transaction(transaction, [account.id])

        return entries[-1].balance_after
```

- `src/resources/transaction.py` (editar): o conteúdo inteiro passa a ser:

```python
from fastapi import Request
from fastapi import status as http_status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from constants import ACCOUNT_TOKEN_HEADER
from controllers import TransactionController
from utils.schema_handler import SchemaHandler


class TransactionResource:
    """A porta HTTP do dinheiro: depósito, saque, transferência, consulta e extrato.

    Sem regra de negócio, sem SQL e sem nada guardado no self (ARQ-02). O
    token da conta chega no cabeçalho ACCOUNT-TOKEN (API-16); quem o
    confere é o controller.
    """

    @SchemaHandler.validate("post_deposits.json")
    def on_post_deposit(self, account_key: str, payload: dict) -> JSONResponse:
        controller = TransactionController()
        transaction = controller.deposit(account_key, payload)

        return JSONResponse(
            content=jsonable_encoder(transaction),
            status_code=http_status.HTTP_201_CREATED,
        )

    @SchemaHandler.validate("post_withdrawals.json")
    def on_post_withdrawal(self, account_key: str, payload: dict, request: Request) -> JSONResponse:
        controller = TransactionController()
        transaction = controller.withdraw(account_key, request.headers.get(ACCOUNT_TOKEN_HEADER), payload)

        return JSONResponse(
            content=jsonable_encoder(transaction),
            status_code=http_status.HTTP_201_CREATED,
        )
```

- `src/app.py` (editar): uma troca, e nada mais. A linha
  ```python
      application.add_api_route("/accounts/{account_key}/deposits", transaction_resource.on_post_deposit, methods=["POST"])
  ```
  vira as duas linhas
  ```python
      application.add_api_route("/accounts/{account_key}/deposits", transaction_resource.on_post_deposit, methods=["POST"])
      application.add_api_route("/accounts/{account_key}/withdrawals", transaction_resource.on_post_withdrawal, methods=["POST"])
  ```

- `tests/integration/transactions/test_withdrawal.py` (criar): o conteúdo inteiro é:

```python
"""Saque: POST /accounts/{account_key}/withdrawals (MOV-05, MOV-07, MOV-08, MOV-09, MOV-12, MOV-15, MOV-19, CLI-09, R8).

Só o dono saca, com o ACCOUNT-TOKEN. O saldo cai exatamente o valor, sem
tarifa, e nunca fica negativo. A resposta traz a key da operação e o
saldo novo. Os testes que erram o token começam com DbUtils.rollback() (PRD-10).
"""

import re
from concurrent.futures import ThreadPoolExecutor

from tests.utils import DbUtils, ObjectGenerator, PayloadGenerator, RequestGenerator


UUID_V4 = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")
PARALLEL_REQUESTS = 8


def balance_of(account: dict) -> int:
    status, response = RequestGenerator.GET_account(account["account_key"], account["account_token"])
    assert status == 200, response
    assert type(response["balance"]) is int, response

    return response["balance"]


def withdraw(account: dict, payload: dict) -> tuple:
    """Saca da conta com o token dela."""
    return RequestGenerator.POST_withdrawal(account["account_key"], account["account_token"], payload)


class TestWithdrawal:
    def test_withdraws(self):
        account = ObjectGenerator.create_funded_account(100000)

        status, response = withdraw(account, PayloadGenerator.withdrawal(amount=30000))

        assert status == 201, response
        assert sorted(response) == ["balance", "transaction_key"]
        assert UUID_V4.match(response["transaction_key"])
        assert type(response["balance"]) is int
        assert response["balance"] == 70000
        assert balance_of(account) == 70000

    def test_withdraws_the_whole_balance(self):
        account = ObjectGenerator.create_funded_account(5000)

        status, response = withdraw(account, PayloadGenerator.withdrawal(amount=5000))

        assert status == 201, response
        assert response["balance"] == 0
        assert balance_of(account) == 0

    def test_refuses_insufficient_balance(self):
        account = ObjectGenerator.create_funded_account(5000)

        status, response = withdraw(account, PayloadGenerator.withdrawal(amount=5001))
        assert status == 422, response
        assert response["code"] == "QIT001015"
        assert balance_of(account) == 5000

        empty_account = ObjectGenerator.create_account()

        status, response = withdraw(empty_account, PayloadGenerator.withdrawal(amount=1))
        assert status == 422, response
        assert response["code"] == "QIT001015"
        assert balance_of(empty_account) == 0

    def test_refuses_body_out_of_schema(self):
        account = ObjectGenerator.create_funded_account(5000)
        bodies = []

        for amount in [0, -1, 1.5, 1000.0, "1000", True]:
            bodies.append(PayloadGenerator.withdrawal(amount=amount))

        for field in ["amount", "request_control_key"]:
            body = PayloadGenerator.withdrawal()
            del body[field]
            bodies.append(body)

        bodies.append(dict(PayloadGenerator.withdrawal(), extra=1))

        for body in bodies:
            status, response = withdraw(account, body)

            assert status == 400, (body, response)
            assert response["code"] == "QIT000001"

        assert balance_of(account) == 5000

    def test_blocked_or_closed_account_refuses_withdrawal(self):
        account = ObjectGenerator.create_funded_account(5000)

        status, response = RequestGenerator.POST_block(account["account_key"], PayloadGenerator.block())
        assert status == 204, response

        status, response = withdraw(account, PayloadGenerator.withdrawal(amount=1000))
        assert status == 409, response
        assert response["code"] == "QIT001011"
        assert balance_of(account) == 5000

        status, response = RequestGenerator.POST_unblock(account["account_key"])
        assert status == 204, response

        status, response = withdraw(account, PayloadGenerator.withdrawal(amount=5000))
        assert status == 201, response

        status, response = RequestGenerator.DELETE_account(account["account_key"], account["account_token"])
        assert status == 204, response

        status, response = withdraw(account, PayloadGenerator.withdrawal(amount=1))
        assert status == 409, response
        assert response["code"] == "QIT001011"

    def test_other_account_token_is_404(self):
        DbUtils.rollback()
        account = ObjectGenerator.create_funded_account(5000)
        other_account = ObjectGenerator.create_account()

        status, response = RequestGenerator.POST_withdrawal(account["account_key"], other_account["account_token"], PayloadGenerator.withdrawal(amount=1000))
        assert status == 404, response
        assert response["code"] == "QIT001010"
        assert balance_of(account) == 5000

        status, response = withdraw(account, PayloadGenerator.withdrawal(amount=1000))
        assert status == 201, response
        assert balance_of(account) == 4000

    def test_missing_or_wrong_token_is_404(self):
        DbUtils.rollback()
        account = ObjectGenerator.create_funded_account(5000)

        for account_token in [None, "token_errado"]:
            status, response = RequestGenerator.POST_withdrawal(account["account_key"], account_token, PayloadGenerator.withdrawal(amount=1000))

            assert status == 404, (account_token, response)
            assert response["code"] == "QIT001010"

        assert balance_of(account) == 5000

    def test_repeated_request_returns_first_response(self):
        account = ObjectGenerator.create_funded_account(10000)
        payload = PayloadGenerator.withdrawal(amount=3000)

        first_status, first_response = withdraw(account, payload)
        second_status, second_response = withdraw(account, payload)

        assert first_status == 201, first_response
        assert second_status == 201, second_response
        assert second_response == first_response
        assert first_response["balance"] == 7000

        status, response = withdraw(account, PayloadGenerator.withdrawal(amount=2000))
        assert status == 201, response

        third_status, third_response = withdraw(account, payload)
        assert third_status == 201, third_response
        assert third_response == first_response
        assert balance_of(account) == 5000

        # A repetição simultânea deve passar mesmo quando a primeira esgota o saldo.
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier

        raced = ObjectGenerator.create_funded_account(1000)
        raced_payload = PayloadGenerator.withdrawal(amount=1000)
        gate = Barrier(2)

        def send_same(_index):
            gate.wait(timeout=5)
            return withdraw(raced, raced_payload)

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(send_same, range(2)))

        assert results[0][0] == 201, results
        assert results == [results[0], results[0]], results
        assert balance_of(raced) == 0


    def test_same_key_with_other_request_is_409(self):
        account = ObjectGenerator.create_funded_account(10000)
        payload = PayloadGenerator.withdrawal(amount=3000)

        status, response = withdraw(account, payload)
        assert status == 201, response

        status, response = withdraw(account, dict(payload, amount=3001))
        assert status == 409, response
        assert response["code"] == "QIT001014"

        deposit_payload = PayloadGenerator.deposit(amount=3000, request_control_key=payload["request_control_key"])
        status, response = RequestGenerator.POST_deposit(account["account_key"], deposit_payload)
        assert status == 409, response
        assert response["code"] == "QIT001014"

        assert balance_of(account) == 7000

    def test_concurrent_withdrawals_never_go_negative(self):
        account = ObjectGenerator.create_funded_account(10000)
        payloads = [PayloadGenerator.withdrawal(amount=3000) for _index in range(PARALLEL_REQUESTS)]

        with ThreadPoolExecutor(max_workers=PARALLEL_REQUESTS) as executor:
            results = list(executor.map(lambda payload: withdraw(account, payload), payloads))

        statuses = sorted(status for status, _response in results)
        assert statuses == [201] * 3 + [422] * (PARALLEL_REQUESTS - 3), results
        assert balance_of(account) == 1000
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/06-dinheiro`; `git log --oneline` mostra `feat(deposito): rota de depósito`.
2. Crie `tests/integration/transactions/test_withdrawal.py` com o conteúdo do campo **Arquivos**.
3. `docker compose up -d --build --wait`.
4. `./.venv/Scripts/python.exe -m pytest -v tests/integration/transactions/test_withdrawal.py` → a última linha tem `10 failed` e não tem `passed`. Os 10 falham por asserção: hoje o caminho `/accounts/{account_key}/withdrawals` responde 404 `QIT000404`.
5. Faça as três mudanças em `src/controllers/transaction_controller.py`.
6. Edite `src/resources/transaction.py` com o conteúdo do campo **Arquivos**.
7. Faça a troca em `src/app.py`.
8. `docker compose up -d --build --wait`.
9. `./.venv/Scripts/python.exe -m pytest -v tests/integration/transactions/test_withdrawal.py` → a última linha tem `10 passed`.
10. Rode as conferências S2 e W1 do **Verificar**.
11. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `159 passed`.
12. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
13. Feche o passo (AGENTS.md, seção 7), um comando por vez:
    ```
    git add -- src/controllers/transaction_controller.py src/resources/transaction.py src/app.py tests/integration/transactions/test_withdrawal.py
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "feat(saque): rota de saque pelo dono"
    git log -1 --format=%B
    ```

**Testes:** `tests/integration/transactions/test_withdrawal.py`. Efeito no banco de cada 201: uma linha em `transaction` (`WITHDRAWAL`), o lançamento da conta (−valor, com o saldo novo) e o da `OUTSIDE_WORLD` (+valor, `balance_after` nulo), e o `balance` da conta diminuído; as recusas não gravam nada além da linha de `request_log`.

| Função de teste | Entrada | Esperado |
|---|---|---|
| `test_withdraws` | conta com 100000; saque de 30000 | 201; o corpo tem exatamente `transaction_key` (UUID v4) e `balance` (inteiro) = 70000; saldo 70000 (MOV-09: sem tarifa) |
| `test_withdraws_the_whole_balance` | conta com 5000; saque de 5000 | 201 com `balance` 0; saldo 0 |
| `test_refuses_insufficient_balance` | conta com 5000, saque de 5001; conta vazia, saque de 1 | 422 `QIT001015` nos dois; saldos 5000 e 0 |
| `test_refuses_body_out_of_schema` | `amount` 0, −1, 1.5, 1000.0, `"1000"`, `true`; cada campo faltando; campo `extra` | 400 `QIT000001` nos 9; saldo 5000 (API-18) |
| `test_blocked_or_closed_account_refuses_withdrawal` | bloqueada; desbloqueio e saque de tudo; encerrada | 409 `QIT001011` e saldo 5000; 201; 409 `QIT001011` (CLI-09) |
| `test_other_account_token_is_404` | começa com `DbUtils.rollback()`; saque da conta A com o token de B; depois com o de A | 404 `QIT001010` e saldo 5000; 201 e saldo 4000 (MOV-15, R8) |
| `test_missing_or_wrong_token_is_404` | começa com `DbUtils.rollback()`; sem `ACCOUNT-TOKEN` e com `token_errado` | 404 `QIT001010` nos dois; saldo 5000 |
| `test_repeated_request_returns_first_response` | o mesmo saque de 3000 duas vezes; outro saque de 2000; o primeiro corpo de novo | 201 com o mesmo corpo da primeira vez (`balance` 7000) nas três; saldo 5000 (MOV-19: o saldo vem do `balance_after` da primeira vez) |
| `test_same_key_with_other_request_is_409` | a mesma chave com outro `amount`; a mesma chave num depósito | 409 `QIT001014` nos dois; saldo 7000 |
| `test_concurrent_withdrawals_never_go_negative` | conta com 10000; 8 saques de 3000 ao mesmo tempo, cada um com a sua chave | três 201 e cinco 422; saldo 1000 (MOV-05) |

**Verificar:**
- `./.venv/Scripts/python.exe -m pytest -v tests/integration/transactions/test_withdrawal.py` → `10 passed`.
- S2 (um comando, numa linha só):
  ```
  docker compose exec -T api python -c "from controllers import TransactionController; print(sorted(n for n in vars(TransactionController) if not n.startswith('__')))"
  ```
  → `['_balance_after', '_find_repeated', '_is_valid_depositor_document', 'deposit', 'withdraw']`
- W1 — o que o saque grava (MOV-07, DAD-09). Um comando, numa linha só:
  ```
  ./.venv/Scripts/python.exe -c "from sqlalchemy import create_engine, text; from tests.utils import DbUtils, ObjectGenerator, PayloadGenerator, RequestGenerator; a = ObjectGenerator.create_funded_account(10000); s, r = RequestGenerator.POST_withdrawal(a['account_key'], a['account_token'], PayloadGenerator.withdrawal(amount=3000)); print(s, r['balance']); c = create_engine(DbUtils.database_url()).connect(); print(c.execute(text('SELECT y.enumerator, t.enumerator, w.enumerator, e.amount, e.balance_after FROM entry e JOIN transaction x ON x.id = e.transaction_id JOIN transaction_type y ON y.id = x.transaction_type_id JOIN account m ON m.id = e.account_id JOIN account_type t ON t.id = m.account_type_id JOIN entry_type w ON w.id = e.entry_type_id WHERE x.transaction_key = :t ORDER BY e.id'), {'t': r['transaction_key']}).fetchall())"
  ```
  → exatamente:
  ```
  201 7000
  [('WITHDRAWAL', 'CUSTOMER', 'AMOUNT', -3000, 7000), ('WITHDRAWAL', 'OUTSIDE_WORLD', 'AMOUNT', 3000, None)]
  ```
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `159 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/app.py
  src/controllers/transaction_controller.py
  src/resources/transaction.py
  tests/integration/transactions/test_withdrawal.py
  ```
- `git log -1 --format=%B` → `feat(saque): rota de saque pelo dono`

**Pronto quando:**
- [ ] Os 10 testes falharam antes do código (item 4) e passam depois (item 9).
- [ ] S2 e W1 dão a saída esperada.
- [ ] Suíte com `159 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/06-dinheiro`.

**Commit:** `feat(saque): rota de saque pelo dono`
**Pare se:**
- O item 4 não terminar com `10 failed`.
- Um teste receber 500 (`QIT000500`) ou o lint acusar `F401` ou `F821` em `transaction_controller.py`: confira o bloco de imports da mudança 1; persistindo, traga `docker compose logs --tail 100 api` e a saída do lint.
- `test_concurrent_withdrawals_never_go_negative` falhar em uma de três rodadas seguidas do item 9.
- A suíte não terminar com `159 passed`.

---

### Passo 6.7 — Transferência: controller
**Branch:** fase/06-dinheiro · **Depende de:** 6.6
**Objetivo:** `TransactionController.transfer`: dono → repetição → trava das duas contas na ordem do `id` → origem ativa → origem diferente do destino → destino existe → destino ativo → saldo cobre valor + `calculate_fee(amount, 0)`; operação `TRANSFER` com os quatro lançamentos; tarifa zero não gera lançamento. O limite diário fica para o 6.9.
**Decisões:** MOV-01 — sem saldo barra · MOV-02 — valor + tarifa · MOV-03 — toda transferência tem tarifa · MOV-05 — trava no saldo · MOV-06 — 1% · MOV-08 — o que barra · MOV-09 — quem envia paga · MOV-10 — tarifa zero sem lançamento · MOV-11 — ordem das travas · MOV-12, MOV-19 — idempotência · DAD-16 — tarifa como lançamento · CLI-09 — bloqueada não envia nem recebe · R8 — outro dono → 404
**Arquivos:**
- `src/controllers/transaction_controller.py` (editar): duas mudanças, e nada mais.
  1. Tudo o que vem antes da linha `class TransactionController(BaseController):` passa a ser exatamente o bloco abaixo (seguido de duas linhas em branco antes do `class`):

```python
from sqlalchemy.exc import IntegrityError

from calculations import calculate_fee
from controllers.base_controller import BaseController
from dtos import TransactionDTO
from errors import (
    AccountNotActive,
    AccountNotFound,
    DestinationAccountNotActive,
    DestinationAccountNotFound,
    IdempotencyKeyConflict,
    InsufficientBalance,
    InvalidDocumentNumber,
    SameAccountTransfer,
)
from models import Account, AccountStatus, AccountType, EntryType, Transaction, TransactionType
from repositories import AccountRepository, BankClockRepository, DepositRepository, EntryRepository, TransactionRepository
from utils.document_number import FORMATTED_CPF_LENGTH, is_valid_cnpj, is_valid_cpf
from utils.request_hash import hash_request_body
```

  2. O método `transfer` abaixo entra logo depois do método `withdraw` e antes de `_find_repeated`, com uma linha em branco antes dele:

```python
    def transfer(self, account_key: str, account_token: str, transfer_data: dict) -> dict:
        """Transferência entre contas de cliente, com tarifa (MOV-01 a MOV-03, MOV-06, MOV-09, DAD-16). As regras, nesta ordem:

        1. a conta de origem é do dono do token (404 QIT001010, R8);
        2. a mesma request_control_key com o mesmo pedido devolve a resposta
           da primeira vez, com o saldo de depois daquela transferência
           (MOV-19); com outro pedido, 409 QIT001014 (MOV-12);
        3. trava a origem e, se o destino existe e é de cliente, também o
           destino, as duas na ordem do id (MOV-05, MOV-11);
        4. a origem está ACTIVE (409 QIT001011, CLI-09);
        5. a origem é diferente do destino (422 QIT001016, MOV-08);
        6. o destino existe e é de cliente (404 QIT001017);
        7. o destino está ACTIVE (409 QIT001018, CLI-09);
        8. o saldo da origem cobre valor + tarifa (422 QIT001015, MOV-01,
           MOV-02); a tarifa é calculate_fee(valor, 0): os pontos entram
           no passo 8.7;
        9. o limite diário (CLI-08) entra no passo 6.9.

        Depois: a operação TRANSFER e os lançamentos, nesta ordem: AMOUNT
        −valor e FEE −tarifa na origem; AMOUNT +valor no destino; FEE
        +tarifa na conta BANK. Tarifa zero não gera lançamento (MOV-10). A
        resposta traz a key e o saldo novo da origem (API-10).
        """
        account = self.get_owned_account(account_key, account_token)

        request_control_key = transfer_data["request_control_key"]
        request_hash = hash_request_body(TransactionType.TRANSFER, account_key, transfer_data)

        repeated_transaction = self._find_repeated(request_control_key, request_hash)
        if repeated_transaction is not None:
            return TransactionDTO.with_balance(repeated_transaction, self._balance_after(repeated_transaction, account))

        accounting_date = self.bank_clock_repository.get_accounting_date()

        destination_account_key = transfer_data["destination_account_key"]
        destination = self.account_repository.get_customer_account(destination_account_key)

        accounts_to_lock = [account]
        if destination is not None:
            accounts_to_lock.append(destination)

        locked_accounts = {}
        for locked_account in self.account_repository.lock_accounts(accounts_to_lock):
            locked_accounts[locked_account.id] = locked_account

        account = locked_accounts[account.id]
        if destination is not None:
            destination = locked_accounts[destination.id]

        # Uma chamada com a mesma chave pode ter concluído enquanto esta esperava a trava.
        repeated_transaction = self._find_repeated(request_control_key, request_hash)
        if repeated_transaction is not None:
            return TransactionDTO.with_balance(repeated_transaction, self._balance_after(repeated_transaction, account))

        if account.status.enumerator != AccountStatus.ACTIVE:
            raise AccountNotActive(account_key, account.status.enumerator)

        if destination_account_key == account.account_key:
            raise SameAccountTransfer()

        if destination is None:
            raise DestinationAccountNotFound(destination_account_key)

        if destination.status.enumerator != AccountStatus.ACTIVE:
            raise DestinationAccountNotActive(destination_account_key)

        amount = transfer_data["amount"]
        fee = calculate_fee(amount, 0)

        if account.balance < amount + fee:
            raise InsufficientBalance(account_key)

        bank = self.account_repository.get_system_account(AccountType.BANK)

        try:
            transaction = self.transaction_repository.create(TransactionType.TRANSFER, request_control_key, request_hash, accounting_date)
            self.entry_repository.create(transaction, account, EntryType.AMOUNT, -amount)

            if fee > 0:
                self.entry_repository.create(transaction, account, EntryType.FEE, -fee)

            self.entry_repository.create(transaction, destination, EntryType.AMOUNT, amount)

            if fee > 0:
                self.entry_repository.create(transaction, bank, EntryType.FEE, fee)

            transaction_dto = TransactionDTO.with_balance(transaction, account.balance)
            self.logger.info("operation_ready_to_commit transaction_key=%s", transaction.transaction_key)
            self.session.commit()
        except IntegrityError:
            self.session.rollback()

            repeated_transaction = self._find_repeated(request_control_key, request_hash)
            if repeated_transaction is None:
                raise

            return TransactionDTO.with_balance(repeated_transaction, self._balance_after(repeated_transaction, account))

        return transaction_dto
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/06-dinheiro`; `git log --oneline` mostra `feat(saque): rota de saque pelo dono`.
2. Faça as duas mudanças em `src/controllers/transaction_controller.py`.
3. `docker compose up -d --build --wait` → termina sem erro.
4. Rode a conferência S3 do **Verificar**.
5. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `159 passed`.
6. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
7. Feche o passo (AGENTS.md, seção 7), um comando por vez:
   ```
   git add -- src/controllers/transaction_controller.py
   git diff --cached --name-only
   git diff --name-only
   git ls-files --others --exclude-standard
   git commit -m "feat(transferencia): controller da transferência com tarifa e travas"
   git log -1 --format=%B
   ```

**Testes:** nenhum teste novo. A rota nasce no 6.8, com os 15 testes que ficam vermelhos antes dela. Aqui, a prova é a S3.
**Verificar:**
- S3 (um comando, numa linha só):
  ```
  docker compose exec -T api python -c "import inspect; from controllers import TransactionController; print(sorted(n for n in vars(TransactionController) if not n.startswith('__'))); src = inspect.getsource(TransactionController.transfer); print(src.count('raise '), 'calculate_fee(amount, 0)' in src, src.count('if fee > 0:'), 'DAILY_TRANSFER_LIMIT' in src)"
  ```
  → exatamente:
  ```
  ['_balance_after', '_find_repeated', '_is_valid_depositor_document', 'deposit', 'transfer', 'withdraw']
  5 True 2 False
  ```
  (os 5 `raise ` com espaço: origem não ativa, mesma conta, destino não existe, destino não ativo e saldo insuficiente; o `raise` sozinho do `IntegrityError` não entra na conta)
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `159 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente `src/controllers/transaction_controller.py`.
- `git log -1 --format=%B` → `feat(transferencia): controller da transferência com tarifa e travas`

**Pronto quando:**
- [ ] O arquivo tem o bloco de imports e o método `transfer` exatamente como no campo **Arquivos**.
- [ ] A S3 dá as 2 linhas esperadas.
- [ ] Suíte com `159 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/06-dinheiro`.

**Commit:** `feat(transferencia): controller da transferência com tarifa e travas`
**Pare se:**
- `docker compose up -d --build --wait` falhar com `ImportError` no `docker compose logs --tail 100 api`: traga a saída.
- A S3 der outra saída depois de 3 tentativas de conferir o arquivo contra o plano.
- O lint acusar `F401` ou `F821`.
- A suíte não terminar com `159 passed`.

---

### Passo 6.8 — `POST /accounts/{account_key}/transfers`
**Branch:** fase/06-dinheiro · **Depende de:** 6.7
**Objetivo:** `TransactionResource.on_post_transfer` e a rota `POST /accounts/{account_key}/transfers` (tokens: conta; schema `post_transfers.json`): 201 com `{"transaction_key", "balance"}`; 404 `QIT001010`; 409 `QIT001011`; 422 `QIT001016`; 404 `QIT001017`; 409 `QIT001018`; 422 `QIT001015`; 409 `QIT001014`; 400 `QIT000001`.
**Decisões:** TST-03 — tarifa e sem saldo · MOV-01, MOV-02, MOV-03, MOV-06, MOV-10 — tarifa e saldo · MOV-05, MOV-11 — travas · MOV-12, MOV-19 — idempotência · API-10 — key e saldo novo · API-18 — valor inteiro ≥ 1 · CLI-09 — bloqueada ou encerrada · DAD-16 — quatro lançamentos · R8 — outro dono → 404 · TST-01 — black box e TDD
**Arquivos:**
- `src/resources/transaction.py` (editar): o conteúdo inteiro passa a ser:

```python
from fastapi import Request
from fastapi import status as http_status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from constants import ACCOUNT_TOKEN_HEADER
from controllers import TransactionController
from utils.schema_handler import SchemaHandler


class TransactionResource:
    """A porta HTTP do dinheiro: depósito, saque, transferência, consulta e extrato.

    Sem regra de negócio, sem SQL e sem nada guardado no self (ARQ-02). O
    token da conta chega no cabeçalho ACCOUNT-TOKEN (API-16); quem o
    confere é o controller.
    """

    @SchemaHandler.validate("post_deposits.json")
    def on_post_deposit(self, account_key: str, payload: dict) -> JSONResponse:
        controller = TransactionController()
        transaction = controller.deposit(account_key, payload)

        return JSONResponse(
            content=jsonable_encoder(transaction),
            status_code=http_status.HTTP_201_CREATED,
        )

    @SchemaHandler.validate("post_withdrawals.json")
    def on_post_withdrawal(self, account_key: str, payload: dict, request: Request) -> JSONResponse:
        controller = TransactionController()
        transaction = controller.withdraw(account_key, request.headers.get(ACCOUNT_TOKEN_HEADER), payload)

        return JSONResponse(
            content=jsonable_encoder(transaction),
            status_code=http_status.HTTP_201_CREATED,
        )

    @SchemaHandler.validate("post_transfers.json")
    def on_post_transfer(self, account_key: str, payload: dict, request: Request) -> JSONResponse:
        controller = TransactionController()
        transaction = controller.transfer(account_key, request.headers.get(ACCOUNT_TOKEN_HEADER), payload)

        return JSONResponse(
            content=jsonable_encoder(transaction),
            status_code=http_status.HTTP_201_CREATED,
        )
```

- `src/app.py` (editar): uma troca, e nada mais. A linha
  ```python
      application.add_api_route("/accounts/{account_key}/withdrawals", transaction_resource.on_post_withdrawal, methods=["POST"])
  ```
  vira as duas linhas
  ```python
      application.add_api_route("/accounts/{account_key}/withdrawals", transaction_resource.on_post_withdrawal, methods=["POST"])
      application.add_api_route("/accounts/{account_key}/transfers", transaction_resource.on_post_transfer, methods=["POST"])
  ```

- `tests/integration/transactions/test_transfer.py` (criar): o conteúdo inteiro é:

```python
"""Transferência: POST /accounts/{account_key}/transfers (TST-03, MOV-01 a MOV-03, MOV-05, MOV-06, MOV-08 a MOV-12, DAD-16, CLI-09, R8).

A conta da URL envia e paga a tarifa de 1%, arredondada para cima ao
centavo; o destino recebe exatamente o valor. O saldo precisa cobrir
valor + tarifa, e nunca fica negativo. A resposta traz a key da operação
e o saldo novo da origem. Os testes que erram o token começam com
DbUtils.rollback() (PRD-10).
"""

import re
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

from tests.utils import DbUtils, ObjectGenerator, PayloadGenerator, RequestGenerator


UUID_V4 = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")
PARALLEL_REQUESTS = 8


def balance_of(account: dict) -> int:
    status, response = RequestGenerator.GET_account(account["account_key"], account["account_token"])
    assert status == 200, response
    assert type(response["balance"]) is int, response

    return response["balance"]


def transfer(origin: dict, payload: dict) -> tuple:
    """Transfere a partir da origem, com o token dela."""
    return RequestGenerator.POST_transfer(origin["account_key"], origin["account_token"], payload)


def assert_balances(origin: dict, destination: dict, origin_balance: int, destination_balance: int) -> None:
    assert balance_of(origin) == origin_balance
    assert balance_of(destination) == destination_balance


class TestTransfer:
    def test_transfers_with_fee(self):
        origin = ObjectGenerator.create_funded_account(50000)
        destination = ObjectGenerator.create_account()

        status, response = transfer(origin, PayloadGenerator.transfer(destination["account_key"], amount=10000))

        assert status == 201, response
        assert sorted(response) == ["balance", "transaction_key"]
        assert UUID_V4.match(response["transaction_key"])
        assert type(response["balance"]) is int
        assert response["balance"] == 39900
        assert_balances(origin, destination, 39900, 10000)

    def test_fee_rounds_up_to_the_cent(self):
        origin = ObjectGenerator.create_funded_account(100000)
        destination = ObjectGenerator.create_account()

        status, response = transfer(origin, PayloadGenerator.transfer(destination["account_key"], amount=1234))
        assert status == 201, response
        assert response["balance"] == 100000 - 1234 - 13

        status, response = transfer(origin, PayloadGenerator.transfer(destination["account_key"], amount=1))
        assert status == 201, response
        assert response["balance"] == 100000 - 1234 - 13 - 1 - 1

        assert_balances(origin, destination, 98751, 1235)

    def test_balance_exactly_covers_amount_plus_fee(self):
        origin = ObjectGenerator.create_funded_account(10100)
        destination = ObjectGenerator.create_account()

        status, response = transfer(origin, PayloadGenerator.transfer(destination["account_key"], amount=10000))

        assert status == 201, response
        assert response["balance"] == 0
        assert_balances(origin, destination, 0, 10000)

    def test_refuses_insufficient_balance(self):
        origin = ObjectGenerator.create_funded_account(10099)
        destination = ObjectGenerator.create_account()

        for amount in [10000, 20000]:
            status, response = transfer(origin, PayloadGenerator.transfer(destination["account_key"], amount=amount))

            assert status == 422, (amount, response)
            assert response["code"] == "QIT001015"

        assert_balances(origin, destination, 10099, 0)

    def test_refuses_same_account(self):
        origin = ObjectGenerator.create_funded_account(10000)

        status, response = transfer(origin, PayloadGenerator.transfer(origin["account_key"], amount=1000))

        assert status == 422, response
        assert response["code"] == "QIT001016"
        assert balance_of(origin) == 10000

    def test_unknown_destination_is_404(self):
        origin = ObjectGenerator.create_funded_account(10000)

        status, response = transfer(origin, PayloadGenerator.transfer(str(uuid4()), amount=1000))

        assert status == 404, response
        assert response["code"] == "QIT001017"
        assert balance_of(origin) == 10000

    def test_inactive_origin_is_409(self):
        origin = ObjectGenerator.create_funded_account(10000)
        destination = ObjectGenerator.create_account()

        status, response = RequestGenerator.POST_block(origin["account_key"], PayloadGenerator.block())
        assert status == 204, response

        status, response = transfer(origin, PayloadGenerator.transfer(destination["account_key"], amount=1000))
        assert status == 409, response
        assert response["code"] == "QIT001011"
        assert_balances(origin, destination, 10000, 0)

        status, response = RequestGenerator.POST_unblock(origin["account_key"])
        assert status == 204, response

        status, response = transfer(origin, PayloadGenerator.transfer(destination["account_key"], amount=1000))
        assert status == 201, response

        closed_origin = ObjectGenerator.create_account()
        status, response = RequestGenerator.DELETE_account(closed_origin["account_key"], closed_origin["account_token"])
        assert status == 204, response

        status, response = transfer(closed_origin, PayloadGenerator.transfer(destination["account_key"], amount=1))
        assert status == 409, response
        assert response["code"] == "QIT001011"

    def test_inactive_destination_is_409(self):
        origin = ObjectGenerator.create_funded_account(10000)
        destination = ObjectGenerator.create_account()

        status, response = RequestGenerator.POST_block(destination["account_key"], PayloadGenerator.block())
        assert status == 204, response

        status, response = transfer(origin, PayloadGenerator.transfer(destination["account_key"], amount=1000))
        assert status == 409, response
        assert response["code"] == "QIT001018"
        assert_balances(origin, destination, 10000, 0)

        status, response = RequestGenerator.POST_unblock(destination["account_key"])
        assert status == 204, response

        status, response = transfer(origin, PayloadGenerator.transfer(destination["account_key"], amount=1000))
        assert status == 201, response

        closed_destination = ObjectGenerator.create_account()
        status, response = RequestGenerator.DELETE_account(closed_destination["account_key"], closed_destination["account_token"])
        assert status == 204, response

        status, response = transfer(origin, PayloadGenerator.transfer(closed_destination["account_key"], amount=1000))
        assert status == 409, response
        assert response["code"] == "QIT001018"
        assert balance_of(origin) == 10000 - 1000 - 10

    def test_refuses_body_out_of_schema(self):
        origin = ObjectGenerator.create_funded_account(10000)
        destination = ObjectGenerator.create_account()
        destination_key = destination["account_key"]
        bodies = []

        for amount in [0, -1, 10.5, 1000.0, "1000", True]:
            bodies.append(PayloadGenerator.transfer(destination_key, amount=amount))

        for field in ["destination_account_key", "amount", "request_control_key"]:
            body = PayloadGenerator.transfer(destination_key)
            del body[field]
            bodies.append(body)

        bodies.append(dict(PayloadGenerator.transfer(destination_key), extra=1))
        bodies.append(PayloadGenerator.transfer(destination_key.upper()))
        bodies.append(PayloadGenerator.transfer("nao-e-uma-key"))

        for body in bodies:
            status, response = transfer(origin, body)

            assert status == 400, (body, response)
            assert response["code"] == "QIT000001"

        assert_balances(origin, destination, 10000, 0)

    def test_other_account_token_is_404(self):
        DbUtils.rollback()
        origin = ObjectGenerator.create_funded_account(10000)
        destination = ObjectGenerator.create_account()
        payload = PayloadGenerator.transfer(destination["account_key"], amount=1000)

        status, response = RequestGenerator.POST_transfer(origin["account_key"], destination["account_token"], payload)
        assert status == 404, response
        assert response["code"] == "QIT001010"
        assert_balances(origin, destination, 10000, 0)

        status, response = transfer(origin, payload)
        assert status == 201, response

    def test_missing_or_wrong_token_is_404(self):
        DbUtils.rollback()
        origin = ObjectGenerator.create_funded_account(10000)
        destination = ObjectGenerator.create_account()

        for account_token in [None, "token_errado"]:
            payload = PayloadGenerator.transfer(destination["account_key"], amount=1000)
            status, response = RequestGenerator.POST_transfer(origin["account_key"], account_token, payload)

            assert status == 404, (account_token, response)
            assert response["code"] == "QIT001010"

        assert_balances(origin, destination, 10000, 0)

    def test_repeated_request_returns_first_response(self):
        origin = ObjectGenerator.create_funded_account(10000)
        destination = ObjectGenerator.create_account()
        payload = PayloadGenerator.transfer(destination["account_key"], amount=1000)

        first_status, first_response = transfer(origin, payload)
        assert first_status == 201, first_response
        assert first_response["balance"] == 8990

        status, response = transfer(origin, PayloadGenerator.transfer(destination["account_key"], amount=2000))
        assert status == 201, response

        second_status, second_response = transfer(origin, payload)
        assert second_status == 201, second_response
        assert second_response == first_response

        assert_balances(origin, destination, 10000 - 1010 - 2020, 3000)

        # A repetição simultânea deve passar mesmo quando a primeira esgota o saldo.
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier

        raced = ObjectGenerator.create_funded_account(1010)
        destination = ObjectGenerator.create_account()
        raced_payload = PayloadGenerator.transfer(destination["account_key"], amount=1000)
        gate = Barrier(2)

        def send_same(_index):
            gate.wait(timeout=5)
            return transfer(raced, raced_payload)

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(send_same, range(2)))

        assert results[0][0] == 201, results
        assert results == [results[0], results[0]], results
        assert balance_of(raced) == 0


    def test_same_key_with_other_request_is_409(self):
        origin = ObjectGenerator.create_funded_account(10000)
        destination = ObjectGenerator.create_account()
        other_destination = ObjectGenerator.create_account()
        payload = PayloadGenerator.transfer(destination["account_key"], amount=1000)

        status, response = transfer(origin, payload)
        assert status == 201, response

        for body in [dict(payload, amount=1001), dict(payload, destination_account_key=other_destination["account_key"])]:
            status, response = transfer(origin, body)

            assert status == 409, (body, response)
            assert response["code"] == "QIT001014"

        assert_balances(origin, destination, 8990, 1000)
        assert balance_of(other_destination) == 0

    def test_concurrent_transfers_never_go_negative(self):
        origin = ObjectGenerator.create_funded_account(20200)
        destination = ObjectGenerator.create_account()
        payloads = [PayloadGenerator.transfer(destination["account_key"], amount=10000) for _index in range(PARALLEL_REQUESTS)]

        with ThreadPoolExecutor(max_workers=PARALLEL_REQUESTS) as executor:
            results = list(executor.map(lambda payload: transfer(origin, payload), payloads))

        statuses = sorted(status for status, _response in results)
        assert statuses == [201] * 2 + [422] * (PARALLEL_REQUESTS - 2), results
        assert_balances(origin, destination, 0, 20000)

    def test_crossed_transfers_do_not_deadlock(self):
        first = ObjectGenerator.create_funded_account(100000)
        second = ObjectGenerator.create_funded_account(100000)
        half = PARALLEL_REQUESTS // 2

        requests = []
        for _index in range(half):
            requests.append((first, PayloadGenerator.transfer(second["account_key"], amount=1000)))
            requests.append((second, PayloadGenerator.transfer(first["account_key"], amount=1000)))

        with ThreadPoolExecutor(max_workers=PARALLEL_REQUESTS) as executor:
            results = list(executor.map(lambda request: transfer(request[0], request[1]), requests))

        assert [status for status, _response in results] == [201] * PARALLEL_REQUESTS, results
        assert_balances(first, second, 100000 - half * 10, 100000 - half * 10)
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/06-dinheiro`; `git log --oneline` mostra `feat(transferencia): controller da transferência com tarifa e travas`.
2. Crie `tests/integration/transactions/test_transfer.py` com o conteúdo do campo **Arquivos**.
3. `docker compose up -d --build --wait`.
4. `./.venv/Scripts/python.exe -m pytest -v tests/integration/transactions/test_transfer.py` → a última linha tem `15 failed` e não tem `passed`. Os 15 falham por asserção: hoje o caminho `/accounts/{account_key}/transfers` responde 404 `QIT000404`.
5. Edite `src/resources/transaction.py` com o conteúdo do campo **Arquivos**.
6. Faça a troca em `src/app.py`.
7. `docker compose up -d --build --wait`.
8. `./.venv/Scripts/python.exe -m pytest -v tests/integration/transactions/test_transfer.py` → a última linha tem `15 passed`.
9. Rode a conferência T1 do **Verificar**.
10. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `174 passed`.
11. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
12. Feche o passo (AGENTS.md, seção 7), um comando por vez:
    ```
    git add -- src/resources/transaction.py src/app.py tests/integration/transactions/test_transfer.py
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "feat(transferencia): rota de transferência"
    git log -1 --format=%B
    ```

**Testes:** `tests/integration/transactions/test_transfer.py`. Efeito no banco de cada 201: uma linha em `transaction` (`TRANSFER`) e quatro lançamentos, que somam zero (DAD-16): `AMOUNT` −valor e `FEE` −tarifa na origem, `AMOUNT` +valor no destino, `FEE` +tarifa na `BANK`; os dois `balance` mudam. As recusas não gravam nada além da linha de `request_log`.

| Função de teste | Entrada | Esperado |
|---|---|---|
| `test_transfers_with_fee` | origem com 50000; 10000 para uma conta nova | 201; corpo com exatamente `transaction_key` (UUID v4) e `balance` (inteiro) = 39900; saldos 39900 e 10000 |
| `test_fee_rounds_up_to_the_cent` | origem com 100000; 1234 e depois 1 | `balance` 98753 (tarifa 13) e 98751 (tarifa 1); destino 1235 (MOV-10) |
| `test_balance_exactly_covers_amount_plus_fee` | origem com 10100; 10000 | 201 com `balance` 0; destino 10000 |
| `test_refuses_insufficient_balance` | origem com 10099; 10000 (o valor cabe, a tarifa não) e 20000 | 422 `QIT001015` nos dois; saldos 10099 e 0 (MOV-01, MOV-02) |
| `test_refuses_same_account` | destino = a própria origem | 422 `QIT001016`; saldo 10000 |
| `test_unknown_destination_is_404` | destino UUID que não existe | 404 `QIT001017`; saldo 10000 |
| `test_inactive_origin_is_409` | origem bloqueada; desbloqueio; origem encerrada | 409 `QIT001011` e saldos iguais; 201; 409 `QIT001011` |
| `test_inactive_destination_is_409` | destino bloqueado; desbloqueio; destino encerrado | 409 `QIT001018` e saldos iguais; 201; 409 `QIT001018` e origem com 8990 |
| `test_refuses_body_out_of_schema` | `amount` 0, −1, 10.5, 1000.0, `"1000"`, `true`; cada campo faltando; campo `extra`; key do destino em maiúsculas; `nao-e-uma-key` | 400 `QIT000001` nos 12; saldos iguais |
| `test_other_account_token_is_404` | começa com `DbUtils.rollback()`; da origem com o token do destino; depois com o token certo | 404 `QIT001010` e saldos iguais; 201 |
| `test_missing_or_wrong_token_is_404` | começa com `DbUtils.rollback()`; sem `ACCOUNT-TOKEN` e com `token_errado` | 404 `QIT001010` nos dois; saldos iguais |
| `test_repeated_request_returns_first_response` | transferência T; outra de 2000; T de novo | a resposta de T se repete igual (`balance` 8990); saldos 6970 e 3000 |
| `test_same_key_with_other_request_is_409` | a chave de T com outro `amount`; com outro destino | 409 `QIT001014` nos dois; saldos 8990, 1000 e 0 |
| `test_concurrent_transfers_never_go_negative` | origem com 20200; 8 transferências de 10000 ao mesmo tempo | dois 201 e seis 422; saldos 0 e 20000 (MOV-05) |
| `test_crossed_transfers_do_not_deadlock` | A e B com 100000; 4 de A para B e 4 de B para A, de 1000, ao mesmo tempo | oito 201, nenhum 500; A e B com 99960 (MOV-11) |

**Verificar:**
- `./.venv/Scripts/python.exe -m pytest -v tests/integration/transactions/test_transfer.py` → `15 passed`.
- T1 — os quatro lançamentos e a soma zero (DAD-16, DAD-09, MOV-09). Um comando, numa linha só:
  ```
  ./.venv/Scripts/python.exe -c "from sqlalchemy import create_engine, text; from tests.utils import DbUtils, ObjectGenerator, PayloadGenerator, RequestGenerator; a = ObjectGenerator.create_funded_account(50000); b = ObjectGenerator.create_account(); s, r = RequestGenerator.POST_transfer(a['account_key'], a['account_token'], PayloadGenerator.transfer(b['account_key'], amount=10000)); print(s, r['balance']); c = create_engine(DbUtils.database_url()).connect(); k = {'t': r['transaction_key']}; print(c.execute(text('SELECT t.enumerator, w.enumerator, e.amount, e.balance_after FROM entry e JOIN transaction x ON x.id = e.transaction_id JOIN account m ON m.id = e.account_id JOIN account_type t ON t.id = m.account_type_id JOIN entry_type w ON w.id = e.entry_type_id WHERE x.transaction_key = :t ORDER BY e.id'), k).fetchall()); print(c.execute(text('SELECT sum(e.amount) FROM entry e JOIN transaction x ON x.id = e.transaction_id WHERE x.transaction_key = :t'), k).scalar()); print(c.execute(text('SELECT count(*) FROM (SELECT transaction_id FROM entry GROUP BY transaction_id HAVING sum(amount) <> 0) z')).scalar())"
  ```
  → exatamente:
  ```
  201 39900
  [('CUSTOMER', 'AMOUNT', -10000, 40000), ('CUSTOMER', 'FEE', -100, 39900), ('CUSTOMER', 'AMOUNT', 10000, 10000), ('BANK', 'FEE', 100, None)]
  0
  0
  ```
  (a última linha: nenhuma operação do banco inteiro tem lançamentos que não somam zero)
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `174 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/app.py
  src/resources/transaction.py
  tests/integration/transactions/test_transfer.py
  ```
- `git log -1 --format=%B` → `feat(transferencia): rota de transferência`

**Pronto quando:**
- [ ] Os 15 testes falharam antes do código (item 4) e passam depois (item 8).
- [ ] A T1 dá as 4 linhas esperadas.
- [ ] Suíte com `174 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/06-dinheiro`.

**Commit:** `feat(transferencia): rota de transferência`
**Pare se:**
- O item 4 não terminar com `15 failed`.
- Um teste receber 500 (`QIT000500`) ou 503 (`QIT000503`): rode `docker compose logs --tail 100 api` e traga a saída. Um 503 em `test_crossed_transfers_do_not_deadlock` quer dizer trava fora da ordem do `id`.
- `test_concurrent_transfers_never_go_negative` ou `test_crossed_transfers_do_not_deadlock` falhar em uma de três rodadas seguidas do item 8.
- A T1 der outra saída depois de 3 tentativas de conferir os arquivos do passo contra o plano.
- A suíte não terminar com `174 passed`.

---

### Passo 6.9 — Limite diário e bloqueio automático
**Branch:** fase/06-dinheiro · **Depende de:** 6.8
**Objetivo:** `TransactionRepository.count_transfers_sent(account, accounting_date, since)` e `AccountRepository.get_active_since(account)` (nome novo); na transferência, depois de todas as outras regras, a 11ª enviada no dia contábil, contada desde o último evento `ACTIVE` (abertura ou desbloqueio), responde 422 `QIT001019` e bloqueia a conta na mesma requisição (`SUSPICIOUS_ACTIVITY`, origem `AUTOMATIC`).
**Decisões:** CLI-08 — bloqueio automático · DAD-13 — a única gravação de pedido barrado · DIA-01 — o dia é o do relógio do banco · CLI-05 — só o banco desbloqueia · R4 — mudança de estado grava evento · TST-01 — black box e TDD
**Arquivos:**
- `src/constants.py` (editar): imediatamente antes de `REQUIRED_VARIABLES`, acrescente `DAILY_TRANSFER_LIMIT = int(os.environ.get("DAILY_TRANSFER_LIMIT", "10"))`; não colocar em `REQUIRED_VARIABLES`, pois tem padrão.
- `docker-compose.yml` (editar): no `environment` do serviço `api`, acrescente `DAILY_TRANSFER_LIMIT: ${DAILY_TRANSFER_LIMIT:-10}`.
- `.env.example` (editar): acrescente `DAILY_TRANSFER_LIMIT=10`. Para as saídas e contagens deste plano, executar com esse padrão; não introduzir outro limite na suíte.
- `src/repositories/transaction_repository.py` (editar): o conteúdo inteiro passa a ser:

```python
from datetime import date, datetime
from uuid import uuid4

from database import Context
from models import Account, Entry, EntryType, Transaction, TransactionType


class TransactionRepository:
    """Consulta e grava as operações (DAD-06). Nenhuma regra de negócio mora aqui.

    A key nasce aqui, com uuid4 (DAD-12). Operação não se altera nem se
    apaga (R4, DAD-11): este repository só cria e consulta.
    """

    def __init__(self, context: Context) -> None:
        self.session = context.db_session

    def create(self, transaction_type_enumerator: str, request_control_key: str, request_hash: str, accounting_date: date) -> Transaction:
        """Cria a operação com as duas datas (DAD-17): accounting_date vem do relógio do banco; created_at, do NOW() do banco.

        O flush manda o INSERT na hora: dá o id aos lançamentos e, se a
        request_control_key já existe, levanta o IntegrityError do UNIQUE
        aqui, antes de qualquer lançamento (MOV-19). Se outra transação
        acabou de gravar a mesma chave e ainda não fez commit, o INSERT
        espera por ela.
        """
        transaction = Transaction()
        transaction.transaction_key = str(uuid4())
        transaction.transaction_type = (
            self.session.query(TransactionType).filter(TransactionType.enumerator == transaction_type_enumerator).one()
        )
        transaction.request_control_key = request_control_key
        transaction.request_hash = request_hash
        transaction.accounting_date = accounting_date

        self.session.add(transaction)
        self.session.flush()

        return transaction

    def get_by_request_control_key(self, request_control_key: str) -> Transaction:
        """A operação gravada com esta chave de idempotência; None quando não existe (MOV-12)."""
        return self.session.query(Transaction).filter(Transaction.request_control_key == request_control_key).first()

    def get_by_key_for_account(self, transaction_key: str, account_ids: list) -> Transaction:
        """A operação com esta key, se ela tem pelo menos um lançamento numa das contas de account_ids; None nos outros casos (R8)."""
        return (
            self.session.query(Transaction)
            .join(Entry, Entry.transaction_id == Transaction.id)
            .filter(Transaction.transaction_key == transaction_key, Entry.account_id.in_(account_ids))
            .first()
        )

    def count_transfers_sent(self, account: Account, accounting_date: date, since: datetime) -> int:
        """Quantas transferências a conta enviou no dia contábil, gravadas depois de `since` (CLI-08).

        Enviada = operação TRANSFER com lançamento AMOUNT negativo nesta
        conta. A recebida não conta. Pedido recusado não gravou operação e
        também não conta (DAD-13). `since` é o created_at do último evento
        ACTIVE da conta (AccountRepository.get_active_since); as duas datas
        vêm do NOW() do banco.
        """
        return (
            self.session.query(Transaction)
            .join(TransactionType, TransactionType.id == Transaction.transaction_type_id)
            .join(Entry, Entry.transaction_id == Transaction.id)
            .join(EntryType, EntryType.id == Entry.entry_type_id)
            .filter(
                TransactionType.enumerator == TransactionType.TRANSFER,
                Transaction.accounting_date == accounting_date,
                Transaction.created_at > since,
                Entry.account_id == account.id,
                EntryType.enumerator == EntryType.AMOUNT,
                Entry.amount < 0,
            )
            .count()
        )
```

- `src/repositories/account_repository.py` (editar): duas mudanças, e nada mais.
  1. A linha
     ```python
     from uuid import uuid4
     ```
     vira as três linhas
     ```python
     from uuid import uuid4

     from sqlalchemy import func
     ```
  2. O método `get_active_since` abaixo entra logo depois do método `change_status` e antes de `_add_status_event`, com uma linha em branco antes dele:

```python
    def get_active_since(self, account: Account) -> datetime:
        """O created_at do último evento ACTIVE da conta: a abertura ou o último desbloqueio (CLI-08).

        É a partir dele que o limite diário de transferências conta. O
        created_at vem do NOW() do banco, o mesmo relógio do created_at das
        operações (TransactionRepository.count_transfers_sent).
        """
        return (
            self.session.query(func.max(AccountStatusEvent.created_at))
            .select_from(AccountStatusEvent)
            .join(AccountStatus, AccountStatus.id == AccountStatusEvent.status_id)
            .filter(AccountStatusEvent.account_id == account.id, AccountStatus.enumerator == AccountStatus.ACTIVE)
            .scalar()
        )
```

- `src/controllers/transaction_controller.py` (editar): duas mudanças, e nada mais.
  1. Tudo o que vem antes da linha `class TransactionController(BaseController):` passa a ser exatamente o bloco abaixo (seguido de duas linhas em branco antes do `class`):

```python
from sqlalchemy.exc import IntegrityError

from calculations import calculate_fee
from constants import DAILY_TRANSFER_LIMIT
from controllers.base_controller import BaseController
from dtos import TransactionDTO
from errors import (
    AccountNotActive,
    AccountNotFound,
    DailyTransferLimitReached,
    DestinationAccountNotActive,
    DestinationAccountNotFound,
    IdempotencyKeyConflict,
    InsufficientBalance,
    InvalidDocumentNumber,
    SameAccountTransfer,
)
from models import Account, AccountStatus, AccountStatusEvent, AccountType, BlockReason, EntryType, Transaction, TransactionType
from repositories import AccountRepository, BankClockRepository, DepositRepository, EntryRepository, TransactionRepository
from utils.document_number import FORMATTED_CPF_LENGTH, is_valid_cnpj, is_valid_cpf
from utils.request_hash import hash_request_body


# CLI-08: limite configurável no ambiente; padrão 10.
```

  2. O método `transfer` inteiro (da linha `    def transfer(` até a linha `        return transaction_dto` que o fecha) passa a ser:

```python
    def transfer(self, account_key: str, account_token: str, transfer_data: dict) -> dict:
        """Transferência entre contas de cliente, com tarifa (MOV-01 a MOV-03, MOV-06, MOV-09, DAD-16). As regras, nesta ordem:

        1. a conta de origem é do dono do token (404 QIT001010, R8);
        2. a mesma request_control_key com o mesmo pedido devolve a resposta
           da primeira vez, com o saldo de depois daquela transferência
           (MOV-19); com outro pedido, 409 QIT001014 (MOV-12);
        3. trava a origem e, se o destino existe e é de cliente, também o
           destino, as duas na ordem do id (MOV-05, MOV-11);
        4. a origem está ACTIVE (409 QIT001011, CLI-09);
        5. a origem é diferente do destino (422 QIT001016, MOV-08);
        6. o destino existe e é de cliente (404 QIT001017);
        7. o destino está ACTIVE (409 QIT001018, CLI-09);
        8. o saldo da origem cobre valor + tarifa (422 QIT001015, MOV-01,
           MOV-02); a tarifa é calculate_fee(valor, 0): os pontos entram
           no passo 8.7;
        9. a origem enviou menos de DAILY_TRANSFER_LIMIT transferências no
           dia contábil, contadas desde o último evento ACTIVE da conta
           (abertura ou desbloqueio). Na 11ª: a conta fica BLOCKED, com
           origem AUTOMATIC e motivo SUSPICIOUS_ACTIVITY, o commit grava só
           o bloqueio, e a resposta é 422 QIT001019 (CLI-08, DAD-13).

        Depois: a operação TRANSFER e os lançamentos, nesta ordem: AMOUNT
        −valor e FEE −tarifa na origem; AMOUNT +valor no destino; FEE
        +tarifa na conta BANK. Tarifa zero não gera lançamento (MOV-10). A
        resposta traz a key e o saldo novo da origem (API-10).
        """
        account = self.get_owned_account(account_key, account_token)

        request_control_key = transfer_data["request_control_key"]
        request_hash = hash_request_body(TransactionType.TRANSFER, account_key, transfer_data)

        repeated_transaction = self._find_repeated(request_control_key, request_hash)
        if repeated_transaction is not None:
            return TransactionDTO.with_balance(repeated_transaction, self._balance_after(repeated_transaction, account))

        accounting_date = self.bank_clock_repository.get_accounting_date()

        destination_account_key = transfer_data["destination_account_key"]
        destination = self.account_repository.get_customer_account(destination_account_key)

        accounts_to_lock = [account]
        if destination is not None:
            accounts_to_lock.append(destination)

        locked_accounts = {}
        for locked_account in self.account_repository.lock_accounts(accounts_to_lock):
            locked_accounts[locked_account.id] = locked_account

        account = locked_accounts[account.id]
        if destination is not None:
            destination = locked_accounts[destination.id]

        # Uma chamada com a mesma chave pode ter concluído enquanto esta esperava a trava.
        repeated_transaction = self._find_repeated(request_control_key, request_hash)
        if repeated_transaction is not None:
            return TransactionDTO.with_balance(repeated_transaction, self._balance_after(repeated_transaction, account))

        if account.status.enumerator != AccountStatus.ACTIVE:
            raise AccountNotActive(account_key, account.status.enumerator)

        if destination_account_key == account.account_key:
            raise SameAccountTransfer()

        if destination is None:
            raise DestinationAccountNotFound(destination_account_key)

        if destination.status.enumerator != AccountStatus.ACTIVE:
            raise DestinationAccountNotActive(destination_account_key)

        amount = transfer_data["amount"]
        fee = calculate_fee(amount, 0)

        if account.balance < amount + fee:
            raise InsufficientBalance(account_key)

        active_since = self.account_repository.get_active_since(account)
        transfers_sent = self.transaction_repository.count_transfers_sent(account, accounting_date, active_since)

        if transfers_sent >= DAILY_TRANSFER_LIMIT:
            self.account_repository.change_status(
                account,
                AccountStatus.BLOCKED,
                AccountStatusEvent.AUTOMATIC,
                BlockReason.SUSPICIOUS_ACTIVITY,
            )
            self.session.commit()

            raise DailyTransferLimitReached(account_key)

        bank = self.account_repository.get_system_account(AccountType.BANK)

        try:
            transaction = self.transaction_repository.create(TransactionType.TRANSFER, request_control_key, request_hash, accounting_date)
            self.entry_repository.create(transaction, account, EntryType.AMOUNT, -amount)

            if fee > 0:
                self.entry_repository.create(transaction, account, EntryType.FEE, -fee)

            self.entry_repository.create(transaction, destination, EntryType.AMOUNT, amount)

            if fee > 0:
                self.entry_repository.create(transaction, bank, EntryType.FEE, fee)

            transaction_dto = TransactionDTO.with_balance(transaction, account.balance)
            self.logger.info("operation_ready_to_commit transaction_key=%s", transaction.transaction_key)
            self.session.commit()
        except IntegrityError:
            self.session.rollback()

            repeated_transaction = self._find_repeated(request_control_key, request_hash)
            if repeated_transaction is None:
                raise

            return TransactionDTO.with_balance(repeated_transaction, self._balance_after(repeated_transaction, account))

        return transaction_dto
```

- `tests/integration/transactions/test_daily_transfer_limit.py` (criar): o conteúdo inteiro é:

```python
"""Limite diário e bloqueio automático (CLI-08, DAD-13): POST /accounts/{account_key}/transfers.

Até 10 transferências enviadas no mesmo dia contábil passam. A 11ª, que
passaria em todas as outras regras, é recusada com 422 QIT001019 e
bloqueia a conta na mesma requisição; a 12ª já encontra a conta
bloqueada (409 QIT001011). Só o banco desbloqueia (rota interna), e a
contagem recomeça no desbloqueio. Transferência recebida e pedido
recusado não contam.

Todos os testes começam com DbUtils.rollback(): o limite conta pelo dia
do relógio do banco, que é um só para a suíte inteira (DIA-01).
"""

from tests.utils import DbUtils, ObjectGenerator, PayloadGenerator, RequestGenerator


DAILY_TRANSFER_LIMIT = 10


def account_of(account: dict) -> dict:
    status, response = RequestGenerator.GET_account(account["account_key"], account["account_token"])
    assert status == 200, response

    return response


def transfer(origin: dict, destination: dict, amount: int = 100) -> tuple:
    payload = PayloadGenerator.transfer(destination["account_key"], amount=amount)

    return RequestGenerator.POST_transfer(origin["account_key"], origin["account_token"], payload)


def send_transfers(origin: dict, destination: dict, count: int, amount: int = 100) -> None:
    for index in range(count):
        status, response = transfer(origin, destination, amount=amount)
        assert status == 201, (index, response)


def assert_limit_reached(status: int, response: dict) -> None:
    assert status == 422, response
    assert response["code"] == "QIT001019"


class TestDailyTransferLimit:
    def test_eleventh_transfer_is_refused_and_blocks_the_account(self):
        DbUtils.rollback()
        origin = ObjectGenerator.create_funded_account(100000)
        destination = ObjectGenerator.create_account()

        send_transfers(origin, destination, DAILY_TRANSFER_LIMIT)
        assert account_of(origin)["status"] == "ACTIVE"

        status, response = transfer(origin, destination)
        assert_limit_reached(status, response)

        origin_account = account_of(origin)
        assert origin_account["status"] == "BLOCKED"
        assert origin_account["balance"] == 100000 - DAILY_TRANSFER_LIMIT * 101
        assert account_of(destination)["balance"] == DAILY_TRANSFER_LIMIT * 100

        status, response = transfer(origin, destination)
        assert status == 409, response
        assert response["code"] == "QIT001011"

    def test_unblock_restarts_the_count(self):
        DbUtils.rollback()
        origin = ObjectGenerator.create_funded_account(100000)
        destination = ObjectGenerator.create_account()

        send_transfers(origin, destination, DAILY_TRANSFER_LIMIT)
        status, response = transfer(origin, destination)
        assert_limit_reached(status, response)

        status, response = RequestGenerator.POST_unblock(origin["account_key"])
        assert status == 204, response

        send_transfers(origin, destination, DAILY_TRANSFER_LIMIT)
        assert account_of(origin)["status"] == "ACTIVE"

        status, response = transfer(origin, destination)
        assert_limit_reached(status, response)
        assert account_of(origin)["status"] == "BLOCKED"

    def test_refused_transfers_do_not_count(self):
        DbUtils.rollback()
        origin = ObjectGenerator.create_funded_account(DAILY_TRANSFER_LIMIT * 101 + 101)
        destination = ObjectGenerator.create_account()

        for _index in range(DAILY_TRANSFER_LIMIT + 1):
            status, response = transfer(origin, destination, amount=1000000)
            assert status == 422, response
            assert response["code"] == "QIT001015"

        send_transfers(origin, destination, DAILY_TRANSFER_LIMIT)
        assert account_of(origin)["status"] == "ACTIVE"

        status, response = transfer(origin, destination)
        assert_limit_reached(status, response)

        origin_account = account_of(origin)
        assert origin_account["status"] == "BLOCKED"
        assert origin_account["balance"] == 101

    def test_eleventh_without_balance_is_insufficient_balance(self):
        DbUtils.rollback()
        origin = ObjectGenerator.create_funded_account(DAILY_TRANSFER_LIMIT * 101 + 101)
        destination = ObjectGenerator.create_account()

        send_transfers(origin, destination, DAILY_TRANSFER_LIMIT)

        status, response = transfer(origin, destination, amount=1000)
        assert status == 422, response
        assert response["code"] == "QIT001015"
        assert account_of(origin)["status"] == "ACTIVE"

        status, response = transfer(origin, destination)
        assert_limit_reached(status, response)

        origin_account = account_of(origin)
        assert origin_account["status"] == "BLOCKED"
        assert origin_account["balance"] == 101

    def test_received_transfers_do_not_count(self):
        DbUtils.rollback()
        first_sender = ObjectGenerator.create_funded_account(100000)
        second_sender = ObjectGenerator.create_funded_account(100000)
        receiver = ObjectGenerator.create_account()

        send_transfers(first_sender, receiver, 6, amount=1000)
        send_transfers(second_sender, receiver, 5, amount=1000)

        send_transfers(receiver, first_sender, DAILY_TRANSFER_LIMIT)
        assert account_of(receiver)["status"] == "ACTIVE"

        status, response = transfer(receiver, first_sender)
        assert_limit_reached(status, response)
        assert account_of(receiver)["status"] == "BLOCKED"
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/06-dinheiro`; `git log --oneline` mostra `feat(transferencia): rota de transferência`.
2. Crie `tests/integration/transactions/test_daily_transfer_limit.py` com o conteúdo do campo **Arquivos**.
3. `docker compose up -d --build --wait`.
4. `./.venv/Scripts/python.exe -m pytest -v tests/integration/transactions/test_daily_transfer_limit.py` → a última linha tem `5 failed` e não tem `passed`. Os 5 falham por asserção: hoje a 11ª transferência responde 201 em vez de 422 `QIT001019`.
5. Edite `src/repositories/transaction_repository.py` com o conteúdo do campo **Arquivos**.
6. Faça as duas mudanças em `src/repositories/account_repository.py`.
7. Edite `src/constants.py`, `docker-compose.yml` e `.env.example` conforme **Arquivos**; depois faça as duas mudanças em `src/controllers/transaction_controller.py`.
8. `docker compose up -d --build --wait`.
9. `./.venv/Scripts/python.exe -m pytest -v tests/integration/transactions/test_daily_transfer_limit.py` → a última linha tem `5 passed`.
10. Rode as conferências S4 e B1 do **Verificar**.
11. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `179 passed`.
12. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
13. Feche o passo (AGENTS.md, seção 7), um comando por vez:
    ```
    git add -- .env.example docker-compose.yml src/constants.py src/repositories/transaction_repository.py src/repositories/account_repository.py src/controllers/transaction_controller.py tests/integration/transactions/test_daily_transfer_limit.py
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "feat(seguranca): limite diário de transferências e bloqueio automático"
    git log -1 --format=%B
    ```

**Testes:** `tests/integration/transactions/test_daily_transfer_limit.py`. Todos começam com `DbUtils.rollback()` (DIA-01: o relógio é um só para a suíte inteira). Efeito no banco da 11ª: a conta passa a `BLOCKED` e ganha um evento com motivo `SUSPICIOUS_ACTIVITY` e origem `AUTOMATIC`; nenhuma operação, lançamento ou chave de idempotência é gravado (DAD-13).

| Função de teste | Entrada | Esperado |
|---|---|---|
| `test_eleventh_transfer_is_refused_and_blocks_the_account` | 10 transferências de 100; a 11ª; a 12ª | dez 201 e a conta `ACTIVE`; 422 `QIT001019`, conta `BLOCKED`, saldos 98990 e 1000 (a 11ª não moveu dinheiro); 409 `QIT001011` |
| `test_unblock_restarts_the_count` | 10 + a 11ª; desbloqueio pela rota interna; mais 10; mais uma | 422; 204; dez 201 com a conta `ACTIVE`; 422 `QIT001019` e `BLOCKED` de novo |
| `test_refused_transfers_do_not_count` | 11 transferências sem saldo; 10 válidas; mais uma | onze 422 `QIT001015`; dez 201 e `ACTIVE`; 422 `QIT001019`, `BLOCKED`, saldo 101 |
| `test_eleventh_without_balance_is_insufficient_balance` | 10 válidas; a 11ª sem saldo; a 11ª com saldo | 422 `QIT001015` e a conta continua `ACTIVE`; 422 `QIT001019` e `BLOCKED`, saldo 101 |
| `test_received_transfers_do_not_count` | a conta recebe 11 transferências; envia 10; envia mais uma | dez 201 e `ACTIVE`; 422 `QIT001019` e `BLOCKED` |

**Verificar:**
- `./.venv/Scripts/python.exe -m pytest -v tests/integration/transactions/test_daily_transfer_limit.py` → `5 passed`.
- Prova da configuração sem mexer no banco: `docker compose exec -T -e DAILY_TRANSFER_LIMIT=3 api python -c "from constants import DAILY_TRANSFER_LIMIT; print(DAILY_TRANSFER_LIMIT)"` → `3`. O serviço que atende os demais testes continua com padrão `10`.
- S4 (um comando, numa linha só):
  ```
  docker compose exec -T api python -c "import inspect; from controllers.transaction_controller import DAILY_TRANSFER_LIMIT, TransactionController; from repositories import AccountRepository, TransactionRepository; print(DAILY_TRANSFER_LIMIT, inspect.getsource(TransactionController.transfer).count('raise '), hasattr(AccountRepository, 'get_active_since'), hasattr(TransactionRepository, 'count_transfers_sent'))"
  ```
  → `10 6 True True`
- B1 — o bloqueio automático (CLI-08, R4, DAD-13). Um comando, numa linha só:
  ```
  ./.venv/Scripts/python.exe -c "from sqlalchemy import create_engine, text; from tests.utils import DbUtils, ObjectGenerator, PayloadGenerator, RequestGenerator; DbUtils.rollback(); a = ObjectGenerator.create_funded_account(100000); b = ObjectGenerator.create_account(); r = [RequestGenerator.POST_transfer(a['account_key'], a['account_token'], PayloadGenerator.transfer(b['account_key'], amount=100)) for _ in range(11)]; print([s for s, _ in r], r[-1][1]['code']); c = create_engine(DbUtils.database_url()).connect(); k = {'k': a['account_key']}; print(c.execute(text('SELECT s.enumerator, w.enumerator, e.source FROM account_status_event e JOIN account m ON m.id = e.account_id JOIN account_status s ON s.id = e.status_id LEFT JOIN block_reason w ON w.id = e.block_reason_id WHERE m.account_key = :k ORDER BY e.id'), k).fetchall()); print(c.execute(text('SELECT count(DISTINCT e.transaction_id) FROM entry e JOIN account m ON m.id = e.account_id WHERE m.account_key = :k AND e.amount < 0'), k).scalar())"
  ```
  → exatamente:
  ```
  [201, 201, 201, 201, 201, 201, 201, 201, 201, 201, 422] QIT001019
  [('ACTIVE', None, None), ('BLOCKED', 'SUSPICIOUS_ACTIVITY', 'AUTOMATIC')]
  10
  ```
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `179 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  .env.example
  docker-compose.yml
  src/constants.py
  src/controllers/transaction_controller.py
  src/repositories/account_repository.py
  src/repositories/transaction_repository.py
  tests/integration/transactions/test_daily_transfer_limit.py
  ```
- `git log -1 --format=%B` → `feat(seguranca): limite diário de transferências e bloqueio automático`

**Pronto quando:**
- [ ] Os 5 testes falharam antes do código (item 4) e passam depois (item 9).
- [ ] S4 e B1 dão a saída esperada.
- [ ] Suíte com `179 passed` (os testes de transferência do 6.8 continuam verdes); lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/06-dinheiro`.

**Commit:** `feat(seguranca): limite diário de transferências e bloqueio automático`
**Pare se:**
- O item 4 não terminar com `5 failed`.
- `test_unblock_restarts_the_count` falhar na 1ª transferência depois do desbloqueio com 422 `QIT001019`: a contagem não recomeçou; traga a saída e a do `docker compose logs --tail 100 api`.
- A B1 der outra saída depois de 3 tentativas de conferir os arquivos do passo contra o plano.
- A suíte não terminar com `179 passed`.

---

### Passo 6.10 — `GET /accounts/{account_key}/transactions/{transaction_key}`
**Branch:** fase/06-dinheiro · **Depende de:** 6.9
**Objetivo:** `TransactionController.get_transaction` (com `_entry_to_dict` e `_counterparty`) e a rota `GET /accounts/{account_key}/transactions/{transaction_key}` (tokens: conta): 200 com a operação e os lançamentos dela na conta e no cofrinho; 404 `QIT001010`; 404 `QIT001020`.
**Decisões:** R8 — outro dono → 404 · API-10 — consulta devolve o objeto pelo DTO · MOV-17 — outra ponta · MOV-18, DAD-17 — duas datas · PRD-12 — documento mascarado · R5 — o `id` nunca sai · MOV-07 — tipos de operação · TST-01 — black box e TDD
**Arquivos:**
- `src/controllers/transaction_controller.py` (editar): três mudanças, e nada mais.
  1. Tudo o que vem antes da linha `class TransactionController(BaseController):` passa a ser exatamente o bloco abaixo (seguido de duas linhas em branco antes do `class`):

```python
from sqlalchemy.exc import IntegrityError

from calculations import calculate_fee
from constants import DAILY_TRANSFER_LIMIT
from controllers.base_controller import BaseController
from dtos import EntryDTO, TransactionDTO
from errors import (
    AccountNotActive,
    AccountNotFound,
    DailyTransferLimitReached,
    DestinationAccountNotActive,
    DestinationAccountNotFound,
    IdempotencyKeyConflict,
    InsufficientBalance,
    InvalidDocumentNumber,
    SameAccountTransfer,
    TransactionNotFound,
)
from models import Account, AccountStatus, AccountStatusEvent, AccountType, BlockReason, Entry, EntryType, Transaction, TransactionType
from repositories import AccountRepository, BankClockRepository, DepositRepository, EntryRepository, TransactionRepository
from utils.document_number import FORMATTED_CPF_LENGTH, is_valid_cnpj, is_valid_cpf
from utils.request_hash import hash_request_body


# CLI-08: limite configurável no ambiente; padrão 10.
```

  2. O método `get_transaction` abaixo entra logo depois do método `transfer` e antes de `_find_repeated`, com uma linha em branco antes dele:

```python
    def get_transaction(self, account_key: str, account_token: str, transaction_key: str) -> dict:
        """Uma operação, só para o dono, com os lançamentos da conta e do cofrinho dela. Não grava nada.

        1. a conta é do dono do token (404 QIT001010, R8);
        2. a operação existe e tem lançamento na conta ou no cofrinho dela
           (404 QIT001020): operação de outra conta responde como se não
           existisse (R8).
        """
        account = self.get_owned_account(account_key, account_token)
        piggy_bank = self.account_repository.get_piggy_bank(account)
        account_ids = [account.id, piggy_bank.id]

        transaction = self.transaction_repository.get_by_key_for_account(transaction_key, account_ids)

        if transaction is None:
            raise TransactionNotFound(transaction_key)

        entries = []
        for entry in self.entry_repository.list_by_transaction(transaction, account_ids):
            entries.append(self._entry_to_dict(entry, transaction))

        return TransactionDTO.obj_to_dict(transaction, entries)
```

  3. Os métodos `_entry_to_dict` e `_counterparty` abaixo entram no fim da classe, nesta ordem, logo depois de `_balance_after`, com uma linha em branco antes de cada um:

```python
    def _entry_to_dict(self, entry: Entry, transaction: Transaction) -> dict:
        return EntryDTO.obj_to_dict(entry, transaction, self._counterparty(entry, transaction))
```

```python
    def _counterparty(self, entry: Entry, transaction: Transaction) -> dict:
        """A outra ponta do lançamento (MOV-17), nesta ordem:

        1. tarifa, prêmio, rendimento, IOF e IR (tudo que não é AMOUNT): o banco;
        2. AMOUNT de transferência: o outro cliente, com o CPF mascarado;
        3. AMOUNT de depósito: quem depositou, com o documento mascarado;
        4. o resto (saque): None. Guardar e resgatar entram no passo 7.7.
        """
        if entry.entry_type.enumerator != EntryType.AMOUNT:
            return EntryDTO.bank_counterparty()

        transaction_type = transaction.transaction_type.enumerator

        if transaction_type == TransactionType.TRANSFER:
            return EntryDTO.customer_counterparty(self.entry_repository.get_transfer_counterparty_customer(entry))

        if transaction_type == TransactionType.DEPOSIT:
            return EntryDTO.depositor_counterparty(self.deposit_repository.get_by_transaction(transaction))

        return None
```

- `src/resources/transaction.py` (editar): o conteúdo inteiro passa a ser:

```python
from fastapi import Request
from fastapi import status as http_status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from constants import ACCOUNT_TOKEN_HEADER
from controllers import TransactionController
from utils.schema_handler import SchemaHandler


class TransactionResource:
    """A porta HTTP do dinheiro: depósito, saque, transferência, consulta e extrato.

    Sem regra de negócio, sem SQL e sem nada guardado no self (ARQ-02). O
    token da conta chega no cabeçalho ACCOUNT-TOKEN (API-16); quem o
    confere é o controller.
    """

    @SchemaHandler.validate("post_deposits.json")
    def on_post_deposit(self, account_key: str, payload: dict) -> JSONResponse:
        controller = TransactionController()
        transaction = controller.deposit(account_key, payload)

        return JSONResponse(
            content=jsonable_encoder(transaction),
            status_code=http_status.HTTP_201_CREATED,
        )

    @SchemaHandler.validate("post_withdrawals.json")
    def on_post_withdrawal(self, account_key: str, payload: dict, request: Request) -> JSONResponse:
        controller = TransactionController()
        transaction = controller.withdraw(account_key, request.headers.get(ACCOUNT_TOKEN_HEADER), payload)

        return JSONResponse(
            content=jsonable_encoder(transaction),
            status_code=http_status.HTTP_201_CREATED,
        )

    @SchemaHandler.validate("post_transfers.json")
    def on_post_transfer(self, account_key: str, payload: dict, request: Request) -> JSONResponse:
        controller = TransactionController()
        transaction = controller.transfer(account_key, request.headers.get(ACCOUNT_TOKEN_HEADER), payload)

        return JSONResponse(
            content=jsonable_encoder(transaction),
            status_code=http_status.HTTP_201_CREATED,
        )

    def on_get_transaction(self, account_key: str, transaction_key: str, request: Request) -> JSONResponse:
        controller = TransactionController()
        transaction = controller.get_transaction(account_key, request.headers.get(ACCOUNT_TOKEN_HEADER), transaction_key)

        return JSONResponse(
            content=jsonable_encoder(transaction),
            status_code=http_status.HTTP_200_OK,
        )
```

- `src/app.py` (editar): uma troca, e nada mais. A linha
  ```python
      application.add_api_route("/accounts/{account_key}/transfers", transaction_resource.on_post_transfer, methods=["POST"])
  ```
  vira as duas linhas
  ```python
      application.add_api_route("/accounts/{account_key}/transfers", transaction_resource.on_post_transfer, methods=["POST"])
      application.add_api_route("/accounts/{account_key}/transactions/{transaction_key}", transaction_resource.on_get_transaction, methods=["GET"])
  ```

- `tests/integration/transactions/test_get_transaction.py` (criar): o conteúdo inteiro é:

```python
"""Consulta da operação: GET /accounts/{account_key}/transactions/{transaction_key} (MOV-07, MOV-09, MOV-17, MOV-18, DAD-17, PRD-12, R5, R8).

O dono vê a operação e os lançamentos dela na conta dele, com a outra
ponta de cada um: na transferência, o outro cliente com o CPF mascarado;
no depósito, quem depositou; na tarifa, o banco; no saque, nada.
Operação de outra conta responde como se não existisse. Os testes que
erram o token começam com DbUtils.rollback() (PRD-10).
"""

import re
from uuid import uuid4

from tests.utils import INTERNAL_TOKEN, DbUtils, ObjectGenerator, PayloadGenerator, RandomGenerator, RequestGenerator
from tests.utils.requisition import ClientRequisition


DATE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
DATETIME = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}")
ENTRY_FIELDS = sorted([
    "entry_key", "transaction_key", "transaction_type", "entry_type", "amount",
    "balance_after", "category", "counterparty", "accounting_date", "created_at",
])


def assert_no_internal_id(body) -> None:
    """R5: nenhum campo id nem terminado em _id, em nenhum nível da resposta."""
    if isinstance(body, dict):
        for field, value in body.items():
            assert field != "id", field
            assert not field.endswith("_id"), field
            assert_no_internal_id(value)

    if isinstance(body, list):
        for item in body:
            assert_no_internal_id(item)


def masked_cpf(document_number: str) -> str:
    return "***" + document_number[3:12] + "**"


def create_named_account(name: str, document_number: str) -> dict:
    customer_key = ObjectGenerator.create_customer(name=name, document_number=document_number)

    return ObjectGenerator.create_account(customer_key)


def get_transaction(account: dict, transaction_key: str) -> tuple:
    return RequestGenerator.GET_transaction(account["account_key"], account["account_token"], transaction_key)


def assert_transaction(response: dict, transaction_key: str, transaction_type: str) -> None:
    assert sorted(response) == ["accounting_date", "created_at", "entries", "transaction_key", "type"]
    assert response["transaction_key"] == transaction_key
    assert response["type"] == transaction_type
    assert DATE.match(response["accounting_date"])
    assert DATETIME.match(response["created_at"])

    for entry in response["entries"]:
        assert sorted(entry) == ENTRY_FIELDS
        assert entry["transaction_key"] == transaction_key
        assert entry["transaction_type"] == transaction_type
        assert entry["accounting_date"] == response["accounting_date"]
        assert DATETIME.match(entry["created_at"])
        assert entry["category"] is None
        assert type(entry["amount"]) is int

    assert_no_internal_id(response)


class TestGetTransaction:
    def test_gets_transfer_from_the_origin(self):
        origin = ObjectGenerator.create_funded_account(50000)
        destination_document = RandomGenerator.generate_cpf()
        destination = create_named_account("Bruno Alves", destination_document)

        status, response = RequestGenerator.POST_transfer(
            origin["account_key"], origin["account_token"], PayloadGenerator.transfer(destination["account_key"], amount=10000)
        )
        assert status == 201, response
        transaction_key = response["transaction_key"]

        status, response = get_transaction(origin, transaction_key)

        assert status == 200, response
        assert_transaction(response, transaction_key, "TRANSFER")
        assert [(entry["entry_type"], entry["amount"], entry["balance_after"]) for entry in response["entries"]] == [
            ("AMOUNT", -10000, 40000),
            ("FEE", -100, 39900),
        ]
        assert response["entries"][0]["counterparty"] == {
            "type": "CUSTOMER",
            "name": "Bruno Alves",
            "document_number": masked_cpf(destination_document),
        }
        assert response["entries"][1]["counterparty"] == {"type": "BANK"}

    def test_gets_transfer_from_the_destination(self):
        origin_document = RandomGenerator.generate_cpf()
        origin = create_named_account("Ana Lima", origin_document)
        status, response = RequestGenerator.POST_deposit(origin["account_key"], PayloadGenerator.deposit(amount=50000))
        assert status == 201, response
        destination = ObjectGenerator.create_account()

        status, response = RequestGenerator.POST_transfer(
            origin["account_key"], origin["account_token"], PayloadGenerator.transfer(destination["account_key"], amount=10000)
        )
        assert status == 201, response
        transaction_key = response["transaction_key"]

        status, response = get_transaction(destination, transaction_key)

        assert status == 200, response
        assert_transaction(response, transaction_key, "TRANSFER")
        assert len(response["entries"]) == 1
        entry = response["entries"][0]
        assert (entry["entry_type"], entry["amount"], entry["balance_after"]) == ("AMOUNT", 10000, 10000)
        assert entry["counterparty"] == {"type": "CUSTOMER", "name": "Ana Lima", "document_number": masked_cpf(origin_document)}

    def test_gets_deposit_with_masked_depositor(self):
        account = ObjectGenerator.create_account()
        cnpj = RandomGenerator.generate_cnpj()
        cpf = RandomGenerator.generate_cpf()

        expected = []
        for depositor_document, masked in [(cnpj, "**" + cnpj[2:11] + "****-**"), (cpf, masked_cpf(cpf))]:
            payload = PayloadGenerator.deposit(amount=5050, depositor_name="Carlos Souza", depositor_document=depositor_document)
            status, response = RequestGenerator.POST_deposit(account["account_key"], payload)
            assert status == 201, response
            expected.append((response["transaction_key"], masked))

        for index, (transaction_key, masked) in enumerate(expected):
            status, response = get_transaction(account, transaction_key)

            assert status == 200, response
            assert_transaction(response, transaction_key, "DEPOSIT")
            assert len(response["entries"]) == 1
            entry = response["entries"][0]
            assert (entry["entry_type"], entry["amount"], entry["balance_after"]) == ("AMOUNT", 5050, 5050 * (index + 1))
            assert entry["counterparty"] == {"type": "DEPOSITOR", "name": "Carlos Souza", "document_number": masked}

    def test_gets_withdrawal_without_counterparty(self):
        account = ObjectGenerator.create_funded_account(10000)

        status, response = RequestGenerator.POST_withdrawal(account["account_key"], account["account_token"], PayloadGenerator.withdrawal(amount=2500))
        assert status == 201, response
        transaction_key = response["transaction_key"]

        status, response = get_transaction(account, transaction_key)

        assert status == 200, response
        assert_transaction(response, transaction_key, "WITHDRAWAL")
        assert len(response["entries"]) == 1
        entry = response["entries"][0]
        assert (entry["entry_type"], entry["amount"], entry["balance_after"], entry["counterparty"]) == ("AMOUNT", -2500, 7500, None)

    def test_transaction_of_other_account_is_404(self):
        origin = ObjectGenerator.create_funded_account(10000)
        destination = ObjectGenerator.create_account()
        stranger = ObjectGenerator.create_account()

        status, response = RequestGenerator.POST_transfer(
            origin["account_key"], origin["account_token"], PayloadGenerator.transfer(destination["account_key"], amount=1000)
        )
        assert status == 201, response

        for transaction_key in [response["transaction_key"], str(uuid4()), "nao-e-uma-key"]:
            status, response = get_transaction(stranger, transaction_key)

            assert status == 404, (transaction_key, response)
            assert response["code"] == "QIT001020"

    def test_other_account_token_is_404(self):
        DbUtils.rollback()
        account = ObjectGenerator.create_funded_account(10000)
        other_account = ObjectGenerator.create_account()

        status, response = RequestGenerator.POST_withdrawal(account["account_key"], account["account_token"], PayloadGenerator.withdrawal(amount=100))
        assert status == 201, response
        transaction_key = response["transaction_key"]

        for account_token in [other_account["account_token"], None, "token_errado"]:
            status, response = RequestGenerator.GET_transaction(account["account_key"], account_token, transaction_key)

            assert status == 404, (account_token, response)
            assert response["code"] == "QIT001010"

        status, response = get_transaction(account, transaction_key)
        assert status == 200, response

    def test_put_patch_and_delete_are_405(self):
        account = ObjectGenerator.create_funded_account(10000)

        status, response = RequestGenerator.POST_withdrawal(account["account_key"], account["account_token"], PayloadGenerator.withdrawal(amount=100))
        assert status == 201, response
        transaction_key = response["transaction_key"]

        status, before = get_transaction(account, transaction_key)
        assert status == 200, before

        endpoint = f"/accounts/{account['account_key']}/transactions/{transaction_key}"
        headers = {"INTERNAL-TOKEN": INTERNAL_TOKEN, "ACCOUNT-TOKEN": account["account_token"]}

        for method in ["PUT", "PATCH", "DELETE"]:
            response = ClientRequisition.send(method, endpoint, payload={"amount": 1}, headers=headers)

            assert response.response_status == 405, (method, response.response_json)
            assert response.response_json["code"] == "QIT000405"

        status, after = get_transaction(account, transaction_key)
        assert status == 200, after
        assert after == before
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/06-dinheiro`; `git log --oneline` mostra `feat(seguranca): limite diário de transferências e bloqueio automático`.
2. Crie `tests/integration/transactions/test_get_transaction.py` com o conteúdo do campo **Arquivos**.
3. `docker compose up -d --build --wait`.
4. `./.venv/Scripts/python.exe -m pytest -v tests/integration/transactions/test_get_transaction.py` → a última linha tem `7 failed` e não tem `passed`. Os 7 falham por asserção: hoje o caminho `/accounts/{account_key}/transactions/{transaction_key}` responde 404 `QIT000404` (no teste dos métodos, o `GET` de antes espera 200).
5. Faça as três mudanças em `src/controllers/transaction_controller.py`.
6. Edite `src/resources/transaction.py` com o conteúdo do campo **Arquivos**.
7. Faça a troca em `src/app.py`.
8. `docker compose up -d --build --wait`.
9. `./.venv/Scripts/python.exe -m pytest -v tests/integration/transactions/test_get_transaction.py` → a última linha tem `7 passed`.
10. Rode a conferência S5 do **Verificar**.
11. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `186 passed`.
12. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
13. Feche o passo (AGENTS.md, seção 7), um comando por vez:
    ```
    git add -- src/controllers/transaction_controller.py src/resources/transaction.py src/app.py tests/integration/transactions/test_get_transaction.py
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "feat(dinheiro): rota de consulta da operação"
    git log -1 --format=%B
    ```

**Testes:** `tests/integration/transactions/test_get_transaction.py`. A rota só lê: nenhum efeito no banco além da linha de `request_log`. A data contábil é conferida pelo formato (`AAAA-MM-DD`) e por bater com a dos lançamentos: o relógio é de todos, e a fase 7 o move (a igualdade com o relógio é a conferência D2 do 6.5).

| Função de teste | Entrada | Esperado |
|---|---|---|
| `test_gets_transfer_from_the_origin` | transferência de 10000 para "Bruno Alves"; consulta pela origem | 200; `type` `TRANSFER`, as duas datas; lançamentos `AMOUNT` −10000 (saldo depois 40000; outra ponta `CUSTOMER` "Bruno Alves" com o CPF mascarado) e `FEE` −100 (39900; outra ponta `BANK`); nenhum `id` em nenhum nível |
| `test_gets_transfer_from_the_destination` | a mesma operação, de "Ana Lima", consultada pelo destino | 200; um lançamento só, `AMOUNT` +10000 (saldo 10000), outra ponta "Ana Lima" com o CPF mascarado; sem `FEE` (quem paga é quem envia) |
| `test_gets_deposit_with_masked_depositor` | depósitos com CNPJ e com CPF de "Carlos Souza" | 200; `DEPOSIT`; `AMOUNT` +5050 com saldos 5050 e 10100; outra ponta `DEPOSITOR` "Carlos Souza" com o documento mascarado: CNPJ como `**.XXX.XXX/****-**` e CPF como `***.XXX.XXX-**` (PRD-12) |
| `test_gets_withdrawal_without_counterparty` | saque de 2500 | 200; `WITHDRAWAL`; `AMOUNT` −2500, saldo 7500, `counterparty` `null` |
| `test_transaction_of_other_account_is_404` | uma terceira conta consulta, com o próprio token, a operação de outras duas; uma key que não existe; `nao-e-uma-key` | 404 `QIT001020` nos três (R8) |
| `test_other_account_token_is_404` | começa com `DbUtils.rollback()`; a operação da conta A pelo caminho de A com o token de B, sem token e com `token_errado`; depois com o token de A | 404 `QIT001010` nos três; 200 |
| `test_put_patch_and_delete_are_405` | `PUT`, `PATCH` e `DELETE` no caminho da operação, com os tokens certos | 405 `QIT000405` nos três; a consulta depois é igual à de antes (nada muda) |

**Verificar:**
- `./.venv/Scripts/python.exe -m pytest -v tests/integration/transactions/test_get_transaction.py` → `7 passed`.
- S5 (um comando, numa linha só):
  ```
  docker compose exec -T api python -c "from controllers import TransactionController; print(sorted(n for n in vars(TransactionController) if not n.startswith('__')))"
  ```
  → `['_balance_after', '_counterparty', '_entry_to_dict', '_find_repeated', '_is_valid_depositor_document', 'deposit', 'get_transaction', 'transfer', 'withdraw']`
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `186 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/app.py
  src/controllers/transaction_controller.py
  src/resources/transaction.py
  tests/integration/transactions/test_get_transaction.py
  ```
- `git log -1 --format=%B` → `feat(dinheiro): rota de consulta da operação`

**Pronto quando:**
- [ ] Os 7 testes falharam antes do código (item 4) e passam depois (item 9).
- [ ] A S5 dá a lista esperada.
- [ ] Suíte com `186 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/06-dinheiro`.

**Commit:** `feat(dinheiro): rota de consulta da operação`
**Pare se:**
- O item 4 não terminar com `7 failed`.
- Um teste receber 500 (`QIT000500`): rode `docker compose logs --tail 100 api` e traga a saída.
- `test_put_patch_and_delete_are_405` receber outro status que não 405.
- A suíte não terminar com `186 passed`.

---

### Passo 6.11 — `GET /accounts/{account_key}/entries` (extrato)
**Branch:** fase/06-dinheiro · **Depende de:** 6.10
**Objetivo:** `EntryRepository.list_page` (`created_at` decrescente, desempate por `id` decrescente, pede `limit + 1`); `TransactionController.list_entries` e a rota `GET /accounts/{account_key}/entries` (tokens: conta; schema `get_entries.json`), no envelope do base; 404 `QIT001010`; 400 `QIT000001`.
**Decisões:** MOV-04 — envelope do extrato · MOV-14 — ordem do extrato · MOV-17 — outra ponta · MOV-18 — duas datas · TST-03 — extrato paginado · DAD-07 — saldo em dois lugares · DAD-13 — recusa não grava · API-03 — schema fechado na query · R8 — outro dono → 404 · TST-01 — black box e TDD
**Arquivos:**
- `src/repositories/entry_repository.py` (editar): o método `list_page` abaixo entra no fim da classe, logo depois de `get_transfer_counterparty_customer`, com uma linha em branco antes dele. Os imports não mudam (`Transaction` já está no arquivo).

```python
    def list_page(self, account: Account, limit: int, offset: int) -> list:
        """Uma página do extrato da conta: pares (lançamento, operação), mais recente primeiro (MOV-14).

        Ordem: created_at decrescente e, no empate (os lançamentos de uma
        operação nascem no mesmo instante), o id decrescente. Pede limit + 1
        linhas: a linha a mais só diz ao controller que existe próxima
        página. O índice entry_account_created_at_id_idx cobre esta consulta.
        """
        return (
            self.session.query(Entry, Transaction)
            .join(Transaction, Transaction.id == Entry.transaction_id)
            .filter(Entry.account_id == account.id)
            .order_by(Entry.created_at.desc(), Entry.id.desc())
            .limit(limit + 1)
            .offset(offset)
            .all()
        )
```

- `src/controllers/transaction_controller.py` (editar): o método `list_entries` abaixo entra logo depois do método `get_transaction` e antes de `_find_repeated`, com uma linha em branco antes dele. Os imports não mudam.

```python
    def list_entries(self, account_key: str, account_token: str, limit: int, offset: int) -> dict:
        """Uma página do extrato da conta principal, só para o dono (MOV-04, MOV-14). Não grava nada.

        Pede limit + 1 linhas ao repository: se veio a linha a mais, existe
        próxima página, e ela não entra na resposta.
        """
        account = self.get_owned_account(account_key, account_token)

        rows = self.entry_repository.list_page(account, limit, offset)

        is_last_page = True
        if len(rows) > limit:
            is_last_page = False
            rows = rows[:-1]

        entries = []
        for entry, transaction in rows:
            entries.append(self._entry_to_dict(entry, transaction))

        return {
            "entries_list_dto": entries,
            "is_last_page": is_last_page,
        }
```

- `src/resources/transaction.py` (editar): o conteúdo inteiro passa a ser:

```python
from fastapi import Request
from fastapi import status as http_status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from constants import ACCOUNT_TOKEN_HEADER
from controllers import TransactionController
from utils.schema_handler import SchemaHandler


# MOV-04: o extrato começa na página 0, com 10 itens, quando a query string não diz.
DEFAULT_LIMIT = 10
DEFAULT_PAGE = 0


class TransactionResource:
    """A porta HTTP do dinheiro: depósito, saque, transferência, consulta e extrato.

    Sem regra de negócio, sem SQL e sem nada guardado no self (ARQ-02). O
    token da conta chega no cabeçalho ACCOUNT-TOKEN (API-16); quem o
    confere é o controller.
    """

    @SchemaHandler.validate("post_deposits.json")
    def on_post_deposit(self, account_key: str, payload: dict) -> JSONResponse:
        controller = TransactionController()
        transaction = controller.deposit(account_key, payload)

        return JSONResponse(
            content=jsonable_encoder(transaction),
            status_code=http_status.HTTP_201_CREATED,
        )

    @SchemaHandler.validate("post_withdrawals.json")
    def on_post_withdrawal(self, account_key: str, payload: dict, request: Request) -> JSONResponse:
        controller = TransactionController()
        transaction = controller.withdraw(account_key, request.headers.get(ACCOUNT_TOKEN_HEADER), payload)

        return JSONResponse(
            content=jsonable_encoder(transaction),
            status_code=http_status.HTTP_201_CREATED,
        )

    @SchemaHandler.validate("post_transfers.json")
    def on_post_transfer(self, account_key: str, payload: dict, request: Request) -> JSONResponse:
        controller = TransactionController()
        transaction = controller.transfer(account_key, request.headers.get(ACCOUNT_TOKEN_HEADER), payload)

        return JSONResponse(
            content=jsonable_encoder(transaction),
            status_code=http_status.HTTP_201_CREATED,
        )

    def on_get_transaction(self, account_key: str, transaction_key: str, request: Request) -> JSONResponse:
        controller = TransactionController()
        transaction = controller.get_transaction(account_key, request.headers.get(ACCOUNT_TOKEN_HEADER), transaction_key)

        return JSONResponse(
            content=jsonable_encoder(transaction),
            status_code=http_status.HTTP_200_OK,
        )

    @SchemaHandler.validate_query_params("get_entries.json")
    def on_get_entries(self, account_key: str, request: Request) -> JSONResponse:
        """Uma página do extrato. O schema get_entries.json já garantiu que limit e page são dígitos."""
        controller = TransactionController()

        query_params = request.query_params
        limit = int(query_params.get("limit", DEFAULT_LIMIT))
        page = int(query_params.get("page", DEFAULT_PAGE))
        offset = page * limit

        entries_page = controller.list_entries(account_key, request.headers.get(ACCOUNT_TOKEN_HEADER), limit, offset)

        # O envelope da página fala de limit e page, vocabulário de HTTP: quem o monta é o resource, como no base.
        page_envelope = {
            "data": entries_page["entries_list_dto"],
            "limit": limit,
            "page": page,
            "is_last_page": entries_page["is_last_page"],
        }

        return JSONResponse(
            content=jsonable_encoder(page_envelope),
            status_code=http_status.HTTP_200_OK,
        )
```

- `src/app.py` (editar): uma troca, e nada mais. A linha
  ```python
      application.add_api_route("/accounts/{account_key}/transactions/{transaction_key}", transaction_resource.on_get_transaction, methods=["GET"])
  ```
  vira as duas linhas
  ```python
      application.add_api_route("/accounts/{account_key}/transactions/{transaction_key}", transaction_resource.on_get_transaction, methods=["GET"])
      application.add_api_route("/accounts/{account_key}/entries", transaction_resource.on_get_entries, methods=["GET"])
  ```
  O trecho `# Dinheiro` fica exatamente assim:
  ```python
      # Dinheiro
      application.add_api_route("/accounts/{account_key}/deposits", transaction_resource.on_post_deposit, methods=["POST"])
      application.add_api_route("/accounts/{account_key}/withdrawals", transaction_resource.on_post_withdrawal, methods=["POST"])
      application.add_api_route("/accounts/{account_key}/transfers", transaction_resource.on_post_transfer, methods=["POST"])
      application.add_api_route("/accounts/{account_key}/transactions/{transaction_key}", transaction_resource.on_get_transaction, methods=["GET"])
      application.add_api_route("/accounts/{account_key}/entries", transaction_resource.on_get_entries, methods=["GET"])
  ```

- `tests/integration/transactions/test_entries.py` (criar): o conteúdo inteiro é:

```python
"""Extrato: GET /accounts/{account_key}/entries (TST-03, MOV-04, MOV-09, MOV-14, MOV-17, MOV-18, DAD-07, DAD-13, R5, R8).

O extrato da conta principal, no envelope do base (`data`, `limit`,
`page`, `is_last_page`; `limit` padrão 10 e máximo 100; `page` a partir
de 0), mais recente primeiro, com desempate pelo lançamento mais novo.
A soma dos lançamentos é o saldo (DAD-07). Pedido recusado não deixa
lançamento (DAD-13). Os testes que erram o token ou que dependem do
relógio começam com DbUtils.rollback() (PRD-10, DIA-01).
"""

from tests.utils import DbUtils, ObjectGenerator, PayloadGenerator, RandomGenerator, RequestGenerator


def assert_no_internal_id(body) -> None:
    """R5: nenhum campo id nem terminado em _id, em nenhum nível da resposta."""
    if isinstance(body, dict):
        for field, value in body.items():
            assert field != "id", field
            assert not field.endswith("_id"), field
            assert_no_internal_id(value)

    if isinstance(body, list):
        for item in body:
            assert_no_internal_id(item)


def get_entries(account: dict, params: dict = None) -> tuple:
    return RequestGenerator.GET_entries(account["account_key"], account["account_token"], params)


def all_entries(account: dict) -> list:
    """Todas as páginas do extrato, com limit 100, da mais recente para a mais antiga."""
    entries = []
    page = 0

    while True:
        status, response = get_entries(account, {"limit": "100", "page": str(page)})
        assert status == 200, response
        entries.extend(response["data"])

        if response["is_last_page"]:
            return entries

        page = page + 1


def balance_of(account: dict) -> int:
    status, response = RequestGenerator.GET_account(account["account_key"], account["account_token"])
    assert status == 200, response

    return response["balance"]


def deposit(account: dict, amount: int) -> None:
    status, response = RequestGenerator.POST_deposit(account["account_key"], PayloadGenerator.deposit(amount=amount))
    assert status == 201, response


def transfer(origin: dict, destination: dict, amount: int) -> tuple:
    payload = PayloadGenerator.transfer(destination["account_key"], amount=amount)

    return RequestGenerator.POST_transfer(origin["account_key"], origin["account_token"], payload)


class TestEntries:
    def test_empty_statement(self):
        account = ObjectGenerator.create_account()

        status, response = get_entries(account)

        assert status == 200, response
        assert response == {"data": [], "limit": 10, "page": 0, "is_last_page": True}

    def test_pagination(self):
        account = ObjectGenerator.create_account()
        for amount in [100, 200, 300]:
            deposit(account, amount)

        status, response = get_entries(account, {"limit": "2", "page": "0"})
        assert status == 200, response
        assert (response["limit"], response["page"], response["is_last_page"]) == (2, 0, False)
        assert [entry["amount"] for entry in response["data"]] == [300, 200]

        status, response = get_entries(account, {"limit": "2", "page": "1"})
        assert status == 200, response
        assert (response["limit"], response["page"], response["is_last_page"]) == (2, 1, True)
        assert [entry["amount"] for entry in response["data"]] == [100]

        status, response = get_entries(account, {"limit": "2", "page": "2"})
        assert status == 200, response
        assert (response["data"], response["is_last_page"]) == ([], True)

    def test_default_and_maximum_limit(self):
        account = ObjectGenerator.create_account()
        for amount in range(1, 12):
            deposit(account, amount)

        status, response = get_entries(account)
        assert status == 200, response
        assert (len(response["data"]), response["limit"], response["page"], response["is_last_page"]) == (10, 10, 0, False)

        status, response = get_entries(account, {"limit": "100"})
        assert status == 200, response
        assert (len(response["data"]), response["limit"], response["is_last_page"]) == (11, 100, True)

    def test_most_recent_first_with_stable_tiebreak(self):
        origin = ObjectGenerator.create_funded_account(50000)
        destination = ObjectGenerator.create_account()

        status, response = transfer(origin, destination, 10000)
        assert status == 201, response

        entries = all_entries(origin)

        assert [(entry["transaction_type"], entry["entry_type"], entry["amount"], entry["balance_after"]) for entry in entries] == [
            ("TRANSFER", "FEE", -100, 39900),
            ("TRANSFER", "AMOUNT", -10000, 40000),
            ("DEPOSIT", "AMOUNT", 50000, 50000),
        ]
        assert entries[0]["transaction_key"] == entries[1]["transaction_key"] == response["transaction_key"]
        assert entries[0]["created_at"] == entries[1]["created_at"]
        assert entries[1]["created_at"] >= entries[2]["created_at"]
        assert all_entries(origin) == entries

    def test_shows_every_operation_with_counterparty_and_dates(self):
        origin_document = RandomGenerator.generate_cpf()
        origin = ObjectGenerator.create_account(ObjectGenerator.create_customer(name="Ana Lima", document_number=origin_document))
        destination_document = RandomGenerator.generate_cpf()
        destination = ObjectGenerator.create_account(ObjectGenerator.create_customer(name="Bruno Alves", document_number=destination_document))
        depositor_document = RandomGenerator.generate_cnpj()

        payload = PayloadGenerator.deposit(amount=50000, depositor_name="Carlos Souza", depositor_document=depositor_document)
        status, response = RequestGenerator.POST_deposit(origin["account_key"], payload)
        assert status == 201, response

        status, response = transfer(origin, destination, 10000)
        assert status == 201, response

        status, response = RequestGenerator.POST_withdrawal(origin["account_key"], origin["account_token"], PayloadGenerator.withdrawal(amount=900))
        assert status == 201, response

        origin_entries = all_entries(origin)
        assert [(entry["transaction_type"], entry["entry_type"], entry["amount"], entry["counterparty"]) for entry in origin_entries] == [
            ("WITHDRAWAL", "AMOUNT", -900, None),
            ("TRANSFER", "FEE", -100, {"type": "BANK"}),
            ("TRANSFER", "AMOUNT", -10000, {"type": "CUSTOMER", "name": "Bruno Alves", "document_number": "***" + destination_document[3:12] + "**"}),
            ("DEPOSIT", "AMOUNT", 50000, {"type": "DEPOSITOR", "name": "Carlos Souza", "document_number": "**" + depositor_document[2:11] + "****-**"}),
        ]

        destination_entries = all_entries(destination)
        assert [(entry["entry_type"], entry["amount"], entry["balance_after"], entry["counterparty"]) for entry in destination_entries] == [
            ("AMOUNT", 10000, 10000, {"type": "CUSTOMER", "name": "Ana Lima", "document_number": "***" + origin_document[3:12] + "**"}),
        ]

        for entry in origin_entries + destination_entries:
            assert entry["category"] is None
            assert len(entry["accounting_date"]) == 10
            assert entry["created_at"][10] == "T"
            assert type(entry["amount"]) is int
            assert type(entry["balance_after"]) is int

        assert_no_internal_id(origin_entries + destination_entries)

    def test_statement_reconciles_with_balance(self):
        first = ObjectGenerator.create_funded_account(30000)
        second = ObjectGenerator.create_funded_account(20000)

        for origin, destination, amount in [(first, second, 1234), (second, first, 999), (first, second, 1)]:
            status, response = transfer(origin, destination, amount)
            assert status == 201, response

        status, response = RequestGenerator.POST_withdrawal(first["account_key"], first["account_token"], PayloadGenerator.withdrawal(amount=777))
        assert status == 201, response

        for account in [first, second]:
            entries = all_entries(account)

            assert sum(entry["amount"] for entry in entries) == balance_of(account)
            assert entries[0]["balance_after"] == balance_of(account)

    def test_refused_requests_leave_no_entry(self):
        DbUtils.rollback()
        origin = ObjectGenerator.create_funded_account(100000)
        destination = ObjectGenerator.create_account()

        status, response = transfer(origin, destination, 200000)
        assert status == 422, response

        status, response = RequestGenerator.POST_withdrawal(origin["account_key"], origin["account_token"], PayloadGenerator.withdrawal(amount=200000))
        assert status == 422, response

        for _index in range(10):
            status, response = transfer(origin, destination, 100)
            assert status == 201, response

        status, response = transfer(origin, destination, 100)
        assert status == 422, response
        assert response["code"] == "QIT001019"

        entries = all_entries(origin)
        assert len(entries) == 1 + 10 * 2
        assert sum(entry["amount"] for entry in entries) == balance_of(origin) == 100000 - 10 * 101

    def test_refuses_query_out_of_schema(self):
        account = ObjectGenerator.create_account()

        for params in [{"limit": "0"}, {"limit": "-1"}, {"limit": "101"}, {"limit": "abc"}, {"page": "-1"}, {"page": "x"}, {"size": "10"}]:
            status, response = get_entries(account, params)

            assert status == 400, (params, response)
            assert response["code"] == "QIT000001"

    def test_other_account_token_is_404(self):
        DbUtils.rollback()
        account = ObjectGenerator.create_funded_account(1000)
        other_account = ObjectGenerator.create_account()

        for account_token in [other_account["account_token"], None, "token_errado"]:
            status, response = RequestGenerator.GET_entries(account["account_key"], account_token)

            assert status == 404, (account_token, response)
            assert response["code"] == "QIT001010"

        status, response = get_entries(account)
        assert status == 200, response
        assert len(response["data"]) == 1
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/06-dinheiro`; `git log --oneline` mostra `feat(dinheiro): rota de consulta da operação`.
2. Crie `tests/integration/transactions/test_entries.py` com o conteúdo do campo **Arquivos**.
3. `docker compose up -d --build --wait`.
4. `./.venv/Scripts/python.exe -m pytest -v tests/integration/transactions/test_entries.py` → a última linha tem `9 failed` e não tem `passed`. Os 9 falham por asserção: hoje o caminho `/accounts/{account_key}/entries` responde 404 `QIT000404`.
5. Acrescente `list_page` em `src/repositories/entry_repository.py`.
6. Acrescente `list_entries` em `src/controllers/transaction_controller.py`.
7. Edite `src/resources/transaction.py` com o conteúdo do campo **Arquivos**.
8. Faça a troca em `src/app.py` e confira o trecho `# Dinheiro`.
9. `docker compose up -d --build --wait`.
10. `./.venv/Scripts/python.exe -m pytest -v tests/integration/transactions/test_entries.py` → a última linha tem `9 passed`.
11. Rode a conferência S6 do **Verificar**.
12. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `195 passed`.
13. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
14. Feche o passo (AGENTS.md, seção 7), um comando por vez:
    ```
    git add -- src/repositories/entry_repository.py src/controllers/transaction_controller.py src/resources/transaction.py src/app.py tests/integration/transactions/test_entries.py
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "feat(extrato): rota do extrato paginado"
    git log -1 --format=%B
    ```

**Testes:** `tests/integration/transactions/test_entries.py`. A rota só lê: nenhum efeito no banco além da linha de `request_log`.

| Função de teste | Entrada | Esperado |
|---|---|---|
| `test_empty_statement` | conta nova, sem query | 200 e exatamente `{"data": [], "limit": 10, "page": 0, "is_last_page": true}` |
| `test_pagination` | depósitos de 100, 200 e 300; `limit=2` nas páginas 0, 1 e 2 | página 0: `[300, 200]`, `is_last_page` falso; página 1: `[100]`, verdadeiro; página 2: vazia, verdadeiro (TST-03, Aula 3) |
| `test_default_and_maximum_limit` | 11 depósitos; sem query; `limit=100` | 10 itens, `limit` 10, `page` 0, `is_last_page` falso; 11 itens, `limit` 100, verdadeiro (MOV-04) |
| `test_most_recent_first_with_stable_tiebreak` | depósito de 50000; transferência de 10000 | `FEE` −100 (39900), `AMOUNT` −10000 (40000), `DEPOSIT` +50000 (50000), nesta ordem; os dois da transferência com a mesma key e o mesmo `created_at` (desempate pelo `id`); a segunda leitura é igual (MOV-14) |
| `test_shows_every_operation_with_counterparty_and_dates` | depósito com CNPJ, transferência para "Bruno Alves" e saque, na conta de "Ana Lima"; o extrato das duas | origem: saque (`null`), tarifa (`BANK`), transferência ("Bruno Alves", CPF mascarado), depósito ("Carlos Souza", CNPJ mascarado); destino: +10000 com "Ana Lima"; `category` nulo, as duas datas, inteiros, nenhum `id` (MOV-17, MOV-18) |
| `test_statement_reconciles_with_balance` | duas contas, três transferências entre elas e um saque | em cada conta, a soma dos `amount` = o saldo, e o `balance_after` mais recente = o saldo (DAD-07) |
| `test_refused_requests_leave_no_entry` | começa com `DbUtils.rollback()`; transferência e saque sem saldo; 10 transferências; a 11ª | 21 lançamentos (o depósito + 10 × 2), nenhum dos recusados; a soma = o saldo = 98990 (DAD-13, CLI-08: "a 11ª não aparece no extrato") |
| `test_refuses_query_out_of_schema` | `limit` 0, −1, 101, `abc`; `page` −1, `x`; `size=10` | 400 `QIT000001` nos 7 |
| `test_other_account_token_is_404` | começa com `DbUtils.rollback()`; o extrato de A com o token de B, sem token e com `token_errado`; depois com o de A | 404 `QIT001010` nos três; 200 com 1 lançamento |

**Verificar:**
- `./.venv/Scripts/python.exe -m pytest -v tests/integration/transactions/test_entries.py` → `9 passed`.
- S6 (um comando, numa linha só):
  ```
  docker compose exec -T api python -c "from controllers import TransactionController; from repositories import EntryRepository; print(sorted(n for n in vars(TransactionController) if not n.startswith('_'))); print(sorted(n for n in vars(EntryRepository) if not n.startswith('_')))"
  ```
  → exatamente:
  ```
  ['deposit', 'get_transaction', 'list_entries', 'transfer', 'withdraw']
  ['create', 'get_transfer_counterparty_customer', 'list_by_transaction', 'list_page']
  ```
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `195 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/app.py
  src/controllers/transaction_controller.py
  src/repositories/entry_repository.py
  src/resources/transaction.py
  tests/integration/transactions/test_entries.py
  ```
- `git log -1 --format=%B` → `feat(extrato): rota do extrato paginado`

**Pronto quando:**
- [ ] Os 9 testes falharam antes do código (item 4) e passam depois (item 10).
- [ ] A S6 dá as 2 linhas esperadas.
- [ ] Suíte com `195 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/06-dinheiro`.

**Commit:** `feat(extrato): rota do extrato paginado`
**Pare se:**
- O item 4 não terminar com `9 failed`.
- `test_most_recent_first_with_stable_tiebreak` mostrar `AMOUNT` antes de `FEE`: o desempate por `id` decrescente não está na consulta.
- Um teste receber 500 (`QIT000500`): rode `docker compose logs --tail 100 api` e traga a saída.
- A suíte não terminar com `195 passed`.

---

### Passo 6.12 — Encerrar só com saldo zero
**Branch:** fase/06-dinheiro · **Depende de:** 6.11
**Objetivo:** `AccountController.close_account` recusa saldo diferente de zero com 409 `QIT001012`, depois de travar a conta e de conferir o estado.
**Decisões:** CLI-06 — encerrar zerada · CLI-05 — estados da conta · CLI-09 — bloqueada não encerra · MOV-05 — trava antes de conferir · TST-01 — black box e TDD
**Arquivos:**
- `src/controllers/account_controller.py` (editar): duas mudanças, e nada mais.
  1. A linha
     ```python
         AccountNotBlocked,
     ```
     vira as duas linhas
     ```python
         AccountNotBlocked,
         AccountNotEmpty,
     ```
  2. O método `close_account` inteiro (da linha `    def close_account(` até a linha `        self.session.commit()` que o fecha) passa a ser:

```python
    def close_account(self, account_key: str, account_token: str) -> None:
        """O dono encerra a conta (CLI-05, CLI-06). As regras, nesta ordem:

        1. a conta é do dono do token (404 QIT001010, R8);
        2. trava a linha da conta (o estado e o saldo são relidos depois da
           trava: um depósito ao mesmo tempo espera ou é esperado);
        3. a conta está ACTIVE (409 QIT001011): bloqueada precisa ser
           desbloqueada antes, e encerrada é final;
        4. o saldo é zero (409 QIT001012, CLI-06).

        O cofrinho zerado entra no passo 7.15, entre a regra 4 e a gravação.
        Depois: estado CLOSED e o evento, sem origem e sem motivo (quem muda
        é o dono).
        """
        account = self.get_owned_account(account_key, account_token)
        account = self.account_repository.lock_accounts([account])[0]

        if account.status.enumerator != AccountStatus.ACTIVE:
            raise AccountNotActive(account_key, account.status.enumerator)

        if account.balance != 0:
            raise AccountNotEmpty(account_key)

        self.account_repository.change_status(account, AccountStatus.CLOSED)

        self.session.commit()
```

- `tests/integration/accounts/test_close_account_with_balance.py` (criar): o conteúdo inteiro é:

```python
"""Encerrar só com saldo zero: DELETE /accounts/{account_key} (CLI-06, CLI-05, CLI-09).

Conta ACTIVE com saldo diferente de zero não encerra (409 QIT001012);
o estado vem antes do saldo: bloqueada responde 409 QIT001011. Depois de
zerar e encerrar, a conta não envia nem recebe dinheiro. O cofrinho
zerado entra no passo 7.15.
"""

from tests.utils import ObjectGenerator, PayloadGenerator, RequestGenerator


def account_of(account: dict) -> dict:
    status, response = RequestGenerator.GET_account(account["account_key"], account["account_token"])
    assert status == 200, response

    return response


def close(account: dict) -> tuple:
    return RequestGenerator.DELETE_account(account["account_key"], account["account_token"])


class TestCloseAccountWithBalance:
    def test_refuses_closing_with_balance(self):
        account = ObjectGenerator.create_funded_account(100)

        status, response = close(account)
        assert status == 409, response
        assert response["code"] == "QIT001012"
        assert (account_of(account)["status"], account_of(account)["balance"]) == ("ACTIVE", 100)

        status, response = RequestGenerator.POST_block(account["account_key"], PayloadGenerator.block())
        assert status == 204, response

        status, response = close(account)
        assert status == 409, response
        assert response["code"] == "QIT001011"

        status, response = RequestGenerator.POST_unblock(account["account_key"])
        assert status == 204, response
        assert account_of(account)["status"] == "ACTIVE"

    def test_closes_after_the_balance_reaches_zero(self):
        account = ObjectGenerator.create_funded_account(5000)
        sender = ObjectGenerator.create_funded_account(10000)

        status, response = close(account)
        assert status == 409, response
        assert response["code"] == "QIT001012"

        status, response = RequestGenerator.POST_withdrawal(account["account_key"], account["account_token"], PayloadGenerator.withdrawal(amount=5000))
        assert status == 201, response

        status, response = close(account)
        assert status == 204, response
        assert (account_of(account)["status"], account_of(account)["balance"]) == ("CLOSED", 0)

        status, response = RequestGenerator.POST_deposit(account["account_key"], PayloadGenerator.deposit(amount=100))
        assert status == 409, response
        assert response["code"] == "QIT001011"

        payload = PayloadGenerator.transfer(account["account_key"], amount=100)
        status, response = RequestGenerator.POST_transfer(sender["account_key"], sender["account_token"], payload)
        assert status == 409, response
        assert response["code"] == "QIT001018"

        assert account_of(account)["balance"] == 0
        assert account_of(sender)["balance"] == 10000
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/06-dinheiro`; `git log --oneline` mostra `feat(extrato): rota do extrato paginado`.
2. Crie `tests/integration/accounts/test_close_account_with_balance.py` com o conteúdo do campo **Arquivos**.
3. `docker compose up -d --build --wait`.
4. `./.venv/Scripts/python.exe -m pytest -v tests/integration/accounts/test_close_account_with_balance.py` → a última linha tem `2 failed` e não tem `passed`. Os 2 falham por asserção: hoje a conta com saldo encerra com 204.
5. Faça as duas mudanças em `src/controllers/account_controller.py`.
6. `docker compose up -d --build --wait`.
7. `./.venv/Scripts/python.exe -m pytest -v tests/integration/accounts/test_close_account_with_balance.py` → a última linha tem `2 passed`.
8. `./.venv/Scripts/python.exe -m pytest -v tests/integration/accounts/test_close_account.py` → a última linha tem `7 passed` (o encerramento de conta zerada continua igual).
9. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `197 passed`.
10. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
11. Feche o passo (AGENTS.md, seção 7), um comando por vez:
    ```
    git add -- src/controllers/account_controller.py tests/integration/accounts/test_close_account_with_balance.py
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "feat(conta): encerrar só com saldo zero"
    git log -1 --format=%B
    ```

**Testes:** `tests/integration/accounts/test_close_account_with_balance.py`. Efeito no banco: o 409 não grava nada além da linha de `request_log`; o 204 grava o estado `CLOSED` e o evento, como no 5.11.

| Função de teste | Entrada | Esperado |
|---|---|---|
| `test_refuses_closing_with_balance` | conta com 100; `DELETE`; bloqueio; `DELETE`; desbloqueio | 409 `QIT001012`, `ACTIVE` e saldo 100; 409 `QIT001011` (o estado vem antes do saldo); `ACTIVE` |
| `test_closes_after_the_balance_reaches_zero` | conta com 5000; `DELETE`; saque de 5000; `DELETE`; depósito nela; transferência para ela | 409 `QIT001012`; 201; 204 e `CLOSED` com saldo 0; 409 `QIT001011`; 409 `QIT001018`; saldos 0 e 10000 (CLI-06: depois de encerrar, qualquer operação → 409) |

**Verificar:**
- `./.venv/Scripts/python.exe -m pytest -v tests/integration/accounts/test_close_account_with_balance.py` → `2 passed`.
- `git grep -n "raise AccountNotEmpty" -- src` → exatamente uma linha, em `src/controllers/account_controller.py`.
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `197 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/controllers/account_controller.py
  tests/integration/accounts/test_close_account_with_balance.py
  ```
- `git log -1 --format=%B` → `feat(conta): encerrar só com saldo zero`

**Pronto quando:**
- [ ] Os 2 testes falharam antes do código (item 4) e passam depois (item 7).
- [ ] Os 7 testes de `test_close_account.py` continuam verdes.
- [ ] Suíte com `197 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/06-dinheiro`.

**Commit:** `feat(conta): encerrar só com saldo zero`
**Pare se:**
- O item 4 não terminar com `2 failed`.
- A linha `    AccountNotBlocked,` não existir exatamente assim em `src/controllers/account_controller.py`.
- Um teste de `test_close_account.py` ficar vermelho.
- A suíte não terminar com `197 passed`.

---

### Passo 6.fim — Fechar a fase
**Branch:** fase/06-dinheiro · **Depende de:** 6.1 a 6.12
**Objetivo:** provar a fase com o banco recriado do zero e levá-la para a `main` com a tag `fase-06`.
**Decisões:** TIM-04 — git por fase · TIM-08 — git automático · ARQ-03 — SQL só com o banco vazio · ARQ-04 — sobe sem `.env` · TST-01 — suíte inteira verde
**Arquivos:** nenhum. O passo não cria, não edita e não apaga arquivo.
**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/06-dinheiro`.
2. `git log --oneline -n 13` → tem as 12 mensagens dos passos 6.1 a 6.12, cada uma uma vez:
   ```
   feat(dinheiro): repositories da operação, do lançamento, do depósito e do relógio
   feat(dinheiro): DTOs da operação e do extrato, CNPJ e documento mascarado
   feat(tarifa): calculate_fee com teste unitário
   feat(deposito): controller do depósito com idempotência
   feat(deposito): rota de depósito
   feat(saque): rota de saque pelo dono
   feat(transferencia): controller da transferência com tarifa e travas
   feat(transferencia): rota de transferência
   feat(seguranca): limite diário de transferências e bloqueio automático
   feat(dinheiro): rota de consulta da operação
   feat(extrato): rota do extrato paginado
   feat(conta): encerrar só com saldo zero
   ```
3. Recrie o banco do zero e suba tudo, um comando por vez:
   ```
   docker compose down -v
   docker compose up -d --build --wait
   ```
4. Rode a conferência T1 (passo 6.8) → as 4 linhas do **Verificar** do passo 6.8.
5. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `197 passed`.
6. `./.venv/Scripts/python.exe -m pytest` de novo → a última linha tem `197 passed` (nada intermitente).
7. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
8. `git status --short` → saída vazia.
9. Leve a fase para a `main`, um comando por vez:
   ```
   git switch main
   git merge --no-ff --no-edit -m "feat(dinheiro): fase 06 com depósito, saque, transferência com tarifa, limite diário, consulta e extrato" fase/06-dinheiro
   git tag fase-06
   ```
10. Rode o **Verificar**.

**Testes:** nenhum teste novo. A suíte inteira (122 de integração + 75 unitários) roda duas vezes com o banco recriado do zero (itens 5 e 6).
**Verificar:**
- O `git status --short` antes do merge não mostra alterações.
- `git branch --show-current` → `main`.
- `git log -1 --format=%B` → `feat(dinheiro): fase 06 com depósito, saque, transferência com tarifa, limite diário, consulta e extrato`.
- `git log -1 --format=%P` → dois hashes separados por um espaço (é um merge).
- `git tag --list fase-06` → `fase-06`.
- `git status --short` → saída vazia.

**Pronto quando:**
- [ ] A T1 dá o esperado com o banco recriado do zero.
- [ ] Suíte com `197 passed`, duas vezes seguidas; lint sem saída.
- [ ] Merge `--no-ff` na `main` com a mensagem exata; tag `fase-06` criada localmente; merge local na `main`.

**Commit:** nenhum commit de passo. Mensagem do merge: `feat(dinheiro): fase 06 com depósito, saque, transferência com tarifa, limite diário, consulta e extrato`
**Pare se:**
- Faltar uma das 12 mensagens do item 2.
- `docker compose up -d --build --wait` falhar: rode `docker compose logs --tail 100 db` e `docker compose logs --tail 100 api` e traga as duas saídas.
- A T1 der outra saída.
- A suíte não terminar com `197 passed` nas duas rodadas, ou o lint imprimir qualquer linha.
- O merge local der conflito (AGENTS.md, seção 8, item 9).

---

## Divergências encontradas

Seção para o Bruno; o agente não executa nada daqui.

| # | Onde | O que foi feito |
|---|---|---|
| 1 | PLANO-00, 6.7: "… destino ativo → trava das duas contas → saldo". | A trava vem antes das regras de estado: o controller busca o destino, trava as duas contas na ordem do `id` e só então confere, na ordem do índice, origem ativa → origem ≠ destino → destino existe → destino ativo → saldo. Mesmos erros e mesma precedência; o estado conferido é o relido depois da trava (MOV-05). Depósito e saque seguem o mesmo desenho. |
| 2 | PLANO-00, 6.9, e CLI-08 não dizem onde o limite entra na ordem nem de quando conta "desde o último desbloqueio". | O limite é a última regra, depois do saldo, na ordem dos erros de `docs/rotas.md` (…`QIT001015` · `QIT001019`…): só conta como 11ª "enviada" a que passaria em todas as outras regras; a 11ª sem saldo dá 422 `QIT001015` e não bloqueia (`test_eleventh_without_balance_is_insufficient_balance`). A contagem parte do `created_at` do último evento `ACTIVE` (abertura ou desbloqueio), por um nome novo, `AccountRepository.get_active_since`; por isso `src/repositories/account_repository.py` entrou nos arquivos do 6.9. |
| 3 | MOV-19: "`request_hash` (SHA-256 do corpo)"; `docs/rotas.md`: "mesmo pedido (a mesma `account_key` da URL e o mesmo corpo)". | O hash cobre a operação (`DEPOSIT`, `WITHDRAWAL`, `TRANSFER`), a `account_key` da URL e o corpo. A mesma chave em outra conta, ou em outra operação, dá 409 `QIT001014`. |
| 4 | PLANO-00, 6.4: "repetição … ; conta de cliente ativa; documento válido" (não cita a conta que não existe). | Ordem do depósito: conta existe (404) → repetição → trava → ativa → documento. A repetição vem antes do estado: o mesmo pedido, repetido depois de a conta ser bloqueada, devolve a resposta da primeira vez. O 404 do depósito não conta como falha de token (a rota não tem token de conta). |
| 5 | DIA-01 e o PLANO-00 não dizem como as operações convivem com a virada (fase 7). | `get_accounting_date` lê o relógio com `FOR SHARE`, antes de travar contas: a virada (`lock`, `FOR UPDATE`) espera as operações em andamento, e as novas esperam a virada. `advance` soma 1 dia de calendário (o dia sem CDI não rende: COF-16). A fase 7 pode trocar o `advance`, se decidir outra coisa. |
| 6 | MOV-10: "tarifa zero não gera lançamento" (TST-01: dois testes por `if`). | Com 0 pontos a tarifa é sempre ≥ 1 centavo, então o lado "tarifa zero" do `if fee > 0` só tem teste black box no passo 8.7 (10 pontos em tarifa). Nesta fase, a conta está no unitário (`test_ten_fee_points_make_the_fee_zero`). Levar para o 8.7: um teste com tarifa 0 que confere a ausência do lançamento `FEE` no extrato. |
| 7 | 09: "bloqueio automático e virada do dia → continua bloqueada". | Fica para a fase 7, quando a rota da virada existir. |
| 8 | `src/utils/document_number.py`: a docstring do base citava `post_sample_entity.json`, e o `git grep -e sample_entity -- src tests/utils` do 4.8 esperava nenhuma linha. | O 6.2 reescreve o arquivo inteiro, citando `post_customers.json`. Se o 4.8 parou nesse ponto e o arquivo já foi corrigido à mão, o conteúdo do 6.2 continua valendo inteiro. |
| 9 | O `RequestGenerator` não tem `PUT` nem `PATCH`. | `test_put_patch_and_delete_are_405` chama `ClientRequisition.send` (de `tests/utils/requisition.py`), com os tokens certos; continua black box (TST-01). |
| 10 | 09: datas no extrato. O relógio é um só para a suíte, e a fase 7 o move. | Os testes conferem o formato da `accounting_date` e que ela bate entre a operação e os lançamentos; a igualdade com o relógio é provada pela conferência D2 do 6.5. |
| 11 | `docs/rotas.md`: `category` no item do extrato e a outra ponta de guardar e resgatar. | `EntryDTO.obj_to_dict` já aceita `category` (nulo nesta fase). `_counterparty` devolve `null` para `SAVE` e `REDEEM` até o passo 7.7, que deve acrescentar `PIGGY_BANK` e `ACCOUNT`. |
| 12 | Provas extras (TST-08, fase 11). | Concorrência, travas cruzadas, mesma chave ao mesmo tempo e reconciliação já têm um teste aqui; a fase 11 repete com 10 rodadas. |

## Nomes novos da fase 06 (registrar no PLANO-00)

Seção para o Bruno; o agente não executa nada daqui.

| Onde | Nomes |
|---|---|
| `TransactionRepository` | assinaturas: `create(transaction_type_enumerator, request_control_key, request_hash, accounting_date)`; `get_by_key_for_account(transaction_key, account_ids)`; `count_transfers_sent(account, accounting_date, since)` |
| `EntryRepository` | `create(transaction, account, entry_type_enumerator, amount, category=None)`; `list_by_transaction(transaction, account_ids)` (6.1, novo); `get_transfer_counterparty_customer(entry)` (6.1, novo); `list_page(account, limit, offset)` devolve pares (lançamento, operação) |
| `DepositRepository` | `create(transaction, depositor_name, depositor_document)`; `get_by_transaction(transaction)` (6.1, novo) |
| `BankClockRepository` | `get_accounting_date()` com `FOR SHARE`; `lock()`; `advance(bank_clock)` (+1 dia) |
| `AccountRepository` | `get_active_since(account)` (6.9, novo) |
| `src/utils/document_number.py` | constantes `CNPJ_LENGTH`, `CNPJ_FIRST_WEIGHTS`, `CNPJ_SECOND_WEIGHTS`, `FORMATTED_CPF_LENGTH`, `FORMATTED_CNPJ_LENGTH` |
| `src/utils/request_hash.py` | assinatura `hash_request_body(transaction_type, account_key, payload)` |
| `src/calculations/fee.py` | constantes `FULL_FEE_TENTHS_OF_PERCENT`, `MAX_FEE_POINTS`, `TENTHS_OF_PERCENT_DIVISOR` |
| `TransactionDTO` | `only_obj_key(transaction)`, `with_balance(transaction, balance)`, `obj_to_dict(transaction, entries)` |
| `EntryDTO` | `obj_to_dict(entry, transaction, counterparty, category=None)`, `customer_counterparty(customer)`, `depositor_counterparty(deposit)`, `bank_counterparty()` |
| `TransactionController` | `DAILY_TRANSFER_LIMIT` importado de `constants`, configurável no ambiente (padrão 10); assinaturas `deposit(account_key, deposit_data)`, `withdraw(account_key, account_token, withdrawal_data)`, `transfer(account_key, account_token, transfer_data)`, `get_transaction(account_key, account_token, transaction_key)`, `list_entries(account_key, account_token, limit, offset)`; privados `_find_repeated`, `_is_valid_depositor_document`, `_balance_after`, `_entry_to_dict`, `_counterparty` |
| `TransactionResource` | `on_post_deposit(account_key, payload)`, `on_post_withdrawal(account_key, payload, request)`, `on_post_transfer(account_key, payload, request)`, `on_get_transaction(account_key, transaction_key, request)`, `on_get_entries(account_key, request)`; constantes `DEFAULT_LIMIT = 10`, `DEFAULT_PAGE = 0` |
| `AccountController.close_account` | regra 4 (saldo zero); o cofrinho zerado do 7.15 entra entre a regra 4 e o `change_status` |
| Testes | pasta `tests/integration/transactions/`; ajudantes locais `balance_of`, `account_of`, `deposit`, `withdraw`, `transfer`, `send_transfers`, `assert_balances`, `assert_limit_reached`, `assert_transaction`, `masked_cpf`, `create_named_account`, `get_transaction`, `get_entries`, `all_entries`; `assert_no_internal_id` passa a descer em todos os níveis |
| Comportamento | ordem de toda operação de dinheiro: dono (ou conta existe) → repetição → relógio (`FOR SHARE`) → trava → regras → gravação |


## Logs críticos — auditoria 08/10

PRD-06: antes do commit, os controllers de dinheiro registram `operation_ready_to_commit` com `transaction_key`; a virada registra `day_closing_ready_to_commit` com data contábil; o bloqueio automático registra `account_block_ready_to_commit` com key e motivo. Não registrar corpo, CPF/CNPJ, tokens, IDs internos nem parâmetros SQL. Após os testes da fase, `docker compose logs --tail 500 api` deve conter as mensagens dos fluxos exercitados; elas indicam tentativa de concluir, não prova de commit. A prova do resultado continua sendo HTTP e reconciliação.
