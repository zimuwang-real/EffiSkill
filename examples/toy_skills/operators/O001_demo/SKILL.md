---
skill_id: O001
type: operator
language: python
name: Accumulate without materializing a list
description: Use a generator when a reduction does not need a stored intermediate list.
triggers:
  - A list comprehension is consumed once by sum.
---

This hand-written toy card demonstrates the registry format. It is not a mined
research skill and has no measured performance claim.

Before: `sum([x * x for x in values])`

After: `sum(x * x for x in values)`

Preserve the order of iteration and arithmetic semantics. Measure on the target
workload before concluding that either form is faster.
