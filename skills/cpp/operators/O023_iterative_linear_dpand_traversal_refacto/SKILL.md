---
skill_id: O023
type: operator
language: cpp
family: graph
name: Iterative Linear DPAnd Traversal Refactor
description: Reusable optimization pattern distilled from weighted traces.
tags:
- dynamic_programming
- 1d-dp
- tree-dp
- rerooting-dp
- dfs-to-iterative
- recursion-removal
- implementation_optimization
- memory_layout
- io_optimization
- type_selection
triggers:
- Top-down recursive DP f(i) with memoization where transitions only reference nearby indices such as i+1, i+2, or i-1, i-2
  (classic linear DP patterns).
- DP states indexed by a small number of integer parameters (1D or low-dimensional) where dependencies form a simple partial
  order that can be linearized into nested loops.
- Recursive DFS over a tree or DAG with depth potentially proportional to n, especially when n can reach 1e5 or more, causing
  stack-overflow risk or heavy call overhead.
- Large fixed global buffers (e.g., arrays sized to 1e6 or 1e7) clearly exceeding the true constraints inferred from input
  limits, causing unnecessary memory usage and initialization cost.
- Use of std::vector<bool> or other bit-packed containers in hot DP loops, leading to slow proxy access compared to plain
  arrays.
- Use of 64-bit long long for all values when constraints imply 32-bit int is sufficient, or conversely use of int where sums
  of many terms may overflow 32-bit range.
- High profiler samples or visible bottlenecks in recursive DP/DFS functions and their small helpers (e.g., has(), gs()) rather
  than in the DP transitions themselves.
- I/O dominated solutions using unoptimized iostreams (cin/cout) or mixed C and C++ I/O for problems with large linear input
  where algorithmic complexity is already optimal.
---

## When to use
- Top-down recursive DP f(i) with memoization where transitions only reference nearby indices such as i+1, i+2, or i-1, i-2 (classic linear DP patterns).
- DP states indexed by a small number of integer parameters (1D or low-dimensional) where dependencies form a simple partial order that can be linearized into nested loops.
- Recursive DFS over a tree or DAG with depth potentially proportional to n, especially when n can reach 1e5 or more, causing stack-overflow risk or heavy call overhead.
- Large fixed global buffers (e.g., arrays sized to 1e6 or 1e7) clearly exceeding the true constraints inferred from input limits, causing unnecessary memory usage and initialization cost.
- Use of std::vector<bool> or other bit-packed containers in hot DP loops, leading to slow proxy access compared to plain arrays.
- Use of 64-bit long long for all values when constraints imply 32-bit int is sufficient, or conversely use of int where sums of many terms may overflow 32-bit range.
- High profiler samples or visible bottlenecks in recursive DP/DFS functions and their small helpers (e.g., has(), gs()) rather than in the DP transitions themselves.
- I/O dominated solutions using unoptimized iostreams (cin/cout) or mixed C and C++ I/O for problems with large linear input where algorithmic complexity is already optimal.

## Steps
1. Detect linear or low-dimensional DP structure: Verify that each DP state depends only on states with strictly smaller or nearby indices (e.g., f[i] depends on f[i-1], f[i-2]).
2. Detect linear or low-dimensional DP structure: For tree or DAG problems, ensure dependencies follow graph edges and can be processed in topological or DFS order.
3. Redesign the DP as bottom-up iteration: Replace recursive f(i) with an array dp[i] and derive explicit iterative transitions matching the original recurrence.
4. Redesign the DP as bottom-up iteration: For linear DP, choose an order (forward or backward) that respects dependencies and write a single loop (or small nested loops) to fill dp.
5. Redesign the DP as bottom-up iteration: For multimodal small-parameter DP (e.g., two counters A, B with small bounds), explicitly enumerate all feasible combinations instead of maintaining an oversized DP over redundant dimensions.
6. Remove recursion in traversals and DP evaluation: For simple 1D or small-D DP, eliminate recursion entirely and compute in loops.
7. Remove recursion in traversals and DP evaluation: For tree or graph problems where recursion depth may reach O(n), convert DFS to an explicit stack-based traversal or use an iterative rerooting framework.
8. Remove recursion in traversals and DP evaluation: For DAG processing, replace Kahn’s indegree-based algorithm with DFS-based topological sort or vice versa, favoring the simpler structure with fewer per-edge operations.

## Complexity
- Time: Typically preserves the original asymptotic complexity (e.g., O(n), O(n*k), O(V+E), O(n^6) for fixed high-dimensional DP) but removes recursion overhead and reduces constant factors via streamlined loops, better memory locality, and more
- Space: Reduces or maintains space complexity: from overprovisioned globals (e.g., O(1e6–1e7)) down to O(n) or O(problem-specific state count). Uses tightly sized arrays and local buffers, improves cache usage, and removes recursion stack

## Pitfalls
- Incorrect base-case translation: mis-setting dp[0], dp[1], dp[N-1], or dp[N-2], or mishandling n=1 or n=2 edge cases when switching from recursion to iteration.
- Off-by-one errors when moving from 1-based to 0-based indexing (or vice versa) in DP arrays, especially in transitions that reference i±1 or i±2.
- Accessing out-of-bounds indices in iterative DP loops because loop limits were not adjusted to align with the recurrence’s valid range.
- Forgetting to handle the second jump / alternative transition near array boundaries (e.g., reading dp[i+2] when i+2 == n or i+2 > n).
- Changing integer width without full range analysis: using int where sums can overflow, or using long long everywhere when not needed, harming performance without benefit.
- Removing memoization but not fully covering the state-space in iterative loops, leaving some dp entries uninitialized or at default sentinel values.
- In tree and graph refactors, failing to reset adjacency lists and auxiliary arrays between test cases, leading to stale edges and incorrect results.
- When replacing Kahn’s algorithm with DFS-based topo, ignoring recursion depth limits and causing stack overflow on large or skewed DAGs; or forgetting to reverse the postorder list to get a valid topological order.

## When not to use
- When the existing recursive solution already runs well within time and memory limits and recursion depth is provably shallow (e.g., logarithmic-depth divide-and-conquer) so refactoring adds complexity without benefit.
- For DPs where the state dependencies do not admit a clear topological or linear order (e.g., states form cycles or rely on non-local transitions) and recursion is the clearest correct expression.
- When memory is not a constraint and readability of a short recursive solution is more valuable than marginal constant-factor improvements, such as in very small constraint problems.
- For problems where stack usage is deliberately managed (e.g., custom stack-extension macros or compiler-specific options) and recursion depth is known to be safe and convenient.
- When a higher-level algorithmic change (e.g., moving from O(n^2) to O(n log n)) is required to pass constraints; applying this operator will not fix an asymptotically suboptimal DP.
- If converting to iterative or rerooting patterns significantly obscures the solution logic, increasing the chance of mistakes under time pressure, and the original code already meets performance requirements.

## Minimal example
Before:
```cpp
int n; long long dp[200000];
long long f(int i){
    if(i <= 1) return 1;
    long long &res = dp[i];
    if(res != -1) return res;
    return res = (f(i-1) + f(i-2)) % 1000000007;
}
// used as: memset(dp, -1, sizeof dp); cin >> n; cout << f(n) << '\n';
```
After:
```cpp
int n; long long dp[200000];
// bottom-up linear DP: no recursion, better cache behavior
// f[i] = number of ways, f[i] = f[i-1] + f[i-2]
cin >> n; dp[0] = dp[1] = 1;
for(int i = 2; i <= n; ++i)
    dp[i] = (dp[i-1] + dp[i-2]) % 1000000007;
cout << dp[n] << '\n';
```
