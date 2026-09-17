

# Chapter 3: fill

Safely inserts variables into text templates without breaking existing code examples or formatting that accidentally contain curly braces. Imagine a mail-merge tool specifically designed for developers, where it only replaces carefully labeled placeholders while leaving all other symbols completely untouched.

This module is the bridge between raw data and LLM prompts. It takes the concatenated source code from `[crawl](01_crawl.md)` and other context, injects it into prompt templates, and passes the result to `[call_llm](02_call_llm.md)`. Because our prompts frequently contain JSON schemas, Mermaid diagrams, and code snippets with literal `{ }`, standard Python formatting would destroy the prompt structure. `fill` solves this by performing targeted string replacement that respects the integrity of the template.

## What you will touch in week one
You’ll spend most of your time inside `llm.py`, specifically the `fill()` function and `read_prompt()` helper. You'll also be editing prompt templates and the nodes that compose them. Your day-to-day will involve:
- Adding new placeholders to prompts when `[OverviewNode](05_overviewnode.md)` or `[json_call](04_json_call.md)` nodes need extra context.
- Verifying that values injected from `[crawl](01_crawl.md)` (which may contain massive blocks of code with braces) land cleanly inside templates without corrupting JSON examples.
- Debugging prompt templates that fail `[call_llm](02_call_llm.md)` cache keys due to invisible whitespace or formatting drift introduced during filling.
- Writing tests that assert `fill` preserves literal braces in complex payloads.

## What to avoid
- **Never use `str.format()` or f-strings on prompts.** Prompts contain JSON examples like `{ "role": "user" }`. Using `.format()` will raise `KeyError` or replace unintended braces. `fill` is the *only* allowed interpolation method.
- **Don't create overlapping placeholder keys.** `fill` uses simple `str.replace`. If a template contains `{ctx}` and `{context}`, calling `fill(t, ctx="X")` will turn `{context}` into `Xtext`. Keys must be unique and non-prefixing.
- **Don't embed placeholder patterns in values.** `fill` iterates sequentially. If you pass `fill(t, code="{secret}", secret="leak")`, the value for `code` contains `{secret}`, which will be replaced in the next iteration, resulting in `code` becoming `"leak"`. Values must be final strings; they cannot contain `{...}` patterns matching other keys.
- **Don't mutate templates in-place.** `fill` returns a new string. Modifying the template reference passed to `fill` can cause shared template objects to become corrupted across concurrent node executions.
- **Don't hardcode `[crawl](01_crawl.md)` output size.** While `fill` itself doesn't cap size, injecting massive crawls into templates can blow the context window before `[call_llm](02_call_llm.md)` even sees the prompt. Always summarize or truncate context at the source, not inside `fill`.

## Commands you need to know
Drop these into your terminal to verify behavior before committing:
```bash
# Verify fill preserves JSON braces in templates
python -c "
from utils.llm import fill
t = 'Example JSON: {data}\nAnother block: { \"key\": 1 }'
print(fill(t, data='{\"id\": 123}'))
"

# Demonstrate the overlapping key risk (this will corrupt {context})
python -c "
from utils.llm import fill
t = 'Short: {ctx}\nLong: {context}'
print(fill(t, ctx='X'))  # Output: 'Short: X\nLong: Xtext' <- BROKEN
"

# Verify value injection safety (values must not contain other keys)
python -c "
from utils.llm import fill
t = 'Code: {code}'
# This is SAFE: value contains braces but no matching keys
print(fill(t, code='{print(\"hello\")}'))  
"

# Smoke test read_prompt integration
python -c "
from utils.llm import read_prompt, fill
# Assumes a test prompt exists; adjust path if needed
# print(read_prompt('prompts', 'test.txt'))
"

# Check how fill interacts with crawl output containing braces
python -c "
from utils.crawl import crawl
from utils.llm import fill
# Simulate filling crawl output into a template
code = crawl('.', keep_ext={'README.md'})
t = 'Context:\n{code}'
result = fill(t, code=code[:500])
print(f'Filled length: {len(result)}')
assert '{' in result and '}' in result, 'Braces should survive fill'
"
```

## Conventions that will trip you up
- **Placeholders use single braces `{key}`.** Unlike Jinja2 or some templating engines, we do not use `{{key}}`. The prompt files are "clean copies" that developers can read directly. Using `{{ }}` would render double braces in the final prompt, confusing the LLM.
- **Key naming must be unique and isolated.** Never use keys that are substrings of other keys. Good: `{code}`, `{context}`, `{user_query}`. Bad: `{code}`, `{code_snippet}`. The team convention is to use distinct words or clear delimiters that don't nest.
- **Prompts live in `prompts/` and are versioned.** Never generate prompt text dynamically in nodes. Always load via `read_prompt()` and fill via `fill()`. This ensures prompts are reviewable, cacheable by `[call_llm](02_call_llm.md)`, and consistent across `[json_call](04_json_call.md)` retries.
- **`fill` does not escape values.** If a value contains newlines, quotes, or special characters, they are injected as-is. It is the caller's responsibility to ensure values are safe for the prompt context. `[crawl](01_crawl.md)` outputs are raw text; they may contain characters that need sanitization depending on the prompt structure.
- **Cache sensitivity.** `[call_llm](02_call_llm.md)` caches based on the exact prompt string. If `fill` introduces a trailing newline or variable difference, the cache misses. Always `strip()` or normalize values before passing to `fill` to ensure deterministic prompts.

## Who to ask
- **Prompt design & template structure:** Ping `@prompt-engineering`. They own the prompt library, define placeholder conventions, and ensure templates interact correctly with model constraints.
- **Template bugs & `fill` behavior:** Ask `@tooling-llm`. They maintain `llm.py` and can help debug edge cases like value injection or brace preservation.
- **Context integration:** If your prompt uses output from `[crawl](01_crawl.md)`, loop in `@infrastructure`. They understand the size and structure of crawl dumps and can advise on truncation or formatting to keep prompts within token budgets.
- **Downstream parsing:** If `fill` output breaks `[json_call](04_json_call.md)` or `[OverviewNode](05_overviewnode.md)` parsing, check with `@prompt-engineering` to ensure the filled prompt still elicits the expected structured response format.

## Your first ticket
**Title:** Add `detect_fill_collisions()` helper to `llm.py`  
**Scope:** Implement a utility function `detect_fill_collisions(template: str, keys: dict) -> list[str]` that scans a template for all `{...}` patterns and warns if any key is a substring of another key. For example, if keys contain `{'ctx': ..., 'context': ...}`, the function should return a warning. Integrate this into a test that validates the existing prompt templates against known keys.  
**Risk:** Low. Purely additive diagnostic tool. No changes to `fill` logic or downstream contracts. Helps prevent the class of bugs that break `[json_call](04_json_call.md)` parsing due to corrupted placeholders.  
**Deadline:** Ship by Friday. Once merged, you'll have protected the prompt pipeline from a subtle but critical failure mode, verified your understanding of `fill`'s replacement mechanics, and added a safety net for future prompt authors. Next week, you'll step into `[json_call](04_json_call.md)` to see how filled prompts extract structured data with retries.