"""
Servicio de extracción de audio desde YouTube usando yt-dlp.

Responsabilidad única: extraer información y URL de audio de un query de YouTube.
"""

import time
import logging

import yt_dlp

from models.track import Track
from services.metrics import metrics

logger = logging.getLogger(__name__)


class YouTubeService:
    """Extrae información de audio de YouTube de forma segura y robusta."""

    def __init__(self):
        self._ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'quiet': True,
            'no_warnings': True,
            'default_search': 'auto',
            'retries': 3,
            'geo_bypass': True,
            'socket_timeout': 10,
            'http_headers': {
                'User-Agent': (
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/125.0.0.0 Safari/537.36'
                ),
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://www.youtube.com/',
            },
        }

    @staticmethod
    def _strip_playlist_params(query: str) -> str:
        """Remueve parámetros de playlist de una URL para forzar video individual."""
        if '&list=' in query:
            query = query.split('&list=')[0]
        if '?list=' in query:
            query = query.split('?list=')[0]
        return query

    @staticmethod
    def _find_audio_url(info: dict) -> str | None:
        """Busca la mejor URL de audio disponible en la información extraída."""
        url = info.get('url')
        if url:
            return url

        # Fallback: buscar en formatos alternativos
        for fmt in info.get('formats', []):
            if fmt.get('url'):
                return fmt['url']

        return None

    def extract_track(self, query: str, requester_id: int | None = None) -> Track | None:
        """
        Extrae la información de un track de YouTube.

        Args:
            query: URL de YouTube o texto de búsqueda.
            requester_id: ID del usuario de Discord que solicitó la canción.

        Returns:
            Un objeto Track con la información del audio, o None si falla.
        """
        start_time = time.time()
        query = self._strip_playlist_params(query)

        try:
            with yt_dlp.YoutubeDL(self._ydl_opts) as ydl:
                info = ydl.extract_info(query, download=False)

                # Si yt-dlp retorna una playlist, tomar solo el primer resultado
                if 'entries' in info:
                    info = info['entries'][0]

                url = self._find_audio_url(info)

                if not url:
                    logger.warning("No se encontró URL de audio para: %s", query)
                    return None

                # Métricas (no-op si Datadog no está disponible)
                elapsed_ms = (time.time() - start_time) * 1000
                metrics.histogram('bot.youtube.extraction_latency_ms', elapsed_ms)
                metrics.increment('bot.youtube.extraction_success')

                return Track(
                    title=info.get('title', 'Desconocido'),
                    url=url,
                    original_url=info.get('webpage_url', query),
                    duration=info.get('duration'),
                    requester_id=requester_id,
                )

        except Exception as e:
            metrics.increment('bot.youtube.extraction_error', tags=[f"error:{type(e).__name__}"])
            logger.error("Error extrayendo audio: %s", e)
            return None