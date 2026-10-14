"""
Servicio de métricas con patrón Null Object.

Si Datadog está configurado y corriendo, las métricas se envían normalmente.
Si no lo está, todas las llamadas se ignoran silenciosamente sin afectar
el funcionamiento del bot.

Principio SOLID aplicado: Dependency Inversion — los módulos del bot
dependen de esta abstracción, no directamente de `datadog.statsd`.
"""

import logging

logger = logging.getLogger(__name__)


class _NullMetrics:
    """Implementación Null Object: acepta cualquier llamada y no hace nada."""

    def __getattr__(self, _name):
        return lambda *args, **kwargs: None


def _create_metrics_client():
    """Intenta crear el cliente real de Datadog; si falla, retorna el Null Object."""
    try:
        from datadog import statsd
        # Verificación rápida: si el módulo carga, lo usamos.
        # statsd envía por UDP así que no lanza error si el agente no está,
        # pero si la importación falla, usamos el Null Object.
        return statsd
    except ImportError:
        logger.info("Datadog no instalado. Las métricas están deshabilitadas.")
        return _NullMetrics()
    except Exception as e:
        logger.warning("No se pudo inicializar Datadog: %s. Las métricas están deshabilitadas.", e)
        return _NullMetrics()


metrics = _create_metrics_client()
