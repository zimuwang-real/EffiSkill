---
skill_id: O006
type: operator
language: cpp
family: state_compression
name: Refactor Recursive DPTo Iterative Greedy And Tight State
description: Reusable optimization pattern distilled from weighted traces.
tags:
- dynamic_programming
- top_down_to_bottom_up
- state_compression
- bitmask_dp
- digit_dp
- grid_dp
- game_dp
- greedy
- memory_optimization
- io_optimization
triggers:
- A memoized recursive DP over a linear index (string, array, days) with small fixed state (e.g. 2–3 options per position)
  and transitions only to the next index.
- A recursive DP on a 2D grid where each cell depends only on a constant number of neighbors (e.g., up/left) and grid sizes
  up to about 1e3 x 1e3.
- Digit DP or small-state DP implemented as recursion f(pos, state, tight, ) over positions with a static 3D or 4D array (often
  over-allocated and only partially used).
- Bitmask DP with n ≤ 15–20 implemented via recursion over masks and manual memoization, plus a full dp[1<<n][ ] table initialized
  for all masks.
- Use of memo tables with a much larger second/third dimension than semantically needed (e.g., dp[N][10] where only 0..2 are
  used).
- DP tables that store only reachability flags or simple win/lose booleans but use int/long long and oversized dimensions
  (e.g., dp[105][105][105] or dp[100010][11]).
- Per-iteration reallocation or reinitialization of full DP layers (double-buffering 2D arrays, memset over whole dp for every
  test/iteration).
- Final answer requires only a simple aggregate (min/max, ratio, parity) but is computed via an O(C^2) or O(state_count^2)
  scan over the entire DP table.
---

## When to use
- A memoized recursive DP over a linear index (string, array, days) with small fixed state (e.g. 2–3 options per position) and transitions only to the next index.
- A recursive DP on a 2D grid where each cell depends only on a constant number of neighbors (e.g., up/left) and grid sizes up to about 1e3 x 1e3.
- Digit DP or small-state DP implemented as recursion f(pos, state, tight, ) over positions with a static 3D or 4D array (often over-allocated and only partially used).
- Bitmask DP with n ≤ 15–20 implemented via recursion over masks and manual memoization, plus a full dp[1<<n][ ] table initialized for all masks.
- Use of memo tables with a much larger second/third dimension than semantically needed (e.g., dp[N][10] where only 0..2 are used).
- DP tables that store only reachability flags or simple win/lose booleans but use int/long long and oversized dimensions (e.g., dp[105][105][105] or dp[100010][11]).
- Per-iteration reallocation or reinitialization of full DP layers (double-buffering 2D arrays, memset over whole dp for every test/iteration).
- Final answer requires only a simple aggregate (min/max, ratio, parity) but is computed via an O(C^2) or O(state_count^2) scan over the entire DP table.

## Steps
1. Analyze DP state and transitions: Write down the logical state tuple explicitly (e.g., (index, last_choice), (i,j), (mask, v), (pos, count, tight)).
2. Analyze DP state and transitions: Identify which components truly affect future transitions and which are redundant or can be encoded implicitly (e.g., via parity or prefix sums).
3. Compress the state space: Remove unused or redundant dimensions (e.g., shrink dp[N][10] to dp[N][3]).
4. Compress the state space: Replace explicit counters with derived or structural information where possible (e.g., use prefix sums or parity instead of a separate 'taken' counter).
5. Compress the state space: For boolean/0–1 DP, switch from int/long long to bool or bitsets when appropriate.
6. Convert recursion to iterative DP: For 1D DP over index i, define an iterative recurrence dp[i][state] from dp[i-1][*] or dp[i+1][*] and implement as a forward or backward loop.
7. Convert recursion to iterative DP: For 2D grid DP, iterate row-by-row or column-by-column, using sentinel borders or base cases instead of recursive calls.
8. Convert recursion to iterative DP: For bitmask DP, iterate masks in topological order (e.g., increasing mask) or switch to top-down only when it meaningfully prunes unreachable states.

## Complexity
- Time: Typically preserves or improves asymptotic time: O(n), O(n*m), O(n*W), O(2^n * poly(n)) remain the same in big-O, but with lower constant factors from removing recursion, avoiding full-table initialization, and pruning unreachable states
- Space: Often reduced from O(n * state) or O(2^n * state) to O(state) via rolling arrays or scalar recurrences. Typical changes include: dp[N][S] -> dp[2][S] or dp[S]; 3D dp[105][105][105] -> O(N*K) or even O(N) buffers; dp[1<<n][n] preserved but

## Pitfalls
- Changing recursion to iteration but altering dependency order, leading to using partially updated states in the same layer (e.g., in-place updates without reverse iteration when required).
- Over-aggressive state compression that drops logically necessary information (e.g., removing a 'taken' dimension that truly affects feasibility), silently breaking correctness.
- Incorrectly tightening bounds (e.g., underestimating ub or reachable ranges), causing out-of-range states to be skipped and answers to be underestimated.
- Using rolling arrays or in-place updates without careful loop direction (e.g., forward iteration in 0/1 knapsack-like transitions), leading to multiple uses of the same item/state in one step.
- Switching from int64 to int for DP states without verifying that intermediate sums stay within 32-bit range or accounting for MOD-safe operations.
- Assuming a greedy simplification is valid based only on small tests or intuition, without a solid argument about monotonicity or absence of long-range trade-offs.
- Retaining recursion for some paths while partially iterating others, resulting in mixed-style logic and duplicated work that is harder to debug and optimize.
- Leaving large DP arrays global and over-dimensioned even after compression, causing unnecessary memory traffic and cache misses.

## When not to use
- When the recursive DP has very small constraints (e.g., n ≤ 30, tiny grids) and performance is already well within limits; the iterative or greedy refactor may not justify added complexity.
- For problems where the state graph has complex, non-local dependencies (e.g., arbitrary DAG DP, tree DP with multiple cross-links) where recursion expresses structure more clearly and stack depth is safely bounded.
- When the DP relies on sophisticated memoization over irregular states (maps, compressed coordinates, dynamic structures) where flat arrays and simple iteration are not straightforward or may introduce bugs.
- In scenarios where code clarity and maintainability outweigh constant-factor performance (e.g., educational code, proofs of concept) and recursion is significantly easier to reason about.
- When an attempted greedy or closed-form collapse cannot be rigorously justified; sticking to a correct DP is preferable to an unjustified heuristic simplification.
- If the language or environment already has very high stack limits and low function-call overhead, and the primary bottleneck is elsewhere (e.g., I/O or an unrelated algorithmic step).

## Minimal example
Before:
```cpp
// O006 focus: refactor
int best = 0;
for (int mask = 0; mask < (1 << n); ++mask)
  best = max(best, score(mask));
```
After:
```cpp
// optimized for refactor
int odd = 0;
for (int x : a) odd += x & 1;
int best = closed_form_from_counts((int)a.size(), odd);
// replace subset scan with parity/count reasoning
```
