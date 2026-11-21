"""P04: Tablas hash propias (FNV-1a y Polinomica): encadenamiento, direccionamiento abierto, borrado, rehash y sharding."""
from __future__ import annotations

import math
import time
from dataclasses import dataclass

from common.generators import generate_tracking_codes
from common.metrics import print_header, print_table, run_timed


def hash_fnv1a(key: str) -> int:
    h = 2166136261
    for ch in key.encode("utf-8"):
        h ^= ch
        h = (h * 16777619) & 0xFFFFFFFF
    return h


def hash_polynomial(key: str, base: int = 131) -> int:
    h = 0
    for ch in key.encode("utf-8"):
        h = (h * base + ch) & 0xFFFFFFFFFFFFFFFF
    return h


def next_prime(n: int) -> int:
    n = max(2, n)
    while True:
        if n < 4 or all(n % d for d in range(2, math.isqrt(n) + 1)):
            return n
        n += 1


@dataclass
class LookupStats:
    found: bool
    probes: int
    collisions: int


class ChainedHashTable:
    """Encadenamiento separado. Soporta alpha >= 1; rehash opcional al superar max_load."""

    def __init__(self, capacity: int = 1024, hash_fn=hash_fnv1a, max_load: float | None = None):
        self.capacity = max(8, capacity)
        self.hash_fn = hash_fn
        self.max_load = max_load
        self.buckets: list[list[tuple[str, str]]] = [[] for _ in range(self.capacity)]
        self.size = 0
        self.total_insert_collisions = 0
        self.rehashes = 0

    @property
    def load_factor(self) -> float:
        return self.size / self.capacity

    def _rehash(self) -> None:
        old = self.buckets
        self.capacity = next_prime(self.capacity * 2)
        self.buckets = [[] for _ in range(self.capacity)]
        for bucket in old:
            for k, v in bucket:
                self.buckets[self.hash_fn(k) % self.capacity].append((k, v))
        self.rehashes += 1

    def insert(self, key: str, value: str) -> int:
        if self.max_load is not None and (self.size + 1) / self.capacity > self.max_load:
            self._rehash()
        bucket = self.buckets[self.hash_fn(key) % self.capacity]
        for i, (k, _) in enumerate(bucket):
            if k == key:
                bucket[i] = (key, value)
                return 1
        if bucket:
            self.total_insert_collisions += 1
        bucket.append((key, value))
        self.size += 1
        return len(bucket)

    def get(self, key: str) -> LookupStats:
        bucket = self.buckets[self.hash_fn(key) % self.capacity]
        probes = 0
        for k, _ in bucket:
            probes += 1
            if k == key:
                return LookupStats(True, probes, probes - 1)
        return LookupStats(False, max(1, probes), max(0, probes - 1))

    def delete(self, key: str) -> bool:
        bucket = self.buckets[self.hash_fn(key) % self.capacity]
        for i, (k, _) in enumerate(bucket):
            if k == key:
                bucket.pop(i)
                self.size -= 1
                return True
        return False


class OpenAddressingHashTable:
    """Direccionamiento abierto: 'linear', 'quadratic' o 'double'.
    La capacidad se redondea a un PRIMO: con doble hash garantiza que h2 sea coprimo con la capacidad
    (el sondeo visita todas las celdas) y con sondeo cuadratico garantiza hallar hueco mientras alpha < 0.5.
    Borrado con lapidas (tombstones); rehash automatico opcional al superar max_load (cuenta lapidas)."""

    _DELETED = object()

    def __init__(self, capacity: int = 1024, mode: str = "double", hash_fn=hash_fnv1a, max_load: float | None = None):
        if mode not in ("linear", "quadratic", "double"):
            raise ValueError(f"Modo desconocido: {mode}")
        self.capacity = next_prime(max(16, capacity))
        self.mode = mode
        self.hash_fn = hash_fn
        self.max_load = max_load
        self.keys: list[object] = [None] * self.capacity
        self.values: list[object] = [None] * self.capacity
        self.size = 0
        self.tombstones = 0
        self.total_probes = 0
        self.collisions = 0
        self.rehashes = 0

    @property
    def load_factor(self) -> float:
        return self.size / self.capacity

    def _slot(self, key: str, i: int, h1: int, h2: int) -> int:
        if self.mode == "linear":
            return (h1 + i) % self.capacity
        if self.mode == "quadratic":
            return (h1 + i * i) % self.capacity
        return (h1 + i * h2) % self.capacity

    def _h2(self, key: str) -> int:
        return 1 + (hash_polynomial(key, 137) % (self.capacity - 1)) if self.mode == "double" else 0

    def _rehash(self) -> None:
        old = list(zip(self.keys, self.values))
        self.capacity = next_prime(self.capacity * 2)
        self.keys, self.values = [None] * self.capacity, [None] * self.capacity
        self.size = self.tombstones = 0
        for k, v in old:
            if k is not None and k is not self._DELETED:
                self.insert(k, v)  # type: ignore[arg-type]
        self.rehashes += 1

    def insert(self, key: str, value: str) -> int:
        if self.max_load is not None and (self.size + self.tombstones + 1) / self.capacity > self.max_load:
            self._rehash()
        h1, h2 = self.hash_fn(key) % self.capacity, self._h2(key)
        first_tombstone: int | None = None
        probes = 0
        for i in range(self.capacity):
            probes += 1
            slot = self._slot(key, i, h1, h2)
            k = self.keys[slot]
            if k is None:
                target = first_tombstone if first_tombstone is not None else slot
                if first_tombstone is not None:
                    self.tombstones -= 1
                self.keys[target], self.values[target] = key, value
                self.size += 1
                self.total_probes += probes
                if i > 0:
                    self.collisions += 1
                return probes
            if k is self._DELETED:
                if first_tombstone is None:
                    first_tombstone = slot
            elif k == key:
                self.values[slot] = value
                self.total_probes += probes
                return probes
        if first_tombstone is not None:
            self.keys[first_tombstone], self.values[first_tombstone] = key, value
            self.tombstones -= 1
            self.size += 1
            return probes
        raise OverflowError("Sin slot libre en la secuencia de sondeo (alpha demasiado alto para este esquema)")

    def _find(self, key: str) -> tuple[int, int]:
        h1, h2 = self.hash_fn(key) % self.capacity, self._h2(key)
        probes = 0
        for i in range(self.capacity):
            probes += 1
            slot = self._slot(key, i, h1, h2)
            k = self.keys[slot]
            if k is None:
                return -1, probes
            if k is not self._DELETED and k == key:
                return slot, probes
        return -1, probes

    def get(self, key: str) -> LookupStats:
        slot, probes = self._find(key)
        return LookupStats(slot >= 0, probes, probes - 1)

    def delete(self, key: str) -> bool:
        slot, _ = self._find(key)
        if slot < 0:
            return False
        self.keys[slot], self.values[slot] = self._DELETED, None
        self.size -= 1
        self.tombstones += 1
        return True


class ShardedIndex:
    """S tablas independientes; el shard se elige con un hash distinto al del bucket (evita correlacion).
    Permite repartir nodos/hilos y limitar el tamano (y el costo de un rehash) de cada tabla."""

    def __init__(self, shards: int = 8, capacity_per_shard: int = 4096, kind: str = "chained"):
        self.shards = shards
        mk = (lambda: ChainedHashTable(capacity_per_shard, max_load=1.0)) if kind == "chained" else \
             (lambda: OpenAddressingHashTable(capacity_per_shard, "double", max_load=0.7))
        self.tables = [mk() for _ in range(shards)]

    def _t(self, key: str):
        return self.tables[(hash_polynomial(key) >> 20) % self.shards]

    def insert(self, key: str, value: str) -> int:
        return self._t(key).insert(key, value)

    def get(self, key: str) -> LookupStats:
        return self._t(key).get(key)

    def delete(self, key: str) -> bool:
        return self._t(key).delete(key)

    def shard_sizes(self) -> list[int]:
        return [t.size for t in self.tables]


# --------------------------------------------------------------------------- teoria (busqueda exitosa)
def theory_probes(kind: str, a: float) -> float:
    if kind == "chained":
        return 1 + a / 2
    if kind == "linear":
        return 0.5 * (1 + 1 / (1 - a))
    if kind == "quadratic":
        return 1 - math.log(1 - a) - a / 2
    return (1 / a) * math.log(1 / (1 - a))


def _absent_keys(count: int) -> list[str]:
    return [f"ZZ-{i:06d}-XXX" for i in range(count)]


def demo() -> None:
    print_header("P04 - Indexacion de Guias (LX-94820-MED): borrado, rehash y sharding")
    codes = generate_tracking_codes(400, seed=42)
    tbl = OpenAddressingHashTable(capacity=1009, mode="double", hash_fn=hash_fnv1a)
    for c in codes:
        tbl.insert(c, "EN_TRANSITO_HUB_MED")
    st = tbl.get(codes[0])
    print(f"Guia {codes[0]} | alpha={tbl.load_factor:.2f} | encontrada={st.found} | sondas={st.probes} | capacidad primo={tbl.capacity}")
    tbl.delete(codes[0])
    print(f"Tras delete: encontrada={tbl.get(codes[0]).found} | otra guia sigue visible={tbl.get(codes[1]).found} | lapidas={tbl.tombstones}")
    grow = OpenAddressingHashTable(capacity=16, mode="double", max_load=0.7)
    for c in codes:
        grow.insert(c, "OK")
    print(f"Rehash automatico (alpha<=0.7): 400 guias desde capacidad 16 -> capacidad {grow.capacity}, rehashes={grow.rehashes}, alpha={grow.load_factor:.2f}")
    sh = ShardedIndex(shards=8)
    for c in generate_tracking_codes(20000, seed=7):
        sh.insert(c, "OK")
    sizes = sh.shard_sizes()
    print(f"Sharding x8 con 20,000 guias: tamanos {sizes} (desbalance max/min = {max(sizes) / min(sizes):.2f})")
    print("Escala LogiX: 20,000,000 consultas/dia = ~231.5 req/s promedio; con picos 5x-15x -> ~1,200-3,500 req/s.")


def benchmark(sizes: list[int] | None = None) -> None:
    cap = 10007
    alphas = sizes or [30, 50, 70, 90, 95]
    print_header(f"P04 - Sondas por busqueda vs alpha (capacidad primo {cap}) - medido vs teoria")
    rows = []
    absent = _absent_keys(2000)
    for a_pct in alphas:
        n = int(cap * a_pct / 100)
        codes = generate_tracking_codes(n, seed=42)
        for kind in ("chained", "linear", "quadratic", "double"):
            tbl = ChainedHashTable(cap) if kind == "chained" else OpenAddressingHashTable(cap, kind)
            failed = 0
            inserted = []
            for c in codes:
                try:
                    tbl.insert(c, "OK")
                    inserted.append(c)
                except OverflowError:
                    failed += 1
            ok = sum(tbl.get(c).probes for c in inserted) / max(1, len(inserted))
            miss = sum(tbl.get(c).probes for c in absent) / len(absent)
            rows.append([f"{a_pct / 100:.2f}", kind, f"{ok:.2f}", f"{theory_probes(kind, a_pct / 100):.2f}", f"{miss:.2f}", failed])
    print_table(["alpha", "Esquema", "Sondas exito (medido)", "Sondas exito (teoria)", "Sondas fallo", "Inserciones fallidas"], rows)

    print_header("P04 - Funcion hash: FNV-1a vs polinomica (encadenamiento, alpha=0.7, memoria con tracemalloc)")
    n = int(cap * 0.7)
    codes = generate_tracking_codes(n, seed=42)
    rows = []
    for name, fn in (("FNV-1a", hash_fnv1a), ("Polinomica b=131", hash_polynomial)):
        m = run_timed(lambda fn=fn: _build_chained(cap, codes, fn))
        t = m.value
        longest = max(len(b) for b in t.buckets)
        empty = sum(1 for b in t.buckets if not b) / cap
        avg = sum(t.get(c).probes for c in codes) / n
        rows.append([name, longest, f"{empty * 100:.1f}% (ideal {math.exp(-0.7) * 100:.1f}%)", f"{avg:.2f}", f"{m.peak_kb:.0f} KB"])
    for kind in ("linear", "double"):
        m = run_timed(lambda kind=kind: _build_oa(cap, codes, kind))
        t = m.value
        rows.append([f"OA {kind} (FNV-1a)", "-", "-", f"{sum(t.get(c).probes for c in codes) / n:.2f}", f"{m.peak_kb:.0f} KB"])
    print_table(["Estructura/Hash", "Cadena mas larga", "Buckets vacios", "Sondas exito", "Memoria pico"], rows)

    print_header("P04 - Rendimiento a escala: 100,000 guias, 100,000 consultas (alpha=0.7 en direccionamiento abierto)")
    big = generate_tracking_codes(100000, seed=11)
    rows = []
    for label, mk in (("Encadenamiento (max_load=1.0)", lambda: ChainedHashTable(1024, max_load=1.0)),
                      ("Abierto doble hash (max_load=0.7)", lambda: OpenAddressingHashTable(1024, "double", max_load=0.7)),
                      ("Sharded x8 encadenado", lambda: ShardedIndex(8, 4096))):
        t = mk()
        t0 = time.perf_counter()
        for c in big:
            t.insert(c, "OK")
        t_ins = time.perf_counter() - t0
        t0 = time.perf_counter()
        hits = sum(1 for c in big if t.get(c).found)
        t_q = time.perf_counter() - t0
        rows.append([label, f"{t_ins * 1000:.0f} ms", f"{t_q * 1000:.0f} ms", f"{len(big) / t_q:,.0f} consultas/s", hits])
    print_table(["Estructura", "Insertar 100k", "100k consultas", "Rendimiento", "Aciertos"], rows)
    print("Referencia: promedio 231.5 req/s, picos ~3,500 req/s -> una sola tabla en memoria (en Python) ya cubre el pico con holgura.")


def _build_chained(cap, codes, fn):
    t = ChainedHashTable(cap, hash_fn=fn)
    for c in codes:
        t.insert(c, "OK")
    return t


def _build_oa(cap, codes, kind):
    t = OpenAddressingHashTable(cap, kind)
    for c in codes:
        t.insert(c, "OK")
    return t
