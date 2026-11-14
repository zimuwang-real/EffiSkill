---
skill_id: O012
type: operator
language: cpp
family: graph
name: Opt Grid Search And State Space
description: 'Refactor grid-based search/DP solutions to eliminate redundant state dimensions, over-sized buffers, and heavy
  STL structures by matching the algorithm and memory layout tightly to the true constraints (grid size, sparsity, special
  points, weight range). Typical transformations: collapsing (position,mask) BFS to multi-source BFS + bitmask DP on a small
  node set, switching Dijkstra to 0-1 BFS on 0/1 weighted grids'
tags:
- grid
- bfs
- shortest_path
- dynamic_programming
- bitmask_dp
- coordinate_compression
- 0-1_bfs
- simulation
- constant_factor_optimization
- state_space_reduction
triggers:
- BFS or Dijkstra on an unweighted or 0/1-weighted grid using priority_queue, std::set, or other log-factor frontiers.
- State space modeled as (position, subset-mask) over an h×w grid with c special cells, giving O(h*w*2^c) states when c is
  small (≈ 10–11).
- Static 2D/3D arrays with large fixed bounds (e.g., 1000×1000, 300×300, 120×120×120) while the instance grid is much smaller
  or the effective search radius is limited.
- Repeated full-grid memset/initialization (or constructor-based clears) per test, especially to MAXN-sized buffers not fully
  used by the instance.
- Use of std::map or std::set for coordinate compression or membership tests on small key universes where sorted vectors +
  lower_bound or direct arrays would suffice.
- Grid BFS that enqueues the same cell multiple times because visited marks are applied on pop instead of on push.
- 'Use of long long for grid distances and coordinates when max path length is ≤ 1e6, and presence of global macros like #define
  int long long in grid BFS.'
- Brute-force over cells or large scalar ranges (e.g., 2^(h*w) subsets or s in [-1e6,1e6]) in constant-size or very small
  grids.
---

## When to use
- BFS or Dijkstra on an unweighted or 0/1-weighted grid using priority_queue, std::set, or other log-factor frontiers.
- State space modeled as (position, subset-mask) over an h×w grid with c special cells, giving O(h*w*2^c) states when c is small (≈ 10–11).
- Static 2D/3D arrays with large fixed bounds (e.g., 1000×1000, 300×300, 120×120×120) while the instance grid is much smaller or the effective search radius is limited.
- Repeated full-grid memset/initialization (or constructor-based clears) per test, especially to MAXN-sized buffers not fully used by the instance.
- Use of std::map or std::set for coordinate compression or membership tests on small key universes where sorted vectors + lower_bound or direct arrays would suffice.
- Grid BFS that enqueues the same cell multiple times because visited marks are applied on pop instead of on push.
- Use of long long for grid distances and coordinates when max path length is ≤ 1e6, and presence of global macros like #define int long long in grid BFS.
- Brute-force over cells or large scalar ranges (e.g., 2^(h*w) subsets or s in [-1e6,1e6]) in constant-size or very small grids.

## Steps
1. Tighten the problem model: Confirm grid dimensions and actual constraints (max H,W, number of special points c, number of non-zero items K).
2. Tighten the problem model: Identify whether edges are unweighted, 0/1-weighted, or small bounded integer weights.
3. Tighten the problem model: Detect sparsity (explicit K items vs implicit R*C cells) and whether only a few special points matter.
4. Choose the right graph/search primitive: For unweighted grids: replace Dijkstra/priority_queue with plain BFS using std::queue and integer (x,y) or linear indices.
5. Choose the right graph/search primitive: For 0/1 weights: replace Dijkstra with 0-1 BFS using a deque, pushing 0-cost transitions to the front and 1-cost to the back.
6. Choose the right graph/search primitive: For grids with small c special nodes: precompute BFS distances from each special node and run bitmask DP on a (c+1)-node graph instead of BFS over (pos,mask).
7. Reduce state space and precompute smartly: Collapse (position,mask) grids to (position) BFS + bitmask DP on special nodes when the objective depends only on visit order of a small set.
8. Reduce state space and precompute smartly: For combinatorial search on tiny grids (h,w ≤ ~6), encode decisions as row/column masks (2^h * 2^w) instead of per-cell subsets (2^(h*w)).

## Complexity
- Time: (pattern dependent)
- Space: Reduces from worst-case static allocations like O(MAXH*MAXW) or O(MAX^3) (e.g., 1000×1000 grids, 120×120×120 volumes, 3D (position,mask) DP) to O(H*W) or O(K + C^2 + c*2^c) as appropriate. Visited and distance arrays use minimal necessary

## Pitfalls
- Shrinking static arrays based on an optimized reference without re-checking problem constraints, causing out-of-bounds access on larger hidden tests.
- Changing from long long to int for distances or indices without verifying the maximum possible value (e.g., H*W up to 1e6) fits in 32 bits.
- Incorrectly marking visited in BFS (e.g., on pop instead of on push) and assuming the optimized version still explores each cell once.
- Implementing 0-1 BFS but accidentally mixing 0- and 1-cost edges in a normal queue, reintroducing the need for Dijkstra.
- Performing coordinate compression but forgetting to adjust bounds and loops to use the compressed size, leaving dead regions that are still memset every test.
- Over-aggressive sparsity: switching to K-based DP when K can be as large as R*C in some tests, inadvertently worsening constants or exceeding memory due to underestimated K.
- Relying on structural/number-theoretic patterns (e.g., distance tilings) without fully handling edge cases (small grids, degenerate distances) leading to off-by-one patterns or missing border cells.
- Interleaving algorithmic changes with I/O refactors and type changes, making it hard to attribute correctness issues and hindering targeted debugging.

## When not to use
- When the original asymptotics are already tight and constraints are tiny (e.g., ≤ 20×20) such that readability is more important than constant-factor gains.
- When edge weights are arbitrary positive values and 0-1 BFS or simple BFS is not applicable; Dijkstra or other SSSP algorithms are inherently required.
- When the grid or graph is highly irregular or dynamic (e.g., obstacles added/removed on the fly, online queries) and precomputation plus state-space reduction becomes more expensive than straightforward search.
- When the problem guarantees that R*C is small but K (number of items) is always dense and near R*C; sparse representations then add overhead with no asymptotic benefit.
- When lattice structure or number-theoretic patterns are non-trivial or poorly understood; forcing a pattern-based solution without a proof can introduce subtle correctness bugs.
- When memory is abundant and development time is very limited; heavy refactors (e.g., custom BFS layouts, bespoke compression) may not be worth it relative to a simpler O(H*W) solution that already passes.

## Minimal example
Before:
```cpp
const int H=20,W=20,C=10;int dist[H][W][1<<C];
queue<tuple<int,int,int>> q;memset(dist,0x3f,sizeof(dist));q.push({sx,sy,1<<start});dist[sx][sy][1<<start]=0;
while(!q.empty()){auto [x,y,mask]=q.front();q.pop();for(int d=0;d<4;d++){int nx=x+dx[d],ny=y+dy[d];if(nx<0||ny<0||nx>=H||ny>=W||grid[nx][ny]=='#')continue;int id=is_dirty[nx][ny];int nmask=mask|(id==-1?0:(1<<id));if(dist[nx][ny][nmask]>dist[x][y][mask]+1){dist[nx][ny][nmask]=dist[x][y][mask]+1;q.push({nx,ny,nmask});}}}
int ans=INF;for(int mask=0;mask<(1<<C);mask++)if(all_clean(mask))ans=min(ans,dist[gx][gy][mask]);
```
After:
```cpp
const int H=20,W=20,C=10;int gdist[C][C],dp[1<<C][C];
vector<pair<int,int>> p(C);p[0]={sx,sy};for(int i=1;i<C;i++)p[i]=dirty[i-1];
for(int s=0;s<C;s++){static int d[H][W];memset(d,0x3f,sizeof(d));queue<pair<int,int>> q;q.push(p[s]);d[p[s].first][p[s].second]=0;while(!q.empty()){auto [x,y]=q.front();q.pop();for(int k=0;k<4;k++){int nx=x+dx[k],ny=y+dy[k];if(nx<0||ny<0||nx>=H||ny>=W||grid[nx][ny]=='#'||d[nx][ny]<=d[x][y]+1)continue;d[nx][ny]=d[x][y]+1;q.push({nx,ny});}}for(int t=0;t<C;t++)gdist[s][t]=d[p[t].first][p[t].second];}
memset(dp,0x3f,sizeof(dp));dp[1][0]=0;for(int mask=0;mask<(1<<C);mask++)for(int u=0;u<C;u++)if(dp[mask][u]<INF)for(int v=0;v<C;v++)if(!(mask>>v&1)&&gdist[u][v]>=0)dp[mask|1<<v][v]=min(dp[mask|1<<v][v],dp[mask][u]+gdist[u][v]);
int ans=INF;for(int u=0;u<C;u++)ans=min(ans,dp[(1<<C)-1][u]);
```
