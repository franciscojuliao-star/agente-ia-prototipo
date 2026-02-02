# AVA RAG API - Sistema RAG Educacional

API REST para sistema RAG (Retrieval-Augmented Generation) educacional **100% gratuito**, sem dependência de APIs pagas.

## Stack Tecnológica

| Componente | Tecnologia |
|------------|------------|
| **Framework** | FastAPI + Python 3.10+ |
| **LLM** | Ollama (llama3.2:3b local) |
| **Embeddings** | Sentence Transformers (all-MiniLM-L6-v2) |
| **Banco Vetorial** | ChromaDB (local persistente) |
| **Banco de Dados** | PostgreSQL + SQLAlchemy |
| **Autenticação** | JWT (python-jose) |


## Funcionalidades

### Para Professores
- Upload de materiais (PDF, vídeos do YouTube, links, texto)
- Geração automática de quizzes com IA
- Geração de resumos estruturados
- Geração de flashcards
- Aprovação/rejeição de conteúdo gerado

### Para Alunos
- Acesso a conteúdos aprovados por disciplina
- Responder quizzes com feedback imediato
- Busca semântica nos materiais
- Visualização de flashcards e resumos

## Instalação Rápida

### Opção 1: Docker (Recomendado)

```bash
docker compose up -d --build
```

Ver [DOCKER.md](DOCKER.md) para instruções detalhadas.

### Opção 2: Manual

#### 1. Pré-requisitos

```bash
# Python 3.10+
python --version

# PostgreSQL
sudo apt install postgresql postgresql-contrib

# Ollama
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.2:3b
```

#### 2. Configurar PostgreSQL

```bash
sudo -u postgres psql -c "CREATE USER ava_user WITH PASSWORD 'senha123';"
sudo -u postgres psql -c "CREATE DATABASE ava_db OWNER ava_user;"
```

#### 3. Configurar Ambiente

```bash
# Criar ambiente virtual
python -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis
cp .env.example .env
```

#### 4. Executar Migrations

```bash
alembic upgrade head
```

#### 5. Iniciar

**Terminal 1 - Ollama:**
```bash
ollama serve
```

**Terminal 2 - Backend:**
```bash
source venv/bin/activate
uvicorn app.main:app --reload
```

**Terminal 3 - Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## URLs

| Serviço | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| API Docs | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |

## Credenciais de Teste

```
Email: professor@teste.com
Senha: senha123
```

## Estrutura do Projeto

```
├── app/
│   ├── main.py              # FastAPI principal
│   ├── config.py            # Configurações
│   ├── database.py          # Conexão SQLAlchemy
│   ├── auth/                # JWT e autenticação
│   ├── models/              # Modelos do banco
│   ├── schemas/             # Schemas Pydantic
│   ├── services/            # Lógica de negócio
│   └── routers/             # Endpoints da API
├── frontend/                # React + Vite
├── docker-compose.yml       # Orquestração Docker
├── Dockerfile               # Build do backend
└── requirements.txt         # Dependências Python
```

## Variáveis de Ambiente

```env
# LLM
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
OLLAMA_TIMEOUT=120

# Banco de Dados
DATABASE_URL=postgresql://ava_user:senha123@localhost:5432/ava_db

# JWT
SECRET_KEY=sua-chave-secreta-aqui
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

## Troubleshooting

### LLM lento
Use o modelo `llama3.2:3b` em vez de `llama3.1:8b` para GPUs com menos de 6GB VRAM.

### Ollama não conecta
```bash
curl http://localhost:11434/api/tags
pkill ollama && ollama serve
```

### Erro de conexão PostgreSQL
```bash
sudo systemctl start postgresql
sudo systemctl status postgresql
```

## Licença

MIT
