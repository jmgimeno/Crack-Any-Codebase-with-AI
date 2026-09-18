# workflow

_Lens: beginner-tutorial_

This project automates the creation of a guided, interactive tour of a software repository using LLMs. It transforms raw source code into a structured, narrative-driven documentation website by crawling files, identifying core concepts, and mapping their relationships.


## Architecture

```mermaid
flowchart TD
    A0["Flow"]
    A1["Node"]
    A2["SmartCrawl"]
    A3["Analyze"]
    A4["Relate"]
    A5["WriteChapters"]
    A0 -- "orchestrates" --> A1
    A1 -- "specializes into" --> A2
    A2 -- "feeds data to" --> A3
    A3 -- "feeds concepts to" --> A4
    A4 -- "feeds connections to" --> A5
```

## Chapters

- [Flow](01_flow.md)
- [Node](02_node.md)
- [SmartCrawl](03_smartcrawl.md)
- [Analyze](04_analyze.md)
- [Relate](05_relate.md)
- [WriteChapters](06_writechapters.md)