"""
Punto de entrada principal del bot de Discord.

Configura el entorno, inicializa dependencias opcionales (Datadog),
y lanza el bot.
"""

import os
import logging

import discord
from discord.ext import commands
from dotenv import load_dotenv

from core.player_manager import PlayerManager
from cogs.music_cog import MusicCog
from services.metrics import metrics

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
)
logger = logging.getLogger(__name__)

# 1. Carga de Variables de Entorno
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# 2. Inicialización opcional de Datadog
dd_api_key = os.getenv('DD_API_KEY')
if dd_api_key:
    try:
        from datadog import initialize
        initialize(
            statsd_host='127.0.0.1',
            statsd_port=8125,
            api_key=dd_api_key,
            app_key=os.getenv('DD_APP_KEY'),
        )
        logger.info("Datadog inicializado correctamente.")
    except ImportError:
        logger.info("Paquete datadog no instalado. Métricas deshabilitadas.")
    except Exception as e:
        logger.warning("Error inicializando Datadog: %s. Métricas deshabilitadas.", e)
else:
    logger.info("DD_API_KEY no configurada. Métricas deshabilitadas.")


# 3. Configuración del Bot
class EnterpriseBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True
        super().__init__(command_prefix='.', intents=intents)

        # Inyección de dependencias (Singleton)
        self.player_manager = PlayerManager(self)

    async def setup_hook(self):
        # Inyectamos el manager al inicializar el Cog
        await self.add_cog(MusicCog(self, self.player_manager))

        logger.info("Sincronizando comandos slash...")
        try:
            await self.tree.sync()
            logger.info("Comandos slash sincronizados.")
        except Exception as e:
            logger.error("Error al sincronizar comandos slash: %s", e)

    async def on_ready(self):
        logger.info("Bot conectado y listo como %s", self.user)
        metrics.increment('bot.system.startup')


if __name__ == '__main__':
    if not TOKEN:
        raise ValueError(
            "Error crítico: DISCORD_TOKEN no encontrado en las variables de entorno. "
            "Asegúrate de tener un archivo .env con DISCORD_TOKEN configurado."
        )

    bot = EnterpriseBot()
    bot.run(TOKEN)