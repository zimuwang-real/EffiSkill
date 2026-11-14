---
skill_id: O014
type: operator
language: cpp
family: state_compression
name: Dp State Compression And Bound Tightening
description: Reusable optimization pattern for dynamic programming over large tables whose transitions depend on only a few
  neighboring layers or a tightly bounded sum/capacity dimension. The operator rewrites 2D/3D DP or over-provisioned ranges
  into 1D or rolling arrays, tightens the active index ranges to the actually reachable state space, and updates in-place
  with reversed iteration where safe. This simultaneously reduces
tags:
- dynamic_programming
- state_compression
- rolling_array
- knapsack
- subset_sum
- bitmask_dp
- combinatorics
- counting
- memory_optimization
- cache_locality
triggers:
- DP state f[i][*] depends only on f[i-1][*] (or a small fixed number of previous layers), but code stores all i-layers in
  a large 2D/3D array.
- Presence of dp[n+1][W+1] (or dp[steps][sum]) where transitions are classic 0/1 or unbounded knapsack / subset-sum updates
  over a sum or capacity dimension.
- Use of an auxiliary buffer tmp[ ] that is fully zeroed and then copied back into dp[ ] each iteration, combined with forward
  iteration over DP indices.
- Fixed global bounds for a sum/capacity dimension (e.g., 1e5, 5000, 2500) independent of the true reachable maximum from
  inputs, with loops always iterating the full range.
- Per-testcase memset over large DP tables (O(n * S)) even though only a portion is touched by transitions.
- Bitmask or extra small dimension k (k <= n or small constant) where dp[k][mask] ultimately collapses to a single aggregate
  value per mask, or intermediate k-states are only used via simple sums/complements.
- Triple nested loops whose innermost loop scans an entire DP row or plane while only a shrinking/growing prefix of indices
  can be reachable given the processed items.
- Knapsack-like DPs using width defined by a global maximum (e.g., 100000) while actual capacity or reachable sum is significantly
  smaller.
---

## When to use
- DP state f[i][*] depends only on f[i-1][*] (or a small fixed number of previous layers), but code stores all i-layers in a large 2D/3D array.
- Presence of dp[n+1][W+1] (or dp[steps][sum]) where transitions are classic 0/1 or unbounded knapsack / subset-sum updates over a sum or capacity dimension.
- Use of an auxiliary buffer tmp[ ] that is fully zeroed and then copied back into dp[ ] each iteration, combined with forward iteration over DP indices.
- Fixed global bounds for a sum/capacity dimension (e.g., 1e5, 5000, 2500) independent of the true reachable maximum from inputs, with loops always iterating the full range.
- Per-testcase memset over large DP tables (O(n * S)) even though only a portion is touched by transitions.
- Bitmask or extra small dimension k (k <= n or small constant) where dp[k][mask] ultimately collapses to a single aggregate value per mask, or intermediate k-states are only used via simple sums/complements.
- Triple nested loops whose innermost loop scans an entire DP row or plane while only a shrinking/growing prefix of indices can be reachable given the processed items.
- Knapsack-like DPs using width defined by a global maximum (e.g., 100000) while actual capacity or reachable sum is significantly smaller.

## Steps
1. Analyze DP dependencies: Confirm that the DP dimension representing time/step/index i only depends on a small fixed set of previous layers (often just i-1).
2. Analyze DP dependencies: Identify which dimension is the main numeric state (sum, capacity, count, distance) and its true reachable bound from input constraints (e.g., total sum of values, maximum capacity, prefix sums).
3. Tighten state bounds: Replace fixed global ranges (e.g., 0..100000, 0..5000) with tight bounds derived from input: S' = sum of a[i], capacity w, or Vmax * n.
4. Tighten state bounds: If sums can be negative after shifting, introduce an offset OFF and represent dp[index] as dp[sum + OFF] with width W = max_sum
5. Tighten state bounds: min_sum + 1.
6. Tighten state bounds: Optionally maintain current reachable min/max indices per iteration to further narrow inner loops.
7. Compress iteration dimension (rolling arrays): Replace f[i][*] with two rows dp_prev[*], dp_cur[*] or a single dp[*] updated in-place when safe.
8. Compress iteration dimension (rolling arrays): For classic 0/1 knapsack or subset-counting, keep a single 1D dp over sum/capacity and iterate the sum dimension in decreasing order so each item is used at most once.

## Complexity
- Time: (pattern dependent)
- Space: Reduces DP memory from O(dim1 * dim2 * ), often O(n * S) or O(n^2 * S), down to O(S') or O(K) or O(2^D) as appropriate. Typical patterns: 2D knapsack dp[n][W] -> dp[W]; 3D subset DP f[i][j][k] -> dp[j][k]; dp[steps][colors] -> two 1D

## Pitfalls
- Incorrect iteration order when switching to 1D 0/1 knapsack: iterating sums increasing instead of decreasing, which allows using an item more than once per layer.
- Underestimating the reachable sum/capacity range when tightening bounds, leading to missing valid states or accessing dp out of range (especially with negative shifts).
- Compressing the step dimension to a single row when transitions depend on more than one previous layer (e.g., i-1 and i-2), silently breaking the recurrence.
- Removing an auxiliary dimension (such as k in dp[k][mask]) without carefully rederiving the probabilistic or combinatorial formula, leading to wrong aggregation.
- Using fixed global maximum widths for DP arrays even after refactor, and then still iterating over the full range, losing most of the intended speedup.
- Failing to guard transitions from unreachable states when using sentinel values (e.g., -1 or INF) and thus doing unnecessary work or risking overflow.
- Mixing shifted indices and offsets incorrectly when supporting negative sums, causing misalignment between logical sums and array positions.
- Relying on recursion after converting to bottom-up DP, keeping both recursion overhead and large tables instead of removing the recursive formulation entirely.

## When not to use
- When the DP recurrence genuinely depends on many previous layers (e.g., DP[i] uses DP[i-1], DP[i-2], , DP[i-L] with large L), and the extra dimension cannot be encoded in a small fixed state; rolling to a single row
- When the DP state space is already minimal and tightly bounded by input constraints, and profiling shows the bottleneck is elsewhere (e.g., heavy math per state rather than memory traffic).
- When the sum/capacity dimension is extremely small (e.g., <= 50), so that memory and initialization costs for 2D DP are negligible and compression adds code complexity without measurable benefit.
- When correctness relies on storing the full DP history for reconstruction of paths, counts per step, or non-local constraints, and you cannot reconstruct solutions from compressed state alone.
- When the problem constraints make the small-dimension exponential alternative (e.g., 2^D enumeration) too large (D ≈ 20+), so replacing pseudo-polynomial DP with bitmask enumeration would be slower or infeasible.
- When applying algebraic reductions (e.g., collapsing dp[k][mask] to dp[mask]) is non-trivial and you cannot formally justify the transformation; in such cases, prefer the clearer higher-dimensional DP.

## Minimal example
Before:
```cpp
// O014 focus: state
int best = 0;
for (int mask = 0; mask < (1 << n); ++mask)
  best = max(best, score(mask));
```
After:
```cpp
// optimized for state
int odd = 0;
for (int x : a) odd += x & 1;
int best = closed_form_from_counts((int)a.size(), odd);
// replace subset scan with parity/count reasoning
```
