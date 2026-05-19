from collections import deque


# ── Nodo ─────────────────────────────────────────────────────────────────────

class Nodo:
    """Nodo binario genérico."""

    def __init__(self, valor):
        self.valor = valor
        self.padre = None
        self.izq = None
        self.der = None

    def hijos(self):
        return [n for n in (self.izq, self.der) if n]

    def __repr__(self):
        return f"Nodo({self.valor})"


# ── funciones de árbol genéricas ─────────────────────────────────────────────

def relacionar(nodoPadre, nodoHijo):
    nodoPadre.hijos.append(nodoHijo)
    nodoHijo.padre = nodoPadre

def relizq(nodoPadre, nodoHijo):
    nodoHijo.nodoPadre = nodoPadre
    nodoPadre.izq = nodoHijo

def relder(nodoPadre, nodoHijo):
    nodoHijo.nodoPadre = nodoPadre
    nodoPadre.der = nodoHijo

def profundidad(nodo):
    explorador, suma = nodo, 0
    while explorador.padre:
        explorador = explorador.padre
        suma += 1
    return suma

def megapadre(nodo):
    while nodo.padre:
        nodo = nodo.padre
    return nodo

def altura(nodo):
    """Altura del subárbol enraizado en `nodo`. Nodo None → -1."""
    if nodo is None:
        return -1
    return 1 + max(altura(nodo.izq), altura(nodo.der))

def menor(nodo):
    while nodo.izq:
        nodo = nodo.izq
    return nodo

def mayor(nodo):
    while nodo.der:
        nodo = nodo.der
    return nodo

def ancestros(nodo):
    lista, explorador = [nodo], nodo
    while explorador.padre:
        explorador = explorador.padre
        lista.append(explorador)
    return lista

def descendientes(nodo):
    lista = [nodo]
    for hijo in nodo.hijos():
        lista += descendientes(hijo)
    return lista

def descendientestotales(nodo):
    return 1 + sum(descendientestotales(h) for h in nodo.hijos())

def sumaabajo(nodo):
    suma = 1
    if nodo.izq:
        suma += sumaabajo(nodo.izq)
    if nodo.der:
        suma += sumaabajo(nodo.der)
    return suma

def dfs(nodo, n):
    """Recorrido en profundidad. n=1 preorden, n=2 inorden, n=3 postorden."""
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
    fila, resultado = deque([nodo]), []
    while fila:
        activo = fila.popleft()
        resultado.append(activo)
        if activo.izq:
            fila.append(activo.izq)
        if activo.der:
            fila.append(activo.der)
    return resultado


# ── BST ──────────────────────────────────────────────────────────────────────

class BST:
    def __init__(self):
        self.raiz = None

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
                    return nuevo
                actual = actual.izq
            else:
                if not actual.der:
                    nuevo = Nodo(valor)
                    nuevo.padre = actual
                    actual.der = nuevo
                    return nuevo
                actual = actual.der

    def buscar(self, valor):
        actual = self.raiz
        while actual:
            if actual.valor == valor:
                return actual
            actual = actual.izq if valor < actual.valor else actual.der
        return None

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

    def mayor(self, nodo):
        return mayor(nodo)

    def menor(self, nodo):
        return menor(nodo)

    def ancestros(self, nodo):
        return ancestros(nodo)

    def derecha(self, nodo):
        return nodo.der

    def izquierda(self, nodo):
        return nodo.izq


# ── AVL ──────────────────────────────────────────────────────────────────────

class AVL:
    def __init__(self):
        self.raiz = None

    # ── balance ──────────────────────────────────────────────────────────────

    def _factor(self, nodo):
        if nodo is None:
            return 0
        return altura(nodo.izq) - altura(nodo.der)

    # ── rotaciones ───────────────────────────────────────────────────────────

    def _rotar_derecha(self, y):
        x, t2 = y.izq, y.izq.der
        x.padre = y.padre
        if y.padre is None:
            self.raiz = x
        elif y.padre.izq == y:
            y.padre.izq = x
        else:
            y.padre.der = x
        x.der, y.padre = y, x
        y.izq = t2
        if t2:
            t2.padre = y
        return x

    def _rotar_izquierda(self, x):
        y, t2 = x.der, x.der.izq
        y.padre = x.padre
        if x.padre is None:
            self.raiz = y
        elif x.padre.izq == x:
            x.padre.izq = y
        else:
            x.padre.der = y
        y.izq, x.padre = x, y
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

    # ── insertar ─────────────────────────────────────────────────────────────

    def insertar(self, valor):
        if not self.raiz:
            self.raiz = Nodo(valor)
            return self.raiz
        actual = self.raiz
        while True:
            if actual.valor.p1.x == valor.p1.x:
                return actual
            elif valor.p1.x < actual.valor.p1.x:
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

    # ── buscar ───────────────────────────────────────────────────────────────

    def buscar(self, valor):
        actual = self.raiz
        while actual:
            if actual.valor == valor:
                return actual
            actual = actual.izq if valor < actual.valor else actual.der
        return None

    # ── sucesor / predecesor ─────────────────────────────────────────────────

    def sucesor(self, nodo):
        if nodo is None:
            return None
        if nodo.der:
            return menor(nodo.der)
        actual, padre = nodo, nodo.padre
        while padre and actual == padre.der:
            actual, padre = padre, padre.padre
        return padre

    def predecesor(self, nodo):
        if nodo is None:
            return None
        if nodo.izq:
            return mayor(nodo.izq)
        actual, padre = nodo, nodo.padre
        while padre and actual == padre.izq:
            actual, padre = padre, padre.padre
        return padre

    # ── eliminar ─────────────────────────────────────────────────────────────

    def eliminar(self, valor):
        nodo = self.buscar(valor)
        if nodo:
            self._eliminar_nodo(nodo)

    def _eliminar_nodo(self, nodo):
        inicio_rebalanceo = nodo.padre

        if not nodo.izq and not nodo.der:           # hoja
            if nodo == self.raiz:
                self.raiz = None
            else:
                padre = nodo.padre
                if padre.izq == nodo:
                    padre.izq = None
                else:
                    padre.der = None

        elif nodo.izq and not nodo.der:             # solo izquierdo
            self._reemplazar_con_hijo(nodo, nodo.izq)

        elif nodo.der and not nodo.izq:             # solo derecho
            self._reemplazar_con_hijo(nodo, nodo.der)

        else:                                       # dos hijos
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

    # ── recorridos ───────────────────────────────────────────────────────────

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
        return ancestros(nodo)

    def rango(self, valormin, valormax):
        return [n for n in self.inorden() if valormin <= n.valor <= valormax]

    # ── diagnóstico ──────────────────────────────────────────────────────────

    def esta_balanceado(self):
        cola = [self.raiz] if self.raiz else []
        while cola:
            nodo = cola.pop(0)
            if abs(self._factor(nodo)) > 1:
                return False
            if nodo.izq:
                cola.append(nodo.izq)
            if nodo.der:
                cola.append(nodo.der)
        return True