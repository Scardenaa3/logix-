"""P07: AVL y Rojo-Negro propios (insercion, borrado, busqueda, rango) con clave compuesta (peso, volumen, id)."""
from __future__ import annotations

import time
from dataclasses import dataclass

from common.generators import make_rng
from common.metrics import print_header, print_table

PalletKey = tuple[float, float, str]


# ============================================================================== AVL
@dataclass
class _AvlNode:
    key: PalletKey
    left: _AvlNode | None = None
    right: _AvlNode | None = None
    height: int = 1


class AvlTree:
    """Balance estricto |h(izq)-h(der)| <= 1  =>  altura <= 1.44 log2(n+2). Mas rotaciones en escritura."""

    def __init__(self):
        self.root: _AvlNode | None = None
        self.rotations = 0
        self.comparisons = 0
        self.size = 0

    @staticmethod
    def _h(n: _AvlNode | None) -> int:
        return n.height if n else 0

    def height(self) -> int:
        return self._h(self.root)

    def _upd(self, n: _AvlNode) -> None:
        n.height = 1 + max(self._h(n.left), self._h(n.right))

    def _rot_r(self, y: _AvlNode) -> _AvlNode:
        self.rotations += 1
        x = y.left
        y.left, x.right = x.right, y
        self._upd(y)
        self._upd(x)
        return x

    def _rot_l(self, x: _AvlNode) -> _AvlNode:
        self.rotations += 1
        y = x.right
        x.right, y.left = y.left, x
        self._upd(x)
        self._upd(y)
        return y

    def _rebalance(self, n: _AvlNode) -> _AvlNode:
        self._upd(n)
        bal = self._h(n.left) - self._h(n.right)
        if bal > 1:
            if self._h(n.left.left) < self._h(n.left.right):
                n.left = self._rot_l(n.left)
            return self._rot_r(n)
        if bal < -1:
            if self._h(n.right.right) < self._h(n.right.left):
                n.right = self._rot_r(n.right)
            return self._rot_l(n)
        return n

    def _insert(self, node: _AvlNode | None, key: PalletKey) -> _AvlNode:
        if node is None:
            self.size += 1
            return _AvlNode(key)
        if key < node.key:
            node.left = self._insert(node.left, key)
        elif key > node.key:
            node.right = self._insert(node.right, key)
        else:
            return node
        return self._rebalance(node)

    def insert(self, key: PalletKey) -> None:
        self.root = self._insert(self.root, key)

    def _delete(self, node: _AvlNode | None, key: PalletKey) -> _AvlNode | None:
        if node is None:
            return None
        if key < node.key:
            node.left = self._delete(node.left, key)
        elif key > node.key:
            node.right = self._delete(node.right, key)
        else:
            self.size -= 1
            if node.left is None:
                return node.right
            if node.right is None:
                return node.left
            succ = node.right
            while succ.left:
                succ = succ.left
            node.key = succ.key
            self.size += 1  # el borrado recursivo siguiente resta 1
            node.right = self._delete(node.right, succ.key)
        return self._rebalance(node)

    def delete(self, key: PalletKey) -> None:
        self.root = self._delete(self.root, key)

    def search(self, key: PalletKey) -> bool:
        cur = self.root
        while cur:
            self.comparisons += 1
            if key == cur.key:
                return True
            cur = cur.left if key < cur.key else cur.right
        return False

    def range_query(self, lo: PalletKey, hi: PalletKey) -> list[PalletKey]:
        out: list[PalletKey] = []

        def rec(n: _AvlNode | None) -> None:
            if n is None:
                return
            if lo < n.key:
                rec(n.left)
            if lo <= n.key <= hi:
                out.append(n.key)
            if n.key < hi:
                rec(n.right)

        rec(self.root)
        return out

    def check_invariants(self) -> bool:
        def rec(n: _AvlNode | None, lo, hi) -> int:
            if n is None:
                return 0
            assert (lo is None or n.key > lo) and (hi is None or n.key < hi), "orden BST roto"
            l, r = rec(n.left, lo, n.key), rec(n.right, n.key, hi)
            assert abs(l - r) <= 1, "desbalance AVL"
            assert n.height == 1 + max(l, r), "altura almacenada incorrecta"
            return 1 + max(l, r)

        rec(self.root, None, None)
        return True


# ============================================================================== Rojo-Negro
RED, BLACK = True, False


class _RbNode:
    __slots__ = ("key", "color", "left", "right", "parent")

    def __init__(self, key, color, nil):
        self.key, self.color = key, color
        self.left = self.right = self.parent = nil


class RedBlackTree:
    """Rojo-Negro (CLRS con centinela NIL). Altura <= 2 log2(n+1); insercion <= 2 rotaciones, borrado <= 3."""

    def __init__(self):
        self.nil = _RbNode(None, BLACK, None)
        self.nil.left = self.nil.right = self.nil.parent = self.nil
        self.root = self.nil
        self.rotations = 0
        self.comparisons = 0
        self.size = 0

    def height(self) -> int:
        def rec(n):
            return 0 if n is self.nil else 1 + max(rec(n.left), rec(n.right))

        return rec(self.root)

    def _rot_l(self, x):
        self.rotations += 1
        y = x.right
        x.right = y.left
        if y.left is not self.nil:
            y.left.parent = x
        y.parent = x.parent
        if x.parent is self.nil:
            self.root = y
        elif x is x.parent.left:
            x.parent.left = y
        else:
            x.parent.right = y
        y.left, x.parent = x, y

    def _rot_r(self, y):
        self.rotations += 1
        x = y.left
        y.left = x.right
        if x.right is not self.nil:
            x.right.parent = y
        x.parent = y.parent
        if y.parent is self.nil:
            self.root = x
        elif y is y.parent.right:
            y.parent.right = x
        else:
            y.parent.left = x
        x.right, y.parent = y, x

    def insert(self, key: PalletKey) -> None:
        parent, cur = self.nil, self.root
        while cur is not self.nil:
            parent = cur
            if key < cur.key:
                cur = cur.left
            elif key > cur.key:
                cur = cur.right
            else:
                return
        z = _RbNode(key, RED, self.nil)
        z.parent = parent
        if parent is self.nil:
            self.root = z
        elif key < parent.key:
            parent.left = z
        else:
            parent.right = z
        self.size += 1
        self._fix_insert(z)

    def _fix_insert(self, z):
        while z.parent.color is RED:
            if z.parent is z.parent.parent.left:
                uncle = z.parent.parent.right
                if uncle.color is RED:
                    z.parent.color = uncle.color = BLACK
                    z.parent.parent.color = RED
                    z = z.parent.parent
                else:
                    if z is z.parent.right:
                        z = z.parent
                        self._rot_l(z)
                    z.parent.color = BLACK
                    z.parent.parent.color = RED
                    self._rot_r(z.parent.parent)
            else:
                uncle = z.parent.parent.left
                if uncle.color is RED:
                    z.parent.color = uncle.color = BLACK
                    z.parent.parent.color = RED
                    z = z.parent.parent
                else:
                    if z is z.parent.left:
                        z = z.parent
                        self._rot_r(z)
                    z.parent.color = BLACK
                    z.parent.parent.color = RED
                    self._rot_l(z.parent.parent)
        self.root.color = BLACK

    def _find(self, key):
        cur = self.root
        while cur is not self.nil and key != cur.key:
            cur = cur.left if key < cur.key else cur.right
        return cur

    def _transplant(self, u, v):
        if u.parent is self.nil:
            self.root = v
        elif u is u.parent.left:
            u.parent.left = v
        else:
            u.parent.right = v
        v.parent = u.parent

    def _minimum(self, n):
        while n.left is not self.nil:
            n = n.left
        return n

    def delete(self, key: PalletKey) -> None:
        z = self._find(key)
        if z is self.nil:
            return
        self.size -= 1
        y, y_color = z, z.color
        if z.left is self.nil:
            x = z.right
            self._transplant(z, z.right)
        elif z.right is self.nil:
            x = z.left
            self._transplant(z, z.left)
        else:
            y = self._minimum(z.right)
            y_color = y.color
            x = y.right
            if y.parent is z:
                x.parent = y
            else:
                self._transplant(y, y.right)
                y.right = z.right
                y.right.parent = y
            self._transplant(z, y)
            y.left = z.left
            y.left.parent = y
            y.color = z.color
        if y_color is BLACK:
            self._fix_delete(x)

    def _fix_delete(self, x):
        while x is not self.root and x.color is BLACK:
            if x is x.parent.left:
                w = x.parent.right
                if w.color is RED:
                    w.color = BLACK
                    x.parent.color = RED
                    self._rot_l(x.parent)
                    w = x.parent.right
                if w.left.color is BLACK and w.right.color is BLACK:
                    w.color = RED
                    x = x.parent
                else:
                    if w.right.color is BLACK:
                        w.left.color = BLACK
                        w.color = RED
                        self._rot_r(w)
                        w = x.parent.right
                    w.color = x.parent.color
                    x.parent.color = BLACK
                    w.right.color = BLACK
                    self._rot_l(x.parent)
                    x = self.root
            else:
                w = x.parent.left
                if w.color is RED:
                    w.color = BLACK
                    x.parent.color = RED
                    self._rot_r(x.parent)
                    w = x.parent.left
                if w.right.color is BLACK and w.left.color is BLACK:
                    w.color = RED
                    x = x.parent
                else:
                    if w.left.color is BLACK:
                        w.right.color = BLACK
                        w.color = RED
                        self._rot_l(w)
                        w = x.parent.left
                    w.color = x.parent.color
                    x.parent.color = BLACK
                    w.left.color = BLACK
                    self._rot_r(x.parent)
                    x = self.root
        x.color = BLACK

    def search(self, key: PalletKey) -> bool:
        cur = self.root
        while cur is not self.nil:
            self.comparisons += 1
            if key == cur.key:
                return True
            cur = cur.left if key < cur.key else cur.right
        return False

    def range_query(self, lo: PalletKey, hi: PalletKey) -> list[PalletKey]:
        out: list[PalletKey] = []

        def rec(n) -> None:
            if n is self.nil:
                return
            if lo < n.key:
                rec(n.left)
            if lo <= n.key <= hi:
                out.append(n.key)
            if n.key < hi:
                rec(n.right)

        rec(self.root)
        return out

    def check_invariants(self) -> bool:
        assert self.root.color is BLACK, "la raiz debe ser negra"

        def rec(n, lo, hi) -> int:
            if n is self.nil:
                return 1
            assert (lo is None or n.key > lo) and (hi is None or n.key < hi), "orden BST roto"
            if n.color is RED:
                assert n.left.color is BLACK and n.right.color is BLACK, "rojo con hijo rojo"
            bl, br = rec(n.left, lo, n.key), rec(n.right, n.key, hi)
            assert bl == br, "altura negra desigual"
            return bl + (1 if n.color is BLACK else 0)

        rec(self.root, None, None)
        return True


# ============================================================================== cargas de trabajo
def _rand_key(rng, i: int) -> PalletKey:
    return (round(rng.uniform(0.5, 50.0), 2), round(rng.uniform(1.0, 120.0), 2), f"ITEM-{i:07d}")


def run_workload(tree_cls, n_initial: int, read_ratio: float, ops: int, seed: int = 42) -> dict:
    """Arbol con n_initial claves; luego 'ops' operaciones: lectura (busqueda) con prob read_ratio;
    el resto son escrituras: 50% inserciones, 50% borrados de una clave existente."""
    rng = make_rng(seed)
    keys = [_rand_key(rng, i) for i in range(n_initial)]
    tree = tree_cls()
    for k in keys:
        tree.insert(k)
    tree.rotations = tree.comparisons = 0
    next_id, reads, writes = n_initial, 0, 0
    t0 = time.perf_counter()
    for _ in range(ops):
        if rng.random() < read_ratio:
            reads += 1
            tree.search(keys[rng.randrange(len(keys))])
        else:
            writes += 1
            if rng.random() < 0.5 or len(keys) < 10:
                next_id += 1
                k = _rand_key(rng, next_id)
                tree.insert(k)
                keys.append(k)
            else:
                j = rng.randrange(len(keys))
                keys[j], keys[-1] = keys[-1], keys[j]
                tree.delete(keys.pop())
    elapsed = (time.perf_counter() - t0) * 1000.0
    tree.check_invariants()
    return {"tree": tree, "height": tree.height(), "rot": tree.rotations, "cmp_per_read": tree.comparisons / max(1, reads),
            "rot_per_write": tree.rotations / max(1, writes), "ms": elapsed, "reads": reads, "writes": writes}


def demo() -> None:
    print_header("P07 - AVL vs Rojo-Negro: clave compuesta (peso, volumen, id), borrado y consulta por rango")
    for name, cls in (("AVL", AvlTree), ("Rojo-Negro", RedBlackTree)):
        t = cls()
        rng = make_rng(1)
        for i in range(200):
            t.insert(_rand_key(rng, i))
        ks = sorted(t.range_query((0.0, 0.0, ""), (99.0, 999.0, "~")))
        for k in ks[::3]:
            t.delete(k)
        t.check_invariants()
        rango = t.range_query((10.0, 0.0, ""), (12.0, 999.0, "~"))
        print(f"{name:10s} | n={t.size} tras borrar 1/3 | altura={t.height()} | invariantes OK | pallets con peso en [10,12] kg: {len(rango)}")
    r_a = run_workload(AvlTree, 500, 0.95, 3000)
    r_b = run_workload(RedBlackTree, 500, 0.95, 3000)
    print(f"Carga 95/5 | AVL: h={r_a['height']} cmp/lectura={r_a['cmp_per_read']:.2f} | RBT: h={r_b['height']} cmp/lectura={r_b['cmp_per_read']:.2f}")
    r_a = run_workload(AvlTree, 500, 0.05, 3000)
    r_b = run_workload(RedBlackTree, 500, 0.05, 3000)
    print(f"Carga 5/95 | AVL: rot/escritura={r_a['rot_per_write']:.2f} | RBT: rot/escritura={r_b['rot_per_write']:.2f}")


def benchmark(sizes: list[int] | None = None) -> None:
    if sizes is None:
        sizes = [1000, 5000]
    print_header("P07 - Benchmark AVL vs Rojo-Negro (escrituras = 50% insertar + 50% borrar; 20,000 operaciones)")
    rows = []
    for n in sizes:
        for label, ratio in (("95% lect / 5% escr", 0.95), ("5% lect / 95% escr", 0.05)):
            a = run_workload(AvlTree, n, ratio, 20000)
            b = run_workload(RedBlackTree, n, ratio, 20000)
            rows.append([f"n={n} {label}",
                         f"h={a['height']} cmp/L={a['cmp_per_read']:.2f} rot/E={a['rot_per_write']:.2f} {a['ms']:.0f}ms",
                         f"h={b['height']} cmp/L={b['cmp_per_read']:.2f} rot/E={b['rot_per_write']:.2f} {b['ms']:.0f}ms"])
    print_table(["Escenario", "AVL", "Rojo-Negro"], rows)
    print("cmp/L = comparaciones por lectura (profundidad media); rot/E = rotaciones por escritura.")

    print_header("P07 - Peor patron de entrada: inserciones en orden ascendente (carga de pallets ya ordenada)")
    rows = []
    for n in (1000, 5000):
        res = []
        for cls in (AvlTree, RedBlackTree):
            t = cls()
            t0 = time.perf_counter()
            for i in range(n):
                t.insert((float(i), float(i), f"S{i}"))
            ms = (time.perf_counter() - t0) * 1000.0
            t.check_invariants()
            res.append(f"h={t.height()} rot={t.rotations} {ms:.0f}ms")
        rows.append([n, *res])
    print_table(["n", "AVL", "Rojo-Negro"], rows)
    print("Lectura: AVL mantiene el arbol mas bajo (mejor para lecturas); Rojo-Negro rota menos por escritura (mejor para escrituras).")
