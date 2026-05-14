# ── Imports ───────────────────────────────────────────────────────────────────
import math
import heapq
from dataclasses import dataclass, field
from typing import Optional, List
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.cm as cm
from matplotlib.patches import Polygon
import numpy as np
import sys
import datetime

class Tee:
    """Escribe simultáneamente en varios flujos (consola + archivo).
    Ignora silenciosamente errores de fichero cerrado."""
    def __init__(self, *files):
        self.files = files
    def write(self, obj):
        for f in self.files:
            try:
                f.write(obj)
                f.flush()
            except (ValueError, OSError):
                pass
    def flush(self):
        for f in self.files:
            try:
                f.flush()
            except (ValueError, OSError):
                pass

# Crear archivo de log con timestamp
log_filename = f"debug_output_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
log_file = open(log_filename, 'w', encoding='utf-8')
sys.stdout = Tee(sys.__stdout__, log_file)




# ══════════════════════════════════════════════════════════════════════════════
# CLASES
# ══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class Punto:
    x: float
    y: float

    def trasSuma(self, x, y):
        return Punto(self.x + x, self.y + y)

    def trasMult(self, x, y):
        return Punto(self.x * x, self.y * y)

    def rotar(self, rad):
        newX = self.x * math.cos(rad) - self.y * math.sin(rad)
        newY = self.x * math.sin(rad) + self.y * math.cos(rad)
        return Punto(newX, newY)

    def corPolar(self):
        radio = math.sqrt(self.x ** 2 + self.y ** 2)
        theta = math.atan2(self.y, self.x)
        print(f"r: {radio}, theta: {theta}")
        return (radio, theta)

    def distancia(self, otro: "Punto") -> float:
        return math.hypot(self.x - otro.x, self.y - otro.y)


# ── Clases DCEL ───────────────────────────────────────────────────────────────

@dataclass
class NodoVertice:
    nombre: str
    coordenadas: Punto
    aristaAdyacente: Optional["NodoArista"] = None

@dataclass
class NodoArista:
    nombre: str
    verticeOriginal: Optional["NodoVertice"] = None
    pareja: Optional["NodoArista"] = None
    cara: Optional["NodoCara"] = None
    siguiente: Optional["NodoArista"] = None
    anterior: Optional["NodoArista"] = None

@dataclass
class NodoCara:
    nombre: str
    aristasInternos: List[NodoArista] = field(default_factory=list)
    # Cambiado de List a Optional[NodoArista]
    aristasExternos: Optional[NodoArista] = None


# ── Clases de línea de barrido ────────────────────────────────────────────────

@dataclass(frozen=True)
class Segmento:
    name: str
    p1: Punto
    p2: Punto
    boundingBox: tuple = field(init=False)
    long: float = field(init=False)
    ang: float = field(init=False)

    def __repr__(self):
        return f"Segmento {self.name} p1={self.p1}, p2={self.p2}"

    def __post_init__(self):
        object.__setattr__(self, "boundingBox", (
            min(self.p1.x, self.p2.x),
            max(self.p1.x, self.p2.x),
            min(self.p1.y, self.p2.y),
            max(self.p1.y, self.p2.y)
        ))
        longitud = self.p1.distancia(self.p2)
        object.__setattr__(self, "long", longitud)
        if longitud == 0:
            object.__setattr__(self, "ang", 0.0)
        else:
            valor = abs((self.p1.x - self.p2.x) / longitud)
            valor = max(-1.0, min(1.0, valor))
            object.__setattr__(self, "ang", math.acos(valor))

    def organAlto(self) -> "Segmento":
        if self.p1.y > self.p2.y:
            return self
        elif self.p1.y == self.p2.y:
            if self.p1.x < self.p2.x:
                return self
            else:
                return Segmento(self.name, self.p2, self.p1)
        else:
            return Segmento(self.name, self.p2, self.p1)

    def yInBound(self, altura: float) -> bool:
        return self.boundingBox[2] <= altura <= self.boundingBox[3]

    def __hash__(self):
        return hash((self.name, self.p1, self.p2))


@dataclass
class evento:
    p: Punto
    eventoL: set = field(default_factory=set)
    eventoC: set = field(default_factory=set)
    eventoU: set = field(default_factory=set)


@dataclass
class Linea:
    A: float
    B: float
    C: float


# ── Nodo del árbol ────────────────────────────────────────────────────────────

class Nodo:
    def __init__(self, valor):
        self.valor = valor
        self.padre = None
        self.izq = None
        self.der = None
        self.x = None
        self.y = None

    def hijos(self):
        r = []
        if self.izq:
            r.append(self.izq)
        if self.der:
            r.append(self.der)
        return r

    def __repr__(self):
        return f"Nodo {self.valor}"


# ══════════════════════════════════════════════════════════════════════════════
# FUNCIONES AUXILIARES GLOBALES
# ══════════════════════════════════════════════════════════════════════════════

def altura(nodo):
    if nodo is None:
        return -1
    return 1 + max(altura(nodo.izq), altura(nodo.der))

def mayor(nodo):
    while nodo.der:
        nodo = nodo.der
    return nodo

def x_at_y(seg: Segmento, y: float) -> float:
    if abs(seg.p1.y - seg.p2.y) < 1e-10:
        return seg.p1.x
    t = (y - seg.p1.y) / (seg.p2.y - seg.p1.y)
    return seg.p1.x + t * (seg.p2.x - seg.p1.x)


# ── AVL especializado para la línea de barrido ────────────────────────────────

class AVL:
    def __init__(self):
        self.raiz = None

    def _altura(self, nodo):
        return altura(nodo)

    def _factor(self, nodo):
        if nodo is None:
            return 0
        return self._altura(nodo.izq) - self._altura(nodo.der)

    def _rotar_derecha(self, y):
        x = y.izq
        t2 = x.der
        x.padre = y.padre
        if y.padre is None:
            self.raiz = x
        elif y.padre.izq == y:
            y.padre.izq = x
        else:
            y.padre.der = x
        x.der = y
        y.padre = x
        y.izq = t2
        if t2:
            t2.padre = y
        return x

    def _rotar_izquierda(self, x):
        y = x.der
        t2 = y.izq
        y.padre = x.padre
        if x.padre is None:
            self.raiz = y
        elif x.padre.izq == x:
            x.padre.izq = y
        else:
            x.padre.der = y
        y.izq = x
        x.padre = y
        x.der = t2
        if t2:
            t2.padre = x
        return y

    def _rebalancear(self, nodo):
        actual = nodo
        while actual is not None:
            fb = self._factor(actual)
            if fb > 1:
                if self._factor(actual.izq) < 0:
                    self._rotar_izquierda(actual.izq)
                self._rotar_derecha(actual)
            elif fb < -1:
                if self._factor(actual.der) > 0:
                    self._rotar_derecha(actual.der)
                self._rotar_izquierda(actual)
            actual = actual.padre

    @staticmethod
    def _clave(seg):
        return (x_at_y(seg, y_sweep), seg.ang)

    def insertar(self, valor):
        if not self.raiz:
            self.raiz = Nodo(valor)
            return self.raiz
        vk = self._clave(valor)
        actual = self.raiz
        while True:
            ak = self._clave(actual.valor)
            if actual.valor is valor:
                return actual
            elif vk < ak:
                if not actual.izq:
                    nuevo = Nodo(valor)
                    nuevo.padre = actual
                    actual.izq = nuevo
                    self._rebalancear(actual)
                    return nuevo
                actual = actual.izq
            else:
                if not actual.der:
                    nuevo = Nodo(valor)
                    nuevo.padre = actual
                    actual.der = nuevo
                    self._rebalancear(actual)
                    return nuevo
                actual = actual.der

    def buscar(self, valor):
        return self.buscarPorIdentidad(valor)

    def buscarContenedores(self, p: Punto) -> set:
        resultado = set()
        for nodo in self.inorden():
            seg = nodo.valor
            if seg.p1 == p or seg.p2 == p:
                continue
            if seg.yInBound(p.y):
                if abs(x_at_y(seg, p.y) - p.x) < 1e-9:
                    resultado.add(seg)
        return resultado

    def buscarVecinosDeX(self, px: float):
        nodos = self.inorden()
        izq = None
        der = None
        for n in nodos:
            ax = x_at_y(n.valor, y_sweep)
            if ax < px - 1e-9:
                izq = n
            elif ax > px + 1e-9:
                if der is None:
                    der = n
        return izq, der

    def buscarEnRangoX(self, x_min: float, x_max: float) -> list:
        resultado = []
        for nodo in self.inorden():
            nx = x_at_y(nodo.valor, y_sweep)
            if x_min - 1e-9 <= nx <= x_max + 1e-9:
                resultado.append(nodo)
        return resultado

    def buscarPorIdentidad(self, seg) -> "Nodo":
        for nodo in self.inorden():
            if nodo.valor is seg:
                return nodo
        return None

    def sucesor(self, nodo):
        if nodo is None:
            return None
        nodos = self.inorden()
        for i, n in enumerate(nodos):
            if n is nodo:
                return nodos[i + 1] if i + 1 < len(nodos) else None
        return None

    def predecesor(self, nodo):
        if nodo is None:
            return None
        nodos = self.inorden()
        for i, n in enumerate(nodos):
            if n is nodo:
                return nodos[i - 1] if i > 0 else None
        return None

    def eliminar(self, valor):
        nodo = self.buscarPorIdentidad(valor)
        if nodo:
            self._eliminar_nodo(nodo)

    def _eliminar_nodo(self, nodo):
        inicio_rebalanceo = nodo.padre
        if not nodo.izq and not nodo.der:
            if nodo == self.raiz:
                self.raiz = None
            else:
                padre = nodo.padre
                if padre.izq == nodo:
                    padre.izq = None
                else:
                    padre.der = None
        elif nodo.izq and not nodo.der:
            self._reemplazar_con_hijo(nodo, nodo.izq)
        elif nodo.der and not nodo.izq:
            self._reemplazar_con_hijo(nodo, nodo.der)
        else:
            suc = mayor(nodo.izq)
            inicio_rebalanceo = suc.padre
            if inicio_rebalanceo == nodo:
                inicio_rebalanceo = suc
            nodo.valor = suc.valor
            self._eliminar_nodo(suc)
            return
        if inicio_rebalanceo:
            self._rebalancear(inicio_rebalanceo)

    def _reemplazar_con_hijo(self, nodo, hijo):
        hijo.padre = nodo.padre
        if nodo.padre is None:
            self.raiz = hijo
        elif nodo.padre.izq == nodo:
            nodo.padre.izq = hijo
        else:
            nodo.padre.der = hijo

    def _inorden_estructural(self, nodo=None):
        if nodo is None:
            nodo = self.raiz
        l = []
        if nodo is None:
            return l
        if nodo.izq:
            l.extend(self._inorden_estructural(nodo.izq))
        l.append(nodo)
        if nodo.der:
            l.extend(self._inorden_estructural(nodo.der))
        return l

    def inorden(self, nodo=None):
        nodos = self._inorden_estructural(nodo)
        # Si la X es igual, desempatamos por el ángulo del segmento
        nodos.sort(key=lambda n: (round(x_at_y(n.valor, y_sweep), 9), n.valor.ang))
        return nodos

# ══════════════════════════════════════════════════════════════════════════════
# FUNCIONES GEOMÉTRICAS
# ══════════════════════════════════════════════════════════════════════════════

def punto_en_poligono(pt, vertices):
    """Algoritmo Ray-Casting para saber si un punto está dentro de un polígono"""
    if not pt or not vertices: return False
    x, y = pt.x, pt.y
    adentro = False
    n = len(vertices)
    for i in range(n):
        j = (i + 1) % n
        xi, yi = vertices[i].x, vertices[i].y
        xj, yj = vertices[j].x, vertices[j].y
        # Verifica si el rayo cruza la arista
        intersecta = ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-9) + xi)
        if intersecta:
            adentro = not adentro
    return adentro

def obtener_punto_prueba(cara):
    if not cara.aristasExternos: return None
    pts = []
    actual = cara.aristasExternos
    inicio = actual
    while True:
        pts.append(actual.verticeOriginal.coordenadas)
        actual = actual.siguiente
        if actual == inicio: break
    
    # Centroide básico
    cx = sum(p.x for p in pts) / len(pts)
    cy = sum(p.y for p in pts) / len(pts)
    
    # Truco: Si el centroide cae fuera (casos cóncavos), 
    # tomamos el punto medio entre el primer vértice y el centroide para acercarlo al borde interior
    p_test = Punto(cx, cy)
    if not punto_en_poligono(p_test, pts):
        return Punto((pts[0].x + cx)/2, (pts[0].y + cy)/2)
    return p_test

def segALinea(segmento):
    x1, x2 = segmento.p1.x, segmento.p2.x
    y1, y2 = segmento.p1.y, segmento.p2.y
    return Linea(y1 - y2, x2 - x1, x1 * y2 - y1 * x2)

def interseccionLineas(linea1, linea2):
    detGen = linea1.A * linea2.B - linea1.B * linea2.A
    if detGen == 0:
        return None
    detX = (-linea1.C) * linea2.B - linea1.B * (-linea2.C)
    detY = linea1.A * (-linea2.C) - (-linea1.C) * linea2.A
    return Punto(detX / detGen, detY / detGen)

def interseccionSeg(segmento1, segmento2) -> list:
    lineaSeg1 = segALinea(segmento1)
    lineaSeg2 = segALinea(segmento2)
    detGen = lineaSeg1.A * lineaSeg2.B - lineaSeg1.B * lineaSeg2.A

    if abs(detGen) < 1e-10:
        prueba = (lineaSeg2.A * segmento1.p1.x
                  + lineaSeg2.B * segmento1.p1.y
                  + lineaSeg2.C)
        if abs(prueba) > 1e-5:
            return []

        dx1 = abs(segmento1.p2.x - segmento1.p1.x)
        dy1 = abs(segmento1.p2.y - segmento1.p1.y)

        if dx1 >= dy1:
            l1 = min(segmento1.p1.x, segmento1.p2.x)
            r1 = max(segmento1.p1.x, segmento1.p2.x)
            l2 = min(segmento2.p1.x, segmento2.p2.x)
            r2 = max(segmento2.p1.x, segmento2.p2.x)
            ol = max(l1, l2)
            or_ = min(r1, r2)
            if ol > or_ + 1e-9:
                return []

            def x_a_punto(x_val):
                if dx1 < 1e-10:
                    return Punto(x_val, segmento1.p1.y)
                t = (x_val - segmento1.p1.x) / (segmento1.p2.x - segmento1.p1.x)
                return Punto(x_val, segmento1.p1.y + t * (segmento1.p2.y - segmento1.p1.y))

            p_inicio = x_a_punto(ol)
            if abs(ol - or_) < 1e-9:
                return [p_inicio]
            return [p_inicio, x_a_punto(or_)]
        else:
            l1 = min(segmento1.p1.y, segmento1.p2.y)
            r1 = max(segmento1.p1.y, segmento1.p2.y)
            l2 = min(segmento2.p1.y, segmento2.p2.y)
            r2 = max(segmento2.p1.y, segmento2.p2.y)
            ol = max(l1, l2)
            or_ = min(r1, r2)
            if ol > or_ + 1e-9:
                return []

            def y_a_punto(y_val):
                if dy1 < 1e-10:
                    return Punto(segmento1.p1.x, y_val)
                t = (y_val - segmento1.p1.y) / (segmento1.p2.y - segmento1.p1.y)
                return Punto(segmento1.p1.x + t * (segmento1.p2.x - segmento1.p1.x), y_val)

            p_inicio = y_a_punto(ol)
            if abs(ol - or_) < 1e-9:
                return [p_inicio]
            return [p_inicio, y_a_punto(or_)]

    inter = interseccionLineas(lineaSeg1, lineaSeg2)
    if inter is None:
        return []
    
    eps = 1e-9

    if (
        segmento1.boundingBox[0] - eps <= inter.x <= segmento1.boundingBox[1] + eps and
        segmento1.boundingBox[2] - eps <= inter.y <= segmento1.boundingBox[3] + eps and
        segmento2.boundingBox[0] - eps <= inter.x <= segmento2.boundingBox[1] + eps and
        segmento2.boundingBox[2] - eps <= inter.y <= segmento2.boundingBox[3] + eps
    ):
            return [inter]
    return []


# ══════════════════════════════════════════════════════════════════════════════
# PROCESAMIENTO DE EVENTOS (línea de barrido)
# ══════════════════════════════════════════════════════════════════════════════

def procesarEvento(p):
    global y_sweep
    y_sweep = p.p.y
    
    # Usar la misma llave redondeada para recuperar el evento
    llave_p = _llave(p.p)          # misma llave que usó el constructor
    event_data = dictPuntos.get(llave_p, p)

    U = event_data.eventoU
    L = event_data.eventoL
    C = T.buscarContenedores(p.p)

    unionULC = U | L | C
    unionUC  = U | C

    if len(unionULC) > 1:
        R.add((p.p, frozenset(unionULC)))

    # [DEBUG] Evento procesado
    print(f"[DEBUG] Evento en y={p.p.y:.4f}, x={p.p.x:.4f}  |U|={len(U)} |L|={len(L)} |C|={len(C)}")

    for seg in L | C:
        T.eliminar(seg)

    y_sweep = p.p.y - 1e-9
    for seg in U | C:
        T.insertar(seg)

    for seg_h in U:
        if abs(seg_h.p1.y - seg_h.p2.y) < 1e-9:
            x_izq = min(seg_h.p1.x, seg_h.p2.x)
            x_der = max(seg_h.p1.x, seg_h.p2.x)
            for nodo_v in T.buscarEnRangoX(x_izq, x_der):
                seg_v = nodo_v.valor
                for inter in interseccionSeg(seg_h, seg_v):
                    R.add((inter, frozenset([seg_h, seg_v])))

    if not unionUC:
        sL, sR = T.buscarVecinosDeX(p.p.x)
        encuentraEvento(sL, sR, p.p)
    else:
        nodos_uc = [T.buscarPorIdentidad(s) for s in unionUC
                    if abs(s.p1.y - s.p2.y) > 1e-9]
        nodos_uc = [n for n in nodos_uc if n is not None]

        if nodos_uc:
            sPrim = min(nodos_uc, key=lambda n: x_at_y(n.valor, y_sweep))
            sL    = T.predecesor(sPrim)
            encuentraEvento(sL, sPrim, p.p)

            sBiPrim = max(nodos_uc, key=lambda n: x_at_y(n.valor, y_sweep))
            sR      = T.sucesor(sBiPrim)
            encuentraEvento(sBiPrim, sR, p.p)

    tipo = ("U" if U else "") + ("L" if L else "") + ("C" if C else "")
    frames.append({
        'y':         p.p.y,
        'punto':     p.p,
        'tipo':      tipo or "?",
        'activos':   {n.valor for n in T.inorden()},
        'resultado': list(R),
    })


def encuentraEvento(sL, sR, p: Punto):
    global _contador_ev
    if sL is None or sR is None:
        return

    for inter in interseccionSeg(sL.valor, sR.valor):
        llave = _llave(inter)
        
        # Reducimos un poco el margen de error para "debajo"
        debajo = inter.y < p.y - 1e-10 
        mismaAltura_derecha = abs(inter.y - p.y) < 1e-10 and inter.x > p.x + 1e-10

        if debajo or mismaAltura_derecha:
            if llave in dictPuntos:
                ev = dictPuntos[llave]
                # CRÍTICO: Asegurar que ambos segmentos se añaden al evento para ser procesados
                ev.eventoC.add(sL.valor)
                ev.eventoC.add(sR.valor)
            else:
                _contador_ev += 1
                ev = evento(inter, eventoL=set(), eventoC={sL.valor, sR.valor}, eventoU=set())
                dictPuntos[llave] = ev
                heapq.heappush(Q, ((-inter.y, inter.x, _contador_ev), ev))


# ══════════════════════════════════════════════════════════════════════════════
# FUNCIONES DE ACTUALIZACIÓN DCEL (ALGORITMO)
# ══════════════════════════════════════════════════════════════════════════════

from collections import defaultdict

def construir_estrellas(aristas):
    estrellas = defaultdict(list)

    for a in aristas:
        v = a.verticeOriginal

        destino = a.pareja.verticeOriginal.coordenadas
        origen = v.coordenadas

        ang = math.atan2(
            destino.y - origen.y,
            destino.x - origen.x
        )

        estrellas[v.nombre].append((ang, a))

    for k in estrellas:
        estrellas[k].sort(key=lambda t: t[0])

    return estrellas


def area_ciclo(ciclo):
    area = 0.0

    for i in range(len(ciclo)):
        p1 = ciclo[i].verticeOriginal.coordenadas
        p2 = ciclo[(i + 1) % len(ciclo)].verticeOriginal.coordenadas

        area += (
            p1.x * p2.y -
            p2.x * p1.y
        )

    return area / 2.0

def unificar_vertices_coincidentes(vertices, aristas):
    """
    Fusiona en un solo objeto vértice todos los NodoVertice de distintos
    layers que comparten coordenadas exactas, y redirige todas las aristas.
    """
    por_posicion = defaultdict(list)
    for v in vertices:
        por_posicion[_llave(v.coordenadas)].append(v)

    reemplazar = {}  # id(duplicado) → canonico
    for grupo in por_posicion.values():
        if len(grupo) < 2:
            continue
        canonico = grupo[0]
        for dup in grupo[1:]:
            reemplazar[id(dup)] = canonico

    if not reemplazar:
        return

    for a in aristas:
        if id(a.verticeOriginal) in reemplazar:
            a.verticeOriginal = reemplazar[id(a.verticeOriginal)]

    vertices[:] = [v for v in vertices if id(v) not in reemplazar]

def reconstruir_topologia(aristas):

    estrellas = construir_estrellas(aristas)

    for a in aristas:

        # vértice al que llega la arista
        destino = a.pareja.verticeOriginal

        lista = estrellas[destino.nombre]

        idx = None

        for i, (_, edge) in enumerate(lista):
            if edge == a.pareja:
                idx = i
                break

        if idx is None:
            continue

        # siguiente angular CCW
        siguiente_idx = (idx + 1) % len(lista)

        siguiente = lista[siguiente_idx][1]

        a.siguiente = siguiente
        siguiente.anterior = a


def procesar_interseccion(
    vertice_x: NodoVertice,
    aristas_intersecadas: List[NodoArista],
    lista_vertices: List[NodoVertice],
    lista_aristas: List[NodoArista],
    lista_caras: List[NodoCara]
):
    """
    Divide cada arista en dos en el punto vertice_x y reconstruye
    correctamente los punteros siguiente/anterior y gemelo (pareja).
    """
    print(f"\n[DEBUG] === Nueva intersección: vértice {vertice_x.nombre} en {vertice_x.coordenadas} ===")
    print(f"[DEBUG] Aristas a dividir: {[a.nombre for a in aristas_intersecadas]}")

    lista_vertices.append(vertice_x)

    aristas_a_eliminar = []       # aristas originales que serán reemplazadas
    todos_primos = {}             # A->X  (primo)
    todos_primo_primos = {}       # X->B  (primo_primo)
    todos_pareja_primos = {}      # B->X  (gemela de primo_primo)
    todos_pareja_primo_primos = {}# X->A  (gemela de primo)

    # ── 1. Crear las cuatro semi-aristas para cada arista cortada ──────────
    for arista in aristas_intersecadas:
        # marcar originales para eliminar después
        aristas_a_eliminar.append(arista)
        aristas_a_eliminar.append(arista.pareja)

        v_origen  = arista.verticeOriginal
        v_destino = arista.pareja.verticeOriginal

        # --- semi-aristas de la cara "frontal" (la que contenía a arista)
        primo = NodoArista(f"{arista.nombre}_P")
        primo.verticeOriginal = v_origen                     # A -> X

        primo_primo = NodoArista(f"{arista.nombre}_PP")
        primo_primo.verticeOriginal = vertice_x              # X -> B

        # --- semi-aristas de la cara opuesta (la que contenía a arista.pareja)
        pareja_primo = NodoArista(f"{arista.pareja.nombre}_P")
        pareja_primo.verticeOriginal = v_destino             # B -> X

        pareja_primo_primo = NodoArista(f"{arista.pareja.nombre}_PP")
        pareja_primo_primo.verticeOriginal = vertice_x       # X -> A

        # ── 2. Establecer las parejas (gemelas) ────────────────────────────
        primo.pareja                 = pareja_primo_primo
        pareja_primo_primo.pareja    = primo

        primo_primo.pareja           = pareja_primo
        pareja_primo.pareja          = primo_primo

        # ── 3. Continuidad de la frontera de las caras ─────────────────────
        # La cara que seguía a través de arista ahora será:
        #   ... → anterior → primo → primo_primo → siguiente → ...
        primo.anterior       = arista.anterior
        primo_primo.siguiente = arista.siguiente

        primo.siguiente       = primo_primo
        primo_primo.anterior  = primo

        # Cara opuesta (la que iba por arista.pareja)
        pareja_primo.anterior        = arista.pareja.anterior
        pareja_primo_primo.siguiente = arista.pareja.siguiente

        pareja_primo.siguiente       = pareja_primo_primo
        pareja_primo_primo.anterior  = pareja_primo

        # Conectar con los vecinos viejos
        if arista.anterior:
            arista.anterior.siguiente = primo
        if arista.siguiente:
            arista.siguiente.anterior = primo_primo

        if arista.pareja.anterior:
            arista.pareja.anterior.siguiente = pareja_primo
        if arista.pareja.siguiente:
            arista.pareja.siguiente.anterior = pareja_primo_primo

        # Guardar para la fase final
        id_orig = arista.nombre
        id_twin = arista.pareja.nombre

        todos_primos[id_orig]                = primo
        todos_primo_primos[id_orig]          = primo_primo
        todos_pareja_primos[id_twin]         = pareja_primo
        todos_pareja_primo_primos[id_twin]   = pareja_primo_primo

        print(f"[DEBUG]   Creando semi-aristas para {id_orig}:")
        print(f"          {primo.nombre}  ({v_origen.nombre} -> {vertice_x.nombre})")
        print(f"          {primo_primo.nombre} ({vertice_x.nombre} -> {v_destino.nombre})")
        print(f"          {pareja_primo.nombre} ({v_destino.nombre} -> {vertice_x.nombre})")
        print(f"          {pareja_primo_primo.nombre} ({vertice_x.nombre} -> {v_origen.nombre})")

    # ── 4. Recolectar todas las aristas que SALEN de vertice_x ────────────
    salientes = []
    for pp in todos_primo_primos.values():
        salientes.append(pp)
    for pp_twin in todos_pareja_primo_primos.values():
        salientes.append(pp_twin)

    # ── 5. Ordenarlas angularmente alrededor de vertice_x ─────────────────
    def angulo_salida(edge):
        destino = edge.siguiente.verticeOriginal.coordenadas
        origen  = vertice_x.coordenadas
        return math.atan2(destino.y - origen.y, destino.x - origen.x)

    salientes.sort(key=angulo_salida)

    print(f"[DEBUG] Aristas salientes de {vertice_x.nombre} ordenadas:")
    for s in salientes:
        print(f"          {s.nombre} -> {s.siguiente.verticeOriginal.nombre}, ángulo={math.degrees(angulo_salida(s)):.2f}°")

    # ── 6. Enlazar circularmente las aristas INCIDENTES a X ────────────────
    n = len(salientes)
    for i in range(n):
        h_actual = salientes[i]
        h_siguiente = salientes[(i + 1) % n]

        # h_actual.pareja es la semi-arista que LLEGA a X
        # su siguiente debe ser la siguiente semi-arista que SALE de X
        h_actual.pareja.siguiente = h_siguiente
        h_siguiente.anterior      = h_actual.pareja
        print(f"[DEBUG]   Enlace: {h_actual.pareja.nombre}.siguiente = {h_siguiente.nombre}")

    # ── 7. Asignar arista incidente del nuevo vértice ─────────────────────
    vertice_x.aristaAdyacente = salientes[0]
    print(f"[DEBUG] {vertice_x.nombre}.aristaAdyacente = {salientes[0].nombre}")

    # ── 8. Actualizar las listas globales ──────────────────────────────────
    lista_aristas[:] = [a for a in lista_aristas if a not in aristas_a_eliminar]
    lista_aristas.extend(todos_primos.values())
    lista_aristas.extend(todos_primo_primos.values())
    lista_aristas.extend(todos_pareja_primos.values())
    lista_aristas.extend(todos_pareja_primo_primos.values())

    print(f"[DEBUG] Aristas totales actuales: {len(lista_aristas)}")

    # ── 9. Reconstruir punteros siguiente/anterior para el resto ───────────
    reconstruir_topologia(lista_aristas)

    # ── 10. Recalcular caras ──────────────────────────────────────────────
    rearmar_caras(lista_aristas, lista_caras)
    print(f"[DEBUG] Caras después de procesar intersección: {len(lista_caras)}")
    for c in lista_caras:
        ext = c.aristasExternos.nombre if c.aristasExternos else "None"
        act = "ACTIVA" if c.nombre in caras_activas_resultado else "inactiva"
        print(f"        {c.nombre:8s}  externo: {ext:10s}  {act}")

def rearmar_caras(lista_aristas, lista_caras):
    global caras_activas_resultado
    print(f"\n[DEBUG] --- Recalculando caras (total aristas: {len(lista_aristas)}) ---")
    lista_caras.clear()

    # Limpiar referencias previas en las aristas
    for a in lista_aristas:
        a.cara = None

    ciclos = []
    visitadas_global = set()

    # =========================================================
    # 1. DETECTAR TODOS LOS CICLOS (CORREGIDO)
    # =========================================================

    for arista in lista_aristas:

        if id(arista) in visitadas_global:
            continue

        ciclo = []
        visitadas_local = set()
        actual = arista
        se_cerro_correctamente = False

        while actual and id(actual) not in visitadas_local:
            visitadas_local.add(id(actual))
            ciclo.append(actual)
            
            actual = actual.siguiente
            
            # Verificación crítica: Si regresamos al inicio exacto, el ciclo es válido
            if actual is arista:
                se_cerro_correctamente = True
                break

        # Si el ciclo no regresó a la arista inicial o es muy pequeño, se descarta
        if not se_cerro_correctamente or len(ciclo) < 3:
            continue

        # Registramos las aristas del ciclo válido en el set global para no duplicar caras
        for a_ciclo in ciclo:
            visitadas_global.add(id(a_ciclo))

        area = area_ciclo(ciclo)

        cara = NodoCara("TEMP")
        cara.aristasExternos = ciclo[0]

        ciclos.append({
            "cara": cara,
            "ciclo": ciclo,
            "area": area,
            "abs_area": abs(area),
        })

        print(f"[DEBUG]   Ciclo detectado: {len(ciclo)} aristas, área={area:.4f}, comienza en {ciclo[0].nombre}")
        if area == 0.0 and len(ciclo) > 6:
            print("[DEBUG] Ciclo de área 0:", [e.verticeOriginal.nombre for e in ciclo])

    if not ciclos:
        print("[DEBUG]   No se detectaron ciclos.")
        return

    # =========================================================
    # 2. IDENTIFICAR CARA INFINITA
    # =========================================================

    infinita_data = max(
        ciclos,
        key=lambda x: x["abs_area"]
    )

    cara_infinita = infinita_data["cara"]
    cara_infinita.nombre = "CARA1"
    print(f"[DEBUG]   Cara infinita: ciclo con área={infinita_data['area']:.4f}")

    # =========================================================
    # 3. ASIGNAR NOMBRES AL RESTO
    # =========================================================

    contador = 2

    for data in ciclos:

        cara = data["cara"]

        if cara is cara_infinita:
            continue

        cara.nombre = f"CARA{contador}"
        contador += 1

    # =========================================================
    # 4. CLASIFICAR ACTIVAS USANDO CONTEXTO ORIGINAL
    # =========================================================

    caras_activas_resultado.clear()

    for data in ciclos:

        cara = data["cara"]

        if cara is cara_infinita:
            continue

        punto_test = obtener_punto_prueba(cara)

        if punto_test is None:
            continue

        dentro_de_activa = False

        # -----------------------------------------------------
        # Revisar si cae dentro de alguna cara activa original
        # -----------------------------------------------------

        for nombre_original, info in poligonos_originales.items():

            if not info["activa"]:
                continue

            vertices_originales = info["vertices"]

            if punto_en_poligono(
                punto_test,
                vertices_originales
            ):
                dentro_de_activa = True
                break

        # -----------------------------------------------------
        # Marcar resultado
        # -----------------------------------------------------

        if dentro_de_activa:
            caras_activas_resultado.append(cara.nombre)

    print(f"[DEBUG]   Caras activas después de clasificar: {caras_activas_resultado}")

    # =========================================================
    # 5. ASIGNAR CARAS A ARISTAS
    # =========================================================

    for data in ciclos:

        cara = data["cara"]

        for arista in data["ciclo"]:
            arista.cara = cara

    # =========================================================
    # 6. DETECTAR HUECOS / CICLOS INTERNOS
    # =========================================================

    for data_externa in ciclos:

        cara_externa = data_externa["cara"]

        if cara_externa is cara_infinita:
            continue

        punto_externo = obtener_punto_prueba(cara_externa)

        if punto_externo is None:
            continue

        for data_interna in ciclos:

            cara_interna = data_interna["cara"]

            if cara_interna == cara_externa:
                continue

            if cara_interna is cara_infinita:
                continue

            punto_interno = obtener_punto_prueba(cara_interna)

            if punto_interno is None:
                continue

            # ---------------------------------------------
            # Si una cara cae dentro de otra:
            # es un posible hueco
            # ---------------------------------------------

            vertices_ext = []

            inicio = cara_externa.aristasExternos
            actual = inicio

            while True:

                vertices_ext.append(
                    actual.verticeOriginal.coordenadas
                )

                actual = actual.siguiente

                if actual == inicio or actual is None:
                    break

            if punto_en_poligono(
                punto_interno,
                vertices_ext
            ):

                # La más pequeña se vuelve interna
                if data_interna["abs_area"] < data_externa["abs_area"]:

                    if (
                        cara_interna.aristasExternos
                        not in cara_externa.aristasInternos
                    ):
                        cara_externa.aristasInternos.append(
                            cara_interna.aristasExternos
                        )
                        print(f"[DEBUG]   Hueco detectado: {cara_interna.nombre} dentro de {cara_externa.nombre}")

    # =========================================================
    # 7. GUARDAR RESULTADO FINAL
    # =========================================================

    for data in ciclos:
        lista_caras.append(data["cara"])   

# ══════════════════════════════════════════════════════════════════════════════
# FUNCIONES DE DIBUJO DCEL
# ══════════════════════════════════════════════════════════════════════════════

def coloresPorLayer(layers):
    cmap = cm.get_cmap("tab10", len(layers))
    return {layer: cmap(i) for i, layer in enumerate(layers)}

def dibujarAristas(aristas, subPlot, color, label=None):
    primer_segmento = True
    for arista in aristas:
        aristasVisitadas = set()
        listaX, listaY = [], []
        aristaAux = arista
        while True:
            if aristaAux.nombre not in aristasVisitadas:
                listaX.append(aristaAux.verticeOriginal.coordenadas.x)
                listaY.append(aristaAux.verticeOriginal.coordenadas.y)
                aristasVisitadas.add(aristaAux.nombre)
                aristaAux = aristaAux.siguiente
            else:
                break
        if listaX:
            listaX.append(listaX[0])
            listaY.append(listaY[0])
        subPlot.plot(listaX, listaY, marker='o', color=color,
                     label=label if primer_segmento else None)
        primer_segmento = False

def dibujarCara(cara, subPlot, color, rellenar=False, label=None):
    # 1. Obtener vértices del contorno externo
    # Ahora cara.aristasExternos es un NodoArista o None
    if cara.aristasExternos:
        coords_externas = []
        arista_actual = cara.aristasExternos  # YA NO ES UNA LISTA
        inicio = arista_actual
        
        while True:
            # Aquí ya no fallará el .verticeOriginal
            coords_externas.append((
                arista_actual.verticeOriginal.coordenadas.x, 
                arista_actual.verticeOriginal.coordenadas.y
            ))
            arista_actual = arista_actual.siguiente
            if arista_actual == inicio or arista_actual is None:
                break
        
        # 2. Dibujar el Polígono
        poly = Polygon(
            coords_externas, 
            closed=True, 
            facecolor=color if rellenar else 'none', 
            edgecolor=color, 
            linewidth=2,
            alpha=0.4 if rellenar else 1.0,
            label=label
        )
        subPlot.add_patch(poly)

    # 3. Dibujar bordes internos (Huecos)
    if cara.aristasInternos:
        dibujarAristas(cara.aristasInternos, subPlot, color)


# ══════════════════════════════════════════════════════════════════════════════
# PARTE 1 — LECTURA Y VISUALIZACIÓN INICIAL DCEL
# ══════════════════════════════════════════════════════════════════════════════

fig = plt.figure()
ax  = fig.add_subplot()

listaLayers = ["layer05"]
colores = coloresPorLayer(listaLayers)

# Variables globales para albergar el universo DCEL total
todasLasAristas: List[NodoArista] = []
todosLosVertices: List[NodoVertice] = []
todasLasCaras: List[NodoCara] = []

global_caras_activas = set()

for layer in listaLayers:
    color = colores[layer]
    listaCaras, listaVertices, listaAristas, listaCarasActivas = [], [], [], []

    listaArchivos = [
        layer + ".aristas",
        layer + ".caras",
        layer + ".vertices",
        layer + ".activos",
    ]

    for archivo in listaArchivos:
        if ".arista" in archivo:
            with open(archivo, "r", encoding="utf-8") as f:
                lineas = [l.strip() for l in f if l.strip() and not l.startswith("#")]
            for linea in lineas:
                partes = linea.split()
                if len(partes) == 6 and not linea.startswith("Nombre"):
                    Nombre, Origen, Pareja, Cara, Sigue, Antes = partes
                    # CAMBIO: Usar layer siempre para que coincidan las llaves
                    arista = NodoArista(Nombre + layer)
                    arista.verticeOriginal = Origen + layer if Origen != "None" else "None"
                    arista.pareja    = Pareja + layer if Pareja != "None" else "None"
                    arista.cara      = Cara + layer if Cara != "None" else "None"
                    arista.siguiente = Sigue + layer if Sigue != "None" else "None"
                    arista.anterior  = Antes + layer if Antes != "None" else "None"
                    listaAristas.append(arista)

        elif ".vertice" in archivo:
            with open(archivo, "r", encoding="utf-8") as f:
                lineas = [l.strip() for l in f if l.strip() and not l.startswith("#")]
            for linea in lineas:
                partes = linea.split()
                if len(partes) == 4 and not linea.startswith("Nombre"):
                    Nombre, x, y, Incidente = partes
                    listaVertices.append(NodoVertice(Nombre + layer, Punto(float(x), float(y)), Incidente + layer if Incidente != "None" else "None"))

        elif ".cara" in archivo:
            with open(archivo, "r", encoding="utf-8") as f:
                lineas = [l.strip() for l in f if l.strip() and not l.startswith("#")]
            for linea in lineas:
                partes = linea.split()
                if len(partes) == 3 and not linea.startswith("Nombre") and not linea.startswith("Archivo"):
                    Nombre, Interno, Externo = partes
                    # No sumamos layer a Interno/Externo aquí porque vienen como "[e1,e2]"
                    listaCaras.append(NodoCara(Nombre + layer, Interno, Externo))

        elif ".activos" in archivo:
            try:
                with open(archivo, "r", encoding="utf-8") as f:
                    lineas = [l.strip() for l in f if l.strip() and not l.startswith("#")]
                for linea in lineas:
                    if not linea.startswith("Caras"):
                        listaCarasActivas.append(linea + layer)
            except Exception: pass

    dicVertices = {v.nombre: v for v in listaVertices}
    dicAristas  = {a.nombre: a for a in listaAristas}
    dicCaras    = {c.nombre: c for c in listaCaras}

    # Usamos .get() para que si es "None" no truene
    for a in listaAristas:
        a.verticeOriginal = dicVertices.get(a.verticeOriginal)
        a.pareja          = dicAristas.get(a.pareja)
        a.siguiente       = dicAristas.get(a.siguiente)
        a.anterior        = dicAristas.get(a.anterior)
        a.cara            = dicCaras.get(a.cara)

    for v in listaVertices:
        if isinstance(v.aristaAdyacente, str):
            v.aristaAdyacente = dicAristas.get(v.aristaAdyacente)

    for c in listaCaras:
        raw_int = c.aristasInternos
        if isinstance(raw_int, str):
            raw_int = raw_int.strip("[]")
            # Sumamos layer al buscar en el diccionario
            c.aristasInternos = [dicAristas.get(n.strip() + layer) for n in raw_int.split(",") if n.strip() and n.strip() != "None"]

        raw_ext = c.aristasExternos
        if isinstance(raw_ext, str):
            raw_ext = raw_ext.strip("[]")
            nombres_ext = [n.strip() for n in raw_ext.split(",") if n.strip() and n.strip() != "None"]
            # Sumamos layer al buscar en el diccionario
            c.aristasExternos = dicAristas.get(nombres_ext[0] + layer) if nombres_ext else None

    todasLasAristas.extend(listaAristas)
    todosLosVertices.extend(listaVertices)
    todasLasCaras.extend(listaCaras)

    # Definimos cuáles están activas para consulta rápida
    set_activas = set(listaCarasActivas) if listaCarasActivas else set()

    for i, cara in enumerate(listaCaras):
        # Solo ponemos label en la primera iteración para evitar duplicados en la leyenda
        label_actual = layer if i == 0 else None
        
        # DETERMINAR SI ESTÁ ACTIVA
        # Si la lista está vacía, ¿consideramos todas activas o ninguna? 
        # Aquí asumo que si hay una lista, solo se rellenan las presentes.
        esta_activa = cara.nombre in set_activas
        
        dibujarCara(
            cara, 
            ax, 
            color=color, 
            rellenar=esta_activa, 
            label=label_actual
        )
    global_caras_activas.update(listaCarasActivas)

ax.legend(title="Layers")
ax.set_aspect("equal")
plt.tight_layout()
plt.show()


# ══════════════════════════════════════════════════════════════════════════════
# PARTE 2 — LÍNEA DE BARRIDO
# ══════════════════════════════════════════════════════════════════════════════
# ── Helper de llave normalizada ───────────────────────────────────────────────
def _llave(p: Punto) -> tuple:
    """
    Clave canónica para dictPuntos.
    Convierte siempre a (float_redondeado, float_redondeado) para evitar
    la mezcla entre objetos Punto y tuplas que rompía la fusión de eventos.
    """
    return (round(p.x, 9), round(p.y, 9))

# RESPALDO ORIGINAL PARA OPERACIONES BOOLEANAS
poligonos_originales = {}
for c in todasLasCaras:
    # Una cara es finita (es un triángulo/polígono) si tiene una arista externa.
    # Las caras infinitas (como f1, f3 o CARA1) se ignoran.
    if c.aristasExternos: 
        pts = []
        inicio = c.aristasExternos
        actual = inicio
        while True:
            pts.append(actual.verticeOriginal.coordenadas)
            actual = actual.siguiente
            if actual == inicio or actual is None: break
        
        # Verificamos si esta cara original era activa usando la memoria global
        es_activa = (c.nombre in global_caras_activas)
        poligonos_originales[c.nombre] = {'vertices': pts, 'activa': es_activa}

S = set()
Q = []
dictPuntos = {}
T = AVL()
R = set()
y_sweep = 0.0
_contador_ev = 0
frames = []

vistasAristas: set = set()

for a in todasLasAristas:
    if a.nombre in vistasAristas:
        continue
    vistasAristas.add(a.nombre)
    vistasAristas.add(a.pareja.nombre)

    p1 = a.verticeOriginal.coordenadas
    p2 = a.pareja.verticeOriginal.coordenadas

    segmento = Segmento(a.nombre, p1, p2).organAlto()
    S.add(segmento)

    lk1 = _llave(segmento.p1)
    if lk1 in dictPuntos:
        dictPuntos[lk1].eventoU.add(segmento)
    else:
        dictPuntos[lk1] = evento(
            segmento.p1, eventoL=set(), eventoC=set(), eventoU={segmento})

    lk2 = _llave(segmento.p2)
    if lk2 in dictPuntos:
        dictPuntos[lk2].eventoL.add(segmento)
    else:
        dictPuntos[lk2] = evento(
            segmento.p2, eventoL={segmento}, eventoC=set(), eventoU=set())

for ev in dictPuntos.values():
    _contador_ev += 1
    heapq.heappush(Q, ((-ev.p.y, ev.p.x, _contador_ev), ev))

while Q:
    _, eventop = heapq.heappop(Q)
    procesarEvento(eventop)


print("\n[DEBUG] Intersecciones encontradas por la línea de barrido:")
for punto, segs in R:
    nombres = [s.name for s in segs]
    print(f"  {punto} → {nombres}")
print(f"[DEBUG] Total: {len(R)}")

txt_filename = "intersecciones.txt"
R_ordenado = sorted(R, key=lambda t: (-t[0].y, t[0].x))

with open(txt_filename, "w", encoding="utf-8") as f:
    f.write(f"Total de intersecciones: {len(R)}\n")
    f.write("=" * 40 + "\n")
    for i, (punto, segs) in enumerate(R_ordenado, 1):
        nombres = sorted(s.name for s in segs)
        f.write(f"{i:>4}. ({punto.x:.6g}, {punto.y:.6g})  →  {', '.join(nombres)}\n")

print(f"Intersecciones guardadas en {txt_filename}")


# ══════════════════════════════════════════════════════════════════════════════
# PARTE 3 — ACTUALIZACIÓN FINAL DE LA DCEL (Aplicación del algoritmo)
# ══════════════════════════════════════════════════════════════════════════════
# ── Cambio: separar cruces reales de vértices compartidos ────────────────────
caras_activas_resultado = []
id_vert_inter = 1
R_ordenado = sorted(R, key=lambda t: (-t[0].y, t[0].x))

print("\n[DEBUG] === Procesando intersecciones como nuevos vértices ===")
for punto, segs in R_ordenado:
    aristas_actuales_a_procesar = []

    for s_original in segs:
        nombre_base = s_original.name if hasattr(s_original, 'name') else s_original.nombre
        encontrado = False
        for candidate in todasLasAristas:
            if nombre_base in candidate.nombre:
                p_start = candidate.verticeOriginal.coordenadas
                p_end   = candidate.pareja.verticeOriginal.coordenadas
                dist_total = math.hypot(p_end.x - p_start.x, p_end.y - p_start.y)
                dist1 = math.hypot(punto.x - p_start.x, punto.y - p_start.y)
                dist2 = math.hypot(punto.x - p_end.x,   punto.y - p_end.y)
                if abs(dist_total - (dist1 + dist2)) < 1e-7:
                    # Solo fragmentar si el punto cae ESTRICTAMENTE dentro
                    if dist1 > 1e-4 and dist2 > 1e-4:
                        aristas_actuales_a_procesar.append(candidate)
                        print(f"[DEBUG]   Intersección en {punto}: {candidate.nombre} será dividida (d1={dist1:.4f}, d2={dist2:.4f})")
                    encontrado = True
                    break   # ya encontramos el fragmento que contiene el punto
        if not encontrado:
            print(f"[DEBUG]   No se encontró arista para {nombre_base} en el punto {punto}")

    if len(aristas_actuales_a_procesar) >= 2:
        nuevo_vertice = NodoVertice(f"V_INT_{id_vert_inter}", punto)
        print(f"\n[DEBUG] >> Creando vértice {nuevo_vertice.nombre} en {punto}")
        id_vert_inter += 1
        procesar_interseccion(nuevo_vertice, aristas_actuales_a_procesar,
                              todosLosVertices, todasLasAristas, todasLasCaras)
    else:
        print(f"[DEBUG]   Intersección en {punto} NO generó al menos 2 aristas para dividir (encontradas: {len(aristas_actuales_a_procesar)}), se omite.")

# ── Unificar vértices compartidos entre layers y reconstruir ─────────────────
print("\n[DEBUG] Unificando vértices compartidos entre layers...")
def merge_collinear_edges(lista_aristas, lista_caras):
    """
    Fusiona aristas duplicadas que comparten mismos vértices origen y destino.
    Elimina los ciclos degenerados de área cero.
    """
    print("[DEBUG] Iniciando fusión de aristas colineales duplicadas...")
    grupos = defaultdict(list)
    for a in lista_aristas:
        # Usar nombres de vértices (hashables) como clave
        start_name = a.verticeOriginal.nombre
        end_name = a.pareja.verticeOriginal.nombre
        grupos[(start_name, end_name)].append(a)

    duplicados = {k: v for k, v in grupos.items() if len(v) > 1}
    if not duplicados:
        print("[DEBUG] No se encontraron aristas duplicadas para fusionar.")
        return

    for (start_name, end_name), aristas in duplicados.items():
        representante = aristas[0]
        # Ajustar las aristas duplicadas que serán eliminadas
        for dup in aristas[1:]:
            # Quitar dup de la cadena de su cara (anterior/siguiente)
            if dup.anterior:
                dup.anterior.siguiente = dup.siguiente
            if dup.siguiente:
                dup.siguiente.anterior = dup.anterior
            # Actualizar la pareja de dup para que apunte al representante
            twin = dup.pareja
            if twin:
                twin.pareja = representante
            # Reemplazar en las aristas internas de las caras si aparece
            for c in lista_caras:
                if dup in c.aristasInternos:
                    idx = c.aristasInternos.index(dup)
                    c.aristasInternos[idx] = representante
        # Eliminar las aristas duplicadas de la lista global
        lista_aristas[:] = [a for a in lista_aristas if a not in aristas[1:]]
        print(f"[DEBUG] Fusionadas {len(aristas)-1} duplicadas de ({start_name} -> {end_name})")

    # Después de fusionar, reconstruir caras para limpiar ciclos degenerados
    rearmar_caras(lista_aristas, lista_caras)

# ── Llamada a la función justo después de la unificación de vértices ─────
# ── Unificar vértices compartidos entre layers y fusionar aristas duplicadas ─
print("\n[DEBUG] Unificando vértices compartidos entre layers...")
unificar_vertices_coincidentes(todosLosVertices, todasLasAristas)

# Fusionar aristas colineales duplicadas (ciclos degenerados de área 0)
merge_collinear_edges(todasLasAristas, todasLasCaras)

# Reconstruir topología y volver a calcular caras
reconstruir_topologia(todasLasAristas)
rearmar_caras(todasLasAristas, todasLasCaras)

print(f"[DEBUG] Topología final: {len(todasLasAristas)} aristas, {len(todasLasCaras)} caras.")
# ══════════════════════════════════════════════════════════════════════════════
# RENOMBRADO FINAL DE LA DCEL
# ══════════════════════════════════════════════════════════════════════════════

def renombrar_dcel(vertices, aristas, caras):
    """
    Asigna nombres secuenciales limpios a todos los elementos de la DCEL
    y actualiza las referencias cruzadas para que sean consistentes.
    
    Convenciones:
      Vértices  → V1, V2, V3, ...
      Aristas   → A1, A2, A3, ...   (y su pareja siempre A<n>_T para "twin")
      Caras     → CARA1 (infinita), CARA2, CARA3, ...
    """

    # ─────────────────────────────────────────────────────────────────────
    # 1. IDENTIFICAR LA CARA INFINITA (la de mayor área absoluta)
    # ─────────────────────────────────────────────────────────────────────
    def _area_cara(cara):
        if not cara.aristasExternos:
            return 0.0
        area = 0.0
        inicio = cara.aristasExternos
        actual = inicio
        visitadas = set()
        while actual and id(actual) not in visitadas:
            visitadas.add(id(actual))
            p1 = actual.verticeOriginal.coordenadas
            p2 = actual.siguiente.verticeOriginal.coordenadas if actual.siguiente else p1
            area += p1.x * p2.y - p2.x * p1.y
            actual = actual.siguiente
            if actual == inicio:
                break
        return abs(area) / 2.0

    cara_infinita = max(caras, key=_area_cara) if caras else None

    # ─────────────────────────────────────────────────────────────────────
    # 2. RENOMBRAR VÉRTICES  →  V1, V2, …
    # ─────────────────────────────────────────────────────────────────────
    # Guardamos el mapeo viejo_nombre → nuevo_nombre por si hace falta auditar
    mapa_vertices = {}
    for idx, v in enumerate(vertices, start=1):
        nuevo = f"V{idx}"
        mapa_vertices[v.nombre] = nuevo
        v.nombre = nuevo

    # ─────────────────────────────────────────────────────────────────────
    # 3. RENOMBRAR ARISTAS en PAREJAS  →  A1 / A1_T, A2 / A2_T, …
    #    Recorremos sin repetir la pareja ya nombrada.
    # ─────────────────────────────────────────────────────────────────────
    mapa_aristas = {}
    contador_arista = 1
    ya_nombradas = set()           # usamos id() para no depender del nombre viejo

    for a in aristas:
        if id(a) in ya_nombradas:
            continue

        nombre_base = f"A{contador_arista}"
        nombre_twin = f"A{contador_arista}_T"
        contador_arista += 1

        mapa_aristas[a.nombre] = nombre_base
        a.nombre = nombre_base
        ya_nombradas.add(id(a))

        if a.pareja and id(a.pareja) not in ya_nombradas:
            mapa_aristas[a.pareja.nombre] = nombre_twin
            a.pareja.nombre = nombre_twin
            ya_nombradas.add(id(a.pareja))

    # ─────────────────────────────────────────────────────────────────────
    # 4. RENOMBRAR CARAS  →  CARA1 (infinita), CARA2, CARA3, …
    # ─────────────────────────────────────────────────────────────────────
    mapa_caras = {}
    if cara_infinita:
        mapa_caras[cara_infinita.nombre] = "CARA1"
        cara_infinita.nombre = "CARA1"

    contador_cara = 2
    for c in caras:
        if c is cara_infinita:
            continue
        nuevo = f"CARA{contador_cara}"
        mapa_caras[c.nombre] = nuevo
        c.nombre = nuevo
        contador_cara += 1

    # ─────────────────────────────────────────────────────────────────────
    # 5. ACTUALIZAR caras_activas_resultado con los nuevos nombres
    # ─────────────────────────────────────────────────────────────────────
    global caras_activas_resultado
    caras_activas_resultado = [
        mapa_caras.get(n, n) for n in caras_activas_resultado
    ]

    print(
        f"[DEBUG] [renombrar_dcel] "
        f"{len(vertices)} vértices, "
        f"{len(aristas)} aristas, "
        f"{len(caras)} caras renombrados correctamente."
    )
    return mapa_vertices, mapa_aristas, mapa_caras


# ── Llamada a la función ──────────────────────────────────────────────────────
print("\n[DEBUG] Renombrando todos los elementos de la DCEL...")
renombrar_dcel(todosLosVertices, todasLasAristas, todasLasCaras)

# ══════════════════════════════════════════════════════════════════════════════
# PARTE 4 — EXPORTAR RESULTADOS (Nuevos Vértices y Aristas)
# ══════════════════════════════════════════════════════════════════════════════

print("\nExportando nuevos archivos .vertices y .aristas...")
resultadosArchivo = "resultado"
# --- 1. Exportar archivo de Vértices ---
with open(resultadosArchivo + ".vertices", "w", encoding="utf-8") as f:
    f.write("#################################\n")
    f.write(f"{'Nombre':<15} {'x':<10} {'y':<10} {'Incidente'}\n")
    f.write("#################################\n")
    
    for v in todosLosVertices:
        # Extraemos el nombre de la arista incidente de forma segura
        incidente = "None"
        if hasattr(v, 'aristaAdyacente') and v.aristaAdyacente:
            incidente = v.aristaAdyacente.nombre if hasattr(v.aristaAdyacente, 'nombre') else str(v.aristaAdyacente)
        
        # Si las intersecciones nuevas no tienen arista incidente asignada, le buscamos una
        if incidente == "None":
            arista_encontrada = next((a for a in todasLasAristas if a.verticeOriginal == v), None)
            if arista_encontrada:
                incidente = arista_encontrada.nombre

        # Formatear a 4 decimales para mantener precisión geométrica
        f.write(f"{v.nombre:<15} {v.coordenadas.x:<10.4f} {v.coordenadas.y:<10.4f} {incidente}\n")

# --- 2. Exportar archivo de Aristas ---
with open(resultadosArchivo + ".aristas", "w", encoding="utf-8") as f:
    f.write("#################################################################\n")
    f.write(f"{'Nombre':<15} {'Origen':<15} {'Pareja':<15} {'Cara':<25} {'Sigue':<15} {'Antes'}\n")
    f.write("#################################################################\n")
    
    for a in todasLasAristas:
        # Extracción segura de nombres navegando por los punteros de la DCEL
        origen = a.verticeOriginal.nombre if hasattr(a.verticeOriginal, 'nombre') else "None"
        pareja = a.pareja.nombre if hasattr(a.pareja, 'nombre') else "None"
        cara   = a.cara.nombre if hasattr(a.cara, 'nombre') else "None"
        sigue  = a.siguiente.nombre if hasattr(a.siguiente, 'nombre') else "None"
        antes  = a.anterior.nombre if hasattr(a.anterior, 'nombre') else "None"
        
        f.write(f"{a.nombre:<15} {origen:<15} {pareja:<15} {cara:<25} {sigue:<15} {antes}\n")

print("Archivos 'resultado.vertices' y 'resultado.aristas' generados exitosamente.")

# --- 3. Exportar archivo de Caras (Formato Estricto) ---
print("\nExportando nuevos archivos .caras y .activos...")

# ¡AQUÍ ESTÁ LA SOLUCIÓN! Inicializamos las variables necesarias
id_cara = 2  # Iniciamos en 2 porque la infinita será siempre CARA1
caras_activas_resultado = []

with open(resultadosArchivo + ".caras", "w", encoding="utf-8") as f:
    f.write("Archivo de caras\n")
    f.write("#######################\n")
    f.write(f"{'Nombre':<8} {'Interno':<20} {'Externo'}\n")
    f.write("#######################\n")
    
    for c in todasLasCaras:
        # 1. Manejo de Ciclos Internos (Huecos)
        if c.aristasInternos:
            # Lista de nombres de las aristas que inician cada ciclo interno
            nombres_int = [a.nombre for a in c.aristasInternos]
            interno_str = f"[{','.join(nombres_int)}]"
        else:
            interno_str = "None"
            
        # 2. Manejo de Ciclo Externo (Borde de la cara)
        externo_str = c.aristasExternos.nombre if c.aristasExternos else "None"
        
        f.write(f"{c.nombre:<8} {interno_str:<20} {externo_str}\n")

# --- 4. Exportar archivo de Activos ---
with open(resultadosArchivo + ".activos", "w", encoding="utf-8") as f:
    f.write("Archivo de activos\n")
    f.write("#######################\n")
    f.write("Caras Activas\n")
    f.write("#######################\n")
    for c_activa in caras_activas_resultado:
        f.write(f"{c_activa}\n")

print("Archivos generados exitosamente.")


# ── Animación ─────────────────────────────────────────────────────────────────
all_x = [c for seg in S for c in (seg.p1.x, seg.p2.x)]
all_y = [c for seg in S for c in (seg.p1.y, seg.p2.y)]
x_min, x_max = min(all_x), max(all_x)
y_min, y_max = min(all_y), max(all_y)
pad_x = (x_max - x_min) * 0.03 or 1
pad_y = (y_max - y_min) * 0.03 or 1

fig2, ax2 = plt.subplots(figsize=(10, 7))

def update(i):
    frame = frames[i]
    ax2.cla()
    ax2.set_xlim(x_min - pad_x, x_max + pad_x)
    ax2.set_ylim(y_min - pad_y, y_max + pad_y)
    ax2.set_aspect('equal')

    for seg in S:
        ax2.plot([seg.p1.x, seg.p2.x], [seg.p1.y, seg.p2.y],
                 color='#cccccc', lw=1, zorder=1)

    for seg in frame['activos']:
        ax2.plot([seg.p1.x, seg.p2.x], [seg.p1.y, seg.p2.y],
                 color='steelblue', lw=2, zorder=2)

    ax2.axhline(y=frame['y'], color='limegreen', linestyle='--', lw=1.2,
                zorder=3, label=f"y = {frame['y']:.2f}")

    for punto, segs in frame['resultado']:
        ax2.plot(punto.x, punto.y, 'ro', markersize=5, zorder=4)

    ax2.plot(frame['punto'].x, frame['punto'].y, '*',
             color='gold', markersize=12, zorder=5, markeredgewidth=0.8)

    ax2.set_title(
        f"Evento {i + 1} / {len(frames)}  |  "
        f"tipo: {frame['tipo']}  |  "
        f"intersecciones: {len(frame['resultado'])}",
        fontsize=10
    )

ani = animation.FuncAnimation(
    fig2, update,
    frames=len(frames),
    interval=80,
    repeat=False,
)

plt.tight_layout()
plt.show()

# ══════════════════════════════════════════════════════════════════════════════
# PARTE 6 — VISUALIZACIÓN TOTAL (CARAS, ARISTAS Y VÉRTICES)
# ══════════════════════════════════════════════════════════════════════════════

def obtener_ciclo(cara):

    if not cara.aristasExternos:
        return []

    ciclo = []

    inicio = cara.aristasExternos
    actual = inicio

    visitadas = set()

    while actual and id(actual) not in visitadas:

        visitadas.add(id(actual))

        ciclo.append(actual)

        actual = actual.siguiente

        if actual == inicio:
            break

    return ciclo

fig_res, ax_res = plt.subplots(figsize=(10, 7))
ax_res.set_title("Layer de Resultados: Malla Completa (Caras, Aristas y Vértices)")

# 1. Dibujar el RELLENO de las caras
for cara in todasLasCaras:
    if cara.nombre == "CARA1": continue # No pintamos el infinito
    # Rellenamos con un azul transparente para que no tape las líneas
    dibujarCara(cara, ax_res, color='dodgerblue', rellenar=True)

# 2. ¡NUEVO! Dibujar las ARISTAS (las líneas que conectan todo)
# Esto es lo que te faltaba para ver cómo quedan al final
for a in todasLasAristas:
    p1 = a.verticeOriginal.coordenadas
    p2 = a.pareja.verticeOriginal.coordenadas
    # Dibujamos una línea negra fina para representar la arista
    ax_res.plot([p1.x, p2.x], [p1.y, p2.y], color='black', lw=1, zorder=3)

# 3. Dibujar todos los VÉRTICES
v_x = [v.coordenadas.x for v in todosLosVertices]
v_y = [v.coordenadas.y for v in todosLosVertices]
ax_res.scatter(v_x, v_y, color='black', s=20, zorder=5, label='Vértices')

# 4. Resaltar INTERSECCIONES en rojo (opcional, para mayor claridad)
v_int_x = [v.coordenadas.x for v in todosLosVertices if "V_INT" in v.nombre]
v_int_y = [v.coordenadas.y for v in todosLosVertices if "V_INT" in v.nombre]
if v_int_x:
    ax_res.scatter(v_int_x, v_int_y, color='red', s=40, zorder=6, label='Intersecciones')

ax_res.set_aspect('equal')
ax_res.legend(loc='upper right', fontsize='small')
plt.grid(True, linestyle=':', alpha=0.6)
plt.show()

# (opcional) Asegurar que se cierre ordenadamente al final
import atexit
@atexit.register
def cerrar_log():
    log_file.close()

# ══════════════════════════════════════════════════════════════════════════════
# PARTE 7 — VISUALIZACIÓN INTERACTIVA CON PYGAME
# ══════════════════════════════════════════════════════════════════════════════

import pygame

pygame.init()

# ─────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────

WIDTH = 1200
HEIGHT = 800
BACKGROUND = (25, 25, 25)

COLOR_ARISTA = (220, 220, 220)
COLOR_VERTICE = (255, 255, 255)
COLOR_INTERSECCION = (255, 80, 80)

COLOR_CARA_ACTIVA = (30, 144, 255)
COLOR_CARA_INACTIVA = (70, 70, 70)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("DCEL Interactiva")

clock = pygame.time.Clock()

# ─────────────────────────────────────────────────────────────
# TRANSFORMACIÓN MUNDO → PANTALLA
# ─────────────────────────────────────────────────────────────

all_x = [v.coordenadas.x for v in todosLosVertices]
all_y = [v.coordenadas.y for v in todosLosVertices]

min_x = min(all_x)
max_x = max(all_x)

min_y = min(all_y)
max_y = max(all_y)

padding = 50

world_w = max_x - min_x
world_h = max_y - min_y

scale_x = (WIDTH - padding * 2) / (world_w if world_w != 0 else 1)
scale_y = (HEIGHT - padding * 2) / (world_h if world_h != 0 else 1)

scale = min(scale_x, scale_y)

def world_to_screen(p: Punto):

    sx = (p.x - min_x) * scale + padding

    # invertir eje Y
    sy = HEIGHT - ((p.y - min_y) * scale + padding)

    return (int(sx), int(sy))


# ─────────────────────────────────────────────────────────────
# OBTENER POLÍGONO DE UNA CARA
# ─────────────────────────────────────────────────────────────

def face_polygon(cara):

    if not cara.aristasExternos:
        return []

    puntos = []

    inicio = cara.aristasExternos
    actual = inicio

    visitadas = set()

    while actual and id(actual) not in visitadas:

        visitadas.add(id(actual))

        puntos.append(
            world_to_screen(
                actual.verticeOriginal.coordenadas
            )
        )

        actual = actual.siguiente

        if actual == inicio:
            break

    return puntos


# ─────────────────────────────────────────────────────────────
# POINT IN POLYGON (PANTALLA)
# ─────────────────────────────────────────────────────────────

def point_in_polygon(point, polygon):

    x, y = point

    inside = False

    n = len(polygon)

    for i in range(n):

        j = (i + 1) % n

        xi, yi = polygon[i]
        xj, yj = polygon[j]

        intersect = (
            ((yi > y) != (yj > y))
            and
            (
                x <
                (xj - xi) * (y - yi)
                / ((yj - yi) + 1e-9)
                + xi
            )
        )

        if intersect:
            inside = not inside

    return inside


# ─────────────────────────────────────────────────────────────
# ESTADO DE ACTIVAS
# ─────────────────────────────────────────────────────────────

caras_activas = set(caras_activas_resultado)

# si quieres empezar todas apagadas:
# caras_activas = set()


# ─────────────────────────────────────────────────────────────
# LOOP
# ─────────────────────────────────────────────────────────────

running = True

while running:

    clock.tick(60)

    # ─────────────────────────────────────────
    # EVENTOS
    # ─────────────────────────────────────────

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:

            mouse_pos = pygame.mouse.get_pos()

            # buscamos desde la más pequeña primero
            # ayuda cuando hay contención
            caras_ordenadas = sorted(
                todasLasCaras,
                key=lambda c: abs(
                    area_ciclo(
                        obtener_ciclo(c)
                    )
                )
                if c.aristasExternos else 999999
            )

            for cara in caras_ordenadas:

                if cara.nombre == "CARA1":
                    continue

                poly = face_polygon(cara)

                if len(poly) < 3:
                    continue

                if point_in_polygon(mouse_pos, poly):

                    if cara.nombre in caras_activas:
                        caras_activas.remove(cara.nombre)
                    else:
                        caras_activas.add(cara.nombre)

                    break

    # ─────────────────────────────────────────
    # DRAW
    # ─────────────────────────────────────────

    screen.fill(BACKGROUND)

    # ─────────────────────────────────────────
    # DIBUJAR CARAS
    # CARA1 (infinita) se dibuja primero como
    # fondo; las caras finitas van encima.
    # ─────────────────────────────────────────

    COLOR_INF_ACTIVA   = ( 20,  60, 100)   # azul oscuro — infinita activa
    COLOR_INF_INACTIVA = ( 35,  35,  45)   # gris casi-negro — infinita inactiva

    # Ordenar de mayor a menor área absoluta:
    # CARA1 queda primero → se pinta como fondo.
    # Las caras pequeñas quedan al final → se pintan encima.
    caras_por_area = sorted(
        todasLasCaras,
        key=lambda c: (
            abs(area_ciclo(obtener_ciclo(c)))
            if c.aristasExternos else 0
        ),
        reverse=True,
    )

    for cara in caras_por_area:

        poly = face_polygon(cara)

        if len(poly) < 3:
            continue

        activa = cara.nombre in caras_activas

        if cara.nombre == "CARA1":
            # Cara infinita: relleno sólido que sirve de fondo
            color = COLOR_INF_ACTIVA if activa else COLOR_INF_INACTIVA
            pygame.draw.polygon(screen, color, poly)

        elif activa:
            pygame.draw.polygon(screen, COLOR_CARA_ACTIVA, poly)

        else:
            pygame.draw.polygon(screen, COLOR_CARA_INACTIVA, poly, width=1)

    # ─────────────────────────────────────────
    # DIBUJAR ARISTAS
    # ─────────────────────────────────────────

    aristas_vistas = set()

    for a in todasLasAristas:

        if a.nombre in aristas_vistas:
            continue

        aristas_vistas.add(a.nombre)
        aristas_vistas.add(a.pareja.nombre)

        p1 = world_to_screen(
            a.verticeOriginal.coordenadas
        )

        p2 = world_to_screen(
            a.pareja.verticeOriginal.coordenadas
        )

        pygame.draw.line(
            screen,
            COLOR_ARISTA,
            p1,
            p2,
            2
        )

    # ─────────────────────────────────────────
    # DIBUJAR VÉRTICES
    # ─────────────────────────────────────────

    for v in todosLosVertices:

        p = world_to_screen(v.coordenadas)

        color = COLOR_VERTICE

        if "V_INT" in v.nombre:
            color = COLOR_INTERSECCION

        pygame.draw.circle(
            screen,
            color,
            p,
            4
        )

    pygame.display.flip()

pygame.quit()
log_file.close()

