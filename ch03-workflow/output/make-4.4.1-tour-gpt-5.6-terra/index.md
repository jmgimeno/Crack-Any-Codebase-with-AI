# make-4.4.1

_Lens: beginner-tutorial_

GNU Make is a build automation tool that reads makefiles, represents targets and prerequisites as an in-memory graph, and rebuilds only the files that need updating. It also expands variables and functions, discovers implicit build rules, runs recipes through shells, and coordinates parallel work across recursive make processes.


## Architecture

```mermaid
flowchart TD
    A0["struct variable"]
    A1["variable_set_list"]
    A2["variable_expand"]
    A3["eval"]
    A4["struct file"]
    A5["struct dep"]
    A6["struct rule"]
    A7["update_goal_chain"]
    A8["new_job"]
    A9["jobserver"]
    A0 -- "is stored and resolved within" --> A1
    A1 -- "provides target-specific scope" --> A4
    A2 -- "expands references to" --> A0
    A2 -- "looks up variables through" --> A1
    A3 -- "parses and defines" --> A0
    A3 -- "creates and records targets" --> A4
    A3 -- "parses and attaches prerequisi" --> A5
    A3 -- "creates implicit pattern rules" --> A6
    A3 -- "uses to expand makefile text" --> A2
    A4 -- "owns dependency edges" --> A5
    A4 -- "holds target-specific variable" --> A1
    A6 -- "describes prerequisite pattern" --> A5
    A6 -- "supplies recipes and dependenc" --> A4
    A7 -- "evaluates whether to rebuild" --> A4
    A7 -- "traverses dependency edges" --> A5
    A7 -- "uses to infer missing build re" --> A6
    A7 -- "starts when a target must be r" --> A8
    A8 -- "executes the target's recipe" --> A4
    A8 -- "expands recipe command lines" --> A2
    A8 -- "uses to construct the target e" --> A1
    A8 -- "acquires and releases parallel" --> A9
    A9 -- "limits concurrent job launches" --> A8
```

## Chapters

- [struct variable](01_struct_variable.md)
- [variable_set_list](02_variable_set_list.md)
- [variable_expand](03_variable_expand.md)
- [eval](04_eval.md)
- [struct file](05_struct_file.md)
- [struct dep](06_struct_dep.md)
- [struct rule](07_struct_rule.md)
- [update_goal_chain](08_update_goal_chain.md)
- [new_job](09_new_job.md)
- [jobserver](10_jobserver.md)