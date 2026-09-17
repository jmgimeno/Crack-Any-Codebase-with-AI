

# Chapter 5: OverviewNode

A reusable workflow step that prepares data, runs the AI to generate page summaries, handles failures gracefully, and stores the results. Think of it as a standardized assembly line station in a factory, consistently turning raw findings into polished introductory text without stopping production if something fails.

## What you will touch in week one
You’ll spend most of your time inside `utils/nodes.py` (the `OverviewNode` class) and `utils/overview.py` (the `write_overview` helper). Your day-to-day will involve:
- Tuning the `_PROMPT` template to adjust tone, density, or section constraints based on how `[crawl](01_crawl.md)` findings are being summarized.
- Mapping upstream analysis results to the `spec(shared)` contract so the node receives `{name, what, sections, facts}` in the expected shape.
- Debugging the regex parser in `write_overview` when the model drifts from the requested `## ` header format.
- Adjusting `max_retries` and `wait` on the node constructor to balance pipeline latency against success rates for large `[call_llm](02_call_llm.md)` prompts.

## What to avoid
- **Do not remove or bypass `exec_fallback`.** It intentionally returns `{"welcome": "", "intros": {}}` on any `exec` failure. Downstream renderers rely on this empty structure to keep the page layout intact. Returning `None` or raising will crash the entire chapter flow.
- **Don’t switch this node to `[json_call](04_json_call.md)`.** `OverviewNode` expects raw markdown output, not structured JSON. The parser explicitly splits on `## ` headers. Forcing JSON extraction will break the regex matcher and require a full pipeline rewrite.
- **Never mutate `shared` outside `post()`.** The `shared` dict is the single source of truth for pipeline state. Only `post()` is allowed to write to `shared["overview"]`. Modifying it in `prep` or `exec` violates the PocketFlow lifecycle and causes race conditions in concurrent chapter runs.
- **Don’t hardcode repo names or facts in `_PROMPT`.** The prompt is intentionally parameterized. If you need static examples, keep them in the prompt template, but always route actual data through `spec(shared)`.
- **Leave the `## ` header expectation alone.** The regex `r'^##[ \t]+(.+?)[ \t]*\n'` is strict. Adding `###` subheaders or changing the spacing will cause sections to silently fall back to their plain `gist` descriptions.

## Commands you need to know
Drop these into your terminal to verify behavior before committing:
```bash
# Smoke test write_overview with mock data
python -c "
from utils.overview import write_overview
sections = [('Architecture', 'high-level component map'), ('Endpoints', 'API surface')]
res = write_overview('MyApp', 'a service mesh', sections, facts='Uses gRPC + sidecar proxy')
print('Welcome:', res['welcome'][:80])
print('Intros keys:', list(res['intros'].keys()))
"

# Verify fallback behavior returns safe empty dicts
python -c "
from utils.nodes import OverviewNode
node = OverviewNode(spec=lambda s: {'name': 'X', 'what': 'Y', 'sections': []})
print(node.exec_fallback(None, RuntimeError('simulated crash')))
"

# Clear LLM cache to force fresh generation during prompt tuning
rm -rf utils/.cache

# Test node lifecycle with a mock shared dict
python -c "
from utils.nodes import OverviewNode
shared = {'crawl': 'mock code dump'}
node = OverviewNode(spec=lambda s: {'name': 'Test', 'what': 'demo', 'sections': [('Intro', 'summary')]})
node.run(shared)
print('Stored key:', 'overview' in shared)
print('Welcome exists:', bool(shared['overview']['welcome']))
"

# Inspect generated prompt before it hits the model
python -c "
from utils.overview import _PROMPT
print(_PROMPT.format(name='Repo', what='schema', facts='none', sections='- A: B', headers='## A')[:300])
"
```

## Conventions that will trip you up
- **`spec(shared)` has a strict return contract.** It must return a dict with exactly `name`, `what`, `sections` (list of `(title, gist)` tuples), and optionally `facts`. Missing keys will cause `KeyError` in `exec()`, triggering the fallback and leaving the page intro blank.
- **`overview.py` uses `.format()`, not `[fill](03_fill.md)`.** Because `_PROMPT` is a private module constant, it uses standard string formatting. If `facts` or `sections` contain literal `{` or `}`, `.format()` will crash. You must escape braces or sanitize upstream findings before they reach this node.
- **Regex parsing is order- and case-insensitive for keys.** The parser strips headers and converts them to `.lower()` for dict keys. If two sections share a base name (e.g., `## Auth` and `## AuthN`), the second will overwrite the first in `blocks`.
- **Fallback swallows the original exception.** `exec_fallback` receives `exc` but does not log it by default. If your pipeline is silently skipping overviews, you’ll need to add a `print()` or `logging.warning()` inside `exec_fallback` to surface the root cause.
- **`shared["overview"]` is consumed synchronously by the renderer.** The pipeline assumes this key exists and contains strings. If you change the return shape of `write_overview` to return HTML, JSON, or nested dicts, the renderer will throw template errors.

## Who to ask
- **Prompt tone & header structure:** Ping `@prompt-engineering`. They own the `_PROMPT` template, define the "knowledgeable colleague" voice, and track how section constraints affect model compliance.
- **Node lifecycle & PocketFlow integration:** Ask `@tooling-llm`. They maintain the base `Node` class, `prep`/`exec`/`post` contracts, and fallback patterns across the repo.
- **Downstream rendering & `shared` consumption:** Loop in `@docs` or `@frontend`. They consume `shared["overview"]` and will tell you if your fallback shape or key naming breaks the HTML generator.
- **Retry budgets & pipeline latency:** Consult `@infrastructure`. They track how `max_retries=2` and `wait=2` interact with `[call_llm](02_call_llm.md)` rate limits and CI timeout budgets.

## Your first ticket
**Title:** Sanitize `{}` in `facts` and `sections` before `.format()` call  
**Scope:** Update `write_overview()` in `overview.py` to escape literal braces in `facts` and `sections` strings before passing them to `_PROMPT.format()`. Replace `{` with `{{` and `}` with `}}` so raw findings from `[crawl](01_crawl.md)` or analysis nodes don’t crash the formatter. Update the docstring to note this safety step, and write a test that passes `facts='{"auth": "jwt"}'` and verifies successful generation.  
**Risk:** Low. Purely additive string sanitization. Does not change return shape, node contract, or `[call_llm](02_call_llm.md)` caching. Prevents a latent `IndexError`/`KeyError` in production pipelines.  
**Deadline:** Ship by Friday. Once merged, you’ll have hardened the prompt injection layer, verified the node’s fallback resilience, and learned exactly how this repo safely bridges raw code analysis into polished documentation.