import json
from typing import Callable

from json_utils import extract_json_object


def call_json(model_call_fn: Callable[[str, str], str], system_prompt: str, input_obj: dict) -> dict:
    """
    Call an LLM that is expected to return JSON and guard the parsing.

    Args:
        model_call_fn: Callable that accepts (system_prompt, user_prompt) and returns raw string content.
        system_prompt: The system prompt to send to the model.
        input_obj: Input payload that will be serialized to JSON for the user message.

    Returns:
        Parsed JSON object as a dict.

    Raises:
        ValueError: If the model call or JSON extraction fails. The error message includes
            a raw_head excerpt when available.
    """

    raw = None
    try:
        user_prompt = json.dumps(input_obj, ensure_ascii=False)
        raw = model_call_fn(system_prompt, user_prompt)
        return extract_json_object(raw)
    except Exception as err:  # noqa: BLE001
        raw_head = repr(raw[:500]) if isinstance(raw, str) else None
        message = f"Model JSON call failed: {err}"
        if raw_head:
            message = f"{message} | raw_head={raw_head}"
        exc = ValueError(message)
        exc.raw = raw  # type: ignore[attr-defined]
        exc.raw_head = raw_head  # type: ignore[attr-defined]
        raise exc from err
