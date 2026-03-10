import httpx
import json
from backend.utils.logger import log, log_action, log_error

# Shared async client — created once, reused across calls
_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0))
    return _client


async def chat_completion(
    base_url: str,
    model: str,
    messages: list[dict],
    max_tokens: int = 4096,
    temperature: float = 0.2,
) -> str:
    """
    Call LM Studio's OpenAI-compatible /v1/chat/completions endpoint.

    Args:
        base_url: LM Studio API base URL (e.g. http://localhost:1234/v1)
        model: Model ID string
        messages: List of {"role": ..., "content": ...} dicts
        max_tokens: Max tokens in response
        temperature: Sampling temperature

    Returns:
        The assistant's response content string.
    """
    url = f"{base_url}/chat/completions"
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    log_action("llm_call", f"POST {url}", {"model": model, "message_count": len(messages)})

    client = _get_client()
    try:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"].strip()
        log_action("llm_response", f"Received {len(content)} chars from {model}")
        return content
    except httpx.ConnectError:
        msg = f"Cannot connect to LM Studio at {base_url}"
        log_error("llm_call", msg)
        raise ConnectionError(msg)
    except httpx.HTTPStatusError as e:
        msg = f"LM Studio returned {e.response.status_code}: {e.response.text[:200]}"
        log_error("llm_call", msg)
        raise RuntimeError(msg)
    except Exception as e:
        log_error("llm_call", str(e))
        raise


async def close_client():
    """Shutdown the shared httpx client (call on app shutdown)."""
    global _client
    if _client and not _client.is_closed:
        await _client.aclose()
        _client = None
