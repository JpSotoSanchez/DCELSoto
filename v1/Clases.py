import math
from collections import deque
from dataclasses import dataclass, field

tol = 1e-6


# BUG 1 FIXED: unsafe_hash=True para que Punto sea hashable aunque defina __eq__
@dataclass(unsafe_hash=True)
class Punto:
    x: float
    y: float

    def trasSuma(self, x, y):
        newX = self.x + x
        newY = self.y + y
        return Punto(newX, newY)

    def trasMult(self, x, y):
        newX = self.x * x
        newY = self.y * y
        return Punto(newX, newY)

    def rotar(self, rad):
        newX = self.x * math.cos(rad) - self.y * math.sin(rad)
        newY = self.x * math.sin(rad) + self.y * math.cos(rad)
        return Punto(newX, newY)

    def corPolar(self):
        radio = math.sqrt(self.x ** 2 + self.y ** 2)
        # BUG 2 FIXED: math.arctan no existe en Python; usar math.atan2
        # BUG 3 FIXED: self.nombre no existe en Punto; eliminado del print
        theta = math.atan2(self.y, self.x)
        print(f"r: {radio}, theta: {theta}")
        return (radio, theta)

    def distancia(self, punto2):
        return math.sqrt((punto2.x - self.x) ** 2 + (punto2.y - self.y) ** 2)

    def __eq__(self, other):
        if other is None:
            return False
        if not isinstance(other, Punto):
            return False
        return (abs(self.x - other.x) < tol) and (abs(self.y - other.y) < tol)


def comparar2puntos(puntoA, puntoB):
    if (abs(puntoA.x - puntoB.x) < tol) and (abs(puntoA.y - puntoB.y) < tol):
        return True
    else:
        return False

def distancia2puntos(punto, punto2):
    return math.sqrt((punto2.x - punto.x) ** 2 + (punto2.y - punto.y) ** 2)

def alturaMinPuntos(puntos):
    return (max(p.y for p in puntos) - min(p.y for p in puntos))

def alturaMinima(puntos):
    hull = ConvexHull(puntos).hull
    n = len(hull)
    minAltura = float('inf')

    for i in range(n):
        p1 = hull[i]
        p2 = hull[(i + 1) % n]
        ang = math.atan2(p2.y - p1.y, p2.x - p1.x)
        rotados = rotarFigura(puntos, -ang)
        h = alturaMinPuntos(rotados)
        if h < minAltura:
            minAltura = h

    return minAltura

def rotarFigura(puntos, ang):
    puntosRotados = []
    for punto in puntos:
        puntoNuevo = punto.rotar(ang)
        puntosRotados.append(puntoNuevo)
    return puntosRotados


@dataclass
class Segmento:
    p1: Punto
    p2: Punto
    boundingBox: tuple = field(init=False)
    long: float = field(init=False)
    ang: float = field(init=False)

    def __post_init__(self):
        self.boundingBox = (
            min(self.p1.x, self.p2.x),
            max(self.p1.x, self.p2.x),
            min(self.p1.y, self.p2.y),
            max(self.p1.y, self.p2.y)
        )
        self.long = self.p1.distancia(self.p2)

        if self.long == 0:
            self.ang = 0.0
        else:
            valor = abs((self.p1.x - self.p2.x) / self.long)
            valor = max(-1.0, min(1.0, valor))
            self.ang = math.acos(valor)

    def organAlto(self):
        # BUG 4 FIXED: los casos sin intercambio hacían "return" (devolvían None)
        # Ahora devuelven self correctamente
        if self.p1.y > self.p2.y:
            return self                    # ya está ordenado
        elif self.p1.y == self.p2.y:
            if self.p1.x < self.p2.x:
                return self                # ya está ordenado
            else:
                extra = self.p2
                self.p2 = self.p1
                self.p1 = extra
                return self
        else:
            extra = self.p2
            self.p2 = self.p1
            self.p1 = extra
            return self

    def yInBound(self, altura):
        if altura >= self.boundingBox[2] and altura <= self.boundingBox[3]:
            return True
        return False


@dataclass
class Linea:
    A: float
    B: float
    C: float

    def __str__(self) -> str:
        m = -self.A / self.B
        b = -self.C / self.B
        return f"Linea: y = {m}x + {b}"


@dataclass
class Vector:
    p1: Punto
    p2: Punto

    def __post_init__(self):
        self.boundingBox = (
            min(self.p1.x, self.p2.x),
            max(self.p1.x, self.p2.x),
            min(self.p1.y, self.p2.y),
            max(self.p1.y, self.p2.y)
        )
        self.long = self.p1.distancia(self.p2)
        self.ang = math.acos(abs((self.p1.x - self.p2.x) / self.long))


@dataclass
class ConvexHull:
    puntos: list

    def __post_init__(self):
        p0 = min(self.puntos, key=lambda p: (p.y, p.x))
        pila = deque()
        for p in self.puntos:
            if p != p0:
                ang = math.atan2(p.y - p0.y, p.x - p0.x)
                pila.append((ang, p))
        pila = sorted(pila, key=lambda x: x[0])
        pila = deque([x[1] for x in pila])
        S = deque()
        S.append(p0)
        S.append(pila.popleft())
        S.append(pila.popleft())

        while pila:
            p = pila.popleft()
            while len(S) >= 2:
                o = S[-2]
                a = S[-1]
                if productoCruz(o, a, p) <= 0:
                    S.pop()
                else:
                    break
            S.append(p)
        self.hull = list(S)

    def area(self):
        suma = 0
        n = len(self.hull)
        for i in range(n):
            suma += self.hull[i].y * (self.hull[i - 1].x - self.hull[(i + 1) % n].x)
        return abs(0.5 * suma)


def relacionar(nodoPadre, nodoHijo):
    nodoPadre.hijos.append(nodoHijo)
    nodoHijo.padre = nodoPadre

def ancestros(nodo):
    explorador = nodo
    lista = [nodo]
    while explorador.padre:
        explorador = explorador.padre
        lista.append(explorador)
    return lista

def ancestros2(nodo):
    if not nodo.padre:
        return [nodo]
    return [nodo] + ancestros2(nodo.padre)

def descendientes(nodo):
    explorador = nodo
    lista = [nodo]
    for i in range(len(explorador.hijos)):
        lista += descendientes(explorador.hijos[i])
    return lista

def descendientestotales(nodo):
    explorador = nodo
    suma = 1
    for i in range(len(explorador.hijos)):
        suma += descendientestotales(explorador.hijos[i])
    return suma

def sumatotal(nodo):
    explorador = megapadre(nodo)
    suma = descendientestotales(explorador)
    return suma

def relizq(nodoPadre, nodoHijo):
    nodoHijo.nodoPadre = nodoPadre
    nodoPadre.izq = nodoHijo

def relder(nodoPadre, nodoHijo):
    nodoHijo.nodoPadre = nodoPadre
    nodoPadre.der = nodoHijo

def sumaabajo(nodo):
    suma = 1
    if nodo.izq:
        suma += sumaabajo(nodo.izq)
    if nodo.der:
        suma += sumaabajo(nodo.der)
    return suma

def dfs(nodo, n):
    lista = []
    if n == 1:
        lista.append(nodo)
    if nodo.izq:
        lista.extend(dfs(nodo.izq, n))
    if n == 2:
        lista.append(nodo)
    if nodo.der:
        lista.extend(dfs(nodo.der, n))
    if n == 3:
        lista.append(nodo)
    return lista

def bfs(nodo):
    fila = deque()
    fila.append(nodo)
    resultado = []
    while fila:
        activo = fila.popleft()
        resultado.append(activo)
        if activo.izq:
            fila.append(activo.izq)
        if activo.der:
            fila.append(activo.der)
    return resultado


class Nodo:
    def __init__(self, valor):
        self.valor = valor
        self.padre = None
        self.izq = None
        self.der = None

    def hijos(self):
        r = []
        if self.izq:
            r.append(self.izq)
        if self.der:
            r.append(self.der)
        return r

    def __repr__(self):
        return f"Nodo {self.valor}"


class BST:
    def __init__(self):
        self.raiz = None

    def insertar(self, valor):
        if not self.raiz:
            nuevo = Nodo(valor)
            self.raiz = nuevo
            return nuevo
        else:
            actual = self.raiz
            while True:
                if actual.valor == valor:
                    return actual
                elif valor < actual.valor:
                    if not actual.izq:
                        nuevo = Nodo(valor)
                        nuevo.padre = actual
                        actual.izq = nuevo
                        return nuevo
                    actual = actual.izq
                else:
                    if not actual.der:
                        nuevo = Nodo(valor)
                        nuevo.padre = actual
                        actual.der = nuevo
                        return nuevo
                    actual = actual.der

    def ancestros(self, nodo):
        actual = nodo
        l = [nodo]
        while actual.padre:
            actual = actual.padre
            l.append(actual)
        return l

    def inorden(self, nodo):
        l = []
        if nodo.izq:
            l.extend(self.inorden(nodo.izq))
        l.append(nodo)
        if nodo.der:
            l.extend(self.inorden(nodo.der))
        return l

    def mayor(self, nodo):
        while nodo.der:
            nodo = nodo.der
        return nodo

    def menor(self, nodo):
        while nodo.izq:
            nodo = nodo.izq
        return nodo

    def buscar(self, valor):
        actual = self.raiz
        while True:
            if actual.valor == valor:
                return actual
            elif valor < actual.valor:
                if not actual.izq:
                    return None
                actual = actual.izq
            else:
                if not actual.der:
                    return None
                actual = actual.der

    def derecha(self, nodo):
        return nodo.der

    # BUG 5 FIXED: retornaba nodo.der en vez de nodo.izq
    def izquierda(self, nodo):
        return nodo.izq


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

    # BUG 6 FIXED: comparación usaba valor.p1.x (específico de Segmento)
    # Ahora usa comparación genérica con < y ==
    def insertar(self, valor):
        if not self.raiz:
            self.raiz = Nodo(valor)
            return self.raiz
        actual = self.raiz
        while True:
            if actual.valor == valor:
                return actual
            elif valor < actual.valor:
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
        actual = self.raiz
        while actual:
            if actual.valor == valor:
                return actual
            elif valor < actual.valor:
                actual = actual.izq
            else:
                actual = actual.der
        return None

    def sucesor(self, nodo):
        if nodo is None:
            return None
        if nodo.der:
            actual = nodo.der
            while actual.izq:
                actual = actual.izq
            return actual
        actual = nodo
        padre = nodo.padre
        while padre and actual == padre.der:
            actual = padre
            padre = padre.padre
        return padre

    def predecesor(self, nodo):
        if nodo is None:
            return None
        if nodo.izq:
            actual = nodo.izq
            while actual.der:
                actual = actual.der
            return actual
        actual = nodo
        padre = nodo.padre
        while padre and actual == padre.izq:
            actual = padre
            padre = padre.padre
        return padre

    def eliminar(self, valor):
        nodo = self.buscar(valor)
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

    def inorden(self, nodo=None):
        if nodo is None:
            nodo = self.raiz
        l = []
        if nodo is None:
            return l
        if nodo.izq:
            l.extend(self.inorden(nodo.izq))
        l.append(nodo)
        if nodo.der:
            l.extend(self.inorden(nodo.der))
        return l

    def ancestros(self, nodo):
        actual = nodo
        l = [nodo]
        while actual.padre:
            actual = actual.padre
            l.append(actual)
        return l

    def rango(self, valormin, valormax):
        return [n for n in self.inorden() if valormin <= n.valor <= valormax]

    def esta_balanceado(self):
        if self.raiz is None:
            return True
        cola = [self.raiz]
        while cola:
            nodo = cola.pop(0)
            if abs(self._factor(nodo)) > 1:
                return False
            if nodo.izq:
                cola.append(nodo.izq)
            if nodo.der:
                cola.append(nodo.der)
        return True


def profundidad(nodo):
    explorador = nodo
    suma = 0
    while explorador.padre:
        explorador = explorador.padre
        suma += 1
    return suma

def megapadre(nodo):
    explorador = nodo
    while explorador.padre:
        explorador = explorador.padre
    return explorador

def altura(nodo):
    if nodo is None:
        return -1
    prof_izq = altura(nodo.izq)
    prof_der = altura(nodo.der)
    return 1 + max(prof_izq, prof_der)

def menor(nodo):
    while nodo.izq:
        nodo = nodo.izq
    return nodo

def mayor(nodo):
    while nodo.der:
        nodo = nodo.der
    return nodo


def segALinea(segmento):
    x1 = segmento.p1.x
    x2 = segmento.p2.x
    y1 = segmento.p1.y
    y2 = segmento.p2.y
    A = y1 - y2
    B = x2 - x1
    C = x1 * y2 - y1 * x2
    return Linea(A, B, C)

def interseccionLineas(linea1, linea2):
    detGen = linea1.A * linea2.B - linea1.B * linea2.A
    if detGen == 0:
        return None
    detX = (-(linea1.C)) * linea2.B - linea1.B * (-(linea2.C))
    detY = linea1.A * (-(linea2.C)) - (-(linea1.C)) * linea2.A
    newX = detX / detGen
    newY = detY / detGen
    return Punto(newX, newY)

def distanciaLinPunto(linea, punto):
    lineaPerpen = perpenLinPunto(linea, punto)
    inter = interseccionLineas(linea, lineaPerpen)
    return distancia2puntos(inter, punto)

def perpenLinPunto(linea, punto):
    cperpen = linea.B * punto.x - linea.A * punto.y
    aperpen = -linea.B
    bperpen = linea.A
    return Linea(aperpen, bperpen, cperpen)

def distanciaSegPunto(segmento, punto):
    lineaSeg = segALinea(segmento)
    lineaPerpen = perpenLinPunto(lineaSeg, punto)
    inter = interseccionLineas(lineaSeg, lineaPerpen)
    if (segmento.boundingBox[0] < inter.x and segmento.boundingBox[1] > inter.x
            and segmento.boundingBox[2] < inter.y and segmento.boundingBox[3] > inter.y):
        return distancia2puntos(inter, punto)
    else:
        return min(distancia2puntos(segmento.p1, punto),
                   distancia2puntos(segmento.p2, punto))

def interseccionSeg(segmento1, segmento2):
    lineaSeg1 = segALinea(segmento1)
    lineaSeg2 = segALinea(segmento2)
    inter = interseccionLineas(lineaSeg1, lineaSeg2)

    if inter is None:
        return None

    if (segmento1.boundingBox[0] <= inter.x <= segmento1.boundingBox[1] and
            segmento1.boundingBox[2] <= inter.y <= segmento1.boundingBox[3] and
            segmento2.boundingBox[0] <= inter.x <= segmento2.boundingBox[1] and
            segmento2.boundingBox[2] <= inter.y <= segmento2.boundingBox[3]):
        return inter
    else:
        return None

def productoCruz(o, a, b):
    return (a.x - o.x) * (b.y - o.y) - (a.y - o.y) * (b.x - o.x)