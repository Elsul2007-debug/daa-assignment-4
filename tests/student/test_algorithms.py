"""Deterministic oracle, witness, boundary and full-domain checks."""
import itertools
import json
from pathlib import Path
import random
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'Python/source'))
import algorithms as a


def occurrences(text, pattern):
    return [i for i in range(len(text) - len(pattern) + 1) if text[i:i + len(pattern)] == pattern]


def subseq(s, t):
    it = iter(t)
    return all(any(c == x for x in it) for c in s)


class AlgorithmsTest(unittest.TestCase):
    def test_lcs_oracle(self):
        rng = random.Random(104)
        for _ in range(100):
            x = ''.join(rng.choices('abc', k=rng.randrange(9)))
            y = ''.join(rng.choices('abc', k=rng.randrange(9)))
            candidates = [''.join(x[i] for i in range(len(x)) if mask >> i & 1) for mask in range(1 << len(x))]
            best = max(len(s) for s in candidates if subseq(s, y))
            r = a.lcs({'a': x, 'b': y})
            self.assertEqual(r['length'], best)
            self.assertEqual(len(r['sequence']), best)
            self.assertTrue(subseq(r['sequence'], x) and subseq(r['sequence'], y))

    def test_merge_oracle_and_plan(self):
        def brute(values):
            if len(values) < 2:
                return 0
            return min(values[i] + values[i + 1] + brute(values[:i] + [values[i] + values[i + 1]] + values[i + 2:]) for i in range(len(values) - 1))
        rng = random.Random(204)
        for _ in range(80):
            sizes = [rng.randrange(6) for _ in range(rng.randrange(7))]
            r = a.merge({'sizes': sizes})
            self.assertEqual(r['cost'], brute(sizes))
            blocks = [(i, i, value) for i, value in enumerate(sizes)]
            cost = 0
            for left, mid, right in r['plan']:
                idx = next(i for i, b in enumerate(blocks) if b[:2] == (left, mid))
                self.assertEqual(blocks[idx + 1][:2], (mid + 1, right))
                size = blocks[idx][2] + blocks[idx + 1][2]
                cost += size
                blocks[idx:idx + 2] = [(left, right, size)]
            self.assertEqual(cost, r['cost'])
            self.assertEqual(len(r['plan']), max(0, len(sizes) - 1))

    def test_tree_oracle(self):
        rng = random.Random(304)
        for _ in range(100):
            n = rng.randrange(11)
            weights = [rng.randrange(-5, 10) for _ in range(n)]
            edges = [[v, rng.randrange(v)] for v in range(1, n)]
            best = max(sum(weights[i] for i in range(n) if mask >> i & 1) for mask in range(1 << n) if all(not (mask >> u & 1 and mask >> v & 1) for u, v in edges))
            r = a.tree({'n': n, 'weights': weights, 'edges': edges})
            selected = set(r['selected'])
            self.assertEqual(len(selected), len(r['selected']))
            self.assertTrue(all(not (u in selected and v in selected) for u, v in edges))
            self.assertEqual(sum(weights[v] for v in selected), best)
            self.assertEqual(r['weight'], best)

    def test_search_exhaustive(self):
        strings = [''.join(s) for n in range(6) for s in itertools.product('ab', repeat=n)]
        for text in strings:
            for pattern in strings:
                expected = {'positions': occurrences(text, pattern)}
                for method in (a.naive, a.kmp, a.rk):
                    self.assertEqual(method({'text': text, 'pattern': pattern}), expected)
        self.assertEqual(a.rk({'text': 'abdj', 'pattern': 'ab'}), {'positions': [0]})
        for method in (a.naive, a.kmp, a.rk):
            self.assertEqual(method({'text': ' ~! ~!', 'pattern': ' ~!'}), {'positions': [0, 3]})

    def test_suffix_oracle(self):
        rng = random.Random(504)
        for _ in range(200):
            text = ''.join(rng.choices('ab ~!', k=rng.randrange(40)))
            sa = sorted(range(len(text)), key=lambda i: text[i:])
            lcp = [0] * len(text)
            for i in range(1, len(text)):
                u, v = sa[i - 1], sa[i]
                while u + lcp[i] < len(text) and v + lcp[i] < len(text) and text[u + lcp[i]] == text[v + lcp[i]]:
                    lcp[i] += 1
            r = a.suffix({'text': text})
            self.assertEqual(r['sa'], sa)
            self.assertEqual(r['lcp'], lcp)
            self.assertEqual(len(r['repeated']), max(lcp, default=0))
            if r['repeated']:
                self.assertGreaterEqual(len(occurrences(text, r['repeated'])), 2)

    def test_aho_oracle(self):
        rng = random.Random(604)
        for _ in range(100):
            patterns = [''.join(rng.choices('ab ~', k=rng.randrange(1, 6))) for _ in range(rng.randrange(15))]
            texts = [''.join(rng.choices('ab ~', k=rng.randrange(30))) for _ in range(rng.randrange(5))]
            self.assertEqual(a.aho({'patterns': patterns, 'texts': texts})['counts'], [[len(occurrences(t, p)) for p in patterns] for t in texts])
        self.assertEqual(a.aho({'patterns': ['he', 'she', 'he'], 'texts': ['sheshe', 'sheshe', '']}), {'counts': [[2, 2, 2], [2, 2, 2], [0, 0, 0]]})

    def test_full_domains(self):
        self.assertEqual(a.lcs({'a': 'a' * 1000, 'b': 'a' * 1000})['length'], 1000)
        self.assertEqual(a.merge({'sizes': [10**9] * 200})['cost'], 1544 * 10**9)
        n = 100000
        tree = a.tree({'n': n, 'weights': [10**9] * n, 'edges': [[i - 1, i] for i in range(1, n)]})
        self.assertEqual(tree['weight'], 50000 * 10**9)
        self.assertEqual(a.naive({'text': 'a' * 3000, 'pattern': 'a' * 1500})['positions'], list(range(1501)))
        self.assertEqual(a.kmp({'text': 'a' * 200000, 'pattern': 'a' * 100000})['positions'], list(range(100001)))
        self.assertEqual(a.rk({'text': 'a' * 10000, 'pattern': 'a' * 2000})['positions'], list(range(8001)))
        r = a.suffix({'text': 'a' * 50000})
        self.assertEqual(r['sa'], list(range(49999, -1, -1)))
        self.assertEqual(r['lcp'], list(range(50000)))
        self.assertEqual(len(r['repeated']), 49999)
        r = a.aho({'patterns': ['a' * 10] * 10000, 'texts': ['a' * 2000] * 100})
        self.assertEqual(r['counts'], [[1991] * 10000 for _ in range(100)])
        r = a.aho({'patterns': ['a' * 100000], 'texts': ['a' * 200000, '']})
        self.assertEqual(r['counts'], [[100001], [0]])

    def test_jsonl_reset(self):
        requests = [{'task': 'lcs', 'a': '', 'b': 'x'}, {'task': 'merge', 'sizes': []}, {'task': 'tree', 'n': 0, 'weights': [], 'edges': []}, {'task': 'suffix', 'text': ''}, {'task': 'aho', 'patterns': [], 'texts': ['', 'abc']}] + [{'task': method, 'text': 'aaa', 'pattern': ''} for method in ('naive', 'kmp', 'rk')]
        expected = [getattr(a, r['task'])(r) for r in requests] * 3
        proc = subprocess.run([sys.executable, str(ROOT / 'Python/source/main.py')], input=''.join(json.dumps(r) + '\n' for r in requests * 3), text=True, capture_output=True, check=True)
        self.assertEqual([json.loads(line) for line in proc.stdout.splitlines()], expected)


if __name__ == '__main__':
    unittest.main(verbosity=2)
