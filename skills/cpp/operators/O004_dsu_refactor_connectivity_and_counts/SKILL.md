---
skill_id: O004
type: operator
language: cpp
family: graph
name: Dsu Refactor Connectivity And Counts
description: Refactor graph/connectivity/counting solutions that currently use DFS/BFS over adjacency lists or balanced-tree
  containers (set/map/multiset) into flat-array Disjoint Set Union (Union-Find) based implementations. Maintain component
  sizes and simple per‑node counters online during unions, and use optional DSU potentials for difference-constraint systems.
  This reduces memory, avoids recursion, and replaces
tags:
- dsu
- union_find
- graph
- connected_components
- offline_processing
- component_size
- difference_constraints
- mst
- permutation_connectivity
- bipartite_check
triggers:
- Static graph or relation set is built once, followed by many connectivity or component-membership queries.
- DFS/BFS is used only to label connected components or compute simple aggregates (component size, sum, min/max) without needing
  explicit paths.
- Adjacency lists or std::set/std::map are stored but edges are never traversed along paths; only component IDs or counts
  are required.
- Per-component std::set/std::map/multiset is used to store vertices or values in each component for membership checking or
  counting.
- Difference-constraint style edges (u, v, w) with invariants like col[v] = col[u] + w are processed with DFS coloring instead
  of a potential DSU.
- Connectivity or counting logic is repeated inside a binary search or multi-pass framework over the same static graph.
- Recursive DFS on graphs/trees with n up to ~1e5 or more is used in a context where only component connectivity or parity
  is needed (stack-depth risk).
---

## When to use
- Static graph or relation set is built once, followed by many connectivity or component-membership queries.
- DFS/BFS is used only to label connected components or compute simple aggregates (component size, sum, min/max) without needing explicit paths.
- Adjacency lists or std::set/std::map are stored but edges are never traversed along paths; only component IDs or counts are required.
- Per-component std::set/std::map/multiset is used to store vertices or values in each component for membership checking or counting.
- Difference-constraint style edges (u, v, w) with invariants like col[v] = col[u] + w are processed with DFS coloring instead of a potential DSU.
- Connectivity or counting logic is repeated inside a binary search or multi-pass framework over the same static graph.
- Recursive DFS on graphs/trees with n up to ~1e5 or more is used in a context where only component connectivity or parity is needed (stack-depth risk).

## Steps
1. Model components with DSU: Implement find(x) with path compression, e.g.: int find(int x){ return par[x] < 0 ? x : par[x] = find(par[x]); }
2. Model components with DSU: Implement unite(a, b) with union by size/rank: ra = find(a), rb = find(b); if (ra == rb) return; if (par[ra] > par[rb]) swap(ra, rb); // ra has larger size (more negative) par[ra] += par[rb]; par[rb] = ra;
3. Replace adjacency/DFS component labeling with DSU unions: When reading each undirected edge (u, v), call unite(u, v) instead of pushing into adjacency vectors for a later DFS.
4. Replace adjacency/DFS component labeling with DSU unions: For static connectivity queries, after processing all edges, components are implicitly defined by roots find(i).
5. Maintain component aggregates online: For component sizes, rely on size(root) = -par[root].
6. Maintain component aggregates online: For aggregate values (sum, counts, custom metrics), maintain parallel arrays agg1[], agg2[], etc. Only update roots during unite
7. Maintain component aggregates online: When merging rb into ra, do agg1[ra] += agg1[rb]; agg2[ra] = combine(agg2[ra], agg2[rb]); according to the needed DP/metric.
8. Eliminate map/set-based per-component storage: Instead of std::map<root, > and per-component std::set/multiset, use flat arrays indexed by DSU root or by element

## Complexity
- Time: Typically O((n + m + q) * α(n)) for connectivity/counting tasks; O(E log E + (V + E) * α(V)) for MST-like tasks using sort + DSU; O((n + m) * α(n)) for difference-constraint consistency with potential DSU. All are effectively near-linear
- Space: O(n) for DSU parents, ranks/sizes, and per-node aggregates, plus O(m) for flat edge arrays or auxiliary tuples when needed. Adjacency lists and per-component tree containers are usually removed.

## Pitfalls
- Incorrect union-by-size/rank: comparing sizes with wrong sign or attaching larger trees under smaller ones, degrading DSU performance and in rare cases causing stack issues if recursion is used in find().
- Forgetting to update all component aggregates when merging: updating only parent or size but not related sum/min/max leads to incorrect counts or DP values.
- Running extra full passes over n to count sizes or compress paths despite already maintaining sizes online during unions, adding unnecessary O(n) work.
- Mixing 0-based and 1-based indices inconsistently in DSU arrays vs. input, especially when combining DSU indices with encoded bipartite or coordinate ranges (like x in [1..MAX], y in [MAX+1..2*MAX]).
- Using std::map/std::set for grouping or membership where simple arrays plus sort or direct root comparisons suffice, preserving an unnecessary O(log n) overhead.
- In weighted/potential DSU, miscomputing the offset update on merge, or checking the wrong relation (e.g., offset[l] - offset[r] instead of offset[r] - offset[l]) when validating constraints.
- Relying on recursion in find() or DFS for very large n without considering stack depth limits; if recursion is used, ensure union-by-size and path compression keep depth small, or implement iterative find/DFS.
- Not trimming initialization and per-test-case clearing to actual n,m, leading to hidden O(maxN) costs, especially in multi-case problems with small actual instance sizes.

## When not to use
- When edges are updated online (insertions and deletions) and queries must be answered in fully dynamic fashion; DSU cannot handle deletions without rollback or heavy machinery.
- When the solution truly needs explicit paths, traversal order, or per-visit state beyond what can be expressed as component-level aggregates (e.g., shortest paths, arbitrary path sums on dynamic trees).
- When problem semantics require online answers interleaved with updates and cannot be processed offline or in reverse; many DSU tricks assume offline processing.
- When the underlying structure is a fixed tree and a simple one-pass DFS/DP is enough without any union operations; adding DSU in such cases may increase constant factors without benefit.
- When constraints on n, m are tiny (e.g., n <= 2000) and algorithmic bottlenecks lie elsewhere; refactoring to DSU yields minimal gain and may complicate code.

## Minimal example
Before:
```cpp
// O004 focus: dsu
vector<vector<int>> g(n, vector<int>(n, 0));
for (auto [u, v] : edges) g[u][v] = 1;
queue<int> q;
q.push(0);
```
After:
```cpp
// optimized for dsu
vector<vector<int>> adj(n);
for (auto [u, v] : edges) adj[u].push_back(v);
deque<int> q{0};
auto ans = topo_dp(adj);
```
