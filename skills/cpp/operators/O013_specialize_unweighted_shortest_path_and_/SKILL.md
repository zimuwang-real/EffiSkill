---
skill_id: O013
type: operator
language: cpp
family: graph
name: Specialize Unweighted Shortest Path And Small Distance Queries
description: Reusable optimization pattern distilled from weighted traces.
tags:
- graph
- shortest_path
- BFS
- Dijkstra
- 0-1_BFS
- unweighted_graph
- distance_2_check
- adjacency_intersection
- optimization
- constant_factor
triggers:
- All edges are unweighted or explicitly added with weight 1, but the code uses Dijkstra or Bellman-Ford.
- The final logic only checks whether dist[target] <= K or == K for a very small K (typically 1 or 2), not general distances.
- The problem asks only for existence of a path of length 2 (or similarly tiny length), e.g. checking whether there exists
  a node x with edges (s, x) and (x, t).
- Shortest paths are computed from a single fixed source to a single fixed target, but the algorithm builds full adjacency
  lists and distances to all nodes.
- A DFS/BFS is run over an unweighted graph and then the code only inspects a simple local property like 'is there a neighbor
  of s that is also a neighbor of t'.
- The code constructs an adjacency list solely to perform a BFS/DFS of depth at most 2 from the source.
- Use of a priority_queue-based Dijkstra on a graph whose edge weights are only 0 or 1.
- Use of Bellman-Ford (O(VE)) on a sparse graph with non-negative weights, where constraints hint that Dijkstra would suffice.
---

## When to use
- All edges are unweighted or explicitly added with weight 1, but the code uses Dijkstra or Bellman-Ford.
- The final logic only checks whether dist[target] <= K or == K for a very small K (typically 1 or 2), not general distances.
- The problem asks only for existence of a path of length 2 (or similarly tiny length), e.g. checking whether there exists a node x with edges (s, x) and (x, t).
- Shortest paths are computed from a single fixed source to a single fixed target, but the algorithm builds full adjacency lists and distances to all nodes.
- A DFS/BFS is run over an unweighted graph and then the code only inspects a simple local property like 'is there a neighbor of s that is also a neighbor of t'.
- The code constructs an adjacency list solely to perform a BFS/DFS of depth at most 2 from the source.
- Use of a priority_queue-based Dijkstra on a graph whose edge weights are only 0 or 1.
- Use of Bellman-Ford (O(VE)) on a sparse graph with non-negative weights, where constraints hint that Dijkstra would suffice.

## Steps
1. Inspect_query_requirements: Determine exactly what the problem asks: full shortest-path distances, or only whether there exists a path with length within a small threshold (often 1 or 2) between fixed endpoints.
2. Inspect_query_requirements: Check whether all edges are unweighted (unit cost) or restricted to {0,1}. If so, general weighted SSSP is likely overkill.
3. Classify_graph_and_weights: If all edge weights are equal and positive (typically 1), treat the graph as unweighted.
4. Classify_graph_and_weights: If all weights are in {0,1}, mark it as a 0-1 weighted graph suitable for 0-1 BFS.
5. Classify_graph_and_weights: If weights are arbitrary but non-negative and the entire graph is used, Dijkstra remains appropriate; otherwise continue specialization.
6. For_unweighted_graphs_with_general_distances: Replace Dijkstra or Bellman-Ford with standard BFS from the source
7. For_unweighted_graphs_with_general_distances: Represent the graph as vector<int> adj[N] (no weights stored).
8. For_unweighted_graphs_with_general_distances: Use a queue<int> and an int dist[N] initialized to -1 (or INF).

## Complexity
- Time: Typically improves from O((N + M) log N) or O(VE) to O(N + M) for BFS/0-1 BFS, and down to O(M + N) or pure O(M) for specialized distance-2 and neighbor-intersection checks.
- Space: Reduces from O(N + M) adjacency structures + priority_queue metadata to O(N + M) for BFS/0-1 BFS or O(N) for simple edge-scan neighbor-marking approaches.

## Pitfalls
- Using Dijkstra or Bellman-Ford on an unweighted graph when BFS (or even a single edge scan) suffices, incurring unnecessary O(M log N) or O(VE) overhead.
- Forgetting edge direction when specializing to length-2 paths on directed graphs, accidentally treating (a, b) as bidirectional.
- Incorrectly treating dist(s, t) <= 2 and dist(s, t) == 2 as the same condition; a direct edge (s, t) must be excluded if the query is about exact distance 2.
- Building full adjacency lists and then only using neighbors of s and neighbors of t, wasting memory and initialization time.
- Over-initializing arrays to a fixed MAX size instead of up to n, causing larger-than-necessary O(MAX) memsets in multi-test environments.
- Misusing sentinels for distances (e.g., memset with a magic byte pattern as INF on int/long long) and then re-implementing specialized logic, leading to subtle bugs.
- In 0-1 BFS, accidentally using a queue instead of a deque or pushing all neighbors to the back, which reverts to O(N*M) behavior in worst cases.
- Assuming that replacing Dijkstra with BFS or a linear scan is always correct merely because edges are unweighted; this is only true when queries do not require weighted optimization or longer distances.

## When not to use
- When edge weights are arbitrary (not all 1 or {0,1}) and the objective truly depends on these weights; Dijkstra or another weighted SSSP algorithm is required.
- When the problem needs full distance information from the source to all nodes (e.g., many queries, or complex DP on distances), not just a small distance threshold or single pair check.
- When you require exact shortest-path distances beyond small constants (e.g., K can be large or not known to be small), and a full BFS/Dijkstra is logically necessary.
- When the graph is dynamic (edges inserted/deleted) and short paths can change in complex ways; specialized one-pass checks may not be easy to maintain or prove correct.
- When clarity or correctness would suffer: if the specialized combinatorial characterization is non-trivial to reason about, sticking to standard BFS/Dijkstra might be preferable despite the performance cost, especially
- When the input size is small enough (n, m ≲ 2e3) that using standard algorithms does not pose performance issues and code simplicity is more valuable than micro-optimization.

## Minimal example
Before:
```cpp
int dijkstra(int s, int t, const vector<vector<int>>& g) {
    const int INF = 1e9; vector<int> dist(g.size(), INF);
    priority_queue<pair<int,int>, vector<pair<int,int>>, greater<>> pq;
    pq.push({0, s}); dist[s] = 0;
    while (!pq.empty()) { auto [d, v] = pq.top(); pq.pop(); if (d != dist[v]) continue;
        for (int to : g[v]) if (dist[to] > d + 1) { dist[to] = d + 1; pq.push({dist[to], to}); } }
    return dist[t];
}
```
After:
```cpp
int bfs_unweighted(int s, int t, const vector<vector<int>>& g) {
    const int INF = 1e9; vector<int> dist(g.size(), INF);
    queue<int> q; q.push(s); dist[s] = 0;
    while (!q.empty()) { int v = q.front(); q.pop(); if (v == t) break;
        for (int to : g[v]) if (dist[to] == INF) { dist[to] = dist[v] + 1; q.push(to); } }
    return dist[t];
}
```
