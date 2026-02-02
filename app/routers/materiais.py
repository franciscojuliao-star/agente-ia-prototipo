"""
Router de materiais didáticos.
"""
import logging
import os
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.auth.dependencies import check_rate_limit, get_current_professor
from app.config import get_settings
from app.database import get_db
from app.models import Material, TipoMaterial, User
from app.schemas.material import (
    LinkUpload,
    MaterialListResponse,
    MaterialResponse,
    TextoUpload,
    VideoUpload,
)
from app.services.processamento import (
    ProcessamentoError,
    dividir_em_chunks,
    extrair_texto_pdf,
    extrair_texto_url,
    extrair_transcricao_youtube,
)
from app.services.vectorstore import VectorStoreService, VectorStoreError, get_vectorstore

settings = get_settings()
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/materiais", tags=["Materiais"])


@router.post(
    "/upload/pdf",
    response_model=MaterialResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload de PDF",
)
async def upload_pdf(
    arquivo: Annotated[UploadFile, File(description="Arquivo PDF")],
    titulo: Annotated[str, Form(min_length=2, max_length=500)],
    disciplina: Annotated[str, Form(min_length=2, max_length=255)],
    professor: Annotated[User, Depends(get_current_professor)],
    db: Annotated[Session, Depends(get_db)],
    vectorstore: Annotated[VectorStoreService, Depends(get_vectorstore)],
) -> Material:
    """
    Faz upload de um arquivo PDF.

    - **arquivo**: Arquivo PDF (máximo 50MB)
    - **titulo**: Título do material
    - **disciplina**: Nome da disciplina

    O PDF será processado, dividido em chunks e indexado para busca semântica.
    """
    check_rate_limit(professor)

    # Valida arquivo
    if not arquivo.filename or not arquivo.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Arquivo deve ser um PDF",
        )

    # Verifica tamanho
    contents = await arquivo.read()
    if len(contents) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Arquivo excede o limite de {settings.max_upload_size_mb}MB",
        )

    try:
        # Extrai texto do PDF
        import io
        texto = extrair_texto_pdf(io.BytesIO(contents))

        # Divide em chunks
        chunks = dividir_em_chunks(texto)

        if not chunks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Não foi possível extrair texto do PDF",
            )

        # Salva arquivo (opcional - pode ser removido se não quiser persistir o arquivo)
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        file_id = uuid.uuid4()
        arquivo_path = f"{upload_dir}/{file_id}.pdf"

        with open(arquivo_path, "wb") as f:
            f.write(contents)

        # Cria registro no banco
        material = Material(
            professor_id=professor.id,
            disciplina=disciplina,
            titulo=titulo,
            tipo=TipoMaterial.PDF,
            conteudo_original=texto[:50000],  # Limita tamanho armazenado
            arquivo_path=arquivo_path,
            num_chunks=len(chunks),
        )

        db.add(material)
        db.commit()
        db.refresh(material)

        # Adiciona ao vector store
        vectorstore.adicionar_documentos(
            chunks=chunks,
            professor_id=professor.id,
            material_id=material.id,
            disciplina=disciplina,
            titulo=titulo,
        )

        logger.info(f"PDF processado: {material.id} com {len(chunks)} chunks")
        return material

    except ProcessamentoError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except VectorStoreError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao indexar documento: {str(e)}",
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Erro ao processar PDF: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao processar arquivo",
        )


@router.post(
    "/upload/video",
    response_model=MaterialResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload de vídeo do YouTube",
)
async def upload_video(
    data: VideoUpload,
    professor: Annotated[User, Depends(get_current_professor)],
    db: Annotated[Session, Depends(get_db)],
    vectorstore: Annotated[VectorStoreService, Depends(get_vectorstore)],
) -> Material:
    """
    Processa vídeo do YouTube extraindo transcrição.

    - **url**: URL do vídeo do YouTube
    - **titulo**: Título do material
    - **disciplina**: Nome da disciplina

    A transcrição será extraída automaticamente e indexada.
    """
    check_rate_limit(professor)

    try:
        # Extrai transcrição
        texto = extrair_transcricao_youtube(str(data.url))

        # Divide em chunks
        chunks = dividir_em_chunks(texto)

        if not chunks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Não foi possível extrair transcrição do vídeo",
            )

        # Cria registro no banco
        material = Material(
            professor_id=professor.id,
            disciplina=data.disciplina,
            titulo=data.titulo,
            tipo=TipoMaterial.VIDEO,
            conteudo_original=texto[:50000],
            url=str(data.url),
            num_chunks=len(chunks),
        )

        db.add(material)
        db.commit()
        db.refresh(material)

        # Adiciona ao vector store
        vectorstore.adicionar_documentos(
            chunks=chunks,
            professor_id=professor.id,
            material_id=material.id,
            disciplina=data.disciplina,
            titulo=data.titulo,
        )

        logger.info(f"Vídeo processado: {material.id} com {len(chunks)} chunks")
        return material

    except ProcessamentoError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except VectorStoreError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao indexar documento: {str(e)}",
        )


@router.post(
    "/upload/link",
    response_model=MaterialResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload de página web",
)
async def upload_link(
    data: LinkUpload,
    professor: Annotated[User, Depends(get_current_professor)],
    db: Annotated[Session, Depends(get_db)],
    vectorstore: Annotated[VectorStoreService, Depends(get_vectorstore)],
) -> Material:
    """
    Processa página web extraindo texto.

    - **url**: URL da página web
    - **titulo**: Título do material
    - **disciplina**: Nome da disciplina
    """
    check_rate_limit(professor)

    try:
        # Extrai texto da página
        texto = extrair_texto_url(str(data.url))

        # Divide em chunks
        chunks = dividir_em_chunks(texto)

        if not chunks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Não foi possível extrair texto da página",
            )

        # Cria registro no banco
        material = Material(
            professor_id=professor.id,
            disciplina=data.disciplina,
            titulo=data.titulo,
            tipo=TipoMaterial.LINK,
            conteudo_original=texto[:50000],
            url=str(data.url),
            num_chunks=len(chunks),
        )

        db.add(material)
        db.commit()
        db.refresh(material)

        # Adiciona ao vector store
        vectorstore.adicionar_documentos(
            chunks=chunks,
            professor_id=professor.id,
            material_id=material.id,
            disciplina=data.disciplina,
            titulo=data.titulo,
        )

        logger.info(f"Link processado: {material.id} com {len(chunks)} chunks")
        return material

    except ProcessamentoError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except VectorStoreError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao indexar documento: {str(e)}",
        )


@router.post(
    "/upload/texto",
    response_model=MaterialResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload de texto puro",
)
async def upload_texto(
    data: TextoUpload,
    professor: Annotated[User, Depends(get_current_professor)],
    db: Annotated[Session, Depends(get_db)],
    vectorstore: Annotated[VectorStoreService, Depends(get_vectorstore)],
) -> Material:
    """
    Processa texto puro enviado diretamente.

    - **texto**: Conteúdo textual
    - **titulo**: Título do material
    - **disciplina**: Nome da disciplina
    """
    check_rate_limit(professor)

    try:
        # Divide em chunks
        chunks = dividir_em_chunks(data.texto)

        if not chunks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Texto muito curto para processar",
            )

        # Cria registro no banco
        material = Material(
            professor_id=professor.id,
            disciplina=data.disciplina,
            titulo=data.titulo,
            tipo=TipoMaterial.TEXTO,
            conteudo_original=data.texto[:50000],
            num_chunks=len(chunks),
        )

        db.add(material)
        db.commit()
        db.refresh(material)

        # Adiciona ao vector store
        vectorstore.adicionar_documentos(
            chunks=chunks,
            professor_id=professor.id,
            material_id=material.id,
            disciplina=data.disciplina,
            titulo=data.titulo,
        )

        logger.info(f"Texto processado: {material.id} com {len(chunks)} chunks")
        return material

    except VectorStoreError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao indexar documento: {str(e)}",
        )


@router.get(
    "",
    response_model=MaterialListResponse,
    summary="Listar materiais",
)
async def listar_materiais(
    professor: Annotated[User, Depends(get_current_professor)],
    db: Annotated[Session, Depends(get_db)],
    disciplina: str | None = None,
) -> MaterialListResponse:
    """
    Lista materiais do professor autenticado.

    - **disciplina**: Filtro opcional por disciplina
    """
    query = db.query(Material).filter(Material.professor_id == professor.id)

    if disciplina:
        query = query.filter(Material.disciplina == disciplina)

    materiais = query.order_by(Material.created_at.desc()).all()

    return MaterialListResponse(
        materiais=[MaterialResponse.model_validate(m) for m in materiais],
        total=len(materiais),
    )


@router.get(
    "/{material_id}",
    response_model=MaterialResponse,
    summary="Obter material",
)
async def obter_material(
    material_id: uuid.UUID,
    professor: Annotated[User, Depends(get_current_professor)],
    db: Annotated[Session, Depends(get_db)],
) -> Material:
    """
    Retorna detalhes de um material específico.

    Apenas o professor dono do material pode acessá-lo.
    """
    material = db.query(Material).filter(
        Material.id == material_id,
        Material.professor_id == professor.id,
    ).first()

    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material não encontrado",
        )

    return material


@router.delete(
    "/{material_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover material",
)
async def remover_material(
    material_id: uuid.UUID,
    professor: Annotated[User, Depends(get_current_professor)],
    db: Annotated[Session, Depends(get_db)],
    vectorstore: Annotated[VectorStoreService, Depends(get_vectorstore)],
) -> None:
    """
    Remove um material e seus chunks do vector store.

    Apenas o professor dono do material pode removê-lo.
    """
    material = db.query(Material).filter(
        Material.id == material_id,
        Material.professor_id == professor.id,
    ).first()

    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material não encontrado",
        )

    try:
        # Remove do vector store
        vectorstore.remover_por_material_id(material_id)

        # Remove arquivo se existir
        if material.arquivo_path and os.path.exists(material.arquivo_path):
            os.remove(material.arquivo_path)

        # Remove do banco
        db.delete(material)
        db.commit()

        logger.info(f"Material removido: {material_id}")

    except VectorStoreError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao remover documento: {str(e)}",
        )
