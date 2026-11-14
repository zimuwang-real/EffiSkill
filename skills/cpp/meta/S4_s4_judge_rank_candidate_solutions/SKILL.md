---
skill_id: S4
type: meta
language: cpp
name: S4 Judge Rank Candidate Solutions
description: A reusable meta-skill for ranking multiple candidate competitive-programming solutions (or refactors) by balancing
  performance upside, correctness risk, and strength of supporting evidence.
---

## S4 - S4-Judge-Rank-Candidate-Solutions

## Inputs
- problem_spec: concise statement of the problem, constraints, and required I/O behavior
- candidates: list of candidate solution designs or code variants
- complexity_estimates: for each candidate, estimated time/space complexity and dominant constants
- risk_annotations: for each candidate, identified correctness risks (edge cases, invariants that are easy to break, numerical issues, etc.)
- evidence_package: for each candidate, available evidence such as prior patterns, known accepted solutions, stress-test results, formal reasoning, or analogies
- resource_limits: practical limits such as time to implement, test budget, and language/runtime constraints
- priority_weights: optional relative importance of performance vs. correctness vs. simplicity (e.g., {performance: 0.4, correctness: 0.4, simplicity: 0.2})

## Procedure
- 1) Normalize context
- - Read problem_spec and identify: (a) main operation pattern (e.g., per-query, per-test linear/near-linear work), (b) maximum input sizes, (c) tolerance for near-constant factors (tight vs. loose constraints).
- - Note resource_limits and priority_weights; if missing, default to correctness >= performance > simplicity.
- 2) Extract candidate summaries
- - For each candidate in candidates:
- - Summarize its core algorithmic idea in 1–2 sentences (e.g., DSU on edges, offline sort + sweep, DP with state compression).
- - Record complexity_estimates, separating asymptotics (e.g., O(n log n)) from obvious constant-factor properties (e.g., heavy recursion, many small allocations, complex branching).
- - List the main data structures and implementation patterns (e.g., recursion depth, custom I/O, static arrays vs. dynamic containers).
- 3) Evaluate performance upside
- - For each candidate:
- - Compare its asymptotic complexity against the problem's worst-case input sizes and known feasible thresholds (e.g., O(n^2) vs. n ≈ 2e5 is likely infeasible).
- - Assess constant-factor implications: I/O strategy, memory layout, cache-friendliness, branch complexity, recursion, and extra passes.
- - Rate performance on a coarse ordinal scale (e.g., 1–5) combining asymptotic suitability and expected constant factors.
- - Note special performance advantages: linear-time transformations, offline sorting, prefix sums, bitset tricks, array-based DSU, etc.
- 4) Evaluate correctness risk
- - For each candidate:
- - Identify fragile assumptions: hidden invariants, reliance on tricky index arithmetic, deep recursion, non-trivial lazy propagation, or subtle math/number-theory invariants.
- - Check how sensitive the algorithm is to off-by-one errors, overflow, precision issues, or boundary cases (empty sets, minimum/maximum constraint values).
- - Evaluate the complexity of state transitions (e.g., DP recurrences, merging rules): the more complex and less locally-checkable, the higher the risk.
- - Consider implementation burden: long, intertwined code paths and custom memory management increase risk.
- - Rate correctness risk on an ordinal scale (e.g., 1–5 where 1 is low risk, 5 is high risk).
- 5) Assess evidence strength
- - For each candidate:
- - Check whether the algorithm matches well-known, previously successful patterns for similar constraint regimes (e.g., DSU for connectivity, segment tree for range updates, prefix sums for range sums).
- - Inspect available test results: coverage of edge cases, randomized stress tests, adversarial scenarios, and large inputs near limits.
- - Consider how thoroughly invariants and correctness arguments are articulated: explicit proofs and invariant checks increase evidence strength.
- - Look for prior issues: known pitfalls, historical bugs, or fixes that signal residual fragility.
- - Rate evidence strength on an ordinal scale (e.g., 1–5 where 1 is weak, 5 is strong).
- 6) Integrate with resource and priority constraints
- - Map performance, correctness risk, and evidence strength to a unified score for each candidate:
- - Define a reliability score as a function of correctness risk and evidence (e.g., reliability ≈ evidence_strength − risk_level, normalized).
- - Combine performance score and reliability using priority_weights.
- - Optionally adjust for implementation cost: if two candidates are close but one is substantially simpler to implement and debug, boost its score.
- 7) Rank candidates
- - Sort candidates by descending combined score.
- - Break ties by applying the following preference order:
- - Higher reliability (lower risk, higher evidence).
- - For comparable reliability, better performance (asymptotics then constants).
- - For near-equal above, lower implementation complexity and clearer reasoning.
- 8) Sanity-check top choices
- - For the top 1–3 candidates:
- - Re-check viability under the strictest plausible input and resource scenarios (max constraints, tight time limits).
- - Ensure there is at least a basic test plan to validate core invariants and edge cases within the available time.
- - Verify that required data structures and primitives are available and practical in the target language.
- 9) Produce final ranking and rationale
- - Output an ordered list of candidates with:
- - Their performance rating and justification (asymptotic and constant-factor reasoning).
- - Their correctness risk rating and main risk factors.
- - Their evidence strength rating and key supporting evidence.
- - A short statement explaining why the top-ranked candidate is preferred under the current priorities and constraints.

## Decision Rules
- If a candidate's asymptotic complexity is clearly incompatible with worst-case constraints, rank it below any candidate with plausible asymptotics, regardless of small constant-factor advantages.
- If two candidates differ substantially in correctness risk and evidence strength, prefer the more reliable one unless performance constraints are extremely tight and the slower option is clearly infeasible.
- If a candidate has theoretical performance advantage but lacks evidence (no tests, unclear invariants) and exhibits high implementation complexity, treat its effective reliability as low and penalize heavily.
- If multiple candidates share the same asymptotic complexity, differentiate mainly on constant factors that align with the problem pattern (e.g., array-based vs. pointer-heavy structures for large linear scans).
- If problem constraints are loose (e.g., small n or low total operations), prioritize reliability and simplicity over peak performance; demote high-risk micro-optimized designs.
- If available time or testing capacity is limited, penalize candidates that require intricate implementations or sophisticated invariants that are difficult to verify under time pressure.
- If evidence includes extensive stress testing or the candidate mirrors a well-established idiom for the same pattern, upgrade evidence strength and allow a small performance or complexity deficit.
- If priority_weights emphasize performance (e.g., strict time limits, historically tight judge), allow a moderately higher correctness risk only when backed by at least moderate evidence strength and a clear test plan.
- If a candidate depends on language features or libraries that are borderline for resource_limits (e.g., recursion depth, memory use, I/O performance), treat this as both a performance and correctness risk.
- If no candidate scores clearly higher on both performance and reliability, select the simplest among the near-ties and note the residual uncertainty.

## Failure Modes
- Overvaluing raw asymptotic complexity and ignoring very large constant factors or poor memory layout that make the "faster" algorithm slower in practice.
- Undervaluing correctness risk by assuming that complex invariants will be implemented flawlessly without sufficient time or tests.
- Treating absence of observed bugs or tests as strong evidence of correctness, instead of recognizing it as weak evidence.
- Anchoring on a familiar pattern even when problem constraints or structure make that pattern ill-suited (e.g., heavy data structures for small inputs).
- Ignoring resource_limits and choosing a theoretically good but practically unimplementable solution under the given time or environment.
- Failing to reassess candidates when updated information appears (e.g., discovering tighter constraints, new edge cases, or runtime behavior).
- Collapsing performance and reliability into a single intuition-based judgment without explicitly rating and comparing each dimension.
- Overfitting to a particular historical example of the pattern, incorrectly assuming identical behavior in a slightly different setting.
- Neglecting language/runtime-specific considerations (e.g., recursion limits, integer size, I/O costs) that materially change performance or correctness risk.
- Producing a ranking without a clear rationale, making it hard to defend or revise the choice if the top candidate later underperforms.

## Output
- Return an ordered list of candidates from best to worst according to the integrated criteria (performance, correctness risk, evidence strength), not just a single chosen solution.
- For each candidate, include numeric or ordinal ratings for performance, correctness risk, and evidence strength, and the combined score used for ranking.
- Provide a brief textual justification (1–3 sentences) per candidate explaining the key reasons for its position in the ranking.
- Explicitly state the main assumptions, such as priority_weights and any simplifying judgments about constant factors or implementation difficulty.
- Highlight the top-ranked candidate with a concise explanation of why it is preferable under the current constraints and priorities.
- If no candidate clearly satisfies both performance and reliability requirements, flag this explicitly and note which dimension is unsatisfactory.
- Ensure that the ranking and rationale remain abstract and reusable: do not depend on any particular problem instance or benchmark details.
