# PocketFlow — Mental Model Quiz

**Q1.** In `cookbook/pocketflow-agent/flow.py`, the loop is wired as `decide - "search" >> search`, `decide - "answer" >> answer`, and `search - "decide" >> decide`. `SearchWeb.post` in `cookbook/pocketflow-agent/nodes.py` appends results to `shared["context"]` and ends with `return "decide"`.

You delete that `return "decide"` line, so `SearchWeb.post` now returns `None`. You run a question that makes `DecideAction` choose `"search"` first. What happens?

A) `Flow.get_next_node` raises a `TypeError`, because `None` is not a valid key in `search.successors`.
B) Nothing changes. `None` is treated as `"default"`, and a node with a single successor falls through to it, so control still returns to `decide`.
C) The flow ends right after the first search. The only signal is a `warnings.warn` saying the action was not found. `shared["answer"]` is never written, even though `shared["context"]` now has search results.
D) `Node._exec` treats the `None` as a failed attempt and re-runs `SearchWeb` until `max_retries` is used up, then calls `exec_fallback`.

---

**Q2.** `pocketflow/__init__.py:BaseNode._run` calls `prep`, then `_exec`, then `post`. `Node._exec` loops `for self.cur_retry in range(self.max_retries)` and calls `exec_fallback` on the final failure. `DecideAction.prep` in `cookbook/pocketflow-agent/nodes.py` reads the question and `shared["context"]`, and `DecideAction.exec` calls `call_llm` and parses the YAML reply.

Suppose `flow.py` builds the node as `DecideAction(max_retries=3, wait=10)`, and the LLM returns unparseable YAML on **all three** attempts. `exec_fallback` is not overridden. What happens?

A) `prep` runs once and `exec` runs 3 times with the same `prep_res`. The node sleeps 10 s after the first and second failures only (20 s total). The third exception is re-raised by the default `exec_fallback`, so `post` never runs and the exception propagates out of `Flow._orch`.
B) `prep`, `exec` and `post` are re-run as a unit 3 times, so each retry re-reads `shared["context"]` and could pick up changes. The total wait is 30 s.
C) `exec` runs 3 times with 10 s sleeps after every failure (30 s). Then `exec_fallback` returns `None`, `post` runs with `exec_res=None`, and the flow routes on `"default"`.
D) `exec` runs 3 times, but `exec_fallback` is called after *each* failure. Since the default one raises, the retry loop actually stops after the first failure.

---

**Q3.** `pocketflow/__init__.py:Flow._run` does `p=self.prep(shared); o=self._orch(shared); return self.post(shared,p,o)`, where `_orch` returns `last_action`. `Flow` overrides `post` to `return exec_res`, while `BaseNode.post` does nothing and returns `None`. `BatchFlow._run` calls `self.post(shared, pr, None)`.

Counterfactual: you delete `Flow.post`, so every `Flow` inherits `BaseNode.post`. Which statement is correct?

A) Nothing observable changes, because `_orch` already returns `last_action` and the parent flow reads that value directly.
B) Top-level runs break. `flow.run(shared)` now returns `None`, so `cookbook/pocketflow-agent/main.py` can no longer find the answer.
C) Nested flows stop early. The inner `_orch` loop exits after its start node because `post` no longer supplies the next action.
D) Every `Flow` used as a node inside another `Flow` now routes its parent on `"default"`, whatever its last inner node returned. `BatchFlow` behaves exactly as before, because it already passes `None` into `post`.

---

## Answer key

Ask me for it when you've committed to your answers.
