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
