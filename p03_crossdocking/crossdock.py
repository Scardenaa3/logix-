"""P03: Arquitectura de 3 flujos en Cross-Docking + indice hash + aging anti-inanicion (O(log n) por operacion)."""
from __future__ import annotations

import heapq
from collections import deque
from dataclasses import dataclass

from common.generators import make_rng
from common.metrics import print_header, print_table, run_timed

URGENT_SLACK = 5  # ticks: un perecedero/alto valor con deadline dentro de este margen se atiende ya


@dataclass
class PackageItem:
    pkg_id: str
    kind: str  # standard | perishable | high_value
    arrival_tick: int
    deadline_tick: int
    value_usd: float
    effective_tier: int = 2
    status: str = "queued"
    dispatch_tick: int = -1


class CrossDockRouter:
    """Estructuras:
    - standard    -> deque FIFO                      (enqueue/dequeue O(1))
    - perishable  -> min-heap EDF (deadline, seq)    (O(log n))
    - high_value  -> min-heap (tier, deadline, seq)  (O(log n)); tier 0 si valor >= 5000
    - aged        -> deque con los estandar que superaron el umbral de espera (aging); como la FIFO esta ordenada
                     por llegada, solo se revisa la CABEZA: promover es O(1) amortizado (antes era un recorrido O(n)).
    - index       -> dict id -> item (consulta/actualizacion O(1) promedio); eliminacion perezosa por 'status'.
    Politica: (a) HV critico o por vencer, (b) perecedero por vencer, (c) estandar envejecido, (d) EDF, (e) HV, (f) FIFO.
    """

    def __init__(self, aging_threshold: int | None = 25):
        self.fifo_standard: deque[PackageItem] = deque()
        self.aged: deque[PackageItem] = deque()
        self.edf_perishable: list[tuple[int, int, str]] = []
        self.hv_heap: list[tuple[int, int, int, str]] = []
        self.index: dict[str, PackageItem] = {}
        self._seq = 0
        self.aging_threshold = aging_threshold  # None => aging desactivado (para comparar)
        self.dispatched_waits: dict[str, list[int]] = {"standard": [], "perishable": [], "high_value": []}
        self.missed_deadlines: dict[str, int] = {"standard": 0, "perishable": 0, "high_value": 0}
        self.promoted = 0

    def enqueue(self, item: PackageItem) -> None:
        self._seq += 1
        self.index[item.pkg_id] = item
        if item.kind == "standard":
            self.fifo_standard.append(item)
        elif item.kind == "perishable":
            heapq.heappush(self.edf_perishable, (item.deadline_tick, self._seq, item.pkg_id))
        elif item.kind == "high_value":
            item.effective_tier = 0 if item.value_usd >= 5000 else 1
            heapq.heappush(self.hv_heap, (item.effective_tier, item.deadline_tick, self._seq, item.pkg_id))
        else:
            raise ValueError(f"Tipo desconocido: {item.kind}")

    def get_status(self, pkg_id: str) -> PackageItem | None:
        return self.index.get(pkg_id)

    def apply_aging(self, current_tick: int) -> int:
        """Mueve de la FIFO a 'aged' los estandar que esperan >= umbral. Solo mira la cabeza: O(1) amortizado."""
        if self.aging_threshold is None:
            return 0
        moved = 0
        while self.fifo_standard:
            head = self.fifo_standard[0]
            if head.status != "queued":
                self.fifo_standard.popleft()
                continue
            if current_tick - head.arrival_tick < self.aging_threshold:
                break
            self.fifo_standard.popleft()
            head.effective_tier = 1
            self.aged.append(head)
            moved += 1
        self.promoted += moved
        return moved

    @staticmethod
    def _top_valid(heap, index, id_pos):
        while heap:
            item = index.get(heap[0][id_pos])
            if item is not None and item.status == "queued":
                return item
            heapq.heappop(heap)
        return None

    def _pop_hv(self):
        item = self._top_valid(self.hv_heap, self.index, 3)
        if item:
            heapq.heappop(self.hv_heap)
        return item

    def _pop_edf(self):
        item = self._top_valid(self.edf_perishable, self.index, 2)
        if item:
            heapq.heappop(self.edf_perishable)
        return item

    @staticmethod
    def _pop_queue(q: deque):
        while q:
            item = q.popleft()
            if item.status == "queued":
                return item
        return None

    def dispatch_next(self, tick: int) -> PackageItem | None:
        self.apply_aging(tick)
        chosen = None
        hv = self._top_valid(self.hv_heap, self.index, 3)
        if hv and (hv.effective_tier == 0 or hv.deadline_tick <= tick + URGENT_SLACK):
            chosen = self._pop_hv()
        if chosen is None:
            pe = self._top_valid(self.edf_perishable, self.index, 2)
            if pe and pe.deadline_tick <= tick + URGENT_SLACK:
                chosen = self._pop_edf()
        if chosen is None:
            chosen = self._pop_queue(self.aged)
        if chosen is None:
            chosen = self._pop_edf()
        if chosen is None:
            chosen = self._pop_hv()
        if chosen is None:
            chosen = self._pop_queue(self.fifo_standard)
        if chosen is not None:
            chosen.status = "dispatched"
            chosen.dispatch_tick = tick
            self.dispatched_waits[chosen.kind].append(max(0, tick - chosen.arrival_tick))
            if tick > chosen.deadline_tick:
                self.missed_deadlines[chosen.kind] += 1
        return chosen


def simulate_band(n_items: int, aging_threshold: int | None = 20, seed: int = 42, load: float = 0.95,
                  priority_share: float = 0.4) -> CrossDockRouter:
    """3 llegadas por tick; la banda despacha un paquete por cada llegada salvo una fraccion (1-load).
    priority_share = fraccion de llegadas perecederas/alto valor (rafagas de trafico prioritario => riesgo de inanicion)."""
    rng = make_rng(seed)
    router = CrossDockRouter(aging_threshold=aging_threshold)
    n_pri = round(priority_share * 10)
    kinds = ["standard"] * (10 - n_pri) + ["perishable"] * (n_pri // 2) + ["high_value"] * (n_pri - n_pri // 2)
    skip_every = max(2, round(1.0 / max(1e-9, 1.0 - load)))
    for i in range(n_items):
        arr = i // 3
        k = rng.choice(kinds)
        dl = arr + (rng.randint(8, 22) if k != "standard" else rng.randint(40, 120))
        val = rng.uniform(6000, 25000) if k == "high_value" else rng.uniform(50, 1200)
        router.enqueue(PackageItem(f"PKG-{i:05d}", k, arr, dl, val))
        if i % skip_every != skip_every - 1:
            router.dispatch_next(arr)
    tick = n_items // 3 + 1
    while router.dispatch_next(tick) is not None:
        tick += 1
    return router


def _wait_stats(waits: list[int]) -> tuple[float, int]:
    return (sum(waits) / len(waits), max(waits)) if waits else (0.0, 0)


def demo() -> None:
    print_header("P03 - Cross-Docking (3 Flujos + Indice Hash + Aging O(1)): 80% de trafico prioritario")
    rows = []
    for label, thr in (("sin aging", None), ("con aging (umbral 15)", 15)):
        r = simulate_band(600, aging_threshold=thr, seed=42, load=0.9, priority_share=0.8)
        for kind in ("standard", "perishable", "high_value"):
            avg, mx = _wait_stats(r.dispatched_waits[kind])
            rows.append([label, kind, len(r.dispatched_waits[kind]), f"{avg:.1f}", mx, r.missed_deadlines[kind]])
    print_table(["Politica", "Flujo", "Despachados", "Espera prom (ticks)", "Espera max", "Deadlines vencidos"], rows)
    r = simulate_band(600, aging_threshold=15, seed=42)
    s = r.get_status("PKG-00010")
    print(f"Consulta O(1) por indice hash: PKG-00010 -> estado={s.status}, tipo={s.kind}, despachado en tick {s.dispatch_tick}")


def benchmark(sizes: list[int] | None = None) -> None:
    if sizes is None:
        sizes = [1000, 2000, 4000, 8000, 16000]
    print_header("P03 - Benchmark Simulacion Banda Cross-Docking (escalado)")
    rows, prev = [], None
    for n in sizes:
        m = run_timed(lambda n=n: simulate_band(n, aging_threshold=25, seed=42))
        avg, mx = _wait_stats(m.value.dispatched_waits["standard"])
        ratio = f"x{m.elapsed_ms / prev:.2f}" if prev else "-"
        prev = m.elapsed_ms
        rows.append([n, f"{m.elapsed_ms:.1f} ms", ratio, f"{m.peak_kb:.0f} KB", f"{avg:.1f} / {mx}", m.value.promoted])
    print_table(["Paquetes", "Tiempo total", "vs fila anterior", "Peak mem", "Espera std prom/max", "Promovidos (aging)"], rows)
    print("Lectura: al duplicar n el tiempo crece ~x2 (O(n log n) total), no ~x4: ya no hay recorrido O(n) por despacho.")
