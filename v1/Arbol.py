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


# ── Funciones auxiliares globales ────────────────────────────────────────────

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
    """Altura del subárbol enraizado en `nodo`. Nodo None → -1."""
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


# ── Árbol AVL ────────────────────────────────────────────────────────────────

class AVL:
    def __init__(self):
        self.raiz = None

    # ── utilidades de balance ────────────────────────────────────────────────

    def _altura(self, nodo):
        return altura(nodo)

    def _factor(self, nodo):
        """Factor de balance = altura(izq) - altura(der).
        AVL válido: factor en {-1, 0, 1}."""
        if nodo is None:
            return 0
        return self._altura(nodo.izq) - self._altura(nodo.der)

    # ── rotaciones ──────────────────────────────────────────────────────────

    def _rotar_derecha(self, y):
        """Rota `y` hacia la derecha (su hijo izquierdo `x` sube)."""
        x = y.izq
        t2 = x.der          # subárbol que cambia de dueño

        # x sube al lugar de y
        x.padre = y.padre
        if y.padre is None:
            self.raiz = x
        elif y.padre.izq == y:
            y.padre.izq = x
        else:
            y.padre.der = x

        # y baja como hijo derecho de x
        x.der = y
        y.padre = x

        # t2 pasa a ser hijo izquierdo de y
        y.izq = t2
        if t2:
            t2.padre = y

        return x   # nueva raíz del subárbol

    def _rotar_izquierda(self, x):
        """Rota `x` hacia la izquierda (su hijo derecho `y` sube)."""
        y = x.der
        t2 = y.izq          # subárbol que cambia de dueño

        # y sube al lugar de x
        y.padre = x.padre
        if x.padre is None:
            self.raiz = y
        elif x.padre.izq == x:
            x.padre.izq = y
        else:
            x.padre.der = y

        # x baja como hijo izquierdo de y
        y.izq = x
        x.padre = y

        # t2 pasa a ser hijo derecho de x
        x.der = t2
        if t2:
            t2.padre = x

        return y   # nueva raíz del subárbol

    def _rebalancear(self, nodo):
        """Sube desde `nodo` hacia la raíz aplicando rotaciones donde haga falta."""
        actual = nodo
        while actual is not None:
            fb = self._factor(actual)

            # Desbalance hacia la izquierda
            if fb > 1:
                if self._factor(actual.izq) < 0:          # Caso izq-der → doble
                    self._rotar_izquierda(actual.izq)
                self._rotar_derecha(actual)

            # Desbalance hacia la derecha
            elif fb < -1:
                if self._factor(actual.der) > 0:          # Caso der-izq → doble
                    self._rotar_derecha(actual.der)
                self._rotar_izquierda(actual)

            actual = actual.padre

    # ── insertar ────────────────────────────────────────────────────────────

    def insertar(self, valor):
        if not self.raiz:
            self.raiz = Nodo(valor)
            return self.raiz

        actual = self.raiz
        while True:
            if actual.valor == valor:
                return actual          # sin duplicados
            elif valor < actual.valor:
                if not actual.izq:
                    nuevo = Nodo(valor)
                    nuevo.padre = actual
                    actual.izq = nuevo
                    self._rebalancear(actual)  # rebalancear desde el padre
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

    # ── buscar ──────────────────────────────────────────────────────────────

    def buscar(self, valor):
        """Devuelve el nodo si existe, o None."""
        actual = self.raiz
        while actual:
            if actual.valor == valor:
                return actual
            elif valor < actual.valor:
                actual = actual.izq
            else:
                actual = actual.der
        return None

    # ── eliminar ────────────────────────────────────────────────────────────

    def eliminar(self, valor):
        nodo = self.buscar(valor)
        if nodo:
            self._eliminar_nodo(nodo)

    def _eliminar_nodo(self, nodo):
        # Guardamos el punto desde donde rebalancear
        inicio_rebalanceo = nodo.padre

        # Caso 1: hoja
        if not nodo.izq and not nodo.der:
            if nodo == self.raiz:
                self.raiz = None
            else:
                padre = nodo.padre
                if padre.izq == nodo:
                    padre.izq = None
                else:
                    padre.der = None

        # Caso 2a: solo hijo izquierdo
        elif nodo.izq and not nodo.der:
            self._reemplazar_con_hijo(nodo, nodo.izq)

        # Caso 2b: solo hijo derecho
        elif nodo.der and not nodo.izq:
            self._reemplazar_con_hijo(nodo, nodo.der)

        # Caso 3: dos hijos → predecesor in-orden (mayor del subárbol izq)
        else:
            sucesor = mayor(nodo.izq)
            inicio_rebalanceo = sucesor.padre
            if inicio_rebalanceo == nodo:       # el sucesor es hijo directo
                inicio_rebalanceo = sucesor
            nodo.valor = sucesor.valor
            self._eliminar_nodo(sucesor)
            return                              # el rebalanceo lo hace la llamada recursiva

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

    # ── recorridos ──────────────────────────────────────────────────────────

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

    # ── info de balance (diagnóstico) ────────────────────────────────────────

    def esta_balanceado(self):
        """Verifica con BFS que todos los nodos tengan factor de balance en {-1,0,1}."""
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


# ── prueba rápida ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    
    arbol = AVL()

    # Caso peor de un BST normal: inserción en orden ascendente
    for v in [3, 9 ,1 ,5 ,7, 8 ,6, 4]:
        arbol.insertar(v)

    print("Inorden:", [n.valor for n in arbol.inorden()])
    print("Raíz:", arbol.raiz)
    print("Altura:", altura(arbol.raiz))      # debe ser 2 (árbol perfecto de 7 nodos)
    print("¿Balanceado?", arbol.esta_balanceado())

    arbol.eliminar(4)
    print("\nTras eliminar 4:")
    print("Inorden:", [n.valor for n in arbol.inorden()])
    print("¿Balanceado?", arbol.esta_balanceado())