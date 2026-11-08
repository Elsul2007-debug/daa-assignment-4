# Assignment 4 — Analysis

## Environment and commands

Language: Python. Measured with CPython 3.13.5, macOS 15.3.1 arm64, Apple M4, 16 GiB RAM. The implementation uses only the standard library and supports Python 3.12+. Run these commands from the repository root:

```sh
python3 tools/run.py --setup
python3 tools/run.py --check
python3 tools/run.py --input examples/lcs.jsonl
python3 tests/student/test_algorithms.py
python3 tests/student/benchmark.py > tests/student/benchmark-results.json
```

Python needs no separate compilation. The unchanged launcher reads UTF-8 JSON Lines, prints one result per request and writes no algorithm diagnostics to stdout. All algorithm state is local to the request. Python integers preserve exact costs and counts.

## Algorithm explanations

### LCS

`dp[i][j]` is the LCS length of `a[:i]` and `b[:j]`. Row zero and column zero are zero. Equal final characters extend `dp[i-1][j-1]`; otherwise the optimum is the maximum of `dp[i-1][j]` and `dp[i][j-1]`. Rows are filled in increasing order, so dependencies are ready. For a mismatch a common subsequence must omit at least one final character; the two alternatives cover an optimum. For equal characters an optimum can use that common final character, leaving the smaller prefix problem. Induction on prefix lengths proves the table.

Backtracking starts at `(n,m)`, collects matching characters on diagonal moves and follows an optimal predecessor on mismatches. Ties prefer removing a character from `a`. Reversing the collected characters restores their order. Empty inputs return the empty subsequence. Time and auxiliary memory are O((n+1)(m+1)); input storage is O(n+m+1), output O(min(n,m)+1). `tea_time` versus `team` distinguishes subsequences from substrings.

### Ordered merging

`dp[l][r]` is the minimum cost to merge the inclusive original interval. Singleton intervals cost zero; zero or one block needs no operations. The last merge splits at some `k` into `[l,k]` and `[k+1,r]`, with cost `dp[l][k]+dp[k+1][r]+prefix[r+1]-prefix[l]`. Every valid last merge has exactly this form. Enumerating all splits and applying induction on interval length therefore gives the optimum. Increasing lengths ensure both children are ready. Prefix sums compute the combined size in constant time.

The first minimum split is retained in ties. An explicit stack emits left and right child operations before their parent, giving a chronological plan of n-1 merges. It never merges nonadjacent blocks. Time O(n^3), auxiliary memory O(n^2), input and output O(n), with O(1) for n=0. Zero sizes test ties; 200 blocks of size 10^9 test a total above 32-bit range. The equal-size optimum is 1544*10^9 (56 leaves at depth 7 and 144 at depth 8).

### Tree independent set

Root the tree at 0 using an iterative traversal and record parents. `take[u]` is the best subtree weight when u is selected; `skip[u]` is the best when u is omitted. Reverse traversal processes children first. `take[u]=weights[u]+sum(skip[v])` and `skip[u]=sum(max(take[v],skip[v]))`. Child subtrees have no cross edges, so their independent optimal choices combine. These two cases exhaust whether u belongs to a solution, proving the recurrence by subtree induction.

Reconstruction follows parent-before-child order. A selected parent forces a child to be skipped; otherwise choose the child exactly when its take value is larger. Ties choose skip. The recorded selected vertices are unique and nonadjacent, and their sum equals the root optimum. The empty set is allowed; all-negative weights give zero. No recursive calls are used, including for a 100000-vertex chain. Time, auxiliary memory and input storage are O(n+1); output is O(n+1).

### Naive search

For each start from 0 through n-m inclusive, compare characters until a mismatch or the end of the pattern. Before each comparison the preceding j characters agree. Therefore a start is reported exactly when the entire pattern agrees. Incrementing start by one retains overlaps and sorted positions. For m=0, the comparison loop is empty and all n+1 boundaries are returned; m>n produces no starts. Time O(nm+n+1), auxiliary space O(1), output O(z+1), input O(n+m+1). `aaaaa`/`aaa` must yield 0,1,2.

### KMP

`pi[i]` is the longest proper prefix of the pattern that is also a suffix ending at i. Build it left to right. On mismatch, replacing j by `pi[j-1]` tries the next possible border without discarding a viable match. The same fallback is used while scanning the text, where j is the length of a matching pattern prefix ending at the previous text character. A full match is recorded and falls back to `pi[m-1]`, preserving overlaps. Empty patterns are handled before indexing. Border lengths rise by at most one per processed character and each fallback strictly decreases them, so the total fallback work is linear.

Time O(n+m+z+1), auxiliary memory O(m+1), output O(z+1), input O(n+m+1). `abababa`/`aba` tests fallback after complete matches; the empty-pattern test catches unsafe indexing.

### Exact Rabin–Karp

The hash is the polynomial of ASCII codes with base 31 and modulus 101, highest power on the left. Initialize pattern and first-window hashes in O(m). With `power=31^(m-1) mod 101`, the next window hash is `((old-ord(outgoing)*power)*31+ord(incoming)) % 101`. Removing the left term and shifting the remaining polynomial proves the update. Python's positive-modulus remainder normalizes negative intermediate values.

Unequal hashes cannot represent equal strings. Equal hashes trigger an explicit character comparison, so collisions cannot create false positives. Empty and too-long patterns return before window initialization. For 1<=m<=n, time is O(n+m+c*m), where c is the number of candidate windows, including true matches. A universal bound is O(nm+n+m+1), not deterministic linear time. Auxiliary space O(1), output O(z+1), input O(n+m+1). `abdj`/`ab` reports only 0 even though `ab` and `dj` both hash to 75.

### Suffix array and Kasai

Initially ranks are character codes. At doubling width k, sort the n starts by `(rank[i], rank[i+k])`, using -1 beyond the end. The first rank describes the first k characters and the second the next k, so their lexicographic pair orders prefixes of length 2k. Assign new ranks to distinct pairs. Induction on doubling rounds proves the invariant. Stop when all ranks differ or the width covers the text. No suffix strings are materialized, and no empty suffix or sentinel is returned. Python comparison sorting gives O(n log^2(n+1)) time and O(n+1) auxiliary storage including temporary keys and sorting workspace.

Kasai builds inverse suffix ranks. It compares each suffix to its lexicographic predecessor, starting at the previous common length minus one. Removing the first character preserves at least that many common characters for an appropriate predecessor, so this lower bound is safe. Successful extensions total O(n), giving O(n) time. Rank zero has LCP zero. The maximum adjacent LCP is a longest repeat: all suffixes sharing a prefix are contiguous, so any repeated prefix appears between adjacent suffixes in that range. The first maximum is chosen in ties; overlapping starts are allowed. Empty text returns empty arrays/string. Total auxiliary and output space are O(n+1), with O(n+1) input storage. `banana` tests ordering and the overlapping repeat `ana`; all-equal length 50000 tests long LCP reuse.

### Aho–Corasick

Build a trie over ASCII 32..126. Each dictionary position stores its terminal state; duplicate strings share a terminal. Rows are compact signed-integer arrays with 95 transitions. Root missing transitions lead to root. Breadth-first construction sets each child's failure link to the longest proper suffix state through its parent's completed failure row, then fills missing transitions from that row. BFS makes shorter-state transitions available first. Thus scanning keeps the longest suffix of the processed text that is a trie prefix.

For each text, reset state and visits. Increment only the reached state for each character. Reverse BFS adds visits from each state to its failure parent. Since failure depth decreases, all deeper contributions arrive before a state is propagated. Every pattern ending at a character lies on this failure chain, so its terminal receives exactly one contribution for that occurrence. This counts overlaps and suffix patterns without copying inherited output lists. Repeated terminals provide equal duplicate counts; repeated texts remain independent. Empty dictionaries return an empty row per text, and an empty texts array gives no rows.

For total dictionary length L, p positions and S states, construction takes O(L+95S+p), auxiliary memory O(95S+p). A text takes O(length+S+p); q output rows take O(q*(p+1)+1) memory. Input storage is O(L+total text length+p+q+1). Dense occurrence lists are never materialized. `he,she,he` against two `sheshe` texts checks suffixes, duplicates and reset.

## Own tests and observed results

`tests/student/test_algorithms.py` uses fixed seeds and independent small oracles: subsequence enumeration, enumeration of adjacent merge schedules, vertex subsets, direct substring comparisons and explicit small suffix sorting. These simple oracles are test-only; they do not replace the required algorithms. Witnesses are validated by their properties, so different valid optima are accepted. The exhaustive search test checks 3969 text/pattern pairs with all three methods.

The setup check, all 44 public cases, the repeated public batch, and all eight student test methods passed. Logs are saved in `tests/student/setup.log`, `public-checks.log` and `student-tests.log`. Full-size checks establish correctness on those constructed families, not on every possible large input or every grading machine.

|Command|Fixture/input|Expected|Actual|Defect detected|
|---|---|---|---|---|
|lcs|1000 copies of a on both sides|length 1000|1000, passed|table boundary/scale|
|merge|200 blocks, each 10^9|cost 1544000000000|1544000000000, passed|overflow and interval cost|
|merge|80 seeded short arrays|optimal cost and legal chronological plan|all passed|nonadjacent or parent-first merges|
|tree|100000-node chain, each 10^9|weight 50000000000000|50000000000000, passed|recursion depth and overflow|
|tree|100 seeded small trees|subset-enumerated optimum and valid witness|all passed|negative weights, ties, adjacency|
|naive/kmp/rk|all binary strings through length 5|all exact starts including empty boundaries|all passed|overlaps and off-by-one starts|
|rk|abdj / ab|[0]|[0]|hash-only false match|
|suffix|a repeated 50000 times|SA 49999..0, LCP 0..49999, repeat length 49999|exact arrays passed|sentinel and Kasai reuse|
|aho|10000 copies of a^10; 100 texts a^2000|100 rows of 10000 counts, each 1991|all passed|duplicate aggregation and resets|
|aho|one a^100000; texts a^200000 and empty|[[100001],[0]]|exactly equal|state-count scale and empty text|
|mixed JSONL|eight tasks repeated three times|24 independent results|24 matching results|request state leakage|

## Search comparison

Generator: `random.Random(20261108)`. Sizes (n,m) are (600,60), (1500,150), (3000,300), all within the shared domain. Random text uses independent choices from `abcd`; its pattern is the m-character slice starting at n//2, ensuring a match. Repetitive text and pattern contain only `a`. Identical pairs are used for all three algorithms. A direct-slicing oracle verifies all outputs before timing and again after each measured call.

The command above writes raw measurements and environment metadata to `tests/student/benchmark-results.json`. Scope: one direct algorithm call including result construction; generation, validation, imports, JSON transport and process startup are excluded equally. There is one untimed warm-up call per case/method after correctness verification; ordinary CPython is run without JIT flags. Three runs per method use rotated method order. Units below are milliseconds; this is an interactive laptop, not an isolated benchmark host.

|Case|n|m|Method|Run 1 (ms)|Run 2 (ms)|Run 3 (ms)|Median (ms)|Correct outputs|
|---|---:|---:|---|---:|---:|---:|---:|---|
|random abcd|600|60|naive|0.035459|0.035000|0.035334|0.035334|yes|
|random abcd|600|60|kmp|0.030083|0.029208|0.028708|0.029208|yes|
|random abcd|600|60|rk|0.057584|0.056959|0.057458|0.057458|yes|
|random abcd|1500|150|naive|0.085458|0.085333|0.083750|0.085333|yes|
|random abcd|1500|150|kmp|0.071709|0.069292|0.071875|0.071709|yes|
|random abcd|1500|150|rk|0.140417|0.138666|0.139417|0.139417|yes|
|random abcd|3000|300|naive|0.168833|0.170834|0.168583|0.168833|yes|
|random abcd|3000|300|kmp|0.139375|0.135333|0.141458|0.139375|yes|
|random abcd|3000|300|rk|0.275833|0.274458|0.277667|0.275833|yes|
|repetitive a|600|60|naive|0.970000|0.953000|0.942000|0.953000|yes|
|repetitive a|600|60|kmp|0.041833|0.046625|0.040041|0.041833|yes|
|repetitive a|600|60|rk|1.029208|1.007709|0.999042|1.007709|yes|
|repetitive a|1500|150|naive|5.760250|6.219542|5.772750|5.772750|yes|
|repetitive a|1500|150|kmp|0.111167|0.102834|0.102917|0.102917|yes|
|repetitive a|1500|150|rk|5.812583|5.902292|5.912209|5.902292|yes|
|repetitive a|3000|300|naive|23.483750|23.289625|23.073500|23.289625|yes|
|repetitive a|3000|300|kmp|0.230209|0.225500|0.220875|0.225500|yes|
|repetitive a|3000|300|rk|23.497000|25.015084|22.841791|23.497000|yes|

Random inputs often reject a naive candidate after a few comparisons. Repetitive inputs make naive and exact RK compare a whole pattern at almost every start, whereas KMP reuses border information. This explains the large repetitive-input gap in these measurements. Constant factors and laptop scheduling also affect small timings; three samples and their medians do not prove asymptotic complexity. Modulus 101 deliberately creates frequent collision candidates. It is a teaching laboratory and should not be generalized to all production rolling hashes. A larger modulus reduces accidental collisions but cannot eliminate verification of actual matches in an exact implementation.

## Sources and AI assistance

Sources: the official RZhaniya/daa-assignment-4-archive template, English specification, contracts, rubric, testing guide, and accompanying bilingual lesson/practice materials. They supplied the interface, required recurrences/algorithms, limits and examples. The JSON Lines launcher and public tests are unchanged template files.

OpenAI Codex assisted with the algorithm implementations, student test and benchmark scripts, this analysis, and executing the recorded checks. Verification performed in this work includes the supplied public checks, independently structured brute-force oracles, witness validation, full-size constructed cases and measured search comparisons. These executions are not a claim that the student has personally reviewed or independently reproduced them. The student should review the code and reproduce the commands before presenting it; the individual defence must be completed independently.
