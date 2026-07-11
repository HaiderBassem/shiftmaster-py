"""
Structured JSON logging configuration using structlog.

All log output is JSON by default (production-ready).
In development (SERVER_ENV=development), logs are rendered as colourised
key-value pairs so they're easier to read in a terminal.

Usage
-----
    logger = get_logger(__name__)
    logger.info("employee.login", employee_id=str(emp_id), ip=request.client.host)

The Correlation ID injected by `asgi-correlation-id` middleware is
automatically included in every log record via the stdlib logging integration.
"""

import logging
import sys
import structlog


def configure_logging(dev_mode: bool = False) -> None:
    """
    Call once at application startup (inside lifespan or top of main.py).

    Parameters
    ----------
    dev_mode:
        When True, renders logs as colourised console output.
        When False (default / production), renders as JSON lines.
    """

    # ── Shared processors (run in every environment) ──────────────────────
    shared_processors: list[structlog.types.Processor] = [
        # Inject stdlib log level as "level" key
        structlog.stdlib.add_log_level,
        # Inject logger name as "logger" key
        structlog.stdlib.add_logger_name,
        # Inject ISO-8601 timestamp
        structlog.processors.TimeStamper(fmt="iso"),
        # Render exception tracebacks as a structured dict
        structlog.processors.format_exc_info,
        # Include any context vars (e.g. correlation_id) in all records
        structlog.contextvars.merge_contextvars,
    ]

    if dev_mode:
        # Pretty colourised output for local development
        renderer: structlog.types.Processor = structlog.dev.ConsoleRenderer(colors=True)
    else:
        # JSON output for production / log aggregators (Loki, ELK, Datadog…)
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=shared_processors + [
            # Prepare event_dict for the final renderer
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        # These are run ONLY for records that come from stdlib logging
        foreign_pre_chain=shared_processors,
        processor=renderer,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(logging.INFO)

    # Silence noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("psycopg.pool").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Return a structlog logger bound to *name*."""
    return structlog.get_logger(name)
