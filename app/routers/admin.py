"""
Router de administração de usuários.
"""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_admin
from app.database import get_db
from app.models import User, UserRole
from app.schemas.user import UserAdminResponse, UserStatusUpdate

router = APIRouter(prefix="/api/admin", tags=["Administração"])


@router.get(
    "/usuarios",
    response_model=list[UserAdminResponse],
    summary="Listar todos os usuários",
)
async def listar_usuarios(
    admin: Annotated[User, Depends(get_current_admin)],
    db: Annotated[Session, Depends(get_db)],
    ativo: bool | None = Query(None, description="Filtrar por status ativo"),
    role: str | None = Query(None, description="Filtrar por role (PROFESSOR, ALUNO)"),
) -> list[User]:
    """
    Lista todos os usuários do sistema.

    - **ativo**: Filtrar por usuários ativos (true) ou inativos (false)
    - **role**: Filtrar por tipo de usuário (PROFESSOR ou ALUNO)
    """
    query = db.query(User).filter(User.role != UserRole.ADMIN)

    if ativo is not None:
        query = query.filter(User.ativo == ativo)

    if role is not None:
        try:
            role_enum = UserRole(role.upper())
            query = query.filter(User.role == role_enum)
        except ValueError:
            pass  # Ignora role inválido

    return query.order_by(User.created_at.desc()).all()


@router.get(
    "/usuarios/pendentes",
    response_model=list[UserAdminResponse],
    summary="Listar usuários pendentes de aprovação",
)
async def listar_usuarios_pendentes(
    admin: Annotated[User, Depends(get_current_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> list[User]:
    """
    Lista todos os usuários que aguardam aprovação (ativo=false).
    """
    return (
        db.query(User)
        .filter(User.ativo == False, User.role != UserRole.ADMIN)
        .order_by(User.created_at.asc())
        .all()
    )


@router.patch(
    "/usuarios/{user_id}/status",
    response_model=UserAdminResponse,
    summary="Atualizar status do usuário",
)
async def atualizar_status_usuario(
    user_id: uuid.UUID,
    status_update: UserStatusUpdate,
    admin: Annotated[User, Depends(get_current_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """
    Ativa ou desativa um usuário.

    - **user_id**: ID do usuário
    - **ativo**: true para ativar, false para desativar
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado",
        )

    if user.role == UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Não é possível alterar status de administradores",
        )

    user.ativo = status_update.ativo
    db.commit()
    db.refresh(user)

    return user


@router.post(
    "/usuarios/{user_id}/aprovar",
    response_model=UserAdminResponse,
    summary="Aprovar usuário",
)
async def aprovar_usuario(
    user_id: uuid.UUID,
    admin: Annotated[User, Depends(get_current_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """
    Aprova um usuário pendente (ativa a conta).
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado",
        )

    if user.role == UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Não é possível alterar status de administradores",
        )

    if user.ativo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuário já está ativo",
        )

    user.ativo = True
    db.commit()
    db.refresh(user)

    return user


@router.delete(
    "/usuarios/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir usuário",
)
async def excluir_usuario(
    user_id: uuid.UUID,
    admin: Annotated[User, Depends(get_current_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """
    Exclui um usuário do sistema.

    ATENÇÃO: Esta ação é irreversível e remove todos os dados do usuário.
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado",
        )

    if user.role == UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Não é possível excluir administradores",
        )

    db.delete(user)
    db.commit()


@router.get(
    "/estatisticas",
    summary="Obter estatísticas de usuários",
)
async def obter_estatisticas(
    admin: Annotated[User, Depends(get_current_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """
    Retorna estatísticas gerais de usuários do sistema.
    """
    total_usuarios = db.query(User).filter(User.role != UserRole.ADMIN).count()
    usuarios_ativos = db.query(User).filter(
        User.ativo == True, User.role != UserRole.ADMIN
    ).count()
    usuarios_pendentes = db.query(User).filter(
        User.ativo == False, User.role != UserRole.ADMIN
    ).count()
    total_professores = db.query(User).filter(User.role == UserRole.PROFESSOR).count()
    total_alunos = db.query(User).filter(User.role == UserRole.ALUNO).count()

    return {
        "total_usuarios": total_usuarios,
        "usuarios_ativos": usuarios_ativos,
        "usuarios_pendentes": usuarios_pendentes,
        "total_professores": total_professores,
        "total_alunos": total_alunos,
    }
