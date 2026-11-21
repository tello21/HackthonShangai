"""The one wrapper around the Anthropic SDK used by every AI feature
(query translation and messages).

ask() returns (result, None) on success or (None, reason) when the AI service is
not available, so the UI can say why instead of showing made-up text.
Credentials: ANTHROPIC_API_KEY (env var or Streamlit secrets, passed in with
set_api_key), or any credential the SDK resolves on its own.
Change MODEL here to switch every feature to another model.
"""

import json
import os
import threading

MODEL = "claude-opus-5-5"
_api_key = None

# Credentials the SDK can find on its own besides an explicit key
_CRED_ENV = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_PROFILE",
             "ANTHROPIC_FEDERATION_RULE_ID", "ANTHROPIC_IDENTITY_TOKEN", "ANTHROPIC_IDENTITY_TOKEN_FILE")


def has_credentials():
    """Cheap check before loading the SDK (importing it takes several seconds)."""
    if _api_key or any(os.getenv(v) for v in _CRED_ENV):
        return True
    return os.path.isdir(os.path.join(os.path.expanduser("~"), ".config", "anthropic"))  # `ant auth login`


def set_api_key(key):
    """Set the key; when there are credentials, load the SDK in the background so the
    first AI call doesn't wait for the import."""
    global _api_key
    _api_key = key or None
    if has_credentials():
        threading.Thread(target=lambda: __import__("anthropic"), daemon=True).start()


def ask(system, messages, schema=None, effort="low", max_tokens=8000):
    """One Messages API call. With `schema`, returns the parsed JSON object; otherwise the text."""
    if not has_credentials():
        return None, "no API key configured"
    try:
        import anthropic
    except ImportError:
        return None, "the anthropic package is not installed"
    try:
        client = anthropic.Anthropic(api_key=_api_key) if _api_key else anthropic.Anthropic()
    except Exception as e:
        return None, f"no API credentials ({type(e).__name__})"

    output_config = {"effort": effort}
    if schema:
        output_config["format"] = {"type": "json_schema", "schema": schema}
    params = dict(model=MODEL, max_tokens=max_tokens, system=system, messages=messages,
                  output_config=output_config)
    try:
        try:
            # if the model declines, the API retries the same request on a fallback model
            resp = client.beta.messages.create(
                betas=["server-side-fallback-2026-07-01"], fallbacks="default", **params)
        except (TypeError, anthropic.BadRequestError) as e:
            if "authentication" in str(e).lower():
                raise
            resp = client.messages.create(**params)  # SDK/platform without server-side fallback
    except TypeError as e:
        if "authentication" in str(e).lower():
            return None, "no API key configured"
        return None, f"AI service not available ({type(e).__name__})"
    except anthropic.AuthenticationError:
        return None, "invalid or missing API key"
    except anthropic.RateLimitError:
        return None, "rate limited, try again shortly"
    except anthropic.APIConnectionError:
        return None, "no connection to the AI service"
    except anthropic.APIStatusError as e:
        return None, f"AI service error ({e.status_code})"
    except Exception as e:
        return None, f"AI service not available ({type(e).__name__})"

    if resp.stop_reason == "refusal":
        return None, "the request was declined"
    if resp.stop_reason == "max_tokens":
        return None, "the answer was cut off"
    text = next((b.text for b in resp.content if b.type == "text"), None)
    if not text:
        return None, "empty answer"
    if not schema:
        return text.strip(), None
    try:
        return json.loads(text), None
    except json.JSONDecodeError:
        return None, "unreadable answer"
