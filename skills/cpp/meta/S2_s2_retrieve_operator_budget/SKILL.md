---
skill_id: S2
type: meta
language: cpp
name: S2 Retrieve Operator Budget
description: Meta-skill that, given task context and an operator registry, selects a small, dynamically sized subset of operator
  skills most likely to improve a competitive-programming style solution (algorithmic and constant-factor optimization). It
  uses problem features, registry metadata, and global trace statistics to pick and order operators while respecting a budget.
---

## S2 - S2-Retrieve-Operator-Budget

## Inputs
- task_brief: concise natural-language or structured description of the problem and current solution status (e.g., timeouts, memory issues, algorithm class, suspected bottlenecks).
- solution_features: extracted or inferred properties of the current or candidate solution (e.g., data structures used, asymptotic complexity, input size ranges, use of recursion, I/O style, language).
- performance_symptoms: known issues or constraints (e.g., TLE/near-TLE, MLE, stack overflow, strict time limit, memory cap, need for implementation-simplification only).
- operator_registry: list/dictionary of operator skills, each with at least {skill_id, family, name, description, tags, triggers}.
- global_trace_stats: aggregated usage and outcome statistics over historical traces (e.g., per-family counts, tag frequencies, typical bottlenecks, complexity deltas).
- max_budget: optional upper bound on number of operators to retrieve in this invocation (integer; may be absent or large).

## Procedure
- 1. Normalize context
- 1.1. Distill task_brief into a short internal summary: problem type (graph/DP/array/math/etc.), main objective (path, counting, combinatorial value, simulation, search), and constraints scale (n, m, q orders of magnitude).
- 1.2. From solution_features, extract clear signals: primary data structures (arrays, sets/maps, priority queues, segment trees, DSU, recursion depth), core algorithm class (brute-force, greedy, DP, search, BFS/DFS, shortest paths, combinatorics), and rough complexity.
- 1.3. From performance_symptoms, classify runtime vs memory vs implementation-pressure vs unknown. Note whether asymptotics already look near-optimal (e.g., O(n log n) for sorting-based solutions, linear-time BFS/DFS, standard shortest-path algorithms) and whether issues are likely constant-factor.
- 1.4. Translate the above into a compact internal feature set, including derived flags such as: large_input, heavy_io, deep_recursion, container_in_hot_path, large_static_buffers, grid_based, state_space_explosion, heavy_precomputation, combinatorics_mod, etc.
- 2. Generate context tags and triggers
- 2.1. Map internal features and performance_symptoms into a bag of contextual tags (e.g., 'graph', 'tree', 'grid', 'dynamic_programming', 'bitmask_dp', 'fast-io-needed', 'constant-factor', 'memory-tight', 'static-intervals', 'dsu', 'shortest_path', 'simulation', 'prefix_sums', 'sorting-heavy').
- 2.2. For each operator in operator_registry, define a lightweight match score function over its tags and triggers against the contextual tags and inferred bottlenecks.
- 2.3. Normalize matches to a consistent internal representation: e.g., match_score in [0, 1], with contributions from tag overlap, trigger phrase alignment, and family alignment with problem type.
- 3. Establish operator family priors using global_trace_stats
- 3.1. From global_trace_stats, compute per-family utility priors: approximate usefulness or impact measures (e.g., relative frequency in past traces, association with significant complexity or constant-factor improvements, match to dominant bottlenecks).
- 3.2. For each operator family, derive a prior_weight that increases with historical success and alignment with currently observed bottleneck types (e.g., if global bottlenecks frequently include I/O and the task has large_input + heavy_io symptoms, boost families with io-optimization and constant_factor tags).
- 3.3. For each individual operator, compute a family_prior_score based on its family’s prior_weight adjusted slightly by its own tag frequencies in successful traces (if available).
- 4. Score each operator
- 4.1. For each operator O in operator_registry, compute:
- relevance_score(O) = f(match_score(O), family_prior_score(O), bottleneck_alignment(O))
- where:
- - match_score(O) captures how well O’s tags/triggers fit the current context tags and inferred bottlenecks.
- - family_prior_score(O) encodes historical utility of O’s family for similar tasks.
- - bottleneck_alignment(O) is an extra boost when O’s triggers explicitly mention the current core symptoms (e.g., 'Large input/output volume' when heavy_io is true).
- 4.2. Optionally penalize very generic operators or those that apply to almost any task if more specific operators are available with similar scores.
- 4.3. Optionally penalize operators whose scope conflicts with the user’s stated constraints (e.g., avoid heavy structural rewrites when user wants implementation-only tweaks, or avoid memory-heavy refactors when memory-tight is flagged).
- 5. Determine dynamic operator budget
- 5.1. Set a soft base budget B_base depending on task complexity and symptom severity:
- - Simple / localized issue (e.g., only I/O bottleneck clearly identified): B_base small (≈ 1–2).
- - Mixed or uncertain issues in a single paradigm (e.g., DP with suspected state blow-up): B_base moderate (≈ 2–4).
- - Complex or multi-bottleneck tasks (e.g., large graphs plus heavy I/O plus memory considerations): B_base larger (≈ 3–6).
- 5.2. If max_budget is provided, clamp B_base to B = min(B_base, max_budget). If max_budget is missing, set a reasonable upper bound (e.g., B ≤ 6) and let B = B_base.
- 5.3. Optionally reduce B when multiple top-ranked operators are highly overlapping (same family, similar tags) to avoid redundancy. Optionally increase B slightly when top scores are spread across distinct families with complementary focus (e.g., one for I/O, one for algorithmic refactor, one for memory layout).
- 6. Select candidate operators
- 6.1. Sort all operators by relevance_score in descending order.
- 6.2. Traverse the sorted list and construct the retrieval set greedily:
- - Always include the highest-scoring operator as the first candidate.
- - For each next operator, only include it if it adds clear coverage: different primary family or substantially different trigger/tag focus than already selected operators.
- - Continue until you reach budget B or exhaust operators with relevance_score above a minimal threshold.
- 6.3. If, before reaching B, you run out of operators exceeding the threshold, stop early. Do not fill the budget with low-confidence operators simply to reach B.
- 7. Order and annotate the final set
- 7.1. Order selected operators primarily by relevance_score, secondarily by diversity of focus (e.g., mix algorithmic and constant-factor operators so that early operators are the most likely to yield large improvements).
- 7.2. For each selected operator, attach a brief internal rationale statement derived from its strongest matching triggers (e.g., 'matches: large_input, heavy_io; family: constant_factor; frequent success for I/O bottlenecks').
- 7.3. Optionally label each operator with a suggested priority tier (e.g., core, secondary, optional) based on its relative score and coverage redundancy.
- 8. Produce retrieval result
- 8.1. Package the selected operators, their ordering, and rationale into the output structure, including the effective budget used (size of retrieval set) and any notable gaps (e.g., 'no strong operator found for memory-specific optimization').
- 8.2. Ensure outputs are abstract and not tied to any specific benchmark or prior instance; only the operator metadata, scores, and rationales should be exposed.

## Decision Rules
- Prioritize operators whose triggers explicitly mention the current dominant bottleneck class (e.g., I/O, algorithmic complexity, memory layout, data-structure overhead) over those that only match by high-level family.
- If the current algorithm is already asymptotically optimal for the problem type and performance_symptoms indicate near-TLE with large input sizes, prefer constant-factor and implementation-focused operators (fast I/O, flat arrays, container simplification) over algorithm-changing operators.
- If the inferred complexity clearly exceeds what constraints allow (e.g., O(n^2) with n ≈ 1e5), prioritize algorithmic refactor operators (prefix-sum refactors, DSU, compressed state DP, search-space pruning) over constant-factor tweaks.
- When multiple operators from the same family have similar relevance_score, prefer the one with more specific triggers that closely match the context and symptoms.
- When the top few operators are highly similar in scope, merge or reduce them by choosing the single best representative and freeing budget for a different family addressing a different plausible bottleneck.
- Use a minimum relevance threshold: if an operator’s score is very low or based only on generic tags (e.g., 'optimization') with no symptom alignment, exclude it even if budget remains.
- When uncertainty about the bottleneck is high (e.g., limited context or ambiguous symptoms), choose a small but diverse set: one high-priority constant-factor operator, one algorithmic operator matching the dominant structural pattern (graph, DP, array), and optionally one memory-focused operator if large structures are involved.
- If performance_symptoms explicitly restrict interventions (e.g., 'cannot change algorithmic idea, only micro-optimizations'), filter out operators whose main impact is algorithmic refactoring.
- If global_trace_stats indicate a certain family almost never helps for tasks of this type or bottleneck, downweight or exclude that family unless match_score is extremely high.
- Ensure that at least one retrieved operator is clearly actionable on the current code style and language; if a high-scoring operator assumes structures or languages not present, either omit it or lower its rank.

## Failure Modes
- Over-selection: returning too many operators, causing dilution of focus and making it unclear which optimization direction to pursue first.
- Under-selection: being overly conservative with thresholds and returning too few or no operators, despite clear bottleneck patterns that match registry triggers.
- Redundancy: retrieving several near-duplicate operators from the same family with overlapping triggers, wasting budget and crowding out more diverse options.
- Misclassification of bottlenecks: misreading performance_symptoms or solution_features so that algorithmic refactor operators are recommended where only I/O is at fault, or vice versa.
- Overfitting to historical priors: relying too heavily on global_trace_stats and underweighting clear local evidence, leading to selection of historically popular operators that are not actually well matched to the present task.
- Ignoring constraints: recommending memory-heavy or structurally invasive refactors when explicit constraints restrict memory usage or algorithmic changes.
- Language or paradigm mismatch: selecting operators whose techniques presuppose particular language features or data-structure idioms that are absent in the current solution context.
- Low-coverage outputs: selecting operators that all target the same suspected bottleneck while leaving other plausible bottlenecks unaddressed, especially when context is ambiguous.
- Ambiguous rationales: failing to attach clear internal rationales, making it hard to understand why each operator was retrieved and whether it is worth applying.

## Output
- Return a structure that includes:
- 1) selected_operators: an ordered list of entries, each at least {skill_id, name, family, tags, rationale, relevance_score}.
- 2) effective_budget: the number of operators actually selected (integer ≤ max_budget if provided).
- 3) coverage_notes: brief statements summarizing which bottleneck categories and problem aspects are covered by the selection (e.g., 'I/O and constant-factor', 'algorithmic DP refactor', 'memory layout').
- 4) gaps: optional notes on suspected but uncovered areas where no strong operator match was found.
- Guarantees:
- - The list is sorted from most to least promising according to relevance_score and decision_rules.
- - The selection size respects the dynamic budget logic and any given max_budget.
- - No operator is included purely because of historical popularity; each has at least one concrete tag/trigger match to the current context.
- - Operators are abstract and reusable; no item is specialized to any specific past problem instance or benchmark.
- - The retrieval result is suitable as input to downstream planning/meta-skills that will decide how and in what order to apply the selected operators.
