import os
import math
import heapq
from glob import glob
from dataclasses import dataclass, field
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
from collections import defaultdict

# ==============================================================================
# 1. ESTRUCTURAS GEOMÉTRICAS BÁSICAS
# ==============================================================================
class Punto:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        
    def distancia(self, otro):
        return math.hypot(self.x - otro.x, self.y - otro.y)
        
    def __eq__(self, otro):
        if not isinstance(otro, Punto): return False
        return abs(self.x - otro.x) < 1e-9 and abs(self.y - otro.y) < 1e-9
        
    def __hash__(self):
        return hash((round(self.x, 9), round(self.y, 9)))
        
    def __repr__(self):
        return f"Punto({self.x:.2f}, {self.y:.2f})"

def _llave(p: Punto):
    """Genera una llave con tolerancia a errores de punto flotante para agrupar eventos."""
    return (round(p.x, 9), round(p.y, 9))

# ==============================================================================
# 2. CLASES DE LÍNEA DE BARRIDO (Bentley-Ottmann)
# ==============================================================================
@dataclass(frozen=True)
class Segmento:
    name: str
    p1: Punto
    p2: Punto
    boundingBox: tuple = field(init=False)
    long: float = field(init=False)
    ang: float = field(init=False)

    def __repr__(self):
        return f"Segmento {self.name}"

    def __post_init__(self):
        object.__setattr__(self, "boundingBox", (
            min(self.p1.x, self.p2.x), max(self.p1.x, self.p2.x),
            min(self.p1.y, self.p2.y), max(self.p1.y, self.p2.y)
        ))
        longitud = self.p1.distancia(self.p2)
        object.__setattr__(self, "long", longitud)
        if longitud == 0:
            object.__setattr__(self, "ang", 0.0)
        else:
            valor = max(-1.0, min(1.0, abs((self.p1.x - self.p2.x) / longitud)))
            object.__setattr__(self, "ang", math.acos(valor))

    def organAlto(self) -> "Segmento":
        if self.p1.y > self.p2.y:
            return self
        elif abs(self.p1.y - self.p2.y) < 1e-9:
            if self.p1.x < self.p2.x: return self
            else: return Segmento(self.name, self.p2, self.p1)
        else:
            return Segmento(self.name, self.p2, self.p1)

    def yInBound(self, altura: float) -> bool:
        return self.boundingBox[2] - 1e-9 <= altura <= self.boundingBox[3] + 1e-9

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

class Nodo:
    def __init__(self, valor):
        self.valor = valor
        self.padre = None
        self.izq = None
        self.der = None

def altura(nodo):
    if nodo is None: return -1
    return 1 + max(altura(nodo.izq), altura(nodo.der))

def mayor(nodo):
    while nodo.der: nodo = nodo.der
    return nodo

def x_at_y(seg: Segmento, y: float) -> float:
    if abs(seg.p1.y - seg.p2.y) < 1e-10: return min(seg.p1.x, seg.p2.x)
    t = (y - seg.p1.y) / (seg.p2.y - seg.p1.y)
    return seg.p1.x + t * (seg.p2.x - seg.p1.x)

class AVL:
    def __init__(self):
        self.raiz = None

    def _factor(self, nodo):
        if nodo is None: return 0
        return altura(nodo.izq) - altura(nodo.der)

    def _rotar_derecha(self, y):
        x = y.izq
        t2 = x.der
        x.padre = y.padre
        if y.padre is None: self.raiz = x
        elif y.padre.izq == y: y.padre.izq = x
        else: y.padre.der = x
        x.der = y
        y.padre = x
        y.izq = t2
        if t2: t2.padre = y
        return x

    def _rotar_izquierda(self, x):
        y = x.der
        t2 = y.izq
        y.padre = x.padre
        if x.padre is None: self.raiz = y
        elif x.padre.izq == x: x.padre.izq = y
        else: x.padre.der = y
        y.izq = x
        x.padre = y
        x.der = t2
        if t2: t2.padre = x
        return y

    def _rebalancear(self, nodo):
        actual = nodo
        while actual is not None:
            fb = self._factor(actual)
            if fb > 1:
                if self._factor(actual.izq) < 0: self._rotar_izquierda(actual.izq)
                self._rotar_derecha(actual)
            elif fb < -1:
                if self._factor(actual.der) > 0: self._rotar_derecha(actual.der)
                self._rotar_izquierda(actual)
            actual = actual.padre

    @staticmethod
    def _clave(seg):
        return (round(x_at_y(seg, y_sweep), 9), seg.ang)

    def insertar(self, valor):
        if not self.raiz:
            self.raiz = Nodo(valor)
            return self.raiz
        vk = self._clave(valor)
        actual = self.raiz
        while True:
            ak = self._clave(actual.valor)
            if actual.valor is valor: return actual
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

    def buscarContenedores(self, p: Punto) -> set:
        resultado = set()
        for nodo in self.inorden():
            seg = nodo.valor
            if seg.p1 == p or seg.p2 == p: continue
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
            if ax < px - 1e-9: izq = n
            elif ax > px + 1e-9:
                if der is None: der = n
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
            if nodo.valor is seg: return nodo
        return None

    def sucesor(self, nodo):
        if nodo is None: return None
        nodos = self.inorden()
        for i, n in enumerate(nodos):
            if n is nodo:
                return nodos[i + 1] if i + 1 < len(nodos) else None
        return None

    def predecesor(self, nodo):
        if nodo is None: return None
        nodos = self.inorden()
        for i, n in enumerate(nodos):
            if n is nodo:
                return nodos[i - 1] if i > 0 else None
        return None

    def eliminar(self, valor):
        nodo = self.buscarPorIdentidad(valor)
        if nodo: self._eliminar_nodo(nodo)

    def _eliminar_nodo(self, nodo):
        inicio_rebalanceo = nodo.padre
        if not nodo.izq and not nodo.der:
            if nodo == self.raiz: self.raiz = None
            else:
                padre = nodo.padre
                if padre.izq == nodo: padre.izq = None
                else: padre.der = None
        elif nodo.izq and not nodo.der: self._reemplazar_con_hijo(nodo, nodo.izq)
        elif nodo.der and not nodo.izq: self._reemplazar_con_hijo(nodo, nodo.der)
        else:
            suc = mayor(nodo.izq)
            inicio_rebalanceo = suc.padre
            if inicio_rebalanceo == nodo: inicio_rebalanceo = suc
            nodo.valor = suc.valor
            self._eliminar_nodo(suc)
            return
        if inicio_rebalanceo: self._rebalancear(inicio_rebalanceo)

    def _reemplazar_con_hijo(self, nodo, hijo):
        hijo.padre = nodo.padre
        if nodo.padre is None: self.raiz = hijo
        elif nodo.padre.izq == nodo: nodo.padre.izq = hijo
        else: nodo.padre.der = hijo

    def _inorden_estructural(self, nodo=None):
        if nodo is None: nodo = self.raiz
        l = []
        if nodo is None: return l
        if nodo.izq: l.extend(self._inorden_estructural(nodo.izq))
        l.append(nodo)
        if nodo.der: l.extend(self._inorden_estructural(nodo.der))
        return l

    def inorden(self, nodo=None):
        nodos = self._inorden_estructural(nodo)
        nodos.sort(key=lambda n: (round(x_at_y(n.valor, y_sweep), 9), n.valor.ang))
        return nodos

def segALinea(segmento):
    x1, x2 = segmento.p1.x, segmento.p2.x
    y1, y2 = segmento.p1.y, segmento.p2.y
    return Linea(y1 - y2, x2 - x1, x1 * y2 - y1 * x2)

def interseccionLineas(linea1, linea2):
    detGen = linea1.A * linea2.B - linea1.B * linea2.A
    if detGen == 0: return None
    detX = (-linea1.C) * linea2.B - linea1.B * (-linea2.C)
    detY = linea1.A * (-linea2.C) - (-linea1.C) * linea2.A
    return Punto(detX / detGen, detY / detGen)

def interseccionSeg(segmento1, segmento2) -> list:
    lineaSeg1 = segALinea(segmento1)
    lineaSeg2 = segALinea(segmento2)
    detGen = lineaSeg1.A * lineaSeg2.B - lineaSeg1.B * lineaSeg2.A

    if abs(detGen) < 1e-10:
        dx1 = abs(segmento1.p2.x - segmento1.p1.x)
        dy1 = abs(segmento1.p2.y - segmento1.p1.y)

        if dx1 >= dy1:
            l1, r1 = min(segmento1.p1.x, segmento1.p2.x), max(segmento1.p1.x, segmento1.p2.x)
            l2, r2 = min(segmento2.p1.x, segmento2.p2.x), max(segmento2.p1.x, segmento2.p2.x)
            ol, or_ = max(l1, l2), min(r1, r2)
            if ol > or_ + 1e-9: return []
            def x_a_punto(x_val):
                if dx1 < 1e-10: return Punto(x_val, segmento1.p1.y)
                t = (x_val - segmento1.p1.x) / (segmento1.p2.x - segmento1.p1.x)
                return Punto(x_val, segmento1.p1.y + t * (segmento1.p2.y - segmento1.p1.y))
            if abs(ol - or_) < 1e-9: return [x_a_punto(ol)]
            return [x_a_punto(ol), x_a_punto(or_)]
        else:
            l1, r1 = min(segmento1.p1.y, segmento1.p2.y), max(segmento1.p1.y, segmento1.p2.y)
            l2, r2 = min(segmento2.p1.y, segmento2.p2.y), max(segmento2.p1.y, segmento2.p2.y)
            ol, or_ = max(l1, l2), min(r1, r2)
            if ol > or_ + 1e-9: return []
            def y_a_punto(y_val):
                if dy1 < 1e-10: return Punto(segmento1.p1.x, y_val)
                t = (y_val - segmento1.p1.y) / (segmento1.p2.y - segmento1.p1.y)
                return Punto(segmento1.p1.x + t * (segmento1.p2.x - segmento1.p1.x), y_val)
            if abs(ol - or_) < 1e-9: return [y_a_punto(ol)]
            return [y_a_punto(ol), y_a_punto(or_)]

    inter = interseccionLineas(lineaSeg1, lineaSeg2)
    if inter is None: return []
    
    eps = 1e-9
    if (segmento1.boundingBox[0] - eps <= inter.x <= segmento1.boundingBox[1] + eps and
        segmento1.boundingBox[2] - eps <= inter.y <= segmento1.boundingBox[3] + eps and
        segmento2.boundingBox[0] - eps <= inter.x <= segmento2.boundingBox[1] + eps and
        segmento2.boundingBox[2] - eps <= inter.y <= segmento2.boundingBox[3] + eps):
            return [inter]
    return []

y_sweep = 0.0
dictPuntos = {}
T = None
R = set()
Q = []
_contador_ev = 0

def procesarEvento(p):
    global y_sweep, dictPuntos, T, R, Q
    y_sweep = p.p.y
    llave_p = _llave(p.p)
    event_data = dictPuntos.get(llave_p, p)

    U = event_data.eventoU
    L = event_data.eventoL
    C = T.buscarContenedores(p.p)
    unionULC = U | L | C
    unionUC  = U | C

    if len(unionULC) > 1: R.add((p.p, frozenset(unionULC)))

    for seg in L | C: T.eliminar(seg)
    y_sweep = p.p.y - 1e-9
    for seg in U | C: T.insertar(seg)

    for seg_h in U:
        if abs(seg_h.p1.y - seg_h.p2.y) < 1e-9:
            x_izq, x_der = min(seg_h.p1.x, seg_h.p2.x), max(seg_h.p1.x, seg_h.p2.x)
            for nodo_v in T.buscarEnRangoX(x_izq, x_der):
                seg_v = nodo_v.valor
                for inter in interseccionSeg(seg_h, seg_v):
                    R.add((inter, frozenset([seg_h, seg_v])))

    if not unionUC:
        sL, sR = T.buscarVecinosDeX(p.p.x)
        encuentraEvento(sL, sR, p.p)
    else:
        nodos_uc = [T.buscarPorIdentidad(s) for s in unionUC if abs(s.p1.y - s.p2.y) > 1e-9]
        nodos_uc = [n for n in nodos_uc if n is not None]

        if nodos_uc:
            sPrim = min(nodos_uc, key=lambda n: x_at_y(n.valor, y_sweep))
            sL    = T.predecesor(sPrim)
            encuentraEvento(sL, sPrim, p.p)

            sBiPrim = max(nodos_uc, key=lambda n: x_at_y(n.valor, y_sweep))
            sR      = T.sucesor(sBiPrim)
            encuentraEvento(sBiPrim, sR, p.p)

def encuentraEvento(sL, sR, p: Punto):
    global _contador_ev, dictPuntos, Q
    if sL is None or sR is None: return
    for inter in interseccionSeg(sL.valor, sR.valor):
        llave = _llave(inter)
        debajo = inter.y < p.y - 1e-9
        mismaAltura_derecha = abs(inter.y - p.y) < 1e-9 and inter.x > p.x + 1e-9

        if debajo or mismaAltura_derecha:
            if llave in dictPuntos:
                ev = dictPuntos[llave]
                ev.eventoC.add(sL.valor)
                ev.eventoC.add(sR.valor)
            else:
                _contador_ev += 1
                ev = evento(inter, eventoL=set(), eventoC={sL.valor, sR.valor}, eventoU=set())
                dictPuntos[llave] = ev
                heapq.heappush(Q, ((-inter.y, inter.x, _contador_ev), ev))

def ejecutar_algoritmo_bentley_ottmann(lista_segmentos):
    global y_sweep, dictPuntos, T, R, Q, _contador_ev
    y_sweep = 0.0
    dictPuntos = {}
    T = AVL()
    R = set()
    Q = []
    _contador_ev = 0

    for seg in lista_segmentos:
        s = seg.organAlto()
        
        k1 = _llave(s.p1)
        if k1 not in dictPuntos:
            _contador_ev += 1
            ev = evento(s.p1, set(), set(), set())
            dictPuntos[k1] = ev
            heapq.heappush(Q, ((-s.p1.y, s.p1.x, _contador_ev), ev))
        dictPuntos[k1].eventoU.add(s)

        k2 = _llave(s.p2)
        if k2 not in dictPuntos:
            _contador_ev += 1
            ev = evento(s.p2, set(), set(), set())
            dictPuntos[k2] = ev
            heapq.heappush(Q, ((-s.p2.y, s.p2.x, _contador_ev), ev))
        dictPuntos[k2].eventoL.add(s)

    while Q:
        _, ev_actual = heapq.heappop(Q)
        procesarEvento(ev_actual)
        
    return R

# ==============================================================================
# 3. ESTRUCTURAS DLEC Y LÓGICAS COMPUESTAS (De Berg)
# ==============================================================================

class Vertice:
    def __init__(self, nombre, x, y):
        self.nombre = nombre
        self.x = float(x)
        self.y = float(y)
        self.incidente = None

class Arista:
    def __init__(self, nombre):
        self.nombre = nombre
        self.origen = None
        self.pareja = None
        self.cara = None
        self.sigue = None
        self.antes = None

class Cara:
    def __init__(self, nombre):
        self.nombre = nombre
        self.interno = []
        self.externo = None
        self.activa = False

class DLEC:
    def __init__(self):
        self.vertices = {}
        self.aristas = {}
        self.caras = {}

    def _renombrar(self, nombre, capa):
        if nombre == "None" or nombre is None or nombre.strip() == "": return None
        return f"{nombre}_{capa}"

    def leer_directorio(self, directorio):
        archivos_vertices = glob(os.path.join(directorio, "*.vertices"))
        capas = [os.path.basename(f).split('.')[0] for f in archivos_vertices]
        for capa in capas:
            ruta_base = os.path.join(directorio, capa)
            self._procesar_capa(capa, f"{ruta_base}.vertices", f"{ruta_base}.aristas", f"{ruta_base}.caras", f"{ruta_base}.activos")
        self._vincular_entidades()

    def _procesar_capa(self, capa, arch_vert, arch_aris, arch_caras, arch_activos):
        def _limpiar(lineas):
            return [l.strip() for l in lineas if l.strip() and not l.strip().startswith('#') and "Nombre" not in l and "Caras Activas" not in l]

        if os.path.exists(arch_vert):
            with open(arch_vert, 'r', encoding='utf-8') as f:
                for p in [l.split() for l in _limpiar(f.readlines()) if len(l.split()) >= 4]:
                    n = self._renombrar(p[0], capa)
                    v = Vertice(n, p[1], p[2])
                    v.incidente = self._renombrar(p[3], capa)
                    self.vertices[n] = v

        if os.path.exists(arch_caras):
            with open(arch_caras, 'r', encoding='utf-8') as f:
                for p in [l.split() for l in _limpiar(f.readlines()) if len(l.split()) >= 3]:
                    n = self._renombrar(p[0], capa)
                    c = Cara(n)
                    if p[1] != "None": c.interno = [self._renombrar(a.strip(), capa) for a in p[1].replace('[', '').replace(']', '').split(',')]
                    c.externo = self._renombrar(p[2], capa)
                    self.caras[n] = c

        if os.path.exists(arch_aris):
            with open(arch_aris, 'r', encoding='utf-8') as f:
                for p in [l.split() for l in _limpiar(f.readlines()) if len(l.split()) >= 6]:
                    n = self._renombrar(p[0], capa)
                    a = Arista(n)
                    a.origen, a.pareja, a.cara = self._renombrar(p[1], capa), self._renombrar(p[2], capa), self._renombrar(p[3], capa)
                    a.sigue, a.antes = self._renombrar(p[4], capa), self._renombrar(p[5], capa)
                    self.aristas[n] = a

        if os.path.exists(arch_activos):
            with open(arch_activos, 'r', encoding='utf-8') as f:
                for l in _limpiar(f.readlines()):
                    n = self._renombrar(l.split()[0], capa)
                    if n in self.caras: self.caras[n].activa = True

    def _vincular_entidades(self):
        for v in self.vertices.values():
            if v.incidente: v.incidente = self.aristas.get(v.incidente)
        for c in self.caras.values():
            if c.externo: c.externo = self.aristas.get(c.externo)
            c.interno = [self.aristas.get(n) for n in c.interno if n in self.aristas]
        for a in self.aristas.values():
            if a.origen: a.origen = self.vertices.get(a.origen)
            if a.pareja: a.pareja = self.aristas.get(a.pareja)
            if a.cara:   a.cara = self.caras.get(a.cara)
            if a.sigue:  a.sigue = self.aristas.get(a.sigue)
            if a.antes:  a.antes = self.aristas.get(a.antes)

    # ==============================================================================
    # SUBDIVISIÓN DE ARISTAS (Primos y Primo-Primos)
    # ==============================================================================
    def subdividir_por_interseccion(self, punto_x, segmentos_involucrados):
        nombre_v_x = f"V_{punto_x.x:.3f}_{punto_x.y:.3f}"
        vertice_x = Vertice(nombre_v_x, punto_x.x, punto_x.y)
        self.vertices[nombre_v_x] = vertice_x
        
        primo_primos_creados = []
        reemplazos = {}
        
        aristas_involucradas = []
        for seg in segmentos_involucrados:
            if seg.name in self.aristas:
                aristas_involucradas.append(self.aristas[seg.name])
            else:
                continue 

        if len(aristas_involucradas) < 2:
            return None 

        for e in aristas_involucradas:
            t = e.pareja
            
            primo_e = Arista(f"{e.nombre}_P_{nombre_v_x}")
            pp_e    = Arista(f"{e.nombre}_PP_{nombre_v_x}")
            primo_t = Arista(f"{t.nombre}_P_{nombre_v_x}")
            pp_t    = Arista(f"{t.nombre}_PP_{nombre_v_x}")
            
            primo_e.origen = e.origen
            primo_t.origen = t.origen
            pp_e.origen    = vertice_x
            pp_t.origen    = vertice_x
            
            primo_e.pareja, pp_t.pareja = pp_t, primo_e
            primo_t.pareja, pp_e.pareja = pp_e, primo_t
            
            primo_e.cara = pp_e.cara = e.cara
            primo_t.cara = pp_t.cara = t.cara
            
            primo_primos_creados.extend([pp_e, pp_t])
            reemplazos[e] = (primo_e, pp_e)
            reemplazos[t] = (primo_t, pp_t)
            
            self.aristas[primo_e.nombre] = primo_e
            self.aristas[pp_e.nombre]    = pp_e
            self.aristas[primo_t.nombre] = primo_t
            self.aristas[pp_t.nombre]    = pp_t

        for original, (primo, pp) in reemplazos.items():
            real_antes = original.antes
            if real_antes in reemplazos:
                real_antes = reemplazos[real_antes][1] 
            primo.antes = real_antes
            if real_antes: real_antes.sigue = primo
                
            real_sigue = original.sigue
            if real_sigue in reemplazos:
                real_sigue = reemplazos[real_sigue][0] 
            pp.sigue = real_sigue
            if real_sigue: real_sigue.antes = pp

        def angulo_radial(arista_saliente):
            destino = arista_saliente.pareja.origen
            return math.atan2(destino.y - vertice_x.y, destino.x - vertice_x.x)
            
        primo_primos_creados.sort(key=angulo_radial, reverse=True)

        n = len(primo_primos_creados)
        for i in range(n):
            s_actual = primo_primos_creados[i]
            s_siguiente = primo_primos_creados[(i + 1) % n]
            p_actual = s_actual.pareja 
            p_actual.sigue = s_siguiente
            s_siguiente.antes = p_actual

        vertice_x.incidente = primo_primos_creados[0]
        
        for e in aristas_involucradas:
            t = e.pareja
            if e.nombre in self.aristas: del self.aristas[e.nombre]
            if t.nombre in self.aristas: del self.aristas[t.nombre]

        return vertice_x

    # ==============================================================================
    # RECONSTRUCCIÓN DE CARAS (Basado en De Berg Section 2.3)
    # ==============================================================================
    def reconstruir_caras(self):
        visitados = set()
        ciclos = []
        
        # 1. Extraer los ciclos cerrados formados por las aristas
        for arista in self.aristas.values():
            if arista.nombre not in visitados:
                ciclo = []
                actual = arista
                while actual and actual.nombre not in visitados:
                    visitados.add(actual.nombre)
                    ciclo.append(actual)
                    actual = actual.sigue
                    
                if ciclo:
                    ciclos.append(ciclo)
                    
        # 2. Clasificar mediante el área entre agujeros (Holes) y Bordes Externos
        ciclos_info = []
        for i, ciclo in enumerate(ciclos):
            area = 0.0
            v_min = ciclo[0].origen
            
            for ar in ciclo:
                p1 = ar.origen
                p2 = ar.sigue.origen if ar.sigue else ar.pareja.origen
                area += (p1.x * p2.y - p2.x * p1.y)
                
                # Identificamos el vértice más a la izquierda (leftmost)
                if p1.x < v_min.x - 1e-9 or (abs(p1.x - v_min.x) < 1e-9 and p1.y < v_min.y):
                    v_min = p1
                    
            is_ccw = area > 0 # Área positiva = CCW = Borde Exterior
            ciclos_info.append({
                'id': i,
                'ciclo': ciclo,
                'is_ccw': is_ccw,
                'v_min': v_min,
                'edge_left': None
            })
            
        # 3. Ray-Casting para conectar Agujeros con sus Caras contenedoras
        for info in ciclos_info:
            if not info['is_ccw']:
                v_min = info['v_min']
                closest_x = -float('inf')
                closest_edge = None
                
                for ar in self.aristas.values():
                    if not ar.sigue: continue
                    p1 = ar.origen
                    p2 = ar.sigue.origen
                    
                    # De Berg señala ubicar la arista inmediata a la izquierda del agujero
                    # Geométricamente esto exige encontrar un borde apuntando "hacia abajo"
                    if p1.y <= p2.y:
                        continue
                        
                    # Comprobación de intersección con el rayo Y horizontal a la izquierda
                    if p2.y <= v_min.y < p1.y:
                        x_int = p2.x + (v_min.y - p2.y) / (p1.y - p2.y) * (p1.x - p2.x)
                        
                        if x_int < v_min.x - 1e-9:
                            if x_int > closest_x:
                                closest_x = x_int
                                closest_edge = ar
                                
                info['edge_left'] = closest_edge

        # 4. Construir Grafo de Componentes y Union-Find
        parent = {i: i for i in range(len(ciclos_info))}
        parent[-1] = -1 # Representa a la Cara Ilimitada (Unbounded Face)
        
        def find(i):
            if parent[i] == i: return i
            parent[i] = find(parent[i])
            return parent[i]
            
        def union(i, j):
            root_i = find(i)
            root_j = find(j)
            if root_i != root_j:
                parent[root_i] = root_j

        edge_to_cycle = {}
        for info in ciclos_info:
            for ar in info['ciclo']:
                edge_to_cycle[ar.nombre] = info['id']

        for info in ciclos_info:
            if not info['is_ccw']:
                e_left = info['edge_left']
                if e_left is None:
                    union(info['id'], -1)
                else:
                    c_left_id = edge_to_cycle[e_left.nombre]
                    union(info['id'], c_left_id)

        # 5. Agrupar y materializar las Caras
        componentes = defaultdict(list)
        for info in ciclos_info:
            componentes[find(info['id'])].append(info)
            
        self.caras = {}
        cara_id = 1
        
        for comp_id, ciclos_comp in componentes.items():
            if comp_id == -1:
                nombre_cara = "CARA_UNBOUNDED"
            else:
                nombre_cara = f"CARA_RECONSTRUIDA_{cara_id}"
                cara_id += 1
                
            nueva_cara = Cara(nombre_cara)
            
            for info in ciclos_comp:
                if info['is_ccw']:
                    nueva_cara.externo = info['ciclo'][0]
                else:
                    nueva_cara.interno.append(info['ciclo'][0])
                    
            self.caras[nombre_cara] = nueva_cara
            
            # Reasignar el puntero interno de las aristas a su nueva cara
            for info in ciclos_comp:
                for ar in info['ciclo']:
                    ar.cara = nueva_cara

    # ==============================================================================
    # MOTOR DE EJECUCIÓN MAESTRO
    # ==============================================================================
    def ejecutar_y_dibujar(self):
        segmentos_para_analisis = []
        aristas_procesadas = set()
        
        for a in self.aristas.values():
            if a.origen and a.pareja and a.pareja.origen:
                identificador = tuple(sorted([a.origen.nombre, a.pareja.origen.nombre]))
                if identificador not in aristas_procesadas:
                    v1, v2 = a.origen, a.pareja.origen
                    segmentos_para_analisis.append(Segmento(a.nombre, Punto(v1.x, v1.y), Punto(v2.x, v2.y)))
                    aristas_procesadas.add(identificador)

        print(f"Ejecutando Bentley-Ottmann sobre {len(segmentos_para_analisis)} segmentos originales...")
        intersecciones = ejecutar_algoritmo_bentley_ottmann(segmentos_para_analisis)
        print(f"¡Análisis completado! Se encontraron {len(intersecciones)} cruces matemáticos.")

        puntos_marcados = []
        for inter_pto, conjuntos_segmentos in intersecciones:
            nuevo_vertice = self.subdividir_por_interseccion(inter_pto, conjuntos_segmentos)
            if nuevo_vertice:
                puntos_marcados.append(inter_pto)
                
        print(f"Subdivisión aplicada. Reconstruyendo caras separadas por las divisiones...")
        self.reconstruir_caras()
        print(f"¡DCEL Actualizado! Total de Caras detectadas: {len(self.caras)}")

        plt.figure(figsize=(10, 8))
        capas = list(set([v.nombre.split('_')[-1] for v in self.vertices.values() if '_' in v.nombre]))
        if not capas: capas = ['default']
        
        colores_mapa = plt.colormaps.get_cmap('tab10')
        color_por_capa = {capa: colores_mapa(i / max(1, len(capas)-1)) for i, capa in enumerate(capas)}

        aristas_dibujadas = set()
        for a in self.aristas.values():
            if a.origen and a.pareja and a.pareja.origen:
                identificador = tuple(sorted([a.origen.nombre, a.pareja.origen.nombre]))
                if identificador not in aristas_dibujadas:
                    v1, v2 = a.origen, a.pareja.origen
                    capa = a.nombre.split('_')[-1] if '_' in a.nombre else 'default'
                    color = color_por_capa.get(capa, 'black')
                    
                    plt.plot([v1.x, v2.x], [v1.y, v2.y], color=color, linestyle='-', linewidth=2)
                    aristas_dibujadas.add(identificador)

        for v in self.vertices.values():
            capa = v.nombre.split('_')[-1] if '_' in v.nombre else 'default'
            color = color_por_capa.get(capa, 'black')
            plt.plot(v.x, v.y, marker='o', color=color, markersize=5)
            if "V_" not in v.nombre:
                plt.text(v.x + 0.1, v.y + 0.1, v.nombre.split('_')[0], fontsize=8, weight='bold')

        for pt in puntos_marcados:
            plt.plot(pt.x, pt.y, marker='X', color='red', markersize=12, markeredgecolor='black')

        plt.title("Grafo DCEL (Post-Subdivisión y Rearmado de Caras)")
        plt.xlabel("X")
        plt.ylabel("Y")
        plt.axis('equal')
        plt.grid(True, linestyle=':')
        
        handles = [mlines.Line2D([0], [0], marker='o', color='w', markerfacecolor=color_por_capa.get(c, 'black'), markersize=8, label=c) for c in capas]
        plt.legend(handles=handles, title="Capas")
        plt.show()

    # ==============================================================================
    # RENOMBRADO FINAL (LEGIBILIDAD)
    # ==============================================================================
    def simplificar_nombres(self):
        """
        Limpia los nombres complejos generados por las intersecciones y multicapas,
        sustituyéndolos por secuencias simples (v1, a1, a1Par, c1) antes de exportar.
        """
        # 1. Renombrar Vértices
        nuevos_vertices = {}
        for i, v in enumerate(self.vertices.values(), 1):
            v.nombre = f"v{i}"
            nuevos_vertices[v.nombre] = v
        self.vertices = nuevos_vertices

        # 2. Renombrar Caras
        nuevas_caras = {}
        cara_id = 1
        for c in self.caras.values():
            if "UNBOUNDED" in c.nombre:
                c.nombre = "c_externa" # Opcional: Nombre para el vacío exterior
            else:
                c.nombre = f"c{cara_id}"
                cara_id += 1
            nuevas_caras[c.nombre] = c
        self.caras = nuevas_caras

        # 3. Renombrar Aristas (respetando las parejas de Half-Edges)
        nuevas_aristas = {}
        aristas_procesadas = set() # Usamos las referencias de memoria
        arista_id = 1
        
        for a in self.aristas.values():
            if a in aristas_procesadas:
                continue
                
            nuevo_nombre_a = f"a{arista_id}"
            nuevo_nombre_pareja = f"a{arista_id}Par"
            
            # Renombramos la arista base
            a.nombre = nuevo_nombre_a
            nuevas_aristas[nuevo_nombre_a] = a
            aristas_procesadas.add(a)
            
            # Renombramos a su gemela (Twin)
            if a.pareja:
                a.pareja.nombre = nuevo_nombre_pareja
                nuevas_aristas[nuevo_nombre_pareja] = a.pareja
                aristas_procesadas.add(a.pareja)
                
            arista_id += 1
            
        self.aristas = nuevas_aristas
        print("¡Nombres simplificados correctamente (v1, a1, a1Par, c1...)!")


    # ==============================================================================
    # EXPORTACIÓN DE RESULTADOS
    # ==============================================================================
    def exportar(self, directorio_salida, prefijo="resultado"):
        """
        Exporta el estado actual del DLEC a los 4 archivos correspondientes,
        manteniendo el formato y alineación original.
        """
        import os
        if not os.path.exists(directorio_salida):
            os.makedirs(directorio_salida)

        # Función auxiliar para extraer el nombre seguro de un objeto (o "None")
        def obtener_nombre(obj):
            if obj is None:
                return "None"
            if isinstance(obj, str):
                return obj
            return getattr(obj, 'nombre', "None")

        # -------------------------------------------------------------
        # 1. Exportar Vértices (.vertices)
        # -------------------------------------------------------------
        ruta_vert = os.path.join(directorio_salida, f"{prefijo}.vertices")
        with open(ruta_vert, 'w', encoding='utf-8') as f:
            f.write("Archivo de vértices\n")
            f.write("#################################\n")
            f.write(f"{'Nombre':<15}{'x':<10}{'y':<10}{'Incidente':<15}\n")
            f.write("#################################\n")
            for v in self.vertices.values():
                # Formatear números para evitar decimales innecesarios (ej: 5.0 -> 5)
                x_str = f"{v.x:g}" if v.x == int(v.x) else f"{v.x:.3f}"
                y_str = f"{v.y:g}" if v.y == int(v.y) else f"{v.y:.3f}"
                incidente = obtener_nombre(v.incidente)
                
                f.write(f"{v.nombre:<15}{x_str:<10}{y_str:<10}{incidente:<15}\n")

        # -------------------------------------------------------------
        # 2. Exportar Aristas (.aristas)
        # -------------------------------------------------------------
        ruta_aris = os.path.join(directorio_salida, f"{prefijo}.aristas")
        with open(ruta_aris, 'w', encoding='utf-8') as f:
            f.write("Archivo de aristas\n")
            f.write("#########################################################################\n")
            f.write(f"{'Nombre':<25}{'Origen':<20}{'Pareja':<25}{'Cara':<20}{'Sigue':<25}{'Antes':<25}\n")
            f.write("#########################################################################\n")
            for a in self.aristas.values():
                origen = obtener_nombre(a.origen)
                pareja = obtener_nombre(a.pareja)
                cara   = obtener_nombre(a.cara)
                sigue  = obtener_nombre(a.sigue)
                antes  = obtener_nombre(a.antes)
                
                f.write(f"{a.nombre:<25}{origen:<20}{pareja:<25}{cara:<20}{sigue:<25}{antes:<25}\n")

        # -------------------------------------------------------------
        # 3. Exportar Caras (.caras) y recolectar Activos
        # -------------------------------------------------------------
        ruta_caras = os.path.join(directorio_salida, f"{prefijo}.caras")
        caras_activas = []
        
        with open(ruta_caras, 'w', encoding='utf-8') as f:
            f.write("Archivo de caras\n")
            f.write("#######################################################\n")
            f.write(f"{'Nombre':<25}{'Interno':<35}{'Externo':<20}\n")
            f.write("#######################################################\n")
            for c in self.caras.values():
                if c.activa:
                    caras_activas.append(c.nombre)
                
                # Procesar lista interna [a1,a2,...]
                if not c.interno:
                    interno_str = "None"
                else:
                    nombres_int = [obtener_nombre(ari) for ari in c.interno]
                    interno_str = f"[{','.join(nombres_int)}]"
                
                externo = obtener_nombre(c.externo)
                f.write(f"{c.nombre:<25}{interno_str:<35}{externo:<20}\n")

        # -------------------------------------------------------------
        # 4. Exportar Activos (.activos)
        # -------------------------------------------------------------
        ruta_activos = os.path.join(directorio_salida, f"{prefijo}.activos")
        with open(ruta_activos, 'w', encoding='utf-8') as f:
            f.write("Archivo de activos\n")
            f.write("#######################\n")
            f.write("Caras Activas\n")
            f.write("#######################\n")
            # Ordenamos alfabéticamente para mayor claridad
            for nombre_cara in sorted(caras_activas):
                f.write(f"{nombre_cara}\n")

        print(f"==================================================")
        print(f"Exportación completada exitosamente.")
        print(f"Directorio: {os.path.abspath(directorio_salida)}")
        print(f"Capa generada: {prefijo}.*")
        print(f"==================================================")
    
    # ==============================================================================
    # INTERFAZ INTERACTIVA CON PYGAME
    # ==============================================================================
    def interfaz_pygame(self, directorio_salida="./resultados", prefijo="resultado_final"):
        """
        Abre una ventana interactiva. Clickea las caras para activar/desactivar.
        Al cerrar la ventana, exporta automáticamente los resultados actualizados.
        """
        try:
            import pygame
        except ImportError:
            print("Error: Pygame no está instalado. Instálalo con 'pip install pygame'")
            return

        pygame.init()
        WIDTH, HEIGHT = 800, 600
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Visualizador DLEC Interactivo (Clickea las caras)")

        # Calcular límites (Bounding Box) de todos los vértices para el auto-escalado
        if not self.vertices:
            print("No hay vértices para dibujar.")
            return

        min_x = min(v.x for v in self.vertices.values())
        max_x = max(v.x for v in self.vertices.values())
        min_y = min(v.y for v in self.vertices.values())
        max_y = max(v.y for v in self.vertices.values())

        rango_x = (max_x - min_x) if (max_x - min_x) != 0 else 1
        rango_y = (max_y - min_y) if (max_y - min_y) != 0 else 1

        margen = 50
        escala_x = (WIDTH - 2 * margen) / rango_x
        escala_y = (HEIGHT - 2 * margen) / rango_y
        escala = min(escala_x, escala_y)

        # Funciones de transformación Espacio Matemático <-> Pantalla Pygame
        def a_pantalla(x, y):
            sx = margen + (x - min_x) * escala
            sy = HEIGHT - (margen + (y - min_y) * escala) # Invertimos eje Y
            return int(sx), int(sy)

        def a_mundo(sx, sy):
            x = (sx - margen) / escala + min_x
            y = (HEIGHT - sy - margen) / escala + min_y
            return Punto(x, y)

        # Algoritmo de punto en polígono (Ray Casting)
        def punto_en_poligono(pt, vertices_poly):
            if not pt or not vertices_poly: return False
            x, y = pt.x, pt.y
            adentro = False
            n = len(vertices_poly)
            for i in range(n):
                j = (i + 1) % n
                xi, yi = vertices_poly[i].x, vertices_poly[i].y
                xj, yj = vertices_poly[j].x, vertices_poly[j].y
                
                intersecta = ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-9) + xi)
                if intersecta:
                    adentro = not adentro
            return adentro

        # Función para extraer los vértices de una frontera (siguiendo el 'sigue')
        def extraer_poligono(arista_inicio):
            poly = []
            actual = arista_inicio
            if not actual: return poly
            while True:
                poly.append(actual.origen)
                actual = actual.sigue
                if actual == arista_inicio or not actual:
                    break
            return poly

        # Bucle principal
        corriendo = True
        font = pygame.font.SysFont(None, 24)

        while corriendo:
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    corriendo = False
                    
                elif evento.type == pygame.MOUSEBUTTONDOWN:
                    if evento.button == 1: # Clic Izquierdo
                        pt_clic = a_mundo(evento.pos[0], evento.pos[1])
                        
                        # Buscar qué cara fue clickeada
                        for cara in self.caras.values():
                            if "UNBOUNDED" in cara.nombre: continue
                            if not cara.externo: continue
                            
                            frontera_externa = extraer_poligono(cara.externo)
                            
                            # Si el clic está dentro del polígono exterior de la cara
                            if punto_en_poligono(pt_clic, frontera_externa):
                                
                                # Verificar que no haya hecho clic dentro de un agujero de esta misma cara
                                en_agujero = False
                                for arista_interna in cara.interno:
                                    frontera_interna = extraer_poligono(arista_interna)
                                    if punto_en_poligono(pt_clic, frontera_interna):
                                        en_agujero = True
                                        break
                                        
                                if not en_agujero:
                                    # Alternar el estado Activo/Inactivo
                                    cara.activa = not cara.activa
                                    break # Detener la búsqueda si ya encontramos la cara

            # DIBUJADO DE LA ESCENA
            screen.fill((250, 250, 250)) # Fondo casi blanco
            
            # 1. Dibujar Caras Activas
            for cara in self.caras.values():
                if cara.activa and cara.externo:
                    frontera = extraer_poligono(cara.externo)
                    pts_pantalla = [a_pantalla(v.x, v.y) for v in frontera]
                    
                    if len(pts_pantalla) >= 3:
                        # Rellenar cara (Ej. color verde translúcido)
                        pygame.draw.polygon(screen, (100, 200, 100), pts_pantalla)
                        
                        # Restar visualmente los agujeros rellenándolos con el color de fondo
                        for ar_int in cara.interno:
                            agujero = extraer_poligono(ar_int)
                            pts_agujero = [a_pantalla(v.x, v.y) for v in agujero]
                            if len(pts_agujero) >= 3:
                                pygame.draw.polygon(screen, (250, 250, 250), pts_agujero)

            # 2. Dibujar Aristas
            for a in self.aristas.values():
                if a.origen and a.pareja and a.pareja.origen:
                    p1 = a_pantalla(a.origen.x, a.origen.y)
                    p2 = a_pantalla(a.pareja.origen.x, a.pareja.origen.y)
                    pygame.draw.line(screen, (50, 50, 50), p1, p2, 2)

            # 3. Dibujar Vértices
            for v in self.vertices.values():
                p = a_pantalla(v.x, v.y)
                pygame.draw.circle(screen, (200, 50, 50), p, 4)

            # 4. Texto de ayuda
            instrucciones = font.render("Clic en una cara para Activada (Verde) / Desactivada (Gris)", True, (0,0,0))
            screen.blit(instrucciones, (10, 10))

            pygame.display.flip()

        pygame.quit()
        
        # Una vez cerrada la ventana, exportar todo el DCEL con sus nuevos estados
        print("Guardando estado final tras interacción...")
        self.exportar(directorio_salida, prefijo)

# ==========================================
# Pruebas y Flujo Completo:
# ==========================================
if __name__ == "__main__":
    # Instanciamos la clase principal
    mi_dlec = DLEC()
    
    # 1. Leer archivos base
    mi_dlec.leer_directorio("./datos") 
    
    # 2. Ejecutar Bentley-Ottmann (Intersectar), Cortar (Primos) y Reconstruir caras
    mi_dlec.ejecutar_y_dibujar() 
    
    # 3. MODO INTERACTIVO PYGAME (Opcional, para activar/desactivar caras)
    # Lo abrimos antes para que puedas ver el Grafo, al cerrarlo exportará:
    mi_dlec.interfaz_pygame(directorio_salida="./resultados", prefijo="resultado_final")
    
    # --- O EN SU LUGAR, SI VAS A EXPORTAR MANUALMENTE: ---
    # 4. LIMPIAR NOMBRES (Esto hace la magia de legibilidad)
    # mi_dlec.simplificar_nombres()
    
    # 5. Exportar a los archivos de texto finales
    # mi_dlec.exportar(directorio_salida="./resultados", prefijo="resultado_final")

    # mi_dlec.interfaz_pygame(directorio_salida="./resultados", prefijo="resultado_final")