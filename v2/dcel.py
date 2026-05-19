from dataclasses import dataclass, field
from typing import Optional, List

from geometry import Point, shoelace


@dataclass(unsafe_hash=True) # <--- Habilitar hash manual
class Vertex:
    name: str
    point: Point
    # Excluimos incident_edge del hash y de la comparación
    incident_edge: Optional["HalfEdge"] = field(default=None, hash=False, compare=False)


@dataclass
class Face:
    name: str
    outer_component: Optional["HalfEdge"] = None
    inner_components: List["HalfEdge"] = field(default_factory=list)


@dataclass(unsafe_hash=True) # <--- Habilitar hash para que funcione en sets/dicts
class HalfEdge:
    name: str
    origin: Optional[Vertex] = field(default=None, hash=False, compare=False)
    # Es VITAL excluir los punteros de conexión del hash y repr para evitar recursión
    twin: Optional["HalfEdge"] = field(default=None, hash=False, compare=False, repr=False)
    next: Optional["HalfEdge"] = field(default=None, hash=False, compare=False, repr=False)
    prev: Optional["HalfEdge"] = field(default=None, hash=False, compare=False, repr=False)
    face: Optional["Face"] = field(default=None, hash=False, compare=False, repr=False)

    @property
    def destination(self):
        return self.twin.origin


class DCEL:

    def __init__(self):
        self.vertices = []
        self.edges = []
        self.faces = []

    def add_vertex(self, vertex: Vertex):
        self.vertices.append(vertex)

    def add_edge_pair(self, e1: HalfEdge, e2: HalfEdge):
        e1.twin = e2
        e2.twin = e1

        self.edges.append(e1)
        self.edges.append(e2)

    def validate(self):
        for edge in self.edges:

            assert edge.twin is not None
            assert edge.twin.twin == edge

            assert edge.next is not None
            assert edge.prev is not None

            assert edge.next.prev == edge
            assert edge.prev.next == edge

            assert edge.face is not None

    def extract_cycles(self):
        visited = set()
        cycles = []

        for edge in self.edges:
            if edge in visited:
                continue

            current = edge
            cycle = []

            while current not in visited:
                visited.add(current)
                cycle.append(current)
                current = current.next

                if current is None:
                    raise RuntimeError("Broken cycle")

            if len(cycle) >= 3:
                cycles.append(cycle)

        return cycles

    def cycle_points(self, cycle):
        return [edge.origin.point for edge in cycle]

    def rebuild_faces(self):
        self.faces.clear()

        cycles = self.extract_cycles()

        infinite = Face("F0")
        self.faces.append(infinite)

        finite = []
        holes = []

        for idx, cycle in enumerate(cycles, start=1):
            pts = self.cycle_points(cycle)
            area = shoelace(pts)

            if area > 0:
                face = Face(f"F{idx}")
                face.outer_component = cycle[0]

                for e in cycle:
                    e.face = face

                finite.append((face, pts))
                self.faces.append(face)
            else:
                holes.append((cycle, pts))

        from geometry import point_in_polygon

        for hole_cycle, hole_pts in holes:
            p = hole_pts[0]

            container = None
            best_area = float("inf")

            for face, pts in finite:
                if point_in_polygon(p, pts):
                    area = abs(shoelace(pts))

                    if area < best_area:
                        best_area = area
                        container = face

            if container is None:
                infinite.inner_components.append(hole_cycle[0])

                for e in hole_cycle:
                    e.face = infinite
            else:
                container.inner_components.append(hole_cycle[0])

                for e in hole_cycle:
                    e.face = container
        # Asegurar que toda arista en el DCEL tenga una cara asignada 
        # (si no entró en un ciclo finite/hole, pertenece a la cara infinita)
        for e in self.edges:
            if e.face is None:
                e.face = infinite