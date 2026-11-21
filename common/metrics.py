"""Utilidades de cronometro, medicion de memoria y formato de consola."""
from __future__ import annotations

import time
import tracemalloc
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Callable, TypeVar

T = TypeVar("T")


@dataclass
class MeasureResult:
    value: T
    elapsed_ms: float
    current_kb: float
    peak_kb: float


@contextmanager
def measure_block(track_memory: bool = True):
    if track_memory:
        tracemalloc.start()
    t0 = time.perf_counter()
    stats = {"elapsed_ms": 0.0, "current_kb": 0.0, "peak_kb": 0.0}
    try:
        yield stats
    finally:
        stats["elapsed_ms"] = (time.perf_counter() - t0) * 1000.0
        if track_memory:
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            stats["current_kb"] = current / 1024.0
            stats["peak_kb"] = peak / 1024.0


def run_timed(fn: Callable[[], T], track_memory: bool = True) -> MeasureResult:
    if track_memory:
        tracemalloc.start()
    t0 = time.perf_counter()
    res = fn()
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    if track_memory:
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        cur_kb, peak_kb = current / 1024.0, peak / 1024.0
    else:
        cur_kb, peak_kb = 0.0, 0.0
    return MeasureResult(value=res, elapsed_ms=elapsed_ms, current_kb=cur_kb, peak_kb=peak_kb)


def print_header(title: str) -> None:
    line = "=" * 76
    print(f"\n{line}\n  {title}\n{line}")


def print_table(headers: list[str], rows: list[list[object]]) -> None:
    str_rows = [[str(c) for c in r] for r in rows]
    widths = [len(h) for h in headers]
    for r in str_rows:
        for i, cell in enumerate(r):
            widths[i] = max(widths[i], len(cell))
    sep = "+-" + "-+-".join("-" * w for w in widths) + "-+"
    hdr = "| " + " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers)) + " |"
    print(sep)
    print(hdr)
    print(sep)
    for r in str_rows:
        print("| " + " | ".join(r[i].ljust(widths[i]) for i, _ in enumerate(headers)) + " |")
    print(sep)


def best_of(fn: Callable[[], T], repeat: int = 3) -> tuple[T, float]:
    """Ejecuta fn varias veces y retorna (ultimo_valor, mejor_tiempo_ms). Reduce el ruido del reloj."""
    best = float("inf")
    value = None
    for _ in range(max(1, repeat)):
        t0 = time.perf_counter()
        value = fn()
        best = min(best, (time.perf_counter() - t0) * 1000.0)
    return value, best  # type: ignore[return-value]
