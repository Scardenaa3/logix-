# LogiX — Prueba Final: Algoritmos y Estructuras de Datos (versión consola)

Implementación en **Python** del caso "Logística Global S.A. (LogiX)": 10 preguntas técnicas, cada una con su estructura
de datos/algoritmo, una demo legible, un benchmark con mediciones y pruebas automáticas. Todo corre **en consola**
(sin web) y usa **solo la biblioteca estándar**.

---

## 1. Requisitos

| Requisito | Detalle |
|---|---|
| Python | 3.10 o superior (`python3 --version`) |
| Librerías externas | Ninguna |
| Sistema operativo | Linux/Ubuntu, WSL, macOS o Windows |
| `pandoc` (opcional) | Solo para regenerar `docs/entrega_logix.docx` |

## 2. Instalación y actualización

### Ubuntu / WSL
```bash
cd ~
mv logix logix_viejo                  # opcional: conservar la versión anterior (ignora el error si no existe)
cp /mnt/c/Users/TU_USUARIO/Downloads/logix_caso_logix_consola_v2.zip .   # si el zip está en Windows
sudo apt install -y unzip             # solo si falta
unzip logix_caso_logix_consola_v2.zip
cd logix
```

### Windows (PowerShell) o macOS/Linux
```powershell
Rename-Item logix logix_viejo         # opcional
Expand-Archive logix_caso_logix_consola_v2.zip -DestinationPath .
cd logix
```
En macOS/Linux use `unzip logix_caso_logix_consola_v2.zip`. Si `python3` no existe, pruebe `python` o `py`.

### Actualizar un solo archivo
```bash
cp /ruta/al/archivo_nuevo.py ~/logix/p09_proximidad_espacial/spatial_index.py
cd ~/logix && python3 main.py --verify
```

## 3. Cómo ejecutar

Siempre desde la carpeta `logix/` (la que contiene `main.py`).

### 3.1 Menú interactivo
```bash
python3 main.py
```
| Opción | Acción |
|---|---|
| 1 – 10 | Demo de la pregunta elegida; luego pregunta si desea correr su benchmark |
| 11 | Todas las demos (1-10) |
| 12 | Todos los benchmarks (1-10) |
| 13 | **Consola interactiva de estiba (P08)**: cargar, mover, quitar, undo, rollback, commit |
| 0 | Salir |

### 3.2 Línea de comandos
```bash
python3 main.py --question 7     # demo + benchmark de una pregunta (1-10)
python3 main.py --all-quick      # demos + benchmarks de las 10 preguntas (~15 s)
python3 main.py --bench-all      # solo benchmarks
python3 main.py --verify         # bateria de pruebas (22 pruebas)
python3 main.py --help
```
Guardar la salida: `python3 main.py --all-quick > salida.txt`

### 3.3 Consola de estiba (P08) — opción 13
| Comando | Efecto |
|---|---|
| `cargar <id>` | Agrega el paquete al final de la cola |
| `intercalar <id> <despues_de_id\|inicio>` | Inserta un paquete nuevo en una posición intermedia o al inicio |
| `mover <id> <despues_de_id\|inicio>` | Reubica un paquete ya cargado |
| `quitar <id>` | Retira el paquete de la cola |
| `undo` | Deshace la última transacción |
| `rollback <n>` | Deshace las últimas *n* transacciones |
| `commit` | Confirma la estiba: vacía la pila y libera memoria |
| `ver` | Muestra la cola y valida las invariantes |
| `ayuda` / `salir` | Ayuda / terminar |

Ejemplo: `cargar A` → `cargar B` → `mover B inicio` → `ver` (queda `B, A`) → `undo` → `ver` (vuelve a `A, B`).

## 4. Cómo comprobar que funciona

```bash
python3 main.py --verify             # debe terminar con: Ran 22 tests ... OK
python3 main.py --all-quick          # ~15 s, sin ningún "Traceback"
python3 -m compileall -q .           # sin salida = sin errores de sintaxis
python3 -m unittest discover -s tests -v    # alternativa: salida detallada
```
Señales de que es la versión correcta:
- P02: la tabla "Admisibilidad de la heurística" muestra `0/500` en las dos primeras filas.
- P09: `fallos {'kd': 0, 'grid': 0, 'geohash': 0}`.
- P03: la columna "vs fila anterior" del benchmark ronda `x2` (escala casi lineal).

**Qué validan las 22 pruebas** (`tests/test_logix.py`, semilla fija):
| Módulo | Prueba |
|---|---|
| P01 | Lista = Matriz en Dijkstra; grafo implícito = grafo materializado |
| P02 | Pesos ≥ distancia; A\* y Contraction Hierarchies = Dijkstra en cientos de pares; Floyd = Dijkstra; el cierre bloquea realmente la vía |
| P03 | Prioridad de alto valor; ningún paquete se pierde ni se duplica con/sin aging; el aging mueve estándar viejos |
| P04 | Las 3 variantes de direccionamiento abierto, encadenamiento y sharding contra un `dict` (insertar/borrar/rehash, 2 funciones hash); doble hash con capacidad no prima |
| P05 | DFS/BFS y verificación aduanera, caso positivo y negativo |
| P06 | Trie, Radix y AVL contra filtro ingenuo de prefijos; compresión de Radix |
| P07 | AVL y Rojo-Negro contra un conjunto en 4.000 operaciones, con invariantes y consulta por rango; altura con entrada ordenada |
| P08 | 3.000 operaciones aleatorias (incluido undo) contra una lista de Python; `commit` libera memoria; historial acotado |
| P09 | KD, cuadrícula y Geohash = fuerza bruta en 5 configuraciones; mensajeros no disponibles; actualización de posiciones; vector conocido de Geohash |
| P10 | Kruskal = Prim-heap = Prim-denso en varias densidades; grafo no conexo lanza error |

## 5. Estructura del proyecto
```
logix/
├── main.py                      menú y modos de ejecución
├── README.md
├── common/
│   ├── generators.py            datos sintéticos con semilla (red vial, guías, códigos postales)
│   └── metrics.py               cronómetro, memoria (tracemalloc), mejor-de-N, tablas de consola
├── p01_representacion_grafos/   graph_models.py
├── p02_ruteo_tiempo_real/       routing.py
├── p03_crossdocking/            crossdock.py
├── p04_hash_guias/              hash_tables.py
├── p05_arbol_empaque/           packing_tree.py
├── p06_prefijos_postales/       prefix_structures.py
├── p07_arboles_balanceados/     balanced_trees.py
├── p08_undo_rollback/           cargo_undo.py
├── p09_proximidad_espacial/     spatial_index.py
├── p10_mst_fibra/               mst_fiber.py
├── tests/test_logix.py
└── docs/
    ├── plantilla_entrega.md     fuente del documento (aquí se escribe/edita)
    ├── generar_entrega.py       inserta la evidencia medida y genera .md/.docx
    ├── evidencia_consola.txt    salida de `main.py --all-quick`
    ├── entrega_logix.md         documento final
    └── entrega_logix.docx       documento final en Word
```
Cada módulo `pXX` expone `demo()` (ejemplo legible con el caso LogiX) y `benchmark()` (mediciones con tamaños crecientes).

## 6. Qué implementa cada pregunta

| P | Estructuras / algoritmos | Decisión adoptada | Complejidad clave |
|---|---|---|---|
| 1 | Matriz, lista de adyacencia, grafo implícito en malla (peajes por regla) | Lista para la red real; implícito para zonas regulares; matriz solo si es pequeña y densa | Matriz Θ(V²); lista Θ(V+E); Dijkstra con heap O((V+E) log V) |
| 2 | Dijkstra, A\* (euclidiana/Manhattan), Floyd-Warshall, Contraction Hierarchies; cierre de vía | Recalcular solo vehículos afectados con A\* (h admisible); Floyd descartado; CH solo para red estática | Dijkstra/A\* O((V+E) log V); Floyd Θ(V³) |
| 3 | FIFO + min-heap EDF + heap de alto valor + cola de envejecidos + índice hash | Política de 6 niveles con aging | O(log n) por operación; aging O(1) amortizado |
| 4 | Hash propio (FNV-1a y polinómica): encadenamiento, lineal, cuadrático, doble hash; borrado, rehash, sharding | Doble hash con capacidad prima y α ≤ 0.7 (o encadenamiento si la carga es impredecible) | O(1) promedio; sondas = 1/(1−α) en abierto |
| 5 | Árbol N-ario con padre, DFS, BFS, índice hash global | Hash + ascenso por padres | DFS/BFS O(n); ascenso O(h)=O(1) |
| 6 | Trie, Radix Tree, AVL de cadenas | Radix para prefijos con colas largas; AVL si hay pocas claves o se necesitan rangos | Trie/Radix O(L); AVL O(L log n) |
| 7 | AVL y Rojo-Negro (insertar, borrar, rango, invariantes) | AVL para lectura intensiva/entradas ordenadas; Rojo-Negro para escritura intensiva | O(log n); AVL h ≤ 1.44 log n, RB h ≤ 2 log n |
| 8 | Lista doblemente enlazada + pila de transacciones (cargar, intercalar, mover, quitar, undo, rollback, commit) | Comando inverso por operación; historial acotado | Todas O(1) con referencia al nodo |
| 9 | KD-Tree, cuadrícula exacta por anillos, Geohash real, fuerza bruta | Geohash/cuadrícula para flota móvil; KD para lotes/zonas estáticas | Actualizar celda O(1); KD construcción O(n log n) |
| 10 | Kruskal + Union-Find (compresión y rango), Prim-heap, Prim-denso | Prim denso para el grafo completo de 40 centros; Kruskal como verificación | O(E log E); O(E log V); O(V²) |

## 7. Qué mide cada benchmark
- **P01:** memoria (tracemalloc) y tiempo de Dijkstra, mismo V en las 3 estructuras (V = 100…1000).
- **P02:** recalcular 500 vehículos tras cerrar la vía más usada: Dijkstra, A\*, A\* solo afectados, Contraction Hierarchies (construcción + consulta) y Floyd-Warshall; más la tabla de admisibilidad de heurísticas.
- **P03:** escalado de 1.000 a 16.000 paquetes; demo con 80 % de tráfico prioritario, con y sin aging, esperas y entregas vencidas.
- **P04:** sondas medidas contra teoría para α = 0.3…0.95; FNV-1a contra polinómica; 100.000 guías y 100.000 consultas.
- **P05:** DFS/BFS contra hash+padre, paquete ausente o último de un contenedor, con tamaños crecientes.
- **P06:** nodos, memoria, búsqueda exacta y autocompletado; segundo caso con claves de cola larga.
- **P07:** 95/5 y 5/95 de lectura/escritura (escritura = 50 % insertar + 50 % borrar) y entrada ordenada.
- **P08:** costo por operación con 2.000, 20.000 y 200.000 paquetes, y rollback masivo.
- **P09:** consulta estática y un tick de flota móvil con 1, 20, 200 y 1.000 consultas por tick.
- **P10:** barrido de densidad (0.05…1.0) con tiempos y conteo de operaciones.

## 8. Reproducibilidad y medición
- Semilla fija (42) en los generadores: los datos y los resultados algorítmicos (rutas, costos, alturas, rotaciones, nodos) se repiten.
- Los **tiempos en ms** cambian con el equipo; interprete tendencias (cómo crece al duplicar n), no valores absolutos.
- Se usa el mejor de varias repeticiones para reducir el ruido, y `tracemalloc` para memoria (mide lo que se asigna durante la construcción; las claves de texto ya existentes se comparten y no se cuentan).

## 9. Documento de entrega (`docs/`)
`entrega_logix.docx` / `.md` contiene las 10 preguntas con la plantilla del enunciado: Prompt · Respuesta de la IA · Análisis crítico individual · Solución unificada (diagrama, pseudocódigo, complejidad y tablas medidas).

Regenerar con sus propios tiempos:
```bash
python3 main.py --all-quick > docs/evidencia_consola.txt
python3 docs/generar_entrega.py        # el .docx requiere pandoc
```
El generador **sobrescribe** `entrega_logix.md/.docx`. Escriba su trabajo propio en `docs/plantilla_entrega.md` (la fuente) o guarde una copia del `.docx` antes de regenerar.

**Lo que el equipo debe completar (no está generado a propósito):**
1. El **prompt literal** enviado a la IA (se propone uno por pregunta).
2. La **respuesta real** de la IA (transcripción fiel).
3. El **análisis crítico de cada integrante**, con sus propias palabras (el documento deja hallazgos verificados con el código como punto de partida).

## 10. Supuestos
1. Red vial: peso ≥ distancia en la métrica de la heurística (condición de admisibilidad de A\*).
2. P3: tres flujos (estándar, perecedero, alto valor) y una banda de capacidad finita; "alto valor crítico" = valor ≥ 5.000.
3. P7: clave compuesta (peso, volumen, id); escrituras = 50 % inserciones y 50 % borrados.
4. P9: plano local en km centrado en Medellín para el Geohash (precisión 6 ≈ 1,2 × 0,6 km por celda).
5. P10: el "tema" suelto del título es un error tipográfico del enunciado y no cambia el problema.

## 11. Limitaciones conocidas
- Contraction Hierarchies devuelve el costo de la ruta, no desempaqueta el camino; es una versión didáctica.
- R-Tree se analiza en el documento pero no está implementado.
- No hay *redo* en P08 (no lo exige el enunciado).
- El sharding de P04 es lógico (varias tablas); no hay concurrencia real entre hilos.
- Las medidas son de CPython: un lenguaje compilado cambiaría los tiempos absolutos y algunas ventajas (p. ej. A\* en tiempo frente a Dijkstra).

## 12. Solución de problemas
| Síntoma | Causa y arreglo |
|---|---|
| `python3: command not found` | Use `python` o `py`; instale Python 3.10+ |
| `unrecognized arguments: --verify` | Está ejecutando la versión vieja: entre a la carpeta `logix` recién descomprimida |
| `ModuleNotFoundError: common` | Ejecute desde la carpeta que contiene `main.py` |
| `SyntaxError` en `X \| None` o `list[...]` | Python menor a 3.10: actualice |
| Falla `generar_entrega.py` al crear el `.docx` | Falta `pandoc` (`sudo apt install pandoc`); el `.md` se genera igual |
| `BrokenPipeError` al usar `\| head` | Es inofensivo: `head` cerró la tubería |

## 13. Cambios de la versión 2 (resumen)
Corrección de la cuadrícula espacial (k-NN exacto) y Geohash real; heurísticas de A\* admisibles y cierre real de vía con recálculo de afectados y Contraction Hierarchies; aging O(1) en cross-docking; hash con borrado, rehash, primos y sharding; borrado y rango en AVL/Rojo-Negro; operación `mover`, `commit` e historial acotado en P08; barrido de densidad en MST; 22 pruebas con modelos de referencia; documento con tablas medidas.

