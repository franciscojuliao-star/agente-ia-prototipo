"""
Serviço de Vector Store usando ChromaDB e Sentence Transformers.
"""
import logging
import uuid
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class VectorStoreError(Exception):
    """Erro do Vector Store."""
    pass


class VectorStoreService:
    """
    Serviço para gerenciamento de embeddings e busca vetorial.
    Usa ChromaDB para persistência e Sentence Transformers para embeddings.
    """

    _instance: "VectorStoreService | None" = None
    _embedding_model: SentenceTransformer | None = None

    def __new__(cls) -> "VectorStoreService":
        """Singleton pattern para garantir uma única instância."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        """Inicializa o serviço de Vector Store."""
        if self._initialized:
            return

        try:
            # Inicializa modelo de embeddings
            logger.info(f"Carregando modelo de embeddings: {settings.embedding_model}")
            self._embedding_model = SentenceTransformer(settings.embedding_model)

            # Inicializa ChromaDB com persistência
            logger.info(f"Inicializando ChromaDB em: {settings.chroma_persist_dir}")
            self._client = chromadb.PersistentClient(
                path=settings.chroma_persist_dir,
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True,
                ),
            )

            # Cria ou obtém a collection principal
            self._collection = self._client.get_or_create_collection(
                name="materiais_educacionais",
                metadata={"hnsw:space": "cosine"},
            )

            self._initialized = True
            logger.info("VectorStoreService inicializado com sucesso")

        except Exception as e:
            logger.error(f"Erro ao inicializar VectorStoreService: {e}")
            raise VectorStoreError(f"Erro ao inicializar Vector Store: {str(e)}")

    def gerar_embeddings(self, textos: list[str]) -> list[list[float]]:
        """
        Gera embeddings para uma lista de textos.

        Args:
            textos: Lista de textos para gerar embeddings

        Returns:
            Lista de vetores de embedding
        """
        if not textos:
            return []

        try:
            embeddings = self._embedding_model.encode(
                textos,
                convert_to_numpy=True,
                show_progress_bar=False,
            )
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Erro ao gerar embeddings: {e}")
            raise VectorStoreError(f"Erro ao gerar embeddings: {str(e)}")

    def adicionar_documentos(
        self,
        chunks: list[str],
        professor_id: uuid.UUID,
        material_id: uuid.UUID,
        disciplina: str,
        titulo: str,
    ) -> int:
        """
        Adiciona documentos (chunks) ao vector store.

        Args:
            chunks: Lista de chunks de texto
            professor_id: ID do professor dono do material
            material_id: ID do material fonte
            disciplina: Nome da disciplina
            titulo: Título do material

        Returns:
            Número de chunks adicionados
        """
        if not chunks:
            return 0

        try:
            # Gera embeddings
            embeddings = self.gerar_embeddings(chunks)

            # Prepara IDs únicos para cada chunk
            ids = [f"{material_id}_{i}" for i in range(len(chunks))]

            # Prepara metadados
            metadatas = [
                {
                    "professor_id": str(professor_id),
                    "material_id": str(material_id),
                    "disciplina": disciplina,
                    "titulo": titulo,
                    "chunk_index": i,
                }
                for i in range(len(chunks))
            ]

            # Adiciona ao ChromaDB
            self._collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=chunks,
                metadatas=metadatas,
            )

            logger.info(
                f"Adicionados {len(chunks)} chunks para material {material_id}"
            )
            return len(chunks)

        except Exception as e:
            logger.error(f"Erro ao adicionar documentos: {e}")
            raise VectorStoreError(f"Erro ao adicionar documentos: {str(e)}")

    def buscar_similares(
        self,
        query: str,
        professor_id: uuid.UUID,
        k: int = 10,
        disciplina: str | None = None,
        material_ids: list[uuid.UUID] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Busca documentos similares à query.

        Args:
            query: Texto de busca
            professor_id: ID do professor (filtra por professor)
            k: Número de resultados a retornar
            disciplina: Filtra por disciplina específica
            material_ids: Filtra por materiais específicos

        Returns:
            Lista de documentos similares com metadados e scores
        """
        try:
            # Gera embedding da query
            query_embedding = self.gerar_embeddings([query])[0]

            # Monta lista de filtros
            filters = [{"professor_id": str(professor_id)}]

            # Se material_ids fornecidos, filtra por eles (ignora disciplina)
            # Caso contrário, filtra pela disciplina
            if material_ids:
                if len(material_ids) == 1:
                    # ChromaDB não aceita $or com apenas 1 elemento
                    filters.append({"material_id": str(material_ids[0])})
                else:
                    filters.append({
                        "$or": [{"material_id": str(mid)} for mid in material_ids]
                    })
            elif disciplina:
                filters.append({"disciplina": disciplina})

            # Combina filtros
            if len(filters) > 1:
                where_filter = {"$and": filters}
            elif filters:
                where_filter = filters[0]
            else:
                # Fallback para garantir que nunca esteja vazio, embora professor_id seja obrigatório
                where_filter = {}

            # Realiza busca
            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                where=where_filter,
                include=["documents", "metadatas", "distances"],
            )

            # Formata resultados
            documentos = []
            if results["documents"] and results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    documentos.append({
                        "texto": doc,
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "distancia": results["distances"][0][i] if results["distances"] else 0,
                        "score": 1 - results["distances"][0][i] if results["distances"] else 1,
                    })

            logger.info(f"Busca retornou {len(documentos)} documentos para query")
            return documentos

        except Exception as e:
            logger.error(f"Erro na busca: {e}")
            raise VectorStoreError(f"Erro na busca: {str(e)}")

    def remover_por_material_id(self, material_id: uuid.UUID) -> int:
        """
        Remove todos os chunks de um material específico.

        Args:
            material_id: ID do material a remover

        Returns:
            Número estimado de documentos removidos
        """
        try:
            # Busca documentos do material
            results = self._collection.get(
                where={"material_id": str(material_id)},
                include=["metadatas"],
            )

            if not results["ids"]:
                return 0

            # Remove os documentos
            self._collection.delete(ids=results["ids"])

            logger.info(f"Removidos {len(results['ids'])} chunks do material {material_id}")
            return len(results["ids"])

        except Exception as e:
            logger.error(f"Erro ao remover documentos: {e}")
            raise VectorStoreError(f"Erro ao remover documentos: {str(e)}")

    def contar_documentos(self, professor_id: uuid.UUID | None = None) -> int:
        """
        Conta documentos no vector store.

        Args:
            professor_id: Filtra por professor específico

        Returns:
            Número de documentos
        """
        try:
            if professor_id:
                results = self._collection.get(
                    where={"professor_id": str(professor_id)},
                )
                return len(results["ids"]) if results["ids"] else 0
            return self._collection.count()
        except Exception as e:
            logger.error(f"Erro ao contar documentos: {e}")
            return 0


# Função helper para obter instância
def get_vectorstore() -> VectorStoreService:
    """Retorna instância do VectorStoreService."""
    return VectorStoreService()
