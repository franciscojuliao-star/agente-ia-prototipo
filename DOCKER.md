# Guia Docker - AVA RAG API

## Requisitos

- Docker 24+
- Docker Compose v2+
- 8GB RAM (mínimo)
- 10GB espaço em disco

## Início Rápido

```bash
# Clonar e entrar no diretório
cd projeto_llm_ava

# Subir todos os serviços
docker compose up -d --build

# Aguardar download do modelo LLM (~2GB)
docker compose logs -f ollama-pull
```

Após conclusão, acesse: **http://localhost**

## Serviços

| Serviço | Porta | Descrição |
|---------|-------|-----------|
| frontend | 80 | Interface web (nginx) |
| backend | 8000 | API FastAPI |
| postgres | 5432 | Banco de dados |
| ollama | 11434 | Servidor LLM |

## Comandos Úteis

### Gerenciamento

```bash
# Iniciar
docker compose up -d

# Parar
docker compose down

# Reiniciar um serviço
docker compose restart backend

# Ver status
docker compose ps
```

### Logs

```bash
# Todos os serviços
docker compose logs -f

# Apenas backend
docker compose logs -f backend

# Últimas 100 linhas
docker compose logs --tail 100 backend
```

### Manutenção

```bash
# Rebuild após alterações
docker compose up -d --build

# Limpar volumes (CUIDADO: apaga dados)
docker compose down -v

# Remover imagens antigas
docker image prune -f
```

## Configuração

### Variáveis de Ambiente

Crie um arquivo `.env.docker` para sobrescrever configurações:

```env
# Segurança (MUDE EM PRODUÇÃO!)
SECRET_KEY=sua-chave-super-secreta-de-producao

# Modelo LLM alternativo
OLLAMA_MODEL=llama3.2:3b

# Timeout maior para modelos grandes
OLLAMA_TIMEOUT=300
```

### GPU NVIDIA

Para usar GPU, edite `docker-compose.yml`:

```yaml
ollama:
  image: ollama/ollama:latest
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

Requisitos:
- NVIDIA Driver 525+
- NVIDIA Container Toolkit

```bash
# Instalar NVIDIA Container Toolkit
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://nvidia.github.io/libnvidia-container/stable/deb/$(ARCH) /" | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt update && sudo apt install -y nvidia-container-toolkit
sudo systemctl restart docker
```

## Deploy em Produção

### 1. Configurar domínio

Edite `frontend/Dockerfile` para configurar o nginx com seu domínio e SSL.

### 2. Variáveis seguras

```bash
# Gerar chave secreta
openssl rand -hex 32
```

### 3. docker-compose.prod.yml

```yaml
services:
  backend:
    environment:
      SECRET_KEY: ${SECRET_KEY}
      ENVIRONMENT: production
      DEBUG: "false"
    restart: always

  frontend:
    restart: always

  postgres:
    restart: always

  ollama:
    restart: always
```

### 4. Executar em produção

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Troubleshooting

### Container não inicia

```bash
# Ver logs de erro
docker compose logs backend

# Verificar se portas estão livres
sudo lsof -i :80
sudo lsof -i :8000
```

### Ollama lento sem GPU

Normal em CPU. O modelo `llama3.2:3b` leva 30-60s por resposta em CPU.

### Erro de memória

```bash
# Verificar uso de memória
docker stats

# Aumentar swap se necessário
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Banco de dados corrompido

```bash
# Backup antes
docker compose exec postgres pg_dump -U ava_user ava_db > backup.sql

# Recriar volume
docker compose down
docker volume rm projeto_llm_ava_postgres_data
docker compose up -d
```

### Modelo LLM não baixou

```bash
# Baixar manualmente
docker compose exec ollama ollama pull llama3.2:3b

# Verificar modelos
docker compose exec ollama ollama list
```

## Volumes

| Volume | Conteúdo |
|--------|----------|
| postgres_data | Dados do PostgreSQL |
| ollama_data | Modelos LLM (~2-5GB) |
| chroma_data | Índice vetorial |
| uploads_data | Arquivos enviados |

## Portas Alternativas

Se as portas padrão estiverem em uso:

```yaml
# docker-compose.override.yml
services:
  frontend:
    ports:
      - "3000:80"
  backend:
    ports:
      - "8080:8000"
```

## Recursos

- [Docker Docs](https://docs.docker.com/)
- [Ollama Docker](https://hub.docker.com/r/ollama/ollama)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/docker/)
