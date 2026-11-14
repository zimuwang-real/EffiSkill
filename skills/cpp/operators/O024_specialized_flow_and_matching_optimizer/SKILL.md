---
skill_id: O024
type: operator
language: cpp
family: graph
name: Specialized Flow And Matching Optimizer
description: Replace generic or over-provisioned network-flow/LP formulations with specialized max-flow, min-cost-flow, or
  bipartite-matching routines and cache-friendly data layouts. This operator targets cases where the mathematical structure
  is flow-like or bipartite but the implementation uses heavyweight abstractions (dense simplex, generic max-flow on inflated
  graphs, SPFA-based min-cost flow, or heuristic search). It
tags:
- graph
- network_flow
- max_flow
- min_cost_flow
- bipartite_matching
- augmenting_path
- Dinic
- Kuhn
- shortest_path_with_potentials
- constant_factor_optimization
triggers:
- A generic max-flow engine (Ford–Fulkerson or Dinic) is used to compute a maximum bipartite matching with unit capacities
  and no need for general multi-commodity flow.
- Bipartite structure is present (two disjoint index ranges, edges only across the partition, cardinality/weight of matching
  requested) but the code models it as source-left-right-sink max-flow with residual edges.
- Min-cost or max-cost flow is implemented with SPFA inside an augmenting-flow loop, with no reduced-cost potentials, on graphs
  up to a few thousand vertices and tens of thousands of edges.
- A dense simplex-based LP solver is used for a small flow-like or circulation problem with integer capacities/costs and clear
  graph structure.
- Global arrays for graph storage are dimensioned for very large MAX_V/MAX_E but only a small prefix of vertices/edges is
  ever used; memset/clear loops touch the entire bound each test.
- Profiling or behavior shows many BFS/DFS passes over large residual networks for small logical graphs, or heavy cache misses
  due to large Edge structs and scattered adjacency.
- Heuristic randomized search or ad-hoc permutations are used to optimize a function that can be interpreted as a closure/min-cut
  or flow problem (e.g., divisibility or subset-closure constraints).
- Ford–Fulkerson with DFS (visited[] per augment, no levels/current-arc) is used with very large capacities, causing strong
  dependence on flow value F.
---

## When to use
- A generic max-flow engine (Ford–Fulkerson or Dinic) is used to compute a maximum bipartite matching with unit capacities and no need for general multi-commodity flow.
- Bipartite structure is present (two disjoint index ranges, edges only across the partition, cardinality/weight of matching requested) but the code models it as source-left-right-sink max-flow with residual edges.
- Min-cost or max-cost flow is implemented with SPFA inside an augmenting-flow loop, with no reduced-cost potentials, on graphs up to a few thousand vertices and tens of thousands of edges.
- A dense simplex-based LP solver is used for a small flow-like or circulation problem with integer capacities/costs and clear graph structure.
- Global arrays for graph storage are dimensioned for very large MAX_V/MAX_E but only a small prefix of vertices/edges is ever used; memset/clear loops touch the entire bound each test.
- Profiling or behavior shows many BFS/DFS passes over large residual networks for small logical graphs, or heavy cache misses due to large Edge structs and scattered adjacency.
- Heuristic randomized search or ad-hoc permutations are used to optimize a function that can be interpreted as a closure/min-cut or flow problem (e.g., divisibility or subset-closure constraints).
- Ford–Fulkerson with DFS (visited[] per augment, no levels/current-arc) is used with very large capacities, causing strong dependence on flow value F.

## Steps
1. Identify the true combinatorial structure: If the graph is bipartite with unit capacities and the output is a maximum matching size/assignment, treat it as bipartite matching rather than generic max-flow.
2. Identify the true combinatorial structure: If constraints are linear over a small graph with capacities/costs, model them explicitly as a min-cost flow or circulation instead of a generic LP.
3. Identify the true combinatorial structure: If there is a closure-like condition (e.g., divisibility or implication edges with weights), recognize a maximum-closure / min-cut formulation.
4. Choose a specialized algorithm: Use a DFS-based Kuhn algorithm for maximum bipartite matching when n is modest (e.g., ≤ 1e3, especially ≤ 1e2) and the graph is dense or constraints are small.
5. Choose a specialized algorithm: Use Dinic’s algorithm for general max-flow when larger graphs or capacities are involved; avoid Ford–Fulkerson with plain DFS.
6. Choose a specialized algorithm: Use successive shortest augmenting paths with Dijkstra + Johnson potentials for min-cost flow instead of SPFA.
7. Choose a specialized algorithm: Replace heuristic permutations or greedy closures with a deterministic max-flow/min-cut formulation when closure or cut structure is evident.
8. Simplify graph representation to the natural size: For bipartite matching, store adjacency as `vector<int> g[L]` or a static adjacency matrix `bool adj[L][R]` for small dense graphs, with a simple `matchR[R]` or `fa[]` array.

## Complexity
- Time: Bipartite matching (Kuhn DFS): typically O(V * E), often written as O(n^3) for dense n×n bipartite graphs; good constants for n up to around 1e3 and especially effective for n ≲ 1e2.
- Space: Specialized matching/flow implementations: O(V + E) space with tightly sized adjacency lists and state arrays; for small dense bipartite matching with matrices, O(n^2).

## Pitfalls
- Choosing Kuhn matching where asymptotically stronger algorithms are required: for very large bipartite graphs (e.g., n ≫ 1e3), O(V * E) matching can be too slow; Hopcroft–Karp or flow-based approaches may be more
- Incorrectly modeling costs or capacities when replacing LP/heuristics with flow: missing a constraint in the flow network can silently produce a different objective.
- For min-cost flow with potentials, forgetting to initialize or update potentials correctly, causing negative reduced costs and invalid Dijkstra assumptions.
- Mishandling residual edges when changing edge structures: failing to update reverse edges consistently (`rev` indices or `i^1` convention) leads to incorrect flows or infinite loops.
- Over-aggressive downsizing of arrays without honoring worst-case constraints, leading to buffer overruns in competitive programming environments.
- Using 32-bit integers for capacities or costs when INF*V might overflow; this can break min-cut or maximum-closure formulations that rely on very large capacities to represent "infinite" edges.
- Accidentally changing semantics when removing auxiliary structures (like vertex-cover arrays) that are used later, even if not printed.
- Assuming SPFA is always fast enough on medium-sized graphs; in adversarial cases, SPFA-based min-cost flow can easily TLE even when Dijkstra-based versions pass.

## When not to use
- When the problem genuinely requires general linear programming (e.g., many unrelated constraints, non-network structure, fractional variables), replacing simplex with min-cost flow would be incorrect.
- When the graph is extremely large and sparse and you need the best asymptotic matching performance; in that case, prefer Hopcroft–Karp over Kuhn for bipartite matching instead of relying solely on DFS-based methods.
- When existing generic flow code already meets time and memory limits comfortably and further micro-optimization increases code complexity without competitive benefit.
- When constraints or judge limits demand floating-point or high-precision arithmetic that is tightly coupled to a specific LP formulation; rewriting to integer flow may be infeasible.
- When the current implementation depends on special features of the generic framework (e.g., multi-source, multi-sink, or repeated incremental updates) that are not supported by the simplified specialized template
- When correctness relies on exact behavior of a heuristic or randomized algorithm prescribed by the problem statement (rare in competitive programming), and replacing it by a deterministic flow algorithm changes the

## Minimal example
Before:
```cpp
int S = 0, T = nL + nR + 1; Dinic din(T + 1);
for (int u = 1; u <= nL; ++u) { din.add_edge(S, u, 1); for (int v : adj[u]) din.add_edge(u, nL + v, 1); }
for (int v = 1; v <= nR; ++v) din.add_edge(nL + v, T, 1);
int maxMatching = din.max_flow(S, T);
```
After:
```cpp
vector<int> matchR(nR + 1, -1), vis(nR + 1);
function<bool(int)> dfs = [&](int u){ for (int v : adj[u]) if (!vis[v]) { vis[v] = 1; if (matchR[v] == -1 || dfs(matchR[v])) return matchR[v] = u, true; } return false; };
int maxMatching = 0; for (int u = 1; u <= nL; ++u) { fill(vis.begin(), vis.end(), 0); if (dfs(u)) ++maxMatching; }
```
