---
skill_id: S3
type: meta
language: cpp
name: S3.Strategize
description: 'A reusable meta-skill for constructing executable optimization strategies: selecting algorithms, data structures,
  and implementation tactics; sequencing them into a coherent plan; and adapting the plan under constraints for broad competitive-programming
  style tasks.'
---

## S3 - S3.Strategize

## Inputs
- problem_spec: textual statement and constraints of the task
- known_skills: available algorithmic and implementation skills (e.g., graph traversal, DP patterns, greedy templates, I/O optimization, data-structure refactors)
- constraints: explicit limits on n, m, time, memory, and output format
- environment: language, libraries, judge characteristics, and typical bottlenecks
- quality_targets: priorities such as performance, simplicity, robustness, or ease-of-implementation
- partial_ideas: any initial approaches, heuristics, or observed patterns

## Procedure
- 1) Normalize_requirements: - Extract input sizes, ranges, and worst-case counts for each dimension. - Classify operation types: queries/updates, offline vs online, one-shot vs multiple test cases. - Identify required output: single value, multiple values per query, construction, or yes/no feasibility. - Record strictness: exact optimal solution vs approximate vs any valid construction.
- 2) Abstract_problem_structure: - Map entities to standard domains: array, sequence, graph, tree, grid, numeric range, combinatorial object. - Determine main operations: connectivity, shortest/longest path, counting, ordering, matching, partitioning, dynamic updates. - Infer constraints on operations (e.g., monotonicity, additivity, locality, independence).
- 3) Derive_complexity_budget: - Translate time limit and environment into safe operation counts (e.g., ~1e8 basic ops, ~2e6 log n operations). - From constraints, estimate maximum viable complexities: O(1), O(log n), O(n), O(n log n), O(n^2), etc. - Record budgets separately for preprocessing, per-query work, and per-test-case overhead.
- 4) Generate_candidate_paradigms: - Enumerate applicable high-level paradigms: brute-force pruning, greedy, dynamic programming, graph algorithms, sweep-line, divide-and-conquer, binary search on answer, offline processing, segment/bit Fenwick trees, disjoint set union, combinatorics, number theory. - For each paradigm, describe its typical data requirements and complexity profile. - Discard paradigms whose baseline complexity clearly exceeds budget.
- 5) Match_substructures_to_skills: - Decompose the problem into subproblems: preprocessing, core computation, per-query handling, result reconstruction. - For each subproblem, list compatible known_skills (e.g., DSU for components, Dijkstra for weighted shortest paths, prefix sums for range sums, bitsets for dense boolean DP). - Map each subproblem to 1–2 primary candidate skills plus possible fallbacks.
- 6) Construct_strategy_variants: - Assemble 2–3 end-to-end strategy variants combining chosen skills. - For each variant, specify: - Data structures and their sizes. - Asymptotic complexity of each phase and dominant term. - Expected constant factors (e.g., heavy log factors, cache-friendly scans, recursion depth). - Implementation difficulty and bug risk. - Ensure at least one variant favors simplicity over maximum speed.
- 7) Evaluate_and_select_primary_plan: - Score each variant against complexity budget, implementation effort, and quality_targets. - Prefer variants that are asymptotically safe and structurally simple; only choose complex structures (e.g., segment trees, heavy-light decomposition) when simpler options fail constraints. - Select a primary plan and one backup plan with different dominant bottlenecks (e.g., CPU vs memory vs I/O).
- 8) Detail_execution_steps: - For the primary plan, write a linear sequence of implementation steps: - Input parsing model. - Core preprocessing (building graphs, sorting, precomputing prefix sums, DP tables, etc.). - Main loop structure (per-element, per-query, or events) and transitions. - Updates to data structures and invariants. - Output assembly and postprocessing. - Annotate each step with needed sub-skills and expected complexity.
- 9) Integrate_optimizations_consciously: - Identify likely bottlenecks (I/O, heavy inner loops, memory layout, recursion depth, branching). - Attach specific optimization skills to those points: fast I/O, contiguous arrays, avoiding repeated initialization, removing unnecessary allocations, flattening recursion. - Ensure optimizations do not change logical behavior; keep them orthogonal to correctness logic.
- 10) Risk_analysis_and_instrumentation: - Enumerate potential correctness risks: off-by-one, overflow, corner cases (empty, all equal, maximum values), disconnected components, degenerate graphs. - Enumerate performance risks: worst-case graph density, adversarial input order, many queries, large coordinate ranges. - Plan minimal instrumentation or sanity checks (assertions, early pruning, small-test verification) compatible with constraints.
- 11) Define_switching_conditions: - Specify conditions under which to abandon or modify the primary plan during solving: - If complexity analysis reveals overlooked quadratic behavior. - If implementation becomes tangled or error-prone. - If memory usage exceeds available limits. - Map each condition to a predefined backup strategy or simplification.
- 12) Finalize_strategy_contract: - Summarize the chosen strategy as a concise contract: - Inputs consumed and their assumed bounds. - Data structures and invariants maintained. - Complexity guarantees per phase. - Expected behavior on edge cases. - Use this contract as the reference while implementing and debugging.

## Decision Rules
- Prefer_linear_or_nlogn: If n or total operations exceed ~1e5–1e6, reject any plan with Θ(n^2) or worse unless the state space is compressed or heavily pruned.
- Exploit_structure_first: Before choosing heavy generic structures (segment trees, flow, 2-SAT), check for special structure: monotonicity, prefix/suffix decomposability, small alphabet, bounded coordinate domain, tree vs general graph.
- Favor_simpler_skill_if_costs_similar: Between two variants with comparable asymptotic complexity, choose the one with fewer moving parts and simpler invariants.
- Match_DS_to_operation_pattern: Use - arrays/prefix sums for static range aggregates, - Fenwick/segment trees for dynamic point or range updates, - DSU for incremental connectivity without deletions, - BFS/DFS for unweighted shortest paths and component labeling, - Dijkstra/0-1 BFS for weighted shortest paths. Avoid overpowered structures when simpler ones suffice.
- Respect_memory_ceiling: If cumulative arrays or tables approach memory limits, choose streaming or compressed representations, iterative DP, or recomputation trade-offs over storing all states.
- Avoid_per_query_heavy_rebuilds: Do not rebuild large graphs, trees, or DP tables inside per-query loops; instead, process offline, precompute, or use persistent or incremental structures.
- Guard_against_recursion_depth: For graphs or trees with n up to ~2e5, prefer iterative traversals or explicit stacks to avoid stack overflow and recursion overhead.
- I/O_as_bottleneck_indicator: If computation per input item is trivial and n is large, prioritize fast I/O and cache-friendly scans over micro-optimizing arithmetic.
- Binary_search_on_answer_when_monotone: If feasibility of an answer parameter is monotone, isolate a fast check() and binary-search the answer instead of scanning all candidate values.
- Backoff_from_overfit: If a strategy relies on fine-tuned behavior or many case distinctions, prefer a more robust generalized method even at a small complexity cost increase.

## Failure Modes
- Underestimated_complexity: The chosen plan hides an extra factor (e.g., nested scans, indirect recomputation), turning nominal O(n log n) into practical near-quadratic.
- Overengineered_solution: Use of unnecessarily complex structures (e.g., segment tree with lazy propagation, heavy decomposition, flow) where a simple linear or greedy method suffices, increasing bug risk and coding time.
- Memory_overflow: Aggregating multiple large arrays, DP tables, or adjacency structures without accounting for combined size, leading to memory limit exceeded.
- Missed_special_case_structure: Treating a constrained instance (e.g., tree, small alphabet, small coordinate range) as fully general, missing much simpler and faster strategies.
- Incorrect_bottleneck_identification: Optimizing I/O or micro-operations when the true bottleneck is an inappropriate algorithmic paradigm.
- Rigid_strategy: Failing to define fallback options; persisting with a failing or overly slow plan instead of switching to a simpler or more appropriate approach.
- Edge_case_blindness: Planning for average behavior but not explicitly accounting for empty, minimal, maximal, or degenerate inputs, leading to incorrect answers or crashes.
- Inconsistent_invariants: Combining multiple skills without clearly defined shared invariants, causing subtle logical conflicts between sub-components.
- Overlooked_constant_factors: Choosing an asymptotically similar but practically slower method (e.g., high-overhead trees over arrays) in a tight time limit scenario.
- I/O_and_layout_mismatch: Strategy assumes cheap random access and dense memory, but the chosen data representation is fragmented, causing unexpected overhead.

## Output
- Produces_one_primary_plan: A clearly specified primary strategy describing algorithms, data structures, invariants, and their sequencing from input to output.
- Includes_at_least_one_backup_plan: An alternative strategy with different dominant bottlenecks or complexity trade-offs, ready to be used if the primary plan proves unsuitable.
- Respects_complexity_budgets: The primary plan is justified to run within time and memory limits under worst-case input sizes, with explicit complexity reasoning.
- Specifies_bottlenecks_and_optimizations: Identifies expected hot spots and associates them with concrete optimization tactics without altering correctness.
- Handles_edge_cases_explicitly: Notes how the strategy behaves on extreme inputs and special structures, avoiding undefined or fragile behavior.
- Modular_composability: The plan is decomposed into substeps that can be mapped to distinct skills, enabling reuse and reordering where appropriate.
- Implementation_ready: The strategy description is detailed enough that an implementation can be derived as a straightforward translation without redesign.
- Adaptable_under_feedback: Contains explicit criteria for when to adjust or replace components of the strategy in response to observed or anticipated failures.
