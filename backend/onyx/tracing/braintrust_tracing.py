import os
from typing import Any
from typing import Dict

import braintrust
from agents import set_trace_processors
from braintrust.wrappers.openai import BraintrustTracingProcessor
from braintrust_langchain import set_global_handler
from braintrust_langchain.callbacks import BraintrustCallbackHandler

from onyx.configs.app_configs import BRAINTRUST_API_KEY
from onyx.configs.app_configs import BRAINTRUST_PROJECT
from onyx.utils.logger import setup_logger
from shared_configs.contextvars import CURRENT_TENANT_ID_CONTEXTVAR
from shared_configs.contextvars import ONYX_REQUEST_ID_CONTEXTVAR

logger = setup_logger()

MASKING_LENGTH = int(os.environ.get("BRAINTRUST_MASKING_LENGTH", "20000"))

# Module-level Braintrust logger handle; set during setup if creds present
BRAINTRUST_LOGGER: Any | None = None


def _truncate_str(s: str) -> str:
    tail = MASKING_LENGTH // 5
    head = MASKING_LENGTH - tail
    return f"{s[:head]}…{s[-tail:]}[TRUNCATED {len(s)} chars to {MASKING_LENGTH}]"


def _mask(data: Any) -> Any:
    """Mask data if it exceeds the maximum length threshold or contains private_key."""
    # Handle dictionaries recursively
    if isinstance(data, dict):
        masked_dict = {}
        for key, value in data.items():
            if isinstance(key, str) and "private_key" in key.lower():
                masked_dict[key] = "***REDACTED***"
            else:
                masked_dict[key] = _mask(value)
        return masked_dict

    # Handle lists recursively
    if isinstance(data, list):
        return [_mask(item) for item in data]

    # Handle strings
    if isinstance(data, str):
        # Mask the value if the key was "private_key" (handled in dict above)
        # Also check for private_key patterns in the string content
        if "private_key" in data.lower():
            return "***REDACTED***"
        if len(data) <= MASKING_LENGTH:
            return data
        return _truncate_str(data)

    # For other types, check length
    if len(str(data)) <= MASKING_LENGTH:
        return data
    return _truncate_str(str(data))


def setup_braintrust_if_creds_available() -> None:
    """Initialize Braintrust logger and set up global callback handler."""
    # Check if Braintrust API key is available
    if not BRAINTRUST_API_KEY:
        logger.info("Braintrust API key not provided, skipping Braintrust setup")
        return

    braintrust_logger = braintrust.init_logger(
        project=BRAINTRUST_PROJECT,
        api_key=BRAINTRUST_API_KEY,
    )
    braintrust.set_masking_function(_mask)
    handler = BraintrustCallbackHandler()
    set_global_handler(handler)
    set_trace_processors([BraintrustTracingProcessor(braintrust_logger)])
    logger.notice("Braintrust tracing initialized")

    # Expose as module-level logger for ad-hoc logging helpers
    global BRAINTRUST_LOGGER
    BRAINTRUST_LOGGER = braintrust_logger


def _with_context(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Attach tenant/request context to metadata."""
    # Best-effort: do not raise if context is missing
    try:
        tenant_id = CURRENT_TENANT_ID_CONTEXTVAR.get()
    except Exception:
        tenant_id = None

    try:
        onyx_request_id = ONYX_REQUEST_ID_CONTEXTVAR.get()
    except Exception:
        onyx_request_id = None

    enriched: Dict[str, Any] = {
        **metadata,
        "tenant_id": tenant_id,
        "onyx_request_id": onyx_request_id,
    }
    return enriched


def log_braintrust_usage(event_name: str, metadata: Dict[str, Any]) -> None:
    """Log a lightweight usage event to Braintrust if configured.

    No-ops safely if Braintrust is not initialized. Exceptions are swallowed to
    avoid impacting request flow.
    """
    try:
        if not BRAINTRUST_LOGGER:
            return

        # Some Braintrust logger implementations expose `.log(name, data=...)`
        # Fallbacks are ignored to stay safe in various environments.
        payload = _with_context(metadata)
        # If spans are enabled, prefer span-based logging
        if hasattr(BRAINTRUST_LOGGER, "start_span"):
            span = None
            try:
                # type: ignore[attr-defined]
                span = BRAINTRUST_LOGGER.start_span(
                    event_name, metadata=payload
                )  # pyright: ignore
            except TypeError:
                try:
                    # Fallback: start span without metadata, log metadata below
                    span = BRAINTRUST_LOGGER.start_span(event_name)
                except Exception:
                    span = None

            if span is not None:
                try:
                    # Prefer single-arg payload; fallback to (event, payload)
                    if hasattr(span, "log"):
                        try:
                            span.log(payload)
                        except TypeError:
                            try:
                                span.log("usage", payload)
                            except Exception:
                                pass
                finally:
                    try:
                        if hasattr(span, "end"):
                            span.end()
                        elif hasattr(span, "finish"):
                            span.finish()
                    except Exception:
                        pass
                return

        # Fallback to toplevel log if spans are not available
        if hasattr(BRAINTRUST_LOGGER, "log"):
            try:
                BRAINTRUST_LOGGER.log(event_name, payload)
            except TypeError:
                try:
                    BRAINTRUST_LOGGER.log(event_name, **payload)
                except Exception:
                    pass
        else:
            logger.debug("Braintrust logger has no .log method; skipping usage event")
    except Exception:
        # Swallow errors; tracing must never break application flow
        pass
