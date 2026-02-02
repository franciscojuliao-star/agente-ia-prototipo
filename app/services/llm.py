"""
Serviço LLM usando Ollama local.
"""
import json
import logging
import re
from typing import Any

import httpx

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class LLMError(Exception):
    """Erro do serviço LLM."""
    pass


class LLMService:
    """
    Serviço para interação com LLM via Ollama.
    """

    SYSTEM_PROMPT_BASE = """Você é um assistente educacional. Responda APENAS com JSON válido. Sem texto antes ou depois do JSON."""

    PROMPT_QUIZ = """Material:
{contexto}

Crie {num_questoes} questões de múltipla escolha ({dificuldade}).

Retorne JSON:
{{"questoes": [{{"pergunta": "...", "alternativas": {{"a": "...", "b": "...", "c": "...", "d": "..."}}, "resposta_correta": "a", "explicacao": "..."}}]}}"""

    PROMPT_RESUMO = """Material sobre {topico}:
{contexto}

Crie um resumo {tamanho} (curto=2 parágrafos, medio=4, longo=6).

Retorne JSON:
{{"resumo": {{"introducao": "...", "desenvolvimento": ["ponto1", "ponto2"], "conclusao": "..."}}}}"""

    PROMPT_FLASHCARDS = """Material:
{contexto}

Crie {num_cards} flashcards.

Retorne JSON:
{{"flashcards": [{{"frente": "pergunta", "verso": "resposta"}}]}}"""

    def __init__(self) -> None:
        """Inicializa o serviço LLM."""
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_model
        self.timeout = settings.ollama_timeout

    async def _verificar_ollama(self) -> bool:
        """
        Verifica se o Ollama está online.

        Returns:
            True se online, False caso contrário
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/tags",
                    timeout=5.0,
                )
                return response.status_code == 200
        except Exception:
            return False

    async def gerar_resposta(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_retries: int = 3,
    ) -> str:
        """
        Gera resposta usando Ollama.

        Args:
            prompt: Prompt do usuário
            system_prompt: System prompt opcional
            temperature: Temperatura de geração
            max_retries: Número máximo de tentativas

        Returns:
            Texto gerado pelo LLM

        Raises:
            LLMError: Se falhar após todas as tentativas
        """
        if system_prompt is None:
            system_prompt = self.SYSTEM_PROMPT_BASE

        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": 0.9,
            },
        }

        last_error = None
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.base_url}/api/generate",
                        json=payload,
                        timeout=self.timeout,
                    )

                    if response.status_code != 200:
                        raise LLMError(
                            f"Ollama retornou status {response.status_code}"
                        )

                    data = response.json()
                    return data.get("response", "")

            except httpx.TimeoutException:
                last_error = LLMError("Timeout ao aguardar resposta do Ollama")
                logger.warning(f"Tentativa {attempt + 1}: Timeout do Ollama")
            except httpx.ConnectError:
                last_error = LLMError(
                    "Serviço de IA temporariamente indisponível. "
                    "Verifique se o Ollama está rodando."
                )
                logger.error("Ollama não está acessível")
                break  # Não adianta tentar de novo se não está conectando
            except Exception as e:
                last_error = LLMError(f"Erro ao gerar resposta: {str(e)}")
                logger.error(f"Tentativa {attempt + 1}: {e}")

        raise last_error or LLMError("Falha ao gerar resposta")

    def _extrair_json(self, texto: str) -> dict[str, Any]:
        """
        Extrai JSON de uma resposta do LLM.
        """
        # Limpa o texto
        texto = texto.strip()

        # Remove prefixos comuns
        for prefix in ["Aqui está", "Segue", "JSON:", "Resposta:"]:
            if texto.lower().startswith(prefix.lower()):
                texto = texto[len(prefix):].strip()

        # Tenta parsear diretamente
        try:
            return json.loads(texto)
        except json.JSONDecodeError:
            pass

        # Extrai conteúdo de code blocks
        code_block = re.search(r"```(?:json)?\s*([\s\S]*?)```", texto)
        if code_block:
            try:
                return json.loads(code_block.group(1).strip())
            except json.JSONDecodeError:
                pass

        # Encontra o primeiro { e último }
        start = texto.find("{")
        end = texto.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(texto[start:end + 1])
            except json.JSONDecodeError:
                pass

        # Tenta corrigir JSON comum (trailing commas)
        if start != -1 and end != -1:
            json_str = texto[start:end + 1]
            json_str = re.sub(r",\s*}", "}", json_str)
            json_str = re.sub(r",\s*]", "]", json_str)
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass

        raise LLMError("Não foi possível extrair JSON válido da resposta")

    async def gerar_quiz(
        self,
        contexto: str,
        num_questoes: int,
        dificuldade: str,
    ) -> dict[str, Any]:
        """
        Gera quiz baseado no contexto.

        Args:
            contexto: Texto do material
            num_questoes: Número de questões
            dificuldade: Nível de dificuldade (facil, medio, dificil)

        Returns:
            Dicionário com as questões do quiz
        """
        prompt = self.PROMPT_QUIZ.format(
            contexto=contexto,
            num_questoes=num_questoes,
            dificuldade=dificuldade,
        )

        for attempt in range(3):
            try:
                resposta = await self.gerar_resposta(prompt, temperature=0.3)
                resultado = self._extrair_json(resposta)

                # Valida estrutura básica
                if "questoes" not in resultado:
                    raise LLMError("Resposta não contém 'questoes'")

                return resultado

            except LLMError as e:
                logger.warning(f"Tentativa {attempt + 1} de gerar quiz falhou: {e}")
                if attempt == 2:
                    raise

        raise LLMError("Falha ao gerar quiz após múltiplas tentativas")

    async def gerar_resumo(
        self,
        contexto: str,
        tamanho: str,
        topico: str,
    ) -> dict[str, Any]:
        """
        Gera resumo baseado no contexto.

        Args:
            contexto: Texto do material
            tamanho: Tamanho do resumo (curto, medio, longo)
            topico: Tópico principal

        Returns:
            Dicionário com o resumo estruturado
        """
        prompt = self.PROMPT_RESUMO.format(
            contexto=contexto,
            tamanho=tamanho,
            topico=topico,
        )

        for attempt in range(3):
            try:
                resposta = await self.gerar_resposta(prompt, temperature=0.3)
                resultado = self._extrair_json(resposta)

                if "resumo" not in resultado:
                    raise LLMError("Resposta não contém 'resumo'")

                return resultado

            except LLMError as e:
                logger.warning(f"Tentativa {attempt + 1} de gerar resumo falhou: {e}")
                if attempt == 2:
                    raise

        raise LLMError("Falha ao gerar resumo após múltiplas tentativas")

    async def gerar_flashcards(
        self,
        contexto: str,
        num_cards: int,
    ) -> dict[str, Any]:
        """
        Gera flashcards baseados no contexto.

        Args:
            contexto: Texto do material
            num_cards: Número de flashcards

        Returns:
            Dicionário com os flashcards
        """
        prompt = self.PROMPT_FLASHCARDS.format(
            contexto=contexto,
            num_cards=num_cards,
        )

        for attempt in range(3):
            try:
                resposta = await self.gerar_resposta(prompt, temperature=0.3)
                resultado = self._extrair_json(resposta)

                if "flashcards" not in resultado:
                    raise LLMError("Resposta não contém 'flashcards'")

                return resultado

            except LLMError as e:
                logger.warning(f"Tentativa {attempt + 1} de gerar flashcards falhou: {e}")
                if attempt == 2:
                    raise

        raise LLMError("Falha ao gerar flashcards após múltiplas tentativas")


# Função helper para obter instância
def get_llm_service() -> LLMService:
    """Retorna instância do LLMService."""
    return LLMService()
