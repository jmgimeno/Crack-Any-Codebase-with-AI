# PocketFlow

_Lens: beginner-tutorial_

PocketFlow is an ultra-minimalist, 100-line Python framework for orchestrating LLM workflows, agents, and pipelines using graph-based nodes and flows. It enables lightweight, zero-dependency development of complex AI applications through a clear graph abstraction.


## Architecture

```mermaid
flowchart TD
    A0["BaseNode"]
    A1["Node"]
    A2["BatchNode"]
    A3["Flow"]
    A4["BatchFlow"]
    A5["AsyncNode"]
    A6["AsyncParallelBatchNode"]
    A7["AsyncFlow"]
    A1 -- "extends" --> A0
    A2 -- "extends" --> A1
    A3 -- "extends" --> A0
    A4 -- "extends" --> A3
    A5 -- "extends" --> A1
    A6 -- "extends" --> A5
    A6 -- "extends" --> A2
    A7 -- "extends" --> A3
    A7 -- "extends" --> A5
    A3 -- "orchestrates" --> A0
```

## Chapters

- [BaseNode](01_basenode.md)
- [Node](02_node.md)
- [BatchNode](03_batchnode.md)
- [Flow](04_flow.md)
- [BatchFlow](05_batchflow.md)
- [AsyncNode](06_asyncnode.md)
- [AsyncParallelBatchNode](07_asyncparallelbatchnode.md)
- [AsyncFlow](08_asyncflow.md)