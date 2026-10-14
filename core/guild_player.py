"""
Reproductor de audio por servidor (guild).

Responsabilidad única: gestionar la cola de reproducción y controlar
la reproducción de audio en un servidor específico de Discord.
"""

import asyncio
import logging

import discord

from models.track import Track
from services.metrics import metrics

logger = logging.getLogger(__name__)


class GuildPlayer:
    """Estado y lógica de reproducción aislada por servidor."""

    def __init__(self, bot, guild_id: int):
        self.bot = bot
        self.guild_id = guild_id
        self.queue: list[Track] = []
        self.current_track: Track | None = None
        self.loop_enabled: bool = False
        self.voice_client: discord.VoiceClient | None = None

    def add_to_queue(self, track: Track) -> None:
        """Añade un track a la cola de reproducción."""
        self.queue.append(track)
        metrics.gauge(
            'bot.music.queue_length',
            len(self.queue),
            tags=[f"guild:{self.guild_id}"],
        )

    async def play_next(self, ctx) -> None:
        """Reproduce el siguiente track en la cola."""
        # Si el loop está activo y hay una canción actual, la re-reproduce
        if not self.loop_enabled or not self.current_track:
            if not self.queue:
                self.current_track = None
                metrics.decrement(
                    'bot.music.active_players',
                    tags=[f"guild:{self.guild_id}"],
                )
                return

            self.current_track = self.queue.pop(0)

        if not self.voice_client or not self.voice_client.is_connected():
            self.voice_client = ctx.voice_client

        if not self.voice_client:
            logger.warning("No hay voice_client activo en guild %s", self.guild_id)
            return

        # Opciones de FFmpeg optimizadas para streaming
        ffmpeg_options = {
            'before_options': (
                '-reconnect 1 -reconnect_streamed 1 '
                '-reconnect_delay_max 5 -nostdin'
            ),
            'options': '-vn -filter:a "volume=0.8"',
        }

        try:
            source = discord.FFmpegPCMAudio(
                self.current_track.url,
                **ffmpeg_options,
            )
            # PCMVolumeTransformer permite controlar el volumen en tiempo real
            source = discord.PCMVolumeTransformer(source, volume=0.8)

            def after_playing(error):
                if error:
                    metrics.increment(
                        'bot.music.playback_error',
                        tags=[f"guild:{self.guild_id}"],
                    )
                    logger.error("Error reproduciendo en guild %s: %s", self.guild_id, error)
                # Ejecutamos la siguiente canción de forma segura en el event loop
                asyncio.run_coroutine_threadsafe(
                    self.play_next(ctx),
                    self.bot.loop,
                )

            self.voice_client.play(source, after=after_playing)

            # Solo avisamos si es una canción nueva para evitar spam en modo loop
            if not self.loop_enabled:
                await ctx.send(f"🎶 Reproduciendo: **{self.current_track.title}**")

        except Exception as e:
            metrics.increment(
                'bot.music.playback_error',
                tags=[f"guild:{self.guild_id}"],
            )
            logger.error("Error al iniciar reproducción en guild %s: %s", self.guild_id, e, exc_info=True)
            await ctx.send(f"Error al reproducir (**{e}**). Saltando a la siguiente...")
            await self.play_next(ctx)

    def clear(self) -> None:
        """Limpia la cola y desactiva el loop."""
        self.queue.clear()
        self.loop_enabled = False
        metrics.gauge(
            'bot.music.queue_length',
            0,
            tags=[f"guild:{self.guild_id}"],
        )