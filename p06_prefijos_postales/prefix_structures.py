"""P06: Trie estandar, Radix Tree (Trie comprimido) y AVL para codigos postales."""
from __future__ import annotations

from dataclasses import dataclass, field

from common.generators import generate_postal_codes, make_rng
from common.metrics import best_of, print_header, print_table, run_timed


@dataclass
class TrieNode:
    children: dict[str, TrieNode] = field(default_factory=dict)
    is_end: bool = False


class StandardTrie:
    def __init__(self):
        self.root = TrieNode()
        self.node_count = 1

    def insert(self, word: str) -> None:
        cur = self.root
        for ch in word:
            if ch not in cur.children:
                cur.children[ch] = TrieNode()
                self.node_count += 1
            cur = cur.children[ch]
        cur.is_end = True

    def search(self, word: str) -> bool:
        cur = self.root
        for ch in word:
            if ch not in cur.children:
                return False
            cur = cur.children[ch]
        return cur.is_end

    def autocomplete(self, prefix: str, limit: int = 20) -> list[str]:
        cur = self.root
        for ch in prefix:
            if ch not in cur.children:
                return []
            cur = cur.children[ch]
        out: list[str] = []

        def dfs(node: TrieNode, acc: str) -> None:
            if len(out) >= limit:
                return
            if node.is_end:
                out.append(acc)
            for c, nxt in sorted(node.children.items()):
                dfs(nxt, acc + c)
                if len(out) >= limit:
                    return

        dfs(cur, prefix)
        return out


class RadixNode:
    """Nodo de Radix Tree. children: primer caracter de la arista -> (etiqueta completa de la arista, nodo hijo).
    Indexar por primer caracter hace cada descenso O(1) por nodo => busqueda O(L) real (sin escanear hermanos)."""

    __slots__ = ("children", "is_end")

    def __init__(self, is_end: bool = False):
        self.children: dict[str, tuple[str, RadixNode]] = {}
        self.is_end = is_end


def _common_prefix_len(a: str, b: str) -> int:
    limit = min(len(a), len(b))
    i = 0
    while i < limit and a[i] == b[i]:
        i += 1
    return i


class RadixTree:
    """Trie comprimido: cada arista almacena un segmento no vacio; los nodos con un solo hijo se fusionan."""

    def __init__(self):
        self.root = RadixNode()
        self.node_count = 1

    def insert(self, word: str) -> None:
        if not word:
            return
        cur, rem = self.root, word
        while rem:
            entry = cur.children.get(rem[0])
            if entry is None:
                cur.children[rem[0]] = (rem, RadixNode(is_end=True))
                self.node_count += 1
                return
            edge, child = entry
            cpl = _common_prefix_len(edge, rem)
            if cpl == len(edge):
                rem = rem[cpl:]
                if not rem:
                    child.is_end = True
                    return
                cur = child
                continue
            # dividir la arista en el punto de divergencia
            split = RadixNode()
            self.node_count += 1
            split.children[edge[cpl]] = (edge[cpl:], child)
            cur.children[rem[0]] = (edge[:cpl], split)
            new_suffix = rem[cpl:]
            if not new_suffix:
                split.is_end = True
            else:
                split.children[new_suffix[0]] = (new_suffix, RadixNode(is_end=True))
                self.node_count += 1
            return

    def search(self, word: str) -> bool:
        cur, rem = self.root, word
        while rem:
            entry = cur.children.get(rem[0])
            if entry is None or not rem.startswith(entry[0]):
                return False
            rem = rem[len(entry[0]):]
            cur = entry[1]
        return cur.is_end

    def autocomplete(self, prefix: str, limit: int = 20) -> list[str]:
        cur, rem, acc = self.root, prefix, ""
        while rem:
            entry = cur.children.get(rem[0])
            if entry is None:
                return []
            edge, child = entry
            if edge.startswith(rem):  # el prefijo termina dentro de la arista
                acc += edge
                cur, rem = child, ""
            elif rem.startswith(edge):
                acc += edge
                cur, rem = child, rem[len(edge):]
            else:
                return []
        out: list[str] = []

        def dfs(node: RadixNode, path: str) -> None:
            if len(out) >= limit:
                return
            if node.is_end:
                out.append(path)
            for _, (edge, nxt) in sorted(node.children.items()):
                dfs(nxt, path + edge)
                if len(out) >= limit:
                    return

        dfs(cur, acc)
        return out


@dataclass
class _AvlStrNode:
    key: str
    left: _AvlStrNode | None = None
    right: _AvlStrNode | None = None
    height: int = 1


class StringAvl:
    def __init__(self):
        self.root: _AvlStrNode | None = None
        self.node_count = 0

    def _h(self, n: _AvlStrNode | None) -> int:
        return n.height if n else 0

    def _rot_r(self, y: _AvlStrNode) -> _AvlStrNode:
        x = y.left
        assert x is not None
        y.left = x.right
        x.right = y
        y.height = 1 + max(self._h(y.left), self._h(y.right))
        x.height = 1 + max(self._h(x.left), self._h(x.right))
        return x

    def _rot_l(self, x: _AvlStrNode) -> _AvlStrNode:
        y = x.right
        assert y is not None
        x.right = y.left
        y.left = x
        x.height = 1 + max(self._h(x.left), self._h(x.right))
        y.height = 1 + max(self._h(y.left), self._h(y.right))
        return y

    def _insert(self, node: _AvlStrNode | None, key: str) -> _AvlStrNode:
        if node is None:
            self.node_count += 1
            return _AvlStrNode(key)
        if key < node.key:
            node.left = self._insert(node.left, key)
        elif key > node.key:
            node.right = self._insert(node.right, key)
        else:
            return node
        node.height = 1 + max(self._h(node.left), self._h(node.right))
        bal = self._h(node.left) - self._h(node.right)
        if bal > 1 and node.left and key < node.left.key:
            return self._rot_r(node)
        if bal < -1 and node.right and key > node.right.key:
            return self._rot_l(node)
        if bal > 1 and node.left and key > node.left.key:
            node.left = self._rot_l(node.left)
            return self._rot_r(node)
        if bal < -1 and node.right and key < node.right.key:
            node.right = self._rot_r(node.right)
            return self._rot_l(node)
        return node

    def insert(self, key: str) -> None:
        self.root = self._insert(self.root, key)

    def search(self, key: str) -> bool:
        cur = self.root
        while cur:
            if key == cur.key:
                return True
            cur = cur.left if key < cur.key else cur.right
        return False

    def autocomplete(self, prefix: str, limit: int = 20) -> list[str]:
        out: list[str] = []

        def inorder(n: _AvlStrNode | None) -> None:
            if not n or len(out) >= limit:
                return
            if n.key >= prefix:
                inorder(n.left)
            if len(out) < limit and n.key.startswith(prefix):
                out.append(n.key)
            if len(out) < limit and (n.key <= prefix + "\uffff"):
                inorder(n.right)

        inorder(self.root)
        return out


def demo() -> None:
    print_header("P06 - Codigos Postales (COL-ANT-MED-050022): Trie vs Radix vs AVL")
    codes = generate_postal_codes(120, seed=42)
    sample_code = "COL-ANT-MED-050022"
    if sample_code not in codes:
        codes.append(sample_code)
    trie, radix, avl = StandardTrie(), RadixTree(), StringAvl()
    for c in codes:
        trie.insert(c)
        radix.insert(c)
        avl.insert(c)
    pref = "COL-ANT-MED"
    print(f"Buscar {sample_code}: Trie={trie.search(sample_code)} | Radix={radix.search(sample_code)} | AVL={avl.search(sample_code)}")
    print(f"Nodos -> Trie: {trie.node_count} | Radix: {radix.node_count} | AVL: {avl.node_count}")
    ref = sorted(c for c in codes if c.startswith(pref))
    same = sorted(radix.autocomplete(pref, 10**6)) == ref == sorted(trie.autocomplete(pref, 10**6)) == sorted(avl.autocomplete(pref, 10**6))
    print(f"Autocompletar '{pref}': {len(ref)} codigos, las 3 estructuras coinciden con el filtro ingenuo: {same}")
    print(f"Primeros 4 (orden lexicografico): {radix.autocomplete(pref, 4)}")


def benchmark(sizes: list[int] | None = None) -> None:
    if sizes is None:
        sizes = [500, 2000, 8000]
    print_header("P06 - Benchmark: nodos, memoria, busqueda exacta y autocompletado (mismos datos en las 3 estructuras)")
    rows = []
    for n in sizes:
        codes = generate_postal_codes(n, seed=42)
        built = {}
        for name, cls in (("Trie", StandardTrie), ("Radix", RadixTree), ("AVL", StringAvl)):
            m = run_timed(lambda cls=cls: _build_struct(cls, codes))
            built[name] = m
        probe = codes[:: max(1, n // 500)]
        t_search, t_pref = {}, {}
        for name, m in built.items():
            obj = m.value
            t_search[name] = best_of(lambda o=obj: [o.search(c) for c in probe])[1]
            t_pref[name] = best_of(lambda o=obj: [o.autocomplete("COL-ANT-MED", 10) for _ in range(100)])[1]
        rows.append([
            n,
            *(f"{built[k].value.node_count} / {built[k].peak_kb:.0f}KB" for k in ("Trie", "Radix", "AVL")),
            *(f"{t_search[k]:.2f}" for k in ("Trie", "Radix", "AVL")),
            *(f"{t_pref[k]:.2f}" for k in ("Trie", "Radix", "AVL")),
        ])
    print_table(["Codigos", "Trie nodos/mem", "Radix nodos/mem", "AVL nodos/mem",
                 "Busq Trie ms", "Busq Radix ms", "Busq AVL ms",
                 "Pref Trie ms", "Pref Radix ms", "Pref AVL ms"], rows)
    print("Lectura honesta: con codigos de 6 digitos densos casi no hay cadenas de un solo hijo que comprimir, asi que Radix ~ Trie "
          "(y en Python el diccionario por nodo puede igualar el ahorro). El AVL usa 1 nodo por clave pero su busqueda es O(L log n).")

    print_header("P06 - Caso favorable a Radix: claves con cola larga (codigo postal + ruta/puerta de ~24 caracteres)")
    rng = make_rng(5)
    alpha = "ABCDEFGHJKLMNPQRSTUVWXYZ0123456789"
    rows = []
    for n in (500, 2000):
        base = generate_postal_codes(n, seed=42)
        long_keys = [f"{c}-RUTA-{''.join(rng.choice(alpha) for _ in range(18))}" for c in base]
        built = {name: run_timed(lambda cls=cls: _build_struct(cls, long_keys)) for name, cls in
                 (("Trie", StandardTrie), ("Radix", RadixTree), ("AVL", StringAvl))}
        rows.append([n, *(f"{built[k].value.node_count} / {built[k].peak_kb:.0f}KB" for k in ("Trie", "Radix", "AVL")),
                     f"{built['Trie'].value.node_count / built['Radix'].value.node_count:.1f}x menos nodos en Radix"])
    print_table(["Claves", "Trie nodos/mem", "Radix nodos/mem", "AVL nodos/mem", "Compresion"], rows)
    print("Radix gana cuando hay colas largas sin ramificar (matriculas, rutas, geohash largos): cada cola es UNA arista, no ~L nodos.")


def _build_struct(cls, codes: list[str]):
    obj = cls()
    for c in codes:
        obj.insert(c)
    return obj
