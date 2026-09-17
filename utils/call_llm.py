"""Shared LLM wrapper used by every chapter in this repo.

Picks the provider based on which env var is set:
  ANTHROPIC_API_KEY  -> Claude (claude-sonnet-4-6)
  OPENAI_API_KEY     -> OpenAI (gpt-4o)
  GEMINI_API_KEY     -> Gemini (gemini-2.5-flash)
  OPENAISH_MODEL     -> OpenAI-like (Qwen/Qwen3.8-27b)


Override the auto pick with LLM_PROVIDER=anthropic|openai|gemini|openaish.
Override the model with ANTHROPIC_MODEL / OPENAI_MODEL / GEMINI_MODEL / OPENAISH_MODEL.

Caching:
  Responses are cached on disk under utils/.cache/ keyed by sha256 of
  (provider + model + prompt). The cache survives across runs so iterating on
  downstream code (UI, post processing, README copy) costs nothing.

  Disable with LLM_CACHE=0.
  Clear with: rm -rf utils/.cache

Smoke test:
  python -m utils.call_llm
"""
import hashlib
import json
import os

CACHE_DIR = os.path.join(os.path.dirname(__file__), ".cache")


def _pick():
    p = os.environ.get("LLM_PROVIDER")
    if p:
        return p.lower()
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "anthropic"
    if os.environ.get("OPENAI_API_KEY"):
        return "openai"
    if os.environ.get("GEMINI_API_KEY"):
        return "gemini"
    if os.environ.get("OPENAISH_API_KEY"):
        return "openaish"
    raise RuntimeError(
        "No LLM key set. Export ANTHROPIC_API_KEY or OPENAI_API_KEY or GEMINI_API_KEY. or OPENAISH_API_KEY"
    )


def _model_for(provider):
    # Defaults aim for "good enough quality, low cost" so the chapter examples
    # are cheap to reproduce. Bump to the pro/opus tier if you want the best
    # answers and don't mind the cost.
    #
    # Override per call with ANTHROPIC_MODEL / OPENAI_MODEL / GEMINI_MODEL / OPENAISH_MODEL.
    return {
        "anthropic": os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
        "openai":    os.environ.get("OPENAI_MODEL", "gpt-5.1"),
        "gemini":    os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"),
        "openaish":  os.environ.get("OPENAISH_MODEL", "Qwen/Qwen3.8-27b"),
    }[provider]


def _cache_path(provider, model, prompt):
    key = hashlib.sha256(f"{provider}|{model}|{prompt}".encode("utf-8")).hexdigest()
    return os.path.join(CACHE_DIR, f"{key}.json")


def _cache_get(provider, model, prompt):
    if os.environ.get("LLM_CACHE", "1") == "0":
        return None
    path = _cache_path(provider, model, prompt)
    if not os.path.exists(path):
        return None
    try:
        return json.load(open(path))["response"]
    except (OSError, ValueError, KeyError):
        return None


def _cache_put(provider, model, prompt, response):
    if os.environ.get("LLM_CACHE", "1") == "0":
        return
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = _cache_path(provider, model, prompt)
    json.dump({"provider": provider, "model": model, "response": response},
              open(path, "w"))


def call_llm(prompt: str) -> str:
    provider = _pick()
    model = _model_for(provider)

    cached = _cache_get(provider, model, prompt)
    if cached is not None:
        return cached

    max_out = int(os.environ.get("LLM_MAX_OUTPUT_TOKENS", "16384"))

    if provider == "anthropic":
        from anthropic import Anthropic
        resp = Anthropic().messages.create(
            model=model,
            max_tokens=max_out,
            messages=[{"role": "user", "content": prompt}],
        )
        text = resp.content[0].text

    elif provider == "openai":
        from openai import OpenAI
        # GPT-5-class models (the default here) reject the old `max_tokens` on
        # chat.completions and require `max_completion_tokens`. Every current
        # OpenAI chat model accepts the newer name, so we always use it.
        resp = OpenAI().chat.completions.create(
            model=model,
            max_completion_tokens=max_out,
            messages=[{"role": "user", "content": prompt}],
        )
        text = resp.choices[0].message.content

    elif provider == "gemini":
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        resp = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(max_output_tokens=max_out),
        )
        text = resp.text

    elif provider == "openaish":
        from openai import OpenAI
        base_url = os.environ.get("OPENAISH_API_BASE_URL")
        resp = OpenAI(
            base_url=base_url,
            api_key=os.environ.get("OPENAISH_API_KEY")
        ).chat.completions.create(
            model=model,
            max_completion_tokens=max_out,
            messages=[{"role": "user", "content": prompt}],
        )
        text = resp.choices[0].message.content
    else:
        raise RuntimeError(f"Unknown LLM_PROVIDER={provider!r}")

    _cache_put(provider, model, prompt, text)
    return text

def load_model_if_needed():
    import requests

    endpoint = os.environ.get("OPENAISH_LOAD_MODEL_ENDPOINT")
    if not endpoint:
        return

    api_key = os.environ.get("OPENAISH_API_KEY")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model_path": os.environ.get("OPENAISH_MODEL"),
        "max_seq_length": os.environ.get("OPENAISH_CONTEXT_LENGTH", 1_000_000)
    }

    response = requests.post(endpoint, headers=headers, json=payload, timeout=30)
    response.raise_for_status()  # raises if status is 4xx/5xx

    data = response.json()
    print(data)


def call_image(prompt: str, output_path: str) -> str:
    """Generate an image using Gemini's image model. Saves to output_path. Returns the path.

    Only Gemini is supported for images. Reads GEMINI_API_KEY.
    Cache: results are NOT cached on disk (images are big and unique per prompt).
    """
    from google import genai
    from google.genai import types

    api_key = os.environ.get("GEMINI_API_KEY")
    assert api_key, "GEMINI_API_KEY required for image generation"
    model = os.environ.get("GEMINI_IMAGE_MODEL", "gemini-3.1-flash-image-preview")

    client = genai.Client(api_key=api_key)
    resp = client.models.generate_content(
        model=model,
        contents=[prompt],
        config=types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"]),
    )
    for part in resp.candidates[0].content.parts:
        if getattr(part, "inline_data", None) is not None:
            part.as_image().save(output_path)
            return output_path
    raise RuntimeError(f"Image model returned no image. Prompt was:\n{prompt[:200]}")


if __name__ == "__main__":
    print(call_llm("Reply with the single word: ready"))
