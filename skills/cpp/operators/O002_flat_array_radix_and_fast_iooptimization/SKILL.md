---
skill_id: O002
type: operator
language: cpp
family: graph
name: Flat Array Radix And Fast IOOptimization
description: Refactor performance‑critical competitive‑programming code to use flat primitive arrays, specialized integer
  sorting (radix/nth_element), lightweight associative structures, and fast I/O while preserving the high‑level algorithm
  (Dijkstra, greedy, KD‑tree, Mo’s algorithm, DSU, etc.). This operator targets large inputs (≈1e5–1e6 elements) where comparison
  sort, tree‑based containers, recursion, and iostreams cause
tags:
- optimization
- radix-sort
- fast-io
- flat-arrays
- cache-locality
- dijkstra
- greedy
- kd-tree
- mo-algorithm
- coordinate-compression
triggers:
- Input size up to about 1e5–1e6 and current solution already uses an optimal or near‑optimal algorithm (e.g., Dijkstra, Mo’s
  algorithm, KD‑tree, greedy on sorted arrays) but still runs near or over the time limit.
- Heavy use of std::map/std::set/multimap or per‑node std::set in hot paths (e.g., for priority queues, dynamic sets, or ordered
  statistics) where keys are integers or can be compressed to integers.
- Sorting of large arrays of 32‑bit or 64‑bit integers or simple pairs/tuples where only grouping or order by those integers
  is required, and profiling or reasoning shows std::sort or qsort dominating runtime.
- Use of std::cin/std::cout or mixed C and C++ I/O in problems with hundreds of thousands of integers of input/output, showing
  up as I/O bottlenecks in profiles.
- Dynamic ordered sets or trees used only for membership/count/maximum over a fixed small domain where coordinate compression
  + flat arrays or buckets would suffice.
---

## When to use
- Input size up to about 1e5–1e6 and current solution already uses an optimal or near‑optimal algorithm (e.g., Dijkstra, Mo’s algorithm, KD‑tree, greedy on sorted arrays) but still runs near or over the time limit.
- Heavy use of std::map/std::set/multimap or per‑node std::set in hot paths (e.g., for priority queues, dynamic sets, or ordered statistics) where keys are integers or can be compressed to integers.
- Sorting of large arrays of 32‑bit or 64‑bit integers or simple pairs/tuples where only grouping or order by those integers is required, and profiling or reasoning shows std::sort or qsort dominating runtime.
- Use of std::cin/std::cout or mixed C and C++ I/O in problems with hundreds of thousands of integers of input/output, showing up as I/O bottlenecks in profiles.
- Dynamic ordered sets or trees used only for membership/count/maximum over a fixed small domain where coordinate compression + flat arrays or buckets would suffice.

## Steps
1. Assess hot spots and data ranges: Identify whether the code is algorithmically optimal already (e.g., O((N+M) log N) Dijkstra, O((N+Q) sqrt N) Mo’s algorithm, O(N log N) greedy on sorted arrays).
2. Assess hot spots and data ranges: Note maximum N, Q, M from constraints to size static/global arrays safely.
3. Flatten data layout into primitive arrays: Replace arrays of heavy structs or vectors of vectors where possible with parallel primitive arrays (SoA): e.g., instead of struct {int x,y;} arr[], use int x[], y[].
4. Flatten data layout into primitive arrays: For graphs, switch from vector<edge> G[N] to flat arrays with head[] / to[] / w[] / next[] and a single edge counter.
5. Flatten data layout into primitive arrays: For KD‑trees or segment trees, use index‑based nodes in a preallocated array instead of per‑node new/malloc.
6. Specialize sorting for integer keys: If sorting 32‑bit ints (or keys packed into 32/64 bits), replace std::sort/qsort with a fixed‑pass LSD radix sort over bytes (8‑bit digits) using small counting arrays on the stack and a global temporary buffer.
7. Specialize sorting for integer keys: For pairs that only need lexicographic order, pack them into a single 64‑bit key when possible (e.g., (a,b) -> (uint64_t(a) << 32) ^ b) and radix‑sort those keys.
8. Specialize sorting for integer keys: When only order statistics (e.g., median) are required, replace full sort with std::nth_element or simple selection, or even a min/max scan if only extremes are needed.

## Complexity
- Time: (pattern dependent)
- Space: Usually O(N + M + Q) with lower hidden constants by using flat primitive arrays and preallocated buffers instead of many small heap‑allocated containers and oversized structs. Global static arrays sized by tight upper bounds are typical.

## Pitfalls
- Under‑sizing static arrays when replacing vectors, leading to out‑of‑bounds writes on worst‑case inputs. Always size using problem upper bounds with safety margin.
- Breaking stability when porting to radix sort or packed‑key sorting, which can change tie‑breaking and logic that implicitly depended on std::sort’s stable or specific ordering assumptions.
- Forgetting to carry associated arrays (e.g., indices, weights) when applying radix sort to keys, causing misalignment between data fields.
- Incorrect handling of negative integers in radix sort: two’s‑complement order requires careful post‑processing or a signed‑aware scheme to maintain correct ascending order.
- Using unordered_map/gp_hash_table in adversarial inputs without reserving capacity, which can degrade to very poor performance or excessive memory usage.
- Improper DSU or heap lazy‑deletion patterns: forgetting to skip outdated heap entries (dist > d[v]) or mismanaging union‑by‑size can reintroduce large constant factors.
- Converting recursive algorithms to iterative or array‑based form but missing base cases or boundary conditions, leading to infinite loops or stack underflow/overflow.
- Changing int/long long widths inconsistently, leading to overflow in sums or mismatched INF comparisons.

## When not to use
- When the current solution is asymptotically suboptimal (e.g., O(N^2) where O(N log N) is needed); algorithmic changes should come first before systems‑level tuning.
- When keys are not fixed‑width integers or require complex comparison semantics that are hard to encode into radix or packed‑key sorts (e.g., arbitrary precision, strings with locale‑dependent ordering).
- When constraints are small (N, M, Q ≲ 1e4) and simpler STL‑based code is easily fast enough; the additional complexity of custom radix sort and fast I/O reduces clarity without meaningful benefit.
- On platforms where custom I/O or GCC‑specific pragmas are disallowed or risky (non‑GCC compilers, strict sandboxing); in such environments, prefer portable optimizations and standard I/O tuning.
- When code maintainability and readability are primary goals (e.g., educational code, long‑term projects) and performance is already comfortably within limits.
- For problems requiring exact ordered‑statistics or complex invariants over dynamic sets where PBDS or tree‑based containers are clearer and fast enough; flattening or hashing may complicate correctness unduly.

## Minimal example
Before:
```cpp
// O002 focus: flat
vector<vector<int>> g(n, vector<int>(n, 0));
for (auto [u, v] : edges) g[u][v] = 1;
queue<int> q;
q.push(0);
```
After:
```cpp
// optimized for flat
vector<vector<int>> adj(n);
for (auto [u, v] : edges) adj[u].push_back(v);
deque<int> q{0};
auto ans = topo_dp(adj);
```
