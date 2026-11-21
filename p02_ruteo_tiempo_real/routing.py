"""P02: Ruteo en tiempo real - Dijkstra, A* (Manhattan/Euclidiana), Floyd-Warshall y Contraction Hierarchies."""
from __future__ import annotations

import heapq
import math
import time
from dataclasses import dataclass

from common.generators import RoadEdge, generate_sparse_road_graph, make_rng
from common.metrics import best_of, print_header, print_table

INF = float("inf")
Adj = list[list[RoadEdge]]


@dataclass
class RouteResult:
    cost: float
    path: list[int]
    expanded_nodes: int


# ----------------------------------------------------------------------------- caminos minimos base
def reconstruct_path(parent: list[int], src: int, dst: int) -> list[int]:
    if src == dst:
        return [src]
    if parent[dst] == -1:
        return []
    cur, out = dst, []
    while cur != -1:
        out.append(cur)
        if cur == src:
            break
        cur = parent[cur]
    out.reverse()
    return out if out and out[0] == src else []


def dijkstra_route(adj: Adj, src: int, dst: int) -> RouteResult:
    n = len(adj)
    dist, parent = [INF] * n, [-1] * n
    dist[src] = 0.0
    pq: list[tuple[float, int]] = [(0.0, src)]
    expanded = 0
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist[u]:
            continue
        expanded += 1
        if u == dst:
            break
        for e in adj[u]:
            if e.weight == INF:
                continue
            nd = d + e.weight
            if nd < dist[e.to]:
                dist[e.to], parent[e.to] = nd, u
                heapq.heappush(pq, (nd, e.to))
    return RouteResult(dist[dst], reconstruct_path(parent, src, dst), expanded)


def heuristic(a: tuple[float, float], b: tuple[float, float], kind: str) -> float:
    dx, dy = abs(a[0] - b[0]), abs(a[1] - b[1])
    return dx + dy if kind == "manhattan" else math.hypot(dx, dy)


def astar_route(adj: Adj, coords: list[tuple[float, float]], src: int, dst: int, kind: str = "euclidean") -> RouteResult:
    """A*. Optimo SOLO si h es admisible: peso(u,v) >= distancia(u,v) en la metrica de h."""
    n = len(adj)
    g_score, parent, closed = [INF] * n, [-1] * n, [False] * n
    g_score[src] = 0.0
    pq: list[tuple[float, float, int]] = [(heuristic(coords[src], coords[dst], kind), 0.0, src)]
    expanded = 0
    while pq:
        _, g, u = heapq.heappop(pq)
        if closed[u]:
            continue
        closed[u] = True
        expanded += 1
        if u == dst:
            break
        for e in adj[u]:
            if e.weight == INF or closed[e.to]:
                continue
            ng = g + e.weight
            if ng < g_score[e.to]:
                g_score[e.to], parent[e.to] = ng, u
                heapq.heappush(pq, (ng + heuristic(coords[e.to], coords[dst], kind), ng, e.to))
    return RouteResult(g_score[dst], reconstruct_path(parent, src, dst), expanded)


def floyd_warshall(adj: Adj) -> list[list[float]]:
    n = len(adj)
    dist = [[INF] * n for _ in range(n)]
    for i in range(n):
        dist[i][i] = 0.0
        for e in adj[i]:
            if e.weight < dist[i][e.to]:
                dist[i][e.to] = e.weight
    for k in range(n):
        dk = dist[k]
        for i in range(n):
            dik = dist[i][k]
            if dik == INF:
                continue
            di = dist[i]
            for j in range(n):
                nd = dik + dk[j]
                if nd < di[j]:
                    di[j] = nd
    return dist


# ----------------------------------------------------------------------------- Contraction Hierarchies
class ContractionHierarchy:
    """CH minimalista (grafo no dirigido). Preproceso: contraer nodos por 'edge difference' agregando atajos
    solo si no existe un camino testigo igual de corto. Consulta: Dijkstra bidireccional ascendente por rank.
    Tras cualquier cambio de peso hay que reconstruirla (los atajos codifican costos viejos)."""

    def __init__(self, adj: Adj):
        t0 = time.perf_counter()
        self.n = len(adj)
        self.shortcuts = 0
        rem: list[dict[int, float]] = [dict() for _ in range(self.n)]
        for u in range(self.n):
            for e in adj[u]:
                if e.weight != INF and e.weight < rem[u].get(e.to, INF):
                    rem[u][e.to] = e.weight
                    rem[e.to][u] = e.weight
        all_edges: dict[tuple[int, int], float] = {}
        for u in range(self.n):
            for v, w in rem[u].items():
                if u < v:
                    all_edges[(u, v)] = w
        self.rank = [-1] * self.n
        heap = [(self._priority(rem, v), v) for v in range(self.n)]
        heapq.heapify(heap)
        order = 0
        while heap:
            p, v = heapq.heappop(heap)
            newp = self._priority(rem, v)
            if heap and newp > heap[0][0]:
                heapq.heappush(heap, (newp, v))
                continue
            for u, w, via in self._needed_shortcuts(rem, v):
                key = (min(u, w), max(u, w))
                if via < all_edges.get(key, INF):
                    all_edges[key] = via
                    if via < rem[u].get(w, INF):
                        self.shortcuts += 1
                    rem[u][w] = via
                    rem[w][u] = via
            for u in list(rem[v]):
                del rem[u][v]
            rem[v] = {}
            self.rank[v] = order
            order += 1
        self.up: list[list[tuple[int, float]]] = [[] for _ in range(self.n)]
        for (a, b), w in all_edges.items():
            lo, hi = (a, b) if self.rank[a] < self.rank[b] else (b, a)
            self.up[lo].append((hi, w))
        self.build_ms = (time.perf_counter() - t0) * 1000.0

    def _needed_shortcuts(self, rem, v):
        nb = list(rem[v].items())
        out = []
        for i in range(len(nb)):
            u, wu = nb[i]
            limit = wu + max((w for _, w in nb[i + 1:]), default=0.0)
            wit = self._witness(rem, u, v, limit)
            for j in range(i + 1, len(nb)):
                x, wx = nb[j]
                via = wu + wx
                if wit.get(x, INF) > via:
                    out.append((u, x, via))
        return out

    @staticmethod
    def _witness(rem, src, banned, limit):
        dist = {src: 0.0}
        pq = [(0.0, src)]
        settled = 0
        while pq and settled < 60:
            d, u = heapq.heappop(pq)
            if d > dist.get(u, INF) or d > limit:
                continue
            settled += 1
            for x, w in rem[u].items():
                if x == banned:
                    continue
                nd = d + w
                if nd < dist.get(x, INF):
                    dist[x] = nd
                    heapq.heappush(pq, (nd, x))
        return dist

    def _priority(self, rem, v) -> int:
        return len(self._needed_shortcuts(rem, v)) - len(rem[v])

    def query(self, s: int, t: int) -> tuple[float, int]:
        if s == t:
            return 0.0, 0
        dist = [{s: 0.0}, {t: 0.0}]
        pqs = [[(0.0, s)], [(0.0, t)]]
        best, settled = INF, 0
        side = 0
        while pqs[0] or pqs[1]:
            if not pqs[side]:
                side ^= 1
            d, u = heapq.heappop(pqs[side])
            if d > dist[side].get(u, INF):
                continue
            if d >= best:
                pqs[side] = []
                side ^= 1
                continue
            settled += 1
            other = dist[side ^ 1].get(u)
            if other is not None and d + other < best:
                best = d + other
            for x, w in self.up[u]:
                nd = d + w
                if nd < dist[side].get(x, INF):
                    dist[side][x] = nd
                    heapq.heappush(pqs[side], (nd, x))
            side ^= 1
        return best, settled


# ----------------------------------------------------------------------------- cierre de via y recalculo
def copy_adj(adj: Adj) -> Adj:
    return [list(es) for es in adj]


def close_edge_in_graph(adj: Adj, u: int, v: int, block: bool = True, penalty_factor: float = 10.0) -> None:
    """Cierra la via u-v: bloqueo total (peso INF) o penalizacion (congestion)."""
    for a, b in ((u, v), (v, u)):
        for idx, e in enumerate(adj[a]):
            if e.to == b:
                w = INF if block else round(e.weight * penalty_factor + 500.0, 2)
                adj[a][idx] = RoadEdge(b, w, e.toll)


def edge_usage(routes: list[RouteResult]) -> dict[tuple[int, int], int]:
    usage: dict[tuple[int, int], int] = {}
    for r in routes:
        for a, b in zip(r.path, r.path[1:]):
            key = (min(a, b), max(a, b))
            usage[key] = usage.get(key, 0) + 1
    return usage


def uses_edge(route: RouteResult, edge: tuple[int, int]) -> bool:
    return any((min(a, b), max(a, b)) == edge for a, b in zip(route.path, route.path[1:]))


def make_requests(n: int, count: int = 500, seed: int = 42) -> list[tuple[int, int]]:
    rng = make_rng(seed)
    reqs = [(rng.randrange(0, n), rng.randrange(0, n)) for _ in range(count)]
    return [(s, d if d != s else (s + 1) % n) for s, d in reqs]


def recalculate_fleet(adj: Adj, coords, requests, algo: str = "astar_euclid") -> tuple[int, float, list[float]]:
    total_expanded, costs = 0, []
    for src, dst in requests:
        if algo == "dijkstra":
            r = dijkstra_route(adj, src, dst)
        elif algo == "astar_manhattan":
            r = astar_route(adj, coords, src, dst, "manhattan")
        else:
            r = astar_route(adj, coords, src, dst, "euclidean")
        total_expanded += r.expanded_nodes
        costs.append(r.cost)
    return total_expanded, sum(c for c in costs if c != INF), costs


def suboptimal_count(adj: Adj, coords, requests, kind: str) -> tuple[int, float]:
    """Cuantas rutas de A* cuestan mas que Dijkstra (evidencia de heuristica no admisible)."""
    bad, worst = 0, 0.0
    for s, d in requests:
        ref = dijkstra_route(adj, s, d).cost
        got = astar_route(adj, coords, s, d, kind).cost
        if ref != INF and got > ref + 1e-9:
            bad += 1
            worst = max(worst, got / ref - 1.0)
    return bad, worst


def run_closure_experiment(n: int, vehicles: int = 500, seed: int = 42) -> dict:
    """Cierra la via arterial (la arista mas usada que no desconecte la red) y compara estrategias."""
    adj, coords = generate_sparse_road_graph(num_nodes=n, avg_degree=3.2, seed=seed)
    reqs = make_requests(n, vehicles, seed)
    base = [dijkstra_route(adj, s, d) for s, d in reqs]
    usage = edge_usage(base)
    for edge, _ in sorted(usage.items(), key=lambda kv: -kv[1]):
        closed = copy_adj(adj)
        close_edge_in_graph(closed, edge[0], edge[1], block=True)
        affected_idx = [i for i, r in enumerate(base) if uses_edge(r, edge)]
        if all(dijkstra_route(closed, *reqs[i]).cost != INF for i in affected_idx):
            break
    out = {"n": n, "edge": edge, "affected": len(affected_idx), "usage": usage[edge], "adj": adj, "closed": closed,
           "coords": coords, "reqs": reqs, "base": base, "affected_idx": affected_idx}
    aff_reqs = [reqs[i] for i in affected_idx]
    (exp_d, cost_d, costs_d), t_d = best_of(lambda: recalculate_fleet(closed, coords, reqs, "dijkstra"))
    (exp_a, cost_a, costs_a), t_a = best_of(lambda: recalculate_fleet(closed, coords, reqs, "astar_euclid"))
    (exp_f, _, _), t_aff = best_of(lambda: recalculate_fleet(closed, coords, aff_reqs, "astar_euclid"))
    out.update(t_dij=t_d, exp_dij=exp_d, t_astar=t_a, exp_astar=exp_a, t_aff=t_aff, exp_aff=exp_f,
               astar_equals_dijkstra=all(abs(x - y) < 1e-6 for x, y in zip(costs_d, costs_a)))
    # costo de la contingencia: cuanto sube la ruta de los vehiculos afectados
    old = sum(base[i].cost for i in affected_idx)
    new = sum(costs_d[i] for i in affected_idx)
    out["extra_cost_pct"] = (new / old - 1.0) * 100.0 if old else 0.0
    # Contraction Hierarchies: preproceso sobre el grafo con la via cerrada (hay que rehacerlo tras el cambio)
    ch = ContractionHierarchy(closed)
    _, t_q = best_of(lambda: [ch.query(s, d) for s, d in reqs])
    ch_costs = [ch.query(s, d)[0] for s, d in reqs]
    out.update(ch_build=ch.build_ms, ch_query=t_q, ch_shortcuts=ch.shortcuts,
               ch_ok=all(abs(x - y) < 1e-6 for x, y in zip(costs_d, ch_costs)))
    return out


def demo() -> None:
    print_header("P02 - Ruteo en Tiempo Real Ante Cierre de Via Arterial (500 Vehiculos)")
    r = run_closure_experiment(160)
    print(f"Via arterial cerrada (bloqueo total): {r['edge'][0]} <-> {r['edge'][1]} | usada por {r['usage']} de 500 rutas")
    print(f"Vehiculos afectados (su ruta usaba la via): {r['affected']} -> costo extra de esas rutas: +{r['extra_cost_pct']:.1f}%")
    rows = [
        ["Dijkstra, los 500", f"{r['t_dij']:.1f} ms", r["exp_dij"]],
        ["A* euclidiana, los 500", f"{r['t_astar']:.1f} ms", r["exp_astar"]],
        [f"A* euclidiana, solo {r['affected']} afectados", f"{r['t_aff']:.1f} ms", r["exp_aff"]],
        [f"CH: reconstruir ({r['ch_shortcuts']} atajos) + 500 consultas", f"{r['ch_build']:.1f} + {r['ch_query']:.1f} ms", "-"],
    ]
    print_table(["Estrategia de recalculo", "Tiempo", "Nodos expandidos"], rows)
    print(f"A* da el mismo costo que Dijkstra en las 500 rutas: {r['astar_equals_dijkstra']} | CH coincide con Dijkstra: {r['ch_ok']}")

    n = 160
    eu_adj, eu_co = generate_sparse_road_graph(n, 3.2, 42, "euclidean")
    ma_adj, ma_co = generate_sparse_road_graph(n, 3.2, 42, "manhattan")
    reqs = make_requests(n)
    rows = []
    for label, adj, co, kind in (("red euclidiana + h euclidiana", eu_adj, eu_co, "euclidean"),
                                 ("red Manhattan + h Manhattan", ma_adj, ma_co, "manhattan"),
                                 ("red euclidiana + h Manhattan (NO admisible)", eu_adj, eu_co, "manhattan")):
        bad, worst = suboptimal_count(adj, co, reqs, kind)
        rows.append([label, f"{bad}/500", f"{worst * 100:.1f}%"])
    print("\nAdmisibilidad de la heuristica (rutas de A* mas caras que Dijkstra):")
    print_table(["Escenario", "Rutas suboptimas", "Peor sobrecosto"], rows)
    print("Nota: si la via solo SUBE de peso (cierre) la heuristica sigue admisible; si BAJA (reapertura) las rutas previas "
          "pueden dejar de ser optimas y hay que revalidar a todos los vehiculos cuyo trayecto pudiera aprovecharla.")


def benchmark(sizes: list[int] | None = None) -> None:
    if sizes is None:
        sizes = [80, 140, 220, 400]
    print_header("P02 - Benchmark Recalculo de 500 Vehiculos tras Cierre (con Floyd-Warshall y CH)")
    rows, fw_ref = [], None
    for n in sizes:
        r = run_closure_experiment(n)
        if n <= 220:
            fw_ms = best_of(lambda a=r["closed"]: floyd_warshall(a), repeat=1)[1]
            fw_ref = (n, fw_ms)
            fw_txt = f"{fw_ms:.0f} ms"
        else:
            fw_txt = f"~{fw_ref[1] * (n / fw_ref[0]) ** 3:.0f} ms (est. V^3)"
        rows.append([
            n, r["affected"],
            f"{r['t_dij']:.1f} ms ({r['exp_dij']})", f"{r['t_astar']:.1f} ms ({r['exp_astar']})",
            f"{r['t_aff']:.1f} ms", f"{r['ch_build']:.0f}+{r['ch_query']:.1f} ms", fw_txt,
        ])
    print_table(["V", "Afectados", "Dijkstra 500 (exp)", "A* 500 (exp)", "A* solo afectados", "CH build+query", "Floyd-Warshall"], rows)
    print("Lectura: A* expande menos nodos que Dijkstra; recalcular solo los afectados es la mayor ganancia; "
          "en Python el costo de evaluar la heuristica compensa el ahorro de nodos (el tiempo es similar); CH consulta rapido pero reconstruirla tras cada cierre cuesta mas que recalcular; Floyd-Warshall crece ~V^3.")
