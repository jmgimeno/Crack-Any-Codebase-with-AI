

# Chapter 1: crawl

Walks through a project folder, filters out noise like tests and build files, and stitches all relevant code into one readable text block. Think of it as a careful librarian who only pulls the essential books from a massive archive and binds them into a single volume for quick review. This module (`[crawl](01_crawl.md)`) is the foundation of our ingestion pipeline.

## What you will touch in week one
You’ll spend most of your time inside `crawl.py`, specifically the three `DEFAULT_*` frozensets and the `crawl()` entry point. Your day-to-day will involve:
- Adjusting `DEFAULT_KEEP_EXT` or `DEFAULT_KEEP_NAMES` when the team adds support for a new language, framework, or build tool.
- Tuning `DEFAULT_SKIP_DIR` to prune new vendor directories or framework-specific caches that aren’t yet covered.
- Inspecting the raw output format to ensure it plays nicely with downstream consumers like `[call_llm](02_call_llm.md)` and `[fill](03_fill.md)`.

## What to avoid
- **Do not rewrite `safe_read()` error handling.** The bare `try/except` for `UnicodeDecodeError` and `PermissionError` is intentional. A single corrupted asset or restrictive permission should never abort a walk over 10,000 files.
- **Don’t mutate the `frozenset` constants.** They are immutable by design. If you need repo-specific overrides, pass them as kwargs to `list_files()` or `crawl()` instead of patching the module globals.
- **Leave `pathspec` alone.** The `.gitignore`-style pattern matching in `list_files()` relies on `pathspec.GitIgnoreSpec`. Swapping it for `fnmatch` or `glob` breaks relative-path resolution and the `include`/`exclude` contract that later chapters depend on.

## Commands you need to know
Drop these into your terminal to verify behavior before committing:
```bash
# Quick sanity check: print the first 1000 chars of a crawl run
python -c "from utils.crawl import crawl; print(crawl('.')[:1000])"

# Inspect which files would be kept without reading disk I/O
python -c "from utils.crawl import list_files; print(len(list_files('.')))"

# Dry-run with custom filters (e.g., only TypeScript, skip examples)
python -c "
from utils.crawl import crawl
out = crawl('.', keep_ext={'.ts', '.tsx'}, skip_dirs=frozenset(['examples', 'node_modules']))
print(f'Bytes: {len(out)}')
"

# Clear LLM cache if you're testing downstream [json_call](04_json_call.md) retries
rm -rf utils/.cache
```

## Conventions that will trip you up
- **The file header format is strict.** Every kept file is wrapped with exactly:
  `{'=' * 60}\nFile: {relative_path}\n{'=' * 60}\n{content}\n`
  Downstream parsers in `[fill](03_fill.md)` and `[OverviewNode](05_overviewnode.md)` split on this exact delimiter. Changing the number of `=` signs or the `\nFile:` prefix will break the entire pipeline.
- **Patterns are relative to `root`.** When you pass `include=["src/**"]` or `exclude=["**/*_test.go"]`, they are evaluated against `os.path.relpath(path, root)`. Absolute paths or paths with `../` will silently fail to match.
- **Size caps are silent.** Files over `DEFAULT_MAX_FILE_BYTES` (500 KB) are dropped without warning. This prevents generated dumps or minified bundles from poisoning the context window. If you need to include a large schema or config, either split it or temporarily override `max_file_bytes` in your call.

## Who to ask
- **Filter & extension questions:** Ping the `@tooling-llm` Slack channel. They maintain the baseline defaults and track which extensions actually appear in production repos.
- **Pattern matching & `pathspec` behavior:** Ask the `@infrastructure` team. They own the context-window budget and will tell you if your new `exclude` pattern is saving tokens or accidentally cutting off critical source.
- **Downstream integration:** If your change breaks how `[call_llm](02_call_llm.md)` caches prompts or how `[json_call](04_json_call.md)` extracts structured data, loop in the `@prompt-engineering` channel. They know the exact token budgets and parsing edge cases.

## Your first ticket
**Title:** Add `.zig` and `.nim` extensions to the default crawl filter  
**Scope:** Update `DEFAULT_KEEP_EXT` in `crawl.py` to include `'.zig'` and `'.nim'`. Write a two-line test that verifies `list_files()` catches them in a mock directory. Verify that `[fill](03_fill.md)` still templates the output correctly and that `[call_llm](02_call_llm.md)` caches the resulting prompt hash without errors.  
**Risk:** Low. Purely additive to an immutable frozenset. No parser changes, no downstream contract shifts.  
**Deadline:** Ship by Friday. Once merged, you’ll have touched the ingestion layer, verified the pipeline, and learned exactly how this repo turns raw code into LLM-ready context. Next week, you’ll step into `[call_llm](02_call_llm.md)` to see how that text becomes a prompt.