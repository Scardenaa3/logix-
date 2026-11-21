"""Pruebas del Caso LogiX: paridad contra versiones ingenuas y modelos de referencia (semilla fija)."""
from __future__ import annotations

import gc
import math
import random
import unittest
import weakref

from common.generators import generate_postal_codes, generate_sparse_road_graph, generate_tracking_codes
from p01_representacion_grafos.graph_models import AdjacencyListGraph, AdjacencyMatrixGraph, ImplicitGridGraph
from p02_ruteo_tiempo_real.routing import (ContractionHierarchy, astar_route, close_edge_in_graph, copy_adj,
                                           dijkstra_route, floyd_warshall, make_requests, run_closure_experiment)
from p03_crossdocking.crossdock import CrossDockRouter, PackageItem, simulate_band
from p04_hash_guias.hash_tables import (ChainedHashTable, OpenAddressingHashTable, ShardedIndex, hash_fnv1a,
                                        hash_polynomial)
from p05_arbol_empaque.packing_tree import bfs_find, build_fleet, build_hierarchy, customs_check, dfs_find
from p06_prefijos_postales.prefix_structures import RadixTree, StandardTrie, StringAvl
from p07_arboles_balanceados.balanced_trees import AvlTree, RedBlackTree
from p08_undo_rollback.cargo_undo import CargoLoadQueue
from p09_proximidad_espacial.spatial_index import (Courier, GeohashIndex, KDTree2D, SpatialGridIndex,
                                                   brute_force_knn, check_parity, geohash_encode, make_fleet)
from p10_mst_fibra.mst_fiber import (build_complete_hub_graph, build_graph_with_density, build_matrix, kruskal_mst,
                                     prim_dense_matrix, prim_heap_mst)
from common.generators import make_rng


class TestP01(unittest.TestCase):
    def test_lista_matriz_paridad_y_implicito_igual_a_materializado(self):
        adj_data, _ = generate_sparse_road_graph(60, 3.0, seed=42)
        lst, mat = AdjacencyListGraph(60), AdjacencyMatrixGraph(60)
        for u, edges in enumerate(adj_data):
            for e in edges:
                if u < e.to:
                    lst.add_undirected_edge(u, e.to, e.weight)
                    mat.add_undirected_edge(u, e.to, e.weight)
        for a, b in zip(lst.dijkstra(0)[0], mat.dijkstra(0)[0]):
            self.assertAlmostEqual(a, b, places=6)
        grid = ImplicitGridGraph(7, 9, seed=3)
        for a, b in zip(grid.dijkstra(5)[0], grid.to_list_graph().dijkstra(5)[0]):
            self.assertAlmostEqual(a, b, places=6)


class TestP02(unittest.TestCase):
    def test_pesos_cumplen_admisibilidad(self):
        for metric in ("euclidean", "manhattan"):
            adj, co = generate_sparse_road_graph(80, 3.2, 42, metric)
            for u in range(80):
                for e in adj[u]:
                    dx, dy = abs(co[u][0] - co[e.to][0]), abs(co[u][1] - co[e.to][1])
                    d = dx + dy if metric == "manhattan" else math.hypot(dx, dy)
                    self.assertGreaterEqual(e.weight, d - 1e-9)

    def test_astar_optimo_y_ch_igual_dijkstra(self):
        for metric, kind in (("euclidean", "euclidean"), ("manhattan", "manhattan")):
            adj, co = generate_sparse_road_graph(90, 3.2, 11, metric)
            ch = ContractionHierarchy(adj)
            for s, d in make_requests(90, 150, seed=5):
                ref = dijkstra_route(adj, s, d).cost
                self.assertAlmostEqual(astar_route(adj, co, s, d, kind).cost, ref, places=6)
                self.assertAlmostEqual(ch.query(s, d)[0], ref, places=6)

    def test_floyd_igual_dijkstra(self):
        adj, _ = generate_sparse_road_graph(40, 3.0, 2)
        fw = floyd_warshall(adj)
        for s in range(0, 40, 7):
            for d in range(40):
                self.assertAlmostEqual(fw[s][d], dijkstra_route(adj, s, d).cost, places=6)

    def test_cierre_total_no_usa_la_via(self):
        r = run_closure_experiment(100)
        self.assertTrue(r["astar_equals_dijkstra"] and r["ch_ok"])
        u, v = r["edge"]
        for i in r["affected_idx"]:
            path = dijkstra_route(r["closed"], *r["reqs"][i]).path
            self.assertNotIn((min(u, v), max(u, v)), [(min(a, b), max(a, b)) for a, b in zip(path, path[1:])])


class TestP03(unittest.TestCase):
    def test_hv_critico_primero_y_estado_en_indice(self):
        r = CrossDockRouter(aging_threshold=10)
        r.enqueue(PackageItem("P1", "standard", 0, 50, 100.0))
        r.enqueue(PackageItem("P2", "high_value", 1, 10, 12000.0))
        self.assertEqual(r.dispatch_next(2).pkg_id, "P2")
        self.assertEqual(r.get_status("P2").status, "dispatched")

    def test_nada_se_pierde_ni_se_duplica(self):
        for thr in (None, 5, 20):
            r = simulate_band(1500, aging_threshold=thr, seed=3, load=0.8, priority_share=0.8)
            self.assertEqual(sum(len(v) for v in r.dispatched_waits.values()), 1500)
            self.assertTrue(all(i.status == "dispatched" for i in r.index.values()))

    def test_aging_mueve_estandar_viejos(self):
        r = CrossDockRouter(aging_threshold=5)
        for i in range(3):
            r.enqueue(PackageItem(f"S{i}", "standard", 0, 100, 50.0))
        self.assertEqual(r.apply_aging(10), 3)
        self.assertEqual(r.dispatch_next(10).pkg_id, "S0")


class TestP04(unittest.TestCase):
    def test_modelo_dict_con_borrado_y_rehash(self):
        rng = random.Random(1)
        keys = generate_tracking_codes(3000, seed=9)
        for hfn in (hash_fnv1a, hash_polynomial):
            tables = {"chained": ChainedHashTable(64, hfn, max_load=1.0),
                      **{m: OpenAddressingHashTable(64, m, hfn, max_load=0.5) for m in ("linear", "quadratic", "double")},
                      "sharded": ShardedIndex(4, 64)}
            for name, t in tables.items():
                model: dict[str, str] = {}
                for step in range(6000):
                    k = rng.choice(keys)
                    if rng.random() < 0.65:
                        t.insert(k, str(step))
                        model[k] = str(step)
                    else:
                        self.assertEqual(t.delete(k), k in model, name)
                        model.pop(k, None)
                for k in keys[:400]:
                    self.assertEqual(t.get(k).found, k in model, name)
                self.assertTrue(all(t.get(k).found for k in model), name)

    def test_capacidad_prima_evita_fallo_de_doble_hash(self):
        t = OpenAddressingHashTable(capacity=128, mode="double")
        for i in range(100):
            t.insert(f"LX-{10000 + i}-MED", "x")
        self.assertTrue(t.get("LX-10005-MED").found)


class TestP05(unittest.TestCase):
    def test_busquedas_y_aduana(self):
        root, idx = build_hierarchy(2, 3, 4)
        for fn in (dfs_find, bfs_find):
            self.assertTrue(fn(root, "PKG-001-001-002-003")[0])
            self.assertFalse(fn(root, "PKG-999")[0])
        containers, index = build_fleet(3, 2, 3, 4)
        self.assertEqual(customs_check(index, "PKG-002-001-002-003", "CONT-002"), (True, 4))
        self.assertFalse(customs_check(index, "PKG-002-001-002-003", "CONT-001")[0])
        self.assertFalse(customs_check(index, "NO-EXISTE", "CONT-001")[0])


class TestP06(unittest.TestCase):
    def test_busqueda_y_autocompletado_vs_filtro_ingenuo(self):
        for seed in (1, 2):
            codes = generate_postal_codes(700, seed=seed)
            t, r, a = StandardTrie(), RadixTree(), StringAvl()
            for c in codes:
                t.insert(c); r.insert(c); a.insert(c)
            for c in codes[:100]:
                self.assertTrue(t.search(c) and r.search(c) and a.search(c))
            for c in ("COL-ANT-MED-0", "COL-ANT-MED-99999", "COL-XXX"):
                self.assertFalse(t.search(c) or r.search(c) or a.search(c))
            for p in ("COL-", "COL-ANT", "COL-ANT-MED", "COL-CUN-BOG-11", "COL-ANT-MED-0500", "ZZ"):
                exp = sorted(c for c in codes if c.startswith(p))
                for s in (t, r, a):
                    self.assertEqual(sorted(s.autocomplete(p, 10**6)), exp, (type(s).__name__, p))

    def test_radix_comprime(self):
        t, r = StandardTrie(), RadixTree()
        for w in ("COL-ANT-MED-050022-RUTA-AAAAAAAA", "COL-ANT-MED-050021-RUTA-BBBBBBBB"):
            t.insert(w); r.insert(w)
        self.assertLess(r.node_count, t.node_count // 5)


class TestP07(unittest.TestCase):
    def test_modelo_conjunto_invariantes_rango(self):
        for cls in (AvlTree, RedBlackTree):
            rng = random.Random(4)
            t, model = cls(), set()
            for step in range(4000):
                k = (round(rng.uniform(1, 30), 1), round(rng.uniform(1, 60), 1), f"S{rng.randrange(400)}")
                if rng.random() < 0.6:
                    t.insert(k); model.add(k)
                else:
                    t.delete(k); model.discard(k)
                if step % 250 == 0:
                    t.check_invariants()
            t.check_invariants()
            self.assertEqual(t.size, len(model))
            for k in list(model)[:200]:
                self.assertTrue(t.search(k))
            lo, hi = (5.0, 0.0, ""), (12.0, 99.0, "~")
            self.assertEqual(t.range_query(lo, hi), sorted(k for k in model if lo <= k <= hi))

    def test_orden_ascendente_se_mantiene_balanceado(self):
        for cls, bound in ((AvlTree, 1.45), (RedBlackTree, 2.0)):
            t = cls()
            for i in range(2000):
                t.insert((float(i), 0.0, "x"))
            t.check_invariants()
            self.assertLessEqual(t.height(), bound * math.log2(2002) + 1)


class TestP08(unittest.TestCase):
    def test_modelo_lista_con_undo_aleatorio(self):
        rng = random.Random(8)
        q, model, history = CargoLoadQueue(), [], []
        counter = 0
        for _ in range(3000):
            op = rng.random()
            if op < 0.25 or not model:
                counter += 1
                pid = f"P{counter}"
                q.load_package(pid); history.append(list(model)); model.append(pid)
            elif op < 0.40:
                counter += 1
                pid = f"P{counter}"
                ref = rng.choice(model)
                q.insert_after_node(pid, q.nodes_by_id[ref]); history.append(list(model)); model.insert(model.index(ref) + 1, pid)
            elif op < 0.55:
                pid = rng.choice(model)
                q.remove_node(q.nodes_by_id[pid]); history.append(list(model)); model.remove(pid)
            elif op < 0.75 and len(model) >= 2:
                pid = rng.choice(model)
                ref = rng.choice([None] + [m for m in model if m != pid])
                q.move_after(q.nodes_by_id[pid], None if ref is None else q.nodes_by_id[ref]); history.append(list(model))
                model.remove(pid)
                model.insert(0 if ref is None else model.index(ref) + 1, pid)
            elif history:
                q.undo(); model = history.pop()
            self.assertEqual(q.to_list(), model)
            self.assertTrue(q.check_invariants()[0])
        q.rollback()
        self.assertEqual(q.to_list(), [])

    def test_commit_libera_y_historial_acotado(self):
        q = CargoLoadQueue()
        a = q.load_package("A"); q.load_package("B")
        q.remove_node(a)
        ref = weakref.ref(a); del a; gc.collect()
        self.assertIsNotNone(ref())
        q.commit(); gc.collect()
        self.assertIsNone(ref())
        q2 = CargoLoadQueue(max_history=10)
        for i in range(100):
            q2.load_package(f"X{i}")
        self.assertEqual(q2.history_size(), 10)
        self.assertTrue(q2.check_invariants()[0])


class TestP09(unittest.TestCase):
    def test_los_tres_indices_igualan_fuerza_bruta(self):
        for n, side, k in ((15, 30.0, 3), (60, 30.0, 5), (400, 30.0, 5), (400, 5.0, 8), (2000, 40.0, 10)):
            bad = check_parity(n=n, queries=150, k=k, side=side, seed=n)
            self.assertEqual(bad, {"kd": 0, "grid": 0, "geohash": 0}, (n, side, k))

    def test_no_disponibles_y_actualizacion(self):
        rng = make_rng(5)
        fleet = make_fleet(200, 20.0, rng)
        for c in fleet[::3]:
            c.available = False
        kd, grid = KDTree2D(fleet), SpatialGridIndex(2.0)
        for c in fleet:
            grid.upsert(c)
        for c in fleet:
            c.x, c.y = rng.uniform(0, 20), rng.uniform(0, 20)
            grid.upsert(c)
        kd = KDTree2D(fleet)
        for _ in range(100):
            qx, qy = rng.uniform(0, 20), rng.uniform(0, 20)
            ref = brute_force_knn(fleet, qx, qy, 4)
            self.assertEqual(kd.knn(qx, qy, 4), ref)
            self.assertEqual(grid.knn(qx, qy, 4), ref)

    def test_geohash_conocido(self):
        self.assertEqual(geohash_encode(57.64911, 10.40744, 11), "u4pruydqqvj")


class TestP10(unittest.TestCase):
    def test_paridad_en_densidades_y_grafo_completo(self):
        for n, d in ((40, 1.0), (30, 0.05), (60, 0.3), (60, 0.9)):
            adj = build_complete_hub_graph(n, 3) if d == 1.0 else build_graph_with_density(n, d, 3)
            wk, ek, _ = kruskal_mst(n, adj)
            wp, ep = prim_heap_mst(n, adj)
            wd = prim_dense_matrix(n, build_matrix(n, adj))
            self.assertEqual((len(ek), len(ep)), (n - 1, n - 1))
            self.assertAlmostEqual(wk, wp, places=2)
            self.assertAlmostEqual(wk, wd, places=2)

    def test_grafo_no_conexo_lanza_error(self):
        adj = [[(1, 1.0)], [(0, 1.0)], []]
        with self.assertRaises(ValueError):
            kruskal_mst(3, adj)
        with self.assertRaises(ValueError):
            prim_heap_mst(3, adj)


if __name__ == "__main__":
    unittest.main()
