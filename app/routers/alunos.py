"""
Router de funcionalidades para alunos.
"""
import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import distinct, func
from sqlalchemy.orm import Session

from app.auth.dependencies import check_rate_limit, get_current_aluno
from app.database import get_db
from app.models import (
    ConteudoGerado,
    StatusConteudo,
    TentativaAluno,
    TipoConteudo,
    User,
)
from app.schemas.conteudo import (
    BuscaSemanticaRequest,
    BuscaSemanticaResponse,
    ConteudoResponse,
    DisciplinaResponse,
    DisciplinasListResponse,
    ResponderQuizRequest,
    TentativaListResponse,
    TentativaResponse,
)
from app.services.vectorstore import VectorStoreService, get_vectorstore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/aluno", tags=["Aluno"])


def _adicionar_watermark_aluno(conteudo: ConteudoGerado) -> ConteudoResponse:
    """Adiciona watermark ao conteúdo para resposta de aluno."""
    response = ConteudoResponse.model_validate(conteudo)
    if conteudo.professor:
        response.watermark = f"Gerado por IA | Revisado por Prof. {conteudo.professor.nome}"
    return response


@router.get(
    "/disciplinas",
    response_model=DisciplinasListResponse,
    summary="Listar disciplinas",
)
async def listar_disciplinas(
    aluno: Annotated[User, Depends(get_current_aluno)],
    db: Annotated[Session, Depends(get_db)],
) -> DisciplinasListResponse:
    """
    Lista disciplinas com conteúdo aprovado disponível.
    """
    # Busca disciplinas com conteúdo aprovado
    resultados = db.query(
        ConteudoGerado.disciplina,
        func.count(ConteudoGerado.id).label("num_conteudos"),
    ).filter(
        ConteudoGerado.status == StatusConteudo.APROVADO,
    ).group_by(
        ConteudoGerado.disciplina,
    ).all()

    disciplinas = [
        DisciplinaResponse(nome=r.disciplina, num_conteudos=r.num_conteudos)
        for r in resultados
    ]

    return DisciplinasListResponse(disciplinas=disciplinas)


@router.get(
    "/materiais/{disciplina}",
    response_model=list[ConteudoResponse],
    summary="Listar conteúdos da disciplina",
)
async def listar_conteudos_disciplina(
    disciplina: str,
    aluno: Annotated[User, Depends(get_current_aluno)],
    db: Annotated[Session, Depends(get_db)],
    tipo: str | None = None,
) -> list[ConteudoResponse]:
    """
    Lista conteúdos aprovados de uma disciplina.

    - **disciplina**: Nome da disciplina
    - **tipo**: Filtro opcional por tipo (QUIZ, RESUMO, FLASHCARD)

    Apenas conteúdos com status APROVADO são retornados.
    """
    query = db.query(ConteudoGerado).filter(
        ConteudoGerado.disciplina == disciplina,
        ConteudoGerado.status == StatusConteudo.APROVADO,
    )

    if tipo:
        try:
            tipo_enum = TipoConteudo(tipo)
            query = query.filter(ConteudoGerado.tipo == tipo_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tipo inválido. Use: QUIZ, RESUMO ou FLASHCARD",
            )

    conteudos = query.order_by(ConteudoGerado.aprovado_em.desc()).all()

    return [_adicionar_watermark_aluno(c) for c in conteudos]


@router.get(
    "/quiz/{conteudo_id}",
    response_model=ConteudoResponse,
    summary="Obter quiz",
)
async def obter_quiz(
    conteudo_id: uuid.UUID,
    aluno: Annotated[User, Depends(get_current_aluno)],
    db: Annotated[Session, Depends(get_db)],
) -> ConteudoResponse:
    """
    Retorna um quiz aprovado para o aluno responder.

    As respostas corretas são removidas da resposta.
    """
    conteudo = db.query(ConteudoGerado).filter(
        ConteudoGerado.id == conteudo_id,
        ConteudoGerado.status == StatusConteudo.APROVADO,
        ConteudoGerado.tipo == TipoConteudo.QUIZ,
    ).first()

    if not conteudo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz não encontrado ou não aprovado",
        )

    # Remove respostas corretas para o aluno
    response = _adicionar_watermark_aluno(conteudo)
    if "questoes" in response.conteudo_json:
        questoes_sem_resposta = []
        for q in response.conteudo_json["questoes"]:
            questao_limpa = {
                "pergunta": q.get("pergunta"),
                "alternativas": q.get("alternativas"),
            }
            questoes_sem_resposta.append(questao_limpa)
        response.conteudo_json = {"questoes": questoes_sem_resposta}

    return response


@router.post(
    "/quiz/{conteudo_id}/responder",
    response_model=TentativaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Responder quiz",
)
async def responder_quiz(
    conteudo_id: uuid.UUID,
    data: ResponderQuizRequest,
    aluno: Annotated[User, Depends(get_current_aluno)],
    db: Annotated[Session, Depends(get_db)],
) -> TentativaResponse:
    """
    Submete respostas de um quiz.

    - **respostas**: Dicionário com índice da questão e alternativa escolhida
      Exemplo: {"0": "a", "1": "c", "2": "b"}

    Retorna pontuação e detalhes das respostas.
    """
    check_rate_limit(aluno)

    conteudo = db.query(ConteudoGerado).filter(
        ConteudoGerado.id == conteudo_id,
        ConteudoGerado.status == StatusConteudo.APROVADO,
        ConteudoGerado.tipo == TipoConteudo.QUIZ,
    ).first()

    if not conteudo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz não encontrado ou não aprovado",
        )

    # Calcula pontuação
    questoes = conteudo.conteudo_json.get("questoes", [])
    if not questoes:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Quiz sem questões válidas",
        )

    acertos = 0
    detalhes = []

    for idx, questao in enumerate(questoes):
        resposta_aluno = data.respostas.get(str(idx))
        resposta_correta = questao.get("resposta_correta")

        acertou = resposta_aluno and resposta_aluno.lower() == resposta_correta.lower()
        if acertou:
            acertos += 1

        detalhes.append({
            "questao_idx": idx,
            "resposta_aluno": resposta_aluno,
            "resposta_correta": resposta_correta,
            "acertou": acertou,
            "explicacao": questao.get("explicacao", ""),
        })

    pontuacao = (acertos / len(questoes)) * 100

    # Salva tentativa
    tentativa = TentativaAluno(
        aluno_id=aluno.id,
        conteudo_id=conteudo_id,
        respostas_json=data.respostas,
        pontuacao=pontuacao,
    )

    db.add(tentativa)
    db.commit()
    db.refresh(tentativa)

    logger.info(
        f"Aluno {aluno.id} respondeu quiz {conteudo_id}: {pontuacao:.1f}%"
    )

    response = TentativaResponse.model_validate(tentativa)
    response.detalhes = {
        "acertos": acertos,
        "total": len(questoes),
        "questoes": detalhes,
    }

    return response


@router.get(
    "/flashcards/{conteudo_id}",
    response_model=ConteudoResponse,
    summary="Obter flashcards",
)
async def obter_flashcards(
    conteudo_id: uuid.UUID,
    aluno: Annotated[User, Depends(get_current_aluno)],
    db: Annotated[Session, Depends(get_db)],
) -> ConteudoResponse:
    """
    Retorna flashcards aprovados para estudo.
    """
    conteudo = db.query(ConteudoGerado).filter(
        ConteudoGerado.id == conteudo_id,
        ConteudoGerado.status == StatusConteudo.APROVADO,
        ConteudoGerado.tipo == TipoConteudo.FLASHCARD,
    ).first()

    if not conteudo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flashcards não encontrados ou não aprovados",
        )

    return _adicionar_watermark_aluno(conteudo)


@router.get(
    "/resumo/{conteudo_id}",
    response_model=ConteudoResponse,
    summary="Obter resumo",
)
async def obter_resumo(
    conteudo_id: uuid.UUID,
    aluno: Annotated[User, Depends(get_current_aluno)],
    db: Annotated[Session, Depends(get_db)],
) -> ConteudoResponse:
    """
    Retorna resumo aprovado para estudo.
    """
    conteudo = db.query(ConteudoGerado).filter(
        ConteudoGerado.id == conteudo_id,
        ConteudoGerado.status == StatusConteudo.APROVADO,
        ConteudoGerado.tipo == TipoConteudo.RESUMO,
    ).first()

    if not conteudo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resumo não encontrado ou não aprovado",
        )

    return _adicionar_watermark_aluno(conteudo)


@router.post(
    "/buscar",
    response_model=BuscaSemanticaResponse,
    summary="Busca semântica",
)
async def buscar_semantica(
    data: BuscaSemanticaRequest,
    aluno: Annotated[User, Depends(get_current_aluno)],
    db: Annotated[Session, Depends(get_db)],
    vectorstore: Annotated[VectorStoreService, Depends(get_vectorstore)],
) -> BuscaSemanticaResponse:
    """
    Realiza busca semântica nos materiais da disciplina.

    - **disciplina**: Disciplina para buscar
    - **pergunta**: Pergunta ou termo de busca

    Retorna trechos relevantes dos materiais aprovados.
    """
    check_rate_limit(aluno)

    # Busca professores com conteúdo aprovado na disciplina
    professores_ids = db.query(distinct(ConteudoGerado.professor_id)).filter(
        ConteudoGerado.disciplina == data.disciplina,
        ConteudoGerado.status == StatusConteudo.APROVADO,
    ).all()

    if not professores_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Nenhum conteúdo encontrado para a disciplina '{data.disciplina}'",
        )

    # Busca em cada professor
    todos_trechos = []
    for (professor_id,) in professores_ids:
        try:
            documentos = vectorstore.buscar_similares(
                query=data.pergunta,
                professor_id=professor_id,
                k=5,
                disciplina=data.disciplina,
            )
            todos_trechos.extend(documentos)
        except Exception as e:
            logger.warning(f"Erro ao buscar para professor {professor_id}: {e}")
            continue

    # Ordena por score e limita
    todos_trechos.sort(key=lambda x: x.get("score", 0), reverse=True)
    trechos_limitados = todos_trechos[:10]

    # Formata resposta
    trechos_formatados = [
        {
            "texto": t["texto"],
            "titulo": t["metadata"].get("titulo", ""),
            "relevancia": round(t.get("score", 0) * 100, 1),
        }
        for t in trechos_limitados
    ]

    return BuscaSemanticaResponse(
        trechos=trechos_formatados,
        pergunta=data.pergunta,
        disciplina=data.disciplina,
    )


@router.get(
    "/historico",
    response_model=TentativaListResponse,
    summary="Histórico de tentativas",
)
async def obter_historico(
    aluno: Annotated[User, Depends(get_current_aluno)],
    db: Annotated[Session, Depends(get_db)],
    limite: int = 50,
) -> TentativaListResponse:
    """
    Retorna histórico de tentativas do aluno.

    - **limite**: Número máximo de tentativas a retornar (default: 50)
    """
    tentativas = db.query(TentativaAluno).filter(
        TentativaAluno.aluno_id == aluno.id,
    ).order_by(
        TentativaAluno.created_at.desc()
    ).limit(limite).all()

    return TentativaListResponse(
        tentativas=[TentativaResponse.model_validate(t) for t in tentativas],
        total=len(tentativas),
    )


@router.get(
    "/tentativa/{tentativa_id}",
    response_model=TentativaResponse,
    summary="Detalhes da tentativa",
)
async def obter_tentativa(
    tentativa_id: uuid.UUID,
    aluno: Annotated[User, Depends(get_current_aluno)],
    db: Annotated[Session, Depends(get_db)],
) -> TentativaResponse:
    """
    Retorna detalhes de uma tentativa específica.
    """
    tentativa = db.query(TentativaAluno).filter(
        TentativaAluno.id == tentativa_id,
        TentativaAluno.aluno_id == aluno.id,
    ).first()

    if not tentativa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tentativa não encontrada",
        )

    # Busca conteúdo para montar detalhes
    conteudo = db.query(ConteudoGerado).filter(
        ConteudoGerado.id == tentativa.conteudo_id,
    ).first()

    response = TentativaResponse.model_validate(tentativa)

    if conteudo and conteudo.tipo == TipoConteudo.QUIZ:
        questoes = conteudo.conteudo_json.get("questoes", [])
        detalhes = []

        for idx, questao in enumerate(questoes):
            resposta_aluno = tentativa.respostas_json.get(str(idx))
            resposta_correta = questao.get("resposta_correta")

            detalhes.append({
                "questao_idx": idx,
                "pergunta": questao.get("pergunta"),
                "resposta_aluno": resposta_aluno,
                "resposta_correta": resposta_correta,
                "acertou": resposta_aluno and resposta_aluno.lower() == resposta_correta.lower(),
                "explicacao": questao.get("explicacao", ""),
            })

        response.detalhes = {
            "topico": conteudo.topico,
            "disciplina": conteudo.disciplina,
            "questoes": detalhes,
        }

    return response
