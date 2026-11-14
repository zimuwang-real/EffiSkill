---
skill_id: O015
type: operator
language: cpp
family: combinatorics
name: Pruned Search And Numeric Tuning
description: Systematically speed up bounded searches and numeric optimization by (1) mathematically pruning the search space,
  (2) reducing unnecessary precision and iterations, and (3) replacing heavy per-iteration work (sqrt, pow, gcd-heavy rational
  ops, full-cost evaluation) with cheaper predicates or closed-form formulas.
tags:
- optimization
- constant_factor
- search_pruning
- numeric_methods
- geometry
- number_theory
- binary_search_on_answer
- bruteforce_optimization
triggers:
- Fixed large iteration caps or hard bounds that are not derived from input, e.g. for (i = 0; i < 1000000000; ++i) or binary
  search loops with 1e5+ iterations.
- Nested loops over a small constant grid (e.g. up to a few thousands) where many candidate states are mathematically impossible
  but still tested.
- Brute-force search over all pairs/triples of points or divisors (O(n^2), O(n^3)) for problems that have divisor symmetry,
  geometric formulas, or known algorithmic upgrades.
- Numeric optimization using ternary/binary search with very tight EPS (1e-9 or smaller) and many iterations, while the judge
  requires only ~1e-6 to 1e-8 accuracy.
- Hot loops with frequent sqrt, pow with small integer exponents, acos/sin/cos, or distance() functions that recompute sqrt(pow(dx,2)+pow(dy,2))
  every time.
- Search loops that always scan up to a fixed upper bound even though any acceptable candidate could terminate the search
  early (earliest-feasible-solution semantics).
- Rational/number-theoretic computations (Frac with gcd, naive pow, non-Euclidean gcd) executed in every iteration of a bounded
  brute-force grid or search.
- Use of generic geometric/number-theoretic toolkits (complex points, dynamic containers, binary searches on geometric parameters)
  where a closed-form or O(sqrt) arithmetic solution exists.
---

## When to use
- Fixed large iteration caps or hard bounds that are not derived from input, e.g. for (i = 0; i < 1000000000; ++i) or binary search loops with 1e5+ iterations.
- Nested loops over a small constant grid (e.g. up to a few thousands) where many candidate states are mathematically impossible but still tested.
- Brute-force search over all pairs/triples of points or divisors (O(n^2), O(n^3)) for problems that have divisor symmetry, geometric formulas, or known algorithmic upgrades.
- Numeric optimization using ternary/binary search with very tight EPS (1e-9 or smaller) and many iterations, while the judge requires only ~1e-6 to 1e-8 accuracy.
- Hot loops with frequent sqrt, pow with small integer exponents, acos/sin/cos, or distance() functions that recompute sqrt(pow(dx,2)+pow(dy,2)) every time.
- Search loops that always scan up to a fixed upper bound even though any acceptable candidate could terminate the search early (earliest-feasible-solution semantics).
- Rational/number-theoretic computations (Frac with gcd, naive pow, non-Euclidean gcd) executed in every iteration of a bounded brute-force grid or search.
- Use of generic geometric/number-theoretic toolkits (complex points, dynamic containers, binary searches on geometric parameters) where a closed-form or O(sqrt) arithmetic solution exists.

## Steps
1. Identify the true objective and required precision: Decide whether the outer algorithm needs a full numeric cost (e.g., value of a function) or only a feasibility predicate for a search (true/false).
2. Identify the true objective and required precision: Check the output specification and judge tolerance to see if double precision and ~1e-6–1e-8 accuracy are sufficient.
3. Prune the search space using math bounds: For integer equations and divisor-like conditions, use symmetry and factor-pair reasoning to restrict loops to i <= sqrt(n) or similar, and derive bounds like i > n / 4 for constrained equations.
4. Prune the search space using math bounds: For modular or periodic problems, bound the active range (e.g. interval length <= modulus) instead of scanning multiples up to a large constant.
5. Prune the search space using math bounds: Tighten brute-force ranges by bounding variables via growth rates (e.g., |x|^5 <= limit ⇒ |x| <= 200 instead of 500).
6. Prune the search space using math bounds: In grid searches over (i, j), derive per-i bounds on j from inequalities and precompute partially-shared expressions once per i.
7. Switch from full-cost evaluation to boolean predicates with early exit: When used inside binary search on an answer, replace heavy calc(x) that returns a numeric cost with a lightweight predicate feasible(x) that returns whether the cost meets the requirement.
8. Switch from full-cost evaluation to boolean predicates with early exit: In multiplicative or aggregating loops, stop as soon as the threshold condition (e.g., s >= n) is met and return; avoid extra iterations and final ceil divisions.

## Complexity
- Time: (pattern dependent)
- Space: Usually unchanged or reduced: O(1) or O(n) as in the original algorithm, since optimizations focus on arithmetic, iteration counts, and search-space bounds rather than new data structures.

## Pitfalls
- Deriving incorrect or too-aggressive bounds, leading to missed solutions (e.g., underestimating the maximum exponent/root and cutting off valid search space).
- Reducing iteration counts or loosening EPS without verifying that the resulting precision still satisfies the problem’s error tolerance.
- Switching from long double to double in geometry or delicate numeric problems where accumulated error can change inequality outcomes or boundary cases.
- Assuming that earliest feasible solution is always acceptable; some tasks genuinely require a global optimum and cannot stop at the first valid candidate.
- Converting distance-based logic to squared distances but forgetting to adjust comparisons or to apply sqrt when producing final outputs.
- Over-optimizing one component (e.g., replacing exact search with heuristic hill-climbing) in tasks that require exact answers rather than approximate ones.
- Replacing robust set-based checks with lookup tables without ensuring the table’s maximum range safely covers all possible values.
- Using integer arithmetic for formulas that actually need rounding or real-valued behavior, causing off-by-one or truncation bugs.

## When not to use
- When the problem strictly requires exact global optima and the proposed optimization relies on heuristics (e.g., simulated annealing or gradient-like hill-climbing) instead of provably correct searches.
- When no solid mathematical proof or constraint-based argument is available to justify the proposed pruning of the search range.
- When high-precision arithmetic (long double, big integers) is necessary for correctness due to extremely tight error bounds or numerically unstable formulas.
- In situations where the bottleneck is clearly asymptotic (e.g., inherently O(n^2) I/O or DP) rather than numeric constant factors; in those cases, a different algorithm is needed, not just tuning.
- When the implementation cost or code complexity of the optimization (e.g., a full smallest-enclosing-circle routine) outweighs its benefit for very small input sizes.

## Minimal example
Before:
```cpp
#include <bits/stdc++.h>
using namespace std;
double best_dist(const vector<pair<double,double>>& p){
    auto f = [&](double t){ // brute numeric, over-precise
        double x = t, y = t*t; double best = 1e100;
        for (auto [px,py]: p) best = min(best, hypot(x-px, y-py)); // sqrt each time
        return best;
    };
    double L = 0, R = 1; // unnecessary 1000 iters, 1e-12-level
    for (int it = 0; it < 1000; ++it){
        double m1 = (2*L+R)/3, m2 = (L+2*R)/3;
        if (f(m1) < f(m2)) R = m2; else L = m1;
    }
    return f((L+R)/2);
}
```
After:
```cpp
#include <bits/stdc++.h>
using namespace std;
double best_dist(const vector<pair<double,double>>& p){
    auto f2 = [&](double t){ // pruned & cheaper eval
        double x = t, y = t*t; double best = 1e100;
        for (auto [px,py]: p){
            double dx = x-px, dy = y-py; // use squared distance, no sqrt
            best = min(best, dx*dx + dy*dy);
        }
        return best;
    };
    double L = 0, R = 1; // 60 iters already < 1e-8 on [0,1]
    for (int it = 0; it < 60; ++it){
        double m1 = (2*L+R)/3, m2 = (L+2*R)/3;
        if (f2(m1) < f2(m2)) R = m2; else L = m1;
    }
    return sqrt(f2((L+R)/2)); // single sqrt at the end
}
```
