# =========================================================
# COMBINED SCRIPT: overlay + viewer + main
# =========================================================

import math
import random
import os
from collections import defaultdict
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, PathPatch
from matplotlib.path import Path

# =========================================================
# GEOMETRY PRIMITIVES
# =========================================================

class Punto:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __str__(self):
        return f"Punto({self.x}, {self.y})"

    def transladar(self, tx, ty):
        return Punto(self.x + tx, self.y + ty)

    def rotar(self, alpha):
        nx = self.x * math.cos(alpha) - self.y * math.sin(alpha)
        ny = self.x * math.sin(alpha) + self.y * math.cos(alpha)
        return Punto(nx, ny)

    def comparar(self, p2):
        epsilon = 1e-6
        return abs(self.x - p2.x) < epsilon and abs(self.y - p2.y) < epsilon

    def polares(self):
        r = math.sqrt(self.x**2 + self.y**2)
        theta = math.atan2(self.y, self.x)
        return r, theta

    def distancia(self, p2):
        return math.sqrt((self.x - p2.x)**2 + (self.y - p2.y)**2)


class segmento:
    def __init__(self, p1, p2):
        self.p1 = p1
        self.p2 = p2
        self.longitud = p1.distancia(p2)
        self.angulo = math.atan2(p2.y - p1.y, p2.x - p1.x)

    def __str__(self):
        return f"Segmento entre ({self.p1}, {self.p2})"

    def aLinea(self):
        a = self.p2.y - self.p1.y
        b = -(self.p2.x - self.p1.x)
        c = (self.p2.x - self.p1.x) * self.p1.y - (self.p2.y - self.p1.y) * self.p1.x
        return linea(a, b, c)

    def interseccion(self, otro):
        L1 = self.aLinea()
        L2 = otro.aLinea()
        inter = L1.interseccion(L2)
        if inter is None:
            return None
        # check bounds
        if (min(self.p1.x, self.p2.x) <= inter.x <= max(self.p1.x, self.p2.x) and
            min(self.p1.y, self.p2.y) <= inter.y <= max(self.p1.y, self.p2.y) and
            min(otro.p1.x, otro.p2.x) <= inter.x <= max(otro.p1.x, otro.p2.x) and
            min(otro.p1.y, otro.p2.y) <= inter.y <= max(otro.p1.y, otro.p2.y)):
            return inter
        return None

    def distancia(self, punto):
        L = self.aLinea()
        Ap = -L.b
        Bp = L.a
        Cp = L.b * punto.x - L.a * punto.y
        perp = linea(Ap, Bp, Cp)
        proy = L.interseccion(perp)
        if (min(self.p1.x, self.p2.x) <= proy.x <= max(self.p1.x, self.p2.x) and
            min(self.p1.y, self.p2.y) <= proy.y <= max(self.p1.y, self.p2.y)):
            return punto.distancia(proy), proy
        else:
            d1 = punto.distancia(self.p1)
            d2 = punto.distancia(self.p2)
            return (d1, self.p1) if d1 <= d2 else (d2, self.p2)


class linea:
    def __init__(self, a, b, c):
        self.a = a
        self.b = b
        self.c = c

    def __str__(self):
        return f"Linea ({self.a})x + ({self.b})y + ({self.c})"

    def interseccion(self, otra):
        det = self.a * otra.b - self.b * otra.a
        if abs(det) < 1e-12:
            return None
        x = ( (-self.c)*otra.b - self.b*(-otra.c) ) / det
        y = ( self.a*(-otra.c) - (-self.c)*otra.a ) / det
        return Punto(x, y)


class vector:
    def __init__(self, p1, p2):
        self.x = p2.x - p1.x
        self.y = p2.y - p1.y
        self.z = 0

    def producto_cruz(self, otro):
        return self.x * otro.y - self.y * otro.x


# =========================================================
# DCEL CLASSES
# =========================================================

class Vertice:
    def __init__(self, nombre, punto):
        self.nombre = nombre
        self.punto = punto
        self.incidente = None

    def __str__(self):
        inc = self.incidente.nombre if self.incidente else "None"
        return f"Vertice {self.nombre}: punto={self.punto}, incidente={inc}"


class Arista:
    def __init__(self, nombre):
        self.nombre = nombre
        self.origen = None
        self.pareja = None
        self.cara = None
        self.siguiente = None
        self.anterior = None

    def __str__(self):
        origen = self.origen.nombre if self.origen else "None"
        pareja = self.pareja.nombre if self.pareja else "None"
        cara = self.cara.nombre if self.cara else "None"
        sig = self.siguiente.nombre if self.siguiente else "None"
        ant = self.anterior.nombre if self.anterior else "None"
        return (f"Arista {self.nombre}: origen={origen}, pareja={pareja}, "
                f"cara={cara}, siguiente={sig}, anterior={ant}")


class Cara:
    def __init__(self, nombre):
        self.nombre = nombre
        self.externo = None
        self.interno = []

    def __str__(self):
        externo = self.externo.nombre if self.externo else "None"
        interno = [e.nombre for e in self.interno]
        return f"{self.nombre} {externo} {interno}"


class Layer:
    def __init__(self, nombre, direccion):
        self.nombre = nombre
        self.direccion = direccion


# =========================================================
# FILE READING (leerFiguras)
# =========================================================

def linea_valida(line):
    line = line.strip()
    return (line and not line.startswith("#") and
            not line.startswith("Archivo") and
            not line.startswith("Nombre"))


def leerArchivos(nombre_archivo, aristas, vertices, caras):
    datos_vertices = []
    datos_aristas = []
    datos_caras = []

    # vértices
    with open(nombre_archivo + ".vertices") as f:
        for line in f:
            line = line.strip()
            if not linea_valida(line):
                continue
            partes = line.split()
            if len(partes) != 4:
                continue
            nombre, x, y, incidente = partes
            pt = Punto(float(x), float(y))
            v = Vertice(nombre, pt)
            vertices[nombre] = v
            datos_vertices.append((nombre, incidente.strip()))

    # aristas
    with open(nombre_archivo + ".aristas") as f:
        for line in f:
            line = line.strip()
            if not linea_valida(line):
                continue
            partes = line.split()
            if len(partes) != 6:
                continue
            nombre, origen, pareja, cara, sig, ant = partes
            e = Arista(nombre)
            aristas[nombre] = e
            datos_aristas.append((nombre.strip(), origen.strip(), pareja.strip(),
                                  cara.strip(), sig.strip(), ant.strip()))

    # caras
    with open(nombre_archivo + ".caras") as f:
        for line in f:
            line = line.strip()
            if not linea_valida(line):
                continue
            partes = line.split()
            if len(partes) != 3:
                continue
            nombre, interno, externo = partes
            c = Cara(nombre.strip())
            caras[nombre.strip()] = c
            datos_caras.append((nombre.strip(), interno.strip(), externo.strip()))

    return datos_aristas, datos_vertices, datos_caras


def hacer_objetos(name):
    vertices = {}
    aristas = {}
    caras = {}
    dt_aristas, dt_vertices, dt_caras = leerArchivos(name, aristas, vertices, caras)

    for nombre, origen, pareja, cara, sig, ant in dt_aristas:
        e = aristas[nombre]
        e.origen = vertices.get(origen)
        e.pareja = aristas.get(pareja)
        e.cara = caras.get(cara)
        e.siguiente = aristas.get(sig)
        e.anterior = aristas.get(ant)

    for nombre, incidente in dt_vertices:
        if incidente in aristas:
            vertices[nombre].incidente = aristas[incidente]

    for nombre, interno, externo in dt_caras:
        c = caras[nombre]
        if interno != "None":
            interno = interno.replace("[", "").replace("]", "").strip()
            lista = [x.strip() for x in interno.split(",") if x.strip()]
            for a in lista:
                if a in aristas:
                    c.interno.append(aristas[a])
        if externo != "None" and externo in aristas:
            c.externo = aristas[externo]

    return vertices, aristas, caras


# =========================================================
# OVERLAY FUNCTIONS (overlay_figuras)
# =========================================================

EPS = 1e-6

class SegmentoOverlay:
    def __init__(self, nombre, p1, p2, layer):
        self.nombre = nombre
        self.p1 = p1
        self.p2 = p2
        self.layer = layer
        self.intersecciones = []

    def __str__(self):
        return f"{self.nombre}: ({self.p1.x},{self.p1.y}) -> ({self.p2.x},{self.p2.y})"


def puntos_iguales(p1, p2):
    return abs(p1.x - p2.x) < EPS and abs(p1.y - p2.y) < EPS


def punto_en_lista(p, lista):
    for q in lista:
        if puntos_iguales(p, q):
            return True
    return False


def parametro_segmento(seg, p):
    dx = seg.p2.x - seg.p1.x
    dy = seg.p2.y - seg.p1.y
    if abs(dx) > abs(dy):
        return (p.x - seg.p1.x) / dx if abs(dx) > EPS else 0
    return (p.y - seg.p1.y) / dy if abs(dy) > EPS else 0


def extraer_segmentos(aristas, layer_id):
    segmentos = []
    visitadas = set()
    for a in aristas.values():
        if a.nombre in visitadas:
            continue
        p1 = a.origen.punto
        p2 = a.pareja.origen.punto
        seg = SegmentoOverlay(a.nombre, p1, p2, layer_id)
        segmentos.append(seg)
        visitadas.add(a.nombre)
        visitadas.add(a.pareja.nombre)
    return segmentos


def orient(a, b, c):
    return (b.x - a.x)*(c.y - a.y) - (b.y - a.y)*(c.x - a.x)


def interseccion_segmentos(s1, s2):
    p = s1.p1
    p2 = s1.p2
    q = s2.p1
    q2 = s2.p2
    den = (p.x - p2.x)*(q.y - q2.y) - (p.y - p2.y)*(q.x - q2.x)
    if abs(den) < EPS:
        return None
    t = ((p.x - q.x)*(q.y - q2.y) - (p.y - q.y)*(q.x - q2.x)) / den
    u = ((p.x - q.x)*(p.y - p2.y) - (p.y - q.y)*(p.x - p2.x)) / den
    if 0 <= t <= 1 and 0 <= u <= 1:
        x = p.x + t*(p2.x - p.x)
        y = p.y + t*(p2.y - p.y)
        return Punto(x, y)
    return None


def detectar_intersecciones(segmentos):
    n = len(segmentos)
    for i in range(n):
        for j in range(i+1, n):
            inter = interseccion_segmentos(segmentos[i], segmentos[j])
            if inter is not None:
                if not punto_en_lista(inter, segmentos[i].intersecciones):
                    segmentos[i].intersecciones.append(inter)
                if not punto_en_lista(inter, segmentos[j].intersecciones):
                    segmentos[j].intersecciones.append(inter)


def partir_segmentos(segmentos):
    nuevos = []
    contador = 0
    for s in segmentos:
        puntos = [s.p1]
        for p in s.intersecciones:
            if not puntos_iguales(p, s.p1) and not puntos_iguales(p, s.p2):
                puntos.append(p)
        puntos.append(s.p2)
        puntos.sort(key=lambda p: parametro_segmento(s, p))
        for i in range(len(puntos)-1):
            a = puntos[i]
            b = puntos[i+1]
            if puntos_iguales(a, b):
                continue
            ns = SegmentoOverlay(f"g{contador}", a, b, s.layer)
            nuevos.append(ns)
            contador += 1
    return nuevos


def crear_vertices(segmentos):
    vertices = {}
    contador = 1
    def obtener_nombre(p):
        nonlocal contador
        for nombre, v in vertices.items():
            if puntos_iguales(v.punto, p):
                return nombre
        nombre = f"p{contador}"
        contador += 1
        vertices[nombre] = Vertice(nombre, p)
        return nombre
    for s in segmentos:
        obtener_nombre(s.p1)
        obtener_nombre(s.p2)
    return vertices


def crear_aristas(segmentos, vertices):
    aristas = {}
    contador = 1
    mapa_vertices = {}
    for v in vertices.values():
        mapa_vertices[(round(v.punto.x,6), round(v.punto.y,6))] = v
    for s in segmentos:
        p1 = mapa_vertices[(round(s.p1.x,6), round(s.p1.y,6))]
        p2 = mapa_vertices[(round(s.p2.x,6), round(s.p2.y,6))]
        e1 = Arista(f"s{contador}"); contador += 1
        e2 = Arista(f"s{contador}"); contador += 1
        e1.origen = p1
        e2.origen = p2
        e1.pareja = e2
        e2.pareja = e1
        aristas[e1.nombre] = e1
        aristas[e2.nombre] = e2
    return aristas


def angulo_arista(e):
    p1 = e.origen.punto
    p2 = e.pareja.origen.punto
    return math.atan2(p2.y - p1.y, p2.x - p1.x)


def conectar_aristas(vertices, aristas):
    incidentes = defaultdict(list)
    for e in aristas.values():
        incidentes[e.origen.nombre].append(e)
    for lista in incidentes.values():
        lista.sort(key=angulo_arista)
    for lista in incidentes.values():
        n = len(lista)
        for i in range(n):
            e = lista[i]
            ant = lista[(i-1)%n]
            e.pareja.siguiente = ant
            ant.anterior = e.pareja


def area_poligono(puntos):
    area = 0.0
    n = len(puntos)
    for i in range(n):
        x1, y1 = puntos[i]
        x2, y2 = puntos[(i+1)%n]
        area += x1*y2 - x2*y1
    return area / 2.0


def crear_caras(aristas):
    caras = {}
    contador = 1
    for e in aristas.values():
        if e.cara is not None:
            continue
        ciclo = []
        puntos = []
        actual = e
        while True:
            if actual is None or (actual.cara is not None and actual != e):
                ciclo = []
                break
            ciclo.append(actual)
            puntos.append([actual.origen.punto.x, actual.origen.punto.y])
            actual = actual.siguiente
            if actual == e:
                break
        if len(ciclo) < 3:
            continue
        area = area_poligono(puntos)
        if area <= EPS:
            continue
        c = Cara(f"f{contador}")
        contador += 1
        c.externo = ciclo[0]
        for ar in ciclo:
            ar.cara = c
        caras[c.nombre] = c
    return caras


def crear_cara_infinita(aristas, caras):
    f0 = Cara("f0")
    usadas = set()
    for e in aristas.values():
        if e.cara is None:
            e.cara = f0
            if e.nombre not in usadas:
                f0.interno.append(e)
                usadas.add(e.nombre)
    caras["f0"] = f0


def exportar(vertices, aristas, caras, nombre):
    # vértices
    with open(nombre + ".vertices", "w") as f:
        f.write("Archivo de vértices\n#################################\nNombre  x       y       Incidente\n#################################\n")
        for v in vertices.values():
            inc = v.incidente.nombre if v.incidente else "None"
            f.write(f"{v.nombre} {v.punto.x} {v.punto.y} {inc}\n")
    # aristas
    with open(nombre + ".aristas", "w") as f:
        f.write("Archivo de aristas\n#############################################\nNombre  Origen  Pareja  Cara    Sigue   Antes\n#############################################\n")
        for e in aristas.values():
            origen = e.origen.nombre if e.origen else "None"
            pareja = e.pareja.nombre if e.pareja else "None"
            cara = e.cara.nombre if e.cara else "None"
            sig = e.siguiente.nombre if e.siguiente else "None"
            ant = e.anterior.nombre if e.anterior else "None"
            f.write(f"{e.nombre} {origen} {pareja} {cara} {sig} {ant}\n")
    # caras
    with open(nombre + ".caras", "w") as f:
        f.write("Archivo de caras\n#######################\nNombre  Interno Externo\n#######################\n")
        for c in caras.values():
            interno = "[" + ",".join([e.nombre for e in c.interno]) + "]"
            externo = c.externo.nombre if c.externo else "None"
            f.write(f"{c.nombre} {interno} {externo}\n")


# =========================================================
# VIEWER FUNCTIONS (viewer.py)
# =========================================================

ARCHIVO_ACTIVOS = "./layouts/layer_global.activos"

def generar_colores(caras):
    colores = {}
    for nombre in caras:
        colores[nombre] = (random.random(), random.random(), random.random())
    colores["f0"] = (0.2, 0.6, 1.0)
    return colores

def leer_activos():
    if not os.path.exists(ARCHIVO_ACTIVOS):
        return set()
    with open(ARCHIVO_ACTIVOS, "r") as f:
        return set(line.strip() for line in f if line.strip())

def guardar_activos(activos):
    with open(ARCHIVO_ACTIVOS, "w") as f:
        for nombre in sorted(activos):
            f.write(nombre + "\n")

def obtener_puntos_ciclo(inicio):
    puntos = []
    e = inicio
    visitadas = set()
    while True:
        if e is None:
            return []
        if e.nombre in visitadas:
            break
        visitadas.add(e.nombre)
        p = e.origen.punto
        puntos.append((p.x, p.y))
        e = e.siguiente
        if e == inicio:
            break
    return puntos

def punto_en_cara(x, y, cara):
    if cara.externo is None:
        return False
    puntos = obtener_puntos_ciclo(cara.externo)
    if len(puntos) < 3:
        return False
    return Path(puntos).contains_point((x, y))

def bounding_box(vertices, margen_rel=0.2):
    xs = [v.punto.x for v in vertices.values()]
    ys = [v.punto.y for v in vertices.values()]
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    margen = max(xmax - xmin, ymax - ymin) * margen_rel
    return xmin, xmax, ymin, ymax, margen

def hacer_patch_cara(cara, color):
    puntos = obtener_puntos_ciclo(cara.externo)
    if len(puntos) < 3:
        return None
    return Polygon(puntos, closed=True, facecolor=color,
                   edgecolor='black', linewidth=1.5, alpha=0.5, zorder=2)

def hacer_patch_f0(caras, color, xmin, xmax, ymin, ymax, margen):
    outer = [
        [xmin - margen, ymin - margen],
        [xmax + margen, ymin - margen],
        [xmax + margen, ymax + margen],
        [xmin - margen, ymax + margen],
        [xmin - margen, ymin - margen],
    ]
    verts_path = list(outer)
    codes = [Path.MOVETO, Path.LINETO, Path.LINETO, Path.LINETO, Path.CLOSEPOLY]
    for c in caras.values():
        if c.nombre == "f0" or c.externo is None:
            continue
        pts = obtener_puntos_ciclo(c.externo)
        if len(pts) < 3:
            continue
        pts = pts[::-1]
        verts_path.extend(pts)
        codes.extend([Path.MOVETO] + [Path.LINETO] * (len(pts)-2) + [Path.CLOSEPOLY])
    return PathPatch(Path(verts_path, codes), facecolor=color,
                     edgecolor='none', alpha=0.5, zorder=1)

def viewer(vertices, aristas, caras):
    fig, ax = plt.subplots(figsize=(10, 10))
    xmin, xmax, ymin, ymax, margen = bounding_box(vertices)
    colores = generar_colores(caras)
    activos = leer_activos()
    patches_activos = {}

    # aristas
    dibujadas = set()
    for a in aristas.values():
        if a.nombre in dibujadas:
            continue
        p1 = a.origen.punto
        p2 = a.pareja.origen.punto
        ax.plot([p1.x, p2.x], [p1.y, p2.y], color='black', linewidth=1, zorder=3)
        dibujadas.add(a.nombre)
        dibujadas.add(a.pareja.nombre)

    # vértices
    for v in vertices.values():
        ax.plot(v.punto.x, v.punto.y, 'ko', markersize=3, zorder=4)

    def pintar_cara(nombre_cara):
        if nombre_cara in patches_activos:
            return
        c = caras.get(nombre_cara)
        if c is None:
            return
        color = colores[nombre_cara]
        if nombre_cara == "f0":
            patch = hacer_patch_f0(caras, color, xmin, xmax, ymin, ymax, margen)
        else:
            patch = hacer_patch_cara(c, color)
        if patch is not None:
            ax.add_patch(patch)
            patches_activos[nombre_cara] = patch

    def despintar_cara(nombre_cara):
        patch = patches_activos.pop(nombre_cara, None)
        if patch is not None:
            patch.remove()

    for nombre in list(activos):
        pintar_cara(nombre)

    label = ax.text(0.02, 0.97, "", transform=ax.transAxes, fontsize=11,
                    verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.85), zorder=10)

    ax.set_xlim(xmin - margen, xmax + margen)
    ax.set_ylim(ymin - margen, ymax + margen)
    ax.set_aspect('equal')
    plt.grid(True)
    ax.set_title("Mapa interactivo: Click para activar/desactivar caras", fontsize=14)

    def onclick(event):
        if event.xdata is None or event.ydata is None:
            return
        x, y = event.xdata, event.ydata
        cara_tocada = None
        for c in caras.values():
            if c.nombre == "f0":
                continue
            if punto_en_cara(x, y, c):
                cara_tocada = c
                break
        if cara_tocada is None and "f0" in caras:
            cara_tocada = caras["f0"]
        if cara_tocada is None:
            return
        nombre = cara_tocada.nombre
        if nombre in activos:
            activos.remove(nombre)
            despintar_cara(nombre)
            msg = f"Desactivada: {nombre}"
        else:
            activos.add(nombre)
            pintar_cara(nombre)
            msg = f"Activada: {nombre}"
        print(f"  {msg}  |  Activas: {sorted(activos)}")
        label.set_text(msg)
        guardar_activos(activos)
        fig.canvas.draw_idle()

    fig.canvas.mpl_connect('button_press_event', onclick)
    plt.tight_layout()
    plt.show()


# =========================================================
# MAIN (main.py)
# =========================================================

if __name__ == "__main__":
    nLay = 6
    TODOS = []

    print("\n===================================")
    print("LEYENDO LAYERS")
    print("===================================")

    for i in range(1, nLay):
        nombre = "./layouts/layer0" + str(i)
        print(f"\nLayer {i}")
        vertices, aristas, caras = hacer_objetos(nombre)
        segs = extraer_segmentos(aristas, i)
        TODOS.extend(segs)

    print("\nSegmentos originales:", len(TODOS))

    print("\n===================================")
    print("DETECTANDO INTERSECCIONES")
    print("===================================")
    detectar_intersecciones(TODOS)

    print("\n===================================")
    print("PARTIENDO SEGMENTOS")
    print("===================================")
    nuevos_segmentos = partir_segmentos(TODOS)
    print("Segmentos nuevos:", len(nuevos_segmentos))

    print("\n===================================")
    print("RECONSTRUYENDO DCEL")
    print("===================================")
    vertices = crear_vertices(nuevos_segmentos)
    aristas = crear_aristas(nuevos_segmentos, vertices)
    conectar_aristas(vertices, aristas)

    for e in aristas.values():
        if e.origen is not None and e.origen.incidente is None:
            e.origen.incidente = e

    print("\n===================================")
    print("CREANDO CARAS")
    print("===================================")
    caras = crear_caras(aristas)
    crear_cara_infinita(aristas, caras)
    print("Caras:", len(caras))

    print("\n===================================")
    print("EXPORTANDO")
    print("===================================")
    exportar(vertices, aristas, caras, "./layouts/layer_global")
    print("Archivos exportados.")

    print("\n===================================")
    print("CARAS")
    print("===================================")
    for c in caras.values():
        print(c)

    print("\n===================================")
    print("ABRIENDO VIEWER")
    print("===================================")
    viewer(vertices, aristas, caras)