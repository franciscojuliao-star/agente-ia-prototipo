"""
Serviço de geração de conteúdo educacional.
Integra Vector Store e LLM para gerar quizzes, resumos e flashcards.
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models import (
    ConteudoGerado,
    Material,
    StatusConteudo,
    TipoConteudo,
    User,
)
from app.services.llm import LLMService, LLMError, get_llm_service
from app.services.vectorstore import VectorStoreService, VectorStoreError, get_vectorstore

logger = logging.getLogger(__name__)


class GeradorError(Exception):
    """Erro do serviço de geração."""
    pass


class GeradorService:
    """
    Serviço para geração de conteúdo educacional.
    Combina busca vetorial com geração via LLM.
    """

    def __init__(
        self,
        db: Session,
        vectorstore: VectorStoreService | None = None,
        llm: LLMService | None = None,
    ) -> None:
        """
        Inicializa o serviço gerador.

        Args:
            db: Sessão do banco de dados
            vectorstore: Serviço de vector store (opcional)
            llm: Serviço LLM (opcional)
        """
        self.db = db
        self.vectorstore = vectorstore or get_vectorstore()
        self.llm = llm or get_llm_service()

    def _buscar_contexto(
        self,
        professor_id: uuid.UUID,
        topico: str,
        disciplina: str,
        material_ids: list[uuid.UUID] | None = None,
        k: int = 5,  # Reduzido para acelerar geração
    ) -> str:
        """
        Busca contexto relevante no vector store.

        Args:
            professor_id: ID do professor
            topico: Tópico para busca
            disciplina: Disciplina dos materiais
            material_ids: IDs de materiais específicos
            k: Número de chunks a retornar

        Returns:
            Contexto concatenado dos chunks relevantes
        """
        try:
            documentos = self.vectorstore.buscar_similares(
                query=topico,
                professor_id=professor_id,
                k=k,
                disciplina=disciplina,
                material_ids=material_ids,
            )

            if not documentos:
                raise GeradorError(
                    f"Nenhum material encontrado para o tópico '{topico}' "
                    f"na disciplina '{disciplina}'"
                )

            # Concatena os textos relevantes
            contexto = "\n\n---\n\n".join([doc["texto"] for doc in documentos])
            return contexto

        except VectorStoreError as e:
            raise GeradorError(f"Erro ao buscar contexto: {str(e)}")

    def _obter_material_ids_usados(
        self,
        professor_id: uuid.UUID,
        disciplina: str,
        material_ids: list[uuid.UUID] | None = None,
    ) -> list[uuid.UUID]:
        """
        Obtém lista de IDs de materiais usados na geração.

        Args:
            professor_id: ID do professor
            disciplina: Disciplina dos materiais
            material_ids: IDs específicos ou None para todos

        Returns:
            Lista de UUIDs dos materiais
        """
        if material_ids:
            # Valida que os materiais pertencem ao professor (sem filtrar por disciplina)
            materiais = self.db.query(Material).filter(
                Material.id.in_(material_ids),
                Material.professor_id == professor_id,
            ).all()
            return [m.id for m in materiais]

        # Busca todos os materiais da disciplina do professor
        materiais = self.db.query(Material).filter(
            Material.professor_id == professor_id,
            Material.disciplina == disciplina,
        ).all()
        return [m.id for m in materiais]

    async def gerar_quiz(
        self,
        professor: User,
        topico: str,
        disciplina: str,
        num_questoes: int = 5,
        dificuldade: str = "medio",
        material_ids: list[uuid.UUID] | None = None,
    ) -> ConteudoGerado:
        """
        Gera um quiz baseado nos materiais do professor.

        Args:
            professor: Usuário professor
            topico: Tópico do quiz
            disciplina: Disciplina
            num_questoes: Número de questões
            dificuldade: Nível de dificuldade
            material_ids: IDs de materiais específicos

        Returns:
            ConteudoGerado com o quiz

        Raises:
            GeradorError: Se falhar na geração
        """
        logger.info(f"Gerando quiz para professor {professor.id}: {topico}")

        try:
            # Busca contexto relevante
            contexto = self._buscar_contexto(
                professor_id=professor.id,
                topico=topico,
                disciplina=disciplina,
                material_ids=material_ids,
            )

            # Gera quiz via LLM
            resultado = await self.llm.gerar_quiz(
                contexto=contexto,
                num_questoes=num_questoes,
                dificuldade=dificuldade,
            )

            # Obtém IDs dos materiais usados
            material_ids_usados = self._obter_material_ids_usados(
                professor_id=professor.id,
                disciplina=disciplina,
                material_ids=material_ids,
            )

            # Cria registro no banco
            conteudo = ConteudoGerado(
                professor_id=professor.id,
                tipo=TipoConteudo.QUIZ,
                topico=topico,
                disciplina=disciplina,
                conteudo_json=resultado,
                status=StatusConteudo.AGUARDANDO_APROVACAO,
                material_fonte_ids=material_ids_usados,
            )

            self.db.add(conteudo)
            self.db.commit()
            self.db.refresh(conteudo)

            logger.info(f"Quiz gerado com sucesso: {conteudo.id}")
            return conteudo

        except LLMError as e:
            logger.error(f"Erro LLM ao gerar quiz: {e}")
            raise GeradorError(str(e))
        except GeradorError:
            raise
        except Exception as e:
            logger.error(f"Erro ao gerar quiz: {e}")
            self.db.rollback()
            raise GeradorError(f"Erro ao gerar quiz: {str(e)}")

    async def gerar_resumo(
        self,
        professor: User,
        topico: str,
        disciplina: str,
        tamanho: str = "medio",
        material_ids: list[uuid.UUID] | None = None,
    ) -> ConteudoGerado:
        """
        Gera um resumo baseado nos materiais do professor.

        Args:
            professor: Usuário professor
            topico: Tópico do resumo
            disciplina: Disciplina
            tamanho: Tamanho do resumo (curto, medio, longo)
            material_ids: IDs de materiais específicos

        Returns:
            ConteudoGerado com o resumo
        """
        logger.info(f"Gerando resumo para professor {professor.id}: {topico}")

        try:
            contexto = self._buscar_contexto(
                professor_id=professor.id,
                topico=topico,
                disciplina=disciplina,
                material_ids=material_ids,
            )

            resultado = await self.llm.gerar_resumo(
                contexto=contexto,
                tamanho=tamanho,
                topico=topico,
            )

            material_ids_usados = self._obter_material_ids_usados(
                professor_id=professor.id,
                disciplina=disciplina,
                material_ids=material_ids,
            )

            conteudo = ConteudoGerado(
                professor_id=professor.id,
                tipo=TipoConteudo.RESUMO,
                topico=topico,
                disciplina=disciplina,
                conteudo_json=resultado,
                status=StatusConteudo.AGUARDANDO_APROVACAO,
                material_fonte_ids=material_ids_usados,
            )

            self.db.add(conteudo)
            self.db.commit()
            self.db.refresh(conteudo)

            logger.info(f"Resumo gerado com sucesso: {conteudo.id}")
            return conteudo

        except LLMError as e:
            logger.error(f"Erro LLM ao gerar resumo: {e}")
            raise GeradorError(str(e))
        except GeradorError:
            raise
        except Exception as e:
            logger.error(f"Erro ao gerar resumo: {e}")
            self.db.rollback()
            raise GeradorError(f"Erro ao gerar resumo: {str(e)}")

    async def gerar_flashcards(
        self,
        professor: User,
        topico: str,
        disciplina: str,
        num_cards: int = 10,
        material_ids: list[uuid.UUID] | None = None,
    ) -> ConteudoGerado:
        """
        Gera flashcards baseados nos materiais do professor.

        Args:
            professor: Usuário professor
            topico: Tópico dos flashcards
            disciplina: Disciplina
            num_cards: Número de flashcards
            material_ids: IDs de materiais específicos

        Returns:
            ConteudoGerado com os flashcards
        """
        logger.info(f"Gerando flashcards para professor {professor.id}: {topico}")

        try:
            contexto = self._buscar_contexto(
                professor_id=professor.id,
                topico=topico,
                disciplina=disciplina,
                material_ids=material_ids,
            )

            resultado = await self.llm.gerar_flashcards(
                contexto=contexto,
                num_cards=num_cards,
            )

            material_ids_usados = self._obter_material_ids_usados(
                professor_id=professor.id,
                disciplina=disciplina,
                material_ids=material_ids,
            )

            conteudo = ConteudoGerado(
                professor_id=professor.id,
                tipo=TipoConteudo.FLASHCARD,
                topico=topico,
                disciplina=disciplina,
                conteudo_json=resultado,
                status=StatusConteudo.AGUARDANDO_APROVACAO,
                material_fonte_ids=material_ids_usados,
            )

            self.db.add(conteudo)
            self.db.commit()
            self.db.refresh(conteudo)

            logger.info(f"Flashcards gerados com sucesso: {conteudo.id}")
            return conteudo

        except LLMError as e:
            logger.error(f"Erro LLM ao gerar flashcards: {e}")
            raise GeradorError(str(e))
        except GeradorError:
            raise
        except Exception as e:
            logger.error(f"Erro ao gerar flashcards: {e}")
            self.db.rollback()
            raise GeradorError(f"Erro ao gerar flashcards: {str(e)}")

    async def regenerar_conteudo(
        self,
        conteudo_id: uuid.UUID,
        professor: User,
        ajustes: str,
    ) -> ConteudoGerado:
        """
        Regenera conteúdo com ajustes solicitados.

        Args:
            conteudo_id: ID do conteúdo a regenerar
            professor: Professor solicitante
            ajustes: Descrição dos ajustes desejados

        Returns:
            Novo ConteudoGerado
        """
        # Busca conteúdo original
        conteudo_original = self.db.query(ConteudoGerado).filter(
            ConteudoGerado.id == conteudo_id,
            ConteudoGerado.professor_id == professor.id,
        ).first()

        if not conteudo_original:
            raise GeradorError("Conteúdo não encontrado")

        # Regenera baseado no tipo
        if conteudo_original.tipo == TipoConteudo.QUIZ:
            # Extrai parâmetros do original
            num_questoes = len(conteudo_original.conteudo_json.get("questoes", []))
            return await self.gerar_quiz(
                professor=professor,
                topico=f"{conteudo_original.topico} - Ajuste: {ajustes}",
                disciplina=conteudo_original.disciplina,
                num_questoes=num_questoes or 5,
                material_ids=conteudo_original.material_fonte_ids,
            )

        elif conteudo_original.tipo == TipoConteudo.RESUMO:
            return await self.gerar_resumo(
                professor=professor,
                topico=f"{conteudo_original.topico} - Ajuste: {ajustes}",
                disciplina=conteudo_original.disciplina,
                material_ids=conteudo_original.material_fonte_ids,
            )

        elif conteudo_original.tipo == TipoConteudo.FLASHCARD:
            num_cards = len(conteudo_original.conteudo_json.get("flashcards", []))
            return await self.gerar_flashcards(
                professor=professor,
                topico=f"{conteudo_original.topico} - Ajuste: {ajustes}",
                disciplina=conteudo_original.disciplina,
                num_cards=num_cards or 10,
                material_ids=conteudo_original.material_fonte_ids,
            )

        raise GeradorError(f"Tipo de conteúdo não suportado: {conteudo_original.tipo}")

    def aprovar_conteudo(
        self,
        conteudo_id: uuid.UUID,
        professor: User,
        modificacoes: dict[str, Any] | None = None,
    ) -> ConteudoGerado:
        """
        Aprova conteúdo gerado.

        Args:
            conteudo_id: ID do conteúdo
            professor: Professor aprovador
            modificacoes: Modificações opcionais

        Returns:
            ConteudoGerado aprovado
        """
        conteudo = self.db.query(ConteudoGerado).filter(
            ConteudoGerado.id == conteudo_id,
            ConteudoGerado.professor_id == professor.id,
        ).first()

        if not conteudo:
            raise GeradorError("Conteúdo não encontrado")

        if conteudo.status != StatusConteudo.AGUARDANDO_APROVACAO:
            raise GeradorError(
                f"Conteúdo não pode ser aprovado. Status atual: {conteudo.status}"
            )

        conteudo.status = StatusConteudo.APROVADO
        conteudo.aprovado_em = datetime.now(timezone.utc)
        if modificacoes:
            conteudo.modificacoes_professor = modificacoes
            # Aplica modificações ao conteúdo
            if "conteudo_json" in modificacoes:
                conteudo.conteudo_json = {
                    **conteudo.conteudo_json,
                    **modificacoes["conteudo_json"],
                }

        self.db.commit()
        self.db.refresh(conteudo)

        logger.info(f"Conteúdo {conteudo_id} aprovado por professor {professor.id}")
        return conteudo

    def rejeitar_conteudo(
        self,
        conteudo_id: uuid.UUID,
        professor: User,
        motivo: str,
    ) -> ConteudoGerado:
        """
        Rejeita conteúdo gerado.

        Args:
            conteudo_id: ID do conteúdo
            professor: Professor que rejeita
            motivo: Motivo da rejeição

        Returns:
            ConteudoGerado rejeitado
        """
        conteudo = self.db.query(ConteudoGerado).filter(
            ConteudoGerado.id == conteudo_id,
            ConteudoGerado.professor_id == professor.id,
        ).first()

        if not conteudo:
            raise GeradorError("Conteúdo não encontrado")

        if conteudo.status != StatusConteudo.AGUARDANDO_APROVACAO:
            raise GeradorError(
                f"Conteúdo não pode ser rejeitado. Status atual: {conteudo.status}"
            )

        conteudo.status = StatusConteudo.REJEITADO
        conteudo.motivo_rejeicao = motivo

        self.db.commit()
        self.db.refresh(conteudo)

        logger.info(f"Conteúdo {conteudo_id} rejeitado por professor {professor.id}")
        return conteudo


def get_gerador_service(db: Session) -> GeradorService:
    """Retorna instância do GeradorService."""
    return GeradorService(db=db)
