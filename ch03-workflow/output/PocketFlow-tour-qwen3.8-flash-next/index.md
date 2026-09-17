# PocketFlow

_Lens: beginner-tutorial_

Pocket Flow is a minimalist LLM framework that models applications as graphs of reusable nodes and flows.
It keeps state in shared dictionaries while supporting sync, async, batch, and nested workflows.


## Architecture

```mermaid
flowchart TD
    A0["shared"]
    A1["Node"]
    A2["successors"]
    A3["Flow"]
    A4["params"]
    A5["BatchNode"]
    A6["BatchFlow"]
    A7["AsyncNode"]
    A8["AsyncFlow"]
    A3 -- "passes through nodes" --> A0
    A1 -- "reads and writes" --> A0
    A1 -- "defines routing table" --> A2
    A3 -- "follows returned actions" --> A2
    A3 -- "supplies per-run settings" --> A4
    A1 -- "reads for reusable behavior" --> A4
    A5 -- "extends with per-item executio" --> A1
    A6 -- "repeats nested flow for each i" --> A3
    A6 -- "generates one params set per i" --> A4
    A7 -- "extends with awaitable lifecyc" --> A1
    A8 -- "orchestrates sync and async no" --> A3
    A8 -- "enables queue-based communicat" --> A0
```

## Chapters

- [shared](01_shared.md)
- [Node](02_node.md)
- [successors](03_successors.md)
- [Flow](04_flow.md)
- [params](05_params.md)
- [BatchNode](06_batchnode.md)
- [BatchFlow](07_batchflow.md)
- [AsyncNode](08_asyncnode.md)
- [AsyncFlow](09_asyncflow.md)