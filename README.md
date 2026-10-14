# Enterprise Discord Music Bot 

Bot de música profesional para Discord diseñado bajo principios **SOLID**, arquitectura modular en capas, soporte multi-servidor (multitenancy), contenedorización con **Docker** e integración nativa de observabilidad con **Datadog**.

## Arquitectura y Patrones Aplicados
* **Clean Architecture / Modular:** Separación estricta entre la interfaz de usuario (Discord Cogs), la lógica de negocio (Core) y los servicios externos (YouTube/Datadog).
* **Principios SOLID:** Aplicación de Responsabilidad Única (SRP) y Abierto/Cerrado (OCP) mediante modelos de datos desacoplados.
* **Observabilidad:** Métricas en tiempo real enviadas a Datadog (latencias de extracción, errores, uso activo).
* **Escalabilidad:** Aislamiento de estado por cada servidor de Discord (`GuildPlayer`).

## Stack Tecnológico
* Python 3.11
* Discord.py
* yt-dlp & FFmpeg
* Datadog (DogStatsD)
* Docker

## Configuración y Ejecución Local
1. Clona el repositorio.
2. Crea un archivo `.env` basado en `.env.example` e introduce tu `DISCORD_TOKEN`.
3. Instala las dependencias: `pip install -r requirements.txt`
4. Ejecuta el bot: `python main.py`

## Ejecución con Docker
```bash
docker build -t discord-music-bot .
docker run -d --env-file .env discord-music-bot