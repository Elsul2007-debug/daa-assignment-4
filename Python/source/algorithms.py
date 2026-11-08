"""Dynamic programming and exact string algorithms for the JSON Lines launcher."""
from array import array
from collections import deque


def lcs(request):
    a, b = request['a'], request['b']
    n, m = len(a), len(b)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    result = []
    i, j = n, m
    while i and j:
        if a[i - 1] == b[j - 1]:
            result.append(a[i - 1])
            i -= 1
            j -= 1
        elif dp[i - 1][j] >= dp[i][j - 1]:
            i -= 1
        else:
            j -= 1
    return {'length': dp[n][m], 'sequence': ''.join(reversed(result))}


def merge(request):
    sizes = request['sizes']
    n = len(sizes)
    if n < 2:
        return {'cost': 0, 'plan': []}
    prefix = [0]
    for value in sizes:
        prefix.append(prefix[-1] + value)
    dp = [[0] * n for _ in range(n)]
    split = [[0] * n for _ in range(n)]
    for length in range(2, n + 1):
        for left in range(n - length + 1):
            right = left + length - 1
            total = prefix[right + 1] - prefix[left]
            best = None
            for mid in range(left, right):
                candidate = dp[left][mid] + dp[mid + 1][right] + total
                if best is None or candidate < best:
                    best = candidate
                    split[left][right] = mid
            dp[left][right] = best
    plan = []
    stack = [(0, n - 1, False)]
    while stack:
        left, right, ready = stack.pop()
        if left == right:
            continue
        mid = split[left][right]
        if ready:
            plan.append([left, mid, right])
        else:
            stack.extend([(left, right, True), (mid + 1, right, False), (left, mid, False)])
    return {'cost': dp[0][n - 1], 'plan': plan}


def tree(request):
    n, weights = request['n'], request['weights']
    if not n:
        return {'weight': 0, 'selected': []}
    adj = [[] for _ in range(n)]
    for u, v in request['edges']:
        adj[u].append(v)
        adj[v].append(u)
    parent = [-1] * n
    order = [0]
    for u in order:
        for v in adj[u]:
            if v != parent[u]:
                parent[v] = u
                order.append(v)
    take = weights.copy()
    skip = [0] * n
    for u in reversed(order):
        if parent[u] != -1:
            p = parent[u]
            take[p] += skip[u]
            skip[p] += max(take[u], skip[u])
    chosen = [False] * n
    selected = []
    for u in order:
        if (parent[u] == -1 or not chosen[parent[u]]) and take[u] > skip[u]:
            chosen[u] = True
            selected.append(u)
    return {'weight': max(take[0], skip[0]), 'selected': selected}


def naive(request):
    text, pattern = request['text'], request['pattern']
    n, m = len(text), len(pattern)
    positions = []
    for start in range(n - m + 1):
        j = 0
        while j < m and text[start + j] == pattern[j]:
            j += 1
        if j == m:
            positions.append(start)
    return {'positions': positions}


def kmp(request):
    text, pattern = request['text'], request['pattern']
    m = len(pattern)
    if m == 0:
        return {'positions': list(range(len(text) + 1))}
    pi = [0] * m
    for i in range(1, m):
        j = pi[i - 1]
        while j and pattern[i] != pattern[j]:
            j = pi[j - 1]
        if pattern[i] == pattern[j]:
            j += 1
        pi[i] = j
    positions = []
    j = 0
    for i, char in enumerate(text):
        while j and char != pattern[j]:
            j = pi[j - 1]
        if char == pattern[j]:
            j += 1
        if j == m:
            positions.append(i - m + 1)
            j = pi[j - 1]
    return {'positions': positions}


def rk(request):
    text, pattern = request['text'], request['pattern']
    n, m = len(text), len(pattern)
    if not m:
        return {'positions': list(range(n + 1))}
    if m > n:
        return {'positions': []}
    base, mod = 31, 101
    power = pow(base, m - 1, mod)
    target = window = 0
    for i in range(m):
        target = (target * base + ord(pattern[i])) % mod
        window = (window * base + ord(text[i])) % mod
    positions = []
    for start in range(n - m + 1):
        if target == window:
            j = 0
            while j < m and text[start + j] == pattern[j]:
                j += 1
            if j == m:
                positions.append(start)
        if start + m < n:
            window = ((window - ord(text[start]) * power) * base + ord(text[start + m])) % mod
    return {'positions': positions}


def suffix(request):
    text = request['text']
    n = len(text)
    if not n:
        return {'sa': [], 'lcp': [], 'repeated': ''}
    sa = list(range(n))
    rank = [ord(c) for c in text]
    width = 1
    while width < n:
        def pair(i):
            return (rank[i], rank[i + width] if i + width < n else -1)
        sa.sort(key=pair)
        updated = [0] * n
        for i in range(1, n):
            updated[sa[i]] = updated[sa[i - 1]] + (pair(sa[i]) != pair(sa[i - 1]))
        rank = updated
        if rank[sa[-1]] == n - 1:
            break
        width *= 2
    inverse = [0] * n
    for i, start in enumerate(sa):
        inverse[start] = i
    lcp = [0] * n
    height = 0
    for i in range(n):
        pos = inverse[i]
        if pos == 0:
            height = 0
            continue
        j = sa[pos - 1]
        while i + height < n and j + height < n and text[i + height] == text[j + height]:
            height += 1
        lcp[pos] = height
        height = max(0, height - 1)
    best = max(range(n), key=lambda i: lcp[i])
    return {'sa': sa, 'lcp': lcp, 'repeated': text[sa[best]:sa[best] + lcp[best]]}


def aho(request):
    patterns, texts = request['patterns'], request['texts']
    if not patterns:
        return {'counts': [[] for _ in texts]}
    # Compact fixed-alphabet rows keep the full transition table affordable.
    go = [array('i', [-1]) * 95]
    failure = [0]
    terminals = []
    for pattern in patterns:
        state = 0
        for char in pattern:
            c = ord(char) - 32
            if go[state][c] == -1:
                go[state][c] = len(go)
                go.append(array('i', [-1]) * 95)
                failure.append(0)
            state = go[state][c]
        terminals.append(state)
    queue = deque()
    for c in range(95):
        child = go[0][c]
        if child == -1:
            go[0][c] = 0
        else:
            queue.append(child)
    order = []
    while queue:
        state = queue.popleft()
        order.append(state)
        fallback = go[failure[state]]
        for c in range(95):
            child = go[state][c]
            if child == -1:
                go[state][c] = fallback[c]
            else:
                failure[child] = fallback[c]
                queue.append(child)
    counts = []
    for text in texts:
        visits = [0] * len(go)
        state = 0
        for char in text:
            state = go[state][ord(char) - 32]
            visits[state] += 1
        for state in reversed(order):
            visits[failure[state]] += visits[state]
        counts.append([visits[state] for state in terminals])
    return {'counts': counts}
