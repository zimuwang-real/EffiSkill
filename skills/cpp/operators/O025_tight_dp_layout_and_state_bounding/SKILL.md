---
skill_id: O025
type: operator
language: cpp
family: dp
name: Tight Dp Layout And State Bounding
description: Refactor dynamic programming and memoization code to keep the same asymptotic complexity but substantially reduce
  constants and memory usage. This operator focuses on (1) tightening DP state ranges to input-driven or logically minimal
  bounds, (2) simplifying state representation (e.g., folding visited flags into the DP table, switching to boolean or bit-packed
  storage when only reachability is needed), (3) using
tags:
- dp-optimization
- state-space-bounding
- memory-optimization
- cache-locality
- memoization
- data-layout
- boolean-dp
- sentinel-values
- constant-factor-optimization
- io-optimization
triggers:
- DP or memoization tables sized by loose magic constants (e.g., 30020, 101010, 600000) instead of tight bounds derived from
  input constraints.
- Secondary DP dimension grows from sums or unconstrained values even though the logic only needs states up to a small cap
  (e.g., values beyond 100 have no effect).
- Parallel vis[][] (or visited[] arrays) exist with the same dimensions as dp[][] just to track computed states.
- Use of 64-bit or long long DP cells where all values are bounded well within 32-bit int, especially with a moderate modulus.
- DP states logically represent reachability or boolean flags, but storage uses int/long long instead of bool or bitsets.
- Nested DP loops access vector<pair< >> or other AoS structures in tight inner loops, with dynamic push_back during preprocessing.
- Very large DP arrays (especially multi-dimensional) cause MLE, paging, or profiler shows most time in memory operations
  on them.
- Use of memset with a non-byte sentinel value on non-char DP arrays to represent INF or uninitialized states.
---

## When to use
- DP or memoization tables sized by loose magic constants (e.g., 30020, 101010, 600000) instead of tight bounds derived from input constraints.
- Secondary DP dimension grows from sums or unconstrained values even though the logic only needs states up to a small cap (e.g., values beyond 100 have no effect).
- Parallel vis[][] (or visited[] arrays) exist with the same dimensions as dp[][] just to track computed states.
- Use of 64-bit or long long DP cells where all values are bounded well within 32-bit int, especially with a moderate modulus.
- DP states logically represent reachability or boolean flags, but storage uses int/long long instead of bool or bitsets.
- Nested DP loops access vector<pair< >> or other AoS structures in tight inner loops, with dynamic push_back during preprocessing.
- Very large DP arrays (especially multi-dimensional) cause MLE, paging, or profiler shows most time in memory operations on them.
- Use of memset with a non-byte sentinel value on non-char DP arrays to represent INF or uninitialized states.

## Steps
1. Identify tight bounds for each DP dimension: Derive maximum needed sizes from problem constraints instead of using loose magic numbers (e.g., replace dp[n+1][30020] with dp[n+1][h+1] when h is an input bound).
2. Identify tight bounds for each DP dimension: When some dimension is logically capped (e.g., experience/energy/score beyond 100 is equivalent), clamp transitions and indices to that cap and allocate dp accordingly.
3. Shrink over-provisioned DP dimensions: Replace oversized arrays like dp[101010][10] with dp[h_max][mask_range] when h_max and mask_range are known (e.g., bitmask only uses 0..7, so second dimension 8 is sufficient).
4. Shrink over-provisioned DP dimensions: For fixed small dimensions (n, K ≈ few hundred), keep DP tables to exactly those ranges, not a larger compile-time constant if n < that constant.
5. Refine state representation using sentinels instead of separate visited flags: If you have dp[][] plus vis[][] for memoization, remove vis and encode "uncomputed" using a dedicated sentinel value INF in dp.
6. Refine state representation using sentinels instead of separate visited flags: Initialize dp states to INF (strictly greater than any achievable cost) and treat dp[state] != INF as "computed".
7. Refine state representation using sentinels instead of separate visited flags: Adjust recursive or iterative checks from `if (vis[state])` to `if (dp[state] != INF)` while keeping base cases and transitions unchanged.
8. Switch to boolean or bit-packed storage for reachability DP: For DP states that are purely boolean (reachable/unreachable), change the table type from int/long long to bool, bitset, or vector<bool>.

## Complexity
- Time: (pattern dependent)
- Space: Reduces space by shrinking over-provisioned dimensions, moving from long long to int where safe, and using boolean/bit-packed representations for reachability. Typical reductions range from modest (2–4×) to substantial (8–64×) in bytes

## Pitfalls
- Choosing an INF sentinel that can be reached by the DP, causing confusion between "uncomputed" and "valid but impossible" states. Always ensure INF > max possible real value.
- Using memset with a numeric INF directly on int/long long arrays (e.g., memset(dp, INF, sizeof(dp))) and assuming it sets the correct integer values. For non-char types, only 0x00 and 0xFF patterns are safe; otherwise
- Switching to int from long long without carefully re-evaluating all upper bounds (sum of weights, combinatorial counts, etc.), leading to silent overflow.
- Switching to vector<bool> or bitsets for DP and then attempting arithmetic on elements (e.g., dp[i][j]++), which changes semantics compared to int-based DP.
- Over-tightening DP bounds (e.g., clamping a dimension at 100 when rare but valid states require larger values), leading to incorrect answers.
- Reducing DP dimensions based only on observed tests rather than proven constraints or invariants, which can mis-handle adversarial cases.
- Using non-standard variable-length arrays (e.g., int dp[n][h]) on the stack, risking stack overflow and relying on compiler extensions instead of standard C++ containers or heap allocations.
- Blindly converting parallel vis[][] + dp[][] to a sentinel-based scheme but forgetting to adjust base cases or transitions that depended on vis semantics.

## When not to use
- When the DP is not the primary bottleneck (e.g., the algorithm is asymptotically too slow, or another part such as sorting or graph traversal dominates runtime). In such cases, focus on algorithmic improvements first.
- When DP values can approach or exceed 32-bit limits (e.g., large combinatorial counts without modulus, huge sums), making a switch from long long to int unsafe.
- When the DP logically requires full-range states and there is no sound argument to cap a dimension (e.g., unbounded knapsack where large values matter). Artificially bounding states risks wrong answers.
- When code clarity is more important than micro-optimizations (education, code review, or problems with very loose time/memory limits). Heavily optimized layouts (SoA, packed bits) can hurt readability.
- When relying on language features or libraries that conflict with the proposed changes (e.g., a framework assumes vector<int> and specific semantics for debugging or instrumentation).
- When you cannot guarantee safe bounds on auxiliary arrays and buffers but also cannot increase them due to strict memory limits; in such cases, reconsider the algorithmic approach instead of aggressive low-level tuning.

## Minimal example
Before:
```cpp
// O025 focus: tight
vector<vector<int>> dp(n + 1, vector<int>(W + 1, 0));
for (int i = 1; i <= n; ++i)
  for (int w = 0; w <= W; ++w)
    dp[i][w] = max(dp[i - 1][w], w >= wt[i] ? dp[i - 1][w - wt[i]] + val[i] : 0);
```
After:
```cpp
// optimized for tight
vector<int> dp(W + 1, 0);
for (int i = 1; i <= n; ++i)
  for (int w = W; w >= wt[i]; --w)
    dp[w] = max(dp[w], dp[w - wt[i]] + val[i]);
```
