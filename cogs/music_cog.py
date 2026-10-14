import discord
from discord import app_commands
from discord.ext import commands
from services.metrics import metrics
from services.audio_extractor import YouTubeService
import asyncio

class MusicCog(commands.Cog):
    def __init__(self, bot, player_manager):
        self.bot = bot
        self.player_manager = player_manager
        self.youtube_service = YouTubeService()

    @commands.command()
    @app_commands.describe(query="URL o nombre de la canción")
    async def play(self, ctx, *, query: str):
        metrics.increment('bot.command.usage', tags=['command:play'])
        
        if not ctx.author.voice:
            return await ctx.send("Debes estar en un canal de voz.")

        voice_client = ctx.voice_client
        if not voice_client:
            try:
                voice_client = await ctx.author.voice.channel.connect(timeout=20.0, reconnect=True)
            except Exception as e:
                return await ctx.send(f"No pude conectarme al canal de voz: {e}")

        player = self.player_manager.get_player(ctx.guild.id)
        player.voice_client = voice_client

        async with ctx.typing():
            # SOLUCIÓN 4006: Ejecutamos la red de forma asíncrona en otro hilo (to_thread)
            track = await asyncio.to_thread(self.youtube_service.extract_track, query, ctx.author.id)
            
            if not track:
                return await ctx.send("No se pudo obtener información de la canción. Revisa la URL.")

            player.add_to_queue(track)
            
            if not voice_client.is_playing() and not voice_client.is_paused():
                await player.play_next(ctx)
            else:
                await ctx.send(f"🎵 Añadido a la cola: **{track.title}** (Posición: {len(player.queue)})")

    @commands.command()
    async def skip(self, ctx):
        metrics.increment('bot.command.usage', tags=['command:skip'])
        player = self.player_manager.get_player(ctx.guild.id)
        
        if player.voice_client and (player.voice_client.is_playing() or player.voice_client.is_paused()):
            player.voice_client.stop()
            await ctx.send("⏭️ Saltando a la siguiente canción...")
        else:
            await ctx.send("No hay nada reproduciéndose para saltar.")

    @commands.command()
    async def loop(self, ctx):
        player = self.player_manager.get_player(ctx.guild.id)
        player.loop_enabled = not player.loop_enabled
        status = "🔂 Activado" if player.loop_enabled else "🔂 Desactivado"
        await ctx.send(f"Modo loop {status}.")

    @commands.command()
    async def stop(self, ctx):
        player = self.player_manager.get_player(ctx.guild.id)
        if player.voice_client:
            player.clear()
            if player.voice_client.is_playing() or player.voice_client.is_paused():
                player.voice_client.stop()
            await player.voice_client.disconnect()
            self.player_manager.remove_player(ctx.guild.id)
            await ctx.send("⏹️ Reproducción detenida y desconectado.")

    @commands.command()
    async def queue(self, ctx):
        player = self.player_manager.get_player(ctx.guild.id)
        if not player.queue:
            return await ctx.send("La cola está vacía.")

        queue_list = [f"{i + 1}. {track.title}" for i, track in enumerate(player.queue[:10])]
        response = "📜 **Cola de reproducción:**\n" + "\n".join(queue_list)
        if len(player.queue) > 10:
            response += f"\n\n...y {len(player.queue) - 10} más."
            
        await ctx.send(response)