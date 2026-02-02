"""
Router de conteúdos gerados (quiz, resumo, flashcards).
"""
import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import check_rate_limit, get_current_professor
from app.database import get_db
from app.models import ConteudoGerado, StatusConteudo, User
from app.schemas.conteudo import (
    AprovarConteudoRequest,
    ConteudoListResponse,
    ConteudoResponse,
    GerarFlashcardsRequest,
    GerarQuizRequest,
    GerarResumoRequest,
    RegenerarConteudoRequest,
    RejeitarConteudoRequest,
)
from app.services.gerador import GeradorError, GeradorService, get_gerador_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/conteudos", tags=["Conteúdos"])


def _adicionar_watermark(conteudo: ConteudoGerado, professor: User) -> ConteudoResponse:
    """Adiciona watermark ao conteúdo para resposta."""
    response = ConteudoResponse.model_validate(conteudo)
    if conteudo.status == StatusConteudo.APROVADO:
        response.watermark = f"Gerado por IA | Revisado por Prof. {professor.nome}"
    return response


@router.post(
    "/gerar/quiz",
    response_model=ConteudoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Gerar quiz",
)
async def gerar_quiz(
    data: GerarQuizRequest,
    professor: Annotated[User, Depends(get_current_professor)],
    db: Annotated[Session, Depends(get_db)],
) -> ConteudoResponse:
    """
    Gera um quiz baseado nos materiais do professor.

    - **topico**: Tópico do quiz
    - **disciplina**: Disciplina dos materiais fonte
    - **num_questoes**: Número de questões (1-20)
    - **dificuldade**: facil, medio ou dificil
    - **material_ids**: Lista opcional de IDs de materiais específicos

    O quiz é criado com status AGUARDANDO_APROVACAO.
    """
    check_rate_limit(professor)

    try:
        gerador = get_gerador_service(db)
        conteudo = await gerador.gerar_quiz(
            professor=professor,
            topico=data.topico,
            disciplina=data.disciplina,
            num_questoes=data.num_questoes,
            dificuldade=data.dificuldade,
            material_ids=data.material_ids,
        )
        return _adicionar_watermark(conteudo, professor)

    except GeradorError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/gerar/resumo",
    response_model=ConteudoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Gerar resumo",
)
async def gerar_resumo(
    data: GerarResumoRequest,
    professor: Annotated[User, Depends(get_current_professor)],
    db: Annotated[Session, Depends(get_db)],
) -> ConteudoResponse:
    """
    Gera um resumo baseado nos materiais do professor.

    - **topico**: Tópico do resumo
    - **disciplina**: Disciplina dos materiais fonte
    - **tamanho**: curto, medio ou longo
    - **material_ids**: Lista opcional de IDs de materiais específicos

    O resumo é criado com status AGUARDANDO_APROVACAO.
    """
    check_rate_limit(professor)

    try:
        gerador = get_gerador_service(db)
        conteudo = await gerador.gerar_resumo(
            professor=professor,
            topico=data.topico,
            disciplina=data.disciplina,
            tamanho=data.tamanho,
            material_ids=data.material_ids,
        )
        return _adicionar_watermark(conteudo, professor)

    except GeradorError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/gerar/flashcards",
    response_model=ConteudoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Gerar flashcards",
)
async def gerar_flashcards(
    data: GerarFlashcardsRequest,
    professor: Annotated[User, Depends(get_current_professor)],
    db: Annotated[Session, Depends(get_db)],
) -> ConteudoResponse:
    """
    Gera flashcards baseados nos materiais do professor.

    - **topico**: Tópico dos flashcards
    - **disciplina**: Disciplina dos materiais fonte
    - **num_cards**: Número de flashcards (1-50)
    - **material_ids**: Lista opcional de IDs de materiais específicos

    Os flashcards são criados com status AGUARDANDO_APROVACAO.
    """
    check_rate_limit(professor)

    try:
        gerador = get_gerador_service(db)
        conteudo = await gerador.gerar_flashcards(
            professor=professor,
            topico=data.topico,
            disciplina=data.disciplina,
            num_cards=data.num_cards,
            material_ids=data.material_ids,
        )
        return _adicionar_watermark(conteudo, professor)

    except GeradorError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/pendentes",
    response_model=ConteudoListResponse,
    summary="Listar conteúdos pendentes",
)
async def listar_pendentes(
    professor: Annotated[User, Depends(get_current_professor)],
    db: Annotated[Session, Depends(get_db)],
) -> ConteudoListResponse:
    """
    Lista conteúdos aguardando aprovação do professor.
    """
    conteudos = db.query(ConteudoGerado).filter(
        ConteudoGerado.professor_id == professor.id,
        ConteudoGerado.status == StatusConteudo.AGUARDANDO_APROVACAO,
    ).order_by(ConteudoGerado.criado_em.desc()).all()

    return ConteudoListResponse(
        conteudos=[_adicionar_watermark(c, professor) for c in conteudos],
        total=len(conteudos),
    )


@router.get(
    "/aprovados",
    response_model=ConteudoListResponse,
    summary="Listar conteúdos aprovados",
)
async def listar_aprovados(
    professor: Annotated[User, Depends(get_current_professor)],
    db: Annotated[Session, Depends(get_db)],
    disciplina: str | None = None,
) -> ConteudoListResponse:
    """
    Lista conteúdos aprovados do professor.

    - **disciplina**: Filtro opcional por disciplina
    """
    query = db.query(ConteudoGerado).filter(
        ConteudoGerado.professor_id == professor.id,
        ConteudoGerado.status == StatusConteudo.APROVADO,
    )

    if disciplina:
        query = query.filter(ConteudoGerado.disciplina == disciplina)

    conteudos = query.order_by(ConteudoGerado.aprovado_em.desc()).all()

    return ConteudoListResponse(
        conteudos=[_adicionar_watermark(c, professor) for c in conteudos],
        total=len(conteudos),
    )


@router.get(
    "/{conteudo_id}",
    response_model=ConteudoResponse,
    summary="Obter conteúdo",
)
async def obter_conteudo(
    conteudo_id: uuid.UUID,
    professor: Annotated[User, Depends(get_current_professor)],
    db: Annotated[Session, Depends(get_db)],
) -> ConteudoResponse:
    """
    Retorna detalhes de um conteúdo específico.

    Apenas o professor dono do conteúdo pode acessá-lo.
    """
    conteudo = db.query(ConteudoGerado).filter(
        ConteudoGerado.id == conteudo_id,
        ConteudoGerado.professor_id == professor.id,
    ).first()

    if not conteudo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conteúdo não encontrado",
        )

    return _adicionar_watermark(conteudo, professor)


@router.put(
    "/{conteudo_id}/aprovar",
    response_model=ConteudoResponse,
    summary="Aprovar conteúdo",
)
async def aprovar_conteudo(
    conteudo_id: uuid.UUID,
    data: AprovarConteudoRequest,
    professor: Annotated[User, Depends(get_current_professor)],
    db: Annotated[Session, Depends(get_db)],
) -> ConteudoResponse:
    """
    Aprova um conteúdo gerado.

    - **modificacoes**: Modificações opcionais a aplicar

    Após aprovação, o conteúdo fica disponível para alunos.
    """
    try:
        gerador = get_gerador_service(db)
        conteudo = gerador.aprovar_conteudo(
            conteudo_id=conteudo_id,
            professor=professor,
            modificacoes=data.modificacoes,
        )
        return _adicionar_watermark(conteudo, professor)

    except GeradorError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.put(
    "/{conteudo_id}/rejeitar",
    response_model=ConteudoResponse,
    summary="Rejeitar conteúdo",
)
async def rejeitar_conteudo(
    conteudo_id: uuid.UUID,
    data: RejeitarConteudoRequest,
    professor: Annotated[User, Depends(get_current_professor)],
    db: Annotated[Session, Depends(get_db)],
) -> ConteudoResponse:
    """
    Rejeita um conteúdo gerado.

    - **motivo**: Motivo da rejeição (mínimo 10 caracteres)
    """
    try:
        gerador = get_gerador_service(db)
        conteudo = gerador.rejeitar_conteudo(
            conteudo_id=conteudo_id,
            professor=professor,
            motivo=data.motivo,
        )
        return _adicionar_watermark(conteudo, professor)

    except GeradorError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/{conteudo_id}/regerar",
    response_model=ConteudoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Regenerar conteúdo",
)
async def regenerar_conteudo(
    conteudo_id: uuid.UUID,
    data: RegenerarConteudoRequest,
    professor: Annotated[User, Depends(get_current_professor)],
    db: Annotated[Session, Depends(get_db)],
) -> ConteudoResponse:
    """
    Regenera um conteúdo com ajustes solicitados.

    - **ajustes**: Descrição dos ajustes desejados

    Cria um novo conteúdo com status AGUARDANDO_APROVACAO.
    """
    check_rate_limit(professor)

    try:
        gerador = get_gerador_service(db)
        conteudo = await gerador.regenerar_conteudo(
            conteudo_id=conteudo_id,
            professor=professor,
            ajustes=data.ajustes,
        )
        return _adicionar_watermark(conteudo, professor)

    except GeradorError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete(
    "/{conteudo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover conteúdo",
)
async def remover_conteudo(
    conteudo_id: uuid.UUID,
    professor: Annotated[User, Depends(get_current_professor)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """
    Remove um conteúdo gerado.

    Apenas o professor dono do conteúdo pode removê-lo.
    """
    conteudo = db.query(ConteudoGerado).filter(
        ConteudoGerado.id == conteudo_id,
        ConteudoGerado.professor_id == professor.id,
    ).first()

    if not conteudo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conteúdo não encontrado",
        )

    db.delete(conteudo)
    db.commit()

    logger.info(f"Conteúdo removido: {conteudo_id}")
