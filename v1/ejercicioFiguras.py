# ── Imports ───────────────────────────────────────────────────────────────────
# BUG 1 FIXED: imports duplicados eliminados (plt, dataclass, math aparecían 2 veces)
import math
import heapq
from dataclasses import dataclass, field
from typing import Optional, List
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.cm as cm
import numpy as np


# ══════════════════════════════════════════════════════════════════════════════
# CLASES
# ══════════════════════════════════════════════════════════════════════════════

# BUG 2 FIXED: Punto estaba definido DOS veces (una mutable y una frozen).
# Se unifica en una sola definición frozen=True que es hashable y sirve para
# ambas partes del programa (DCEL y línea de barrido).
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
    aristasExternos: List[NodoArista] = field(default_factory=list)


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
# BUG 3 FIXED: estas funciones estaban definidas DESPUÉS del bucle while Q
# que las necesitaba, causando NameError en tiempo de ejecución.
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

def dibujarCara(cara, subPlot, color, label=None):
    dibujarAristas(cara.aristasInternos, subPlot, color, label=label)
    dibujarAristas(cara.aristasExternos, subPlot, color)


# ══════════════════════════════════════════════════════════════════════════════
# PARTE 1 — VISUALIZACIÓN DCEL
# ══════════════════════════════════════════════════════════════════════════════

fig = plt.figure()
ax  = fig.add_subplot()

listaLayers = ["layer04", "layer05"]
colores = coloresPorLayer(listaLayers)

# Acumula TODAS las aristas ya resueltas de todos los layers
# para alimentar la línea de barrido en la Parte 2.
todasLasAristas: List[NodoArista] = []

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
        for attr in ("aristasInternos", "aristasExternos"):
            raw = getattr(c, attr)
            if isinstance(raw, str):
                raw = raw.strip("[]")
                setattr(c, attr,
                        [dicAristas[n] for n in raw.split(",") if n and n != "None"]
                        if raw and raw != "None" else [])

    # Guardar aristas ya resueltas para usarlas en el barrido
    todasLasAristas.extend(listaAristas)

    carasADibujar = (
        [c for c in listaCaras if c.nombre in listaCarasActivas]
        if listaCarasActivas else listaCaras
    )
    for i, cara in enumerate(carasADibujar):
        label = layer if i == 0 else None
        dibujarCara(cara, ax, color=color, label=label)

ax.legend(title="Layers")
ax.set_aspect("equal")
plt.tight_layout()
plt.show()


# ══════════════════════════════════════════════════════════════════════════════
# PARTE 2 — LÍNEA DE BARRIDO
# BUG 4 FIXED: el bloque de ejecución (while Q, prints, animación) estaba
# ANTES de la lectura del archivo y antes de que se definieran los eventos.
# Ahora el orden correcto es: leer → poblar Q → barrer → imprimir → animar.
# ══════════════════════════════════════════════════════════════════════════════

# Variables globales de la línea de barrido
S = set()
Q = []
dictPuntos = {}
# BUG 5 FIXED: era ClasesArbol.AVL() — ClasesArbol no existe; AVL está definido aquí
T = AVL()
R = set()
y_sweep = 0.0
_contador_ev = 0
frames = []

# ── Extraer segmentos desde la lista ligada de aristas de la DCEL ─────────────
# Cada arista `a` representa una semi-arista; su pareja `a.pareja` va en sentido
# contrario sobre la misma arista geométrica.  Para no duplicar segmentos se
# procesa solo una de las dos semi-aristas de cada par, usando el conjunto
# `vistasAristas` como guardia.
vistasAristas: set = set()

for a in todasLasAristas:
    if a.nombre in vistasAristas:
        continue                          # esta arista geométrica ya fue procesada
    vistasAristas.add(a.nombre)
    vistasAristas.add(a.pareja.nombre)   # marcar también la semi-arista gemela

    p1 = a.verticeOriginal.coordenadas           # Punto origen
    p2 = a.pareja.verticeOriginal.coordenadas    # Punto destino (= origen de la pareja)

    segmento = Segmento(a.nombre, p1, p2).organAlto()
    S.add(segmento)

    # Registrar evento superior (U) en p1
    if segmento.p1 in dictPuntos:
        dictPuntos[segmento.p1].eventoU.add(segmento)
    else:
        dictPuntos[segmento.p1] = evento(
            segmento.p1, eventoL=set(), eventoC=set(), eventoU={segmento})

    # Registrar evento inferior (L) en p2
    if segmento.p2 in dictPuntos:
        dictPuntos[segmento.p2].eventoL.add(segmento)
    else:
        dictPuntos[segmento.p2] = evento(
            segmento.p2, eventoL={segmento}, eventoC=set(), eventoU=set())

# ── Poblar la cola de prioridad ───────────────────────────────────────────────
for ev in dictPuntos.values():
    _contador_ev += 1
    heapq.heappush(Q, ((-ev.p.y, ev.p.x, _contador_ev), ev))

# ── Ejecutar el barrido ───────────────────────────────────────────────────────
# BUG 6 FIXED: era ClasesArbol.heapq.heappop y ClasesArbol.procesarEvento
while Q:
    _, eventop = heapq.heappop(Q)
    procesarEvento(eventop)

# ── Imprimir y guardar resultados ─────────────────────────────────────────────
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

# BUG 7 FIXED: era ClasesArbol.animation.FuncAnimation
ani = animation.FuncAnimation(
    fig2, update,
    frames=len(frames),
    interval=80,
    repeat=False,
)

plt.tight_layout()
# BUG 8 FIXED: faltaba plt.show() para mostrar la animación
plt.show()
