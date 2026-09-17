# PocketFlow — Personal Learning Note

Orienting fact: the whole framework is the single file `pocketflow/__init__.py`, about 100 lines. Everything under `cookbook/` is an example app built on it. This note treats that file as the core and uses two cookbook apps to show it in use.

## Section 1. Concepts I need to know

| # | Concept | Plain English (one sentence, no jargon) | Where in the code |
|---|---|---|---|
| 1 | Shared store | One ordinary Python dict is passed to every step, and it is the only way steps hand data to each other; there are no return-value pipes between steps. | `pocketflow/__init__.py:BaseNode._run` (the `shared` argument threaded through `prep`/`post`) |
| 2 | Node lifecycle (`prep` → `exec` → `post`) | Each step reads what it needs from the dict (`prep`), does the actual work such as calling an LLM (a text-generating AI model) without touching the dict (`exec`), then writes results back and names what should happen next (`post`). | `pocketflow/__init__.py:BaseNode._run` |
| 3 | Action + successors | The string `post` returns is a label, and each node keeps a dict mapping labels to the next node; `a - "search" >> b` means "if `a` returns `"search"`, go to `b`", and returning `None` means `"default"`. | `pocketflow/__init__.py:BaseNode.next`, `BaseNode.__sub__`, `_ConditionalTransition.__rshift__` |
| 4 | Flow orchestration loop | A Flow starts at one node, runs it, looks up the returned label in that node's successor dict, and repeats until no successor matches; it shallow-copies each node before running it. | `pocketflow/__init__.py:Flow._orch`, `Flow.get_next_node` |
| 5 | Agent = a loop in the graph | An "agent" here is just a decision node whose LLM picks a label (e.g. `search` or `answer`), with the tool nodes wired back to it so it can decide again. | `cookbook/pocketflow-agent/flow.py:create_agent_flow`, `cookbook/pocketflow-agent/nodes.py:DecideAction.post` |
| 6 | Retries and fallback | Only `exec` is retried: if it raises, it is re-run up to `max_retries` times, sleeping `wait` seconds between tries, and then `exec_fallback` either re-raises or returns a substitute result. | `pocketflow/__init__.py:Node._exec` |
| 7 | Flow is a Node (nesting) | A Flow can be dropped into another Flow like a single step, and the last label its inner nodes returned becomes the label used for routing in the outer flow. | `pocketflow/__init__.py:Flow._run`, `Flow.post`; example `cookbook/pocketflow-coding-agent/flow.py:PatchFile` |
| 8 | Batch, params, and async/parallel | `BatchNode` runs `exec` once per item in a list (the "map" half of map-reduce, which splits work into pieces and then combines the results). `BatchFlow` re-runs a whole sub-flow once per small `params` dict, which nodes read via `self.params`. The `Async*`/`Parallel*` variants do the same with `await` or `asyncio.gather` so slow network calls overlap. | `pocketflow/__init__.py:BatchNode._exec`, `BatchFlow._run`, `AsyncFlow._orch_async`, `AsyncParallelBatchNode._exec` |

## Section 2. The important files

| # | File | What it does (one sentence) | Imports from (other files in this list) |
|---|---|---|---|
| 1 | `pocketflow/__init__.py` | Defines the node base classes, action-based wiring (`>>`, `-`), the Flow run loop, retries, and the batch/async/parallel variants, with zero dependencies. | none |
| 2 | `cookbook/pocketflow-agent/utils.py` | Wraps the external world: `call_llm` sends a prompt to OpenAI and returns text, and `search_web_duckduckgo` returns search results as one string. | none |
| 3 | `cookbook/pocketflow-agent/nodes.py` | Implements `DecideAction`, which prompts the LLM for a YAML reply and returns `"search"` or `"answer"`, plus `SearchWeb`, which appends results to `shared["context"]`, and `AnswerQuestion`. | `pocketflow/__init__.py`, `cookbook/pocketflow-agent/utils.py` |
| 4 | `cookbook/pocketflow-agent/flow.py` | Wires the three nodes into a decide → search → decide loop, with an exit to answer. | `pocketflow/__init__.py`, `cookbook/pocketflow-agent/nodes.py` |
| 5 | `cookbook/pocketflow-agent/main.py` | Builds `shared = {"question": ...}` from the command line, runs the flow, and prints `shared["answer"]`. | `cookbook/pocketflow-agent/flow.py` |
| 6 | `cookbook/pocketflow-coding-agent/nodes.py` | Defines the larger agent. It has one node per tool (list/grep/read/run), history compaction to keep prompts short, a `step` counter capped at `MAX_STEPS`, and the three patch nodes (read → validate → apply) used as a sub-flow. | `pocketflow/__init__.py` (its own `utils/call_llm.py` is outside this list) |
| 7 | `cookbook/pocketflow-coding-agent/flow.py` | Wraps the patch nodes in a `Flow` subclass that overrides `post` to log history, then routes every tool back through `CompactHistory` → `DecideAction`. | `pocketflow/__init__.py`, `cookbook/pocketflow-coding-agent/nodes.py` |

Note for future me: every cookbook folder has its own `flow.py`, `nodes.py`, and `utils.py`, and their imports are relative to that folder. Same filenames do not mean the same code.

## Section 3. Dependency chain

```
cookbook/pocketflow-agent/main.py
    -> cookbook/pocketflow-agent/flow.py
        -> cookbook/pocketflow-agent/nodes.py
            -> cookbook/pocketflow-agent/utils.py
            -> pocketflow/__init__.py
        -> pocketflow/__init__.py

cookbook/pocketflow-coding-agent/flow.py
    -> cookbook/pocketflow-coding-agent/nodes.py
        -> pocketflow/__init__.py
    -> pocketflow/__init__.py
```
