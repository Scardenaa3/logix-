"""P10: MST para 40 centros logisticos - Kruskal (Union-Find) vs Prim (Heap y arreglo denso)."""
from __future__ import annotations

import heapq
import math

from common.generators import make_rng
from common.metrics import best_of, print_header, print_table

INF = float("inf")
Adj = list[list[tuple[int, float]]]


class UnionFind:
    """Disjoint-Set con union por tamano (rango) y compresion de caminos: costo amortizado O(alpha(n)) ~ O(1)."""

    def __init__(self, n: int):
        self.parent = list(range(n))
        self.size = [1] * n
        self.ops = 0

    def find(self, x: int) -> int:
        root = x
        while self.parent[root] != root:
            self.ops += 1
            root = self.parent[root]
        while self.parent[x] != root:  # compresion de caminos
            self.ops += 1
            self.parent[x], x = root, self.parent[x]
        return root

    def union(self, a: int, b: int) -> bool:
        ra, rb = self.find(a), self.find(b)
        self.ops += 1
        if ra == rb:
            return False
        if self.size[ra] < self.size[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        self.size[ra] += self.size[rb]
        return True


def _coords(n: int, rng) -> list[tuple[float, float]]:
    return [(rng.uniform(0.0, 100.0), rng.uniform(0.0, 100.0)) for _ in range(n)]


def build_complete_hub_graph(n: int = 40, seed: int = 42) -> Adj:
    """Grafo completo: costo de tendido = distancia x factor de terreno U(0.9, 1.25)."""
    rng = make_rng(seed)
    coords = _coords(n, rng)
    adj: Adj = [[] for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            d = math.hypot(coords[i][0] - coords[j][0], coords[i][1] - coords[j][1])
            cost = round(d * rng.uniform(0.9, 1.25), 3)
            adj[i].append((j, cost))
            adj[j].append((i, cost))
    return adj


def build_graph_with_density(n: int, density: float, seed: int = 42) -> Adj:
    """Grafo conexo con ~density * n(n-1)/2 aristas (siempre incluye un arbol aleatorio para garantizar conexidad)."""
    rng = make_rng(seed)
    coords = _coords(n, rng)
    adj: Adj = [[] for _ in range(n)]
    edges_set: set[tuple[int, int]] = set()

    def add_e(u: int, v: int) -> None:
        a, b = min(u, v), max(u, v)
        if a == b or (a, b) in edges_set:
            return
        edges_set.add((a, b))
        w = round(math.hypot(coords[a][0] - coords[b][0], coords[a][1] - coords[b][1]), 3)
        adj[a].append((b, w))
        adj[b].append((a, w))

    for v in range(1, n):
        add_e(rng.randrange(0, v), v)
    max_edges = n * (n - 1) // 2
    target = max(len(edges_set), int(max_edges * max(0.0, min(1.0, density))))
    if target >= max_edges * 0.6:  # denso: completar por enumeracion (evita bucles de rechazo)
        pairs = [(i, j) for i in range(n) for j in range(i + 1, n) if (i, j) not in edges_set]
        rng.shuffle(pairs)
        for i, j in pairs[: target - len(edges_set)]:
            add_e(i, j)
    else:
        guards = 0
        while len(edges_set) < target and guards < max_edges * 5:
            guards += 1
            add_e(rng.randrange(0, n), rng.randrange(0, n))
    return adj


def edge_count(adj: Adj) -> int:
    return sum(len(a) for a in adj) // 2


def _require_connected(n: int, mst_edges: list) -> None:
    if len(mst_edges) != n - 1:
        raise ValueError(f"Grafo no conexo: el MST tiene {len(mst_edges)} aristas (se esperaban {n - 1})")


def kruskal_mst(n: int, adj: Adj, stats: dict | None = None) -> tuple[float, list[tuple[int, int, float]], int]:
    edges = [(w, u, v) for u in range(n) for v, w in adj[u] if u < v]
    edges.sort(key=lambda t: t[0])
    uf = UnionFind(n)
    mst: list[tuple[int, int, float]] = []
    total, examined = 0.0, 0
    for w, u, v in edges:
        examined += 1
        if uf.union(u, v):
            mst.append((u, v, w))
            total += w
            if len(mst) == n - 1:
                break
    _require_connected(n, mst)
    if stats is not None:
        stats.update(E=len(edges), examined=examined, uf_ops=uf.ops, sort_cmp=int(len(edges) * math.log2(max(2, len(edges)))))
    return round(total, 3), mst, uf.ops


def prim_heap_mst(n: int, adj: Adj, start: int = 0, stats: dict | None = None) -> tuple[float, list[tuple[int, int, float]]]:
    visited = [False] * n
    visited[start] = True
    pq: list[tuple[float, int, int]] = [(w, start, v) for v, w in adj[start]]
    heapq.heapify(pq)
    pushes, pops = len(pq), 0
    mst: list[tuple[int, int, float]] = []
    total = 0.0
    while pq and len(mst) < n - 1:
        w, u, v = heapq.heappop(pq)
        pops += 1
        if visited[v]:
            continue
        visited[v] = True
        mst.append((u, v, w))
        total += w
        for nxt, nw in adj[v]:
            if not visited[nxt]:
                heapq.heappush(pq, (nw, v, nxt))
                pushes += 1
    _require_connected(n, mst)
    if stats is not None:
        stats.update(pushes=pushes, pops=pops)
    return round(total, 3), mst


def build_matrix(n: int, adj: Adj) -> list[list[float]]:
    mat = [[INF] * n for _ in range(n)]
    for u in range(n):
        mat[u][u] = 0.0
        for v, w in adj[u]:
            if w < mat[u][v]:
                mat[u][v] = w
    return mat


def prim_dense_matrix(n: int, mat: list[list[float]], start: int = 0) -> float:
    """Prim con arreglo: O(V^2) sin heap; ideal cuando E ~ V^2."""
    in_mst, min_e = [False] * n, [INF] * n
    min_e[start] = 0.0
    total, added = 0.0, 0
    for _ in range(n):
        u, best = -1, INF
        for i in range(n):
            if not in_mst[i] and min_e[i] < best:
                best, u = min_e[i], i
        if u == -1:
            break
        in_mst[u] = True
        added += 1
        total += best
        row = mat[u]
        for v in range(n):
            if not in_mst[v] and row[v] < min_e[v]:
                min_e[v] = row[v]
    if added != n:
        raise ValueError("Grafo no conexo")
    return round(total, 3)


def prim_dense_array_mst(n: int, adj: Adj, start: int = 0) -> float:
    return prim_dense_matrix(n, build_matrix(n, adj), start)


def demo() -> None:
    print_header("P10 - Red de Fibra Optica entre 40 Centros Logisticos (780 aristas candidatas)")
    adj = build_complete_hub_graph(40, seed=42)
    st: dict = {}
    w_k, e_k, uf_ops = kruskal_mst(40, adj, st)
    sp: dict = {}
    w_ph, _ = prim_heap_mst(40, adj, stats=sp)
    w_pd = prim_dense_array_mst(40, adj)
    total_all = sum(w for u in range(40) for v, w in adj[u] if u < v)
    print(f"Aristas candidatas={edge_count(adj)} | Aristas en el MST={len(e_k)} (= V-1)")
    print(f"Costo MST: Kruskal={w_k:.3f} | Prim-Heap={w_ph:.3f} | Prim-Denso={w_pd:.3f} | coinciden: {w_k == w_ph == w_pd}")
    print(f"Costo de tender TODOS los enlaces candidatos: {total_all:,.1f} -> el MST cuesta {w_k / total_all * 100:.1f}% de eso")
    print(f"Kruskal: aristas examinadas={st['examined']}/{st['E']} (corta al completar V-1), pasos Union-Find={uf_ops} | Prim-Heap: push={sp['pushes']}, pop={sp['pops']}")
    print("Primeros enlaces elegidos (u, v, costo):", [(u, v, w) for u, v, w in e_k[:5]])


def benchmark(sizes: list[int] | None = None) -> None:
    n = 150
    print_header(f"P10 - Barrido de densidad (V={n}): tiempo (ms, mejor de 5) y operaciones")
    rows = []
    for dens in (0.05, 0.10, 0.20, 0.40, 0.60, 0.80, 1.00):
        adj = build_graph_with_density(n, dens, seed=42)
        mat = build_matrix(n, adj)  # fuera del cronometro: en un sistema denso la matriz ya existe como estructura
        st_k: dict = {}
        st_p: dict = {}
        _, tk = best_of(lambda: kruskal_mst(n, adj, st_k), 5)
        _, tp = best_of(lambda: prim_heap_mst(n, adj, stats=st_p), 5)
        _, td = best_of(lambda: prim_dense_matrix(n, mat), 5)
        _, tb = best_of(lambda: build_matrix(n, adj), 3)
        winner = min((("Kruskal", tk), ("Prim-Heap", tp), ("Prim-Denso", td)), key=lambda t: t[1])[0]
        rows.append([f"{dens:.2f}", edge_count(adj), f"{tk:.2f}", f"{tp:.2f}", f"{td:.2f}", f"+{tb:.2f}",
                     f"{st_k['sort_cmp']:,}", f"{st_p['pushes'] + st_p['pops']:,}", f"{n * n:,}", winner])
    print_table(["Densidad", "E", "Kruskal", "Prim-Heap", "Prim-Denso", "(+matriz)", "Op Kruskal ~ElogE", "Op Prim-Heap", "Op Denso V^2", "Mas rapido"], rows)
    print("Lectura: en grafos dispersos Kruskal/Prim-Heap hacen ~E log E / ~E log V operaciones (E << V^2); al acercarse a E ~ V^2 "
          "el costo log del heap/ordenamiento pesa y Prim con arreglo O(V^2) se vuelve competitivo (si ya se tiene la matriz).")
