from io_utils import load_project, export_layer

from sweep_line import SweepLine

from reconstruction import ReconstructionEngine

from visualization import (
    draw_original_layers,
    draw_result, 
    debug_dcel
)

from geometry import Segment


def build_segments(dcel):
    segments = []
    used = set()

    for edge in dcel.edges:
        if edge.name in used:
            continue
        
        # VALIDACIÓN CRUCIAL
        if edge.origin is None or edge.twin is None or edge.twin.origin is None:
            print(f"ADVERTENCIA: Saltando arista incompleta: {edge.name}")
            continue

        used.add(edge.name)
        used.add(edge.twin.name)

        s = Segment(
            name=edge.name,
            p1=edge.origin.point,
            p2=edge.destination.point,
            edge=edge
        )
        segments.append(s)

    return segments


# 1. CARGA LAS CAPAS LIMPIAS
layer_names = ["layer01", "layer03","layer04"]
dcel, layers = load_project(layer_names)

# 2. PROCESO
sweep = SweepLine()
segments = build_segments(dcel)
for s in segments:
    sweep.add_segment(s)
intersections = sweep.run()

print("Visualizando estado inicial de la carga...")
debug_dcel(dcel) # <--- Aquí verás si las flechas salen de donde deben

# 3. RECONSTRUCCIÓN
reconstruction = ReconstructionEngine(dcel)
reconstruction.rebuild(intersections)
print("Visualizando estado tras reconstrucción...")
debug_dcel(dcel) # <--- Aquí verás si los nuevos vértices dividieron bien las aristas

# 4. EXPORTAR RESULTADO NUEVO
export_layer(dcel, "resultado")

# 5. VALIDAR Y DIBUJAR
dcel.validate()
draw_result(dcel, intersections)