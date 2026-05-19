from dataclasses import dataclass
from pathlib import Path
from typing import List, Set

from dcel import (
    Vertex,
    HalfEdge,
    Face,
    DCEL
)

from geometry import Point


DATA_DIR = Path("data")


@dataclass
class LayerData:

    name: str

    vertices: List[Vertex]
    edges: List[HalfEdge]
    faces: List[Face]

    active_faces: Set[str]


# =========================================================
# UTILIDADES
# =========================================================

def clean_lines(path):

    with open(path, "r", encoding="utf-8") as f:

        lines = []

        for line in f:

            line = line.strip()

            if not line:
                continue

            if line.startswith("#"):
                continue

            if line.startswith("Archivo"):
                continue

            lines.append(line)

        return lines


# =========================================================
# PARSER LISTAS
# =========================================================

def parse_list_field(raw):

    raw = raw.strip()

    if raw in ("None", "[]", ""):
        return []

    raw = raw.strip("[]")

    return [
        item.strip()
        for item in raw.split(",")
        if item.strip()
    ]


# =========================================================
# LOAD LAYER
# =========================================================

def load_layer(layer_name: str):

    vertices = []
    edges = []
    faces = []

    active_faces = set()

    # =====================================================
    # VERTICES
    # =====================================================

    path = DATA_DIR / f"{layer_name}.vertices"

    for line in clean_lines(path):

        if line.startswith("Nombre"):
            continue

        parts = line.split()

        if len(parts) < 3:
            continue

        if len(parts) == 3:

            name, x, y = parts

            incident = "None"

        else:

            name = parts[0]
            x = parts[1]
            y = parts[2]
            incident = parts[3]

        v = Vertex(
            name=name,
            point=Point(float(x), float(y))
        )

        v._incident_name = incident

        vertices.append(v)

    # =====================================================
    # EDGES
    # =====================================================

    path = DATA_DIR / f"{layer_name}.aristas"

    for line in clean_lines(path):

        if line.startswith("Nombre"):
            continue

        parts = line.split()

        if len(parts) != 6:

            raise ValueError(
                f"Formato inválido aristas:\n{line}"
            )

        (
            name,
            origin,
            twin,
            face,
            next_edge,
            prev_edge
        ) = parts

        e = HalfEdge(name=name)

        e._origin_name = origin
        e._twin_name = twin
        e._face_name = face
        e._next_name = next_edge
        e._prev_name = prev_edge

        edges.append(e)

    # =====================================================
    # FACES
    # =====================================================

    path = DATA_DIR / f"{layer_name}.caras"

    for line in clean_lines(path):

        if line.startswith("Nombre"):
            continue

        parts = line.split()

        if len(parts) < 3:

            raise ValueError(
                f"Formato inválido caras:\n{line}"
            )

        name = parts[0]
        internal = parts[1]
        external = parts[2]

        f = Face(name=name)

        f._internal_names = internal
        f._external_name = external

        faces.append(f)

    # =====================================================
    # ACTIVOS (OPCIONAL)
    # =====================================================

    try:

        path = DATA_DIR / f"{layer_name}.activos"

        for line in clean_lines(path):

            if line.startswith("Caras"):
                continue

            active_faces.add(line)

    except FileNotFoundError:
        pass

    # =====================================================
    # MAPAS
    # =====================================================

    vertex_map = {
        v.name: v
        for v in vertices
    }

    edge_map = {
        e.name: e
        for e in edges
    }

    face_map = {
        f.name: f
        for f in faces
    }

    # =====================================================
    # RESOLVER EDGES
    # =====================================================
    for e in edges:
        # ASIGNAR ORIGEN (ESTO FALTABA)
        if e._origin_name != "None":
            e.origin = vertex_map.get(e._origin_name)

        # ASIGNAR CARA (ESTO TAMBIÉN FALTABA)
        if e._face_name != "None":
            e.face = face_map.get(e._face_name)

        # RESOLVER VECINOS
        if e._twin_name != "None":
            e.twin = edge_map.get(e._twin_name)
        
        if e._next_name != "None":
            e.next = edge_map.get(e._next_name)
            
        if e._prev_name != "None":
            e.prev = edge_map.get(e._prev_name)

    # =====================================================
    # RESOLVER VERTICES
    # =====================================================

    for v in vertices:

        if v._incident_name != "None":

            v.incident_edge = edge_map[v._incident_name]

    # =====================================================
    # RESOLVER FACES
    # =====================================================

    for f in faces:

        # OUTER COMPONENT

        outer = parse_list_field(
            f._external_name
        )

        if outer:

            f.outer_component = edge_map[
                outer[0]
            ]

        else:

            f.outer_component = None

        # INNER COMPONENTS

        f.inner_components = []

        inner = parse_list_field(
            f._internal_names
        )

        for edge_name in inner:

            f.inner_components.append(
                edge_map[edge_name]
            )

    return LayerData(
        name=layer_name,
        vertices=vertices,
        edges=edges,
        faces=faces,
        active_faces=active_faces
    )


# =========================================================
# LOAD PROJECT
# =========================================================

def load_project(layer_names):

    dcel = DCEL()

    layers = []

    for layer_name in layer_names:

        layer = load_layer(layer_name)

        layers.append(layer)

        dcel.vertices.extend(layer.vertices)

        dcel.edges.extend(layer.edges)

        dcel.faces.extend(layer.faces)

    return dcel, layers
def export_layer(dcel, layer_name):
    """
    Exporta el DCEL filtrando referencias a aristas que ya no existen.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    base_path = DATA_DIR / layer_name
    
    # Creamos un conjunto con los nombres de las aristas que sí están en el DCEL
    valid_names = {e.name for e in dcel.edges}

    # --- VÉRTICES ---
    with open(f"{base_path}.vertices", "w", encoding="utf-8") as f:
        f.write("Archivo de vértices\n#################################\n")
        f.write("Nombre\tx\ty\tIncidente\n#################################\n")
        for v in dcel.vertices:
            # Solo exportar incident_edge si existe en la lista actual
            inc = v.incident_edge.name if (v.incident_edge and v.incident_edge.name in valid_names) else "None"
            f.write(f"{v.name}\t{v.point.x}\t{v.point.y}\t{inc}\n")

    # --- ARISTAS (Aquí es donde ocurría el KeyError) ---
    with open(f"{base_path}.aristas", "w", encoding="utf-8") as f:
        f.write("Archivo de aristas\n#############################################\n")
        f.write("Nombre\tOrigen\tPareja\tCara\tSigue\tAntes\n#############################################\n")
        for e in dcel.edges:
            ori = e.origin.name if e.origin else "None"
            # FILTRO CRÍTICO: Si el vecino no está en valid_names, ponemos "None"
            twn = e.twin.name if (e.twin and e.twin.name in valid_names) else "None"
            fce = e.face.name if e.face else "None"
            nxt = e.next.name if (e.next and e.next.name in valid_names) else "None"
            prv = e.prev.name if (e.prev and e.prev.name in valid_names) else "None"
            f.write(f"{e.name}\t{ori}\t{twn}\t{fce}\t{nxt}\t{prv}\n")

    # --- CARAS ---
    with open(f"{base_path}.caras", "w", encoding="utf-8") as f:
        f.write("Archivo de caras\n#######################\nNombre\tInterno\tExterno\n#######################\n")
        for face in dcel.faces:
            ext = face.outer_component.name if (face.outer_component and face.outer_component.name in valid_names) else "None"
            inners = "None"
            if face.inner_components:
                valid_inners = [e.name for e in face.inner_components if e.name in valid_names]
                if valid_inners:
                    inners = "[" + ",".join(valid_inners) + "]"
            f.write(f"{face.name}\t{inners}\t{ext}\n")

    # --- ACTIVOS ---
    with open(f"{base_path}.activos", "w", encoding="utf-8") as f:
        f.write("Archivo de activos\n#######################\nCaras Activas\n#######################\n")
        for face in dcel.faces:
            if face.name != "F0":
                f.write(f"{face.name}\n")