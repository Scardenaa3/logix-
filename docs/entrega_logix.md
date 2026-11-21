# Prueba Final: Algoritmos y Estructuras de Datos — Caso LogiX

**Equipo:** _(nombres de los integrantes)_  ·  **Código:** `python main.py` (Python 3.10+, solo biblioteca estándar)

## Cómo usar este documento

Cada pregunta sigue la plantilla del enunciado (Prompt · Respuesta de la IA · Análisis crítico individual · Solución unificada).

- **Prompt:** se propone un prompt técnico completo. Úsenlo (o ajústenlo) y **dejen aquí el texto literal que efectivamente enviaron**.
- **Respuesta de la IA:** pegar la transcripción fiel de lo que respondió su herramienta. Este documento no la incluye porque debe ser real.
- **Análisis crítico individual:** cada integrante lo escribe con sus palabras. Se dejan **hallazgos verificados con el código** (correcciones y supuestos que una IA suele pasar por alto) como punto de partida.
- **Solución unificada:** ya redactada, con diagrama, pseudocódigo, complejidad y **tablas medidas** producidas por `python main.py` (sección "Evidencia"). Los tiempos varían según el equipo; las tendencias no.

Todos los resultados usan semilla fija (42). Verificación automática: `python main.py --verify` (22 pruebas, incluidas pruebas aleatorias contra versiones ingenuas).

---

## Pregunta 1 — Modelado de la red de transporte (Grafos)

### Prompt a la IA (propuesto)
> Actúa como ingeniero senior en algoritmos de grafos. LogiX modela vías, peajes, centros de consolidación y puntos de entrega (red urbana dispersa, E ≈ 3V, hasta 50.000 nodos, restricciones de horario y peajes). Compara matriz de adyacencia, lista de adyacencia y grafo implícito en memoria (Θ), en eficiencia de Dijkstra y en flexibilidad para reglas dinámicas. Da fórmulas, un ejemplo numérico y una recomendación final justificada.

### Respuesta de la IA
_(pegar transcripción literal)_

### Análisis crítico individual
Hallazgos verificados con el código (base para cada integrante):
- Una IA suele decir "el grafo implícito usa O(1) memoria": es cierto **solo para el grafo**; Dijkstra sigue necesitando O(V) para `dist`. Además solo es posible si los vecinos se calculan por regla (mallas, reglas de peaje por fórmula), no para una red vial real irregular.
- Compararlas con el mismo V importa: una malla implícita tiene V' = filas × columnas ≠ n; el benchmark usa V' ≥ n para que la comparación sea justa.
- La matriz de doubles con V = 50.000 ocuparía ≈ 20 GB; la lista ≈ 5,6 MB.

_Integrante 1: …  ·  Integrante 2: …  ·  Integrante 3: …  ·  Integrante 4: …_

### Solución unificada
**Decisión:** lista de adyacencia (arreglos compactos tipo CSR en producción) para la red vial real; grafo implícito para zonas regulares (mallas, simulaciones, reglas por fórmula como peajes); matriz solo para submatrices densas pequeñas (p. ej. costos entre los 40 hubs).

```text
Lista:   adj[u] = [(v, peso, peaje, restriccion), ...]      Espacio Θ(V+E)
Matriz:  M[u][v] = peso o ∞                                 Espacio Θ(V²)
Implícito: vecinos(u) = f(fila, col)  ; peso = g(u, v)       Espacio Θ(1) (grafo)

Dijkstra(src):                       # heap binario
  dist[*]=∞; dist[src]=0; PQ={(0,src)}
  mientras PQ no vacía:
     (d,u)=extraer_min(PQ); si d>dist[u]: continuar
     para (v,w) en vecinos(u): si d+w<dist[v]: dist[v]=d+w; insertar(PQ,(dist[v],v))
```

| Estructura | Espacio | Dijkstra | Consulta arista (u,v) |
|---|---|---|---|
| Matriz | Θ(V²) | Θ(V²) | O(1) |
| Lista | Θ(V+E) | O((V+E) log V) | O(grado) |
| Implícito | Θ(1) + O(V) del algoritmo | O((V+E) log V) | O(1) por regla |

Con E ≈ 3V la lista gana en memoria y tiempo por un factor ≈ V/log V.

**Evidencia medida**

```text
[P01] Representacion de Grafos Viales (Matriz vs Lista vs Implicito)
Red de 12 nodos | Lista: d(0->11)=17.63 (ops=51) | Matriz: d(0->11)=17.63 (ops=288)
Malla 3x4 implicita | d(0->11)=4.65 (ops=46) | identica a la version materializada: True
Teoria: con V=50,000 una matriz de doubles ocuparia 20 GB; una lista con E=3V, ~5.6 MB.
```

```text
[P01] Benchmark Memoria y Dijkstra (Red Dispersa E ~ 3V, mismo V en las 3 estructuras)
+------+-----------+-----------+------------+------------+---------------+-------------------+
| V    | Lista mem | Dij Lista | Matriz mem | Dij Matriz | Implicito mem | Dij Implicito     |
+------+-----------+-----------+------------+------------+---------------+-------------------+
| 100  | 18.7 KB   | 0.040 ms  | 85.0 KB    | 0.626 ms   | 0.34 KB       | 0.281 ms (V=100)  |
| 250  | 41.5 KB   | 0.113 ms  | 504.6 KB   | 3.748 ms   | 0.33 KB       | 0.818 ms (V=255)  |
| 500  | 89.8 KB   | 0.266 ms  | 1985.1 KB  | 17.414 ms  | 0.35 KB       | 1.630 ms (V=506)  |
| 1000 | 189.1 KB  | 0.549 ms  | 7876.4 KB  | 74.126 ms  | 0.34 KB       | 3.426 ms (V=1023) |
+------+-----------+-----------+------------+------------+---------------+-------------------+
Lectura: la matriz crece ~V^2 en memoria y tiempo; lista e implicito crecen ~V. El implicito no guarda aristas (memoria ~constante) pero solo sirve si los vecinos se pueden calcular por regla.
```

---

## Pregunta 2 — Ruteo óptimo en tiempo real

### Prompt a la IA (propuesto)
> Actúa como experto en ruteo. Se cierra una vía arterial y deben recalcularse 500 vehículos en tránsito sobre una red de decenas de miles de nodos. Justifica la elección entre Dijkstra, A* (heurística euclidiana/Manhattan), Floyd-Warshall y Contraction Hierarchies. Indica condiciones de admisibilidad de la heurística, costos de preproceso y cómo afecta la actualización dinámica de pesos (subidas y bajadas). Da complejidades.

### Respuesta de la IA
_(pegar transcripción literal)_

### Análisis crítico individual
Hallazgos verificados con el código:
- **Admisibilidad:** A* solo es óptimo si peso(u,v) ≥ distancia en la métrica de la heurística. En una red donde algunas aristas pesan menos que la distancia euclidiana, A* devolvió rutas hasta 4 % más caras (euclidiana) y hasta 15 % (Manhattan). Con la red corregida (peso ≥ distancia) A* iguala a Dijkstra en las 500 rutas; la heurística Manhattan sobre una red euclidiana **no** es admisible (ver tabla).
- En Python A* expande menos nodos pero el tiempo es similar a Dijkstra: el ahorro depende del costo de evaluar la heurística.
- La ganancia mayor no es el algoritmo sino **recalcular solo los vehículos afectados** (los que usaban la vía cerrada).
- Contraction Hierarchies consulta muy rápido pero sus atajos codifican pesos viejos: tras el cierre hay que reconstruirla, y en esta medición reconstruir cuesta más que recalcular con A*.

_Integrante 1: …  ·  Integrante 2: …  ·  Integrante 3: …  ·  Integrante 4: …_

### Solución unificada
**Decisión:** (1) detectar los vehículos cuya ruta contiene la arista cerrada (índice arista → vehículos); (2) recalcular solo esos con A* (euclidiana si peso ≥ distancia) o Dijkstra cuando haya muchos destinos comunes (un Dijkstra inverso desde el hub sirve a todos); (3) Floyd-Warshall descartado (Θ(V³) tiempo, Θ(V²) espacio); (4) CH solo para consultas sobre red estática con preproceso fuera de línea (o variantes personalizables).

```text
cerrar_arista(u,v):  peso(u,v)=∞  (bloqueo)  o  peso*k+penal (congestión)
afectados = { vehículo : (u,v) ∈ ruta(vehículo) }          # O(500·|ruta|) o índice inverso
para cada vehículo en afectados: ruta = A*(posición_actual, destino)     # O((V+E) log V) peor caso
```

- Dijkstra con heap: O((V+E) log V). A*: igual en el peor caso, menos nodos con h admisible. Floyd: Θ(V³).
- **Pesos que suben** (cierres, congestión): la heurística sigue admisible y solo se recalculan los afectados. **Pesos que bajan** (reapertura): cualquier ruta previa podría mejorar; hay que revalidar (o usar algoritmos incrementales tipo D* Lite).

**Evidencia medida**

```text
[P02] Ruteo en Tiempo Real Ante Cierre de Via Arterial (500 Vehiculos)
Via arterial cerrada (bloqueo total): 4 <-> 39 | usada por 48 de 500 rutas
Vehiculos afectados (su ruta usaba la via): 48 -> costo extra de esas rutas: +19.0%
+----------------------------------------------+----------------+------------------+
| Estrategia de recalculo                      | Tiempo         | Nodos expandidos |
+----------------------------------------------+----------------+------------------+
| Dijkstra, los 500                            | 23.3 ms        | 40933            |
| A* euclidiana, los 500                       | 23.3 ms        | 24646            |
| A* euclidiana, solo 48 afectados             | 3.5 ms         | 4118             |
| CH: reconstruir (283 atajos) + 500 consultas | 32.2 + 10.8 ms | -                |
+----------------------------------------------+----------------+------------------+
A* da el mismo costo que Dijkstra en las 500 rutas: True | CH coincide con Dijkstra: True

Admisibilidad de la heuristica (rutas de A* mas caras que Dijkstra):
+---------------------------------------------+------------------+-----------------+
| Escenario                                   | Rutas suboptimas | Peor sobrecosto |
+---------------------------------------------+------------------+-----------------+
| red euclidiana + h euclidiana               | 0/500            | 0.0%            |
| red Manhattan + h Manhattan                 | 0/500            | 0.0%            |
| red euclidiana + h Manhattan (NO admisible) | 36/500           | 6.1%            |
+---------------------------------------------+------------------+-----------------+
Nota: si la via solo SUBE de peso (cierre) la heuristica sigue admisible; si BAJA (reapertura) las rutas previas pueden dejar de ser optimas y hay que revalidar a todos los vehiculos cuyo trayecto pudiera aprovecharla.
```

```text
[P02] Benchmark Recalculo de 500 Vehiculos tras Cierre (con Floyd-Warshall y CH)
+-----+-----------+--------------------+-----------------+-------------------+----------------+---------------------+
| V   | Afectados | Dijkstra 500 (exp) | A* 500 (exp)    | A* solo afectados | CH build+query | Floyd-Warshall      |
+-----+-----------+--------------------+-----------------+-------------------+----------------+---------------------+
| 80  | 77        | 11.0 ms (20380)    | 11.4 ms (12875) | 2.6 ms            | 9+4.9 ms       | 12 ms               |
| 140 | 49        | 20.4 ms (35589)    | 21.8 ms (23177) | 3.4 ms            | 23+7.5 ms      | 61 ms               |
| 220 | 64        | 34.5 ms (56761)    | 34.0 ms (35345) | 5.1 ms            | 53+13.1 ms     | 335 ms              |
| 400 | 50        | 67.4 ms (99740)    | 66.4 ms (61673) | 9.0 ms            | 158+19.5 ms    | ~2011 ms (est. V^3) |
+-----+-----------+--------------------+-----------------+-------------------+----------------+---------------------+
Lectura: A* expande menos nodos que Dijkstra; recalcular solo los afectados es la mayor ganancia; en Python el costo de evaluar la heuristica compensa el ahorro de nodos (el tiempo es similar); CH consulta rapido pero reconstruirla tras cada cierre cuesta mas que recalcular; Floyd-Warshall crece ~V^3.
```

---

## Pregunta 3 — Cross-docking (arquitectura de estructuras)

### Prompt a la IA (propuesto)
> Actúa como arquitecto de sistemas de cross-docking. Llegan paquetes estándar, express perecederos y de alto valor con ventana estricta. Define la arquitectura de estructuras de datos (colas, heaps, índices), la política de despacho, el riesgo de inanición y cómo mitigarlo, con complejidades por operación.

### Respuesta de la IA
_(pegar transcripción literal)_

### Análisis crítico individual
Hallazgos verificados con el código:
- La pregunta está poco especificada: se declara el supuesto de tres flujos con SLA distintos y capacidad finita de la banda.
- Una primera implementación de aging recorría toda la cola en cada despacho (O(n²): al duplicar n el tiempo se cuadruplicaba). Corregido: la cola FIFO está ordenada por llegada, así que solo se mira la **cabeza** → O(1) amortizado.
- Ordenar no crea capacidad: bajo sobrecarga, el aging reparte la espera y reduce vencimientos de estándar, pero el sistema sigue necesitando más capacidad. Se miden los deadlines vencidos por flujo.

_Integrante 1: …  ·  Integrante 2: …  ·  Integrante 3: …  ·  Integrante 4: …_

### Solución unificada
```text
estándar    → cola FIFO (deque)                         enqueue/dequeue O(1)
perecedero  → min-heap por fecha límite (EDF)           O(log n)
alto valor  → min-heap (nivel, ventana)                 O(log n)
envejecidos → deque; se mueve de la FIFO solo la cabeza O(1) amortizado
índice      → hash id → paquete (consulta/estado)       O(1) promedio, borrado perezoso

despachar(t):
  1) alto valor crítico o con ventana por vencer      2) perecedero por vencer (≤ 5 ticks)
  3) estándar envejecido (≥ umbral)                    4) perecedero por EDF
  5) alto valor restante                               6) FIFO estándar
```
Complejidad por operación: O(log n) (O(1) para estándar/aging). Espacio: O(n).

**Evidencia medida**

```text
[P03] Cross-Docking (3 Flujos + Indice Hash + Aging O(1)): 80% de trafico prioritario
+-----------------------+------------+-------------+---------------------+------------+--------------------+
| Politica              | Flujo      | Despachados | Espera prom (ticks) | Espera max | Deadlines vencidos |
+-----------------------+------------+-------------+---------------------+------------+--------------------+
| sin aging             | standard   | 101         | 75.7                | 123        | 52                 |
| sin aging             | perishable | 246         | 0.5                 | 7          | 0                  |
| sin aging             | high_value | 253         | 0.1                 | 2          | 0                  |
| con aging (umbral 15) | standard   | 101         | 55.2                | 109        | 30                 |
| con aging (umbral 15) | perishable | 246         | 8.9                 | 22         | 2                  |
| con aging (umbral 15) | high_value | 253         | 0.1                 | 2          | 0                  |
+-----------------------+------------+-------------+---------------------+------------+--------------------+
Consulta O(1) por indice hash: PKG-00010 -> estado=dispatched, tipo=standard, despachado en tick 3
```

```text
[P03] Benchmark Simulacion Banda Cross-Docking (escalado)
+----------+--------------+------------------+----------+---------------------+--------------------+
| Paquetes | Tiempo total | vs fila anterior | Peak mem | Espera std prom/max | Promovidos (aging) |
+----------+--------------+------------------+----------+---------------------+--------------------+
| 1000     | 11.7 ms      | -                | 263 KB   | 16.0 / 51           | 106                |
| 2000     | 25.1 ms      | x2.15            | 568 KB   | 30.5 / 100          | 716                |
| 4000     | 52.0 ms      | x2.07            | 1173 KB  | 62.6 / 200          | 1872               |
| 8000     | 116.6 ms     | x2.24            | 2398 KB  | 126.9 / 400         | 4246               |
| 16000    | 225.9 ms     | x1.94            | 4956 KB  | 255.4 / 800         | 9012               |
+----------+--------------+------------------+----------+---------------------+--------------------+
Lectura: al duplicar n el tiempo crece ~x2 (O(n log n) total), no ~x4: ya no hay recorrido O(n) por despacho.
```

---

## Pregunta 4 — Indexación de guías con tablas hash

### Prompt a la IA (propuesto)
> Actúa como especialista en estructuras de datos de alto rendimiento. El sistema recibe 20 millones de consultas diarias sobre guías alfanuméricas tipo LX-94820-MED. Diseña la indexación en memoria con tablas hash: función de dispersión, factor de carga ideal, y compara direccionamiento abierto (lineal, cuadrático, doble hash) con encadenamiento. Incluye borrado, rehash y estrategia de picos/escala.

### Respuesta de la IA
_(pegar transcripción literal)_

### Análisis crítico individual
Hallazgos verificados con el código:
- 20 M consultas/día ≈ 231 req/s promedio; el requisito real es el **pico** (5×–15× ≈ 1.200–3.500 req/s). Una sola tabla en memoria ya soporta cientos de miles de consultas/s; el diseño debe cuidar rehash y concurrencia, no la capacidad bruta.
- El doble hash exige que h2 sea coprimo con la capacidad: con capacidad 128 el sondeo falló antes de α = 0.8. Solución: capacidades **primas**.
- El borrado en direccionamiento abierto requiere lápidas (tombstones) o se rompe la búsqueda.
- La teoría (1/(1−α) etc.) coincide con lo medido; lineal se degrada fuerte desde α ≈ 0.7–0.9.
- La comparación de memoria entre estructuras en Python debe leerse con cuidado: las claves ya existen y se comparten.

_Integrante 1: …  ·  Integrante 2: …  ·  Integrante 3: …  ·  Integrante 4: …_

### Solución unificada
**Decisión:** hash FNV-1a (rápida, buena dispersión; pasar a 64 bits o SipHash si hay claves adversarias); capacidad prima; direccionamiento abierto con **doble hash** y α ≤ 0.7 con rehash automático (compacto y amigable con la caché), o **encadenamiento** (α hasta ≈ 1, borrado simple) cuando la carga es impredecible; **sharding** por un segundo hash para repartir entre hilos/nodos y acotar el costo de cada rehash.

| Esquema | Sondas (éxito) | Sondas (fallo) | α recomendado |
|---|---|---|---|
| Encadenamiento | 1 + α/2 | ≈ α | ≤ 1 |
| Lineal | ½(1 + 1/(1−α)) | ½(1 + 1/(1−α)²) | ≤ 0.5–0.7 |
| Cuadrático | ≈ 1 − ln(1−α) − α/2 | — | < 0.5 garantizado, ≤ 0.7 práctico |
| Doble hash | (1/α) ln(1/(1−α)) | ≈ 1/(1−α) | ≤ 0.7–0.8 |

Operaciones promedio O(1); peor caso O(n) (mitigado con buena función y α acotado). Espacio: abierto Θ(m) con m ≥ n/0.7; encadenado Θ(m + n).

**Evidencia medida**

```text
[P04] Indexacion de Guias (LX-94820-MED): borrado, rehash y sharding
Guia LX-98573-BOG | alpha=0.40 | encontrada=True | sondas=1 | capacidad primo=1009
Tras delete: encontrada=False | otra guia sigue visible=True | lapidas=1
Rehash automatico (alpha<=0.7): 400 guias desde capacidad 16 -> capacidad 673, rehashes=5, alpha=0.59
Sharding x8 con 20,000 guias: tamanos [2512, 2565, 2475, 2541, 2420, 2501, 2522, 2464] (desbalance max/min = 1.06)
Escala LogiX: 20,000,000 consultas/dia = ~231.5 req/s promedio; con picos 5x-15x -> ~1,200-3,500 req/s.
```

```text
[P04] Sondas por busqueda vs alpha (capacidad primo 10007) - medido vs teoria
+-------+-----------+-----------------------+-----------------------+--------------+----------------------+
| alpha | Esquema   | Sondas exito (medido) | Sondas exito (teoria) | Sondas fallo | Inserciones fallidas |
+-------+-----------+-----------------------+-----------------------+--------------+----------------------+
| 0.30  | chained   | 1.14                  | 1.15                  | 1.04         | 0                    |
| 0.30  | linear    | 1.20                  | 1.21                  | 1.50         | 0                    |
| 0.30  | quadratic | 1.19                  | 1.21                  | 1.49         | 0                    |
| 0.30  | double    | 1.18                  | 1.19                  | 1.44         | 0                    |
| 0.50  | chained   | 1.25                  | 1.25                  | 1.12         | 0                    |
| 0.50  | linear    | 1.48                  | 1.50                  | 2.46         | 0                    |
| 0.50  | quadratic | 1.41                  | 1.44                  | 2.14         | 0                    |
| 0.50  | double    | 1.38                  | 1.39                  | 2.03         | 0                    |
| 0.70  | chained   | 1.35                  | 1.35                  | 1.20         | 0                    |
| 0.70  | linear    | 2.14                  | 2.17                  | 6.23         | 0                    |
| 0.70  | quadratic | 1.80                  | 1.85                  | 3.61         | 0                    |
| 0.70  | double    | 1.70                  | 1.72                  | 3.38         | 0                    |
| 0.90  | chained   | 1.45                  | 1.45                  | 1.32         | 0                    |
| 0.90  | linear    | 4.88                  | 5.50                  | 35.26        | 0                    |
| 0.90  | quadratic | 2.73                  | 2.85                  | 10.94        | 0                    |
| 0.90  | double    | 2.58                  | 2.56                  | 9.92         | 0                    |
| 0.95  | chained   | 1.47                  | 1.48                  | 1.35         | 0                    |
| 0.95  | linear    | 7.23                  | 10.50                 | 82.89        | 0                    |
| 0.95  | quadratic | 3.34                  | 3.52                  | 21.62        | 0                    |
| 0.95  | double    | 3.16                  | 3.15                  | 20.27        | 0                    |
+-------+-----------+-----------------------+-----------------------+--------------+----------------------+
```

```text
[P04] Funcion hash: FNV-1a vs polinomica (encadenamiento, alpha=0.7, memoria con tracemalloc)
+--------------------+------------------+---------------------+--------------+--------------+
| Estructura/Hash    | Cadena mas larga | Buckets vacios      | Sondas exito | Memoria pico |
+--------------------+------------------+---------------------+--------------+--------------+
| FNV-1a             | 7                | 49.5% (ideal 49.7%) | 1.35         | 1059 KB      |
| Polinomica b=131   | 5                | 49.2% (ideal 49.7%) | 1.34         | 1173 KB      |
| OA linear (FNV-1a) | -                | -                   | 2.14         | 157 KB       |
| OA double (FNV-1a) | -                | -                   | 1.70         | 157 KB       |
+--------------------+------------------+---------------------+--------------+--------------+
```

```text
[P04] Rendimiento a escala: 100,000 guias, 100,000 consultas (alpha=0.7 en direccionamiento abierto)
+-----------------------------------+---------------+----------------+---------------------+----------+
| Estructura                        | Insertar 100k | 100k consultas | Rendimiento         | Aciertos |
+-----------------------------------+---------------+----------------+---------------------+----------+
| Encadenamiento (max_load=1.0)     | 461 ms        | 193 ms         | 519,201 consultas/s | 100000   |
| Abierto doble hash (max_load=0.7) | 923 ms        | 386 ms         | 258,795 consultas/s | 100000   |
| Sharded x8 encadenado             | 539 ms        | 329 ms         | 303,934 consultas/s | 100000   |
+-----------------------------------+---------------+----------------+---------------------+----------+
Referencia: promedio 231.5 req/s, picos ~3,500 req/s -> una sola tabla en memoria (en Python) ya cubre el pico con holgura.
```

---

## Pregunta 5 — Jerarquía de empaque (árbol N-ario)

### Prompt a la IA (propuesto)
> Actúa como ingeniero de estructuras de datos. Modela Contenedor → Pallet → Caja Master → Paquete con un árbol N-ario. Explica cómo verificar eficientemente si un paquete está dentro de un contenedor (inspección aduanera), comparando DFS, BFS y ascenso por punteros al padre, con complejidad temporal y espacial, incluyendo el caso en que el paquete NO está.

### Respuesta de la IA
_(pegar transcripción literal)_

### Análisis crítico individual
Hallazgos verificados con el código:
- DFS/BFS son O(n) tiempo en el peor caso, y **el caso negativo (paquete ausente) siempre lo alcanza**: recorren todo el contenedor. Una IA suele analizar solo el caso positivo.
- Espacio: DFS O(h·b) (pila con hermanos pendientes), BFS O(ancho del nivel) — en la práctica BFS usa bastante más memoria.
- La solución eficiente combina un **índice hash global id → nodo** (O(1) promedio) con **ascenso por padres** (altura fija 4 ⇒ ≤ 4 pasos).

_Integrante 1: …  ·  Integrante 2: …  ·  Integrante 3: …  ·  Integrante 4: …_

### Solución unificada
```text
nodo = {id, nivel, padre, hijos[]}      índice[id] → nodo
verificar(paquete, contenedor):
   p = índice[paquete]; c = índice[contenedor]          # O(1) promedio
   mientras p ≠ nulo: si p == c: retornar verdadero; p = p.padre     # ≤ 4 pasos
   retornar falso
```
Tiempo O(h) = O(1) para h = 4; espacio extra O(1) (más O(n) del índice). DFS/BFS quedan como respaldo cuando no existe el índice.

**Evidencia medida**

```text
[P05] Jerarquia N-aria: inspeccion aduanera (DFS vs BFS vs indice + ascenso por padre)
Paquete inspeccionado: PKG-001-002-003-004
+--------------------------------+------------------+------------------+--------------------------+
| Contenedor consultado          | DFS              | BFS              | Hash + ascenso por padre |
+--------------------------------+------------------+------------------+--------------------------+
| CONT-001 (contiene el paquete) | True (76 nodos)  | True (76 nodos)  | True (4 pasos)           |
| CONT-002 (NO lo contiene)      | False (76 nodos) | False (76 nodos) | False (4 pasos)          |
+--------------------------------+------------------+------------------+--------------------------+
El caso negativo es el peor para DFS/BFS: recorren TODO el contenedor; el ascenso por padre sigue en <= 4 pasos.
```

```text
[P05] Benchmark inspeccion aduanera (peor caso: paquete ausente o ultimo del contenedor)
+------------------+---------------------+---------------------+---------------+---------------+----------------------+
| Nodos/contenedor | DFS ultimo: vis/mem | BFS ultimo: vis/mem | DFS ausente   | BFS ausente   | Hash+padre (ausente) |
+------------------+---------------------+---------------------+---------------+---------------+----------------------+
| 225              | 225 / 0.3KB         | 225 / 2.3KB         | 225 (0.31ms)  | 225 (0.10ms)  | 4 pasos (0.3us)      |
| 449              | 449 / 0.3KB         | 449 / 4.4KB         | 449 (0.67ms)  | 449 (0.26ms)  | 4 pasos (0.3us)      |
| 897              | 897 / 0.4KB         | 897 / 7.5KB         | 897 (1.58ms)  | 897 (0.68ms)  | 4 pasos (0.4us)      |
| 1793             | 1793 / 0.6KB        | 1793 / 13.7KB       | 1793 (3.21ms) | 1793 (1.30ms) | 4 pasos (0.3us)      |
+------------------+---------------------+---------------------+---------------+---------------+----------------------+
Lectura: DFS/BFS crecen linealmente con n (BFS usa mas memoria: cola de todo un nivel); el ascenso es constante.
```

---

## Pregunta 6 — Códigos postales y prefijos (Trie, Radix, AVL)

### Prompt a la IA (propuesto)
> Actúa como experto en estructuras para cadenas. Escáneres leen prefijos como COL-ANT-MED-050022. Compara Trie estándar, Radix Tree y AVL/Rojo-Negro en búsqueda, autocompletado y memoria, con complejidades en función de la longitud L de la clave y el número n de claves. Explica cuándo Radix es la mejor opción y cuándo no.

### Respuesta de la IA
_(pegar transcripción literal)_

### Análisis crítico individual
Hallazgos verificados con el código:
- La afirmación "Radix siempre ahorra memoria" **no se sostiene en general**: con códigos postales de 6 dígitos densos casi no hay cadenas de un solo hijo, y Radix ≈ Trie; el AVL (1 nodo por clave) usa menos nodos. Radix gana de forma clara con **colas largas sin ramificar** (≈ 19× menos nodos en la tabla de claves con ruta).
- AVL: la comparación de cadenas cuesta O(L), por lo que la búsqueda es O(L log n), no O(log n); y no ofrece autocompletado nativo por prefijo.
- Indexar los hijos por primer carácter (diccionario) hace el descenso del Radix O(1) por nodo ⇒ búsqueda O(L) real.

_Integrante 1: …  ·  Integrante 2: …  ·  Integrante 3: …  ·  Integrante 4: …_

### Solución unificada
| Estructura | Búsqueda | Autocompletado | Espacio |
|---|---|---|---|
| Trie | O(L) | O(L + salida) | O(n·L·σ) en el peor caso |
| Radix | O(L) | O(L + salida) | O(n) nodos (colas comprimidas) |
| AVL | O(L log n) | recorrido en orden desde el límite inferior | O(n) nodos, claves completas |

**Decisión:** Radix Tree para clasificación por prefijo en compuertas (O(L) independiente de n, autocompletado natural, memoria acotada cuando las claves comparten prefijos largos y tienen colas únicas); AVL/Rojo-Negro si el conjunto es pequeño, se requieren recorridos ordenados/rangos o se prioriza la simplicidad.

**Evidencia medida**

```text
[P06] Codigos Postales (COL-ANT-MED-050022): Trie vs Radix vs AVL
Buscar COL-ANT-MED-050022: Trie=True | Radix=True | AVL=True
Nodos -> Trie: 302 | Radix: 178 | AVL: 120
Autocompletar 'COL-ANT-MED': 15 codigos, las 3 estructuras coinciden con el filtro ingenuo: True
Primeros 4 (orden lexicografico): ['COL-ANT-MED-050006', 'COL-ANT-MED-050007', 'COL-ANT-MED-050008', 'COL-ANT-MED-050022']
```

```text
[P06] Benchmark: nodos, memoria, busqueda exacta y autocompletado (mismos datos en las 3 estructuras)
+---------+----------------+-----------------+---------------+--------------+---------------+-------------+--------------+---------------+-------------+
| Codigos | Trie nodos/mem | Radix nodos/mem | AVL nodos/mem | Busq Trie ms | Busq Radix ms | Busq AVL ms | Pref Trie ms | Pref Radix ms | Pref AVL ms |
+---------+----------------+-----------------+---------------+--------------+---------------+-------------+--------------+---------------+-------------+
| 500     | 760 / 131KB    | 674 / 93KB      | 500 / 47KB    | 0.65         | 0.93          | 0.37        | 1.65         | 1.30          | 0.83        |
| 2000    | 2745 / 476KB   | 2616 / 399KB    | 2000 / 188KB  | 0.55         | 0.46          | 0.31        | 1.57         | 0.74          | 0.48        |
| 8000    | 10712 / 1860KB | 10446 / 1927KB  | 8000 / 750KB  | 0.33         | 0.51          | 0.36        | 0.92         | 0.85          | 0.52        |
+---------+----------------+-----------------+---------------+--------------+---------------+-------------+--------------+---------------+-------------+
Lectura honesta: con codigos de 6 digitos densos casi no hay cadenas de un solo hijo que comprimir, asi que Radix ~ Trie (y en Python el diccionario por nodo puede igualar el ahorro). El AVL usa 1 nodo por clave pero su busqueda es O(L log n).
```

```text
[P06] Caso favorable a Radix: claves con cola larga (codigo postal + ruta/puerta de ~24 caracteres)
+--------+-----------------+-----------------+---------------+----------------------------+
| Claves | Trie nodos/mem  | Radix nodos/mem | AVL nodos/mem | Compresion                 |
+--------+-----------------+-----------------+---------------+----------------------------+
| 500    | 12760 / 3233KB  | 674 / 165KB     | 500 / 47KB    | 18.9x menos nodos en Radix |
| 2000   | 50745 / 12849KB | 2616 / 641KB    | 2000 / 188KB  | 19.4x menos nodos en Radix |
+--------+-----------------+-----------------+---------------+----------------------------+
Radix gana cuando hay colas largas sin ramificar (matriculas, rutas, geohash largos): cada cola es UNA arista, no ~L nodos.
```

---

## Pregunta 7 — Balanceo de cargas (AVL vs Rojo-Negro)

### Prompt a la IA (propuesto)
> Actúa como especialista en árboles balanceados. Los paquetes se ordenan por clave compuesta (peso, volumen) en el almacén central. ¿Qué estructura rinde mejor cuando las lecturas superan ampliamente a las escrituras y viceversa? Justifica con altura máxima, rotaciones por inserción/borrado y complejidades.

### Respuesta de la IA
_(pegar transcripción literal)_

### Análisis crítico individual
Hallazgos verificados con el código:
- Supuesto declarado: clave compuesta (peso, volumen, id) y "escritura" = inserción **y borrado** (el borrado es donde más difieren las estructuras).
- AVL: altura ≤ 1,44 log₂ n; Rojo-Negro: ≤ 2 log₂ n. Con claves aleatorias la diferencia de profundidad media es pequeña (≈ 1–2 % de comparaciones por lectura); con entradas ordenadas es grande (AVL mucho más bajo).
- Rojo-Negro hace menos rotaciones por escritura y fue más rápido en las cargas con muchas escrituras; AVL no fue sustancialmente mejor en lectura con claves aleatorias. Conviene decir esto en vez de repetir la regla sin matices.
- Ambos árboles se validan con invariantes (balance AVL; color, altura negra) y con consultas por rango (consolidar pallets por rango de peso).

_Integrante 1: …  ·  Integrante 2: …  ·  Integrante 3: …  ·  Integrante 4: …_

### Solución unificada
| Criterio | AVL | Rojo-Negro |
|---|---|---|
| Altura | ≤ 1,44 log₂ n | ≤ 2 log₂ n |
| Rotaciones en inserción | ≤ 2 | ≤ 2 |
| Rotaciones en borrado | O(log n) | ≤ 3 |
| Búsqueda | O(log n), más baja | O(log n) |
| Mejor para | lecturas ≫ escrituras, entradas ordenadas | escrituras frecuentes |

**Decisión:** AVL en catálogos de lectura intensiva (≥ 90 % lecturas) o cuando llegan lotes ordenados; Rojo-Negro cuando la mezcla tiene muchas inserciones/borrados (consolidación continua de pallets). Costo en ambos: O(log n) por operación, O(n) de espacio.

**Evidencia medida**

```text
[P07] AVL vs Rojo-Negro: clave compuesta (peso, volumen, id), borrado y consulta por rango
AVL        | n=133 tras borrar 1/3 | altura=8 | invariantes OK | pallets con peso en [10,12] kg: 5
Rojo-Negro | n=133 tras borrar 1/3 | altura=9 | invariantes OK | pallets con peso en [10,12] kg: 5
Carga 95/5 | AVL: h=11 cmp/lectura=8.18 | RBT: h=11 cmp/lectura=8.32
Carga 5/95 | AVL: rot/escritura=0.49 | RBT: rot/escritura=0.41
```

```text
[P07] Benchmark AVL vs Rojo-Negro (escrituras = 50% insertar + 50% borrar; 20,000 operaciones)
+---------------------------+-----------------------------------+----------------------------------+
| Escenario                 | AVL                               | Rojo-Negro                       |
+---------------------------+-----------------------------------+----------------------------------+
| n=1000 95% lect / 5% escr | h=12 cmp/L=9.15 rot/E=0.50 34ms   | h=13 cmp/L=9.29 rot/E=0.45 23ms  |
| n=1000 5% lect / 95% escr | h=12 cmp/L=9.19 rot/E=0.50 153ms  | h=13 cmp/L=9.27 rot/E=0.41 43ms  |
| n=5000 95% lect / 5% escr | h=15 cmp/L=11.52 rot/E=0.50 37ms  | h=15 cmp/L=11.69 rot/E=0.43 29ms |
| n=5000 5% lect / 95% escr | h=15 cmp/L=11.55 rot/E=0.50 160ms | h=16 cmp/L=11.71 rot/E=0.42 44ms |
+---------------------------+-----------------------------------+----------------------------------+
cmp/L = comparaciones por lectura (profundidad media); rot/E = rotaciones por escritura.
```

```text
[P07] Peor patron de entrada: inserciones en orden ascendente (carga de pallets ya ordenada)
+------+--------------------+--------------------+
| n    | AVL                | Rojo-Negro         |
+------+--------------------+--------------------+
| 1000 | h=10 rot=990 7ms   | h=17 rot=983 2ms   |
| 5000 | h=13 rot=4987 38ms | h=22 rot=4978 10ms |
+------+--------------------+--------------------+
Lectura: AVL mantiene el arbol mas bajo (mejor para lecturas); Rojo-Negro rota menos por escritura (mejor para escrituras).
```

---

## Pregunta 8 — Historial y reversión (Lista doblemente enlazada + Pila)

### Prompt a la IA (propuesto)
> Actúa como ingeniero de software transaccional. Propón una estructura que combine lista doblemente enlazada (cola de carga con inserción/extracción en cualquier punto) y una pila LIFO de transacciones para Undo/Rollback. Incluye operaciones (cargar, intercalar, mover, quitar, deshacer), operación inversa de cada una, complejidades y cómo evitar punteros colgantes y fugas de memoria.

### Respuesta de la IA
_(pegar transcripción literal)_

### Análisis crítico individual
Hallazgos verificados con el código:
- La estructura debe incluir la operación **mover** (reorganizar en posiciones intermedias): se guarda el predecesor original y el inverso la reubica.
- Memoria: un nodo removido sigue vivo mientras la pila lo referencie; `commit()` vacía la pila y libera (se comprueba con `weakref`). `max_history` acota la auditoría.
- Coherencia: al desenlazar se anulan `prev/next` y se marca el nodo inactivo; `check_invariants()` valida enlaces, conteo e índice. Se prueba con 3.000 operaciones aleatorias contra una lista de Python como modelo.

_Integrante 1: …  ·  Integrante 2: …  ·  Integrante 3: …  ·  Integrante 4: …_

### Solución unificada
```text
DLL: nodo{id, prev, next, activo}   índice id → nodo   Pila: comandos (op, nodo, predecesor_previo)
cargar(id)      → enlazar al final            inverso: desenlazar
intercalar(id,r)→ enlazar tras r              inverso: desenlazar
quitar(n)       → guardar n.prev; desenlazar  inverso: reenlazar tras el predecesor guardado
mover(n,r)      → guardar n.prev; desenlazar; enlazar tras r   inverso: desenlazar; reenlazar tras el predecesor guardado
undo(): pop de la pila y ejecutar el inverso     rollback(k): k veces undo     commit(): vaciar pila
```
Todas las operaciones O(1) con referencia directa al nodo; espacio O(n + t) con t transacciones (acotable con `max_history`).

**Evidencia medida**

```text
[P08] Cola de Carga (DLL) + Transacciones Undo/Rollback (Pila LIFO)
Cargar 101,102,103 + intercalar 102B tras 102 : ['G-101', 'G-102', 'G-102B', 'G-103'] | OK (4 nodos, pila=4)
Mover G-103 al inicio                         : ['G-103', 'G-101', 'G-102', 'G-102B'] | OK (4 nodos, pila=5)
Quitar G-101                                  : ['G-103', 'G-102', 'G-102B'] | OK (3 nodos, pila=6)
UNDO (restaura G-101 en su posicion)          : ['G-103', 'G-101', 'G-102', 'G-102B'] | OK (4 nodos, pila=5)
UNDO (deshace el movimiento de G-103)         : ['G-101', 'G-102', 'G-102B', 'G-103'] | OK (4 nodos, pila=4)
UNDO (quita G-102B)                           : ['G-101', 'G-102', 'G-103'] | OK (3 nodos, pila=3)
Nodo removido vivo en memoria con la pila activa: True | tras commit(): False (liberado)
Historial acotado (max_history=100): 1000 cargas -> pila=100 (memoria de auditoria constante)
```

```text
[P08] Benchmark: operaciones O(1) por transaccion y rollback masivo
+----------+----------+-----------+----------+---------+----------------+--------------------------+
| Paquetes | us/carga | us/quitar | us/mover | us/undo | Deshechas/Pila | Invariantes + cola vacia |
+----------+----------+-----------+----------+---------+----------------+--------------------------+
| 2000     | 0.90     | 0.53      | 0.94     | 0.40    | 3500/3500      | OK                       |
| 20000    | 1.01     | 0.62      | 1.06     | 0.43    | 35000/35000    | OK                       |
| 200000   | 1.69     | 1.27      | 2.36     | 0.59    | 350000/350000  | OK                       |
+----------+----------+-----------+----------+---------+----------------+--------------------------+
Lectura: el costo por operacion es ~constante al crecer n x100 => O(1); el rollback total deja la cola vacia e integra.
```

---

## Pregunta 9 — Proximidad espacial (KD-Tree vs Geohash/cuadrícula)

### Prompt a la IA (propuesto)
> Actúa como experto en indexación espacial. Para asignar la entrega urgente al mensajero disponible más cercano, compara Árbol KD, cuadrícula espacial/Geohash y R-Tree para k-NN. Analiza el comportamiento con una flota cuyas coordenadas cambian cada pocos segundos (costo de actualización vs consulta), el efecto borde del Geohash y complejidades.

### Respuesta de la IA
_(pegar transcripción literal)_

### Análisis crítico individual
Hallazgos verificados con el código:
- Una cuadrícula que solo revisa las 9 celdas vecinas **devuelve vecinos incorrectos** cuando el k-ésimo más cercano está a más de una celda: en una prueba con 200 mensajeros falló en ≈ 19 % de las consultas. La versión corregida expande en anillos hasta que el k-ésimo candidato está a menos de r·tamaño_de_celda; coincide con la fuerza bruta en todas las pruebas.
- El Geohash tiene efecto borde (puntos cercanos con prefijos distintos): se resuelve consultando celdas vecinas, aquí con la misma expansión en anillos.
- "El KD-Tree es peor con flotas móviles" depende de cuántas consultas haya por tick: con muchas consultas la reconstrucción se amortiza y el KD alcanza o supera a las cuadrículas; con una sola consulta ni siquiera conviene indexar.

_Integrante 1: …  ·  Integrante 2: …  ·  Integrante 3: …  ·  Integrante 4: …_

### Solución unificada
| Estructura | Construcción | Actualizar un agente | k-NN | Observación |
|---|---|---|---|---|
| Fuerza bruta | — | O(1) | O(n) | verificador; óptimo con pocas consultas |
| KD-Tree | O(n log n) | reconstruir | ≈ O(log n + k) | ideal para datos casi estáticos o muchas consultas por lote |
| Cuadrícula/Geohash | O(n) | **O(1)** | ≈ O(k) con densidad uniforme | ideal para flota móvil; peor caso O(n) si los datos se concentran |
| R-Tree | O(n log n) | O(log n) | ≈ O(log n + k) | alternativa dinámica para datos no uniformes (no implementado) |

**Decisión:** índice Geohash/cuadrícula con expansión en anillos para la flota móvil (actualización O(1) por posición); KD-Tree para análisis por lotes o zonas estáticas; fuerza bruta como verificador de pruebas.

**Evidencia medida**

```text
[P09] Proximidad Espacial: KD-Tree vs Cuadricula vs Geohash vs Fuerza Bruta
Consulta (10.0, 10.0) km, k=3 | geohash de la consulta: d34k41 (celda ~1.22 x 0.61 km)
  Fuerza bruta : [('M-00017', 2.64), ('M-00007', 3.13), ('M-00027', 3.68)]
  KD-Tree      : [('M-00017', 2.64), ('M-00007', 3.13), ('M-00027', 3.68)]
  Cuadricula   : [('M-00017', 2.64), ('M-00007', 3.13), ('M-00027', 3.68)]
  Geohash      : [('M-00017', 2.64), ('M-00007', 3.13), ('M-00027', 3.68)]
Paridad con fuerza bruta en 300 consultas aleatorias (300 mensajeros, k=5): fallos {'kd': 0, 'grid': 0, 'geohash': 0}
```

```text
[P09] Consulta estatica k=5: construccion y tiempo por consulta (us)
+------------+-------------------------------+------------+-----------+--------------+
| Mensajeros | KD build ms / us por consulta | Cuadricula | Geohash   | Fuerza bruta |
+------------+-------------------------------+------------+-----------+--------------+
| 1000       | 1.4 / 13                      | 0.8 / 13   | 3.4 / 152 | - / 293      |
| 5000       | 8.7 / 24                      | 4.2 / 42   | 16.8 / 96 | - / 1755     |
+------------+-------------------------------+------------+-----------+--------------+
```

```text
[P09] Flota movil: costo de UN tick (todos se mueven + Q consultas k=5), n=2000
+----------------+------------------+------------+----------+--------------+-------------------------+
| Consultas/tick | KD (reconstruir) | Cuadricula | Geohash  | Fuerza bruta | Mas rapido              |
+----------------+------------------+------------+----------+--------------+-------------------------+
| 1              | 2.9 ms           | 0.8 ms     | 6.6 ms   | 0.6 ms       | Fuerza bruta            |
| 20             | 3.4 ms           | 1.2 ms     | 9.0 ms   | 11.4 ms      | Cuadricula (actualizar) |
| 200            | 5.9 ms           | 4.7 ms     | 33.8 ms  | 118.2 ms     | Cuadricula (actualizar) |
| 1000           | 16.8 ms          | 21.2 ms    | 134.4 ms | 642.5 ms     | KD (reconstruir)        |
+----------------+------------------+------------+----------+--------------+-------------------------+
Lectura: con 1 consulta por tick, ni siquiera conviene indexar (la fuerza bruta evita el costo de mantener el indice); con pocas, actualizar celdas (O(1) por agente) vence a reconstruir el KD (O(n log n)); con muchas consultas por tick, la reconstruccion se amortiza y el KD (consulta ~O(log n)) alcanza o supera a las cuadriculas.
```

---

## Pregunta 10 — Conectividad de mínimo costo (Kruskal vs Prim)

### Prompt a la IA (propuesto)
> Actúa como experto en algoritmos voraces. LogiX tenderá fibra óptica entre 40 centros logísticos con costo mínimo. Compara formalmente Kruskal (Union-Find con compresión de caminos y unión por rango) y Prim (min-heap), y Prim con arreglo para grafos densos. ¿Bajo qué densidad conviene cada uno? Incluye complejidades y demuestra por qué producen el mismo costo.

### Respuesta de la IA
_(pegar transcripción literal)_

### Análisis crítico individual
Hallazgos verificados con el código:
- El enunciado dice "tema" suelto en el título; es un error tipográfico que no cambia el problema.
- Con 40 centros el grafo es completo (780 aristas): las tres variantes dan **el mismo costo** (el MST es único en peso aunque varíe el conjunto de aristas ante empates). Tender todos los enlaces costaría ≈ 100× el MST.
- La regla "Prim denso para grafos densos" se cumple en este barrido recién a partir de una densidad de ≈ 0,3–0,4; por debajo, Kruskal y Prim con heap son equivalentes o mejores. Con Python, el `sort` en C favorece a Kruskal frente a su costo teórico.
- Grafo no conexo: no existe un árbol de expansión; el código lo detecta y lanza error.

_Integrante 1: …  ·  Integrante 2: …  ·  Integrante 3: …  ·  Integrante 4: …_

### Solución unificada
| Algoritmo | Tiempo | Espacio | Conviene si |
|---|---|---|---|
| Kruskal + Union-Find (compresión + rango) | O(E log E) = O(E log V) | O(V + E) | grafo disperso, aristas ya listadas |
| Prim + min-heap | O(E log V) | O(V + E) | densidad media, lista de adyacencia |
| Prim + arreglo | O(V²) | O(V²) | grafo denso (E ≈ V²) |

Union-Find: cada operación en O(α(n)) amortizado ≈ O(1). Corrección: la propiedad del corte garantiza que la arista más barata que cruza cualquier corte pertenece a algún MST; ambos algoritmos la aplican.

**Decisión para los 40 centros:** grafo completo ⇒ Prim con arreglo O(V²)=1.600 pasos es el más simple y suficiente; Kruskal da el mismo resultado y se usa como verificación cruzada.

**Evidencia medida**

```text
[P10] Red de Fibra Optica entre 40 Centros Logisticos (780 aristas candidatas)
Aristas candidatas=780 | Aristas en el MST=39 (= V-1)
Costo MST: Kruskal=440.345 | Prim-Heap=440.345 | Prim-Denso=440.345 | coinciden: True
Costo de tender TODOS los enlaces candidatos: 43,618.0 -> el MST cuesta 1.0% de eso
Kruskal: aristas examinadas=124/780 (corta al completar V-1), pasos Union-Find=356 | Prim-Heap: push=780, pop=124
Primeros enlaces elegidos (u, v, costo): [(1, 39, 2.599), (14, 18, 2.715), (14, 19, 2.816), (10, 15, 3.698), (24, 37, 3.811)]
```

```text
[P10] Barrido de densidad (V=150): tiempo (ms, mejor de 5) y operaciones
+----------+-------+---------+-----------+------------+-----------+-------------------+--------------+--------------+------------+
| Densidad | E     | Kruskal | Prim-Heap | Prim-Denso | (+matriz) | Op Kruskal ~ElogE | Op Prim-Heap | Op Denso V^2 | Mas rapido |
+----------+-------+---------+-----------+------------+-----------+-------------------+--------------+--------------+------------+
| 0.05     | 558   | 0.28    | 0.18      | 0.74       | +0.11     | 5,091             | 931          | 22,500       | Prim-Heap  |
| 0.10     | 1117  | 0.33    | 0.32      | 0.75       | +0.11     | 11,310            | 1,661        | 22,500       | Prim-Heap  |
| 0.20     | 2235  | 0.52    | 0.49      | 0.74       | +0.23     | 24,866            | 2,706        | 22,500       | Prim-Heap  |
| 0.40     | 4470  | 1.16    | 1.07      | 0.93       | +0.38     | 54,203            | 4,940        | 22,500       | Prim-Denso |
| 0.60     | 6705  | 1.72    | 1.39      | 0.79       | +0.47     | 85,227            | 6,990        | 22,500       | Prim-Denso |
| 0.80     | 8940  | 2.41    | 2.12      | 0.89       | +0.70     | 117,346           | 9,267        | 22,500       | Prim-Denso |
| 1.00     | 11175 | 3.13    | 2.49      | 0.79       | +0.81     | 150,281           | 11,592       | 22,500       | Prim-Denso |
+----------+-------+---------+-----------+------------+-----------+-------------------+--------------+--------------+------------+
Lectura: en grafos dispersos Kruskal/Prim-Heap hacen ~E log E / ~E log V operaciones (E << V^2); al acercarse a E ~ V^2 el costo log del heap/ordenamiento pesa y Prim con arreglo O(V^2) se vuelve competitivo (si ya se tiene la matriz).
```

---

## Supuestos declarados
1. Red vial: pesos ≥ distancia en la métrica de la heurística (condición de admisibilidad de A*).
2. Pregunta 3: tres flujos (estándar, perecedero, alto valor) con una banda de capacidad finita; "alto valor crítico" = valor ≥ 5.000.
3. Pregunta 7: clave compuesta (peso, volumen, id); escrituras = 50 % inserciones y 50 % borrados.
4. Pregunta 9: plano local en km centrado en Medellín para el índice Geohash (precisión 6 ≈ 1,2 × 0,6 km por celda).
5. Tiempos en Python (CPython) sobre una máquina de escritorio: sirven para tendencias, no como valores absolutos.
