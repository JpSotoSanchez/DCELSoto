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
        nodos.sort(key=lambda n: x_at_y(n.valor, y_sweep))
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
        if abs(prueba) > 1e-9:
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
    if (segmento1.boundingBox[0] <= inter.x <= segmento1.boundingBox[1] and
            segmento1.boundingBox[2] <= inter.y <= segmento1.boundingBox[3] and
            segmento2.boundingBox[0] <= inter.x <= segmento2.boundingBox[1] and
            segmento2.boundingBox[2] <= inter.y <= segmento2.boundingBox[3]):
        return [inter]
    return []


# ══════════════════════════════════════════════════════════════════════════════
# PROCESAMIENTO DE EVENTOS (línea de barrido)
# ══════════════════════════════════════════════════════════════════════════════

def procesarEvento(p):
    global y_sweep
    y_sweep = p.p.y

    U = p.eventoU
    L = p.eventoL
    C = T.buscarContenedores(p.p)

    unionULC = U | L | C
    unionUC  = U | C

    if len(unionULC) > 1:
        R.add((p.p, frozenset(unionULC)))

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
        debajo = inter.y < p.y - 1e-9
        mismaAltura_derecha = abs(inter.y - p.y) < 1e-9 and inter.x > p.x + 1e-9

        if debajo or mismaAltura_derecha:
            if inter not in dictPuntos:
                _contador_ev += 1
                ev = evento(inter, eventoL=set(), eventoC={sL.valor, sR.valor}, eventoU=set())
                dictPuntos[inter] = ev
                heapq.heappush(Q, ((-inter.y, inter.x, _contador_ev), ev))


# ══════════════════════════════════════════════════════════════════════════════
# FUNCIONES DE ACTUALIZACIÓN DCEL (ALGORITMO)
# ══════════════════════════════════════════════════════════════════════════════

def procesar_interseccion(vertice_x: NodoVertice, aristas_intersecadas: List[NodoArista],
                          lista_vertices: List[NodoVertice], lista_aristas: List[NodoArista],
                          lista_caras: List[NodoCara]):
    lista_vertices.append(vertice_x)

    primos = {}
    primo_primos = {}
    aristas_a_eliminar = []

    for arista in aristas_intersecadas:
        aristas_a_eliminar.append(arista)
        aristas_a_eliminar.append(arista.pareja)

        primo = NodoArista(f"{arista.nombre}_P")
        primo.verticeOriginal = arista.verticeOriginal

        primo_primo = NodoArista(f"{arista.nombre}_PP")
        primo_primo.verticeOriginal = vertice_x

        pareja_primo = NodoArista(f"{arista.pareja.nombre}_P")
        pareja_primo.verticeOriginal = arista.pareja.verticeOriginal

        pareja_primo_primo = NodoArista(f"{arista.pareja.nombre}_PP")
        pareja_primo_primo.verticeOriginal = vertice_x

        primos[arista.nombre] = primo
        primo_primos[arista.nombre] = primo_primo
        primos[arista.pareja.nombre] = pareja_primo
        primo_primos[arista.pareja.nombre] = pareja_primo_primo

        primo.anterior = arista.anterior
        pareja_primo.anterior = arista.pareja.anterior

        primo_primo.siguiente = arista.siguiente
        pareja_primo_primo.siguiente = arista.pareja.siguiente

        if arista.anterior:
            arista.anterior.siguiente = primo
        if arista.siguiente:
            arista.siguiente.anterior = primo_primo

        if arista.pareja.anterior:
            arista.pareja.anterior.siguiente = pareja_primo
        if arista.pareja.siguiente:
            arista.pareja.siguiente.anterior = pareja_primo_primo

    vectores_salida = []
    for nombre_arista, pp in primo_primos.items():
        v_destino = pp.siguiente.verticeOriginal.coordenadas
        v_origen = vertice_x.coordenadas
        angulo = math.atan2(v_destino.y - v_origen.y, v_destino.x - v_origen.x)
        vectores_salida.append((angulo, nombre_arista))

    vectores_salida.sort(key=lambda x: x[0], reverse=True)

    n = len(vectores_salida)
    for i in range(n):
        id_actual = vectores_salida[i][1]
        id_siguiente_circular = vectores_salida[(i + 1) % n][1]

        P_actual = primos[id_actual]
        PP_actual = primo_primos[id_actual]

        arista_orig = next(a for a in aristas_a_eliminar if a.nombre == id_actual)
        id_pareja_original = arista_orig.pareja.nombre

        P_actual.pareja = primo_primos[id_pareja_original]
        primo_primos[id_pareja_original].pareja = P_actual

        P_actual.siguiente = primo_primos[id_siguiente_circular]
        primo_primos[id_siguiente_circular].anterior = P_actual

    lista_aristas[:] = [a for a in lista_aristas if a not in aristas_a_eliminar]
    lista_aristas.extend(primos.values())
    lista_aristas.extend(primo_primos.values())

    rearmar_caras(lista_aristas, lista_caras)

def rearmar_caras(lista_aristas: List[NodoArista], lista_caras: List[NodoCara]):
    lista_caras.clear()
    
    # 1. Extraer todos los ciclos cerrados de la DCEL
    ciclos = []
    visitadas = set()
    for a in lista_aristas:
        if a.nombre not in visitadas:
            ciclo = []
            actual = a
            while True:
                ciclo.append(actual)
                visitadas.add(actual.nombre)
                actual = actual.siguiente
                if actual == a or actual is None: break
            if len(ciclo) >= 3:
                ciclos.append(ciclo)
            
    # 2. Clasificar cada ciclo (CCW = Borde Externo, CW = Hueco)
    class CicloInfo:
        def __init__(self, aristas):
            self.aristas = aristas
            area = 0.0
            min_x = float('inf')
            self.v_left = None
            for i in range(len(aristas)):
                p1 = aristas[i].verticeOriginal.coordenadas
                p2 = aristas[(i+1)%len(aristas)].verticeOriginal.coordenadas
                area += (p1.x * p2.y - p2.x * p1.y)
                if p1.x < min_x:
                    min_x, self.v_left = p1.x, aristas[i].verticeOriginal
            self.es_externo = (area > 0) # CCW
            self.cara_asignada = None

    infos = [CicloInfo(c) for c in ciclos]
    
    # 3. Crear las caras
    cara_infinita = NodoCara("CARA1") 
    lista_caras.append(cara_infinita)
    
    id_c = 2
    # Primero: Cada ciclo EXTERNO es una CARA nueva
    for info in infos:
        if info.es_externo:
            nueva = NodoCara(f"CARA{id_c}")
            nueva.aristasExternos = info.aristas[0]
            info.cara_asignada = nueva
            lista_caras.append(nueva)
            id_c += 1
            
    # Segundo: Los ciclos INTERNOS son huecos (Interno)
    # Por simplificación, si no sabes en qué cara cae, van a la CARA1
    for info in infos:
        if not info.es_externo:
            # Aquí podrías usar punto_en_poligono para ver en qué CARA cae el hueco
            # Por ahora, los mandamos a la CARA1 como en tu ejemplo
            cara_infinita.aristasInternos.append(info.aristas[0])
            info.cara_asignada = cara_infinita

    # 4. Asignar la cara a cada arista
    for info in infos:
        for a in info.aristas:
            a.cara = info.cara_asignada 

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

listaLayers = ["layer01", "layer03", "layer04"]
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
                    arista = NodoArista(Nombre)
                    arista.verticeOriginal = Origen
                    arista.pareja    = Pareja
                    arista.cara      = Cara
                    arista.siguiente = Sigue
                    arista.anterior  = Antes
                    listaAristas.append(arista)

        elif ".vertice" in archivo:
            with open(archivo, "r", encoding="utf-8") as f:
                lineas = [l.strip() for l in f if l.strip() and not l.startswith("#")]
            for linea in lineas:
                partes = linea.split()
                if len(partes) == 4 and not linea.startswith("Nombre"):
                    Nombre, x, y, Incidente = partes
                    listaVertices.append(NodoVertice(Nombre, Punto(float(x), float(y)), Incidente))

        elif ".cara" in archivo:
            with open(archivo, "r", encoding="utf-8") as f:
                lineas = [l.strip() for l in f if l.strip() and not l.startswith("#")]
            for linea in lineas:
                partes = linea.split()
                if len(partes) == 3 and not linea.startswith("Nombre") and not linea.startswith("Archivo"):
                    Nombre, Interno, Externo = partes
                    listaCaras.append(NodoCara(Nombre, Interno, Externo))

        elif ".activos" in archivo:
            try:
                with open(archivo, "r", encoding="utf-8") as f:
                    lineas = [l.strip() for l in f if l.strip() and not l.startswith("#")]
                for linea in lineas:
                    partes = linea.split()
                    if len(partes) == 1 and not linea.startswith("Caras"):
                        listaCarasActivas.append(linea)
            except Exception:
                pass

    dicVertices = {v.nombre: v for v in listaVertices}
    dicAristas  = {a.nombre: a for a in listaAristas}
    dicCaras    = {c.nombre: c for c in listaCaras}

    for a in listaAristas:
        a.verticeOriginal = dicVertices[a.verticeOriginal]
        a.pareja          = dicAristas[a.pareja]
        a.siguiente       = dicAristas[a.siguiente]
        a.anterior        = dicAristas[a.anterior]
        a.cara            = dicCaras[a.cara]

    for v in listaVertices:
        if isinstance(v.aristaAdyacente, str):
            v.aristaAdyacente = dicAristas[v.aristaAdyacente]

    for c in listaCaras:
        # --- Tratar aristas Internas (Siguen siendo Lista) ---
        raw_int = c.aristasInternos
        if isinstance(raw_int, str):
            raw_int = raw_int.strip("[]")
            c.aristasInternos = [dicAristas[n] for n in raw_int.split(",") if n and n != "None"]

        # --- Tratar aristas Externas (AHORA ES UN SOLO OBJETO) ---
        raw_ext = c.aristasExternos
        if isinstance(raw_ext, str):
            raw_ext = raw_ext.strip("[]")
            # Tomamos solo el primer elemento si existe
            nombres_ext = [n for n in raw_ext.split(",") if n and n != "None"]
            c.aristasExternos = dicAristas[nombres_ext[0]] if nombres_ext else None

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

    if segmento.p1 in dictPuntos:
        dictPuntos[segmento.p1].eventoU.add(segmento)
    else:
        dictPuntos[segmento.p1] = evento(
            segmento.p1, eventoL=set(), eventoC=set(), eventoU={segmento})

    if segmento.p2 in dictPuntos:
        dictPuntos[segmento.p2].eventoL.add(segmento)
    else:
        dictPuntos[segmento.p2] = evento(
            segmento.p2, eventoL={segmento}, eventoC=set(), eventoU=set())

for ev in dictPuntos.values():
    _contador_ev += 1
    heapq.heappush(Q, ((-ev.p.y, ev.p.x, _contador_ev), ev))

while Q:
    _, eventop = heapq.heappop(Q)
    procesarEvento(eventop)


print("Intersecciones encontradas:")
for punto, segs in R:
    nombres = [s.name for s in segs]
    print(f"  {punto} → {nombres}")
print(len(R))

txt_filename = "intersecciones3.txt"
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

print("\nReconstruyendo la estructura de la DCEL...")
id_vert_inter = 1

# Ordenamos las intersecciones por Y descendente
R_ordenado = sorted(R, key=lambda t: (-t[0].y, t[0].x))

for punto, segs in R_ordenado:
    aristas_actuales_a_procesar = []
    
    for s_original in segs:
        # En el barrido, segs guarda objetos de tipo segmento de línea, no NodoArista.
        # Buscamos el nombre base (ej. 'f1') ignorando si es un primo.
        nombre_base = s_original.name if hasattr(s_original, 'name') else s_original.nombre
        
        for candidate in todasLasAristas:
            if nombre_base in candidate.nombre:
                p_start = candidate.verticeOriginal.coordenadas
                p_end = candidate.pareja.verticeOriginal.coordenadas
                
                # Calculamos distancias reales
                dist_total = math.hypot(p_end.x - p_start.x, p_end.y - p_start.y)
                dist1 = math.hypot(punto.x - p_start.x, punto.y - p_start.y)
                dist2 = math.hypot(punto.x - p_end.x, punto.y - p_end.y)
                
                # Si el punto cae sobre el segmento...
                if abs(dist_total - (dist1 + dist2)) < 1e-7:
                    # ¡AQUÍ ESTÁ LA SOLUCIÓN AL PROBLEMA DE LAYER05!
                    # Si la distancia a los extremos es muy pequeña, es una esquina original.
                    # Solo lo agregamos para fragmentar si está estrictamente en medio de la línea.
                    if dist1 > 1e-4 and dist2 > 1e-4:
                        aristas_actuales_a_procesar.append(candidate)
                    break 
                    
    # Solo procesamos si hay al menos 2 aristas que de verdad se cruzan en medio de su trayectoria
    if len(aristas_actuales_a_procesar) >= 2:
        nuevo_vertice = NodoVertice(f"V_INT_{id_vert_inter}", punto)
        id_vert_inter += 1
        
        procesar_interseccion(nuevo_vertice, aristas_actuales_a_procesar, 
                              todosLosVertices, todasLasAristas, todasLasCaras)

print(f"¡Listo! Sistema reconstruido con {len(todasLasAristas)} aristas.")

# ══════════════════════════════════════════════════════════════════════════════
# PARTE 4 — EXPORTAR RESULTADOS (Nuevos Vértices y Aristas)
# ══════════════════════════════════════════════════════════════════════════════

print("\nExportando nuevos archivos .vertices y .aristas...")

# --- 1. Exportar archivo de Vértices ---
with open("resultado.vertices", "w", encoding="utf-8") as f:
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
with open("resultado.aristas", "w", encoding="utf-8") as f:
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

with open("resultado.caras", "w", encoding="utf-8") as f:
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
with open("resultado.activos", "w", encoding="utf-8") as f:
    f.write("Archivo de activos\n")
    f.write("#######################\n")
    f.write("Caras Activas\n")
    f.write("#######################\n")
    for c_activa in caras_activas_resultado:
        f.write(f"{c_activa}\n")

print("Archivos 'resultado.caras' y 'resultado.activos' generados exitosamente.")

print("Archivos 'resultado.caras' y 'resultado.activos' generados exitosamente.")

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
# PARTE 5 — VISUALIZACIÓN TOTAL (CARAS, ARISTAS Y VÉRTICES)
# ══════════════════════════════════════════════════════════════════════════════
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