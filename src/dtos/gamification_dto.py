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
