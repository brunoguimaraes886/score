> **Git local — Bruno, 08/10/2026:** durante a produção, branches, commits, merges e tags ficam locais. Não executar push, pull ou fetch nem exigir acesso ao GitHub. O envio completo será feito pelo Bruno somente no final, quando tudo estiver pronto. As verificações de commits e dependências são locais.

# PLANO — Fase 07 — cofrinho, virada do dia, ranque e carência

**Branch:** `fase/07-cofrinho` · **Depende de:** fase 8
**Objetivo:** guardar e resgatar na categoria "economias", com lotes; o extrato do cofrinho; o connector do CDI e o Mockserver; a virada do dia com rendimento por lote, XP de recorde, ranque e carência; encerrar a conta só com o cofrinho zerado.

Regras de execução: `AGENTS.md`. Nomes obrigatórios: `docs/plano/PLANO-00-indice.md`, `docs/plano/PLANO-fase-02.md` (tabelas, models, constantes dos models e ids dos tipos fixos), `docs/plano/PLANO-fase-03.md` (`docs/rotas.md`, catálogo de erros, schemas), `docs/plano/PLANO-fase-04.md` (`RequestGenerator`, `PayloadGenerator`, `ObjectGenerator`), `docs/plano/PLANO-fase-05.md` (`AccountRepository`, `CategoryRepository`, `AccountController.close_account`), `docs/plano/PLANO-fase-06.md` (`TransactionRepository`, `EntryRepository`, `BankClockRepository`, `TransactionDTO`, `EntryDTO`, `TransactionController`) e `docs/plano/PLANO-fase-08.md` (`GamificationController`, `GamificationRepository`, `GamificationDTO`). Um passo por vez, na ordem: 7.1 a 7.15 e, por último, 7.fim. A fase 7 roda depois da fase 8 (PLANO-00, "Ordem das fases").

**Pausa obrigatória entre o 7.9 e o 7.10.** O 7.10 só começa depois que o Bruno rodar o script do 7.9 e fizer o commit `chore(cdi): dados do CDI para o mockserver` na branch `fase/07-cofrinho` (PLANO-00, "(c) Feito à mão", item 4). O pedido ao agente é feito em duas vezes: `Execute os passos 7.1 a 7.9 de docs/plano/PLANO-fase-07.md` e, depois do commit à mão, `Execute os passos 7.10 a 7.fim de docs/plano/PLANO-fase-07.md`.

Contagem de testes da suíte (última linha do pytest): `244 passed` no começo; `259 passed` em 7.1; `269 passed` de 7.2 a 7.4; `280 passed` em 7.5; `292 passed` em 7.6; `302 passed` de 7.7 a 7.10; `311 passed` em 7.11; `318 passed` em 7.12; `322 passed` em 7.13; `329 passed` em 7.14; `331 passed` em 7.15 e no 7.fim (244 de antes + 25 unitários + 62 de integração).

Comandos usados nesta fase que não estão na seção 3 do `AGENTS.md`:

| Quero | Comando |
|---|---|
| Rodar uma linha de Python no `.venv` (a raiz do repositório no caminho de import) | `./.venv/Scripts/python.exe -c "<código>"` |
| Rodar uma linha de Python dentro do container da API | `docker compose exec -T api python -c "<código>"` |
| Rodar SQL no banco | `docker compose exec -T db psql -U bootcamp -d bootcamp -t -A -c "<SQL>"` |
| Ver o fim do log do Mockserver (a partir do 7.10) | `docker compose logs --tail 100 mockserver` |
| Procurar texto nos arquivos do Git | `git grep <opções> -- <pastas>` |
| Procurar texto também em arquivo novo, ainda fora do Git | `git grep --untracked <opções> -- <arquivo>` |

O `-T` desliga o terminal interativo, que o Git Bash não oferece. O `-t -A` do `psql` tira cabeçalho, rodapé e alinhamento. O `git grep` termina com código 1 quando não acha nada: nos itens em que o esperado é "nenhuma linha", esse código 1 sem linha impressa é o resultado certo.

Nas conferências que rodam dentro do container (`docker compose exec -T api python -c`), o código de `src/` é importado direto, sem HTTP, e tudo termina em `s.rollback()`: nada fica gravado. As conferências que rodam no `.venv` e começam com `DbUtils.rollback()` apagam o banco e o recriam do zero, como os testes que dependem do relógio.

Todas as saídas esperadas abaixo valem sem `.env` na raiz do repositório (ARQ-04). Existe um `.env`: PARE.

Valores que a fase usa (a conta está nos unitários do 7.1 e do 7.2):

| O quê | Valor |
|---|---|
| Mínimo de cada ranque, em centavos (GAM-13) | `DEFAULT` 0 · `BRONZE` 200000 · `SILVER` 500000 · `GOLD` 1000000 · `PLATINUM` 3000000 · `DIAMOND` 5000000 |
| CDI de teste | `"0.054266"` (% ao dia) → taxa diária `0.00054266` no `DEFAULT`, `0.00055622` no `BRONZE` (102,5%), `0.00059692` no `GOLD` (110%) |
| R$ 1.000,00 guardados, 4 dias a `"0.054266"` | o cofrinho fica com 100054, 100108, 100162 e 100217 (a fração de centavo passa para o dia seguinte) |
| R$ 10.000,00 guardados (ranque `GOLD` na hora) | dia 1 rende 542 (a 100%, o ranque que rende é o do início do dia); dia 2 rende 597 (a 110%): 1000542 e 1001139 |
| CDI `"1.000000"` (1% ao dia) | R$ 1.000,00 rendem R$ 10,00 no dia: números redondos para o XP de recorde |

Decisões do Bruno de 08/10 que este plano aplica (registrar no `04 - Decisões.md`, ver "Divergências"): carência cai na virada que fecha o dia `grace_until` · no resgate de parte de um lote, a parte de rendimento é arredondada para cima · a taxa diária é truncada na 8ª casa · a virada não processa conta encerrada.

## Cobertura das regras desta fase (TST-02)

| Regra | O que fica vermelho se a regra deixar de valer |
|---|---|
| GAM-12, GAM-13 — ranque pelo saldo do cofrinho, com os mínimos | `test_ranks.py::TestRanks::test_minimum_of_each_rank`, `test_rank_for_balance_at_each_minimum`; `test_save.py::test_rank_goes_up_when_saving` |
| COF-11 — sem limite para guardar | `test_ranks.py::TestRanks::test_no_maximum`; `test_save.py::test_saves_the_whole_balance_and_refuses_more` (o único limite é o saldo da conta) |
| COF-02 — % do CDI por ranque | `test_ranks.py::TestRanks::test_cdi_percent_of_each_rank`; `test_piggy_yield.py::TestDailyRate::test_rate_of_each_rank`; `test_day_closing_rank.py::test_yield_rank_follows_the_rank_from_the_next_day`, `test_grace_starts_and_keeps_yielding_at_the_rank` |
| COF-15 — taxa com 8 casas (truncada) e fração de centavo guardada | `test_piggy_yield.py` (`test_rate_is_truncated_at_eight_places`, `test_keeps_the_fraction_of_the_cent`, `test_fraction_carries_to_the_next_day`); `test_day_closing_yield.py::test_yields_whole_cents_and_keeps_the_fraction` |
| COF-13 — rendimento contado em cada lote | `test_piggy_yield.py::TestLotYield::test_small_lot_waits_for_a_whole_cent`; `test_day_closing_yield.py::test_each_lot_yields_on_its_own` |
| COF-24 — resgate proporcional, rendimento arredondado para cima | `test_lots.py` (7 testes); conferência P1 do 7.12 |
| COF-06 — lote por guardar; resgate do mais antigo | conferência L2 do 7.6 (o lote mais antigo zera antes do seguinte) |
| COF-23 — soma dos lotes = saldo da categoria = soma dos lançamentos | conferências L1 (7.3) e C1 (7.12 e 7.fim) |
| COF-07 — resgate maior que a categoria → 422 | `test_redeem.py::test_refuses_more_than_category_balance`, `test_refuses_redemption_from_empty_piggy_bank` |
| COF-08 — bruto e líquido | `test_redeem.py::test_redeems_into_account`; `test_piggy_bank_entries.py::test_gets_saving_and_redemption_transactions` |
| COF-10, MOV-09 — guardar e resgatar livres, sem tarifa | `test_save.py::test_saves_into_default_category`; `test_redeem.py::test_redeems_into_account` (os saldos mudam exatamente o valor) |
| COF-03 — só "economias" nesta fase; sem `category_key` vai para ela | `test_save.py::test_unknown_category_is_404`; `test_redeem.py::test_unknown_category_is_404`; `test_piggy_bank_entries.py::test_saves_and_redeems_with_the_default_category_key` |
| COF-05, MOV-04 — extrato do cofrinho por categoria, paginado | `test_piggy_bank_entries.py` (`test_empty_piggy_bank_statement`, `test_pagination`, `test_filters_by_the_default_category`, `test_unknown_category_is_404`) |
| MOV-17 — outra ponta de guardar, resgatar e rendimento | `test_piggy_bank_entries.py::test_shows_saving_and_redemption_on_both_sides`, `test_gets_saving_and_redemption_transactions`; `test_day_closing_yield.py::test_yield_entry_is_paid_by_the_bank` |
| GAM-04 — só passar do recorde dá XP; tirar e pôr de volta não dá | `test_save.py::test_saving_gives_record_xp`; `test_redeem.py::test_saving_again_after_redeeming_gives_no_xp`; `test_day_closing_record_xp.py::test_yield_below_the_record_gives_no_xp_until_it_passes` |
| GAM-25 — XP do recorde em reais inteiros | `test_save.py::test_saving_gives_record_xp`; `test_day_closing_record_xp.py::test_cents_of_yield_become_xp_when_they_complete_a_real` |
| GAM-19 — sobe na hora; cai só na virada; rende o ranque do início do dia; XP na hora e na virada | `test_save.py::test_rank_goes_up_when_saving`; `test_redeem.py::test_rank_does_not_fall_when_redeeming`; `test_day_closing_yield.py::test_yield_uses_the_rank_of_the_start_of_the_day`; `test_day_closing_rank.py::test_rank_goes_up_at_day_closing`, `test_yield_rank_follows_the_rank_from_the_next_day`; `test_day_closing_record_xp.py::test_yield_above_the_record_gives_xp` |
| GAM-14 — carência de 30 dias; volta ao mínimo mantém; cai direto para o ranque do saldo | `test_day_closing_rank.py::test_grace_starts_and_keeps_yielding_at_the_rank`, `test_grace_ends_when_the_balance_returns`, `test_rank_falls_straight_to_the_balance_rank_after_thirty_days`; conferência R1 do 7.14 |
| COF-16 — dia sem taxa não rende | `test_day_closing.py::test_day_without_cdi_rate_still_closes`; `test_day_closing_yield.py::test_day_without_rate_does_not_yield` |
| COF-22 — guardado antes da virada rende o dia; resgatado não | `test_day_closing_yield.py::test_yields_whole_cents_and_keeps_the_fraction`, `test_redeemed_money_does_not_yield_the_day` |
| COF-17, ARQ-07 — CDI pelo connector | conferências B1 e B2 do 7.8 e M2 do 7.10; todos os testes da virada |
| COF-20 — Banco Central fora → 503 e o dia não avança | `test_day_closing.py::test_central_bank_down_is_503_and_the_day_does_not_advance`; conferência B2 do 7.8 |
| DIA-01, DIA-02, DIA-05 — relógio, virada por rota, data da virada | `test_day_closing.py` (`test_closes_the_day_and_advances_the_clock`, `test_same_day_twice_is_409`, `test_future_date_is_422`, `test_impossible_date_is_422`) |
| DIA-03 — ordem da virada | `test_day_closing_record_xp.py::test_yield_above_the_record_gives_xp` (o XP conta o rendimento do mesmo dia); `test_day_closing_rank.py::test_rank_goes_up_at_day_closing` (o ranque conta o rendimento do mesmo dia) |
| CLI-07 — bloqueada segue na virada | `test_day_closing_yield.py::test_blocked_account_still_yields`; `test_day_closing_record_xp.py::test_blocked_account_gains_record_xp`; `test_day_closing_rank.py::test_blocked_account_rank_follows` |
| CLI-05 — encerrada só lê (a virada não a processa, decisão de 08/10) | `test_day_closing_rank.py::test_closed_account_is_skipped` |
| CLI-09 — bloqueada ou encerrada não guarda nem resgata | `test_save.py::test_blocked_or_closed_account_refuses_saving`; `test_redeem.py::test_blocked_or_closed_account_refuses_redemption`; `test_close_account_with_piggy.py::test_closes_after_the_piggy_bank_reaches_zero` |
| CLI-06 — encerrar só com o cofrinho zerado | `test_close_account_with_piggy.py` (2 testes) |
| MOV-12, MOV-19 — idempotência em guardar e resgatar | `test_repeated_request_returns_first_response` e `test_same_key_with_other_request_is_409` em `test_save.py` e `test_redeem.py`; `test_save.py::test_saves_the_whole_balance_and_refuses_more` (pedido barrado não guarda a chave) |
| API-18, API-03 — valor inteiro ≥ 1; schema fechado | `test_refuses_body_out_of_schema` em `test_save.py`, `test_redeem.py` e `test_day_closing.py`; `test_piggy_bank_entries.py::test_refuses_query_out_of_schema` |
| R8, API-09 — outro dono → 404 | `test_other_account_token_is_404` e `test_missing_or_wrong_token_is_404` em `test_save.py`, `test_redeem.py` e `test_piggy_bank_entries.py` |
| PRD-07, PRD-13 — `ADMIN-TOKEN` na virada | `test_day_closing.py::test_requires_admin_token` |
| R5 — o `id` nunca sai | `assert_no_internal_id` em `test_piggy_bank_entries.py` |
| R6, DAD-08 — centavos inteiros, sem float | `type(...) is int` em `test_save.py` e `test_redeem.py`; `test_returns_*_never_float` nos três unitários |
| DAD-07 — saldo em dois lugares | `test_piggy_bank_entries.py::test_shows_saving_and_redemption_on_both_sides`; `test_day_closing_yield.py::test_yield_entry_is_paid_by_the_bank` (a soma do extrato do cofrinho é o saldo dele) |

Dos "Testes previstos" do `09 - Plano de trabalho`, caem nesta fase:

| Cenário do 09 | Teste |
|---|---|
| Transação: bloqueio automático e virada do dia → a conta continua bloqueada | `test_day_closing.py::test_automatically_blocked_account_stays_blocked` |
| Transação: conta bloqueada ou encerrada → 409 (no cofrinho) | `test_save.py::test_blocked_or_closed_account_refuses_saving`; `test_redeem.py::test_blocked_or_closed_account_refuses_redemption` |
| Transação: valor zero, negativo, decimal ou float (no cofrinho) | `test_refuses_body_out_of_schema` em `test_save.py` e `test_redeem.py` |
| Extrato: `limit` zero, acima de 100 ou texto (no cofrinho) | `test_piggy_bank_entries.py::test_refuses_query_out_of_schema` |
| Transação: varrer as respostas atrás de `id` (no cofrinho) | `test_piggy_bank_entries.py` (`assert_no_internal_id` nos dois extratos e na consulta da operação) |

O critério das partes 6, 7 e 8 na "Ordem de construção" do 09 fica vermelho em: "o dinheiro vai e volta, sem tarifa" → `test_redeem.py::test_redeems_into_account`; "o dia vira e o cofrinho rende" → `test_day_closing_yield.py::test_yields_whole_cents_and_keeps_the_fraction`; "o ranque sobe, segura 30 dias e cai" → `test_day_closing_rank.py::test_rank_falls_straight_to_the_balance_rank_after_thirty_days`.

---

### Passo 7.1 — Ranques e lotes (unitário)
**Branch:** fase/07-cofrinho · **Depende de:** fase 8 (merge `feat(gamificacao): fase 08 com XP, nível, pontos e tarifa menor` e commit `docs(plano): roteiros auditados`, os dois na `main`; tag `fase-08`)
**Objetivo:** `RANK_ORDER`, `RANK_MINIMUM_CENTS`, `RANK_CDI_PERCENT`, `GRACE_DAYS` e `rank_for_balance(balance_cents)` em `src/calculations/ranks.py`; `split_redemption(principal_remaining, yield_remaining, amount_cents)` em `src/calculations/lots.py`; o `GamificationDTO` passa a ler o % do CDI de `ranks.py`. Os unitários vêm antes.
**Decisões:** GAM-12 — ranque pelo cofrinho · GAM-13 — mínimos · GAM-14 — 30 dias de carência · COF-02 — % do CDI por ranque · COF-11 — sem limite · COF-24 — resgate proporcional (rendimento arredondado para cima, decisão de 08/10) · TST-05 — unitários em pasta separada, escritos primeiro · R6 — sem float
**Arquivos:**
- `tests/unit/test_ranks.py` (criar): o conteúdo inteiro é:

```python
"""Ranques do cofrinho: calculations.ranks (GAM-12, GAM-13, GAM-14, COF-02, COF-11, TST-05).

Unitário: importa só de calculations, da biblioteca padrão e do pytest.
O pytest.ini põe src/ no caminho de import.
"""

from decimal import Decimal

import pytest

from calculations import GRACE_DAYS, RANK_CDI_PERCENT, RANK_MINIMUM_CENTS, RANK_ORDER, rank_for_balance


class TestRanks:
    def test_order_from_default_to_diamond(self):
        assert RANK_ORDER == ("DEFAULT", "BRONZE", "SILVER", "GOLD", "PLATINUM", "DIAMOND")

    def test_minimum_of_each_rank(self):
        assert RANK_MINIMUM_CENTS == {
            "DEFAULT": 0,
            "BRONZE": 200000,
            "SILVER": 500000,
            "GOLD": 1000000,
            "PLATINUM": 3000000,
            "DIAMOND": 5000000,
        }

    def test_cdi_percent_of_each_rank(self):
        assert RANK_CDI_PERCENT == {
            "DEFAULT": "100",
            "BRONZE": "102.5",
            "SILVER": "105",
            "GOLD": "110",
            "PLATINUM": "115",
            "DIAMOND": "120",
        }

    def test_grace_is_thirty_days(self):
        assert GRACE_DAYS == 30

    def test_rank_for_balance_at_each_minimum(self):
        assert rank_for_balance(0) == "DEFAULT"
        assert rank_for_balance(199999) == "DEFAULT"
        assert rank_for_balance(200000) == "BRONZE"
        assert rank_for_balance(499999) == "BRONZE"
        assert rank_for_balance(500000) == "SILVER"
        assert rank_for_balance(999999) == "SILVER"
        assert rank_for_balance(1000000) == "GOLD"
        assert rank_for_balance(2999999) == "GOLD"
        assert rank_for_balance(3000000) == "PLATINUM"
        assert rank_for_balance(4999999) == "PLATINUM"
        assert rank_for_balance(5000000) == "DIAMOND"

    def test_no_maximum(self):
        assert rank_for_balance(9223372036854775807) == "DIAMOND"

    def test_refuses_negative_balance(self):
        with pytest.raises(ValueError):
            rank_for_balance(-1)

    def test_returns_text_never_float(self):
        for rank in RANK_ORDER:
            assert type(RANK_CDI_PERCENT[rank]) is str
            assert type(RANK_MINIMUM_CENTS[rank]) is int
            assert Decimal(RANK_CDI_PERCENT[rank]) >= Decimal("100")

        assert type(rank_for_balance(200000)) is str
```

- `tests/unit/test_lots.py` (criar): o conteúdo inteiro é:

```python
"""Resgate de um lote: calculations.lots (COF-24, TST-05).

Unitário: importa só de calculations, da biblioteca padrão e do pytest.
Principal e rendimento saem na proporção do lote; a parte de rendimento é
arredondada para cima ao centavo (decisão de 08/10).
"""

import pytest

from calculations import split_redemption


class TestSplitRedemption:
    def test_whole_lot_takes_everything(self):
        assert split_redemption(10000, 250, 10250) == (10000, 250)

    def test_part_follows_the_proportion(self):
        assert split_redemption(10000, 250, 4100) == (4000, 100)
        assert split_redemption(100000, 54, 50000) == (49973, 27)

    def test_yield_part_rounds_up(self):
        assert split_redemption(10000, 1, 100) == (99, 1)
        assert split_redemption(10000, 250, 1) == (0, 1)

    def test_lot_without_yield(self):
        assert split_redemption(5000, 0, 3000) == (3000, 0)

    def test_parts_always_add_up(self):
        for amount_cents in range(1, 43):
            principal_part, yield_part = split_redemption(37, 5, amount_cents)

            assert principal_part + yield_part == amount_cents
            assert 0 <= principal_part <= 37
            assert 0 <= yield_part <= 5

    def test_refuses_invalid_input(self):
        for principal_remaining, yield_remaining, amount_cents in [(100, 10, 0), (100, 10, 111), (-1, 10, 5), (100, -1, 5), (0, 0, 1)]:
            with pytest.raises(ValueError):
                split_redemption(principal_remaining, yield_remaining, amount_cents)

    def test_returns_int_never_float(self):
        for value in split_redemption(100000, 54, 50000):
            assert type(value) is int
```

- `src/calculations/ranks.py` (criar): o conteúdo inteiro é:

```python
"""Ranques do cofrinho (GAM-12, GAM-13, GAM-14, COF-02). Conta pura: sem banco e sem HTTP.

Os ranques são os enumerators da tabela piggy_rank, em texto: esta pasta
não importa models.
"""


# GAM-12: do menor para o maior.
RANK_ORDER = ("DEFAULT", "BRONZE", "SILVER", "GOLD", "PLATINUM", "DIAMOND")

# GAM-13: o saldo mínimo do cofrinho, em centavos, para alcançar cada ranque.
RANK_MINIMUM_CENTS = {
    "DEFAULT": 0,
    "BRONZE": 200000,
    "SILVER": 500000,
    "GOLD": 1000000,
    "PLATINUM": 3000000,
    "DIAMOND": 5000000,
}

# COF-02: quanto o cofrinho rende em cada ranque, em % do CDI. Em texto:
# vira Decimal exato na conta do rendimento (R6) e sai igual na resposta
# da gamificação (docs/rotas.md, "Formatos").
RANK_CDI_PERCENT = {
    "DEFAULT": "100",
    "BRONZE": "102.5",
    "SILVER": "105",
    "GOLD": "110",
    "PLATINUM": "115",
    "DIAMOND": "120",
}

# GAM-14: dias de carência, contados do dia em que o cofrinho caiu abaixo
# do mínimo do ranque.
GRACE_DAYS = 30


def rank_for_balance(balance_cents: int) -> str:
    """O maior ranque cujo mínimo o saldo do cofrinho alcança (GAM-12, GAM-13). Sem teto (COF-11)."""
    if balance_cents < 0:
        raise ValueError(f"saldo do cofrinho não pode ser negativo, veio {balance_cents}")

    rank = RANK_ORDER[0]
    for candidate in RANK_ORDER:
        if balance_cents >= RANK_MINIMUM_CENTS[candidate]:
            rank = candidate

    return rank
```

- `src/calculations/lots.py` (criar): o conteúdo inteiro é:

```python
"""Resgate de um lote do cofrinho (COF-24). Conta pura: sem banco e sem HTTP."""


def split_redemption(principal_remaining: int, yield_remaining: int, amount_cents: int) -> tuple:
    """Quanto de um resgate sai do principal e quanto do rendimento de um lote: (principal, rendimento), em centavos.

    As duas partes saem na proporção do lote (COF-24). A parte de
    rendimento é arredondada para cima ao centavo, e o principal fica com o
    resto: como na tarifa (MOV-10) e no imposto (COF-12), dividir o resgate
    nunca sai mais barato (decisão de 08/10). Como o resgate não passa do
    saldo do lote, a parte de rendimento nunca passa do rendimento do lote,
    e a de principal nunca passa do principal.
    """
    if principal_remaining < 0 or yield_remaining < 0:
        raise ValueError(f"lote com valor negativo: principal {principal_remaining}, rendimento {yield_remaining}")

    lot_balance = principal_remaining + yield_remaining

    if amount_cents < 1 or amount_cents > lot_balance:
        raise ValueError(f"o resgate de {amount_cents} centavos não cabe no lote de {lot_balance}")

    # -(-a // b) é a divisão inteira arredondada para cima, sem float.
    yield_part = -(-amount_cents * yield_remaining // lot_balance)

    return amount_cents - yield_part, yield_part
```

- `src/calculations/__init__.py` (editar): o conteúdo inteiro passa a ser:

```python
from calculations.fee import calculate_fee
from calculations.xp import MAX_LEVEL, XpGain, gain_record_xp, gain_transfer_xp, level_cost, next_level_n, record_whole_reais
from calculations.ranks import GRACE_DAYS, RANK_CDI_PERCENT, RANK_MINIMUM_CENTS, RANK_ORDER, rank_for_balance
from calculations.lots import split_redemption
```

- `src/dtos/gamification_dto.py` (editar): o conteúdo inteiro passa a ser o abaixo. Muda em relação ao 8.2: o import de `calculations` ganha `RANK_CDI_PERCENT`, o de `models` perde `PiggyRank`, e `CDI_PERCENT_BY_RANK` deixa de ter os números e passa a ser o `RANK_CDI_PERCENT` (os números ficam num lugar só, PLANO-fase-08, divergência 4). A resposta não muda.

```python
from calculations import MAX_LEVEL, RANK_CDI_PERCENT, level_cost, next_level_n
from calculations.fee import FULL_FEE_TENTHS_OF_PERCENT
from models import Account


# COF-02: quanto o cofrinho rende, em % do CDI, pelo ranque. Os números
# moram em src/calculations/ranks.py, em texto, como todo percentual de
# docs/rotas.md ("Formatos").
CDI_PERCENT_BY_RANK = RANK_CDI_PERCENT

# GAM-09, GAM-10: cada ponto vale um décimo de ponto percentual.
TENTHS_PER_PERCENT = 10


class GamificationDTO:
    """A gamificação da conta (API-14): só valores e textos, nunca id (R5)."""

    @staticmethod
    def obj_to_dict(account: Account) -> dict:
        """O corpo de GET /accounts/{account_key}/gamification, de point_applications e de point_resets.

        xp_to_next_level é nulo no nível 10, onde o XP segue sem teto
        (GAM-16). fee_percent e chance_percent saem dos pontos (GAM-09,
        GAM-10). cdi_percent é o do ranque atual (COF-02). grace_until é
        nulo fora da carência (GAM-14).
        """
        xp_to_next_level = None
        if account.level < MAX_LEVEL:
            xp_to_next_level = level_cost(next_level_n(account.level)) - account.xp

        grace_until = None
        if account.grace_until is not None:
            grace_until = account.grace_until.isoformat()

        rank = account.rank.enumerator

        return {
            "level": account.level,
            "xp": account.xp,
            "xp_to_next_level": xp_to_next_level,
            "points_free": account.points_free,
            "points_fee": account.points_fee,
            "points_chance": account.points_chance,
            "fee_percent": GamificationDTO.percent_text(FULL_FEE_TENTHS_OF_PERCENT - account.points_fee),
            "chance_percent": GamificationDTO.percent_text(account.points_chance),
            "rank": rank,
            "cdi_percent": CDI_PERCENT_BY_RANK[rank],
            "piggy_record": account.piggy_record,
            "grace_until": grace_until,
        }

    @staticmethod
    def percent_text(tenths_of_percent: int) -> str:
        """Décimos de ponto percentual em texto, sem float (R6): 10 → "1"; 9 → "0.9"; 1 → "0.1"; 0 → "0"."""
        whole = tenths_of_percent // TENTHS_PER_PERCENT
        tenths = tenths_of_percent % TENTHS_PER_PERCENT

        if tenths == 0:
            return str(whole)

        return f"{whole}.{tenths}"
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia.
2. Abra a fase, um comando por vez:
   ```
   git switch main
   git log --oneline
   git tag --list fase-08
   git switch -c fase/07-cofrinho
   ```
   O `git log` mostra `docs(plano): roteiros auditados` e `feat(gamificacao): fase 08 com XP, nível, pontos e tarifa menor`; o `git tag` mostra `fase-08`.
3. Crie `tests/unit/test_ranks.py` e `tests/unit/test_lots.py` com o conteúdo do campo **Arquivos**.
4. `./.venv/Scripts/python.exe -m pytest -v tests/unit/test_ranks.py tests/unit/test_lots.py` → a saída tem `ImportError` com `cannot import name 'GRACE_DAYS' from 'calculations'` e `ImportError` com `cannot import name 'split_redemption' from 'calculations'`; a última linha tem `2 errors`. É o motivo certo (AGENTS.md, seção 6).
5. Crie `src/calculations/ranks.py` e `src/calculations/lots.py` com o conteúdo do campo **Arquivos**.
6. Edite `src/calculations/__init__.py` com o conteúdo do campo **Arquivos**.
7. `./.venv/Scripts/python.exe -m pytest -v tests/unit/test_ranks.py tests/unit/test_lots.py` → a última linha tem `15 passed`.
8. Edite `src/dtos/gamification_dto.py` com o conteúdo do campo **Arquivos**.
9. `docker compose up -d --build --wait` → termina sem erro.
10. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `259 passed`.
11. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
12. Rode o **Verificar**.
13. Feche o passo (AGENTS.md, seção 7), um comando por vez:
    ```
    git add -- tests/unit/test_ranks.py tests/unit/test_lots.py src/calculations/ranks.py src/calculations/lots.py src/calculations/__init__.py src/dtos/gamification_dto.py
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "feat(cofrinho): ranques e resgate por lote com teste unitário"
    git log -1 --format=%B
    ```

**Testes:** `tests/unit/test_ranks.py` e `tests/unit/test_lots.py` (TST-05). Não tocam na API nem no banco.

| Função de teste | Entrada | Esperado |
|---|---|---|
| `TestRanks::test_order_from_default_to_diamond` | `RANK_ORDER` | os 6 ranques, do `DEFAULT` ao `DIAMOND` (GAM-12) |
| `TestRanks::test_minimum_of_each_rank` | `RANK_MINIMUM_CENTS` | 0, 200000, 500000, 1000000, 3000000, 5000000 (GAM-13) |
| `TestRanks::test_cdi_percent_of_each_rank` | `RANK_CDI_PERCENT` | `"100"`, `"102.5"`, `"105"`, `"110"`, `"115"`, `"120"` (COF-02) |
| `TestRanks::test_grace_is_thirty_days` | `GRACE_DAYS` | 30 (GAM-14) |
| `TestRanks::test_rank_for_balance_at_each_minimum` | cada mínimo e o centavo abaixo dele | o ranque do mínimo; abaixo, o anterior |
| `TestRanks::test_no_maximum` | 9223372036854775807 | `DIAMOND` (COF-11) |
| `TestRanks::test_refuses_negative_balance` | −1 | `ValueError` |
| `TestRanks::test_returns_text_never_float` | as constantes e um `rank_for_balance` | percentuais `str` ≥ 100; mínimos `int`; ranque `str` (R6) |
| `TestSplitRedemption::test_whole_lot_takes_everything` | lote 10000 + 250; resgate 10250 | `(10000, 250)` |
| `TestSplitRedemption::test_part_follows_the_proportion` | 10000 + 250, resgate 4100; 100000 + 54, resgate 50000 | `(4000, 100)`; `(49973, 27)` (26,99 sobe para 27) (COF-24) |
| `TestSplitRedemption::test_yield_part_rounds_up` | 10000 + 1, resgate 100; 10000 + 250, resgate 1 | `(99, 1)`; `(0, 1)` (decisão de 08/10) |
| `TestSplitRedemption::test_lot_without_yield` | 5000 + 0, resgate 3000 | `(3000, 0)` |
| `TestSplitRedemption::test_parts_always_add_up` | lote 37 + 5, resgates de 1 a 42 | as partes somam o resgate e nenhuma passa do que o lote tem |
| `TestSplitRedemption::test_refuses_invalid_input` | resgate 0; resgate maior que o lote; principal −1; rendimento −1; lote vazio | `ValueError` nos cinco |
| `TestSplitRedemption::test_returns_int_never_float` | 100000 + 54, resgate 50000 | as duas partes `int` (R6) |

**Verificar:**
- `./.venv/Scripts/python.exe -m pytest -v tests/unit/test_ranks.py tests/unit/test_lots.py` → `15 passed`.
- `git grep --untracked -n -e "^import" -e "^from" -- src/calculations/ranks.py src/calculations/lots.py` → nenhuma linha (as duas contas puras não importam nada).
- `git grep -n -e "102.5" -- src` → exatamente uma linha, em `src/calculations/ranks.py` (os percentuais moram num lugar só).
- `./.venv/Scripts/python.exe -m pytest -v tests/integration/gamification/test_get_gamification.py` → `6 passed` (a resposta da gamificação não mudou).
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `259 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/calculations/__init__.py
  src/calculations/lots.py
  src/calculations/ranks.py
  src/dtos/gamification_dto.py
  tests/unit/test_lots.py
  tests/unit/test_ranks.py
  ```
- `git log -1 --format=%B` → `feat(cofrinho): ranques e resgate por lote com teste unitário`

**Pronto quando:**
- [ ] A branch `fase/07-cofrinho` nasceu da `main` com o merge da fase 8.
- [ ] Os testes falharam antes do código com `ImportError` (item 4) e passam depois (item 7).
- [ ] Os seis arquivos têm exatamente o conteúdo do campo **Arquivos**.
- [ ] Suíte com `259 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/07-cofrinho`.

**Commit:** `feat(cofrinho): ranques e resgate por lote com teste unitário`
**Pare se:**
- O `git log` do item 2 não mostrar as duas mensagens, ou o `git tag` não mostrar `fase-08`.
- O item 4 não mostrar os dois `ImportError` (outro erro, ou algum teste rodou).
- O item 7 não terminar com `15 passed` depois de 3 tentativas de conferir os dois arquivos de `src/calculations/` contra o plano.
- Um teste de `test_get_gamification.py` ou de `test_points.py` ficar vermelho.
- A suíte não terminar com `259 passed`.

---

### Passo 7.2 — Rendimento (unitário)
**Branch:** fase/07-cofrinho · **Depende de:** 7.1
**Objetivo:** `daily_rate(cdi_daily_percent, rank_cdi_percent)` (a taxa do dia como fração, truncada em 8 casas) e `lot_yield(lot_balance_cents, residue, rate)` (os centavos inteiros do dia e o resíduo novo, com 8 casas, em `Decimal`) em `src/calculations/piggy_yield.py`, com o unitário escrito antes.
**Decisões:** COF-02 — % do CDI por ranque · COF-13 — rendimento por lote · COF-15 — taxa e resíduo com 8 casas (taxa truncada, decisão de 08/10) · TST-05 — unitários · R6 — sem float
**Arquivos:**
- `tests/unit/test_piggy_yield.py` (criar): o conteúdo inteiro é:

```python
"""Rendimento diário: calculations.piggy_yield (COF-02, COF-13, COF-15, TST-05).

Unitário: importa só de calculations, da biblioteca padrão e do pytest.
CDI de teste: 0,054266% ao dia; a 100% do CDI, a taxa diária é 0,00054266.
"""

from decimal import Decimal

import pytest

from calculations import daily_rate, lot_yield


CDI = "0.054266"
RATE = Decimal("0.00054266")


class TestDailyRate:
    def test_default_rank_is_the_cdi(self):
        assert daily_rate(CDI, "100") == RATE

    def test_rate_of_each_rank(self):
        assert daily_rate(CDI, "102.5") == Decimal("0.00055622")
        assert daily_rate(CDI, "105") == Decimal("0.00056979")
        assert daily_rate(CDI, "110") == Decimal("0.00059692")
        assert daily_rate(CDI, "115") == Decimal("0.00062405")
        assert daily_rate(CDI, "120") == Decimal("0.00065119")

    def test_rate_is_truncated_at_eight_places(self):
        rate = daily_rate(CDI, "110")

        assert rate != Decimal("0.00059693")
        assert rate.as_tuple().exponent == -8
        assert daily_rate("1.000000", "100") == Decimal("0.01")

    def test_refuses_float_and_negative(self):
        with pytest.raises(TypeError):
            daily_rate(0.054266, "100")

        with pytest.raises(TypeError):
            daily_rate(CDI, 100)

        with pytest.raises(ValueError):
            daily_rate("-0.054266", "100")


class TestLotYield:
    def test_keeps_the_fraction_of_the_cent(self):
        assert lot_yield(1000000, Decimal("0"), RATE) == (542, Decimal("0.66"))
        assert lot_yield(100000, Decimal("0"), RATE) == (54, Decimal("0.266"))

    def test_fraction_carries_to_the_next_day(self):
        balance = 100000
        residue = Decimal("0")
        gains = []

        for _ in range(5):
            cents, residue = lot_yield(balance, residue, RATE)
            gains.append(cents)
            balance = balance + cents

        assert gains == [54, 54, 54, 55, 54]
        assert balance == 100271
        assert residue == Decimal("0.62357906")

    def test_small_lot_waits_for_a_whole_cent(self):
        assert lot_yield(1000, Decimal("0"), RATE) == (0, Decimal("0.54266"))
        assert lot_yield(1000, Decimal("0.54266"), RATE) == (1, Decimal("0.08532"))

    def test_zero_rate_keeps_the_residue(self):
        assert lot_yield(500, Decimal("0.3"), Decimal("0")) == (0, Decimal("0.3"))

    def test_refuses_invalid_input(self):
        for lot_balance_cents, residue, rate in [(1000.0, Decimal("0"), RATE), (1000, 0.5, RATE), (1000, Decimal("0"), 0.0005)]:
            with pytest.raises(TypeError):
                lot_yield(lot_balance_cents, residue, rate)

        for lot_balance_cents, residue, rate in [(-1, Decimal("0"), RATE), (1000, Decimal("1"), RATE), (1000, Decimal("-0.1"), RATE), (1000, Decimal("0"), Decimal("-0.1"))]:
            with pytest.raises(ValueError):
                lot_yield(lot_balance_cents, residue, rate)

    def test_returns_int_and_decimal_never_float(self):
        cents, residue = lot_yield(100000, Decimal("0"), RATE)

        assert type(cents) is int
        assert type(residue) is Decimal
        assert type(daily_rate(CDI, "100")) is Decimal
```

- `src/calculations/piggy_yield.py` (criar): o conteúdo inteiro é:

```python
"""Rendimento diário do cofrinho (COF-02, COF-13, COF-15). Conta pura: sem banco e sem HTTP.

Dinheiro inteiro em centavos (int); a taxa e a fração de centavo em
Decimal, nunca float (R6).
"""

from decimal import ROUND_DOWN, Decimal, localcontext


# COF-15: a taxa diária e o resíduo do lote têm 8 casas.
EIGHT_PLACES = Decimal("0.00000001")

# Para passar de percentual para fração.
PERCENT = Decimal(100)

# Dígitos significativos da conta em Decimal: sobra para qualquer saldo em BIGINT.
YIELD_PRECISION = 50


def daily_rate(cdi_daily_percent: str, rank_cdi_percent: str) -> Decimal:
    """A taxa do dia como fração, truncada na 8ª casa (COF-02, COF-15).

    cdi_daily_percent: o CDI do dia em % ao dia, como o Banco Central o
    publica ("0.054266" = 0,054266% ao dia). rank_cdi_percent: o % do CDI
    do ranque (RANK_CDI_PERCENT, "102.5"). Os dois em texto, nunca float.
    A taxa é CDI ÷ 100 × percentual ÷ 100, cortada na 8ª casa: o banco
    nunca paga a mais (decisão de 08/10). 0,054266% a 110% = 0,000596926 →
    0,00059692.
    """
    for name, value in [("cdi_daily_percent", cdi_daily_percent), ("rank_cdi_percent", rank_cdi_percent)]:
        if type(value) is not str:
            raise TypeError(f"{name} precisa ser texto, veio {type(value).__name__}")

    with localcontext() as context:
        context.prec = YIELD_PRECISION
        rate = Decimal(cdi_daily_percent) / PERCENT * Decimal(rank_cdi_percent) / PERCENT

        if rate < 0:
            raise ValueError(f"taxa negativa: {cdi_daily_percent} x {rank_cdi_percent}")

        return rate.quantize(EIGHT_PLACES, rounding=ROUND_DOWN)


def lot_yield(lot_balance_cents: int, residue: Decimal, rate: Decimal) -> tuple:
    """O rendimento de um lote num dia: (centavos inteiros, resíduo novo) (COF-13, COF-15).

    O valor exato é o saldo do lote × a taxa + o resíduo de ontem. Os
    centavos inteiros viram lançamento hoje; a fração (de 0 a menos de 1
    centavo) fica no lote para amanhã. Com a taxa e o resíduo em 8 casas, a
    conta é exata: nada se arredonda aqui.
    """
    if type(lot_balance_cents) is not int:
        raise TypeError(f"lot_balance_cents precisa ser int, veio {type(lot_balance_cents).__name__}")

    for name, value in [("residue", residue), ("rate", rate)]:
        if type(value) is not Decimal:
            raise TypeError(f"{name} precisa ser Decimal, veio {type(value).__name__}")

    if lot_balance_cents < 0:
        raise ValueError(f"saldo do lote não pode ser negativo, veio {lot_balance_cents}")

    if residue < 0 or residue >= 1:
        raise ValueError(f"o resíduo é uma fração de centavo, de 0 a menos de 1; veio {residue}")

    if rate < 0:
        raise ValueError(f"taxa negativa: {rate}")

    with localcontext() as context:
        context.prec = YIELD_PRECISION
        exact = Decimal(lot_balance_cents) * rate + residue
        cents = int(exact.to_integral_value(rounding=ROUND_DOWN))

        return cents, (exact - cents).quantize(EIGHT_PLACES, rounding=ROUND_DOWN)
```

- `src/calculations/__init__.py` (editar): o conteúdo inteiro passa a ser:

```python
from calculations.fee import calculate_fee
from calculations.xp import MAX_LEVEL, XpGain, gain_record_xp, gain_transfer_xp, level_cost, next_level_n, record_whole_reais
from calculations.ranks import GRACE_DAYS, RANK_CDI_PERCENT, RANK_MINIMUM_CENTS, RANK_ORDER, rank_for_balance
from calculations.lots import split_redemption
from calculations.piggy_yield import daily_rate, lot_yield
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/07-cofrinho`; `git log --oneline -n 3` mostra `feat(cofrinho): ranques e resgate por lote com teste unitário`.
2. Crie `tests/unit/test_piggy_yield.py` com o conteúdo do campo **Arquivos**.
3. `./.venv/Scripts/python.exe -m pytest -v tests/unit/test_piggy_yield.py` → a saída tem `ImportError` com `cannot import name 'daily_rate' from 'calculations'` e a última linha tem `1 error`.
4. Crie `src/calculations/piggy_yield.py` com o conteúdo do campo **Arquivos**.
5. Edite `src/calculations/__init__.py` com o conteúdo do campo **Arquivos**.
6. `./.venv/Scripts/python.exe -m pytest -v tests/unit/test_piggy_yield.py` → a última linha tem `10 passed`.
7. `docker compose up -d --build --wait` → termina sem erro.
8. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `269 passed`.
9. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
10. Rode o **Verificar**.
11. Feche o passo (AGENTS.md, seção 7), um comando por vez:
    ```
    git add -- tests/unit/test_piggy_yield.py src/calculations/piggy_yield.py src/calculations/__init__.py
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "feat(cofrinho): rendimento diário com teste unitário"
    git log -1 --format=%B
    ```

**Testes:** `tests/unit/test_piggy_yield.py` (TST-05). Não toca na API nem no banco.

| Função de teste | Entrada | Esperado |
|---|---|---|
| `TestDailyRate::test_default_rank_is_the_cdi` | `"0.054266"`, `"100"` | `Decimal("0.00054266")` |
| `TestDailyRate::test_rate_of_each_rank` | o mesmo CDI a 102,5, 105, 110, 115 e 120% | 0.00055622, 0.00056979, 0.00059692, 0.00062405, 0.00065119 (COF-02) |
| `TestDailyRate::test_rate_is_truncated_at_eight_places` | 110%; `"1.000000"` a 100% | 0.00059692, nunca 0.00059693; expoente −8; 0.01 (decisão de 08/10) |
| `TestDailyRate::test_refuses_float_and_negative` | CDI float; percentual int; CDI negativo | `TypeError`, `TypeError`, `ValueError` (R6) |
| `TestLotYield::test_keeps_the_fraction_of_the_cent` | 1000000 e 100000 centavos a 0.00054266 | `(542, 0.66)`; `(54, 0.266)` (COF-15) |
| `TestLotYield::test_fraction_carries_to_the_next_day` | 100000 por 5 dias, rendimento somado ao lote | 54, 54, 54, 55, 54; lote 100271; resíduo 0.62357906 |
| `TestLotYield::test_small_lot_waits_for_a_whole_cent` | 1000 com resíduo 0; depois com 0.54266 | `(0, 0.54266)`; `(1, 0.08532)` (COF-13: cada lote conta o próprio centavo) |
| `TestLotYield::test_zero_rate_keeps_the_residue` | 500, resíduo 0.3, taxa 0 | `(0, 0.3)` |
| `TestLotYield::test_refuses_invalid_input` | saldo float; resíduo float; taxa float; saldo −1; resíduo 1 e −0.1; taxa −0.1 | `TypeError` nos três primeiros; `ValueError` nos quatro últimos |
| `TestLotYield::test_returns_int_and_decimal_never_float` | 100000 a 0.00054266 | centavos `int`; resíduo e taxa `Decimal` (R6) |

**Verificar:**
- `./.venv/Scripts/python.exe -m pytest -v tests/unit/test_piggy_yield.py` → `10 passed`.
- `git grep --untracked -n -e "^import" -e "^from" -- src/calculations/piggy_yield.py` → exatamente:
  ```
  src/calculations/piggy_yield.py:7:from decimal import ROUND_DOWN, Decimal, localcontext
  ```
- `git grep --untracked -n -e "float(" -- src/calculations` → nenhuma linha.
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `269 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/calculations/__init__.py
  src/calculations/piggy_yield.py
  tests/unit/test_piggy_yield.py
  ```
- `git log -1 --format=%B` → `feat(cofrinho): rendimento diário com teste unitário`

**Pronto quando:**
- [ ] O teste falhou antes do código com `ImportError` (item 3) e passa depois (item 6).
- [ ] Os três arquivos têm exatamente o conteúdo do campo **Arquivos**.
- [ ] Suíte com `269 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/07-cofrinho`.

**Commit:** `feat(cofrinho): rendimento diário com teste unitário`
**Pare se:**
- O item 3 não mostrar `cannot import name 'daily_rate' from 'calculations'`.
- O item 6 não terminar com `10 passed` depois de 3 tentativas de conferir `src/calculations/piggy_yield.py` contra o plano.
- O `git grep` do import mostrar outra linha.
- A suíte não terminar com `269 passed`.

---
### Passo 7.3 — Lotes: repository
**Branch:** fase/07-cofrinho · **Depende de:** 7.2
**Objetivo:** `LotRepository` (`create`, `list_open_for_update`, do mais antigo para o mais novo, e o nome novo `update_remaining`) e `CategoryRepository.get_balance` (a soma dos lançamentos do cofrinho na categoria).
**Decisões:** COF-06 — lote por guardar, resgate do mais antigo · COF-23 — colunas do lote e a prova das somas · COF-05 — saldo por categoria · DAD-12 — UUID no repository · MOV-05 — trava antes de ler · R4 — append-only (o lote é estado: só as colunas de resto mudam)
**Arquivos:**
- `src/repositories/lot_repository.py` (criar): o conteúdo inteiro é:

```python
from datetime import date
from decimal import Decimal
from uuid import uuid4

from database import Context
from models import Category, Lot, Transaction


class LotRepository:
    """Consulta e grava os lotes do cofrinho (COF-06, COF-23). Nenhuma regra de negócio mora aqui.

    A key nasce aqui, com uuid4 (DAD-12). O lote guarda em colunas o
    principal e o rendimento que restam e o resíduo; quem decide os valores
    é o controller, com o cofrinho travado (COF-23, MOV-05). Lote não se
    apaga: o que zera continua na tabela, com os restos em 0.
    """

    def __init__(self, context: Context) -> None:
        self.session = context.db_session

    def create(self, category: Category, transaction: Transaction, accounting_date: date, principal: int) -> Lot:
        """Um lote novo para cada guardar (COF-06): o principal guardado, rendimento 0 e resíduo 0, com a data contábil do guardar."""
        lot = Lot()
        lot.lot_key = str(uuid4())
        lot.category_id = category.id
        lot.transaction_id = transaction.id
        lot.accounting_date = accounting_date
        lot.principal_remaining = principal
        lot.yield_remaining = 0
        lot.residue = Decimal("0")

        self.session.add(lot)
        self.session.flush()

        return lot

    def list_open_for_update(self, category: Category) -> list:
        """Os lotes da categoria que ainda têm dinheiro, do mais antigo para o mais novo (id crescente), travados com SELECT ... FOR UPDATE (COF-06)."""
        return (
            self.session.query(Lot)
            .filter(Lot.category_id == category.id, Lot.principal_remaining + Lot.yield_remaining > 0)
            .order_by(Lot.id)
            .with_for_update()
            .populate_existing()
            .all()
        )

    def update_remaining(self, lot: Lot, principal_remaining: int, yield_remaining: int, residue: Decimal) -> None:
        """Escreve no lote o principal e o rendimento que restam e o resíduo (COF-23)."""
        lot.principal_remaining = principal_remaining
        lot.yield_remaining = yield_remaining
        lot.residue = residue
```

- `src/repositories/category_repository.py` (editar): duas mudanças, e nada mais.
  1. As linhas
     ```python
     from database import Context
     from models import Account, Category, CategoryStatus, CategoryStatusEvent
     ```
     viram as linhas
     ```python
     from sqlalchemy import func

     from database import Context
     from models import Account, Category, CategoryStatus, CategoryStatusEvent, Entry
     ```
  2. O método `get_balance` abaixo entra no fim da classe, logo depois de `get_default`, com uma linha em branco antes dele:

```python
    def get_balance(self, category: Category) -> int:
        """O saldo da categoria: a soma dos lançamentos do cofrinho nela, em centavos (COF-05, COF-23).

        Só os lançamentos do cofrinho têm category_id. O PostgreSQL devolve
        a soma de BIGINT como NUMERIC: o int() a traz de volta para centavos
        inteiros (DAD-08).
        """
        total = self.session.query(func.coalesce(func.sum(Entry.amount), 0)).filter(Entry.category_id == category.id).scalar()

        return int(total)
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
from repositories.gamification_repository import GamificationRepository
from repositories.lot_repository import LotRepository
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/07-cofrinho`; `git log --oneline -n 3` mostra `feat(cofrinho): rendimento diário com teste unitário`.
2. Crie `src/repositories/lot_repository.py` com o conteúdo do campo **Arquivos**.
3. Faça as duas mudanças em `src/repositories/category_repository.py`.
4. Edite `src/repositories/__init__.py` com o conteúdo do campo **Arquivos**.
5. `docker compose up -d --build --wait` → termina sem erro.
6. Rode a conferência L1 do **Verificar**.
7. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `269 passed`.
8. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
9. Feche o passo (AGENTS.md, seção 7), um comando por vez:
   ```
   git add -- src/repositories/lot_repository.py src/repositories/category_repository.py src/repositories/__init__.py
   git diff --cached --name-only
   git diff --name-only
   git ls-files --others --exclude-standard
   git commit -m "feat(cofrinho): repository dos lotes e saldo da categoria"
   git log -1 --format=%B
   ```

**Testes:** nenhum teste novo. O passo é de camada de baixo; as rotas dos passos 7.5 e 7.6 usam estas peças por HTTP. Aqui, a prova é a L1: numa transação só, abre uma conta, grava um lançamento de 1500 no cofrinho e dois lotes (1000 e 500), confere o saldo da categoria, a ordem dos lotes e que um lote zerado sai da lista, e desfaz tudo (`rollback`).
**Verificar:**
- L1 (um comando, numa linha só):
  ```
  docker compose exec -T api python -c "from datetime import date; from decimal import Decimal; from database import open_context; from repositories import AccountRepository, CategoryRepository, CustomerRepository, EntryRepository, LotRepository, TransactionRepository; c = open_context(); s = c.get_or_create_session(); x = CustomerRepository(c).create('Ana Lima', '529.982.247-25', 'ana.conferencia.l1@example.com', date(1995, 4, 12)); s.flush(); r = AccountRepository(c); a = r.create_customer_account(x, '0' * 64); p = r.get_piggy_bank(a); g = CategoryRepository(c).create_default(p); s.flush(); d = date(2026, 6, 1); t = TransactionRepository(c).create('SAVE', None, None, d); EntryRepository(c).create(t, p, 'AMOUNT', 1500, g); lr = LotRepository(c); l1 = lr.create(g, t, d, 1000); l2 = lr.create(g, t, d, 500); b = CategoryRepository(c).get_balance(g); print(b, type(b) is int, len(l1.lot_key), l1.accounting_date); print([(l.principal_remaining, l.yield_remaining, l.residue == 0) for l in lr.list_open_for_update(g)]); lr.update_remaining(l1, 0, 0, Decimal('0.5')); s.flush(); print([l.id == l2.id for l in lr.list_open_for_update(g)]); s.rollback()"
  ```
  → exatamente:
  ```
  1500 True 36 2026-06-01
  [(1000, 0, True), (500, 0, True)]
  [True]
  ```
  Linha a linha: o saldo da categoria é a soma dos lançamentos, em `int`; os dois lotes, do mais antigo para o mais novo; o lote zerado (mesmo com resíduo) sai da lista dos que têm dinheiro.
- `git grep -n -e "session.delete" -e "\.delete(" -- src/repositories/lot_repository.py` → nenhuma linha (R4).
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `269 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/repositories/__init__.py
  src/repositories/category_repository.py
  src/repositories/lot_repository.py
  ```
- `git log -1 --format=%B` → `feat(cofrinho): repository dos lotes e saldo da categoria`

**Pronto quando:**
- [ ] `lot_repository.py` e `__init__.py` têm exatamente o conteúdo do campo **Arquivos**; `category_repository.py` tem as duas mudanças, e só elas.
- [ ] A L1 dá as 3 linhas esperadas.
- [ ] Suíte com `269 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/07-cofrinho`.

**Commit:** `feat(cofrinho): repository dos lotes e saldo da categoria`
**Pare se:**
- As duas linhas de import citadas na mudança 1 não existirem exatamente assim em `src/repositories/category_repository.py`.
- `docker compose up -d --build --wait` falhar com `ImportError` ou `circular import` no `docker compose logs --tail 100 api`: traga a saída.
- A L1 terminar com `Traceback` ou der outra saída depois de 3 tentativas de conferir os três arquivos contra o plano. Um `IntegrityError` com `customer_document_number_key` ou `customer_email_key`: rode `docker compose down -v`, `docker compose up -d --build --wait` e a L1 de novo.
- A suíte não terminar com `269 passed`.

---

### Passo 7.4 — Guardar e resgatar: controller
**Branch:** fase/07-cofrinho · **Depende de:** 7.3
**Objetivo:** `PiggyBankController.save` e `redeem` (só a categoria "economias"; outra `category_key` → 404 `QIT001021`); o nome novo `GamificationController.raise_rank` (o ranque sobe na hora) e `GamificationRepository.update_rank`; `TransactionDTO` com as respostas de guardar e de resgatar (bruto e líquido) e a consulta da operação com os valores do resgate.
**Decisões:** COF-01 — um cofrinho por conta · COF-03 — "economias" sem `category_key` · COF-06 — lote por guardar, resgate do mais antigo · COF-07 — resgate maior que a categoria → 422 · COF-08 — bruto e líquido · COF-10 — guardar e resgatar livres · COF-11 — sem limite · COF-23 — colunas do lote · COF-24 — resgate proporcional · MOV-05, MOV-11 — trava da conta e do cofrinho na ordem do `id` · MOV-09 — sem tarifa · MOV-12, MOV-19 — idempotência · GAM-04 — XP de recorde · GAM-19 — ranque sobe na hora e não cai fora da virada · CLI-09 — bloqueada não mexe em dinheiro · DAD-13 — recusa não grava · ARQ-02 — quem chama faz o commit
**Arquivos:**
- `src/controllers/piggy_bank_controller.py` (criar): o conteúdo inteiro é:

```python
from sqlalchemy.exc import IntegrityError

from calculations import split_redemption
from controllers.base_controller import BaseController
from controllers.gamification_controller import GamificationController
from dtos import TransactionDTO
from errors import (
    AccountNotActive,
    CategoryNotFound,
    IdempotencyKeyConflict,
    InsufficientBalance,
    InsufficientCategoryBalance,
)
from models import Account, AccountStatus, AccountType, Category, EntryType, Transaction, TransactionType
from repositories import AccountRepository, BankClockRepository, CategoryRepository, EntryRepository, LotRepository, TransactionRepository
from utils.request_hash import hash_request_body


class PiggyBankController(BaseController):
    """As regras do cofrinho: guardar e resgatar (COF).

    Guardar e resgatar seguem o desenho do dinheiro em movimento
    (TransactionController): dono → repetição → relógio → trava → regras →
    gravação. A trava pega a conta e o cofrinho, na ordem do id (MOV-05,
    MOV-11). Sem tarifa (MOV-09) e sem XP de movimentação (GAM-17): o único
    XP é o do recorde do cofrinho (GAM-04).
    """

    def __init__(self) -> None:
        super().__init__(__name__)
        self.account_repository = AccountRepository(self.context)
        self.bank_clock_repository = BankClockRepository(self.context)
        self.category_repository = CategoryRepository(self.context)
        self.entry_repository = EntryRepository(self.context)
        self.lot_repository = LotRepository(self.context)
        self.transaction_repository = TransactionRepository(self.context)
        self.gamification_controller = GamificationController()

    def save(self, account_key: str, account_token: str, saving_data: dict) -> dict:
        """Guardar: leva dinheiro da conta para uma categoria do cofrinho (COF-06, COF-10, COF-11). As regras, nesta ordem:

        1. a conta é do dono do token (404 QIT001010, R8);
        2. a mesma request_control_key com o mesmo pedido devolve a resposta
           da primeira vez, com os saldos de depois daquele guardar (MOV-19);
           com outro pedido, 409 QIT001014 (MOV-12);
        3. trava a conta e o cofrinho (MOV-05);
        4. a conta está ACTIVE (409 QIT001011, CLI-09);
        5. a categoria é a "economias": sem category_key no corpo, é ela;
           outra key, 404 QIT001021 (as outras categorias entram no 9.6);
        6. o saldo da conta cobre o valor (422 QIT001015).

        Depois: a operação SAVE; AMOUNT −valor na conta e AMOUNT +valor no
        cofrinho, na categoria; um lote novo com o valor e a data contábil
        (COF-06). O ranque sobe na hora se o saldo do cofrinho alcançou um
        ranque maior (GAM-19), e passar do recorde dá XP (GAM-04). A
        resposta traz a key, o saldo da conta e o saldo do cofrinho.
        """
        account = self.get_owned_account(account_key, account_token)

        request_control_key = saving_data["request_control_key"]
        request_hash = hash_request_body(TransactionType.SAVE, account_key, saving_data)

        repeated_transaction = self._find_repeated(request_control_key, request_hash)
        if repeated_transaction is not None:
            return self._saving_response(repeated_transaction, account)

        accounting_date = self.bank_clock_repository.get_accounting_date()
        account, piggy_bank = self._lock_account_and_piggy_bank(account)

        # Uma chamada com a mesma chave pode ter concluído enquanto esta esperava a trava.
        repeated_transaction = self._find_repeated(request_control_key, request_hash)
        if repeated_transaction is not None:
            return self._saving_response(repeated_transaction, account)

        if account.status.enumerator != AccountStatus.ACTIVE:
            raise AccountNotActive(account_key, account.status.enumerator)

        category = self._get_category(piggy_bank, saving_data.get("category_key"))
        amount = saving_data["amount"]

        if account.balance < amount:
            raise InsufficientBalance(account_key)

        try:
            transaction = self.transaction_repository.create(TransactionType.SAVE, request_control_key, request_hash, accounting_date)
            self.entry_repository.create(transaction, account, EntryType.AMOUNT, -amount)
            self.entry_repository.create(transaction, piggy_bank, EntryType.AMOUNT, amount, category)
            self.lot_repository.create(category, transaction, accounting_date, amount)

            self.gamification_controller.raise_rank(account, piggy_bank, accounting_date)
            self.gamification_controller.award_record_xp(account, transaction, accounting_date)

            transaction_dto = TransactionDTO.with_piggy_bank_balance(transaction, account.balance, piggy_bank.balance)
            self.logger.info("operation_ready_to_commit transaction_key=%s", transaction.transaction_key)
            self.session.commit()
        except IntegrityError:
            self.session.rollback()

            repeated_transaction = self._find_repeated(request_control_key, request_hash)
            if repeated_transaction is None:
                raise

            return self._saving_response(repeated_transaction, account)

        return transaction_dto

    def redeem(self, account_key: str, account_token: str, redemption_data: dict) -> dict:
        """Resgatar: traz dinheiro de uma categoria do cofrinho para a conta (COF-06, COF-07, COF-10, COF-24). As regras, nesta ordem:

        1. a conta é do dono do token (404 QIT001010, R8);
        2. a mesma request_control_key com o mesmo pedido devolve a resposta
           da primeira vez (MOV-19); com outro pedido, 409 QIT001014 (MOV-12);
        3. trava a conta e o cofrinho (MOV-05);
        4. a conta está ACTIVE (409 QIT001011, CLI-09);
        5. a categoria é a "economias": sem category_key no corpo, é ela;
           outra key, 404 QIT001021 (as outras categorias entram no 9.6);
        6. o saldo da categoria cobre o valor (422 QIT001023, COF-07), mesmo
           que o cofrinho todo tenha o dinheiro.

        Depois: a operação REDEEM; o valor sai dos lotes da categoria, do
        mais antigo para o mais novo, cada um até zerar (COF-06), e de cada
        lote o principal e o rendimento saem na proporção do lote (COF-24);
        AMOUNT −valor no cofrinho, na categoria, e AMOUNT +valor na conta.
        IOF e IR entram no passo 9.2: nesta fase o bruto é o líquido. O
        ranque não cai (GAM-19) e o recorde não muda (GAM-04). A resposta
        traz a key, os dois saldos, o bruto, o IOF, o IR e o líquido (COF-08).
        """
        account = self.get_owned_account(account_key, account_token)

        request_control_key = redemption_data["request_control_key"]
        request_hash = hash_request_body(TransactionType.REDEEM, account_key, redemption_data)

        repeated_transaction = self._find_repeated(request_control_key, request_hash)
        if repeated_transaction is not None:
            return self._redemption_response(repeated_transaction, account)

        accounting_date = self.bank_clock_repository.get_accounting_date()
        account, piggy_bank = self._lock_account_and_piggy_bank(account)

        # Uma chamada com a mesma chave pode ter concluído enquanto esta esperava a trava.
        repeated_transaction = self._find_repeated(request_control_key, request_hash)
        if repeated_transaction is not None:
            return self._redemption_response(repeated_transaction, account)

        if account.status.enumerator != AccountStatus.ACTIVE:
            raise AccountNotActive(account_key, account.status.enumerator)

        category = self._get_category(piggy_bank, redemption_data.get("category_key"))
        amount = redemption_data["amount"]

        if self.category_repository.get_balance(category) < amount:
            raise InsufficientCategoryBalance(category.category_key)

        try:
            transaction = self.transaction_repository.create(TransactionType.REDEEM, request_control_key, request_hash, accounting_date)
            self._take_from_lots(category, amount)
            self.entry_repository.create(transaction, piggy_bank, EntryType.AMOUNT, -amount, category)
            self.entry_repository.create(transaction, account, EntryType.AMOUNT, amount)

            redemption_amounts = self.get_redemption_amounts(transaction, piggy_bank)
            transaction_dto = TransactionDTO.with_redemption(transaction, account.balance, piggy_bank.balance, redemption_amounts)
            self.logger.info("operation_ready_to_commit transaction_key=%s", transaction.transaction_key)
            self.session.commit()
        except IntegrityError:
            self.session.rollback()

            repeated_transaction = self._find_repeated(request_control_key, request_hash)
            if repeated_transaction is None:
                raise

            return self._redemption_response(repeated_transaction, account)

        return transaction_dto

    def get_redemption_amounts(self, transaction: Transaction, piggy_bank: Account) -> dict:
        """O bruto, o IOF, o IR e o líquido de um resgate, remontados dos lançamentos da operação (COF-08, MOV-19).

        Bruto: o que saiu do cofrinho (os AMOUNT do cofrinho, com o sinal
        trocado). IOF e IR: os lançamentos IOF e IR da conta BANK (passo
        9.2; nesta fase, 0). Líquido: bruto − IOF − IR. A consulta da
        operação (TransactionController.get_transaction) usa o mesmo método.
        """
        bank = self.account_repository.get_system_account(AccountType.BANK)

        gross_amount = 0
        iof = 0
        ir = 0

        for entry in self.entry_repository.list_by_transaction(transaction, [piggy_bank.id, bank.id]):
            entry_type = entry.entry_type.enumerator

            if entry.account_id == piggy_bank.id and entry_type == EntryType.AMOUNT:
                gross_amount = gross_amount - entry.amount

            if entry.account_id == bank.id and entry_type == EntryType.IOF:
                iof = iof + entry.amount

            if entry.account_id == bank.id and entry_type == EntryType.IR:
                ir = ir + entry.amount

        return {
            "gross_amount": gross_amount,
            "iof": iof,
            "ir": ir,
            "net_amount": gross_amount - iof - ir,
        }

    def _take_from_lots(self, category: Category, amount: int) -> int:
        """Tira o valor dos lotes da categoria, do mais antigo para o mais novo, cada um até zerar (COF-06).

        De cada lote, principal e rendimento saem na proporção dele
        (split_redemption, COF-24); o resíduo fica. Devolve quanto saiu de
        rendimento, somado: é sobre ele que o imposto do passo 9.2 incide.
        """
        remaining = amount
        yield_taken = 0

        for lot in self.lot_repository.list_open_for_update(category):
            if remaining == 0:
                break

            taken = min(remaining, lot.principal_remaining + lot.yield_remaining)
            principal_part, yield_part = split_redemption(lot.principal_remaining, lot.yield_remaining, taken)

            self.lot_repository.update_remaining(lot, lot.principal_remaining - principal_part, lot.yield_remaining - yield_part, lot.residue)

            yield_taken = yield_taken + yield_part
            remaining = remaining - taken

        return yield_taken

    def _get_category(self, piggy_bank: Account, category_key: str) -> Category:
        """A categoria do pedido: sem category_key, a "economias" (COF-03).

        Nesta fase o cofrinho só tem a "economias": outra key responde 404
        QIT001021 (passo 9.6).
        """
        category = self.category_repository.get_default(piggy_bank)

        if category_key is not None and category_key != category.category_key:
            raise CategoryNotFound(category_key)

        return category

    def _lock_account_and_piggy_bank(self, account: Account) -> tuple:
        """A conta e o cofrinho dela, travados na ordem do id (MOV-05, MOV-11), com os valores relidos do banco."""
        piggy_bank = self.account_repository.get_piggy_bank(account)

        locked_accounts = {}
        for locked_account in self.account_repository.lock_accounts([account, piggy_bank]):
            locked_accounts[locked_account.id] = locked_account

        return locked_accounts[account.id], locked_accounts[piggy_bank.id]

    def _saving_response(self, transaction: Transaction, account: Account) -> dict:
        """A resposta de um guardar já feito, remontada dos lançamentos (MOV-19)."""
        piggy_bank = self.account_repository.get_piggy_bank(account)

        return TransactionDTO.with_piggy_bank_balance(
            transaction,
            self._balance_after(transaction, account),
            self._balance_after(transaction, piggy_bank),
        )

    def _redemption_response(self, transaction: Transaction, account: Account) -> dict:
        """A resposta de um resgate já feito, remontada dos lançamentos (MOV-19)."""
        piggy_bank = self.account_repository.get_piggy_bank(account)

        return TransactionDTO.with_redemption(
            transaction,
            self._balance_after(transaction, account),
            self._balance_after(transaction, piggy_bank),
            self.get_redemption_amounts(transaction, piggy_bank),
        )

    def _find_repeated(self, request_control_key: str, request_hash: str) -> Transaction:
        """A operação já gravada com esta chave e o mesmo pedido; None quando a chave é nova (MOV-12, MOV-19).

        A chave já usada com outro pedido (outro hash, inclusive de outra
        operação) responde 409 QIT001014.
        """
        transaction = self.transaction_repository.get_by_request_control_key(request_control_key)

        if transaction is None:
            return None

        if transaction.request_hash != request_hash:
            raise IdempotencyKeyConflict(request_control_key)

        return transaction

    def _balance_after(self, transaction: Transaction, account: Account) -> int:
        """O saldo da conta (ou do cofrinho) logo depois da operação: o balance_after do último lançamento dela na operação (MOV-19)."""
        entries = self.entry_repository.list_by_transaction(transaction, [account.id])

        return entries[-1].balance_after
```

- `src/controllers/__init__.py` (editar): o conteúdo inteiro passa a ser:

```python
from controllers.customer_controller import CustomerController
from controllers.account_controller import AccountController
from controllers.transaction_controller import TransactionController
from controllers.gamification_controller import GamificationController
from controllers.piggy_bank_controller import PiggyBankController
```

- `src/controllers/gamification_controller.py` (editar): três mudanças, e nada mais.
  1. A linha
     ```python
     from calculations import XpGain, gain_record_xp, gain_transfer_xp, record_whole_reais
     ```
     vira
     ```python
     from calculations import RANK_ORDER, XpGain, gain_record_xp, gain_transfer_xp, rank_for_balance, record_whole_reais
     ```
  2. A linha
     ```python
     from models import Account, AccountStatus, PointsEvent, Transaction, XpEvent
     ```
     vira
     ```python
     from models import Account, AccountStatus, PointsEvent, RankEvent, Transaction, XpEvent
     ```
  3. O método `raise_rank` abaixo entra logo depois do método `award_record_xp` e antes de `_apply_xp_gain`, com uma linha em branco antes dele:

```python
    def raise_rank(self, account: Account, piggy_bank: Account, accounting_date: date) -> bool:
        """Sobe o ranque da conta se o saldo do cofrinho alcança um ranque maior que o atual (GAM-12, GAM-13, GAM-19).

        1. o ranque que o saldo dá (rank_for_balance) é maior que o atual:
           se não é, nada muda e a resposta é False;
        2. o ranque novo vale na hora, a carência acaba (grace_until nulo) e
           o evento UP é gravado com o ranque novo.

        O ranque que rende (yield_rank) não muda aqui: só a virada o grava
        (GAM-19). Quem chama (guardar, passo 7.4; a virada, passo 7.14) já
        travou a conta e o cofrinho e faz o commit.
        """
        balance_rank = rank_for_balance(piggy_bank.balance)

        if RANK_ORDER.index(balance_rank) <= RANK_ORDER.index(account.rank.enumerator):
            return False

        if account.grace_until is not None:
            self.gamification_repository.create_rank_event(account, account.rank.enumerator, RankEvent.GRACE_END, accounting_date)

        self.gamification_repository.update_rank(account, balance_rank, None)
        self.gamification_repository.create_rank_event(account, balance_rank, RankEvent.UP, accounting_date)

        return True
```

- `src/repositories/gamification_repository.py` (editar): o método `update_rank` abaixo entra no fim da classe, logo depois de `update_piggy_record`, com uma linha em branco antes dele. Os imports não mudam (`PiggyRank` e `date` já estão no arquivo).

```python
    def update_rank(self, account: Account, rank_enumerator: str, grace_until: date) -> None:
        """Escreve o ranque atual da conta e o fim da carência; grace_until nulo fora da carência (GAM-12, GAM-14)."""
        account.rank = self.session.query(PiggyRank).filter(PiggyRank.enumerator == rank_enumerator).one()
        account.grace_until = grace_until
```

- `src/dtos/transaction_dto.py` (editar): o conteúdo inteiro passa a ser:

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
    def with_piggy_bank_balance(transaction: Transaction, balance: int, piggy_bank_balance: int) -> dict:
        """A resposta do guardar: a key, o saldo da conta e o saldo total do cofrinho, os dois depois de guardar (docs/rotas.md)."""
        return {
            "transaction_key": transaction.transaction_key,
            "balance": balance,
            "piggy_bank_balance": piggy_bank_balance,
        }

    @staticmethod
    def with_redemption(transaction: Transaction, balance: int, piggy_bank_balance: int, redemption_amounts: dict) -> dict:
        """A resposta do resgate: a do guardar mais o bruto, o IOF, o IR e o líquido (COF-08)."""
        return {
            "transaction_key": transaction.transaction_key,
            "balance": balance,
            "piggy_bank_balance": piggy_bank_balance,
            "gross_amount": redemption_amounts["gross_amount"],
            "iof": redemption_amounts["iof"],
            "ir": redemption_amounts["ir"],
            "net_amount": redemption_amounts["net_amount"],
        }

    @staticmethod
    def obj_to_dict(transaction: Transaction, entries: list, redemption_amounts: dict = None) -> dict:
        """A operação para o dono (GET .../transactions/{transaction_key}), com os lançamentos já no formato do extrato.

        Na operação REDEEM, `redemption_amounts` traz o bruto, o IOF, o IR e
        o líquido, que entram no fim do objeto (docs/rotas.md, COF-08).
        """
        transaction_dict = {
            "transaction_key": transaction.transaction_key,
            "type": transaction.transaction_type.enumerator,
            "accounting_date": transaction.accounting_date.isoformat(),
            "created_at": transaction.created_at.isoformat(),
            "entries": entries,
        }

        if redemption_amounts is not None:
            transaction_dict.update(redemption_amounts)

        return transaction_dict
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/07-cofrinho`; `git log --oneline -n 3` mostra `feat(cofrinho): repository dos lotes e saldo da categoria`.
2. Crie `src/controllers/piggy_bank_controller.py` com o conteúdo do campo **Arquivos**.
3. Edite `src/controllers/__init__.py` com o conteúdo do campo **Arquivos**.
4. Faça as três mudanças em `src/controllers/gamification_controller.py`.
5. Acrescente `update_rank` em `src/repositories/gamification_repository.py`.
6. Edite `src/dtos/transaction_dto.py` com o conteúdo do campo **Arquivos**.
7. `docker compose up -d --build --wait` → termina sem erro.
8. Rode as conferências S1 e R1 do **Verificar**.
9. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `269 passed`.
10. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
11. Feche o passo (AGENTS.md, seção 7), um comando por vez:
    ```
    git add -- src/controllers/piggy_bank_controller.py src/controllers/__init__.py src/controllers/gamification_controller.py src/repositories/gamification_repository.py src/dtos/transaction_dto.py
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "feat(cofrinho): controller de guardar e resgatar"
    git log -1 --format=%B
    ```

**Testes:** nenhum teste novo. As rotas que usam o controller nascem no 7.5 (guardar) e no 7.6 (resgatar), com os testes que ficam vermelhos antes delas; a consulta da operação com os valores do resgate ganha teste no 7.7. Aqui, a prova são a S1 (os nomes existem e a API sobe com eles) e a R1 (numa transação só, o ranque sobe pelo saldo do cofrinho, não cai, e cada subida grava `UP`; tudo desfeito com `rollback`).
**Verificar:**
- S1 (um comando, numa linha só):
  ```
  docker compose exec -T api python -c "from controllers import GamificationController, PiggyBankController; from controllers.base_controller import BaseController; from dtos import TransactionDTO; print(sorted(n for n in vars(PiggyBankController) if not n.startswith('__'))); print(issubclass(PiggyBankController, BaseController), 'raise_rank' in vars(GamificationController)); print(sorted(n for n in vars(TransactionDTO) if not n.startswith('_')))"
  ```
  → exatamente:
  ```
  ['_balance_after', '_find_repeated', '_get_category', '_lock_account_and_piggy_bank', '_redemption_response', '_saving_response', '_take_from_lots', 'get_redemption_amounts', 'redeem', 'save']
  True True
  ['obj_to_dict', 'only_obj_key', 'with_balance', 'with_piggy_bank_balance', 'with_redemption']
  ```
- R1 (um comando, numa linha só):
  ```
  docker compose exec -T api python -c "from datetime import date; from database import open_context; from controllers import GamificationController; from models import RankEvent; from repositories import AccountRepository, CustomerRepository; c = open_context(); s = c.get_or_create_session(); x = CustomerRepository(c).create('Ana Lima', '529.982.247-25', 'ana.conferencia.r1@example.com', date(1995, 4, 12)); s.flush(); r = AccountRepository(c); a = r.create_customer_account(x, '0' * 64); p = r.get_piggy_bank(a); g = GamificationController(); d = date(2026, 6, 1); print(g.raise_rank(a, p, d)); p.balance = 200000; print(g.raise_rank(a, p, d), a.rank.enumerator, a.yield_rank.enumerator, a.grace_until); p.balance = 199999; print(g.raise_rank(a, p, d), a.rank.enumerator); p.balance = 5000000; print(g.raise_rank(a, p, d), a.rank.enumerator); s.flush(); print([(e.rank.enumerator, e.kind) for e in s.query(RankEvent).filter(RankEvent.account_id == a.id).order_by(RankEvent.id)]); s.rollback()"
  ```
  → exatamente:
  ```
  False
  True BRONZE DEFAULT None
  False BRONZE
  True DIAMOND
  [('BRONZE', 'UP'), ('DIAMOND', 'UP')]
  ```
  Linha a linha: cofrinho em 0 não sobe; R$ 2.000,00 dão `BRONZE` na hora, e o ranque que rende continua `DEFAULT` (GAM-19); um centavo abaixo do mínimo não faz cair (a queda é só na virada); R$ 50.000,00 pulam direto para `DIAMOND`; um evento `UP` por subida.
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `269 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/controllers/__init__.py
  src/controllers/gamification_controller.py
  src/controllers/piggy_bank_controller.py
  src/dtos/transaction_dto.py
  src/repositories/gamification_repository.py
  ```
- `git log -1 --format=%B` → `feat(cofrinho): controller de guardar e resgatar`

**Pronto quando:**
- [ ] `piggy_bank_controller.py`, `controllers/__init__.py` e `transaction_dto.py` têm exatamente o conteúdo do campo **Arquivos**; `gamification_controller.py` e `gamification_repository.py` têm só as mudanças do passo.
- [ ] S1 e R1 dão a saída esperada.
- [ ] Suíte com `269 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/07-cofrinho`.

**Commit:** `feat(cofrinho): controller de guardar e resgatar`
**Pare se:**
- Alguma linha citada nas mudanças de `gamification_controller.py` não for encontrada igual.
- `docker compose up -d --build --wait` falhar com `ImportError` ou `circular import` no `docker compose logs --tail 100 api`: traga a saída.
- S1 ou R1 derem outra saída depois de 3 tentativas de conferir os cinco arquivos contra o plano. Um `IntegrityError` com `customer_document_number_key` ou `customer_email_key` na R1: rode `docker compose down -v`, `docker compose up -d --build --wait` e a R1 de novo.
- A suíte não terminar com `269 passed`.

---
### Passo 7.5 — `POST /accounts/{account_key}/savings`
**Branch:** fase/07-cofrinho · **Depende de:** 7.4
**Objetivo:** `PiggyBankResource.on_post_saving` e a rota `POST /accounts/{account_key}/savings` (tokens: conta; schema `post_savings.json`): 201 com `{"transaction_key", "balance", "piggy_bank_balance"}`; 404 `QIT001010`; 409 `QIT001011`; 404 `QIT001021`; 422 `QIT001015`; 409 `QIT001014`; 400 `QIT000001`.
**Decisões:** COF-10 — guardar livre · COF-11 — sem limite · COF-03 — "economias" sem `category_key` · MOV-09 — sem tarifa · MOV-12, MOV-19 — idempotência · GAM-04 — XP de recorde · GAM-25 — XP em reais inteiros · GAM-19 — ranque sobe na hora · CLI-09 — bloqueada ou encerrada → 409 · API-03, API-18 — schema fechado, valor inteiro ≥ 1 · R8 — outro dono → 404 · TST-01 — black box e TDD
**Arquivos:**
- `src/resources/piggy_bank.py` (criar): o conteúdo inteiro é:

```python
from fastapi import Request
from fastapi import status as http_status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from constants import ACCOUNT_TOKEN_HEADER
from controllers import PiggyBankController
from utils.schema_handler import SchemaHandler


class PiggyBankResource:
    """A porta HTTP do cofrinho: guardar, resgatar e o extrato do cofrinho.

    Sem regra de negócio, sem SQL e sem nada guardado no self (ARQ-02). O
    token da conta chega no cabeçalho ACCOUNT-TOKEN (API-16); quem o
    confere é o controller.
    """

    @SchemaHandler.validate("post_savings.json")
    def on_post_saving(self, account_key: str, payload: dict, request: Request) -> JSONResponse:
        controller = PiggyBankController()
        transaction = controller.save(account_key, request.headers.get(ACCOUNT_TOKEN_HEADER), payload)

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
from resources.gamification import GamificationResource
from resources.piggy_bank import PiggyBankResource
```

- `src/app.py` (editar): três trocas, e nada mais.
  1. A linha
     ```python
     from resources import AccountResource, CustomerResource, GamificationResource, HealthCheckResource, InternalResource, TransactionResource
     ```
     vira
     ```python
     from resources import AccountResource, CustomerResource, GamificationResource, HealthCheckResource, InternalResource, PiggyBankResource, TransactionResource
     ```
  2. A linha
     ```python
         gamification_resource = GamificationResource()
     ```
     vira as duas linhas
     ```python
         gamification_resource = GamificationResource()
         piggy_bank_resource = PiggyBankResource()
     ```
  3. A linha
     ```python
         application.add_api_route("/accounts/{account_key}/point_resets", gamification_resource.on_post_point_reset, methods=["POST"])
     ```
     vira as quatro linhas
     ```python
         application.add_api_route("/accounts/{account_key}/point_resets", gamification_resource.on_post_point_reset, methods=["POST"])

         # Cofrinho
         application.add_api_route("/accounts/{account_key}/savings", piggy_bank_resource.on_post_saving, methods=["POST"])
     ```

- `tests/integration/piggy_bank/test_save.py` (criar; a pasta `tests/integration/piggy_bank/` é nova e fica sem `__init__.py`): o conteúdo inteiro é:

```python
"""Guardar no cofrinho: POST /accounts/{account_key}/savings (COF-03, COF-10, COF-11, GAM-04, GAM-19, GAM-25, MOV-09, MOV-12, CLI-09, R8).

O dinheiro sai da conta e entra na categoria "economias" do cofrinho, sem
tarifa. O ranque sobe na hora; passar do recorde do cofrinho dá n XP por
real inteiro. Os testes que erram o token começam com DbUtils.rollback()
(PRD-10).
"""

from uuid import uuid4

from tests.utils import DbUtils, ObjectGenerator, PayloadGenerator, RequestGenerator


def balances_of(account: dict) -> tuple:
    """(saldo da conta, saldo do cofrinho)."""
    status, response = RequestGenerator.GET_account(account["account_key"], account["account_token"])
    assert status == 200, response

    return response["balance"], response["piggy_bank_balance"]


def gamification_of(account: dict) -> dict:
    status, response = RequestGenerator.GET_gamification(account["account_key"], account["account_token"])
    assert status == 200, response

    return response


def record_progress_of(account: dict) -> tuple:
    """(nível, XP, recorde do cofrinho)."""
    gamification = gamification_of(account)

    return gamification["level"], gamification["xp"], gamification["piggy_record"]


def save(account: dict, payload: dict) -> tuple:
    return RequestGenerator.POST_saving(account["account_key"], account["account_token"], payload)


def assert_saved(account: dict, amount: int) -> dict:
    status, response = save(account, PayloadGenerator.saving(amount=amount))
    assert status == 201, response

    return response


class TestSave:
    def test_saves_into_default_category(self):
        account = ObjectGenerator.create_funded_account(100000)

        status, response = save(account, PayloadGenerator.saving(amount=30000))

        assert status == 201, response
        assert sorted(response) == ["balance", "piggy_bank_balance", "transaction_key"]
        assert len(response["transaction_key"]) == 36
        assert (response["balance"], response["piggy_bank_balance"]) == (70000, 30000)
        assert type(response["balance"]) is int
        assert type(response["piggy_bank_balance"]) is int
        assert balances_of(account) == (70000, 30000)

    def test_saves_the_whole_balance_and_refuses_more(self):
        account = ObjectGenerator.create_funded_account(1000)
        payload = PayloadGenerator.saving(amount=1001)

        status, response = save(account, payload)
        assert status == 422, response
        assert response["code"] == "QIT001015"
        assert balances_of(account) == (1000, 0)

        payload["amount"] = 1000
        status, response = save(account, payload)
        assert status == 201, response
        assert balances_of(account) == (0, 1000)

        status, response = save(account, PayloadGenerator.saving(amount=1))
        assert status == 422, response
        assert response["code"] == "QIT001015"
        assert balances_of(account) == (0, 1000)

    def test_repeated_request_returns_first_response(self):
        account = ObjectGenerator.create_funded_account(100000)
        payload = PayloadGenerator.saving(amount=30000)

        first_status, first_response = save(account, payload)
        assert first_status == 201, first_response

        status, response = save(account, payload)
        assert (status, response) == (first_status, first_response)
        assert balances_of(account) == (70000, 30000)

        assert_saved(account, 10000)

        status, response = save(account, payload)
        assert (status, response) == (first_status, first_response)
        assert balances_of(account) == (60000, 40000)

        # A repetição simultânea deve passar mesmo quando a primeira esgota o saldo.
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier

        raced = ObjectGenerator.create_funded_account(1000)
        raced_payload = PayloadGenerator.saving(amount=1000)
        gate = Barrier(2)

        def send_same(_index):
            gate.wait(timeout=5)
            return save(raced, raced_payload)

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(send_same, range(2)))

        assert results[0][0] == 201, results
        assert results == [results[0], results[0]], results
        assert balances_of(raced) == (0, 1000)


    def test_same_key_with_other_request_is_409(self):
        account = ObjectGenerator.create_funded_account(100000)
        payload = PayloadGenerator.saving(amount=30000)

        status, response = save(account, payload)
        assert status == 201, response

        other_payload = PayloadGenerator.saving(amount=20000, request_control_key=payload["request_control_key"])
        status, response = save(account, other_payload)
        assert status == 409, response
        assert response["code"] == "QIT001014"

        withdrawal = PayloadGenerator.withdrawal(amount=30000, request_control_key=payload["request_control_key"])
        status, response = RequestGenerator.POST_withdrawal(account["account_key"], account["account_token"], withdrawal)
        assert status == 409, response
        assert response["code"] == "QIT001014"

        assert balances_of(account) == (70000, 30000)

    def test_unknown_category_is_404(self):
        account = ObjectGenerator.create_funded_account(10000)

        status, response = save(account, PayloadGenerator.saving(amount=1000, category_key=str(uuid4())))
        assert status == 404, response
        assert response["code"] == "QIT001021"
        assert balances_of(account) == (10000, 0)

        assert_saved(account, 1000)
        assert balances_of(account) == (9000, 1000)

    def test_blocked_or_closed_account_refuses_saving(self):
        account = ObjectGenerator.create_funded_account(10000)

        status, response = RequestGenerator.POST_block(account["account_key"], PayloadGenerator.block())
        assert status == 204, response

        status, response = save(account, PayloadGenerator.saving(amount=1000))
        assert status == 409, response
        assert response["code"] == "QIT001011"
        assert balances_of(account) == (10000, 0)

        status, response = RequestGenerator.POST_unblock(account["account_key"])
        assert status == 204, response

        assert_saved(account, 1000)
        assert balances_of(account) == (9000, 1000)

        closed_account = ObjectGenerator.create_account()
        status, response = RequestGenerator.DELETE_account(closed_account["account_key"], closed_account["account_token"])
        assert status == 204, response

        status, response = save(closed_account, PayloadGenerator.saving(amount=1))
        assert status == 409, response
        assert response["code"] == "QIT001011"

    def test_rank_goes_up_when_saving(self):
        account = ObjectGenerator.create_funded_account(600000)

        assert_saved(account, 199999)
        gamification = gamification_of(account)
        assert (gamification["rank"], gamification["cdi_percent"]) == ("DEFAULT", "100")

        assert_saved(account, 1)
        gamification = gamification_of(account)
        assert (gamification["rank"], gamification["cdi_percent"], gamification["grace_until"]) == ("BRONZE", "102.5", None)

        assert_saved(account, 300000)
        gamification = gamification_of(account)
        assert (gamification["rank"], gamification["cdi_percent"]) == ("SILVER", "105")

        assert balances_of(account) == (100000, 500000)

    def test_saving_gives_record_xp(self):
        account = ObjectGenerator.create_funded_account(20000)
        assert record_progress_of(account) == (0, 0, 0)

        assert_saved(account, 10000)
        assert record_progress_of(account) == (0, 100, 10000)

        assert_saved(account, 50)
        assert record_progress_of(account) == (0, 100, 10050)

        assert_saved(account, 50)
        assert record_progress_of(account) == (0, 101, 10100)

    def test_other_account_token_is_404(self):
        DbUtils.rollback()
        account_a = ObjectGenerator.create_funded_account(10000)
        account_b = ObjectGenerator.create_funded_account(10000)

        status, response = RequestGenerator.POST_saving(account_a["account_key"], account_b["account_token"], PayloadGenerator.saving())
        assert status == 404, response
        assert response["code"] == "QIT001010"

        status, response = RequestGenerator.POST_saving(account_b["account_key"], account_a["account_token"], PayloadGenerator.saving())
        assert status == 404, response
        assert response["code"] == "QIT001010"

        assert balances_of(account_a) == (10000, 0)
        assert balances_of(account_b) == (10000, 0)

        assert_saved(account_a, 1000)

    def test_missing_or_wrong_token_is_404(self):
        DbUtils.rollback()
        account = ObjectGenerator.create_funded_account(10000)

        for account_token in [None, "token_errado"]:
            status, response = RequestGenerator.POST_saving(account["account_key"], account_token, PayloadGenerator.saving())
            assert status == 404, (account_token, response)
            assert response["code"] == "QIT001010"

        status, response = RequestGenerator.POST_saving(str(uuid4()), account["account_token"], PayloadGenerator.saving())
        assert status == 404, response
        assert response["code"] == "QIT001010"

        assert balances_of(account) == (10000, 0)
        assert_saved(account, 1000)

    def test_refuses_body_out_of_schema(self):
        account = ObjectGenerator.create_funded_account(10000)
        request_control_key = str(uuid4())
        payloads = [
            {"amount": 0, "request_control_key": request_control_key},
            {"amount": -1, "request_control_key": request_control_key},
            {"amount": 1.5, "request_control_key": request_control_key},
            {"amount": "100", "request_control_key": request_control_key},
            {"request_control_key": request_control_key},
            {"amount": 100},
            {"amount": 100, "request_control_key": "nao-e-uma-key"},
            {"amount": 100, "request_control_key": request_control_key, "category_key": "economias"},
            {"amount": 100, "request_control_key": request_control_key, "extra": 1},
        ]

        for payload in payloads:
            status, response = save(account, payload)
            assert status == 400, (payload, response)
            assert response["code"] == "QIT000001"

        assert balances_of(account) == (10000, 0)
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/07-cofrinho`; `git log --oneline -n 3` mostra `feat(cofrinho): controller de guardar e resgatar`.
2. Crie `tests/integration/piggy_bank/test_save.py` com o conteúdo do campo **Arquivos**.
3. `docker compose up -d --build --wait`.
4. `./.venv/Scripts/python.exe -m pytest -v tests/integration/piggy_bank/test_save.py` → a última linha tem `11 failed` e não tem `passed`. Os 11 falham por asserção: hoje o caminho `/accounts/{account_key}/savings` responde 404 `QIT000404` (onde o teste espera 201, 400, 409, 422 ou 404 com outro código).
5. Crie `src/resources/piggy_bank.py` com o conteúdo do campo **Arquivos**.
6. Edite `src/resources/__init__.py` com o conteúdo do campo **Arquivos**.
7. Faça as três trocas em `src/app.py`.
8. `docker compose up -d --build --wait`.
9. `./.venv/Scripts/python.exe -m pytest -v tests/integration/piggy_bank/test_save.py` → a última linha tem `11 passed`.
10. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `280 passed`.
11. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
12. Feche o passo (AGENTS.md, seção 7), um comando por vez:
    ```
    git add -- src/resources/piggy_bank.py src/resources/__init__.py src/app.py tests/integration/piggy_bank/test_save.py
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "feat(cofrinho): rota de guardar"
    git log -1 --format=%B
    ```

**Testes:** `tests/integration/piggy_bank/test_save.py`. Efeito no banco de cada 201: uma operação `SAVE`, dois lançamentos `AMOUNT` (conta − e cofrinho +, na categoria "economias"), um lote com o valor e a data contábil; o ranque e o XP de recorde quando a regra manda. Cada recusa não grava nada além da linha de `request_log`.

| Função de teste | Entrada | Esperado |
|---|---|---|
| `test_saves_into_default_category` | conta com 100000; guardar 30000 sem `category_key` | 201 com exatamente `transaction_key` (36 caracteres), `balance` 70000 e `piggy_bank_balance` 30000, os dois `int`; a conta mostra 70000 e 30000 (COF-10, MOV-09) |
| `test_saves_the_whole_balance_and_refuses_more` | conta com 1000; guardar 1001; o mesmo corpo com 1000 e a mesma chave; guardar 1 | 422 `QIT001015` e nada muda; 201, conta 0 e cofrinho 1000 (o pedido barrado não guardou a chave, MOV-12); 422 `QIT001015` |
| `test_repeated_request_returns_first_response` | o mesmo corpo duas vezes; outro guardar de 10000; o primeiro corpo de novo | a mesma resposta 201 nas três vezes, com os saldos da primeira (70000 e 30000); a conta fica com 60000 e 40000 (MOV-12, MOV-19) |
| `test_same_key_with_other_request_is_409` | guardar 30000; a mesma chave com 20000; a mesma chave num saque | 201; 409 `QIT001014`; 409 `QIT001014`; saldos 70000 e 30000 |
| `test_unknown_category_is_404` | `category_key` aleatória; depois sem `category_key` | 404 `QIT001021` e nada muda; 201 (COF-03) |
| `test_blocked_or_closed_account_refuses_saving` | conta bloqueada; desbloqueada; outra conta encerrada | 409 `QIT001011` e nada muda; 201; 409 `QIT001011` (CLI-09) |
| `test_rank_goes_up_when_saving` | conta com 600000; guardar 199999, 1 e 300000 | `DEFAULT` e `"100"`; `BRONZE`, `"102.5"` e sem carência; `SILVER` e `"105"` (GAM-19, GAM-13) |
| `test_saving_gives_record_xp` | conta com 20000; guardar 10000, 50 e 50 | (nível, XP, recorde) = (0, 0, 0); (0, 100, 10000); (0, 100, 10050); (0, 101, 10100) (GAM-04, GAM-25: os 50 centavos só viram XP quando completam um real) |
| `test_other_account_token_is_404` | começa com `DbUtils.rollback()`; A com o token de B; B com o de A; A com o de A | 404 `QIT001010` nos dois; saldos iguais; 201 (R8) |
| `test_missing_or_wrong_token_is_404` | começa com `DbUtils.rollback()`; sem `ACCOUNT-TOKEN`; `token_errado`; key que não existe; o token certo | 404 `QIT001010` nos três; 201 |
| `test_refuses_body_out_of_schema` | `amount` 0, −1, 1.5 e `"100"`; sem `amount`; sem `request_control_key`; chave malformada; `category_key` `"economias"`; campo a mais | 400 `QIT000001` nos nove; saldos iguais (API-18, API-03) |

**Verificar:**
- `./.venv/Scripts/python.exe -m pytest -v tests/integration/piggy_bank/test_save.py` → `11 passed`.
- `git grep -n "piggy_bank_resource" -- src/app.py` → exatamente 2 linhas: a do `piggy_bank_resource = PiggyBankResource()` e a da rota `/accounts/{account_key}/savings`.
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `280 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/app.py
  src/resources/__init__.py
  src/resources/piggy_bank.py
  tests/integration/piggy_bank/test_save.py
  ```
- `git log -1 --format=%B` → `feat(cofrinho): rota de guardar`

**Pronto quando:**
- [ ] Os 11 testes falharam antes do código (item 4) e passam depois (item 9).
- [ ] Suíte com `280 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/07-cofrinho`.

**Commit:** `feat(cofrinho): rota de guardar`
**Pare se:**
- O item 4 não terminar com `11 failed`.
- Alguma linha citada nas trocas de `src/app.py` não for encontrada igual.
- Um teste receber 500 (`QIT000500`): rode `docker compose logs --tail 100 api` e traga a saída.
- Um teste receber 403 onde o plano espera 404 (R8).
- A suíte não terminar com `280 passed`.

---

### Passo 7.6 — `POST /accounts/{account_key}/redemptions`
**Branch:** fase/07-cofrinho · **Depende de:** 7.5
**Objetivo:** `PiggyBankResource.on_post_redemption` e a rota `POST /accounts/{account_key}/redemptions` (tokens: conta; schema `post_redemptions.json`): 201 com `{"transaction_key", "balance", "piggy_bank_balance", "gross_amount", "iof", "ir", "net_amount"}`; 404 `QIT001010`; 409 `QIT001011`; 404 `QIT001021`; 422 `QIT001023`; 409 `QIT001014`; 400 `QIT000001`.
**Decisões:** COF-06 — lote mais antigo primeiro · COF-07 — resgate maior que a categoria → 422 · COF-08 — bruto e líquido · COF-10 — resgate livre · COF-24 — resgate proporcional · GAM-04 — tirar e pôr de volta não dá XP · GAM-19 — o ranque não cai fora da virada · MOV-12, MOV-19 — idempotência · CLI-09 — bloqueada ou encerrada → 409 · R8 — outro dono → 404 · TST-01 — black box e TDD
**Arquivos:**
- `src/resources/piggy_bank.py` (editar): o método `on_post_redemption` abaixo entra no fim da classe, logo depois de `on_post_saving`, com uma linha em branco antes dele:

```python
    @SchemaHandler.validate("post_redemptions.json")
    def on_post_redemption(self, account_key: str, payload: dict, request: Request) -> JSONResponse:
        controller = PiggyBankController()
        transaction = controller.redeem(account_key, request.headers.get(ACCOUNT_TOKEN_HEADER), payload)

        return JSONResponse(
            content=jsonable_encoder(transaction),
            status_code=http_status.HTTP_201_CREATED,
        )
```

- `src/app.py` (editar): uma troca, e nada mais. A linha
  ```python
      application.add_api_route("/accounts/{account_key}/savings", piggy_bank_resource.on_post_saving, methods=["POST"])
  ```
  vira as duas linhas
  ```python
      application.add_api_route("/accounts/{account_key}/savings", piggy_bank_resource.on_post_saving, methods=["POST"])
      application.add_api_route("/accounts/{account_key}/redemptions", piggy_bank_resource.on_post_redemption, methods=["POST"])
  ```

- `tests/integration/piggy_bank/test_redeem.py` (criar): o conteúdo inteiro é:

```python
"""Resgatar do cofrinho: POST /accounts/{account_key}/redemptions (COF-06, COF-07, COF-08, COF-10, COF-24, GAM-04, GAM-19, MOV-12, CLI-09, R8).

O dinheiro sai da categoria "economias" (do lote mais antigo) e volta para
a conta. A resposta mostra o bruto e o líquido; o IOF e o IR são 0 até o
passo 9.2. Resgate maior que a categoria → 422 QIT001023. O ranque não cai
e o recorde não muda. Os testes que erram o token começam com
DbUtils.rollback() (PRD-10).
"""

from uuid import uuid4

from tests.utils import DbUtils, ObjectGenerator, PayloadGenerator, RequestGenerator


def balances_of(account: dict) -> tuple:
    """(saldo da conta, saldo do cofrinho)."""
    status, response = RequestGenerator.GET_account(account["account_key"], account["account_token"])
    assert status == 200, response

    return response["balance"], response["piggy_bank_balance"]


def gamification_of(account: dict) -> dict:
    status, response = RequestGenerator.GET_gamification(account["account_key"], account["account_token"])
    assert status == 200, response

    return response


def record_progress_of(account: dict) -> tuple:
    """(nível, XP, recorde do cofrinho)."""
    gamification = gamification_of(account)

    return gamification["level"], gamification["xp"], gamification["piggy_record"]


def assert_saved(account: dict, amount: int) -> None:
    status, response = RequestGenerator.POST_saving(account["account_key"], account["account_token"], PayloadGenerator.saving(amount=amount))
    assert status == 201, response


def redeem(account: dict, payload: dict) -> tuple:
    return RequestGenerator.POST_redemption(account["account_key"], account["account_token"], payload)


def assert_redeemed(account: dict, amount: int) -> dict:
    status, response = redeem(account, PayloadGenerator.redemption(amount=amount))
    assert status == 201, response

    return response


class TestRedeem:
    def test_redeems_into_account(self):
        account = ObjectGenerator.create_funded_account(100000)
        assert_saved(account, 30000)

        status, response = redeem(account, PayloadGenerator.redemption(amount=10000))

        assert status == 201, response
        assert len(response["transaction_key"]) == 36
        assert response == {
            "transaction_key": response["transaction_key"],
            "balance": 80000,
            "piggy_bank_balance": 20000,
            "gross_amount": 10000,
            "iof": 0,
            "ir": 0,
            "net_amount": 10000,
        }
        for field in ["balance", "piggy_bank_balance", "gross_amount", "iof", "ir", "net_amount"]:
            assert type(response[field]) is int, field

        assert balances_of(account) == (80000, 20000)

    def test_refuses_more_than_category_balance(self):
        account = ObjectGenerator.create_funded_account(100000)
        assert_saved(account, 20000)

        status, response = redeem(account, PayloadGenerator.redemption(amount=20001))
        assert status == 422, response
        assert response["code"] == "QIT001023"
        assert balances_of(account) == (80000, 20000)

        assert_redeemed(account, 20000)
        assert balances_of(account) == (100000, 0)

    def test_refuses_redemption_from_empty_piggy_bank(self):
        account = ObjectGenerator.create_funded_account(100000)

        status, response = redeem(account, PayloadGenerator.redemption(amount=1))
        assert status == 422, response
        assert response["code"] == "QIT001023"
        assert balances_of(account) == (100000, 0)

    def test_saving_again_after_redeeming_gives_no_xp(self):
        account = ObjectGenerator.create_funded_account(20000)

        assert_saved(account, 10000)
        assert record_progress_of(account) == (0, 100, 10000)

        assert_redeemed(account, 10000)
        assert record_progress_of(account) == (0, 100, 10000)

        assert_saved(account, 10000)
        assert record_progress_of(account) == (0, 100, 10000)

        assert_saved(account, 100)
        assert record_progress_of(account) == (0, 101, 10100)

    def test_rank_does_not_fall_when_redeeming(self):
        account = ObjectGenerator.create_funded_account(300000)
        assert_saved(account, 200000)
        assert gamification_of(account)["rank"] == "BRONZE"

        assert_redeemed(account, 1000)

        gamification = gamification_of(account)
        assert (gamification["rank"], gamification["grace_until"]) == ("BRONZE", None)
        assert balances_of(account) == (101000, 199000)

    def test_repeated_request_returns_first_response(self):
        account = ObjectGenerator.create_funded_account(100000)
        assert_saved(account, 50000)
        payload = PayloadGenerator.redemption(amount=10000)

        first_status, first_response = redeem(account, payload)
        assert first_status == 201, first_response

        status, response = redeem(account, payload)
        assert (status, response) == (first_status, first_response)
        assert balances_of(account) == (60000, 40000)

        assert_redeemed(account, 5000)

        status, response = redeem(account, payload)
        assert (status, response) == (first_status, first_response)
        assert balances_of(account) == (65000, 35000)

        # A repetição simultânea deve passar mesmo quando a primeira esgota o saldo.
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier

        raced = ObjectGenerator.create_funded_account(1000)
        assert_saved(raced, 1000)
        raced_payload = PayloadGenerator.redemption(amount=1000)
        gate = Barrier(2)

        def send_same(_index):
            gate.wait(timeout=5)
            return redeem(raced, raced_payload)

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(send_same, range(2)))

        assert results[0][0] == 201, results
        assert results == [results[0], results[0]], results
        assert balances_of(raced) == (1000, 0)


    def test_same_key_with_other_request_is_409(self):
        account = ObjectGenerator.create_funded_account(100000)
        saving = PayloadGenerator.saving(amount=50000)
        status, response = RequestGenerator.POST_saving(account["account_key"], account["account_token"], saving)
        assert status == 201, response

        status, response = redeem(account, PayloadGenerator.redemption(amount=50000, request_control_key=saving["request_control_key"]))
        assert status == 409, response
        assert response["code"] == "QIT001014"

        payload = PayloadGenerator.redemption(amount=10000)
        status, response = redeem(account, payload)
        assert status == 201, response

        status, response = redeem(account, PayloadGenerator.redemption(amount=20000, request_control_key=payload["request_control_key"]))
        assert status == 409, response
        assert response["code"] == "QIT001014"

        assert balances_of(account) == (60000, 40000)

    def test_unknown_category_is_404(self):
        account = ObjectGenerator.create_funded_account(10000)
        assert_saved(account, 5000)

        status, response = redeem(account, PayloadGenerator.redemption(amount=1000, category_key=str(uuid4())))
        assert status == 404, response
        assert response["code"] == "QIT001021"
        assert balances_of(account) == (5000, 5000)

        assert_redeemed(account, 1000)
        assert balances_of(account) == (6000, 4000)

    def test_blocked_or_closed_account_refuses_redemption(self):
        account = ObjectGenerator.create_funded_account(10000)
        assert_saved(account, 5000)

        status, response = RequestGenerator.POST_block(account["account_key"], PayloadGenerator.block())
        assert status == 204, response

        status, response = redeem(account, PayloadGenerator.redemption(amount=1000))
        assert status == 409, response
        assert response["code"] == "QIT001011"
        assert balances_of(account) == (5000, 5000)

        status, response = RequestGenerator.POST_unblock(account["account_key"])
        assert status == 204, response

        assert_redeemed(account, 1000)
        assert balances_of(account) == (6000, 4000)

        closed_account = ObjectGenerator.create_account()
        status, response = RequestGenerator.DELETE_account(closed_account["account_key"], closed_account["account_token"])
        assert status == 204, response

        status, response = redeem(closed_account, PayloadGenerator.redemption(amount=1))
        assert status == 409, response
        assert response["code"] == "QIT001011"

    def test_other_account_token_is_404(self):
        DbUtils.rollback()
        account_a = ObjectGenerator.create_funded_account(10000)
        account_b = ObjectGenerator.create_funded_account(10000)
        assert_saved(account_a, 5000)
        assert_saved(account_b, 5000)

        status, response = RequestGenerator.POST_redemption(account_a["account_key"], account_b["account_token"], PayloadGenerator.redemption())
        assert status == 404, response
        assert response["code"] == "QIT001010"

        status, response = RequestGenerator.POST_redemption(account_b["account_key"], account_a["account_token"], PayloadGenerator.redemption())
        assert status == 404, response
        assert response["code"] == "QIT001010"

        assert balances_of(account_a) == (5000, 5000)
        assert balances_of(account_b) == (5000, 5000)

        assert_redeemed(account_a, 1000)

    def test_missing_or_wrong_token_is_404(self):
        DbUtils.rollback()
        account = ObjectGenerator.create_funded_account(10000)
        assert_saved(account, 5000)

        for account_token in [None, "token_errado"]:
            status, response = RequestGenerator.POST_redemption(account["account_key"], account_token, PayloadGenerator.redemption())
            assert status == 404, (account_token, response)
            assert response["code"] == "QIT001010"

        status, response = RequestGenerator.POST_redemption(str(uuid4()), account["account_token"], PayloadGenerator.redemption())
        assert status == 404, response
        assert response["code"] == "QIT001010"

        assert balances_of(account) == (5000, 5000)
        assert_redeemed(account, 1000)

    def test_refuses_body_out_of_schema(self):
        account = ObjectGenerator.create_funded_account(10000)
        assert_saved(account, 5000)
        request_control_key = str(uuid4())
        payloads = [
            {"amount": 0, "request_control_key": request_control_key},
            {"amount": -1, "request_control_key": request_control_key},
            {"amount": 1.5, "request_control_key": request_control_key},
            {"amount": "100", "request_control_key": request_control_key},
            {"request_control_key": request_control_key},
            {"amount": 100},
            {"amount": 100, "request_control_key": "nao-e-uma-key"},
            {"amount": 100, "request_control_key": request_control_key, "category_key": "economias"},
            {"amount": 100, "request_control_key": request_control_key, "extra": 1},
        ]

        for payload in payloads:
            status, response = redeem(account, payload)
            assert status == 400, (payload, response)
            assert response["code"] == "QIT000001"

        assert balances_of(account) == (5000, 5000)
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/07-cofrinho`; `git log --oneline -n 3` mostra `feat(cofrinho): rota de guardar`.
2. Crie `tests/integration/piggy_bank/test_redeem.py` com o conteúdo do campo **Arquivos**.
3. `docker compose up -d --build --wait`.
4. `./.venv/Scripts/python.exe -m pytest -v tests/integration/piggy_bank/test_redeem.py` → a última linha tem `12 failed` e não tem `passed`. Os 12 falham por asserção: hoje o caminho `/accounts/{account_key}/redemptions` responde 404 `QIT000404`.
5. Acrescente `on_post_redemption` em `src/resources/piggy_bank.py`.
6. Faça a troca em `src/app.py`.
7. `docker compose up -d --build --wait`.
8. `./.venv/Scripts/python.exe -m pytest -v tests/integration/piggy_bank/test_redeem.py` → a última linha tem `12 passed`.
9. Rode a conferência L2 do **Verificar**.
10. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `292 passed`.
11. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
12. Feche o passo (AGENTS.md, seção 7), um comando por vez:
    ```
    git add -- src/resources/piggy_bank.py src/app.py tests/integration/piggy_bank/test_redeem.py
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "feat(cofrinho): rota de resgatar"
    git log -1 --format=%B
    ```

**Testes:** `tests/integration/piggy_bank/test_redeem.py`. Efeito no banco de cada 201: uma operação `REDEEM`, dois lançamentos `AMOUNT` (cofrinho −, na categoria, e conta +) e os restos dos lotes atualizados, do mais antigo para o mais novo. Cada recusa não grava nada além da linha de `request_log`.

| Função de teste | Entrada | Esperado |
|---|---|---|
| `test_redeems_into_account` | conta com 100000; guardar 30000; resgatar 10000 | 201 com exatamente `transaction_key`, `balance` 80000, `piggy_bank_balance` 20000, `gross_amount` 10000, `iof` 0, `ir` 0, `net_amount` 10000, todos `int` (COF-08, COF-10) |
| `test_refuses_more_than_category_balance` | cofrinho com 20000; resgatar 20001; depois 20000 | 422 `QIT001023` e nada muda; 201, conta 100000 e cofrinho 0 (COF-07) |
| `test_refuses_redemption_from_empty_piggy_bank` | cofrinho vazio; resgatar 1 | 422 `QIT001023` |
| `test_saving_again_after_redeeming_gives_no_xp` | guardar 10000; resgatar 10000; guardar 10000; guardar 100 | (nível, XP, recorde) = (0, 100, 10000) três vezes; depois (0, 101, 10100) (GAM-04) |
| `test_rank_does_not_fall_when_redeeming` | guardar 200000 (`BRONZE`); resgatar 1000 | continua `BRONZE`, sem carência (GAM-19) |
| `test_repeated_request_returns_first_response` | o mesmo resgate duas vezes; outro resgate de 5000; o primeiro de novo | a mesma resposta 201 nas três vezes; saldos 65000 e 35000 (MOV-19) |
| `test_same_key_with_other_request_is_409` | a chave de um guardar num resgate; um resgate e a chave dele com outro valor | 409 `QIT001014`; 201; 409 `QIT001014`; saldos 60000 e 40000 |
| `test_unknown_category_is_404` | `category_key` aleatória; depois sem `category_key` | 404 `QIT001021`; 201 |
| `test_blocked_or_closed_account_refuses_redemption` | conta bloqueada; desbloqueada; outra conta encerrada | 409 `QIT001011` e nada muda; 201; 409 `QIT001011` (CLI-09) |
| `test_other_account_token_is_404` | começa com `DbUtils.rollback()`; A com o token de B; B com o de A; A com o de A | 404 `QIT001010` nos dois; 201 (R8) |
| `test_missing_or_wrong_token_is_404` | começa com `DbUtils.rollback()`; sem token; `token_errado`; key que não existe; o certo | 404 `QIT001010` nos três; 201 |
| `test_refuses_body_out_of_schema` | os mesmos nove corpos do teste do guardar | 400 `QIT000001` nos nove; saldos iguais |

**Verificar:**
- `./.venv/Scripts/python.exe -m pytest -v tests/integration/piggy_bank/test_redeem.py` → `12 passed`.
- L2 — o resgate sai do lote mais antigo (COF-06). Um comando, numa linha só; começa com `DbUtils.rollback()`:
  ```
  ./.venv/Scripts/python.exe -c "from sqlalchemy import create_engine, text; from tests.utils import DbUtils, ObjectGenerator, PayloadGenerator, RequestGenerator as R; DbUtils.rollback(); a = ObjectGenerator.create_funded_account(100000); k, t = a['account_key'], a['account_token']; print([R.POST_saving(k, t, PayloadGenerator.saving(amount=v))[0] for v in [30000, 20000]], R.POST_redemption(k, t, PayloadGenerator.redemption(amount=40000))[0]); e = create_engine(DbUtils.database_url()); c = e.connect(); q = text('SELECT principal_remaining, yield_remaining FROM lot ORDER BY id'); print([tuple(r) for r in c.execute(q).all()]); print(R.POST_redemption(k, t, PayloadGenerator.redemption(amount=5000))[0]); print([tuple(r) for r in c.execute(q).all()]); c.close(); e.dispose()"
  ```
  → exatamente:
  ```
  [201, 201] 201
  [(0, 0), (10000, 0)]
  201
  [(0, 0), (5000, 0)]
  ```
  Os 40000 zeram o lote de 30000 (o mais antigo) e tiram 10000 do de 20000; o resgate seguinte sai do único lote com dinheiro. Os lotes zerados continuam na tabela (R4).
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `292 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/app.py
  src/resources/piggy_bank.py
  tests/integration/piggy_bank/test_redeem.py
  ```
- `git log -1 --format=%B` → `feat(cofrinho): rota de resgatar`

**Pronto quando:**
- [ ] Os 12 testes falharam antes do código (item 4) e passam depois (item 8).
- [ ] A L2 dá as 4 linhas esperadas.
- [ ] Suíte com `292 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/07-cofrinho`.

**Commit:** `feat(cofrinho): rota de resgatar`
**Pare se:**
- O item 4 não terminar com `12 failed`.
- A linha citada na troca de `src/app.py` não for encontrada igual.
- Um teste receber 500 (`QIT000500`): rode `docker compose logs --tail 100 api` e traga a saída.
- A L2 der outra saída.
- A suíte não terminar com `292 passed`.

---
### Passo 7.7 — `GET /accounts/{account_key}/piggy_bank_entries`
**Branch:** fase/07-cofrinho · **Depende de:** 7.6
**Objetivo:** `EntryRepository.list_piggy_bank_page` (filtro opcional por categoria) e o nome novo `EntryRepository.get_counterparty_category`; o nome novo `CategoryRepository.get_by_id`; `PiggyBankController.list_piggy_bank_entries` e a rota `GET /accounts/{account_key}/piggy_bank_entries` (tokens: conta; schema `get_piggy_bank_entries.json`), no envelope do extrato; 404 `QIT001010`; 404 `QIT001021`; 400 `QIT000001`. As duas pontas de guardar e resgatar no extrato da conta e na consulta da operação (`PIGGY_BANK` e `ACCOUNT`), com a categoria de cada lançamento do cofrinho, e o bruto, o IOF, o IR e o líquido na consulta de um `REDEEM`.
**Decisões:** COF-05 — saldo e extrato do cofrinho por categoria · COF-08 — bruto e líquido · MOV-04 — envelope do extrato · MOV-14 — ordem do extrato · MOV-17 — outra ponta · MOV-18 — duas datas · DAD-07 — saldo em dois lugares · API-03 — schema fechado na query · R5 — o `id` nunca sai · R8 — outro dono → 404 · TST-01 — black box e TDD
**Arquivos:**
- `src/repositories/entry_repository.py` (editar): os dois métodos abaixo entram no fim da classe, nesta ordem, logo depois de `list_page`, com uma linha em branco antes de cada um. Os imports não mudam (`Category` já está no arquivo).

```python
    def list_piggy_bank_page(self, piggy_bank: Account, limit: int, offset: int, category: Category = None) -> list:
        """Uma página do extrato do cofrinho: pares (lançamento, operação), mais recente primeiro (COF-05, MOV-14).

        A mesma ordem do list_page (created_at decrescente; no empate, id
        decrescente) e a mesma linha a mais (limit + 1). Com `category`, só
        os lançamentos dessa categoria.
        """
        query = (
            self.session.query(Entry, Transaction)
            .join(Transaction, Transaction.id == Entry.transaction_id)
            .filter(Entry.account_id == piggy_bank.id)
        )

        if category is not None:
            query = query.filter(Entry.category_id == category.id)

        return query.order_by(Entry.created_at.desc(), Entry.id.desc()).limit(limit + 1).offset(offset).all()
```

```python
    def get_counterparty_category(self, entry: Entry) -> Category:
        """A categoria do outro lançamento da mesma operação: em guardar e resgatar, a do lançamento do cofrinho (MOV-17)."""
        return (
            self.session.query(Category)
            .join(Entry, Entry.category_id == Category.id)
            .filter(Entry.transaction_id == entry.transaction_id, Entry.id != entry.id)
            .first()
        )
```

- `src/repositories/category_repository.py` (editar): o método `get_by_id` abaixo entra no fim da classe, logo depois de `get_balance`, com uma linha em branco antes dele:

```python
    def get_by_id(self, category_id: int) -> Category:
        """A categoria com este id; None quando não existe. O id só circula por dentro: para fora sai a category_key (R5)."""
        return self.session.query(Category).filter(Category.id == category_id).first()
```

- `src/dtos/entry_dto.py` (editar): os dois métodos abaixo entram no fim da classe, nesta ordem, logo depois de `bank_counterparty`, com uma linha em branco antes de cada um. Os imports não mudam (`Category` já está no arquivo).

```python
    @staticmethod
    def piggy_bank_counterparty(category: Category) -> dict:
        """Em guardar e resgatar, na conta principal: o cofrinho e a categoria (MOV-17)."""
        return {
            "type": "PIGGY_BANK",
            "category_key": category.category_key,
            "name": category.name,
        }
```

```python
    @staticmethod
    def account_counterparty() -> dict:
        """Em guardar e resgatar, no cofrinho: a conta principal (MOV-17)."""
        return {"type": "ACCOUNT"}
```

- `src/controllers/piggy_bank_controller.py` (editar): três mudanças, e nada mais.
  1. A linha
     ```python
     from dtos import TransactionDTO
     ```
     vira
     ```python
     from dtos import EntryDTO, TransactionDTO
     ```
  2. O método `list_piggy_bank_entries` abaixo entra logo depois do método `get_redemption_amounts` e antes de `_take_from_lots`, com uma linha em branco antes dele:

```python
    def list_piggy_bank_entries(self, account_key: str, account_token: str, limit: int, offset: int, category_key: str = None) -> dict:
        """Uma página do extrato do cofrinho, só para o dono (COF-05, MOV-04, MOV-14). Não grava nada. As regras, nesta ordem:

        1. a conta é do dono do token (404 QIT001010, R8);
        2. com category_key, a categoria existe neste cofrinho (404
           QIT001021); nesta fase, só a "economias" (passo 9.6).

        Pede limit + 1 linhas ao repository: se veio a linha a mais, existe
        próxima página, e ela não entra na resposta.
        """
        account = self.get_owned_account(account_key, account_token)
        piggy_bank = self.account_repository.get_piggy_bank(account)

        category = None
        if category_key is not None:
            category = self._get_category(piggy_bank, category_key)

        rows = self.entry_repository.list_piggy_bank_page(piggy_bank, limit, offset, category)

        is_last_page = True
        if len(rows) > limit:
            is_last_page = False
            rows = rows[:-1]

        entries = []
        for entry, transaction in rows:
            entries.append(self._piggy_bank_entry_to_dict(entry, transaction))

        return {
            "entries_list_dto": entries,
            "is_last_page": is_last_page,
        }
```

  3. O método `_piggy_bank_entry_to_dict` abaixo entra no fim da classe, logo depois de `_balance_after`, com uma linha em branco antes dele:

```python
    def _piggy_bank_entry_to_dict(self, entry, transaction: Transaction) -> dict:
        """Um lançamento do cofrinho no formato do extrato, com a categoria dele e a outra ponta (MOV-17).

        No cofrinho só há dois tipos de lançamento: AMOUNT (guardar e
        resgatar), cuja outra ponta é a conta principal, e YIELD (rendimento,
        passo 7.12), cuja outra ponta é o banco.
        """
        category = self.category_repository.get_by_id(entry.category_id)

        counterparty = EntryDTO.account_counterparty()
        if entry.entry_type.enumerator != EntryType.AMOUNT:
            counterparty = EntryDTO.bank_counterparty()

        return EntryDTO.obj_to_dict(entry, transaction, counterparty, category)
```

- `src/controllers/transaction_controller.py` (editar): seis mudanças, e nada mais.
  1. A linha
     ```python
     from controllers.gamification_controller import GamificationController
     ```
     vira as duas linhas
     ```python
     from controllers.gamification_controller import GamificationController
     from controllers.piggy_bank_controller import PiggyBankController
     ```
  2. A linha
     ```python
     from repositories import AccountRepository, BankClockRepository, DepositRepository, EntryRepository, TransactionRepository
     ```
     vira
     ```python
     from repositories import AccountRepository, BankClockRepository, CategoryRepository, DepositRepository, EntryRepository, TransactionRepository
     ```
  3. A linha
     ```python
             self.gamification_controller = GamificationController()
     ```
     vira as três linhas
     ```python
             self.gamification_controller = GamificationController()
             self.category_repository = CategoryRepository(self.context)
             self.piggy_bank_controller = PiggyBankController()
     ```
  4. O método `get_transaction` inteiro (da linha `    def get_transaction(` até a linha `        return TransactionDTO.obj_to_dict(transaction, entries)` que o fecha) passa a ser:

```python
    def get_transaction(self, account_key: str, account_token: str, transaction_key: str) -> dict:
        """Uma operação, só para o dono, com os lançamentos da conta e do cofrinho dela. Não grava nada.

        1. a conta é do dono do token (404 QIT001010, R8);
        2. a operação existe e tem lançamento na conta ou no cofrinho dela
           (404 QIT001020): operação de outra conta responde como se não
           existisse (R8).

        Na operação REDEEM, a resposta traz também o bruto, o IOF, o IR e o
        líquido, como a resposta do resgate (COF-08).
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

        redemption_amounts = None
        if transaction.transaction_type.enumerator == TransactionType.REDEEM:
            redemption_amounts = self.piggy_bank_controller.get_redemption_amounts(transaction, piggy_bank)

        return TransactionDTO.obj_to_dict(transaction, entries, redemption_amounts)
```

  5. O método `_entry_to_dict` inteiro passa a ser:

```python
    def _entry_to_dict(self, entry: Entry, transaction: Transaction) -> dict:
        category = None
        if entry.category_id is not None:
            category = self.category_repository.get_by_id(entry.category_id)

        return EntryDTO.obj_to_dict(entry, transaction, self._counterparty(entry, transaction), category)
```

  6. O método `_counterparty` inteiro passa a ser:

```python
    def _counterparty(self, entry: Entry, transaction: Transaction) -> dict:
        """A outra ponta do lançamento (MOV-17), nesta ordem:

        1. tarifa, prêmio, rendimento, IOF e IR (tudo que não é AMOUNT): o banco;
        2. AMOUNT de transferência: o outro cliente, com o CPF mascarado;
        3. AMOUNT de depósito: quem depositou, com o documento mascarado;
        4. AMOUNT de guardar e de resgatar: no cofrinho (o lançamento tem
           categoria), a conta principal; na conta principal, o cofrinho e a
           categoria do outro lançamento da operação;
        5. o resto (saque): None.
        """
        if entry.entry_type.enumerator != EntryType.AMOUNT:
            return EntryDTO.bank_counterparty()

        transaction_type = transaction.transaction_type.enumerator

        if transaction_type == TransactionType.TRANSFER:
            return EntryDTO.customer_counterparty(self.entry_repository.get_transfer_counterparty_customer(entry))

        if transaction_type == TransactionType.DEPOSIT:
            return EntryDTO.depositor_counterparty(self.deposit_repository.get_by_transaction(transaction))

        if transaction_type in [TransactionType.SAVE, TransactionType.REDEEM]:
            if entry.category_id is not None:
                return EntryDTO.account_counterparty()

            return EntryDTO.piggy_bank_counterparty(self.entry_repository.get_counterparty_category(entry))

        return None
```

- `src/resources/piggy_bank.py` (editar): o conteúdo inteiro passa a ser:

```python
from fastapi import Request
from fastapi import status as http_status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from constants import ACCOUNT_TOKEN_HEADER
from controllers import PiggyBankController
from utils.schema_handler import SchemaHandler


# MOV-04: o extrato do cofrinho começa na página 0, com 10 itens, quando a query string não diz.
DEFAULT_LIMIT = 10
DEFAULT_PAGE = 0


class PiggyBankResource:
    """A porta HTTP do cofrinho: guardar, resgatar e o extrato do cofrinho.

    Sem regra de negócio, sem SQL e sem nada guardado no self (ARQ-02). O
    token da conta chega no cabeçalho ACCOUNT-TOKEN (API-16); quem o
    confere é o controller.
    """

    @SchemaHandler.validate("post_savings.json")
    def on_post_saving(self, account_key: str, payload: dict, request: Request) -> JSONResponse:
        controller = PiggyBankController()
        transaction = controller.save(account_key, request.headers.get(ACCOUNT_TOKEN_HEADER), payload)

        return JSONResponse(
            content=jsonable_encoder(transaction),
            status_code=http_status.HTTP_201_CREATED,
        )

    @SchemaHandler.validate("post_redemptions.json")
    def on_post_redemption(self, account_key: str, payload: dict, request: Request) -> JSONResponse:
        controller = PiggyBankController()
        transaction = controller.redeem(account_key, request.headers.get(ACCOUNT_TOKEN_HEADER), payload)

        return JSONResponse(
            content=jsonable_encoder(transaction),
            status_code=http_status.HTTP_201_CREATED,
        )

    @SchemaHandler.validate_query_params("get_piggy_bank_entries.json")
    def on_get_piggy_bank_entries(self, account_key: str, request: Request) -> JSONResponse:
        """Uma página do extrato do cofrinho. O schema get_piggy_bank_entries.json já garantiu limit, page e category_key."""
        controller = PiggyBankController()

        query_params = request.query_params
        limit = int(query_params.get("limit", DEFAULT_LIMIT))
        page = int(query_params.get("page", DEFAULT_PAGE))
        offset = page * limit

        entries_page = controller.list_piggy_bank_entries(
            account_key,
            request.headers.get(ACCOUNT_TOKEN_HEADER),
            limit,
            offset,
            query_params.get("category_key"),
        )

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
      application.add_api_route("/accounts/{account_key}/redemptions", piggy_bank_resource.on_post_redemption, methods=["POST"])
  ```
  vira as duas linhas
  ```python
      application.add_api_route("/accounts/{account_key}/redemptions", piggy_bank_resource.on_post_redemption, methods=["POST"])
      application.add_api_route("/accounts/{account_key}/piggy_bank_entries", piggy_bank_resource.on_get_piggy_bank_entries, methods=["GET"])
  ```

- `tests/integration/piggy_bank/test_piggy_bank_entries.py` (criar): o conteúdo inteiro é:

```python
"""Extrato do cofrinho e as duas pontas de guardar e resgatar (COF-05, COF-08, MOV-04, MOV-14, MOV-17, MOV-18, DAD-07, R5, R8).

GET /accounts/{account_key}/piggy_bank_entries: o extrato do cofrinho, no
envelope e na ordem do extrato da conta, com a categoria de cada
lançamento e a outra ponta (a conta principal). No extrato da conta e na
consulta da operação, a outra ponta de guardar e resgatar é o cofrinho e a
categoria. Os testes que erram o token começam com DbUtils.rollback()
(PRD-10).
"""

import re
from uuid import uuid4

from tests.utils import DbUtils, ObjectGenerator, PayloadGenerator, RequestGenerator


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


def piggy_bank_entries(account: dict, params: dict = None) -> dict:
    status, response = RequestGenerator.GET_piggy_bank_entries(account["account_key"], account["account_token"], params)
    assert status == 200, response

    return response


def account_entries(account: dict) -> dict:
    status, response = RequestGenerator.GET_entries(account["account_key"], account["account_token"])
    assert status == 200, response

    return response


def piggy_bank_balance_of(account: dict) -> int:
    status, response = RequestGenerator.GET_account(account["account_key"], account["account_token"])
    assert status == 200, response

    return response["piggy_bank_balance"]


def save(account: dict, amount: int, category_key: str = None) -> str:
    payload = PayloadGenerator.saving(amount=amount, category_key=category_key)
    status, response = RequestGenerator.POST_saving(account["account_key"], account["account_token"], payload)
    assert status == 201, response

    return response["transaction_key"]


def redeem(account: dict, amount: int, category_key: str = None) -> str:
    payload = PayloadGenerator.redemption(amount=amount, category_key=category_key)
    status, response = RequestGenerator.POST_redemption(account["account_key"], account["account_token"], payload)
    assert status == 201, response

    return response["transaction_key"]


def default_category_key(account: dict) -> str:
    """A key da "economias", lida no extrato do cofrinho (a rota das categorias nasce na fase 9). A conta já guardou."""
    return piggy_bank_entries(account)["data"][0]["category"]["category_key"]


class TestPiggyBankEntries:
    def test_empty_piggy_bank_statement(self):
        account = ObjectGenerator.create_account()

        status, response = RequestGenerator.GET_piggy_bank_entries(account["account_key"], account["account_token"])

        assert status == 200, response
        assert response == {"data": [], "limit": 10, "page": 0, "is_last_page": True}

    def test_shows_saving_and_redemption_on_both_sides(self):
        account = ObjectGenerator.create_funded_account(100000)
        saving_key = save(account, 30000)
        redemption_key = redeem(account, 10000)

        statement = piggy_bank_entries(account)
        assert_no_internal_id(statement)
        assert (statement["limit"], statement["page"], statement["is_last_page"]) == (10, 0, True)

        redemption_entry, saving_entry = statement["data"]
        category = saving_entry["category"]
        assert sorted(category) == ["category_key", "name"]
        assert category["name"] == "economias"
        assert len(category["category_key"]) == 36

        for entry in statement["data"]:
            assert sorted(entry) == ENTRY_FIELDS
            assert entry["entry_type"] == "AMOUNT"
            assert entry["category"] == category
            assert entry["counterparty"] == {"type": "ACCOUNT"}
            assert DATE.match(entry["accounting_date"])
            assert DATETIME.match(entry["created_at"])
            assert type(entry["amount"]) is int
            assert type(entry["balance_after"]) is int

        assert (redemption_entry["transaction_key"], redemption_entry["transaction_type"], redemption_entry["amount"], redemption_entry["balance_after"]) == (redemption_key, "REDEEM", -10000, 20000)
        assert (saving_entry["transaction_key"], saving_entry["transaction_type"], saving_entry["amount"], saving_entry["balance_after"]) == (saving_key, "SAVE", 30000, 30000)
        assert sum(entry["amount"] for entry in statement["data"]) == piggy_bank_balance_of(account) == 20000

        statement = account_entries(account)
        assert_no_internal_id(statement)
        piggy_bank_counterparty = {"type": "PIGGY_BANK", "category_key": category["category_key"], "name": "economias"}

        redemption_entry, saving_entry, deposit_entry = statement["data"]
        assert (redemption_entry["transaction_type"], redemption_entry["amount"], redemption_entry["balance_after"]) == ("REDEEM", 10000, 80000)
        assert (redemption_entry["category"], redemption_entry["counterparty"]) == (None, piggy_bank_counterparty)
        assert (saving_entry["transaction_type"], saving_entry["amount"], saving_entry["balance_after"]) == ("SAVE", -30000, 70000)
        assert (saving_entry["category"], saving_entry["counterparty"]) == (None, piggy_bank_counterparty)
        assert deposit_entry["transaction_type"] == "DEPOSIT"

    def test_pagination(self):
        account = ObjectGenerator.create_funded_account(100000)
        for amount in [100, 200, 300]:
            save(account, amount)

        first_page = piggy_bank_entries(account, {"limit": "2", "page": "0"})
        assert [entry["amount"] for entry in first_page["data"]] == [300, 200]
        assert (first_page["limit"], first_page["page"], first_page["is_last_page"]) == (2, 0, False)

        second_page = piggy_bank_entries(account, {"limit": "2", "page": "1"})
        assert [entry["amount"] for entry in second_page["data"]] == [100]
        assert (second_page["limit"], second_page["page"], second_page["is_last_page"]) == (2, 1, True)

    def test_filters_by_the_default_category(self):
        account = ObjectGenerator.create_funded_account(100000)
        save(account, 1000)
        save(account, 2000)

        filtered = piggy_bank_entries(account, {"category_key": default_category_key(account)})

        assert [entry["amount"] for entry in filtered["data"]] == [2000, 1000]
        assert filtered["is_last_page"] is True

    def test_unknown_category_is_404(self):
        account = ObjectGenerator.create_funded_account(10000)
        save(account, 1000)

        status, response = RequestGenerator.GET_piggy_bank_entries(account["account_key"], account["account_token"], {"category_key": str(uuid4())})
        assert status == 404, response
        assert response["code"] == "QIT001021"

        assert len(piggy_bank_entries(account)["data"]) == 1

    def test_saves_and_redeems_with_the_default_category_key(self):
        account = ObjectGenerator.create_funded_account(10000)
        save(account, 1000)
        category_key = default_category_key(account)

        save(account, 500, category_key)
        assert piggy_bank_balance_of(account) == 1500

        redeem(account, 700, category_key)
        assert piggy_bank_balance_of(account) == 800

        assert [entry["category"]["category_key"] for entry in piggy_bank_entries(account)["data"]] == [category_key, category_key, category_key]

    def test_gets_saving_and_redemption_transactions(self):
        account = ObjectGenerator.create_funded_account(100000)
        saving_key = save(account, 30000)
        redemption_key = redeem(account, 10000)
        category_key = default_category_key(account)
        category = {"category_key": category_key, "name": "economias"}
        piggy_bank_counterparty = {"type": "PIGGY_BANK", "category_key": category_key, "name": "economias"}

        status, saving = RequestGenerator.GET_transaction(account["account_key"], account["account_token"], saving_key)
        assert status == 200, saving
        assert_no_internal_id(saving)
        assert saving["type"] == "SAVE"
        assert "gross_amount" not in saving
        assert [(entry["amount"], entry["balance_after"], entry["category"], entry["counterparty"]) for entry in saving["entries"]] == [
            (-30000, 70000, None, piggy_bank_counterparty),
            (30000, 30000, category, {"type": "ACCOUNT"}),
        ]

        status, redemption = RequestGenerator.GET_transaction(account["account_key"], account["account_token"], redemption_key)
        assert status == 200, redemption
        assert_no_internal_id(redemption)
        assert redemption["type"] == "REDEEM"
        assert (redemption["gross_amount"], redemption["iof"], redemption["ir"], redemption["net_amount"]) == (10000, 0, 0, 10000)
        assert [(entry["amount"], entry["balance_after"], entry["category"], entry["counterparty"]) for entry in redemption["entries"]] == [
            (-10000, 20000, category, {"type": "ACCOUNT"}),
            (10000, 80000, None, piggy_bank_counterparty),
        ]

    def test_refuses_query_out_of_schema(self):
        account = ObjectGenerator.create_account()

        for params in [{"limit": "0"}, {"limit": "101"}, {"limit": "abc"}, {"page": "-1"}, {"category_key": "economias"}, {"size": "10"}]:
            status, response = RequestGenerator.GET_piggy_bank_entries(account["account_key"], account["account_token"], params)
            assert status == 400, (params, response)
            assert response["code"] == "QIT000001"

    def test_other_account_token_is_404(self):
        DbUtils.rollback()
        account_a = ObjectGenerator.create_account()
        account_b = ObjectGenerator.create_account()

        status, response = RequestGenerator.GET_piggy_bank_entries(account_a["account_key"], account_b["account_token"])
        assert status == 404, response
        assert response["code"] == "QIT001010"

        status, response = RequestGenerator.GET_piggy_bank_entries(account_b["account_key"], account_a["account_token"])
        assert status == 404, response
        assert response["code"] == "QIT001010"

        piggy_bank_entries(account_a)

    def test_missing_or_wrong_token_is_404(self):
        DbUtils.rollback()
        account = ObjectGenerator.create_account()

        for account_token in [None, "token_errado"]:
            status, response = RequestGenerator.GET_piggy_bank_entries(account["account_key"], account_token)
            assert status == 404, (account_token, response)
            assert response["code"] == "QIT001010"

        status, response = RequestGenerator.GET_piggy_bank_entries(str(uuid4()), account["account_token"])
        assert status == 404, response
        assert response["code"] == "QIT001010"

        piggy_bank_entries(account)
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/07-cofrinho`; `git log --oneline -n 3` mostra `feat(cofrinho): rota de resgatar`.
2. Crie `tests/integration/piggy_bank/test_piggy_bank_entries.py` com o conteúdo do campo **Arquivos**.
3. `docker compose up -d --build --wait`.
4. `./.venv/Scripts/python.exe -m pytest -v tests/integration/piggy_bank/test_piggy_bank_entries.py` → a última linha tem `10 failed` e não tem `passed`. Os 10 falham por asserção: o caminho `/accounts/{account_key}/piggy_bank_entries` responde 404 `QIT000404`, e a consulta do `SAVE` traz `counterparty` nulo.
5. Acrescente os dois métodos em `src/repositories/entry_repository.py`.
6. Acrescente `get_by_id` em `src/repositories/category_repository.py`.
7. Acrescente os dois métodos em `src/dtos/entry_dto.py`.
8. Faça as três mudanças em `src/controllers/piggy_bank_controller.py`.
9. Faça as seis mudanças em `src/controllers/transaction_controller.py`.
10. Edite `src/resources/piggy_bank.py` com o conteúdo do campo **Arquivos**.
11. Faça a troca em `src/app.py`.
12. `docker compose up -d --build --wait`.
13. `./.venv/Scripts/python.exe -m pytest -v tests/integration/piggy_bank/test_piggy_bank_entries.py` → a última linha tem `10 passed`.
14. `./.venv/Scripts/python.exe -m pytest -v tests/integration/transactions/test_get_transaction.py tests/integration/transactions/test_entries.py` → a última linha tem `passed` e não tem `failed` (a outra ponta das outras operações não mudou).
15. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `302 passed`.
16. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
17. Feche o passo (AGENTS.md, seção 7), um comando por vez:
    ```
    git add -- src/repositories/entry_repository.py src/repositories/category_repository.py src/dtos/entry_dto.py src/controllers/piggy_bank_controller.py src/controllers/transaction_controller.py src/resources/piggy_bank.py src/app.py tests/integration/piggy_bank/test_piggy_bank_entries.py
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "feat(cofrinho): extrato do cofrinho e as duas pontas de guardar e resgatar"
    git log -1 --format=%B
    ```

**Testes:** `tests/integration/piggy_bank/test_piggy_bank_entries.py`. As rotas só leem: nenhum efeito no banco além da linha de `request_log`.

| Função de teste | Entrada | Esperado |
|---|---|---|
| `test_empty_piggy_bank_statement` | conta nova | 200 e exatamente `{"data": [], "limit": 10, "page": 0, "is_last_page": true}` (MOV-04) |
| `test_shows_saving_and_redemption_on_both_sides` | conta com 100000; guardar 30000; resgatar 10000 | no cofrinho: `REDEEM` −10000 (saldo 20000) e `SAVE` +30000 (saldo 30000), os dois com os 10 campos, categoria `economias`, outra ponta `ACCOUNT` e as duas datas; a soma do extrato é o saldo do cofrinho (DAD-07); na conta: `REDEEM` +10000 (80000) e `SAVE` −30000 (70000), sem categoria, outra ponta `PIGGY_BANK` com a categoria; nenhum `id` (MOV-17, MOV-18, R5) |
| `test_pagination` | guardar 100, 200 e 300; `limit=2` nas páginas 0 e 1 | `[300, 200]` com `is_last_page` falso; `[100]` com verdadeiro (MOV-14) |
| `test_filters_by_the_default_category` | guardar 1000 e 2000; `category_key` da "economias" | `[2000, 1000]` (COF-05) |
| `test_unknown_category_is_404` | `category_key` aleatória; depois sem filtro | 404 `QIT001021`; 200 com 1 item |
| `test_saves_and_redeems_with_the_default_category_key` | guardar sem key; guardar 500 e resgatar 700 com a key da "economias" | cofrinho 1500 e 800; os três lançamentos com a mesma categoria (COF-03) |
| `test_gets_saving_and_redemption_transactions` | `GET .../transactions/{key}` do guardar e do resgate | `SAVE` sem `gross_amount`, lançamentos da conta (−30000, `PIGGY_BANK`) e do cofrinho (+30000, `ACCOUNT`, com categoria); `REDEEM` com bruto 10000, IOF 0, IR 0, líquido 10000 e os dois lançamentos na ordem de gravação (COF-08, MOV-17) |
| `test_refuses_query_out_of_schema` | `limit` 0, 101 e `abc`; `page` −1; `category_key` `economias`; parâmetro a mais | 400 `QIT000001` nos seis (API-03) |
| `test_other_account_token_is_404` | começa com `DbUtils.rollback()`; A com o token de B; B com o de A; A com o de A | 404 `QIT001010` nos dois; 200 (R8) |
| `test_missing_or_wrong_token_is_404` | começa com `DbUtils.rollback()`; sem token; `token_errado`; key que não existe; o certo | 404 `QIT001010` nos três; 200 |

**Verificar:**
- `./.venv/Scripts/python.exe -m pytest -v tests/integration/piggy_bank/test_piggy_bank_entries.py` → `10 passed`.
- `git grep -n "piggy_bank_resource" -- src/app.py` → exatamente 4 linhas: a do `piggy_bank_resource = PiggyBankResource()` e as três rotas do cofrinho.
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `302 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/app.py
  src/controllers/piggy_bank_controller.py
  src/controllers/transaction_controller.py
  src/dtos/entry_dto.py
  src/repositories/category_repository.py
  src/repositories/entry_repository.py
  src/resources/piggy_bank.py
  tests/integration/piggy_bank/test_piggy_bank_entries.py
  ```
- `git log -1 --format=%B` → `feat(cofrinho): extrato do cofrinho e as duas pontas de guardar e resgatar`

**Pronto quando:**
- [ ] Os 10 testes falharam antes do código (item 4) e passam depois (item 13).
- [ ] `test_get_transaction.py` e `test_entries.py` continuam verdes (item 14).
- [ ] Suíte com `302 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/07-cofrinho`.

**Commit:** `feat(cofrinho): extrato do cofrinho e as duas pontas de guardar e resgatar`
**Pare se:**
- O item 4 não terminar com `10 failed`.
- Alguma linha citada nas mudanças de `piggy_bank_controller.py`, `transaction_controller.py` ou `src/app.py` não for encontrada igual.
- `docker compose up -d --build --wait` falhar com `ImportError` ou `circular import` no `docker compose logs --tail 100 api`: traga a saída.
- Um teste de `test_get_transaction.py` ou `test_entries.py` ficar vermelho.
- A suíte não terminar com `302 passed`.

---
### Passo 7.8 — Connector do Banco Central
**Branch:** fase/07-cofrinho · **Depende de:** 7.7
**Objetivo:** `BcbConnector.get_cdi_rate(accounting_date)`: a taxa do dia em texto, `None` quando o dia não tem taxa, e `CdiUnavailable` (503 `QIT001031`) em timeout, erro de conexão ou resposta fora do formato; `BCB_API_URL` e `BCB_API_TIMEOUT` em `src/constants.py`; o connector de boletos e as constantes `BANKSLIP_*` saem do código.
**Decisões:** ARQ-07 — CDI por connector · COF-16 — dia sem taxa · COF-17 — CDI real, série 12 · COF-20 — Banco Central fora → 503 · PRD-01 — configuração no ambiente · PRD-03 — timeout no connector · ARQ-11 — pode apagar o que é do base
**Arquivos:**
- `src/connectors/bcb_connector.py` (criar): o conteúdo inteiro é:

```python
import re
from datetime import date

from requests.exceptions import RequestException

from connectors.rest_connector import RestConnector
from constants import BCB_API_TIMEOUT, BCB_API_URL
from errors import CdiUnavailable


# COF-17: o caminho da série 12 do SGS (CDI diário), o mesmo no Banco
# Central e no Mockserver que faz o papel dele (ARQ-07, ARQ-12).
CDI_SERIES_PATH = "/dados/serie/bcdata.sgs.12/dados"

# A taxa vem em texto, em % ao dia, com ponto decimal ("0.054266").
CDI_RATE_PATTERN = re.compile(r"^[0-9]+\.[0-9]+$")


class BcbConnector(RestConnector):
    """Fala com o Banco Central: a taxa do CDI de um dia (ARQ-07, COF-17).

    Quem responde é o Mockserver do compose, carregado com 10 anos de CDI
    real (ARQ-12). O endereço e o timeout vêm do ambiente (PRD-01, PRD-03).
    O Banco Central não pede token: internal_token None deixa o cabeçalho
    INTERNAL-TOKEN de fora (o requests descarta cabeçalho com valor None).
    """

    def __init__(self) -> None:
        super().__init__(
            class_name=__name__,
            base_url=BCB_API_URL,
            timeout=BCB_API_TIMEOUT,
            internal_token=None,
        )

    def get_cdi_rate(self, accounting_date: date) -> str:
        """A taxa do CDI do dia, em texto e em % ao dia ("0.054266"); None quando o dia não tem taxa (COF-16).

        Resposta esperada: 200 com uma lista JSON. Lista vazia: o dia não
        tem taxa (fim de semana ou feriado). Lista com um item {"data":
        "DD/MM/AAAA", "valor": "0.054266"} do mesmo dia: a taxa. Qualquer
        outra coisa (timeout, erro de conexão, outro status, outro corpo)
        levanta CdiUnavailable: 503 QIT001031, e a virada não grava nada
        (COF-20).
        """
        day = accounting_date.strftime("%d/%m/%Y")
        endpoint = f"{CDI_SERIES_PATH}?formato=json&dataInicial={day}&dataFinal={day}"

        try:
            response = self.send(endpoint=endpoint, method="GET")
        except RequestException:
            raise CdiUnavailable(accounting_date.isoformat()) from None

        if response.status != 200 or not isinstance(response.json, list) or len(response.json) > 1:
            raise CdiUnavailable(accounting_date.isoformat())

        if len(response.json) == 0:
            return None

        rate = response.json[0]

        if not isinstance(rate, dict) or rate.get("data") != day or not isinstance(rate.get("valor"), str):
            raise CdiUnavailable(accounting_date.isoformat())

        if CDI_RATE_PATTERN.fullmatch(rate["valor"]) is None:
            raise CdiUnavailable(accounting_date.isoformat())

        return rate["valor"]
```

- `src/connectors/__init__.py` (editar): o conteúdo inteiro passa a ser:

```python
from connectors.bcb_connector import BcbConnector
```

- `src/connectors/bankslip_connector.py` (apagar, com `git rm`).
- `src/constants.py` (editar): uma troca, e nada mais. O bloco de 12 linhas que começa em `# A API de boletos: o serviço de fora que este projeto chama pra emitir` e termina em `BANKSLIP_API_TIMEOUT = int(os.environ.get("BANKSLIP_API_TIMEOUT", "5"))` (os dois comentários e as três constantes `BANKSLIP_*`) vira exatamente:

```python
# ARQ-07, COF-17: o Banco Central, de onde vem a taxa do CDI (série 12 do
# SGS). Na entrega e nos testes, quem responde é o Mockserver do compose
# (ARQ-12): a API nunca fala com o Banco Central de verdade.
BCB_API_URL = os.environ.get("BCB_API_URL", "http://mockserver:1080")

# PRD-03, COF-20: quantos segundos esperar pela taxa antes de desistir.
# Passou, a virada responde 503 e o dia não avança.
BCB_API_TIMEOUT = int(os.environ.get("BCB_API_TIMEOUT", "5"))
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/07-cofrinho`; `git log --oneline -n 3` mostra `feat(cofrinho): extrato do cofrinho e as duas pontas de guardar e resgatar`.
2. `git grep -n -e "BankSlipConnector" -e "BANKSLIP_" -- src` → só linhas de `src/connectors/__init__.py`, `src/connectors/bankslip_connector.py` e `src/constants.py`.
3. Crie `src/connectors/bcb_connector.py` com o conteúdo do campo **Arquivos**.
4. Edite `src/connectors/__init__.py` com o conteúdo do campo **Arquivos**.
5. `git rm -- src/connectors/bankslip_connector.py`
6. Faça a troca em `src/constants.py`.
7. `docker compose up -d --build --wait` → termina sem erro.
8. Rode as conferências B1 e B2 do **Verificar**.
9. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `302 passed`.
10. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
11. Feche o passo (AGENTS.md, seção 7), um comando por vez:
    ```
    git add -- src/connectors/bcb_connector.py src/connectors/__init__.py src/constants.py
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "feat(cdi): connector do Banco Central"
    git log -1 --format=%B
    ```

**Testes:** nenhum teste novo. O connector só tem uso na virada (7.11), e o Mockserver só nasce no 7.10: os testes black box do 503 e do dia sem taxa entram no 7.11. Aqui, a prova são a B1 (sem Mockserver, a chamada vira `CdiUnavailable`, nunca uma exceção do `requests`) e a B2 (cada forma de resposta, com o `send` trocado por uma resposta de mentira).
**Verificar:**
- B1 (um comando, numa linha só; o código de saída 1 é o esperado):
  ```
  docker compose exec -T api python -c "from datetime import date; import constants as c; from connectors import BcbConnector; print(c.BCB_API_URL, c.BCB_API_TIMEOUT, hasattr(c, 'BANKSLIP_API_URL')); BcbConnector().get_cdi_rate(date(2026, 6, 1))"
  ```
  → a primeira linha é `http://mockserver:1080 5 False`; a saída termina com um `Traceback` cuja última linha começa com `errors.custom_errors.CdiUnavailable`. O serviço `mockserver` ainda não existe, e a falha de conexão vira o erro do catálogo.
- B2 (um comando, numa linha só):
  ```
  docker compose exec -T api python -c "from datetime import date; from types import SimpleNamespace as N; from connectors import BcbConnector; from errors import CdiUnavailable; b = BcbConnector(); d = date(2026, 6, 1); exec(chr(10).join(['def f(resp):', ' b.send = lambda endpoint, method: resp', ' try:', '  return b.get_cdi_rate(d)', ' except CdiUnavailable as e:', '  return e.code'])); print([f(N(status=200, json=x)) for x in [[{'data': '01/06/2026', 'valor': '0.054266'}], [], [{'data': '02/06/2026', 'valor': '0.054266'}], [{'data': '01/06/2026', 'valor': 0.054266}], [{'data': '01/06/2026', 'valor': '1,5'}], {'valor': '1'}, None]]); print(f(N(status=404, json=[])), f(N(status=200, json=[{'data': '01/06/2026', 'valor': '1.0'}, {'data': '01/06/2026', 'valor': '2.0'}])))"
  ```
  → exatamente:
  ```
  ['0.054266', None, 'QIT001031', 'QIT001031', 'QIT001031', 'QIT001031', 'QIT001031']
  QIT001031 QIT001031
  ```
  Em ordem: a taxa do dia; o dia sem taxa; taxa de outro dia; taxa em número; taxa com vírgula; corpo que não é lista; corpo vazio; status 404; dois itens.
- `git grep -n -e "BankSlipConnector" -e "BANKSLIP_" -- src` → nenhuma linha. A docstring herdada de `RestConnector` não é uma dependência executável.
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `302 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/connectors/__init__.py
  src/connectors/bankslip_connector.py
  src/connectors/bcb_connector.py
  src/constants.py
  ```
- `git log -1 --format=%B` → `feat(cdi): connector do Banco Central`

**Pronto quando:**
- [ ] `bcb_connector.py` e `connectors/__init__.py` têm exatamente o conteúdo do campo **Arquivos**; `bankslip_connector.py` saiu por `git rm`; `constants.py` tem só a troca do passo.
- [ ] B1 e B2 dão a saída esperada.
- [ ] Suíte com `302 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/07-cofrinho`.

**Commit:** `feat(cdi): connector do Banco Central`
**Pare se:**
- O item 2 mostrar `BankSlipConnector` ou `BANKSLIP_` em outro arquivo de `src/`.
- O bloco de 12 linhas citado na troca de `src/constants.py` não for encontrado igual.
- A B1 terminar com `requests.exceptions` na última linha em vez de `errors.custom_errors.CdiUnavailable`, ou a B2 der outra saída.
- A suíte não terminar com `302 passed`.

---

### Passo 7.9 — Script que baixa o CDI
**Branch:** fase/07-cofrinho · **Depende de:** 7.8
**Objetivo:** `scripts/download_cdi.py`: baixa a série 12 do SGS de 2016-10-01 a 2026-09-30 e grava `mockserver/cdi_expectations.json`, uma expectativa do Mockserver por dia de calendário (dia sem taxa responde a lista vazia). O agente escreve e confere o script sem rede; quem roda é o Bruno.
**Decisões:** ARQ-12 — Banco Central só no download · COF-17 — CDI real, série 12 · COF-16 — dia sem taxa · ARQ-07 — Mockserver no lugar do Banco Central
**Arquivos:**
- `scripts/download_cdi.py` (criar; a pasta `scripts/` é nova): o conteúdo inteiro é:

```python
"""Baixa o CDI diário do Banco Central e grava as respostas do Mockserver (ARQ-07, ARQ-12, COF-16, COF-17).

Roda uma vez, à mão, no desenvolvimento, e nunca na suíte nem no compose:
na entrega, o Mockserver já sobe com o arquivo gerado aqui, e nem a API
nem os testes falam com o Banco Central (ARQ-12).

Da raiz do repositório:

    ./.venv/Scripts/python.exe scripts/download_cdi.py

O que faz:
1. pede ao Banco Central a série 12 do SGS (CDI, em % ao dia) de
   START_DATE a END_DATE, numa chamada só (o SGS entrega até 10 anos);
2. confere cada linha: data dentro do período, sem repetição, taxa em
   texto com ponto decimal;
3. grava mockserver/cdi_expectations.json: uma expectativa do Mockserver
   por dia de calendário do período. Dia com taxa responde a lista com a
   taxa, como o Banco Central; dia sem taxa (fim de semana e feriado)
   responde a lista vazia (COF-16).

Depois, confira as três datas que o script mostra contra o site do Banco
Central antes do commit (ARQ-12).
"""

import json
import re
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path


SERIES_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados"

# O caminho que o BcbConnector chama no Mockserver: o mesmo do Banco Central.
CDI_SERIES_PATH = "/dados/serie/bcdata.sgs.12/dados"

# O período: 10 anos menos um dia, dentro do limite de uma chamada do SGS.
START_DATE = date(2016, 10, 1)
END_DATE = date(2026, 9, 30)

DOWNLOAD_TIMEOUT_SECONDS = 120
CDI_RATE_PATTERN = re.compile(r"^[0-9]+\.[0-9]+$")
OUTPUT_FILE = Path(__file__).resolve().parents[1] / "mockserver" / "cdi_expectations.json"

# As três datas que o script mostra no fim, para conferir no site do Banco Central.
CHECK_DATES = [date(2026, 6, 1), date(2026, 6, 2), date(2026, 6, 3)]


def brazilian_date(day: date) -> str:
    """2026-06-01 → "01/06/2026", o formato do SGS."""
    return day.strftime("%d/%m/%Y")


def download_rates() -> dict:
    """{data: taxa em texto} dos dias com taxa publicada no período."""
    query = f"?formato=json&dataInicial={brazilian_date(START_DATE)}&dataFinal={brazilian_date(END_DATE)}"
    request = urllib.request.Request(SERIES_URL + query, headers={"Accept": "application/json"})

    with urllib.request.urlopen(request, timeout=DOWNLOAD_TIMEOUT_SECONDS) as response:
        rows = json.loads(response.read().decode("utf-8"))

    rates = {}
    for row in rows:
        day = datetime.strptime(row["data"], "%d/%m/%Y").date()
        rate = row["valor"]

        if day < START_DATE or day > END_DATE:
            raise ValueError(f"o SGS mandou uma data fora do período: {row['data']}")

        if day in rates:
            raise ValueError(f"o SGS mandou a mesma data duas vezes: {row['data']}")

        if not isinstance(rate, str) or CDI_RATE_PATTERN.fullmatch(rate) is None:
            raise ValueError(f"taxa fora do formato em {row['data']}: {rate!r}")

        rates[day] = rate

    return rates


def build_expectation(day: date, rate: str) -> dict:
    """A expectativa do Mockserver para um dia: a lista com a taxa, ou a lista vazia quando rate é None."""
    body = []
    if rate is not None:
        body = [{"data": brazilian_date(day), "valor": rate}]

    return {
        "httpRequest": {
            "method": "GET",
            "path": CDI_SERIES_PATH,
            "queryStringParameters": {
                "formato": ["json"],
                "dataInicial": [brazilian_date(day)],
                "dataFinal": [brazilian_date(day)],
            },
        },
        "httpResponse": {
            "statusCode": 200,
            "headers": {"Content-Type": ["application/json"]},
            "body": json.dumps(body),
        },
        "times": {"unlimited": True},
    }


def main() -> None:
    rates = download_rates()

    expectations = []
    day = START_DATE
    while day <= END_DATE:
        expectations.append(build_expectation(day, rates.get(day)))
        day = day + timedelta(days=1)

    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8", newline="\n") as output:
        json.dump(expectations, output, ensure_ascii=True, indent=2)
        output.write("\n")

    print(f"{len(expectations)} dias, {len(rates)} com taxa, de {START_DATE.isoformat()} a {END_DATE.isoformat()}")
    for check_date in CHECK_DATES:
        print(check_date.isoformat(), rates.get(check_date))
    print(f"gravado em {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/07-cofrinho`; `git log --oneline -n 3` mostra `feat(cdi): connector do Banco Central`.
2. Crie `scripts/download_cdi.py` com o conteúdo do campo **Arquivos**.
3. Rode a conferência D1 do **Verificar**. Não rode o script: quem o roda, com rede, é o Bruno.
4. `docker compose up -d --build --wait` → termina sem erro.
5. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `302 passed`.
6. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
7. Feche o passo (AGENTS.md, seção 7), um comando por vez:
   ```
   git add -- scripts/download_cdi.py
   git diff --cached --name-only
   git diff --name-only
   git ls-files --others --exclude-standard
   git commit -m "chore(cdi): script que baixa o CDI do Banco Central"
   git log -1 --format=%B
   ```
8. PARE e responda `PASSO 7.9 CONCLUÍDO` com a saída de `git log -1 --oneline`. O 7.10 só começa depois do commit à mão do Bruno (cabeçalho deste plano).

**Testes:** nenhum teste novo. O script não é conta pura de `src/calculations/` nem rota (TST-05, TST-01) e nunca roda na suíte (ARQ-12). A prova é a D1: importa o script sem rodar o `main`, monta a expectativa de um dia com taxa e de um dia sem taxa e conta os dias do período.
**Verificar:**
- D1 (um comando, numa linha só):
  ```
  ./.venv/Scripts/python.exe -c "import sys, json; sys.path.insert(0, 'scripts'); import download_cdi as d; from datetime import date; print((d.END_DATE - d.START_DATE).days + 1, d.OUTPUT_FILE.parent.name, d.OUTPUT_FILE.name); e = d.build_expectation(date(2026, 6, 1), '0.054266'); print(json.dumps(e['httpRequest'], sort_keys=True)); print(e['httpResponse']['body'], d.build_expectation(date(2026, 6, 6), None)['httpResponse']['body'], e['times'])"
  ```
  → exatamente:
  ```
  3652 mockserver cdi_expectations.json
  {"method": "GET", "path": "/dados/serie/bcdata.sgs.12/dados", "queryStringParameters": {"dataFinal": ["01/06/2026"], "dataInicial": ["01/06/2026"], "formato": ["json"]}}
  [{"data": "01/06/2026", "valor": "0.054266"}] [] {'unlimited': True}
  ```
- `git ls-files --others --exclude-standard` (antes do `git add`) → exatamente `scripts/download_cdi.py` (a D1 não criou o arquivo de dados).
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `302 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente `scripts/download_cdi.py`.
- `git log -1 --format=%B` → `chore(cdi): script que baixa o CDI do Banco Central`

**Pronto quando:**
- [ ] `scripts/download_cdi.py` tem exatamente o conteúdo do campo **Arquivos**.
- [ ] A D1 dá as 3 linhas esperadas; `mockserver/` não existe.
- [ ] Suíte com `302 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/07-cofrinho`.

**Commit:** `chore(cdi): script que baixa o CDI do Banco Central`
**Pare se:**
- A D1 der outra saída, ou a pasta `mockserver/` aparecer depois dela.
- A suíte não terminar com `302 passed`.

Fim do passo: PARE (item 8). Depois do commit à mão do Bruno, o pedido seguinte é `Execute os passos 7.10 a 7.fim de docs/plano/PLANO-fase-07.md`.

---

### Passo 7.10 — Mockserver no compose
**Branch:** fase/07-cofrinho · **Depende de:** 7.9 e o commit à mão `chore(cdi): dados do CDI para o mockserver`
**Objetivo:** o serviço `mockserver` no compose (imagem de `mockserver/Dockerfile`, com `mockserver/cdi_expectations.json` dentro; porta `${MOCKSERVER_PORT:-1080}`); `BCB_API_URL` e `BCB_API_TIMEOUT` na API, com padrão; `BANKSLIP_*` saem do compose e do `.env.example`; `MockGenerator` (`set_cdi_rate`, `set_cdi_delay`, `clear_cdi`) para os testes programarem o Mockserver.
**Decisões:** ARQ-05 — serviço novo no compose · ARQ-06 — três peças · ARQ-07 — Mockserver no lugar do Banco Central · ARQ-08 — ambiente de entrega · ARQ-04 — sobe sem `.env` · ARQ-12 — o Mockserver sobe com os dados · PRD-01 — configuração no ambiente · TST-01 — o teste programa o Mockserver por `tests/utils/`
**Arquivos:**
- `mockserver/Dockerfile` (criar): o conteúdo inteiro é:

```dockerfile
# Imagem oficial e publica do Mockserver (ARQ-05, ARQ-07).
FROM mockserver/mockserver:5.15.0

# ARQ-12: as respostas do Banco Central (CDI diario, serie 12 do SGS), uma
# por dia de calendario, geradas por scripts/download_cdi.py. O Mockserver
# carrega o arquivo quando sobe.
COPY cdi_expectations.json /config/cdi_expectations.json
ENV MOCKSERVER_INITIALIZATION_JSON_PATH=/config/cdi_expectations.json
```

- `docker-compose.yml` (editar): o conteúdo inteiro passa a ser:

```yaml
# O docker compose sobe a aplicacao, o banco e o Mockserver juntos, com um
# comando so:
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
      # O Banco Central, de onde vem a taxa do CDI (ARQ-07). Dentro do
      # compose, quem responde e o Mockserver, pelo nome "mockserver".
      # BCB_API_TIMEOUT em segundos: passou, a virada responde 503 (COF-20).
      BCB_API_URL: ${BCB_API_URL:-http://mockserver:1080}
      BCB_API_TIMEOUT: ${BCB_API_TIMEOUT:-5}
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
      mockserver:
        condition: service_started

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

  mockserver:
    # ARQ-05, ARQ-07: o Mockserver faz o papel do Banco Central. A imagem
    # (mockserver/Dockerfile) ja traz os 10 anos de CDI real do arquivo
    # mockserver/cdi_expectations.json (ARQ-12): ninguem fala com o Banco
    # Central de verdade, nem na entrega nem nos testes. A imagem nao tem
    # shell, entao nao ha healthcheck: os testes esperam o Mockserver
    # responder (tests/utils/mock_generator.py).
    build: ./mockserver/.
    ports:
      # Os testes programam o Mockserver por esta porta. Se a 1080 estiver
      # ocupada: MOCKSERVER_PORT=1081 e MOCKSERVER_URL=http://127.0.0.1:1081
      # no seu .env.
      - "${MOCKSERVER_PORT:-1080}:1080"
```

- `.env.example` (editar): duas trocas, e nada mais.
  1. O bloco que começa na linha `# A API de boletos (o connector)` (com a linha de `─` logo acima dela) e termina na linha `BANKSLIP_API_TIMEOUT=5` vira exatamente:

```bash
# ─────────────────────────────────────────────────────────────
# O Banco Central (o connector do CDI)
#
# É o serviço de FORA de onde vem a taxa do CDI de cada dia — veja
# src/connectors/bcb_connector.py. Quem faz o papel dele é o Mockserver
# do compose, que já sobe com 10 anos de CDI real: nem a API nem os
# testes falam com o Banco Central de verdade.
# ─────────────────────────────────────────────────────────────

# Onde o Banco Central atende, visto de DENTRO do container da API.
BCB_API_URL=http://mockserver:1080

# Quantos segundos esperar pela taxa antes de desistir: passou, a virada
# do dia responde 503 e o dia não avança.
BCB_API_TIMEOUT=5

# Onde os testes programam o Mockserver, quando rodados fora do Docker.
MOCKSERVER_URL=http://127.0.0.1:1080
```

  2. As duas linhas
     ```bash
     # Em qual porta da SUA máquina a API vai atender (http://localhost:3000).
     #API_PORT=3001
     ```
     viram as cinco linhas
     ```bash
     # Em qual porta da SUA máquina a API vai atender (http://localhost:3000).
     #API_PORT=3001

     # Em qual porta da SUA máquina o Mockserver vai atender. Mude junto o MOCKSERVER_URL.
     #MOCKSERVER_PORT=1081
     ```

- `tests/utils/mock_generator.py` (criar): o conteúdo inteiro é:

```python
"""Programa o Mockserver, que faz o papel do Banco Central nos testes (ARQ-05, ARQ-07, TST-01).

O Mockserver sobe com 10 anos de CDI real (mockserver/cdi_expectations.json).
Cada teste que fecha um dia programa a taxa desse dia por aqui: a
expectativa do teste tem prioridade maior que a do arquivo e um id fixo
por data, e programar a mesma data de novo troca a anterior.
"""

import json
import time
from os import environ

from requests import request
from requests.exceptions import ConnectionError as RequestsConnectionError, Timeout as RequestsTimeout


MOCKSERVER_URL = environ.get("MOCKSERVER_URL", "http://127.0.0.1:1080")

# O mesmo caminho que o BcbConnector chama (COF-17).
CDI_SERIES_PATH = "/dados/serie/bcdata.sgs.12/dados"

# As expectativas do arquivo têm prioridade 0: a do teste ganha.
TEST_PRIORITY = 10

# Limite de espera real, incluindo o tempo das chamadas HTTP.
READY_TIMEOUT_SECONDS = 60
REQUEST_TIMEOUT_SECONDS = 10

MOCKSERVER_OFFLINE = (
    "Não consegui falar com o Mockserver em {base_url}.\n"
    "Ele precisa estar de pé pros testes da virada. Suba com:  docker compose up -d --build --wait"
)


def _brazilian_date(accounting_date: str) -> str:
    """"2026-06-01" → "01/06/2026", o formato da série do Banco Central."""
    year, month, day = accounting_date.split("-")

    return f"{day}/{month}/{year}"


def _expectation_id(accounting_date: str) -> str:
    return f"cdi-test-{accounting_date}"


def _send(path: str, payload: dict):
    """PUT no Mockserver; espera ele subir, uma tentativa por segundo."""
    deadline = time.monotonic() + READY_TIMEOUT_SECONDS
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        try:
            return request("PUT", f"{MOCKSERVER_URL}{path}", json=payload, timeout=min(REQUEST_TIMEOUT_SECONDS, remaining))
        except (RequestsConnectionError, RequestsTimeout):
            remaining = deadline - time.monotonic()
            if remaining > 0:
                time.sleep(min(1, remaining))

    raise RuntimeError(MOCKSERVER_OFFLINE.format(base_url=MOCKSERVER_URL))


def _put_expectation(accounting_date: str, body: list, delay_seconds: int = None) -> None:
    day = _brazilian_date(accounting_date)

    http_response = {
        "statusCode": 200,
        "headers": {"Content-Type": ["application/json"]},
        "body": json.dumps(body),
    }

    if delay_seconds is not None:
        http_response["delay"] = {"timeUnit": "SECONDS", "value": delay_seconds}

    expectation = {
        "id": _expectation_id(accounting_date),
        "priority": TEST_PRIORITY,
        "httpRequest": {
            "method": "GET",
            "path": CDI_SERIES_PATH,
            "queryStringParameters": {
                "formato": ["json"],
                "dataInicial": [day],
                "dataFinal": [day],
            },
        },
        "httpResponse": http_response,
        "times": {"unlimited": True},
    }

    response = _send("/mockserver/expectation", expectation)
    assert response.status_code == 201, response.text


class MockGenerator:
    """Um método por situação do Banco Central que os testes da virada precisam (COF-16, COF-17, COF-20)."""

    @staticmethod
    def set_cdi_rate(accounting_date: str, cdi_rate: str = None) -> None:
        """A taxa do CDI do dia (AAAA-MM-DD), em texto e em % ao dia ("0.054266"). None: o dia não tem taxa (COF-16)."""
        body = []
        if cdi_rate is not None:
            body = [{"data": _brazilian_date(accounting_date), "valor": cdi_rate}]

        _put_expectation(accounting_date, body)

    @staticmethod
    def set_cdi_delay(accounting_date: str, delay_seconds: int, cdi_rate: str = "0.054266") -> None:
        """A taxa do dia chega só depois de delay_seconds: acima do BCB_API_TIMEOUT (5), a API desiste (COF-20)."""
        body = [{"data": _brazilian_date(accounting_date), "valor": cdi_rate}]

        _put_expectation(accounting_date, body, delay_seconds)

    @staticmethod
    def clear_cdi(accounting_date: str) -> None:
        """Apaga a expectativa do teste para a data: volta a valer a do arquivo."""
        response = _send("/mockserver/clear?type=EXPECTATIONS", {"id": _expectation_id(accounting_date)})
        assert response.status_code == 200, response.text
```

- `tests/utils/__init__.py` (editar): o conteúdo inteiro passa a ser:

```python
from tests.utils.db_utils import DbUtils
from tests.utils.random_generator import RandomGenerator
from tests.utils.payload_generator import PayloadGenerator
from tests.utils.request_generator import RequestGenerator, INTERNAL_TOKEN, ADMIN_TOKEN
from tests.utils.object_generator import ObjectGenerator
from tests.utils.mock_generator import MockGenerator
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/07-cofrinho`.
2. `git log --oneline -n 3` → mostra `chore(cdi): dados do CDI para o mockserver` e `chore(cdi): script que baixa o CDI do Banco Central`; `git ls-files mockserver` → exatamente `mockserver/cdi_expectations.json`.
3. Crie `mockserver/Dockerfile` com o conteúdo do campo **Arquivos**.
4. Edite `docker-compose.yml` com o conteúdo do campo **Arquivos**.
5. Faça as duas trocas em `.env.example`.
6. Crie `tests/utils/mock_generator.py` com o conteúdo do campo **Arquivos**.
7. Edite `tests/utils/__init__.py` com o conteúdo do campo **Arquivos**.
8. `docker compose up -d --build --wait` → termina sem erro (a primeira vez baixa a imagem do Mockserver).
9. `docker compose ps` → três serviços: `api` (healthy), `db` (healthy) e `mockserver` (running).
10. Rode as conferências M1 e M2 do **Verificar**.
11. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `302 passed`.
12. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
13. Feche o passo (AGENTS.md, seção 7), um comando por vez:
    ```
    git add -- mockserver/Dockerfile docker-compose.yml .env.example tests/utils/mock_generator.py tests/utils/__init__.py
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "feat(cdi): Mockserver no compose e MockGenerator nos testes"
    git log -1 --format=%B
    ```

**Testes:** nenhum teste novo. O `MockGenerator` é ferramenta de teste e ganha uso nos testes da virada (7.11 a 7.14). A prova são a M1 (os dados do arquivo respondem; o teste troca a taxa de um dia, tira a taxa e volta ao arquivo) e a M2 (a API, de dentro do compose, recebe a taxa pelo connector).
**Verificar:**
- M1 (um comando, numa linha só):
  ```
  ./.venv/Scripts/python.exe -c "import requests; from tests.utils import MockGenerator; from tests.utils.mock_generator import CDI_SERIES_PATH, MOCKSERVER_URL; g = lambda d: requests.get(MOCKSERVER_URL + CDI_SERIES_PATH, params={'formato': 'json', 'dataInicial': d, 'dataFinal': d}, timeout=10); MockGenerator.clear_cdi('2026-06-01'); r = g('01/06/2026'); print(r.status_code, len(r.json()), r.json()[0]['data'], g('06/06/2026').json()); MockGenerator.set_cdi_rate('2026-06-01', '9.999999'); print(g('01/06/2026').json()); MockGenerator.set_cdi_rate('2026-06-01'); print(g('01/06/2026').json()); MockGenerator.clear_cdi('2026-06-01'); print(g('01/06/2026').json()[0]['valor'] != '9.999999', g('01/10/2026').status_code)"
  ```
  → exatamente:
  ```
  200 1 01/06/2026 []
  [{'data': '01/06/2026', 'valor': '9.999999'}]
  []
  True 404
  ```
  Linha a linha: 01/06/2026 (segunda-feira) tem a taxa real do arquivo, e 06/06/2026 (sábado) responde a lista vazia; o teste troca a taxa; o teste tira a taxa; o `clear_cdi` volta à taxa do arquivo; uma data depois do período do arquivo não tem expectativa (404).
- M2 (um comando, numa linha só):
  ```
  docker compose exec -T api python -c "from datetime import date; from connectors import BcbConnector; b = BcbConnector(); r = b.get_cdi_rate(date(2026, 6, 1)); print(type(r).__name__, r is not None, b.get_cdi_rate(date(2026, 6, 6)))"
  ```
  → exatamente `str True None`.
- `git grep -n -e "BankSlipConnector" -e "BANKSLIP_" -- src .env.example docker-compose.yml tests/utils` → nenhuma linha. Não buscar documentação histórica e planos.
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `302 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  .env.example
  docker-compose.yml
  mockserver/Dockerfile
  tests/utils/__init__.py
  tests/utils/mock_generator.py
  ```
- `git log -1 --format=%B` → `feat(cdi): Mockserver no compose e MockGenerator nos testes`

**Pronto quando:**
- [ ] `mockserver/Dockerfile`, `docker-compose.yml`, `mock_generator.py` e `tests/utils/__init__.py` têm exatamente o conteúdo do campo **Arquivos**; `.env.example` tem só as duas trocas.
- [ ] Os três serviços sobem com `docker compose up -d --build --wait`, sem `.env`.
- [ ] M1 e M2 dão a saída esperada.
- [ ] Suíte com `302 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/07-cofrinho`.

**Commit:** `feat(cdi): Mockserver no compose e MockGenerator nos testes`
**Pare se:**
- O item 2 não mostrar as duas mensagens ou o arquivo `mockserver/cdi_expectations.json`: o commit à mão do Bruno ainda não aconteceu.
- `docker compose up -d --build --wait` falhar: rode `docker compose logs --tail 100 mockserver` e `docker compose logs --tail 100 api` e traga as duas saídas.
- Aparecer `port is already allocated` na porta 1080.
- A M1 terminar com `AssertionError` (o Mockserver recusou o `PUT /mockserver/expectation` ou o `PUT /mockserver/clear`) ou com `RuntimeError` (não respondeu em 60 s): traga a saída e `docker compose logs --tail 100 mockserver`.
- A M1 ou a M2 derem outra saída.
- O bloco citado na troca 1 do `.env.example` não for encontrado igual.
- A suíte não terminar com `302 passed`.

---
### Passo 7.11 — Virada do dia: data, CDI e relógio
**Branch:** fase/07-cofrinho · **Depende de:** 7.10
**Objetivo:** `DayClosingController.close_day` e a rota `POST /internal/day_closings` (tokens: admin; schema `post_day_closings.json`): data igual ao relógio → pede a taxa e avança um dia, 200 com `{"closed_date", "accounting_date"}`; data que não existe → 422 `QIT001030`; já fechada → 409 `QIT001028`; no futuro → 422 `QIT001029`; Banco Central fora → 503 `QIT001031` e o dia não avança.
**Decisões:** DIA-01 — relógio do banco · DIA-02 — virada por rota, fechar duas vezes não paga duas vezes · DIA-03 — uma transação só · DIA-05 — data da virada · COF-16 — dia sem taxa · COF-20 — Banco Central fora → 503 · CLI-08 — o bloqueio automático continua depois da virada · API-13 — rota `/internal` · PRD-07, PRD-13 — token de administração · API-03 — schema fechado · TST-01 — black box e TDD
**Arquivos:**
- `src/controllers/day_closing_controller.py` (criar): o conteúdo inteiro é:

```python
from datetime import date

from connectors import BcbConnector
from controllers.base_controller import BaseController
from errors import DayAlreadyClosed, FutureAccountingDate, InvalidAccountingDate
from repositories import BankClockRepository


class DayClosingController(BaseController):
    """A virada do dia (DIA-01 a DIA-05): uma transação só, tudo ou nada.

    Ordem (DIA-03): pede a taxa do CDI → rendimento por lote (7.12) → XP
    de recorde (7.13) → ranques e carência, e o ranque que rende amanhã
    (7.14) → avança a data.
    """

    def __init__(self) -> None:
        super().__init__(__name__)
        self.bank_clock_repository = BankClockRepository(self.context)
        self.bcb_connector = BcbConnector()

    def close_day(self, day_closing_data: dict) -> dict:
        """Fecha o dia do relógio do banco. As regras, nesta ordem:

        1. a data existe no calendário (422 QIT001030);
        2. trava o relógio (SELECT ... FOR UPDATE): as operações em
           andamento terminam antes, e as novas esperam a virada;
        3. a data não é anterior ao relógio (409 QIT001028): fechar o mesmo
           dia duas vezes não paga duas vezes (DIA-02);
        4. a data não é posterior ao relógio (422 QIT001029);
        5. o Banco Central responde a taxa do dia (503 QIT001031, COF-20):
           a exceção desfaz tudo, e o dia não avança; dia sem taxa segue,
           sem rendimento (COF-16).

        Depois: avança o relógio um dia de calendário e faz o commit. A
        resposta traz o dia fechado e o novo dia do relógio.
        """
        accounting_date = day_closing_data["accounting_date"]
        closing_date = self._parse_accounting_date(accounting_date)
        bank_clock = self.bank_clock_repository.lock()

        if closing_date < bank_clock.accounting_date:
            raise DayAlreadyClosed(accounting_date)

        if closing_date > bank_clock.accounting_date:
            raise FutureAccountingDate(accounting_date, bank_clock.accounting_date.isoformat())

        self.bcb_connector.get_cdi_rate(closing_date)

        new_date = self.bank_clock_repository.advance(bank_clock)
        self.logger.info("day_closing_ready_to_commit accounting_date=%s", closing_date)
        self.session.commit()

        return {
            "closed_date": closing_date.isoformat(),
            "accounting_date": new_date.isoformat(),
        }

    def _parse_accounting_date(self, accounting_date: str) -> date:
        """A data do corpo como date. O schema já garantiu o formato AAAA-MM-DD; data que não existe (2026-02-30) → 422 QIT001030."""
        try:
            return date.fromisoformat(accounting_date)
        except ValueError:
            raise InvalidAccountingDate(accounting_date) from None
```

- `src/controllers/__init__.py` (editar): o conteúdo inteiro passa a ser:

```python
from controllers.customer_controller import CustomerController
from controllers.account_controller import AccountController
from controllers.transaction_controller import TransactionController
from controllers.gamification_controller import GamificationController
from controllers.piggy_bank_controller import PiggyBankController
from controllers.day_closing_controller import DayClosingController
```

- `src/resources/internal.py` (editar): o conteúdo inteiro passa a ser:

```python
from fastapi import Response
from fastapi import status as http_status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from controllers import AccountController, DayClosingController
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

    @SchemaHandler.validate("post_day_closings.json")
    def on_post_day_closing(self, payload: dict) -> JSONResponse:
        controller = DayClosingController()
        day_closing = controller.close_day(payload)

        return JSONResponse(
            content=jsonable_encoder(day_closing),
            status_code=http_status.HTTP_200_OK,
        )
```

- `src/app.py` (editar): uma troca, e nada mais. A linha
  ```python
      application.add_api_route("/internal/accounts/{account_key}/unblocks", internal_resource.on_post_unblock, methods=["POST"])
  ```
  vira as duas linhas
  ```python
      application.add_api_route("/internal/accounts/{account_key}/unblocks", internal_resource.on_post_unblock, methods=["POST"])
      application.add_api_route("/internal/day_closings", internal_resource.on_post_day_closing, methods=["POST"])
  ```
  O bloco das rotas fica exatamente assim (de `health_check_resource = HealthCheckResource()` até `register_error_handlers(application)`):
  ```python
      health_check_resource = HealthCheckResource()
      customer_resource = CustomerResource()
      account_resource = AccountResource()
      internal_resource = InternalResource()
      transaction_resource = TransactionResource()
      gamification_resource = GamificationResource()
      piggy_bank_resource = PiggyBankResource()

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
      application.add_api_route("/accounts/{account_key}/withdrawals", transaction_resource.on_post_withdrawal, methods=["POST"])
      application.add_api_route("/accounts/{account_key}/transfers", transaction_resource.on_post_transfer, methods=["POST"])
      application.add_api_route("/accounts/{account_key}/transactions/{transaction_key}", transaction_resource.on_get_transaction, methods=["GET"])
      application.add_api_route("/accounts/{account_key}/entries", transaction_resource.on_get_entries, methods=["GET"])

      # Gamificação
      application.add_api_route("/accounts/{account_key}/gamification", gamification_resource.on_get, methods=["GET"])
      application.add_api_route("/accounts/{account_key}/point_applications", gamification_resource.on_post_point_application, methods=["POST"])
      application.add_api_route("/accounts/{account_key}/point_resets", gamification_resource.on_post_point_reset, methods=["POST"])

      # Cofrinho
      application.add_api_route("/accounts/{account_key}/savings", piggy_bank_resource.on_post_saving, methods=["POST"])
      application.add_api_route("/accounts/{account_key}/redemptions", piggy_bank_resource.on_post_redemption, methods=["POST"])
      application.add_api_route("/accounts/{account_key}/piggy_bank_entries", piggy_bank_resource.on_get_piggy_bank_entries, methods=["GET"])

      # Rotas internas (API-13): INTERNAL-TOKEN e ADMIN-TOKEN
      application.add_api_route("/internal/accounts/{account_key}/blocks", internal_resource.on_post_block, methods=["POST"])
      application.add_api_route("/internal/accounts/{account_key}/unblocks", internal_resource.on_post_unblock, methods=["POST"])
      application.add_api_route("/internal/day_closings", internal_resource.on_post_day_closing, methods=["POST"])

      register_error_handlers(application)
  ```

- `tests/integration/internal/test_day_closing.py` (criar): o conteúdo inteiro é:

```python
"""Virada do dia: POST /internal/day_closings (DIA-01, DIA-02, DIA-05, COF-16, COF-20, CLI-08, PRD-13).

O relógio do banco é um só para a suíte: todo teste daqui começa com
DbUtils.rollback(), que o põe de volta em 2026-06-01 (DIA-04), e programa
no Mockserver a taxa de cada dia que fecha (MockGenerator). O dia do
relógio é lido por fora: a data contábil de um depósito feito agora.
"""

from tests.utils import DbUtils, MockGenerator, ObjectGenerator, PayloadGenerator, RequestGenerator


CDI = "0.054266"


def close_day(accounting_date: str) -> tuple:
    return RequestGenerator.POST_day_closing(PayloadGenerator.day_closing(accounting_date))


def bank_date() -> str:
    """O dia do relógio do banco, visto por fora: a data contábil de um depósito feito agora (DIA-01, DAD-17)."""
    account = ObjectGenerator.create_account()

    status, response = RequestGenerator.POST_deposit(account["account_key"], PayloadGenerator.deposit(amount=100))
    assert status == 201, response

    status, response = RequestGenerator.GET_transaction(account["account_key"], account["account_token"], response["transaction_key"])
    assert status == 200, response

    return response["accounting_date"]


def account_status(account: dict) -> str:
    status, response = RequestGenerator.GET_account(account["account_key"], account["account_token"])
    assert status == 200, response

    return response["status"]


def transfer(origin: dict, destination: dict, amount: int) -> tuple:
    payload = PayloadGenerator.transfer(destination["account_key"], amount=amount)

    return RequestGenerator.POST_transfer(origin["account_key"], origin["account_token"], payload)


class TestDayClosing:
    def test_closes_the_day_and_advances_the_clock(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate("2026-06-01", CDI)
        assert bank_date() == "2026-06-01"

        status, response = close_day("2026-06-01")

        assert status == 200, response
        assert response == {"closed_date": "2026-06-01", "accounting_date": "2026-06-02"}
        assert bank_date() == "2026-06-02"
        MockGenerator.clear_cdi("2026-06-01")

    def test_same_day_twice_is_409(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate("2026-06-01", CDI)
        MockGenerator.set_cdi_rate("2026-06-02", CDI)

        status, response = close_day("2026-06-01")
        assert status == 200, response

        status, response = close_day("2026-06-01")
        assert status == 409, response
        assert response["code"] == "QIT001028"
        assert bank_date() == "2026-06-02"

        status, response = close_day("2026-06-02")
        assert status == 200, response
        assert response == {"closed_date": "2026-06-02", "accounting_date": "2026-06-03"}
        MockGenerator.clear_cdi("2026-06-01")
        MockGenerator.clear_cdi("2026-06-02")

    def test_future_date_is_422(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate("2026-06-01", CDI)

        status, response = close_day("2026-06-02")
        assert status == 422, response
        assert response["code"] == "QIT001029"
        assert bank_date() == "2026-06-01"

        status, response = close_day("2026-06-01")
        assert status == 200, response
        MockGenerator.clear_cdi("2026-06-01")

    def test_impossible_date_is_422(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate("2026-06-01", CDI)

        for accounting_date in ["2026-02-30", "2026-13-01"]:
            status, response = close_day(accounting_date)
            assert status == 422, (accounting_date, response)
            assert response["code"] == "QIT001030"

        assert bank_date() == "2026-06-01"

        status, response = close_day("2026-06-01")
        assert status == 200, response
        MockGenerator.clear_cdi("2026-06-01")

    def test_day_without_cdi_rate_still_closes(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate("2026-06-01")

        status, response = close_day("2026-06-01")

        assert status == 200, response
        assert response == {"closed_date": "2026-06-01", "accounting_date": "2026-06-02"}
        MockGenerator.clear_cdi("2026-06-01")

    def test_central_bank_down_is_503_and_the_day_does_not_advance(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_delay("2026-06-01", 7)

        status, response = close_day("2026-06-01")
        assert status == 503, response
        assert response["code"] == "QIT001031"
        assert bank_date() == "2026-06-01"

        MockGenerator.set_cdi_rate("2026-06-01", CDI)
        status, response = close_day("2026-06-01")
        assert status == 200, response
        assert response == {"closed_date": "2026-06-01", "accounting_date": "2026-06-02"}
        MockGenerator.clear_cdi("2026-06-01")

    def test_automatically_blocked_account_stays_blocked(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate("2026-06-01", CDI)
        origin = ObjectGenerator.create_funded_account(100000)
        destination = ObjectGenerator.create_account()

        for _ in range(10):
            status, response = transfer(origin, destination, 100)
            assert status == 201, response

        status, response = transfer(origin, destination, 100)
        assert status == 422, response
        assert response["code"] == "QIT001019"
        assert account_status(origin) == "BLOCKED"

        status, response = close_day("2026-06-01")
        assert status == 200, response
        assert account_status(origin) == "BLOCKED"

        status, response = transfer(origin, destination, 100)
        assert status == 409, response
        assert response["code"] == "QIT001011"

        status, response = RequestGenerator.POST_unblock(origin["account_key"])
        assert status == 204, response

        status, response = transfer(origin, destination, 100)
        assert status == 201, response
        MockGenerator.clear_cdi("2026-06-01")

    def test_refuses_body_out_of_schema(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate("2026-06-01", CDI)
        payloads = [
            {},
            {"accounting_date": "2026-6-1"},
            {"accounting_date": 20260601},
            {"accounting_date": "2026-06-01", "extra": 1},
        ]

        for payload in payloads:
            status, response = RequestGenerator.POST_day_closing(payload)
            assert status == 400, (payload, response)
            assert response["code"] == "QIT000001"

        status, response = close_day("2026-06-01")
        assert status == 200, response
        MockGenerator.clear_cdi("2026-06-01")

    def test_requires_admin_token(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate("2026-06-01", CDI)
        MockGenerator.set_cdi_rate("2026-06-02", CDI)

        status, response = close_day("2026-06-01")
        assert status == 200, response

        for admin_token in [None, "token_errado"]:
            status, response = RequestGenerator.POST_day_closing(PayloadGenerator.day_closing("2026-06-02"), admin_token=admin_token)
            assert status == 403, (admin_token, response)
            assert response["code"] == "QIT000003"

        status, response = RequestGenerator.POST_day_closing(PayloadGenerator.day_closing("2026-06-02"), internal_token=None)
        assert status == 403, response
        assert response["code"] == "QIT000002"

        assert bank_date() == "2026-06-02"
        MockGenerator.clear_cdi("2026-06-01")
        MockGenerator.clear_cdi("2026-06-02")
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/07-cofrinho`; `git log --oneline -n 3` mostra `feat(cdi): Mockserver no compose e MockGenerator nos testes`.
2. Crie `tests/integration/internal/test_day_closing.py` com o conteúdo do campo **Arquivos**.
3. `docker compose up -d --build --wait`.
4. `./.venv/Scripts/python.exe -m pytest -v tests/integration/internal/test_day_closing.py` → a última linha tem `9 failed` e não tem `passed`. Os 9 falham por asserção: hoje o caminho `/internal/day_closings` responde 404 `QIT000404` com os dois tokens certos.
5. Crie `src/controllers/day_closing_controller.py` com o conteúdo do campo **Arquivos**.
6. Edite `src/controllers/__init__.py` com o conteúdo do campo **Arquivos**.
7. Edite `src/resources/internal.py` com o conteúdo do campo **Arquivos**.
8. Faça a troca em `src/app.py` e confira o bloco das rotas contra o do campo **Arquivos**.
9. `docker compose up -d --build --wait`.
10. `./.venv/Scripts/python.exe -m pytest -v tests/integration/internal/test_day_closing.py` → a última linha tem `9 passed` (o teste do 503 espera os 5 s do timeout).
11. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `311 passed`.
12. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
13. Feche o passo (AGENTS.md, seção 7), um comando por vez:
    ```
    git add -- src/controllers/day_closing_controller.py src/controllers/__init__.py src/resources/internal.py src/app.py tests/integration/internal/test_day_closing.py
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "feat(virada): rota da virada do dia com o CDI e o relógio"
    git log -1 --format=%B
    ```

**Testes:** `tests/integration/internal/test_day_closing.py`. Todos começam com `DbUtils.rollback()` (o relógio é de todos, DIA-01). Efeito no banco do 200: `bank_clock.accounting_date` + 1 dia; nada mais nesta fase. Cada recusa (400, 403, 409, 422, 503) não muda o relógio.

| Função de teste | Entrada | Esperado |
|---|---|---|
| `test_closes_the_day_and_advances_the_clock` | relógio em 2026-06-01; fechar 2026-06-01 | 200 e exatamente `{"closed_date": "2026-06-01", "accounting_date": "2026-06-02"}`; um depósito depois conta em 2026-06-02 (DIA-01, DIA-05) |
| `test_same_day_twice_is_409` | fechar 2026-06-01 duas vezes; depois 2026-06-02 | 200; 409 `QIT001028` e o relógio fica em 2026-06-02 (DIA-02); 200 com 2026-06-03 |
| `test_future_date_is_422` | relógio em 2026-06-01; fechar 2026-06-02; depois 2026-06-01 | 422 `QIT001029` e o relógio não muda; 200 |
| `test_impossible_date_is_422` | `2026-02-30` e `2026-13-01`; depois 2026-06-01 | 422 `QIT001030` nos dois; 200 |
| `test_day_without_cdi_rate_still_closes` | o Mockserver responde lista vazia para 2026-06-01 | 200 e o relógio avança (COF-16) |
| `test_central_bank_down_is_503_and_the_day_does_not_advance` | o Mockserver demora 7 s; depois responde na hora | 503 `QIT001031` e o relógio fica em 2026-06-01; 200 (COF-20) |
| `test_automatically_blocked_account_stays_blocked` | 10 transferências; a 11ª; fechar o dia; transferir; desbloquear; transferir | 201 nas 10; 422 `QIT001019` e `BLOCKED`; 200 e continua `BLOCKED`; 409 `QIT001011`; 204; 201 (CLI-08; 09, "bloqueio automático e virada do dia") |
| `test_refuses_body_out_of_schema` | `{}`; `2026-6-1`; número; campo a mais; depois o corpo certo | 400 `QIT000001` nos quatro; 200 (API-03) |
| `test_requires_admin_token` | fechar com os tokens certos; sem `ADMIN-TOKEN`; `ADMIN-TOKEN` errado; sem `INTERNAL-TOKEN` | 200; 403 `QIT000003` nos dois; 403 `QIT000002`; o relógio fica em 2026-06-02 (PRD-13) |

**Verificar:**
- `./.venv/Scripts/python.exe -m pytest -v tests/integration/internal/test_day_closing.py` → `9 passed`.
- `git grep -n "day_closings" -- src/app.py` → exatamente uma linha, a da rota.
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `311 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/app.py
  src/controllers/__init__.py
  src/controllers/day_closing_controller.py
  src/resources/internal.py
  tests/integration/internal/test_day_closing.py
  ```
- `git log -1 --format=%B` → `feat(virada): rota da virada do dia com o CDI e o relógio`

**Pronto quando:**
- [ ] Os 9 testes falharam antes do código (item 4) e passam depois (item 10).
- [ ] O bloco das rotas de `src/app.py` é o do campo **Arquivos**.
- [ ] Suíte com `311 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/07-cofrinho`.

**Commit:** `feat(virada): rota da virada do dia com o CDI e o relógio`
**Pare se:**
- O item 4 não terminar com `9 failed`.
- A linha citada na troca de `src/app.py` não for encontrada igual.
- Um teste receber 500 (`QIT000500`) ou 503 `QIT000503`: rode `docker compose logs --tail 100 api` e `docker compose logs --tail 100 mockserver` e traga as duas saídas.
- Um teste parar com `RuntimeError` do `MockGenerator` (o Mockserver não respondeu).
- A suíte não terminar com `311 passed`.

---
### Passo 7.12 — Rendimento na virada
**Branch:** fase/07-cofrinho · **Depende de:** 7.11
**Objetivo:** `LotRepository.list_open_by_piggy_bank_for_update` e o nome novo `AccountRepository.list_open_customer_accounts`; na virada, cada cofrinho de conta não encerrada rende lote por lote, pela taxa do ranque que rende hoje (`yield_rank`): os centavos inteiros viram um par de lançamentos `YIELD` por categoria (banco − e cofrinho +), numa operação `YIELD`; a fração fica no resíduo do lote; dia sem taxa não rende; conta bloqueada rende.
**Decisões:** COF-02 — % do CDI por ranque · COF-13 — rendimento por lote · COF-15 — fração de centavo · COF-16 — só dias com taxa · COF-22 — rende o dia inteiro · COF-23 — colunas do lote e lançamentos por categoria · DIA-03 — ordem da virada · CLI-07 — bloqueada segue na virada · CLI-05 — encerrada só lê (decisão de 08/10: a virada não a processa) · GAM-19 — rende o ranque do início do dia · DAD-09 — a conta do banco paga · DAD-16 — a operação soma zero · MOV-05, MOV-11 — trava da conta e do cofrinho na ordem do `id` · TST-01 — black box e TDD
**Arquivos:**
- `src/controllers/day_closing_controller.py` (editar): o conteúdo inteiro passa a ser:

```python
from datetime import date

from calculations import RANK_CDI_PERCENT, daily_rate, lot_yield
from connectors import BcbConnector
from controllers.base_controller import BaseController
from errors import DayAlreadyClosed, FutureAccountingDate, InvalidAccountingDate
from models import Account, AccountStatus, AccountType, EntryType, TransactionType
from repositories import AccountRepository, BankClockRepository, CategoryRepository, EntryRepository, LotRepository, TransactionRepository


class DayClosingController(BaseController):
    """A virada do dia (DIA-01 a DIA-05): uma transação só, tudo ou nada.

    Ordem (DIA-03): pede a taxa do CDI → rendimento por lote (7.12) → XP
    de recorde (7.13) → ranques e carência, e o ranque que rende amanhã
    (7.14) → avança a data. Percorre as contas de cliente não encerradas,
    ACTIVE e BLOCKED (CLI-07); a encerrada só lê (CLI-05).
    """

    def __init__(self) -> None:
        super().__init__(__name__)
        self.account_repository = AccountRepository(self.context)
        self.bank_clock_repository = BankClockRepository(self.context)
        self.category_repository = CategoryRepository(self.context)
        self.entry_repository = EntryRepository(self.context)
        self.lot_repository = LotRepository(self.context)
        self.transaction_repository = TransactionRepository(self.context)
        self.bcb_connector = BcbConnector()

    def close_day(self, day_closing_data: dict) -> dict:
        """Fecha o dia do relógio do banco. As regras, nesta ordem:

        1. a data existe no calendário (422 QIT001030);
        2. trava o relógio (SELECT ... FOR UPDATE): as operações em
           andamento terminam antes, e as novas esperam a virada;
        3. a data não é anterior ao relógio (409 QIT001028): fechar o mesmo
           dia duas vezes não paga duas vezes (DIA-02);
        4. a data não é posterior ao relógio (422 QIT001029);
        5. o Banco Central responde a taxa do dia (503 QIT001031, COF-20):
           a exceção desfaz tudo, e o dia não avança; dia sem taxa segue,
           sem rendimento (COF-16).

        Depois, para cada conta de cliente não encerrada, na ordem do id,
        com a conta e o cofrinho travados: o rendimento do dia, se o dia
        tem taxa. Por último, avança o relógio um dia de calendário e faz
        o commit. A resposta traz o dia fechado e o novo dia do relógio.
        """
        accounting_date = day_closing_data["accounting_date"]
        closing_date = self._parse_accounting_date(accounting_date)
        bank_clock = self.bank_clock_repository.lock()

        if closing_date < bank_clock.accounting_date:
            raise DayAlreadyClosed(accounting_date)

        if closing_date > bank_clock.accounting_date:
            raise FutureAccountingDate(accounting_date, bank_clock.accounting_date.isoformat())

        cdi_rate = self.bcb_connector.get_cdi_rate(closing_date)
        bank = self.account_repository.get_system_account(AccountType.BANK)

        for customer_account in self.account_repository.list_open_customer_accounts():
            account, piggy_bank = self._lock_account_and_piggy_bank(customer_account)

            # O encerramento pode ter ocorrido entre a listagem e a trava.
            if account.status.enumerator == AccountStatus.CLOSED:
                continue

            if cdi_rate is not None:
                self._pay_yield(account, piggy_bank, bank, cdi_rate, closing_date)

        new_date = self.bank_clock_repository.advance(bank_clock)
        self.logger.info("day_closing_ready_to_commit accounting_date=%s", closing_date)
        self.session.commit()

        return {
            "closed_date": closing_date.isoformat(),
            "accounting_date": new_date.isoformat(),
        }

    def _pay_yield(self, account: Account, piggy_bank: Account, bank: Account, cdi_rate: str, closing_date: date) -> None:
        """O rendimento do dia de um cofrinho (COF-02, COF-13, COF-15, COF-22, COF-23), nesta ordem:

        1. a taxa do dia é a do ranque que rende hoje (yield_rank, gravado
           pela virada de ontem: GAM-19), truncada na 8ª casa;
        2. cada lote com dinheiro rende sobre o próprio saldo (principal +
           rendimento que restam) mais o resíduo de ontem: os centavos
           inteiros vão para o rendimento do lote, e a fração fica no
           resíduo dele;
        3. os centavos somam por categoria; cada categoria que rendeu ao
           menos 1 centavo ganha um par de lançamentos YIELD: −centavos na
           conta BANK e +centavos no cofrinho, na categoria (COF-23, DAD-09).

        Uma operação YIELD por cofrinho por dia, sem request_control_key, e
        nenhuma quando nenhum centavo rendeu. O dinheiro resgatado antes da
        virada já saiu do lote e não rende o dia; o guardado antes rende o
        dia inteiro (COF-22).
        """
        rate = daily_rate(cdi_rate, RANK_CDI_PERCENT[account.yield_rank.enumerator])

        yield_by_category = {}
        for lot in self.lot_repository.list_open_by_piggy_bank_for_update(piggy_bank):
            cents, residue = lot_yield(lot.principal_remaining + lot.yield_remaining, lot.residue, rate)

            self.lot_repository.update_remaining(lot, lot.principal_remaining, lot.yield_remaining + cents, residue)
            yield_by_category[lot.category_id] = yield_by_category.get(lot.category_id, 0) + cents

        category_ids = []
        for category_id in sorted(yield_by_category):
            if yield_by_category[category_id] > 0:
                category_ids.append(category_id)

        if len(category_ids) == 0:
            return

        transaction = self.transaction_repository.create(TransactionType.YIELD, None, None, closing_date)

        for category_id in category_ids:
            category = self.category_repository.get_by_id(category_id)
            cents = yield_by_category[category_id]

            self.entry_repository.create(transaction, bank, EntryType.YIELD, -cents)
            self.entry_repository.create(transaction, piggy_bank, EntryType.YIELD, cents, category)

    def _lock_account_and_piggy_bank(self, account: Account) -> tuple:
        """A conta e o cofrinho dela, travados na ordem do id (MOV-05, MOV-11), com os valores relidos do banco."""
        piggy_bank = self.account_repository.get_piggy_bank(account)

        locked_accounts = {}
        for locked_account in self.account_repository.lock_accounts([account, piggy_bank]):
            locked_accounts[locked_account.id] = locked_account

        return locked_accounts[account.id], locked_accounts[piggy_bank.id]

    def _parse_accounting_date(self, accounting_date: str) -> date:
        """A data do corpo como date. O schema já garantiu o formato AAAA-MM-DD; data que não existe (2026-02-30) → 422 QIT001030."""
        try:
            return date.fromisoformat(accounting_date)
        except ValueError:
            raise InvalidAccountingDate(accounting_date) from None
```

- `src/repositories/lot_repository.py` (editar): duas mudanças, e nada mais.
  1. A linha
     ```python
     from models import Category, Lot, Transaction
     ```
     vira
     ```python
     from models import Account, Category, Lot, Transaction
     ```
  2. O método `list_open_by_piggy_bank_for_update` abaixo entra logo depois de `list_open_for_update` e antes de `update_remaining`, com uma linha em branco antes dele:

```python
    def list_open_by_piggy_bank_for_update(self, piggy_bank: Account) -> list:
        """Os lotes com dinheiro de todas as categorias do cofrinho, por categoria e do mais antigo para o mais novo (id crescente), travados (COF-13, COF-23)."""
        return (
            self.session.query(Lot)
            .join(Category, Category.id == Lot.category_id)
            .filter(Category.account_id == piggy_bank.id, Lot.principal_remaining + Lot.yield_remaining > 0)
            .order_by(Lot.category_id, Lot.id)
            .with_for_update(of=Lot)
            .populate_existing()
            .all()
        )
```

- `src/repositories/account_repository.py` (editar): o método `list_open_customer_accounts` abaixo entra logo depois de `get_open_account_by_customer` e antes de `get_piggy_bank`, com uma linha em branco antes dele. Os imports não mudam.

```python
    def list_open_customer_accounts(self) -> list:
        """As contas de cliente não encerradas (ACTIVE e BLOCKED), na ordem do id: as que a virada do dia percorre (CLI-07; a encerrada só lê, CLI-05)."""
        return (
            self.session.query(Account)
            .join(Account.account_type)
            .join(Account.status)
            .filter(
                AccountType.enumerator == AccountType.CUSTOMER,
                AccountStatus.enumerator != AccountStatus.CLOSED,
            )
            .order_by(Account.id)
            .all()
        )
```

- `tests/integration/internal/test_day_closing_yield.py` (criar): o conteúdo inteiro é:

```python
"""Rendimento na virada: POST /internal/day_closings e o cofrinho (COF-02, COF-13, COF-15, COF-16, COF-22, COF-23, CLI-07, GAM-19).

Cada lote rende sobre o próprio saldo, pela taxa do ranque que rende no
dia; os centavos inteiros entram no cofrinho, e a fração fica para o dia
seguinte. CDI de teste: 0,054266% ao dia (taxa 0,00054266 a 100%). Todo
teste começa com DbUtils.rollback() (o relógio volta a 2026-06-01) e
programa no Mockserver a taxa de cada dia que fecha.
"""

from datetime import date, timedelta

from tests.utils import DbUtils, MockGenerator, ObjectGenerator, PayloadGenerator, RequestGenerator


CDI = "0.054266"
FIRST_DAY = date(2026, 6, 1)


def day(offset: int) -> str:
    """2026-06-01 + offset dias, em texto: o relógio começa em 2026-06-01 depois do DbUtils.rollback() (DIA-04)."""
    return (FIRST_DAY + timedelta(days=offset)).isoformat()


def close_day(accounting_date: str) -> None:
    status, response = RequestGenerator.POST_day_closing(PayloadGenerator.day_closing(accounting_date))
    assert status == 200, response


def piggy_bank_balance_of(account: dict) -> int:
    status, response = RequestGenerator.GET_account(account["account_key"], account["account_token"])
    assert status == 200, response

    return response["piggy_bank_balance"]


def piggy_bank_entries(account: dict) -> list:
    status, response = RequestGenerator.GET_piggy_bank_entries(account["account_key"], account["account_token"], {"limit": "100"})
    assert status == 200, response

    return response["data"]


def save(account: dict, amount: int) -> None:
    status, response = RequestGenerator.POST_saving(account["account_key"], account["account_token"], PayloadGenerator.saving(amount=amount))
    assert status == 201, response


def redeem(account: dict, amount: int) -> None:
    status, response = RequestGenerator.POST_redemption(account["account_key"], account["account_token"], PayloadGenerator.redemption(amount=amount))
    assert status == 201, response


class TestDayClosingYield:
    def test_yields_whole_cents_and_keeps_the_fraction(self):
        DbUtils.rollback()
        for offset in range(4):
            MockGenerator.set_cdi_rate(day(offset), CDI)

        account = ObjectGenerator.create_funded_account(100000)
        save(account, 100000)

        balances = []
        for offset in range(4):
            close_day(day(offset))
            balances.append(piggy_bank_balance_of(account))

        assert balances == [100054, 100108, 100162, 100217]

        for offset in range(4):
            MockGenerator.clear_cdi(day(offset))

    def test_each_lot_yields_on_its_own(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate(day(0), CDI)
        two_lots = ObjectGenerator.create_funded_account(2000)
        one_lot = ObjectGenerator.create_funded_account(2000)
        save(two_lots, 1000)
        save(two_lots, 1000)
        save(one_lot, 2000)

        close_day(day(0))

        assert piggy_bank_balance_of(one_lot) == 2001
        assert piggy_bank_balance_of(two_lots) == 2000
        MockGenerator.clear_cdi(day(0))

    def test_redeemed_money_does_not_yield_the_day(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate(day(0), CDI)
        account = ObjectGenerator.create_funded_account(100000)
        save(account, 100000)
        redeem(account, 40000)

        close_day(day(0))

        assert piggy_bank_balance_of(account) == 60032
        MockGenerator.clear_cdi(day(0))

    def test_day_without_rate_does_not_yield(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate(day(0))
        MockGenerator.set_cdi_rate(day(1), CDI)
        account = ObjectGenerator.create_funded_account(100000)
        save(account, 100000)

        close_day(day(0))
        assert piggy_bank_balance_of(account) == 100000
        assert [entry["transaction_type"] for entry in piggy_bank_entries(account)] == ["SAVE"]

        close_day(day(1))
        assert piggy_bank_balance_of(account) == 100054
        MockGenerator.clear_cdi(day(0))
        MockGenerator.clear_cdi(day(1))

    def test_blocked_account_still_yields(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate(day(0), CDI)
        account = ObjectGenerator.create_funded_account(100000)
        save(account, 100000)

        status, response = RequestGenerator.POST_block(account["account_key"], PayloadGenerator.block())
        assert status == 204, response

        close_day(day(0))

        assert piggy_bank_balance_of(account) == 100054
        MockGenerator.clear_cdi(day(0))

    def test_yield_uses_the_rank_of_the_start_of_the_day(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate(day(0), CDI)
        account = ObjectGenerator.create_funded_account(1000000)
        save(account, 1000000)

        status, response = RequestGenerator.GET_gamification(account["account_key"], account["account_token"])
        assert status == 200, response
        assert response["rank"] == "GOLD"

        close_day(day(0))

        assert piggy_bank_balance_of(account) == 1000542
        MockGenerator.clear_cdi(day(0))

    def test_yield_entry_is_paid_by_the_bank(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate(day(0), CDI)
        account = ObjectGenerator.create_funded_account(100000)
        save(account, 100000)

        close_day(day(0))

        entries = piggy_bank_entries(account)
        yield_entry = entries[0]
        assert (yield_entry["transaction_type"], yield_entry["entry_type"], yield_entry["amount"], yield_entry["balance_after"]) == ("YIELD", "YIELD", 54, 100054)
        assert yield_entry["category"]["name"] == "economias"
        assert yield_entry["counterparty"] == {"type": "BANK"}
        assert yield_entry["accounting_date"] == "2026-06-01"
        assert sum(entry["amount"] for entry in entries) == piggy_bank_balance_of(account) == 100054

        status, response = RequestGenerator.GET_transaction(account["account_key"], account["account_token"], yield_entry["transaction_key"])
        assert status == 200, response
        assert (response["type"], response["accounting_date"]) == ("YIELD", "2026-06-01")
        assert "gross_amount" not in response
        assert [(entry["entry_type"], entry["amount"], entry["counterparty"]) for entry in response["entries"]] == [("YIELD", 54, {"type": "BANK"})]

        status, response = RequestGenerator.GET_entries(account["account_key"], account["account_token"])
        assert status == 200, response
        assert [entry["transaction_type"] for entry in response["data"]] == ["SAVE", "DEPOSIT"]
        MockGenerator.clear_cdi(day(0))
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/07-cofrinho`; `git log --oneline -n 3` mostra `feat(virada): rota da virada do dia com o CDI e o relógio`.
2. Crie `tests/integration/internal/test_day_closing_yield.py` com o conteúdo do campo **Arquivos**.
3. `docker compose up -d --build --wait`.
4. `./.venv/Scripts/python.exe -m pytest -v tests/integration/internal/test_day_closing_yield.py` → a última linha tem `7 failed` e não tem `passed`. Os 7 falham por asserção: hoje a virada não rende, e o cofrinho fica com o valor guardado.
5. Edite `src/controllers/day_closing_controller.py` com o conteúdo do campo **Arquivos**.
6. Faça as duas mudanças em `src/repositories/lot_repository.py`.
7. Acrescente `list_open_customer_accounts` em `src/repositories/account_repository.py`.
8. `docker compose up -d --build --wait`.
9. `./.venv/Scripts/python.exe -m pytest -v tests/integration/internal/test_day_closing_yield.py` → a última linha tem `7 passed`.
10. Rode as conferências P1 e C1 do **Verificar**.
11. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `318 passed`.
12. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
13. Feche o passo (AGENTS.md, seção 7), um comando por vez:
    ```
    git add -- src/controllers/day_closing_controller.py src/repositories/lot_repository.py src/repositories/account_repository.py tests/integration/internal/test_day_closing_yield.py
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "feat(virada): rendimento do cofrinho por lote"
    git log -1 --format=%B
    ```

**Testes:** `tests/integration/internal/test_day_closing_yield.py`. Todos começam com `DbUtils.rollback()`. Efeito no banco de cada virada com taxa: por cofrinho que rendeu ao menos 1 centavo, uma operação `YIELD` com a data do dia fechado e um par de lançamentos `YIELD` por categoria (`BANK` −, cofrinho +); em cada lote com dinheiro, `yield_remaining` e `residue` novos.

| Função de teste | Entrada | Esperado |
|---|---|---|
| `test_yields_whole_cents_and_keeps_the_fraction` | guardar 100000; fechar 4 dias a `0.054266` | cofrinho 100054, 100108, 100162 e 100217: o 4º dia rende 55 porque as frações de centavo dos três primeiros se juntaram (COF-15); o dinheiro guardado antes da virada rende o dia inteiro (COF-22) |
| `test_each_lot_yields_on_its_own` | conta A guarda 1000 duas vezes; conta B guarda 2000 uma vez; fechar o dia | B fica com 2001; A fica com 2000: cada lote de 1000 rende 0,54 centavo e guarda a fração (COF-13) |
| `test_redeemed_money_does_not_yield_the_day` | guardar 100000; resgatar 40000; fechar o dia | cofrinho 60032: só os 60000 que ficaram rendem (COF-22) |
| `test_day_without_rate_does_not_yield` | dia 1 sem taxa; dia 2 a `0.054266` | 100000 e o extrato só com o `SAVE`; depois 100054 (COF-16) |
| `test_blocked_account_still_yields` | guardar 100000; bloquear; fechar o dia | cofrinho 100054 (CLI-07) |
| `test_yield_uses_the_rank_of_the_start_of_the_day` | guardar 1000000 (ranque `GOLD` na hora); fechar o dia | cofrinho 1000542: o dia rende a 100%, o ranque do início do dia; a 110% seriam 1000596 (GAM-19) |
| `test_yield_entry_is_paid_by_the_bank` | guardar 100000; fechar o dia | no extrato do cofrinho, o primeiro item é `YIELD`/`YIELD` de 54, saldo 100054, categoria `economias`, outra ponta `BANK`, data contábil 2026-06-01; a soma do extrato é o saldo (DAD-07); a consulta da operação mostra só o lançamento do cofrinho; o extrato da conta não tem rendimento (COF-02: a conta principal não rende) |

**Verificar:**
- `./.venv/Scripts/python.exe -m pytest -v tests/integration/internal/test_day_closing_yield.py` → `7 passed`.
- P1 — resgate proporcional depois do rendimento (COF-24, decisão de 08/10). Um comando, numa linha só; começa com `DbUtils.rollback()`:
  ```
  ./.venv/Scripts/python.exe -c "from sqlalchemy import create_engine, text; from tests.utils import DbUtils, MockGenerator, ObjectGenerator, PayloadGenerator, RequestGenerator as R; DbUtils.rollback(); MockGenerator.set_cdi_rate('2026-06-01', '0.054266'); a = ObjectGenerator.create_funded_account(100000); k, t = a['account_key'], a['account_token']; print(R.POST_saving(k, t, PayloadGenerator.saving(amount=100000))[0], R.POST_day_closing(PayloadGenerator.day_closing('2026-06-01'))[0], R.POST_redemption(k, t, PayloadGenerator.redemption(amount=50000))[0]); e = create_engine(DbUtils.database_url()); c = e.connect(); print([tuple(str(v) for v in r) for r in c.execute(text('SELECT principal_remaining, yield_remaining, residue FROM lot')).all()]); c.close(); e.dispose(); MockGenerator.clear_cdi('2026-06-01')"
  ```
  → exatamente:
  ```
  201 200 201
  [('50027', '27', '0.26600000')]
  ```
  O lote rendeu 54 (resíduo 0,266); o resgate de 50000 levou 49973 de principal e 27 de rendimento (26,99 arredondado para cima); o lote fica com 50027 + 27, e o resíduo não muda.
- C1 — a prova da COF-23, no banco que a suíte deixou: em toda categoria, a soma dos lotes é a soma dos lançamentos; em todo cofrinho, o saldo é a soma dos lançamentos. Um comando, numa linha só:
  ```
  docker compose exec -T db psql -U bootcamp -d bootcamp -t -A -c "SELECT (SELECT count(*) FROM category c WHERE (SELECT coalesce(sum(l.principal_remaining + l.yield_remaining), 0) FROM lot l WHERE l.category_id = c.id) <> (SELECT coalesce(sum(e.amount), 0) FROM entry e WHERE e.category_id = c.id)) || ':' || (SELECT count(*) FROM account a WHERE a.account_type_id = 2 AND a.balance <> (SELECT coalesce(sum(e.amount), 0) FROM entry e WHERE e.account_id = a.id))"
  ```
  → exatamente `0:0` (nenhuma categoria e nenhum cofrinho fora da conta; `account_type` 2 = `PIGGY_BANK`).
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `318 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/controllers/day_closing_controller.py
  src/repositories/account_repository.py
  src/repositories/lot_repository.py
  tests/integration/internal/test_day_closing_yield.py
  ```
- `git log -1 --format=%B` → `feat(virada): rendimento do cofrinho por lote`

**Pronto quando:**
- [ ] Os 7 testes falharam antes do código (item 4) e passam depois (item 9).
- [ ] P1 e C1 dão a saída esperada.
- [ ] Suíte com `318 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/07-cofrinho`.

**Commit:** `feat(virada): rendimento do cofrinho por lote`
**Pare se:**
- O item 4 não terminar com `7 failed`.
- A linha de import citada na mudança 1 de `lot_repository.py` não for encontrada igual.
- Um teste receber 500 (`QIT000500`): rode `docker compose logs --tail 100 api` e traga a saída.
- P1 ou C1 derem outra saída.
- A suíte não terminar com `318 passed`.

---
### Passo 7.13 — XP do recorde na virada
**Branch:** fase/07-cofrinho · **Depende de:** 7.12
**Objetivo:** depois do rendimento de cada conta, `GamificationController.award_record_xp(account, None, closing_date)`: o cofrinho que passou do recorde dá n XP por real inteiro, e o recorde sobe.
**Decisões:** GAM-04 — só passar do recorde dá XP; o rendimento conta · GAM-19 — XP de recorde também na virada · GAM-25 — XP do recorde em reais inteiros · DIA-03 — o XP vem depois do rendimento · CLI-07 — bloqueada segue na virada · DAD-14 — evento e colunas · TST-01 — black box e TDD
**Arquivos:**
- `src/controllers/day_closing_controller.py` (editar): quatro mudanças, e nada mais.
  1. A linha
     ```python
     from controllers.base_controller import BaseController
     ```
     vira as duas linhas
     ```python
     from controllers.base_controller import BaseController
     from controllers.gamification_controller import GamificationController
     ```
  2. A linha
     ```python
             self.bcb_connector = BcbConnector()
     ```
     vira as duas linhas
     ```python
             self.bcb_connector = BcbConnector()
             self.gamification_controller = GamificationController()
     ```
  3. As linhas
     ```python
                 if cdi_rate is not None:
                     self._pay_yield(account, piggy_bank, bank, cdi_rate, closing_date)
     ```
     viram as linhas
     ```python
                 if cdi_rate is not None:
                     self._pay_yield(account, piggy_bank, bank, cdi_rate, closing_date)

                 self.gamification_controller.award_record_xp(account, None, closing_date)
     ```
  4. As linhas da docstring de `close_day`
     ```python
             Depois, para cada conta de cliente não encerrada, na ordem do id,
             com a conta e o cofrinho travados: o rendimento do dia, se o dia
             tem taxa. Por último, avança o relógio um dia de calendário e faz
             o commit. A resposta traz o dia fechado e o novo dia do relógio.
     ```
     viram as linhas
     ```python
             Depois, para cada conta de cliente não encerrada, na ordem do id,
             com a conta e o cofrinho travados: o rendimento do dia, se o dia
             tem taxa; o XP de recorde, se o cofrinho passou do recorde
             (GAM-04, GAM-25; a operação fica nula no xp_event). Por último,
             avança o relógio um dia de calendário e faz o commit. A resposta
             traz o dia fechado e o novo dia do relógio.
     ```

- `tests/integration/internal/test_day_closing_record_xp.py` (criar): o conteúdo inteiro é:

```python
"""XP do recorde na virada: POST /internal/day_closings e a gamificação (GAM-04, GAM-19, GAM-25, DIA-03, CLI-07).

O rendimento conta para o recorde: quando o cofrinho passa do maior saldo
que já teve, cada real inteiro novo dá n XP (n = próximo nível). CDI de
teste: 1% ao dia, para números redondos. Todo teste começa com
DbUtils.rollback() e programa no Mockserver a taxa de cada dia que fecha.
"""

from tests.utils import DbUtils, MockGenerator, ObjectGenerator, PayloadGenerator, RequestGenerator


ONE_PERCENT = "1.000000"
HALF_PERCENT = "0.500000"


def close_day(accounting_date: str) -> None:
    status, response = RequestGenerator.POST_day_closing(PayloadGenerator.day_closing(accounting_date))
    assert status == 200, response


def record_progress_of(account: dict) -> tuple:
    """(nível, XP, recorde do cofrinho)."""
    status, response = RequestGenerator.GET_gamification(account["account_key"], account["account_token"])
    assert status == 200, response

    return response["level"], response["xp"], response["piggy_record"]


def piggy_bank_balance_of(account: dict) -> int:
    status, response = RequestGenerator.GET_account(account["account_key"], account["account_token"])
    assert status == 200, response

    return response["piggy_bank_balance"]


def save(account: dict, amount: int) -> None:
    status, response = RequestGenerator.POST_saving(account["account_key"], account["account_token"], PayloadGenerator.saving(amount=amount))
    assert status == 201, response


def redeem(account: dict, amount: int) -> None:
    status, response = RequestGenerator.POST_redemption(account["account_key"], account["account_token"], PayloadGenerator.redemption(amount=amount))
    assert status == 201, response


class TestDayClosingRecordXp:
    def test_yield_above_the_record_gives_xp(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate("2026-06-01", ONE_PERCENT)
        account = ObjectGenerator.create_funded_account(100000)
        save(account, 100000)
        assert record_progress_of(account) == (1, 0, 100000)

        close_day("2026-06-01")

        assert piggy_bank_balance_of(account) == 101000
        assert record_progress_of(account) == (1, 20, 101000)
        MockGenerator.clear_cdi("2026-06-01")

    def test_yield_below_the_record_gives_no_xp_until_it_passes(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate("2026-06-01", ONE_PERCENT)
        MockGenerator.set_cdi_rate("2026-06-02", ONE_PERCENT)
        account = ObjectGenerator.create_funded_account(100000)
        save(account, 100000)
        redeem(account, 1000)
        assert record_progress_of(account) == (1, 0, 100000)

        close_day("2026-06-01")
        assert piggy_bank_balance_of(account) == 99990
        assert record_progress_of(account) == (1, 0, 100000)

        close_day("2026-06-02")
        assert piggy_bank_balance_of(account) == 100989
        assert record_progress_of(account) == (1, 18, 100989)
        MockGenerator.clear_cdi("2026-06-01")
        MockGenerator.clear_cdi("2026-06-02")

    def test_cents_of_yield_become_xp_when_they_complete_a_real(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate("2026-06-01", HALF_PERCENT)
        MockGenerator.set_cdi_rate("2026-06-02", HALF_PERCENT)
        account = ObjectGenerator.create_funded_account(10000)
        save(account, 10000)
        assert record_progress_of(account) == (0, 100, 10000)

        close_day("2026-06-01")
        assert piggy_bank_balance_of(account) == 10050
        assert record_progress_of(account) == (0, 100, 10050)

        close_day("2026-06-02")
        assert piggy_bank_balance_of(account) == 10100
        assert record_progress_of(account) == (0, 101, 10100)
        MockGenerator.clear_cdi("2026-06-01")
        MockGenerator.clear_cdi("2026-06-02")

    def test_blocked_account_gains_record_xp(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate("2026-06-01", ONE_PERCENT)
        account = ObjectGenerator.create_funded_account(100000)
        save(account, 100000)

        status, response = RequestGenerator.POST_block(account["account_key"], PayloadGenerator.block())
        assert status == 204, response

        close_day("2026-06-01")

        assert piggy_bank_balance_of(account) == 101000
        assert record_progress_of(account) == (1, 20, 101000)
        MockGenerator.clear_cdi("2026-06-01")
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/07-cofrinho`; `git log --oneline -n 3` mostra `feat(virada): rendimento do cofrinho por lote`.
2. Crie `tests/integration/internal/test_day_closing_record_xp.py` com o conteúdo do campo **Arquivos**.
3. `docker compose up -d --build --wait`.
4. `./.venv/Scripts/python.exe -m pytest -v tests/integration/internal/test_day_closing_record_xp.py` → a última linha tem `4 failed` e não tem `passed`. Os 4 falham por asserção: hoje a virada rende, mas o recorde e o XP ficam como estavam.
5. Faça as quatro mudanças em `src/controllers/day_closing_controller.py`.
6. `docker compose up -d --build --wait`.
7. `./.venv/Scripts/python.exe -m pytest -v tests/integration/internal/test_day_closing_record_xp.py` → a última linha tem `4 passed`.
8. Rode a conferência X1 do **Verificar**.
9. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `322 passed`.
10. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
11. Feche o passo (AGENTS.md, seção 7), um comando por vez:
    ```
    git add -- src/controllers/day_closing_controller.py tests/integration/internal/test_day_closing_record_xp.py
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "feat(virada): XP de recorde do cofrinho na virada"
    git log -1 --format=%B
    ```

**Testes:** `tests/integration/internal/test_day_closing_record_xp.py`. Todos começam com `DbUtils.rollback()`. Efeito no banco da virada em que o cofrinho passa do recorde: `piggy_record` novo; quando o XP é maior que 0, um `xp_event` `PIGGY_RECORD` sem operação, com a data do dia fechado, e um `level_event` por nível novo.

| Função de teste | Entrada | Esperado |
|---|---|---|
| `test_yield_above_the_record_gives_xp` | guardar 100000 (nível 1, XP 0, recorde 100000); fechar o dia a 1% | cofrinho 101000; (nível, XP, recorde) = (1, 20, 101000): 10 reais novos × n = 2 (GAM-04, GAM-19, DIA-03) |
| `test_yield_below_the_record_gives_no_xp_until_it_passes` | guardar 100000; resgatar 1000; fechar dois dias a 1% | dia 1: cofrinho 99990, abaixo do recorde, (1, 0, 100000); dia 2: cofrinho 100989, (1, 18, 100989): 9 reais × n = 2 (GAM-04) |
| `test_cents_of_yield_become_xp_when_they_complete_a_real` | guardar 10000 (XP 100); fechar dois dias a 0,5% | dia 1: 10050, (0, 100, 10050): o recorde sobe e os 50 centavos não dão XP; dia 2: 10100, (0, 101, 10100) (GAM-25) |
| `test_blocked_account_gains_record_xp` | guardar 100000; bloquear; fechar o dia a 1% | cofrinho 101000; (1, 20, 101000) (CLI-07) |

**Verificar:**
- `./.venv/Scripts/python.exe -m pytest -v tests/integration/internal/test_day_closing_record_xp.py` → `4 passed`.
- X1 — os eventos de XP do recorde: o do guardar tem operação; o da virada, não. Um comando, numa linha só; começa com `DbUtils.rollback()`:
  ```
  ./.venv/Scripts/python.exe -c "from sqlalchemy import create_engine, text; from tests.utils import DbUtils, MockGenerator, ObjectGenerator, PayloadGenerator, RequestGenerator as R; DbUtils.rollback(); MockGenerator.set_cdi_rate('2026-06-01', '1.000000'); a = ObjectGenerator.create_funded_account(100000); print(R.POST_saving(a['account_key'], a['account_token'], PayloadGenerator.saving(amount=100000))[0], R.POST_day_closing(PayloadGenerator.day_closing('2026-06-01'))[0]); e = create_engine(DbUtils.database_url()); c = e.connect(); print([tuple(str(v) for v in r) for r in c.execute(text('SELECT source, xp, transaction_id IS NULL, accounting_date FROM xp_event ORDER BY id')).all()]); print([r[0] for r in c.execute(text('SELECT level FROM level_event ORDER BY id')).all()]); c.close(); e.dispose(); MockGenerator.clear_cdi('2026-06-01')"
  ```
  → exatamente:
  ```
  201 200
  [('PIGGY_RECORD', '1000', 'False', '2026-06-01'), ('PIGGY_RECORD', '20', 'True', '2026-06-01')]
  [1]
  ```
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `322 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/controllers/day_closing_controller.py
  tests/integration/internal/test_day_closing_record_xp.py
  ```
- `git log -1 --format=%B` → `feat(virada): XP de recorde do cofrinho na virada`

**Pronto quando:**
- [ ] Os 4 testes falharam antes do código (item 4) e passam depois (item 7).
- [ ] A X1 dá as 3 linhas esperadas.
- [ ] Suíte com `322 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/07-cofrinho`.

**Commit:** `feat(virada): XP de recorde do cofrinho na virada`
**Pare se:**
- O item 4 não terminar com `4 failed`.
- Alguma linha citada nas mudanças de `day_closing_controller.py` não for encontrada igual.
- `docker compose up -d --build --wait` falhar com `ImportError` ou `circular import` no `docker compose logs --tail 100 api`: traga a saída.
- A X1 der outra saída.
- A suíte não terminar com `322 passed`.

---
### Passo 7.14 — Ranque e carência na virada
**Branch:** fase/07-cofrinho · **Depende de:** 7.13
**Objetivo:** depois do XP de recorde de cada conta: sobe (`UP`); abre a carência (`GRACE_START`, `grace_until` = dia fechado + 30 dias); encerra a carência quando o saldo volta ao mínimo (`GRACE_END`); cai direto para o ranque do saldo na virada que fecha o dia `grace_until` (`DOWN`); por último, grava o ranque que rende amanhã (`yield_rank`). O nome novo `GamificationRepository.update_yield_rank`.
**Decisões:** GAM-12 — ranque pelo cofrinho · GAM-13 — mínimos · GAM-14 — carência (cai na virada que fecha `grace_until`, decisão de 08/10) · GAM-19 — queda e carência só na virada; o rendimento usa o ranque do início do dia · COF-02 — % do CDI por ranque · DIA-03 — ordem da virada · CLI-07 — bloqueada segue na virada · CLI-05 — encerrada só lê · DAD-14 — evento e colunas · TST-01 — black box e TDD
**Arquivos:**
- `src/controllers/day_closing_controller.py` (editar): o conteúdo inteiro passa a ser:

```python
from datetime import date, timedelta

from calculations import GRACE_DAYS, RANK_CDI_PERCENT, RANK_ORDER, daily_rate, lot_yield, rank_for_balance
from connectors import BcbConnector
from controllers.base_controller import BaseController
from controllers.gamification_controller import GamificationController
from errors import DayAlreadyClosed, FutureAccountingDate, InvalidAccountingDate
from models import Account, AccountStatus, AccountType, EntryType, RankEvent, TransactionType
from repositories import (
    AccountRepository,
    BankClockRepository,
    CategoryRepository,
    EntryRepository,
    GamificationRepository,
    LotRepository,
    TransactionRepository,
)


class DayClosingController(BaseController):
    """A virada do dia (DIA-01 a DIA-05): uma transação só, tudo ou nada.

    Ordem (DIA-03): pede a taxa do CDI → rendimento por lote → XP de
    recorde → ranques e carência, e o ranque que rende amanhã → avança a
    data. Percorre as contas de cliente não encerradas, ACTIVE e BLOCKED
    (CLI-07); a encerrada só lê (CLI-05).
    """

    def __init__(self) -> None:
        super().__init__(__name__)
        self.account_repository = AccountRepository(self.context)
        self.bank_clock_repository = BankClockRepository(self.context)
        self.category_repository = CategoryRepository(self.context)
        self.entry_repository = EntryRepository(self.context)
        self.gamification_repository = GamificationRepository(self.context)
        self.lot_repository = LotRepository(self.context)
        self.transaction_repository = TransactionRepository(self.context)
        self.bcb_connector = BcbConnector()
        self.gamification_controller = GamificationController()

    def close_day(self, day_closing_data: dict) -> dict:
        """Fecha o dia do relógio do banco. As regras, nesta ordem:

        1. a data existe no calendário (422 QIT001030);
        2. trava o relógio (SELECT ... FOR UPDATE): as operações em
           andamento terminam antes, e as novas esperam a virada;
        3. a data não é anterior ao relógio (409 QIT001028): fechar o mesmo
           dia duas vezes não paga duas vezes (DIA-02);
        4. a data não é posterior ao relógio (422 QIT001029);
        5. o Banco Central responde a taxa do dia (503 QIT001031, COF-20):
           a exceção desfaz tudo, e o dia não avança; dia sem taxa segue,
           sem rendimento (COF-16).

        Depois, para cada conta de cliente não encerrada, na ordem do id,
        com a conta e o cofrinho travados: o rendimento do dia, se o dia
        tem taxa; o XP de recorde, se o cofrinho passou do recorde
        (GAM-04, GAM-25; a operação fica nula no xp_event); o ranque, a
        carência e o ranque que rende amanhã. Por último, avança o relógio
        um dia de calendário e faz o commit. A resposta traz o dia fechado
        e o novo dia do relógio.
        """
        accounting_date = day_closing_data["accounting_date"]
        closing_date = self._parse_accounting_date(accounting_date)
        bank_clock = self.bank_clock_repository.lock()

        if closing_date < bank_clock.accounting_date:
            raise DayAlreadyClosed(accounting_date)

        if closing_date > bank_clock.accounting_date:
            raise FutureAccountingDate(accounting_date, bank_clock.accounting_date.isoformat())

        cdi_rate = self.bcb_connector.get_cdi_rate(closing_date)
        bank = self.account_repository.get_system_account(AccountType.BANK)

        for customer_account in self.account_repository.list_open_customer_accounts():
            account, piggy_bank = self._lock_account_and_piggy_bank(customer_account)

            # O encerramento pode ter ocorrido entre a listagem e a trava.
            if account.status.enumerator == AccountStatus.CLOSED:
                continue

            if cdi_rate is not None:
                self._pay_yield(account, piggy_bank, bank, cdi_rate, closing_date)

            self.gamification_controller.award_record_xp(account, None, closing_date)
            self._update_rank(account, piggy_bank, closing_date)

        new_date = self.bank_clock_repository.advance(bank_clock)
        self.logger.info("day_closing_ready_to_commit accounting_date=%s", closing_date)
        self.session.commit()

        return {
            "closed_date": closing_date.isoformat(),
            "accounting_date": new_date.isoformat(),
        }

    def _pay_yield(self, account: Account, piggy_bank: Account, bank: Account, cdi_rate: str, closing_date: date) -> None:
        """O rendimento do dia de um cofrinho (COF-02, COF-13, COF-15, COF-22, COF-23), nesta ordem:

        1. a taxa do dia é a do ranque que rende hoje (yield_rank, gravado
           pela virada de ontem: GAM-19), truncada na 8ª casa;
        2. cada lote com dinheiro rende sobre o próprio saldo (principal +
           rendimento que restam) mais o resíduo de ontem: os centavos
           inteiros vão para o rendimento do lote, e a fração fica no
           resíduo dele;
        3. os centavos somam por categoria; cada categoria que rendeu ao
           menos 1 centavo ganha um par de lançamentos YIELD: −centavos na
           conta BANK e +centavos no cofrinho, na categoria (COF-23, DAD-09).

        Uma operação YIELD por cofrinho por dia, sem request_control_key, e
        nenhuma quando nenhum centavo rendeu. O dinheiro resgatado antes da
        virada já saiu do lote e não rende o dia; o guardado antes rende o
        dia inteiro (COF-22).
        """
        rate = daily_rate(cdi_rate, RANK_CDI_PERCENT[account.yield_rank.enumerator])

        yield_by_category = {}
        for lot in self.lot_repository.list_open_by_piggy_bank_for_update(piggy_bank):
            cents, residue = lot_yield(lot.principal_remaining + lot.yield_remaining, lot.residue, rate)

            self.lot_repository.update_remaining(lot, lot.principal_remaining, lot.yield_remaining + cents, residue)
            yield_by_category[lot.category_id] = yield_by_category.get(lot.category_id, 0) + cents

        category_ids = []
        for category_id in sorted(yield_by_category):
            if yield_by_category[category_id] > 0:
                category_ids.append(category_id)

        if len(category_ids) == 0:
            return

        transaction = self.transaction_repository.create(TransactionType.YIELD, None, None, closing_date)

        for category_id in category_ids:
            category = self.category_repository.get_by_id(category_id)
            cents = yield_by_category[category_id]

            self.entry_repository.create(transaction, bank, EntryType.YIELD, -cents)
            self.entry_repository.create(transaction, piggy_bank, EntryType.YIELD, cents, category)

    def _update_rank(self, account: Account, piggy_bank: Account, closing_date: date) -> None:
        """O ranque e a carência na virada (GAM-12, GAM-14, GAM-19). Compara o ranque que o saldo do cofrinho dá com o atual, nesta ordem:

        1. o saldo dá um ranque maior que o atual: sobe na hora, e a
           carência acaba (raise_rank, evento UP com o ranque novo);
        2. o saldo dá o ranque atual e a conta está em carência: a carência
           acaba (GRACE_END, com o ranque atual; grace_until nulo);
        3. o saldo dá um ranque menor e a conta não está em carência: a
           carência começa (GRACE_START, com o ranque atual; grace_until =
           dia fechado + GRACE_DAYS). O ranque não muda e continua rendendo;
        4. o saldo dá um ranque menor, a conta está em carência e o dia
           fechado chegou ao último dia dela (grace_until): cai direto para
           o ranque que o saldo dá (DOWN, com o ranque novo; grace_until
           nulo). A queda é na virada que fecha o dia grace_until (decisão
           de 08/10);
        5. o saldo dá um ranque menor e a carência ainda não acabou: nada.

        Por último, o ranque atual passa a ser o que rende amanhã
        (yield_rank, GAM-19).
        """
        current_rank = account.rank.enumerator
        balance_rank = rank_for_balance(piggy_bank.balance)

        if RANK_ORDER.index(balance_rank) > RANK_ORDER.index(current_rank):
            self.gamification_controller.raise_rank(account, piggy_bank, closing_date)
        elif balance_rank == current_rank:
            if account.grace_until is not None:
                self.gamification_repository.update_rank(account, current_rank, None)
                self.gamification_repository.create_rank_event(account, current_rank, RankEvent.GRACE_END, closing_date)
        elif account.grace_until is None:
            self.gamification_repository.update_rank(account, current_rank, closing_date + timedelta(days=GRACE_DAYS))
            self.gamification_repository.create_rank_event(account, current_rank, RankEvent.GRACE_START, closing_date)
        elif closing_date >= account.grace_until:
            self.gamification_repository.update_rank(account, balance_rank, None)
            self.gamification_repository.create_rank_event(account, balance_rank, RankEvent.DOWN, closing_date)

        self.gamification_repository.update_yield_rank(account, account.rank.enumerator)

    def _lock_account_and_piggy_bank(self, account: Account) -> tuple:
        """A conta e o cofrinho dela, travados na ordem do id (MOV-05, MOV-11), com os valores relidos do banco."""
        piggy_bank = self.account_repository.get_piggy_bank(account)

        locked_accounts = {}
        for locked_account in self.account_repository.lock_accounts([account, piggy_bank]):
            locked_accounts[locked_account.id] = locked_account

        return locked_accounts[account.id], locked_accounts[piggy_bank.id]

    def _parse_accounting_date(self, accounting_date: str) -> date:
        """A data do corpo como date. O schema já garantiu o formato AAAA-MM-DD; data que não existe (2026-02-30) → 422 QIT001030."""
        try:
            return date.fromisoformat(accounting_date)
        except ValueError:
            raise InvalidAccountingDate(accounting_date) from None
```

- `src/repositories/gamification_repository.py` (editar): o método `update_yield_rank` abaixo entra no fim da classe, logo depois de `update_rank`, com uma linha em branco antes dele:

```python
    def update_yield_rank(self, account: Account, rank_enumerator: str) -> None:
        """Escreve o ranque que rende a partir do dia seguinte; só a virada o grava (GAM-19)."""
        account.yield_rank = self.session.query(PiggyRank).filter(PiggyRank.enumerator == rank_enumerator).one()
```

- `tests/integration/internal/test_day_closing_rank.py` (criar): o conteúdo inteiro é:

```python
"""Ranque e carência na virada: POST /internal/day_closings e a gamificação (GAM-12, GAM-13, GAM-14, GAM-19, COF-02, CLI-05, CLI-07).

O ranque sobe na hora e também na virada; a queda só é vista na virada.
Abaixo do mínimo, a carência começa: o ranque vale e rende por mais 30
dias; voltou ao mínimo, a carência acaba; na virada que fecha o último dia
dela, cai direto para o ranque que o saldo dá. Todo teste começa com
DbUtils.rollback() e programa no Mockserver cada dia que fecha (sem taxa,
quando o rendimento não importa).
"""

from datetime import date, timedelta

from tests.utils import DbUtils, MockGenerator, ObjectGenerator, PayloadGenerator, RequestGenerator


CDI = "0.054266"
FIRST_DAY = date(2026, 6, 1)


def day(offset: int) -> str:
    """2026-06-01 + offset dias, em texto: o relógio começa em 2026-06-01 depois do DbUtils.rollback() (DIA-04)."""
    return (FIRST_DAY + timedelta(days=offset)).isoformat()


def close_day(accounting_date: str) -> None:
    status, response = RequestGenerator.POST_day_closing(PayloadGenerator.day_closing(accounting_date))
    assert status == 200, response


def rank_of(account: dict) -> tuple:
    """(ranque, % do CDI, fim da carência)."""
    status, response = RequestGenerator.GET_gamification(account["account_key"], account["account_token"])
    assert status == 200, response

    return response["rank"], response["cdi_percent"], response["grace_until"]


def piggy_bank_balance_of(account: dict) -> int:
    status, response = RequestGenerator.GET_account(account["account_key"], account["account_token"])
    assert status == 200, response

    return response["piggy_bank_balance"]


def save(account: dict, amount: int) -> None:
    status, response = RequestGenerator.POST_saving(account["account_key"], account["account_token"], PayloadGenerator.saving(amount=amount))
    assert status == 201, response


def redeem(account: dict, amount: int) -> None:
    status, response = RequestGenerator.POST_redemption(account["account_key"], account["account_token"], PayloadGenerator.redemption(amount=amount))
    assert status == 201, response


def create_account_in_grace() -> dict:
    """Uma conta com o cofrinho em 199999 e o ranque BRONZE: guardou 200000 e resgatou 1 (a queda só aparece na virada)."""
    account = ObjectGenerator.create_funded_account(300000)
    save(account, 200000)
    redeem(account, 1)

    return account


class TestDayClosingRank:
    def test_rank_goes_up_at_day_closing(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate(day(0), "0.100000")
        account = ObjectGenerator.create_funded_account(200000)
        save(account, 199900)
        assert rank_of(account) == ("DEFAULT", "100", None)

        close_day(day(0))

        assert piggy_bank_balance_of(account) == 200099
        assert rank_of(account) == ("BRONZE", "102.5", None)
        MockGenerator.clear_cdi(day(0))

    def test_yield_rank_follows_the_rank_from_the_next_day(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate(day(0), CDI)
        MockGenerator.set_cdi_rate(day(1), CDI)
        account = ObjectGenerator.create_funded_account(1000000)
        save(account, 1000000)

        close_day(day(0))
        assert piggy_bank_balance_of(account) == 1000542

        close_day(day(1))
        assert piggy_bank_balance_of(account) == 1001139
        MockGenerator.clear_cdi(day(0))
        MockGenerator.clear_cdi(day(1))

    def test_grace_starts_and_keeps_yielding_at_the_rank(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate(day(0))
        MockGenerator.set_cdi_rate(day(1), CDI)
        account = ObjectGenerator.create_funded_account(300000)
        save(account, 200000)
        redeem(account, 10000)
        assert rank_of(account) == ("BRONZE", "102.5", None)

        close_day(day(0))
        assert rank_of(account) == ("BRONZE", "102.5", "2026-07-01")

        close_day(day(1))
        assert piggy_bank_balance_of(account) == 190105
        assert rank_of(account) == ("BRONZE", "102.5", "2026-07-01")
        MockGenerator.clear_cdi(day(0))
        MockGenerator.clear_cdi(day(1))

    def test_grace_ends_when_the_balance_returns(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate(day(0))
        MockGenerator.set_cdi_rate(day(1))
        account = create_account_in_grace()

        close_day(day(0))
        assert rank_of(account) == ("BRONZE", "102.5", "2026-07-01")

        save(account, 1)
        assert rank_of(account) == ("BRONZE", "102.5", "2026-07-01")

        close_day(day(1))
        assert rank_of(account) == ("BRONZE", "102.5", None)
        MockGenerator.clear_cdi(day(0))
        MockGenerator.clear_cdi(day(1))

    def test_rank_falls_straight_to_the_balance_rank_after_thirty_days(self):
        DbUtils.rollback()
        for offset in range(31):
            MockGenerator.set_cdi_rate(day(offset))

        account = ObjectGenerator.create_funded_account(1000000)
        save(account, 1000000)
        redeem(account, 700000)
        assert rank_of(account) == ("GOLD", "110", None)

        close_day(day(0))
        assert rank_of(account) == ("GOLD", "110", "2026-07-01")

        for offset in range(1, 30):
            close_day(day(offset))

        assert day(29) == "2026-06-30"
        assert rank_of(account) == ("GOLD", "110", "2026-07-01")

        close_day(day(30))
        assert rank_of(account) == ("BRONZE", "102.5", None)

        for offset in range(31):
            MockGenerator.clear_cdi(day(offset))

    def test_blocked_account_rank_follows(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate(day(0))
        account = create_account_in_grace()

        status, response = RequestGenerator.POST_block(account["account_key"], PayloadGenerator.block())
        assert status == 204, response

        close_day(day(0))

        assert rank_of(account) == ("BRONZE", "102.5", "2026-07-01")
        MockGenerator.clear_cdi(day(0))

    def test_closed_account_is_skipped(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate(day(0))
        open_account = create_account_in_grace()

        closed_account = ObjectGenerator.create_funded_account(200000)
        save(closed_account, 200000)
        redeem(closed_account, 200000)

        payload = PayloadGenerator.withdrawal(amount=200000)
        status, response = RequestGenerator.POST_withdrawal(closed_account["account_key"], closed_account["account_token"], payload)
        assert status == 201, response

        status, response = RequestGenerator.DELETE_account(closed_account["account_key"], closed_account["account_token"])
        assert status == 204, response

        close_day(day(0))

        assert rank_of(open_account) == ("BRONZE", "102.5", "2026-07-01")
        assert rank_of(closed_account) == ("BRONZE", "102.5", None)
        MockGenerator.clear_cdi(day(0))
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/07-cofrinho`; `git log --oneline -n 3` mostra `feat(virada): XP de recorde do cofrinho na virada`.
2. Crie `tests/integration/internal/test_day_closing_rank.py` com o conteúdo do campo **Arquivos**.
3. `docker compose up -d --build --wait`.
4. `./.venv/Scripts/python.exe -m pytest -v tests/integration/internal/test_day_closing_rank.py` → a última linha tem `7 failed` e não tem `passed`. Os 7 falham por asserção: hoje a virada não mexe no ranque, na carência nem no ranque que rende.
5. Edite `src/controllers/day_closing_controller.py` com o conteúdo do campo **Arquivos**.
6. Acrescente `update_yield_rank` em `src/repositories/gamification_repository.py`.
7. `docker compose up -d --build --wait`.
8. `./.venv/Scripts/python.exe -m pytest -v tests/integration/internal/test_day_closing_rank.py` → a última linha tem `7 passed`.
9. Rode a conferência R1 do **Verificar**.
10. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `329 passed`.
11. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
12. Feche o passo (AGENTS.md, seção 7), um comando por vez:
    ```
    git add -- src/controllers/day_closing_controller.py src/repositories/gamification_repository.py tests/integration/internal/test_day_closing_rank.py
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "feat(virada): ranque e carência na virada"
    git log -1 --format=%B
    ```

**Testes:** `tests/integration/internal/test_day_closing_rank.py`. Todos começam com `DbUtils.rollback()`. Efeito no banco de cada virada, por conta de cliente não encerrada: `rank_id`, `grace_until` e `yield_rank_id` novos e, quando o ranque ou a carência mudam, um `rank_event` com a data do dia fechado.

| Função de teste | Entrada | Esperado |
|---|---|---|
| `test_rank_goes_up_at_day_closing` | guardar 199900 (`DEFAULT`); fechar o dia a 0,1% | cofrinho 200099; `BRONZE`, `"102.5"`, sem carência: o rendimento do dia conta para o ranque (GAM-19, DIA-03) |
| `test_yield_rank_follows_the_rank_from_the_next_day` | guardar 1000000 (`GOLD` na hora); fechar dois dias a `0.054266` | 1000542 (dia 1 a 100%); 1001139 (dia 2 a 110%) (GAM-19, COF-02) |
| `test_grace_starts_and_keeps_yielding_at_the_rank` | guardar 200000 (`BRONZE`); resgatar 10000; dia 1 sem taxa; dia 2 a `0.054266` | antes: sem carência; dia 1: carência até `2026-07-01`; dia 2: cofrinho 190105 (rendeu 105 a 102,5%; a 100% seriam 103) e a carência continua (GAM-14) |
| `test_grace_ends_when_the_balance_returns` | conta em 199999 e `BRONZE`; dia 1; guardar 1; dia 2 | carência até `2026-07-01`; continua depois de guardar (só a virada a encerra, GAM-19); depois da virada, `BRONZE` sem carência (GAM-14) |
| `test_rank_falls_straight_to_the_balance_rank_after_thirty_days` | guardar 1000000 (`GOLD`); resgatar 700000 (sobram 300000, saldo de `BRONZE`); fechar de 2026-06-01 a 2026-07-01, sem taxa | dia 1: `GOLD` com carência até `2026-07-01`; depois de fechar 2026-06-30: ainda `GOLD`; depois de fechar 2026-07-01: `BRONZE`, sem carência, sem passar por `SILVER` (GAM-14; decisão de 08/10) |
| `test_blocked_account_rank_follows` | conta em 199999 e `BRONZE`, bloqueada; fechar o dia | carência até `2026-07-01` (CLI-07) |
| `test_closed_account_is_skipped` | conta aberta em 199999 e `BRONZE`; outra que chegou a `BRONZE`, zerou tudo e foi encerrada; fechar o dia | a aberta entra em carência; a encerrada continua `BRONZE`, sem carência (CLI-05; decisão de 08/10) |

**Verificar:**
- `./.venv/Scripts/python.exe -m pytest -v tests/integration/internal/test_day_closing_rank.py` → `7 passed`.
- R1 — os eventos de ranque e o ranque que rende. Um comando, numa linha só; começa com `DbUtils.rollback()`:
  ```
  ./.venv/Scripts/python.exe -c "from sqlalchemy import create_engine, text; from tests.utils import DbUtils, MockGenerator, ObjectGenerator, PayloadGenerator, RequestGenerator as R; DbUtils.rollback(); [MockGenerator.set_cdi_rate(d) for d in ['2026-06-01', '2026-06-02']]; a = ObjectGenerator.create_funded_account(300000); k, t = a['account_key'], a['account_token']; print(R.POST_saving(k, t, PayloadGenerator.saving(amount=200000))[0], R.POST_redemption(k, t, PayloadGenerator.redemption(amount=1))[0], R.POST_day_closing(PayloadGenerator.day_closing('2026-06-01'))[0], R.POST_saving(k, t, PayloadGenerator.saving(amount=1))[0], R.POST_day_closing(PayloadGenerator.day_closing('2026-06-02'))[0]); e = create_engine(DbUtils.database_url()); c = e.connect(); print([tuple(str(v) for v in r) for r in c.execute(text('SELECT p.enumerator, r.kind, r.accounting_date FROM rank_event r JOIN piggy_rank p ON p.id = r.rank_id ORDER BY r.id')).all()]); print([tuple(str(v) for v in r) for r in c.execute(text('SELECT p.enumerator, a.grace_until FROM account a JOIN piggy_rank p ON p.id = a.yield_rank_id WHERE a.account_key = :k'), {'k': k}).all()]); c.close(); e.dispose(); [MockGenerator.clear_cdi(d) for d in ['2026-06-01', '2026-06-02']]"
  ```
  → exatamente:
  ```
  201 201 200 201 200
  [('BRONZE', 'UP', '2026-06-01'), ('BRONZE', 'GRACE_START', '2026-06-01'), ('BRONZE', 'GRACE_END', '2026-06-02')]
  [('BRONZE', 'None')]
  ```
  O `UP` vem do guardar; a carência começa na virada de 2026-06-01 e acaba na de 2026-06-02; o ranque que rende passou a ser `BRONZE` (GAM-19).
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `329 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/controllers/day_closing_controller.py
  src/repositories/gamification_repository.py
  tests/integration/internal/test_day_closing_rank.py
  ```
- `git log -1 --format=%B` → `feat(virada): ranque e carência na virada`

**Pronto quando:**
- [ ] Os 7 testes falharam antes do código (item 4) e passam depois (item 8).
- [ ] A R1 dá as 3 linhas esperadas.
- [ ] Suíte com `329 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/07-cofrinho`.

**Commit:** `feat(virada): ranque e carência na virada`
**Pare se:**
- O item 4 não terminar com `7 failed`.
- Um teste receber 500 (`QIT000500`) ou 503 `QIT000503`: rode `docker compose logs --tail 100 api` e traga a saída.
- A R1 der outra saída.
- A suíte não terminar com `329 passed`.

---

### Passo 7.15 — Encerrar só com cofrinho zerado
**Branch:** fase/07-cofrinho · **Depende de:** 7.14
**Objetivo:** `AccountController.close_account` recusa cofrinho diferente de zero com 409 `QIT001012`, depois do saldo, com o cofrinho travado depois da conta.
**Decisões:** CLI-06 — encerrar com saldo e cofrinho zerados · CLI-05 — estados da conta · CLI-09 — encerrada não guarda nem resgata · MOV-05, MOV-11 — trava na ordem do `id` · TST-01 — black box e TDD
**Arquivos:**
- `src/controllers/account_controller.py` (editar): uma troca, e nada mais. O método `close_account` inteiro (da linha `    def close_account(` até a linha `        self.session.commit()` que o fecha) passa a ser:

```python
    def close_account(self, account_key: str, account_token: str) -> None:
        """O dono encerra a conta (CLI-05, CLI-06). As regras, nesta ordem:

        1. a conta é do dono do token (404 QIT001010, R8);
        2. trava a linha da conta (o estado e o saldo são relidos depois da
           trava: um depósito ao mesmo tempo espera ou é esperado);
        3. a conta está ACTIVE (409 QIT001011): bloqueada precisa ser
           desbloqueada antes, e encerrada é final;
        4. o saldo é zero (409 QIT001012, CLI-06);
        5. o cofrinho está zerado (409 QIT001012, CLI-06): o cofrinho é
           travado depois da conta, na ordem do id (MOV-11).

        Depois: estado CLOSED e o evento, sem origem e sem motivo (quem muda
        é o dono).
        """
        account = self.get_owned_account(account_key, account_token)
        account = self.account_repository.lock_accounts([account])[0]

        if account.status.enumerator != AccountStatus.ACTIVE:
            raise AccountNotActive(account_key, account.status.enumerator)

        if account.balance != 0:
            raise AccountNotEmpty(account_key)

        piggy_bank = self.account_repository.lock_accounts([self.account_repository.get_piggy_bank(account)])[0]

        if piggy_bank.balance != 0:
            raise AccountNotEmpty(account_key)

        self.account_repository.change_status(account, AccountStatus.CLOSED)

        self.session.commit()
```

- `tests/integration/accounts/test_close_account_with_piggy.py` (criar): o conteúdo inteiro é:

```python
"""Encerrar só com o cofrinho zerado: DELETE /accounts/{account_key} (CLI-06, CLI-05, CLI-09).

Conta ACTIVE com saldo zero e dinheiro no cofrinho não encerra (409
QIT001012). Depois de resgatar, sacar e encerrar, a conta não guarda nem
resgata (409 QIT001011).
"""

from tests.utils import ObjectGenerator, PayloadGenerator, RequestGenerator


def balances_of(account: dict) -> tuple:
    """(estado, saldo da conta, saldo do cofrinho)."""
    status, response = RequestGenerator.GET_account(account["account_key"], account["account_token"])
    assert status == 200, response

    return response["status"], response["balance"], response["piggy_bank_balance"]


def close(account: dict) -> tuple:
    return RequestGenerator.DELETE_account(account["account_key"], account["account_token"])


def save(account: dict, amount: int) -> tuple:
    return RequestGenerator.POST_saving(account["account_key"], account["account_token"], PayloadGenerator.saving(amount=amount))


def redeem(account: dict, amount: int) -> tuple:
    return RequestGenerator.POST_redemption(account["account_key"], account["account_token"], PayloadGenerator.redemption(amount=amount))


class TestCloseAccountWithPiggy:
    def test_refuses_closing_with_money_in_the_piggy_bank(self):
        account = ObjectGenerator.create_funded_account(1000)

        status, response = save(account, 1000)
        assert status == 201, response
        assert balances_of(account) == ("ACTIVE", 0, 1000)

        status, response = close(account)
        assert status == 409, response
        assert response["code"] == "QIT001012"
        assert balances_of(account) == ("ACTIVE", 0, 1000)

    def test_closes_after_the_piggy_bank_reaches_zero(self):
        account = ObjectGenerator.create_funded_account(1000)

        status, response = save(account, 400)
        assert status == 201, response

        status, response = close(account)
        assert status == 409, response
        assert response["code"] == "QIT001012"

        status, response = redeem(account, 400)
        assert status == 201, response

        status, response = close(account)
        assert status == 409, response
        assert response["code"] == "QIT001012"

        status, response = RequestGenerator.POST_withdrawal(account["account_key"], account["account_token"], PayloadGenerator.withdrawal(amount=1000))
        assert status == 201, response

        status, response = close(account)
        assert status == 204, response
        assert balances_of(account) == ("CLOSED", 0, 0)

        status, response = save(account, 1)
        assert status == 409, response
        assert response["code"] == "QIT001011"

        status, response = redeem(account, 1)
        assert status == 409, response
        assert response["code"] == "QIT001011"
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/07-cofrinho`; `git log --oneline -n 3` mostra `feat(virada): ranque e carência na virada`.
2. Crie `tests/integration/accounts/test_close_account_with_piggy.py` com o conteúdo do campo **Arquivos**.
3. `docker compose up -d --build --wait`.
4. `./.venv/Scripts/python.exe -m pytest -v tests/integration/accounts/test_close_account_with_piggy.py` → a última linha tem `2 failed` e não tem `passed`. Os 2 falham por asserção: hoje a conta com saldo zero e dinheiro no cofrinho encerra com 204.
5. Faça a troca em `src/controllers/account_controller.py`.
6. `docker compose up -d --build --wait`.
7. `./.venv/Scripts/python.exe -m pytest -v tests/integration/accounts/test_close_account_with_piggy.py` → a última linha tem `2 passed`.
8. `./.venv/Scripts/python.exe -m pytest -v tests/integration/accounts/test_close_account.py tests/integration/accounts/test_close_account_with_balance.py` → a última linha tem `9 passed`.
9. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `331 passed`.
10. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
11. Feche o passo (AGENTS.md, seção 7), um comando por vez:
    ```
    git add -- src/controllers/account_controller.py tests/integration/accounts/test_close_account_with_piggy.py
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "feat(conta): encerrar só com o cofrinho zerado"
    git log -1 --format=%B
    ```

**Testes:** `tests/integration/accounts/test_close_account_with_piggy.py`. Efeito no banco: o 409 não grava nada além da linha de `request_log`; o 204 grava o estado `CLOSED` e o evento, como no 5.11.

| Função de teste | Entrada | Esperado |
|---|---|---|
| `test_refuses_closing_with_money_in_the_piggy_bank` | conta com 1000; guardar 1000; `DELETE` | 409 `QIT001012`; `ACTIVE`, saldo 0, cofrinho 1000 (CLI-06) |
| `test_closes_after_the_piggy_bank_reaches_zero` | guardar 400; `DELETE`; resgatar 400; `DELETE`; sacar 1000; `DELETE`; guardar; resgatar | 409 `QIT001012` (cofrinho); 201; 409 `QIT001012` (saldo); 201; 204 e `CLOSED` com 0 e 0; 409 `QIT001011` nos dois (CLI-09) |

**Verificar:**
- `./.venv/Scripts/python.exe -m pytest -v tests/integration/accounts/test_close_account_with_piggy.py` → `2 passed`.
- `git grep -n "raise AccountNotEmpty" -- src` → exatamente duas linhas, as duas em `src/controllers/account_controller.py`.
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `331 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/controllers/account_controller.py
  tests/integration/accounts/test_close_account_with_piggy.py
  ```
- `git log -1 --format=%B` → `feat(conta): encerrar só com o cofrinho zerado`

**Pronto quando:**
- [ ] Os 2 testes falharam antes do código (item 4) e passam depois (item 7).
- [ ] Os 9 testes de `test_close_account.py` e `test_close_account_with_balance.py` continuam verdes.
- [ ] Suíte com `331 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/07-cofrinho`.

**Commit:** `feat(conta): encerrar só com o cofrinho zerado`
**Pare se:**
- O item 4 não terminar com `2 failed`.
- O método `close_account` atual não for o do passo 6.12 (as quatro regras e o `change_status`).
- Um teste de `test_close_account.py` ou `test_close_account_with_balance.py` ficar vermelho.
- A suíte não terminar com `331 passed`.

---
### Passo 7.fim — Fechar a fase
**Branch:** fase/07-cofrinho · **Depende de:** 7.1 a 7.15 e o commit à mão `chore(cdi): dados do CDI para o mockserver`
**Objetivo:** provar a fase com o banco recriado do zero e levá-la para a `main` com a tag `fase-07`.
**Decisões:** TIM-04 — git por fase · TIM-08 — git automático · ARQ-03 — SQL só com o banco vazio · ARQ-04 — sobe sem `.env` · ARQ-06 — três peças no compose · TST-01 — suíte inteira verde
**Arquivos:** nenhum. O passo não cria, não edita e não apaga arquivo.
**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/07-cofrinho`.
2. `git log --oneline -n 17` → tem as 16 mensagens abaixo, cada uma uma vez (15 dos passos e a do commit à mão):
   ```
   feat(cofrinho): ranques e resgate por lote com teste unitário
   feat(cofrinho): rendimento diário com teste unitário
   feat(cofrinho): repository dos lotes e saldo da categoria
   feat(cofrinho): controller de guardar e resgatar
   feat(cofrinho): rota de guardar
   feat(cofrinho): rota de resgatar
   feat(cofrinho): extrato do cofrinho e as duas pontas de guardar e resgatar
   feat(cdi): connector do Banco Central
   chore(cdi): script que baixa o CDI do Banco Central
   chore(cdi): dados do CDI para o mockserver
   feat(cdi): Mockserver no compose e MockGenerator nos testes
   feat(virada): rota da virada do dia com o CDI e o relógio
   feat(virada): rendimento do cofrinho por lote
   feat(virada): XP de recorde do cofrinho na virada
   feat(virada): ranque e carência na virada
   feat(conta): encerrar só com o cofrinho zerado
   ```
3. Recrie o banco do zero e suba tudo, um comando por vez:
   ```
   docker compose down -v
   docker compose up -d --build --wait
   ```
4. `docker compose ps` → três serviços: `api` (healthy), `db` (healthy) e `mockserver` (running).
5. Rode a conferência M2 (passo 7.10) → `str True None`.
6. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `331 passed`.
7. `./.venv/Scripts/python.exe -m pytest` de novo → a última linha tem `331 passed` (nada intermitente).
8. Rode a conferência C1 (passo 7.12) → `0:0`.
9. Rode a conferência R1 (passo 7.14) → as 3 linhas do **Verificar** do passo 7.14.
10. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
11. `git status --short` → saída vazia.
12. Leve a fase para a `main`, um comando por vez:
    ```
    git switch main
    git merge --no-ff --no-edit -m "feat(cofrinho): fase 07 com cofrinho, lotes, CDI pelo Mockserver, virada do dia, ranque e carência" fase/07-cofrinho
    git tag fase-07
    ```
13. Rode o **Verificar**.

**Testes:** nenhum teste novo. A suíte inteira (212 de integração + 119 unitários) roda duas vezes com o banco recriado do zero (itens 6 e 7).
**Verificar:**
- O `git status --short` antes do merge não mostra alterações.
- `git branch --show-current` → `main`.
- `git log -1 --format=%B` → `feat(cofrinho): fase 07 com cofrinho, lotes, CDI pelo Mockserver, virada do dia, ranque e carência`.
- `git log -1 --format=%P` → dois hashes separados por um espaço (é um merge).
- `git tag --list fase-07` → `fase-07`.
- `git ls-files mockserver scripts` → exatamente:
  ```
  mockserver/Dockerfile
  mockserver/cdi_expectations.json
  scripts/download_cdi.py
  ```
- `git status --short` → saída vazia.

**Pronto quando:**
- [ ] Os três serviços sobem do zero, sem `.env`; M2, C1 e R1 dão o esperado.
- [ ] Suíte com `331 passed`, duas vezes seguidas; lint sem saída.
- [ ] Merge `--no-ff` na `main` com a mensagem exata; tag `fase-07` criada localmente; merge local na `main`.

**Commit:** nenhum commit de passo. Mensagem do merge: `feat(cofrinho): fase 07 com cofrinho, lotes, CDI pelo Mockserver, virada do dia, ranque e carência`
**Pare se:**
- Faltar uma das 16 mensagens do item 2.
- `docker compose up -d --build --wait` falhar: rode `docker compose logs --tail 100 db`, `docker compose logs --tail 100 api` e `docker compose logs --tail 100 mockserver` e traga as três saídas.
- M2, C1 ou R1 derem outra saída.
- A suíte não terminar com `331 passed` nas duas rodadas, ou o lint imprimir qualquer linha.
- O merge local der conflito (AGENTS.md, seção 8, item 9).

---

## Divergências encontradas

Seção para o Bruno; o agente não executa nada daqui.

| # | Onde | O que foi feito |
|---|---|---|
| 1 | Decisões do Bruno de 08/10 que ainda não estão no `04 - Decisões.md`. | Aplicadas no plano; registrar no 04: GAM-14 — a queda é na virada que fecha o dia `grace_until` (`grace_until` = dia da queda + 30); COF-24 — a parte de rendimento do resgate parcial é arredondada para cima ao centavo; COF-15 — a taxa diária é truncada na 8ª casa; CLI-05/CLI-07 — a virada não processa conta encerrada (o ranque dela congela). |
| 2 | PLANO-fase-08, divergência 4: `CDI_PERCENT_BY_RANK` no DTO repetia os números de `RANK_CDI_PERCENT`. | O 7.1 faz `CDI_PERCENT_BY_RANK = RANK_CDI_PERCENT`; os percentuais moram só em `src/calculations/ranks.py`. Por isso `src/dtos/gamification_dto.py` entrou nos arquivos do 7.1. |
| 3 | PLANO-00, arquivos do 7.4: só controller, `controllers/__init__.py` e `transaction_dto.py`. | Entraram também `gamification_controller.py` (`raise_rank`, usado no guardar e na virada) e `gamification_repository.py` (`update_rank`). O `TransactionDTO.obj_to_dict` ganhou `redemption_amounts` já no 7.4; quem o usa é o 7.7. |
| 4 | PLANO-00, arquivos do 7.7; PLANO-fase-06, divergência 11 (a outra ponta de guardar e resgatar fica para o 7.7). | Entraram `transaction_controller.py` (`_counterparty` com `PIGGY_BANK` e `ACCOUNT`, categoria nos lançamentos do cofrinho, bruto e líquido na consulta do `REDEEM`), `category_repository.py` (`get_by_id`) e `entry_dto.py` (as duas outras pontas). |
| 5 | PLANO-00, arquivos do 7.12: só controller e `lot_repository.py`. | Entrou `account_repository.py` (`list_open_customer_accounts`): a virada precisa listar as contas de cliente não encerradas. |
| 6 | DIA-03 manda pedir a taxa dentro da transação da virada. | A virada trava o relógio e depois chama o Banco Central (até 5 s). Nesse tempo, toda operação de dinheiro espera a trava do relógio; passando do `DB_LOCK_TIMEOUT_MS` (5 s), responde 503 `QIT000503`. Fica assim: sem trava antes da chamada, duas viradas da mesma data poderiam pedir a taxa juntas. Vale um parágrafo na RFC. |
| 7 | COF-15 guarda o resíduo no lote; nenhuma decisão diz o que acontece com o resíduo de um lote que zerou. | Lote zerado sai da virada (só rende lote com dinheiro); a fração de centavo que ficou nele não rende mais. É menos de 1 centavo por lote. |
| 8 | GAM-19 e GAM-14: o guardar pode subir o ranque de uma conta em carência. | GAM-26: se havia carência, gravar GRACE_END com o ranque anterior antes de UP com o novo; sem carência, só UP. A prova isolada e a prova PostgreSQL estão no passo 11.6. |
| 9 | COF-16 e ARQ-12: o formato da resposta de dia sem taxa não estava decidido. | O Mockserver responde uma expectativa por dia de calendário: lista com a taxa, ou lista vazia nos dias sem taxa. O connector trata lista vazia como "sem taxa" e qualquer outra coisa como 503. |
| 10 | ARQ-07: 10 anos de CDI. | O script baixa de 2016-10-01 a 2026-09-30 (10 anos menos um dia, dentro do limite de uma chamada do SGS). Fechar um dia depois de 2026-09-30 dá 503 `QIT001031` até o script rodar de novo com `END_DATE` maior. Com o relógio em 2026-06-01, são 122 viradas até lá. |
| 11 | ARQ-05 e o `--wait` do AGENTS.md. | A imagem do Mockserver não tem shell, e o serviço fica sem healthcheck (a API depende dele com `service_started`). Quem espera o Mockserver responder é o `MockGenerator` (até 60 s). |
| 12 | PLANO-00, arquivo não rastreado dentro de pasta nova. | Corrigido na auditoria: usar `git status --short --untracked-files=all`, que mostra o arquivo individual. |
| 13 | AGENTS.md, seção 2: pedido com vários passos segue até o fim. | O 7.9 termina com PARE: o 7.10 precisa do arquivo de dados, que só o Bruno gera (com rede). O cabeçalho do plano diz como pedir as duas metades. |
| 14 | ARQ-07, plano B (CDI fixo em configuração). | Não entrou: o Mockserver faz o papel do Banco Central. Se o script não conseguir baixar a série (rede, bloqueio do SGS), PARE e volte ao chat antes do 7.10. |
| 15 | `docs/rotas.md`: na consulta da operação, "os lançamentos desta conta e do cofrinho dela". | A consulta de um `YIELD` mostra só o lançamento do cofrinho (o do banco não é da conta). O bruto, o IOF, o IR e o líquido de um `REDEEM` são remontados dos lançamentos, inclusive os da conta `BANK` (IOF e IR, a partir do 9.2). |
| 16 | Testes previstos do 09: nenhum cenário de cofrinho, virada, ranque ou carência. | Os testes desta fase saem das decisões COF, GAM e DIA (tabela de cobertura no topo). Acrescentar ao 09 as linhas "guardar e resgatar", "virada e rendimento" e "ranque e carência". |

## Nomes novos da fase 07 (registrar no PLANO-00)

Seção para o Bruno; o agente não executa nada daqui.

| Onde | Nomes |
|---|---|
| `src/calculations/piggy_yield.py` | constantes `EIGHT_PLACES`, `PERCENT`, `YIELD_PRECISION`; assinaturas `daily_rate(cdi_daily_percent, rank_cdi_percent)` (os dois em texto) e `lot_yield(lot_balance_cents, residue, rate)` → `(centavos, resíduo)` |
| `src/calculations/lots.py` | `split_redemption` devolve `(principal, rendimento)` |
| `src/calculations/ranks.py` | ranques em texto (`"DEFAULT"` … `"DIAMOND"`); `RANK_CDI_PERCENT` em texto (`"102.5"`) |
| `LotRepository` | `create(category, transaction, accounting_date, principal)`; `list_open_for_update(category)`; `list_open_by_piggy_bank_for_update(piggy_bank)`; novo `update_remaining(lot, principal_remaining, yield_remaining, residue)` |
| `CategoryRepository` | `get_balance(category)` (soma dos lançamentos, `int`); novo `get_by_id(category_id)` |
| `EntryRepository` | `list_piggy_bank_page(piggy_bank, limit, offset, category=None)`; novo `get_counterparty_category(entry)` |
| `AccountRepository` | novo `list_open_customer_accounts()` |
| `GamificationRepository` | novos `update_rank(account, rank_enumerator, grace_until)`, `update_yield_rank(account, rank_enumerator)` |
| `GamificationController` | novo `raise_rank(account, piggy_bank, accounting_date)` → `bool` |
| `PiggyBankController` | `save(account_key, account_token, saving_data)`; `redeem(account_key, account_token, redemption_data)`; `list_piggy_bank_entries(account_key, account_token, limit, offset, category_key=None)`; novo `get_redemption_amounts(transaction, piggy_bank)`; privados `_take_from_lots`, `_get_category`, `_lock_account_and_piggy_bank`, `_saving_response`, `_redemption_response`, `_find_repeated`, `_balance_after`, `_piggy_bank_entry_to_dict` |
| `DayClosingController` | `close_day(day_closing_data)`; privados `_pay_yield`, `_update_rank`, `_lock_account_and_piggy_bank`, `_parse_accounting_date` |
| `TransactionController` | atributos `category_repository`, `piggy_bank_controller` |
| `TransactionDTO` | novos `with_piggy_bank_balance(transaction, balance, piggy_bank_balance)`, `with_redemption(transaction, balance, piggy_bank_balance, redemption_amounts)`; `obj_to_dict(transaction, entries, redemption_amounts=None)` |
| `EntryDTO` | novos `piggy_bank_counterparty(category)`, `account_counterparty()` |
| `PiggyBankResource` | `on_post_saving(account_key, payload, request)`, `on_post_redemption(account_key, payload, request)`, `on_get_piggy_bank_entries(account_key, request)`; constantes `DEFAULT_LIMIT = 10`, `DEFAULT_PAGE = 0` |
| `InternalResource` | `on_post_day_closing(payload)` |
| `BcbConnector` | constantes `CDI_SERIES_PATH`, `CDI_RATE_PATTERN` |
| `scripts/download_cdi.py` | `SERIES_URL`, `START_DATE`, `END_DATE`, `CHECK_DATES`, `OUTPUT_FILE`; `download_rates`, `build_expectation`, `main` |
| `tests/utils/mock_generator.py` | `MOCKSERVER_URL`, `CDI_SERIES_PATH`, `TEST_PRIORITY = 10`, `READY_TIMEOUT_SECONDS = 60`; assinaturas `set_cdi_rate(accounting_date, cdi_rate=None)`, `set_cdi_delay(accounting_date, delay_seconds, cdi_rate="0.054266")`, `clear_cdi(accounting_date)`; id da expectativa `cdi-test-AAAA-MM-DD` |
| Testes | pasta `tests/integration/piggy_bank/`; ajudantes locais `balances_of`, `record_progress_of`, `piggy_bank_balance_of`, `piggy_bank_entries`, `default_category_key`, `bank_date`, `day`, `rank_of`, `create_account_in_grace`; constantes `CDI = "0.054266"`, `ONE_PERCENT`, `HALF_PERCENT`, `FIRST_DAY` |
| Comportamento | guardar e resgatar travam a conta e o cofrinho; a virada trava o relógio, depois cada conta de cliente não encerrada e o cofrinho dela; o rendimento é uma operação `YIELD` por cofrinho por dia, com um par de lançamentos por categoria |


## Logs críticos — auditoria 08/10

PRD-06: antes do commit, os controllers de dinheiro registram `operation_ready_to_commit` com `transaction_key`; a virada registra `day_closing_ready_to_commit` com data contábil; o bloqueio automático registra `account_block_ready_to_commit` com key e motivo. Não registrar corpo, CPF/CNPJ, tokens, IDs internos nem parâmetros SQL. Após os testes da fase, `docker compose logs --tail 500 api` deve conter as mensagens dos fluxos exercitados; elas indicam tentativa de concluir, não prova de commit. A prova do resultado continua sendo HTTP e reconciliação.
