"""
Serviço de processamento de documentos.
Extração de texto de PDFs, vídeos do YouTube e páginas web.
"""
import io
import logging
import re
from typing import BinaryIO

import requests
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
)

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class ProcessamentoError(Exception):
    """Erro durante processamento de documento."""
    pass


def extrair_texto_pdf(file: BinaryIO) -> str:
    """
    Extrai texto de um arquivo PDF.

    Args:
        file: Arquivo PDF em formato binário

    Returns:
        Texto extraído do PDF

    Raises:
        ProcessamentoError: Se falhar ao extrair texto
    """
    try:
        pdf_reader = PdfReader(file)
        texto_completo = []

        for page_num, page in enumerate(pdf_reader.pages):
            try:
                texto = page.extract_text()
                if texto:
                    texto_completo.append(texto)
            except Exception as e:
                logger.warning(f"Erro ao extrair página {page_num}: {e}")
                continue

        if not texto_completo:
            raise ProcessamentoError("Não foi possível extrair texto do PDF")

        return "\n\n".join(texto_completo)

    except ProcessamentoError:
        raise
    except Exception as e:
        logger.error(f"Erro ao processar PDF: {e}")
        raise ProcessamentoError(f"Erro ao processar PDF: {str(e)}")


def extrair_video_id(url: str) -> str | None:
    """
    Extrai o ID do vídeo de uma URL do YouTube.

    Args:
        url: URL do YouTube

    Returns:
        ID do vídeo ou None se não encontrado
    """
    patterns = [
        r"(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})",
        r"youtube\.com\/v\/([a-zA-Z0-9_-]{11})",
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return None


def extrair_transcricao_youtube(url: str) -> str:
    """
    Extrai transcrição de um vídeo do YouTube.

    Args:
        url: URL do vídeo do YouTube

    Returns:
        Transcrição do vídeo

    Raises:
        ProcessamentoError: Se falhar ao extrair transcrição
    """
    video_id = extrair_video_id(url)
    if not video_id:
        raise ProcessamentoError("URL do YouTube inválida")

    try:
        # Tenta obter transcrição em português primeiro, depois inglês
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        transcript = None
        for lang in ["pt", "pt-BR", "en", "en-US"]:
            try:
                transcript = transcript_list.find_transcript([lang])
                break
            except NoTranscriptFound:
                continue

        if transcript is None:
            # Tenta pegar qualquer transcrição disponível
            try:
                transcript = transcript_list.find_generated_transcript(["pt", "en"])
            except NoTranscriptFound:
                pass

        if transcript is None:
            # Última tentativa: pegar a primeira disponível
            for t in transcript_list:
                transcript = t
                break

        if transcript is None:
            raise ProcessamentoError("Nenhuma transcrição disponível para este vídeo")

        # Extrai o texto da transcrição
        transcript_data = transcript.fetch()
        texto_completo = " ".join([item["text"] for item in transcript_data])

        return texto_completo

    except TranscriptsDisabled:
        raise ProcessamentoError("Transcrições desabilitadas para este vídeo")
    except VideoUnavailable:
        raise ProcessamentoError("Vídeo não disponível")
    except ProcessamentoError:
        raise
    except Exception as e:
        logger.error(f"Erro ao extrair transcrição do YouTube: {e}")
        raise ProcessamentoError(f"Erro ao extrair transcrição: {str(e)}")


def extrair_texto_url(url: str) -> str:
    """
    Extrai texto de uma página web usando BeautifulSoup.

    Args:
        url: URL da página web

    Returns:
        Texto extraído da página

    Raises:
        ProcessamentoError: Se falhar ao extrair texto
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")

        # Remove scripts, styles e outros elementos não textuais
        for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
            element.decompose()

        # Extrai texto
        texto = soup.get_text(separator="\n", strip=True)

        # Limpa linhas vazias múltiplas
        linhas = [linha.strip() for linha in texto.split("\n") if linha.strip()]
        texto_limpo = "\n".join(linhas)

        if not texto_limpo or len(texto_limpo) < 50:
            raise ProcessamentoError("Página não contém texto suficiente")

        return texto_limpo

    except requests.exceptions.RequestException as e:
        logger.error(f"Erro ao acessar URL {url}: {e}")
        raise ProcessamentoError(f"Erro ao acessar URL: {str(e)}")
    except ProcessamentoError:
        raise
    except Exception as e:
        logger.error(f"Erro ao processar URL {url}: {e}")
        raise ProcessamentoError(f"Erro ao processar página: {str(e)}")


def dividir_em_chunks(
    texto: str,
    tamanho: int | None = None,
    overlap: int | None = None,
) -> list[str]:
    """
    Divide texto em chunks para processamento vetorial.

    Args:
        texto: Texto a ser dividido
        tamanho: Tamanho máximo de cada chunk (default: config)
        overlap: Sobreposição entre chunks (default: config)

    Returns:
        Lista de chunks de texto
    """
    if tamanho is None:
        tamanho = settings.chunk_size
    if overlap is None:
        overlap = settings.chunk_overlap

    if not texto:
        return []

    # Normaliza espaços em branco
    texto = re.sub(r"\s+", " ", texto).strip()

    if len(texto) <= tamanho:
        return [texto]

    chunks = []
    inicio = 0

    while inicio < len(texto):
        fim = inicio + tamanho

        # Se não é o último chunk, tenta cortar em um espaço
        if fim < len(texto):
            # Procura o último espaço dentro do limite
            ultimo_espaco = texto.rfind(" ", inicio, fim)
            if ultimo_espaco > inicio:
                fim = ultimo_espaco

        chunk = texto[inicio:fim].strip()
        if chunk:
            chunks.append(chunk)

        # Avança com overlap
        inicio = fim - overlap if fim < len(texto) else fim

    return chunks
