"""P05: Arbol N-ario con puntero al padre (Contenedor -> Pallet -> Caja Master -> Paquete) e inspeccion aduanera."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from common.metrics import best_of, print_header, print_table, run_timed


@dataclass
class PackNode:
    node_id: str
    level: str
    parent: PackNode | None = None
    children: list[PackNode] = field(default_factory=list)

    def add_child(self, child: PackNode) -> None:
        child.parent = self
        self.children.append(child)


def dfs_find(root: PackNode, target_id: str) -> tuple[bool, int]:
    """DFS iterativo con pila. Espacio: O(h * b) (la pila guarda hermanos pendientes); tiempo O(n) en el peor caso."""
    visited, stack = 0, [root]
    while stack:
        node = stack.pop()
        visited += 1
        if node.node_id == target_id:
            return True, visited
        stack.extend(reversed(node.children))
    return False, visited


def bfs_find(root: PackNode, target_id: str) -> tuple[bool, int]:
    """BFS con cola. Espacio: O(ancho maximo); tiempo O(n) en el peor caso."""
    visited, q = 0, deque([root])
    while q:
        node = q.popleft()
        visited += 1
        if node.node_id == target_id:
            return True, visited
        q.extend(node.children)
    return False, visited


def verify_package_in_container_upward(pkg: PackNode, container: PackNode) -> tuple[bool, int]:
    """Ascenso por punteros al padre: O(h) = O(4) = O(1) en la jerarquia fija; espacio O(1)."""
    steps, cur = 0, pkg
    while cur is not None:
        steps += 1
        if cur is container:
            return True, steps
        cur = cur.parent
    return False, steps


def build_hierarchy(num_pallets: int, boxes_per_pallet: int, pkgs_per_box: int, cid: str = "CONT-001") -> tuple[PackNode, dict[str, PackNode]]:
    root = PackNode(cid, "container")
    index: dict[str, PackNode] = {root.node_id: root}
    for p in range(num_pallets):
        pallet = PackNode(f"{cid}/PAL-{p:03d}", "pallet")
        root.add_child(pallet)
        index[pallet.node_id] = pallet
        for b in range(boxes_per_pallet):
            box = PackNode(f"{cid}/BOX-{p:03d}-{b:03d}", "box")
            pallet.add_child(box)
            index[box.node_id] = box
            for k in range(pkgs_per_box):
                pkg = PackNode(f"PKG-{cid[-3:]}-{p:03d}-{b:03d}-{k:03d}", "package")
                box.add_child(pkg)
                index[pkg.node_id] = pkg
    return root, index


def build_fleet(num_containers: int, pallets: int, boxes: int, pkgs: int) -> tuple[dict[str, PackNode], dict[str, PackNode]]:
    """Varios contenedores + indice hash GLOBAL id -> nodo (para ubicar el paquete en O(1) promedio)."""
    containers: dict[str, PackNode] = {}
    index: dict[str, PackNode] = {}
    for c in range(num_containers):
        root, idx = build_hierarchy(pallets, boxes, pkgs, cid=f"CONT-{c + 1:03d}")
        containers[root.node_id] = root
        index.update(idx)
    return containers, index


def customs_check(index: dict[str, PackNode], pkg_id: str, container_id: str) -> tuple[bool, int]:
    """Inspeccion aduanera: ubica el paquete por hash (O(1)) y sube por padres (O(h)). Total O(1) acotado."""
    node = index.get(pkg_id)
    cont = index.get(container_id)
    if node is None or cont is None:
        return False, 0
    return verify_package_in_container_upward(node, cont)


def demo() -> None:
    print_header("P05 - Jerarquia N-aria: inspeccion aduanera (DFS vs BFS vs indice + ascenso por padre)")
    containers, index = build_fleet(3, 3, 4, 5)
    pkg = "PKG-001-002-003-004"
    c1, c2 = containers["CONT-001"], containers["CONT-002"]
    rows = []
    for label, cont in (("CONT-001 (contiene el paquete)", c1), ("CONT-002 (NO lo contiene)", c2)):
        fd, vd = dfs_find(cont, pkg)
        fb, vb = bfs_find(cont, pkg)
        fu, su = customs_check(index, pkg, cont.node_id)
        rows.append([label, f"{fd} ({vd} nodos)", f"{fb} ({vb} nodos)", f"{fu} ({su} pasos)"])
    print(f"Paquete inspeccionado: {pkg}")
    print_table(["Contenedor consultado", "DFS", "BFS", "Hash + ascenso por padre"], rows)
    print("El caso negativo es el peor para DFS/BFS: recorren TODO el contenedor; el ascenso por padre sigue en <= 4 pasos.")


def benchmark(sizes: list[int] | None = None) -> None:
    if sizes is None:
        sizes = [4, 8, 16, 32]
    print_header("P05 - Benchmark inspeccion aduanera (peor caso: paquete ausente o ultimo del contenedor)")
    rows = []
    for pallets in sizes:
        containers, index = build_fleet(2, pallets, 5, 10)
        c1, c2 = containers["CONT-001"], containers["CONT-002"]
        last = f"PKG-001-{pallets - 1:03d}-004-009"
        nodes_c = sum(1 for k in index if k.startswith(("CONT-001", "PKG-001")))
        d_pos = run_timed(lambda: dfs_find(c1, last))
        b_pos = run_timed(lambda: bfs_find(c1, last))
        d_neg = run_timed(lambda: dfs_find(c2, last))
        b_neg = run_timed(lambda: bfs_find(c2, last))
        _, t_up = best_of(lambda: customs_check(index, last, "CONT-002"), repeat=5)
        steps = customs_check(index, last, "CONT-002")[1]
        rows.append([
            nodes_c,
            f"{d_pos.value[1]} / {d_pos.peak_kb:.1f}KB",
            f"{b_pos.value[1]} / {b_pos.peak_kb:.1f}KB",
            f"{d_neg.value[1]} ({d_neg.elapsed_ms:.2f}ms)",
            f"{b_neg.value[1]} ({b_neg.elapsed_ms:.2f}ms)",
            f"{steps} pasos ({t_up * 1000:.1f}us)",
        ])
    print_table(["Nodos/contenedor", "DFS ultimo: vis/mem", "BFS ultimo: vis/mem", "DFS ausente", "BFS ausente", "Hash+padre (ausente)"], rows)
    print("Lectura: DFS/BFS crecen linealmente con n (BFS usa mas memoria: cola de todo un nivel); el ascenso es constante.")
