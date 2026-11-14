---
skill_id: O008
type: operator
language: cpp
family: digit
name: Dsu Pair Grouping Via Sorted Flat Array
description: Replace per-component std::map/std::set aggregation of DSU components with a single global pass that builds (compA,
  compB, index) tuples in a flat array, sorts them once, and run-length-encodes equal pairs to obtain group sizes. This removes
  many small associative containers, reduces DSU find calls, and greatly improves cache locality while keeping time at O(N
  log N).
tags:
- dsu
- sorting
- pair-grouping
- frequency-counting
- offline-processing
- arrays
- cache-efficiency
- map-to-sort-refactor
triggers:
- You have two DSU structures (or other equivalence relations) over the same N elements and need, for each element, the size
  of its intersection class (compA(element), compB(element)).
- The current implementation builds a std::map or unordered_map for each DSU component to count how many members fall into
  each other-component, or uses std::set to store membership lists.
- Profiling shows most time in associative container operations (std::map/std::set insert/find) rather than in the DSU unions
  themselves.
- Components are identified by integer roots in [1..N], but counting intersections is done via per-component maps instead
  of a single global grouping of (rootA, rootB) pairs.
- There exist per-component vectors like node[comp] or sets of vertices, followed by nested loops over these vectors combined
  with DSU find calls and map increments.
---

## When to use
- You have two DSU structures (or other equivalence relations) over the same N elements and need, for each element, the size of its intersection class (compA(element), compB(element)).
- The current implementation builds a std::map or unordered_map for each DSU component to count how many members fall into each other-component, or uses std::set to store membership lists.
- Profiling shows most time in associative container operations (std::map/std::set insert/find) rather than in the DSU unions themselves.
- Components are identified by integer roots in [1..N], but counting intersections is done via per-component maps instead of a single global grouping of (rootA, rootB) pairs.
- There exist per-component vectors like node[comp] or sets of vertices, followed by nested loops over these vectors combined with DSU find calls and map increments.

## Steps
1. Ensure DSU implementation is array-based: Maintain parent arrays parentA[1..N], parentB[1..N] with path-compressed find().
2. Ensure DSU implementation is array-based: Optionally keep rank/size arrays, but they are not needed for grouping.
3. Finalize component representatives: After all unions for both DSUs are processed, perform a pass i=1..N and call findA(i), findB(i) once each.
4. Finalize component representatives: Store the compressed roots into arrays rootA[i], rootB[i]. This prevents repeated find calls later.
5. Build a flat array of tuples: Define a simple struct: struct Node { int a; int b; int idx; };
6. Build a flat array of tuples: Allocate Node nodes[N]. For each i in [0..N-1]: nodes[i].a = rootA[i+1]; nodes[i].b = rootB[i+1]; nodes[i].idx = i+1; // or 0-based original index.
7. Build a flat array of tuples: This is one contiguous buffer containing all grouping keys.
8. Sort by the component pair: After sorting, all elements with the same (a,b) are contiguous.

## Complexity
- Time: (pattern dependent)
- Space: O(N) additional memory for the flat Node array, group-size array, and answer array, plus O(N) for DSU parent arrays; no per-component maps/sets.

## Pitfalls
- Forgetting a full path-compression pass before building tuples, leading to multiple equivalent representatives for what should be a single component and thus incorrect grouping.
- Sorting only by the first component ID and ignoring the second (or vice versa), which merges distinct (a,b) pairs into one group.
- Using 1-based indices in some places and 0-based in others when filling nodes[idx] and mapping back to ans[], causing off-by-one bugs.
- Allocating nodes and runSize on the stack for large N (e.g., N > 2e5) rather than static/global or heap, which can trigger stack overflows.
- Recomputing find() inside the sort comparator or during the grouping pass instead of precomputing rootA/rootB, blowing up constant factors.
- Using std::map for final grouping after already sorting the flat array, which defeats the purpose of the optimization.
- Relying on an unstable sort when equality conditions are incomplete; always define a total order (a,b,idx) to keep behavior deterministic.
- Neglecting 64-bit indices or sizes when N can approach limits where int might overflow in intermediate computations (e.g., when building encoded keys for grid pairs).

## When not to use
- When the number of elements N is very small (e.g., N <= 1e3) and the overhead of introducing an extra sort does not outweigh the simplicity of a direct per-component map.
- When component identifiers are not integers or cannot be cheaply stored and compared in a flat struct (e.g., complex keys where hashing or specialized structures are required).
- When you need dynamic online queries over changing DSU structures (insertions and deletions) and cannot afford to rebuild and sort the full (compA, compB) pair array after each update.
- When only aggregate statistics over all intersection sizes are needed (like total number of non-empty intersections) rather than per-element group sizes; in such cases a lighter aggregation scheme may suffice.
- When memory is extremely constrained and an extra O(N) flat buffer is not acceptable, but DSU and per-component maps/sets already exist and must be reused despite their higher constant factors.

## Minimal example
Before:
```cpp
#include <bits/stdc++.h>
using namespace std; vector<int> p;
int find(int x){ return p[x]==x?x:p[x]=find(p[x]); }
void group_edges(const vector<pair<int,int>>& edges){
    unordered_map<long long, vector<int>> g; // per-(compA,compB) hash bucket
    for(int i=0;i<(int)edges.size();++i){ int a=find(edges[i].first), b=find(edges[i].second); if(a>b) swap(a,b); long long k=((long long)a<<32)|b; g[k].push_back(i); }
}
```
After:
```cpp
#include <bits/stdc++.h>
using namespace std; vector<int> p;
int find(int x){ return p[x]==x?x:p[x]=find(p[x]); }
void group_edges(const vector<pair<int,int>>& edges){
    vector<tuple<int,int,int>> flat; flat.reserve(edges.size());
    for(int i=0;i<(int)edges.size();++i){ int a=find(edges[i].first), b=find(edges[i].second); if(a>b) swap(a,b); flat.emplace_back(a,b,i); }
    sort(flat.begin(), flat.end()); for(int i=0,j;i<(int)flat.size();i=j){ j=i; while(j<(int)flat.size() && get<0>(flat[j])==get<0>(flat[i]) && get<1>(flat[j])==get<1>(flat[i])) ++j; /* process group [i,j) */ }
}
```
