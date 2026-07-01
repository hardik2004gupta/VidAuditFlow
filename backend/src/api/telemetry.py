"""Azure Monitor OpenTelemetry setup.

Reads its connection string from ``core.config.settings`` (never directly
from ``os.getenv``) and degrades gracefully -- a missing/invalid connection
string disables telemetry rather than crashing the app.
"""

from azure.monitor.opentelemetry import configure_azure_monitor

from backend.src.core.config import settings
from backend.src.core.logging import get_logger

logger = get_logger(__name__)


def setup_telemetry() -> None:
    """Enable Azure Monitor OpenTelemetry instrumentation, if configured.

    Automatically instruments FastAPI request/response tracking, logging,
    and outbound dependency calls once enabled. No-ops (with a warning) if
    ``APPLICATIONINSIGHTS_CONNECTION_STRING`` is not set.
    """
    connection_string = settings.applicationinsights_connection_string

    if not connection_string:
        logger.warning("No Application Insights connection string found; telemetry is disabled.")
        return

    try:
        configure_azure_monitor(
            connection_string=connection_string,
            logger_name="vidauditflow",
        )
        logger.info("Azure Monitor telemetry enabled.")
    except Exception:
        logger.exception("Failed to initialize Azure Monitor telemetry.")
        # Telemetry failing to initialize must never crash the app.
