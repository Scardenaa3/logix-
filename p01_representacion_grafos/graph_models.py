"""P01: Matriz de adyacencia, lista de adyacencia y grafo implicito en cuadricula."""
from __future__ import annotations

import heapq
import math

from common.generators import generate_sparse_road_graph
from common.metrics import best_of, print_header, print_table, run_timed

INF = float("inf")
FLOAT_BYTES = 8  # double de C: referencia teorica para extrapolar a redes reales


class AdjacencyMatrixGraph:
    """Representacion densa/matriz: espacio Theta(V^2), Dijkstra Theta(V^2)."""

    def __init__(self, n: int):
        self.n = n
        self.mat: list[list[float]] = [[INF] * n for _ in range(n)]
        for i in range(n):
            self.mat[i][i] = 0.0

    def add_undirected_edge(self, u: int, v: int, w: float) -> None:
        if w < self.mat[u][v]:
            self.mat[u][v] = w
            self.mat[v][u] = w

    def dijkstra(self, src: int) -> tuple[list[float], int]:
        dist = [INF] * self.n
        visited = [False] * self.n
        dist[src] = 0.0
        ops = 0
        for _ in range(self.n):
            u, best = -1, INF
            for i in range(self.n):
                ops += 1
                if not visited[i] and dist[i] < best:
                    best, u = dist[i], i
            if u == -1:
                break
            visited[u] = True
            row = self.mat[u]
            for v in range(self.n):
                ops += 1
                w = row[v]
                if not visited[v] and w != INF and dist[u] + w < dist[v]:
                    dist[v] = dist[u] + w
        return dist, ops


class AdjacencyListGraph:
    """Representacion dispersa: espacio Theta(V + E), Dijkstra con heap O((V+E) log V)."""

    def __init__(self, n: int):
        self.n = n
        self.adj: list[list[tuple[int, float]]] = [[] for _ in range(n)]

    def add_undirected_edge(self, u: int, v: int, w: float) -> None:
        self.adj[u].append((v, w))
        self.adj[v].append((u, w))

    def dijkstra(self, src: int) -> tuple[list[float], int]:
        dist = [INF] * self.n
        dist[src] = 0.0
        pq: list[tuple[float, int]] = [(0.0, src)]
        ops = 0
        while pq:
            d, u = heapq.heappop(pq)
            ops += 1
            if d > dist[u]:
                continue
            for v, w in self.adj[u]:
                ops += 1
                nd = d + w
                if nd < dist[v]:
                    dist[v] = nd
                    heapq.heappush(pq, (nd, v))
        return dist, ops


class ImplicitGridGraph:
    """Grafo implicito en malla rows x cols.

    NO almacena aristas ni pesos: los vecinos y el costo (incluido un peaje por regla)
    se calculan al vuelo desde (fila, columna). Memoria del grafo: O(1) (solo rows, cols);
    el algoritmo de camino minimo usa O(V) para dist, igual que con cualquier otra representacion.
    """

    def __init__(self, rows: int, cols: int, seed: int = 42):
        self.rows = rows
        self.cols = cols
        self.n = rows * cols
        self.seed = seed

    def _cell_cost(self, r: int, c: int) -> float:
        # Costo determinista por celda (congestion), sin tabla: funcion de (r, c, seed)
        return 0.8 + ((r * 31 + c * 17 + self.seed) % 8) * 0.1

    def _toll(self, r: int, c: int, nr: int, nc: int) -> float:
        # Regla de peaje: cruzar entre columnas multiplo de 10 cobra recargo
        return 1.5 if (c != nc and min(c, nc) % 10 == 9) else 0.0

    def neighbors(self, node: int) -> list[tuple[int, float]]:
        r, c = divmod(node, self.cols)
        res: list[tuple[int, float]] = []
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                w = (self._cell_cost(r, c) + self._cell_cost(nr, nc)) * 0.5 + self._toll(r, c, nr, nc)
                res.append((nr * self.cols + nc, round(w, 3)))
        return res

    def dijkstra(self, src: int) -> tuple[list[float], int]:
        dist = [INF] * self.n
        dist[src] = 0.0
        pq: list[tuple[float, int]] = [(0.0, src)]
        ops = 0
        while pq:
            d, u = heapq.heappop(pq)
            ops += 1
            if d > dist[u]:
                continue
            for v, w in self.neighbors(u):
                ops += 1
                nd = d + w
                if nd < dist[v]:
                    dist[v] = nd
                    heapq.heappush(pq, (nd, v))
        return dist, ops

    def to_list_graph(self) -> AdjacencyListGraph:
        """Materializa el grafo (para verificar que implicito == explicito)."""
        g = AdjacencyListGraph(self.n)
        for u in range(self.n):
            for v, w in self.neighbors(u):
                if u < v:
                    g.add_undirected_edge(u, v, w)
        return g


def _fill(graph, adj_data) -> None:
    for u, edges in enumerate(adj_data):
        for e in edges:
            if u < e.to:
                graph.add_undirected_edge(u, e.to, e.weight)


def demo() -> None:
    print_header("P01 - Representacion de Grafos Viales (Matriz vs Lista vs Implicito)")
    adj_data, _ = generate_sparse_road_graph(num_nodes=12, avg_degree=3.0, seed=42)
    lst_g, mat_g = AdjacencyListGraph(12), AdjacencyMatrixGraph(12)
    _fill(lst_g, adj_data)
    _fill(mat_g, adj_data)
    d_lst, ops_lst = lst_g.dijkstra(0)
    d_mat, ops_mat = mat_g.dijkstra(0)
    print(f"Red de 12 nodos | Lista: d(0->11)={d_lst[11]:.2f} (ops={ops_lst}) | Matriz: d(0->11)={d_mat[11]:.2f} (ops={ops_mat})")
    grid = ImplicitGridGraph(3, 4, seed=42)
    d_imp, ops_imp = grid.dijkstra(0)
    d_exp, _ = grid.to_list_graph().dijkstra(0)
    same = all(abs(a - b) < 1e-9 for a, b in zip(d_imp, d_exp))
    print(f"Malla 3x4 implicita | d(0->11)={d_imp[11]:.2f} (ops={ops_imp}) | identica a la version materializada: {same}")
    print(f"Teoria: con V=50,000 una matriz de doubles ocuparia {50000**2 * FLOAT_BYTES / 1e9:.0f} GB; "
          f"una lista con E=3V, ~{(50000 + 2 * 3 * 50000) * 16 / 1e6:.1f} MB.")


def benchmark(sizes: list[int] | None = None) -> None:
    if sizes is None:
        sizes = [100, 250, 500, 1000]
    print_header("P01 - Benchmark Memoria y Dijkstra (Red Dispersa E ~ 3V, mismo V en las 3 estructuras)")
    rows = []
    for n in sizes:
        adj_data, _ = generate_sparse_road_graph(num_nodes=n, avg_degree=3.0, seed=42)

        def build_list(n=n, a=adj_data):
            g = AdjacencyListGraph(n)
            _fill(g, a)
            return g

        def build_matrix(n=n, a=adj_data):
            g = AdjacencyMatrixGraph(n)
            _fill(g, a)
            return g

        m_lst, m_mat = run_timed(build_list), run_timed(build_matrix)
        _, d_lst = best_of(lambda: m_lst.value.dijkstra(0))
        _, d_mat = best_of(lambda: m_mat.value.dijkstra(0))

        side = max(2, math.isqrt(n))
        rows_g, cols_g = side, math.ceil(n / side)  # malla con V' >= n (V' - n < side)
        m_grd = run_timed(lambda: ImplicitGridGraph(rows_g, cols_g, seed=42))
        _, d_grd = best_of(lambda: m_grd.value.dijkstra(0))
        rows.append([
            n,
            f"{m_lst.peak_kb:.1f} KB", f"{d_lst:.3f} ms",
            f"{m_mat.peak_kb:.1f} KB", f"{d_mat:.3f} ms",
            f"{m_grd.peak_kb:.2f} KB", f"{d_grd:.3f} ms (V={rows_g * cols_g})",
        ])
    print_table(["V", "Lista mem", "Dij Lista", "Matriz mem", "Dij Matriz", "Implicito mem", "Dij Implicito"], rows)
    print("Lectura: la matriz crece ~V^2 en memoria y tiempo; lista e implicito crecen ~V. "
          "El implicito no guarda aristas (memoria ~constante) pero solo sirve si los vecinos se pueden calcular por regla.")
