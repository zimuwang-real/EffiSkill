---
skill_id: O018
type: operator
language: cpp
family: graph
name: Optimize Small Alphabet String Processing
description: Refactor string-heavy solutions—especially over small fixed alphabets (e.g., lowercase letters or DNA bases)—to
  remove redundant passes, dynamic substring creation, heavy ordered containers, and custom hash tables. Replace them with
  linear or near-linear algorithms that operate directly on the original buffers, use compact frequency tables or tries, process
  input in a single pass when possible, and apply
tags:
- strings
- small-alphabet
- frequency-counting
- hashing
- tries
- distinct-count
- kth-substring
- single-pass
- I/O-optimization
- constant-factor-optimization
triggers:
- Code uses std::string::substr, std::string concatenation, or creates many temporary strings inside nested loops.
- All inputs are stored (e.g., global array of strings) even though only aggregate statistics (counts, max/min, distinct count)
  are required.
- Sorting or ordered containers (std::sort on all strings, std::set<string>, std::map<string, int>) are used solely for counting
  or membership tests where ordering is irrelevant.
- A very small fixed alphabet (e.g., 'a'..'z', 'A','C','G','T','T') is present but the code uses general-purpose maps/sets
  or per-letter rescans of whole strings.
- Multiple full passes over the same string or array are performed for simple tasks like counting statuses, finding a pattern,
  or validating character frequencies.
- Custom modulo-based hash tables (head/nex/to arrays) are used for short fixed-alphabet strings where direct addressing or
  std::unordered_set/map would be simpler and faster.
- Nested loops with an unused outer index or repeated substring scans (e.g., substr + find/find_first_of in hot loops) dominate
  runtime.
- Use of cin/cout with default sync, std::endl flushes, or std::string copies on large inputs where profiling or constraints
  indicate an I/O-bound solution.
---

## When to use
- Code uses std::string::substr, std::string concatenation, or creates many temporary strings inside nested loops.
- All inputs are stored (e.g., global array of strings) even though only aggregate statistics (counts, max/min, distinct count) are required.
- Sorting or ordered containers (std::sort on all strings, std::set<string>, std::map<string, int>) are used solely for counting or membership tests where ordering is irrelevant.
- A very small fixed alphabet (e.g., 'a'..'z', 'A','C','G','T','T') is present but the code uses general-purpose maps/sets or per-letter rescans of whole strings.
- Multiple full passes over the same string or array are performed for simple tasks like counting statuses, finding a pattern, or validating character frequencies.
- Custom modulo-based hash tables (head/nex/to arrays) are used for short fixed-alphabet strings where direct addressing or std::unordered_set/map would be simpler and faster.
- Nested loops with an unused outer index or repeated substring scans (e.g., substr + find/find_first_of in hot loops) dominate runtime.
- Use of cin/cout with default sync, std::endl flushes, or std::string copies on large inputs where profiling or constraints indicate an I/O-bound solution.

## Steps
1. Analyze data needs: Check if the alphabet is small and fixed; if so, prefer arrays over maps for character-indexed data.
2. Refactor I/O and storage: If input size is large, enable fast I/O (`ios::sync_with_stdio(false); cin.tie(nullptr);`) or use scanf/printf.
3. Refactor I/O and storage: Replace global arrays of strings with on-the-fly processing using a single reusable buffer (`string s;` or `char buf[]`). Store only what is actually needed (e.g., one map from canonical key to count).
4. Eliminate redundant passes: Combine multiple traversals into a single loop whenever each item is logically independent (e.g., classify by first character, count internal patterns, and update counters in one pass).
5. Avoid dynamic substring creation and repeated scanning: Replace `substr` + comparison with indexed in-place checks on the original string.
6. Avoid dynamic substring creation and repeated scanning: Where possible, implement early exit on first mismatch or first successful match.
7. Exploit small alphabets with frequency tables: Build per-string frequency arrays `int freq[26];` in one pass instead of scanning each string 26 times.

## Complexity
- Time: (pattern dependent)
- Space: (pattern dependent)

## Pitfalls
- Overusing std::string and STL containers in tight inner loops: repeated substr(), concatenation, and dynamic allocations can dominate runtime even when asymptotics look linear.
- Replacing sorting with map-based canonicalization but still using tree-based std::map for small alphabets, ending up with O(L log Σ) instead of simple O(L) flat arrays.
- Switching to direct-address arrays without correctly bounding the encoded key space, potentially causing out-of-bounds writes.
- Using unordered_set/map without reserving capacity when N is large, leading to many rehashes and higher constant factors.
- Removing data storage too aggressively and then discovering that later output or reconstruction actually needs some form of stored structure.
- Simplifying to character counters where ordering or multiplicity relationships still matter, thereby changing the problem semantics.
- Optimizing I/O (e.g., mixing scanf/printf with cin/cout) incorrectly, causing subtle I/O bugs or slower performance due to improper sync settings.
- Eliminating redundant passes but reintroducing them indirectly via repeated map lookups or string comparisons in inner loops.

## When not to use
- When the alphabet is large or unbounded and direct-address tables or fixed-size frequency arrays would be too big (e.g., full Unicode or arbitrary-byte strings without tight length limits).
- When the problem truly requires global ordering over all strings or substrings (e.g., full lexicographic listing or sorting) and you cannot avoid materializing or sorting most of them.
- When K (e.g., k-th substring) or maximal substring length is not small; DFS over an implicit substring trie may become too slow or memory intensive.
- If the bottleneck is clearly algorithmic (e.g., an inherently O(N^2) comparison logic) and the main improvement needed is a different algorithm, not just constant-factor reductions.
- When code clarity and maintainability are prioritized over extreme performance, and the current solution already meets time and memory limits with comfortable margins.
- If input sizes are small enough that additional complexity from encoding, tries, or custom frequency structures would not pay off in practice.

## Minimal example
Before:
```cpp
string s; int k; cin >> s >> k; map<string,int> freq;
for (int i = 0; i + k <= (int)s.size(); ++i) {
    string t = s.substr(i, k);          // alloc every time
    ++freq[t];                          // log|freq| tree ops on strings
}
int ans = 0; for (auto &p : freq) ans = max(ans, p.second);
cout << ans << '\n';
```
After:
```cpp
string s; int k; cin >> s >> k; const int KMAX = 10; // assume k <= 10
static int freq[1 << 20]; memset(freq, 0, sizeof(freq));
int mask = 0, cnt = 0; auto enc = [](char c){ return c=='A'?0:c=='C'?1:c=='G'?2:3; };
for (char c : s) { mask = ((mask << 2) | enc(c)) & ((1 << (2*k)) - 1); if (++cnt >= k) ++freq[mask]; }
int ans = 0; for (int i = 0; i < (1 << (2*k)); ++i) ans = max(ans, freq[i]);
cout << ans << '\n';
```
