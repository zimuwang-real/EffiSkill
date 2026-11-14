---
skill_id: O011
type: operator
language: cpp
family: constant_factor
name: Template Preamble Refactor
description: Refactor or standardize the competitive-programming template/preamble (includes, macros, typedefs, utilities,
  fast I/O, debug helpers) without changing the underlying algorithm. The goal is to reduce compile-time overhead, improve
  code conciseness and reuse, and set up a robust utility layer (modular arithmetic, basic number theory, loops, fast I/O,
  debug gating) while preserving runtime asymptotics of the actual
tags:
- c++
- template
- preamble
- fast-io
- boilerplate
- modint
- number-theory-helpers
- debug-macros
- compile-time-optimization
- competitive-programming
triggers:
- The visible slow and fast solutions are identical in all algorithmic regions; only header/includes, macros, typedefs, and
  utility helpers differ or are being reorganized.
- The code has a very long, explicit list of standard headers (many of them unused or duplicated) and you want to replace
  them with a more compact include strategy (e.g., <bits/stdc++.h> or a minimal curated set).
- The solution frequently uses ad-hoc implementations of gcd, pow, modular inverse, combinatorics, or small geometry/utility
  functions scattered throughout multiple files instead of a centralized, inline utility layer.
- Debug macros or logging helpers (e.g., printing vectors, maps, traces) are present and may be active in performance-critical
  builds, and you want a clean way to gate or remove them in production runs.
- Compile times are noticeably high due to header bloat and template-heavy libraries, even though runtime is acceptable, and
  you want to streamline the build without changing the main algorithm.
- You are building a reusable competitive-programming library and want a consistent, minimal, and fast preamble that can be
  dropped into new solutions without rethinking basic utilities each time.
---

## When to use
- The visible slow and fast solutions are identical in all algorithmic regions; only header/includes, macros, typedefs, and utility helpers differ or are being reorganized.
- The code has a very long, explicit list of standard headers (many of them unused or duplicated) and you want to replace them with a more compact include strategy (e.g., <bits/stdc++.h> or a minimal curated set).
- The solution frequently uses ad-hoc implementations of gcd, pow, modular inverse, combinatorics, or small geometry/utility functions scattered throughout multiple files instead of a centralized, inline utility layer.
- Debug macros or logging helpers (e.g., printing vectors, maps, traces) are present and may be active in performance-critical builds, and you want a clean way to gate or remove them in production runs.
- Compile times are noticeably high due to header bloat and template-heavy libraries, even though runtime is acceptable, and you want to streamline the build without changing the main algorithm.
- You are building a reusable competitive-programming library and want a consistent, minimal, and fast preamble that can be dropped into new solutions without rethinking basic utilities each time.

## Steps
1. Unify and minimize includes: Replace long lists of standard headers with either `#include <bits/stdc++.h>` (for GCC/Clang contest environments) or a small curated set of headers actually needed by your library.
2. Unify and minimize includes: Remove duplicated includes and rarely used heavy headers (regex, locale, iomanip, etc.) unless the library truly depends on them.
3. Unify and minimize includes: Keep any special includes (e.g., `ext/pb_ds` or Boost) clearly separated and conditional if they are not always used.
4. Centralize type aliases and basic macros: Define common aliases (`using ll = long long; using pii = pair<int,int>; using vi = vector<int>;` etc.) in one place.
5. Centralize type aliases and basic macros: Provide concise loop macros and helpers if desired (`REP(i,n)`, `FOR(i,l,r)`, `all(v)`, `sz(v)`), but keep them simple and consistent.
6. Centralize type aliases and basic macros: Avoid fragile macros that change fundamental types (e.g., `#define int long long`); prefer `using` aliases instead to keep types explicit and tooling-friendly.
7. Set up fast I/O once and consistently: For iostreams: configure `ios::sync_with_stdio(false); cin.tie(nullptr);` in a standard `init_io()` function or at the start of `main`.
8. Set up fast I/O once and consistently: Optionally provide a lightweight scanf/printf or custom buffered reader if the library targets extremely tight I/O constraints.

## Complexity
- Time: O(1) per operation for the preamble utilities (type aliases, macros, simple helpers). Overall algorithmic time complexity T(n) of the solution remains unchanged; this operator targets constant-factor and compile-time improvements rather
- Space: O(1) additional space at runtime. Some helpers (e.g., combinatorial precomputation tables) may add O(K) or O(N) space when explicitly included, but those are part of the problem-specific logic rather than the template refactor itself.

## Pitfalls
- Using non-portable constructs like `#include <bits/stdc++.h>` or `typeof` in macros when targeting compilers/platforms that do not support them (e.g., MSVC, some online judges).
- Overusing macros, especially ones that redefine core language tokens or types (like `#define int long long`), which can break third-party code, cause subtle bugs, or confuse debugging and static analysis tools.
- Pulling in too many heavy libraries (Boost, PBDS, multiprecision, regex, etc.) by default in the template when they are rarely used, which can increase compile time and binary size without benefit.
- Leaving debug macros active in production or contest submissions, causing huge slowdowns due to extensive logging to `cerr` or `cout` in tight loops.
- Assuming template refactor alone will fix time-limit issues when the true bottleneck is algorithmic (e.g., O(n^2) where O(n log n) is needed). This operator is about infrastructure and constant factors, not changing
- Accidentally changing numeric behavior while refactoring helpers (e.g., different handling of negatives in modulo, overflow, or precision changes from double to long double) which can introduce subtle wrong answers.
- Exposing too many global macros and `using namespace std;` leading to name clashes and ambiguous overload resolution as the library grows.

## When not to use
- When the performance issue is clearly algorithmic (e.g., known O(n^2) behavior on large inputs) and must be addressed by changing the core algorithm or data structures, not by adjusting templates or includes.
- When targeting platforms or compilers where `#include <bits/stdc++.h>` or GNU extensions are unavailable or discouraged, and portability is a primary requirement.
- When working in a production or long-lived codebase where heavy macro usage, global aliases, and monolithic headers reduce maintainability and code clarity.
- When compile times are already acceptable and further improvements are negligible compared to the development and testing cost of refactoring the common template.
- When a problem requires strict control over dependencies, binary size, or symbol visibility (e.g., embedded or constrained environments), and a generic, all-in-one competitive template would be too heavyweight.

## Minimal example
Before:
```cpp
// O011 focus: template
vector<int> vals;
for (int i = 0; i < n; ++i) vals.push_back(read());
sort(vals.begin(), vals.end());
```
After:
```cpp
// optimized for template
vector<int> vals;
vals.reserve(n);
for (int i = 0; i < n; ++i) vals.push_back(read());
sort(vals.begin(), vals.end());
```
