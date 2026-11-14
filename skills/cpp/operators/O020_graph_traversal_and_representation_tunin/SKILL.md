---
skill_id: O020
type: operator
language: cpp
family: graph
name: Graph Traversal And Representation Tuning
description: Refactor graph algorithms and their memory layout to exploit problem structure (functional graphs, 0/1 weights,
  2-SAT implications, sparse grids, difference-constraints) and to remove unnecessary overhead (overkill SCC/Tarjan, SPFA-style
  relaxations, segment-tree-expanded graphs, repeated full-array clears, heap-heavy MST). Keep or improve asymptotic complexity
  while reducing constant factors via specialized
tags:
- graph
- DFS
- BFS
- 0-1_BFS
- SCC
- Tarjan
- 2-SAT
- SPFA
- difference-constraints
- functional-graph
triggers:
- Using Tarjan SCC or generic lowlink on a functional graph where each node has exactly one outgoing edge (parent pointer).
- Using SPFA-style relaxation (queue/DFS with `d[v] > d[u] + w` updates) on graphs with small integer weights, especially
  0/1 weights.
- Encoding 2-SAT or simple boolean constraints via segment trees or inflated graph layers, resulting in far more nodes than
  logical variables.
- Running DFS/SCC on graphs with many more technical nodes than logical entities (e.g., segment-tree nodes, duplicated layers).
- Prim MST with a binary heap on a sparse graph with O(N) edges where edge candidates are already almost sorted or easily
  listable.
- Graph defined implicitly (grid via ±n offsets, modular transitions, functional parent arrays) but built as an explicit dense
  adjacency list.
- Distance / potential consistency check using repeated relaxations and a super-source, when constraints are equalities or
  simple difference constraints that can be checked in one DFS pass.
- SPFA or generic SSSP on a 0/1-weight graph (or fixed small weights) where 0-1 BFS or specialized BFS would suffice.
---

## When to use
- Using Tarjan SCC or generic lowlink on a functional graph where each node has exactly one outgoing edge (parent pointer).
- Using SPFA-style relaxation (queue/DFS with `d[v] > d[u] + w` updates) on graphs with small integer weights, especially 0/1 weights.
- Encoding 2-SAT or simple boolean constraints via segment trees or inflated graph layers, resulting in far more nodes than logical variables.
- Running DFS/SCC on graphs with many more technical nodes than logical entities (e.g., segment-tree nodes, duplicated layers).
- Prim MST with a binary heap on a sparse graph with O(N) edges where edge candidates are already almost sorted or easily listable.
- Graph defined implicitly (grid via ±n offsets, modular transitions, functional parent arrays) but built as an explicit dense adjacency list.
- Distance / potential consistency check using repeated relaxations and a super-source, when constraints are equalities or simple difference constraints that can be checked in one DFS pass.
- SPFA or generic SSSP on a 0/1-weight graph (or fixed small weights) where 0-1 BFS or specialized BFS would suffice.

## Steps
1. Exploit special graph structure: Functional graphs: Replace generic SCC/Tarjan with simple cycle detection via following parent pointers and marking visited and in-cycle nodes.
2. Exploit special graph structure: 0/1-weight SSSP: Replace SPFA with 0-1 BFS using a deque, computing neighbors on the fly when edges are defined by formulas.
3. Exploit special graph structure: Difference/equality constraints: Replace relaxation-based SPFA-like DFS with a single DFS/BFS that assigns potentials once and only checks consistency on revisits.
4. Exploit special graph structure: SAT: Replace segment-tree-expanded graphs with a flat implication graph over 2 * n literal nodes and standard SCC.
5. Flatten and specialize graph representation: Use static arrays (head[], to[], next[]) or vector-of-int adjacency lists sized by n rather than over-provisioned globals.
6. Flatten and specialize graph representation: For undirected edges with fixed weight pattern, remove explicit weight fields and encode weight via edge index parity or construction order.
7. Flatten and specialize graph representation: Prefer contiguous edge arrays and integer indices for tight DFS/BFS loops over pointer-heavy or nested vector structures where appropriate.
8. Tighten initialization and test-case handling: Avoid repeated O(n) clears for each component; move clears outside outer loops or use versioned visited/color arrays (generation counters).

## Complexity
- Time: (pattern dependent)
- Space: (pattern dependent)

## Pitfalls
- Breaking problem semantics when replacing a generic algorithm with a specialized one: Assuming functional-graph properties (out-degree 1) when the graph can have higher out-degree.
- Breaking problem semantics when replacing a generic algorithm with a specialized one: Replacing SPFA with 0-1 BFS when edge weights are not restricted to {0,1} or can be negative.
- Over-tightening array bounds based on observed fast-code constants instead of actual constraints, causing out-of-bounds writes on larger inputs.
- Copying counting or answer formulas from a reference implementation that solved a related but not identical task (e.g., using `cntot - 1` from a component-counting solution instead of a bridge count).
- Incorrect initialization when removing memset: Forgetting that globals are zero-initialized only once, leading to stale state across multiple testcases if not reset or versioned.
- Incorrect initialization when removing memset: Misusing versioned arrays by not incrementing generation counters or using too small a type, causing wrap-around and false "visited" marks.
- Incorrect negative-cycle or contradiction detection when refactoring SPFA/difference-constraints code: Using too small per-vertex relax limits or miscounting pops, causing false positives.
- Incorrect negative-cycle or contradiction detection when refactoring SPFA/difference-constraints code: Failing to enforce equality/consistency checks on revisiting already-assigned nodes.

## When not to use
- When the graph does not satisfy the structural assumptions required by the specialized optimization: Non-functional graphs (out-degree > 1) where you considered replacing SCC with functional-graph cycle detection.
- When the graph does not satisfy the structural assumptions required by the specialized optimization: Edge weights are arbitrary (including negative or >1) but you plan to use 0-1 BFS or a simplified DFS-based
- When constraints are small (e.g., V, E ≤ 2000) and code clarity or rapid implementation is more important than shaving constant factors via specialized memory layouts or custom IO.
- When using standard libraries and generic algorithms is required (e.g., educational settings, library-restricted environments) and custom fast IO or non-standard tricks (generation counters, parity-encoded weights)
- When multiple problem variants share the same implementation and specialized restructuring would break generality (e.g., a library SSSP routine intended to handle arbitrary non-negative weights, not just 0/1 weights).
- When you cannot rigorously re-verify equivalence of the simplified model to the original constraints (e.g., subtle 2-SAT encodings with interval constraints where removing the segment tree changes semantics).

## Minimal example
Before:
```cpp
int n = graph.size();
for (int s = 0; s < n; ++s) {
  queue<int> q; vector<int> dist(n, -1); q.push(s); dist[s] = 0;
  while (!q.empty()) { int u = q.front(); q.pop();
    for (int v = 0; v < n; ++v) if (graph[u][v] && dist[v] == -1)
      dist[v] = dist[u] + 1, q.push(v); // scans full row (adj matrix)
  }
}
```
After:
```cpp
int n = adj.size();
for (int s = 0; s < n; ++s) {
  queue<int> q; vector<int> dist(n, -1); q.push(s); dist[s] = 0;
  while (!q.empty()) { int u = q.front(); q.pop();
    for (int v : adj[u]) if (dist[v] == -1) // sparse adj list
      dist[v] = dist[u] + 1, q.push(v);
  }
}
```
