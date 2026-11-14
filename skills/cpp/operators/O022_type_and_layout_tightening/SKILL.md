---
skill_id: O022
type: operator
language: cpp
family: state_compression
name: Type And Layout Tightening
description: Refactor solutions to keep the algorithm but aggressively tighten numeric types, memory layout, and per-iteration
  work. Replace oversized arrays, generic geometry, and long double / 64-bit arithmetic with problem-appropriate types and
  closed-form or precomputed math. Aim to keep asymptotic complexity while substantially reducing constant factors, improving
  cache locality, and eliminating unnecessary floating-point
tags:
- constant-factor-optimization
- numeric-types
- memory-layout
- bitmask-dp
- dijkstra
- probability
- expected-value
- computational-geometry
- precomputation
- implementation-detail
triggers:
- Code uses long double or std::complex<long double> while required precision is around 1e-8..1e-10 and coordinates or distances
  are moderate.
- All problem constraints fit comfortably in 32-bit int but the implementation uses long long for loop indices, counters,
  and small values in hot paths.
- Large static arrays are sized with loose upper bounds (e.g., 1000x1000, 31^3, or hard-coded MASK) and fully cleared each
  test, while actual constraints are much smaller.
- Heavy floating-point loops approximate a clear mathematical pattern (geometric series, binomial probabilities, expected
  attempts) that suggests a closed-form or precomputable expression.
- Graph or DP state uses unnecessarily wide or complex payloads (nested pairs, chars misused for indices, redundant dimensions
  like prev that do not affect transitions).
- Geometry-heavy code spends most time in generic primitives (cross, ccw, std::vector segments, complex arithmetic) although
  the specific task is low-dimensional or structured (e.g., piecewise-linear in x).
- Bitmask DP or inclusion–exclusion enumerations use long long, repeated gcd/lcm, or extra sorts inside 2^m loops where m
  ≤ 20.
- Per-test arrays are zero-initialized with = {0} or cleared via double nested loops even when only the first n or m entries
  are used.
---

## When to use
- Code uses long double or std::complex<long double> while required precision is around 1e-8..1e-10 and coordinates or distances are moderate.
- All problem constraints fit comfortably in 32-bit int but the implementation uses long long for loop indices, counters, and small values in hot paths.
- Large static arrays are sized with loose upper bounds (e.g., 1000x1000, 31^3, or hard-coded MASK) and fully cleared each test, while actual constraints are much smaller.
- Heavy floating-point loops approximate a clear mathematical pattern (geometric series, binomial probabilities, expected attempts) that suggests a closed-form or precomputable expression.
- Graph or DP state uses unnecessarily wide or complex payloads (nested pairs, chars misused for indices, redundant dimensions like prev that do not affect transitions).
- Geometry-heavy code spends most time in generic primitives (cross, ccw, std::vector segments, complex arithmetic) although the specific task is low-dimensional or structured (e.g., piecewise-linear in x).
- Bitmask DP or inclusion–exclusion enumerations use long long, repeated gcd/lcm, or extra sorts inside 2^m loops where m ≤ 20.
- Per-test arrays are zero-initialized with = {0} or cleared via double nested loops even when only the first n or m entries are used.

## Steps
1. Tighten scalar numeric types: Replace long double with double when EPS and constraints do not require extra precision.
2. Tighten scalar numeric types: Use int instead of long long for counts, indices, and small values if constraints guarantee they fit.
3. Tighten scalar numeric types: Ensure graph node indices, bitmasks, and small speeds are stored as int, not double or char.
4. Simplify floating-point math and geometry: Switch std::complex<long double> to std::complex<double> or a simple POD struct { double x, y; } for points.
5. Simplify floating-point math and geometry: Remove generic 2D geometry layers when the problem is effectively 1D (e.g., piecewise-linear along x) and replace with direct interpolation and closed-form formulas.
6. Simplify floating-point math and geometry: Fix geometry helpers to use correct APIs (e.g., (a * conj(b)).real()).
7. Right-size and localize memory: Replace large global arrays (e.g., timed[101][1500], a[999][999], vector map[31][31][31]) with local structures sized from input constraints (n, m, h, w, S_MAX).
8. Right-size and localize memory: Use exact bitmask dimensions like dist[m][1<<n] instead of fixed MASK-based ranges.

## Complexity
- Time: Typically preserves asymptotic complexity (e.g., O(n), O(n log n), O(2^m m), O(h * w^2)), but reduces constant factors substantially. In some cases, also reduces exponents or factors, e.g., O(n^3 * S_MAX) → O((n^2 + m) * S_MAX), O(m^3) →
- Space: (pattern dependent)

## Pitfalls
- Blindly narrowing types and causing overflows or precision loss because constraints were misread or borderline (e.g., assuming sums fit into 32-bit when they do not).
- Switching from long double to double in truly tight-precision geometry without re-evaluating EPS or problem-required error bounds.
- Reducing array bounds to match typical but not absolute constraints, leading to out-of-bounds writes on worst-case tests.
- Over-aggressive integerization of probability or time formulas where intermediate products exceed 64-bit limits, or where integer arithmetic breaks subtle ordering or rounding assumptions.
- Removing a dimension like prev or an index from DP/graph state because it looks redundant, while it actually encodes a necessary constraint (e.g., forbidden backtracking).
- Refactoring to closed form without re-deriving the math carefully, resulting in off-by-one factors (missing attempts, wrong power-of-two factor, or sign errors).
- Assuming any std::complex<double> replacement with a manual struct will be faster even when the main cost is algorithmic (e.g., still O(n^2) with large n).
- Ignoring the cost of divisions: moving them out of inner loops is good, but replacing them with multiplications by precomputed reciprocals in double may reintroduce precision issues if not carefully bounded.

## When not to use
- When the current solution is already clearly within time and memory limits and optimization effort would add complexity without practical benefit.
- When problem constraints truly require extended precision (e.g., long double) or wide integers, such as exact arithmetic or very large sums/products beyond 64-bit ranges.
- When you are uncertain about worst-case bounds on n, m, coordinates, or cumulative sums; premature type narrowing can introduce subtle bugs on edge cases.
- When algorithmic complexity is the dominant bottleneck (e.g., O(n^2) with n up to 2e5): in these cases, constant-factor tuning cannot compensate for a fundamentally too-slow algorithm.
- When generic geometry robustness (robust predicates, degeneracy handling) is essential; replacing it with problem-specific shortcuts may break corner cases unless thoroughly reasoned and tested.
- When a derivation of a closed form or precomputation is nontrivial and time is limited; a clear, slightly slower solution may be preferable to a fragile, hard-to-verify formula.

## Minimal example
Before:
```cpp
// O022 focus: type
int best = 0;
for (int mask = 0; mask < (1 << n); ++mask)
  best = max(best, score(mask));
```
After:
```cpp
// optimized for type
int odd = 0;
for (int x : a) odd += x & 1;
int best = closed_form_from_counts((int)a.size(), odd);
// replace subset scan with parity/count reasoning
```
