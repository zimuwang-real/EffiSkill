---
skill_id: O019
type: operator
language: cpp
family: dp
name: Streaming Prefix Optimization
description: Reusable optimization pattern distilled from weighted traces.
tags:
- prefix_sum
- arrays
- counting
- single_pass
- sliding_window
- fenwick_tree
- parity
- constant_factor_optimization
- space_optimization
- io_optimization
triggers:
- Code constructs a full prefix-sum array but later uses only sequential scans, the total sum, or a single running prefix
  value in the final expression.
- Fenwick tree or segment tree is used only for maintaining a prefix count at the current index (no random queries or range
  updates).
- Two or more large auxiliary arrays encode prefix/suffix counts or gains, but each is only ever consumed via a single max/min
  scan or simple arithmetic.
- Per-element logic is simple (additions, comparisons) inside a tight loop, and large N (around 1e5–1e6) suggests constant
  factors and memory traffic dominate.
- I/O loops read or write up to 1e5–1e6 integers using formatted streams, and the computation itself is linear and light.
- Problem output depends only on parity, counts, or simple aggregates (e.g., even/odd sum, number of positives) rather than
  exact large numeric values.
- Range costs depend only on local differences around an index or a fixed-length window, but current code recomputes via global
  prefix/suffix arrays.
- Static global arrays are memset over their entire capacity each test case despite only a prefix proportional to n being
  used.
---

## When to use
- Code constructs a full prefix-sum array but later uses only sequential scans, the total sum, or a single running prefix value in the final expression.
- Fenwick tree or segment tree is used only for maintaining a prefix count at the current index (no random queries or range updates).
- Two or more large auxiliary arrays encode prefix/suffix counts or gains, but each is only ever consumed via a single max/min scan or simple arithmetic.
- Per-element logic is simple (additions, comparisons) inside a tight loop, and large N (around 1e5–1e6) suggests constant factors and memory traffic dominate.
- I/O loops read or write up to 1e5–1e6 integers using formatted streams, and the computation itself is linear and light.
- Problem output depends only on parity, counts, or simple aggregates (e.g., even/odd sum, number of positives) rather than exact large numeric values.
- Range costs depend only on local differences around an index or a fixed-length window, but current code recomputes via global prefix/suffix arrays.
- Static global arrays are memset over their entire capacity each test case despite only a prefix proportional to n being used.

## Steps
1. Identify the true dependencies of the final expression: Inspect how prefix sums or DP arrays are used in the final loops.
2. Identify the true dependencies of the final expression: Check whether only the total sum, a running prefix sum, local differences, or fixed-size window aggregates are needed at each step.
3. Replace full prefix arrays with scalar accumulators when possible: For sums of an array, keep `total` and a running `prefix` instead of storing all prefix sums.
4. Replace full prefix arrays with scalar accumulators when possible: For prefix counting (e.g., count of a certain character), keep a single counter updated per index.
5. Stream computations in a single pass where feasible: Fuse the prefix-construction pass and the evaluation pass.
6. Stream computations in a single pass where feasible: For each element: read value, update running sums/counters, and immediately update the candidate answer.
7. Exploit local-update structure for per-index modifications: When removing or altering a single element only affects a small neighborhood, derive a constant-time delta using local neighbors and a global baseline (e.g., a global total cost `tot`).
8. Exploit local-update structure for per-index modifications: Avoid rebuilding prefix/suffix arrays when only local adjustments are necessary.

## Complexity
- Time: (pattern dependent)
- Space: Reduces auxiliary space from O(n) to O(1) where only streaming state is needed, or from multiple O(n) arrays to a single O(n) array when some structure (e.g., input array, prefix/suffix best) is inherently required. Eliminates extraneous

## Pitfalls
- Changing semantics during streaming refactors: Misaligning prefix indices when removing arrays (e.g., old code used `pre[i]` and `pre[i-1]`, new code collapses both into a single `prefix` variable incorrectly).
- Changing semantics during streaming refactors: Off-by-one errors when converting from 1-based to 0-based indexing or when dropping sentinel cells.
- Incorrect handling of boundaries in local-update formulas: Forgetting special cases at the first or last element when computing deltas based on neighbors.
- Incorrect handling of boundaries in local-update formulas: Using uninitialized sentinel values or relying on implicit zeros without ensuring arrays are large enough.
- Removing Fenwick trees when multiple query points actually exist: Replacing BIT with a scalar counter even though the code queries prefix sums for arbitrary indices, breaking correctness.
- Removing Fenwick trees when multiple query points actually exist: Overlooking that offline queries or coordinate compression rely on the full BIT structure.
- Numeric overflows after narrowing representations: Switching from big integers or wider types to 32-bit ints in contexts where sums can reach 1e12 or more.
- Numeric overflows after narrowing representations: Using `abs` on 64-bit values or printing `long long` with `%d` instead of `%lld`.

## When not to use
- When the algorithm truly needs random-access range queries or updates: Tasks requiring arbitrary prefix sums, range updates, or offline query sets should retain Fenwick/segment trees instead of collapsing to a single
- When intermediate state must be preserved for later queries or reconstructions: If all prefix values, DP tables, or path details are needed for output or backtracking, streaming away those arrays is inappropriate.
- When constraints are very small and code clarity is more important than micro-optimizations: For small n or loose time limits, extra complexity from custom I/O and tightly packed loops may harm readability without
- When numeric ranges exceed 64-bit safety or require exact big-integer behavior: Problems that truly demand arbitrary-precision arithmetic cannot safely switch to 64-bit types or parity-only reasoning.
- When logic heavily depends on non-local interactions: If each step depends on many prior or future positions in complex ways (e.g., full 2D DP, all-pairs relationships), simple streaming substitutions may not capture

## Minimal example
Before:
```cpp
long long pref[N];
pref[0] = 0;
for (int i = 1; i <= n; ++i) pref[i] = pref[i - 1] + (a[i] - k);
long long ans = 0;
for (int i = 1; i <= n; ++i)
    if (pref[i] >= 0) ++ans;
```
After:
```cpp
long long pref = 0, ans = 0;
for (int i = 1; i <= n; ++i) {
    pref += a[i] - k;            // streaming prefix update
    if (pref >= 0) ++ans;        // use it immediately
}
// no O(n) prefix array: fewer cache misses, less memory traffic
```
