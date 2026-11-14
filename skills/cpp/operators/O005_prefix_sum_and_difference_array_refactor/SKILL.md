---
skill_id: O005
type: operator
language: cpp
family: dp
name: Prefix Sum And Difference Array Refactor
description: Reusable optimization pattern distilled from weighted traces.
tags:
- prefix_sums
- difference_array
- intervals
- offline_queries
- counting
- DP_optimization
- array_based
- constant_factor
- Fenwick_tree_replacement
- two_pointers
triggers:
- A Fenwick tree or segment tree used only for point updates with final offline inspection, where queries appear as query(i)
  - query(i-1) or range-add/point-query and there are no truly online constraints.
- Range sums or interval counts computed by looping from L to R inside another loop (e.g., getsum(L,R) with a for loop), especially
  inside DP transitions or nested over all pairs of endpoints.
- Brute-force scanning of all candidates in a value or index domain (e.g., for v in 1..U) combined with repeated binary searches
  or scans over the same sorted array.
- Interval problems where all operations are known upfront (no updates after queries) and logic only asks for counts inside
  static intervals or rectangles in index/value space.
- DP over intervals or sums where transitions require summing over a contiguous range of indices or values and a prefix-sum-like
  array already exists or could be added cheaply.
- Nested loops over n combined with a BIT/segment tree for each iteration producing O(n log n) or worse, when the actual needed
  information is just per-position frequency or prefix/suffix aggregates.
- Use of a large occupancy array or per-coordinate marking (e.g., map[x]++ in [L,R]) followed by a full scan when only the
  total or per-interval counts are required.
- Small bounded dimensions (e.g., value range <= 1000 or exponent <= 400) where a 1D/2D frequency table plus prefix sums can
  replace binary searches in tight inner loops.
---

## When to use
- A Fenwick tree or segment tree used only for point updates with final offline inspection, where queries appear as query(i) - query(i-1) or range-add/point-query and there are no truly online constraints.
- Range sums or interval counts computed by looping from L to R inside another loop (e.g., getsum(L,R) with a for loop), especially inside DP transitions or nested over all pairs of endpoints.
- Brute-force scanning of all candidates in a value or index domain (e.g., for v in 1..U) combined with repeated binary searches or scans over the same sorted array.
- Interval problems where all operations are known upfront (no updates after queries) and logic only asks for counts inside static intervals or rectangles in index/value space.
- DP over intervals or sums where transitions require summing over a contiguous range of indices or values and a prefix-sum-like array already exists or could be added cheaply.
- Nested loops over n combined with a BIT/segment tree for each iteration producing O(n log n) or worse, when the actual needed information is just per-position frequency or prefix/suffix aggregates.
- Use of a large occupancy array or per-coordinate marking (e.g., map[x]++ in [L,R]) followed by a full scan when only the total or per-interval counts are required.
- Small bounded dimensions (e.g., value range <= 1000 or exponent <= 400) where a 1D/2D frequency table plus prefix sums can replace binary searches in tight inner loops.

## Steps
1. Identify aggregate-only dependencies: Confirm there are no true online operations: all updates are applied before any query that depends on them, or the final answer only uses final counts.
2. Choose an appropriate aggregate structure: For 1D static counts or sums on indices: use a prefix sum array pref[i] = sum_{1..i} a[i]. Range sums become O(1): sum(L,R) = pref[R]
3. Choose an appropriate aggregate structure: pref[L-1].
4. Choose an appropriate aggregate structure: For 1D range-add/point-query or point-add/range-query patterns: use a difference array diff, doing diff[L]+=v, diff[R+1]-=v and a final prefix pass.
5. Choose an appropriate aggregate structure: For 2D static counting (e.g., intervals by (start,end) or points in grid cells with bounded coordinates): use a 2D frequency grid freq[x][y] and build 2D prefix sums for O(1) rectangle queries.
6. Choose an appropriate aggregate structure: For small bounded value ranges: build frequency or DP tables freq[value] or freq[x][y] and prefix sums over the bounded dimension instead of binary searches.
7. Choose an appropriate aggregate structure: For DP over ranges: precompute prefix sums of DP layers so that transitions of the form sum_{k in [L..R]} dp[i-1][k] become O(1).
8. Replace heavy structures with arrays: If a Fenwick tree is used only to store per-index counts and queried as query(i)

## Complexity
- Time: (pattern dependent)
- Space: Generally O(n) or O(n + q) for 1D prefix/difference arrays, sometimes O(n^2) or O(k^2) when trading memory for speed on small-bounded dimensions. Replacing trees/BITs and scattered vectors with flat arrays often reduces memory

## Pitfalls
- Off-by-one errors in prefix sums and difference arrays, especially mixing 0-based and 1-based indexing (e.g., using pref[R] - pref[L] instead of pref[R] - pref[L-1] when L is 1-based).
- Forgetting to guard the right-side decrement in difference arrays (writing diff[R+1]-- when R+1 exceeds the array size) and causing out-of-bounds writes.
- Building 2D prefix sums with the wrong recurrence or order, or double-subtracting/forgetting the overlap term (mp[i][j] += mp[i-1][j] + mp[i][j-1] - mp[i-1][j-1]).
- Degrading asymptotics by recomputing prefix or difference arrays inside loops instead of once upfront (e.g., rebuilding prefix sums per query).
- Underestimating memory usage when switching to dense 2D tables; for n or value-range too large, O(n^2) space can blow limits or thrash caches.
- Losing necessary online behavior: attempting to replace a needed online BIT/segment tree with offline prefix sums where queries depend on interleaved updates.
- Overflow in accumulated sums or counts when switching to prefix sums without promoting the accumulator to 64-bit (long long).
- Not leveraging ordering: failing to sort when needed, which breaks assumptions used in prefix/suffix schemes or two-pointers.

## When not to use
- When updates and queries are fully online and interleaved, and you must answer queries after each update without knowing future operations; BIT/segment trees may then be necessary.
- When n or the relevant dimension is so large that O(n^2) or O(U^2) memory required for a dense 2D prefix-sum grid is infeasible (e.g., n ~ 2e5 on both axes). In such cases, stick to O(n log n) structures or sparse
- When the range queries are not over contiguous segments (e.g., arbitrary subsets or dynamically changing ranges) and cannot be expressed via simple prefix sums or difference arrays.
- When conditions are highly non-linear or depend on complex ordering beyond aggregate counts/sums (e.g., lexicographic constraints, dynamic medians with deletions) where trees or heaps are the appropriate tool.
- When value domains are huge and unbounded, making coordinate compression or dense frequency tables impractical or error-prone without careful design.
- For problems where recursion depth and state-space search are genuinely required (e.g., graph traversal with non-trivial constraints) and there is no clear aggregation-based reformulation.

## Minimal example
Before:
```cpp
// O005 focus: prefix
vector<vector<int>> dp(n + 1, vector<int>(W + 1, 0));
for (int i = 1; i <= n; ++i)
  for (int w = 0; w <= W; ++w)
    dp[i][w] = max(dp[i - 1][w], w >= wt[i] ? dp[i - 1][w - wt[i]] + val[i] : 0);
```
After:
```cpp
// optimized for prefix
vector<int> dp(W + 1, 0);
for (int i = 1; i <= n; ++i)
  for (int w = W; w >= wt[i]; --w)
    dp[w] = max(dp[w], dp[w - wt[i]] + val[i]);
```
