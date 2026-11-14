---
skill_id: S1
type: meta
language: cpp
name: S1.Diagnose
description: Turn structured performance traces for competitive-programming style solutions into a concise optimization brief
  that identifies dominant bottlenecks and prescribes abstract refactor directions.
---

## S1 - S1.Diagnose

## Inputs
- global_trace_stats: aggregated statistics over many traces (problem tags, bottlenecks, delta types, complexity deltas, counts)
- cluster_patterns: per-pattern summaries (top tags, bottlenecks, complexity deltas, triggers, common optimization steps)
- diverse_examples: a small set of heterogeneous examples with before/after complexity and bottlenecks
- constraints: high-level environment constraints if available (time limits, input size scales, language/runtime assumptions)
- current_solution_profile (optional): known or suspected characteristics of the target solution (uses recursion, heavy STL, naive I/O, etc.)

## Procedure
- 1. Normalize inputs
- 1.1. Verify that global_trace_stats, cluster_patterns, and diverse_examples follow the expected schema; discard malformed entries.
- 1.2. Canonicalize terminology for bottlenecks, delta types, and complexity notation (e.g., map I/O_overhead and io to I/O; algorithmic_structure to algorithmic).
- 1.3. Extract high-level dimensions: problem_tags_universe, bottleneck_universe, delta_type_universe, complexity_delta_universe.
- 2. Establish dominant context
- 2.1. From global_trace_stats.top_problem_tags, identify the most frequent categories (e.g., graph, dynamic_programming, greedy, implementation, etc.).
- 2.2. From global_trace_stats.top_bottlenecks, rank bottleneck types by frequency and weight; record the top 3–5 as primary recurring bottlenecks.
- 2.3. From global_trace_stats.top_delta_type and top_complexity_delta, infer typical optimization styles (constant-factor vs algorithmic redesign) and how often asymptotic complexity actually changes.
- 3. Synthesize bottleneck → lever mapping
- 3.1. For each dominant bottleneck type, scan cluster_patterns where that bottleneck appears; extract recurring triggers and steps.
- 3.2. Abstract each recurring trigger into a pattern descriptor (e.g., 'heavy I/O in linear scans', 'nested scans with re-initialization', 'overly generic data structure in hot path').
- 3.3. Abstract the associated steps into levers (e.g., 'fast I/O + buffered output', 'replace per-iteration memset with bounded clear', 'switch to flat arrays and CSR layout', 'remove unnecessary preprocessing').
- 3.4. For each bottleneck, create a prioritized list of levers ordered by (a) how often they appear in cluster_patterns, and (b) how invasive they are (prefer low-risk changes first).
- 4. Characterize typical complexity movement
- 4.1. Group complexity_delta entries into categories: constant-factor-only (same big-O), modest-asymptotic improvement (e.g., n log n → n), same-asymptotic-with-memory-reduction, and unknown.
- 4.2. Estimate the proportion of traces in each category; record whether the ecosystem is primarily about constant-factor tuning or about full algorithmic redesign.
- 4.3. For each category, associate typical levers: constant-factor (I/O, memory layout, loop micro-structure), asymptotic improvement (better algorithms, specialized data structures, pruning, offline transforms).
- 5. Align with target solution profile
- 5.1. If current_solution_profile is provided, match its descriptors (e.g., 'recursive DFS on large tree', 'uses cin/cout without sync tweaks', 'uses vector<vector<int>> adjacency') to triggers in cluster_patterns.
- 5.2. Produce a list of suspected local bottlenecks in the target solution, annotated with which cluster-style patterns they resemble and what levers were successful there.
- 5.3. If no explicit profile is provided, fall back to generic guidance for the dominant problem_tags and bottlenecks from global_trace_stats.
- 6. Draft bottleneck-focused sections
- 6.1. For each primary bottleneck (in order of global importance, then relevance to current_solution_profile):
- 6.1.1. Provide a one-sentence description of how this bottleneck usually manifests in similar tasks.
- 6.1.2. Summarize the key triggers to look for in code or design (bullet points, pattern-like language).
- 6.1.3. List the recommended levers, grouped into:
- - 'Immediate low-risk tweaks' (e.g., fast I/O configuration, local array usage, loop-structure cleanup).
- - 'Structural refactors' (e.g., change graph representation, replace data structure, switch from recursive to iterative).
- - 'Algorithmic redesign candidates' (e.g., change from naive scan to sweep-line, from generic segment tree to simpler BIT, from simulation to prefix-sums).
- 6.1.4. Where cluster_patterns indicate it, note dependencies between levers (e.g., adjacency restructuring may be prerequisite for DSU optimization).
- 7. Extract key algorithmic themes
- 7.1. From problem_tags and delta_type distributions, derive common algorithmic upgrade paths (e.g., 'brute-force → DP', 'DP with 3D state → compressed 2D state', 'online processing → offline + sort').
- 7.2. For each theme, write a short template transformation, specifying:
- - Input pattern (how the slow design tends to look).
- - Output pattern (what the optimized approach tends to resemble).
- - Complexity shift and typical constraints where the shift matters.
- 7.3. Cross-reference these themes with the primary bottlenecks; only retain themes that directly support the identified bottlenecks.
- 8. Define non-goals and constraints
- 8.1. Based on complexity_delta_universe, state clearly whether the focus should be on constant factors or asymptotic improvements for the target context.
- 8.2. Record typical input size scales and memory budgets implied by the traces (e.g., appearance of n up to ~2e5 suggests attention to O(n log n) vs O(n^2) and I/O).
- 8.3. Note any methods that are systematically underused or absent (e.g., no need for heavy generic segment trees if most improvements come from simpler structures).
- 9. Compose the optimization brief
- 9.1. Start with a short diagnostic summary: typical task families, dominant bottlenecks, and whether constant-factor or algorithmic upgrades dominate.
- 9.2. Add a prioritized bottleneck list, each with:
- - Description of how it usually appears.
- - Signals/triggers to look for in the target solution.
- - Recommended levers, grouped by invasiveness (immediate tweaks, structural refactors, algorithmic redesign).
- 9.3. Add an 'Algorithmic upgrade paths' section with a few high-yield transformation templates relevant to the current context.
- 9.4. Add a 'Constraints & non-goals' section specifying: expected input scales, time/memory targets, and what kinds of heavy infrastructure are likely overkill.
- 9.5. If current_solution_profile is known, highlight the 2–4 most relevant levers as primary next steps; otherwise, present the brief as a generic checklist for similar tasks.
- 10. Sanity-check for overfitting and example leakage
- 10.1. Ensure that the brief speaks in terms of patterns, signals, and levers, not in terms of any specific problem statement or hard-coded data ranges beyond generic scales (e.g., 'up to ~2e5').
- 10.2. Confirm that no single trace or example is implicitly reconstructed; all guidance must be aggregate and abstract.
- 10.3. Remove any identifiers or names that directly reference specific historical instances; retain only generic descriptors.

## Decision Rules
- If I/O-related bottlenecks appear among the top global bottlenecks AND many complexity deltas keep the same big-O, then prioritize constant-factor I/O strategies (fast input, buffered output, avoiding per-item flushing) as first-line levers.
- If algorithmic bottlenecks appear frequently AND there are many deltas with improved asymptotic complexity (e.g., n log n → n or n^2 → n log n), then prioritize algorithm redesign patterns (e.g., offline processing, prefix sums, smarter DP) over micro-optimizations.
- If memory_layout or data_structure bottlenecks are common AND cluster_patterns show steps that replace nested/high-level containers with flat arrays or CSR-like layouts, then recommend data layout simplification before considering more complex structures.
- If recursion_depth or recursion_overhead is common in graph- or tree-heavy traces, prefer iterative traversals or explicit stacks, especially when combined with large input sizes.
- If most improvements in a tag family (e.g., graph, DP, segment_tree, combinatorics) are constant-factor-only, then emphasize local loop, branching, and initialization optimizations for that family rather than encouraging wholesale algorithm swaps.
- If diverse_examples show that an operation has already optimal asymptotic complexity (e.g., single-pass O(n)), treat any heavy auxiliary machinery (e.g., segment trees, complex DSU layering) as suspect and candidates for removal or simplification.
- If a bottleneck is rare globally but central in the current_solution_profile, still include it, but mark its levers as lower-priority unless constraints explicitly emphasize it.
- If constraints indicate tight memory but traces show frequent memory_layout optimizations, promote space-reduction levers (state compression, smaller types, fewer large static arrays) even when time complexity remains unchanged.
- If triggers mention repeated full-array initialization or scans in inner loops, recommend reducing initialization ranges and performing localized updates, even when the overall big-O is unchanged.
- If cluster_patterns consistently pair a bottleneck with a specific lever (e.g., I/O bottleneck with using faster input primitives), treat that lever as canonical for that bottleneck in the brief unless contradicted by constraints.

## Failure Modes
- Overfitting: deriving recommendations that are tailored to a specific historical problem instead of abstract patterns, leading to brittle or irrelevant advice.
- Example leakage: implicitly reconstructing a particular problem or solution (including its constants, naming, or structure) instead of remaining generic.
- Misclassification of bottlenecks: misreading global or cluster statistics and emphasizing a bottleneck that is not actually dominant in the target context.
- Ignoring constraints: recommending heavy algorithmic redesign when time limits or input sizes suggest that simple constant-factor tweaks would suffice, or vice versa.
- Overemphasizing low-yield micro-optimizations: focusing on tiny local changes while ignoring large algorithmic or data-structure issues highlighted by the traces.
- Under-specifying actionable steps: producing a brief that talks about bottlenecks in general terms but fails to map them to concrete, reusable levers.
- Conflicting guidance: proposing incompatible refactor paths (e.g., both removing and heavily relying on a specific data structure) due to not reconciling patterns across clusters.
- Neglecting interaction effects: treating I/O, algorithm, and memory layout as independent when traces show that they compound (e.g., heavy structures amplifying I/O overhead).
- Assuming availability of advanced libraries or language features that may not be present in the target environment, when traces are actually agnostic.
- Excessive verbosity: generating a brief that is too long or detailed for practical use in a contest setting, obscuring the few high-impact next steps.

## Output
- Produce a self-contained optimization brief in abstract, pattern-oriented language, with no references to specific historical problems or identifiers.
- The brief MUST include: (a) a short diagnostic summary, (b) a prioritized list of primary bottlenecks, (c) for each bottleneck, a set of recommended levers grouped by invasiveness, and (d) a constraints & non-goals section.
- All recommendations MUST be phrased as generic patterns or transformations (e.g., 'replace nested dynamic containers with flat arrays in the hot path') and MUST NOT rely on any problem-specific context.
- The brief SHOULD distinguish between constant-factor improvements and asymptotic complexity improvements, indicating which category each major lever falls into.
- The brief SHOULD explicitly connect each recommended lever to the bottleneck(s) it addresses, so that readers can trace rationale from issue to action.
- The brief MUST avoid reconstructing or describing any particular past benchmark problem; it can only discuss families of problems (e.g., 'graph traversal tasks', 'DP with 2D states').
- The brief SHOULD be concise enough for practical use in time-constrained settings, favoring clear bullet points and short sections over lengthy exposition.
- Where uncertainty exists (e.g., missing current_solution_profile), the brief MUST either note assumptions or present guidance as generic checklists rather than definitive steps.
- The brief MUST be consistent with the aggregated evidence provided by global_trace_stats, cluster_patterns, and diverse_examples; ad-hoc speculation is not allowed.
- The brief SHOULD be reusable: it must be possible to apply its patterns and levers to other, similar optimization tasks without modification.
