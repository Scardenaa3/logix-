"""P08: Cola de carga (lista doblemente enlazada) + pila LIFO de transacciones (Undo/Rollback)."""
from __future__ import annotations

import gc
import time
import weakref
from collections import deque
from dataclasses import dataclass

from common.metrics import print_header, print_table, run_timed


@dataclass(eq=False)
class CargoNode:
    pkg_id: str
    prev: CargoNode | None = None
    next: CargoNode | None = None
    active: bool = True


@dataclass(eq=False)
class _TxCommand:
    op: str  # load_back | insert_after | insert_front | remove | move
    node: CargoNode
    prev_ref: CargoNode | None = None  # predecesor del nodo ANTES de la operacion (None = era la cabeza / no aplica)


class CargoLoadQueue:
    """Lista doblemente enlazada (insercion/extraccion O(1) con referencia directa) + pila de comandos inversos.

    Gestion de memoria/consistencia:
    - Al desenlazar: prev = next = None y active = False (no quedan punteros colgantes ni ciclos).
    - Un nodo removido solo queda referenciado por la pila de transacciones; commit() vacia la pila y libera esos nodos.
    - max_history acota la pila (las transacciones mas antiguas se descartan: ya no son deshacibles).
    - undo valida el estado: si el predecesor guardado no esta activo, el historial es inconsistente y se lanza error.
    """

    def __init__(self, max_history: int | None = None):
        self.head: CargoNode | None = None
        self.tail: CargoNode | None = None
        self.count = 0
        self.nodes_by_id: dict[str, CargoNode] = {}
        self._undo_stack: deque[_TxCommand] = deque(maxlen=max_history)
        self.max_history = max_history

    # ---- primitivas de enlace (todas O(1)) ----
    def _link_front(self, node: CargoNode) -> None:
        node.active, node.prev, node.next = True, None, self.head
        if self.head is not None:
            self.head.prev = node
        else:
            self.tail = node
        self.head = node
        self.count += 1
        self.nodes_by_id[node.pkg_id] = node

    def _link_back(self, node: CargoNode) -> None:
        if self.tail is None:
            self._link_front(node)
            return
        node.active, node.prev, node.next = True, self.tail, None
        self.tail.next = node
        self.tail = node
        self.count += 1
        self.nodes_by_id[node.pkg_id] = node

    def _link_after(self, node: CargoNode, ref: CargoNode) -> None:
        if not ref.active:
            raise ValueError("Nodo de referencia inactivo")
        node.active, node.prev, node.next = True, ref, ref.next
        if ref.next is not None:
            ref.next.prev = node
        else:
            self.tail = node
        ref.next = node
        self.count += 1
        self.nodes_by_id[node.pkg_id] = node

    def _unlink(self, node: CargoNode) -> None:
        if not node.active:
            return
        if node.prev is not None:
            node.prev.next = node.next
        else:
            self.head = node.next
        if node.next is not None:
            node.next.prev = node.prev
        else:
            self.tail = node.prev
        node.prev = node.next = None
        node.active = False
        self.count -= 1
        self.nodes_by_id.pop(node.pkg_id, None)

    def _relink_at(self, node: CargoNode, prev_ref: CargoNode | None) -> None:
        if prev_ref is None:
            self._link_front(node)
        elif not prev_ref.active:
            raise RuntimeError("Historial inconsistente: el predecesor guardado ya no esta en la cola")
        else:
            self._link_after(node, prev_ref)

    # ---- operaciones de negocio (cada una apila su comando inverso) ----
    def load_package(self, pkg_id: str) -> CargoNode:
        self._check_new(pkg_id)
        node = CargoNode(pkg_id)
        self._link_back(node)
        self._undo_stack.append(_TxCommand("load_back", node))
        return node

    def insert_front(self, pkg_id: str) -> CargoNode:
        self._check_new(pkg_id)
        node = CargoNode(pkg_id)
        self._link_front(node)
        self._undo_stack.append(_TxCommand("insert_front", node))
        return node

    def insert_after_node(self, pkg_id: str, ref_node: CargoNode) -> CargoNode:
        self._check_new(pkg_id)
        node = CargoNode(pkg_id)
        self._link_after(node, ref_node)
        self._undo_stack.append(_TxCommand("insert_after", node, ref_node))
        return node

    def remove_node(self, node: CargoNode) -> None:
        if not node.active:
            raise ValueError("El nodo ya fue removido")
        prev_ref = node.prev
        self._unlink(node)
        self._undo_stack.append(_TxCommand("remove", node, prev_ref))

    def move_after(self, node: CargoNode, ref_node: CargoNode | None) -> None:
        """Reubica un paquete ya cargado justo despues de ref_node (None = al inicio). O(1)."""
        if not node.active:
            raise ValueError("El nodo no esta en la cola")
        if ref_node is node:
            raise ValueError("No se puede mover un paquete despues de si mismo")
        if ref_node is not None and not ref_node.active:
            raise ValueError("Nodo de referencia inactivo")
        old_prev = node.prev
        self._unlink(node)
        self._relink_at(node, ref_node)
        self._undo_stack.append(_TxCommand("move", node, old_prev))

    def undo(self) -> bool:
        if not self._undo_stack:
            return False
        cmd = self._undo_stack.pop()
        if cmd.op in ("load_back", "insert_after", "insert_front"):
            self._unlink(cmd.node)
        elif cmd.op == "remove":
            self._relink_at(cmd.node, cmd.prev_ref)
        elif cmd.op == "move":
            self._unlink(cmd.node)
            self._relink_at(cmd.node, cmd.prev_ref)
        return True

    def rollback(self, steps: int | None = None) -> int:
        """Deshace 'steps' transacciones (todas si None). Retorna cuantas deshizo."""
        done = 0
        while self._undo_stack and (steps is None or done < steps):
            self.undo()
            done += 1
        return done

    def commit(self) -> int:
        """Confirma la estiba: vacia la pila y libera los nodos removidos que solo ella mantenia vivos."""
        n = len(self._undo_stack)
        self._undo_stack.clear()
        return n

    def history_size(self) -> int:
        return len(self._undo_stack)

    def _check_new(self, pkg_id: str) -> None:
        if pkg_id in self.nodes_by_id:
            raise ValueError(f"Paquete {pkg_id} ya esta cargado")

    def to_list(self) -> list[str]:
        out, cur = [], self.head
        while cur:
            out.append(cur.pkg_id)
            cur = cur.next
        return out

    def check_invariants(self) -> tuple[bool, str]:
        if self.count == 0:
            if self.head is not None or self.tail is not None or self.nodes_by_id:
                return False, "Conteo 0 pero head/tail/indice no vacios"
            return True, "OK (vacia)"
        if self.head is None or self.tail is None:
            return False, "Conteo > 0 pero head o tail es None"
        if self.head.prev is not None or self.tail.next is not None:
            return False, "Limites head.prev o tail.next no nulos"
        visited, cur, prev = 0, self.head, None
        while cur is not None:
            if not cur.active:
                return False, f"Nodo inactivo {cur.pkg_id} en lista"
            if cur.prev is not prev:
                return False, f"Enlace prev roto en {cur.pkg_id}"
            if self.nodes_by_id.get(cur.pkg_id) is not cur:
                return False, f"Indice id->nodo inconsistente en {cur.pkg_id}"
            visited += 1
            prev, cur = cur, cur.next
            if visited > self.count:
                return False, "Ciclo detectado"
        if prev is not self.tail:
            return False, "Tail no coincide con ultimo nodo"
        if visited != self.count or len(self.nodes_by_id) != self.count:
            return False, f"Visitados {visited} / indice {len(self.nodes_by_id)} != count {self.count}"
        return True, f"OK ({self.count} nodos, pila={len(self._undo_stack)})"


def demo() -> None:
    print_header("P08 - Cola de Carga (DLL) + Transacciones Undo/Rollback (Pila LIFO)")
    q = CargoLoadQueue()
    n1 = q.load_package("G-101")
    n2 = q.load_package("G-102")
    n3 = q.load_package("G-103")
    q.insert_after_node("G-102B", n2)
    print("Cargar 101,102,103 + intercalar 102B tras 102 :", q.to_list(), "|", q.check_invariants()[1])
    q.move_after(n3, None)
    print("Mover G-103 al inicio                         :", q.to_list(), "|", q.check_invariants()[1])
    q.remove_node(n1)
    print("Quitar G-101                                  :", q.to_list(), "|", q.check_invariants()[1])
    q.undo()
    print("UNDO (restaura G-101 en su posicion)          :", q.to_list(), "|", q.check_invariants()[1])
    q.undo()
    print("UNDO (deshace el movimiento de G-103)         :", q.to_list(), "|", q.check_invariants()[1])
    q.undo()
    print("UNDO (quita G-102B)                           :", q.to_list(), "|", q.check_invariants()[1])

    # Evidencia anti-fuga: un nodo removido solo vive mientras la pila lo referencie
    q2 = CargoLoadQueue()
    a = q2.load_package("X-1")
    q2.load_package("X-2")
    ref = weakref.ref(a)
    q2.remove_node(a)
    del a
    gc.collect()
    vivo_antes = ref() is not None
    q2.commit()
    gc.collect()
    print(f"Nodo removido vivo en memoria con la pila activa: {vivo_antes} | tras commit(): {ref() is not None} (liberado)")
    q3 = CargoLoadQueue(max_history=100)
    for i in range(1000):
        q3.load_package(f"H-{i}")
    print(f"Historial acotado (max_history=100): 1000 cargas -> pila={q3.history_size()} (memoria de auditoria constante)")


def interactive_console() -> None:
    print_header("P08 - Consola Interactiva de Estiba (escribe 'ayuda' o 'salir')")
    q = CargoLoadQueue()
    while True:
        try:
            raw = input("estiba> ").strip()
        except EOFError:
            break
        if not raw:
            continue
        parts = raw.split()
        cmd = parts[0].lower()
        try:
            if cmd in ("salir", "exit"):
                break
            if cmd == "ayuda":
                print("Comandos: cargar <id> | intercalar <id> <despues_de_id|inicio> | mover <id> <despues_de_id|inicio> | "
                      "quitar <id> | undo | rollback <n> | commit | ver | salir")
            elif cmd == "cargar" and len(parts) == 2:
                q.load_package(parts[1])
                print("OK:", q.to_list())
            elif cmd == "intercalar" and len(parts) == 3:
                if parts[2] == "inicio":
                    q.insert_front(parts[1])
                else:
                    ref = q.nodes_by_id.get(parts[2])
                    if ref is None:
                        print("Referencia no encontrada")
                        continue
                    q.insert_after_node(parts[1], ref)
                print("OK:", q.to_list())
            elif cmd == "mover" and len(parts) == 3:
                node = q.nodes_by_id.get(parts[1])
                ref = None if parts[2] == "inicio" else q.nodes_by_id.get(parts[2])
                if node is None or (parts[2] != "inicio" and ref is None):
                    print("Paquete o referencia no encontrados")
                    continue
                q.move_after(node, ref)
                print("OK:", q.to_list())
            elif cmd == "quitar" and len(parts) == 2:
                node = q.nodes_by_id.get(parts[1])
                if node is None:
                    print("Paquete no encontrado")
                    continue
                q.remove_node(node)
                print("OK:", q.to_list())
            elif cmd == "undo":
                print("Undo:", q.undo(), "|", q.to_list())
            elif cmd == "rollback" and len(parts) == 2 and parts[1].isdigit():
                print(f"Deshechas {q.rollback(int(parts[1]))} transacciones |", q.to_list())
            elif cmd == "commit":
                print(f"Estiba confirmada: {q.commit()} transacciones liberadas")
            elif cmd == "ver":
                print("Cola:", q.to_list(), "|", q.check_invariants())
            else:
                print("Comando invalido. Usa 'ayuda'.")
        except (ValueError, RuntimeError) as exc:
            print("Error:", exc)


def benchmark(sizes: list[int] | None = None) -> None:
    if sizes is None:
        sizes = [2000, 20000, 200000]
    print_header("P08 - Benchmark: operaciones O(1) por transaccion y rollback masivo")
    rows = []
    for n in sizes:
        q = CargoLoadQueue()
        t0 = time.perf_counter()
        nodes = [q.load_package(f"P-{i:06d}") for i in range(n)]
        t_load = time.perf_counter() - t0
        t0 = time.perf_counter()
        for i in range(0, n, 2):
            q.remove_node(nodes[i])
        t_rem = time.perf_counter() - t0
        t0 = time.perf_counter()
        odd = nodes[1::2]
        for i in range(0, len(odd) - 1, 2):
            q.move_after(odd[i], odd[i + 1])
        t_mov = time.perf_counter() - t0
        ok_mid, _ = q.check_invariants()
        tx = q.history_size()
        t0 = time.perf_counter()
        undone = q.rollback()
        t_undo = time.perf_counter() - t0
        ok_end, msg = q.check_invariants()
        rows.append([n, f"{t_load / n * 1e6:.2f}", f"{t_rem / (n / 2) * 1e6:.2f}", f"{t_mov / max(1, len(odd) // 2) * 1e6:.2f}",
                     f"{t_undo / undone * 1e6:.2f}", f"{undone}/{tx}", "OK" if ok_mid and ok_end and q.count == 0 else "FALLA"])
    print_table(["Paquetes", "us/carga", "us/quitar", "us/mover", "us/undo", "Deshechas/Pila", "Invariantes + cola vacia"], rows)
    print("Lectura: el costo por operacion es ~constante al crecer n x100 => O(1); el rollback total deja la cola vacia e integra.")
