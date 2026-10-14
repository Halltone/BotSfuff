from core.guild_player import GuildPlayer
from services.metrics import metrics

class PlayerManager:
    def __init__(self, bot):
        self.bot = bot
        # Diccionario para almacenar el estado aislado de cada servidor
        self.players: dict[int, GuildPlayer] = {}

    def get_player(self, guild_id: int) -> GuildPlayer:
        """Obtiene el reproductor del servidor, si no existe lo crea."""
        if guild_id not in self.players:
            self.players[guild_id] = GuildPlayer(self.bot, guild_id)
            # Monitoreamos cuántos servidores simultáneos usan el bot
            metrics.gauge('bot.system.total_players', len(self.players))
            
        return self.players[guild_id]

    def remove_player(self, guild_id: int):
        """Limpia el reproductor cuando el bot se desconecta."""
        if guild_id in self.players:
            self.players[guild_id].clear()
            del self.players[guild_id]
            metrics.gauge('bot.system.total_players', len(self.players))