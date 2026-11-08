"""Run from repository root: python3 tests/student/benchmark.py."""
import json
import platform
import random
import statistics
import subprocess
import sys
from pathlib import Path
from time import perf_counter_ns

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'Python/source'))
import algorithms

rng = random.Random(20261108)
rows = []
for distribution in ('random abcd', 'repetitive a'):
    for n, m in ((600, 60), (1500, 150), (3000, 300)):
        if distribution == 'random abcd':
            text = ''.join(rng.choices('abcd', k=n))
            pattern = text[n // 2:n // 2 + m]
        else:
            text, pattern = 'a' * n, 'a' * m
        request = {'text': text, 'pattern': pattern}
        expected = {'positions': [i for i in range(n - m + 1) if text[i:i + m] == pattern]}
        methods = [algorithms.naive, algorithms.kmp, algorithms.rk]
        for method in methods:
            assert method(request) == expected
            method(request)  # One untimed warm-up per method and case.
        times = {method.__name__: [] for method in methods}
        for run in range(3):
            for method in methods[run:] + methods[:run]:
                start = perf_counter_ns()
                result = method(request)
                elapsed = (perf_counter_ns() - start) / 1e6
                assert result == expected
                times[method.__name__].append(elapsed)
        for method in methods:
            values = times[method.__name__]
            rows.append({'distribution': distribution, 'n': n, 'm': m, 'matches': len(expected['positions']), 'method': method.__name__, 'runs_ms': values, 'median_ms': statistics.median(values)})
try:
    cpu = subprocess.check_output(['sysctl', '-n', 'machdep.cpu.brand_string'], text=True).strip()
except (OSError, subprocess.CalledProcessError):
    cpu = platform.processor() or platform.machine()
print(json.dumps({'seed': 20261108, 'python': sys.version, 'platform': platform.platform(), 'cpu': cpu, 'scope': 'one direct algorithm call, including result construction; excludes imports, generation, oracle, validation, JSON, process startup', 'warmup': 'one untimed call per method/case after validation; CPython without JIT flags', 'rows': rows}, indent=2))
