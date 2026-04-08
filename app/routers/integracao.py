"""
Router de integração para sistemas externos (ex: Spring Boot).
Endpoints que aceitam conteúdo texto direto, sem necessidade de RAG.
Autenticação via API Key no header X-Api-Key.
"""
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.config import get_settings
from app.schemas.conteudo import (
    ConteudoHTMLResponse,
    GerarConteudoDiretoRequest,
    GerarQuizDiretoRequest,
    QuestaosDiretaResponse,
)
from app.services.llm import LLMError, get_llm_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/integracao", tags=["Integração"])


def verificar_api_key(x_api_key: Annotated[str | None, Header()] = None) -> None:
    """Valida a API key enviada no header X-Api-Key."""
    settings = get_settings()
    if x_api_key != settings.api_key_integracoes:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key inválida ou ausente",
        )


@router.post(
    "/gerar/quiz",
    response_model=list[QuestaosDiretaResponse],
    status_code=status.HTTP_200_OK,
    summary="Gerar quiz a partir de texto direto",
    description=(
        "Recebe o conteúdo textual já extraído (de aulas, PDFs, etc.) "
        "e retorna um array de questões de múltipla escolha. "
        "Não utiliza RAG — o contexto é enviado diretamente. "
        "Requer header **X-Api-Key**."
    ),
)
async def gerar_quiz_direto(
    data: GerarQuizDiretoRequest,
    _: Annotated[None, Depends(verificar_api_key)],
) -> list[QuestaosDiretaResponse]:
    llm = get_llm_service()
    try:
        questoes = await llm.gerar_quiz_direto(
            conteudo=data.conteudo,
            num_questoes=data.quantidade,
        )
        return [QuestaosDiretaResponse(**q) for q in questoes]
    except LLMError as e:
        logger.error(f"Erro ao gerar quiz direto: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )


@router.post(
    "/gerar/conteudo-html",
    response_model=ConteudoHTMLResponse,
    status_code=status.HTTP_200_OK,
    summary="Gerar conteúdo de aula em HTML a partir de texto direto",
    description=(
        "Recebe o conteúdo textual já extraído (de aulas, PDFs, etc.) "
        "e retorna HTML semântico formatado para exibição em aula. "
        "Não utiliza RAG — o contexto é enviado diretamente. "
        "Requer header **X-Api-Key**."
    ),
)
async def gerar_conteudo_html(
    data: GerarConteudoDiretoRequest,
    _: Annotated[None, Depends(verificar_api_key)],
) -> ConteudoHTMLResponse:
    llm = get_llm_service()
    try:
        html = await llm.gerar_conteudo_html(conteudo=data.conteudo)
        return ConteudoHTMLResponse(conteudo_html=html)
    except LLMError as e:
        logger.error(f"Erro ao gerar conteúdo HTML: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )
