"""Generadores deterministicos de datos sinteticos para el caso LogiX."""
from __future__ import annotations

import math
import random
from dataclasses import dataclass

DEFAULT_SEED = 42


def make_rng(seed: int = DEFAULT_SEED) -> random.Random:
    return random.Random(seed)


@dataclass(frozen=True)
class RoadEdge:
    to: int
    weight: float
    toll: float = 0.0


def generate_sparse_road_graph(
    num_nodes: int,
    avg_degree: float = 3.0,
    seed: int = DEFAULT_SEED,
    metric: str = "euclidean",
) -> tuple[list[list[RoadEdge]], list[tuple[float, float]]]:
    """Genera un grafo vial disperso conexo con coordenadas (x, y) y pesos positivos.

    Garantia de admisibilidad: peso(u, v) >= distancia(u, v) en la metrica elegida
    ('euclidean' o 'manhattan'), por lo que la heuristica de esa misma metrica nunca
    sobreestima el costo restante (A* devuelve rutas optimas).
    """
    rng = make_rng(seed)
    coords: list[tuple[float, float]] = [
        (rng.uniform(0.0, 50.0), rng.uniform(0.0, 50.0)) for _ in range(num_nodes)
    ]
    adj: list[list[RoadEdge]] = [[] for _ in range(num_nodes)]

    def dist_weight(u: int, v: int) -> float:
        dx = coords[u][0] - coords[v][0]
        dy = coords[u][1] - coords[v][1]
        dist = abs(dx) + abs(dy) if metric == "manhattan" else math.hypot(dx, dy)
        base = max(0.5, dist)
        return math.ceil(base * rng.uniform(1.0, 1.35) * 1000.0) / 1000.0

    for v in range(1, num_nodes):
        u = rng.randrange(0, v)
        w = dist_weight(u, v)
        adj[u].append(RoadEdge(v, w, rng.choice([0.0, 0.0, 0.0, 2.5])))
        adj[v].append(RoadEdge(u, w, rng.choice([0.0, 0.0, 0.0, 2.5])))

    target_undirected = max(num_nodes - 1, int((num_nodes * avg_degree) / 2))
    existing = set()
    for u in range(num_nodes):
        for e in adj[u]:
            existing.add((min(u, e.to), max(u, e.to)))

    attempts = 0
    max_attempts = target_undirected * 8 + 100
    while len(existing) < target_undirected and attempts < max_attempts:
        attempts += 1
        u = rng.randrange(0, num_nodes)
        v = rng.randrange(0, num_nodes)
        if u == v:
            continue
        pair = (min(u, v), max(u, v))
        if pair in existing:
            continue
        existing.add(pair)
        w = dist_weight(u, v)
        adj[u].append(RoadEdge(v, w, rng.choice([0.0, 0.0, 1.5, 3.0])))
        adj[v].append(RoadEdge(u, w, rng.choice([0.0, 0.0, 1.5, 3.0])))

    return adj, coords


def generate_tracking_codes(count: int, seed: int = DEFAULT_SEED) -> list[str]:
    """Genera guias tipo LX-94820-MED."""
    rng = make_rng(seed)
    zones = ["MED", "BOG", "CAL", "BAQ", "CTG", "PER", "BGA", "SMR"]
    codes: list[str] = []
    seen: set[str] = set()
    idx = 10000
    while len(codes) < count:
        idx += 1
        num = (idx * 7919 + rng.randint(0, 999)) % 90000 + 10000
        zone = rng.choice(zones)
        code = f"LX-{num}-{zone}"
        if code not in seen:
            seen.add(code)
            codes.append(code)
    return codes


def generate_postal_codes(count: int, seed: int = DEFAULT_SEED) -> list[str]:
    """Genera codigos unicos tipo COL-ANT-MED-050022 (sector de 6 digitos)."""
    rng = make_rng(seed)
    regions = [
        ("ANT", "MED", 50000), ("ANT", "ENV", 55400), ("ANT", "RNE", 54600),
        ("CUN", "BOG", 110000), ("VAC", "CAL", 760000), ("ATL", "BAQ", 80000),
        ("SAN", "BGA", 680000), ("BOL", "CTG", 130000),
    ]
    per_region = [[] for _ in regions]
    span = max(200, (count // len(regions) + 1) * 3)
    for r, (_, _, base) in enumerate(regions):
        offs = rng.sample(range(0, span), min(span, count // len(regions) + 2))
        per_region[r] = [base + o for o in offs]
    codes: list[str] = []
    i = 0
    while len(codes) < count:
        r = i % len(regions)
        pool = per_region[r]
        if pool:
            dept, mun, _ = regions[r]
            codes.append(f"COL-{dept}-{mun}-{pool.pop():06d}")
        i += 1
    rng.shuffle(codes)
    return codes
