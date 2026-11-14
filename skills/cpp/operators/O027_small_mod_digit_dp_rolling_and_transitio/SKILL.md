---
skill_id: O027
type: operator
language: cpp
family: dp
name: Small Mod Digit DP Rolling And Transition Compression
description: Refactor digit- or remainder-based DP with a small fixed modulus into an iterative rolling-array DP with precomputed
  transitions and primitive modular arithmetic, eliminating recursion, oversized tables, and heavy abstractions. When the
  DP states arise from sums of digits in fixed bases with exponentially growing coin values, replace the DP entirely with
  digit-sum formulas in those bases.
tags:
- dp
- digit_dp
- string_dp
- modular_arithmetic
- rolling_array
- precomputation
- constant_factor_optimization
- math_optimization
triggers:
- DP states are (position, remainder mod M) or similar with a very small fixed M (e.g., <= 20).
- Large DP table dimensioned as dp[N][M] where N is up to 1e5+ and only adjacent positions depend on each other.
- Implementation uses recursion over position with depth proportional to input size, risking stack overflow.
- Inner loops repeatedly compute (rem * base + digit) % M with small fixed base and digit range.
- A generic modular integer struct or heavy operator overloading is used in tight DP loops.
- DP uses 64-bit values where results are always modulo a 32-bit constant (e.g., 1e9+7).
- Per-test memset over large dp[N][M] tables where only a small frontier is needed.
- Problem structure is coin-change-like with denominations {1} ∪ {b1^k} ∪ {b2^k} for small integer bases b1, b2, suggesting
  digit-sum formulas.
---

## When to use
- DP states are (position, remainder mod M) or similar with a very small fixed M (e.g., <= 20).
- Large DP table dimensioned as dp[N][M] where N is up to 1e5+ and only adjacent positions depend on each other.
- Implementation uses recursion over position with depth proportional to input size, risking stack overflow.
- Inner loops repeatedly compute (rem * base + digit) % M with small fixed base and digit range.
- A generic modular integer struct or heavy operator overloading is used in tight DP loops.
- DP uses 64-bit values where results are always modulo a 32-bit constant (e.g., 1e9+7).
- Per-test memset over large dp[N][M] tables where only a small frontier is needed.
- Problem structure is coin-change-like with denominations {1} ∪ {b1^k} ∪ {b2^k} for small integer bases b1, b2, suggesting digit-sum formulas.

## Steps
1. Detect the small-mod DP structure: Identify that states are indexed by (position i, remainder r) or comparable small remainder-like dimension.
2. Detect the small-mod DP structure: Confirm that transitions only depend on previous position(s), e.g., position i uses only position i-1.
3. Eliminate recursion: Replace solve(i, r) or similar recursive routines by an explicit for-loop over positions.
4. Eliminate recursion: Convert memoized recursion into bottom-up DP that scans the string/array left-to-right.
5. Introduce rolling DP over the small remainder dimension: Replace dp[N][M] with dp[2][M] (or two arrays curr[M], next[M]) and toggle between them each step.
6. Introduce rolling DP over the small remainder dimension: Zero only the next layer each iteration instead of memset over the full N×M table.
7. Precompute remainder transitions for digits or small symbols: Use g[r][d] directly inside the DP loops instead of recomputing the formula.
8. Optimize DP transitions for fixed vs wildcard characters: For a fixed digit x: for each remainder r, do next[g[r][x]] += curr[r].

## Complexity
- Time: General small-mod digit DP (before): typically O(N * M * B) where N is length, M is modulus states, B is branching factor (e.g., up to 10 digits), with large constants from recursion and redundant modulo.
- Space: Before refactor: O(N * M) DP table plus recursion stack O(N) in recursive formulations.

## Pitfalls
- Using long long for DP values modulo a 32-bit MOD without need, doubling memory and slowing modulo operations.
- Leaving recursive DP with depth ~N in place, leading to stack overflow on large inputs despite optimal asymptotics.
- Forgetting to clear the 'next' DP layer before filling it, causing incorrect accumulation across positions.
- Recomputing (r * base + d) % M inside nested loops instead of using a precomputed transition table.
- Applying the modulus on every single addition in hot loops rather than batching reductions, causing unnecessary overhead.
- Keeping an oversized DP dimension (e.g., M+2) or global dp[N_max][M] even when only 2×M states are used, hurting cache efficiency.
- Using a generic modular-int class with operator overloading in very tight loops, which can prevent full inlining or introduce extra instructions.
- Misapplying the digit-sum reformulation: it only works for coin sets matching {1} plus pure powers of fixed bases without additional arbitrary denominations.

## When not to use
- When the remainder dimension M is large (e.g., M ~ N or >= 1e5); rolling 2×M is still fine, but precomputing full M×B transition tables may be too expensive or memory-heavy.
- When transitions depend on the full history or multiple non-adjacent positions, so that only keeping two DP layers is insufficient.
- When generic modular operations (inverse, division) are essential in the inner loops; replacing them with ad-hoc arithmetic might be error-prone or impossible.
- When coin denominations are arbitrary and do not match a clean mixed-radix structure; the digit-sum shortcut will not be correct in that case and a normal DP is required.
- When the modulus or DP value range exceeds 32-bit bounds and careful 64-bit handling is required to avoid overflow.

## Minimal example
Before:
```cpp
#include <bits/stdc++.h>
using namespace std; const int MOD=1e9+7; string s; int n,dp[100005][13];
int solve(int i,int r){
 if(i==n) return r==5;
 int &res=dp[i][r]; if(res!=-1) return res; res=0;
 if(s[i]=='?') for(int d=0;d<10;d++) res=(res+solve(i+1,(r*10+d)%13))%MOD;
 else res=solve(i+1,(r*10+s[i]-'0')%13);
 return res;
}
```
After:
```cpp
#include <bits/stdc++.h>
using namespace std; const int MOD=1e9+7; string s; int n,nxt[13][10];
int solve(){
 int dp[2][13]={0}; dp[0][0]=1;
 for(int i=0,cur=0;i<n;i++,cur^=1){ memset(dp[cur^1],0,sizeof dp[cur^1]);
  for(int r=0;r<13;r++) if(dp[cur][r]){ if(s[i]=='?') for(int d=0;d<10;d++) dp[cur^1][nxt[r][d]]=(dp[cur^1][nxt[r][d]]+dp[cur][r])%MOD; else dp[cur^1][nxt[r][s[i]-'0']]=(dp[cur^1][nxt[r][s[i]-'0']]+dp[cur][r])%MOD; }
 }
 return dp[n&1][5];
}
```
