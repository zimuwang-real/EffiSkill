---
skill_id: O009
type: operator
language: cpp
family: combinatorics
name: Optimize Mod Comb Precomputation
description: Systematically minimize time and space overhead in modular-combinatorics code by (1) using linear-time factorial/inverse-factorial
  precomputation instead of repeated modular exponentiation or exgcd, (2) sizing precomputation tightly to the actual input
  bounds, and (3) replacing generic combinatorics with algebraic or closed-form simplifications when the structure allows.
  Applicable to grid paths, binomial sums
tags:
- combinatorics
- binomial-coefficients
- modular-arithmetic
- factorials
- inverse-factorials
- precomputation
- constant-factor-optimization
- NTT
- FWT
- grid-paths
triggers:
- Factorial / inverse-factorial tables built up to a large fixed MAXN before reading input, regardless of actual n, m.
- Precomputation loops of length N that call pow(x, MOD-2) or exgcd in each iteration to build inverse or inverse-factorial
  arrays.
- Combination helper C(n, k) that recomputes modular inverses via pow or exgcd on every call, especially inside O(n) or O(n
  log n) loops.
- Large global arrays for combinatorics (e.g., 1e5–1e6) used for only a constant number of combinations or a single test case.
- Problems that only need special cases like C(x, 2), C(x, 1), or rigid frequency patterns, but currently use full generic
  nCr and factorial tables.
- Bitmask DP, NTT/FWT, or polynomial convolutions where factorial/inverse or root-of-unity setup dominates runtime via repeated
  modpow.
- Binomial arguments bounded by simple functions of the input (e.g., up to h + w - 2, m + k, n + p[i] - 1), but code still
  uses a larger hard-coded bound.
- Hot loops that repeatedly call a small combinatorics helper or perform many a * b % MOD operations with scattered '%' and
  64-bit temporaries.
---

## When to use
- Factorial / inverse-factorial tables built up to a large fixed MAXN before reading input, regardless of actual n, m.
- Precomputation loops of length N that call pow(x, MOD-2) or exgcd in each iteration to build inverse or inverse-factorial arrays.
- Combination helper C(n, k) that recomputes modular inverses via pow or exgcd on every call, especially inside O(n) or O(n log n) loops.
- Large global arrays for combinatorics (e.g., 1e5–1e6) used for only a constant number of combinations or a single test case.
- Problems that only need special cases like C(x, 2), C(x, 1), or rigid frequency patterns, but currently use full generic nCr and factorial tables.
- Bitmask DP, NTT/FWT, or polynomial convolutions where factorial/inverse or root-of-unity setup dominates runtime via repeated modpow.
- Binomial arguments bounded by simple functions of the input (e.g., up to h + w - 2, m + k, n + p[i] - 1), but code still uses a larger hard-coded bound.
- Hot loops that repeatedly call a small combinatorics helper or perform many a * b % MOD operations with scattered '%' and 64-bit temporaries.

## Steps
1. Analyze actual combinatorial needs: , max(n, m), or n + max_exponent
2. Analyze actual combinatorial needs: .
3. Analyze actual combinatorial needs: Check whether only special forms (e.g., C(x, 0), C(x, 1), C(x, 2)) or a small constant set of nCr values are needed; note any closed-form simplifications.
4. Analyze actual combinatorial needs: For frequency/pattern problems, derive whether the count simplifies to a small formula like 2^{n/2} or C(cnt, 2) instead of generic nCr.
5. Tighten precomputation bounds and structure: Let LIM be the smallest safe maximum needed for n in any C(n, k).
6. Tighten precomputation bounds and structure: Allocate factorial and inverse-factorial arrays fact[0..LIM], invfact[0..LIM] (or a single combined array if convenient), rather than using a hard-coded constant much larger than LIM.
7. Tighten precomputation bounds and structure: If LIM depends on input, read all relevant parameters first, compute LIM, then precompute up to LIM instead of a fixed global MAXN.
8. Tighten precomputation bounds and structure: For tasks with a very small number of combinations or tiny n, consider skipping tables entirely and using direct O(n) factorial loops or O(min(k, n-k)) multiplicative nCr.

## Complexity
- Time: Typical transformed patterns move from O(N log MOD + Q) precomputation-and-query cost (due to per-index or per-call modular exponentiation) to O(N + log MOD + Q) where N is the tight maximum over binomial arguments or related
- Space: Space is typically reduced from O(MAXN) with large fixed bounds (up to ~1e6) to O(LIM) where LIM is the true required maximum n across all combinations. In some single-query cases, factorial tables can be removed entirely, improving space

## Pitfalls
- Undersizing factorial / inverse-factorial arrays relative to the largest n used in C(n, k) (e.g., forgetting that grid-path formulas need up to h + w - 2).
- Leaving a mix of old and new combinatorics code paths (some using exgcd or pow-based inverses, some using tables) leading to inconsistent performance and harder debugging.
- Miscomputing inverse factorial propagation: writing invfact[i-1] = invfact[i] * (i-1) instead of * i, or starting the backward loop from the wrong index.
- Using 32-bit int for intermediate products when MOD or arguments are large enough that i * j can overflow; always widen to 64-bit for multiplications before reducing modulo.
- Accidentally applying MOD arithmetic where exact integer arithmetic was intended (or vice versa) when replacing factorial-based formulas with closed-form expressions.
- Assuming that generic nCr is always needed: sometimes a much simpler combinatorial identity (C(x, 2), 2^{n/2}, etc.) suffices; overlooking this can leave large constant factors.
- Over-optimizing precomputation (large LIM) for a single-query problem, where direct O(n) multiplicative nCr or factorial computation would be simpler and faster overall.
- Using pow_mod in inner loops (NTT, FWT, DP transitions) after introducing factorial tables, thus keeping an unnecessary log MOD factor in hot paths.

## When not to use
- When the problem needs only a handful of small nCr values with very small n (e.g., n <= 50) and no tight time limits; a direct multiplicative nCr or even a naive DP is sufficient and simpler.
- When MOD is not prime or modular inverses may not exist for all required values; factorial/inverse-factorial techniques relying on Fermat’s little theorem are not directly applicable.
- When memory constraints are very tight and LIM is large enough that even O(LIM) factorial tables are borderline (for example, LIM on the order of 10^7 with strict memory limits).
- When the combinatorial structure does not fit standard binomial-coefficient patterns (e.g., arbitrary recurrence with no closed-form, non-modular counting with exact big integers).
- When profiling shows that combinatorics precomputation is negligible compared to some other bottleneck (heavy graph traversal, complex geometry, large NTTs), and further refactoring combinatorics adds complexity
- When problem guarantees only a single very small test and clarity or code golf matters more than micro-optimizations; in such cases, elaborate factorial tables and optimization infrastructure may be overkill.

## Minimal example
Before:
```cpp
const int MOD = 1e9+7;
long long modpow(long long a,long long e){long long r=1;while(e){if(e&1)r=r*a%MOD;a=a*a%MOD;e>>=1;}return r;}
long long C(long long n,long long k){if(k<0||k>n)return 0;long long num=1,den=1;for(long long i=1;i<=k;i++){num=num*(n-k+i)%MOD;den=den*i%MOD;}return num*modpow(den,MOD-2)%MOD;}
int main(){int n;cin>>n;long long ans=0;for(int i=0;i<=n;i++)ans=(ans+C(n,i))%MOD;cout<<ans;}
```
After:
```cpp
const int MOD = 1e9+7;
long long modpow(long long a,long long e){long long r=1;while(e){if(e&1)r=r*a%MOD;a=a*a%MOD;e>>=1;}return r;}
int main(){int n;cin>>n;vector<long long> fact(n+1),invf(n+1);fact[0]=1;for(int i=1;i<=n;i++)fact[i]=fact[i-1]*i%MOD;invf[n]=modpow(fact[n],MOD-2);for(int i=n;i;i--)invf[i-1]=invf[i]*i%MOD;auto C=[&](int N,int K){if(K<0||K>N)return 0LL;return fact[N]*invf[K]%MOD*invf[N-K]%MOD;};long long ans=0;for(int i=0;i<=n;i++)ans=(ans+C(n,i))%MOD;cout<<ans;}
```
