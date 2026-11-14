---
skill_id: O007
type: operator
language: cpp
family: state_compression
name: Parity And Streaming Refactor
description: 'Refactor solutions that use explicit simulations, large auxiliary arrays, or heavy per-test initialization into
  parity/invariant-based decisions and single-pass streaming algorithms with tight memory and I/O. Applicable when the final
  result depends only on aggregate properties (parity, min/max, counts, simple predicates) rather than the full simulated
  state evolution. This operator systematically: (1) replaces'
tags:
- optimization
- algorithmic-refactor
- parity
- simulation-to-formula
- single-pass
- streaming
- frequency-counting
- binary-search-check-optimization
- memory-traffic-reduction
- io-optimization
triggers:
- Game or process is simulated step-by-step with a mutable array (e.g., marking deletions or states) and repeated full scans,
  but the final decision is only "which player wins" or depends on the parity of an event count.
- Presence of while(1) or do-while loops that repeatedly sweep over an entire string/array until no more changes occur, especially
  combined with compaction passes or marker-based deletions.
- A separate check() used inside a binary search that performs O(n^2) or heavy O(n) work per mid by rewriting segments or
  auxiliary arrays, where the predicate ultimately depends on comparisons to the mid or simple
- Multiple full passes over the same array/string (for zero detection, product computation, prefix/suffix stats, frequency
  counting) when the final answer is a simple aggregate (sum/product/min/max/parity/count) that
- Large fixed-size global/local arrays whose size reflects an upper bound (e.g., 1e5–1e6) but where only a small logical subrange
  or a tiny alphabet (like digits 0–9 or letters) is actually used.
- Per-testcase memset over big arrays (frequency, visited, boolean markers) when the real working set per test is much smaller
  or when globals are already zero-initialized.
- Simulation of cycles or modular processes with an O(k) visited[] that is redundantly memset before single-use in a single
  test.
- Use of helper functions in the innermost per-character loop that do small linear searches over a constant alphabet (e.g.,
  get(c) scanning "ACGT"), rather than direct table lookup.
---

## When to use
- Game or process is simulated step-by-step with a mutable array (e.g., marking deletions or states) and repeated full scans, but the final decision is only "which player wins" or depends on the parity of an event count.
- Presence of while(1) or do-while loops that repeatedly sweep over an entire string/array until no more changes occur, especially combined with compaction passes or marker-based deletions.
- A separate check() used inside a binary search that performs O(n^2) or heavy O(n) work per mid by rewriting segments or auxiliary arrays, where the predicate ultimately depends on comparisons to the mid or simple
- Multiple full passes over the same array/string (for zero detection, product computation, prefix/suffix stats, frequency counting) when the final answer is a simple aggregate (sum/product/min/max/parity/count) that
- Large fixed-size global/local arrays whose size reflects an upper bound (e.g., 1e5–1e6) but where only a small logical subrange or a tiny alphabet (like digits 0–9 or letters) is actually used.
- Per-testcase memset over big arrays (frequency, visited, boolean markers) when the real working set per test is much smaller or when globals are already zero-initialized.
- Simulation of cycles or modular processes with an O(k) visited[] that is redundantly memset before single-use in a single test.
- Use of helper functions in the innermost per-character loop that do small linear searches over a constant alphabet (e.g., get(c) scanning "ACGT"), rather than direct table lookup.

## Steps
1. Classify the computation as invariant- or aggregation-based: Inspect the slow solution to see if it simulates a process (game, deletion, interval updates, digit operations) but the final result is a simple predicate or aggregate
2. Classify the computation as invariant- or aggregation-based: Winner determined by parity of moves or deletions.
3. Classify the computation as invariant- or aggregation-based: Feasibility of a configuration based on min/max, parity, or counts.
4. Classify the computation as invariant- or aggregation-based: Coverage count, degree parity, or simple yes/no conditions.
5. Classify the computation as invariant- or aggregation-based: If the outcome does not depend on the exact sequence of state transitions, but only on invariant properties (endpoints, length parity, counts, comparisons to thresholds), mark the problem as a
6. Derive a closed-form or linear-time invariant-based rule (if a game/simulation is present): Analyze the simulated rules to extract what actually matters
7. Derive a closed-form or linear-time invariant-based rule (if a game/simulation is present): For repeated deletion/simplification processes: determine whether only the parity of deletions or a symmetric property around the center controls the result.
8. Derive a closed-form or linear-time invariant-based rule (if a game/simulation is present): Replace the full simulation with a direct O(1) or O(n) decision based on these invariants, verifying on small examples that it matches the simulation result.

## Complexity
- Time: Typical transformations reduce time from O(n^2) simulations or O(n * log C * n)-style heavy checks to O(n) or O(n log C) with small constants. In many cases the asymptotic remains O(n), but constants drop by eliminating extra passes
- Space: (pattern dependent)

## Pitfalls
- Assuming a single test case when the judge actually provides multiple, based solely on an optimized reference snippet. Removing per-test resets in a multi-test environment can leak state across tests.
- Compressing multi-pass logic into a single streaming pass but changing the order of operations subtly (e.g., updating running minimum before computing profit for the same index), thereby altering semantics.
- Shrinking frequency or flag arrays to small alphabets without confirming that the value domain is truly limited (e.g., replacing freq[1e5] with freq[10] when values can exceed 9). This risks out-of-bounds access.
- Relying on global zero-initialization for arrays that are reused across multiple testcases, while also using loops like while (~scanf()) for multiple runs. Without explicit per-test reset or a timestamping scheme
- Mismanaging binary search bounds or the monotonicity of the check() function after refactoring it to use invariants; an incorrect monotone predicate breaks binary search despite being individually O(n) and fast.
- Replacing difference arrays with scalar countdown coverage without matching exact boundary conditions (e.g., off-by-one in inclusive/exclusive endpoints or last index handled).
- Switching to faster I/O but mixing scanf/printf with cin/cout without disabling sync, causing unexpected slowdowns or subtle issues.
- Simplifying string processing by reading tokens with operator>> and indexing [0] without handling potential empty strings or edge-case lengths (though rare in well-defined contest problems).

## When not to use
- When the problem’s outcome genuinely depends on the full detailed sequence of states (e.g., specific positions after many steps) and cannot be expressed via simple invariants, parity, or aggregate counts.
- When a full state representation or history is required for output (e.g., reconstructing a sequence of moves, printing a modified array/string, or listing all valid numbers), and streaming aggregates would discard
- When the value domain is large and you truly need per-value frequencies with random accesses (e.g., coordinate-compressed indices still large), in which case reducing the frequency array to a tiny alphabet is incorrect.
- For multi-query scenarios where a heavier precomputation (e.g., building and sorting a global list once, using binary search per query) is asymptotically superior to repeatedly running a per-query DFS/greedy that the
- When constraints are small enough that O(n^2) or heavy O(n log C) simulations are clearly acceptable and simpler to implement, and further optimization risks introducing subtle correctness bugs for minimal gain.
- When problem statements demand strict formatting (precision, trailing spaces) or specific I/O behavior that a change of I/O model could inadvertently break. Always respect format guarantees before altering I/O routines.

## Minimal example
Before:
```cpp
// O007 focus: parity
vector<int> ans;
for (int x = 1; x <= MAXV; ++x) {
  bool ok = true;
  for (const auto& grp : groups) if (!binary_search(grp.begin(), grp.end(), x)) ok = false;
  if (ok) ans.push_back(x);
}
```
After:
```cpp
// optimized for parity
vector<int> freq(MAXV + 1, 0);
for (const auto& grp : groups)
  for (int x : grp) ++freq[x];
for (int x = 1; x <= MAXV; ++x)
  if (freq[x] == (int)groups.size()) ans.push_back(x);
```
