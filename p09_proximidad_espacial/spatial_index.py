"""P09: k-NN espacial - Arbol KD, cuadricula exacta (anillos), indice Geohash real y fuerza bruta (verificador)."""
from __future__ import annotations

import heapq
import math
import time
from dataclasses import dataclass

from common.generators import make_rng
from common.metrics import print_header, print_table

KM_PER_DEG_LAT = 110.57
KM_PER_DEG_LON_EQ = 111.32
MED_LAT, MED_LON = 6.2442, -75.5812  # Medellin: origen del plano en km para el indice Geohash


@dataclass
class Courier:
    courier_id: str
    x: float  # km (este)
    y: float  # km (norte)
    available: bool = True


def _dist2(ax: float, ay: float, bx: float, by: float) -> float:
    dx, dy = ax - bx, ay - by
    return dx * dx + dy * dy


def brute_force_knn(couriers: list[Courier], qx: float, qy: float, k: int = 3) -> list[tuple[float, str]]:
    items = [(math.sqrt(_dist2(c.x, c.y, qx, qy)), c.courier_id) for c in couriers if c.available]
    items.sort()
    return items[:k]


# ============================================================================ KD-Tree
@dataclass
class _KdNode:
    courier: Courier
    axis: int
    left: _KdNode | None = None
    right: _KdNode | None = None


class KDTree2D:
    """KD estatico 2D: construccion O(n log n); k-NN ~O(log n + k) con poda; no soporta movimiento (se reconstruye)."""

    def __init__(self, couriers: list[Courier]):
        self.root = self._build([c for c in couriers if c.available], 0)

    def _build(self, pts: list[Courier], depth: int) -> _KdNode | None:
        if not pts:
            return None
        axis = depth % 2
        pts.sort(key=(lambda c: c.x) if axis == 0 else (lambda c: c.y))
        mid = len(pts) // 2
        return _KdNode(pts[mid], axis, self._build(pts[:mid], depth + 1), self._build(pts[mid + 1:], depth + 1))

    def knn(self, qx: float, qy: float, k: int = 3) -> list[tuple[float, str]]:
        heap: list[tuple[float, str]] = []  # max-heap simulado con distancias negativas

        def search(node: _KdNode | None) -> None:
            if node is None:
                return
            d2 = _dist2(node.courier.x, node.courier.y, qx, qy)
            if len(heap) < k:
                heapq.heappush(heap, (-d2, node.courier.courier_id))
            elif d2 < -heap[0][0]:
                heapq.heapreplace(heap, (-d2, node.courier.courier_id))
            diff = (qx - node.courier.x) if node.axis == 0 else (qy - node.courier.y)
            near, far = (node.left, node.right) if diff < 0 else (node.right, node.left)
            search(near)
            if len(heap) < k or diff * diff <= -heap[0][0]:
                search(far)

        search(self.root)
        return sorted((math.sqrt(-nd2), cid) for nd2, cid in heap)


# ============================================================================ Cuadricula exacta
class SpatialGridIndex:
    """Cuadricula uniforme (hash de celdas). Actualizacion O(1). k-NN EXACTO: se exploran anillos de celdas hasta que
    el k-esimo candidato queda mas cerca que la distancia minima al siguiente anillo (r * cell_size).
    Con una sola ventana 3x3 el resultado puede ser incorrecto cuando el k-esimo vecino esta a mas de 1 celda."""

    def __init__(self, cell_size: float = 2.0):
        self.cell_size = cell_size
        self.cells: dict[tuple[int, int], dict[str, Courier]] = {}
        self.courier_cell: dict[str, tuple[int, int]] = {}
        self._minx = self._miny = 10**9
        self._maxx = self._maxy = -10**9

    def _cell_of(self, x: float, y: float) -> tuple[int, int]:
        return math.floor(x / self.cell_size), math.floor(y / self.cell_size)

    def upsert(self, c: Courier) -> None:
        new_cell = self._cell_of(c.x, c.y)
        old_cell = self.courier_cell.get(c.courier_id)
        if old_cell == new_cell:
            self.cells[new_cell][c.courier_id] = c
            return
        if old_cell is not None:
            bucket = self.cells[old_cell]
            del bucket[c.courier_id]
            if not bucket:
                del self.cells[old_cell]
        self.cells.setdefault(new_cell, {})[c.courier_id] = c
        self.courier_cell[c.courier_id] = new_cell
        self._minx, self._maxx = min(self._minx, new_cell[0]), max(self._maxx, new_cell[0])
        self._miny, self._maxy = min(self._miny, new_cell[1]), max(self._maxy, new_cell[1])

    def remove(self, courier_id: str) -> None:
        cell = self.courier_cell.pop(courier_id, None)
        if cell is not None:
            bucket = self.cells[cell]
            del bucket[courier_id]
            if not bucket:
                del self.cells[cell]

    @staticmethod
    def _ring(cx: int, cy: int, r: int):
        if r == 0:
            yield cx, cy
            return
        for dx in range(-r, r + 1):
            yield cx + dx, cy - r
            yield cx + dx, cy + r
        for dy in range(-r + 1, r):
            yield cx - r, cy + dy
            yield cx + r, cy + dy

    def knn(self, qx: float, qy: float, k: int = 3) -> list[tuple[float, str]]:
        if not self.cells:
            return []
        cx, cy = self._cell_of(qx, qy)
        max_r = max(abs(cx - self._minx), abs(cx - self._maxx), abs(cy - self._miny), abs(cy - self._maxy))
        cands: list[tuple[float, str]] = []
        r = 0
        while True:
            for cell in self._ring(cx, cy, r):
                bucket = self.cells.get(cell)
                if bucket:
                    for c in bucket.values():
                        if c.available:
                            cands.append((math.sqrt(_dist2(c.x, c.y, qx, qy)), c.courier_id))
            if len(cands) >= k:
                cands = heapq.nsmallest(k, cands)
                if cands[-1][0] <= r * self.cell_size:
                    break
            if r >= max_r:
                break
            r += 1
        return sorted(heapq.nsmallest(k, cands))


# ============================================================================ Geohash real
_B32 = "0123456789bcdefghjkmnpqrstuvwxyz"


def geohash_encode(lat: float, lon: float, precision: int = 6) -> str:
    lat_lo, lat_hi, lon_lo, lon_hi = -90.0, 90.0, -180.0, 180.0
    out, bit, ch, even = [], 0, 0, True
    while len(out) < precision:
        if even:
            mid = (lon_lo + lon_hi) / 2
            if lon >= mid:
                ch = (ch << 1) | 1
                lon_lo = mid
            else:
                ch <<= 1
                lon_hi = mid
        else:
            mid = (lat_lo + lat_hi) / 2
            if lat >= mid:
                ch = (ch << 1) | 1
                lat_lo = mid
            else:
                ch <<= 1
                lat_hi = mid
        even = not even
        bit += 1
        if bit == 5:
            out.append(_B32[ch])
            bit, ch = 0, 0
    return "".join(out)


class GeohashIndex:
    """Celdas identificadas por cadenas Geohash de 'precision' caracteres (prefijo comun = cercania).
    Coordenadas de los mensajeros en km sobre un plano local centrado en (lat0, lon0); se convierten a lat/lon para codificar.
    k-NN exacto con expansion en anillos de celdas (los vecinos de una celda se obtienen codificando el centro de la celda
    desplazada), lo que cubre el 'efecto borde' del geohash."""

    def __init__(self, precision: int = 6, lat0: float = MED_LAT, lon0: float = MED_LON):
        self.p, self.lat0, self.lon0 = precision, lat0, lon0
        bits = 5 * precision
        self.dlon = 360.0 / (1 << ((bits + 1) // 2))
        self.dlat = 180.0 / (1 << (bits // 2))
        self.kx = KM_PER_DEG_LON_EQ * math.cos(math.radians(lat0))
        self.ky = KM_PER_DEG_LAT
        self.cell_km = min(self.dlon * self.kx, self.dlat * self.ky)  # cota inferior segura por anillo
        self.cells: dict[str, dict[str, Courier]] = {}
        self.courier_cell: dict[str, str] = {}
        self._r_max = 0

    def _latlon(self, x: float, y: float) -> tuple[float, float]:
        return self.lat0 + y / self.ky, self.lon0 + x / self.kx

    def _idx(self, x: float, y: float) -> tuple[int, int]:
        lat, lon = self._latlon(x, y)
        return math.floor((lon + 180.0) / self.dlon), math.floor((lat + 90.0) / self.dlat)

    def _key_of_idx(self, ix: int, iy: int) -> str:
        return geohash_encode(-90.0 + (iy + 0.5) * self.dlat, -180.0 + (ix + 0.5) * self.dlon, self.p)

    def key_of(self, x: float, y: float) -> str:
        lat, lon = self._latlon(x, y)
        return geohash_encode(lat, lon, self.p)

    def upsert(self, c: Courier) -> None:
        key = self.key_of(c.x, c.y)
        old = self.courier_cell.get(c.courier_id)
        if old == key:
            self.cells[key][c.courier_id] = c
            return
        if old is not None:
            bucket = self.cells[old]
            del bucket[c.courier_id]
            if not bucket:
                del self.cells[old]
        self.cells.setdefault(key, {})[c.courier_id] = c
        self.courier_cell[c.courier_id] = key

    def knn(self, qx: float, qy: float, k: int = 3) -> list[tuple[float, str]]:
        if not self.cells:
            return []
        ix, iy = self._idx(qx, qy)
        total = sum(len(b) for b in self.cells.values())
        cands: list[tuple[float, str]] = []
        r, seen = 0, 0
        while True:
            for cx, cy in SpatialGridIndex._ring(ix, iy, r):
                bucket = self.cells.get(self._key_of_idx(cx, cy))
                if bucket:
                    for c in bucket.values():
                        seen += 1
                        if c.available:
                            cands.append((math.sqrt(_dist2(c.x, c.y, qx, qy)), c.courier_id))
            if len(cands) >= k:
                cands = heapq.nsmallest(k, cands)
                if cands[-1][0] <= r * self.cell_km:
                    break
            if seen >= total or r > 400:
                break
            r += 1
        return sorted(heapq.nsmallest(k, cands))


# ============================================================================ utilidades de simulacion
def make_fleet(n: int, side_km: float, rng) -> list[Courier]:
    return [Courier(f"M-{i:05d}", rng.uniform(0, side_km), rng.uniform(0, side_km)) for i in range(n)]


def move_fleet(fleet: list[Courier], side_km: float, rng, step: float = 0.4) -> None:
    for c in fleet:
        c.x = max(0.0, min(side_km, c.x + rng.uniform(-step, step)))
        c.y = max(0.0, min(side_km, c.y + rng.uniform(-step, step)))


def check_parity(n: int = 300, queries: int = 300, k: int = 5, side: float = 30.0, seed: int = 7) -> dict[str, int]:
    """Cuenta consultas donde cada indice difiere de la fuerza bruta (debe ser 0 en todos)."""
    rng = make_rng(seed)
    fleet = make_fleet(n, side, rng)
    kd, grid, geo = KDTree2D(fleet), SpatialGridIndex(2.0), GeohashIndex(6)
    for c in fleet:
        grid.upsert(c)
        geo.upsert(c)
    bad = {"kd": 0, "grid": 0, "geohash": 0}
    for _ in range(queries):
        qx, qy = rng.uniform(0, side), rng.uniform(0, side)
        ref = [i for _, i in brute_force_knn(fleet, qx, qy, k)]
        bad["kd"] += [i for _, i in kd.knn(qx, qy, k)] != ref
        bad["grid"] += [i for _, i in grid.knn(qx, qy, k)] != ref
        bad["geohash"] += [i for _, i in geo.knn(qx, qy, k)] != ref
    return bad


def demo() -> None:
    print_header("P09 - Proximidad Espacial: KD-Tree vs Cuadricula vs Geohash vs Fuerza Bruta")
    rng = make_rng(42)
    fleet = make_fleet(60, 20.0, rng)
    kd, grid, geo = KDTree2D(fleet), SpatialGridIndex(2.5), GeohashIndex(6)
    for c in fleet:
        grid.upsert(c)
        geo.upsert(c)
    qx, qy = 10.0, 10.0
    print(f"Consulta ({qx}, {qy}) km, k=3 | geohash de la consulta: {geo.key_of(qx, qy)} (celda ~{geo.dlon * geo.kx:.2f} x {geo.dlat * geo.ky:.2f} km)")
    for name, res in (("Fuerza bruta", brute_force_knn(fleet, qx, qy, 3)), ("KD-Tree", kd.knn(qx, qy, 3)),
                      ("Cuadricula", grid.knn(qx, qy, 3)), ("Geohash", geo.knn(qx, qy, 3))):
        print(f"  {name:13s}: {[(cid, round(d, 2)) for d, cid in res]}")
    bad = check_parity()
    print(f"Paridad con fuerza bruta en 300 consultas aleatorias (300 mensajeros, k=5): fallos {bad}")


def benchmark(sizes: list[int] | None = None) -> None:
    side = 30.0
    print_header("P09 - Consulta estatica k=5: construccion y tiempo por consulta (us)")
    rows = []
    for n in sizes or [1000, 5000]:
        rng = make_rng(1)
        fleet = make_fleet(n, side, rng)
        qs = [(rng.uniform(0, side), rng.uniform(0, side)) for _ in range(300)]
        t0 = time.perf_counter(); kd = KDTree2D(fleet); b_kd = (time.perf_counter() - t0) * 1000
        t0 = time.perf_counter()
        grid, geo = SpatialGridIndex(2.0), GeohashIndex(6)
        for c in fleet:
            grid.upsert(c)
        b_grid = (time.perf_counter() - t0) * 1000
        t0 = time.perf_counter()
        for c in fleet:
            geo.upsert(c)
        b_geo = (time.perf_counter() - t0) * 1000
        def per_q(f):
            t0 = time.perf_counter()
            for qx, qy in qs:
                f(qx, qy, 5)
            return (time.perf_counter() - t0) / len(qs) * 1e6
        rows.append([n, f"{b_kd:.1f} / {per_q(kd.knn):.0f}", f"{b_grid:.1f} / {per_q(grid.knn):.0f}",
                     f"{b_geo:.1f} / {per_q(geo.knn):.0f}", f"- / {per_q(lambda x, y, k: brute_force_knn(fleet, x, y, k)):.0f}"])
    print_table(["Mensajeros", "KD build ms / us por consulta", "Cuadricula", "Geohash", "Fuerza bruta"], rows)

    print_header("P09 - Flota movil: costo de UN tick (todos se mueven + Q consultas k=5), n=2000")
    n = 2000
    rows = []
    for q_per_tick in (1, 20, 200, 1000):
        res = {}
        for name in ("KD (reconstruir)", "Cuadricula (actualizar)", "Geohash (actualizar)", "Fuerza bruta"):
            rng = make_rng(3)
            fleet = make_fleet(n, side, rng)
            grid, geo = SpatialGridIndex(2.0), GeohashIndex(6)
            for c in fleet:
                grid.upsert(c)
                geo.upsert(c)
            qs = [(rng.uniform(0, side), rng.uniform(0, side)) for _ in range(q_per_tick)]
            best = float("inf")
            for _ in range(3):
                move_fleet(fleet, side, rng)
                t0 = time.perf_counter()
                if name.startswith("KD"):
                    idx = KDTree2D(fleet)
                    for qx, qy in qs:
                        idx.knn(qx, qy, 5)
                elif name.startswith("Cuad"):
                    for c in fleet:
                        grid.upsert(c)
                    for qx, qy in qs:
                        grid.knn(qx, qy, 5)
                elif name.startswith("Geo"):
                    for c in fleet:
                        geo.upsert(c)
                    for qx, qy in qs:
                        geo.knn(qx, qy, 5)
                else:
                    for qx, qy in qs:
                        brute_force_knn(fleet, qx, qy, 5)
                best = min(best, (time.perf_counter() - t0) * 1000)
            res[name] = best
        winner = min(res, key=res.get)
        rows.append([q_per_tick, *(f"{res[k]:.1f} ms" for k in res), winner])
    print_table(["Consultas/tick", "KD (reconstruir)", "Cuadricula", "Geohash", "Fuerza bruta", "Mas rapido"], rows)
    print("Lectura: con 1 consulta por tick, ni siquiera conviene indexar (la fuerza bruta evita el costo de mantener el indice); con pocas, actualizar celdas (O(1) por agente) vence a reconstruir el KD (O(n log n)); "
          "con muchas consultas por tick, la reconstruccion se amortiza y el KD (consulta ~O(log n)) alcanza o supera a las cuadriculas.")
