---
skill_id: O017
type: operator
language: cpp
family: dp
name: Sliding Window And Prefix Min DPRefactor
description: Refactor DP or counting logic that currently uses segment trees, Fenwick trees, multisets, or maps for range
  minima/sums over indices into linear-time or lower-constant-factor solutions based on prefix sums, prefix/suffix minima,
  two-pointers, and monotonic queues. This operator targets patterns where transitions depend on contiguous index ranges whose
  boundaries move monotonically with the outer loop index
tags:
- dynamic_programming
- sliding_window
- two_pointers
- prefix_sums
- prefix_min
- suffix_min
- monotonic_queue
- range_min_query
- range_sum_query
- geometry_transform
triggers:
- DP transition depends on sum or min over a contiguous range of previous states dp[l..r] where l and r move monotonically
  with i (sliding window or growing/shrinking prefix/suffix).
- Segment tree or Fenwick tree is used only for range sums/minima on a 1D array with point updates in increasing index order;
  no arbitrary updates or queries on past indices are needed.
- Constraints of the form r - l < K or 2 * (a[i] - a[j+1]) <= T define a contiguous set of valid predecessors for each i,
  and as i increases the left boundary of this set moves only forward.
- Range queries in DP or counting logic always involve either [1..i], [i..n], [i-L..i-R], or [l[i]..i] where l[i] is non-decreasing,
  suggesting prefix sums or prefix/suffix minima can replace trees.
- Use of multiset or ordered_set in the innermost DP loop merely to maintain the minimum (or maximum) over an active index
  set that changes monotonically (indices only activated once and later deactivated once).
- Geometry or interval problems where the result is a global extremum (e.g., maximum Manhattan distance, extrema of ±x ± y,
  or perimeter ordering) but the code uses sorting + segment trees or complex comparators instead
- Presence of BIT or segment tree nodes storing affine transforms of DP states (like f[j] ± a[j] ± 2*a[j+1]) and DP transitions
  of the form f[i] = min_j (f[j] + linear_function(i, j)), which suggests that running minima
- Top-down recursive DP with segment tree RMQ and binary search per state over up to n ≈ 1e5 indices, where an equivalent
  bottom-up iterative DP with prefix sums and Fenwick or sliding-window logic exists.
---

## When to use
- DP transition depends on sum or min over a contiguous range of previous states dp[l..r] where l and r move monotonically with i (sliding window or growing/shrinking prefix/suffix).
- Segment tree or Fenwick tree is used only for range sums/minima on a 1D array with point updates in increasing index order; no arbitrary updates or queries on past indices are needed.
- Constraints of the form r - l < K or 2 * (a[i] - a[j+1]) <= T define a contiguous set of valid predecessors for each i, and as i increases the left boundary of this set moves only forward.
- Range queries in DP or counting logic always involve either [1..i], [i..n], [i-L..i-R], or [l[i]..i] where l[i] is non-decreasing, suggesting prefix sums or prefix/suffix minima can replace trees.
- Use of multiset or ordered_set in the innermost DP loop merely to maintain the minimum (or maximum) over an active index set that changes monotonically (indices only activated once and later deactivated once).
- Geometry or interval problems where the result is a global extremum (e.g., maximum Manhattan distance, extrema of ±x ± y, or perimeter ordering) but the code uses sorting + segment trees or complex comparators instead
- Presence of BIT or segment tree nodes storing affine transforms of DP states (like f[j] ± a[j] ± 2*a[j+1]) and DP transitions of the form f[i] = min_j (f[j] + linear_function(i, j)), which suggests that running minima
- Top-down recursive DP with segment tree RMQ and binary search per state over up to n ≈ 1e5 indices, where an equivalent bottom-up iterative DP with prefix sums and Fenwick or sliding-window logic exists.

## Steps
1. Re-derive the DP or counting recurrence: Explicitly write dp[i] in terms of previous states or prefix information, e.g., dp[i] = sum_{j in [L(i), R(i)]} dp[j] or dp[i] = min_{j in [L(i), R(i)]} (dp[j] + g(i, j)).
2. Re-derive the DP or counting recurrence: Identify whether L(i) and R(i) form a contiguous range in index space and how they evolve with i.
3. Detect structural monotonicity and prefix-friendliness: Check that as i increases, L(i) and/or R(i) move monotonically (e.g., L(i+1) >= L(i)).
4. Detect structural monotonicity and prefix-friendliness: Confirm that operations over dp[j] in [L(i), R(i)] are associative/commutative (sum, min, max) and independent from query order.
5. Detect structural monotonicity and prefix-friendliness: a[j+1]) <= T, r
6. Detect structural monotonicity and prefix-friendliness: l < K), verify that the valid predecessor indices for each i form a single contiguous block.
7. Replace segment-tree/Fenwick range sums with prefix sums: If transitions require range sums over dp on a growing index: • Maintain prefix[i] = (prefix[i-1] + dp[i]) % MOD. • Compute sum(dp[l..r]) as prefix[r]
8. Replace segment-tree/Fenwick range sums with prefix sums: prefix[l-1] (with modular fix-up if needed).

## Complexity
- Time: (pattern dependent)
- Space: Reduces from O(n)–O(4n) plus auxiliary tree/multiset/map overhead to O(n) arrays and O(1)–O(k) extra scalars/queues. Removes large 4*n segment-tree arrays, BITs, and per-key vectors, typically leading to more cache-friendly linear layouts.

## Pitfalls
- Incorrect window boundaries and off-by-one errors when translating constraints (r - l < K, 2 * (a[i] - a[j+1]) <= T, etc.) into indices for prefix sums or two-pointers.
- Using prefix sums or prefix minima with inconsistent indexing (0-based vs 1-based), leading to missing the first element or reading from index 0 when uninitialized.
- Assuming monotonicity of L(i)/R(i) without proof; if the valid predecessor set is not truly monotone, a two-pointer window or monotonic queue will miss candidates that a segment tree would have captured.
- Maintaining a monotonic queue with the wrong key (e.g., dp[j] instead of dp[j] - a[j]) so that dominance comparisons are incorrect and optimal states are discarded.
- Forgetting to remove expired indices from the front of a deque when they leave the sliding window, which yields incorrect minima and underestimates costs or overcounts solutions.
- Breaking problem semantics when changing from tree-based counting to prefix sums (especially with modular arithmetic): neglecting to apply modulo after each prefix or difference can overflow or produce negative results.
- Incorrectly translating geometric identities (e.g., Manhattan distance via ±x ± y) or perimeter mappings, causing subtle errors on boundaries or corners of rectangles.
- Over-tightening type ranges: using 32-bit ints for sums or coordinate transforms that can exceed int limits; conversely, using long long everywhere unnecessarily, which can increase constant factors.

## When not to use
- When the operation over the range is non-associative or non-idempotent, or depends on complex order-sensitive aggregation that cannot be represented by simple prefix sums or minima.
- When there are many interleaved, arbitrary-range queries and updates that cannot be expressed as incrementally shifting windows or prefixes; typical fully dynamic RMQ/RMQ-with-updates scenarios.
- When index sets are not contiguous, such as arbitrary sparse subsets or multi-dimensional ranges, where prefix sums/one-dimensional sliding windows do not capture the structure.
- When constraints on candidate indices do not yield monotone L(i) and R(i) (the optimal predecessor index can move backward as i increases) or when the best j is not guaranteed to lie in a contiguous window
- When correctness relies on full generality and robustness of ordered_set/multiset semantics (e.g., arbitrary insert/erase of non-monotone events) and these cannot be rephrased as a precomputed l[i] with a forward-only
- When coordinate ranges are extremely large and cannot be normalized or compressed cheaply, but the reference solution explicitly expects a range-based data structure like a segment tree over compressed indices.

## Minimal example
Before:
```cpp
// O017 focus: sliding
vector<vector<int>> dp(n + 1, vector<int>(W + 1, 0));
for (int i = 1; i <= n; ++i)
  for (int w = 0; w <= W; ++w)
    dp[i][w] = max(dp[i - 1][w], w >= wt[i] ? dp[i - 1][w - wt[i]] + val[i] : 0);
```
After:
```cpp
// optimized for sliding
vector<int> dp(W + 1, 0);
for (int i = 1; i <= n; ++i)
  for (int w = W; w >= wt[i]; --w)
    dp[w] = max(dp[w], dp[w - wt[i]] + val[i]);
```
