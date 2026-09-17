

# Chapter 4: json_call

Sends a prompt to an AI and repeatedly tries to parse the response into clean JSON, adding gentle reminders on retries if the output is incomplete. It works like a quality control inspector who keeps sending back a poorly filled form until every required box is properly checked.

`json_call` sits on top of `[call_llm](02_call_llm.md)` and adds a retry loop specifically for structured extraction. LLMs are probabilistic; sometimes they hallucinate a field, truncate the output, or wrap JSON in conversational filler. `json_call` catches these failures, appends a nudging "tail" to the prompt, and tries again. Because the tail changes the prompt string, it also busts the cache in `[call_llm](02_call_llm.md)`, ensuring the model generates a fresh response rather than replaying the cached failure.

## What you will touch in week one
You'll spend most of your time inside `llm.py`, specifically `json_call()`, `parse_json()`, and the `normalize` callbacks you write in your nodes. Your day-to-day will involve:
- Writing `normalize` functions that validate the shape of extracted JSON and raise `KeyError` for missing fields, triggering automatic retries.
- Tuning the `retries` parameter or customizing the retry tail text when `[fill](03_fill.md)` prompts produce complex schemas that models struggle with.
- Debugging `parse_json` edge cases where the model returns multiple JSON blocks or markdown artifacts that confuse the decoder.
- Ensuring your nodes handle the case where `json_call` exhausts retries and raises, falling back gracefully instead of crashing the pipeline.

## What to avoid
- **Don't remove or staticize the retry tail.** The tail (`\n\nReturn COMPLETE JSON... (retry {k})`) serves two critical purposes: it nudges the model, and it changes the prompt string to bust the cache in `[call_llm](02_call_llm.md)`. If you make the tail identical across retries, `json_call` will loop forever on a cached bad response.
- **Don't catch `KeyError` inside `normalize`.** `json_call` relies on `KeyError` bubbling up to detect missing fields. If you silence it in your normalization logic, the retry loop won't trigger, and you'll get partial data without a second chance to fix it.
- **Never mutate the `prompt` argument inside `json_call`.** The function appends the tail to a new string; it never modifies the input. If you wrap `json_call` and mutate the prompt passed in, you may corrupt calls from `[OverviewNode](05_overviewnode.md)` or other consumers that reuse the same prompt object.
- **Don't rely on `parse_json` for streaming.** `json_call` waits for the full response before parsing. It is not designed for incremental processing. Use it for batch extraction where the full context is available.
- **Avoid passing huge payloads to `normalize`.** While `json_call` handles the parsing, your `normalize` function should be lightweight. Heavy transformations or secondary API calls inside `normalize` will slow down the retry loop and increase latency on every attempt.

## Commands you need to know
Drop these into your terminal to verify behavior before committing:
```bash
# Smoke test json_call with a simple prompt
python -c "
from utils.llm import json_call
result = json_call(
    'Reply with JSON: {\"status\": \"ok\"}',
    normalize=lambda d: d,
    retries=2
)
print(result)
"

# Test parse_json robustness against markdown fences
python -c "
from utils.llm import parse_json
# Should extract the object even with surrounding text
text = 'Here is the data:\n```json\n{\"key\": \"value\", \"nested\": {1}}\n```\nHope this helps!'
print(parse_json(text))
"

# Verify cache busting on retries (requires cache enabled)
# Run this twice; second run should hit cache if no retries occur
LLM_CACHE=1 python -c "
from utils.llm import json_call
import time
start = time.time()
try:
    # This will retry and cache each variation
    json_call('Give me {bad}', lambda x: x['missing_key'], retries=2)
except AssertionError:
    print(f'Failed in {time.time()-start:.2f}s')
"

# Clear cache to force fresh retries during development
rm -rf utils/.cache

# Test with cache disabled to see real retry behavior
LLM_CACHE=0 python -c "
from utils.llm import json_call
try:
    json_call('Return JSON', lambda d: d['x'], retries=3)
except AssertionError as e:
    print(e)
"
```

## Conventions that will trip you up
- **`parse_json` returns the *first* complete JSON value.** It uses `json.JSONDecoder().raw_decode()` which stops at the first valid object. If the model outputs multiple JSON blocks, `parse_json` grabs the first one and ignores the rest. Your `normalize` function must handle this; it won't see subsequent blocks.
- **Retry tails affect cache keys.** Every retry appends a unique suffix including the retry count. This means a successful extraction on retry 2 creates a cache entry for `prompt + tail2`. If you later run with `retries=1`, you'll miss that cache. This is intentional; the cache key includes the retry state to ensure consistency.
- **`normalize` is your contract with the node.** `json_call` doesn't know what your data should look like. The `normalize` function defines the schema validation. If `normalize` succeeds, the data is good. If it raises, `json_call` retries. Use this to enforce strict typing or required keys.
- **Network errors are not caught.** `json_call` only catches parsing and normalization errors. Network timeouts, rate limits, and API failures bubble up to the node level. Rely on the node's `max_retries` and `wait` parameters for transient infrastructure issues.
- **Prompts must request JSON explicitly.** `json_call` doesn't inject instructions; it assumes the prompt already asks for JSON. Always use `[fill](03_fill.md)` to include JSON schema examples or explicit instructions in the prompt before passing it to `json_call`.

## Who to ask
- **JSON schema design & model compliance:** Ping `@prompt-engineering`. They know which models reliably output nested JSON and how to structure prompts to minimize retry rates.
- **Parser bugs & `raw_decode` behavior:** Ask `@tooling-llm`. They maintain `parse_json` and can help debug edge cases where models return malformed or truncated JSON.
- **Retry logic & cache interaction:** Loop in `@infrastructure`. They understand the cache key contract and can advise if your retry tails are causing unexpected cache fragmentation.
- **Node integration:** If `json_call` failures are breaking `[OverviewNode](05_overviewnode.md)` or downstream flows, check with `@prompt-engineering` to ensure your normalization logic aligns with the expected data shape.

## Your first ticket
**Title:** Add context-aware retry tails for missing keys  
**Scope:** Update `json_call` to inspect `KeyError` exceptions and include the missing key name in the retry tail. For example, if `normalize` raises `KeyError: 'author'`, the retry tail should become `\n\nReturn COMPLETE JSON with every required top-level field. Specifically, include the missing key: author. (retry {k})`. This helps the model fix specific omissions rather than guessing what was wrong. Implement this in `llm.py`, update the docstring, and write a test that verifies the tail includes the key name when a `KeyError` occurs.  
**Risk:** Low. The change only affects the retry tail string, which is already designed to vary. It improves the signal sent to the model and does not alter cache keys beyond the existing retry count variation. No downstream contracts are affected.  
**Deadline:** Ship by Friday. Once merged, you'll have enhanced the resilience of our structured extraction, learned how retry tails interact with cache keys, and seen exactly how `json_call` turns parser failures into actionable feedback. Next week, you'll step into `[OverviewNode](05_overviewnode.md)` to see how these structured results power the final documentation.