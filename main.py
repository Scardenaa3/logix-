"""Punto de entrada de consola para el Caso LogiX (sin dependencias externas)."""
from __future__ import annotations

import argparse
import sys

from common.metrics import print_header
from p01_representacion_grafos import graph_models as p01
from p02_ruteo_tiempo_real import routing as p02
from p03_crossdocking import crossdock as p03
from p04_hash_guias import hash_tables as p04
from p05_arbol_empaque import packing_tree as p05
from p06_prefijos_postales import prefix_structures as p06
from p07_arboles_balanceados import balanced_trees as p07
from p08_undo_rollback import cargo_undo as p08
from p09_proximidad_espacial import spatial_index as p09
from p10_mst_fibra import mst_fiber as p10

MODULES = {
    1: ("P01 - Representacion de Grafos", p01),
    2: ("P02 - Ruteo en Tiempo Real", p02),
    3: ("P03 - Cross-Docking (3 Flujos)", p03),
    4: ("P04 - Indexacion de Guias (Hash)", p04),
    5: ("P05 - Jerarquia de Empaque (Arbol N-ario)", p05),
    6: ("P06 - Codigos Postales (Trie/Radix/AVL)", p06),
    7: ("P07 - Balanceo AVL vs Rojo-Negro", p07),
    8: ("P08 - Cola de Carga y Undo/Rollback", p08),
    9: ("P09 - Proximidad Espacial (KD vs Grid)", p09),
    10: ("P10 - MST Red de Fibra (Kruskal vs Prim)", p10),
}


def run_all(quick: bool = False) -> None:
    for _, (_, mod) in MODULES.items():
        mod.demo()
        if quick:
            mod.benchmark()


def _ask(prompt: str) -> str | None:
    """input() tolerante a EOF/Ctrl-C (por ejemplo cuando se ejecuta sin teclado)."""
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return None


def menu() -> None:
    while True:
        print_header("LOGIX - PRUEBA FINAL ALGORITMOS Y ESTRUCTURAS DE DATOS (CONSOLA)")
        for num, (label, _) in MODULES.items():
            print(f"  {num:2d}) {label} [demo]")
        print("  11) Ejecutar TODAS las demos (1-10)")
        print("  12) Ejecutar TODOS los benchmarks (1-10)")
        print("  13) Modo interactivo P08 (estiba + undo)")
        print("   0) Salir")
        choice = _ask("\nSeleccione una opcion: ")
        if choice is None or choice == "0":
            print("Hasta luego.")
            break
        if choice == "11":
            for _, (_, mod) in MODULES.items():
                mod.demo()
        elif choice == "12":
            for _, (_, mod) in MODULES.items():
                mod.benchmark()
        elif choice == "13":
            p08.interactive_console()
        elif choice.isdigit() and int(choice) in MODULES:
            idx = int(choice)
            _, mod = MODULES[idx]
            mod.demo()
            sub = _ask("¿Ejecutar benchmark de este modulo? [s/N]: ")
            if sub and sub.lower() == "s":
                mod.benchmark()
        else:
            print("Opcion no valida.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Consola interactiva Caso LogiX")
    parser.add_argument("--all-quick", action="store_true", help="Ejecuta demos y benchmarks de los 10 modulos")
    parser.add_argument("--bench-all", action="store_true", help="Ejecuta solo benchmarks de los 10 modulos")
    parser.add_argument("--verify", action="store_true", help="Ejecuta la bateria de pruebas unitarias/aleatorias")
    parser.add_argument("--question", type=int, choices=range(1, 11), help="Ejecuta demo + benchmark de una pregunta (1-10)")
    args = parser.parse_args(argv)

    if args.verify:
        import os
        import unittest

        suite = unittest.defaultTestLoader.discover(os.path.join(os.path.dirname(os.path.abspath(__file__)), "tests"),
                                                    top_level_dir=os.path.dirname(os.path.abspath(__file__)))
        return 0 if unittest.TextTestRunner(verbosity=1).run(suite).wasSuccessful() else 1
    if args.all_quick:
        run_all(quick=True)
        return 0
    if args.bench_all:
        for _, (_, mod) in MODULES.items():
            mod.benchmark()
        return 0
    if args.question:
        _, mod = MODULES[args.question]
        mod.demo()
        mod.benchmark()
        return 0
    menu()
    return 0


if __name__ == "__main__":
    sys.exit(main())
