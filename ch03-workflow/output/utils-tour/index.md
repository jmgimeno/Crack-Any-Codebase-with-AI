# utils

_Lens: onboarding-guide_

This repository provides a reusable Python toolkit for analyzing codebases and generating technical documentation using large language models. It abstracts away model selection, file crawling, prompt templating, and structured response parsing into a cohesive, cache-friendly workflow pipeline.


## Architecture

```mermaid
flowchart TD
    A0["crawl"]
    A1["call_llm"]
    A2["fill"]
    A3["json_call"]
    A4["OverviewNode"]
    A0 -- "provides code context" --> A4
    A2 -- "templates prompt variables" --> A3
    A3 -- "delegates model invocation" --> A1
    A4 -- "requests narrative summaries" --> A1
```

## Chapters

- [crawl](01_crawl.md)
- [call_llm](02_call_llm.md)
- [fill](03_fill.md)
- [json_call](04_json_call.md)
- [OverviewNode](05_overviewnode.md)