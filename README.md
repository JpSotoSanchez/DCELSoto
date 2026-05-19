# Geometric Overlay Engine – DCEL Construction and Face Classification

This project implements a **geometric overlay algorithm** that reads multiple planar subdivisions (layers), computes their overlay (the arrangement formed by all edges), builds a **Doubly Connected Edge List (DCEL)**, and determines which faces of the new arrangement correspond to active regions from the original layers.

The code is written in **Python** and relies on **Matplotlib** for visualisation. A detailed debug log is written to `debug/debug_overlay.log` for troubleshooting missing edges or faces.

---

## Table of Contents

1. [Algorithm Overview](#algorithm-overview)
2. [Input Format](#input-format)
3. [Output Format](#output-format)
4. [Code Structure](#code-structure)
5. [Dependencies](#dependencies)
6. [How to Run](#how-to-run)
7. [Visualisations](#visualisations)
8. [Debugging](#debugging)
9. [Configuration](#configuration)
10. [Authors / Credits](#authors--credits)

---

## Algorithm Overview

1. **Load Layers**  
   Each layer is stored in four plain-text files (`.vertices`, `.aristas`, `.caras`, `.activos`) that describe a planar subdivision as a DCEL.  
   The script resolves internal references (vertex, edge, face pointers) and collects all edges.

2. **Incremental Intersection Detection**  
   As each layer is loaded, its segments are crossed against all previously loaded segments. Intersection points are recorded on each segment.

3. **Segment Splitting & Unification**  
   All segments are split at every intersection point, resulting in a set of atomic, non-overlapping sub-segments.  
   Collinear overlapping segments are then merged to avoid duplicated geometry.

4. **DCEL Construction**  
   - **Vertices** are created at every unique endpoint.  
   - **Half-edges** are created in opposite pairs for each sub-segment.  
   - Half-edges are sorted angularly around each vertex and linked (`siguiente` / `anterior`) to form closed cycles.

5. **Face Formation**  
   Cycles of half-edges that have positive area become **finite faces**.  
   All remaining half-edges are assigned to the **infinite face** (`f0`). Each cyclic component of these edges becomes an internal boundary (hole) of `f0`.

6. **Active Face Classification**  
   Original active faces (polygons) are tested against each new face using a point-in-polygon test. A new face is marked **active** if its interior lies inside at least one original active polygon.

7. **Export**  
   The resulting DCEL is exported to `.vertices`, `.aristas`, `.caras` and `.activos` files in the `resultados/` folder.

---

## Input Format

Each layer is represented by four files with the same base name:

### `<layer>.vertices`

```text
Nombre  x       y       Incidente
v1    10.0    20.0    e1
v2    30.0    20.0    e2
...
```

- **Nombre**: vertex identifier.
- **x, y**: coordinates (floating point).
- **Incidente**: name of an incident half-edge (or `None`).

---

### `<layer>.aristas`

```text
Nombre  Origen  Pareja  Cara    Sigue   Antes
e1    v1      e2      c1      e3      e5
...
```

- **Nombre**: half-edge identifier.
- **Origen**: vertex where the half-edge starts.
- **Pareja**: twin half-edge (opposite direction).
- **Cara**: face to which this half-edge belongs (or `None` initially).
- **Sigue**: next half-edge in the face cycle.
- **Antes**: previous half-edge.

---

### `<layer>.caras`

```text
Nombre  Interno           Externo
c1    [e10,e11]          e1
...
```

- **Interno**: comma-separated list of half-edges that represent internal holes (enclosed in `[]`). Use `None` if no holes.
- **Externo**: name of one half-edge of the outer cycle, or `None`.

---

### `<layer>.activos`

```text
Caras Activas
c1
c3
...
```

Lists the names of the active faces of this layer (one per line, no header lines after the first two).

> **Note:** All identifiers in a layer are suffixed with the layer name during loading to avoid collisions across layers.

---

## Output Format

After processing, the script generates in the `resultados/` folder:

- `resultado.vertices`
- `resultado.aristas`
- `resultado.caras`
- `resultado.activos`

These files follow exactly the same format as the input, describing the overlay arrangement and which of its faces are active.

---

## Code Structure

| Section | Description |
|---|---|
| `Punto` | Immutable point class with distance method. |
| `SegmentoOverlay` | Segment with layer tag and list of intersection points. |
| `NodoVertice`, `NodoArista`, `NodoCara` | DCEL node classes. |
| Geometrical functions | Point equality, segment parameter, orientation, intersection (handles collinear and overlapping cases). |
| `cargar_layer()` | Reads the four files of one layer and builds DCEL objects, resolving cross-references. |
| `extraer_segmentos()` | Converts half-edges (twin pairs) into directed segments. |
| `partir_segmentos()` | Splits segments at every recorded intersection point. |
| `unificar_segmentos_colineales()` | Merges overlapping collinear segments into a minimal set of non-redundant sub-segments. |
| `crear_vertices()` | Creates unique DCEL vertices from segment endpoints. |
| `crear_aristas()` | Creates a pair of twin half-edges for each sub-segment. |
| `conectar_aristas()` | Sorts half-edges angularly around each vertex and links `siguiente`/`anterior`. |
| `crear_caras()` | Traverses half-edge cycles to form finite faces (ignores cycles with area ≤ 0). |
| `crear_cara_infinita()` | Assigns remaining half-edges to the infinite face `f0`, grouping them into internal cycles (holes). |
| Classification | Uses point-in-polygon to determine which new faces lie inside original active polygons. |
| Visualisation functions | `visualizar_capas_originales()`, `visualizar_resultado_final()`, `visualizar_resultado_interactivo()`, and others. |
| `main()` | Orchestrates the whole process and writes the debug log. |

---

## Dependencies

- **Python 3.7+** (uses `dataclasses`, `typing`)
- **Matplotlib ≥ 3.0**
- Standard libraries: `math`, `os`, `sys`, `collections`

Install Matplotlib with:

```bash
pip install matplotlib
```

---

## How to Run

1. Place your layer files in subdirectories as described in [Configuration](#configuration).

2. Create the output folder `resultados/` (the script does not create it automatically). The `debug/` folder will be created if it does not exist.

3. Edit the `main()` function (around line 600) to select which layers to process. Uncomment one of the `listaLayers` assignments and adjust the paths as needed. Example:

   ```python
   listaLayers = ["equipo67/layer01", "equipo67/layer02", "equipo67/layer03"]
   ```

4. Run the script:

   ```bash
   python main_adaptado_con_pygame_y_matplotlib.py
   ```

5. Close each visualisation window to proceed to the next step. The script will output the final result to the `resultados/` directory and print a summary to the console.

---

## Visualisations

The script opens several Matplotlib figures sequentially:

1. **Original Layers** – Each layer is drawn with a different colour; all original edges and vertices are shown.

2. **DCEL Vertices** – All unique points (original vertices + intersection points) are plotted, labelled if few enough.

3. **DCEL Edges** – All half-edges are drawn with directional arrows (blue forward, red backward).

4. **Final Overlay (Static)** – Each face is filled with a distinct colour; active faces appear coloured while inactive faces are white. Edges and vertices are also shown.

5. **Interactive Overlay** – Click on any face to toggle its active/inactive state. Checkboxes allow toggling the display of:
   - Face names (at centroids)
   - Vertex names
   - Edge names and their `siguiente` links
   - Directional arrows for face cycles: blue for outer boundary, red for inner holes (offset from the edge for clarity).

---

## Debugging

A comprehensive trace is written to `debug/debug_overlay.log`. This log includes:

- Every vertex, edge, and face read from the input files.
- Resolved internal references.
- All detected intersections (between layers and within the same layer).
- The splitting and unification of segments.
- The construction of the DCEL: vertex creation, angular sorting, linking of half-edges.
- Face cycle formation, area calculations, and which cycles are kept or discarded.
- Final classification of active faces.
- A summary of the final DCEL (all vertices, edges, and faces).

If you encounter missing faces, dangling edges, or unexpected results, inspect this log to trace the problem. Compare the logged cycles with the input geometry.

---

## Configuration

The script expects your layer files to be organised in subdirectories, one per data set. For example:

```text
project/
├── main_adaptado_con_pygame_y_matplotlib.py
├── debug/
├── resultados/
├── equipo67/
│   ├── layer01.vertices
│   ├── layer01.aristas
│   ├── layer01.caras
│   ├── layer01.activos
│   ├── layer02.vertices
│   └── …
└── equipoALCARAZ/
    ├── layer01.vertices
    └── …
```

Inside `main()`, modify `listaLayers` to match the relative paths (subdirectory + base name) of the layers you want to process. The base name is the filename without the extension (e.g., `equipo67/layer01` refers to `equipo67/layer01.vertices`, etc.).

---

## Authors / Credits

This implementation was developed for a computational geometry course/project.  
It is an adapted version that uses Matplotlib instead of Pygame, with incremental intersection detection, collinear segment unification, and an extensive debug trace.

For questions or improvements, please refer to the project documentation or contact the authors.