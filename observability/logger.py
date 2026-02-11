import structlog
import logging
import os
import sys
from dotenv import load_dotenv
from langfuse import Langfuse
from datetime import datetime

# Load environment variables
load_dotenv()

# Configure Langfuse
langfuse = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_BASE_URL")
)

def configure_logger():
    """
    Configure structured logging with structlog.
    Outputs JSON logs to current directory for machine parsing,
    and pretty logs to console for dev.
    """
    
    # Configure Structlog Processors
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ]

    structlog.configure(
        processors=processors,
        logger_factory=structlog.PrintLoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        cache_logger_on_first_use=True,
    )

    # Allow standard logging bridge if needed (for libraries that use std logging)
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=logging.INFO)

def log_event(event_name: str, **kwargs):
    """
    Log an event to both Structlog (local) and Langfuse (cloud).
    """
    # Local Log
    logger = structlog.get_logger()
    logger.info(event_name, **kwargs)

    # Cloud Trace (Optional - we might want more granular spans later)
    # For now, just a simple event or span could be useful.
    # But usually Langfuse works with Spans/Traces.
    # We will assume granular tracing happens in the Engine, 
    # this function is for high-level events.
    try:
        langfuse.create_event(
            name=event_name,
            metadata={
                "input": kwargs.get("input", {}),
                **kwargs
            }
        )
    except Exception as e:
        logger.error("langfuse_error", error=str(e))

if __name__ == "__main__":
    configure_logger()
    log_event("Observer_Initialized", status="ready")
