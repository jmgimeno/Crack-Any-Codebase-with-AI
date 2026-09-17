## Line under microscope

> A Flow starts at one node, runs it, looks up the returned label in that node's successor dict, and repeats until no successor matches; it shallow-copies each node before running it.

The clause "it shallow-copies each node before running it" is easy to skip in a review. It also invites a wrong conclusion: that each run is isolated. The copy isolates the node object, not the shared store (the one dict every node reads and writes), and that is the sibling you would confuse it with.

## What it actually means: copying the node vs copying the state

Input: `cookbook/pocketflow-parallel-batch-flow`, running `ImageParallelBatchFlow` on 3 images × 3 filters. That makes 9 param dicts, such as `{"image_path": "images/cat.jpg", "filter": "blur"}` and `{"image_path": "images/dog.jpg", "filter": "sepia"}`. All 9 go through **one** graph, `LoadImage → ApplyFilter → SaveImage`, at the same time via `asyncio.gather`.

### What copying the node does with it

1. `AsyncParallelBatchFlow._run_async` starts 9 copies of `_orch_async` at once, and each gets its own param dict.
2. Inside each one, `curr = copy.copy(self.start_node)` creates a fresh `LoadImage` object, and `curr.set_params(p)` sets `.params` **on that copy only**. The cat/blur run holds one `LoadImage`, and the dog/sepia run holds a different one.
3. All 9 `LoadImage.exec_async` calls then hit `await asyncio.sleep(0.5)` and suspend together.
4. Now suppose `SaveImage.post_async` printed `self.params["filter"]` *after* its `await`. The cat/blur copy would still say `blur`, because nobody else ever touched that object's `.params`.
5. Result: `self.params` is private to each run. The copy is shallow, but that is enough, because `set_params` **replaces** the `.params` attribute rather than mutating a shared dict. The `successors` dict is still shared, which is fine because it is read-only during a run.

### What copying the state would do (and what PocketFlow does NOT do)

1. `shared` is **not** copied. All 9 runs receive the same dict object.
2. `LoadImage.post_async` writes `shared["image"] = <cat image>`. `ApplyFilter.prep_async` reads `shared["image"]` back.
3. This works today only by luck of timing. Between that write and that read there is no `await`: finishing `post_async`, returning to `_orch_async`, copying the next node, and running `prep_async` up to the first `await` all happen without yielding. So no other run can overwrite `shared["image"]` in between.
4. Now add one line to `LoadImage.post_async`, for example `await log_async(...)`, before returning. The event loop switches tasks, the dog run writes `shared["image"] = <dog image>`, and the cat run's `ApplyFilter` reads the dog image.
5. Result: `output/cat_blur.jpg` silently contains a blurred dog. No exception is raised, and the params are still correct, so logs would say "cat, blur".

### Why this codebase chose copying the node (and not the state)

`shared` is the only channel between nodes, so copying it per run would break the pipeline. Copying the node is the minimum needed for `pocketflow/__init__.py:AsyncParallelBatchFlow._run_async` to run many `_orch_async` loops over one graph (`curr=copy.copy(self.start_node)` in `Flow._orch` / `AsyncFlow._orch_async`), so per-run data belongs in `self.params` or in per-run keys of `shared`, never in fixed keys like `shared["image"]`.
