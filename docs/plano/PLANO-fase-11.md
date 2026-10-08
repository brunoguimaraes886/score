> **Git local — Bruno, 08/10/2026:** durante a produção, branches, commits, merges e tags ficam locais. Não executar push, pull ou fetch nem exigir acesso ao GitHub. O envio completo será feito pelo Bruno somente no final, quando tudo estiver pronto. As verificações de commits e dependências são locais.

# PLANO — Fase 11 — provas extras

**Branch:** `fase/11-provas-extras` · **Depende de:** fase 9
**Objetivo:** provar, pela API, concorrência (duas transferências com saldo para uma; A paga B e B paga A), idempotência na corrida (a mesma chave ao mesmo tempo), reconciliação (a soma do extrato é o saldo) e que nenhum teste da suíte recebe 5xx fora dos dois 503 de dependência.

Regras de execução: `AGENTS.md`. Nomes obrigatórios: `docs/plano/PLANO-00-indice.md`, `docs/plano/PLANO-fase-03.md` (`docs/rotas.md`, catálogo de erros), `docs/plano/PLANO-fase-04.md` (`RequestGenerator`, `PayloadGenerator`, `ObjectGenerator`), `docs/plano/PLANO-fase-07.md` (`MockGenerator`) e `docs/plano/PLANO-fase-09.md` (o `transfer` com o sorteio). Um passo por vez, na ordem: 11.1 a 11.6 e, por último, 11.fim.

Todos os passos são de prova (AGENTS.md, seção 6): o teste confere o que já existe. Escreva, rode e veja passar; se falhar, PARE, porque o conserto fica fora do passo. Nenhum arquivo de `src/` muda nesta fase.

Contagem de testes da suíte (última linha do pytest): `401 passed` no começo; `403 passed` em 11.1; `410 passed` em 11.2; `412 passed` em 11.3; `414 passed` em 11.4 e 11.5; `426 passed` em 11.6 e no 11.fim (271 de integração + 155 em tests/unit, destes 3 usam PostgreSQL real).

Comandos usados nesta fase que não estão na seção 3 do `AGENTS.md`:

| Quero | Comando |
|---|---|
| Rodar uma linha de Python no `.venv` (a raiz do repositório no caminho de import) | `./.venv/Scripts/python.exe -c "<código>"` |
| Rodar SQL no banco | `docker compose exec -T db psql -U bootcamp -d bootcamp -t -A -c "<SQL>"` |
| Procurar texto também em arquivo novo, ainda fora do Git | `git grep --untracked <opções> -- <arquivos>` |
| Ver os commits que mexeram em arquivos | `git log --oneline -- <arquivos>` |
| Ver as fixtures que um teste usa, sem rodar o teste | `./.venv/Scripts/python.exe -m pytest --setup-plan <teste>` |

O `-T` desliga o terminal interativo, que o Git Bash não oferece. O `-t -A` do `psql` tira cabeçalho, rodapé e alinhamento. O `git grep` termina com código 1 quando não acha nada: nos itens em que o esperado é "nenhuma linha", esse código 1 sem linha impressa é o resultado certo.

Todas as saídas esperadas abaixo valem sem `.env` na raiz do repositório (ARQ-04). Existe um `.env`: PARE.

Como os testes desta fase mandam requisições ao mesmo tempo: cada teste roda as requisições em threads (`concurrent.futures.ThreadPoolExecutor`, biblioteca padrão); as threads esperam juntas numa `threading.Barrier` e saem dela ao mesmo tempo, e quem decide a ordem é a trava do banco. Uma corrida pode não acontecer numa rodada: por isso os testes repetem a corrida em rodadas, e o 11.fim roda a pasta `tests/integration/extras/` 10 vezes seguidas (etapa 11 do `09 - Plano de trabalho`).

Valores que a fase usa:

| O quê | Valor |
|---|---|
| Tarifa (MOV-06, MOV-10), sem pontos em tarifa | 1% do valor, para cima: 1000 → 10 · 2000 → 20 · 3000 → 30 · 4000 → 40 · 10000 → 100 · 12345 → 124 |
| Sorteio (GAM-10) | nenhuma conta desta fase aplica pontos em chance: `draw_prize(0, rng)` nunca devolve, e o saldo de quem envia cai sempre valor + tarifa |
| Limite diário (CLI-08) | nenhuma conta desta fase envia mais de 6 transferências no dia: o bloqueio da 11ª nunca acontece |
| CDI de teste (11.4) | `"1.000000"` (1% ao dia), programado para `2026-06-01`, o dia do relógio depois do `DbUtils.rollback()` (DIA-04) |
| 5xx aceitos na suíte (11.5) | só 503 `QIT000503` (banco passou do timeout, PRD-08) e 503 `QIT001031` (Banco Central fora, COF-20) |

## Cobertura das regras desta fase (TST-02)

| Regra | O que fica vermelho se a regra deixar de valer |
|---|---|
| MOV-01 — sem saldo barra, os dois saldos ficam como estavam | `test_concurrent_transfers.py::test_two_transfers_when_the_balance_covers_one` (a segunda recebe 422 `QIT001015` e o destino dela fica com 0); `test_six_transfers_at_once_when_the_balance_covers_three`; `test_reconciliation.py::test_entries_add_up_to_the_balance_after_every_kind_of_operation` (as recusas não mudam saldo nem extrato) |
| MOV-02 — o saldo cobre valor + tarifa | `test_two_transfers_when_the_balance_covers_one`: o saldo é exatamente 10000 + 100; a primeira passa e zera a conta |
| MOV-05 — trava no saldo | `test_two_transfers_when_the_balance_covers_one` e `test_six_transfers_at_once_when_the_balance_covers_three`: sem a trava, uma sobreposição das leituras pode aprovar mais de uma (ou mais de três); a barreira HTTP não garante essa sobreposição, e os saldos das respostas 201 não saem distintos |
| MOV-11 — ordem das travas | `test_crossed_transfers.py::test_a_pays_b_and_b_pays_a_at_once` e `test_three_accounts_pay_in_a_circle_at_once`: a execução concorrente detecta deadlock se as esperas se cruzarem; a prova de ordem fixa exige também a conferência determinística do passo 11.6 |
| MOV-12 — idempotência (mesma chave e mesmo pedido → a primeira resposta; outro pedido → 409) | `test_idempotency_race.py` (os 7 testes): uma operação por chave; respostas iguais; 409 `QIT001014` na chave com outro corpo |
| MOV-19 — o `IntegrityError` da corrida vira repetição, nunca 500; o `balance_after` remonta a resposta | `test_idempotency_race.py` (a chamada que esperou a trava precisa responder 201 igual à primeira; o catch do UNIQUE é uma proteção adicional, não uma interleaving garantida pelo teste HTTP); `test_reconciliation.py::test_entries_add_up_to_the_balance_after_every_kind_of_operation` (o `balance_after` de cada linha é a soma acumulada) |
| DAD-07 — saldo em dois lugares | `test_reconciliation.py` (os 2 testes); conferência C2 (11.4) |
| DAD-16 — os lançamentos de cada operação somam zero | conferência C2 (11.4 e 11.fim) |
| COF-05 — saldo por categoria | `test_reconciliation.py` (a soma das categorias é o saldo do cofrinho) |
| R3 — nunca 500 por regra | a fixture `no_server_errors` (11.5), em todos os testes da suíte; a conferência V1 (11.5) prova o filtro |
| TST-08 — provas extras | os 4 arquivos de `tests/integration/extras/` e a fixture `no_server_errors` |
| TST-09 — infraestrutura e concorrência reproduzível | passo 11.6: 7 provas controladas, 3 PostgreSQL e 2 HTTP |
| PRD-15 — cliente compartilha barreira da conta | test_customer_auth_barrier.py e janela real em test_day_closing_postgres.py |
| GAM-26 — carência acaba antes do UP | test_rank_upgrade_ends_previous_grace_before_up |
| COF-26 — fração congelada do lote zerado | test_zeroed_lot_keeps_its_fraction_and_new_saving_creates_an_independent_lot |

Dos "Testes previstos" do `09 - Plano de trabalho`, caem nesta fase os seis de "Provas extras":

| Cenário do 09 | Teste |
|---|---|
| duas transferências ao mesmo tempo, e o saldo cobre só uma | `test_concurrent_transfers.py::test_two_transfers_when_the_balance_covers_one` |
| A paga B e B paga A ao mesmo tempo | `test_crossed_transfers.py::test_a_pays_b_and_b_pays_a_at_once` |
| mesma chave de idempotência duas vezes | `test_idempotency_race.py::test_same_transfer_twice_at_once_moves_money_once` e os outros 4 de mesmo pedido |
| mesma chave com corpo diferente (MOV-12: 409) | `test_idempotency_race.py::test_same_key_with_another_body_at_once_is_409` |
| soma do extrato = saldo, em cada conta | `test_reconciliation.py` (os 2 testes) |
| nenhuma resposta 5xx na suíte inteira | a fixture `no_server_errors` (11.5) |

---

### Passo 11.1 — Duas transferências ao mesmo tempo
**Branch:** fase/11-provas-extras · **Depende de:** fase 9 (merge `feat(categorias): fase 09 com categorias, IR e IOF no resgate e chance de não debitar` e tag `fase-09`) e o commit `docs(plano): roteiros auditados`, os dois na `main`
**Objetivo:** provar que, com o saldo para uma transferência só, de duas (ou seis) mandadas ao mesmo tempo passa exatamente o que o saldo cobre, e o saldo nunca fica negativo.
**Decisões:** TST-08 — provas extras · MOV-01 — sem saldo barra · MOV-02 — valor + tarifa · MOV-05 — trava no saldo · TST-01 — black box
**Arquivos:**
- `tests/integration/extras/test_concurrent_transfers.py` (criar; a pasta `tests/integration/extras/` é nova e fica sem `__init__.py`, como as outras pastas de integração): o conteúdo inteiro é:

```python
"""Duas transferências ao mesmo tempo quando o saldo cobre só uma: POST /accounts/{account_key}/transfers (TST-08, MOV-01, MOV-02, MOV-05).

As requisições saem juntas de threads que esperam numa barreira. A API
trava a conta de origem antes de ler o saldo (MOV-05): a segunda espera a
primeira gravar, lê o saldo novo e é barrada com 422 QIT001015 (MOV-01).
Sem a trava, as duas leriam o mesmo saldo e as duas passariam.

Nenhuma conta aplica pontos: a tarifa é 1% (MOV-06) e o sorteio da
chance de não debitar nunca devolve (GAM-10).
"""

from concurrent.futures import ThreadPoolExecutor
from functools import partial
from threading import Barrier

from tests.utils import ObjectGenerator, PayloadGenerator, RequestGenerator


# MOV-06, MOV-10: a tarifa de 10000 é 100.
AMOUNT = 10000
FEE = 100

ROUNDS = 5
BARRIER_TIMEOUT_SECONDS = 30


def run_at_the_same_time(calls: list) -> list:
    """Roda cada função de `calls` numa thread e devolve os resultados, na ordem de `calls`.

    As threads esperam juntas na barreira e saem dela ao mesmo tempo: as
    requisições chegam juntas à API, e quem decide a ordem são as travas
    do banco.
    """
    barrier = Barrier(len(calls), timeout=BARRIER_TIMEOUT_SECONDS)

    def wait_and_call(call):
        barrier.wait()

        return call()

    with ThreadPoolExecutor(max_workers=len(calls)) as executor:
        futures = [executor.submit(wait_and_call, call) for call in calls]

        return [future.result() for future in futures]


def balance_of(account: dict) -> int:
    status, response = RequestGenerator.GET_account(account["account_key"], account["account_token"])
    assert status == 200, response

    return response["balance"]


def entries_total(account: dict) -> int:
    """A soma do amount de todos os lançamentos do extrato da conta, página por página."""
    total = 0
    page = 0

    while True:
        status, response = RequestGenerator.GET_entries(account["account_key"], account["account_token"], {"limit": "100", "page": str(page)})
        assert status == 200, response

        total += sum(entry["amount"] for entry in response["data"])

        if response["is_last_page"]:
            return total

        page += 1


def transfer_call(origin: dict, destination: dict, amount: int):
    """A chamada de uma transferência com request_control_key nova, pronta para rodar numa thread."""
    payload = PayloadGenerator.transfer(destination["account_key"], amount=amount)

    return partial(RequestGenerator.POST_transfer, origin["account_key"], origin["account_token"], payload)


class TestConcurrentTransfers:
    def test_two_transfers_when_the_balance_covers_one(self):
        for _ in range(ROUNDS):
            origin = ObjectGenerator.create_funded_account(AMOUNT + FEE)
            first_destination = ObjectGenerator.create_account()
            second_destination = ObjectGenerator.create_account()

            results = run_at_the_same_time([transfer_call(origin, first_destination, AMOUNT), transfer_call(origin, second_destination, AMOUNT)])

            assert sorted(status for status, _ in results) == [201, 422], results

            for status, response in results:
                if status == 201:
                    assert response["balance"] == 0, response
                else:
                    assert response["code"] == "QIT001015", response

            assert balance_of(origin) == 0
            assert sorted([balance_of(first_destination), balance_of(second_destination)]) == [0, AMOUNT]
            assert entries_total(origin) == 0

    def test_six_transfers_at_once_when_the_balance_covers_three(self):
        origin = ObjectGenerator.create_funded_account(3 * (AMOUNT + FEE))
        destination = ObjectGenerator.create_account()

        results = run_at_the_same_time([transfer_call(origin, destination, AMOUNT) for _ in range(6)])

        assert sorted(status for status, _ in results) == [201, 201, 201, 422, 422, 422], results
        assert sorted(response["balance"] for status, response in results if status == 201) == [0, AMOUNT + FEE, 2 * (AMOUNT + FEE)]
        assert [response["code"] for status, response in results if status == 422] == ["QIT001015", "QIT001015", "QIT001015"]

        assert balance_of(origin) == 0
        assert balance_of(destination) == 3 * AMOUNT
        assert entries_total(origin) == 0
        assert entries_total(destination) == 3 * AMOUNT
```

**Passo a passo:**
1. Abra a fase (AGENTS.md, seção 7): `git status --short` → saída vazia; depois, um por vez:
   ```
   git switch main
   git switch -c fase/11-provas-extras
   ```
2. `git log --oneline` → mostra `docs(plano): roteiros auditados` e `feat(categorias): fase 09 com categorias, IR e IOF no resgate e chance de não debitar`. `git tag --list fase-09` → `fase-09`.
3. `docker compose up -d --build --wait`.
4. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `401 passed` (o ponto de partida da fase).
5. Crie `tests/integration/extras/test_concurrent_transfers.py` com o conteúdo do campo **Arquivos**.
6. `./.venv/Scripts/python.exe -m pytest -v tests/integration/extras/test_concurrent_transfers.py` → a última linha tem `2 passed`. É prova: se falhar, PARE.
7. Rode o mesmo comando do item 6 mais duas vezes, um de cada vez → `2 passed` nas duas.
8. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `403 passed`.
9. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
10. Rode o resto do **Verificar**.
11. Feche o passo (AGENTS.md, seção 7), um comando por vez:
    ```
    git add -- tests/integration/extras/test_concurrent_transfers.py
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "test(provas): duas transferências ao mesmo tempo com saldo para uma"
    git log -1 --format=%B
    ```

**Testes:** prova — `tests/integration/extras/test_concurrent_transfers.py`. Não há código novo: a trava é do passo 6.7 (MOV-05, MOV-11). Nenhum teste deste arquivo conta linhas do banco nem depende do relógio: nenhum começa com `DbUtils.rollback()`.

| Função de teste | Entrada | Esperado (status, corpo e efeito no banco) |
|---|---|---|
| `test_two_transfers_when_the_balance_covers_one` | 5 rodadas; em cada uma, contas novas: origem com 10100 (depósito), dois destinos com 0; duas transferências de 10000 da origem, uma para cada destino, ao mesmo tempo, cada uma com a sua `request_control_key` | em cada rodada: uma 201 com `balance` 0 e uma 422 `QIT001015`; a origem fica com 0; um destino com 10000 e o outro com 0; a soma do extrato da origem é 0. No banco: uma operação `TRANSFER` por rodada, com `AMOUNT` −10000 e `FEE` −100 na origem, `AMOUNT` +10000 num destino e `FEE` +100 na conta `BANK`; a recusada não grava nada (DAD-13) |
| `test_six_transfers_at_once_when_the_balance_covers_three` | origem com 30300 (depósito); um destino com 0; seis transferências de 10000 para o mesmo destino, ao mesmo tempo, cada uma com a sua chave | três 201 e três 422 `QIT001015`; os `balance` das três 201, em ordem, são 0, 10100 e 20200 (uma de cada vez, sob a trava); a origem fica com 0 e o destino com 30000; o extrato soma 0 na origem e 30000 no destino. No banco: três operações `TRANSFER`; as três recusadas não gravam nada |

**Verificar:**
- `./.venv/Scripts/python.exe -m pytest -v tests/integration/extras/test_concurrent_transfers.py` → `2 passed`, três vezes seguidas (itens 6 e 7).
- `git grep --untracked -n -e "from src" -e "import src" -e "sqlalchemy" -e "DbUtils" -- tests/integration/extras/test_concurrent_transfers.py` → nenhuma linha (TST-01: só HTTP).
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `403 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente `tests/integration/extras/test_concurrent_transfers.py`.
- `git log -1 --format=%B` → `test(provas): duas transferências ao mesmo tempo com saldo para uma`

**Pronto quando:**
- [ ] A fase abriu da `main` com `docs(plano): roteiros auditados` e a tag `fase-09`.
- [ ] `test_concurrent_transfers.py` igual ao do campo **Arquivos**; `2 passed` três vezes seguidas.
- [ ] Suíte com `403 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/11-provas-extras`.

**Commit:** `test(provas): duas transferências ao mesmo tempo com saldo para uma`
**Pare se:**
- O item 2 não mostrar as duas mensagens ou a tag `fase-09`: a fase 9 ou o plano da fase 11 não chegaram à `main`.
- A suíte do item 4 não terminar com `401 passed`.
- O arquivo falhar em qualquer uma das três rodadas (é prova: o conserto fica fora do passo). Traga a saída inteira do pytest e `docker compose logs --tail 100 api`.
- Aparecer 503 `QIT000503` numa resposta: a espera pela trava passou de `DB_LOCK_TIMEOUT_MS`.
- O teste ficar parado mais de 2 minutos sem terminar.

---

### Passo 11.2 — Mesma chave de idempotência ao mesmo tempo
**Branch:** fase/11-provas-extras · **Depende de:** 11.1
**Objetivo:** provar que o mesmo pedido mandado duas vezes ao mesmo tempo, com a mesma `request_control_key`, gera uma operação só e duas respostas iguais, nas cinco operações com chave; e que a mesma chave com outro corpo, ao mesmo tempo, dá uma 201 e um 409.
**Decisões:** TST-08 — provas extras · MOV-12 — idempotência · MOV-19 — idempotência na prática · TST-01 — black box
**Arquivos:**
- `tests/integration/extras/test_idempotency_race.py` (criar): o conteúdo inteiro é:

```python
"""A mesma request_control_key duas vezes ao mesmo tempo (TST-08, MOV-12, MOV-19).

As duas requisições saem juntas. As duas podem passar pela procura da
chave antes de qualquer uma gravar. Depois da trava, a segunda reconsulta
a chave antes de conferir estado ou saldo. O UNIQUE e o tratamento de
IntegrityError continuam protegendo colisões que cheguem à gravação; a
barreira HTTP não garante que esse caminho específico seja percorrido.

Mesmo pedido: uma operação só e as duas respostas iguais. A mesma chave
com outro corpo: uma passa e a outra recebe 409 QIT001014 (MOV-12). Vale
para as cinco operações com chave: depósito, saque, transferência,
guardar e resgatar.

Nenhuma conta aplica pontos: a tarifa é 1% (MOV-06) e o sorteio da
chance de não debitar nunca devolve (GAM-10).
"""

from concurrent.futures import ThreadPoolExecutor
from functools import partial
from threading import Barrier
from uuid import uuid4

from tests.utils import DbUtils, MockGenerator, ObjectGenerator, PayloadGenerator, RequestGenerator


ROUNDS = 5
BARRIER_TIMEOUT_SECONDS = 30


def run_at_the_same_time(calls: list) -> list:
    """Roda cada função de `calls` numa thread e devolve os resultados, na ordem de `calls`.

    As threads esperam juntas na barreira e saem dela ao mesmo tempo: as
    requisições chegam juntas à API, e quem decide a ordem são as travas
    do banco.
    """
    barrier = Barrier(len(calls), timeout=BARRIER_TIMEOUT_SECONDS)

    def wait_and_call(call):
        barrier.wait()

        return call()

    with ThreadPoolExecutor(max_workers=len(calls)) as executor:
        futures = [executor.submit(wait_and_call, call) for call in calls]

        return [future.result() for future in futures]


def balances_of(account: dict) -> tuple:
    """(saldo da conta, saldo do cofrinho)."""
    status, response = RequestGenerator.GET_account(account["account_key"], account["account_token"])
    assert status == 200, response

    return response["balance"], response["piggy_bank_balance"]


def all_entries(account: dict) -> list:
    """Todos os lançamentos do extrato da conta principal, página por página."""
    entries = []
    page = 0

    while True:
        status, response = RequestGenerator.GET_entries(account["account_key"], account["account_token"], {"limit": "100", "page": str(page)})
        assert status == 200, response

        entries.extend(response["data"])

        if response["is_last_page"]:
            return entries

        page += 1


def operation_count(account: dict, transaction_type: str) -> int:
    """Quantas operações do tipo têm lançamento no extrato da conta principal."""
    return len({entry["transaction_key"] for entry in all_entries(account) if entry["transaction_type"] == transaction_type})


def same_request_twice_at_once(call) -> tuple:
    """Manda o mesmo pedido duas vezes ao mesmo tempo; confere que as duas respostas são 201 e iguais, e devolve a resposta."""
    (first_status, first), (second_status, second) = run_at_the_same_time([call, call])

    assert (first_status, second_status) == (201, 201), (first, second)
    assert first == second

    return first


class TestIdempotencyRace:
    def test_same_transfer_twice_at_once_moves_money_once(self):
        for _ in range(ROUNDS):
            origin = ObjectGenerator.create_funded_account(10100)
            destination = ObjectGenerator.create_account()
            payload = PayloadGenerator.transfer(destination["account_key"], amount=10000)
            response = same_request_twice_at_once(partial(RequestGenerator.POST_transfer, origin["account_key"], origin["account_token"], payload))

            assert response["balance"] == 0
            assert balances_of(origin) == (0, 0)
            assert balances_of(destination) == (10000, 0)
            assert operation_count(origin, "TRANSFER") == 1
            assert operation_count(destination, "TRANSFER") == 1
            for account in [origin, destination]:
                status, gamification = RequestGenerator.GET_gamification(account["account_key"], account["account_token"])
                assert status == 200, gamification
                assert gamification["xp"] == 25

    def test_same_key_with_another_body_at_once_is_409(self):
        for operation, transaction_type in [("deposit", "DEPOSIT"), ("withdrawal", "WITHDRAWAL"),
                                             ("transfer", "TRANSFER"), ("saving", "SAVE"), ("redemption", "REDEEM")]:
            for _ in range(ROUNDS):
                account = ObjectGenerator.create_funded_account(9000)
                destination = ObjectGenerator.create_account()
                key, token = account["account_key"], account["account_token"]
                if operation == "redemption":
                    assert RequestGenerator.POST_saving(key, token, PayloadGenerator.saving(amount=9000))[0] == 201
                control_key = str(uuid4())
                payloads = []
                for amount in [1000, 2000]:
                    kwargs = {"amount": amount, "request_control_key": control_key}
                    if operation == "transfer":
                        kwargs["destination_account_key"] = destination["account_key"]
                    payloads.append(getattr(PayloadGenerator, operation)(**kwargs))
                method = getattr(RequestGenerator, "POST_" + operation)
                args = [key] if operation == "deposit" else [key, token]
                results = run_at_the_same_time([partial(method, *args, payload) for payload in payloads])
                assert sorted(status for status, _ in results) == [201, 409], results
                winner_index = next(i for i, (status, _) in enumerate(results) if status == 201)
                winner = results[winner_index][1]
                loser = results[1 - winner_index][1]
                amount = payloads[winner_index]["amount"]
                assert loser["code"] == "QIT001014", loser
                expected = {"deposit": (9000 + amount, 0), "withdrawal": (9000 - amount, 0),
                            "transfer": (9000 - amount - amount // 100, 0),
                            "saving": (9000 - amount, amount), "redemption": (amount, 9000 - amount)}[operation]
                assert balances_of(account) == expected
                assert winner["balance"] == expected[0]
                assert operation_count(account, transaction_type) == 1
                if operation == "transfer":
                    assert balances_of(destination) == (amount, 0)
                    assert operation_count(destination, "TRANSFER") == 1

    def test_same_deposit_twice_at_once_credits_once(self):
        account = ObjectGenerator.create_account()

        for round_number in range(1, ROUNDS + 1):
            payload = PayloadGenerator.deposit(amount=5000)
            same_request_twice_at_once(partial(RequestGenerator.POST_deposit, account["account_key"], payload))

            assert balances_of(account) == (round_number * 5000, 0)

        assert operation_count(account, "DEPOSIT") == ROUNDS

    def test_same_withdrawal_twice_at_once_debits_once(self):
        for _ in range(ROUNDS):
            account = ObjectGenerator.create_funded_account(7000)
            payload = PayloadGenerator.withdrawal(amount=7000)
            response = same_request_twice_at_once(partial(RequestGenerator.POST_withdrawal, account["account_key"], account["account_token"], payload))
            assert response["balance"] == 0
            assert balances_of(account) == (0, 0)
            assert operation_count(account, "WITHDRAWAL") == 1

    def test_same_saving_twice_at_once_saves_once(self):
        for _ in range(ROUNDS):
            account = ObjectGenerator.create_funded_account(6000)
            payload = PayloadGenerator.saving(amount=6000)
            response = same_request_twice_at_once(partial(RequestGenerator.POST_saving, account["account_key"], account["account_token"], payload))
            assert (response["balance"], response["piggy_bank_balance"]) == (0, 6000)
            assert balances_of(account) == (0, 6000)
            assert operation_count(account, "SAVE") == 1

    def test_same_redemption_twice_at_once_redeems_once(self):
        for _ in range(ROUNDS):
            account = ObjectGenerator.create_funded_account(4000)
            status, response = RequestGenerator.POST_saving(account["account_key"], account["account_token"], PayloadGenerator.saving(amount=4000))
            assert status == 201, response
            payload = PayloadGenerator.redemption(amount=4000)
            response = same_request_twice_at_once(partial(RequestGenerator.POST_redemption, account["account_key"], account["account_token"], payload))
            assert (response["balance"], response["piggy_bank_balance"]) == (4000, 0)
            assert balances_of(account) == (4000, 0)
            assert operation_count(account, "REDEEM") == 1

    def test_zero_net_taxed_redemption_repeats_original_balance(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate("2026-06-01", "1.000000")
        account = ObjectGenerator.create_funded_account(100000)
        key, token = account["account_key"], account["account_token"]
        assert RequestGenerator.POST_saving(key, token, PayloadGenerator.saving(amount=100000))[0] == 201
        assert RequestGenerator.POST_day_closing(PayloadGenerator.day_closing("2026-06-01"))[0] == 200
        payload = PayloadGenerator.redemption(amount=1)
        response = same_request_twice_at_once(partial(RequestGenerator.POST_redemption, key, token, payload))
        assert (response["iof"], response["ir"], response["net_amount"], response["balance"]) == (1, 0, 0, 0)
        assert balances_of(account) == (0, 100999)
        assert RequestGenerator.POST_deposit(key, PayloadGenerator.deposit(amount=7))[0] == 201
        assert RequestGenerator.POST_redemption(key, token, payload) == (201, response)
        assert balances_of(account) == (7, 100999)
        status, page = RequestGenerator.GET_piggy_bank_entries(key, token, {"limit": "100"})
        assert status == 200, page
        assert len([e for e in page["data"] if e["transaction_type"] == "REDEEM"]) == 1
        MockGenerator.clear_cdi("2026-06-01")

```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/11-provas-extras`; `git log --oneline -n 3` mostra `test(provas): duas transferências ao mesmo tempo com saldo para uma`.
2. `docker compose up -d --build --wait`.
3. Crie `tests/integration/extras/test_idempotency_race.py` com o conteúdo do campo **Arquivos**.
4. `./.venv/Scripts/python.exe -m pytest -v tests/integration/extras/test_idempotency_race.py` → a última linha tem `7 passed`. É prova: se falhar, PARE.
5. Rode o mesmo comando do item 4 mais duas vezes, um de cada vez → `7 passed` nas duas.
6. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `410 passed`.
7. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
8. Rode o resto do **Verificar**.
9. Feche o passo (AGENTS.md, seção 7), um comando por vez:
   ```
   git add -- tests/integration/extras/test_idempotency_race.py
   git diff --cached --name-only
   git diff --name-only
   git ls-files --others --exclude-standard
   git commit -m "test(provas): mesma chave de idempotência ao mesmo tempo"
   git log -1 --format=%B
   ```

**Testes:** prova — `tests/integration/extras/test_idempotency_race.py`. Não há código novo: a idempotência é dos passos 6.4, 6.6, 6.7 e 7.4 (MOV-12, MOV-19). Contrato de cada rota: `docs/rotas.md`. Somente o teste com imposto zera o banco e programa o CDI; os demais isolam dados por keys novas.

A ajudante `same_request_twice_at_once` manda o mesmo pedido (a mesma chave e o mesmo corpo) duas vezes ao mesmo tempo e confere: as duas respostas são 201 e os dois corpos são iguais. A ajudante `operation_count` conta, no extrato da conta principal, as `transaction_key` distintas de um `transaction_type`.

| Função de teste | Entrada | Esperado (status, corpo e efeito no banco) |
|---|---|---|
| `test_same_transfer_twice_at_once_moves_money_once` | 5 contas de origem com saldo exato 10100; 10000 para destino vazio | duas 201 iguais, saldo 0/10000, uma operação por lado e XP 25 por cliente |
| `test_same_key_with_another_body_at_once_is_409` | cinco operações, cinco rodadas cada, mesma chave com valores 1000/2000 | uma 201 e uma 409 QIT001014; somente o efeito vencedor nos saldos/extratos |
| `test_same_deposit_twice_at_once_credits_once` | conta com 0; 5 rodadas; em cada uma, o mesmo depósito de 5000 mandado duas vezes ao mesmo tempo | em cada rodada: duas 201 iguais (`{"transaction_key"}`), e o saldo sobe 5000 uma vez só; no fim, 25000 e 5 operações `DEPOSIT`. No banco: uma operação e uma linha em `deposits` por chave |
| `test_same_withdrawal_twice_at_once_debits_once` | cinco contas com saldo exato 7000 | duas 201 iguais, saldo zero, uma operação |
| `test_same_saving_twice_at_once_saves_once` | cinco contas com saldo exato 6000 | duas 201 iguais, principal zero, cofrinho 6000 e uma SAVE |
| `test_same_redemption_twice_at_once_redeems_once` | cinco cofrinhos com saldo exato 4000 | duas 201 iguais, principal 4000, cofrinho zero e uma REDEEM |

**Verificar:**
- `./.venv/Scripts/python.exe -m pytest -v tests/integration/extras/test_idempotency_race.py` → `7 passed`, três vezes seguidas (itens 4 e 5).
- `git grep --untracked -n -e "from src" -e "import src" -e "sqlalchemy" -- tests/integration/extras/test_idempotency_race.py` → nenhuma linha.
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `410 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente `tests/integration/extras/test_idempotency_race.py`.
- `git log -1 --format=%B` → `test(provas): mesma chave de idempotência ao mesmo tempo`

**Pronto quando:**
- [ ] `test_idempotency_race.py` igual ao do campo **Arquivos**; `7 passed` três vezes seguidas.
- [ ] Suíte com `410 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/11-provas-extras`.

**Commit:** `test(provas): mesma chave de idempotência ao mesmo tempo`
**Pare se:**
- O arquivo falhar em qualquer uma das três rodadas (é prova). Traga a saída inteira do pytest e `docker compose logs --tail 100 api`.
- Uma resposta da corrida vier com status 500 (o `IntegrityError` não virou repetição, MOV-19) ou com 503 `QIT000503`.
- O teste ficar parado mais de 2 minutos sem terminar.

---


Os quatro casos que debitam ou guardam usam saldo exato em cada rodada: a chamada que esperou a trava deve repetir a resposta mesmo depois de o saldo zerar. O sétimo caso prova imposto, líquido zero e resposta original após um depósito posterior.

### Passo 11.3 — A paga B e B paga A ao mesmo tempo
**Branch:** fase/11-provas-extras · **Depende de:** 11.2
**Objetivo:** provar que transferências cruzadas mandadas ao mesmo tempo (A → B com B → A, e A → B, B → C e C → A) passam todas, sem deadlock, sem 500 e com os saldos certos.
**Decisões:** TST-08 — provas extras · MOV-11 — ordem das travas · MOV-05 — trava no saldo · TST-01 — black box
**Arquivos:**
- `tests/integration/extras/test_crossed_transfers.py` (criar): o conteúdo inteiro é:

```python
"""A paga B e B paga A ao mesmo tempo: POST /accounts/{account_key}/transfers (TST-08, MOV-05, MOV-11).

Cada transferência trava as duas contas antes de ler o saldo (MOV-05). Se
cada uma travasse primeiro a própria origem, A esperaria B e B esperaria
A: deadlock, e o PostgreSQL derrubaria uma delas. A API trava sempre na
ordem do id, a menor primeiro (MOV-11): uma espera a outra terminar, e as
duas passam. O mesmo vale para três contas pagando em roda.

Nenhuma conta aplica pontos: a tarifa é 1% (MOV-06) e o sorteio da
chance de não debitar nunca devolve (GAM-10).
"""

from concurrent.futures import ThreadPoolExecutor
from functools import partial
from threading import Barrier

from tests.utils import ObjectGenerator, PayloadGenerator, RequestGenerator


ROUNDS = 5
BARRIER_TIMEOUT_SECONDS = 30


def run_at_the_same_time(calls: list) -> list:
    """Roda cada função de `calls` numa thread e devolve os resultados, na ordem de `calls`.

    As threads esperam juntas na barreira e saem dela ao mesmo tempo: as
    requisições chegam juntas à API, e quem decide a ordem são as travas
    do banco.
    """
    barrier = Barrier(len(calls), timeout=BARRIER_TIMEOUT_SECONDS)

    def wait_and_call(call):
        barrier.wait()

        return call()

    with ThreadPoolExecutor(max_workers=len(calls)) as executor:
        futures = [executor.submit(wait_and_call, call) for call in calls]

        return [future.result() for future in futures]


def balance_of(account: dict) -> int:
    status, response = RequestGenerator.GET_account(account["account_key"], account["account_token"])
    assert status == 200, response

    return response["balance"]


def entries_total(account: dict) -> int:
    """A soma do amount de todos os lançamentos do extrato da conta, página por página."""
    total = 0
    page = 0

    while True:
        status, response = RequestGenerator.GET_entries(account["account_key"], account["account_token"], {"limit": "100", "page": str(page)})
        assert status == 200, response

        total += sum(entry["amount"] for entry in response["data"])

        if response["is_last_page"]:
            return total

        page += 1


def transfer_call(origin: dict, destination: dict, amount: int):
    """A chamada de uma transferência com request_control_key nova, pronta para rodar numa thread."""
    payload = PayloadGenerator.transfer(destination["account_key"], amount=amount)

    return partial(RequestGenerator.POST_transfer, origin["account_key"], origin["account_token"], payload)


class TestCrossedTransfers:
    def test_a_pays_b_and_b_pays_a_at_once(self):
        account_a = ObjectGenerator.create_funded_account(100000)
        account_b = ObjectGenerator.create_funded_account(100000)

        for _ in range(ROUNDS):
            results = run_at_the_same_time([transfer_call(account_a, account_b, 10000), transfer_call(account_b, account_a, 3000)])

            assert [status for status, _ in results] == [201, 201], results

        # MOV-06, MOV-10: a tarifa de 10000 é 100; a de 3000, 30.
        assert balance_of(account_a) == 100000 - ROUNDS * 10100 + ROUNDS * 3000
        assert balance_of(account_b) == 100000 - ROUNDS * 3030 + ROUNDS * 10000
        assert entries_total(account_a) == balance_of(account_a)
        assert entries_total(account_b) == balance_of(account_b)

    def test_three_accounts_pay_in_a_circle_at_once(self):
        account_a = ObjectGenerator.create_funded_account(100000)
        account_b = ObjectGenerator.create_funded_account(100000)
        account_c = ObjectGenerator.create_funded_account(100000)

        for _ in range(ROUNDS):
            results = run_at_the_same_time([transfer_call(account_a, account_b, 1000), transfer_call(account_b, account_c, 2000), transfer_call(account_c, account_a, 4000)])

            assert [status for status, _ in results] == [201, 201, 201], results

        # MOV-06, MOV-10: a tarifa de 1000 é 10; a de 2000, 20; a de 4000, 40.
        assert balance_of(account_a) == 100000 - ROUNDS * 1010 + ROUNDS * 4000
        assert balance_of(account_b) == 100000 - ROUNDS * 2020 + ROUNDS * 1000
        assert balance_of(account_c) == 100000 - ROUNDS * 4040 + ROUNDS * 2000

        for account in [account_a, account_b, account_c]:
            assert entries_total(account) == balance_of(account)
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/11-provas-extras`; `git log --oneline -n 3` mostra `test(provas): mesma chave de idempotência ao mesmo tempo`.
2. `docker compose up -d --build --wait`.
3. Crie `tests/integration/extras/test_crossed_transfers.py` com o conteúdo do campo **Arquivos**.
4. `./.venv/Scripts/python.exe -m pytest -v tests/integration/extras/test_crossed_transfers.py` → a última linha tem `2 passed`. É prova: se falhar, PARE.
5. Rode o mesmo comando do item 4 mais duas vezes, um de cada vez → `2 passed` nas duas.
6. `docker compose logs --tail 100 db` → nenhuma linha com `deadlock detected`.
7. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `412 passed`.
8. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
9. Rode o resto do **Verificar**.
10. Feche o passo (AGENTS.md, seção 7), um comando por vez:
    ```
    git add -- tests/integration/extras/test_crossed_transfers.py
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "test(provas): transferências cruzadas ao mesmo tempo sem deadlock"
    git log -1 --format=%B
    ```

**Testes:** prova — `tests/integration/extras/test_crossed_transfers.py`. Não há código novo: a ordem das travas é do passo 6.7 (`AccountRepository.lock_accounts`, MOV-11). Nenhum teste deste arquivo começa com `DbUtils.rollback()`.

| Função de teste | Entrada | Esperado (status, corpo e efeito no banco) |
|---|---|---|
| `test_a_pays_b_and_b_pays_a_at_once` | A e B com 100000 cada; 5 rodadas; em cada uma, A → B de 10000 e B → A de 3000, ao mesmo tempo | as duas 201 em todas as rodadas; no fim, A com 64500 (100000 − 5 × 10100 + 5 × 3000) e B com 134850 (100000 − 5 × 3030 + 5 × 10000); o extrato de cada uma soma o saldo dela. No banco: 10 operações `TRANSFER`, cada uma com `AMOUNT` e `FEE` na origem, `AMOUNT` no destino e `FEE` na conta `BANK` |
| `test_three_accounts_pay_in_a_circle_at_once` | A, B e C com 100000 cada; 5 rodadas; em cada uma, A → B de 1000, B → C de 2000 e C → A de 4000, ao mesmo tempo | as três 201 em todas as rodadas; no fim, A com 114950 (100000 − 5 × 1010 + 5 × 4000), B com 94900 (100000 − 5 × 2020 + 5 × 1000) e C com 89800 (100000 − 5 × 4040 + 5 × 2000); o extrato de cada uma soma o saldo dela. No banco: 15 operações `TRANSFER` |

**Verificar:**
- `./.venv/Scripts/python.exe -m pytest -v tests/integration/extras/test_crossed_transfers.py` → `2 passed`, três vezes seguidas (itens 4 e 5).
- `docker compose logs --tail 100 db` → nenhuma linha com `deadlock detected` (item 6).
- `git grep --untracked -n -e "from src" -e "import src" -e "sqlalchemy" -e "DbUtils" -- tests/integration/extras/test_crossed_transfers.py` → nenhuma linha.
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `412 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente `tests/integration/extras/test_crossed_transfers.py`.
- `git log -1 --format=%B` → `test(provas): transferências cruzadas ao mesmo tempo sem deadlock`

**Pronto quando:**
- [ ] `test_crossed_transfers.py` igual ao do campo **Arquivos**; `2 passed` três vezes seguidas.
- [ ] O log do banco não tem `deadlock detected`.
- [ ] Suíte com `412 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/11-provas-extras`.

**Commit:** `test(provas): transferências cruzadas ao mesmo tempo sem deadlock`
**Pare se:**
- O arquivo falhar em qualquer uma das três rodadas (é prova). Traga a saída inteira do pytest, `docker compose logs --tail 100 api` e `docker compose logs --tail 100 db`.
- O log do banco do item 6 tiver `deadlock detected`, mesmo com os testes verdes.
- Aparecer 503 `QIT000503` numa resposta.
- O teste ficar parado mais de 2 minutos sem terminar.

---

### Passo 11.4 — Reconciliação
**Branch:** fase/11-provas-extras · **Depende de:** 11.3
**Objetivo:** provar que, em cada conta criada no teste, a soma dos lançamentos do extrato é o saldo da conta, e a do extrato do cofrinho é o saldo do cofrinho, depois de todos os tipos de operação (em sequência, com virada do dia) e depois de operações ao mesmo tempo.
**Decisões:** TST-08 — provas extras · DAD-07 — saldo em dois lugares · MOV-19 — `balance_after` em cada lançamento · DAD-16 — lançamentos somam zero (conferência C2) · COF-05 — saldo por categoria · DIA-01 — relógio do banco · TST-01 — black box
**Arquivos:**
- `tests/integration/extras/test_reconciliation.py` (criar): o conteúdo inteiro é:

```python
"""Reconciliação: em cada conta criada no teste, a soma do extrato é o saldo (TST-08, DAD-07, MOV-19, COF-05).

O saldo mora em dois lugares (DAD-07): na coluna balance da conta, que sai
em GET /accounts/{account_key}, e nos lançamentos, que saem no extrato. O
teste soma o amount de todos os lançamentos, página por página, e compara
com o saldo: o da conta principal com GET .../entries e o do cofrinho com
GET .../piggy_bank_entries. O saldo do cofrinho também é a soma dos saldos
das categorias (COF-05).

Com as operações uma depois da outra, o teste confere também cada linha:
do lançamento mais antigo para o mais novo, o balance_after é a soma
acumulada (MOV-19). Com as operações ao mesmo tempo, confere só o total.

O primeiro teste fecha o dia (rendimento e, no resgate, IOF e IR): começa
com DbUtils.rollback() (o relógio volta a 2026-06-01, DIA-01) e programa
o CDI de 1% no Mockserver.

Nenhuma conta aplica pontos: a tarifa é 1% (MOV-06) e o sorteio da
chance de não debitar nunca devolve (GAM-10).
"""

from concurrent.futures import ThreadPoolExecutor
from functools import partial
from threading import Barrier

from tests.utils import DbUtils, MockGenerator, ObjectGenerator, PayloadGenerator, RandomGenerator, RequestGenerator


FIRST_DAY = "2026-06-01"
ONE_PERCENT = "1.000000"

# MOV-08: não há valor máximo; este valor passa no schema e nenhuma conta do teste tem saldo para ele.
TOO_MUCH = 1000000000

ROUNDS = 3
BARRIER_TIMEOUT_SECONDS = 30


def run_at_the_same_time(calls: list) -> list:
    """Roda cada função de `calls` numa thread e devolve os resultados, na ordem de `calls`.

    As threads esperam juntas na barreira e saem dela ao mesmo tempo: as
    requisições chegam juntas à API, e quem decide a ordem são as travas
    do banco.
    """
    barrier = Barrier(len(calls), timeout=BARRIER_TIMEOUT_SECONDS)

    def wait_and_call(call):
        barrier.wait()

        return call()

    with ThreadPoolExecutor(max_workers=len(calls)) as executor:
        futures = [executor.submit(wait_and_call, call) for call in calls]

        return [future.result() for future in futures]


def expect(result: tuple, status: int) -> dict:
    """Confere o status de uma resposta (status, corpo) e devolve o corpo."""
    assert result[0] == status, result

    return result[1]


def balances_of(account: dict) -> tuple:
    """(saldo da conta, saldo do cofrinho)."""
    response = expect(RequestGenerator.GET_account(account["account_key"], account["account_token"]), 200)

    return response["balance"], response["piggy_bank_balance"]


def all_entries(route, account: dict) -> list:
    """Todos os lançamentos de um extrato, do mais recente para o mais antigo, página por página.

    `route` é RequestGenerator.GET_entries (conta principal) ou
    RequestGenerator.GET_piggy_bank_entries (cofrinho).
    """
    entries = []
    page = 0

    while True:
        response = expect(route(account["account_key"], account["account_token"], {"limit": "100", "page": str(page)}), 200)

        entries.extend(response["data"])

        if response["is_last_page"]:
            return entries

        page += 1


def categories_total(account: dict) -> int:
    """A soma dos saldos das categorias ativas do cofrinho."""
    response = expect(RequestGenerator.GET_categories(account["account_key"], account["account_token"], {"limit": "100"}), 200)
    assert response["is_last_page"] is True, response

    return sum(category["balance"] for category in response["data"])


def assert_running_balance(entries: list, balance: int) -> None:
    """Do lançamento mais antigo para o mais novo, o balance_after de cada um é a soma dos amount até ele; a soma final é o saldo (MOV-19)."""
    running = 0

    for entry in reversed(entries):
        running += entry["amount"]
        assert entry["balance_after"] == running, entry

    assert running == balance


def reconcile(account: dict, check_each_line: bool) -> None:
    """A soma do extrato é o saldo, na conta principal e no cofrinho; o cofrinho é a soma das categorias (DAD-07, COF-05)."""
    balance, piggy_bank_balance = balances_of(account)
    entries = all_entries(RequestGenerator.GET_entries, account)
    piggy_bank_entries = all_entries(RequestGenerator.GET_piggy_bank_entries, account)

    assert sum(entry["amount"] for entry in entries) == balance
    assert sum(entry["amount"] for entry in piggy_bank_entries) == piggy_bank_balance
    assert categories_total(account) == piggy_bank_balance

    if check_each_line:
        assert_running_balance(entries, balance)
        assert_running_balance(piggy_bank_entries, piggy_bank_balance)


class TestReconciliation:
    def test_entries_add_up_to_the_balance_after_every_kind_of_operation(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate(FIRST_DAY, ONE_PERCENT)

        account_a = ObjectGenerator.create_funded_account(300000)
        account_b = ObjectGenerator.create_funded_account(50000)
        key_a, token_a = account_a["account_key"], account_a["account_token"]
        key_b, token_b = account_b["account_key"], account_b["account_token"]

        expect(RequestGenerator.POST_deposit(key_a, PayloadGenerator.deposit(amount=20000, depositor_document=RandomGenerator.generate_cnpj())), 201)
        expect(RequestGenerator.POST_transfer(key_a, token_a, PayloadGenerator.transfer(key_b, amount=12345)), 201)
        expect(RequestGenerator.POST_transfer(key_b, token_b, PayloadGenerator.transfer(key_a, amount=2000)), 201)

        withdrawal = PayloadGenerator.withdrawal(amount=5000)
        first_withdrawal = expect(RequestGenerator.POST_withdrawal(key_a, token_a, withdrawal), 201)
        assert expect(RequestGenerator.POST_withdrawal(key_a, token_a, withdrawal), 201) == first_withdrawal

        expect(RequestGenerator.POST_saving(key_a, token_a, PayloadGenerator.saving(amount=100000)), 201)
        category_key = expect(RequestGenerator.POST_category(key_a, token_a, PayloadGenerator.category()), 201)["category_key"]
        expect(RequestGenerator.POST_saving(key_a, token_a, PayloadGenerator.saving(amount=30000, category_key=category_key)), 201)

        # MOV-06, MOV-10: a tarifa de 12345 é 124 (123,45 para cima); a de 2000, 20.
        assert balances_of(account_a) == (174531, 130000)
        assert balances_of(account_b) == (60325, 0)

        assert expect(RequestGenerator.POST_transfer(key_a, token_a, PayloadGenerator.transfer(key_b, amount=TOO_MUCH)), 422)["code"] == "QIT001015"
        assert expect(RequestGenerator.POST_withdrawal(key_b, token_b, PayloadGenerator.withdrawal(amount=TOO_MUCH)), 422)["code"] == "QIT001015"
        assert expect(RequestGenerator.POST_redemption(key_a, token_a, PayloadGenerator.redemption(amount=TOO_MUCH, category_key=category_key)), 422)["code"] == "QIT001023"
        assert balances_of(account_a) == (174531, 130000)
        assert balances_of(account_b) == (60325, 0)

        assert expect(RequestGenerator.POST_day_closing(PayloadGenerator.day_closing(FIRST_DAY)), 200)["closed_date"] == FIRST_DAY

        balance, piggy_bank_balance = balances_of(account_a)
        assert balance == 174531
        assert piggy_bank_balance > 130000
        assert "YIELD" in [entry["transaction_type"] for entry in all_entries(RequestGenerator.GET_piggy_bank_entries, account_a)]

        for redemption in [PayloadGenerator.redemption(amount=50000), PayloadGenerator.redemption(amount=10000, category_key=category_key)]:
            response = expect(RequestGenerator.POST_redemption(key_a, token_a, redemption), 201)

            assert response["gross_amount"] == redemption["amount"]
            assert response["net_amount"] == response["gross_amount"] - response["iof"] - response["ir"]
            assert response["balance"] == balance + response["net_amount"]
            assert response["piggy_bank_balance"] == piggy_bank_balance - response["gross_amount"]

            balance, piggy_bank_balance = response["balance"], response["piggy_bank_balance"]

        assert balances_of(account_a) == (balance, piggy_bank_balance)

        reconcile(account_a, check_each_line=True)
        reconcile(account_b, check_each_line=True)
        MockGenerator.clear_cdi(FIRST_DAY)

    def test_entries_add_up_to_the_balance_after_concurrent_operations(self):
        account_a = ObjectGenerator.create_funded_account(100000)
        account_b = ObjectGenerator.create_funded_account(100000)
        account_c = ObjectGenerator.create_funded_account(100000)
        key_a, token_a = account_a["account_key"], account_a["account_token"]
        key_b, token_b = account_b["account_key"], account_b["account_token"]
        key_c, token_c = account_c["account_key"], account_c["account_token"]

        for _ in range(ROUNDS):
            calls = []
            calls.append(partial(RequestGenerator.POST_transfer, key_a, token_a, PayloadGenerator.transfer(key_b, amount=1000)))
            calls.append(partial(RequestGenerator.POST_transfer, key_b, token_b, PayloadGenerator.transfer(key_c, amount=2000)))
            calls.append(partial(RequestGenerator.POST_transfer, key_c, token_c, PayloadGenerator.transfer(key_a, amount=3000)))
            calls.append(partial(RequestGenerator.POST_deposit, key_a, PayloadGenerator.deposit(amount=500)))
            calls.append(partial(RequestGenerator.POST_withdrawal, key_b, token_b, PayloadGenerator.withdrawal(amount=700)))
            calls.append(partial(RequestGenerator.POST_saving, key_c, token_c, PayloadGenerator.saving(amount=400)))

            results = run_at_the_same_time(calls)

            assert [status for status, _ in results] == [201, 201, 201, 201, 201, 201], results

        # MOV-06, MOV-10: a tarifa de 1000 é 10; a de 2000, 20; a de 3000, 30.
        assert balances_of(account_a) == (100000 - ROUNDS * 1010 + ROUNDS * 3000 + ROUNDS * 500, 0)
        assert balances_of(account_b) == (100000 - ROUNDS * 2020 + ROUNDS * 1000 - ROUNDS * 700, 0)
        assert balances_of(account_c) == (100000 - ROUNDS * 3030 + ROUNDS * 2000 - ROUNDS * 400, ROUNDS * 400)

        for account in [account_a, account_b, account_c]:
            reconcile(account, check_each_line=False)
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/11-provas-extras`; `git log --oneline -n 3` mostra `test(provas): transferências cruzadas ao mesmo tempo sem deadlock`.
2. `docker compose up -d --build --wait`.
3. `docker compose ps` → três serviços: `api` (healthy), `db` (healthy) e `mockserver` (running). O primeiro teste fecha o dia e precisa do Mockserver.
4. Crie `tests/integration/extras/test_reconciliation.py` com o conteúdo do campo **Arquivos**.
5. `./.venv/Scripts/python.exe -m pytest -v tests/integration/extras/test_reconciliation.py` → a última linha tem `2 passed`. É prova: se falhar, PARE.
6. Rode o mesmo comando do item 5 mais duas vezes, um de cada vez → `2 passed` nas duas.
7. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `414 passed`.
8. Rode a conferência C2 do **Verificar** → `0:0`.
9. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
10. Rode o resto do **Verificar**.
11. Feche o passo (AGENTS.md, seção 7), um comando por vez:
    ```
    git add -- tests/integration/extras/test_reconciliation.py
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "test(provas): reconciliação do extrato com o saldo"
    git log -1 --format=%B
    ```

**Testes:** prova — `tests/integration/extras/test_reconciliation.py`. Não há código novo: o saldo em dois lugares é do passo 6.1 (DAD-07) e o `balance_after`, do 6.1 e do 6.4 (MOV-19). O primeiro teste depende do relógio do banco e começa com `DbUtils.rollback()` (DIA-01: o relógio volta a `2026-06-01`); o segundo não depende do relógio nem conta linhas, e não começa com ele.

A ajudante `reconcile` confere numa conta: a soma do `amount` de todas as linhas de `GET .../entries` é o `balance` de `GET /accounts/{account_key}`; a soma de todas as linhas de `GET .../piggy_bank_entries` é o `piggy_bank_balance`; a soma do `balance` das categorias de `GET .../categories` é o `piggy_bank_balance`. Com `check_each_line=True`, confere também, nos dois extratos, do lançamento mais antigo para o mais novo, que o `balance_after` de cada linha é a soma acumulada dos `amount` (o extrato sai do mais recente para o mais antigo, MOV-14).

| Função de teste | Entrada | Esperado (status, corpo e efeito no banco) |
|---|---|---|
| `test_entries_add_up_to_the_balance_after_every_kind_of_operation` | `DbUtils.rollback()`; CDI de 1% em `2026-06-01`. A com 300000 e B com 50000 (depósitos); depósito de 20000 em A, de quem tem CNPJ; A → B de 12345; B → A de 2000; saque de 5000 em A, mandado duas vezes com a mesma chave; A guarda 100000 em "economias"; A cria uma categoria e guarda 30000 nela. Depois, três recusas: A → B de 1000000000; saque de 1000000000 em B; resgate de 1000000000 da categoria de A. Depois, a virada de `2026-06-01`; e dois resgates em A: 50000 de "economias" e 10000 da categoria | todas as operações aceitas respondem 201; o saque repetido devolve o corpo da primeira vez; antes da virada, A com (174531, 130000) e B com (60325, 0); as recusas respondem 422 `QIT001015`, 422 `QIT001015` e 422 `QIT001023`, e os saldos não mudam; a virada responde 200 com `closed_date` `2026-06-01`; depois dela, o cofrinho de A passa de 130000 e o extrato dele tem uma linha `YIELD`; em cada resgate, `gross_amount` é o valor pedido, `net_amount` = `gross_amount` − `iof` − `ir`, e `balance` e `piggy_bank_balance` andam o líquido e o bruto. No fim, `reconcile` com `check_each_line=True` passa em A e em B. No banco: as recusas e a repetição não gravam operação |
| `test_entries_add_up_to_the_balance_after_concurrent_operations` | A, B e C com 100000 cada (depósitos); 3 rodadas; em cada uma, seis pedidos ao mesmo tempo: A → B de 1000, B → C de 2000, C → A de 3000, depósito de 500 em A, saque de 700 em B e C guarda 400 | os seis respondem 201 em todas as rodadas; no fim, A com (107470, 0), B com (94840, 0) e C com (95710, 1200); `reconcile` com `check_each_line=False` passa nas três |

**Verificar:**
- `./.venv/Scripts/python.exe -m pytest -v tests/integration/extras/test_reconciliation.py` → `2 passed`, três vezes seguidas (itens 5 e 6).
- C2 — no banco que a suíte deixou, toda conta de cliente tem o saldo igual à soma dos lançamentos dela (DAD-07), e toda operação soma zero (DAD-16). A mesma conferência do 9.fim; um comando, numa linha só:
  ```
  docker compose exec -T db psql -U bootcamp -d bootcamp -t -A -c "SELECT (SELECT count(*) FROM account a WHERE a.account_type_id = 1 AND a.balance <> (SELECT coalesce(sum(e.amount), 0) FROM entry e WHERE e.account_id = a.id)) || ':' || (SELECT count(*) FROM (SELECT e.transaction_id FROM entry e GROUP BY e.transaction_id HAVING sum(e.amount) <> 0) z)"
  ```
  → exatamente `0:0` (`account_type` 1 = `CUSTOMER`).
- `git grep --untracked -n -e "from src" -e "import src" -e "sqlalchemy" -- tests/integration/extras/test_reconciliation.py` → nenhuma linha.
- `git grep --untracked -n -e "^from tests.utils import" -e "^[ ]*DbUtils.rollback()" -- tests/integration/extras/test_reconciliation.py` → exatamente 2 linhas: o import e a chamada de limpeza.
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `414 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente `tests/integration/extras/test_reconciliation.py`.
- `git log -1 --format=%B` → `test(provas): reconciliação do extrato com o saldo`

**Pronto quando:**
- [ ] `test_reconciliation.py` igual ao do campo **Arquivos**; `2 passed` três vezes seguidas.
- [ ] C2 dá `0:0`.
- [ ] Suíte com `414 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/11-provas-extras`.

**Commit:** `test(provas): reconciliação do extrato com o saldo`
**Pare se:**
- O item 3 não mostrar o `mockserver` rodando.
- O arquivo falhar em qualquer uma das três rodadas (é prova). Traga a saída inteira do pytest e `docker compose logs --tail 100 api`. Se a falha for no `assert entry["balance_after"] == running`, traga também a linha do extrato que o pytest mostra.
- C2 der outra saída.
- O teste ficar parado mais de 2 minutos sem terminar.

---

### Passo 11.5 — Nenhum erro 500 na suíte
**Branch:** fase/11-provas-extras · **Depende de:** 11.4
**Objetivo:** uma fixture automática em `tests/conftest.py` reprova todo teste que receber da API um 5xx que não seja 503 `QIT000503` ou 503 `QIT001031`; o `ClientRequisition` guarda método, caminho, status e `code` de cada resposta do teste em andamento.
**Decisões:** TST-08 — provas extras · R3 — nunca 500 por regra · PRD-08 — timeout no banco (503 `QIT000503`) · COF-20 — Banco Central fora (503 `QIT001031`) · TST-01 — black box
**Arquivos:**
- `tests/utils/requisition.py` (editar): o conteúdo inteiro passa a ser (o do base com a troca do passo 2.1, mais a lista de respostas e os três métodos novos; `send` ganha só a linha do `record`):

```python
import json
from requests import request, Response
from requests.exceptions import ConnectionError as RequestsConnectionError
from os import environ


API_OFFLINE = (
    "Não consegui falar com a API em {base_url}.\n"
    "Ela precisa estar de pé pros testes rodarem. Suba com:  docker compose up"
)

# R3, TST-08: os únicos 5xx que um teste pode receber da API, os dois de
# dependência fora do ar ou lenta: o banco passou do timeout (PRD-08) e o
# Banco Central não respondeu (COF-20).
ACCEPTED_SERVER_ERROR_CODES = ("QIT000503", "QIT001031")


class ClientRequisition:
    # Cada resposta da API recebida no teste em andamento, como (método,
    # caminho, status, code). É da classe, e não do objeto: as threads dos
    # testes de concorrência gravam na mesma lista. Quem a esvazia antes de
    # cada teste e a confere depois é a fixture no_server_errors, em
    # tests/conftest.py.
    received_responses = []

    @staticmethod
    def send(
        method,
        endpoint,
        payload=None,
        headers=None,
        data=None,
        cert=None,
        query_params=None,
        verify=True,
    ):

        if headers is None:
            headers = dict()

        api_host = environ.get("SERVER_LOCALHOST", "127.0.0.1")
        api_port = environ.get("API_PORT", "3000")
        base_url = f"http://{api_host}:{api_port}"

        url = f"{base_url}{endpoint}"

        try:
            response = request(
                method.upper(),
                url,
                headers=headers,
                json=payload,
                data=data,
                cert=cert,
                verify=verify,
                params=query_params,
                timeout=30,
            )
        except RequestsConnectionError:
            raise RuntimeError(API_OFFLINE.format(base_url=base_url)) from None

        base_response = BaseConnectorResponse(
            endpoint=endpoint,
            method=method,
            payload=payload,
            headers=headers,
            response=response,
        )

        ClientRequisition.record(method, endpoint, base_response.response_status, base_response.response_json)

        return base_response

    @staticmethod
    def start_test() -> None:
        """Esvazia a lista de respostas: a fixture no_server_errors chama antes de cada teste."""
        ClientRequisition.received_responses.clear()

    @staticmethod
    def record(method: str, endpoint: str, status: int, response_json) -> None:
        """Guarda uma resposta da API: método, caminho, status e o campo code do corpo (None quando o corpo não é um objeto JSON com code)."""
        code = None

        if isinstance(response_json, dict):
            code = response_json.get("code")

        ClientRequisition.received_responses.append((method.upper(), endpoint, status, code))

    @staticmethod
    def server_errors() -> list:
        """As respostas 5xx do teste em andamento, menos o 503 com um código de ACCEPTED_SERVER_ERROR_CODES (R3)."""
        errors = []

        for method, endpoint, status, code in list(ClientRequisition.received_responses):
            if status < 500:
                continue

            if status == 503 and code in ACCEPTED_SERVER_ERROR_CODES:
                continue

            errors.append((method, endpoint, status, code))

        return errors


class BaseConnectorResponse:
    def __init__(
        self,
        response: Response,
        endpoint: str,
        method: str,
        headers: dict,
        payload: dict,
    ) -> None:
        self.endpoint = endpoint
        self.method = method
        self.payload = payload
        self.headers = headers
        self.response = response
        self.response_content = response.content
        self.response_status = response.status_code

        self.response_json = None
        try:
            self.response_json = json.loads(self.response_content)
        except Exception as ex:
            print(ex)
            ...
            # logger warning
```

- `tests/conftest.py` (editar): o conteúdo inteiro passa a ser (o do passo 2.1, mais o `import pytest` e a fixture):

```python
from pathlib import Path
from os import path, environ

import pytest

root = Path(__file__).resolve().parents[1]

if not environ.get("APP_ENV") or environ.get("APP_ENV") == "local":
    from dotenv import load_dotenv

    load_dotenv(path.join(str(root), ".env"))

    if environ.get("SERVER_LOCALHOST") is None:
        environ["SERVER_LOCALHOST"] = "127.0.0.1"


@pytest.fixture(autouse=True)
def no_server_errors():
    """R3, TST-08: reprova o teste que recebeu da API um 5xx fora dos dois 503 de dependência.

    Antes de cada teste, esvazia a lista de respostas do ClientRequisition;
    depois dele, confere a lista. Os únicos 5xx aceitos são o 503 QIT000503
    (o banco passou do timeout, PRD-08) e o 503 QIT001031 (o Banco Central
    não respondeu, COF-20). Qualquer outro 5xx vira erro na desmontagem do
    teste, com as respostas na mensagem.

    O import fica aqui dentro, e não no topo: o tests.utils lê o
    INTERNAL_TOKEN do ambiente quando é importado, e o .env tem de ser lido
    antes disso.
    """
    from tests.utils.requisition import ClientRequisition

    ClientRequisition.start_test()

    yield

    server_errors = ClientRequisition.server_errors()
    assert server_errors == [], f"Resposta 5xx da API neste teste (R3): {server_errors}"
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/11-provas-extras`; `git log --oneline -n 3` mostra `test(provas): reconciliação do extrato com o saldo`.
2. `git log --oneline -- tests/conftest.py tests/utils/requisition.py` → exatamente 2 linhas: a primeira termina em `chore(ambiente): venv com flake8, pytest.ini e testes em 127.0.0.1`; a segunda, em `chore: base do bootcamp, AGENTS.md e plano`. Os dois arquivos são os do base com a troca do 2.1, e o conteúdo inteiro do campo **Arquivos** parte deles.
3. Rode a conferência V1 do **Verificar** → a saída termina com `AttributeError` e tem `has no attribute 'start_test'`. É o vermelho antes do código.
4. Rode a conferência V3 do **Verificar** → a saída não tem `no_server_errors`.
5. Edite `tests/utils/requisition.py` com o conteúdo do campo **Arquivos**.
6. Edite `tests/conftest.py` com o conteúdo do campo **Arquivos**.
7. Rode a V1 → a saída esperada.
8. `docker compose up -d --build --wait`.
9. Rode a V2 e a V3 → as saídas esperadas.
10. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `414 passed` e não tem `error`. É a prova: nenhum teste da suíte recebeu 5xx fora dos dois 503 aceitos.
11. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
12. Rode o resto do **Verificar**.
13. Feche o passo (AGENTS.md, seção 7), um comando por vez:
    ```
    git add -- tests/utils/requisition.py tests/conftest.py
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "test(provas): nenhuma resposta 5xx na suíte"
    git log -1 --format=%B
    ```

**Testes:** prova — nenhum arquivo de teste novo; a contagem continua `414 passed`. A fixture `no_server_errors` vale para todos os testes da suíte (`autouse=True`, escopo de função). O vermelho antes do código é a V1 (item 3). Teste que recebe um 5xx fora dos aceitos aparece como `ERROR at teardown of <teste>`, e a última linha do pytest passa a ter `error`.

| O que roda | Entrada | Esperado |
|---|---|---|
| a fixture `no_server_errors`, em cada teste da suíte | as respostas que o teste recebeu da API | nenhuma resposta com status 500 ou mais, fora do 503 `QIT000503` e do 503 `QIT001031`: o teste termina sem erro na desmontagem. Os testes da virada do dia com o Banco Central fora (503 `QIT001031`, passo 7.11) continuam verdes |
| a suíte inteira | os 414 testes | `414 passed`, sem `error` |

**Verificar:**
- V1 — o filtro dos 5xx (R3), sem falar com a API. Um comando, numa linha só:
  ```
  ./.venv/Scripts/python.exe -c "from tests.utils.requisition import ClientRequisition as C; C.start_test(); C.record('GET', '/a', 200, {}); C.record('POST', '/b', 503, {'code': 'QIT001031'}); C.record('POST', '/c', 503, {'code': 'QIT000503'}); C.record('GET', '/d', 500, {'code': 'QIT000500'}); C.record('POST', '/e', 503, {'code': 'QIT000002'}); C.record('get', '/f', 502, None); print(len(C.received_responses)); print(C.server_errors()); C.start_test(); print(C.received_responses, C.server_errors())"
  ```
  → antes do código (item 3): termina com `AttributeError: type object 'ClientRequisition' has no attribute 'start_test'`. Depois (item 7), exatamente:
  ```
  6
  [('GET', '/d', 500, 'QIT000500'), ('POST', '/e', 503, 'QIT000002'), ('GET', '/f', 502, None)]
  [] []
  ```
  Linha 1: as seis respostas guardadas. Linha 2: o 500, o 503 com outro código e o 502 são reprovados; os 503 `QIT001031` e `QIT000503`, não. Linha 3: o `start_test` esvazia a lista.
- V2 — o `send` guarda cada resposta da API (precisa da API de pé). Um comando, numa linha só:
  ```
  ./.venv/Scripts/python.exe -c "from tests.utils.requisition import ClientRequisition as C; C.start_test(); C.send('GET', '/health_check'); C.send('PUT', '/health_check'); print(C.received_responses)"
  ```
  → exatamente estas 2 linhas (a primeira é o `print(ex)` do `BaseConnectorResponse`, que já existia, para o 204 sem corpo):
  ```
  Expecting value: line 1 column 1 (char 0)
  [('GET', '/health_check', 204, None), ('PUT', '/health_check', 405, 'QIT000405')]
  ```
- V3 — a fixture está ligada aos testes. Um comando:
  ```
  ./.venv/Scripts/python.exe -m pytest --setup-plan tests/integration/test_healthcheck.py::TestHealthCheck::test_home
  ```
  → antes do código (item 4): nenhuma linha com `no_server_errors`. Depois (item 9): uma linha que contém `SETUP` e `no_server_errors`, e uma linha que termina em `(fixtures used: no_server_errors)`.
- `git grep -n "no_server_errors" -- tests` → exatamente 3 linhas: uma em `tests/conftest.py` (a do `def no_server_errors():`) e duas em `tests/utils/requisition.py` (a do comentário acima de `received_responses` e a da docstring do `start_test`).
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `414 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  tests/conftest.py
  tests/utils/requisition.py
  ```
- `git log -1 --format=%B` → `test(provas): nenhuma resposta 5xx na suíte`

**Pronto quando:**
- [ ] A V1 terminou com `AttributeError` antes do código e dá as 3 linhas esperadas depois.
- [ ] A V2 dá as 2 linhas esperadas; a V3 mostra `no_server_errors` só depois do código.
- [ ] `tests/utils/requisition.py` e `tests/conftest.py` iguais aos do campo **Arquivos**.
- [ ] Suíte com `414 passed`, sem `error`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/11-provas-extras`.

**Commit:** `test(provas): nenhuma resposta 5xx na suíte`
**Pare se:**
- O item 2 mostrar outra quantidade de linhas ou outras mensagens: algum passo mexeu nestes arquivos, e o conteúdo inteiro do plano apagaria a mudança.
- A V1 do item 3 não terminar com `AttributeError`, ou a V3 do item 4 já mostrar `no_server_errors`.
- A V1, a V2 ou a V3 derem outra saída depois de 3 tentativas de conferir os arquivos contra o plano.
- A suíte do item 10 terminar com `error`: um teste recebeu 5xx. Não mexa no teste nem na fixture; traga a saída inteira do pytest (a mensagem lista método, caminho, status e `code`) e `docker compose logs --tail 100 api`.
- A suíte não terminar com `414 passed`.

---

### Passo 11.6 — Provas reproduziveis de infraestrutura e PostgreSQL
**Branch:** fase/11-provas-extras · **Depende de:** 11.5, 9.9 a 9.11, correções PRD-15 no 5.9 e GAM-26 no 7.4
**Objetivo:** provar a reconsulta após espera, ordem de travas, eventos, timeouts, sorteio, janela da barreira e encerramento durante a virada.
**Decisões:** TST-09 — infraestrutura controlada e PostgreSQL real; PRD-15 — barreira cliente/conta; GAM-26 — eventos de carência; MOV-19 — idempotência; PRD-08 e COF-20 — timeouts; CLI-05 — encerrada congela; COF-26 — resíduo do lote zerado congelado
**Arquivos:**
- `tests/unit/infrastructure/test_infrastructure_rules.py` (criar): conteúdo inteiro:

```python
import json
from datetime import date
from os import environ
from types import SimpleNamespace
from unittest.mock import Mock, call

import pytest
from psycopg2.errors import LockNotAvailable, QueryCanceled
from requests.exceptions import Timeout
from sqlalchemy.exc import OperationalError

environ.setdefault("DATABASE_URL", "postgresql+psycopg2://bootcamp:bootcamp@localhost:5432/bootcamp")

from connectors import BcbConnector
from controllers.gamification_controller import GamificationController
from controllers.piggy_bank_controller import PiggyBankController
from controllers.transaction_controller import TransactionController
from errors import CdiUnavailable
from errors.handlers import register_error_handlers
from models import Account, AccountStatus
from repositories import AccountRepository
from tests.utils.requisition import ClientRequisition


def test_idempotency_is_rechecked_after_waiting_before_state_and_balance():
    account = SimpleNamespace(id=1, account_key="a", status=SimpleNamespace(enumerator=AccountStatus.BLOCKED), balance=0)
    piggy = SimpleNamespace(id=2, balance=0)
    first = SimpleNamespace(transaction_key="first")
    for method, response_method in [("save", "_saving_response"), ("redeem", "_redemption_response")]:
        controller = PiggyBankController.__new__(PiggyBankController)
        controller.get_owned_account = Mock(return_value=account)
        controller._find_repeated = Mock(side_effect=[None, first])
        controller.bank_clock_repository = Mock()
        controller._lock_account_and_piggy_bank = Mock(return_value=(account, piggy))
        setattr(controller, response_method, Mock(return_value={"transaction_key": "first", "balance": 7}))
        result = getattr(controller, method)("a", "token", {"request_control_key": "key", "amount": 1})
        assert result == {"transaction_key": "first", "balance": 7}
        assert controller._find_repeated.call_count == 2
    controller = TransactionController.__new__(TransactionController)
    controller.get_owned_account = Mock(return_value=account)
    controller._find_repeated = Mock(side_effect=[None, first])
    controller.bank_clock_repository = Mock()
    controller.account_repository = Mock()
    controller.account_repository.get_customer_account.return_value = None
    controller.account_repository.lock_accounts.return_value = [account]
    controller._balance_after = Mock(return_value=7)
    controller.rng = Mock()
    assert controller.transfer("a", "token", {"request_control_key": "key", "amount": 1, "destination_account_key": "b"}) == {"transaction_key": "first", "balance": 7}
    assert controller._find_repeated.call_count == 2
    assert controller.rng.mock_calls == []


def test_lock_accounts_orders_by_internal_id_before_for_update():
    repository = AccountRepository.__new__(AccountRepository)
    repository.session = Mock()
    query = Mock()
    repository.session.query.return_value = query
    for name in ["filter", "order_by", "with_for_update", "populate_existing"]:
        getattr(query, name).return_value = query
    query.all.return_value = ["locked"]
    assert repository.lock_accounts([SimpleNamespace(id=9), SimpleNamespace(id=2)]) == ["locked"]
    query.order_by.assert_called_once_with(Account.id)
    query.with_for_update.assert_called_once_with()
    assert query.method_calls.index(call.order_by(Account.id)) < query.method_calls.index(call.with_for_update())
    assert query.filter.call_args.args[0].right.value == [2, 9]


def test_rank_upgrade_ends_previous_grace_before_up():
    controller = GamificationController.__new__(GamificationController)
    controller.gamification_repository = Mock()
    account = SimpleNamespace(rank=SimpleNamespace(enumerator="BRONZE"), grace_until=date(2026, 7, 1))
    day = date(2026, 6, 2)
    assert controller.raise_rank(account, SimpleNamespace(balance=500000), day) is True
    assert controller.gamification_repository.create_rank_event.call_args_list == [
        call(account, "BRONZE", "GRACE_END", day), call(account, "SILVER", "UP", day)]
    controller.gamification_repository.reset_mock()
    account.grace_until = None
    assert controller.raise_rank(account, SimpleNamespace(balance=500000), day) is True
    controller.gamification_repository.create_rank_event.assert_called_once_with(account, "SILVER", "UP", day)
    controller.gamification_repository.reset_mock()
    assert controller.raise_rank(account, SimpleNamespace(balance=100000), day) is False
    assert controller.gamification_repository.mock_calls == []


def test_every_unexpected_5xx_is_reported_and_clear_resets():
    ClientRequisition.start_test()
    try:
        for status, code in [(200, None), (503, "QIT001031"), (503, "QIT000503"),
                             (500, "QIT000500"), (503, "other"), (502, None), (504, None)]:
            ClientRequisition.record("get", "/probe", status, {"code": code})
        assert [(status, code) for _, _, status, code in ClientRequisition.server_errors()] == [
            (500, "QIT000500"), (503, "other"), (502, None), (504, None)]
    finally:
        ClientRequisition.start_test()
    assert ClientRequisition.server_errors() == []


def test_database_timeouts_map_to_the_specific_503_without_waiting():
    class Application:
        def __init__(self):
            self.handlers = {}

        def exception_handler(self, error_class):
            def save(handler):
                self.handlers[error_class] = handler
                return handler
            return save

    application = Application()
    register_error_handlers(application)
    request = SimpleNamespace(method="POST", url=SimpleNamespace(path="/probe"))
    for original in [LockNotAvailable(), QueryCanceled()]:
        response = application.handlers[OperationalError](request, OperationalError("probe", {}, original))
        assert response.status_code == 503
        assert json.loads(response.body)["code"] == "QIT000503"


def test_cdi_timeout_is_a_project_503_without_network_or_waiting():
    connector = BcbConnector()
    connector.send = Mock(side_effect=Timeout())
    with pytest.raises(CdiUnavailable) as result:
        connector.get_cdi_rate(date(2026, 6, 1))
    assert (result.value.http_status, result.value.code) == (503, "QIT001031")


def test_transfer_prize_uses_injected_generator_and_normal_xp_only():
    origin = SimpleNamespace(id=1, account_key="a", balance=10100,
                             status=SimpleNamespace(enumerator="ACTIVE"), points_fee=0, points_chance=10)
    destination = SimpleNamespace(id=2, account_key="b", balance=0, status=SimpleNamespace(enumerator="ACTIVE"))
    bank = SimpleNamespace(id=3, balance=None)
    controller = TransactionController.__new__(TransactionController)
    controller.get_owned_account = Mock(return_value=origin)
    controller._find_repeated = Mock(return_value=None)
    controller.bank_clock_repository = Mock()
    controller.bank_clock_repository.get_accounting_date.return_value = date(2026, 6, 1)
    controller.account_repository = Mock()
    controller.account_repository.get_customer_account.return_value = destination
    controller.account_repository.lock_accounts.return_value = [origin, destination]
    controller.account_repository.get_system_account.return_value = bank
    controller.transaction_repository = Mock()
    controller.transaction_repository.count_transfers_sent.return_value = 0
    controller.transaction_repository.create.return_value = SimpleNamespace(transaction_key="first")
    controller.entry_repository = Mock()
    created = []

    def create(transaction, account, kind, amount):
        created.append((account.id, kind, amount))
        if account.balance is not None:
            account.balance += amount

    controller.entry_repository.create.side_effect = create
    controller.gamification_controller = Mock()
    controller.rng = Mock()
    controller.rng.randrange.return_value = 0
    controller.session = Mock()
    controller.logger = Mock()
    result = controller.transfer("a", "token", {"request_control_key": "key", "amount": 10000, "destination_account_key": "b"})
    assert result == {"transaction_key": "first", "balance": 10100}
    assert destination.balance == 10000
    assert created == [(1, "AMOUNT", -10000), (1, "FEE", -100), (2, "AMOUNT", 10000),
                       (3, "FEE", 100), (3, "PRIZE", -10100), (1, "PRIZE", 10100)]
    controller.rng.randrange.assert_called_once_with(1000)
    assert [c.args[1:3] for c in controller.gamification_controller.award_transfer_xp.call_args_list] == [
        (10000, "TRANSFER_SENT"), (10000, "TRANSFER_RECEIVED")]
    controller.session.commit.assert_called_once_with()
```

- `tests/unit/infrastructure/test_day_closing_postgres.py` (criar): conteúdo inteiro:

```python
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from os import environ
from threading import Event
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

from sqlalchemy import create_engine, func, literal, text
from sqlalchemy.orm import sessionmaker

from tests.utils import DbUtils, ObjectGenerator, PayloadGenerator, RequestGenerator

environ.setdefault("DATABASE_URL", DbUtils.database_url())


def test_account_closed_between_listing_and_lock_is_not_processed(monkeypatch):
    DbUtils.rollback()
    import database
    from controllers import AccountController, DayClosingController

    engine = create_engine(DbUtils.database_url())
    monkeypatch.setattr(database, "SessionLocal", sessionmaker(bind=engine, autoflush=False))
    account = ObjectGenerator.create_funded_account(200000)
    key, token = account["account_key"], account["account_token"]
    assert RequestGenerator.POST_saving(key, token, PayloadGenerator.saving(amount=200000))[0] == 201
    assert RequestGenerator.POST_redemption(key, token, PayloadGenerator.redemption(amount=200000))[0] == 201
    assert RequestGenerator.POST_withdrawal(key, token, PayloadGenerator.withdrawal(amount=200000))[0] == 201

    def snapshot():
        with engine.connect() as connection:
            values = connection.execute(text("SELECT xp, rank_id, yield_rank_id, piggy_record, grace_until FROM account WHERE account_key=:key"), {"key": key}).one()
            events = connection.execute(text("SELECT count(*) FROM rank_event e JOIN account a ON a.id=e.account_id WHERE a.account_key=:key"), {"key": key}).scalar()
            return tuple(values), events

    before = snapshot()
    listed, resume = Event(), Event()

    def run_closing():
        context = database.open_context()
        try:
            controller = DayClosingController()
            original = controller.account_repository.list_open_customer_accounts

            def pause_after_listing():
                rows = original()
                listed.set()
                assert resume.wait(30), "encerramento nao liberou a virada"
                return rows

            controller.account_repository.list_open_customer_accounts = pause_after_listing
            controller.bcb_connector.get_cdi_rate = Mock(return_value=None)
            controller.gamification_controller.award_record_xp = Mock(wraps=controller.gamification_controller.award_record_xp)
            result = controller.close_day({"accounting_date": "2026-06-01"})
            assert controller.gamification_controller.award_record_xp.call_count == 0
            return result
        finally:
            if context.db_session is not None:
                context.db_session.close()
            database.clear_context()

    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(run_closing)
            try:
                assert listed.wait(30), "virada nao chegou a listagem"
                context = database.open_context()
                try:
                    AccountController().close_account(key, token)
                finally:
                    if context.db_session is not None:
                        context.db_session.close()
                    database.clear_context()
            finally:
                resume.set()
            assert future.result(timeout=30) == {"closed_date": "2026-06-01", "accounting_date": "2026-06-02"}
        assert RequestGenerator.GET_account(key, token)[1]["status"] == "CLOSED"
        assert snapshot() == before
    finally:
        engine.dispose()


def test_auth_failure_window_boundary_and_expiration_without_sleep(monkeypatch):
    DbUtils.rollback()
    from models import RequestLog
    from repositories import RequestLogRepository
    from repositories import request_log_repository as module

    engine = create_engine(DbUtils.database_url())
    factory = sessionmaker(bind=engine)
    monkeypatch.setattr(module, "SessionLocal", factory)
    now = [datetime(2026, 10, 8, 12)]
    monkeypatch.setattr(module, "func", SimpleNamespace(count=func.count, now=lambda: literal(now[0])))
    account_key = str(uuid4())
    with factory() as session:
        for age in [timedelta(minutes=15, microseconds=1), timedelta(minutes=15), timedelta(0)]:
            session.add(RequestLog(request_log_key=str(uuid4()), request_id=str(uuid4()),
                                   created_at=now[0] - age, method="GET", path="/probe", status=404,
                                   error_code="QIT001010", client_ip="127.0.0.1", account_key=account_key,
                                   auth_failure="ACCOUNT"))
        session.commit()
    repository = RequestLogRepository()
    try:
        assert repository.count_auth_failures("127.0.0.1", ["ACCOUNT"], 15, account_key) == 2
        assert repository.count_auth_failures("127.0.0.1", ["ACCOUNT"], 15, str(uuid4())) == 0
        now[0] += timedelta(minutes=15)
        assert repository.count_auth_failures("127.0.0.1", ["ACCOUNT"], 15, account_key) == 1
        now[0] += timedelta(microseconds=1)
        assert repository.count_auth_failures("127.0.0.1", ["ACCOUNT"], 15, account_key) == 0
    finally:
        engine.dispose()

def test_zeroed_lot_keeps_its_fraction_and_new_saving_creates_an_independent_lot():
    from decimal import Decimal
    from tests.utils import DbUtils, MockGenerator, ObjectGenerator, PayloadGenerator, RequestGenerator
    from database import DATABASE_URL
    from sqlalchemy import create_engine, text

    DbUtils.rollback()
    engine = create_engine(DATABASE_URL)
    account = ObjectGenerator.create_funded_account(1000)
    key, token = account["account_key"], account["account_token"]

    def lots():
        with engine.connect() as connection:
            return connection.execute(text("SELECT l.id, l.principal_remaining, l.yield_remaining, l.residue FROM lot l JOIN category c ON c.id = l.category_id JOIN account p ON p.id = c.account_id JOIN account a ON a.id = p.parent_account_id WHERE a.account_key = :key ORDER BY l.id"), {"key": key}).all()

    try:
        assert RequestGenerator.POST_saving(key, token, PayloadGenerator.saving(amount=1000))[0] == 201
        MockGenerator.set_cdi_rate("2026-06-01", "0.054266")
        assert RequestGenerator.POST_day_closing(PayloadGenerator.day_closing("2026-06-01"))[0] == 200
        old_id = lots()[0].id
        assert lots()[0][1:] == (1000, 0, Decimal("0.54266000"))
        assert RequestGenerator.POST_redemption(key, token, PayloadGenerator.redemption(amount=1000))[0] == 201
        assert lots()[0][1:] == (0, 0, Decimal("0.54266000"))
        assert RequestGenerator.POST_saving(key, token, PayloadGenerator.saving(amount=1000))[0] == 201
        assert len(lots()) == 2 and lots()[1].id != old_id
        assert lots()[1][1:] == (1000, 0, Decimal("0.00000000"))
        for day, expected_yield, expected_residue in [("2026-06-02", 0, "0.54266000"),
                                                       ("2026-06-03", 1, "0.08532000")]:
            MockGenerator.set_cdi_rate(day, "0.054266")
            assert RequestGenerator.POST_day_closing(PayloadGenerator.day_closing(day))[0] == 200
            assert lots()[0][1:] == (0, 0, Decimal("0.54266000"))
            assert lots()[1][1:] == (1000, expected_yield, Decimal(expected_residue))
            status, summary = RequestGenerator.GET_account(key, token)
            assert status == 200, summary
            assert (summary["piggy_bank_balance"], summary["piggy_bank_gross_yield"]) == (1000 + expected_yield, expected_yield)
    finally:
        for day in ["2026-06-01", "2026-06-02", "2026-06-03"]:
            MockGenerator.clear_cdi(day)
        engine.dispose()

```

- `tests/integration/internal/test_customer_auth_barrier.py` (criar): conteúdo inteiro:

```python
from uuid import uuid4

from tests.utils import DbUtils, ObjectGenerator, RequestGenerator


class TestCustomerAuthBarrier:
    def test_customer_and_account_share_the_account_ip_counter(self):
        DbUtils.rollback()
        account = ObjectGenerator.create_account()
        other = ObjectGenerator.create_account()
        for _ in range(5):
            status, response = RequestGenerator.GET_customer(account["customer_key"], "wrong")
            assert (status, response["code"]) == (404, "QIT001008")
        for _ in range(5):
            status, response = RequestGenerator.GET_account(account["account_key"], "wrong")
            assert (status, response["code"]) == (404, "QIT001010")
        for send, key in [(RequestGenerator.GET_customer, account["customer_key"]),
                          (RequestGenerator.GET_account, account["account_key"])]:
            status, response = send(key, account["account_token"])
            assert (status, response["code"]) == (429, "QIT000429")
        assert RequestGenerator.GET_account(other["account_key"], other["account_token"])[0] == 200

    def test_unknown_customer_has_a_normalized_fallback_counter(self):
        DbUtils.rollback()
        key = str(uuid4())
        for _ in range(5):
            for spelling in [key, key.upper()]:
                status, response = RequestGenerator.GET_customer(spelling, "wrong")
                assert (status, response["code"]) == (404, "QIT001008")
        status, response = RequestGenerator.GET_customer(key, "wrong")
        assert (status, response["code"]) == (429, "QIT000429")
```

**Passo a passo:**
1. Conferir branch limpa e commits 11.1 a 11.5 conforme AGENTS. Este passo e de prova: nao altera src.
2. Criar os tres arquivos exatamente como acima. Os imports diretos de src ficam apenas em tests/unit/infrastructure, conforme TST-09; o arquivo HTTP usa somente os geradores.
3. `docker compose up -d --build --wait`.
4. `./.venv/Scripts/python.exe -m pytest -v tests/unit/infrastructure/test_infrastructure_rules.py`: 7 passed; nenhum banco/rede/espera real neste arquivo.
5. `./.venv/Scripts/python.exe -m pytest -v tests/unit/infrastructure/test_day_closing_postgres.py`: 3 passed. Este arquivo usa PostgreSQL REAL do compose, limpa antes de cada prova e nao tem skip/fallback. A primeira prova para depois da listagem, encerra a conta numa segunda sessao e somente entao libera a virada. A segunda controla now() e testa a query real no PostgreSQL, inclusive o limite inclusivo e a expiracao, sem sleep. A terceira confere o residuo congelado e um novo lote independente em tres viradas.
6. `./.venv/Scripts/python.exe -m pytest -v tests/integration/internal/test_customer_auth_barrier.py`: 2 passed.
7. Rodar os comandos dos itens 4 a 6 mais duas vezes, um por vez: mesmas contagens.
8. `./.venv/Scripts/python.exe -m pytest`: suite inteira verde, sem failed/error/skipped.
9. `./.venv/Scripts/python.exe -m flake8 src tests`: nenhuma linha.
10. Encerrar conforme AGENTS, um comando por vez:
```
git add -- tests/unit/infrastructure/test_infrastructure_rules.py tests/unit/infrastructure/test_day_closing_postgres.py tests/integration/internal/test_customer_auth_barrier.py
git diff --cached --name-only
git diff --name-only
git ls-files --others --exclude-standard
git commit -m "test(provas): infraestrutura controlada e encerramento concorrente no PostgreSQL"
git log -1 --format=%B
```
**Testes:** prova. Os 7 isolados detectam retirada de reconsulta/trava/evento/filtro/traducao do timeout/premio; os 3 PostgreSQL forcam a interleaving, a janela e a independencia do residuo; os 2 HTTP provam compartilhamento e fallback. Os 503 previstos continuam tendo suas provas de ausencia de escrita por HTTP no 7.11; estes testes nao as substituem.
**Verificar:** contagens 7/3/2 nos arquivos e suite inteira verde; `git diff --cached --name-only` lista exatamente:
```
tests/integration/internal/test_customer_auth_barrier.py
tests/unit/infrastructure/test_day_closing_postgres.py
tests/unit/infrastructure/test_infrastructure_rules.py
```
Diffs restantes vazios; commit com mensagem exata.
**Pronto quando:**
- [ ] Provas isoladas, HTTP e PostgreSQL passaram tres vezes; nenhum skip.
- [ ] Suite inteira verde e lint vazio; somente os tres arquivos alterados.
- [ ] Commit local da branch.
**Commit:** `test(provas): infraestrutura controlada e encerramento concorrente no PostgreSQL`
**Pare se:** falhar qualquer prova ou faltar dependencia, banco ou arquivo; nao adaptar resultado nem pular PostgreSQL; registrar saida e logs conforme AGENTS.

---

### Passo 11.fim — Fechar a fase
**Branch:** fase/11-provas-extras · **Depende de:** 11.1 a 11.6
**Objetivo:** provar a fase com o banco recriado do zero, rodar as provas extras 10 vezes seguidas e levar a fase para a `main` com a tag `fase-11`.
**Decisões:** TIM-04 — git por fase · TIM-08 — git automático · ARQ-03 — SQL só com o banco vazio · ARQ-04 — sobe sem `.env` · ARQ-06 — três peças no compose · TST-08 — provas extras · DAD-07 — saldo em dois lugares · DAD-16 — lançamentos somam zero
**Arquivos:** nenhum. O passo não cria, não edita e não apaga arquivo.
**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/11-provas-extras`.
2. `git log --oneline -n 7` → tem as 6 mensagens abaixo, cada uma uma vez:
   ```
   test(provas): duas transferências ao mesmo tempo com saldo para uma
   test(provas): mesma chave de idempotência ao mesmo tempo
   test(provas): transferências cruzadas ao mesmo tempo sem deadlock
   test(provas): reconciliação do extrato com o saldo
   test(provas): nenhuma resposta 5xx na suíte
   test(provas): infraestrutura controlada e encerramento concorrente no PostgreSQL
   ```
3. Recrie o banco do zero e suba tudo, um comando por vez:
   ```
   docker compose down -v
   docker compose up -d --build --wait
   ```
4. `docker compose ps` → três serviços: `api` (healthy), `db` (healthy) e `mockserver` (running).
5. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `426 passed`.
6. `./.venv/Scripts/python.exe -m pytest` de novo → a última linha tem `426 passed` (nada intermitente).
7. As provas extras 10 vezes seguidas (etapa 11 do `09 - Plano de trabalho`): rode o comando abaixo 10 vezes, um de cada vez, e confira cada saída antes de rodar a próxima:
   ```
   ./.venv/Scripts/python.exe -m pytest tests/integration/extras
   ```
   → a última linha tem `13 passed` nas 10 rodadas.
8. Rode a conferência C2 (passo 11.4) → `0:0`.
9. `docker compose logs --tail 100 db` → nenhuma linha com `deadlock detected`.
10. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
11. `git status --short` → saída vazia.
12. Leve a fase para a `main`, um comando por vez:
    ```
    git switch main
    git merge --no-ff --no-edit -m "test(provas): fase 11 com concorrência, idempotência, reconciliação e nenhum 5xx" fase/11-provas-extras
    git tag fase-11
    ```
13. Rode o resto do **Verificar**.

**Testes:** nenhum teste novo. A suíte inteira (271 de integração + 155 em tests/unit (3 com PostgreSQL real)) roda duas vezes com o banco recriado do zero (itens 5 e 6), e os 13 testes de `tests/integration/extras/` rodam mais 10 vezes (item 7), com a fixture `no_server_errors` ligada em todas as rodadas.
**Verificar:**
- As saídas dos itens 4 a 10, como descritas no **Passo a passo**.
- O `git status --short` antes do merge não mostra alterações.
- `git branch --show-current` → `main`.
- `git log -1 --format=%B` → `test(provas): fase 11 com concorrência, idempotência, reconciliação e nenhum 5xx`.
- `git log -1 --format=%P` → dois hashes separados por um espaço (é um merge).
- `git tag --list fase-11` → `fase-11`.
- `git ls-files tests/integration/extras` → exatamente:
  ```
  tests/integration/extras/test_concurrent_transfers.py
  tests/integration/extras/test_crossed_transfers.py
  tests/integration/extras/test_idempotency_race.py
  tests/integration/extras/test_reconciliation.py
  ```
- `git status --short` → saída vazia.

**Pronto quando:**
- [ ] Os três serviços sobem do zero, sem `.env`.
- [ ] Suíte com `426 passed`, duas vezes seguidas; `tests/integration/extras` com `13 passed`, 10 vezes seguidas; C2 dá `0:0`; o log do banco sem `deadlock detected`; lint sem saída.
- [ ] Merge `--no-ff` na `main` com a mensagem exata; tag `fase-11` criada localmente; merge local na `main`.

**Commit:** nenhum commit de passo. Mensagem do merge: `test(provas): fase 11 com concorrência, idempotência, reconciliação e nenhum 5xx`
**Pare se:**
- Faltar uma das 6 mensagens do item 2.
- `docker compose up -d --build --wait` falhar: rode `docker compose logs --tail 100 db`, `docker compose logs --tail 100 api` e `docker compose logs --tail 100 mockserver` e traga as três saídas.
- A suíte não terminar com `426 passed` nas duas rodadas, ou terminar com `error`.
- Uma das 10 rodadas do item 7 não terminar com `13 passed`: uma falha em dez é o sinal de alerta do risco "concorrência mal resolvida" do `09 - Plano de trabalho`. Pare na rodada que falhou e traga a saída dela e `docker compose logs --tail 100 api`.
- C2 der outra saída, ou o log do banco tiver `deadlock detected`.
- O lint imprimir qualquer linha.
- O merge local der conflito (AGENTS.md, seção 8, item 9).

---

## Divergências encontradas

Seção para o Bruno; o agente não executa nada daqui.

| # | Onde | O que foi feito |
|---|---|---|
| 1 | TST-08 diz "nenhum 5xx na suíte"; COF-20 manda responder 503 `QIT001031`, e a suíte provoca esse 503 de propósito (7.11). O PLANO-00 (11.5) diz "reprova 500, ou 503 com código diferente de `QIT001031` e `QIT000503`". | A fixture reprova qualquer status de 500 para cima, fora dos dois 503 aceitos: 502 e 504 também reprovam, mais perto do TST-08 que a frase do índice. Texto do 11.5 no PLANO-00 sincronizado: qualquer status >= 500 reprova, salvo os dois 503 expressamente aceitos. |
| 2 | TST-01 (o teste falha antes do código) e TST-02. | Os passos 11.1 a 11.4 são de prova (PLANO-00): não há código novo, e o teste passa de primeira. As corridas são probabilísticas: cada teste repete a corrida em rodadas, cada passo roda o arquivo 3 vezes e o 11.fim roda a pasta 10 vezes. O vermelho antes do código só existe no 11.5 (V1). |
| 3 | PLANO-00, 11.2: "uma operação só; as duas respostas iguais". | Coberta a corrida nas cinco operações com chave da MOV-12 (depósito, saque, transferência, guardar e resgatar) e, do 09, "mesma chave com corpo diferente" (MOV-12: 409 `QIT001014`), também ao mesmo tempo. |
| 4 | PLANO-00, 11.4: "a soma do extrato é o saldo". | Somados o extrato do cofrinho (contra `piggy_bank_balance`), a soma das categorias (COF-05) e o `balance_after` linha a linha (MOV-19, só nas operações em sequência: nas simultâneas a ordem do extrato é a do `created_at`). A C2 (SQL do 9.fim) entra no Verificar. |
| 5 | A fixture falha na desmontagem do teste. | O teste com 5xx aparece como `ERROR at teardown`, não como `failed`; a suíte deixa de ficar verde do mesmo jeito (AGENTS.md, seção 9). |
| 6 | O índice não tem arquivo de apoio para os testes de concorrência. | `run_at_the_same_time` e as leituras de saldo e extrato são ajudantes locais, repetidas em cada arquivo de `extras/`; nenhum arquivo novo em `tests/utils/`. |
| 7 | Corte opcional da fase 11. | Removido: os passos 11.1 a 11.6 são necessários para fechar TST-08/TST-09 e PRD-15. O fechamento exige 426 testes e todas as seis mensagens. |

## Nomes novos da fase 11 (sincronizados no PLANO-00)

Seção para o Bruno; o agente não executa nada daqui.

| Onde | Nomes |
|---|---|
| `tests/conftest.py` | fixture `no_server_errors` (`autouse=True`) |
| `tests/utils/requisition.py` | constante `ACCEPTED_SERVER_ERROR_CODES = ("QIT000503", "QIT001031")`; atributo de classe `ClientRequisition.received_responses`; métodos `ClientRequisition.start_test()`, `record(method, endpoint, status, response_json)`, `server_errors()` |
| Testes | pasta `tests/integration/extras/`; classes `TestConcurrentTransfers`, `TestIdempotencyRace`, `TestCrossedTransfers`, `TestReconciliation`; ajudantes locais `run_at_the_same_time`, `transfer_call`, `entries_total`, `all_entries`, `operation_count`, `same_request_twice_at_once`, `expect`, `categories_total`, `assert_running_balance`, `reconcile`; constantes `AMOUNT`, `FEE`, `ROUNDS`, `BARRIER_TIMEOUT_SECONDS`, `FIRST_DAY`, `ONE_PERCENT`, `TOO_MUCH` |
