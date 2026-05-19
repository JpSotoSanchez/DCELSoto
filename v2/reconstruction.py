from collections import defaultdict
from geometry import angle
from dcel import Vertex, HalfEdge

class ReconstructionEngine:
    def __init__(self, dcel):
        self.dcel = dcel

    def split_edge(self, edge, vertex_x):
        # 1. Crear las nuevas aristas
        e1 = HalfEdge(edge.name + "_P")
        e2 = HalfEdge(edge.name + "_PP")
        t1 = HalfEdge(edge.twin.name + "_P")
        t2 = HalfEdge(edge.twin.name + "_PP")

        # 2. Configurar Orígenes
        e1.origin = edge.origin
        e2.origin = vertex_x
        t1.origin = edge.twin.origin
        t2.origin = vertex_x

        # 3. Configurar Twins
        e1.twin = t2
        t2.twin = e1
        e2.twin = t1
        t1.twin = e2

        # 4. HEREDAR CARAS (Crucial para pasar el validate())
        e1.face = edge.face
        e2.face = edge.face
        t1.face = edge.twin.face
        t2.face = edge.twin.face

        # 5. CONEXIÓN INTERNA 
        e1.next = e2
        e2.prev = e1
        t1.next = t2
        t2.prev = t1

        # 6. CONEXIÓN EXTERNA
        e1.prev = edge.prev
        if edge.prev:
            edge.prev.next = e1

        e2.next = edge.next
        if edge.next:
            edge.next.prev = e2

        t1.prev = edge.twin.prev
        if edge.twin.prev:
            edge.twin.prev.next = t1

        t2.next = edge.twin.next
        if edge.twin.next:
            edge.twin.next.prev = t2

    
        return e1, e2, t1, t2

    def relink_vertex(self, vertex, outgoing):
        if not outgoing:
            return
            
        # Ordenar aristas por ángulo para mantener consistencia horaria/antihoraria
        outgoing.sort(
            key=lambda e: angle(vertex.point, e.destination.point),
            reverse=True
        )

        n = len(outgoing)
        for i in range(n):
            current = outgoing[i]
            previous = outgoing[(i - 1) % n]
            
            # Conectar el final de una arista que entra al vértice 
            # con el inicio de la siguiente que sale
            current.twin.next = previous
            previous.prev = current.twin

    def rebuild(self, intersections):
        if not intersections:
            print("No se detectaron intersecciones.")
            return

        outgoing_by_vertex = defaultdict(list)

        for point, segments in intersections: 
            vx = Vertex(f"V_{len(self.dcel.vertices)+1}", point)
            self.dcel.vertices.append(vx)

            for s in segments:
                real_edge = s.edge 
                
                # Dividir la arista
                e1, e2, t1, t2 = self.split_edge(real_edge, vx)
                vx.incident_edge = e2 

                outgoing_by_vertex[vx].append(e2)
                outgoing_by_vertex[vx].append(t2)

                self.dcel.edges.extend([e1, e2, t1, t2])

                # Eliminar aristas viejas con seguridad
                if real_edge in self.dcel.edges:
                    self.dcel.edges.remove(real_edge)
                if real_edge.twin in self.dcel.edges:
                    self.dcel.edges.remove(real_edge.twin)

        # Reorganizar punteros alrededor de cada nueva intersección
        for vertex, outgoing in outgoing_by_vertex.items():
            self.relink_vertex(vertex, outgoing)

        # RECALCULAR CARAS (Sin el extend duplicado)
        self.dcel.rebuild_faces()