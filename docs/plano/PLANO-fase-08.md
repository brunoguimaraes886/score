> **Git local — Bruno, 08/10/2026:** durante a produção, branches, commits, merges e tags ficam locais. Não executar push, pull ou fetch nem exigir acesso ao GitHub. O envio completo será feito pelo Bruno somente no final, quando tudo estiver pronto. As verificações de commits e dependências são locais.

# PLANO — Fase 08 — XP, nível e pontos

**Branch:** `fase/08-xp-pontos` · **Depende de:** fase 6
**Objetivo:** XP por transferência para quem envia e para quem recebe, níveis com 1 ponto livre cada, aplicar e zerar pontos, tarifa menor com os pontos em tarifa e a rota que mostra a gamificação; o XP de recorde do cofrinho fica pronto para a fase 7.

Regras de execução: `AGENTS.md`. Nomes obrigatórios: `docs/plano/PLANO-00-indice.md`, `docs/plano/PLANO-fase-02.md` (tabelas, models e constantes dos models), `docs/plano/PLANO-fase-03.md` (`docs/rotas.md`, catálogo de erros, schemas), `docs/plano/PLANO-fase-04.md` (`RequestGenerator`, `PayloadGenerator`, `ObjectGenerator`), `docs/plano/PLANO-fase-05.md` (`AccountRepository`, `BaseController.get_owned_account`) e `docs/plano/PLANO-fase-06.md` (`TransactionController`, `calculate_fee`). Um passo por vez, na ordem: 8.1 a 8.7 e, por último, 8.fim. A fase 8 roda antes da fase 7 (PLANO-00, "Ordem das fases").

Contagem de testes da suíte (última linha do pytest): `197 passed` no começo; `216 passed` em 8.1, 8.2 e 8.3; `222 passed` em 8.4; `231 passed` em 8.5; `240 passed` em 8.6; `244 passed` em 8.7 e no 8.fim (197 de antes + 19 unitários + 28 de integração).

Comandos usados nesta fase que não estão na seção 3 do `AGENTS.md`:

| Quero | Comando |
|---|---|
| Rodar uma linha de Python no `.venv` (a raiz do repositório no caminho de import) | `./.venv/Scripts/python.exe -c "<código>"` |
| Rodar uma linha de Python dentro do container da API | `docker compose exec -T api python -c "<código>"` |
| Procurar texto nos arquivos do Git | `git grep <opções> -- <pastas>` |
| Procurar texto também em arquivo novo, ainda fora do Git | `git grep --untracked <opções> -- <arquivo>` |

O `-T` desliga o terminal interativo, que o Git Bash não oferece. O `git grep` termina com código 1 quando não acha nada: nos itens em que o esperado é "nenhuma linha", esse código 1 sem linha impressa é o resultado certo.

Nas conferências que rodam dentro do container (`docker compose exec -T api python -c`), o código de `src/` é importado direto, sem HTTP, e tudo termina em `s.rollback()`: nada fica gravado.

Todas as saídas esperadas abaixo valem sem `.env` na raiz do repositório (ARQ-04). Existe um `.env`: PARE.

Valores de dinheiro que a fase usa para subir de nível (GAM-24; a conta está no unitário do 8.1): R$ 4.000,00 (`400000`) levam do nível 0 ao nível 1 com XP 0; R$ 17.000,00 (`1700000`) levam ao nível 2 com XP 259; R$ 830.000,00 (`83000000`) levam ao nível 10 com XP 1500. Não há valor máximo (MOV-08).

## Cobertura das regras desta fase (TST-02)

| Regra | O que fica vermelho se a regra deixar de valer |
|---|---|
| GAM-05 — o nível não cai; a sobra passa adiante | `test_xp.py::TestTransferXp::test_level_up_carries_the_rest_with_the_new_n`, `TestRecordXp::test_level_up_carries_the_rest_with_the_new_n`; `test_transfer_xp.py::test_level_up_carries_the_rest` |
| GAM-15 — 10 níveis, 1 ponto por nível | `test_xp.py::TestLevels::test_ten_levels`, `TestTransferXp::test_reaches_level_ten_and_has_no_cap`; `test_transfer_xp.py::test_reaches_level_ten_without_xp_cap` (10 pontos livres) |
| GAM-16 — fórmulas de XP; n = próximo nível, 10 no nível 10 | `test_xp.py::TestLevels::test_n_is_the_next_level_and_stays_ten`, `TestTransferXp::test_quarter_of_the_reais_at_level_zero`, `test_uses_log_of_n_times_ten`, `TestRecordXp::test_n_xp_per_whole_real`; `test_transfer_xp.py::test_each_side_uses_its_own_n`, `test_reaches_level_ten_without_xp_cap` |
| GAM-17 — XP para quem envia e para quem recebe; depósito e saque sem XP | `test_transfer_xp.py::test_both_sides_gain_xp`, `test_each_side_uses_its_own_n`, `test_only_transfers_give_xp` |
| GAM-18 — XP inteiro, truncado | `test_xp.py::TestTransferXp::test_xp_is_truncated`, `TestXpGain::test_returns_int_never_float`; `test_transfer_xp.py::test_xp_is_truncated` |
| GAM-24 — cada nível custa 1.000 × n² | `test_xp.py::TestLevels::test_level_cost_is_1000_times_n_squared`, `TestTransferXp::test_exact_cost_reaches_the_next_level`; `xp_to_next_level` em `test_transfer_xp.py` |
| GAM-25 — XP do recorde em reais inteiros | `test_xp.py::TestRecordXp` (5 testes); conferência R3 do 8.3; o lado black box nasce no 7.13 |
| GAM-04 — só passar do recorde dá XP | conferência R3 do 8.3 (`None` quando o saldo não passa do recorde); o lado black box nasce nos passos 7.5 e 7.13 |
| GAM-06 — pontos ganhos ficam livres | `test_transfer_xp.py` (`points_free` em cada nível); `test_points.py::test_applies_points_to_fee` |
| GAM-07, GAM-21 — aplicar +Y, faltou ponto → 422, zerar tudo, cada mudança é um evento | `test_points.py::test_applies_points_to_fee`, `test_applies_points_to_chance`, `test_refuses_more_than_free_points`, `test_applies_in_steps_and_resets`; conferência P1 do 8.6 |
| GAM-09 — cada ponto em tarifa tira 0,1 p.p. | `test_fee_with_points.py::test_each_fee_point_lowers_the_fee`, `test_only_fee_points_lower_the_fee`; `tests/unit/test_fee.py` (fase 6) |
| MOV-10 — tarifa zero não gera lançamento | `test_fee_with_points.py::test_ten_fee_points_make_the_fee_zero_without_entry`; conferência F1 do 8.7 |
| MOV-02 — o saldo cobre valor + a tarifa já reduzida | `test_fee_with_points.py::test_balance_must_cover_amount_plus_reduced_fee` |
| GAM-01 — gamificação por conta; conta nova começa do zero | `test_transfer_xp.py::test_new_account_after_closing_starts_from_zero`; `test_get_gamification.py::test_new_account_starts_at_zero` |
| API-14 — rota e campos da gamificação | `test_get_gamification.py::test_new_account_starts_at_zero`; `test_points.py::test_applies_points_to_fee` (o corpo inteiro) |
| CLI-09 — bloqueada mexe em pontos; CLI-05 — encerrada só lê | `test_points.py::test_blocked_account_manages_points`, `test_closed_account_is_409`; `test_get_gamification.py::test_blocked_and_closed_accounts_still_read` |
| R8, API-09 — outro dono → 404 | `test_other_account_token_is_404` e `test_missing_or_wrong_token_is_404` em `test_get_gamification.py` e `test_points.py`; `test_get_gamification.py::test_unknown_account_is_404` |
| R5 — o `id` nunca sai | `test_get_gamification.py::test_new_account_starts_at_zero` (`assert_no_internal_id`) |
| R6, DAD-08 — sem float | `test_get_gamification.py::test_new_account_starts_at_zero` (`type(...) is int`; percentuais em texto); `test_xp.py::TestXpGain::test_returns_int_never_float` |
| MOV-12 — o pedido repetido não dá XP de novo | `test_transfer_xp.py::test_repeated_transfer_gives_xp_once` |
| DAD-13 — pedido recusado não dá XP | `test_transfer_xp.py::test_refused_transfer_gives_no_xp` |
| DAD-14 — eventos e valores atuais em colunas | conferências R2 (8.2), R3 (8.3), X1 (8.5) e P1 (8.6) |
| API-03 — schema fechado | `test_points.py::test_refuses_body_out_of_schema` |
| API-04 — `INTERNAL-TOKEN` | `test_get_gamification.py::test_requires_internal_token` |

Dos "Testes previstos" do `09 - Plano de trabalho`, nenhum cenário é de gamificação (o 09 diz que eles entram quando as decisões fecharem). O critério da parte 5 na "Ordem de construção" do 09 — "transferir dá XP, o nível sobe e o ponto aplicado baixa a tarifa" — fica vermelho em `test_transfer_xp.py::test_both_sides_gain_xp` (XP), `test_level_up_carries_the_rest` (nível) e `test_fee_with_points.py::test_each_fee_point_lowers_the_fee` (tarifa). O item 6 das "Divergências" do PLANO-fase-06 (tarifa zero sem lançamento, por HTTP) é `test_fee_with_points.py::test_ten_fee_points_make_the_fee_zero_without_entry`.

---

### Passo 8.1 — XP e nível (unitário)
**Branch:** fase/08-xp-pontos · **Depende de:** fase 6 (merge `feat(dinheiro): fase 06 com depósito, saque, transferência com tarifa, limite diário, consulta e extrato` e commit `docs(plano): roteiros auditados`, os dois na `main`; tag `fase-06`)
**Objetivo:** `MAX_LEVEL`, `level_cost(next_level)`, `next_level_n(level)`, `record_whole_reais(new_balance_cents, record_cents)`, `gain_transfer_xp(level, xp, amount_cents)`, `gain_record_xp(level, xp, whole_reais)` e `XpGain` (`level`, `xp`, `xp_gained`, `levels_gained`) em `src/calculations/xp.py`, com o teste unitário escrito antes.
**Decisões:** GAM-05 — nível não cai · GAM-15 — 10 níveis · GAM-16 — fórmulas de XP · GAM-18 — XP inteiro · GAM-24 — custo do nível · GAM-25 — XP do recorde em reais · TST-05 — unitários em pasta separada, escritos primeiro · R6 — sem float
**Arquivos:**
- `tests/unit/test_xp.py` (criar): o conteúdo inteiro é:

```python
"""XP e nível: calculations.xp (GAM-05, GAM-15, GAM-16, GAM-18, GAM-24, GAM-25, TST-05).

Unitário: importa só de calculations, da biblioteca padrão e do pytest.
O pytest.ini põe src/ no caminho de import.
"""

import pytest

from calculations import MAX_LEVEL, XpGain, gain_record_xp, gain_transfer_xp, level_cost, next_level_n, record_whole_reais


class TestLevels:
    def test_ten_levels(self):
        assert MAX_LEVEL == 10

    def test_level_cost_is_1000_times_n_squared(self):
        assert level_cost(1) == 1000
        assert level_cost(2) == 4000
        assert level_cost(9) == 81000
        assert level_cost(10) == 100000
        assert sum(level_cost(next_level) for next_level in range(1, 11)) == 385000

    def test_n_is_the_next_level_and_stays_ten(self):
        assert next_level_n(0) == 1
        assert next_level_n(1) == 2
        assert next_level_n(9) == 10
        assert next_level_n(10) == 10

    def test_refuses_levels_out_of_range(self):
        for next_level in [0, 11]:
            with pytest.raises(ValueError):
                level_cost(next_level)

        for level in [-1, 11]:
            with pytest.raises(ValueError):
                next_level_n(level)


class TestTransferXp:
    def test_quarter_of_the_reais_at_level_zero(self):
        assert gain_transfer_xp(0, 0, 10000) == XpGain(0, 25, 25, 0)
        assert gain_transfer_xp(0, 0, 400) == XpGain(0, 1, 1, 0)
        assert gain_transfer_xp(0, 7, 10000) == XpGain(0, 32, 25, 0)

    def test_xp_is_truncated(self):
        assert gain_transfer_xp(0, 0, 399) == XpGain(0, 0, 0, 0)
        assert gain_transfer_xp(0, 0, 1234) == XpGain(0, 3, 3, 0)
        assert gain_transfer_xp(0, 0, 1) == XpGain(0, 0, 0, 0)

    def test_uses_log_of_n_times_ten(self):
        assert gain_transfer_xp(1, 0, 10000) == XpGain(1, 32, 32, 0)
        assert gain_transfer_xp(4, 0, 10000) == XpGain(4, 42, 42, 0)
        assert gain_transfer_xp(10, 0, 10000) == XpGain(10, 50, 50, 0)

    def test_exact_cost_reaches_the_next_level(self):
        assert gain_transfer_xp(0, 0, 400000) == XpGain(1, 0, 1000, 1)
        assert gain_transfer_xp(0, 0, 399999) == XpGain(0, 999, 999, 0)

    def test_level_up_carries_the_rest_with_the_new_n(self):
        assert gain_transfer_xp(0, 990, 10000) == XpGain(1, 19, 29, 1)

    def test_several_levels_in_one_operation(self):
        assert gain_transfer_xp(0, 0, 1700000) == XpGain(2, 259, 5259, 2)

    def test_reaches_level_ten_and_has_no_cap(self):
        assert gain_transfer_xp(0, 0, 83000000) == XpGain(10, 1500, 386500, 10)
        assert gain_transfer_xp(10, 1500, 40000) == XpGain(10, 1700, 200, 0)
        assert gain_transfer_xp(10, 1000000000, 40000) == XpGain(10, 1000000200, 200, 0)

    def test_refuses_invalid_input(self):
        for level, xp, amount_cents in [(0, 0, 0), (0, 0, -1), (0, -1, 100), (0, 1000, 100), (1, 4000, 100), (11, 0, 100), (-1, 0, 100)]:
            with pytest.raises(ValueError):
                gain_transfer_xp(level, xp, amount_cents)


class TestRecordXp:
    def test_n_xp_per_whole_real(self):
        assert gain_record_xp(0, 0, 10) == XpGain(0, 10, 10, 0)
        assert gain_record_xp(2, 0, 10) == XpGain(2, 30, 30, 0)
        assert gain_record_xp(10, 0, 7) == XpGain(10, 70, 70, 0)

    def test_level_up_carries_the_rest_with_the_new_n(self):
        assert gain_record_xp(1, 3995, 10) == XpGain(2, 22, 27, 1)
        assert gain_record_xp(0, 0, 12345) == XpGain(4, 11725, 41725, 4)

    def test_zero_reais_gives_no_xp(self):
        assert gain_record_xp(3, 7, 0) == XpGain(3, 7, 0, 0)

    def test_record_counts_whole_reais(self):
        assert record_whole_reais(100120, 100050) == 1
        assert record_whole_reais(100099, 100050) == 0
        assert record_whole_reais(500000, 0) == 5000
        assert record_whole_reais(99, 0) == 0
        assert record_whole_reais(100, 250) == 0

    def test_refuses_invalid_input(self):
        with pytest.raises(ValueError):
            gain_record_xp(0, 0, -1)

        for new_balance_cents, record_cents in [(-1, 0), (0, -1)]:
            with pytest.raises(ValueError):
                record_whole_reais(new_balance_cents, record_cents)


class TestXpGain:
    def test_fields_in_order(self):
        assert XpGain._fields == ("level", "xp", "xp_gained", "levels_gained")

    def test_returns_int_never_float(self):
        for xp_gain in [gain_transfer_xp(0, 990, 10000), gain_transfer_xp(4, 0, 10000), gain_record_xp(1, 3995, 10)]:
            assert type(xp_gain) is XpGain
            for value in xp_gain:
                assert type(value) is int, xp_gain

        assert type(record_whole_reais(100120, 100050)) is int
```

- `src/calculations/xp.py` (criar): o conteúdo inteiro é:

```python
"""XP e nível da gamificação (GAM-05, GAM-15, GAM-16, GAM-18, GAM-24, GAM-25). Conta pura: sem banco e sem HTTP.

O XP não é dinheiro, mas a conta também não passa por float: as frações
são Fraction (exatas), e o único número aproximado é o log10, calculado
em Decimal com LOG_PRECISION dígitos.
"""

from decimal import Decimal, localcontext
from fractions import Fraction
from math import floor
from typing import NamedTuple


# GAM-15: 10 níveis; o nível nunca cai (GAM-05).
MAX_LEVEL = 10

# GAM-24: cada nível custa 1.000 × n² de XP.
LEVEL_COST_FACTOR = 1000

# GAM-16, GAM-18: XP da transferência = (x / 4) · log10(n · 10), com
# x = centavos ÷ 100. Em centavos: centavos / 400 · log10(n · 10).
TRANSFER_XP_CENTS_DIVISOR = 400
LOG_ARGUMENT_FACTOR = 10

# GAM-25: o XP do recorde conta reais inteiros.
CENTS_PER_REAL = 100

# Dígitos do log10 em Decimal: muito mais do que o XP inteiro precisa.
LOG_PRECISION = 50


class XpGain(NamedTuple):
    """O resultado de um ganho de XP: o nível e o XP depois dele, quanto XP entrou e quantos níveis subiram."""

    level: int
    xp: int
    xp_gained: int
    levels_gained: int


def next_level_n(level: int) -> int:
    """O n das fórmulas (GAM-16): o próximo nível. Nível 0 → 1; nível 9 → 10; no nível 10, n continua 10."""
    if level < 0 or level > MAX_LEVEL:
        raise ValueError(f"level precisa estar entre 0 e {MAX_LEVEL}, veio {level}")

    if level == MAX_LEVEL:
        return MAX_LEVEL

    return level + 1


def level_cost(next_level: int) -> int:
    """O XP que custa chegar a next_level, saindo do nível anterior (GAM-24): 1.000 × n²."""
    if next_level < 1 or next_level > MAX_LEVEL:
        raise ValueError(f"next_level precisa estar entre 1 e {MAX_LEVEL}, veio {next_level}")

    return LEVEL_COST_FACTOR * next_level * next_level


def record_whole_reais(new_balance_cents: int, record_cents: int) -> int:
    """Quantos reais inteiros o saldo novo do cofrinho passou do recorde (GAM-25).

    reais inteiros do saldo novo − reais inteiros do recorde; nunca menos
    que 0. Os centavos não se perdem: viram XP quando completam um real.
    """
    if new_balance_cents < 0 or record_cents < 0:
        raise ValueError(f"saldo e recorde não podem ser negativos, vieram {new_balance_cents} e {record_cents}")

    whole_reais = new_balance_cents // CENTS_PER_REAL - record_cents // CENTS_PER_REAL

    if whole_reais < 0:
        return 0

    return whole_reais


def gain_transfer_xp(level: int, xp: int, amount_cents: int) -> XpGain:
    """O XP de uma transferência de amount_cents para quem está em `level` com `xp` (GAM-16, GAM-17).

    Cada centavo vale log10(n · 10) / 400 de XP, com o n do nível em que
    a conta está naquele momento.
    """
    if amount_cents < 1:
        raise ValueError(f"amount_cents precisa ser pelo menos 1, veio {amount_cents}")

    return _gain(level, xp, Fraction(amount_cents), _transfer_xp_per_cent)


def gain_record_xp(level: int, xp: int, whole_reais: int) -> XpGain:
    """O XP de um novo recorde do cofrinho: n de XP por real inteiro (GAM-16, GAM-25)."""
    if whole_reais < 0:
        raise ValueError(f"whole_reais não pode ser negativo, veio {whole_reais}")

    return _gain(level, xp, Fraction(whole_reais), _record_xp_per_real)


def _transfer_xp_per_cent(n: int) -> Fraction:
    with localcontext() as context:
        context.prec = LOG_PRECISION
        log = Decimal(n * LOG_ARGUMENT_FACTOR).log10()

    return Fraction(log) / TRANSFER_XP_CENTS_DIVISOR


def _record_xp_per_real(n: int) -> Fraction:
    return Fraction(n)


def _gain(level: int, xp: int, units: Fraction, xp_per_unit) -> XpGain:
    """Soma o XP de `units` (centavos ou reais) a quem está em `level` com `xp`.

    Enquanto o valor que resta completa o nível, a parte do valor que
    completa o nível é gasta com o n desse nível, o nível sobe, o XP zera
    e o resto do valor segue com o n novo (GAM-05, GAM-24). No nível 10, o
    XP cresce sem teto (GAM-16). O XP final é truncado uma vez, no fim
    (GAM-18): nenhuma fração se perde ao subir de nível.
    """
    if xp < 0:
        raise ValueError(f"xp não pode ser negativo, veio {xp}")

    if level < MAX_LEVEL and xp >= level_cost(next_level_n(level)):
        raise ValueError(f"xp {xp} já completa o nível {level + 1}")

    start_level = level
    start_xp = xp
    current_xp = Fraction(xp)
    remaining = units
    completed_levels_cost = 0

    while level < MAX_LEVEL:
        n = next_level_n(level)
        rate = xp_per_unit(n)
        missing_xp = level_cost(n) - current_xp

        if remaining * rate < missing_xp:
            break

        remaining = remaining - missing_xp / rate
        completed_levels_cost = completed_levels_cost + level_cost(n)
        level = level + 1
        current_xp = Fraction(0)

    final_xp = floor(current_xp + remaining * xp_per_unit(next_level_n(level)))

    return XpGain(level, final_xp, completed_levels_cost + final_xp - start_xp, level - start_level)
```

- `src/calculations/__init__.py` (editar): o conteúdo inteiro passa a ser:

```python
from calculations.fee import calculate_fee
from calculations.xp import MAX_LEVEL, XpGain, gain_record_xp, gain_transfer_xp, level_cost, next_level_n, record_whole_reais
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia.
2. Abra a fase, um comando por vez:
   ```
   git switch main
   git log --oneline
   git tag --list fase-06
   git switch -c fase/08-xp-pontos
   ```
   O `git log` mostra `docs(plano): roteiros auditados` e `feat(dinheiro): fase 06 com depósito, saque, transferência com tarifa, limite diário, consulta e extrato`; o `git tag` mostra `fase-06`.
3. Crie `tests/unit/test_xp.py` com o conteúdo do campo **Arquivos**.
4. `./.venv/Scripts/python.exe -m pytest -v tests/unit/test_xp.py` → a saída tem `ImportError` com `cannot import name 'MAX_LEVEL' from 'calculations'` e a última linha tem `1 error`. É o motivo certo (AGENTS.md, seção 6): `src/calculations/xp.py` ainda não existe.
5. Crie `src/calculations/xp.py` com o conteúdo do campo **Arquivos**.
6. Edite `src/calculations/__init__.py` com o conteúdo do campo **Arquivos**.
7. `./.venv/Scripts/python.exe -m pytest -v tests/unit/test_xp.py` → a última linha tem `19 passed`.
8. `docker compose up -d --build --wait` → termina sem erro.
9. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `216 passed`.
10. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
11. Rode o **Verificar**.
12. Feche o passo (AGENTS.md, seção 7), um comando por vez:
    ```
    git add -- tests/unit/test_xp.py src/calculations/xp.py src/calculations/__init__.py
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "feat(xp): XP e nível com teste unitário"
    git log -1 --format=%B
    ```

**Testes:** `tests/unit/test_xp.py` (TST-05). Não toca na API nem no banco. "XpGain(a, b, c, d)" = nível, XP no nível, XP ganho, níveis ganhos.

| Função de teste | Entrada | Esperado |
|---|---|---|
| `TestLevels::test_ten_levels` | `MAX_LEVEL` | 10 (GAM-15) |
| `TestLevels::test_level_cost_is_1000_times_n_squared` | `level_cost` de 1, 2, 9, 10; soma de 1 a 10 | 1000, 4000, 81000, 100000; 385000 (GAM-24) |
| `TestLevels::test_n_is_the_next_level_and_stays_ten` | `next_level_n` de 0, 1, 9, 10 | 1, 2, 10, 10 (GAM-16) |
| `TestLevels::test_refuses_levels_out_of_range` | `level_cost` de 0 e 11; `next_level_n` de −1 e 11 | `ValueError` nos quatro |
| `TestTransferXp::test_quarter_of_the_reais_at_level_zero` | nível 0: 10000 com XP 0; 400 com XP 0; 10000 com XP 7 | `XpGain(0, 25, 25, 0)`; `XpGain(0, 1, 1, 0)`; `XpGain(0, 32, 25, 0)` |
| `TestTransferXp::test_xp_is_truncated` | nível 0: 399, 1234 e 1 centavo | XP 0, 3 e 0 (GAM-18: 0,9975 e 3,085 viram 0 e 3) |
| `TestTransferXp::test_uses_log_of_n_times_ten` | 10000 nos níveis 1, 4 e 10 | XP 32, 42 e 50 (25 × log10(20), 25 × log10(50), 25 × log10(100)) |
| `TestTransferXp::test_exact_cost_reaches_the_next_level` | nível 0: 400000 e 399999 | `XpGain(1, 0, 1000, 1)`; `XpGain(0, 999, 999, 0)` |
| `TestTransferXp::test_level_up_carries_the_rest_with_the_new_n` | nível 0 com XP 990; 10000 | `XpGain(1, 19, 29, 1)`: 4000 centavos completam o nível e os 6000 restantes rendem com n = 2 (GAM-05, GAM-24) |
| `TestTransferXp::test_several_levels_in_one_operation` | nível 0; 1700000 | `XpGain(2, 259, 5259, 2)` |
| `TestTransferXp::test_reaches_level_ten_and_has_no_cap` | nível 0, 83000000; nível 10 com XP 1500, 40000; nível 10 com XP 1000000000, 40000 | `XpGain(10, 1500, 386500, 10)`; `XpGain(10, 1700, 200, 0)`; `XpGain(10, 1000000200, 200, 0)` |
| `TestTransferXp::test_refuses_invalid_input` | valor 0 e −1; XP −1; XP 1000 no nível 0; XP 4000 no nível 1; nível 11 e −1 | `ValueError` nos sete |
| `TestRecordXp::test_n_xp_per_whole_real` | 10 reais no nível 0; 10 no nível 2; 7 no nível 10 | XP 10, 30 e 70 (GAM-16: n por real) |
| `TestRecordXp::test_level_up_carries_the_rest_with_the_new_n` | nível 1 com XP 3995, 10 reais; nível 0, 12345 reais | `XpGain(2, 22, 27, 1)`; `XpGain(4, 11725, 41725, 4)` |
| `TestRecordXp::test_zero_reais_gives_no_xp` | nível 3 com XP 7; 0 reais | `XpGain(3, 7, 0, 0)` |
| `TestRecordXp::test_record_counts_whole_reais` | `record_whole_reais` de (100120, 100050), (100099, 100050), (500000, 0), (99, 0), (100, 250) | 1, 0, 5000, 0, 0 (GAM-25: só reais inteiros; nunca negativo) |
| `TestRecordXp::test_refuses_invalid_input` | `gain_record_xp` com −1 real; `record_whole_reais` com −1 em cada lado | `ValueError` nos três |
| `TestXpGain::test_fields_in_order` | `XpGain._fields` | `("level", "xp", "xp_gained", "levels_gained")` |
| `TestXpGain::test_returns_int_never_float` | três ganhos e um `record_whole_reais` | tipo `XpGain`; cada campo `int` (R6) |

**Verificar:**
- `./.venv/Scripts/python.exe -m pytest -v tests/unit/test_xp.py` → `19 passed`.
- `git grep --untracked -n -e "^import" -e "^from" -- src/calculations/xp.py` → exatamente (a conta pura importa só a biblioteca padrão):
  ```
  src/calculations/xp.py:8:from decimal import Decimal, localcontext
  src/calculations/xp.py:9:from fractions import Fraction
  src/calculations/xp.py:10:from math import floor
  src/calculations/xp.py:11:from typing import NamedTuple
  ```
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `216 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/calculations/__init__.py
  src/calculations/xp.py
  tests/unit/test_xp.py
  ```
- `git log -1 --format=%B` → `feat(xp): XP e nível com teste unitário`

**Pronto quando:**
- [ ] A branch `fase/08-xp-pontos` nasceu da `main` com o merge da fase 6.
- [ ] O teste falhou antes do código com `ImportError` (item 4) e passa depois (item 7).
- [ ] Os três arquivos têm exatamente o conteúdo do campo **Arquivos**.
- [ ] O `git grep` dá as 4 linhas esperadas.
- [ ] Suíte com `216 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/08-xp-pontos`.

**Commit:** `feat(xp): XP e nível com teste unitário`
**Pare se:**
- O `git log` do item 2 não mostrar as duas mensagens, ou o `git tag` não mostrar `fase-06`.
- O item 4 não mostrar `cannot import name 'MAX_LEVEL' from 'calculations'` (outro erro, ou algum teste rodou).
- O item 7 não terminar com `19 passed` depois de 3 tentativas de conferir `src/calculations/xp.py` contra o plano.
- A suíte não terminar com `216 passed`.

---

### Passo 8.2 — Gamificação: repository e DTO
**Branch:** fase/08-xp-pontos · **Depende de:** 8.1
**Objetivo:** `GamificationRepository` (`create_xp_event`, `create_level_event`, `create_points_event`, `create_rank_event` e os nomes novos `update_progress`, `update_points`, `update_piggy_record`) e `GamificationDTO` (`obj_to_dict`, `percent_text`; constantes novas `CDI_PERCENT_BY_RANK` e `TENTHS_PER_PERCENT`).
**Decisões:** DAD-14 — gamificação em eventos e colunas · DAD-12 — UUID no repository · R4 — evento não se altera · API-14 — rota da gamificação · COF-02 — % do CDI por ranque · GAM-09, GAM-10 — ponto vale 0,1 p.p. · GAM-14 — fim da carência · R5 — o `id` nunca sai · R6 — percentual em texto, sem float
**Arquivos:**
- `src/repositories/gamification_repository.py` (criar): o conteúdo inteiro é:

```python
from datetime import date
from uuid import uuid4

from database import Context
from models import Account, LevelEvent, PiggyRank, PointsEvent, RankEvent, Transaction, XpEvent


class GamificationRepository:
    """Grava a gamificação da conta: os eventos e os valores atuais nas colunas da conta (DAD-14).

    Nenhuma regra de negócio mora aqui: quem decide quanto XP, que nível e
    quantos pontos é o GamificationController. A key de cada evento nasce
    aqui, com uuid4 (DAD-12). Evento não se altera nem se apaga (R4): este
    repository só cria eventos; nas colunas da conta, só escreve o valor
    novo que o controller manda. Quem chama já travou a conta (MOV-05).
    """

    def __init__(self, context: Context) -> None:
        self.session = context.db_session

    def create_xp_event(self, account: Account, source: str, xp: int, accounting_date: date, transaction: Transaction = None) -> XpEvent:
        """Um ganho de XP: XpEvent.TRANSFER_SENT, TRANSFER_RECEIVED ou PIGGY_RECORD. A operação fica nula no XP da virada."""
        xp_event = XpEvent()
        xp_event.xp_event_key = str(uuid4())
        xp_event.account_id = account.id
        xp_event.source = source
        xp_event.xp = xp
        xp_event.accounting_date = accounting_date

        if transaction is not None:
            xp_event.transaction_id = transaction.id

        self.session.add(xp_event)

        return xp_event

    def create_level_event(self, account: Account, level: int, accounting_date: date) -> LevelEvent:
        """Um nível alcançado (GAM-05): cada um vale 1 ponto livre (GAM-06)."""
        level_event = LevelEvent()
        level_event.level_event_key = str(uuid4())
        level_event.account_id = account.id
        level_event.level = level
        level_event.accounting_date = accounting_date

        self.session.add(level_event)

        return level_event

    def create_points_event(self, account: Account, action: str, points: int, benefit: str = None) -> PointsEvent:
        """Uma mudança dos pontos (GAM-07, GAM-21): PointsEvent.APPLY com o benefício, ou PointsEvent.RESET sem benefício."""
        points_event = PointsEvent()
        points_event.points_event_key = str(uuid4())
        points_event.account_id = account.id
        points_event.action = action
        points_event.benefit = benefit
        points_event.points = points

        self.session.add(points_event)

        return points_event

    def create_rank_event(self, account: Account, rank_enumerator: str, kind: str, accounting_date: date) -> RankEvent:
        """Uma mudança de ranque (GAM-12, GAM-14): RankEvent.UP, GRACE_START, GRACE_END ou DOWN. Quem usa é a fase 7."""
        rank_event = RankEvent()
        rank_event.rank_event_key = str(uuid4())
        rank_event.account_id = account.id
        rank_event.rank = self.session.query(PiggyRank).filter(PiggyRank.enumerator == rank_enumerator).one()
        rank_event.kind = kind
        rank_event.accounting_date = accounting_date

        self.session.add(rank_event)

        return rank_event

    def update_progress(self, account: Account, level: int, xp: int, points_free: int) -> None:
        """Escreve o nível, o XP dentro do nível e os pontos livres da conta (DAD-14)."""
        account.level = level
        account.xp = xp
        account.points_free = points_free

    def update_points(self, account: Account, points_free: int, points_fee: int, points_chance: int) -> None:
        """Escreve os pontos livres, em tarifa e em chance da conta (DAD-14)."""
        account.points_free = points_free
        account.points_fee = points_fee
        account.points_chance = points_chance

    def update_piggy_record(self, account: Account, piggy_record: int) -> None:
        """Escreve o recorde do cofrinho, em centavos (GAM-04)."""
        account.piggy_record = piggy_record
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
```

- `src/dtos/gamification_dto.py` (criar): o conteúdo inteiro é:

```python
from calculations import MAX_LEVEL, level_cost, next_level_n
from calculations.fee import FULL_FEE_TENTHS_OF_PERCENT
from models import Account, PiggyRank


# COF-02: quanto o cofrinho rende, em % do CDI, pelo ranque. Em texto,
# como todo percentual de docs/rotas.md ("Formatos").
CDI_PERCENT_BY_RANK = {
    PiggyRank.DEFAULT: "100",
    PiggyRank.BRONZE: "102.5",
    PiggyRank.SILVER: "105",
    PiggyRank.GOLD: "110",
    PiggyRank.PLATINUM: "115",
    PiggyRank.DIAMOND: "120",
}

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

- `src/dtos/__init__.py` (editar): o conteúdo inteiro passa a ser:

```python
from dtos.customer_dto import CustomerDTO
from dtos.account_dto import AccountDTO
from dtos.transaction_dto import TransactionDTO
from dtos.entry_dto import EntryDTO
from dtos.gamification_dto import GamificationDTO
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/08-xp-pontos`; `git log --oneline` mostra `feat(xp): XP e nível com teste unitário`.
2. Crie `src/repositories/gamification_repository.py` com o conteúdo do campo **Arquivos**.
3. Edite `src/repositories/__init__.py` com o conteúdo do campo **Arquivos**.
4. Crie `src/dtos/gamification_dto.py` com o conteúdo do campo **Arquivos**.
5. Edite `src/dtos/__init__.py` com o conteúdo do campo **Arquivos**.
6. `docker compose up -d --build --wait` → termina sem erro.
7. Rode a conferência R2 do **Verificar**.
8. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `216 passed`.
9. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
10. Feche o passo (AGENTS.md, seção 7), um comando por vez:
    ```
    git add -- src/repositories/gamification_repository.py src/repositories/__init__.py src/dtos/gamification_dto.py src/dtos/__init__.py
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "feat(gamificacao): repository e DTO da gamificação"
    git log -1 --format=%B
    ```

**Testes:** nenhum teste novo. O passo é de camada de baixo; as rotas dos passos 8.4 e 8.6 usam estas peças por HTTP. Aqui, a prova é a R2: numa transação só, cadastra um cliente, abre a conta, grava um evento de cada tipo, escreve as colunas da conta, monta o DTO (também com um objeto de mentira no nível 10, ranque `DIAMOND` e carência) e desfaz tudo (`rollback`).
**Verificar:**
- R2 (um comando, numa linha só):
  ```
  docker compose exec -T api python -c "from datetime import date; from types import SimpleNamespace as N; from database import open_context; from dtos import GamificationDTO; from models import PointsEvent, RankEvent, XpEvent; from repositories import AccountRepository, CustomerRepository, GamificationRepository; c = open_context(); s = c.get_or_create_session(); x = CustomerRepository(c).create('Ana Lima', '529.982.247-25', 'ana.conferencia.r2@example.com', date(1995, 4, 12)); s.flush(); a = AccountRepository(c).create_customer_account(x, '0' * 64); g = GamificationRepository(c); d = date(2026, 6, 1); e1 = g.create_xp_event(a, XpEvent.TRANSFER_SENT, 25, d); e2 = g.create_level_event(a, 1, d); e3 = g.create_points_event(a, PointsEvent.APPLY, 1, PointsEvent.FEE); e4 = g.create_points_event(a, PointsEvent.RESET, 1); e5 = g.create_rank_event(a, 'BRONZE', RankEvent.UP, d); g.update_progress(a, 1, 19, 1); g.update_points(a, 0, 1, 0); g.update_piggy_record(a, 123456); s.flush(); print(len(e1.xp_event_key), e1.source, e1.xp, e1.transaction_id, e1.accounting_date, e1.account_id == a.id); print(len(e2.level_event_key), e2.level, e3.action, e3.benefit, e3.points, e4.action, e4.benefit, e4.points); print(len(e5.rank_event_key), e5.rank.enumerator, e5.kind); print(GamificationDTO.obj_to_dict(a)); print(GamificationDTO.obj_to_dict(N(level=10, xp=1700, points_free=0, points_fee=10, points_chance=0, rank=N(enumerator='DIAMOND'), piggy_record=5000000, grace_until=date(2026, 7, 1)))); print([GamificationDTO.percent_text(t) for t in [10, 9, 1, 0]]); s.rollback()"
  ```
  → exatamente:
  ```
  36 TRANSFER_SENT 25 None 2026-06-01 True
  36 1 APPLY FEE 1 RESET None 1
  36 BRONZE UP
  {'level': 1, 'xp': 19, 'xp_to_next_level': 3981, 'points_free': 0, 'points_fee': 1, 'points_chance': 0, 'fee_percent': '0.9', 'chance_percent': '0', 'rank': 'DEFAULT', 'cdi_percent': '100', 'piggy_record': 123456, 'grace_until': None}
  {'level': 10, 'xp': 1700, 'xp_to_next_level': None, 'points_free': 0, 'points_fee': 10, 'points_chance': 0, 'fee_percent': '0', 'chance_percent': '0', 'rank': 'DIAMOND', 'cdi_percent': '120', 'piggy_record': 5000000, 'grace_until': '2026-07-01'}
  ['1', '0.9', '0.1', '0']
  ```
- `git grep -n -e "session.delete" -e "\.delete(" -e "\.update(" -- src/repositories/gamification_repository.py` → nenhuma linha (R4: evento só se cria).
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `216 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/dtos/__init__.py
  src/dtos/gamification_dto.py
  src/repositories/__init__.py
  src/repositories/gamification_repository.py
  ```
- `git log -1 --format=%B` → `feat(gamificacao): repository e DTO da gamificação`

**Pronto quando:**
- [ ] Os dois arquivos novos e os dois `__init__.py` têm exatamente o conteúdo do campo **Arquivos**.
- [ ] A R2 dá as 6 linhas esperadas; o `git grep` não acha nada.
- [ ] Suíte com `216 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/08-xp-pontos`.

**Commit:** `feat(gamificacao): repository e DTO da gamificação`
**Pare se:**
- `docker compose up -d --build --wait` falhar com `ImportError` ou `circular import` no `docker compose logs --tail 100 api`: traga a saída.
- A R2 terminar com `Traceback` ou der outra saída depois de 3 tentativas de conferir os quatro arquivos contra o plano. Um `IntegrityError` com `customer_document_number_key` ou `customer_email_key` quer dizer que o CPF ou o e-mail da R2 já está no banco: rode `docker compose down -v`, `docker compose up -d --build --wait` e a R2 de novo.
- A suíte não terminar com `216 passed`.

---

### Passo 8.3 — Gamificação: controller
**Branch:** fase/08-xp-pontos · **Depende de:** 8.2
**Objetivo:** `GamificationController` com `get_gamification(account_key, account_token)`, `award_transfer_xp(account, amount_cents, source, transaction, accounting_date)`, `award_record_xp(account, transaction, accounting_date)` e o privado `_apply_xp_gain`: cada nível novo grava `level_event` e soma 1 ponto livre; cada ganho maior que 0 grava um `xp_event`.
**Decisões:** GAM-02 — as peças · GAM-04 — XP só ao passar do recorde · GAM-05 — a sobra passa adiante · GAM-06 — pontos livres · GAM-16, GAM-17, GAM-18, GAM-24, GAM-25 — fórmulas · DAD-14 — eventos e colunas · API-14 — rota da gamificação · R8 — outro dono → 404 · ARQ-02 — quem chama faz o commit
**Arquivos:**
- `src/controllers/gamification_controller.py` (criar): o conteúdo inteiro é:

```python
from datetime import date

from calculations import XpGain, gain_record_xp, gain_transfer_xp, record_whole_reais
from controllers.base_controller import BaseController
from dtos import GamificationDTO
from models import Account, Transaction, XpEvent
from repositories import AccountRepository, GamificationRepository


class GamificationController(BaseController):
    """XP, nível e pontos da conta (GAM-01, GAM-02, DAD-14).

    award_transfer_xp e award_record_xp não são rotas: outros controllers
    os chamam (a transferência, no passo 8.5; guardar e a virada do dia,
    na fase 7), dentro da transação deles. Quem chama já travou a conta e
    faz o commit; os dois não fazem commit.
    """

    def __init__(self) -> None:
        super().__init__(__name__)
        self.account_repository = AccountRepository(self.context)
        self.gamification_repository = GamificationRepository(self.context)

    def get_gamification(self, account_key: str, account_token: str) -> dict:
        """A gamificação da conta, só para o dono; também bloqueada ou encerrada (API-14, CLI-05). Não grava nada.

        1. a conta é do dono do token (404 QIT001010, R8).
        """
        account = self.get_owned_account(account_key, account_token)

        return GamificationDTO.obj_to_dict(account)

    def award_transfer_xp(
        self,
        account: Account,
        amount_cents: int,
        source: str,
        transaction: Transaction,
        accounting_date: date,
    ) -> XpGain:
        """Dá à conta o XP de uma transferência de amount_cents, com o n dela (GAM-16, GAM-17, GAM-18, GAM-24).

        `source`: XpEvent.TRANSFER_SENT ou XpEvent.TRANSFER_RECEIVED.
        Devolve o XpGain da conta.
        """
        xp_gain = gain_transfer_xp(account.level, account.xp, amount_cents)
        self._apply_xp_gain(account, xp_gain, source, transaction, accounting_date)

        return xp_gain

    def award_record_xp(self, account: Account, transaction: Transaction, accounting_date: date) -> XpGain:
        """Dá à conta o XP do novo recorde do cofrinho, se o saldo dele passou do recorde (GAM-04, GAM-25).

        1. o saldo do cofrinho passou do recorde (piggy_record): se não
           passou, nada muda e a resposta é None (tirar e pôr de volta não
           dá XP);
        2. o recorde passa a ser o saldo novo, em centavos;
        3. o XP é n por real inteiro que o saldo passou do recorde: os
           centavos viram XP quando completam um real.

        Quem chama (fase 7: guardar e a virada do dia) já gravou o saldo
        novo do cofrinho na mesma sessão. `transaction` é None no XP da
        virada.
        """
        piggy_bank = self.account_repository.get_piggy_bank(account)

        if piggy_bank.balance <= account.piggy_record:
            return None

        whole_reais = record_whole_reais(piggy_bank.balance, account.piggy_record)
        self.gamification_repository.update_piggy_record(account, piggy_bank.balance)

        xp_gain = gain_record_xp(account.level, account.xp, whole_reais)
        self._apply_xp_gain(account, xp_gain, XpEvent.PIGGY_RECORD, transaction, accounting_date)

        return xp_gain

    def _apply_xp_gain(self, account: Account, xp_gain: XpGain, source: str, transaction: Transaction, accounting_date: date) -> None:
        """Grava o ganho: um level_event por nível novo, o xp_event e os valores novos da conta (DAD-14).

        Ganho de 0 XP não grava nada. Cada nível novo soma 1 ponto livre
        (GAM-06).
        """
        if xp_gain.xp_gained == 0:
            return

        for level in range(account.level + 1, xp_gain.level + 1):
            self.gamification_repository.create_level_event(account, level, accounting_date)

        self.gamification_repository.create_xp_event(account, source, xp_gain.xp_gained, accounting_date, transaction)
        self.gamification_repository.update_progress(account, xp_gain.level, xp_gain.xp, account.points_free + xp_gain.levels_gained)
```

- `src/controllers/__init__.py` (editar): o conteúdo inteiro passa a ser:

```python
from controllers.customer_controller import CustomerController
from controllers.account_controller import AccountController
from controllers.transaction_controller import TransactionController
from controllers.gamification_controller import GamificationController
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/08-xp-pontos`; `git log --oneline` mostra `feat(gamificacao): repository e DTO da gamificação`.
2. Crie `src/controllers/gamification_controller.py` com o conteúdo do campo **Arquivos**.
3. Edite `src/controllers/__init__.py` com o conteúdo do campo **Arquivos**.
4. `docker compose up -d --build --wait` → termina sem erro.
5. Rode as conferências S1 e R3 do **Verificar**.
6. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `216 passed`.
7. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
8. Feche o passo (AGENTS.md, seção 7), um comando por vez:
   ```
   git add -- src/controllers/gamification_controller.py src/controllers/__init__.py
   git diff --cached --name-only
   git diff --name-only
   git ls-files --others --exclude-standard
   git commit -m "feat(gamificacao): controller do XP de transferência e de recorde"
   git log -1 --format=%B
   ```

**Testes:** nenhum teste novo. A rota de consulta nasce no 8.4 e o XP da transferência no 8.5, com os testes que ficam vermelhos antes deles. `award_record_xp` só tem rota na fase 7 (guardar, 7.5; virada, 7.13), onde ganha os testes black box; aqui, a prova é a R3: numa transação só, abre duas contas, dá XP de transferência a uma e XP de recorde à outra, mudando à mão o saldo do cofrinho, e desfaz tudo (`rollback`).
**Verificar:**
- S1 (um comando, numa linha só):
  ```
  docker compose exec -T api python -c "from controllers import GamificationController; from controllers.base_controller import BaseController; print(sorted(n for n in vars(GamificationController) if not n.startswith('_'))); print(hasattr(GamificationController, '_apply_xp_gain'), issubclass(GamificationController, BaseController))"
  ```
  → exatamente:
  ```
  ['award_record_xp', 'award_transfer_xp', 'get_gamification']
  True True
  ```
- R3 (um comando, numa linha só):
  ```
  docker compose exec -T api python -c "from datetime import date; from database import open_context; from controllers import GamificationController; from models import LevelEvent, XpEvent; from repositories import AccountRepository, CustomerRepository; c = open_context(); s = c.get_or_create_session(); x = CustomerRepository(c).create('Ana Lima', '529.982.247-25', 'ana.conferencia.r3@example.com', date(1995, 4, 12)); y = CustomerRepository(c).create('Bruno Alves', '111.444.777-35', 'bruno.conferencia.r3@example.com', date(1990, 1, 20)); s.flush(); r = AccountRepository(c); a = r.create_customer_account(x, '0' * 64); b = r.create_customer_account(y, '1' * 64); p = r.get_piggy_bank(a); g = GamificationController(); d = date(2026, 6, 1); print(g.award_transfer_xp(b, 10000, XpEvent.TRANSFER_SENT, None, d), g.award_transfer_xp(b, 396000, XpEvent.TRANSFER_RECEIVED, None, d)); print(g.award_record_xp(a, None, d)); p.balance = 1234567; print(g.award_record_xp(a, None, d), a.piggy_record, a.points_free); print(g.award_record_xp(a, None, d)); p.balance = 1234650; print(g.award_record_xp(a, None, d), a.piggy_record); p.balance = 1234660; print(g.award_record_xp(a, None, d), a.piggy_record); s.flush(); print(s.query(XpEvent).filter(XpEvent.account_id == a.id).count(), [e.level for e in s.query(LevelEvent).filter(LevelEvent.account_id == a.id).order_by(LevelEvent.id)], (b.level, b.xp, b.points_free)); s.rollback()"
  ```
  → exatamente:
  ```
  XpGain(level=0, xp=25, xp_gained=25, levels_gained=0) XpGain(level=1, xp=19, xp_gained=994, levels_gained=1)
  None
  XpGain(level=4, xp=11725, xp_gained=41725, levels_gained=4) 1234567 4
  None
  XpGain(level=4, xp=11730, xp_gained=5, levels_gained=0) 1234650
  XpGain(level=4, xp=11730, xp_gained=0, levels_gained=0) 1234660
  2 [1, 2, 3, 4] (1, 19, 1)
  ```
  Linha a linha: a transferência de R$ 100,00 dá 25 XP e a de R$ 3.960,00, com 25 XP de antes, passa do nível 1 e sobram 19 XP com n = 2; cofrinho em 0 com recorde 0 não dá XP (GAM-04); R$ 12.345,67 dão 12.345 reais de recorde e 4 níveis; o mesmo saldo de novo não dá XP; R$ 12.346,50 dão 1 real a n = 5; R$ 12.346,60 não completam outro real: 0 XP, sem evento, mas o recorde sobe; no banco, 2 `xp_event` e os 4 `level_event` da conta `a`.
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `216 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/controllers/__init__.py
  src/controllers/gamification_controller.py
  ```
- `git log -1 --format=%B` → `feat(gamificacao): controller do XP de transferência e de recorde`

**Pronto quando:**
- [ ] Os dois arquivos têm exatamente o conteúdo do campo **Arquivos**.
- [ ] S1 e R3 dão a saída esperada.
- [ ] Suíte com `216 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/08-xp-pontos`.

**Commit:** `feat(gamificacao): controller do XP de transferência e de recorde`
**Pare se:**
- `docker compose up -d --build --wait` falhar com `ImportError` ou `circular import` no `docker compose logs --tail 100 api`: traga a saída.
- A R3 terminar com `Traceback` ou der outra saída depois de 3 tentativas de conferir os dois arquivos contra o plano. Um `IntegrityError` com `customer_document_number_key` ou `customer_email_key`: rode `docker compose down -v`, `docker compose up -d --build --wait` e a R3 de novo.
- A suíte não terminar com `216 passed`.

---

### Passo 8.4 — `GET /accounts/{account_key}/gamification`
**Branch:** fase/08-xp-pontos · **Depende de:** 8.3
**Objetivo:** `GamificationResource.on_get` e a rota `GET /accounts/{account_key}/gamification` (tokens: conta; sem schema): 200 com o corpo de `docs/rotas.md` ("Gamificação"); 404 `QIT001010`; 403 `QIT000002`. Conta bloqueada ou encerrada lê.
**Decisões:** API-14 — rota da gamificação · GAM-01 — gamificação por conta · CLI-05 — encerrada e bloqueada só leem · R8, API-09 — outro dono → 404 · API-02 — 200 na consulta · R5 — o `id` nunca sai · R6, DAD-08 — inteiros e percentuais em texto · TST-01 — black box e TDD
**Arquivos:**
- `src/resources/gamification.py` (criar): o conteúdo inteiro é:

```python
from fastapi import Request
from fastapi import status as http_status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from constants import ACCOUNT_TOKEN_HEADER
from controllers import GamificationController


class GamificationResource:
    """A porta HTTP da gamificação: consultar, aplicar pontos e zerar pontos.

    Sem regra de negócio, sem SQL e sem nada guardado no self (ARQ-02). O
    token da conta chega no cabeçalho ACCOUNT-TOKEN (API-16); quem o
    confere é o controller.
    """

    def on_get(self, account_key: str, request: Request) -> JSONResponse:
        controller = GamificationController()
        gamification = controller.get_gamification(account_key, request.headers.get(ACCOUNT_TOKEN_HEADER))

        return JSONResponse(
            content=jsonable_encoder(gamification),
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
```

- `src/app.py` (editar): três trocas, e nada mais.
  1. A linha
     ```python
     from resources import AccountResource, CustomerResource, HealthCheckResource, InternalResource, TransactionResource
     ```
     vira
     ```python
     from resources import AccountResource, CustomerResource, GamificationResource, HealthCheckResource, InternalResource, TransactionResource
     ```
  2. A linha
     ```python
         transaction_resource = TransactionResource()
     ```
     vira as duas linhas
     ```python
         transaction_resource = TransactionResource()
         gamification_resource = GamificationResource()
     ```
  3. A linha
     ```python
         application.add_api_route("/accounts/{account_key}/entries", transaction_resource.on_get_entries, methods=["GET"])
     ```
     vira as quatro linhas
     ```python
         application.add_api_route("/accounts/{account_key}/entries", transaction_resource.on_get_entries, methods=["GET"])

         # Gamificação
         application.add_api_route("/accounts/{account_key}/gamification", gamification_resource.on_get, methods=["GET"])
     ```
  O bloco das rotas fica exatamente assim (de `health_check_resource = HealthCheckResource()` até `register_error_handlers(application)`):
  ```python
      health_check_resource = HealthCheckResource()
      customer_resource = CustomerResource()
      account_resource = AccountResource()
      internal_resource = InternalResource()
      transaction_resource = TransactionResource()
      gamification_resource = GamificationResource()

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

      # Rotas internas (API-13): INTERNAL-TOKEN e ADMIN-TOKEN
      application.add_api_route("/internal/accounts/{account_key}/blocks", internal_resource.on_post_block, methods=["POST"])
      application.add_api_route("/internal/accounts/{account_key}/unblocks", internal_resource.on_post_unblock, methods=["POST"])

      register_error_handlers(application)
  ```

- `tests/integration/gamification/test_get_gamification.py` (criar; a pasta `tests/integration/gamification/` é nova e fica sem `__init__.py`): o conteúdo inteiro é:

```python
"""Gamificação da conta: GET /accounts/{account_key}/gamification (API-14, GAM-01, GAM-02, CLI-05, R5, R8).

Só o dono vê: XP, nível e XP que falta; pontos livres, em tarifa e em
chance; tarifa e chance atuais; ranque, % do CDI, recorde do cofrinho e
fim da carência. Conta bloqueada ou encerrada continua lendo. Os testes
que erram o token começam com DbUtils.rollback() (PRD-10).
"""

from uuid import uuid4

from tests.utils import DbUtils, ObjectGenerator, PayloadGenerator, RequestGenerator


NEW_ACCOUNT_GAMIFICATION = {
    "level": 0,
    "xp": 0,
    "xp_to_next_level": 1000,
    "points_free": 0,
    "points_fee": 0,
    "points_chance": 0,
    "fee_percent": "1",
    "chance_percent": "0",
    "rank": "DEFAULT",
    "cdi_percent": "100",
    "piggy_record": 0,
    "grace_until": None,
}
INTEGER_FIELDS = ["level", "xp", "xp_to_next_level", "points_free", "points_fee", "points_chance", "piggy_record"]


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


def get_gamification(account: dict) -> tuple:
    return RequestGenerator.GET_gamification(account["account_key"], account["account_token"])


def assert_owner_reads(account: dict) -> None:
    status, response = get_gamification(account)
    assert status == 200, response


def assert_account_not_found(status: int, response: dict) -> None:
    assert status == 404, response
    assert response["code"] == "QIT001010"


class TestGetGamification:
    def test_new_account_starts_at_zero(self):
        account = ObjectGenerator.create_account()

        status, response = get_gamification(account)

        assert status == 200, response
        assert response == NEW_ACCOUNT_GAMIFICATION
        for field in INTEGER_FIELDS:
            assert type(response[field]) is int, field
        assert_no_internal_id(response)

    def test_blocked_and_closed_accounts_still_read(self):
        blocked_account = ObjectGenerator.create_account()
        status, response = RequestGenerator.POST_block(blocked_account["account_key"], PayloadGenerator.block())
        assert status == 204, response

        closed_account = ObjectGenerator.create_account()
        status, response = RequestGenerator.DELETE_account(closed_account["account_key"], closed_account["account_token"])
        assert status == 204, response

        for account in [blocked_account, closed_account]:
            status, response = get_gamification(account)

            assert status == 200, response
            assert response == NEW_ACCOUNT_GAMIFICATION

    def test_other_account_token_is_404(self):
        DbUtils.rollback()
        first = ObjectGenerator.create_account()
        second = ObjectGenerator.create_account()

        status, response = RequestGenerator.GET_gamification(first["account_key"], second["account_token"])
        assert_account_not_found(status, response)

        status, response = RequestGenerator.GET_gamification(second["account_key"], first["account_token"])
        assert_account_not_found(status, response)

        assert_owner_reads(first)

    def test_missing_or_wrong_token_is_404(self):
        DbUtils.rollback()
        account = ObjectGenerator.create_account()

        for account_token in [None, "token_errado"]:
            status, response = RequestGenerator.GET_gamification(account["account_key"], account_token)
            assert_account_not_found(status, response)

        assert_owner_reads(account)

    def test_unknown_account_is_404(self):
        DbUtils.rollback()
        account = ObjectGenerator.create_account()

        for account_key in [str(uuid4()), "nao-e-uma-key"]:
            status, response = RequestGenerator.GET_gamification(account_key, account["account_token"])
            assert_account_not_found(status, response)

        assert_owner_reads(account)

    def test_requires_internal_token(self):
        DbUtils.rollback()
        account = ObjectGenerator.create_account()

        assert_owner_reads(account)

        status, response = RequestGenerator.GET_gamification(account["account_key"], account["account_token"], internal_token=None)

        assert status == 403, response
        assert response["code"] == "QIT000002"
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/08-xp-pontos`; `git log --oneline` mostra `feat(gamificacao): controller do XP de transferência e de recorde`.
2. Crie `tests/integration/gamification/test_get_gamification.py` com o conteúdo do campo **Arquivos**.
3. `docker compose up -d --build --wait`.
4. `./.venv/Scripts/python.exe -m pytest -v tests/integration/gamification/test_get_gamification.py` → a última linha tem `6 failed` e não tem `passed`. Os 6 falham por asserção: hoje o caminho `/accounts/{account_key}/gamification` responde 404 `QIT000404` (onde o teste espera 200, ou 404 com `QIT001010`).
5. Crie `src/resources/gamification.py` com o conteúdo do campo **Arquivos**.
6. Edite `src/resources/__init__.py` com o conteúdo do campo **Arquivos**.
7. Faça as três trocas em `src/app.py` e confira o bloco das rotas contra o do campo **Arquivos**.
8. `docker compose up -d --build --wait`.
9. `./.venv/Scripts/python.exe -m pytest -v tests/integration/gamification/test_get_gamification.py` → a última linha tem `6 passed`.
10. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `222 passed`.
11. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
12. Feche o passo (AGENTS.md, seção 7), um comando por vez:
    ```
    git add -- src/resources/gamification.py src/resources/__init__.py src/app.py tests/integration/gamification/test_get_gamification.py
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "feat(gamificacao): rota de consulta da gamificação"
    git log -1 --format=%B
    ```

**Testes:** `tests/integration/gamification/test_get_gamification.py`. A rota só lê: nenhum efeito no banco além da linha de `request_log` (as recusas gravam `auth_failure = ACCOUNT`).

| Função de teste | Entrada | Esperado |
|---|---|---|
| `test_new_account_starts_at_zero` | conta nova; `GET .../gamification` com o token dela | 200 e exatamente `{"level": 0, "xp": 0, "xp_to_next_level": 1000, "points_free": 0, "points_fee": 0, "points_chance": 0, "fee_percent": "1", "chance_percent": "0", "rank": "DEFAULT", "cdi_percent": "100", "piggy_record": 0, "grace_until": null}`; os 7 campos numéricos são `int`; nenhum `id` em nenhum nível (GAM-01, API-14, R5) |
| `test_blocked_and_closed_accounts_still_read` | conta bloqueada pela rota interna; outra encerrada pelo dono | 200 e o mesmo corpo de conta nova nas duas (CLI-05) |
| `test_other_account_token_is_404` | começa com `DbUtils.rollback()`; contas A e B; A com o token de B; B com o token de A; A com o de A | 404 `QIT001010` nos dois primeiros; 200 (R8) |
| `test_missing_or_wrong_token_is_404` | começa com `DbUtils.rollback()`; sem `ACCOUNT-TOKEN` e com `token_errado`; depois o token certo | 404 `QIT001010` nos dois; 200 |
| `test_unknown_account_is_404` | começa com `DbUtils.rollback()`; key UUID que não existe e `nao-e-uma-key`, com o token de A; depois A com o token de A | 404 `QIT001010` nos dois; 200 |
| `test_requires_internal_token` | começa com `DbUtils.rollback()`; A com os dois tokens; depois sem `INTERNAL-TOKEN` | 200; 403 `QIT000002` (API-04) |

**Verificar:**
- `./.venv/Scripts/python.exe -m pytest -v tests/integration/gamification/test_get_gamification.py` → `6 passed`.
- `git grep -n "gamification_resource" -- src/app.py` → exatamente 2 linhas: a do `gamification_resource = GamificationResource()` e a da rota `/accounts/{account_key}/gamification`.
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `222 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/app.py
  src/resources/__init__.py
  src/resources/gamification.py
  tests/integration/gamification/test_get_gamification.py
  ```
- `git log -1 --format=%B` → `feat(gamificacao): rota de consulta da gamificação`

**Pronto quando:**
- [ ] Os 6 testes falharam antes do código (item 4) e passam depois (item 9).
- [ ] O bloco das rotas de `src/app.py` é o do campo **Arquivos**.
- [ ] Suíte com `222 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/08-xp-pontos`.

**Commit:** `feat(gamificacao): rota de consulta da gamificação`
**Pare se:**
- O item 4 não terminar com `6 failed`.
- Alguma linha citada nas trocas de `src/app.py` não for encontrada igual.
- Um teste receber 500 (`QIT000500`): rode `docker compose logs --tail 100 api` e traga a saída.
- Um teste receber 403 onde o plano espera 404 (R8).
- A suíte não terminar com `222 passed`.

---

### Passo 8.5 — XP na transferência
**Branch:** fase/08-xp-pontos · **Depende de:** 8.4
**Objetivo:** `TransactionController.transfer` chama `GamificationController.award_transfer_xp` para quem envia (`XpEvent.TRANSFER_SENT`) e para quem recebe (`XpEvent.TRANSFER_RECEIVED`), cada um com o seu n, dentro da transação da transferência, depois dos lançamentos e antes do commit.
**Decisões:** GAM-16 — fórmulas de XP · GAM-17 — XP dos dois lados · GAM-18 — XP inteiro · GAM-24 — custo do nível · GAM-05 — a sobra passa adiante · GAM-06 — 1 ponto livre por nível · GAM-01 — conta nova começa do zero · MOV-12 — o repetido não dá XP de novo · DAD-13 — recusa não grava · DAD-14 — eventos e colunas · TST-01 — black box e TDD
**Arquivos:**
- `src/controllers/transaction_controller.py` (editar): três mudanças, e nada mais.
  1. Tudo o que vem antes da linha `class TransactionController(BaseController):` passa a ser exatamente o bloco abaixo (seguido de duas linhas em branco antes do `class`). Muda em relação ao 6.10: a linha `from controllers.gamification_controller import GamificationController` e o `XpEvent` no import de `models`, que passa a ter um nome por linha.

```python
from sqlalchemy.exc import IntegrityError

from calculations import calculate_fee
from constants import DAILY_TRANSFER_LIMIT
from controllers.base_controller import BaseController
from controllers.gamification_controller import GamificationController
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
from models import (
    Account,
    AccountStatus,
    AccountStatusEvent,
    AccountType,
    BlockReason,
    Entry,
    EntryType,
    Transaction,
    TransactionType,
    XpEvent,
)
from repositories import AccountRepository, BankClockRepository, DepositRepository, EntryRepository, TransactionRepository
from utils.document_number import FORMATTED_CPF_LENGTH, is_valid_cnpj, is_valid_cpf
from utils.request_hash import hash_request_body


# CLI-08: limite configurável no ambiente; padrão 10.
```

  2. A linha
     ```python
             self.transaction_repository = TransactionRepository(self.context)
     ```
     vira as duas linhas
     ```python
             self.transaction_repository = TransactionRepository(self.context)
             self.gamification_controller = GamificationController()
     ```
  3. O método `transfer` inteiro (da linha `    def transfer(` até a linha `        return transaction_dto` que o fecha, antes de `    def get_transaction(`) passa a ser:

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
        +tarifa na conta BANK. Tarifa zero não gera lançamento (MOV-10). Em
        seguida, o XP do valor para a origem (TRANSFER_SENT) e para o
        destino (TRANSFER_RECEIVED), cada um com o seu n (GAM-16, GAM-17),
        na mesma transação: o pedido repetido devolve a resposta da
        primeira vez e não dá XP de novo. A resposta traz a key e o saldo
        novo da origem (API-10).
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

- `tests/integration/gamification/test_transfer_xp.py` (criar): o conteúdo inteiro é:

```python
"""XP da transferência: POST /accounts/{account_key}/transfers e GET .../gamification (GAM-01, GAM-05, GAM-06, GAM-15 a GAM-18, GAM-24).

Quem envia e quem recebe ganham (x / 4) · log10(n · 10) de XP, com
x = valor em reais e n = o próximo nível de cada um; o XP é inteiro,
truncado. Cada nível custa 1.000 × n² e dá 1 ponto livre; ao subir, o
resto do valor rende com o n novo. Depósito, saque e pedido recusado não
dão XP; o pedido repetido não dá XP de novo.
"""

from tests.utils import ObjectGenerator, PayloadGenerator, RequestGenerator


# GAM-24: R$ 4.000,00 dão exatamente os 1.000 XP do nível 1 (n = 1).
LEVEL_ONE_AMOUNT = 400000

# R$ 830.000,00 passam dos 385.000 XP dos 10 níveis e sobram 1.500 XP no nível 10.
LEVEL_TEN_AMOUNT = 83000000


def gamification_of(account: dict) -> dict:
    status, response = RequestGenerator.GET_gamification(account["account_key"], account["account_token"])
    assert status == 200, response

    return response


def progress_of(account: dict) -> tuple:
    """(nível, XP, XP que falta, pontos livres) da conta."""
    gamification = gamification_of(account)

    return gamification["level"], gamification["xp"], gamification["xp_to_next_level"], gamification["points_free"]


def transfer(origin: dict, destination: dict, amount: int) -> tuple:
    payload = PayloadGenerator.transfer(destination["account_key"], amount=amount)

    return RequestGenerator.POST_transfer(origin["account_key"], origin["account_token"], payload)


def send(origin: dict, destination: dict, amount: int) -> None:
    status, response = transfer(origin, destination, amount)
    assert status == 201, response


def create_level_one_account() -> dict:
    """Uma conta que recebeu R$ 4.000,00: nível 1, XP 0, 1 ponto livre e saldo 400000."""
    sender = ObjectGenerator.create_funded_account(LEVEL_ONE_AMOUNT + LEVEL_ONE_AMOUNT // 100)
    receiver = ObjectGenerator.create_account()
    send(sender, receiver, LEVEL_ONE_AMOUNT)

    return receiver


class TestTransferXp:
    def test_both_sides_gain_xp(self):
        origin = ObjectGenerator.create_funded_account(10100)
        destination = ObjectGenerator.create_account()

        send(origin, destination, 10000)

        assert progress_of(origin) == (0, 25, 975, 0)
        assert progress_of(destination) == (0, 25, 975, 0)

    def test_xp_is_truncated(self):
        origin = ObjectGenerator.create_funded_account(2000)
        destination = ObjectGenerator.create_account()

        send(origin, destination, 399)
        assert progress_of(origin) == (0, 0, 1000, 0)
        assert progress_of(destination) == (0, 0, 1000, 0)

        send(origin, destination, 1234)
        assert progress_of(origin) == (0, 3, 997, 0)
        assert progress_of(destination) == (0, 3, 997, 0)

    def test_each_side_uses_its_own_n(self):
        receiver = create_level_one_account()
        assert progress_of(receiver) == (1, 0, 4000, 1)

        sender = ObjectGenerator.create_funded_account(10100)
        send(sender, receiver, 10000)

        assert progress_of(sender) == (0, 25, 975, 0)
        assert progress_of(receiver) == (1, 32, 3968, 1)

    def test_level_up_carries_the_rest(self):
        origin = ObjectGenerator.create_funded_account(396000 + 3960 + 10000 + 100)
        first_destination = ObjectGenerator.create_account()
        second_destination = ObjectGenerator.create_account()

        send(origin, first_destination, 396000)
        assert progress_of(origin) == (0, 990, 10, 0)

        send(origin, second_destination, 10000)

        assert progress_of(origin) == (1, 19, 3981, 1)
        assert progress_of(first_destination) == (0, 990, 10, 0)
        assert progress_of(second_destination) == (0, 25, 975, 0)

    def test_reaches_level_ten_without_xp_cap(self):
        origin = ObjectGenerator.create_funded_account(LEVEL_TEN_AMOUNT + LEVEL_TEN_AMOUNT // 100)
        destination = ObjectGenerator.create_account()

        send(origin, destination, LEVEL_TEN_AMOUNT)

        assert progress_of(origin) == (10, 1500, None, 10)
        assert progress_of(destination) == (10, 1500, None, 10)

        send(destination, origin, 40000)

        assert progress_of(destination) == (10, 1700, None, 10)
        assert progress_of(origin) == (10, 1700, None, 10)

    def test_only_transfers_give_xp(self):
        account = ObjectGenerator.create_funded_account(100000)
        destination = ObjectGenerator.create_account()

        withdrawal = PayloadGenerator.withdrawal(amount=50000)
        status, response = RequestGenerator.POST_withdrawal(account["account_key"], account["account_token"], withdrawal)
        assert status == 201, response
        assert progress_of(account) == (0, 0, 1000, 0)

        send(account, destination, 10000)
        assert progress_of(account) == (0, 25, 975, 0)

    def test_refused_transfer_gives_no_xp(self):
        origin = ObjectGenerator.create_funded_account(10099)
        destination = ObjectGenerator.create_account()

        status, response = transfer(origin, destination, 10000)
        assert status == 422, response
        assert response["code"] == "QIT001015"
        assert progress_of(origin) == (0, 0, 1000, 0)
        assert progress_of(destination) == (0, 0, 1000, 0)

        send(origin, destination, 9000)
        assert progress_of(origin) == (0, 22, 978, 0)
        assert progress_of(destination) == (0, 22, 978, 0)

    def test_repeated_transfer_gives_xp_once(self):
        origin = ObjectGenerator.create_funded_account(20200)
        destination = ObjectGenerator.create_account()
        payload = PayloadGenerator.transfer(destination["account_key"], amount=10000)

        first_status, first_response = RequestGenerator.POST_transfer(origin["account_key"], origin["account_token"], payload)
        second_status, second_response = RequestGenerator.POST_transfer(origin["account_key"], origin["account_token"], payload)

        assert (first_status, second_status) == (201, 201), (first_response, second_response)
        assert second_response == first_response
        assert progress_of(origin) == (0, 25, 975, 0)
        assert progress_of(destination) == (0, 25, 975, 0)

    def test_new_account_after_closing_starts_from_zero(self):
        old_account = create_level_one_account()

        status, response = RequestGenerator.POST_withdrawal(
            old_account["account_key"], old_account["account_token"], PayloadGenerator.withdrawal(amount=LEVEL_ONE_AMOUNT)
        )
        assert status == 201, response

        status, response = RequestGenerator.DELETE_account(old_account["account_key"], old_account["account_token"])
        assert status == 204, response

        status, response = RequestGenerator.POST_account(old_account["customer_key"])
        assert status == 201, response
        new_account = {"account_key": response["account_key"], "account_token": response["account_token"]}

        assert progress_of(new_account) == (0, 0, 1000, 0)
        assert progress_of(old_account) == (1, 0, 4000, 1)
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/08-xp-pontos`; `git log --oneline` mostra `feat(gamificacao): rota de consulta da gamificação`.
2. Crie `tests/integration/gamification/test_transfer_xp.py` com o conteúdo do campo **Arquivos**.
3. `docker compose up -d --build --wait`.
4. `./.venv/Scripts/python.exe -m pytest -v tests/integration/gamification/test_transfer_xp.py` → a última linha tem `9 failed` e não tem `passed`. Os 9 falham por asserção: hoje a transferência não dá XP, e a gamificação das contas continua em nível 0 com XP 0.
5. Faça as três mudanças em `src/controllers/transaction_controller.py`.
6. `docker compose up -d --build --wait`.
7. `./.venv/Scripts/python.exe -m pytest -v tests/integration/gamification/test_transfer_xp.py` → a última linha tem `9 passed`.
8. Rode as conferências S2 e X1 do **Verificar**.
9. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `231 passed` (os testes de transferência da fase 6 continuam verdes: o XP não muda saldo nenhum).
10. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
11. Feche o passo (AGENTS.md, seção 7), um comando por vez:
    ```
    git add -- src/controllers/transaction_controller.py tests/integration/gamification/test_transfer_xp.py
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "feat(xp): XP para quem envia e para quem recebe a transferência"
    git log -1 --format=%B
    ```

**Testes:** `tests/integration/gamification/test_transfer_xp.py`. Efeito no banco de cada transferência com 201: além do que a fase 6 grava, um `xp_event` por lado com XP ganho maior que 0 (com a operação e a data contábil), um `level_event` por nível novo e as colunas `level`, `xp` e `points_free` das duas contas (conferência X1). Recusa e repetição não gravam XP.

| Função de teste | Entrada | Esperado |
|---|---|---|
| `test_both_sides_gain_xp` | origem com 10100; 10000 para uma conta nova | as duas: nível 0, XP 25, faltam 975, 0 pontos livres (GAM-16, GAM-17) |
| `test_xp_is_truncated` | origem com 2000; 399; depois 1234 | as duas com XP 0 (0,9975 truncado); depois XP 3 (GAM-18) |
| `test_each_side_uses_its_own_n` | conta R no nível 1 (recebeu 400000); outra conta, no nível 0, manda 10000 para R | quem envia: XP 25 (n = 1); R: nível 1, XP 32, faltam 3968, 1 ponto livre (n = 2) |
| `test_level_up_carries_the_rest` | origem com 410060; 396000 para B; 10000 para C | a origem com XP 990 e depois nível 1, XP 19, faltam 3981, 1 ponto livre; B com XP 990; C com XP 25 (GAM-05, GAM-24) |
| `test_reaches_level_ten_without_xp_cap` | origem com 83830000; 83000000 para uma conta nova; a conta nova devolve 40000 | as duas no nível 10, XP 1500, `xp_to_next_level` nulo, 10 pontos livres; depois as duas com XP 1700 (n continua 10, sem teto; GAM-15, GAM-16) |
| `test_only_transfers_give_xp` | conta com depósito de 100000; saque de 50000; transferência de 10000 | XP 0 depois do depósito e do saque; XP 25 depois da transferência (GAM-17) |
| `test_refused_transfer_gives_no_xp` | origem com 10099; 10000 (sem saldo para a tarifa); depois 9000 | 422 `QIT001015` e XP 0 nas duas; depois XP 22 nas duas (DAD-13) |
| `test_repeated_transfer_gives_xp_once` | o mesmo corpo de 10000 duas vezes | 201 duas vezes, corpos iguais; XP 25 em cada lado, uma vez só (MOV-12) |
| `test_new_account_after_closing_starts_from_zero` | conta no nível 1; saque de tudo; encerramento; nova conta para o mesmo cliente | a nova: nível 0, XP 0, faltam 1000, 0 pontos; a encerrada continua no nível 1 com 1 ponto (GAM-01) |

**Verificar:**
- `./.venv/Scripts/python.exe -m pytest -v tests/integration/gamification/test_transfer_xp.py` → `9 passed`.
- S2 (um comando, numa linha só):
  ```
  docker compose exec -T api python -c "import inspect; from controllers import TransactionController; src = inspect.getsource(TransactionController.transfer); print(src.count('award_transfer_xp('), 'XpEvent.TRANSFER_SENT' in src, 'XpEvent.TRANSFER_RECEIVED' in src, src.index('award_transfer_xp(') < src.rindex('self.session.commit()'))"
  ```
  → `2 True True True`
- X1 — o que a transferência grava de XP (DAD-14, GAM-06). Um comando, numa linha só:
  ```
  ./.venv/Scripts/python.exe -c "from sqlalchemy import create_engine, text; from tests.utils import DbUtils, ObjectGenerator, PayloadGenerator, RequestGenerator; a = ObjectGenerator.create_funded_account(404000); b = ObjectGenerator.create_account(); s, r = RequestGenerator.POST_transfer(a['account_key'], a['account_token'], PayloadGenerator.transfer(b['account_key'], amount=400000)); print(s, r['balance']); c = create_engine(DbUtils.database_url()).connect(); k = {'t': r['transaction_key'], 'a': a['account_key'], 'b': b['account_key']}; print(c.execute(text('SELECT x.source, x.xp, m.account_key = :a, x.accounting_date = t.accounting_date FROM xp_event x JOIN transaction t ON t.id = x.transaction_id JOIN account m ON m.id = x.account_id WHERE t.transaction_key = :t ORDER BY x.id'), k).fetchall()); print(c.execute(text('SELECT m.account_key = :a, l.level FROM level_event l JOIN account m ON m.id = l.account_id WHERE m.account_key IN (:a, :b) ORDER BY l.id'), k).fetchall()); print(c.execute(text('SELECT level, xp, points_free FROM account WHERE account_key IN (:a, :b) ORDER BY id'), k).fetchall())"
  ```
  → exatamente:
  ```
  201 0
  [('TRANSFER_SENT', 1000, True, True), ('TRANSFER_RECEIVED', 1000, False, True)]
  [(True, 1), (False, 1)]
  [(1, 0, 1), (1, 0, 1)]
  ```
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `231 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/controllers/transaction_controller.py
  tests/integration/gamification/test_transfer_xp.py
  ```
- `git log -1 --format=%B` → `feat(xp): XP para quem envia e para quem recebe a transferência`

**Pronto quando:**
- [ ] Os 9 testes falharam antes do código (item 4) e passam depois (item 7).
- [ ] S2 e X1 dão a saída esperada.
- [ ] Suíte com `231 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/08-xp-pontos`.

**Commit:** `feat(xp): XP para quem envia e para quem recebe a transferência`
**Pare se:**
- O item 4 não terminar com `9 failed`.
- `docker compose up -d --build --wait` falhar com `ImportError` ou `circular import` no `docker compose logs --tail 100 api`: traga a saída.
- Um teste receber 500 (`QIT000500`) ou 503 (`QIT000503`): rode `docker compose logs --tail 100 api` e traga a saída.
- Um teste da fase 6 (`tests/integration/transactions/`) ficar vermelho.
- A X1 der outra saída depois de 3 tentativas de conferir os arquivos do passo contra o plano.
- A suíte não terminar com `231 passed`.

---

### Passo 8.6 — Aplicar e zerar pontos
**Branch:** fase/08-xp-pontos · **Depende de:** 8.5
**Objetivo:** `GamificationController.apply_points(account_key, account_token, point_application_data)` e `reset_points(account_key, account_token)`; as rotas `POST /accounts/{account_key}/point_applications` (tokens: conta; schema `post_point_applications.json`) e `POST /accounts/{account_key}/point_resets` (tokens: conta; sem corpo): 200 com a gamificação atualizada; 404 `QIT001010`; 409 `QIT001011` (encerrada); 422 `QIT001027` (só na aplicação); 400 `QIT000001` (só na aplicação). Cada mudança grava `points_event`.
**Decisões:** GAM-06 — pontos livres · GAM-07 — redistribuir; cada mudança é um evento · GAM-21 — aplicar +Y e zerar tudo, sem chave · CLI-09 — bloqueada mexe em pontos · CLI-05 — encerrada só lê · MOV-05 — trava antes de ler os pontos · API-03 — schema fechado · R8 — outro dono → 404 · TST-01 — black box e TDD
**Arquivos:**
- `src/controllers/gamification_controller.py` (editar): o conteúdo inteiro passa a ser o abaixo. Muda em relação ao 8.3: os imports de `errors` e de `models` (`AccountStatus`, `PointsEvent`) e os métodos `apply_points` e `reset_points`, entre `get_gamification` e `award_transfer_xp`.

```python
from datetime import date

from calculations import XpGain, gain_record_xp, gain_transfer_xp, record_whole_reais
from controllers.base_controller import BaseController
from dtos import GamificationDTO
from errors import AccountNotActive, NotEnoughFreePoints
from models import Account, AccountStatus, PointsEvent, Transaction, XpEvent
from repositories import AccountRepository, GamificationRepository


class GamificationController(BaseController):
    """XP, nível e pontos da conta (GAM-01, GAM-02, DAD-14).

    award_transfer_xp e award_record_xp não são rotas: outros controllers
    os chamam (a transferência, no passo 8.5; guardar e a virada do dia,
    na fase 7), dentro da transação deles. Quem chama já travou a conta e
    faz o commit; os dois não fazem commit.
    """

    def __init__(self) -> None:
        super().__init__(__name__)
        self.account_repository = AccountRepository(self.context)
        self.gamification_repository = GamificationRepository(self.context)

    def get_gamification(self, account_key: str, account_token: str) -> dict:
        """A gamificação da conta, só para o dono; também bloqueada ou encerrada (API-14, CLI-05). Não grava nada.

        1. a conta é do dono do token (404 QIT001010, R8).
        """
        account = self.get_owned_account(account_key, account_token)

        return GamificationDTO.obj_to_dict(account)

    def apply_points(self, account_key: str, account_token: str, point_application_data: dict) -> dict:
        """Aplicar +Y: tira Y pontos dos livres e põe num benefício (GAM-06, GAM-07, GAM-21). As regras, nesta ordem:

        1. a conta é do dono do token (404 QIT001010, R8);
        2. trava a conta (MOV-05): os pontos são relidos depois da trava, e
           uma transferência ao mesmo tempo, que pode subir o nível, espera
           ou é esperada;
        3. a conta não está CLOSED (409 QIT001011); bloqueada aplica (CLI-09);
        4. os pontos pedidos cabem nos pontos livres (422 QIT001027).

        Depois: os pontos saem dos livres e entram em points_fee (FEE) ou
        em points_chance (CHANCE), e o evento APPLY com o benefício e os
        pontos. A resposta é a gamificação atualizada.
        """
        account = self.get_owned_account(account_key, account_token)
        account = self.account_repository.lock_accounts([account])[0]

        if account.status.enumerator == AccountStatus.CLOSED:
            raise AccountNotActive(account_key, account.status.enumerator)

        benefit = point_application_data["benefit"]
        points = point_application_data["points"]

        if points > account.points_free:
            raise NotEnoughFreePoints(points, account.points_free)

        points_fee = account.points_fee
        points_chance = account.points_chance

        if benefit == PointsEvent.FEE:
            points_fee = points_fee + points
        else:
            points_chance = points_chance + points

        self.gamification_repository.update_points(account, account.points_free - points, points_fee, points_chance)
        self.gamification_repository.create_points_event(account, PointsEvent.APPLY, points, benefit)

        gamification_dto = GamificationDTO.obj_to_dict(account)
        self.session.commit()

        return gamification_dto

    def reset_points(self, account_key: str, account_token: str) -> dict:
        """Zerar tudo: os pontos em tarifa e em chance voltam a livres (GAM-07, GAM-21). As regras, nesta ordem:

        1. a conta é do dono do token (404 QIT001010, R8);
        2. trava a conta (MOV-05);
        3. a conta não está CLOSED (409 QIT001011); bloqueada zera (CLI-09).

        Depois: points_fee e points_chance vão a 0, os livres somam os dois,
        e o evento RESET com quantos pontos voltaram (0 quando nada estava
        aplicado: zerar de novo deixa os pontos como estão). A resposta é a
        gamificação atualizada.
        """
        account = self.get_owned_account(account_key, account_token)
        account = self.account_repository.lock_accounts([account])[0]

        if account.status.enumerator == AccountStatus.CLOSED:
            raise AccountNotActive(account_key, account.status.enumerator)

        returned_points = account.points_fee + account.points_chance

        self.gamification_repository.update_points(account, account.points_free + returned_points, 0, 0)
        self.gamification_repository.create_points_event(account, PointsEvent.RESET, returned_points)

        gamification_dto = GamificationDTO.obj_to_dict(account)
        self.session.commit()

        return gamification_dto

    def award_transfer_xp(
        self,
        account: Account,
        amount_cents: int,
        source: str,
        transaction: Transaction,
        accounting_date: date,
    ) -> XpGain:
        """Dá à conta o XP de uma transferência de amount_cents, com o n dela (GAM-16, GAM-17, GAM-18, GAM-24).

        `source`: XpEvent.TRANSFER_SENT ou XpEvent.TRANSFER_RECEIVED.
        Devolve o XpGain da conta.
        """
        xp_gain = gain_transfer_xp(account.level, account.xp, amount_cents)
        self._apply_xp_gain(account, xp_gain, source, transaction, accounting_date)

        return xp_gain

    def award_record_xp(self, account: Account, transaction: Transaction, accounting_date: date) -> XpGain:
        """Dá à conta o XP do novo recorde do cofrinho, se o saldo dele passou do recorde (GAM-04, GAM-25).

        1. o saldo do cofrinho passou do recorde (piggy_record): se não
           passou, nada muda e a resposta é None (tirar e pôr de volta não
           dá XP);
        2. o recorde passa a ser o saldo novo, em centavos;
        3. o XP é n por real inteiro que o saldo passou do recorde: os
           centavos viram XP quando completam um real.

        Quem chama (fase 7: guardar e a virada do dia) já gravou o saldo
        novo do cofrinho na mesma sessão. `transaction` é None no XP da
        virada.
        """
        piggy_bank = self.account_repository.get_piggy_bank(account)

        if piggy_bank.balance <= account.piggy_record:
            return None

        whole_reais = record_whole_reais(piggy_bank.balance, account.piggy_record)
        self.gamification_repository.update_piggy_record(account, piggy_bank.balance)

        xp_gain = gain_record_xp(account.level, account.xp, whole_reais)
        self._apply_xp_gain(account, xp_gain, XpEvent.PIGGY_RECORD, transaction, accounting_date)

        return xp_gain

    def _apply_xp_gain(self, account: Account, xp_gain: XpGain, source: str, transaction: Transaction, accounting_date: date) -> None:
        """Grava o ganho: um level_event por nível novo, o xp_event e os valores novos da conta (DAD-14).

        Ganho de 0 XP não grava nada. Cada nível novo soma 1 ponto livre
        (GAM-06).
        """
        if xp_gain.xp_gained == 0:
            return

        for level in range(account.level + 1, xp_gain.level + 1):
            self.gamification_repository.create_level_event(account, level, accounting_date)

        self.gamification_repository.create_xp_event(account, source, xp_gain.xp_gained, accounting_date, transaction)
        self.gamification_repository.update_progress(account, xp_gain.level, xp_gain.xp, account.points_free + xp_gain.levels_gained)
```

- `src/resources/gamification.py` (editar): o conteúdo inteiro passa a ser:

```python
from fastapi import Request
from fastapi import status as http_status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from constants import ACCOUNT_TOKEN_HEADER
from controllers import GamificationController
from utils.schema_handler import SchemaHandler


class GamificationResource:
    """A porta HTTP da gamificação: consultar, aplicar pontos e zerar pontos.

    Sem regra de negócio, sem SQL e sem nada guardado no self (ARQ-02). O
    token da conta chega no cabeçalho ACCOUNT-TOKEN (API-16); quem o
    confere é o controller.
    """

    def on_get(self, account_key: str, request: Request) -> JSONResponse:
        controller = GamificationController()
        gamification = controller.get_gamification(account_key, request.headers.get(ACCOUNT_TOKEN_HEADER))

        return JSONResponse(
            content=jsonable_encoder(gamification),
            status_code=http_status.HTTP_200_OK,
        )

    @SchemaHandler.validate("post_point_applications.json")
    def on_post_point_application(self, account_key: str, payload: dict, request: Request) -> JSONResponse:
        controller = GamificationController()
        gamification = controller.apply_points(account_key, request.headers.get(ACCOUNT_TOKEN_HEADER), payload)

        return JSONResponse(
            content=jsonable_encoder(gamification),
            status_code=http_status.HTTP_200_OK,
        )

    def on_post_point_reset(self, account_key: str, request: Request) -> JSONResponse:
        controller = GamificationController()
        gamification = controller.reset_points(account_key, request.headers.get(ACCOUNT_TOKEN_HEADER))

        return JSONResponse(
            content=jsonable_encoder(gamification),
            status_code=http_status.HTTP_200_OK,
        )
```

- `src/app.py` (editar): uma troca, e nada mais. A linha
  ```python
      application.add_api_route("/accounts/{account_key}/gamification", gamification_resource.on_get, methods=["GET"])
  ```
  vira as três linhas
  ```python
      application.add_api_route("/accounts/{account_key}/gamification", gamification_resource.on_get, methods=["GET"])
      application.add_api_route("/accounts/{account_key}/point_applications", gamification_resource.on_post_point_application, methods=["POST"])
      application.add_api_route("/accounts/{account_key}/point_resets", gamification_resource.on_post_point_reset, methods=["POST"])
  ```
  O trecho `# Gamificação` fica exatamente assim:
  ```python
      # Gamificação
      application.add_api_route("/accounts/{account_key}/gamification", gamification_resource.on_get, methods=["GET"])
      application.add_api_route("/accounts/{account_key}/point_applications", gamification_resource.on_post_point_application, methods=["POST"])
      application.add_api_route("/accounts/{account_key}/point_resets", gamification_resource.on_post_point_reset, methods=["POST"])
  ```

- `tests/integration/gamification/test_points.py` (criar): o conteúdo inteiro é:

```python
"""Pontos: POST /accounts/{account_key}/point_applications e /point_resets (GAM-06, GAM-07, GAM-21, CLI-09, R8).

Cada nível dá 1 ponto livre. "Aplicar +Y" tira Y pontos dos livres e põe
no benefício FEE (tarifa menor) ou CHANCE (chance de não debitar);
faltou ponto livre → 422 QIT001027. "Zerar" devolve todos os pontos aos
livres. Conta bloqueada aplica e zera; encerrada → 409 QIT001011. A
resposta é a gamificação já atualizada. Os testes que erram o token
começam com DbUtils.rollback() (PRD-10).
"""

from tests.utils import DbUtils, ObjectGenerator, PayloadGenerator, RequestGenerator


# GAM-24: R$ 4.000,00 dão o nível 1; R$ 17.000,00 passam do nível 2 (1 ponto por nível).
LEVEL_ONE_AMOUNT = 400000
LEVEL_TWO_AMOUNT = 1700000


def create_account_with_levels(amount: int) -> dict:
    """Uma conta que recebeu uma transferência de `amount`: sobe de nível e fica com saldo `amount`."""
    sender = ObjectGenerator.create_funded_account(amount + amount // 100)
    receiver = ObjectGenerator.create_account()

    payload = PayloadGenerator.transfer(receiver["account_key"], amount=amount)
    status, response = RequestGenerator.POST_transfer(sender["account_key"], sender["account_token"], payload)
    assert status == 201, response

    return receiver


def gamification_of(account: dict) -> dict:
    status, response = RequestGenerator.GET_gamification(account["account_key"], account["account_token"])
    assert status == 200, response

    return response


def points_of(gamification: dict) -> tuple:
    """(livres, em tarifa, em chance, tarifa, chance)."""
    return (
        gamification["points_free"],
        gamification["points_fee"],
        gamification["points_chance"],
        gamification["fee_percent"],
        gamification["chance_percent"],
    )


def apply_points(account: dict, benefit: str, points: int) -> tuple:
    payload = PayloadGenerator.point_application(benefit=benefit, points=points)

    return RequestGenerator.POST_point_application(account["account_key"], account["account_token"], payload)


def reset_points(account: dict) -> tuple:
    return RequestGenerator.POST_point_reset(account["account_key"], account["account_token"])


def assert_points(status: int, response: dict, account: dict, expected: tuple) -> None:
    """200, os pontos esperados na resposta e a resposta igual à leitura de GET .../gamification."""
    assert status == 200, response
    assert points_of(response) == expected
    assert response == gamification_of(account)


class TestPoints:
    def test_applies_points_to_fee(self):
        account = create_account_with_levels(LEVEL_ONE_AMOUNT)

        status, response = apply_points(account, "FEE", 1)

        assert status == 200, response
        assert response == {
            "level": 1,
            "xp": 0,
            "xp_to_next_level": 4000,
            "points_free": 0,
            "points_fee": 1,
            "points_chance": 0,
            "fee_percent": "0.9",
            "chance_percent": "0",
            "rank": "DEFAULT",
            "cdi_percent": "100",
            "piggy_record": 0,
            "grace_until": None,
        }
        assert response == gamification_of(account)

    def test_applies_points_to_chance(self):
        account = create_account_with_levels(LEVEL_ONE_AMOUNT)

        status, response = apply_points(account, "CHANCE", 1)

        assert_points(status, response, account, (0, 0, 1, "1", "0.1"))

    def test_refuses_more_than_free_points(self):
        account = create_account_with_levels(LEVEL_ONE_AMOUNT)
        account_without_points = ObjectGenerator.create_account()

        for target, points in [(account, 2), (account_without_points, 1)]:
            status, response = apply_points(target, "FEE", points)

            assert status == 422, (points, response)
            assert response["code"] == "QIT001027"

        assert points_of(gamification_of(account)) == (1, 0, 0, "1", "0")
        assert points_of(gamification_of(account_without_points)) == (0, 0, 0, "1", "0")

        status, response = apply_points(account, "FEE", 1)
        assert_points(status, response, account, (0, 1, 0, "0.9", "0"))

    def test_applies_in_steps_and_resets(self):
        account = create_account_with_levels(LEVEL_TWO_AMOUNT)
        assert points_of(gamification_of(account)) == (2, 0, 0, "1", "0")

        status, response = apply_points(account, "FEE", 1)
        assert_points(status, response, account, (1, 1, 0, "0.9", "0"))

        status, response = apply_points(account, "CHANCE", 1)
        assert_points(status, response, account, (0, 1, 1, "0.9", "0.1"))

        status, response = apply_points(account, "FEE", 1)
        assert status == 422, response
        assert response["code"] == "QIT001027"

        for _repeat in range(2):
            status, response = reset_points(account)
            assert_points(status, response, account, (2, 0, 0, "1", "0"))

        status, response = apply_points(account, "FEE", 2)
        assert_points(status, response, account, (0, 2, 0, "0.8", "0"))

    def test_blocked_account_manages_points(self):
        account = create_account_with_levels(LEVEL_ONE_AMOUNT)

        status, response = RequestGenerator.POST_block(account["account_key"], PayloadGenerator.block())
        assert status == 204, response

        status, response = apply_points(account, "FEE", 1)
        assert_points(status, response, account, (0, 1, 0, "0.9", "0"))

        status, response = reset_points(account)
        assert_points(status, response, account, (1, 0, 0, "1", "0"))

    def test_closed_account_is_409(self):
        account = create_account_with_levels(LEVEL_ONE_AMOUNT)

        withdrawal = PayloadGenerator.withdrawal(amount=LEVEL_ONE_AMOUNT)
        status, response = RequestGenerator.POST_withdrawal(account["account_key"], account["account_token"], withdrawal)
        assert status == 201, response

        status, response = RequestGenerator.DELETE_account(account["account_key"], account["account_token"])
        assert status == 204, response

        for status, response in [apply_points(account, "FEE", 1), reset_points(account)]:
            assert status == 409, response
            assert response["code"] == "QIT001011"

        assert points_of(gamification_of(account)) == (1, 0, 0, "1", "0")

    def test_refuses_body_out_of_schema(self):
        account = create_account_with_levels(LEVEL_ONE_AMOUNT)
        bodies = [
            {"benefit": "fee", "points": 1},
            {"benefit": "OTHER", "points": 1},
            {"benefit": "FEE", "points": 0},
            {"benefit": "FEE", "points": -1},
            {"benefit": "FEE", "points": 1.5},
            {"benefit": "FEE", "points": 1.0},
            {"benefit": "FEE", "points": "1"},
            {"benefit": "FEE", "points": True},
            {"benefit": "FEE"},
            {"points": 1},
            {"benefit": "FEE", "points": 1, "extra": 1},
            {},
        ]

        for body in bodies:
            status, response = RequestGenerator.POST_point_application(account["account_key"], account["account_token"], body)

            assert status == 400, (body, response)
            assert response["code"] == "QIT000001"

        assert points_of(gamification_of(account)) == (1, 0, 0, "1", "0")

    def test_other_account_token_is_404(self):
        DbUtils.rollback()
        account = create_account_with_levels(LEVEL_ONE_AMOUNT)
        other_account = ObjectGenerator.create_account()

        payload = PayloadGenerator.point_application(benefit="FEE", points=1)
        status, response = RequestGenerator.POST_point_application(account["account_key"], other_account["account_token"], payload)
        assert status == 404, response
        assert response["code"] == "QIT001010"

        status, response = RequestGenerator.POST_point_reset(account["account_key"], other_account["account_token"])
        assert status == 404, response
        assert response["code"] == "QIT001010"

        status, response = apply_points(account, "FEE", 1)
        assert_points(status, response, account, (0, 1, 0, "0.9", "0"))

    def test_missing_or_wrong_token_is_404(self):
        DbUtils.rollback()
        account = create_account_with_levels(LEVEL_ONE_AMOUNT)
        payload = PayloadGenerator.point_application(benefit="FEE", points=1)

        for account_token in [None, "token_errado"]:
            status, response = RequestGenerator.POST_point_application(account["account_key"], account_token, payload)
            assert status == 404, (account_token, response)
            assert response["code"] == "QIT001010"

            status, response = RequestGenerator.POST_point_reset(account["account_key"], account_token)
            assert status == 404, (account_token, response)
            assert response["code"] == "QIT001010"

        assert points_of(gamification_of(account)) == (1, 0, 0, "1", "0")
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/08-xp-pontos`; `git log --oneline` mostra `feat(xp): XP para quem envia e para quem recebe a transferência`.
2. Crie `tests/integration/gamification/test_points.py` com o conteúdo do campo **Arquivos**.
3. `docker compose up -d --build --wait`.
4. `./.venv/Scripts/python.exe -m pytest -v tests/integration/gamification/test_points.py` → a última linha tem `9 failed` e não tem `passed`. Os 9 falham por asserção: hoje os caminhos `/accounts/{account_key}/point_applications` e `/point_resets` respondem 404 `QIT000404`.
5. Edite `src/controllers/gamification_controller.py` com o conteúdo do campo **Arquivos**.
6. Edite `src/resources/gamification.py` com o conteúdo do campo **Arquivos**.
7. Faça a troca em `src/app.py` e confira o trecho `# Gamificação`.
8. `docker compose up -d --build --wait`.
9. `./.venv/Scripts/python.exe -m pytest -v tests/integration/gamification/test_points.py` → a última linha tem `9 passed`.
10. Rode as conferências S3 e P1 do **Verificar**.
11. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `240 passed`.
12. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
13. Feche o passo (AGENTS.md, seção 7), um comando por vez:
    ```
    git add -- src/controllers/gamification_controller.py src/resources/gamification.py src/app.py tests/integration/gamification/test_points.py
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "feat(pontos): aplicar e zerar pontos"
    git log -1 --format=%B
    ```

**Testes:** `tests/integration/gamification/test_points.py`. "Pontos" = (livres, em tarifa, em chance, `fee_percent`, `chance_percent`). Conta no nível 1 = recebeu 400000 (1 ponto livre); no nível 2 = recebeu 1700000 (2 pontos livres). Efeito no banco de cada 200: as colunas `points_free`, `points_fee` e `points_chance` da conta e uma linha em `points_event` (conferência P1); as recusas não gravam nada além da linha de `request_log`.

| Função de teste | Entrada | Esperado |
|---|---|---|
| `test_applies_points_to_fee` | conta no nível 1; aplicar `FEE` 1 | 200 e exatamente o corpo de `docs/rotas.md` com nível 1, XP 0, faltam 4000, pontos (0, 1, 0, `"0.9"`, `"0"`), `DEFAULT`, `"100"`, recorde 0, carência nula; a leitura de `GET .../gamification` é igual (API-14, GAM-09) |
| `test_applies_points_to_chance` | conta no nível 1; aplicar `CHANCE` 1 | 200 com pontos (0, 0, 1, `"1"`, `"0.1"`) (GAM-10) |
| `test_refuses_more_than_free_points` | conta no nível 1, aplicar 2; conta nova, aplicar 1; depois a primeira aplica 1 | 422 `QIT001027` nos dois, pontos iguais a antes; depois 200 com (0, 1, 0, `"0.9"`, `"0"`) (GAM-21) |
| `test_applies_in_steps_and_resets` | conta no nível 2; `FEE` 1; `CHANCE` 1; `FEE` 1; zerar duas vezes; `FEE` 2 | (1, 1, 0); (0, 1, 1, `"0.9"`, `"0.1"`); 422 `QIT001027`; (2, 0, 0, `"1"`, `"0"`) nas duas vezes; (0, 2, 0, `"0.8"`, `"0"`) (GAM-07) |
| `test_blocked_account_manages_points` | conta no nível 1 bloqueada; aplicar `FEE` 1; zerar | 200 com (0, 1, 0); 200 com (1, 0, 0) (CLI-09) |
| `test_closed_account_is_409` | conta no nível 1; saque de tudo; encerrar; aplicar; zerar | 409 `QIT001011` nos dois; a leitura continua com (1, 0, 0) (CLI-05) |
| `test_refuses_body_out_of_schema` | `benefit` `fee` e `OTHER`; `points` 0, −1, 1.5, 1.0, `"1"`, `true`; sem `points`; sem `benefit`; campo `extra`; `{}` | 400 `QIT000001` nos 12; pontos iguais a antes (API-03) |
| `test_other_account_token_is_404` | começa com `DbUtils.rollback()`; aplicar e zerar na conta A com o token de B; depois aplicar com o de A | 404 `QIT001010` nos dois; 200 com (0, 1, 0) (R8) |
| `test_missing_or_wrong_token_is_404` | começa com `DbUtils.rollback()`; aplicar e zerar sem `ACCOUNT-TOKEN` e com `token_errado` | 404 `QIT001010` nos quatro; pontos iguais a antes |

**Verificar:**
- `./.venv/Scripts/python.exe -m pytest -v tests/integration/gamification/test_points.py` → `9 passed`.
- S3 (um comando, numa linha só):
  ```
  docker compose exec -T api python -c "from controllers import GamificationController; from resources import GamificationResource; print(sorted(n for n in vars(GamificationController) if not n.startswith('_'))); print(sorted(n for n in vars(GamificationResource) if not n.startswith('_')))"
  ```
  → exatamente:
  ```
  ['apply_points', 'award_record_xp', 'award_transfer_xp', 'get_gamification', 'reset_points']
  ['on_get', 'on_post_point_application', 'on_post_point_reset']
  ```
- P1 — os eventos dos pontos (GAM-07, DAD-14). Um comando, numa linha só:
  ```
  ./.venv/Scripts/python.exe -c "from sqlalchemy import create_engine, text; from tests.utils import DbUtils, ObjectGenerator, PayloadGenerator, RequestGenerator; a = ObjectGenerator.create_funded_account(1717000); b = ObjectGenerator.create_account(); s, r = RequestGenerator.POST_transfer(a['account_key'], a['account_token'], PayloadGenerator.transfer(b['account_key'], amount=1700000)); k = (b['account_key'], b['account_token']); x = [RequestGenerator.POST_point_application(*k, PayloadGenerator.point_application('FEE', 1))[0], RequestGenerator.POST_point_application(*k, PayloadGenerator.point_application('CHANCE', 1))[0], RequestGenerator.POST_point_reset(*k)[0], RequestGenerator.POST_point_reset(*k)[0]]; print(s, x); c = create_engine(DbUtils.database_url()).connect(); print(c.execute(text('SELECT e.action, e.benefit, e.points, length(e.points_event_key) FROM points_event e JOIN account m ON m.id = e.account_id WHERE m.account_key = :k ORDER BY e.id'), {'k': b['account_key']}).fetchall()); print(c.execute(text('SELECT points_free, points_fee, points_chance FROM account WHERE account_key = :k'), {'k': b['account_key']}).fetchall())"
  ```
  → exatamente:
  ```
  201 [200, 200, 200, 200]
  [('APPLY', 'FEE', 1, 36), ('APPLY', 'CHANCE', 1, 36), ('RESET', None, 2, 36), ('RESET', None, 0, 36)]
  [(2, 0, 0)]
  ```
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `240 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/app.py
  src/controllers/gamification_controller.py
  src/resources/gamification.py
  tests/integration/gamification/test_points.py
  ```
- `git log -1 --format=%B` → `feat(pontos): aplicar e zerar pontos`

**Pronto quando:**
- [ ] Os 9 testes falharam antes do código (item 4) e passam depois (item 9).
- [ ] S3 e P1 dão a saída esperada.
- [ ] Suíte com `240 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/08-xp-pontos`.

**Commit:** `feat(pontos): aplicar e zerar pontos`
**Pare se:**
- O item 4 não terminar com `9 failed`.
- Um teste receber 500 (`QIT000500`): rode `docker compose logs --tail 100 api` e traga a saída.
- `test_blocked_account_manages_points` receber 409: a conta bloqueada foi barrada (CLI-09).
- A P1 der outra saída depois de 3 tentativas de conferir os arquivos do passo contra o plano.
- A suíte não terminar com `240 passed`.

---

### Passo 8.7 — Tarifa menor com pontos
**Branch:** fase/08-xp-pontos · **Depende de:** 8.6
**Objetivo:** `TransactionController.transfer` calcula a tarifa com `calculate_fee(amount, account.points_fee)`, com os pontos da origem relidos depois da trava; com 10 pontos em tarifa, a tarifa é 0 e a transferência não tem lançamento `FEE`.
**Decisões:** GAM-09 — ponto em tarifa · MOV-10 — tarifa zero sem lançamento · MOV-02 — valor + tarifa · MOV-06 — 1% sem pontos · DAD-16 — tarifa como lançamento · MOV-05 — trava antes de ler · TST-01 — black box e TDD
**Arquivos:**
- `src/controllers/transaction_controller.py` (editar): duas trocas no método `transfer`, e nada mais.
  1. As três linhas da docstring
     ```python
             8. o saldo da origem cobre valor + tarifa (422 QIT001015, MOV-01,
                MOV-02); a tarifa é calculate_fee(valor, 0): os pontos entram
                no passo 8.7;
     ```
     viram as três linhas
     ```python
             8. o saldo da origem cobre valor + tarifa (422 QIT001015, MOV-01,
                MOV-02); a tarifa é calculate_fee(valor, pontos em tarifa da
                origem), com os pontos relidos depois da trava (GAM-09);
     ```
  2. A linha
     ```python
             fee = calculate_fee(amount, 0)
     ```
     vira
     ```python
             fee = calculate_fee(amount, account.points_fee)
     ```
  O método `transfer` fica exatamente assim:

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

        Depois: a operação TRANSFER e os lançamentos, nesta ordem: AMOUNT
        −valor e FEE −tarifa na origem; AMOUNT +valor no destino; FEE
        +tarifa na conta BANK. Tarifa zero não gera lançamento (MOV-10). Em
        seguida, o XP do valor para a origem (TRANSFER_SENT) e para o
        destino (TRANSFER_RECEIVED), cada um com o seu n (GAM-16, GAM-17),
        na mesma transação: o pedido repetido devolve a resposta da
        primeira vez e não dá XP de novo. A resposta traz a key e o saldo
        novo da origem (API-10).
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

- `tests/integration/gamification/test_fee_with_points.py` (criar): o conteúdo inteiro é:

```python
"""Tarifa menor com pontos: POST /accounts/{account_key}/transfers (GAM-09, MOV-02, MOV-10, DAD-16).

Cada ponto em tarifa tira 0,1 p.p. do 1% (arredondado para cima ao
centavo); ponto em chance não muda a tarifa; com os 10 pontos em tarifa,
a tarifa é 0% e a transferência não tem lançamento FEE. O saldo precisa
cobrir valor + a tarifa já reduzida.
"""

from tests.utils import ObjectGenerator, PayloadGenerator, RequestGenerator


# GAM-24: R$ 4.000,00 dão o nível 1; R$ 17.000,00, o nível 2; R$ 830.000,00, o nível 10.
LEVEL_ONE_AMOUNT = 400000
LEVEL_TWO_AMOUNT = 1700000
LEVEL_TEN_AMOUNT = 83000000


def create_account_with_levels(amount: int) -> dict:
    """Uma conta que recebeu uma transferência de `amount`: sobe de nível e fica com saldo `amount`."""
    sender = ObjectGenerator.create_funded_account(amount + amount // 100)
    receiver = ObjectGenerator.create_account()

    payload = PayloadGenerator.transfer(receiver["account_key"], amount=amount)
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


def transfer(origin: dict, destination: dict, amount: int) -> tuple:
    payload = PayloadGenerator.transfer(destination["account_key"], amount=amount)

    return RequestGenerator.POST_transfer(origin["account_key"], origin["account_token"], payload)


def fee_paid(origin: dict, destination: dict, amount: int) -> int:
    """Transfere `amount` e devolve a tarifa que a origem pagou, conferida pelo saldo e pelos lançamentos da operação."""
    balance_before = balance_of(origin)

    status, response = transfer(origin, destination, amount)
    assert status == 201, response

    status, operation = RequestGenerator.GET_transaction(origin["account_key"], origin["account_token"], response["transaction_key"])
    assert status == 200, operation

    fee = balance_before - amount - response["balance"]
    entries = [(entry["entry_type"], entry["amount"]) for entry in operation["entries"]]

    if fee == 0:
        assert entries == [("AMOUNT", -amount)], entries
    else:
        assert entries == [("AMOUNT", -amount), ("FEE", -fee)], entries

    return fee


class TestFeeWithPoints:
    def test_each_fee_point_lowers_the_fee(self):
        account = create_account_with_levels(LEVEL_ONE_AMOUNT)
        destination = ObjectGenerator.create_account()

        gamification = apply_points(account, "FEE", 1)
        assert gamification["fee_percent"] == "0.9"

        assert fee_paid(account, destination, 10000) == 90
        assert fee_paid(account, destination, 1234) == 12
        assert balance_of(destination) == 10000 + 1234

    def test_only_fee_points_lower_the_fee(self):
        account = create_account_with_levels(LEVEL_TWO_AMOUNT)
        destination = ObjectGenerator.create_account()

        apply_points(account, "FEE", 1)
        assert fee_paid(account, destination, 10000) == 90

        status, response = RequestGenerator.POST_point_reset(account["account_key"], account["account_token"])
        assert status == 200, response
        assert fee_paid(account, destination, 10000) == 100

        apply_points(account, "CHANCE", 2)
        assert fee_paid(account, destination, 10000) == 100

    def test_ten_fee_points_make_the_fee_zero_without_entry(self):
        account = create_account_with_levels(LEVEL_TEN_AMOUNT)
        destination = ObjectGenerator.create_account()

        gamification = apply_points(account, "FEE", 10)
        assert (gamification["points_free"], gamification["points_fee"], gamification["fee_percent"]) == (0, 10, "0")

        assert fee_paid(account, destination, 10000) == 0
        assert balance_of(account) == LEVEL_TEN_AMOUNT - 10000
        assert balance_of(destination) == 10000

    def test_balance_must_cover_amount_plus_reduced_fee(self):
        account = create_account_with_levels(LEVEL_ONE_AMOUNT)
        destination = ObjectGenerator.create_account()
        apply_points(account, "FEE", 1)

        withdrawal = PayloadGenerator.withdrawal(amount=LEVEL_ONE_AMOUNT - 10089)
        status, response = RequestGenerator.POST_withdrawal(account["account_key"], account["account_token"], withdrawal)
        assert status == 201, response

        status, response = transfer(account, destination, 10000)
        assert status == 422, response
        assert response["code"] == "QIT001015"

        status, response = RequestGenerator.POST_deposit(account["account_key"], PayloadGenerator.deposit(amount=1))
        assert status == 201, response

        status, response = transfer(account, destination, 10000)
        assert status == 201, response
        assert response["balance"] == 0
        assert balance_of(destination) == 10000
```

**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/08-xp-pontos`; `git log --oneline` mostra `feat(pontos): aplicar e zerar pontos`.
2. Crie `tests/integration/gamification/test_fee_with_points.py` com o conteúdo do campo **Arquivos**.
3. `docker compose up -d --build --wait`.
4. `./.venv/Scripts/python.exe -m pytest -v tests/integration/gamification/test_fee_with_points.py` → a última linha tem `4 failed` e não tem `passed`. Os 4 falham por asserção: hoje a tarifa é sempre 1%, com ou sem pontos (100 onde o teste espera 90 ou 0; 422 onde a tarifa reduzida caberia no saldo).
5. Faça as duas trocas em `src/controllers/transaction_controller.py` e confira o método `transfer` contra o do campo **Arquivos**.
6. `docker compose up -d --build --wait`.
7. `./.venv/Scripts/python.exe -m pytest -v tests/integration/gamification/test_fee_with_points.py` → a última linha tem `4 passed`.
8. Rode a conferência F1 do **Verificar**.
9. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `244 passed`.
10. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
11. Feche o passo (AGENTS.md, seção 7), um comando por vez:
    ```
    git add -- src/controllers/transaction_controller.py tests/integration/gamification/test_fee_with_points.py
    git diff --cached --name-only
    git diff --name-only
    git ls-files --others --exclude-standard
    git commit -m "feat(tarifa): pontos em tarifa reduzem a tarifa da transferência"
    git log -1 --format=%B
    ```

**Testes:** `tests/integration/gamification/test_fee_with_points.py`. A ajudante `fee_paid` transfere, mede a tarifa pelo saldo (antes − valor − saldo da resposta) e confere os lançamentos da operação na origem por `GET .../transactions/{transaction_key}`: `AMOUNT` e `FEE`, ou só `AMOUNT` quando a tarifa é 0. Efeito no banco de cada 201: o da fase 6, com o `FEE` −tarifa reduzida na origem e +tarifa na `BANK`; sem nenhum `FEE` quando a tarifa é 0 (conferência F1).

| Função de teste | Entrada | Esperado |
|---|---|---|
| `test_each_fee_point_lowers_the_fee` | conta no nível 1 com 1 ponto em `FEE`; transferências de 10000 e de 1234 | `fee_percent` `"0.9"`; tarifas 90 e 12 (teto de 11,106), com o lançamento `FEE` de cada uma; o destino recebe 11234 (GAM-09, MOV-10) |
| `test_only_fee_points_lower_the_fee` | conta no nível 2; `FEE` 1 e 10000; zerar e 10000; `CHANCE` 2 e 10000 | tarifas 90, 100 e 100 (ponto em chance não muda a tarifa) |
| `test_ten_fee_points_make_the_fee_zero_without_entry` | conta no nível 10; `FEE` 10; transferência de 10000 | pontos (0 livres, 10 em tarifa) e `fee_percent` `"0"`; tarifa 0 e só o lançamento `AMOUNT` −10000 na operação; saldos 82990000 e 10000 (MOV-10) |
| `test_balance_must_cover_amount_plus_reduced_fee` | conta no nível 1 com 1 ponto em `FEE`; saque que deixa 10089; 10000; depósito de 1; 10000 | 422 `QIT001015` (faltou 1 centavo para 10000 + 90); depois 201 com `balance` 0 e destino com 10000 (MOV-02) |

**Verificar:**
- `./.venv/Scripts/python.exe -m pytest -v tests/integration/gamification/test_fee_with_points.py` → `4 passed`.
- `git grep -n "calculate_fee(amount, 0)" -- src` → nenhuma linha.
- `git grep -c "calculate_fee(amount, account.points_fee)" -- src/controllers/transaction_controller.py` → `src/controllers/transaction_controller.py:1`
- F1 — transferência com tarifa 0 (MOV-10, DAD-16). Um comando, numa linha só:
  ```
  ./.venv/Scripts/python.exe -c "from sqlalchemy import create_engine, text; from tests.utils import DbUtils, ObjectGenerator, PayloadGenerator, RequestGenerator; a = ObjectGenerator.create_funded_account(83830000); b = ObjectGenerator.create_account(); s1 = RequestGenerator.POST_transfer(a['account_key'], a['account_token'], PayloadGenerator.transfer(b['account_key'], amount=83000000))[0]; s2 = RequestGenerator.POST_point_application(b['account_key'], b['account_token'], PayloadGenerator.point_application('FEE', 10))[0]; s3, r = RequestGenerator.POST_transfer(b['account_key'], b['account_token'], PayloadGenerator.transfer(a['account_key'], amount=10000)); print(s1, s2, s3, r['balance']); c = create_engine(DbUtils.database_url()).connect(); print(c.execute(text('SELECT t.enumerator, w.enumerator, e.amount FROM entry e JOIN transaction x ON x.id = e.transaction_id JOIN account m ON m.id = e.account_id JOIN account_type t ON t.id = m.account_type_id JOIN entry_type w ON w.id = e.entry_type_id WHERE x.transaction_key = :t ORDER BY e.id'), {'t': r['transaction_key']}).fetchall())"
  ```
  → exatamente (dois lançamentos, nenhum `FEE`, nem na conta `BANK`):
  ```
  201 200 201 82990000
  [('CUSTOMER', 'AMOUNT', -10000), ('CUSTOMER', 'AMOUNT', 10000)]
  ```
- `./.venv/Scripts/python.exe -m pytest` → a última linha tem `244 passed` e não tem `failed`, `error` nem `skipped`.
- `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
- `git diff --cached --name-only` (antes do commit) → exatamente:
  ```
  src/controllers/transaction_controller.py
  tests/integration/gamification/test_fee_with_points.py
  ```
- `git log -1 --format=%B` → `feat(tarifa): pontos em tarifa reduzem a tarifa da transferência`

**Pronto quando:**
- [ ] Os 4 testes falharam antes do código (item 4) e passam depois (item 7).
- [ ] O método `transfer` é o do campo **Arquivos**; os dois `git grep` dão o esperado.
- [ ] A F1 dá as 2 linhas esperadas.
- [ ] Suíte com `244 passed`; lint sem saída.
- [ ] Commit local com a mensagem exata na `fase/08-xp-pontos`.

**Commit:** `feat(tarifa): pontos em tarifa reduzem a tarifa da transferência`
**Pare se:**
- O item 4 não terminar com `4 failed`.
- As três linhas da docstring ou a linha `        fee = calculate_fee(amount, 0)` não forem encontradas iguais.
- Um teste da fase 6 (`tests/integration/transactions/`) ou `tests/unit/test_fee.py` ficar vermelho.
- A F1 der outra saída depois de 3 tentativas de conferir os arquivos do passo contra o plano.
- A suíte não terminar com `244 passed`.

---

### Passo 8.fim — Fechar a fase
**Branch:** fase/08-xp-pontos · **Depende de:** 8.1 a 8.7
**Objetivo:** provar a fase com o banco recriado do zero e levá-la para a `main` com a tag `fase-08`.
**Decisões:** TIM-04 — git por fase · TIM-08 — git automático · ARQ-03 — SQL só com o banco vazio · ARQ-04 — sobe sem `.env` · TST-01 — suíte inteira verde
**Arquivos:** nenhum. O passo não cria, não edita e não apaga arquivo.
**Passo a passo:**
1. Começo do passo (AGENTS.md, seção 7): `git status --short` → saída vazia; `git branch --show-current` → `fase/08-xp-pontos`.
2. `git log --oneline -n 8` → tem as 7 mensagens dos passos 8.1 a 8.7, cada uma uma vez:
   ```
   feat(xp): XP e nível com teste unitário
   feat(gamificacao): repository e DTO da gamificação
   feat(gamificacao): controller do XP de transferência e de recorde
   feat(gamificacao): rota de consulta da gamificação
   feat(xp): XP para quem envia e para quem recebe a transferência
   feat(pontos): aplicar e zerar pontos
   feat(tarifa): pontos em tarifa reduzem a tarifa da transferência
   ```
3. Recrie o banco do zero e suba tudo, um comando por vez:
   ```
   docker compose down -v
   docker compose up -d --build --wait
   ```
4. Rode a conferência X1 (passo 8.5) → as 4 linhas do **Verificar** do passo 8.5.
5. Rode a conferência F1 (passo 8.7) → as 2 linhas do **Verificar** do passo 8.7.
6. `./.venv/Scripts/python.exe -m pytest` → a última linha tem `244 passed`.
7. `./.venv/Scripts/python.exe -m pytest` de novo → a última linha tem `244 passed` (nada intermitente).
8. `./.venv/Scripts/python.exe -m flake8 src tests` → nenhuma linha.
9. `git status --short` → saída vazia.
10. Leve a fase para a `main`, um comando por vez:
    ```
    git switch main
    git merge --no-ff --no-edit -m "feat(gamificacao): fase 08 com XP, nível, pontos e tarifa menor" fase/08-xp-pontos
    git tag fase-08
    ```
11. Rode o **Verificar**.

**Testes:** nenhum teste novo. A suíte inteira (150 de integração + 94 unitários) roda duas vezes com o banco recriado do zero (itens 6 e 7).
**Verificar:**
- O `git status --short` antes do merge não mostra alterações.
- `git branch --show-current` → `main`.
- `git log -1 --format=%B` → `feat(gamificacao): fase 08 com XP, nível, pontos e tarifa menor`.
- `git log -1 --format=%P` → dois hashes separados por um espaço (é um merge).
- `git tag --list fase-08` → `fase-08`.
- `git status --short` → saída vazia.

**Pronto quando:**
- [ ] X1 e F1 dão o esperado com o banco recriado do zero.
- [ ] Suíte com `244 passed`, duas vezes seguidas; lint sem saída.
- [ ] Merge `--no-ff` na `main` com a mensagem exata; tag `fase-08` criada localmente; merge local na `main`.

**Commit:** nenhum commit de passo. Mensagem do merge: `feat(gamificacao): fase 08 com XP, nível, pontos e tarifa menor`
**Pare se:**
- Faltar uma das 7 mensagens do item 2.
- `docker compose up -d --build --wait` falhar: rode `docker compose logs --tail 100 db` e `docker compose logs --tail 100 api` e traga as duas saídas.
- X1 ou F1 derem outra saída.
- A suíte não terminar com `244 passed` nas duas rodadas, ou o lint imprimir qualquer linha.
- O merge local der conflito (AGENTS.md, seção 8, item 9).

---

## Divergências encontradas

Seção para o Bruno; o agente não executa nada daqui.

| # | Onde | O que foi feito |
|---|---|---|
| 1 | GAM-24 ("o resto do valor rende com o n novo") e GAM-18 ("XP inteiro, truncado") não dizem onde truncar quando a operação cruza um nível. | A parte do valor que completa o nível é calculada exata (`Fraction`), o resto segue com o n novo, e o XP é truncado uma vez, no fim. Assim nenhuma fração se perde ao subir (GAM-05). O único número aproximado é o `log10`, em `Decimal` com 50 dígitos. |
| 2 | GAM-16 é sobre XP, não dinheiro; R6 proíbe float em dinheiro. | `xp.py` não usa float em lugar nenhum; os percentuais da resposta (`fee_percent`, `chance_percent`, `cdi_percent`) são texto, como manda `docs/rotas.md`. |
| 3 | `cdi_percent` (API-14): o ranque atual ou o que rende hoje (GAM-19)? | O do ranque atual (`rank`), confirmado pelo Bruno em 08/10. Na fase 8 os dois são sempre `DEFAULT`. |
| 4 | O `ranks.py`, com `RANK_CDI_PERCENT`, só nasce no 7.1, depois desta fase. | O DTO tem a constante nova `CDI_PERCENT_BY_RANK`, em texto (COF-02). O plano da fase 7 deve fazer o 7.1 reaproveitá-la ou trocar o DTO para ler do `ranks.py`, para os números não ficarem em dois lugares. |
| 5 | DAD-14 e ARQ-02: quem escreve as colunas da gamificação na conta. | O repository, por três nomes novos: `update_progress`, `update_points`, `update_piggy_record`. O controller só decide os valores. |
| 6 | "Cada mudança é um evento" (GAM-07); zerar sem nada aplicado. | Zerar sempre grava o `RESET`, com quantos pontos voltaram (0 quando nada estava aplicado). Ganho de 0 XP (transferência abaixo de R$ 4,00 no nível 0) não grava `xp_event`. |
| 7 | `award_record_xp` (GAM-04, GAM-25) nasce aqui, mas a primeira rota que o usa é o guardar (7.5). | Provado nesta fase pela conferência R3 (8.3). Os testes black box e os dois lados de cada `if` dele entram nos passos 7.5 e 7.13. O recorde sobe sempre que o saldo passa dele, mesmo quando os centavos ainda não completam um real (0 XP). |
| 8 | PLANO-00, 8.3/8.5: um controller chama outro (`TransactionController` → `GamificationController`). | `TransactionController` cria o `GamificationController` no `__init__`; os dois usam a mesma sessão (o contexto é da requisição). `award_*` não fazem commit: quem chama faz. |
| 9 | `docs/rotas.md`: aplicar e zerar dão 409 `QIT001011` com a conta "encerrada"; CLI-09 libera pontos na bloqueada. | O controller barra só `CLOSED`; bloqueada aplica e zera. A consulta da gamificação lê em qualquer estado (CLI-05). |
| 10 | PLANO-fase-06, divergência 6: o lado black box da tarifa zero ficou para cá. | `test_fee_with_points.py::test_ten_fee_points_make_the_fee_zero_without_entry` e a conferência F1. |
| 11 | Os testes precisam de contas em nível alto. | Uma transferência grande sobe os dois lados de nível (R$ 830.000,00 = nível 10); não há valor máximo (MOV-08) e cada teste usa contas próprias. |
| 12 | GAM-23 (prêmio do sorteio sem XP) entra no 9.8. | Nesta fase toda transferência com 201 dá XP aos dois lados. A fase 9 mantém o XP normal do valor transferido para os dois lados (GAM-16); apenas o lançamento `PRIZE` nunca dá XP adicional (GAM-23). |

## Nomes novos da fase 08 (registrar no PLANO-00)

Seção para o Bruno; o agente não executa nada daqui.

| Onde | Nomes |
|---|---|
| `src/calculations/xp.py` | constantes `LEVEL_COST_FACTOR`, `TRANSFER_XP_CENTS_DIVISOR`, `LOG_ARGUMENT_FACTOR`, `CENTS_PER_REAL`, `LOG_PRECISION`; privados `_transfer_xp_per_cent`, `_record_xp_per_real`, `_gain`; `XpGain` é `NamedTuple` |
| `GamificationRepository` | assinaturas `create_xp_event(account, source, xp, accounting_date, transaction=None)`, `create_level_event(account, level, accounting_date)`, `create_points_event(account, action, points, benefit=None)`, `create_rank_event(account, rank_enumerator, kind, accounting_date)`; novos `update_progress(account, level, xp, points_free)`, `update_points(account, points_free, points_fee, points_chance)`, `update_piggy_record(account, piggy_record)` |
| `GamificationDTO` | `obj_to_dict(account)`, `percent_text(tenths_of_percent)`; constantes `CDI_PERCENT_BY_RANK`, `TENTHS_PER_PERCENT` |
| `GamificationController` | `get_gamification(account_key, account_token)`; `award_transfer_xp` e `award_record_xp` devolvem `XpGain` (`award_record_xp` devolve `None` quando o saldo não passa do recorde; `transaction` aceita `None`); `apply_points(account_key, account_token, point_application_data)`; `reset_points(account_key, account_token)`; privado `_apply_xp_gain` |
| `TransactionController` | atributo `gamification_controller` |
| `GamificationResource` | `on_get(account_key, request)`, `on_post_point_application(account_key, payload, request)`, `on_post_point_reset(account_key, request)` |
| Testes | pasta `tests/integration/gamification/`; ajudantes locais `gamification_of`, `progress_of`, `points_of`, `send`, `create_level_one_account`, `create_account_with_levels`, `apply_points`, `reset_points`, `assert_points`, `fee_paid`; constantes `LEVEL_ONE_AMOUNT = 400000`, `LEVEL_TWO_AMOUNT = 1700000`, `LEVEL_TEN_AMOUNT = 83000000` |
| Comportamento | o XP da transferência entra depois dos lançamentos e antes do commit, dentro do `try` do `IntegrityError`; a fase 7 chama `award_record_xp(account, transaction, accounting_date)` com a conta de cliente travada e o saldo novo do cofrinho já escrito na sessão |
