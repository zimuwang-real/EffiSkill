---
skill_id: O010
type: operator
language: cpp
family: graph
name: Refactor To Flat Iterative Core
description: Refactor heavy, recursion- and container-centric solutions into cache-friendly, flat-array, iterative cores.
  This operator preserves or improves asymptotic complexity while aggressively reducing constant factors via better memory
  layout, specialized data structures (arrays, bitsets, treaps), and streamlined DP / traversal structure. Typical applications
  include trees, graphs, binary lifting, subtree hashing
tags:
- optimization
- tree
- graph
- dfs
- bfs
- dynamic_programming
- binary_lifting
- bitmask_enumeration
- subtree_hashing
- convex_hull
triggers:
- Solution uses std::map/std::set or other tree-based associative containers in inner loops where indices are small integers
  and a flat array or unordered_map would suffice.
- DP table is larger-than-necessary (e.g., extra dimensions or overestimated LOG) and many entries are never initialized but
  still iterated over.
- Graph or tree traversals are written as deep recursive DFS/BFS with potential depth O(N) and noticeable function-call overhead,
  especially for N≈1e5.
- Adjacency is stored in nested or pointer-heavy containers (vector<vector<int>>, std::map neighbors, pointer-based edge structs)
  with many cache-miss-prone indirections.
- Binary lifting tables or doubling tables use fixed large heights (e.g., 100, 20, 18) instead of LOG≈ceil(log2 N), or have
  sentinel values (-1) whose checks dominate query loops.
- Bitmask brute-force is implemented by recursion exploring partial assignments and recomputing full scores at non-leaf states
  (redundant work) instead of iterating masks iteratively.
- Subtree or structural comparisons are done via explicit representations (vectors, strings, multisets) per node, leading
  to O(n^2) behavior where a 64-bit hash would suffice.
- Fenwick trees or segment trees are used inside an O(n^2) DP, adding an unnecessary log n factor where precomputed prefix-cost
  tables can make transitions O(1).
---

## When to use
- Solution uses std::map/std::set or other tree-based associative containers in inner loops where indices are small integers and a flat array or unordered_map would suffice.
- DP table is larger-than-necessary (e.g., extra dimensions or overestimated LOG) and many entries are never initialized but still iterated over.
- Graph or tree traversals are written as deep recursive DFS/BFS with potential depth O(N) and noticeable function-call overhead, especially for N≈1e5.
- Adjacency is stored in nested or pointer-heavy containers (vector<vector<int>>, std::map neighbors, pointer-based edge structs) with many cache-miss-prone indirections.
- Binary lifting tables or doubling tables use fixed large heights (e.g., 100, 20, 18) instead of LOG≈ceil(log2 N), or have sentinel values (-1) whose checks dominate query loops.
- Bitmask brute-force is implemented by recursion exploring partial assignments and recomputing full scores at non-leaf states (redundant work) instead of iterating masks iteratively.
- Subtree or structural comparisons are done via explicit representations (vectors, strings, multisets) per node, leading to O(n^2) behavior where a 64-bit hash would suffice.
- Fenwick trees or segment trees are used inside an O(n^2) DP, adding an unnecessary log n factor where precomputed prefix-cost tables can make transitions O(1).

## Steps
1. Flatten core data structures into arrays or tightly sized vectors: Replace std::map / std::set in hot paths with vector / array indexed by small integer keys, or unordered_map with reserved capacity when key range is large but sparse.
2. Flatten core data structures into arrays or tightly sized vectors: Use static or globally allocated arrays (head[], to[], nxt[]) for adjacency when N,M are known upper bounds; otherwise, use vector<vector<int>> or vector<Edge> resized exactly to N.
3. Flatten core data structures into arrays or tightly sized vectors: For trees and graphs, store parents, depths, subtree sizes, and DP states in flat arrays (parent[], depth[], sz[], dp[] or dp[u][small_dim]).
4. Eliminate redundant recursion and restructure traversals iteratively where beneficial: Replace deep recursive DFS on trees with iterative BFS/DFS or leaf-to-root processing using parent and remaining-children counters (sons[], rsons[]) when stack depth is a
5. Eliminate redundant recursion and restructure traversals iteratively where beneficial: For subtree hashing or bottom-up DP, root the tree once, then process nodes in a queue from leaves upward instead of repeated recursive traversals.
6. Eliminate redundant recursion and restructure traversals iteratively where beneficial: Keep recursion where it is shallow and simple, but avoid patterns that recompute large subproblems or cause stack risk.
7. Tighten binary lifting / doubling structures: Determine LOG = ceil(log2(N_max)) or from actual n and allocate lifting tables as table[LOG][n] instead of large fixed heights.
8. Tighten binary lifting / doubling structures: Build tables in cache-friendly order (outer loop over level, inner over node), using layout table[level][node] to ensure contiguous inner-loop access.

## Complexity
- Time: (pattern dependent)
- Space: (pattern dependent)

## Pitfalls
- Breaking invariants when changing layout: reordering dimensions of DP tables (dp[i][j] to dp[j][i]) or changing binary lifting layout (sp[node][level] to fa[level][node]) without systematically updating all accesses.
- Introducing subtle off-by-one or UB in binary lifting and reachability tables when switching from sentinel-based to saturated transitions; all indices must remain in-range for every table lookup.
- Underestimating memory usage when replacing bitsets or compressed representations with full int[N][N] tables; this can exceed limits if N is larger than ~2000.
- Switching std::map to unordered_map or custom hash without reserving enough capacity, causing high load factors and long probe chains that may perform worse than the original map.
- Eliminating recursion without preserving traversal order, which can change DP semantics if the algorithm relies on specific entry/exit times or Euler tours.
- Incorrectly sharing mutable global arrays across multiple test cases without reinitialization or resizing, after converting from fixed globals to per-test vectors.
- Using too-small LOG or assumptions about n when resizing binary lifting tables; underestimating LOG breaks queries for large n.
- Over-aggressive micro-optimizations (manual loop unrolling, custom PRNGs, branch tricks) that obscure code and may not yield benefits under modern compilers, or that introduce subtle bugs.

## When not to use
- When the existing solution already runs comfortably within time and memory limits and further optimization adds complexity with marginal benefit.
- When constraints are small (e.g., N≤2000) and simpler high-level containers (std::map, vector<vector<int>>) keep code clearer with negligible performance cost.
- When exact, formally collision-free behavior is required (e.g., in proof-oriented settings) and replacing explicit structures with hashing could compromise theoretical guarantees.
- When memory is extremely tight and replacing bitsets or compressed structures with full 2D integer tables or large LOG-based tables would exceed memory limits.
- When debugging or rapid prototyping is the current priority; aggressively flattening data structures and removing recursion may hinder readability and ease of verification.
- When problem structure genuinely requires higher-level abstractions (e.g., dynamic trees with link-cut operations, arbitrary precision arithmetic, or generic graph libraries) and flattening them would significantly

## Minimal example
Before:
```cpp
int n; vector<vector<int>> g; vector<int> sub;
void dfs(int u, int p){
    sub[u] = 1;
    for(int v : g[u]) if(v != p){
        dfs(v, u);
        sub[u] += sub[v];
    }
}
// call: g.assign(n,{}); sub.assign(n,0); dfs(0,-1);
```
After:
```cpp
const int MAXN = 200000, MAXM = 2*MAXN;
int head[MAXN], to[MAXM], nxt[MAXM], sub[MAXN], st[MAXN], it[MAXN], ec;
void add_edge(int u,int v){ to[ec]=v; nxt[ec]=head[u]; head[u]=ec++; }
void dfs_iter(int root){ int sp=0; st[sp]=root; it[sp]=head[root]; sub[root]=0;
    while(sp>=0){ int u=st[sp]; if(it[sp]==head[u]) sub[u]=1; int &e=it[sp];
        if(e==-1){ if(sp) sub[st[sp-1]]+=sub[u]; --sp; continue; }
        int v=to[e]; e=nxt[e]; if(v!=st[sp?(sp-1):sp]){ st[++sp]=v; it[sp]=head[v]; }
    }
}
// init: fill(head,head+n,-1); ec=0; add_edge(u,v); add_edge(v,u); dfs_iter(0);
```
