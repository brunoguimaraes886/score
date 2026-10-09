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
