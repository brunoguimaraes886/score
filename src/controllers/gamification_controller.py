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
