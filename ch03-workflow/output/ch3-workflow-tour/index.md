# workflow

_Lens: beginner-tutorial_

This project is an automated codebase documentation generator that uses an LLM-powered pipeline to analyze repositories and produce structured learning guides. It selects key files, extracts core concepts, maps their relationships, and sequentially writes formatted HTML tutorials.


## Architecture

```mermaid
flowchart TD
    A0["Flow"]
    A1["Node"]
    A2["shared"]
    A3["SmartCrawl"]
    A4["Analyze"]
    A5["Relate"]
    A6["WriteChapters"]
    A7["parse_yaml"]
    A0 -- "sequences execution of" --> A3
    A3 -- "feeds filtered codebase to" --> A4
    A4 -- "extracts core concepts for" --> A5
    A5 -- "maps structural dependencies f" --> A6
    A6 -- "populates final output in" --> A2
    A1 -- "reads and writes context to" --> A2
    A1 -- "defines prep-exec-post lifecyc" --> A3
    A3 -- "validates LLM output with" --> A7
```

## Chapters

- [Flow](01_flow.md)
- [Node](02_node.md)
- [shared](03_shared.md)
- [SmartCrawl](04_smartcrawl.md)
- [Analyze](05_analyze.md)
- [Relate](06_relate.md)
- [WriteChapters](07_writechapters.md)
- [parse_yaml](08_parse_yaml.md)