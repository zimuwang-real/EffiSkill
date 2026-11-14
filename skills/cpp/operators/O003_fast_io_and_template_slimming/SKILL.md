---
skill_id: O003
type: operator
language: cpp
family: constant_factor
name: Fast Io And Template Slimming
description: Implementation-level optimization for competitive C++ code when the asymptotic algorithm is already optimal (typically
  O(n), DSU, Dijkstra, or simple greedy/arithmetics). The operator targets constant-factor speedups and robustness by configuring
  fast I/O, removing unused template scaffolding and globals, right-sizing containers, tightening types, and simplifying linear
  passes without changing the core algorithm.
tags:
- constant-factor-optimization
- fast-io
- template-cleanup
- memory-footprint
- implementation
- micro-optimization
triggers:
- Both slow and reference solutions use the same asymptotic algorithm (e.g., single linear pass, DSU, Dijkstra) but one is
  significantly faster in practice.
- Code uses std::cin/std::cout with default synchronization (no ios::sync_with_stdio(false), no cin.tie(nullptr)) under large
  input/output size.
- Presence of many unused globals (large arrays, vectors, graphs, utilities) and headers clearly copy-pasted from a generic
  template.
- Global arrays or containers are sized to a fixed upper bound (e.g., MAXN, MAX_V) regardless of actual input sizes, and are
  fully initialized each test.
- Profiling or judge feedback indicates time spent mostly in I/O, initialization, or dead work instead of the core O(F(N))
  logic.
- Use of std::endl in loops or macros that flush on every newline.
- Simple problems (O(1) or tiny loops) accompanied by heavy templates and big unused data structures.
- 'Use of unnecessarily wide integer types (long long for indices, or #define int long long) in tight loops where 32-bit is
  safe.'
---

## When to use
- Both slow and reference solutions use the same asymptotic algorithm (e.g., single linear pass, DSU, Dijkstra) but one is significantly faster in practice.
- Code uses std::cin/std::cout with default synchronization (no ios::sync_with_stdio(false), no cin.tie(nullptr)) under large input/output size.
- Presence of many unused globals (large arrays, vectors, graphs, utilities) and headers clearly copy-pasted from a generic template.
- Global arrays or containers are sized to a fixed upper bound (e.g., MAXN, MAX_V) regardless of actual input sizes, and are fully initialized each test.
- Profiling or judge feedback indicates time spent mostly in I/O, initialization, or dead work instead of the core O(F(N)) logic.
- Use of std::endl in loops or macros that flush on every newline.
- Simple problems (O(1) or tiny loops) accompanied by heavy templates and big unused data structures.
- Use of unnecessarily wide integer types (long long for indices, or #define int long long) in tight loops where 32-bit is safe.

## Steps
1. Configure fast I/O: At the start of main (or in a global init helper), add
2. Configure fast I/O: ios::sync_with_stdio(false);
3. Configure fast I/O: cin.tie(nullptr);
4. Configure fast I/O: Avoid std::endl in hot paths; use '\n' or '\n' + explicit flush only when necessary.
5. Configure fast I/O: For very heavy I/O, consider scanf/printf or a custom buffered reader/writer.
6. Remove unused template scaffolding: Delete unused global containers (e.g., adjacency lists, DSU arrays, vectors, counters) that are never referenced in the actual solution.
7. Remove unused template scaffolding: Remove dead helper functions (dfs, gcd, power, unused graph/geometry utilities).
8. Remove unused template scaffolding: Prune unused macros, typedefs, and debug utilities that are not on the hot path.

## Complexity
- Time: Preserves the original algorithm’s time complexity (e.g., O(n), O((N+Q) * α(N)), O((V+E) log V), O(1)); only reduces constant factors from I/O, initialization, and micro-structure.
- Space: Preserves or improves asymptotic space usage (often from O(MAXN) globals to O(n) or O(1) actual usage) by removing unused structures and right-sizing containers.

## Pitfalls
- Changing algorithm semantics while refactoring: off-by-one errors when switching between 0-based and 1-based indexing or resizing arrays to exact n.
- Accidentally removing code that is logically necessary but looks unused (e.g., precomputed arrays, sentinels, or initialization required by later passes).
- Using int where long long is required, causing overflows in cumulative sums, combinatorics, or large edge weights.
- Over-aggressively shrinking arrays without respecting true worst-case constraints, leading to out-of-bounds access on some inputs.
- Mixing C and C++ I/O without care (e.g., scanf with cin) and forgetting to disable sync or leaving streams tied, which can negate I/O improvements or cause subtle issues.
- Defining #define int long long and then assuming 32-bit behavior in array sizes, loop bounds, or library calls.
- Relying on UB fixes (e.g., removing a memset that was indirectly masking use of uninitialized memory) without understanding why the original code behaved correctly.
- Adding heavy optimization pragmas in environments where they are disallowed or misconfigured, causing compilation failures.

## When not to use
- When the solution is fundamentally too slow asymptotically (e.g., O(n^2) where O(n log n) is required); in such cases, algorithmic changes are needed instead of constant-factor tweaks.
- When the existing code already meets time and memory limits comfortably and readability or maintainability is more important than minor speedups.
- In environments where aggressive I/O tricks, custom readers, or compiler pragmas violate platform rules or conflict with provided harnesses.
- When debugging or developing a new algorithm: premature micro-optimizations (fast I/O, heavy macros, template slimming) can obscure logic and hinder correctness verification.
- If the problem constraints are small (e.g., n ≤ 10^3 with few test cases) such that standard cin/cout and simple templates are easily fast enough.

## Minimal example
Before:
```cpp
#include <bits/stdc++.h>
using namespace std;
template<class T> void read(vector<T>& a){ for(auto &x:a) cin>>x; }
int main(){ int n; cin>>n; vector<long long> a(n); read(a); long long s=0; for(auto x:a) s+=x; cout<<s; }
```
After:
```cpp
#include <bits/stdc++.h>
using namespace std;
int main(){ ios::sync_with_stdio(false); cin.tie(nullptr);
  int n; cin>>n; long long s=0,x; for(int i=0;i<n;++i){ cin>>x; s+=x; }
  cout<<s; }
```
