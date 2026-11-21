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

{{DEMO:P01}}

{{BENCH:P01}}

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

{{DEMO:P02}}

{{BENCH:P02}}

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

{{DEMO:P03}}

{{BENCH:P03}}

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

{{DEMO:P04}}

{{BENCH:P04}}

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

{{DEMO:P05}}

{{BENCH:P05}}

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

{{DEMO:P06}}

{{BENCH:P06}}

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

{{DEMO:P07}}

{{BENCH:P07}}

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

{{DEMO:P08}}

{{BENCH:P08}}

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

{{DEMO:P09}}

{{BENCH:P09}}

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

{{DEMO:P10}}

{{BENCH:P10}}

---

## Supuestos declarados
1. Red vial: pesos ≥ distancia en la métrica de la heurística (condición de admisibilidad de A*).
2. Pregunta 3: tres flujos (estándar, perecedero, alto valor) con una banda de capacidad finita; "alto valor crítico" = valor ≥ 5.000.
3. Pregunta 7: clave compuesta (peso, volumen, id); escrituras = 50 % inserciones y 50 % borrados.
4. Pregunta 9: plano local en km centrado en Medellín para el índice Geohash (precisión 6 ≈ 1,2 × 0,6 km por celda).
5. Tiempos en Python (CPython) sobre una máquina de escritorio: sirven para tendencias, no como valores absolutos.
