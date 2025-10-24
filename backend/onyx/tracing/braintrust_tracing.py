import os
from typing import Any
from typing import Dict

import braintrust
from agents import set_trace_processors
from agents.tracing import Span
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


class TenantContextTracingProcessor(BraintrustTracingProcessor):
    def on_span_end(self, span: Span) -> None:
        current_span = span.current_span()
        current_span.log(metadata={"tenant_id": CURRENT_TENANT_ID_CONTEXTVAR.get()})
        super().on_span_end(span)


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
    set_trace_processors([TenantContextTracingProcessor(braintrust_logger)])
    # set_trace_processors([BraintrustTracingProcessor(braintrust_logger)])
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


def braintrust_log(event_name: str, metadata: Dict[str, Any]) -> None:
    """Log a lightweight usage event to Braintrust if configured.

    No-ops safely if Braintrust is not initialized. Exceptions are swallowed to
    avoid impacting request flow.
    """
    try:
        if not BRAINTRUST_LOGGER:
            return

        # Attach request/tenant context to metadata first
        enriched = _with_context(metadata)

        # Extract token usage into Braintrust "data" payload
        # Prefer canonical prompt/completion names and derive if needed
        prompt_tokens = enriched.get("prompt_tokens")
        if prompt_tokens is None:
            prompt_tokens = enriched.get("input_tokens")

        completion_tokens = enriched.get("completion_tokens")
        if completion_tokens is None:
            completion_tokens = enriched.get("output_tokens")

        total_tokens = enriched.get("total_tokens")
        if (
            total_tokens is None
            and prompt_tokens is not None
            and completion_tokens is not None
        ):
            try:
                total_tokens = int(prompt_tokens) + int(completion_tokens)
            except Exception:
                # Best-effort only; if inputs aren't numeric, skip deriving
                total_tokens = None

        data: Dict[str, Any] = {}
        if prompt_tokens is not None:
            data["prompt_tokens"] = prompt_tokens
        if completion_tokens is not None:
            data["completion_tokens"] = completion_tokens
        if total_tokens is not None:
            data["total_tokens"] = total_tokens

        # Maintain compatibility with any downstream consumers expecting input/output names
        if "prompt_tokens" in data:
            data.setdefault("input_tokens", data["prompt_tokens"])  # alias
        if "completion_tokens" in data:
            data.setdefault("output_tokens", data["completion_tokens"])  # alias

        # Carry through useful flags alongside token data if present
        for k in ("streaming", "is_estimate", "estimate_method"):
            if k in enriched:
                data[k] = enriched[k]

        # Keep other fields as metadata (avoid duplicating token fields)
        token_keys = {
            "prompt_tokens",
            "completion_tokens",
            "total_tokens",
            "input_tokens",
            "output_tokens",
            "streaming",
            "is_estimate",
            "estimate_method",
        }
        meta_only = {k: v for k, v in enriched.items() if k not in token_keys}

        # For legacy callers/tests, also include tenant context in the data payload
        if "tenant_id" in enriched:
            data["tenant_id"] = enriched["tenant_id"]
        if "onyx_request_id" in enriched:
            data["onyx_request_id"] = enriched["onyx_request_id"]

        logger_obj = BRAINTRUST_LOGGER

        # Prefer simple event logging API if available
        if hasattr(logger_obj, "log"):
            # Some implementations expect None for absent payloads
            logger_obj.log(
                event_name, data=(data or None), metadata=(meta_only or None)
            )
            return

        # Fallback to span-based API
        if hasattr(logger_obj, "start_span"):
            with logger_obj.start_span(
                event_name, metadata=(meta_only or None)
            ) as span:
                if data:
                    span.log(data)
            return
    except Exception:
        # Swallow errors; tracing must never break application flow
        pass
