# PocketFlow Quiz — Answer Key

**Q1: C.** When `SearchWeb.post` returns `None`, `Flow._orch` does `last_action = curr._run(shared)`, then calls `get_next_node(curr, None)`. That looks up `curr.successors.get(action or "default")`, which becomes `successors.get("default")`. The search node's successor dict is `{"decide": decide}`, with no `"default"` key, so the lookup returns `None`. Because `curr.successors` is non-empty, `get_next_node` only calls `warnings.warn(...)` and returns `None`. Then `copy.copy(None)` is `None`, so the `while curr` loop exits.

The search results are already in `shared["context"]`, since `post` wrote them before returning. But `AnswerQuestion` never runs, so `shared["answer"]` is never set.

Why the wrong answers are wrong:
- **A** misses the `action or "default"` conversion, and `dict.get` never raises on a missing key anyway.
- **B** invents a "single successor fall-through" rule. Routing is an exact key lookup, and `"default"` is just another key.
- **D** confuses routing with retries. `Node._exec` retries only when `exec` raises. `post` is outside the retry loop, and returning `None` is not an error.

---

**Q2: A.** `BaseNode._run` calls `prep` exactly once, and only `_exec` loops.

With `max_retries=3`, the loop in `Node._exec` goes like this:
1. `cur_retry=0`: `exec` fails. This is not the last attempt, so it sleeps 10 s.
2. `cur_retry=1`: `exec` fails. It sleeps 10 s again.
3. `cur_retry=2`: `exec` fails. This is the last attempt, so it calls `exec_fallback(prep_res, e)` immediately, with no sleep.

The default `exec_fallback` is `raise exc`. The exception passes through `_run` before `post` is ever called, and then through `Flow._orch`, which has no `try` block, out to your caller. Every attempt receives the same `prep_res`, so a retry cannot see new data in `shared["context"]`.

Why the wrong answers are wrong:
- **B** assumes the whole lifecycle retries. That would be a different design, where `prep` re-reads state on every attempt. It also counts one sleep too many.
- **C** assumes the default fallback swallows the error and returns `None`. It re-raises. C also sleeps after the final failure, which the code skips.
- **D** misreads where `exec_fallback` sits. It is called only inside the `if self.cur_retry == self.max_retries-1` branch, not after every failure.

---

**Q3: D.** A parent flow learns what a child flow did only through `last_action = curr._run(shared)`. For a `Flow`, `_run` returns `self.post(shared, p, o)`, where `o` is the inner `last_action`.

`Flow.post` exists solely to pass `o` up (`return exec_res`). Without it, `BaseNode.post` returns `None`. The parent then turns `None` into `"default"`, so a sub-flow whose last inner node returned `"error"` could no longer route its parent to an error handler.

`BatchFlow._run` already calls `self.post(shared, pr, None)`, so it always routed on `"default"`. Removing `Flow.post` changes nothing for it. This is also a quirk worth remembering on its own: a `BatchFlow` can never emit a meaningful action unless you override its `post`.

Why the wrong answers are wrong:
- **A** assumes the parent reads `_orch`'s return value directly. It does not. The value passes through `post`, and that hop is exactly what you deleted.
- **B** confuses the return value of `flow.run(shared)` with the output channel. In PocketFlow, results live in `shared`. `main.py` reads the answer from the shared store, not from what `run` returns, so a top-level run is unaffected.
- **C** mixes up the two levels. The inner `_orch` loop routes on each *inner node's* `_run` return value. `Flow.post` runs only once, after that loop has finished.
