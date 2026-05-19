import matplotlib.pyplot as plt
import math
import random
from geometry import EPS

def debug_dcel(dcel):
    fig, ax = plt.subplots(figsize=(14, 14))
    
    # Paleta de colores para distinguir aristas adyacentes
    colors = ['#FF5733', '#33FF57', '#3357FF', '#F333FF', '#FF33A1', '#33FFF5']

    for i, e in enumerate(dcel.edges):
        if not e.origin or not e.twin or not e.twin.origin:
            continue

        p1, p2 = e.origin.point, e.destination.point
        x1, y1, x2, y2 = p1.x, p1.y, p2.x, p2.y

        dx, dy = x2 - x1, y2 - y1
        L = math.sqrt(dx*dx + dy*dy)
        if L < EPS: continue

        # Normalización y Offset
        nx, ny = -dy/L, dx/L
        
        # Separamos los Twins: El original va a un lado, el twin irá al otro
        offset = 0.25 
        sx1, sy1 = x1 + nx * offset, y1 + ny * offset
        sx2, sy2 = x2 + nx * offset, y2 + ny * offset

        color = colors[i % len(colors)]

        # Dibujar arista con flecha grande
        ax.annotate("", xy=(sx2, sy2), xytext=(sx1, sy1),
                    arrowprops=dict(arrowstyle="->", color=color, lw=2, mutation_scale=20))

        # Etiquetas - Calculamos punto medio
        mx, my = (sx1 + sx2) / 2, (sy1 + sy2) / 2
        
        # Nombre de la arista (Fondo blanco para que sea legible sobre líneas)
        ax.text(mx, my, e.name, fontsize=10, color='black', fontweight='bold',
                bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=1))
        
        # Puntero al siguiente (Un poco más desplazado)
        if e.next:
            ax.text(mx + nx*0.3, my + ny*0.3, f"n: {e.next.name}", 
                    fontsize=8, color=color, style='italic',
                    bbox=dict(facecolor='white', alpha=0.5, edgecolor='none', pad=0))

    # Vértices
    for v in dcel.vertices:
        ax.plot(v.point.x, v.point.y, 'ko', markersize=6, zorder=5)
        ax.text(v.point.x + 0.15, v.point.y + 0.15, v.name, 
                fontsize=11, color='darkred', fontweight='black')

    ax.set_aspect('equal')
    plt.title("DEBUG DCEL V2: Inspección de Conectividad", fontsize=15)
    plt.grid(True, which='both', linestyle='--', alpha=0.5)
    
    # Ajustar límites para que no se corten etiquetas
    all_x = [v.point.x for v in dcel.vertices]
    all_y = [v.point.y for v in dcel.vertices]
    if all_x and all_y:
        ax.set_xlim(min(all_x)-1, max(all_x)+1)
        ax.set_ylim(min(all_y)-1, max(all_y)+1)

    plt.show()

LAYER_COLORS = {
    "layer01": "#4E79A7",
    "layer02": "#F28E2B",
    "layer03": "#E15759",
    "layer04": "#76B7B2",
    "layer05": "#59A14F",
}

# =========================================================
# EXTRAER POLÍGONO
# =========================================================

def face_polygon(face):

    if face.outer_component is None:
        return None

    points = []

    start = face.outer_component

    current = start

    visited = set()

    while current.name not in visited:

        visited.add(current.name)

        p = current.origin.point

        points.append((p.x, p.y))

        current = current.next

        if current is None:
            return None

    return points


# =========================================================
# DIBUJAR CARA
# =========================================================

def draw_face(ax, face, color, fill=False, alpha=0.35):

    polygon = face_polygon(face)

    if polygon is None:
        return

    xs = [p[0] for p in polygon]
    ys = [p[1] for p in polygon]

    xs.append(xs[0])
    ys.append(ys[0])

    if fill:
        ax.fill(xs, ys, color=color, alpha=alpha)

    ax.plot(xs, ys, color=color)


# =========================================================
# FIGURA 1
# =========================================================

def draw_original_layers(layers):

    fig, ax = plt.subplots(figsize=(12, 12))

    used_labels = set()

    for layer in layers:

        color = LAYER_COLORS.get(
            layer.name,
            "gray"
        )

        for face in layer.faces:

            is_active = (
                face.name in layer.active_faces
            )

            label = None

            if layer.name not in used_labels:

                label = layer.name

                used_labels.add(layer.name)

            draw_face(
                ax,
                face,
                color=color,
                fill=is_active
            )

    ax.set_title("Capas Originales")

    ax.set_aspect("equal")

    ax.legend(used_labels)

    plt.tight_layout()

    plt.show()


# =========================================================
# FIGURA 2
# =========================================================

def draw_result(dcel, intersections):

    fig, ax = plt.subplots(figsize=(12, 12))

    # =====================================================
    # FACES
    # =====================================================

    for face in dcel.faces:

        if face.name == "F0":
            continue

        draw_face(
            ax,
            face,
            color="lightblue",
            fill=True
        )

    # =====================================================
    # EDGES
    # =====================================================

    drawn = set()

    for edge in dcel.edges:

        if edge.name in drawn:
            continue

        drawn.add(edge.name)
        drawn.add(edge.twin.name)

        p1 = edge.origin.point
        p2 = edge.destination.point

        ax.plot(
            [p1.x, p2.x],
            [p1.y, p2.y],
            color="black",
            linewidth=1
        )

    # =====================================================
    # VERTICES
    # =====================================================

    for vertex in dcel.vertices:

        ax.scatter(
            vertex.point.x,
            vertex.point.y,
            color="black",
            s=15
        )

    # =====================================================
    # INTERSECTIONS
    # =====================================================

    for point, _ in intersections:

        ax.scatter(
            point.x,
            point.y,
            color="red",
            s=40
        )

    ax.set_title("Resultado Reconstruido")

    ax.set_aspect("equal")

    plt.tight_layout()

    plt.show()