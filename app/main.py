"""
Aplicação principal FastAPI - Sistema RAG Educacional.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database import init_db
from app.routers import auth_router, materiais_router, conteudos_router, alunos_router

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia ciclo de vida da aplicação."""
    # Startup
    logger.info("Iniciando aplicação...")
    logger.info(f"Ambiente: {settings.environment}")
    logger.info(f"LLM Provider: {settings.llm_provider}")
    logger.info(f"Modelo: {settings.ollama_model}")

    # Inicializa banco de dados
    try:
        init_db()
        logger.info("Banco de dados inicializado")
    except Exception as e:
        logger.error(f"Erro ao inicializar banco de dados: {e}")
        raise

    yield

    # Shutdown
    logger.info("Encerrando aplicação...")


# Cria aplicação FastAPI
app = FastAPI(
    title="AVA RAG API",
    description="""
    API REST para Sistema RAG Educacional.

    ## Funcionalidades

    ### Para Professores
    - Upload de materiais (PDF, vídeos do YouTube, links, texto)
    - Geração de quizzes, resumos e flashcards com IA
    - Aprovação e modificação de conteúdo gerado

    ### Para Alunos
    - Acesso a conteúdos aprovados por disciplina
    - Responder quizzes com feedback imediato
    - Busca semântica nos materiais
    - Histórico de tentativas

    ## Stack Tecnológica
    - **LLM**: Ollama (llama3.1:8b local)
    - **Embeddings**: Sentence Transformers (all-MiniLM-L6-v2)
    - **Vector Store**: ChromaDB
    - **Banco de Dados**: PostgreSQL

    ## Autenticação
    Todas as rotas (exceto /api/auth) requerem token JWT no header:
    ```
    Authorization: Bearer <token>
    ```
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware de tratamento de erros global
@app.middleware("http")
async def error_handling_middleware(request: Request, call_next):
    """Middleware para tratamento global de erros."""
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        logger.exception(f"Erro não tratado: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Erro interno do servidor"},
        )


# Registra routers
app.include_router(auth_router)
app.include_router(materiais_router)
app.include_router(conteudos_router)
app.include_router(alunos_router)


# Rota de health check
@app.get(
    "/health",
    tags=["Health"],
    summary="Health Check",
)
async def health_check():
    """Verifica se a API está funcionando."""
    return {
        "status": "healthy",
        "environment": settings.environment,
        "llm_provider": settings.llm_provider,
        "ollama_model": settings.ollama_model,
    }


# Rota raiz
@app.get(
    "/",
    tags=["Root"],
    summary="Informações da API",
)
async def root():
    """Retorna informações básicas da API."""
    return {
        "name": "AVA RAG API",
        "version": "1.0.0",
        "description": "Sistema RAG Educacional 100% Gratuito",
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
