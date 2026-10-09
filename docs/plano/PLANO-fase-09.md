> **Git local — Bruno, 08/10/2026:** durante a produção, branches, commits, merges e tags ficam locais. Não executar push, pull ou fetch nem exigir acesso ao GitHub. O envio completo será feito pelo Bruno somente no final, quando tudo estiver pronto. As verificações de commits e dependências são locais.

# PLANO — Fase 09 — categorias, IR/IOF e chance de não debitar

**Branch:** `fase/09-categorias-impostos-sorteio` · **Depende de:** fase 7
**Objetivo:** IOF e IR descontados no resgate do cofrinho; categorias criadas pelo dono (criar, listar, consultar, excluir, guardar e resgatar nelas); o sorteio que devolve a transferência de até R$ 100,00.

Regras de execução: `AGENTS.md`. Nomes obrigatórios: `docs/plano/PLANO-00-indice.md`, `docs/plano/PLANO-fase-02.md` (tabelas, models, constantes dos models e ids dos tipos fixos), `docs/plano/PLANO-fase-03.md` (`docs/rotas.md`, catálogo de erros, schemas `post_categories.json` e `get_categories.json`), `docs/plano/PLANO-fase-04.md` (`RequestGenerator`, `PayloadGenerator`, `ObjectGenerator`), `docs/plano/PLANO-fase-05.md` (`AccountRepository`, `CategoryRepository`, `BaseController.get_owned_account`), `docs/plano/PLANO-fase-06.md` (`TransactionRepository`, `EntryRepository`, `TransactionController`), `docs/plano/PLANO-fase-08.md` (`GamificationController`, `calculate_fee`) e `docs/plano/PLANO-fase-07.md` (`PiggyBankController`, `LotRepository`, `split_redemption`, `MockGenerator`). Um passo por vez, na ordem: 9.1 a 9.11 e, por último, 9.fim.

Contagem de testes da suíte (última linha do pytest): `331 passed` no começo; `346 passed` em 9.1; `351 passed` em 9.2 e 9.3; `361 passed` em 9.4; `370 passed` em 9.5; `376 passed` em 9.6; `384 passed` em 9.7; `389 passed` em 9.8; `392 passed` em 9.9; `398 passed` em 9.10; `401 passed` em 9.11 e no 9.fim (331 de antes + 26 unitários + 44 de integração).

Comandos usados nesta fase que não estão na seção 3 do `AGENTS.md`:

| Quero | Comando |
|---|---|
| Rodar uma linha de Python no `.venv` (a raiz do repositório no caminho de import) | `./.venv/Scripts/python.exe -c "<código>"` |
| Rodar uma linha de Python dentro do container da API | `docker compose exec -T api python -c "<código>"` |
| Rodar SQL no banco | `docker compose exec -T db psql -U bootcamp -d bootcamp -t -A -c "<SQL>"` |
| Procurar texto nos arquivos do Git | `git grep <opções> -- <pastas>` |
| Procurar texto também em arquivo novo, ainda fora do Git | `git grep --untracked <opções> -- <arquivo>` |

O `-T` desliga o terminal interativo, que o Git Bash não oferece. O `-t -A` do `psql` tira cabeçalho, rodapé e alinhamento. O `git grep` termina com código 1 quando não acha nada: nos itens em que o esperado é "nenhuma linha", esse código 1 sem linha impressa é o resultado certo.

Nas conferências que rodam dentro do container (`docker compose exec -T api python -c`), o código de `src/` é importado direto, sem HTTP, e tudo termina em `s.rollback()`: nada fica gravado. A conferência P1 (9.8) troca o `commit` da sessão por `flush` (`s.commit = s.flush`) para o controller rodar inteiro sem gravar. As conferências que rodam no `.venv` e começam com `DbUtils.rollback()` apagam o banco e o recriam do zero, como os testes que dependem do relógio.

Todas as saídas esperadas abaixo valem sem `.env` na raiz do repositório (ARQ-04). Existe um `.env`: PARE.

Valores que a fase usa (a conta está nos unitários do 9.1 e do 9.7):

| O quê | Valor |
|---|---|
| IOF (COF-12), % do rendimento por dias de prazo do lote | 1: 96 · 2: 93 · 3: 90 · 4: 86 · 5: 83 · 6: 80 · 7: 76 · 8: 73 · 9: 70 · 10: 66 · 11: 63 · 12: 60 · 13: 56 · 14: 53 · 15: 50 · 16: 46 · 17: 43 · 18: 40 · 19: 36 · 20: 33 · 21: 30 · 22: 26 · 23: 23 · 24: 20 · 25: 16 · 26: 13 · 27: 10 · 28: 6 · 29: 3 · 30 ou mais: 0 |
| IR (COF-12), % pelo prazo do lote | até 180 dias: 22,5 · até 360: 20 · até 720: 17,5 · acima de 720: 15 |
| Prazo do lote | data contábil do resgate − data contábil do lote, em dias corridos |
| Conta do imposto, por lote | IOF = rendimento × % do IOF; IR = (rendimento − IOF) × % do IR |
| Arredondamento | cada imposto é somado, exato, em todos os lotes do resgate e arredondado uma vez, para cima; o IR para em rendimento − IOF |
| CDI de teste | `"1.000000"` (1% ao dia): R$ 1.000,00 rendem R$ 10,00 no dia |
| R$ 1.010,00 resgatados (100000 + 1000 de rendimento), 1 dia | IOF 960 · IR 9 (22,5% de 40) · líquido 100031 |
| O mesmo lote, 30 dias | IOF 0 · IR 225 · líquido 100775 |
| 1 centavo resgatado de um lote com rendimento, 1 dia | IOF 1 · IR 0 (o limite) · líquido 0 |
| Sorteio (GAM-10, GAM-22) | concorre transferência de 1 a 10000 centavos; sorteia `rng.randrange(1000)`; ganha quem tirou menos que os pontos em chance (0 a 10) |

Decisões já consolidadas no `04 - Decisões.md` que este plano aplica: o IR incide sobre o rendimento menos o IOF, como na vida real · o IR para em rendimento − IOF: o imposto nunca passa do rendimento · no extrato da conta principal, o resgate é uma linha só, com o líquido; o bruto, o IOF e o IR saem na resposta e na consulta da operação · resgate com líquido 0 não tem lançamento na conta.

## Cobertura das regras desta fase (TST-02)

| Regra | O que fica vermelho se a regra deixar de valer |
|---|---|
| COF-12 — IR e IOF reais, por lote, arredondados uma vez para cima | `test_taxes.py` (todo o `TestIofPercent`, `TestIrPercent` e `TestRedemptionTaxes`); `test_redeem_taxes.py::test_one_day_lot_pays_iof_and_ir_on_the_yield`, `test_each_lot_pays_by_its_own_term`, `test_no_iof_from_thirty_days` |
| COF-12 — o IR incide sobre rendimento − IOF (decisão de 08/10) | `test_taxes.py::TestRedemptionTaxes::test_ir_base_is_the_yield_minus_iof`; `test_redeem_taxes.py::test_one_day_lot_pays_iof_and_ir_on_the_yield` (IR 9, e não 225) |
| COF-12 — arredonda uma vez, no total do resgate | `test_taxes.py::TestRedemptionTaxes::test_rounds_once_for_the_whole_redemption` |
| COF-24 — imposto só sobre o rendimento; nunca passa dele | `test_taxes.py::TestRedemptionTaxes::test_tax_never_passes_the_yield`, `test_parts_without_yield_pay_nothing`; `test_redeem_taxes.py::test_partial_redemption_taxes_only_the_yield_part`, `test_tax_can_take_the_whole_yield_of_a_tiny_redemption` |
| COF-08 — bruto e líquido na resposta e na consulta | `test_redeem_taxes.py::test_one_day_lot_pays_iof_and_ir_on_the_yield` |
| COF-25 — imposto para o banco; o extrato da conta mostra só o líquido | conferência D1 (9.2); `test_redeem_taxes.py::test_one_day_lot_pays_iof_and_ir_on_the_yield`, `test_tax_can_take_the_whole_yield_of_a_tiny_redemption` |
| MOV-12, MOV-19 — o resgate com imposto repetido devolve a primeira resposta | `test_redeem_taxes.py::test_one_day_lot_pays_iof_and_ir_on_the_yield`, `test_tax_can_take_the_whole_yield_of_a_tiny_redemption` |
| COF-03 — o dono cria categorias; "economias" é a padrão | `test_create_and_list_categories.py::test_new_account_lists_only_economias`, `test_creates_category`; `test_category_money.py::test_saves_and_redeems_in_a_created_category` |
| COF-04 — só exclui categoria zerada; a padrão nunca; zerada não some sozinha | `test_category_money.py::test_category_with_money_cannot_be_deleted`, `test_saves_and_redeems_in_a_created_category`; `test_get_and_delete_category.py::test_default_category_cannot_be_deleted` |
| COF-05 — saldo por categoria | `test_create_and_list_categories.py::test_lists_the_balance_of_each_category`; `test_category_money.py::test_redemption_comes_only_from_the_chosen_category` |
| COF-06 — lotes por categoria | `test_category_money.py::test_each_category_has_its_own_lots_and_taxes` |
| COF-07 — resgate maior que a categoria → 422 | `test_category_money.py::test_redemption_comes_only_from_the_chosen_category` |
| COF-18 — nome único entre as ativas | `test_create_and_list_categories.py::test_duplicated_active_name_is_409`; `test_get_and_delete_category.py::test_name_can_be_used_again_after_delete` |
| COF-19 — sem mover entre categorias | `test_category_money.py::test_redemption_comes_only_from_the_chosen_category` (o dinheiro de uma categoria não paga o resgate da outra) |
| API-15 — excluir muda o estado; excluída aparece `DELETED` e não guarda nem resgata | `test_get_and_delete_category.py::test_deletes_empty_category`; `test_category_money.py::test_deleted_category_refuses_saving_and_redemption` |
| CLI-09 — bloqueada mexe em categoria | `test_create_and_list_categories.py::test_blocked_account_creates_and_lists`; `test_get_and_delete_category.py::test_blocked_account_deletes` |
| CLI-05 — encerrada só lê | `test_create_and_list_categories.py::test_closed_account_refuses_creating_but_lists`; `test_get_and_delete_category.py::test_closed_account_refuses_deleting_but_reads` |
| R4 — excluir grava evento, nada é apagado | conferências G1 (9.3) e E1 (9.5) |
| R8 — categoria e conta de outro dono → 404 | `test_*_categor*.py::test_other_account_token_is_404`, `test_missing_or_wrong_token_is_404`; `test_get_and_delete_category.py::test_unknown_category_is_404`; `test_category_money.py::test_category_of_another_piggy_bank_is_404` |
| API-03 — schema fechado | `test_create_and_list_categories.py::test_refuses_body_and_query_out_of_schema` |
| GAM-10 — 1 ponto em chance = 1 número em 1000; o sorteio vem depois de todas as regras | `test_lottery.py::TestDrawPrize::test_each_point_is_one_in_a_thousand`, `test_without_points_never_wins`; conferências P1 e P2 (9.8); `test_chance.py::test_refused_transfer_never_reaches_the_draw` |
| GAM-11 — ponto em chance vale o mesmo que ponto em tarifa, a R$ 100 | `test_lottery.py::TestDrawPrize::test_one_chance_point_is_worth_one_fee_point_at_the_limit` |
| GAM-22 — só concorre transferência de até R$ 100,00 | `test_lottery.py::TestEligibility::test_eligible_up_to_the_limit`; conferência P1 (9.8, a de 10001 não concorre com gerador que sempre ganha) |
| GAM-23 — o prêmio não dá XP | conferência P1 (9.8, os dois `xp_event` de 25); `test_chance.py` (o XP da origem sobe o mesmo nos dois resultados) |
| TST-06 — gerador injetável | `test_lottery.py` (gerador falso); conferência P1 (9.8); `test_chance.py` (os dois resultados) |

---

### Passo 9.1 — Impostos (unitário)
**Branch:** fase/09-categorias-impostos-sorteio · **Depende de:** fase 7 (tag `fase-07`)
**Objetivo:** `iof_percent`, `ir_percent` e `redemption_taxes` em `src/calculations/taxes.py`, com o teste unitário escrito antes.
**Decisões:** COF-12 — IR e IOF reais · COF-24 — imposto só sobre o rendimento · TST-05 — contas puras com unitário · R6, DAD-08 — dinheiro em centavos inteiros, fração em `Decimal`
**Arquivos:**
- `tests/unit/test_taxes.py` (criar): o conteúdo inteiro é:

```python
"""IOF e IR do resgate: calculations.taxes (COF-12, COF-24, TST-05).

Unitário: importa só de calculations, da biblioteca padrão e do pytest.
Em cada lote, IOF = rendimento × % do IOF pelo prazo; IR = (rendimento −
IOF) × % do IR pelo prazo, como na vida real. Cada imposto é somado em
todos os lotes e arredondado uma vez, para cima; o imposto nunca passa do
rendimento.
"""

import pytest

from calculations import iof_percent, ir_percent, redemption_taxes


IOF_TABLE = [
    "96", "93", "90", "86", "83", "80", "76", "73", "70", "66",
    "63", "60", "56", "53", "50", "46", "43", "40", "36", "33",
    "30", "26", "23", "20", "16", "13", "10", "6", "3",
]


class TestIofPercent:
    def test_real_table_from_day_one_to_twenty_nine(self):
        assert [iof_percent(days) for days in range(1, 30)] == IOF_TABLE

    def test_zero_from_thirty_days(self):
        for days in [30, 31, 180, 3650]:
            assert iof_percent(days) == "0"

    def test_refuses_invalid_days(self):
        for days in [0, -1]:
            with pytest.raises(ValueError):
                iof_percent(days)

        with pytest.raises(TypeError):
            iof_percent(1.0)


class TestIrPercent:
    def test_brackets_by_term(self):
        expected = {0: "22.5", 1: "22.5", 180: "22.5", 181: "20", 360: "20", 361: "17.5", 720: "17.5", 721: "15", 3650: "15"}

        for days, percent in expected.items():
            assert ir_percent(days) == percent, days

    def test_refuses_invalid_days(self):
        with pytest.raises(ValueError):
            ir_percent(-1)

        with pytest.raises(TypeError):
            ir_percent(30.0)


class TestRedemptionTaxes:
    def test_one_day_lot(self):
        assert redemption_taxes([(1, 1000)]) == (960, 9)
        assert redemption_taxes([(1, 500)]) == (480, 5)

    def test_ir_base_is_the_yield_minus_iof(self):
        assert redemption_taxes([(15, 1000)]) == (500, 113)
        assert redemption_taxes([(29, 1000)]) == (30, 219)
        # IOF exato 4,5: IR ceil(4,5 * 22,5%) = 2, antes do limite.
        assert redemption_taxes([(15, 9)]) == (5, 2)

    def test_no_iof_from_thirty_days(self):
        assert redemption_taxes([(30, 1000)]) == (0, 225)

    def test_long_terms(self):
        assert redemption_taxes([(181, 1000)]) == (0, 200)
        assert redemption_taxes([(361, 1000)]) == (0, 175)
        assert redemption_taxes([(721, 1000)]) == (0, 150)

    def test_each_lot_uses_its_own_term(self):
        assert redemption_taxes([(2, 1005), (1, 500)]) == (1415, 21)
        assert redemption_taxes([(1, 500), (2, 1005)]) == (1415, 21)

    def test_rounds_once_for_the_whole_redemption(self):
        assert redemption_taxes([(15, 1)]) == (1, 0)
        assert redemption_taxes([(15, 1), (15, 1)]) == (1, 1)

    def test_tax_never_passes_the_yield(self):
        assert redemption_taxes([(1, 1)]) == (1, 0)
        assert redemption_taxes([(30, 1)]) == (0, 1)

        for days in range(1, 40):
            for yield_cents in range(1, 30):
                iof, ir = redemption_taxes([(days, yield_cents)])

                assert iof + ir <= yield_cents, (days, yield_cents)

    def test_parts_without_yield_pay_nothing(self):
        assert redemption_taxes([]) == (0, 0)
        assert redemption_taxes([(0, 0), (400, 0)]) == (0, 0)
        assert redemption_taxes([(0, 0), (1, 1000)]) == (960, 9)

    def test_refuses_invalid_input(self):
        for yield_parts in [[(1, -1)], [(-1, 0)], [(0, 1)]]:
            with pytest.raises(ValueError):
                redemption_taxes(yield_parts)

        for yield_parts in [[(1, 1.5)], [(1.0, 10)]]:
            with pytest.raises(TypeError):
                redemption_taxes(yield_parts)

    def test_returns_int_never_float(self):
        for value in redemption_taxes([(2, 1005), (1, 500)]):
            assert type(value) is int

        assert type(iof_percent(1)) is str
        assert type(ir_percent(1)) is str
```

- `src/calculations/taxes.py` (criar): o conteúdo inteiro é:

```python
"""IOF e IR do resgate do cofrinho (COF-12, COF-24). Conta pura: sem banco e sem HTTP.

Os percentuais ficam em texto, como em ranks.py, e viram Decimal exato na
conta (R6). O prazo de cada lote é contado em dias corridos do relógio do
banco: a data contábil do resgate menos a data contábil do lote.
"""

from decimal import ROUND_CEILING, Decimal, localcontext


# COF-12: IOF regressivo, a tabela real (Decreto 6.306/2007, anexo): o
# percentual do rendimento que vira IOF no resgate com 1, 2, ..., 29 dias.
IOF_PERCENT_BY_DAY = (
    "96", "93", "90", "86", "83", "80", "76", "73", "70", "66",
    "63", "60", "56", "53", "50", "46", "43", "40", "36", "33",
    "30", "26", "23", "20", "16", "13", "10", "6", "3",
)

# COF-12: a partir de 30 dias, sem IOF.
IOF_FREE_DAYS = 30

# COF-12: IR regressivo pelo prazo do lote: (até quantos dias, percentual).
IR_PERCENT_BY_TERM = (
    (180, "22.5"),
    (360, "20"),
    (720, "17.5"),
)

# COF-12: acima de 720 dias.
IR_LONG_TERM_PERCENT = "15"

# Para passar de percentual para fração.
PERCENT = Decimal(100)

# Dígitos significativos da conta em Decimal: sobra para qualquer valor em BIGINT.
TAX_PRECISION = 50


def iof_percent(days: int) -> str:
    """O percentual do rendimento que vira IOF num resgate com `days` dias de prazo (COF-12).

    De 1 a 29 dias, a tabela real; a partir de 30, "0". Menos de 1 dia não
    tem rendimento (o lote só rende na virada, que avança o relógio), e é
    recusado com ValueError.
    """
    if type(days) is not int:
        raise TypeError(f"days precisa ser int, veio {type(days).__name__}")

    if days < 1:
        raise ValueError(f"o IOF conta a partir de 1 dia, veio {days}")

    if days >= IOF_FREE_DAYS:
        return "0"

    return IOF_PERCENT_BY_DAY[days - 1]


def ir_percent(days: int) -> str:
    """O percentual de IR sobre o rendimento de um lote com `days` dias de prazo (COF-12).

    22,5% até 180 dias; 20% até 360; 17,5% até 720; 15% acima de 720.
    """
    if type(days) is not int:
        raise TypeError(f"days precisa ser int, veio {type(days).__name__}")

    if days < 0:
        raise ValueError(f"prazo negativo: {days}")

    for limit_days, percent in IR_PERCENT_BY_TERM:
        if days <= limit_days:
            return percent

    return IR_LONG_TERM_PERCENT


def redemption_taxes(yield_parts: list) -> tuple:
    """O IOF e o IR de um resgate: (iof, ir), em centavos inteiros (COF-12, COF-24).

    `yield_parts`: uma tupla (dias de prazo, centavos de rendimento) por
    lote de onde o resgate tirou dinheiro. O imposto incide só sobre o
    rendimento (COF-24); parte sem rendimento não paga nada.

    Em cada lote, como na vida real: IOF = rendimento × iof_percent(dias);
    IR = (rendimento − IOF) × ir_percent(dias). Os valores exatos de todos
    os lotes são somados, e cada imposto é arredondado uma vez, no total do
    resgate, para cima (COF-12). O imposto nunca passa do rendimento: o IR
    para em rendimento − IOF (COF-24).
    """
    yield_total = 0
    iof_exact = Decimal(0)
    ir_exact = Decimal(0)

    with localcontext() as context:
        context.prec = TAX_PRECISION

        for days, yield_cents in yield_parts:
            for name, value in [("days", days), ("yield_cents", yield_cents)]:
                if type(value) is not int:
                    raise TypeError(f"{name} precisa ser int, veio {type(value).__name__}")

            if days < 0 or yield_cents < 0:
                raise ValueError(f"parte de resgate inválida: {days} dias, {yield_cents} centavos")

            if yield_cents == 0:
                continue

            lot_iof = Decimal(yield_cents) * Decimal(iof_percent(days)) / PERCENT
            lot_ir = (Decimal(yield_cents) - lot_iof) * Decimal(ir_percent(days)) / PERCENT

            yield_total = yield_total + yield_cents
            iof_exact = iof_exact + lot_iof
            ir_exact = ir_exact + lot_ir

        iof = int(iof_exact.to_integral_value(rounding=ROUND_CEILING))
        ir = int(ir_exact.to_integral_value(rounding=ROUND_CEILING))

    return iof, min(ir, yield_total - iof)
```

- `src/calculations/__init__.py` (editar): o conteúdo inteiro passa a ser:

```python
from calculations.fee import calculate_fee
from calculations.xp import MAX_LEVEL, XpGain, gain_record_xp, gain_transfer_xp, level_cost, next_level_n, record_whole_reais
from calculations.ranks import GRACE_DAYS, RANK_CDI_PERCENT, RANK_MINIMUM_CENTS, RANK_ORDER, rank_for_balance
from calculations.lots import split_redemption
from calculations.piggy_yield import daily_rate, lot_yield
from calculations.taxes import iof_percent, ir_percent, redemption_taxes
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia.
2. Abra a fase, um comando por vez:
   ```
   git switch main
   git log --oneline
   git tag --list fase-07
   git switch -c fase/09-categorias-impostos-sorteio
   ```
   O `git log` mostra `docs(plano): roteiros auditados` e `feat(cofrinho): fase 07 com cofrinho, lotes, CDI pelo Mockserver, virada do dia, ranque e carência`; o `git tag` mostra `fase-07`.
3. Crie `tests/unit/test_taxes.py` com o conteúdo do campo **Arquivos**.
4. `./.venv/Scripts/python.exe -m pytest -v tests/unit/test_taxes.py` → a saída tem `ImportError` com `cannot import name 'iof_percent' from 'calculations'` e a última linha tem `1 error`. É o motivo certo (AGENTS.md, seção 6).
5. Crie `src/calculations/taxes.py` com o conteúdo do campo **Arquivos**.
6. Edite `src/calculations/__init__.py` com o conteúdo do campo **Arquivos**.
7. `./.venv/Scripts/python.exe -m pytest -v tests/unit/test_taxes.py` → a última linha tem `15 passed`.
8. `docker compose up -d --build --wait` → termina sem erro.
9. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `346 passed`.
10. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
11. Rode o **Verificar**.
12. Feche o passo (AGENTS.md, seção 7), um comando por vez:
    ```
    git add -- tests/unit/test_taxes.py src/calculations/taxes.py src/calculations/__init__.py
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "feat(impostos): IOF e IR do resgate com teste unitário"
    git log -1 --format=%B
    ```

**Testes:** `tests/unit/test_taxes.py` (TST-05). Não toca na API nem no banco. A entrada de `redemption_taxes` é uma lista de tuplas (dias de prazo, centavos de rendimento), uma por lote.

| Função de teste | Entrada | Esperado |
|---|---|---|
| `TestIofPercent::test_real_table_from_day_one_to_twenty_nine` | dias 1 a 29 | os 29 percentuais da tabela real, de `"96"` a `"3"` (COF-12) |
| `TestIofPercent::test_zero_from_thirty_days` | 30, 31, 180, 3650 | `"0"` nos quatro |
| `TestIofPercent::test_refuses_invalid_days` | 0; −1; `1.0` | `ValueError`; `ValueError`; `TypeError` |
| `TestIrPercent::test_brackets_by_term` | 0, 1, 180, 181, 360, 361, 720, 721, 3650 | `"22.5"` até 180; `"20"` até 360; `"17.5"` até 720; `"15"` acima (COF-12) |
| `TestIrPercent::test_refuses_invalid_days` | −1; `30.0` | `ValueError`; `TypeError` |
| `TestRedemptionTaxes::test_one_day_lot` | `[(1, 1000)]`; `[(1, 500)]` | `(960, 9)`; `(480, 5)` (22,5% de 20 = 4,5 sobe para 5) |
| `TestRedemptionTaxes::test_ir_base_is_the_yield_minus_iof` | `[(15, 1000)]`; `[(29, 1000)]` | `(500, 113)` (22,5% de 500 = 112,5); `(30, 219)` (22,5% de 970 = 218,25) (decisão de 08/10) |
| `TestRedemptionTaxes::test_no_iof_from_thirty_days` | `[(30, 1000)]` | `(0, 225)` |
| `TestRedemptionTaxes::test_long_terms` | `[(181, 1000)]`; `[(361, 1000)]`; `[(721, 1000)]` | `(0, 200)`; `(0, 175)`; `(0, 150)` |
| `TestRedemptionTaxes::test_each_lot_uses_its_own_term` | `[(2, 1005), (1, 500)]` e a ordem trocada | `(1415, 21)` nas duas (IOF 934,65 + 480; IR 15,82875 + 4,5) |
| `TestRedemptionTaxes::test_rounds_once_for_the_whole_redemption` | `[(15, 1)]`; `[(15, 1), (15, 1)]` | `(1, 0)`; `(1, 1)` (0,5 + 0,5 = 1 de IOF, e não 2) (COF-12) |
| `TestRedemptionTaxes::test_tax_never_passes_the_yield` | `[(1, 1)]`; `[(30, 1)]`; todo prazo de 1 a 39 com todo rendimento de 1 a 29 | `(1, 0)`; `(0, 1)`; IOF + IR nunca passa do rendimento (COF-24) |
| `TestRedemptionTaxes::test_parts_without_yield_pay_nothing` | `[]`; `[(0, 0), (400, 0)]`; `[(0, 0), (1, 1000)]` | `(0, 0)`; `(0, 0)`; `(960, 9)` |
| `TestRedemptionTaxes::test_refuses_invalid_input` | `[(1, -1)]`, `[(-1, 0)]`, `[(0, 1)]`; `[(1, 1.5)]`, `[(1.0, 10)]` | `ValueError` nos três primeiros; `TypeError` nos dois últimos |
| `TestRedemptionTaxes::test_returns_int_never_float` | `[(2, 1005), (1, 500)]`; `iof_percent(1)`; `ir_percent(1)` | os dois impostos `int`; os percentuais `str` (R6) |

**Verificar:**
- `./.venv/Scripts/python.exe -m pytest -v tests/unit/test_taxes.py` → `15 passed`.
- `git grep -n -e "^import" -e "^from" -- src/calculations/taxes.py` → exatamente uma linha: `src/calculations/taxes.py:8:from decimal import ROUND_CEILING, Decimal, localcontext`.
- `git grep -n -e "float" -- src/calculations/taxes.py` → nenhuma linha.
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `346 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/calculations/__init__.py
  src/calculations/taxes.py
  tests/unit/test_taxes.py
  ```
- `git log -1 --format=%B` → `feat(impostos): IOF e IR do resgate com teste unitário`

**Pronto quando:**
- [ ] A branch `fase/09-categorias-impostos-sorteio` nasceu da `main` com o merge da fase 7.
- [ ] O teste falhou antes do código com `ImportError` (item 4) e passa depois (item 7).
- [ ] Os três arquivos têm exatamente o conteúdo do campo **Arquivos**.
- [ ] Suíte com `346 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/09-categorias-impostos-sorteio`.

**Commit:** `feat(impostos): IOF e IR do resgate com teste unitário`
**Pare se:**
- O `git log` do item 2 não mostrar as duas mensagens, ou o `git tag` não mostrar `fase-07`.
- O item 4 não mostrar o `ImportError` (outro erro, ou algum teste rodou).
- O item 7 não terminar com `15 passed` depois de 3 tentativas de conferir `src/calculations/taxes.py` contra o plano.
- Um teste de `tests/unit/` que já existia ficar vermelho.
- A suíte não terminar com `346 passed`.

---

### Passo 9.2 — IR e IOF no resgate
**Branch:** fase/09-categorias-impostos-sorteio · **Depende de:** 9.1
**Objetivo:** `PiggyBankController.redeem` calcula o IOF e o IR sobre a parte de rendimento de cada lote (`redemption_taxes`), põe na conta só o líquido e credita o IOF e o IR na conta `BANK`, em lançamentos `IOF` e `IR`.
**Decisões:** COF-08 — bruto e líquido · COF-12 — IR e IOF reais · COF-24 — imposto só sobre o rendimento · COF-25 — imposto para o banco · DAD-16 — lançamentos somam zero · MOV-10 — valor zero não gera lançamento · MOV-12, MOV-19 — idempotência · TST-01 — black box e TDD · decisões do Bruno de 08/10 (cabeçalho)
**Arquivos:**
- `src/controllers/piggy_bank_controller.py` (editar): o conteúdo inteiro passa a ser:

```python
from datetime import date

from sqlalchemy.exc import IntegrityError

from calculations import redemption_taxes, split_redemption
from controllers.base_controller import BaseController
from controllers.gamification_controller import GamificationController
from dtos import EntryDTO, TransactionDTO
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

        # MOV-19: reconsultar depois da espera pela trava, antes de estado e saldo.
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
        """Resgatar: traz dinheiro de uma categoria do cofrinho para a conta, com IOF e IR (COF-06, COF-07, COF-08, COF-10, COF-12, COF-24, COF-25). As regras, nesta ordem:

        1. a conta é do dono do token (404 QIT001010, R8);
        2. a mesma request_control_key com o mesmo pedido devolve a resposta
           da primeira vez (MOV-19); com outro pedido, 409 QIT001014 (MOV-12);
        3. trava a conta e o cofrinho (MOV-05);
        4. a conta está ACTIVE (409 QIT001011, CLI-09);
        5. a categoria é a "economias": sem category_key no corpo, é ela;
           outra key, 404 QIT001021 (as outras categorias entram no 9.6);
        6. o saldo da categoria cobre o valor (422 QIT001023, COF-07), mesmo
           que o cofrinho todo tenha o dinheiro.

        Depois: a operação REDEEM; o valor bruto sai dos lotes da categoria,
        do mais antigo para o mais novo, cada um até zerar (COF-06), e de
        cada lote o principal e o rendimento saem na proporção do lote
        (COF-24). O IOF e o IR incidem só sobre o rendimento, pelo prazo de
        cada lote (redemption_taxes, COF-12). Os lançamentos, nesta ordem:
        AMOUNT −bruto no cofrinho, na categoria; AMOUNT +líquido na conta
        (líquido = bruto − IOF − IR); IOF +IOF e IR +IR na conta BANK
        (COF-25). Valor zero não gera lançamento. No extrato da conta, o
        resgate é uma linha só, com o líquido; o bruto, o IOF e o IR saem na
        resposta e na consulta da operação. O ranque não cai (GAM-19) e o
        recorde não muda (GAM-04). A resposta traz a key, os dois saldos, o
        bruto, o IOF, o IR e o líquido (COF-08).
        """
        account = self.get_owned_account(account_key, account_token)

        request_control_key = redemption_data["request_control_key"]
        request_hash = hash_request_body(TransactionType.REDEEM, account_key, redemption_data)

        repeated_transaction = self._find_repeated(request_control_key, request_hash)
        if repeated_transaction is not None:
            return self._redemption_response(repeated_transaction, account)

        accounting_date = self.bank_clock_repository.get_accounting_date()
        account, piggy_bank = self._lock_account_and_piggy_bank(account)

        # MOV-19: reconsultar depois da espera pela trava, antes de estado e saldo.
        repeated_transaction = self._find_repeated(request_control_key, request_hash)
        if repeated_transaction is not None:
            return self._redemption_response(repeated_transaction, account)

        if account.status.enumerator != AccountStatus.ACTIVE:
            raise AccountNotActive(account_key, account.status.enumerator)

        category = self._get_category(piggy_bank, redemption_data.get("category_key"))
        amount = redemption_data["amount"]

        if self.category_repository.get_balance(category) < amount:
            raise InsufficientCategoryBalance(category.category_key)

        bank = self.account_repository.get_system_account(AccountType.BANK)

        try:
            transaction = self.transaction_repository.create(TransactionType.REDEEM, request_control_key, request_hash, accounting_date)
            yield_parts = self._take_from_lots(category, amount, accounting_date)
            iof, ir = redemption_taxes(yield_parts)
            net_amount = amount - iof - ir

            self.entry_repository.create(transaction, piggy_bank, EntryType.AMOUNT, -amount, category)

            if net_amount > 0:
                self.entry_repository.create(transaction, account, EntryType.AMOUNT, net_amount)

            if iof > 0:
                self.entry_repository.create(transaction, bank, EntryType.IOF, iof)

            if ir > 0:
                self.entry_repository.create(transaction, bank, EntryType.IR, ir)

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
        trocado). IOF e IR: os lançamentos IOF e IR da conta BANK (COF-25).
        Líquido: bruto − IOF − IR, o que entrou na conta. A consulta da
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

    def _take_from_lots(self, category: Category, amount: int, accounting_date: date) -> list:
        """Tira o valor dos lotes da categoria, do mais antigo para o mais novo, cada um até zerar (COF-06).

        De cada lote, principal e rendimento saem na proporção dele
        (split_redemption, COF-24); o resíduo fica. Devolve, por lote de
        onde saiu dinheiro, a tupla (dias de prazo, centavos de rendimento)
        que redemption_taxes recebe: o prazo é a data contábil do resgate
        menos a do lote, em dias corridos (COF-12).
        """
        remaining = amount
        yield_parts = []

        for lot in self.lot_repository.list_open_for_update(category):
            if remaining == 0:
                break

            taken = min(remaining, lot.principal_remaining + lot.yield_remaining)
            principal_part, yield_part = split_redemption(lot.principal_remaining, lot.yield_remaining, taken)

            self.lot_repository.update_remaining(lot, lot.principal_remaining - principal_part, lot.yield_remaining - yield_part, lot.residue)

            yield_parts.append(((accounting_date - lot.accounting_date).days, yield_part))
            remaining = remaining - taken

        return yield_parts

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
        """O saldo da conta (ou do cofrinho) logo depois da operação: o balance_after do último lançamento dela na operação (MOV-19).

        O resgate cujo líquido é 0 (o imposto levou todo o rendimento de um
        resgate só de rendimento) não tem lançamento na conta: o saldo dela
        é o de antes da operação.
        """
        entries = self.entry_repository.list_by_transaction(transaction, [account.id])

        if not entries:
            return self.entry_repository.get_balance_before(account, transaction)

        return entries[-1].balance_after

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

  O que muda em relação ao 7.7: `from datetime import date` e `redemption_taxes` nos imports; a docstring e o miolo de `redeem` (a conta `BANK`, os impostos, o `AMOUNT` do líquido, os lançamentos `IOF` e `IR` e o "valor zero não gera lançamento"); a docstring de `get_redemption_amounts`; `_take_from_lots` recebe a data contábil e devolve a lista `(dias, rendimento)`; `_balance_after` cai em `get_balance_before` quando a conta não tem lançamento na operação. Preservar os demais métodos e as correções da auditoria anterior: reconsulta após trava e logs críticos.

- `src/repositories/entry_repository.py` (editar): o método `get_balance_before` abaixo entra no fim da classe, logo depois de `get_counterparty_category`, com uma linha em branco antes dele. Os imports não mudam (`Account`, `Entry` e `Transaction` já estão no arquivo).

```python
    def get_balance_before(self, account: Account, transaction: Transaction) -> int:
        """O saldo da conta logo antes da operação: o balance_after do último lançamento dela numa operação anterior; 0 se não tem (MOV-19).

        Serve à resposta repetida de um resgate cujo líquido é 0 (passo
        9.2): ele não tem lançamento na conta, e o saldo dela ficou o de
        antes. Operação anterior = id menor: as operações de uma conta são
        gravadas uma por vez, com a conta travada (MOV-05).
        """
        entry = (
            self.session.query(Entry)
            .filter(Entry.account_id == account.id, Entry.transaction_id < transaction.id)
            .order_by(Entry.id.desc())
            .first()
        )

        if entry is None:
            return 0

        return entry.balance_after
```

- `tests/integration/piggy_bank/test_redeem_taxes.py` (criar): o conteúdo inteiro é:

```python
"""IOF e IR no resgate: POST /accounts/{account_key}/redemptions depois da virada (COF-08, COF-12, COF-24, COF-25, MOV-12, MOV-19).

O imposto incide só sobre o rendimento que sai de cada lote, pelo prazo
do lote em dias do relógio do banco: IOF regressivo nos primeiros 29 dias;
IR de 22,5% até 180 dias, sobre o rendimento menos o IOF. Cada imposto é
arredondado uma vez, no total do resgate, para cima, e nunca passa do
rendimento. No extrato da conta, o resgate é uma linha só, com o líquido;
o bruto, o IOF e o IR saem na resposta e na consulta da operação.

CDI de teste: 1% ao dia (R$ 1.000,00 rendem R$ 10,00), para números
redondos. Todo teste começa com DbUtils.rollback() (o relógio volta a
2026-06-01) e programa no Mockserver a taxa de cada dia que fecha.
"""

from datetime import date, timedelta
from uuid import uuid4

from tests.utils import DbUtils, MockGenerator, ObjectGenerator, PayloadGenerator, RequestGenerator


ONE_PERCENT = "1.000000"
FIRST_DAY = date(2026, 6, 1)


def day(offset: int) -> str:
    """2026-06-01 + offset dias, em texto: o relógio começa em 2026-06-01 depois do DbUtils.rollback() (DIA-04)."""
    return (FIRST_DAY + timedelta(days=offset)).isoformat()


def close_day(accounting_date: str) -> None:
    status, response = RequestGenerator.POST_day_closing(PayloadGenerator.day_closing(accounting_date))
    assert status == 200, response


def save(account: dict, amount: int) -> None:
    status, response = RequestGenerator.POST_saving(account["account_key"], account["account_token"], PayloadGenerator.saving(amount=amount))
    assert status == 201, response


def redeem(account: dict, amount: int, request_control_key: str = None) -> dict:
    payload = PayloadGenerator.redemption(amount=amount, request_control_key=request_control_key)
    status, response = RequestGenerator.POST_redemption(account["account_key"], account["account_token"], payload)
    assert status == 201, response

    return response


def amounts_of(redemption: dict) -> tuple:
    """(bruto, IOF, IR, líquido)."""
    return redemption["gross_amount"], redemption["iof"], redemption["ir"], redemption["net_amount"]


def balances_of(account: dict) -> tuple:
    """(saldo da conta, saldo do cofrinho)."""
    status, response = RequestGenerator.GET_account(account["account_key"], account["account_token"])
    assert status == 200, response

    return response["balance"], response["piggy_bank_balance"]


def redemption_lines(account: dict) -> list:
    """(tipo de lançamento, valor) das linhas de resgate no extrato da conta principal."""
    status, response = RequestGenerator.GET_entries(account["account_key"], account["account_token"], {"limit": "100"})
    assert status == 200, response

    return [(entry["entry_type"], entry["amount"]) for entry in response["data"] if entry["transaction_type"] == "REDEEM"]


def create_account_with_one_day_yield() -> dict:
    """Uma conta que guardou R$ 1.000,00 em 2026-06-01; depois da virada desse dia, o lote tem 100000 + 1000 de rendimento, com 1 dia de prazo."""
    account = ObjectGenerator.create_funded_account(100000)
    save(account, 100000)
    close_day(day(0))
    assert balances_of(account) == (0, 101000)

    return account


class TestRedeemTaxes:
    def test_one_day_lot_pays_iof_and_ir_on_the_yield(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate(day(0), ONE_PERCENT)
        account = create_account_with_one_day_yield()

        request_control_key = str(uuid4())
        redemption = redeem(account, 101000, request_control_key)

        assert amounts_of(redemption) == (101000, 960, 9, 100031)
        assert (redemption["balance"], redemption["piggy_bank_balance"]) == (100031, 0)
        assert balances_of(account) == (100031, 0)
        assert redemption_lines(account) == [("AMOUNT", 100031)]

        status, operation = RequestGenerator.GET_transaction(account["account_key"], account["account_token"], redemption["transaction_key"])
        assert status == 200, operation
        assert amounts_of(operation) == (101000, 960, 9, 100031)
        assert [(entry["entry_type"], entry["amount"]) for entry in operation["entries"]] == [("AMOUNT", -101000), ("AMOUNT", 100031)]

        assert redeem(account, 101000, request_control_key) == redemption
        assert balances_of(account) == (100031, 0)
        MockGenerator.clear_cdi(day(0))

    def test_partial_redemption_taxes_only_the_yield_part(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate(day(0), ONE_PERCENT)
        account = create_account_with_one_day_yield()

        first = redeem(account, 50500)
        assert amounts_of(first) == (50500, 480, 5, 50015)
        assert balances_of(account) == (50015, 50500)

        second = redeem(account, 50500)
        assert amounts_of(second) == (50500, 480, 5, 50015)
        assert balances_of(account) == (100030, 0)
        MockGenerator.clear_cdi(day(0))

    def test_each_lot_pays_by_its_own_term(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate(day(0), ONE_PERCENT)
        MockGenerator.set_cdi_rate(day(1), ONE_PERCENT)
        account = ObjectGenerator.create_funded_account(100000)

        save(account, 50000)
        close_day(day(0))
        save(account, 50000)
        close_day(day(1))
        assert balances_of(account) == (0, 101505)

        redemption = redeem(account, 101505)

        assert amounts_of(redemption) == (101505, 1415, 21, 100069)
        assert balances_of(account) == (100069, 0)
        MockGenerator.clear_cdi(day(0))
        MockGenerator.clear_cdi(day(1))

    def test_no_iof_from_thirty_days(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate(day(0), ONE_PERCENT)
        for offset in range(1, 30):
            MockGenerator.set_cdi_rate(day(offset))

        account = create_account_with_one_day_yield()
        for offset in range(1, 30):
            close_day(day(offset))

        assert balances_of(account) == (0, 101000)

        redemption = redeem(account, 101000)

        assert amounts_of(redemption) == (101000, 0, 225, 100775)
        assert balances_of(account) == (100775, 0)
        for offset in range(30):
            MockGenerator.clear_cdi(day(offset))

    def test_tax_can_take_the_whole_yield_of_a_tiny_redemption(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate(day(0), ONE_PERCENT)
        account = create_account_with_one_day_yield()

        request_control_key = str(uuid4())
        redemption = redeem(account, 1, request_control_key)

        assert amounts_of(redemption) == (1, 1, 0, 0)
        assert (redemption["balance"], redemption["piggy_bank_balance"]) == (0, 100999)
        assert balances_of(account) == (0, 100999)
        assert redemption_lines(account) == []

        assert redeem(account, 1, request_control_key) == redemption
        MockGenerator.clear_cdi(day(0))
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/09-categorias-impostos-sorteio`; `git log --oneline -n 3` mostra `feat(impostos): IOF e IR do resgate com teste unitário`.
2. Crie `tests/integration/piggy_bank/test_redeem_taxes.py` com o conteúdo do campo **Arquivos**.
3. `docker compose up -d --build --wait`.
4. `./.venv/Scripts/python.exe -m pytest -v tests/integration/piggy_bank/test_redeem_taxes.py` → a última linha tem `5 failed` e não tem `passed`. Os 5 falham por asserção: hoje o resgate não cobra imposto (`iof` e `ir` saem 0, e o líquido é o bruto).
5. Edite `src/controllers/piggy_bank_controller.py` com o conteúdo do campo **Arquivos**.
6. Acrescente `get_balance_before` em `src/repositories/entry_repository.py`.
7. `docker compose up -d --build --wait`.
8. `./.venv/Scripts/python.exe -m pytest -v tests/integration/piggy_bank/test_redeem_taxes.py` → a última linha tem `5 passed`.
9. Rode a conferência D1 do **Verificar**.
10. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `351 passed`.
11. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
12. Rode o resto do **Verificar**.
13. Feche o passo (AGENTS.md, seção 7), um comando por vez:
    ```
    git add -- src/controllers/piggy_bank_controller.py src/repositories/entry_repository.py tests/integration/piggy_bank/test_redeem_taxes.py
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "feat(impostos): IOF e IR descontados no resgate do cofrinho"
    git log -1 --format=%B
    ```

**Testes:** `tests/integration/piggy_bank/test_redeem_taxes.py`. Todos começam com `DbUtils.rollback()` (o relógio volta a 2026-06-01) e programam o CDI de 1% no Mockserver. A ajudante `create_account_with_one_day_yield` abre uma conta, guarda 100000 e fecha 2026-06-01: o lote fica com 100000 + 1000 de rendimento, e o relógio em 2026-06-02 (1 dia de prazo). Efeito no banco de cada resgate com imposto: operação `REDEEM`; `AMOUNT` −bruto no cofrinho, na categoria; `AMOUNT` +líquido na conta (nenhum, se o líquido é 0); `IOF` e `IR` positivos na conta `BANK` (nenhum, se o imposto é 0); os lotes perdem o bruto, do mais antigo para o mais novo.

| Função de teste | Entrada | Esperado |
|---|---|---|
| `test_one_day_lot_pays_iof_and_ir_on_the_yield` | lote de 1 dia (100000 + 1000); resgate de 101000 com chave fixa; consulta da operação; o mesmo resgate de novo | 201 com bruto 101000, IOF 960, IR 9, líquido 100031, `balance` 100031, `piggy_bank_balance` 0; saldos (100031, 0); no extrato da conta, uma linha de `REDEEM`: `AMOUNT` +100031; a consulta traz os mesmos quatro valores e os lançamentos `AMOUNT` −101000 e `AMOUNT` +100031; a repetição devolve a mesma resposta e os saldos não mudam (COF-08, COF-12, COF-25, MOV-19) |
| `test_partial_redemption_taxes_only_the_yield_part` | lote de 1 dia; resgate de 50500; outro de 50500 | os dois com bruto 50500, IOF 480, IR 5, líquido 50015 (a parte de rendimento de cada um é 500); saldos (50015, 50500) e depois (100030, 0) (COF-24) |
| `test_each_lot_pays_by_its_own_term` | guarda 50000 em 2026-06-01, fecha o dia, guarda 50000, fecha 2026-06-02; resgate de 101505 | cofrinho 101505 antes; bruto 101505, IOF 1415, IR 21, líquido 100069 (lote de 2 dias: 50000 + 1005; lote de 1 dia: 50000 + 500); saldos (100069, 0) (COF-12) |
| `test_no_iof_from_thirty_days` | lote de 1 dia; mais 29 viradas sem taxa (relógio em 2026-07-01); resgate de 101000 | cofrinho 101000 antes; bruto 101000, IOF 0, IR 225, líquido 100775; saldos (100775, 0) |
| `test_tax_can_take_the_whole_yield_of_a_tiny_redemption` | lote de 1 dia; resgate de 1 com chave fixa; o mesmo resgate de novo | 201 com bruto 1, IOF 1, IR 0, líquido 0, `balance` 0, `piggy_bank_balance` 100999; saldos (0, 100999); nenhuma linha de `REDEEM` no extrato da conta; a repetição devolve a mesma resposta, sem erro 500 (COF-24, decisão de 08/10) |

**Verificar:**
- `./.venv/Scripts/python.exe -m pytest -v tests/integration/piggy_bank/test_redeem_taxes.py` → `5 passed`.
- `./.venv/Scripts/python.exe -m pytest -v tests/integration/piggy_bank/test_redeem.py tests/integration/piggy_bank/test_piggy_bank_entries.py` → a última linha tem `passed` e não tem `failed` (resgate sem rendimento não paga imposto, como antes).
- D1 — os lançamentos do resgate com imposto (COF-25, DAD-16). Um comando, numa linha só; começa com `DbUtils.rollback()`:
  ```
  ./.venv/Scripts/python.exe -c "from sqlalchemy import create_engine, text; from tests.utils import DbUtils, MockGenerator, ObjectGenerator, PayloadGenerator, RequestGenerator; DbUtils.rollback(); MockGenerator.set_cdi_rate('2026-06-01', '1.000000'); a = ObjectGenerator.create_funded_account(100000); k, t = a['account_key'], a['account_token']; s1 = RequestGenerator.POST_saving(k, t, PayloadGenerator.saving(amount=100000))[0]; s2 = RequestGenerator.POST_day_closing(PayloadGenerator.day_closing('2026-06-01'))[0]; s3, r = RequestGenerator.POST_redemption(k, t, PayloadGenerator.redemption(amount=101000)); print(s1, s2, s3, r['gross_amount'], r['iof'], r['ir'], r['net_amount']); c = create_engine(DbUtils.database_url()).connect(); print(c.execute(text('SELECT y.enumerator, w.enumerator, e.amount FROM entry e JOIN transaction x ON x.id = e.transaction_id JOIN account m ON m.id = e.account_id JOIN account_type y ON y.id = m.account_type_id JOIN entry_type w ON w.id = e.entry_type_id WHERE x.transaction_key = :t ORDER BY e.id'), {'t': r['transaction_key']}).fetchall()); print(c.execute(text('SELECT principal_remaining, yield_remaining FROM lot')).fetchall()); MockGenerator.clear_cdi('2026-06-01')"
  ```
  → exatamente (a soma dos quatro lançamentos é zero; o IOF e o IR só aparecem na conta `BANK`):
  ```
  201 200 201 101000 960 9 100031
  [('PIGGY_BANK', 'AMOUNT', -101000), ('CUSTOMER', 'AMOUNT', 100031), ('BANK', 'IOF', 960), ('BANK', 'IR', 9)]
  [(0, 0)]
  ```
- Conferência C1 (passo 7.12) → `0:0` (lotes, categorias e cofrinhos continuam batendo com os lançamentos).
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `351 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/controllers/piggy_bank_controller.py
  src/repositories/entry_repository.py
  tests/integration/piggy_bank/test_redeem_taxes.py
  ```
- `git log -1 --format=%B` → `feat(impostos): IOF e IR descontados no resgate do cofrinho`

**Pronto quando:**
- [ ] Os 5 testes falharam antes do código (item 4) e passam depois (item 8).
- [ ] `piggy_bank_controller.py` tem exatamente o conteúdo do campo **Arquivos**; `get_balance_before` está no fim de `EntryRepository`.
- [ ] D1 dá as 3 linhas esperadas; C1 dá `0:0`.
- [ ] Suíte com `351 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/09-categorias-impostos-sorteio`.

**Commit:** `feat(impostos): IOF e IR descontados no resgate do cofrinho`
**Pare se:**
- O item 4 não terminar com `5 failed`.
- O método `get_counterparty_category` não for o último de `src/repositories/entry_repository.py`.
- Um teste de `tests/integration/piggy_bank/` ou de `tests/integration/internal/` que já existia ficar vermelho.
- D1 ou C1 derem outra saída depois de 3 tentativas de conferir os arquivos do passo contra o plano.
- A suíte não terminar com `351 passed`.

---

### Passo 9.3 — Categorias: repository, DTO e controller
**Branch:** fase/09-categorias-impostos-sorteio · **Depende de:** 9.2
**Objetivo:** `CategoryRepository` ganha `create`, `get_by_key`, `list_active_page` e `delete` (muda o estado e grava o evento); `CategoryDTO`; `CategoryController` com `create_category`, `list_categories`, `get_category` e `delete_category`.
**Decisões:** COF-03 — categorias · COF-04 — excluir categoria · COF-05 — saldo por categoria · COF-18 — nome único · API-15 — excluir categoria · CLI-05 — encerrada só lê · CLI-09 — bloqueada mexe em categoria · R3 — `IntegrityError` nunca vira 500 · R4 — append-only · R5, DAD-12 — key para fora, UUID no repository · R8 — outro dono → 404 · MOV-05, MOV-11 — trava na ordem do `id`
**Arquivos:**
- `src/repositories/category_repository.py` (editar): o conteúdo inteiro passa a ser:

```python
from datetime import datetime
from uuid import uuid4

from sqlalchemy import func

from database import Context
from models import Account, Category, CategoryStatus, CategoryStatusEvent, Entry


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

    def get_balance(self, category: Category) -> int:
        """O saldo da categoria: a soma dos lançamentos do cofrinho nela, em centavos (COF-05, COF-23).

        Só os lançamentos do cofrinho têm category_id. O PostgreSQL devolve
        a soma de BIGINT como NUMERIC: o int() a traz de volta para centavos
        inteiros (DAD-08).
        """
        total = self.session.query(func.coalesce(func.sum(Entry.amount), 0)).filter(Entry.category_id == category.id).scalar()

        return int(total)

    def get_by_id(self, category_id: int) -> Category:
        """A categoria com este id; None quando não existe. O id só circula por dentro: para fora sai a category_key (R5)."""
        return self.session.query(Category).filter(Category.id == category_id).first()

    def create(self, piggy_bank: Account, name: str) -> Category:
        """Cria uma categoria do dono no cofrinho, ACTIVE e não padrão, e grava o evento do estado (COF-03, R4).

        A key nasce aqui, com uuid4 (DAD-12). O flush manda o INSERT na hora:
        um nome repetido entre as categorias ativas do cofrinho levanta aqui
        o IntegrityError do índice category_active_name_idx (COF-18).
        """
        category = Category()
        category.category_key = str(uuid4())
        category.account_id = piggy_bank.id
        category.status = self._get_status(CategoryStatus.ACTIVE)
        category.name = name
        category.is_default = False

        self.session.add(category)
        self.session.flush()

        self._add_status_event(category)

        return category

    def get_by_key(self, piggy_bank: Account, category_key: str) -> Category:
        """A categoria com esta key, se ela é deste cofrinho, ativa ou excluída; None nos outros casos (R8)."""
        return (
            self.session.query(Category)
            .filter(Category.account_id == piggy_bank.id, Category.category_key == category_key)
            .first()
        )

    def list_active_page(self, piggy_bank: Account, limit: int, offset: int) -> list:
        """Uma página das categorias ativas do cofrinho, na ordem em que foram criadas (created_at crescente; no empate, id crescente).

        Pede limit + 1 linhas: a linha a mais diz ao controller que existe
        próxima página (MOV-04).
        """
        return (
            self.session.query(Category)
            .join(Category.status)
            .filter(Category.account_id == piggy_bank.id, CategoryStatus.enumerator == CategoryStatus.ACTIVE)
            .order_by(Category.created_at, Category.id)
            .limit(limit + 1)
            .offset(offset)
            .all()
        )

    def delete(self, category: Category) -> None:
        """Exclui a categoria: o estado passa a DELETED e o evento é gravado, na mesma transação (API-15, R4). Nada é apagado."""
        category.status = self._get_status(CategoryStatus.DELETED)
        self._add_status_event(category)

    def _add_status_event(self, category: Category) -> None:
        status_event = CategoryStatusEvent()
        status_event.category_id = category.id
        status_event.status = category.status
        status_event.event_datetime = datetime.now()

        self.session.add(status_event)

    def _get_status(self, enumerator: str) -> CategoryStatus:
        """A linha de category_status pelo enumerator (ACTIVE ou DELETED)."""
        return self.session.query(CategoryStatus).filter(CategoryStatus.enumerator == enumerator).one()
```

  O que muda em relação ao 7.7: os métodos novos `create`, `get_by_key`, `list_active_page`, `delete`, `_add_status_event` e `_get_status`, no fim da classe. `create_default`, `get_default`, `get_balance` e `get_by_id` ficam iguais.

- `src/dtos/category_dto.py` (criar): o conteúdo inteiro é:

```python
from models import Category


class CategoryDTO:
    """A categoria que a API devolve: a key pública, nunca o id nem o account_id (R5)."""

    @staticmethod
    def only_obj_key(category: Category) -> dict:
        """A resposta da criação: só a key (API-10)."""
        return {"category_key": category.category_key}

    @staticmethod
    def obj_to_dict(category: Category, balance: int) -> dict:
        """A categoria na lista e na consulta: o saldo em centavos (COF-05) e o estado público em maiúsculas, ACTIVE ou DELETED (API-15, docs/rotas.md)."""
        return {
            "category_key": category.category_key,
            "name": category.name,
            "is_default": category.is_default,
            "status": category.status.enumerator,
            "balance": balance,
            "created_at": category.created_at.isoformat(),
        }
```

- `src/dtos/__init__.py` (editar): o conteúdo inteiro passa a ser:

```python
from dtos.customer_dto import CustomerDTO
from dtos.account_dto import AccountDTO
from dtos.transaction_dto import TransactionDTO
from dtos.entry_dto import EntryDTO
from dtos.gamification_dto import GamificationDTO
from dtos.category_dto import CategoryDTO
```

- `src/controllers/category_controller.py` (criar): o conteúdo inteiro é:

```python
from sqlalchemy.exc import IntegrityError

from controllers.base_controller import BaseController
from dtos import CategoryDTO
from errors import (
    AccountNotActive,
    CategoryDeleted,
    CategoryNotEmpty,
    CategoryNotFound,
    DefaultCategoryCannotBeDeleted,
    DuplicatedCategoryName,
)
from models import Account, AccountStatus, Category, CategoryStatus
from repositories import AccountRepository, CategoryRepository


class CategoryController(BaseController):
    """As regras das categorias do cofrinho: criar, listar, consultar e excluir (COF-03, COF-04, COF-05, COF-18, API-15).

    Conta bloqueada cria, lista e exclui categoria (CLI-09); conta
    encerrada só lê (CLI-05). Nenhuma categoria se apaga: excluir é mudar
    o estado para DELETED e gravar o evento (R4).
    """

    def __init__(self) -> None:
        super().__init__(__name__)
        self.account_repository = AccountRepository(self.context)
        self.category_repository = CategoryRepository(self.context)

    def create_category(self, account_key: str, account_token: str, category_data: dict) -> dict:
        """Cria uma categoria no cofrinho da conta (COF-03, COF-18). As regras, nesta ordem:

        1. a conta é do dono do token (404 QIT001010, R8);
        2. a conta não está CLOSED (409 QIT001011, CLI-05); BLOCKED cria
           (CLI-09);
        3. o nome não se repete entre as categorias ativas do cofrinho (409
           QIT001024, COF-18). Quem confere é o índice
           category_active_name_idx, na gravação: o IntegrityError desfaz
           tudo e vira o 409, nunca 500 (R3).

        Depois: a categoria ACTIVE, não padrão, e o evento do estado. A
        resposta traz só a key (API-10).
        """
        account = self.get_owned_account(account_key, account_token)
        account, piggy_bank = self._lock_account_and_piggy_bank(account)

        if account.status.enumerator == AccountStatus.CLOSED:
            raise AccountNotActive(account_key, account.status.enumerator)

        name = category_data["name"]

        try:
            category = self.category_repository.create(piggy_bank, name)

            category_dto = CategoryDTO.only_obj_key(category)
            self.session.commit()
        except IntegrityError:
            self.session.rollback()

            raise DuplicatedCategoryName(name)

        return category_dto

    def list_categories(self, account_key: str, account_token: str, limit: int, offset: int) -> dict:
        """Uma página das categorias ativas do cofrinho, com o saldo de cada uma, na ordem em que foram criadas (COF-05, API-15). Não grava nada.

        1. a conta é do dono do token (404 QIT001010, R8); encerrada também
           lê (CLI-05).

        Pede limit + 1 linhas ao repository: se veio a linha a mais, existe
        próxima página, e ela não entra na resposta.
        """
        account = self.get_owned_account(account_key, account_token)
        piggy_bank = self.account_repository.get_piggy_bank(account)

        rows = self.category_repository.list_active_page(piggy_bank, limit, offset)

        is_last_page = True
        if len(rows) > limit:
            is_last_page = False
            rows = rows[:-1]

        categories = []
        for category in rows:
            categories.append(CategoryDTO.obj_to_dict(category, self.category_repository.get_balance(category)))

        return {
            "categories_list_dto": categories,
            "is_last_page": is_last_page,
        }

    def get_category(self, account_key: str, account_token: str, category_key: str) -> dict:
        """Uma categoria do cofrinho, ativa ou excluída, com o saldo (COF-05, API-15). Não grava nada. As regras, nesta ordem:

        1. a conta é do dono do token (404 QIT001010, R8);
        2. a categoria existe neste cofrinho (404 QIT001021): a de outro
           cofrinho responde como se não existisse (R8).

        Excluída sai com status DELETED (API-15).
        """
        account = self.get_owned_account(account_key, account_token)
        piggy_bank = self.account_repository.get_piggy_bank(account)

        category = self._get_category(piggy_bank, category_key)

        return CategoryDTO.obj_to_dict(category, self.category_repository.get_balance(category))

    def delete_category(self, account_key: str, account_token: str, category_key: str) -> None:
        """Exclui uma categoria do cofrinho (COF-04, API-15). As regras, nesta ordem:

        1. a conta é do dono do token (404 QIT001010, R8);
        2. trava a conta e o cofrinho, na ordem do id, como guardar e
           resgatar (MOV-05, MOV-11): um guardar na mesma categoria espera a
           exclusão terminar, e depois vê a categoria excluída;
        3. a conta não está CLOSED (409 QIT001011, CLI-05); BLOCKED exclui
           (CLI-09);
        4. a categoria existe neste cofrinho (404 QIT001021, R8);
        5. a categoria não está excluída (409 QIT001022);
        6. a categoria não é a "economias" (409 QIT001025, COF-04);
        7. o saldo da categoria é 0 (409 QIT001026, COF-04).

        Depois: o estado DELETED e o evento, na mesma transação (R4). Sem
        corpo na resposta (204).
        """
        account = self.get_owned_account(account_key, account_token)
        account, piggy_bank = self._lock_account_and_piggy_bank(account)

        if account.status.enumerator == AccountStatus.CLOSED:
            raise AccountNotActive(account_key, account.status.enumerator)

        category = self._get_category(piggy_bank, category_key)

        if category.status.enumerator == CategoryStatus.DELETED:
            raise CategoryDeleted(category_key)

        if category.is_default:
            raise DefaultCategoryCannotBeDeleted(category_key)

        if self.category_repository.get_balance(category) != 0:
            raise CategoryNotEmpty(category_key)

        self.category_repository.delete(category)
        self.session.commit()

    def _get_category(self, piggy_bank: Account, category_key: str) -> Category:
        """A categoria com esta key neste cofrinho, ativa ou excluída; 404 QIT001021 quando não existe aqui (R8)."""
        category = self.category_repository.get_by_key(piggy_bank, category_key)

        if category is None:
            raise CategoryNotFound(category_key)

        return category

    def _lock_account_and_piggy_bank(self, account: Account) -> tuple:
        """A conta e o cofrinho dela, travados na ordem do id (MOV-05, MOV-11), com os valores relidos do banco."""
        piggy_bank = self.account_repository.get_piggy_bank(account)

        locked_accounts = {}
        for locked_account in self.account_repository.lock_accounts([account, piggy_bank]):
            locked_accounts[locked_account.id] = locked_account

        return locked_accounts[account.id], locked_accounts[piggy_bank.id]
```

- `src/controllers/__init__.py` (editar): o conteúdo inteiro passa a ser:

```python
from controllers.customer_controller import CustomerController
from controllers.account_controller import AccountController
from controllers.transaction_controller import TransactionController
from controllers.gamification_controller import GamificationController
from controllers.piggy_bank_controller import PiggyBankController
from controllers.day_closing_controller import DayClosingController
from controllers.category_controller import CategoryController
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/09-categorias-impostos-sorteio`; `git log --oneline -n 3` mostra `feat(impostos): IOF e IR descontados no resgate do cofrinho`.
2. Edite `src/repositories/category_repository.py` com o conteúdo do campo **Arquivos**.
3. Crie `src/dtos/category_dto.py` e edite `src/dtos/__init__.py` com o conteúdo do campo **Arquivos**.
4. Crie `src/controllers/category_controller.py` e edite `src/controllers/__init__.py` com o conteúdo do campo **Arquivos**.
5. `docker compose up -d --build --wait` → termina sem erro.
6. Rode as conferências S1 e G1 do **Verificar**.
7. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `351 passed`.
8. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
9. Feche o passo (AGENTS.md, seção 7), um comando por vez:
   ```
   git add -- src/repositories/category_repository.py src/dtos/category_dto.py src/dtos/__init__.py src/controllers/category_controller.py src/controllers/__init__.py
   git diff --cached --name-only
   git diff --name-only
   git ls-files --others --exclude-standard
   git commit -m "feat(categorias): repository, DTO e controller das categorias"
   git log -1 --format=%B
   ```

**Testes:** nenhum teste novo. O passo é de camada de baixo; as rotas dos passos 9.4 e 9.5 usam estas peças por HTTP, com os testes que ficam vermelhos antes delas. Aqui, a prova é a S1 (os nomes existem e a API sobe com eles) e a G1 (numa transação só, cria a categoria padrão e uma do dono, busca, lista, exclui, confere o evento e o DTO, e desfaz tudo).
**Verificar:**
- S1 (um comando, numa linha só):
  ```
  docker compose exec -T api python -c "from controllers import CategoryController; from controllers.base_controller import BaseController; from dtos import CategoryDTO; from repositories import CategoryRepository; print(sorted(n for n in vars(CategoryController) if not n.startswith('__'))); print(sorted(n for n in vars(CategoryRepository) if not n.startswith('__'))); print(sorted(n for n in vars(CategoryDTO) if not n.startswith('_')), issubclass(CategoryController, BaseController))"
  ```
  → exatamente:
  ```
  ['_get_category', '_lock_account_and_piggy_bank', 'create_category', 'delete_category', 'get_category', 'list_categories']
  ['_add_status_event', '_get_status', 'create', 'create_default', 'delete', 'get_balance', 'get_by_id', 'get_by_key', 'get_default', 'list_active_page']
  ['obj_to_dict', 'only_obj_key'] True
  ```
- G1 (um comando, numa linha só):
  ```
  docker compose exec -T api python -c "from datetime import date; from database import open_context; from dtos import CategoryDTO; from models import CategoryStatusEvent; from repositories import AccountRepository, CategoryRepository, CustomerRepository; c = open_context(); s = c.get_or_create_session(); x = CustomerRepository(c).create('Ana Lima', '529.982.247-25', 'ana.conferencia.g1@example.com', date(1995, 4, 12)); s.flush(); r = AccountRepository(c); a = r.create_customer_account(x, '0' * 64); p = r.get_piggy_bank(a); cr = CategoryRepository(c); g = cr.create_default(p); k = cr.create(p, 'carro'); s.flush(); print(len(k.category_key), k.is_default, k.status.enumerator, cr.get_by_key(p, k.category_key) is k, cr.get_by_key(a, k.category_key), cr.get_by_key(p, 'nao-existe')); print([y.name for y in cr.list_active_page(p, 10, 0)], [y.name for y in cr.list_active_page(p, 1, 0)], [y.name for y in cr.list_active_page(p, 1, 1)]); cr.delete(k); s.flush(); print(k.status.enumerator, [y.name for y in cr.list_active_page(p, 10, 0)], cr.get_by_key(p, k.category_key) is k); print([e.status.enumerator for e in s.query(CategoryStatusEvent).filter(CategoryStatusEvent.category_id == k.id).order_by(CategoryStatusEvent.id)]); d = CategoryDTO.obj_to_dict(k, 0); print(sorted(d), d['status'], d['balance'], d['is_default']); s.rollback()"
  ```
  → exatamente:
  ```
  36 False ACTIVE True None None
  ['economias', 'carro'] ['economias', 'carro'] ['carro']
  DELETED ['economias'] True
  ['ACTIVE', 'DELETED']
  ['balance', 'category_key', 'created_at', 'is_default', 'name', 'status'] DELETED 0 False
  ```
  (a segunda linha mostra o `limit + 1`: com limit 1, vêm 2 categorias; a terceira linha mostra que a categoria excluída continua no banco, com os dois eventos)
- `git grep -n -e "session.delete" -e "DELETE FROM" -- src/repositories/category_repository.py` → nenhuma linha (excluir só muda o estado e grava o evento, R4).
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `351 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/controllers/__init__.py
  src/controllers/category_controller.py
  src/dtos/__init__.py
  src/dtos/category_dto.py
  src/repositories/category_repository.py
  ```
- `git log -1 --format=%B` → `feat(categorias): repository, DTO e controller das categorias`

**Pronto quando:**
- [ ] Os cinco arquivos têm exatamente o conteúdo do campo **Arquivos**.
- [ ] S1 dá as 3 linhas esperadas; G1 dá as 5.
- [ ] Suíte com `351 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/09-categorias-impostos-sorteio`.

**Commit:** `feat(categorias): repository, DTO e controller das categorias`
**Pare se:**
- `docker compose up -d --build --wait` falhar com `ImportError` ou `circular import` no `docker compose logs --tail 100 api`: traga a saída.
- A G1 terminar com `IntegrityError` com `customer_document_number_key` ou `customer_email_key`: rode `docker compose down -v`, `docker compose up -d --build --wait` e a G1 de novo; repetindo o erro, PARE.
- S1 ou G1 derem outra saída depois de 3 tentativas de conferir os cinco arquivos contra o plano.
- A suíte não terminar com `351 passed`.

---

### Passo 9.4 — Criar e listar categorias
**Branch:** fase/09-categorias-impostos-sorteio · **Depende de:** 9.3
**Objetivo:** `CategoryResource` com `on_post` e `on_get_list`; as rotas `POST` e `GET /accounts/{account_key}/categories` (só as ativas, com saldo, na ordem em que foram criadas).
**Decisões:** COF-03 — categorias · COF-05 — saldo por categoria · COF-18 — nome único · CLI-09 — bloqueada mexe em categoria · CLI-05 — encerrada só lê · MOV-04 — paginação · API-02 — status de sucesso no resource · API-03 — schema fechado · R8 — outro dono → 404 · TST-01 — black box e TDD
**Arquivos:**
- `src/resources/category.py` (criar): o conteúdo inteiro é:

```python
from fastapi import Request
from fastapi import status as http_status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from constants import ACCOUNT_TOKEN_HEADER
from controllers import CategoryController
from utils.schema_handler import SchemaHandler


# MOV-04: a lista de categorias começa na página 0, com 10 itens, quando a query string não diz.
DEFAULT_LIMIT = 10
DEFAULT_PAGE = 0


class CategoryResource:
    """A porta HTTP das categorias do cofrinho: criar e listar (consultar e excluir entram no 9.5).

    Sem regra de negócio, sem SQL e sem nada guardado no self (ARQ-02). O
    token da conta chega no cabeçalho ACCOUNT-TOKEN (API-16); quem o
    confere é o controller.
    """

    @SchemaHandler.validate("post_categories.json")
    def on_post(self, account_key: str, payload: dict, request: Request) -> JSONResponse:
        controller = CategoryController()
        category = controller.create_category(account_key, request.headers.get(ACCOUNT_TOKEN_HEADER), payload)

        return JSONResponse(
            content=jsonable_encoder(category),
            status_code=http_status.HTTP_201_CREATED,
        )

    @SchemaHandler.validate_query_params("get_categories.json")
    def on_get_list(self, account_key: str, request: Request) -> JSONResponse:
        """Uma página das categorias ativas. O schema get_categories.json já garantiu limit e page."""
        controller = CategoryController()

        query_params = request.query_params
        limit = int(query_params.get("limit", DEFAULT_LIMIT))
        page = int(query_params.get("page", DEFAULT_PAGE))
        offset = page * limit

        categories_page = controller.list_categories(account_key, request.headers.get(ACCOUNT_TOKEN_HEADER), limit, offset)

        # O envelope da página fala de limit e page, vocabulário de HTTP: quem o monta é o resource, como no base.
        page_envelope = {
            "data": categories_page["categories_list_dto"],
            "limit": limit,
            "page": page,
            "is_last_page": categories_page["is_last_page"],
        }

        return JSONResponse(
            content=jsonable_encoder(page_envelope),
            status_code=http_status.HTTP_200_OK,
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
from resources.category import CategoryResource
```

- `src/app.py` (editar): três trocas, e nada mais.
  1. A linha
     ```python
     from resources import AccountResource, CustomerResource, GamificationResource, HealthCheckResource, InternalResource, PiggyBankResource, TransactionResource
     ```
     vira
     ```python
     from resources import AccountResource, CategoryResource, CustomerResource, GamificationResource, HealthCheckResource, InternalResource, PiggyBankResource, TransactionResource
     ```
  2. A linha
     ```python
         piggy_bank_resource = PiggyBankResource()
     ```
     vira as duas linhas
     ```python
         piggy_bank_resource = PiggyBankResource()
         category_resource = CategoryResource()
     ```
  3. A linha
     ```python
         application.add_api_route("/accounts/{account_key}/piggy_bank_entries", piggy_bank_resource.on_get_piggy_bank_entries, methods=["GET"])
     ```
     vira as cinco linhas
     ```python
         application.add_api_route("/accounts/{account_key}/piggy_bank_entries", piggy_bank_resource.on_get_piggy_bank_entries, methods=["GET"])

         # Categorias do cofrinho
         application.add_api_route("/accounts/{account_key}/categories", category_resource.on_post, methods=["POST"])
         application.add_api_route("/accounts/{account_key}/categories", category_resource.on_get_list, methods=["GET"])
     ```

- `tests/integration/categories/test_create_and_list_categories.py` (criar; a pasta `tests/integration/categories/` é nova e fica sem `__init__.py`): o conteúdo inteiro é:

```python
"""Criar e listar categorias: POST e GET /accounts/{account_key}/categories (COF-03, COF-05, COF-18, CLI-05, CLI-09, MOV-04, API-03, R5, R8).

O cofrinho nasce com a "economias"; o dono cria as suas. O nome não se
repete entre as categorias ativas do mesmo cofrinho. A lista traz só as
ativas, com o saldo de cada uma, na ordem em que foram criadas, no
envelope do extrato. Conta bloqueada cria; encerrada só lê. Os testes que
erram o token começam com DbUtils.rollback() (PRD-10).
"""

from uuid import uuid4

from tests.utils import DbUtils, ObjectGenerator, PayloadGenerator, RequestGenerator


CATEGORY_FIELDS = ["balance", "category_key", "created_at", "is_default", "name", "status"]


def create_category(account: dict, name: str) -> tuple:
    return RequestGenerator.POST_category(account["account_key"], account["account_token"], PayloadGenerator.category(name=name))


def list_categories(account: dict, params: dict = None) -> dict:
    status, response = RequestGenerator.GET_categories(account["account_key"], account["account_token"], params)
    assert status == 200, response

    return response


def names_and_balances(page: dict) -> list:
    return [(category["name"], category["balance"]) for category in page["data"]]


class TestCreateAndListCategories:
    def test_new_account_lists_only_economias(self):
        account = ObjectGenerator.create_account()

        page = list_categories(account)

        assert (page["limit"], page["page"], page["is_last_page"]) == (10, 0, True)
        assert len(page["data"]) == 1

        economias = page["data"][0]
        assert sorted(economias) == CATEGORY_FIELDS
        assert (economias["name"], economias["is_default"], economias["status"], economias["balance"]) == ("economias", True, "ACTIVE", 0)
        assert len(economias["category_key"]) == 36
        assert type(economias["balance"]) is int

    def test_creates_category(self):
        account = ObjectGenerator.create_account()

        status, response = create_category(account, "carro")

        assert status == 201, response
        assert list(response) == ["category_key"]
        assert len(response["category_key"]) == 36

        page = list_categories(account)
        assert names_and_balances(page) == [("economias", 0), ("carro", 0)]

        carro = page["data"][1]
        assert (carro["category_key"], carro["is_default"], carro["status"]) == (response["category_key"], False, "ACTIVE")

    def test_lists_the_balance_of_each_category(self):
        account = ObjectGenerator.create_funded_account(50000)
        status, response = create_category(account, "viagem")
        assert status == 201, response

        status, response = RequestGenerator.POST_saving(account["account_key"], account["account_token"], PayloadGenerator.saving(amount=30000))
        assert status == 201, response

        assert names_and_balances(list_categories(account)) == [("economias", 30000), ("viagem", 0)]

    def test_duplicated_active_name_is_409(self):
        account = ObjectGenerator.create_account()
        other_account = ObjectGenerator.create_account()

        status, response = create_category(account, "carro")
        assert status == 201, response

        for name in ["carro", "economias"]:
            status, response = create_category(account, name)
            assert status == 409, (name, response)
            assert response["code"] == "QIT001024"

        assert names_and_balances(list_categories(account)) == [("economias", 0), ("carro", 0)]

        status, response = create_category(other_account, "carro")
        assert status == 201, response

    def test_blocked_account_creates_and_lists(self):
        account = ObjectGenerator.create_account()

        status, response = RequestGenerator.POST_block(account["account_key"], PayloadGenerator.block())
        assert status == 204, response

        status, response = create_category(account, "reserva")
        assert status == 201, response

        assert names_and_balances(list_categories(account)) == [("economias", 0), ("reserva", 0)]

    def test_closed_account_refuses_creating_but_lists(self):
        account = ObjectGenerator.create_account()

        status, response = RequestGenerator.DELETE_account(account["account_key"], account["account_token"])
        assert status == 204, response

        status, response = create_category(account, "carro")
        assert status == 409, response
        assert response["code"] == "QIT001011"

        assert names_and_balances(list_categories(account)) == [("economias", 0)]

    def test_pagination(self):
        account = ObjectGenerator.create_account()
        names = [f"c{number:02d}" for number in range(1, 12)]

        for name in names:
            status, response = create_category(account, name)
            assert status == 201, response

        first = list_categories(account, {"limit": "5", "page": "0"})
        second = list_categories(account, {"limit": "5", "page": "1"})
        third = list_categories(account, {"limit": "5", "page": "2"})

        assert [category["name"] for category in first["data"]] == ["economias"] + names[:4]
        assert [category["name"] for category in second["data"]] == names[4:9]
        assert [category["name"] for category in third["data"]] == names[9:]
        assert (first["is_last_page"], second["is_last_page"], third["is_last_page"]) == (False, False, True)
        assert (third["limit"], third["page"]) == (5, 2)

    def test_refuses_body_and_query_out_of_schema(self):
        account = ObjectGenerator.create_account()

        for payload in [{}, {"name": ""}, {"name": 1}, {"name": "x" * 256}, {"name": "carro", "is_default": True}]:
            status, response = RequestGenerator.POST_category(account["account_key"], account["account_token"], payload)
            assert status == 400, (payload, response)
            assert response["code"] == "QIT000001"

        for params in [{"limit": "0"}, {"limit": "101"}, {"limit": "abc"}, {"page": "-1"}, {"status": "DELETED"}]:
            status, response = RequestGenerator.GET_categories(account["account_key"], account["account_token"], params)
            assert status == 400, (params, response)
            assert response["code"] == "QIT000001"

        assert names_and_balances(list_categories(account)) == [("economias", 0)]

    def test_other_account_token_is_404(self):
        DbUtils.rollback()
        account_a = ObjectGenerator.create_account()
        account_b = ObjectGenerator.create_account()

        status, response = RequestGenerator.POST_category(account_a["account_key"], account_b["account_token"], PayloadGenerator.category(name="carro"))
        assert status == 404, response
        assert response["code"] == "QIT001010"

        status, response = RequestGenerator.GET_categories(account_a["account_key"], account_b["account_token"])
        assert status == 404, response
        assert response["code"] == "QIT001010"

        assert names_and_balances(list_categories(account_a)) == [("economias", 0)]

    def test_missing_or_wrong_token_is_404(self):
        DbUtils.rollback()
        account = ObjectGenerator.create_account()

        for account_token in [None, "token_errado"]:
            status, response = RequestGenerator.GET_categories(account["account_key"], account_token)
            assert status == 404, response
            assert response["code"] == "QIT001010"

        status, response = RequestGenerator.POST_category(str(uuid4()), account["account_token"], PayloadGenerator.category())
        assert status == 404, response
        assert response["code"] == "QIT001010"
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/09-categorias-impostos-sorteio`; `git log --oneline -n 3` mostra `feat(categorias): repository, DTO e controller das categorias`.
2. Crie `tests/integration/categories/test_create_and_list_categories.py` com o conteúdo do campo **Arquivos**.
3. `docker compose up -d --build --wait`.
4. `./.venv/Scripts/python.exe -m pytest -v tests/integration/categories/test_create_and_list_categories.py` → a última linha tem `10 failed` e não tem `passed`. Os 10 falham por asserção: as rotas ainda não existem, e a API responde 404 `QIT000404`.
5. Crie `src/resources/category.py` e edite `src/resources/__init__.py` com o conteúdo do campo **Arquivos**.
6. Faça as três trocas em `src/app.py`.
7. `docker compose up -d --build --wait`.
8. `./.venv/Scripts/python.exe -m pytest -v tests/integration/categories/test_create_and_list_categories.py` → a última linha tem `10 passed`.
9. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `361 passed`.
10. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
11. Rode o **Verificar**.
12. Feche o passo (AGENTS.md, seção 7), um comando por vez:
    ```
    git add -- src/resources/category.py src/resources/__init__.py src/app.py tests/integration/categories/test_create_and_list_categories.py
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "feat(categorias): rotas de criar e listar categorias"
    git log -1 --format=%B
    ```

**Testes:** `tests/integration/categories/test_create_and_list_categories.py`. As duas rotas pedem `INTERNAL-TOKEN` e `ACCOUNT-TOKEN` (da conta da URL).

`POST /accounts/{account_key}/categories` — corpo `{"name": "<1 a 255 caracteres>"}` (`post_categories.json`). Respostas: 201 `{"category_key": "<uuid>"}`; 400 `QIT000001` (corpo fora do schema); 404 `QIT001010` (conta não é do token); 409 `QIT001011` (conta encerrada); 409 `QIT001024` (nome de categoria ativa do mesmo cofrinho). Efeito no banco do 201: uma linha em `category` (`ACTIVE`, `is_default` falso, `account_id` = id do cofrinho) e uma em `category_status_event` (`ACTIVE`).

`GET /accounts/{account_key}/categories?limit=&page=` (`get_categories.json`, padrão `limit` 10 e `page` 0). Respostas: 200 `{"data": [{"category_key", "name", "is_default", "status", "balance", "created_at"}], "limit", "page", "is_last_page"}`, só as ativas, na ordem em que foram criadas; 400 `QIT000001`; 404 `QIT001010`. Não grava nada.

| Função de teste | Entrada | Esperado |
|---|---|---|
| `test_new_account_lists_only_economias` | conta nova; `GET` sem query | 200 com `limit` 10, `page` 0, `is_last_page` verdadeiro e uma categoria: `economias`, `is_default` verdadeiro, `ACTIVE`, saldo 0 (`int`), key de 36 caracteres, exatamente os seis campos (COF-03, R5) |
| `test_creates_category` | `POST` com `carro`; `GET` | 201 só com `category_key` (36); a lista é `economias` e `carro`, nessa ordem, com saldo 0; `carro` tem a key do 201, `is_default` falso e `ACTIVE` |
| `test_lists_the_balance_of_each_category` | conta com 50000; cria `viagem`; guarda 30000 sem `category_key` | a lista mostra `economias` com 30000 e `viagem` com 0 (COF-05) |
| `test_duplicated_active_name_is_409` | cria `carro`; cria `carro` de novo; cria `economias`; outra conta cria `carro` | 201; 409 `QIT001024` nas duas tentativas, e a lista continua com duas categorias; 201 na outra conta (o nome é único por cofrinho) (COF-18) |
| `test_blocked_account_creates_and_lists` | conta bloqueada pela rota interna; cria `reserva`; `GET` | 204 no bloqueio; 201; a lista tem `economias` e `reserva` (CLI-09) |
| `test_closed_account_refuses_creating_but_lists` | conta encerrada (saldo e cofrinho zerados); cria `carro`; `GET` | 409 `QIT001011`; 200 só com `economias` (CLI-05) |
| `test_pagination` | cria `c01` a `c11` (12 categorias); `limit` 5, `page` 0, 1 e 2 | `economias`, `c01` a `c04`; `c05` a `c09`; `c10` e `c11`; `is_last_page` falso, falso e verdadeiro; a última página diz `limit` 5 e `page` 2 (MOV-04) |
| `test_refuses_body_and_query_out_of_schema` | corpos `{}`, nome vazio, nome número, nome de 256 caracteres, campo a mais; query `limit=0`, `limit=101`, `limit=abc`, `page=-1`, `status=DELETED` | 400 `QIT000001` nos dez; nada criado (API-03) |
| `test_other_account_token_is_404` | começa com `DbUtils.rollback()`; key da conta A com o token da conta B, no `POST` e no `GET` | 404 `QIT001010` nos dois; a conta A continua só com `economias` (R8) |
| `test_missing_or_wrong_token_is_404` | começa com `DbUtils.rollback()`; `GET` sem token e com token errado; `POST` numa key de conta que não existe | 404 `QIT001010` nos três (R8) |

**Verificar:**
- `./.venv/Scripts/python.exe -m pytest -v tests/integration/categories/test_create_and_list_categories.py` → `10 passed`.
- `git grep -n "categories" -- src/app.py` → exatamente duas linhas, com `category_resource.on_post` e `category_resource.on_get_list`.
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `361 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/app.py
  src/resources/__init__.py
  src/resources/category.py
  tests/integration/categories/test_create_and_list_categories.py
  ```
- `git log -1 --format=%B` → `feat(categorias): rotas de criar e listar categorias`

**Pronto quando:**
- [ ] Os 10 testes falharam antes do código (item 4) e passam depois (item 8).
- [ ] Os arquivos têm exatamente o conteúdo e as trocas do campo **Arquivos**.
- [ ] Suíte com `361 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/09-categorias-impostos-sorteio`.

**Commit:** `feat(categorias): rotas de criar e listar categorias`
**Pare se:**
- O item 4 não terminar com `10 failed`.
- Alguma das três linhas de `src/app.py` não for encontrada igual.
- Um teste recusar o corpo `{"name": "carro"}` com 400 `QIT000001`: o `post_categories.json` da fase 3 não é o esperado; traga o arquivo.
- A suíte não terminar com `361 passed`.

---

### Passo 9.5 — Consultar e excluir categoria
**Branch:** fase/09-categorias-impostos-sorteio · **Depende de:** 9.4
**Objetivo:** `CategoryResource.on_get_by_key` e `on_delete_by_key`; as rotas `GET` e `DELETE /accounts/{account_key}/categories/{category_key}`; a excluída aparece com `status` `DELETED`.
**Decisões:** COF-04 — excluir categoria · API-15 — excluir categoria · COF-18 — nome único · CLI-05 — encerrada só lê · CLI-09 — bloqueada mexe em categoria · R4 — append-only · R8 — outro dono → 404 · API-02 — 204 sem corpo · TST-01 — black box e TDD
**Arquivos:**
- `src/resources/category.py` (editar): o conteúdo inteiro passa a ser:

```python
from fastapi import Request, Response
from fastapi import status as http_status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from constants import ACCOUNT_TOKEN_HEADER
from controllers import CategoryController
from utils.schema_handler import SchemaHandler


# MOV-04: a lista de categorias começa na página 0, com 10 itens, quando a query string não diz.
DEFAULT_LIMIT = 10
DEFAULT_PAGE = 0


class CategoryResource:
    """A porta HTTP das categorias do cofrinho: criar, listar, consultar e excluir.

    Sem regra de negócio, sem SQL e sem nada guardado no self (ARQ-02). O
    token da conta chega no cabeçalho ACCOUNT-TOKEN (API-16); quem o
    confere é o controller.
    """

    @SchemaHandler.validate("post_categories.json")
    def on_post(self, account_key: str, payload: dict, request: Request) -> JSONResponse:
        controller = CategoryController()
        category = controller.create_category(account_key, request.headers.get(ACCOUNT_TOKEN_HEADER), payload)

        return JSONResponse(
            content=jsonable_encoder(category),
            status_code=http_status.HTTP_201_CREATED,
        )

    @SchemaHandler.validate_query_params("get_categories.json")
    def on_get_list(self, account_key: str, request: Request) -> JSONResponse:
        """Uma página das categorias ativas. O schema get_categories.json já garantiu limit e page."""
        controller = CategoryController()

        query_params = request.query_params
        limit = int(query_params.get("limit", DEFAULT_LIMIT))
        page = int(query_params.get("page", DEFAULT_PAGE))
        offset = page * limit

        categories_page = controller.list_categories(account_key, request.headers.get(ACCOUNT_TOKEN_HEADER), limit, offset)

        # O envelope da página fala de limit e page, vocabulário de HTTP: quem o monta é o resource, como no base.
        page_envelope = {
            "data": categories_page["categories_list_dto"],
            "limit": limit,
            "page": page,
            "is_last_page": categories_page["is_last_page"],
        }

        return JSONResponse(
            content=jsonable_encoder(page_envelope),
            status_code=http_status.HTTP_200_OK,
        )

    def on_get_by_key(self, account_key: str, category_key: str, request: Request) -> JSONResponse:
        controller = CategoryController()
        category = controller.get_category(account_key, request.headers.get(ACCOUNT_TOKEN_HEADER), category_key)

        return JSONResponse(
            content=jsonable_encoder(category),
            status_code=http_status.HTTP_200_OK,
        )

    def on_delete_by_key(self, account_key: str, category_key: str, request: Request) -> Response:
        controller = CategoryController()
        controller.delete_category(account_key, request.headers.get(ACCOUNT_TOKEN_HEADER), category_key)

        return Response(status_code=http_status.HTTP_204_NO_CONTENT)
```

  O que muda em relação ao 9.4: `Response` no import do `fastapi`, a docstring da classe e os métodos `on_get_by_key` e `on_delete_by_key`, no fim.

- `src/app.py` (editar): uma troca, e nada mais. A linha
  ```python
      application.add_api_route("/accounts/{account_key}/categories", category_resource.on_get_list, methods=["GET"])
  ```
  vira as três linhas
  ```python
      application.add_api_route("/accounts/{account_key}/categories", category_resource.on_get_list, methods=["GET"])
      application.add_api_route("/accounts/{account_key}/categories/{category_key}", category_resource.on_get_by_key, methods=["GET"])
      application.add_api_route("/accounts/{account_key}/categories/{category_key}", category_resource.on_delete_by_key, methods=["DELETE"])
  ```

- `tests/integration/categories/test_get_and_delete_category.py` (criar): o conteúdo inteiro é:

```python
"""Consultar e excluir categoria: GET e DELETE /accounts/{account_key}/categories/{category_key} (COF-04, COF-18, API-15, CLI-05, CLI-09, R4, R5, R8).

A consulta devolve a categoria ativa ou excluída; a excluída sai com
status DELETED. Excluir só muda o estado e grava o evento: a categoria
some da lista, e o nome pode ser usado de novo. A "economias" nunca é
excluída. Conta bloqueada exclui; encerrada só lê. Os testes que erram o
token começam com DbUtils.rollback() (PRD-10).
"""

from uuid import uuid4

from tests.utils import DbUtils, ObjectGenerator, PayloadGenerator, RequestGenerator


CATEGORY_FIELDS = ["balance", "category_key", "created_at", "is_default", "name", "status"]


def create_category(account: dict, name: str) -> str:
    status, response = RequestGenerator.POST_category(account["account_key"], account["account_token"], PayloadGenerator.category(name=name))
    assert status == 201, response

    return response["category_key"]


def get_category(account: dict, category_key: str) -> tuple:
    return RequestGenerator.GET_category(account["account_key"], account["account_token"], category_key)


def delete_category(account: dict, category_key: str) -> tuple:
    return RequestGenerator.DELETE_category(account["account_key"], account["account_token"], category_key)


def active_names(account: dict) -> list:
    status, response = RequestGenerator.GET_categories(account["account_key"], account["account_token"])
    assert status == 200, response

    return [category["name"] for category in response["data"]]


def default_category_key(account: dict) -> str:
    status, response = RequestGenerator.GET_categories(account["account_key"], account["account_token"])
    assert status == 200, response

    return response["data"][0]["category_key"]


def status_of(account: dict, category_key: str) -> str:
    status, response = get_category(account, category_key)
    assert status == 200, response

    return response["status"]


class TestGetAndDeleteCategory:
    def test_gets_active_category(self):
        account = ObjectGenerator.create_account()
        category_key = create_category(account, "carro")

        status, response = get_category(account, category_key)

        assert status == 200, response
        assert sorted(response) == CATEGORY_FIELDS
        assert (response["category_key"], response["name"], response["is_default"], response["status"], response["balance"]) == (category_key, "carro", False, "ACTIVE", 0)

        status, response = get_category(account, default_category_key(account))
        assert status == 200, response
        assert (response["name"], response["is_default"], response["status"]) == ("economias", True, "ACTIVE")

    def test_deletes_empty_category(self):
        account = ObjectGenerator.create_account()
        category_key = create_category(account, "carro")

        status, response = delete_category(account, category_key)
        assert status == 204, response
        assert response is None

        status, response = get_category(account, category_key)
        assert status == 200, response
        assert (response["name"], response["status"], response["balance"]) == ("carro", "DELETED", 0)
        assert active_names(account) == ["economias"]

        status, response = delete_category(account, category_key)
        assert status == 409, response
        assert response["code"] == "QIT001022"

    def test_name_can_be_used_again_after_delete(self):
        account = ObjectGenerator.create_account()
        old_key = create_category(account, "carro")

        status, response = delete_category(account, old_key)
        assert status == 204, response

        new_key = create_category(account, "carro")

        assert new_key != old_key
        assert active_names(account) == ["economias", "carro"]
        assert status_of(account, old_key) == "DELETED"
        assert status_of(account, new_key) == "ACTIVE"

    def test_default_category_cannot_be_deleted(self):
        account = ObjectGenerator.create_account()
        category_key = default_category_key(account)

        status, response = delete_category(account, category_key)
        assert status == 409, response
        assert response["code"] == "QIT001025"

        assert status_of(account, category_key) == "ACTIVE"
        assert active_names(account) == ["economias"]

    def test_unknown_category_is_404(self):
        account = ObjectGenerator.create_account()
        other_account = ObjectGenerator.create_account()
        other_key = create_category(other_account, "carro")

        for category_key in [str(uuid4()), "nao-e-uma-key", other_key]:
            for send in [get_category, delete_category]:
                status, response = send(account, category_key)
                assert status == 404, (category_key, response)
                assert response["code"] == "QIT001021"

        assert status_of(other_account, other_key) == "ACTIVE"

    def test_blocked_account_deletes(self):
        account = ObjectGenerator.create_account()
        category_key = create_category(account, "reserva")

        status, response = RequestGenerator.POST_block(account["account_key"], PayloadGenerator.block())
        assert status == 204, response

        status, response = delete_category(account, category_key)
        assert status == 204, response
        assert status_of(account, category_key) == "DELETED"

    def test_closed_account_refuses_deleting_but_reads(self):
        account = ObjectGenerator.create_account()
        category_key = create_category(account, "carro")

        status, response = RequestGenerator.DELETE_account(account["account_key"], account["account_token"])
        assert status == 204, response

        status, response = delete_category(account, category_key)
        assert status == 409, response
        assert response["code"] == "QIT001011"

        assert status_of(account, category_key) == "ACTIVE"

    def test_other_account_token_is_404(self):
        DbUtils.rollback()
        account_a = ObjectGenerator.create_account()
        account_b = ObjectGenerator.create_account()
        category_key = create_category(account_a, "carro")

        for send in [RequestGenerator.GET_category, RequestGenerator.DELETE_category]:
            status, response = send(account_a["account_key"], account_b["account_token"], category_key)
            assert status == 404, response
            assert response["code"] == "QIT001010"

        assert status_of(account_a, category_key) == "ACTIVE"

    def test_missing_or_wrong_token_is_404(self):
        DbUtils.rollback()
        account = ObjectGenerator.create_account()
        category_key = create_category(account, "carro")

        for account_token in [None, "token_errado"]:
            for send in [RequestGenerator.GET_category, RequestGenerator.DELETE_category]:
                status, response = send(account["account_key"], account_token, category_key)
                assert status == 404, response
                assert response["code"] == "QIT001010"

        assert status_of(account, category_key) == "ACTIVE"
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/09-categorias-impostos-sorteio`; `git log --oneline -n 3` mostra `feat(categorias): rotas de criar e listar categorias`.
2. Crie `tests/integration/categories/test_get_and_delete_category.py` com o conteúdo do campo **Arquivos**.
3. `docker compose up -d --build --wait`.
4. `./.venv/Scripts/python.exe -m pytest -v tests/integration/categories/test_get_and_delete_category.py` → a última linha tem `9 failed` e não tem `passed`. Os 9 falham por asserção: as duas rotas ainda não existem, e a API responde 404 `QIT000404`.
5. Edite `src/resources/category.py` com o conteúdo do campo **Arquivos**.
6. Faça a troca em `src/app.py`.
7. `docker compose up -d --build --wait`.
8. `./.venv/Scripts/python.exe -m pytest -v tests/integration/categories/test_get_and_delete_category.py` → a última linha tem `9 passed`.
9. Rode a conferência E1 do **Verificar**.
10. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `370 passed`.
11. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
12. Rode o resto do **Verificar**.
13. Feche o passo (AGENTS.md, seção 7), um comando por vez:
    ```
    git add -- src/resources/category.py src/app.py tests/integration/categories/test_get_and_delete_category.py
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "feat(categorias): rotas de consultar e excluir categoria"
    git log -1 --format=%B
    ```

**Testes:** `tests/integration/categories/test_get_and_delete_category.py`. As duas rotas pedem `INTERNAL-TOKEN` e `ACCOUNT-TOKEN` (da conta da URL); nenhuma tem corpo nem query string.

`GET /accounts/{account_key}/categories/{category_key}` — 200 `{"category_key", "name", "is_default", "status", "balance", "created_at"}`, ativa (`ACTIVE`) ou excluída (`DELETED`); 404 `QIT001010` (conta não é do token); 404 `QIT001021` (categoria não é deste cofrinho, ou a key não existe ou é mal formada). Não grava nada.

`DELETE /accounts/{account_key}/categories/{category_key}` — 204 sem corpo; 404 `QIT001010`; 409 `QIT001011` (conta encerrada); 404 `QIT001021`; 409 `QIT001022` (já excluída); 409 `QIT001025` (`economias`); 409 `QIT001026` (com saldo; o teste é do 9.6, porque só o 9.6 guarda em categoria do dono). Efeito no banco do 204: `category.status_id` passa a `DELETED` e entra uma linha `DELETED` em `category_status_event`; nada é apagado (R4).

| Função de teste | Entrada | Esperado |
|---|---|---|
| `test_gets_active_category` | cria `carro`; `GET` dela; `GET` da `economias` | 200 com exatamente os seis campos: key do 201, `carro`, `is_default` falso, `ACTIVE`, saldo 0; a `economias` com `is_default` verdadeiro e `ACTIVE` |
| `test_deletes_empty_category` | cria `carro`; `DELETE`; `GET`; lista; `DELETE` de novo | 204 sem corpo; 200 com `carro`, `DELETED`, saldo 0; a lista só tem `economias`; 409 `QIT001022` (COF-04, API-15) |
| `test_name_can_be_used_again_after_delete` | cria `carro`; exclui; cria `carro` de novo | 201 com outra key; a lista tem `economias` e o `carro` novo; a key velha continua `DELETED` e a nova é `ACTIVE` (COF-18) |
| `test_default_category_cannot_be_deleted` | `DELETE` da `economias` | 409 `QIT001025`; ela continua `ACTIVE` e na lista (COF-04) |
| `test_unknown_category_is_404` | `GET` e `DELETE` com uma key aleatória, com `nao-e-uma-key` e com a key de uma categoria de outra conta | 404 `QIT001021` nos seis; a categoria da outra conta continua `ACTIVE` (R8) |
| `test_blocked_account_deletes` | cria `reserva`; bloqueia a conta; `DELETE` | 204; `DELETED` (CLI-09) |
| `test_closed_account_refuses_deleting_but_reads` | cria `carro`; encerra a conta; `DELETE`; `GET` | 409 `QIT001011`; 200 com `ACTIVE` (CLI-05) |
| `test_other_account_token_is_404` | começa com `DbUtils.rollback()`; a categoria da conta A pela key de A com o token de B, no `GET` e no `DELETE` | 404 `QIT001010` nos dois; a categoria continua `ACTIVE` (R8) |
| `test_missing_or_wrong_token_is_404` | começa com `DbUtils.rollback()`; `GET` e `DELETE` sem token e com token errado | 404 `QIT001010` nos quatro; a categoria continua `ACTIVE` (R8) |

**Verificar:**
- `./.venv/Scripts/python.exe -m pytest -v tests/integration/categories/test_get_and_delete_category.py` → `9 passed`.
- E1 — a exclusão grava o evento e não apaga nada (R4, API-15). Um comando, numa linha só:
  ```
  ./.venv/Scripts/python.exe -c "from sqlalchemy import create_engine, text; from tests.utils import DbUtils, ObjectGenerator, PayloadGenerator, RequestGenerator; a = ObjectGenerator.create_account(); k, t = a['account_key'], a['account_token']; s1, r = RequestGenerator.POST_category(k, t, PayloadGenerator.category(name='carro')); g = r['category_key']; s2 = RequestGenerator.DELETE_category(k, t, g)[0]; s3, r = RequestGenerator.POST_category(k, t, PayloadGenerator.category(name='carro')); print(s1, s2, s3, r['category_key'] != g); c = create_engine(DbUtils.database_url()).connect(); print(c.execute(text('SELECT s.enumerator FROM category_status_event e JOIN category_status s ON s.id = e.status_id JOIN category y ON y.id = e.category_id WHERE y.category_key = :g ORDER BY e.id'), {'g': g}).fetchall()); print(c.execute(text('SELECT y.name, s.enumerator, y.is_default FROM category y JOIN category_status s ON s.id = y.status_id JOIN account p ON p.id = y.account_id JOIN account m ON m.id = p.parent_account_id WHERE m.account_key = :k ORDER BY y.id'), {'k': k}).fetchall())"
  ```
  → exatamente:
  ```
  201 204 201 True
  [('ACTIVE',), ('DELETED',)]
  [('economias', 'ACTIVE', True), ('carro', 'DELETED', False), ('carro', 'ACTIVE', False)]
  ```
- `git grep -n "categories" -- src/app.py` → exatamente quatro linhas: `on_post`, `on_get_list`, `on_get_by_key` e `on_delete_by_key`.
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `370 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/app.py
  src/resources/category.py
  tests/integration/categories/test_get_and_delete_category.py
  ```
- `git log -1 --format=%B` → `feat(categorias): rotas de consultar e excluir categoria`

**Pronto quando:**
- [ ] Os 9 testes falharam antes do código (item 4) e passam depois (item 8).
- [ ] `src/resources/category.py` tem exatamente o conteúdo do campo **Arquivos**; a troca de `src/app.py` está feita.
- [ ] E1 dá as 3 linhas esperadas.
- [ ] Suíte com `370 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/09-categorias-impostos-sorteio`.

**Commit:** `feat(categorias): rotas de consultar e excluir categoria`
**Pare se:**
- O item 4 não terminar com `9 failed`.
- A linha de `src/app.py` não for encontrada igual.
- Um teste de `test_create_and_list_categories.py` ficar vermelho.
- E1 der outra saída depois de 3 tentativas de conferir os arquivos do passo contra o plano.
- A suíte não terminar com `370 passed`.

---

### Passo 9.6 — Guardar e resgatar por categoria
**Branch:** fase/09-categorias-impostos-sorteio · **Depende de:** 9.5
**Objetivo:** `save` e `redeem` usam a `category_key` do corpo (sem ela, "economias"): categoria de outro cofrinho → 404 `QIT001021`; excluída → 409 `QIT001022`; resgate maior que a categoria → 422 `QIT001023`. O extrato do cofrinho filtra por qualquer categoria do cofrinho, ativa ou excluída.
**Decisões:** COF-03 — categorias · COF-04 — excluir só zerada · COF-06 — lotes por categoria · COF-07 — resgate maior que a categoria · COF-12 — imposto por lote · COF-19 — sem mover entre categorias · API-15 — guardar em excluída · R8 — outro dono → 404 · TST-01 — black box e TDD
**Arquivos:**
- `src/controllers/piggy_bank_controller.py` (editar): o conteúdo inteiro passa a ser:

```python
from datetime import date

from sqlalchemy.exc import IntegrityError

from calculations import redemption_taxes, split_redemption
from controllers.base_controller import BaseController
from controllers.gamification_controller import GamificationController
from dtos import EntryDTO, TransactionDTO
from errors import (
    AccountNotActive,
    CategoryDeleted,
    CategoryNotFound,
    IdempotencyKeyConflict,
    InsufficientBalance,
    InsufficientCategoryBalance,
)
from models import Account, AccountStatus, AccountType, Category, CategoryStatus, EntryType, Transaction, TransactionType
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
        5. a categoria: sem category_key no corpo, a "economias" (COF-03);
           com category_key, uma categoria deste cofrinho (404 QIT001021)
           que não foi excluída (409 QIT001022, API-15);
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

        # MOV-19: reconsultar depois da espera pela trava, antes de estado e saldo.
        repeated_transaction = self._find_repeated(request_control_key, request_hash)
        if repeated_transaction is not None:
            return self._saving_response(repeated_transaction, account)

        if account.status.enumerator != AccountStatus.ACTIVE:
            raise AccountNotActive(account_key, account.status.enumerator)

        category = self._get_active_category(piggy_bank, saving_data.get("category_key"))
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
        """Resgatar: traz dinheiro de uma categoria do cofrinho para a conta, com IOF e IR (COF-06, COF-07, COF-08, COF-10, COF-12, COF-24, COF-25). As regras, nesta ordem:

        1. a conta é do dono do token (404 QIT001010, R8);
        2. a mesma request_control_key com o mesmo pedido devolve a resposta
           da primeira vez (MOV-19); com outro pedido, 409 QIT001014 (MOV-12);
        3. trava a conta e o cofrinho (MOV-05);
        4. a conta está ACTIVE (409 QIT001011, CLI-09);
        5. a categoria: sem category_key no corpo, a "economias" (COF-03);
           com category_key, uma categoria deste cofrinho (404 QIT001021)
           que não foi excluída (409 QIT001022, API-15);
        6. o saldo da categoria cobre o valor (422 QIT001023, COF-07), mesmo
           que o cofrinho todo tenha o dinheiro.

        Depois: a operação REDEEM; o valor bruto sai dos lotes da categoria,
        do mais antigo para o mais novo, cada um até zerar (COF-06), e de
        cada lote o principal e o rendimento saem na proporção do lote
        (COF-24). O IOF e o IR incidem só sobre o rendimento, pelo prazo de
        cada lote (redemption_taxes, COF-12). Os lançamentos, nesta ordem:
        AMOUNT −bruto no cofrinho, na categoria; AMOUNT +líquido na conta
        (líquido = bruto − IOF − IR); IOF +IOF e IR +IR na conta BANK
        (COF-25). Valor zero não gera lançamento. No extrato da conta, o
        resgate é uma linha só, com o líquido; o bruto, o IOF e o IR saem na
        resposta e na consulta da operação. O ranque não cai (GAM-19) e o
        recorde não muda (GAM-04). A resposta traz a key, os dois saldos, o
        bruto, o IOF, o IR e o líquido (COF-08).
        """
        account = self.get_owned_account(account_key, account_token)

        request_control_key = redemption_data["request_control_key"]
        request_hash = hash_request_body(TransactionType.REDEEM, account_key, redemption_data)

        repeated_transaction = self._find_repeated(request_control_key, request_hash)
        if repeated_transaction is not None:
            return self._redemption_response(repeated_transaction, account)

        accounting_date = self.bank_clock_repository.get_accounting_date()
        account, piggy_bank = self._lock_account_and_piggy_bank(account)

        # MOV-19: reconsultar depois da espera pela trava, antes de estado e saldo.
        repeated_transaction = self._find_repeated(request_control_key, request_hash)
        if repeated_transaction is not None:
            return self._redemption_response(repeated_transaction, account)

        if account.status.enumerator != AccountStatus.ACTIVE:
            raise AccountNotActive(account_key, account.status.enumerator)

        category = self._get_active_category(piggy_bank, redemption_data.get("category_key"))
        amount = redemption_data["amount"]

        if self.category_repository.get_balance(category) < amount:
            raise InsufficientCategoryBalance(category.category_key)

        bank = self.account_repository.get_system_account(AccountType.BANK)

        try:
            transaction = self.transaction_repository.create(TransactionType.REDEEM, request_control_key, request_hash, accounting_date)
            yield_parts = self._take_from_lots(category, amount, accounting_date)
            iof, ir = redemption_taxes(yield_parts)
            net_amount = amount - iof - ir

            self.entry_repository.create(transaction, piggy_bank, EntryType.AMOUNT, -amount, category)

            if net_amount > 0:
                self.entry_repository.create(transaction, account, EntryType.AMOUNT, net_amount)

            if iof > 0:
                self.entry_repository.create(transaction, bank, EntryType.IOF, iof)

            if ir > 0:
                self.entry_repository.create(transaction, bank, EntryType.IR, ir)

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
        trocado). IOF e IR: os lançamentos IOF e IR da conta BANK (COF-25).
        Líquido: bruto − IOF − IR, o que entrou na conta. A consulta da
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

    def list_piggy_bank_entries(self, account_key: str, account_token: str, limit: int, offset: int, category_key: str = None) -> dict:
        """Uma página do extrato do cofrinho, só para o dono (COF-05, MOV-04, MOV-14). Não grava nada. As regras, nesta ordem:

        1. a conta é do dono do token (404 QIT001010, R8);
        2. com category_key, a categoria existe neste cofrinho (404
           QIT001021), ativa ou excluída (docs/rotas.md).

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

    def _take_from_lots(self, category: Category, amount: int, accounting_date: date) -> list:
        """Tira o valor dos lotes da categoria, do mais antigo para o mais novo, cada um até zerar (COF-06).

        De cada lote, principal e rendimento saem na proporção dele
        (split_redemption, COF-24); o resíduo fica. Devolve, por lote de
        onde saiu dinheiro, a tupla (dias de prazo, centavos de rendimento)
        que redemption_taxes recebe: o prazo é a data contábil do resgate
        menos a do lote, em dias corridos (COF-12).
        """
        remaining = amount
        yield_parts = []

        for lot in self.lot_repository.list_open_for_update(category):
            if remaining == 0:
                break

            taken = min(remaining, lot.principal_remaining + lot.yield_remaining)
            principal_part, yield_part = split_redemption(lot.principal_remaining, lot.yield_remaining, taken)

            self.lot_repository.update_remaining(lot, lot.principal_remaining - principal_part, lot.yield_remaining - yield_part, lot.residue)

            yield_parts.append(((accounting_date - lot.accounting_date).days, yield_part))
            remaining = remaining - taken

        return yield_parts

    def _get_category(self, piggy_bank: Account, category_key: str) -> Category:
        """A categoria do pedido, ativa ou excluída: sem category_key, a "economias" (COF-03).

        Com category_key, só uma categoria deste cofrinho: a de outro
        cofrinho responde como se não existisse, 404 QIT001021 (R8).
        """
        if category_key is None:
            return self.category_repository.get_default(piggy_bank)

        category = self.category_repository.get_by_key(piggy_bank, category_key)

        if category is None:
            raise CategoryNotFound(category_key)

        return category

    def _get_active_category(self, piggy_bank: Account, category_key: str) -> Category:
        """A categoria do pedido (_get_category), que precisa estar ativa: excluída responde 409 QIT001022 (API-15).

        Guardar e resgatar usam esta; o extrato do cofrinho usa a
        _get_category, que aceita a excluída. Não existe mover dinheiro
        entre categorias: resgata de uma e guarda na outra (COF-19).
        """
        category = self._get_category(piggy_bank, category_key)

        if category.status.enumerator == CategoryStatus.DELETED:
            raise CategoryDeleted(category.category_key)

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
        """O saldo da conta (ou do cofrinho) logo depois da operação: o balance_after do último lançamento dela na operação (MOV-19).

        O resgate cujo líquido é 0 (o imposto levou todo o rendimento de um
        resgate só de rendimento) não tem lançamento na conta: o saldo dela
        é o de antes da operação.
        """
        entries = self.entry_repository.list_by_transaction(transaction, [account.id])

        if not entries:
            return self.entry_repository.get_balance_before(account, transaction)

        return entries[-1].balance_after

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

  O que muda em relação ao 9.2: `CategoryDeleted` e `CategoryStatus` nos imports; o item 5 da docstring de `save` e de `redeem`; `save` e `redeem` chamam `_get_active_category`; o item 2 da docstring de `list_piggy_bank_entries`; `_get_category` busca pela key no cofrinho; o método novo `_get_active_category`, logo depois de `_get_category`. Preservar os demais métodos e as correções da auditoria anterior: reconsulta após trava e logs críticos.

- `tests/integration/piggy_bank/test_category_money.py` (criar): o conteúdo inteiro é:

```python
"""Guardar e resgatar por categoria: POST .../savings e .../redemptions com category_key (COF-03, COF-04, COF-06, COF-07, COF-12, COF-19, API-15, R8).

Cada categoria tem os seus lotes: o resgate sai só da categoria
escolhida, do lote mais antigo dela, mesmo que o cofrinho todo tenha mais
dinheiro. Não existe mover dinheiro entre categorias. Categoria excluída
não guarda nem resgata (409); categoria de outro cofrinho responde como se
não existisse (404). Categoria com dinheiro não é excluída; zerada, pode
ser.
"""

from datetime import date, timedelta
from uuid import uuid4

from tests.utils import DbUtils, MockGenerator, ObjectGenerator, PayloadGenerator, RequestGenerator


ONE_PERCENT = "1.000000"
FIRST_DAY = date(2026, 6, 1)


def day(offset: int) -> str:
    """2026-06-01 + offset dias, em texto: o relógio começa em 2026-06-01 depois do DbUtils.rollback() (DIA-04)."""
    return (FIRST_DAY + timedelta(days=offset)).isoformat()


def create_category(account: dict, name: str) -> str:
    status, response = RequestGenerator.POST_category(account["account_key"], account["account_token"], PayloadGenerator.category(name=name))
    assert status == 201, response

    return response["category_key"]


def save(account: dict, amount: int, category_key: str = None) -> tuple:
    payload = PayloadGenerator.saving(amount=amount, category_key=category_key)

    return RequestGenerator.POST_saving(account["account_key"], account["account_token"], payload)


def redeem(account: dict, amount: int, category_key: str = None) -> tuple:
    payload = PayloadGenerator.redemption(amount=amount, category_key=category_key)

    return RequestGenerator.POST_redemption(account["account_key"], account["account_token"], payload)


def category_balances(account: dict) -> list:
    """(nome, saldo) das categorias ativas, na ordem em que foram criadas."""
    status, response = RequestGenerator.GET_categories(account["account_key"], account["account_token"])
    assert status == 200, response

    return [(category["name"], category["balance"]) for category in response["data"]]


def balances_of(account: dict) -> tuple:
    """(saldo da conta, saldo do cofrinho)."""
    status, response = RequestGenerator.GET_account(account["account_key"], account["account_token"])
    assert status == 200, response

    return response["balance"], response["piggy_bank_balance"]


class TestCategoryMoney:
    def test_saves_and_redeems_in_a_created_category(self):
        account = ObjectGenerator.create_funded_account(100000)
        carro = create_category(account, "carro")

        status, response = save(account, 30000, carro)
        assert status == 201, response
        assert (response["balance"], response["piggy_bank_balance"]) == (70000, 30000)
        assert category_balances(account) == [("economias", 0), ("carro", 30000)]

        status, response = redeem(account, 30000, carro)
        assert status == 201, response
        assert (response["gross_amount"], response["net_amount"]) == (30000, 30000)
        assert balances_of(account) == (100000, 0)

        assert category_balances(account) == [("economias", 0), ("carro", 0)]

        status, response = RequestGenerator.GET_piggy_bank_entries(account["account_key"], account["account_token"], {"category_key": carro})
        assert status == 200, response
        assert [(entry["transaction_type"], entry["amount"], entry["category"]["name"]) for entry in response["data"]] == [
            ("REDEEM", -30000, "carro"),
            ("SAVE", 30000, "carro"),
        ]

    def test_redemption_comes_only_from_the_chosen_category(self):
        account = ObjectGenerator.create_funded_account(100000)
        carro = create_category(account, "carro")

        status, response = save(account, 30000)
        assert status == 201, response
        status, response = save(account, 10000, carro)
        assert status == 201, response

        status, response = redeem(account, 10001, carro)
        assert status == 422, response
        assert response["code"] == "QIT001023"
        assert category_balances(account) == [("economias", 30000), ("carro", 10000)]

        status, response = redeem(account, 10000, carro)
        assert status == 201, response
        assert category_balances(account) == [("economias", 30000), ("carro", 0)]
        assert balances_of(account) == (70000, 30000)

    def test_each_category_has_its_own_lots_and_taxes(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate(day(0), ONE_PERCENT)
        account = ObjectGenerator.create_funded_account(40000)
        carro = create_category(account, "carro")

        status, response = save(account, 30000)
        assert status == 201, response
        status, response = save(account, 10000, carro)
        assert status == 201, response

        status, response = RequestGenerator.POST_day_closing(PayloadGenerator.day_closing(day(0)))
        assert status == 200, response
        assert category_balances(account) == [("economias", 30300), ("carro", 10100)]

        status, response = redeem(account, 10100, carro)
        assert status == 201, response
        assert (response["gross_amount"], response["iof"], response["ir"], response["net_amount"]) == (10100, 96, 1, 10003)
        assert category_balances(account) == [("economias", 30300), ("carro", 0)]
        assert balances_of(account) == (10003, 30300)
        MockGenerator.clear_cdi(day(0))

    def test_deleted_category_refuses_saving_and_redemption(self):
        account = ObjectGenerator.create_funded_account(10000)
        carro = create_category(account, "carro")

        status, response = save(account, 1000, carro)
        assert status == 201, response
        status, response = redeem(account, 1000, carro)
        assert status == 201, response

        status, response = RequestGenerator.DELETE_category(account["account_key"], account["account_token"], carro)
        assert status == 204, response

        for send in [save, redeem]:
            status, response = send(account, 1000, carro)
            assert status == 409, response
            assert response["code"] == "QIT001022"

        status, response = RequestGenerator.GET_piggy_bank_entries(account["account_key"], account["account_token"], {"category_key": carro})
        assert status == 200, response
        assert len(response["data"]) == 2
        assert balances_of(account) == (10000, 0)

    def test_category_of_another_piggy_bank_is_404(self):
        account = ObjectGenerator.create_funded_account(10000)
        other_account = ObjectGenerator.create_account()
        own_key = create_category(account, "carro")
        other_key = create_category(other_account, "carro")

        status, response = save(account, 1000, own_key)
        assert status == 201, response

        for category_key in [other_key, str(uuid4())]:
            for send in [save, redeem]:
                status, response = send(account, 1000, category_key)
                assert status == 404, (category_key, response)
                assert response["code"] == "QIT001021"

            status, response = RequestGenerator.GET_piggy_bank_entries(account["account_key"], account["account_token"], {"category_key": category_key})
            assert status == 404, response
            assert response["code"] == "QIT001021"

        assert balances_of(account) == (9000, 1000)
        assert category_balances(other_account) == [("economias", 0), ("carro", 0)]

    def test_category_with_money_cannot_be_deleted(self):
        account = ObjectGenerator.create_funded_account(10000)
        carro = create_category(account, "carro")

        status, response = save(account, 1000, carro)
        assert status == 201, response

        status, response = RequestGenerator.DELETE_category(account["account_key"], account["account_token"], carro)
        assert status == 409, response
        assert response["code"] == "QIT001026"
        assert category_balances(account) == [("economias", 0), ("carro", 1000)]

        status, response = redeem(account, 1000, carro)
        assert status == 201, response

        status, response = RequestGenerator.DELETE_category(account["account_key"], account["account_token"], carro)
        assert status == 204, response
        assert category_balances(account) == [("economias", 0)]
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/09-categorias-impostos-sorteio`; `git log --oneline -n 3` mostra `feat(categorias): rotas de consultar e excluir categoria`.
2. Crie `tests/integration/piggy_bank/test_category_money.py` com o conteúdo do campo **Arquivos**.
3. `docker compose up -d --build --wait`.
4. `./.venv/Scripts/python.exe -m pytest -v tests/integration/piggy_bank/test_category_money.py` → a última linha tem `6 failed` e não tem `passed`. Os 6 falham por asserção: hoje guardar numa categoria criada pelo dono responde 404 `QIT001021`, e o teste espera 201.
5. Edite `src/controllers/piggy_bank_controller.py` com o conteúdo do campo **Arquivos**.
6. `docker compose up -d --build --wait`.
7. `./.venv/Scripts/python.exe -m pytest -v tests/integration/piggy_bank/test_category_money.py` → a última linha tem `6 passed`.
8. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `376 passed`.
9. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
10. Rode o **Verificar**.
11. Feche o passo (AGENTS.md, seção 7), um comando por vez:
    ```
    git add -- src/controllers/piggy_bank_controller.py tests/integration/piggy_bank/test_category_money.py
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "feat(categorias): guardar e resgatar por categoria"
    git log -1 --format=%B
    ```

**Testes:** `tests/integration/piggy_bank/test_category_money.py`. As rotas são as da fase 7 (`POST .../savings`, `POST .../redemptions`, `GET .../piggy_bank_entries`), agora com a `category_key` de uma categoria criada pelo dono. Efeito no banco de cada 201: o da fase 7 e do 9.2, com o `category_id` da categoria escolhida no lançamento do cofrinho, e o lote nela (guardar) ou tirado só dos lotes dela (resgatar).

| Função de teste | Entrada | Esperado |
|---|---|---|
| `test_saves_and_redeems_in_a_created_category` | conta com 100000; cria `carro`; guarda 30000 nela; resgata 30000 dela; extrato do cofrinho filtrado por `carro` | 201 com saldos (70000, 30000); categorias `economias` 0 e `carro` 30000; resgate com bruto e líquido 30000; saldos (100000, 0); `carro` continua na lista, com 0 (COF-04: zerada não some); o extrato tem `REDEEM` −30000 e `SAVE` +30000, os dois em `carro` (COF-03, COF-05) |
| `test_redemption_comes_only_from_the_chosen_category` | guarda 30000 em `economias` e 10000 em `carro`; resgata 10001 de `carro`; resgata 10000 de `carro` | 422 `QIT001023`, mesmo com 40000 no cofrinho, e nada muda; depois 201, `carro` 0, `economias` 30000, saldos (70000, 30000) (COF-07, COF-19) |
| `test_each_category_has_its_own_lots_and_taxes` | começa com `DbUtils.rollback()`; CDI de 1% em 2026-06-01; guarda 30000 em `economias` e 10000 em `carro`; fecha o dia; resgata 10100 de `carro` | `economias` 30300 e `carro` 10100 depois da virada; bruto 10100, IOF 96, IR 1 (22,5% de 4 = 0,9), líquido 10003; `economias` continua 30300; saldos (10003, 30300) (COF-06, COF-12) |
| `test_deleted_category_refuses_saving_and_redemption` | guarda 1000 em `carro` e resgata 1000; exclui `carro`; guarda e resgata nela; extrato do cofrinho filtrado por `carro` | 204 na exclusão; 409 `QIT001022` nos dois; o extrato responde 200 com os 2 lançamentos (filtrar por excluída vale); saldos (10000, 0) (API-15) |
| `test_category_of_another_piggy_bank_is_404` | guarda 1000 na própria `carro`; guarda, resgata e filtra o extrato com a `carro` de outra conta e com uma key aleatória | 201; 404 `QIT001021` nos seis; saldos (9000, 1000); a `carro` da outra conta continua com 0 (R8) |
| `test_category_with_money_cannot_be_deleted` | guarda 1000 em `carro`; exclui; resgata 1000; exclui | 409 `QIT001026`, e `carro` continua com 1000; depois 201 e 204, e a lista só tem `economias` (COF-04) |

**Verificar:**
- `./.venv/Scripts/python.exe -m pytest -v tests/integration/piggy_bank/test_category_money.py` → `6 passed`.
- `./.venv/Scripts/python.exe -m pytest -v tests/integration/piggy_bank/` → a última linha tem `passed` e não tem `failed` (os testes de guardar, resgatar e extrato da fase 7, com categoria aleatória → 404 `QIT001021`, continuam verdes).
- `git grep -n "_get_active_category(" -- src/controllers/piggy_bank_controller.py` → exatamente três linhas: a chamada em `save`, a chamada em `redeem` e o `def`.
- Conferência C1 (passo 7.12) → `0:0`.
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `376 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/controllers/piggy_bank_controller.py
  tests/integration/piggy_bank/test_category_money.py
  ```
- `git log -1 --format=%B` → `feat(categorias): guardar e resgatar por categoria`

**Pronto quando:**
- [ ] Os 6 testes falharam antes do código (item 4) e passam depois (item 7).
- [ ] `piggy_bank_controller.py` tem exatamente o conteúdo do campo **Arquivos**.
- [ ] C1 dá `0:0`.
- [ ] Suíte com `376 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/09-categorias-impostos-sorteio`.

**Commit:** `feat(categorias): guardar e resgatar por categoria`
**Pare se:**
- O item 4 não terminar com `6 failed`.
- Um teste de `tests/integration/piggy_bank/`, `tests/integration/categories/` ou `tests/integration/internal/` que já existia ficar vermelho.
- C1 der outra saída.
- A suíte não terminar com `376 passed`.

---

### Passo 9.7 — Sorteio (unitário)
**Branch:** fase/09-categorias-impostos-sorteio · **Depende de:** 9.6
**Objetivo:** `PRIZE_LIMIT_CENTS = 10000`, `is_eligible_for_prize` e `draw_prize(chance_points, rng)` (`rng.randrange(1000) < chance_points`) em `src/calculations/lottery.py`, com o teste unitário escrito antes.
**Decisões:** GAM-10 — chance de não debitar · GAM-11 — ponto vale igual · GAM-22 — sorteio até R$ 100 · TST-05 — contas puras com unitário · TST-06 — sorteio com gerador injetável
**Arquivos:**
- `tests/unit/test_lottery.py` (criar): o conteúdo inteiro é:

```python
"""Sorteio da chance de não debitar: calculations.lottery (GAM-10, GAM-11, GAM-22, TST-05, TST-06).

Unitário: importa só de calculations, da biblioteca padrão e do pytest.
O gerador de números é falso (TST-06): devolve sempre o número que o
teste escolheu e anota com que limite foi chamado.
"""

import pytest

from calculations import DRAW_SIZE, PRIZE_LIMIT_CENTS, calculate_fee, draw_prize, is_eligible_for_prize


class FakeRandom:
    """Gerador falso: randrange devolve sempre `value` e guarda o limite pedido."""

    def __init__(self, value: int) -> None:
        self.value = value
        self.stops = []

    def randrange(self, stop: int) -> int:
        self.stops.append(stop)

        return self.value


class TestEligibility:
    def test_prize_limit_is_one_hundred_reais(self):
        assert PRIZE_LIMIT_CENTS == 10000
        assert DRAW_SIZE == 1000

    def test_eligible_up_to_the_limit(self):
        assert is_eligible_for_prize(1) is True
        assert is_eligible_for_prize(10000) is True
        assert is_eligible_for_prize(10001) is False
        assert is_eligible_for_prize(9223372036854775807) is False

    def test_refuses_invalid_amount(self):
        for amount_cents in [0, -1]:
            with pytest.raises(ValueError):
                is_eligible_for_prize(amount_cents)

        with pytest.raises(TypeError):
            is_eligible_for_prize(100.0)


class TestDrawPrize:
    def test_each_point_is_one_in_a_thousand(self):
        rng = FakeRandom(0)
        assert draw_prize(1, rng) is True
        assert rng.stops == [1000]

        assert draw_prize(1, FakeRandom(1)) is False
        assert draw_prize(10, FakeRandom(9)) is True
        assert draw_prize(10, FakeRandom(10)) is False
        assert draw_prize(10, FakeRandom(999)) is False

    def test_without_points_never_wins(self):
        for value in [0, 1, 999]:
            assert draw_prize(0, FakeRandom(value)) is False

    def test_refuses_invalid_points(self):
        for chance_points in [-1, 11]:
            with pytest.raises(ValueError):
                draw_prize(chance_points, FakeRandom(0))

        with pytest.raises(TypeError):
            draw_prize(1.0, FakeRandom(0))

    def test_one_chance_point_is_worth_one_fee_point_at_the_limit(self):
        fee_point_saving = calculate_fee(PRIZE_LIMIT_CENTS, 0) - calculate_fee(PRIZE_LIMIT_CENTS, 1)
        winning_numbers = sum(1 for value in range(DRAW_SIZE) if draw_prize(1, FakeRandom(value)))

        assert fee_point_saving == 10
        assert winning_numbers * PRIZE_LIMIT_CENTS // DRAW_SIZE == fee_point_saving

    def test_returns_bool(self):
        assert type(is_eligible_for_prize(500)) is bool
        assert type(draw_prize(5, FakeRandom(3))) is bool
```

- `src/calculations/lottery.py` (criar): o conteúdo inteiro é:

```python
"""Sorteio da chance de não debitar (GAM-10, GAM-11, GAM-22). Conta pura: sem banco e sem HTTP.

O gerador de números entra por parâmetro (TST-06): na API, o do sistema
operacional; no teste, um falso, que devolve o número que o teste quer.
"""


# GAM-22: concorre a transferência de até R$ 100,00, sem contar a tarifa.
PRIZE_LIMIT_CENTS = 10000

# GAM-10: cada ponto em chance vale 0,1 p.p. = 1 número em 1000.
DRAW_SIZE = 1000

# GAM-10, GAM-15: no máximo 10 pontos em chance (1%).
MAX_CHANCE_POINTS = 10


def is_eligible_for_prize(amount_cents: int) -> bool:
    """True quando a transferência concorre ao sorteio: valor de 1 a PRIZE_LIMIT_CENTS centavos, sem a tarifa (GAM-22)."""
    if type(amount_cents) is not int:
        raise TypeError(f"amount_cents precisa ser int, veio {type(amount_cents).__name__}")

    if amount_cents < 1:
        raise ValueError(f"amount_cents precisa ser pelo menos 1, veio {amount_cents}")

    return amount_cents <= PRIZE_LIMIT_CENTS


def draw_prize(chance_points: int, rng) -> bool:
    """Sorteia um número de 0 a DRAW_SIZE − 1 com `rng`; ganha quem tirou menos que os pontos em chance (GAM-10, GAM-11).

    `rng` é qualquer objeto com randrange(stop), como random.SystemRandom.
    Com 0 pontos, nunca ganha; com 10, ganha em 10 de 1000 números (1%).
    """
    if type(chance_points) is not int:
        raise TypeError(f"chance_points precisa ser int, veio {type(chance_points).__name__}")

    if chance_points < 0 or chance_points > MAX_CHANCE_POINTS:
        raise ValueError(f"chance_points precisa estar entre 0 e {MAX_CHANCE_POINTS}, veio {chance_points}")

    return rng.randrange(DRAW_SIZE) < chance_points
```

- `src/calculations/__init__.py` (editar): o conteúdo inteiro passa a ser:

```python
from calculations.fee import calculate_fee
from calculations.xp import MAX_LEVEL, XpGain, gain_record_xp, gain_transfer_xp, level_cost, next_level_n, record_whole_reais
from calculations.ranks import GRACE_DAYS, RANK_CDI_PERCENT, RANK_MINIMUM_CENTS, RANK_ORDER, rank_for_balance
from calculations.lots import split_redemption
from calculations.piggy_yield import daily_rate, lot_yield
from calculations.taxes import iof_percent, ir_percent, redemption_taxes
from calculations.lottery import DRAW_SIZE, MAX_CHANCE_POINTS, PRIZE_LIMIT_CENTS, draw_prize, is_eligible_for_prize
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/09-categorias-impostos-sorteio`; `git log --oneline -n 3` mostra `feat(categorias): guardar e resgatar por categoria`.
2. Crie `tests/unit/test_lottery.py` com o conteúdo do campo **Arquivos**.
3. `./.venv/Scripts/python.exe -m pytest -v tests/unit/test_lottery.py` → a saída tem `ImportError` com `cannot import name 'DRAW_SIZE' from 'calculations'` e a última linha tem `1 error`. É o motivo certo (AGENTS.md, seção 6).
4. Crie `src/calculations/lottery.py` com o conteúdo do campo **Arquivos**.
5. Edite `src/calculations/__init__.py` com o conteúdo do campo **Arquivos**.
6. `./.venv/Scripts/python.exe -m pytest -v tests/unit/test_lottery.py` → a última linha tem `8 passed`.
7. `docker compose up -d --build --wait` → termina sem erro.
8. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `384 passed`.
9. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
10. Rode o **Verificar**.
11. Feche o passo (AGENTS.md, seção 7), um comando por vez:
    ```
    git add -- tests/unit/test_lottery.py src/calculations/lottery.py src/calculations/__init__.py
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "feat(sorteio): sorteio da chance de não debitar com teste unitário"
    git log -1 --format=%B
    ```

**Testes:** `tests/unit/test_lottery.py` (TST-05, TST-06). Não toca na API nem no banco. O gerador é o `FakeRandom` do próprio teste: `randrange` devolve sempre o número escolhido e guarda o limite com que foi chamado.

| Função de teste | Entrada | Esperado |
|---|---|---|
| `TestEligibility::test_prize_limit_is_one_hundred_reais` | `PRIZE_LIMIT_CENTS`, `DRAW_SIZE` | 10000 e 1000 (GAM-22, GAM-10) |
| `TestEligibility::test_eligible_up_to_the_limit` | 1; 10000; 10001; 9223372036854775807 | `True`; `True`; `False`; `False` (GAM-22) |
| `TestEligibility::test_refuses_invalid_amount` | 0; −1; `100.0` | `ValueError`; `ValueError`; `TypeError` |
| `TestDrawPrize::test_each_point_is_one_in_a_thousand` | 1 ponto e número 0; 1 ponto e 1; 10 pontos e 9; 10 pontos e 10; 10 pontos e 999 | `True`, com `randrange(1000)`; `False`; `True`; `False`; `False` (GAM-10) |
| `TestDrawPrize::test_without_points_never_wins` | 0 pontos com os números 0, 1 e 999 | `False` nos três |
| `TestDrawPrize::test_refuses_invalid_points` | −1; 11; `1.0` | `ValueError`; `ValueError`; `TypeError` (GAM-15: até 10 pontos) |
| `TestDrawPrize::test_one_chance_point_is_worth_one_fee_point_at_the_limit` | `calculate_fee(10000, 0) − calculate_fee(10000, 1)`; quantos números de 0 a 999 ganham com 1 ponto | o ponto em tarifa poupa 10; 1 ponto em chance ganha em 1 número, que vale 1 × 10000 ÷ 1000 = 10 (GAM-11) |
| `TestDrawPrize::test_returns_bool` | `is_eligible_for_prize(500)`; `draw_prize(5, FakeRandom(3))` | os dois `bool` |

**Verificar:**
- `./.venv/Scripts/python.exe -m pytest -v tests/unit/test_lottery.py` → `8 passed`.
- `git grep -n -e "^import" -e "^from" -- src/calculations/lottery.py` → nenhuma linha (a conta pura não importa nada; o gerador chega por parâmetro).
- `git grep -n "PRIZE_LIMIT_CENTS = " -- src` → exatamente uma linha: `src/calculations/lottery.py:9:PRIZE_LIMIT_CENTS = 10000`.
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `384 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/calculations/__init__.py
  src/calculations/lottery.py
  tests/unit/test_lottery.py
  ```
- `git log -1 --format=%B` → `feat(sorteio): sorteio da chance de não debitar com teste unitário`

**Pronto quando:**
- [ ] O teste falhou antes do código com `ImportError` (item 3) e passa depois (item 6).
- [ ] Os três arquivos têm exatamente o conteúdo do campo **Arquivos**.
- [ ] Suíte com `384 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/09-categorias-impostos-sorteio`.

**Commit:** `feat(sorteio): sorteio da chance de não debitar com teste unitário`
**Pare se:**
- O item 3 não mostrar o `ImportError` (outro erro, ou algum teste rodou).
- O item 6 não terminar com `8 passed` depois de 3 tentativas de conferir `src/calculations/lottery.py` contra o plano.
- Um teste de `tests/unit/` que já existia ficar vermelho.
- A suíte não terminar com `384 passed`.

---

### Passo 9.8 — Chance de não debitar
**Branch:** fase/09-categorias-impostos-sorteio · **Depende de:** 9.7
**Objetivo:** depois de todas as regras da transferência, `transfer` sorteia com `self.rng` (gerador injetável no construtor do `TransactionController`); quando sai, a conta `BANK` devolve valor + tarifa num par de lançamentos `PRIZE`, e o prêmio não dá XP.
**Decisões:** GAM-10 — chance de não debitar · GAM-22 — sorteio até R$ 100 · GAM-23 — prêmio sem XP · TST-06 — sorteio injetável · DAD-16 — lançamentos somam zero · MOV-12, MOV-19 — idempotência · DAD-13 — recusa não grava
**Arquivos:**
- `src/controllers/transaction_controller.py` (editar): cinco mudanças, e nada mais.
  1. A linha de import existente
     ```python
     from sqlalchemy.exc import IntegrityError
     ```
     vira as três linhas
     ```python
     import random

     from sqlalchemy.exc import IntegrityError
     ```
  2. A linha
     ```python
     from calculations import calculate_fee
     ```
     vira
     ```python
     from calculations import calculate_fee, draw_prize, is_eligible_for_prize
     ```
  3. A linha
     ```python
         def __init__(self) -> None:
     ```
     vira
     ```python
         def __init__(self, rng=None) -> None:
     ```
  4. A linha
     ```python
             self.piggy_bank_controller = PiggyBankController()
     ```
     vira as três linhas
     ```python
             self.piggy_bank_controller = PiggyBankController()
             # TST-06: o gerador do sorteio é injetável; sem gerador, o do sistema operacional.
             self.rng = rng if rng is not None else random.SystemRandom()
     ```
  5. O método `transfer` inteiro (da linha `    def transfer(` até a linha `        return transaction_dto` que o fecha, antes de `    def get_transaction(`) passa a ser:

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
           MOV-02); a tarifa é calculate_fee(valor, pontos em tarifa da
           origem), com os pontos relidos depois da trava (GAM-09);
        9. a origem enviou menos de DAILY_TRANSFER_LIMIT transferências no
           dia contábil, contadas desde o último evento ACTIVE da conta
           (abertura ou desbloqueio). Na 11ª: a conta fica BLOCKED, com
           origem AUTOMATIC e motivo SUSPICIOUS_ACTIVITY, o commit grava só
           o bloqueio, e a resposta é 422 QIT001019 (CLI-08, DAD-13).

        Só depois de todas as regras, o sorteio da chance de não debitar
        (GAM-10): concorre a transferência de até PRIZE_LIMIT_CENTS, sem
        contar a tarifa (GAM-22), e ganha com a chance dos pontos em chance
        da origem, relidos depois da trava (draw_prize, com o gerador
        self.rng, TST-06). Pedido recusado nunca chega ao sorteio.

        Depois: a operação TRANSFER e os lançamentos, nesta ordem: AMOUNT
        −valor e FEE −tarifa na origem; AMOUNT +valor no destino; FEE
        +tarifa na conta BANK. Tarifa zero não gera lançamento (MOV-10). Se
        o sorteio saiu, mais dois: PRIZE −(valor + tarifa) na conta BANK e
        PRIZE +(valor + tarifa) na origem (GAM-10). Em seguida, o XP do valor
        para a origem (TRANSFER_SENT) e para o destino (TRANSFER_RECEIVED),
        cada um com o seu n (GAM-16, GAM-17), na mesma transação: o pedido
        repetido devolve a resposta da primeira vez e não dá XP de novo. O
        prêmio não dá XP (GAM-23). A resposta traz a key e o saldo novo da
        origem, já com o prêmio, se saiu (API-10).
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

        # MOV-19: a primeira chamada pode ter terminado durante a espera.
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
        fee = calculate_fee(amount, account.points_fee)

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
            self.logger.info("automatic_block_ready_to_commit account_key=%s", account.account_key)
            self.session.commit()

            raise DailyTransferLimitReached(account_key)

        prize = 0
        if is_eligible_for_prize(amount) and draw_prize(account.points_chance, self.rng):
            prize = amount + fee

        bank = self.account_repository.get_system_account(AccountType.BANK)

        try:
            transaction = self.transaction_repository.create(TransactionType.TRANSFER, request_control_key, request_hash, accounting_date)
            self.entry_repository.create(transaction, account, EntryType.AMOUNT, -amount)

            if fee > 0:
                self.entry_repository.create(transaction, account, EntryType.FEE, -fee)

            self.entry_repository.create(transaction, destination, EntryType.AMOUNT, amount)

            if fee > 0:
                self.entry_repository.create(transaction, bank, EntryType.FEE, fee)

            if prize > 0:
                self.entry_repository.create(transaction, bank, EntryType.PRIZE, -prize)
                self.entry_repository.create(transaction, account, EntryType.PRIZE, prize)

            self.gamification_controller.award_transfer_xp(account, amount, XpEvent.TRANSFER_SENT, transaction, accounting_date)
            self.gamification_controller.award_transfer_xp(destination, amount, XpEvent.TRANSFER_RECEIVED, transaction, accounting_date)

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

  O que muda no `transfer` em relação ao 8.7: a docstring (o parágrafo do sorteio e o do `PRIZE`); o bloco `prize = 0` e o sorteio, entre o limite diário e a conta `BANK`; o `if prize > 0:` com os dois lançamentos `PRIZE`, entre o `FEE` da conta `BANK` e o XP. Preservar os demais métodos e as correções da auditoria anterior: reconsulta após trava e logs críticos.

- `tests/integration/gamification/test_fee_with_points.py` (editar): uma troca, e nada mais. Com pontos em chance, a transferência de 10000 passa a concorrer ao sorteio, e a tarifa medida pelo saldo deixaria de ser certa. As duas linhas
  ```python
          apply_points(account, "CHANCE", 2)
          assert fee_paid(account, destination, 10000) == 100
  ```
  viram
  ```python
          apply_points(account, "CHANCE", 2)
          assert fee_paid(account, destination, 10001) == 101
  ```
  (10001 não concorre ao sorteio, GAM-22; a tarifa cheia dele é 101: o teste continua provando que ponto em chance não muda a tarifa)

- `tests/integration/gamification/test_chance.py` (criar): o conteúdo inteiro é:

```python
"""Chance de não debitar: POST /accounts/{account_key}/transfers com pontos em chance (GAM-10, GAM-22, GAM-23, MOV-12, TST-06).

O sorteio usa o gerador do sistema operacional: por HTTP, o teste não
escolhe o resultado. Cada teste confere o que vale nos dois resultados
(TST-06): sem prêmio, a origem paga valor + tarifa; com prêmio, a conta do
banco devolve valor + tarifa num lançamento PRIZE, e a origem fica com o
saldo de antes. Nos dois, o destino recebe o valor e a origem ganha o
mesmo XP: o prêmio não dá XP. A prova com o resultado escolhido é a
conferência P1 do passo 9.8, com gerador falso.
"""

from tests.utils import ObjectGenerator, PayloadGenerator, RequestGenerator


# GAM-24: R$ 830.000,00 recebidos levam ao nível 10, com os 10 pontos livres.
LEVEL_TEN_AMOUNT = 83000000

# GAM-22: o maior valor que concorre ao sorteio; a tarifa dele, sem pontos em tarifa, é 100.
PRIZE_LIMIT = 10000
PRIZE_LIMIT_FEE = 100

# GAM-16: no nível 10 (n = 10), R$ 100,00 dão (100 / 4) · log10(100) = 50 XP.
PRIZE_LIMIT_XP = 50


def create_level_ten_account() -> dict:
    """Uma conta que recebeu R$ 830.000,00: nível 10, 10 pontos livres e saldo 83000000."""
    sender = ObjectGenerator.create_funded_account(LEVEL_TEN_AMOUNT + LEVEL_TEN_AMOUNT // 100)
    receiver = ObjectGenerator.create_account()

    payload = PayloadGenerator.transfer(receiver["account_key"], amount=LEVEL_TEN_AMOUNT)
    status, response = RequestGenerator.POST_transfer(sender["account_key"], sender["account_token"], payload)
    assert status == 201, response

    return receiver


def apply_points(account: dict, benefit: str, points: int) -> dict:
    payload = PayloadGenerator.point_application(benefit=benefit, points=points)
    status, response = RequestGenerator.POST_point_application(account["account_key"], account["account_token"], payload)
    assert status == 200, response

    return response


def balance_of(account: dict) -> int:
    status, response = RequestGenerator.GET_account(account["account_key"], account["account_token"])
    assert status == 200, response

    return response["balance"]


def xp_of(account: dict) -> int:
    status, response = RequestGenerator.GET_gamification(account["account_key"], account["account_token"])
    assert status == 200, response

    return response["xp"]


def origin_entries(account: dict, transaction_key: str) -> list:
    """(tipo, valor) de cada lançamento da operação na conta, na ordem em que foram gravados."""
    status, response = RequestGenerator.GET_transaction(account["account_key"], account["account_token"], transaction_key)
    assert status == 200, response

    return [(entry["entry_type"], entry["amount"]) for entry in response["entries"]]


def send_and_check(origin: dict, destination: dict, amount: int, fee: int) -> bool:
    """Transfere `amount` e confere os dois resultados possíveis do sorteio. Devolve True quando o prêmio saiu."""
    balance_before = balance_of(origin)
    destination_before = balance_of(destination)
    xp_before = xp_of(origin)

    payload = PayloadGenerator.transfer(destination["account_key"], amount=amount)
    status, response = RequestGenerator.POST_transfer(origin["account_key"], origin["account_token"], payload)
    assert status == 201, response

    entries = origin_entries(origin, response["transaction_key"])
    charged = [("AMOUNT", -amount), ("FEE", -fee)]
    returned = charged + [("PRIZE", amount + fee)]

    assert entries in [charged, returned], entries
    prize_won = entries == returned

    if prize_won:
        assert response["balance"] == balance_before
    else:
        assert response["balance"] == balance_before - amount - fee

    assert balance_of(origin) == response["balance"]
    assert balance_of(destination) == destination_before + amount
    assert xp_of(origin) - xp_before == PRIZE_LIMIT_XP * amount // PRIZE_LIMIT

    return prize_won


class TestChance:
    def test_transfer_up_to_the_limit_is_charged_or_returned_whole(self):
        origin = create_level_ten_account()
        destination = ObjectGenerator.create_account()

        gamification = apply_points(origin, "CHANCE", 10)
        assert (gamification["points_chance"], gamification["chance_percent"], gamification["fee_percent"]) == (10, "1", "1")

        for _ in range(5):
            send_and_check(origin, destination, PRIZE_LIMIT, PRIZE_LIMIT_FEE)

        assert balance_of(destination) == 5 * PRIZE_LIMIT

    def test_transfer_above_the_limit_is_always_charged(self):
        origin = create_level_ten_account()
        destination = ObjectGenerator.create_account()
        apply_points(origin, "CHANCE", 10)

        for _ in range(5):
            assert send_and_check(origin, destination, PRIZE_LIMIT + 1, PRIZE_LIMIT_FEE + 1) is False

    def test_without_chance_points_is_always_charged(self):
        origin = create_level_ten_account()
        destination = ObjectGenerator.create_account()

        for _ in range(5):
            assert send_and_check(origin, destination, PRIZE_LIMIT, PRIZE_LIMIT_FEE) is False

    def test_refused_transfer_never_reaches_the_draw(self):
        origin = create_level_ten_account()
        destination = ObjectGenerator.create_account()
        apply_points(origin, "CHANCE", 10)

        withdrawal = PayloadGenerator.withdrawal(amount=LEVEL_TEN_AMOUNT - PRIZE_LIMIT - PRIZE_LIMIT_FEE + 1)
        status, response = RequestGenerator.POST_withdrawal(origin["account_key"], origin["account_token"], withdrawal)
        assert status == 201, response
        assert balance_of(origin) == PRIZE_LIMIT + PRIZE_LIMIT_FEE - 1

        for _ in range(5):
            payload = PayloadGenerator.transfer(destination["account_key"], amount=PRIZE_LIMIT)
            status, response = RequestGenerator.POST_transfer(origin["account_key"], origin["account_token"], payload)
            assert status == 422, response
            assert response["code"] == "QIT001015"

        assert balance_of(origin) == PRIZE_LIMIT + PRIZE_LIMIT_FEE - 1
        assert balance_of(destination) == 0

    def test_repeated_transfer_returns_the_first_response(self):
        origin = create_level_ten_account()
        destination = ObjectGenerator.create_account()
        apply_points(origin, "CHANCE", 10)

        payload = PayloadGenerator.transfer(destination["account_key"], amount=PRIZE_LIMIT)
        status, first = RequestGenerator.POST_transfer(origin["account_key"], origin["account_token"], payload)
        assert status == 201, first

        xp_after_first = xp_of(origin)

        for _ in range(3):
            status, response = RequestGenerator.POST_transfer(origin["account_key"], origin["account_token"], payload)
            assert status == 201, response
            assert response == first

        assert balance_of(origin) == first["balance"]
        assert balance_of(destination) == PRIZE_LIMIT
        assert xp_of(origin) == xp_after_first
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/09-categorias-impostos-sorteio`; `git log --oneline -n 3` mostra `feat(sorteio): sorteio da chance de não debitar com teste unitário`.
2. `docker compose up -d --build --wait` e rode a conferência P1 do **Verificar** → a saída termina com `TypeError` e tem `unexpected keyword argument 'rng'`. É o vermelho antes do código: o controller ainda não recebe gerador.
3. Faça a troca em `tests/integration/gamification/test_fee_with_points.py`.
4. Faça as cinco mudanças em `src/controllers/transaction_controller.py` e confira o método `transfer` contra o do campo **Arquivos**.
5. `docker compose up -d --build --wait`.
6. Rode as conferências P1 e P2 do **Verificar** → as saídas esperadas.
7. `./.venv/Scripts/python.exe -m pytest -v tests/integration/gamification/test_fee_with_points.py tests/integration/gamification/test_transfer_xp.py` → a última linha tem `passed` e não tem `failed`.
8. Crie `tests/integration/gamification/test_chance.py` com o conteúdo do campo **Arquivos**.
9. `./.venv/Scripts/python.exe -m pytest -v tests/integration/gamification/test_chance.py` → a última linha tem `5 passed`.
10. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `389 passed`.
11. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
12. Rode o resto do **Verificar**.
13. Feche o passo (AGENTS.md, seção 7), um comando por vez:
    ```
    git add -- src/controllers/transaction_controller.py tests/integration/gamification/test_fee_with_points.py tests/integration/gamification/test_chance.py
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "feat(sorteio): chance de não debitar na transferência"
    git log -1 --format=%B
    ```

**Testes:** prova — `tests/integration/gamification/test_chance.py`, escrito depois do código (AGENTS.md, seção 6, "prova"). Por HTTP, o sorteio usa o gerador do sistema operacional e o teste não escolhe o resultado: cada caso confere o que vale nos dois resultados (TST-06), e por isso passaria também antes do código. O vermelho antes do código, com o resultado escolhido, é a conferência P1 (item 2), com gerador falso dentro do container.

`POST /accounts/{account_key}/transfers` não muda de contrato: 201 `{"transaction_key", "balance"}`, com o `balance` já com o prêmio, se saiu. Efeito no banco quando o prêmio sai: os lançamentos da fase 8 e mais `PRIZE` −(valor + tarifa) na conta `BANK` e `PRIZE` +(valor + tarifa) na origem, nessa ordem; os `xp_event` são os mesmos de uma transferência sem prêmio.

A ajudante `send_and_check` transfere e confere: os lançamentos da operação na origem são `[AMOUNT −valor, FEE −tarifa]` (sem prêmio) ou `[AMOUNT −valor, FEE −tarifa, PRIZE +(valor + tarifa)]` (com prêmio); o saldo da origem caiu valor + tarifa (sem prêmio) ou não mudou (com prêmio); o destino recebeu o valor; o XP da origem subiu o XP da transferência, nos dois resultados (GAM-23).

| Função de teste | Entrada | Esperado |
|---|---|---|
| `test_transfer_up_to_the_limit_is_charged_or_returned_whole` | conta no nível 10 com os 10 pontos em `CHANCE`; 5 transferências de 10000 | pontos (10, `"1"`, `"1"`); cada uma passa no `send_and_check` com tarifa 100 e XP +50; o destino fica com 50000 (GAM-10, GAM-23) |
| `test_transfer_above_the_limit_is_always_charged` | conta no nível 10 com 10 pontos em `CHANCE`; 5 transferências de 10001 | as 5 sem prêmio, com tarifa 101 (GAM-22) |
| `test_without_chance_points_is_always_charged` | conta no nível 10 sem pontos aplicados; 5 transferências de 10000 | as 5 sem prêmio, com tarifa 100 |
| `test_refused_transfer_never_reaches_the_draw` | conta no nível 10 com 10 pontos em `CHANCE`; saque que deixa 10099; 5 transferências de 10000 | 422 `QIT001015` nas 5; saldo 10099 e destino 0 (GAM-10: o sorteio vem depois do saldo; DAD-13) |
| `test_repeated_transfer_returns_the_first_response` | conta no nível 10 com 10 pontos em `CHANCE`; uma transferência de 10000 e o mesmo pedido mais 3 vezes | as 4 respostas iguais; saldo da origem igual ao da primeira resposta; destino 10000; o XP não muda nas repetições (MOV-12, MOV-19) |

**Verificar:**
- P1 — o sorteio com o resultado escolhido (GAM-10, GAM-22, GAM-23, TST-06). Dentro do container, com o `commit` da sessão trocado por `flush`; tudo termina em `s.rollback()`. Um comando, numa linha só:
  ```
  docker compose exec -T api python -c "from datetime import date; from uuid import uuid4; from database import open_context; from controllers import TransactionController; from models import Entry, Transaction, XpEvent; from repositories import AccountRepository, CustomerRepository; from utils.account_token import hash_account_token; c = open_context(); s = c.get_or_create_session(); s.commit = s.flush; cr = CustomerRepository(c); x = cr.create('Ana Lima', '529.982.247-25', 'ana.conferencia.p1@example.com', date(1995, 4, 12)); y = cr.create('Bia Lima', '111.444.777-35', 'bia.conferencia.p1@example.com', date(1996, 5, 13)); s.flush(); r = AccountRepository(c); a = r.create_customer_account(x, hash_account_token('token-a')); b = r.create_customer_account(y, hash_account_token('token-b')); a.balance = 20200; a.points_chance = 10; s.flush(); win = type('Fake', (), {'randrange': lambda self, n: 0})(); lose = type('Fake', (), {'randrange': lambda self, n: n - 1})(); send = lambda rng, amount: TransactionController(rng=rng).transfer(a.account_key, 'token-a', {'destination_account_key': b.account_key, 'amount': amount, 'request_control_key': str(uuid4())}); entries = lambda t: [(e.entry_type.enumerator, e.amount) for e in s.query(Entry).join(Transaction, Transaction.id == Entry.transaction_id).filter(Transaction.transaction_key == t['transaction_key']).order_by(Entry.id)]; t1 = send(win, 10000); print(t1['balance'], b.balance, entries(t1)); print(sorted((e.source, e.xp) for e in s.query(XpEvent).join(Transaction, Transaction.id == XpEvent.transaction_id).filter(Transaction.transaction_key == t1['transaction_key']))); t2 = send(win, 10001); print(t2['balance'], len(entries(t2))); t3 = send(lose, 100); print(t3['balance'], len(entries(t3))); a.points_chance = 0; s.flush(); t4 = send(win, 100); print(t4['balance'], len(entries(t4))); s.rollback()"
  ```
  → exatamente:
  ```
  20200 10000 [('AMOUNT', -10000), ('FEE', -100), ('AMOUNT', 10000), ('FEE', 100), ('PRIZE', -10100), ('PRIZE', 10100)]
  [('TRANSFER_RECEIVED', 25), ('TRANSFER_SENT', 25)]
  10098 4
  9997 4
  9896 4
  ```
  Linha 1: o gerador que sempre ganha, numa transferência de 10000: o banco devolve 10100 e a origem fica com o saldo de antes; os seis lançamentos somam zero. Linha 2: o XP é só o da transferência (25 para cada lado, n = 1); o prêmio não deu XP. Linha 3: 10001 não concorre, mesmo com o gerador que sempre ganha (paga 10001 + 101). Linha 4: o gerador que sempre perde (paga 100 + 1). Linha 5: sem pontos em chance, o gerador que sempre ganha não ganha.
- P2 — a ordem no `transfer` (GAM-10: o sorteio só depois do saldo e do limite diário, antes de gravar). Um comando, numa linha só:
  ```
  docker compose exec -T api python -c "import inspect; from controllers import TransactionController; src = inspect.getsource(TransactionController.transfer); print(src.index('raise InsufficientBalance') < src.index('raise DailyTransferLimitReached') < src.index('draw_prize(') < src.index('self.transaction_repository.create('), src.count('EntryType.PRIZE'), src.count('award_transfer_xp(account, amount,'), 'rng=None' in inspect.getsource(TransactionController.__init__))"
  ```
  → exatamente `True 2 1 True`.
- `git grep -n "SystemRandom()" -- src` → exatamente uma linha, em `src/controllers/transaction_controller.py` (o gerador de produção nasce só ali).
- `./.venv/Scripts/python.exe -m pytest -v tests/integration/gamification/test_chance.py` → `5 passed`.
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `389 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/controllers/transaction_controller.py
  tests/integration/gamification/test_chance.py
  tests/integration/gamification/test_fee_with_points.py
  ```
- `git log -1 --format=%B` → `feat(sorteio): chance de não debitar na transferência`

**Pronto quando:**
- [ ] A P1 terminou com `TypeError` antes do código (item 2) e dá as 5 linhas esperadas depois (item 6); a P2 dá `True 2 1 True`.
- [ ] O método `transfer` é o do campo **Arquivos**; as outras quatro mudanças estão feitas.
- [ ] `test_fee_with_points.py` tem só a troca do campo **Arquivos**, e os 4 testes dele passam.
- [ ] `test_chance.py` passa (`5 passed`).
- [ ] Suíte com `389 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/09-categorias-impostos-sorteio`.

**Commit:** `feat(sorteio): chance de não debitar na transferência`
**Pare se:**
- A P1 do item 2 não terminar com `TypeError` e `unexpected keyword argument 'rng'`.
- Alguma das linhas das mudanças 1 a 4, ou as duas linhas de `test_fee_with_points.py`, não for encontrada igual.
- A P1 terminar com `IntegrityError` com `customer_document_number_key` ou `customer_email_key`: rode `docker compose down -v`, `docker compose up -d --build --wait` e a P1 de novo; repetindo o erro, PARE.
- A P1 ou a P2 derem outra saída depois de 3 tentativas de conferir os arquivos do passo contra o plano.
- `test_chance.py` falhar (é prova: o conserto fica fora do passo).
- Um teste de `tests/integration/transactions/` ou de `tests/integration/gamification/` que já existia ficar vermelho.
- A suíte não terminar com `389 passed`.

---

### Passo 9.9 — Consultar rendimento bruto e liquido
**Branch:** fase/09-categorias-impostos-sorteio · **Depende de:** 9.8
**Objetivo:** Consultar rendimento bruto e liquido.
**Decisões:** COF-28 — consulta; COF-27 — impostos; COF-26 — residuo congelado; MOV-11 — ordem das travas
**Arquivos:**
- `src/controllers/__init__.py`: acrescentar o export indicado abaixo.
- `tests/integration/accounts/test_get_account.py`: editar ACCOUNT_FIELDS para os nove campos abaixo.
- `src/controllers/yield_controller.py`: criar, conteúdo completo abaixo.
- `src/controllers/account_controller.py`: editar somente import e get_account abaixo.
- `src/controllers/category_controller.py`: editar somente import, list_categories e get_category abaixo.
- `src/dtos/account_dto.py`: editar assinatura e retorno abaixo.
- `src/dtos/category_dto.py`: editar assinatura e retorno abaixo.
- `tests/integration/piggy_bank/test_yield_queries.py`: criar, conteúdo completo abaixo.
- `tests/integration/categories/test_create_and_list_categories.py`: editar CATEGORY_FIELDS conforme abaixo.
- `tests/integration/categories/test_get_and_delete_category.py`: editar CATEGORY_FIELDS conforme abaixo.

**Passo a passo:**
1. Confira branch e estado limpo conforme AGENTS, seção 7.
2. Crie primeiro os arquivos de teste listados, com o conteúdo completo abaixo.
3. Suba a API: `docker compose up -d --build --wait`.
4. Rode `./.venv/Scripts/python.exe -m pytest -v tests/integration/piggy_bank/test_yield_queries.py`. Antes do código: os três casos falham por asserção de ausência dos campos de rendimento; não por erro de import.
5. Aplique as alterações abaixo na ordem apresentada. Nenhum arquivo fora de **Arquivos**.
6. `docker compose up -d --build --wait`.
7. Repita o comando do item 4: todos os testes devem passar.
8. `./.venv/Scripts/python.exe -m pytest`: suíte inteira verde, sem failed/error/skipped.
9. `./.venv/Scripts/python.exe -m flake8 src tests`: nenhuma linha.
10. Feche conforme AGENTS, seção 7: `git add -- src/controllers/__init__.py tests/integration/accounts/test_get_account.py src/controllers/account_controller.py src/controllers/category_controller.py src/controllers/yield_controller.py src/dtos/account_dto.py src/dtos/category_dto.py tests/integration/categories/test_create_and_list_categories.py tests/integration/categories/test_get_and_delete_category.py tests/integration/piggy_bank/test_yield_queries.py`; confira a lista exata abaixo e diffs restantes vazios; commit local da branch, um comando por vez.

- `tests/integration/piggy_bank/test_yield_queries.py` (criar): conteúdo inteiro:

```python
from datetime import date, timedelta

from tests.utils import DbUtils, MockGenerator, ObjectGenerator, PayloadGenerator, RequestGenerator


def get_account(account):
    status, result = RequestGenerator.GET_account(account["account_key"], account["account_token"])
    assert status == 200, result
    assert "piggy_bank_gross_yield" in result
    return result


def get_category(account, key):
    status, result = RequestGenerator.GET_category(account["account_key"], account["account_token"], key)
    assert status == 200, result
    assert "gross_yield" in result
    return result


class TestYieldQueries:
    def test_query_matches_full_redemption_on_the_same_date(self):
        DbUtils.rollback()
        MockGenerator.set_cdi_rate("2026-06-01", "1.000000")
        account = ObjectGenerator.create_funded_account(100000)
        key, token = account["account_key"], account["account_token"]
        assert RequestGenerator.POST_saving(key, token, PayloadGenerator.saving(amount=100000))[0] == 201
        assert RequestGenerator.POST_day_closing(PayloadGenerator.day_closing("2026-06-01"))[0] == 200
        summary = get_account(account)
        assert (summary["piggy_bank_gross_yield"], summary["piggy_bank_net_yield"], summary["yield_accounting_date"]) == (1000, 31, "2026-06-02")
        category = RequestGenerator.GET_categories(key, token)[1]["data"][0]
        assert (category["gross_yield"], category["net_yield"], category["yield_accounting_date"]) == (1000, 31, "2026-06-02")
        assert get_category(account, category["category_key"]) == category
        status, result = RequestGenerator.POST_redemption(key, token, PayloadGenerator.redemption(amount=101000))
        assert status == 201, result
        assert result["net_amount"] - 100000 == summary["piggy_bank_net_yield"]
        assert get_account(account)["piggy_bank_gross_yield"] == 0
        MockGenerator.clear_cdi("2026-06-01")

    def test_account_adds_the_separate_category_estimates(self):
        DbUtils.rollback()
        account = ObjectGenerator.create_funded_account(200)
        key, token = account["account_key"], account["account_token"]
        first = RequestGenerator.GET_categories(key, token)[1]["data"][0]["category_key"]
        status, result = RequestGenerator.POST_category(key, token, PayloadGenerator.category(name="carro"))
        assert status == 201, result
        second = result["category_key"]
        for category_key in [first, second]:
            assert RequestGenerator.POST_saving(key, token, PayloadGenerator.saving(amount=100, category_key=category_key))[0] == 201
        for offset in range(30):
            day = (date(2026, 6, 1) + timedelta(days=offset)).isoformat()
            MockGenerator.set_cdi_rate(day, "1.000000" if offset == 0 else None)
            assert RequestGenerator.POST_day_closing(PayloadGenerator.day_closing(day))[0] == 200
            MockGenerator.clear_cdi(day)
        summary = get_account(account)
        assert (summary["piggy_bank_gross_yield"], summary["piggy_bank_net_yield"]) == (2, 0)
        for category_key in [first, second]:
            category = get_category(account, category_key)
            assert (category["gross_yield"], category["net_yield"], category["yield_accounting_date"]) == (1, 0, "2026-07-01")
            status, result = RequestGenerator.POST_redemption(key, token, PayloadGenerator.redemption(amount=101, category_key=category_key))
            assert status == 201, result
            assert (result["iof"], result["ir"], result["net_amount"]) == (0, 1, 100)

    def test_empty_blocked_closed_and_deleted_resources_are_readable(self):
        DbUtils.rollback()
        account = ObjectGenerator.create_account()
        key, token = account["account_key"], account["account_token"]
        status, result = RequestGenerator.POST_category(key, token, PayloadGenerator.category(name="carro"))
        assert status == 201, result
        category_key = result["category_key"]
        assert RequestGenerator.DELETE_category(key, token, category_key)[0] == 204
        for expected_status in ["ACTIVE", "BLOCKED", "CLOSED"]:
            if expected_status == "BLOCKED":
                assert RequestGenerator.POST_block(key, PayloadGenerator.block())[0] == 204
            if expected_status == "CLOSED":
                assert RequestGenerator.POST_unblock(key)[0] == 204
                assert RequestGenerator.DELETE_account(key, token)[0] == 204
            summary = get_account(account)
            assert summary["status"] == expected_status
            assert (summary["piggy_bank_gross_yield"], summary["piggy_bank_net_yield"]) == (0, 0)
            category = get_category(account, category_key)
            assert (category["gross_yield"], category["net_yield"], category["status"]) == (0, 0, "DELETED")
```

- `src/controllers/yield_controller.py` (criar): conteúdo inteiro:

```python
from controllers.base_controller import BaseController
from calculations import redemption_taxes
from repositories import AccountRepository, BankClockRepository, CategoryRepository, LotRepository


class YieldController(BaseController):
    """Estimativa de resgate total por categoria, na data contabil atual (COF-28)."""

    def __init__(self) -> None:
        super().__init__(__name__)
        self.account_repository = AccountRepository(self.context)
        self.bank_clock_repository = BankClockRepository(self.context)
        self.category_repository = CategoryRepository(self.context)
        self.lot_repository = LotRepository(self.context)

    def lock_snapshot(self, account):
        accounting_date = self.bank_clock_repository.get_accounting_date()
        piggy_bank = self.account_repository.get_piggy_bank(account)
        locked = {a.id: a for a in self.account_repository.lock_accounts([account, piggy_bank])}
        return locked[account.id], locked[piggy_bank.id], accounting_date

    def category_summary(self, category, accounting_date) -> dict:
        parts = [((accounting_date - lot.accounting_date).days, lot.yield_remaining)
                 for lot in self.lot_repository.list_open_for_update(category)]
        gross_yield = sum(value for _, value in parts)
        iof, ir = redemption_taxes(parts)
        return {"gross_yield": gross_yield, "net_yield": gross_yield - iof - ir,
                "yield_accounting_date": accounting_date.isoformat()}

    def account_summary(self, piggy_bank, accounting_date) -> dict:
        gross_yield = 0
        net_yield = 0
        offset = 0
        while True:
            categories = self.category_repository.list_active_page(piggy_bank, 100, offset)
            for category in categories[:100]:
                summary = self.category_summary(category, accounting_date)
                gross_yield += summary["gross_yield"]
                net_yield += summary["net_yield"]
            if len(categories) <= 100:
                break
            offset += 100
        return {"piggy_bank_gross_yield": gross_yield, "piggy_bank_net_yield": net_yield,
                "yield_accounting_date": accounting_date.isoformat()}
```

- `src/controllers/account_controller.py` e `src/controllers/category_controller.py`: acrescentar `from controllers.yield_controller import YieldController` aos imports. Em `src/controllers/__init__.py`, acrescentar `from controllers.yield_controller import YieldController` ao fim. Os dois controllers usam o import pelo módulo. Substituir get_account no primeiro e list_categories/get_category no segundo pelos métodos completos:

```python
    def get_account(self, account_key: str, account_token: str) -> dict:
        account = self.get_owned_account(account_key, account_token)
        yields = YieldController()
        account, piggy_bank, accounting_date = yields.lock_snapshot(account)
        customer = self.customer_repository.get_by_id(account.customer_id)
        summary = yields.account_summary(piggy_bank, accounting_date)
        return AccountDTO.obj_to_dict(account, customer, piggy_bank, summary)
```
```python
    def list_categories(self, account_key: str, account_token: str, limit: int, offset: int) -> dict:
        account = self.get_owned_account(account_key, account_token)
        yields = YieldController()
        account, piggy_bank, accounting_date = yields.lock_snapshot(account)
        rows = self.category_repository.list_active_page(piggy_bank, limit, offset)
        is_last_page = len(rows) <= limit
        rows = rows[:limit]
        categories = [CategoryDTO.obj_to_dict(category, self.category_repository.get_balance(category),
                      yields.category_summary(category, accounting_date)) for category in rows]
        return {"categories_list_dto": categories, "is_last_page": is_last_page}

    def get_category(self, account_key: str, account_token: str, category_key: str) -> dict:
        account = self.get_owned_account(account_key, account_token)
        yields = YieldController()
        account, piggy_bank, accounting_date = yields.lock_snapshot(account)
        category = self._get_category(piggy_bank, category_key)
        return CategoryDTO.obj_to_dict(category, self.category_repository.get_balance(category),
                                       yields.category_summary(category, accounting_date))
```

- `src/dtos/account_dto.py`: assinatura `obj_to_dict(account: Account, customer: Customer, piggy_bank: Account, yield_summary: dict)`; acrescentar `**yield_summary,` ao dicionário de retorno desse método, depois de created_at. open_account_to_dict fica igual.
- `src/dtos/category_dto.py`: assinatura `obj_to_dict(category: Category, balance: int, yield_summary: dict)`; acrescentar `**yield_summary,` ao retorno, depois de created_at. only_obj_key fica igual.
- Nos dois arquivos antigos de teste de categorias listados em Arquivos, trocar a linha CATEGORY_FIELDS inteira por:

```python
CATEGORY_FIELDS = ["balance", "category_key", "created_at", "gross_yield", "is_default", "name", "net_yield", "status", "yield_accounting_date"]
```

No arquivo antigo tests/integration/accounts/test_get_account.py, substituir ACCOUNT_FIELDS por:

```python
ACCOUNT_FIELDS = ["account_key", "balance", "created_at", "customer_key", "piggy_bank_balance", "piggy_bank_gross_yield", "piggy_bank_net_yield", "status", "yield_accounting_date"]
```

O bruto ignora principal e resíduo; o líquido usa COF-27 por categoria. Lotes zerados não entram na consulta list_open_for_update, preservando COF-26. Relógio antes de conta/cofrinho/lotes conserva a ordem de travas. Nenhum GET grava ou faz commit.

**Testes:** tests/integration/piggy_bank/test_yield_queries.py. Os casos e resultados estão nas asserções completas; integração usa apenas HTTP.
**Verificar:**
- Comando do item 4 verde.
- Suíte inteira verde e lint sem saída.
- `git diff --cached --name-only` lista exatamente:
```
src/controllers/__init__.py
src/controllers/account_controller.py
src/controllers/category_controller.py
src/controllers/yield_controller.py
src/dtos/account_dto.py
src/dtos/category_dto.py
tests/integration/accounts/test_get_account.py
tests/integration/categories/test_create_and_list_categories.py
tests/integration/categories/test_get_and_delete_category.py
tests/integration/piggy_bank/test_yield_queries.py
```
- `git log -1 --format=%B`: `feat(cofrinho): consulta rendimento bruto e liquido por categoria`.

**Pronto quando:**
- [ ] Vermelho pelo motivo definido antes do código; casos novos e suíte verdes depois.
- [ ] Arquivos e alterações iguais ao plano; lint sem saída.
- [ ] Commit local da branch conforme AGENTS.

**Commit:** `feat(cofrinho): consulta rendimento bruto e liquido por categoria`
**Pare se:** algum nome/trecho de encaixe não existir; falha de comando; vermelho por motivo diferente; teste ou lint falhar após 3 conferências. Não mudar o teste esperado para fazê-lo passar.

---


### Passo 9.10 — Validar acumuladores antes de ultrapassar BIGINT
**Branch:** fase/09-categorias-impostos-sorteio · **Depende de:** 9.9
**Objetivo:** Validar acumuladores antes de ultrapassar BIGINT.
**Decisões:** DAD-19 — BIGINT e rollback integral; TST-09 — testes isolados de infraestrutura; R3 — erro de regra
**Arquivos:**
- `src/controllers/base_controller.py`: editar import e acrescentar método estático abaixo ao fim da classe.
- `src/controllers/transaction_controller.py`: inserir validações nos dois pontos definidos abaixo.
- `src/controllers/piggy_bank_controller.py`: inserir validações nos dois pontos definidos abaixo.
- `src/controllers/gamification_controller.py`: inserir validações antes dos eventos/valores abaixo.
- `src/controllers/day_closing_controller.py`: validar acumuladores antes de atualizar cada lote, abaixo.
- `tests/unit/infrastructure/test_numeric_limits.py`: criar, conteúdo inteiro abaixo; pasta infrastructure nova, sem __init__.py.
- `tests/integration/transactions/test_numeric_overflow.py`: criar, conteúdo inteiro abaixo.

**Passo a passo:**
1. Confira branch e estado limpo conforme AGENTS, seção 7.
2. Crie primeiro os arquivos de teste listados, com o conteúdo completo abaixo.
3. Suba a API: `docker compose up -d --build --wait`.
4. Rode `./.venv/Scripts/python.exe -m pytest -v tests/unit/infrastructure/test_numeric_limits.py tests/integration/transactions/test_numeric_overflow.py`. Antes do código: unitário: AttributeError com check_numeric_limits; HTTP: asserção de status 422 contra a falha ainda não tratada.
5. Aplique as alterações abaixo na ordem apresentada. Nenhum arquivo fora de **Arquivos**.
6. `docker compose up -d --build --wait`.
7. Repita o comando do item 4: todos os testes devem passar.
8. `./.venv/Scripts/python.exe -m pytest`: suíte inteira verde, sem failed/error/skipped.
9. `./.venv/Scripts/python.exe -m flake8 src tests`: nenhuma linha.
10. Feche conforme AGENTS, seção 7: `git add -- src/controllers/base_controller.py src/controllers/day_closing_controller.py src/controllers/gamification_controller.py src/controllers/piggy_bank_controller.py src/controllers/transaction_controller.py tests/integration/transactions/test_numeric_overflow.py tests/unit/infrastructure/test_numeric_limits.py`; confira a lista exata abaixo e diffs restantes vazios; commit local da branch, um comando por vez.

- `tests/unit/infrastructure/test_numeric_limits.py` (criar): conteúdo inteiro:

```python
from os import environ
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

environ.setdefault("DATABASE_URL", "postgresql+psycopg2://bootcamp:bootcamp@localhost:5432/bootcamp")

from calculations import XpGain
from controllers.base_controller import BaseController
from controllers.gamification_controller import GamificationController
from errors import NumericLimitExceeded


MAXIMUM = 9223372036854775807


def test_numeric_boundaries_are_accepted():
    BaseController.check_numeric_limits(0, 1, MAXIMUM)


def test_numeric_overflow_is_a_project_error():
    with pytest.raises(NumericLimitExceeded) as result:
        BaseController.check_numeric_limits(MAXIMUM + 1)
    assert (result.value.http_status, result.value.code) == (422, "QIT001032")


def test_xp_overflow_precedes_every_progress_write():
    controller = GamificationController.__new__(GamificationController)
    controller.gamification_repository = Mock()
    account = SimpleNamespace(level=10, points_free=0)
    with pytest.raises(NumericLimitExceeded):
        controller._apply_xp_gain(account, XpGain(10, MAXIMUM + 1, 1, 0), "TRANSFER_SENT", None, None)
    assert controller.gamification_repository.mock_calls == []
```

- `tests/integration/transactions/test_numeric_overflow.py` (criar): conteúdo inteiro:

```python
from tests.utils import DbUtils, MockGenerator, ObjectGenerator, PayloadGenerator, RequestGenerator


MAXIMUM = 9223372036854775807


def account_data(account):
    status, result = RequestGenerator.GET_account(account["account_key"], account["account_token"])
    assert status == 200, result
    return result


def entries(account):
    status, result = RequestGenerator.GET_entries(account["account_key"], account["account_token"], {"limit": "100"})
    assert status == 200, result
    return result["data"]


class TestNumericOverflow:
    def test_deposit_at_limit_rejects_next_cent_and_does_not_keep_the_key(self):
        DbUtils.rollback()
        account = ObjectGenerator.create_funded_account(MAXIMUM)
        key, token = account["account_key"], account["account_token"]
        before = entries(account)
        payload = PayloadGenerator.deposit(amount=1)
        status, result = RequestGenerator.POST_deposit(key, payload)
        assert status == 422, result
        assert result["code"] == "QIT001032"
        assert account_data(account)["balance"] == MAXIMUM
        assert entries(account) == before
        assert RequestGenerator.POST_deposit(key, PayloadGenerator.deposit(amount=MAXIMUM + 1))[0] == 400
        assert RequestGenerator.POST_withdrawal(key, token, PayloadGenerator.withdrawal(amount=1))[0] == 201
        assert RequestGenerator.POST_deposit(key, payload)[0] == 201
        assert account_data(account)["balance"] == MAXIMUM

    def test_transfer_overflow_leaves_both_accounts_and_xp_unchanged(self):
        DbUtils.rollback()
        origin = ObjectGenerator.create_funded_account(10100)
        destination = ObjectGenerator.create_funded_account(MAXIMUM)
        before = [entries(origin), entries(destination)]
        payload = PayloadGenerator.transfer(destination["account_key"], amount=10000)
        status, result = RequestGenerator.POST_transfer(origin["account_key"], origin["account_token"], payload)
        assert status == 422, result
        assert result["code"] == "QIT001032"
        assert [account_data(a)["balance"] for a in [origin, destination]] == [10100, MAXIMUM]
        assert [entries(origin), entries(destination)] == before
        for account in [origin, destination]:
            assert RequestGenerator.GET_gamification(account["account_key"], account["account_token"])[1]["xp"] == 0

    def test_yield_overflow_rolls_back_the_whole_day(self):
        DbUtils.rollback()
        earlier = ObjectGenerator.create_funded_account(1000)
        earlier_key, earlier_token = earlier["account_key"], earlier["account_token"]
        assert RequestGenerator.POST_saving(earlier_key, earlier_token, PayloadGenerator.saving(amount=1000))[0] == 201
        earlier_before = account_data(earlier)
        earlier_progress = RequestGenerator.GET_gamification(earlier_key, earlier_token)[1]
        earlier_entries = RequestGenerator.GET_piggy_bank_entries(earlier_key, earlier_token)[1]
        account = ObjectGenerator.create_funded_account(MAXIMUM)
        key, token = account["account_key"], account["account_token"]
        assert RequestGenerator.POST_saving(key, token, PayloadGenerator.saving(amount=MAXIMUM))[0] == 201
        before = account_data(account)
        before_progress = RequestGenerator.GET_gamification(key, token)[1]
        before_entries = RequestGenerator.GET_piggy_bank_entries(key, token)[1]
        MockGenerator.set_cdi_rate("2026-06-01", "1.000000")
        payload = PayloadGenerator.day_closing("2026-06-01")
        status, result = RequestGenerator.POST_day_closing(payload)
        assert status == 422, result
        assert result["code"] == "QIT001032"
        assert account_data(earlier) == earlier_before
        assert RequestGenerator.GET_gamification(earlier_key, earlier_token)[1] == earlier_progress
        assert RequestGenerator.GET_piggy_bank_entries(earlier_key, earlier_token)[1] == earlier_entries
        assert account_data(account) == before
        assert RequestGenerator.GET_gamification(key, token)[1] == before_progress
        assert RequestGenerator.GET_piggy_bank_entries(key, token)[1] == before_entries
        MockGenerator.set_cdi_rate("2026-06-01")
        status, result = RequestGenerator.POST_day_closing(payload)
        assert status == 200, result
        assert result["accounting_date"] == "2026-06-02"
        MockGenerator.clear_cdi("2026-06-01")
```

- `src/controllers/base_controller.py`: no import de errors, manter AccountNotFound e acrescentar NumericLimitExceeded (criado no 3.2). Acrescentar ao fim da classe:

```python
    @staticmethod
    def check_numeric_limits(*values) -> None:
        """DAD-19: conferir acumuladores antes da escrita; erro provoca rollback integral."""
        if any(value > 9223372036854775807 for value in values):
            raise NumericLimitExceeded()
```

- `src/controllers/transaction_controller.py`: em deposit, depois de `amount = deposit_data["amount"]` e antes do try, inserir `self.check_numeric_limits(account.balance + amount)`. Em transfer, depois de `bank = self.account_repository.get_system_account(AccountType.BANK)` e antes do try, inserir `self.check_numeric_limits(destination.balance + amount)`. Não inserir em get_redemption_amounts nem em outros métodos.
- `src/controllers/piggy_bank_controller.py`: em save, depois da recusa de InsufficientBalance e antes do try, inserir `self.check_numeric_limits(piggy_bank.balance + amount)`. Em redeem, depois de `net_amount = amount - iof - ir` e antes do primeiro entry_repository.create, inserir `self.check_numeric_limits(account.balance + net_amount)`. Os lotes alterados até aqui são desfeitos pelo encerramento da sessão se a regra falhar; nenhuma escrita parcial é commitada.
- `src/controllers/gamification_controller.py`: em award_record_xp, antes de update_piggy_record, inserir `self.check_numeric_limits(piggy_bank.balance)`. Em _apply_xp_gain, antes do primeiro if, inserir `self.check_numeric_limits(xp_gain.xp, xp_gain.xp_gained, account.points_free + xp_gain.levels_gained)`. Assim nem eventos nem flush recebem BIGINT inválido.
- `src/controllers/day_closing_controller.py`: em _pay_yield, entre `cents, residue = lot_yield(...)` e update_remaining, inserir exatamente:

```python
            self.check_numeric_limits(lot.principal_remaining + lot.yield_remaining + cents,
                                      lot.yield_remaining + cents,
                                      piggy_bank.balance + sum(yield_by_category.values()) + cents)
```

As duas contas de sistema mantêm saldo nulo; nenhum acumulador novo é criado. Valores individuais fora do BIGINT continuam 400 pelo schema da fase 3. A transação aborta integralmente no 422, inclusive XP, ranque, lotes, chave e dia; o log externo é preservado (PRD-06).

**Testes:** tests/unit/infrastructure/test_numeric_limits.py tests/integration/transactions/test_numeric_overflow.py. Os casos e resultados estão nas asserções completas; integração usa apenas HTTP.
**Verificar:**
- Comando do item 4 verde.
- Suíte inteira verde e lint sem saída.
- `git diff --cached --name-only` lista exatamente:
```
src/controllers/base_controller.py
src/controllers/day_closing_controller.py
src/controllers/gamification_controller.py
src/controllers/piggy_bank_controller.py
src/controllers/transaction_controller.py
tests/integration/transactions/test_numeric_overflow.py
tests/unit/infrastructure/test_numeric_limits.py
```
- `git log -1 --format=%B`: `fix(dinheiro): limita acumuladores e desfaz overflow integralmente`.

**Pronto quando:**
- [ ] Vermelho pelo motivo definido antes do código; casos novos e suíte verdes depois.
- [ ] Arquivos e alterações iguais ao plano; lint sem saída.
- [ ] Commit local da branch conforme AGENTS.

**Commit:** `fix(dinheiro): limita acumuladores e desfaz overflow integralmente`
**Pare se:** algum nome/trecho de encaixe não existir; falha de comando; vermelho por motivo diferente; teste ou lint falhar após 3 conferências. Não mudar o teste esperado para fazê-lo passar.

---

### Passo 9.11 — Rejeitar corpo e query inesperados em todas as rotas
**Branch:** fase/09-categorias-impostos-sorteio · **Depende de:** 9.10
**Objetivo:** Rejeitar corpo e query inesperados em todas as rotas.
**Decisões:** API-19 — entradas extras; API-03 — schema fechado; R8 — dono; API-04 e PRD-13 — precedencia dos tokens
**Arquivos:**
- `src/middlewares/input_contract.py`: criar, conteúdo inteiro abaixo.
- `src/middlewares/__init__.py`: acrescentar import abaixo.
- `src/app.py`: acrescentar import e registro abaixo; preservar todas as rotas e registros atuais.
- `tests/integration/test_unexpected_inputs.py`: criar, conteúdo inteiro abaixo.

**Passo a passo:**
1. Confira branch e estado limpo conforme AGENTS, seção 7.
2. Crie primeiro os arquivos de teste listados, com o conteúdo completo abaixo.
3. Suba a API: `docker compose up -d --build --wait`.
4. Rode `./.venv/Scripts/python.exe -m pytest -v tests/integration/test_unexpected_inputs.py`. Antes do código: os dois primeiros casos falham por asserção de 400, pois GET /accounts ignora as entradas; o terceiro é uma prova e pode passar antes.
5. Aplique as alterações abaixo na ordem apresentada. Nenhum arquivo fora de **Arquivos**.
6. `docker compose up -d --build --wait`.
7. Repita o comando do item 4: todos os testes devem passar.
8. `./.venv/Scripts/python.exe -m pytest`: suíte inteira verde, sem failed/error/skipped.
9. `./.venv/Scripts/python.exe -m flake8 src tests`: nenhuma linha.
10. Feche conforme AGENTS, seção 7: `git add -- src/app.py src/middlewares/__init__.py src/middlewares/input_contract.py tests/integration/test_unexpected_inputs.py`; confira a lista exata abaixo e diffs restantes vazios; commit local da branch, um comando por vez.

- `tests/integration/test_unexpected_inputs.py` (criar): conteúdo inteiro:

```python
from uuid import uuid4

from tests.utils import ADMIN_TOKEN, DbUtils, INTERNAL_TOKEN, ObjectGenerator, PayloadGenerator, RequestGenerator
from tests.utils.requisition import ClientRequisition


def headers(account):
    return {"INTERNAL-TOKEN": INTERNAL_TOKEN, "ADMIN-TOKEN": ADMIN_TOKEN, "ACCOUNT-TOKEN": account["account_token"]}


def expect_error(response, status, code):
    assert response.response_status == status, response.response_json
    assert response.response_json["code"] == code


class TestUnexpectedInputs:
    def test_routes_without_body_reject_even_empty_json(self):
        DbUtils.rollback()
        account = ObjectGenerator.create_account()
        key, token = account["account_key"], account["account_token"]
        category = RequestGenerator.GET_categories(key, token)[1]["data"][0]["category_key"]
        routes = [("GET", f"/accounts/{key}"), ("GET", "/"), ("GET", "/health_check"),
                  ("GET", f"/customers/{account['customer_key']}"),
                  ("GET", f"/accounts/{key}/entries"), ("GET", f"/accounts/{key}/piggy_bank_entries"),
                  ("GET", f"/accounts/{key}/gamification"), ("GET", f"/accounts/{key}/categories"),
                  ("GET", f"/accounts/{key}/categories/{category}"),
                  ("DELETE", f"/accounts/{key}"), ("DELETE", f"/accounts/{key}/categories/{category}"),
                  ("POST", f"/accounts/{key}/point_resets"),
                  ("POST", f"/customers/{account['customer_key']}/accounts"),
                  ("POST", f"/internal/accounts/{key}/unblocks")]
        for method, path in routes:
            expect_error(ClientRequisition.send(method, path, payload={}, headers=headers(account)), 400, "QIT000001")
        assert RequestGenerator.GET_account(key, token)[1]["status"] == "ACTIVE"

    def test_routes_without_query_reject_any_parameter(self):
        DbUtils.rollback()
        account = ObjectGenerator.create_account()
        key, token = account["account_key"], account["account_token"]
        destination = ObjectGenerator.create_account()
        routes = [("GET", f"/accounts/{key}", None), ("GET", "/health_check", None),
                  ("POST", f"/accounts/{key}/deposits", PayloadGenerator.deposit(amount=1)),
                  ("POST", f"/accounts/{key}/withdrawals", PayloadGenerator.withdrawal(amount=1)),
                  ("POST", f"/accounts/{key}/transfers", PayloadGenerator.transfer(destination["account_key"], amount=1)),
                  ("POST", f"/accounts/{key}/savings", PayloadGenerator.saving(amount=1)),
                  ("POST", f"/accounts/{key}/redemptions", PayloadGenerator.redemption(amount=1)),
                  ("POST", f"/accounts/{key}/categories", PayloadGenerator.category())]
        for method, path, payload in routes:
            expect_error(ClientRequisition.send(method, path, payload=payload, query_params={"unexpected": "1"}, headers=headers(account)), 400, "QIT000001")
        assert RequestGenerator.GET_account(key, token)[1]["balance"] == 0

    def test_authentication_and_unknown_route_or_method_keep_precedence(self):
        DbUtils.rollback()
        account = ObjectGenerator.create_account()
        key = account["account_key"]
        bad_headers = headers(account)
        bad_headers["INTERNAL-TOKEN"] = "wrong"
        expect_error(ClientRequisition.send("GET", f"/accounts/{key}", payload={}, headers=bad_headers), 403, "QIT000002")
        bad_headers = headers(account)
        bad_headers["ACCOUNT-TOKEN"] = "wrong"
        expect_error(ClientRequisition.send("GET", f"/accounts/{key}", payload={}, headers=bad_headers), 404, "QIT001010")
        expect_error(ClientRequisition.send("GET", f"/accounts/{uuid4()}", payload={}, headers=headers(account)), 404, "QIT001010")
        expect_error(ClientRequisition.send("GET", "/unknown-route", payload={}, headers=headers(account)), 404, "QIT000404")
        expect_error(ClientRequisition.send("PUT", f"/accounts/{key}", payload={}, headers=headers(account)), 405, "QIT000405")
```

- `src/middlewares/input_contract.py` (criar): conteúdo inteiro:

```python
from fastapi import FastAPI, Request
from fastapi.concurrency import run_in_threadpool
from starlette.routing import Match

from constants import ACCOUNT_TOKEN_HEADER
from controllers.base_controller import BaseController
from controllers.customer_controller import CustomerController
from errors import InvalidSchema, QIException
from errors.handlers import qi_exception_to_response


BODY_ROUTES = {
    ("POST", "/customers"),
    ("POST", "/accounts/{account_key}/deposits"),
    ("POST", "/accounts/{account_key}/withdrawals"),
    ("POST", "/accounts/{account_key}/transfers"),
    ("POST", "/accounts/{account_key}/savings"),
    ("POST", "/accounts/{account_key}/redemptions"),
    ("POST", "/accounts/{account_key}/point_applications"),
    ("POST", "/accounts/{account_key}/categories"),
    ("POST", "/internal/accounts/{account_key}/blocks"),
    ("POST", "/internal/day_closings"),
}
QUERY_ROUTES = {
    ("GET", "/accounts/{account_key}/entries"),
    ("GET", "/accounts/{account_key}/piggy_bank_entries"),
    ("GET", "/accounts/{account_key}/categories"),
}


def check_owner(method, path, params, account_token):
    if path.startswith("/internal/"):
        return
    if "account_key" in params and (method, path) != ("POST", "/accounts/{account_key}/deposits"):
        BaseController(__name__).get_owned_account(params["account_key"], account_token)
    elif method == "GET" and path == "/customers/{customer_key}":
        CustomerController().get_by_key(params["customer_key"], account_token)


def register_input_contract_middleware(application: FastAPI) -> None:
    @application.middleware("http")
    async def check_input_contract(request: Request, call_next):
        selected = None
        params = {}
        for route in application.router.routes:
            match, scope = route.matches(request.scope)
            if match == Match.FULL:
                selected = route
                params = scope.get("path_params", {})
                break
        if selected is None:
            return await call_next(request)
        route_key = (request.method, selected.path)
        unexpected_query = route_key not in QUERY_ROUTES and len(request.query_params) > 0
        unexpected_body = route_key not in BODY_ROUTES and len(await request.body()) > 0
        if unexpected_query or unexpected_body:
            try:
                await run_in_threadpool(check_owner, request.method, selected.path, params,
                                        request.headers.get(ACCOUNT_TOKEN_HEADER))
            except QIException as error:
                return qi_exception_to_response(error)
            return qi_exception_to_response(InvalidSchema("Unexpected request body or query parameter."))
        return await call_next(request)
```

- `src/middlewares/__init__.py`: acrescentar `from middlewares.input_contract import register_input_contract_middleware`.
- `src/app.py`: acrescentar register_input_contract_middleware ao import existente de middlewares. Em create_app, inserir `register_input_contract_middleware(application)` imediatamente ANTES de `register_session_manager_middleware(application)`. O novo middleware é o primeiro registrado e o último executado: contexto, logs, barreira e tokens permanecem por fora; session_manager prepara e encerra a sessão. No corpo/query inesperado de recurso do dono, validar dono antes do 400. Se não houve Match.FULL, deixar router produzir 404/405. Nenhuma rota nova, bypass ou schema novo. Os schemas existentes continuam validando corpos e as três query strings previstas.

**Testes:** tests/integration/test_unexpected_inputs.py. Os casos e resultados estão nas asserções completas; integração usa apenas HTTP.
**Verificar:**
- Comando do item 4 verde.
- Suíte inteira verde e lint sem saída.
- `git diff --cached --name-only` lista exatamente:
```
src/app.py
src/middlewares/__init__.py
src/middlewares/input_contract.py
tests/integration/test_unexpected_inputs.py
```
- `git log -1 --format=%B`: `fix(api): rejeita entradas inesperadas preservando autenticacao`.

**Pronto quando:**
- [ ] Vermelho pelo motivo definido antes do código; casos novos e suíte verdes depois.
- [ ] Arquivos e alterações iguais ao plano; lint sem saída.
- [ ] Commit local da branch conforme AGENTS.

**Commit:** `fix(api): rejeita entradas inesperadas preservando autenticacao`
**Pare se:** algum nome/trecho de encaixe não existir; falha de comando; vermelho por motivo diferente; teste ou lint falhar após 3 conferências. Não mudar o teste esperado para fazê-lo passar.

---

### Passo 9.fim — Fechar a fase
**Branch:** fase/09-categorias-impostos-sorteio · **Depende de:** 9.1 a 9.11
**Objetivo:** provar a fase com o banco recriado do zero e levá-la para a `main` com a tag `fase-09`.
**Decisões:** TIM-04 — git por fase · TIM-08 — git automático · ARQ-03 — SQL só com o banco vazio · ARQ-04 — sobe sem `.env` · ARQ-06 — três peças no compose · DAD-07 — saldo em dois lugares · DAD-16 — lançamentos somam zero · TST-01 — suíte inteira verde
**Arquivos:** nenhum. O passo não cria, não edita e não apaga arquivo.
**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/09-categorias-impostos-sorteio`.
2. `git log --oneline -n 12` → tem as 11 mensagens abaixo, cada uma uma vez:
   ```
   feat(impostos): IOF e IR do resgate com teste unitário
   feat(impostos): IOF e IR descontados no resgate do cofrinho
   feat(categorias): repository, DTO e controller das categorias
   feat(categorias): rotas de criar e listar categorias
   feat(categorias): rotas de consultar e excluir categoria
   feat(categorias): guardar e resgatar por categoria
   feat(sorteio): sorteio da chance de não debitar com teste unitário
   feat(sorteio): chance de não debitar na transferência
   feat(cofrinho): consulta rendimento bruto e liquido por categoria
   fix(dinheiro): limita acumuladores e desfaz overflow integralmente
   fix(api): rejeita entradas inesperadas preservando autenticacao
   ```
3. Recrie o banco do zero e suba tudo, um comando por vez:
   ```
   docker compose down -v
   docker compose up -d --build --wait
   ```
4. `docker compose ps` → três serviços: `api` (healthy), `db` (healthy) e `mockserver` (running).
5. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `401 passed`.
6. `./.venv/Scripts/python.exe -m pytest` de novo → a última linha tem `401 passed` (nada intermitente).
7. Rode a conferência C1 (passo 7.12) → `0:0`.
8. Rode a conferência C2 do **Verificar** → `0:0`.
9. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
10. `git status --short` → saída vazia.
11. Leve a fase para a `main`, um comando por vez:
    ```
    git switch main
    git merge --no-ff --no-edit -m "feat(categorias): fase 09 com categorias, IR e IOF no resgate e chance de não debitar" fase/09-categorias-impostos-sorteio
    git tag fase-09
    ```
12. Rode o resto do **Verificar**.

**Testes:** nenhum teste novo. A suíte inteira (256 de integração + 145 unitários) roda duas vezes com o banco recriado do zero (itens 5 e 6).
**Verificar:**
- C2 — no banco que a suíte deixou, toda conta de cliente tem o saldo igual à soma dos lançamentos dela (DAD-07), e toda operação soma zero (DAD-16), inclusive o resgate com IOF e IR e a transferência com prêmio. Um comando, numa linha só:
  ```
  docker compose exec -T db psql -U bootcamp -d bootcamp -t -A -c "SELECT (SELECT count(*) FROM account a WHERE a.account_type_id = 1 AND a.balance <> (SELECT coalesce(sum(e.amount), 0) FROM entry e WHERE e.account_id = a.id)) || ':' || (SELECT count(*) FROM (SELECT e.transaction_id FROM entry e GROUP BY e.transaction_id HAVING sum(e.amount) <> 0) z)"
  ```
  → exatamente `0:0` (`account_type` 1 = `CUSTOMER`).
- O `git status --short` antes do merge não mostra alterações.
- `git branch --show-current` → `main`.
- `git log -1 --format=%B` → `feat(categorias): fase 09 com categorias, IR e IOF no resgate e chance de não debitar`.
- `git log -1 --format=%P` → dois hashes separados por um espaço (é um merge).
- `git tag --list fase-09` → `fase-09`.
- `git ls-files tests/integration/categories` → exatamente:
  ```
  tests/integration/categories/test_create_and_list_categories.py
  tests/integration/categories/test_get_and_delete_category.py
  ```
- `git status --short` → saída vazia.

**Pronto quando:**
- [ ] Os três serviços sobem do zero, sem `.env`; C1 e C2 dão `0:0`.
- [ ] Suíte com `401 passed`, duas vezes seguidas; lint sem saída.
- [ ] Merge `--no-ff` na `main` com a mensagem exata; tag `fase-09` criada localmente; merge local na `main`.

**Commit:** nenhum commit de passo. Mensagem do merge: `feat(categorias): fase 09 com categorias, IR e IOF no resgate e chance de não debitar`
**Pare se:**
- Faltar uma das 11 mensagens do item 2.
- `docker compose up -d --build --wait` falhar: rode `docker compose logs --tail 100 db`, `docker compose logs --tail 100 api` e `docker compose logs --tail 100 mockserver` e traga as três saídas.
- C1 ou C2 derem outra saída.
- A suíte não terminar com `401 passed` nas duas rodadas (um teste de `test_chance.py` que falha numa rodada e passa na outra também é PARE), ou o lint imprimir qualquer linha.
- O merge local der conflito (AGENTS.md, seção 8, item 9).

---

## Divergências encontradas

Seção para o Bruno; o agente não executa nada daqui.

| # | Onde | O que foi feito |
|---|---|---|
| 1 | Impostos e extrato do resgate. | COF-27 já consolidada: IR usa IOF exato, cada soma arredonda uma vez e IR inteiro respeita o teto. COF-25: conta mostra somente o líquido; resgate líquido zero não gera lançamento na conta. |
| 2 | Status público da categoria. | Por solicitação do Bruno, DTO, testes e texto usam ACTIVE/DELETED, como docs/rotas.md e as constantes internas/SQL; o DTO preserva o enumerator sem conversão para minúsculas. |
| 3 | `docs/rotas.md`, tabela do `counterparty`: "IOF e IR → BANK" no extrato. | Com a decisão 1, os lançamentos `IOF` e `IR` ficam só na conta `BANK`, que nenhum cliente consulta: a linha da tabela não aparece no extrato do cliente. Contrato que cria `docs/rotas.md` corrigido no 3.1: tabela pública sem IOF/IR e regra COF-25 explícita. |
| 4 | PLANO-00, arquivos do 9.2: só controller e teste. | Entrou `src/repositories/entry_repository.py` (`get_balance_before`): a resposta repetida de um resgate com líquido 0 (sem lançamento na conta) precisa do saldo de antes, e sem ele a repetição daria erro 500. |
| 5 | PLANO-00, arquivos do 9.8: só controller e teste novo. | Entrou a troca em `tests/integration/gamification/test_fee_with_points.py` (fase 8): ele aplica pontos em chance e depois transfere 10000, que passa a concorrer ao sorteio; com o prêmio (0,2% de chance), a tarifa medida pelo saldo sairia errada e o teste falharia de vez em quando. A última transferência dele passa a ser de 10001 (tarifa 101), que não concorre. |
| 6 | TST-01 (TDD: o teste falha antes do código) e TST-06 (o black box confere os dois resultados). | Por HTTP o teste não escolhe o resultado do sorteio, e um teste que confere os dois resultados passa também antes do código. O `test_chance.py` entra como prova, escrito depois do código; o vermelho antes do código é a conferência P1, com gerador falso no construtor do `TransactionController` (`rng`). |
| 7 | PLANO-00, 9.5: o 409 `QIT001026` (categoria com dinheiro) é da exclusão. | O teste dele está no 9.6 (`test_category_with_money_cannot_be_deleted`): antes do 9.6, só a "economias" recebe dinheiro, e ela já é barrada antes, pelo `QIT001025`. O código da regra nasce no 9.3. |
| 8 | COF-18 e R3: conferir o nome repetido. | O `create_category` não pergunta antes; quem barra é o índice, na gravação, e o `IntegrityError` vira 409 `QIT001024` (nunca 500). Assim duas criações ao mesmo tempo também dão um 201 e um 409. |
| 9 | Nenhuma decisão diz como a exclusão de categoria convive com um guardar na mesma categoria ao mesmo tempo. | `delete_category` trava a conta e o cofrinho, na ordem do `id`, como guardar e resgatar (MOV-05, MOV-11): o guardar espera, e depois vê a categoria excluída (409 `QIT001022`). |
| 10 | GAM-10 e CLI-08: a transferência premiada conta no limite diário? | Conta: é uma transferência enviada, com o `AMOUNT` negativo na origem. O prêmio é outro par de lançamentos, `PRIZE`. |
| 11 | COF-12: IOF de resgate com menos de 1 dia de prazo. | Não acontece: o lote só rende na virada, que avança o relógio. `iof_percent(0)` é recusado com `ValueError`, e `redemption_taxes` pula a parte sem rendimento antes de perguntar o percentual. |
| 12 | Testes previstos do 09: nenhum cenário de categoria, imposto ou sorteio. | Os testes desta fase saem das decisões COF e GAM (tabela de cobertura no topo). Cobertura consolidada no `09 - Plano de trabalho`: categorias, IR/IOF no resgate e chance de não debitar, com referências aos passos 9.1 a 9.8. |

## Nomes novos da fase 09 (sincronizados no PLANO-00)

Seção para o Bruno; o agente não executa nada daqui.

| Onde | Nomes |
|---|---|
| `src/calculations/taxes.py` | constantes `IOF_PERCENT_BY_DAY`, `IOF_FREE_DAYS = 30`, `IR_PERCENT_BY_TERM`, `IR_LONG_TERM_PERCENT`, `PERCENT`, `TAX_PRECISION`; assinaturas `iof_percent(days)` e `ir_percent(days)` → percentual em texto; `redemption_taxes(yield_parts)`, com `yield_parts` = lista de `(dias, centavos de rendimento)` → `(iof, ir)` |
| `src/calculations/lottery.py` | constantes novas `DRAW_SIZE = 1000`, `MAX_CHANCE_POINTS = 10`; assinaturas `is_eligible_for_prize(amount_cents)`, `draw_prize(chance_points, rng)` |
| `CategoryRepository` | `create(piggy_bank, name)`; `get_by_key(piggy_bank, category_key)`; `list_active_page(piggy_bank, limit, offset)` (pede `limit + 1`); `delete(category)`; privados novos `_add_status_event(category)`, `_get_status(enumerator)` |
| `EntryRepository` | novo `get_balance_before(account, transaction)` |
| `CategoryDTO` | `obj_to_dict(category, balance, yield_summary)`, `only_obj_key(category)` |
| `CategoryController` | `create_category(account_key, account_token, category_data)`; `list_categories(account_key, account_token, limit, offset)` → `{"categories_list_dto", "is_last_page"}`; `get_category(account_key, account_token, category_key)`; `delete_category(account_key, account_token, category_key)`; privados `_get_category`, `_lock_account_and_piggy_bank` |
| `CategoryResource` | `on_post(account_key, payload, request)`, `on_get_list(account_key, request)`, `on_get_by_key(account_key, category_key, request)`, `on_delete_by_key(account_key, category_key, request)`; constantes `DEFAULT_LIMIT = 10`, `DEFAULT_PAGE = 0` |
| `PiggyBankController` | privado novo `_get_active_category(piggy_bank, category_key)`; `_take_from_lots(category, amount, accounting_date)` passa a devolver a lista `(dias, rendimento)` |
| `TransactionController` | construtor `__init__(rng=None)`; atributo `rng` (`random.SystemRandom()` quando não vem gerador) |
| Testes | pasta `tests/integration/categories/`; ajudantes locais `create_account_with_one_day_yield`, `amounts_of`, `redemption_lines`, `names_and_balances`, `active_names`, `status_of`, `category_balances`, `create_level_ten_account`, `origin_entries`, `send_and_check`, `xp_of`; classe `FakeRandom` (no unitário); constantes `CATEGORY_FIELDS`, `PRIZE_LIMIT`, `PRIZE_LIMIT_FEE`, `PRIZE_LIMIT_XP` |
| Comportamento | o resgate grava `AMOUNT` −bruto no cofrinho, `AMOUNT` +líquido na conta e `IOF` e `IR` na conta `BANK`; valor 0 não gera lançamento; a transferência premiada grava `PRIZE` −(valor + tarifa) na `BANK` e `PRIZE` +(valor + tarifa) na origem; excluir categoria trava a conta e o cofrinho |
