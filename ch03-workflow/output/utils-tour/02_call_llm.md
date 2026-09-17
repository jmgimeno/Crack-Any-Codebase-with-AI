

# Chapter 2: call_llm

Acts as a universal remote control for different AI models, automatically picking the right provider based on environment variables while saving past answers to disk. It’s like a translation agency that routes your request to the best available translator and keeps a filing cabinet of previous conversations.

## What you will touch in week one
You’ll spend most of your time inside `call_llm.py`, specifically `_pick()`, `_model_for()`, and the cache helpers (`_cache_get`/`_cache_put`). Your day-to-day will involve:
- Tweaking `LLM_MAX_OUTPUT_TOKENS` or per-provider model defaults when `[crawl](01_crawl.md)` dumps exceed the default context window.
- Verifying cache hit/miss ratios when iterating on prompt templates passed through `[fill](03_fill.md)`.
- Adding or swapping provider dispatch logic if the team onboards a new inference endpoint.
- Inspecting `utils/.cache/` to ensure deterministic keys aren't causing stale responses in `[json_call](04_json_call.md)` or `[OverviewNode](05_overviewnode.md)`.

## What to avoid
- **Don’t mutate the cache key format.** The SHA256 hash of `provider|model|prompt` is the contract that makes `[json_call](04_json_call.md)` retries cheap. Changing the delimiter or hashing strategy will silently invalidate thousands of cached responses.
- **Don’t mix `max_tokens` and `max_completion_tokens`.** OpenAI’s GPT-5-class models reject the legacy param; Anthropic and Gemini require it. The provider blocks already split this correctly. Hardcoding one name across the board will crash half your test suite.
- **Never hardcode API keys or model names.** Always route through the environment variables. The auto-pick logic in `_pick()` is the single source of truth for routing.
- **Don’t bypass `LLM_CACHE=0`.** The cache is the only thing keeping local iteration costs near zero. Disabling it for “quick tests” will trigger rate limits and burn through daily budgets.

## Commands you need to know
Drop these into your terminal to verify behavior before committing:
```bash
# Smoke test: verify provider routing and basic cache write
python -m utils.call_llm

# Clear the on-disk cache (safe, recreates on next run)
rm -rf utils/.cache

# Run with cache disabled to force live model calls
LLM_CACHE=0 python -c "from utils.call_llm import call_llm; print(call_llm('Say yes')[:20])"

# Override provider explicitly and check which model gets picked
LLM_PROVIDER=anthropic python -c "
from utils.call_llm import _pick, _model_for
print(f'Provider: {_pick()} | Model: {_model_for(_pick())}')
"

# Inspect cache size and file count without parsing JSON
find utils/.cache -type f -name '*.json' | wc -l
du -sh utils/.cache
```

## Conventions that will trip you up
- **Cache keys are prompt-strict.** A single trailing space or newline difference in a string passed from `[fill](03_fill.md)` creates a brand-new cache miss. Always `strip()` or normalize inputs before calling `call_llm()`.
- **Environment variable precedence is strict.** `LLM_PROVIDER` overrides everything. If it’s absent, the first available API key wins in this order: Anthropic → OpenAI → Gemini → OpenAI-like. Silent fallbacks cause hard-to-trace cost shifts.
- **Output token caps are global by default.** `LLM_MAX_OUTPUT_TOKENS` defaults to `16384`. If you pass a massive `[crawl](01_crawl.md)` dump and the model truncates mid-sentence, `[json_call](04_json_call.md)` will fail to parse and exhaust retries. Bump the env var per-run rather than patching the default.
- **`call_image()` intentionally skips caching.** Images are large, unique per prompt, and stored externally or on-disk via `output_path`. The cache bypass is deliberate; don’t wrap it in `_cache_get`/`_cache_put`.
- **OpenAI-like endpoints require a base URL.** `OPENAI_LIKE_API_BASE_URL` defaults to the internal proxy. If you point it at a public provider without setting it, the SDK will 404 silently until timeout.

## Who to ask
- **Provider routing & API credentials:** Ping `@infrastructure`. They manage key rotation, rate limits, and cost dashboards for each model tier.
- **Cache behavior & disk I/O:** Ask the `@tooling-llm` channel. They own the cache lifecycle, eviction strategies, and ensure `utils/.cache/` doesn’t balloon on CI runners.
- **Token budgets & prompt formatting:** Loop in `@prompt-engineering`. They know exactly how `[fill](03_fill.md)` templates interact with context windows and why `[json_call](04_json_call.md)` retries sometimes need a nudged prompt tail.

## Your first ticket
**Title:** Add explicit fallback chain for per-provider output token limits  
**Scope:** Extend `call_llm()` to read `ANTHROPIC_MAX_OUTPUT_TOKENS`, `OPENAI_MAX_OUTPUT_TOKENS`, `GEMINI_MAX_OUTPUT_TOKENS`, and `OPENAI_LIKE_MAX_OUTPUT_TOKENS` before falling back to the global `LLM_MAX_OUTPUT_TOKENS`. Update the module docstring with the new variables. Write a two-line test that verifies a per-provider override applies without affecting other branches.  
**Risk:** Low. Backwards-compatible fallback chain. No cache key changes, no parser shifts.  
**Deadline:** Ship by Friday. Once merged, you’ll have touched the routing layer, verified token caps against `[crawl](01_crawl.md)` outputs, and learned exactly how this repo prevents silent truncation downstream. Next week, you’ll step into `[fill](03_fill.md)` to see how raw text becomes structured prompts.