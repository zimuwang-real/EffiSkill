---
skill_id: O016
type: operator
language: cpp
family: coprimality
name: Number Theory Prime Infra Refactor
description: Reusable optimization pattern distilled from weighted traces.
tags:
- number_theory
- sieve
- prime_factorization
- divisors
- gcd
- mobius_like
- DP_over_divisors
- loop_optimization
- memory_optimization
- precomputation_elimination
triggers:
- Full SPF or sieve arrays sized to a large fixed MAX (e.g. 1e6) regardless of actual max(A[i]) or required prime range.
- Per-query or per-element primality checks using trial division up to sqrt(x) without any shared precomputation or prime
  caching.
- Nested loops that factor every number in [1..n] or every array element with repeated modulus/division by all integers or
  all primes each time.
- Secondary passes that only re-count states (e.g. counting unique values, or values with a certain divisor count) which are
  already derivable inside the main sieve/factorization loop.
- Sieve implementations with non-standard O(N^2) patterns (double loops over i and j up to N) or missing i*i start / prime-only
  inner loops.
- Global state arrays or maps used to track prime usage/factors where the relevant prime set is small and static (e.g. primes
  up to sqrt(MAX)).
- Precomputation of primes or SPF that are never actually used in the main computation.
- Factorial-related divisor counting implemented by enumerating divisors or exploring exponent combinations recursively rather
  than using exponent-count DP.
---

## When to use
- Full SPF or sieve arrays sized to a large fixed MAX (e.g. 1e6) regardless of actual max(A[i]) or required prime range.
- Per-query or per-element primality checks using trial division up to sqrt(x) without any shared precomputation or prime caching.
- Nested loops that factor every number in [1..n] or every array element with repeated modulus/division by all integers or all primes each time.
- Secondary passes that only re-count states (e.g. counting unique values, or values with a certain divisor count) which are already derivable inside the main sieve/factorization loop.
- Sieve implementations with non-standard O(N^2) patterns (double loops over i and j up to N) or missing i*i start / prime-only inner loops.
- Global state arrays or maps used to track prime usage/factors where the relevant prime set is small and static (e.g. primes up to sqrt(MAX)).
- Precomputation of primes or SPF that are never actually used in the main computation.
- Factorial-related divisor counting implemented by enumerating divisors or exploring exponent combinations recursively rather than using exponent-count DP.

## Steps
1. Analyze required number-theoretic primitives: Identify exactly what the task needs: primality for many queries, factorization of numbers up to MAX, divisor counts, gcd-based classifications, or specific divisor-sum identities.
2. Analyze required number-theoretic primitives: Determine tight numeric bounds: max(A[i]), max query value, and whether they are global or per-testcase.
3. Choose the minimal prime infrastructure: If you need primality for many values up to a global bound V (e.g. 1e6): use a standard Sieve of Eratosthenes up to V with O(V log log V) time and O(V) space.
4. Choose the minimal prime infrastructure: If you only need factorization for values up to 1e6 and in small quantity: pre-embed a static table of all primes up to sqrt(1e6)=1000 and factor by trial division over this fixed list.
5. Choose the minimal prime infrastructure: If only a few sparse values are relevant (e.g. special primes like p with (p+1)/2 prime): consider offline precomputation and hardcoding the resulting list.
6. Tighten sieve / prime generation: Implement a clean Eratosthenes sieve: boolean is_prime[0..V], set all true then mark 0,1 false. For i from 2 to floor(sqrt(V)), if is_prime[i], mark j = i*i, i*i+i, <= V as false.
7. Tighten sieve / prime generation: Use the minimal V required by the problem, e.g. V = maxA or V = floor(sqrt(maxA)) depending on whether you sieve values or potential divisors.
8. Tighten sieve / prime generation: Avoid nested O(V^2) patterns and redundant work over composite bases.

## Complexity
- Time: (pattern dependent)
- Space: Reduced from O(MAX) or O(V) for large SPF/sieve tables and assorted helper arrays to either O(V_eff) where V_eff is the actual needed domain (e.g. maxA or sqrt(maxA)), or to O(1) additional space beyond the input when using static

## Pitfalls
- Over-sieving: allocating SPF or sieve arrays up to 1e6 or higher when the input maximum is far smaller, causing unnecessary O(MAX) precomputation and memory traffic.
- Recomputing sieves or prime lists from scratch for each test case even when the global bound is fixed and can be reused.
- Using naive trial division up to sqrt(x) for each query while ignoring that many queries share the same small divisors and could benefit from a shared sieve.
- Implementing custom or linear sieves with extra branches and irregular inner loops that, for moderate N (<=1e6), are slower in practice than a clean Eratosthenes implementation.
- Relying on map/unordered_map keyed by primes or small integers when a flat array indexed by position would be simpler, faster, and more memory efficient.
- Factoring every integer in a range to compute a divisor-sum or divisor-count expression that actually has a known arithmetic identity allowing O(n) computation without factorization.
- Leaving unused prime infrastructure (sieves, SPF arrays, vectors of primes) in the code path, paying their initialization cost even though the main algorithm no longer uses them.
- Incorrect or missing overflow checks when building multiplicative signatures, nth-root divisors, or powers (e.g., computing i^n in a loop without checking for overflow).

## When not to use
- When input bounds are extremely large (e.g. values near 1e12–1e18) and you need many factorizations of arbitrary numbers; in such cases, Pollard–Rho + Miller–Rabin with carefully tuned modular arithmetic is more
- When the number of queries Q is very small and the maxima are moderate (e.g. a handful of primality checks up to 1e9); one-off trial division or deterministic Miller–Rabin may be simpler and fast enough without setting
- When the code already uses a well-implemented, minimal Eratosthenes sieve or small-prime static table tuned to constraints, and profiling shows that the dominant time is elsewhere (e.g. in combinatorial DP or I/O)
- When the problem requires exact tracking of high prime powers or large intermediate products surpassing 64-bit ranges, where aggressive capping or sentinel-based overflow handling would break correctness; in such

## Minimal example
Before:
```cpp
#include <bits/stdc++.h>
using namespace std;

bool isPrime(long long x){
    if (x < 2) return false;
    for (long long p = 2; p * p <= x; ++p)
        if (x % p == 0) return false;
    return true;
}

int main(){
    long long n; cin >> n;
    vector<long long> a(n);
    for (auto &x : a) cin >> x;
    long long cnt = 0;
    for (auto x : a) if (isPrime(x)) ++cnt;
    cout << cnt;
}
```
After:
```cpp
#include <bits/stdc++.h>
using namespace std;

struct PrimeInfra {
    vector<int> spf; // smallest prime factor
    PrimeInfra(int N){
        spf.assign(N + 1, 0);
        for (int i = 2; i <= N; ++i) if (!spf[i]) {
            spf[i] = i;
            if ((long long)i * i <= N)
                for (int j = i * i; j <= N; j += i)
                    if (!spf[j]) spf[j] = i;
        }
    }
    bool isPrime(int x) const { return x >= 2 && spf[x] == x; }
};

int main(){
    int n; cin >> n;
    vector<int> a(n);
    int mx = 0;
    for (auto &x : a) { cin >> x; mx = max(mx, x); }
    PrimeInfra infra(mx);
    long long cnt = 0;
    for (int x : a) if (infra.isPrime(x)) ++cnt;
    cout << cnt;
}
```
