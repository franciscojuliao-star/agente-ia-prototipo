"""
Routers da API.
"""
from app.routers.auth import router as auth_router
from app.routers.materiais import router as materiais_router
from app.routers.conteudos import router as conteudos_router
from app.routers.alunos import router as alunos_router
from app.routers.admin import router as admin_router

__all__ = [
    "auth_router",
    "materiais_router",
    "conteudos_router",
    "alunos_router",
    "admin_router",
]
