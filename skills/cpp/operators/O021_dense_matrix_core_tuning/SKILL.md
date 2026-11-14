---
skill_id: O021
type: operator
language: cpp
family: graph
name: Dense Matrix Core Tuning
description: 'Optimization pattern for small-to-medium dense matrix kernels (Floyd–Warshall-style APSP, distance-matrix checks,
  dense DP on graphs, GF(2) Gaussian elimination, and matrix exponentiation). The operator focuses on reducing constant factors
  and memory footprint without changing asymptotic complexity: tightening matrix bounds to real constraints, improving memory
  layout and access order, eliminating redundant'
tags:
- optimization
- dense-matrix
- floyd-warshall
- all-pairs-shortest-path
- gaussian-elimination
- bitset
- matrix-exponentiation
- graph
- DP
- I/O
triggers:
- Using a large fixed-size adjacency or distance matrix (e.g., 1000x1000 or 1100x1100) when the actual number of vertices
  or labels is tiny (<= ~10–100).
- Initialization loops that always iterate over the full static bound instead of the actual used dimension (e.g., always 0..MAXN
  instead of 0..n-1).
- O(N^3) triple loops (Floyd–Warshall, dense DP) where profiling shows time dominated by memory traffic, branching inside
  the innermost loop, or redundant matrix accesses.
- Distance or adjacency matrices represented as int/long long for boolean or GF(2) values, with scalar XOR in triple loops.
- Multiple almost-identical matrices (e.g., separate L and S graphs, or A/B/C for distances and redundancy) updated in the
  same loops.
- All-pairs shortest paths implemented via repeated single-source runs (e.g., Dijkstra/Bellman-Ford from every node) on very
  small dense graphs.
- Large 3D DP or distance tensors (like C×N×N) mostly filled with INF, with heavy initialization and poor locality.
- Matrix exponentiation routines where matrix objects are passed by value to operator* / operator*=, causing O(N² log K) copying
  overhead.
---

## When to use
- Using a large fixed-size adjacency or distance matrix (e.g., 1000x1000 or 1100x1100) when the actual number of vertices or labels is tiny (<= ~10–100).
- Initialization loops that always iterate over the full static bound instead of the actual used dimension (e.g., always 0..MAXN instead of 0..n-1).
- O(N^3) triple loops (Floyd–Warshall, dense DP) where profiling shows time dominated by memory traffic, branching inside the innermost loop, or redundant matrix accesses.
- Distance or adjacency matrices represented as int/long long for boolean or GF(2) values, with scalar XOR in triple loops.
- Multiple almost-identical matrices (e.g., separate L and S graphs, or A/B/C for distances and redundancy) updated in the same loops.
- All-pairs shortest paths implemented via repeated single-source runs (e.g., Dijkstra/Bellman-Ford from every node) on very small dense graphs.
- Large 3D DP or distance tensors (like C×N×N) mostly filled with INF, with heavy initialization and poor locality.
- Matrix exponentiation routines where matrix objects are passed by value to operator* / operator*=, causing O(N² log K) copying overhead.

## Steps
1. Apply the core transformation while preserving correctness and interface.

## Complexity
- Time: Typically preserves asymptotic complexity (e.g., O(N^3) for Floyd–Warshall, O(N^3/W) for bitset-based GF(2) elimination, O(N^3 log K) for matrix exponentiation, O(F·E log V) for refactored min-cost flow), but substantially reduces
- Space: Reduces from overly conservative allocations (e.g., multiple N×N long long matrices, large static MAX_V arrays) toward tight O(N^2) or O(N^2/W) storage with small constant factors; often eliminates auxiliary matrices or large unused

## Pitfalls
- Keeping oversized static arrays (e.g., 1000x1000) even when constraints guarantee much smaller n, causing unnecessary initialization cost and cache misses.
- Running repeated single-source shortest paths over a tiny dense graph instead of a single Floyd–Warshall, or recomputing closures via DFS after already running Floyd–Warshall.
- Leaving branches like (i == j) or index guards (i == k || j == k) inside tight O(N²)/O(N³) loops instead of structuring initialization or sentinels to avoid them.
- Using int matrices for boolean or GF(2) data, which wastes memory and prevents leveraging bit-parallel operations.
- Precomputing large global tables (e.g., cost[d] for all d up to a big limit) that are never fully used, inflating memory and time.
- Implementing matrix exponentiation with operator* or operator*= taking arguments by value, leading to O(N² log K) copying overhead.
- Using int for distances or total sums where values can overflow (e.g., many cells times large costs) and not guarding INF + INF additions.
- Failing to early-exit on detected inconsistencies in distance matrices, wasting the remaining O(N³) iterations.

## When not to use
- When the problem graph is large and sparse (e.g., N >= 1e5, M ~ N), where dense O(N^2)/O(N^3) matrix algorithms are fundamentally inappropriate; use adjacency lists and sparse algorithms instead.
- When constraints demand generic scalability and the true maximum N may approach large static bounds; over-tightening matrix sizes to a smaller guessed bound risks overflow or out-of-bounds indexing.
- When the main bottleneck is fundamentally I/O or external (e.g., interactive problems, network latency) and internal O(N²)/O(N³) kernels are negligible by comparison.
- When code clarity or modularity is more important than micro-optimization (e.g., educational codebases), and the current implementation already meets time limits comfortably.
- When using bitsets for GF(2) matrices would complicate the logic (e.g., non-binary fields, mixed integer operations) or when N is so small that scalar operations are simpler and already fast enough.
- When a library is intended to be highly generic / template-based over arbitrary N and matrix types; aggressive constraint-specialization and manual fixed bounds may reduce reusability.

## Minimal example
Before:
```cpp
// O021 focus: dense
vector<vector<int>> g(n, vector<int>(n, 0));
for (auto [u, v] : edges) g[u][v] = 1;
queue<int> q;
q.push(0);
```
After:
```cpp
// optimized for dense
vector<vector<int>> adj(n);
for (auto [u, v] : edges) adj[u].push_back(v);
deque<int> q{0};
auto ans = topo_dp(adj);
```
