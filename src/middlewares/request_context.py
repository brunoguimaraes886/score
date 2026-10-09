from fastapi import FastAPI, Request

from utils.request_context import REQUEST_ID_HEADER, build_request_id, set_request_id, start_request_state


def register_request_context_middleware(application: FastAPI) -> None:
    """Dá um nome próprio a cada requisição e abre o estado dela.

    É o middleware mais de fora, e não pula rota nenhuma: não existe
    requisição que não mereça um nome.

    • O identificador vai para o ContextVar que o logger lê: toda linha de
      log da mesma requisição sai com o mesmo nome.
    • O identificador volta no cabeçalho X-Request-ID da resposta: quem
      chamou pode citá-lo ao abrir um chamado.
    • O RequestState nasce aqui. As camadas de dentro o preenchem, e o
      middleware request_log_writer o grava em request_log (PRD-06).
    """

    @application.middleware("http")
    async def create_request_context(request: Request, call_next):
        request_id = build_request_id(request.headers.get(REQUEST_ID_HEADER))
        request.state.request_id = request_id
        set_request_id(request_id)
        start_request_state(request_id)

        response = await call_next(request)

        response.headers[REQUEST_ID_HEADER] = request_id

        return response
