---
skill_id: O026
type: operator
language: cpp
family: graph
name: Offline Small Radius Graph Paint
description: Optimize multiple distance-limited updates on an undirected graph ("paint within radius d and later paints override
  earlier ones") by processing queries offline in reverse, lifting the state space to (vertex, remaining_depth), and pruning
  via per-vertex or per-(vertex,depth) visitation. Replace per-query BFS/DFS with a single shared traversal over this lifted
  state space, and use flat adjacency arrays for tight
tags:
- graph
- offline-queries
- dfs
- bfs-to-dfs-conversion
- pruning
- small-parameter-optimization
- memory-layout
- adjacency-array
- reverse-processing
triggers:
- Undirected (or simple) graph with up to ~1e5 vertices/edges and up to ~1e5 queries.
- Each query applies a radius-limited operation from a source vertex (e.g., color/mark all nodes within distance <= d).
- Radius/maximum depth d is small and globally bounded (e.g., d <= 10..20).
- Later queries override earlier ones (last-wins semantics), or you need the effect of all queries combined.
- Baseline solution performs a BFS/DFS from scratch for every query, leading to O(q * (n + m)) time.
- Code repeatedly memset() or reinitializes O(n)-sized arrays (e.g., dist[], visited[]) per query.
- Adjacency is stored as vector<vector<int>> or similar STL-heavy structure, and traversal is in very tight loops.
- There is a heuristic per-vertex pruning array (like maxDist[u]) but it still allows many repeated traversals.
---

## When to use
- Undirected (or simple) graph with up to ~1e5 vertices/edges and up to ~1e5 queries.
- Each query applies a radius-limited operation from a source vertex (e.g., color/mark all nodes within distance <= d).
- Radius/maximum depth d is small and globally bounded (e.g., d <= 10..20).
- Later queries override earlier ones (last-wins semantics), or you need the effect of all queries combined.
- Baseline solution performs a BFS/DFS from scratch for every query, leading to O(q * (n + m)) time.
- Code repeatedly memset() or reinitializes O(n)-sized arrays (e.g., dist[], visited[]) per query.
- Adjacency is stored as vector<vector<int>> or similar STL-heavy structure, and traversal is in very tight loops.
- There is a heuristic per-vertex pruning array (like maxDist[u]) but it still allows many repeated traversals.

## Steps
1. Model queries offline with reverse processing: Read all queries (source v[i], radius d[i], payload/color c[i]).
2. Model queries offline with reverse processing: Process them from last to first so that earlier queries only fill states not already claimed by later ones.
3. Choose a state representation and pruning strategy depending on constraints: If d_max is very small and truly bounded (e.g., <= 10..20), use a 2D state table col[v][dep] where dep is remaining depth (0..d_max).
4. Implement a compact adjacency representation using flat arrays: Use forward-star / CSR-style arrays: head[u], to[idx], next[idx].
5. Implement a compact adjacency representation using flat arrays: For each undirected edge (u, v), add two directed edges (u -> v) and (v -> u).
6. Implement a compact adjacency representation using flat arrays: This avoids per-vertex dynamic allocations and improves memory locality in DFS.
7. Design the DFS over the lifted state space: Function signature examples: * 2D state: dfs(u, dep, color) * 1D state: dfs(u, ran, color) where ran = remaining_depth + 1
8. Design the DFS over the lifted state space: Base cases: * If dep < 0 (or ran <= 0), stop recursion. * If the state is already visited/colored, prune

## Complexity
- Time: (pattern dependent)
- Space: O(n + m + q) for adjacency, queries, and pruning arrays, plus an optional O(n * D_max) table if a 2D (vertex, depth) state representation is used and D_max is small. No per-query O(n) auxiliary arrays are required.

## Pitfalls
- Breaking last-wins overwrite semantics: Forgetting to process queries in reverse, or overwriting ans[u] multiple times, breaks the intended behavior. Ensure ans[u] is written at most once and only for the first visit
- Memory blow-up with large d: Allocating col[n][d_max+1] when d_max is not actually small can exceed memory limits. Only use fixed 2D tables if the depth bound is strict and tiny.
- Forgetting to add both directions of an undirected edge: When moving to a manual adjacency array, it is easy to add only (u -> v) and forget (v -> u), which will silently break reachability in one direction.
- Stack overflow from deep recursion: Although depth-limited DFS has shallow depth in the small-d_max case, combining it with long chains and self-loops can still be risky on platforms with small stacks. For safety
- Indexing mistakes when converting to 1-based/0-based arrays: Off-by-one errors in head, to, next arrays, especially when mixing 0-based input with 1-based internal representation.
- Inconsistent initialization of pruning arrays: f[u] must be initialized to a baseline that represents "unvisited" (commonly 0 or -1) and your pruning condition must be coherent with this choice. Mixing >= and >
- Relying on depth-specific visited states for correctness when switching to per-vertex pruning: If the logic truly depends on the exact depth at which a node was visited (e.g., different payload per depth), a 1D f[u]

## When not to use
- When the maximum radius/depth d is large (e.g., up to n or 1e9) and not tightly bounded, and you need depth-specific behavior that a per-vertex maximum-depth marker cannot capture. A 2D state table would be too large
- When queries interact in non-monotone ways that break last-wins semantics (e.g., additive contributions, minimum/maximum aggregations that depend on all queries simultaneously). Reverse processing with one-time
- When the number of queries q is very small (e.g., O(1) or O(log n)), in which case a straightforward BFS/DFS per query may be simpler and fast enough without the overhead of an offline lifted-state design.
- When the graph is extremely small and constant factors dominate, making the complexity gains of offline processing negligible compared to the code complexity and risk of implementation bugs.
- When recursion depth cannot be safely bounded (e.g., very large d combined with long chains) and implementing an iterative DFS/stack is not acceptable or significantly complicates the solution.
- When you must rely on high-level containers and abstractions (e.g., due to coding constraints), and cannot switch to flat arrays; many of the constant-factor advantages of this pattern depend on tight, low-level data

## Minimal example
Before:
```cpp
#include <bits/stdc++.h>
using namespace std; int n,m,Q; vector<vector<int>> g(100005); int col[100005];
// Per-query BFS: touches same (v,dist) states many times
for (int i=0;i<m;i++){int u,v;cin>>u>>v;g[u].push_back(v);g[v].push_back(u);} memset(col,-1,sizeof(col));
for (int qi=0;qi<Q;qi++){int s,d,c;cin>>s>>d>>c; queue<pair<int,int>> q; q.push({s,0});
  vector<int> vis(n+1); vis[s]=1; while(!q.empty()){auto [v,dist]=q.front();q.pop(); if(dist>d) continue; if(col[v]==-1) col[v]=c;
    for(int to:g[v]) if(!vis[to]){vis[to]=1; q.push({to,dist+1});}}}
for(int i=1;i<=n;i++) cout<<col[i]<<"\n";
```
After:
```cpp
#include <bits/stdc++.h>
using namespace std; const int N=100000+5,D=10+1; int n,m,Q,head[N],to[200005*2],nxt[200005*2],ecol[N][D],seen[N][D],vid;
auto ae=[&](int u,int v){static int e=0;to[e]=v;nxt[e]=head[u];head[u]=e++;}; // CSR-style adjacency + self-loops
int V[100005],R[100005],C[100005]; // SoA queries: source, radius, color
void dfs(int s,int dep,int c){ static int st_v[N*D],st_d[N*D]; int top=0; st_v[top]=s; st_d[top++]=dep;
  while(top){int v=st_v[--top],d=st_d[top]; if(d<0||seen[v][d]==vid) continue; seen[v][d]=vid; if(ecol[v][d]==-1) ecol[v][d]=c; for(int e=head[v];~e;e=nxt[e]){int u=to[e]; st_v[top]=u; st_d[top++]=d-1;}}}
int main(){memset(head,-1,sizeof(head)); memset(ecol,-1,sizeof(ecol)); cin>>n>>m>>Q; for(int i=0;i<m;i++){int u,v;cin>>u>>v;ae(u,v);ae(v,u);} for(int i=1;i<=n;i++) ae(i,i);
  for(int i=0;i<Q;i++) cin>>V[i]>>R[i]>>C[i]; for(int qi=Q-1;qi>=0;qi--){++vid; dfs(V[qi],R[qi],C[qi]);} for(int v=1;v<=n;v++) cout<<ecol[v][0]<<"\n"; }
```
