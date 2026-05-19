# =============================================================================
# main_adaptado_con_pygame_y_matplotlib.py
# =============================================================================
# Versión con debug exhaustivo para localizar aristas/caras perdidas.
# Escribe toda la traza en "debug_overlay.log".
# =============================================================================

import math
import os
import sys
from collections import defaultdict
from typing import List, Set
from dataclasses import dataclass, field
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.patches import Polygon
import numpy as np


# ------------------------------------------------
# 5. VISUALIZACIONES CON MATPLOTLIB
# ------------------------------------------------

def visualizar_capas_originales(listaLayers, todas_las_caras_originales):
    """
    Muestra cada capa con un color diferente.
    Dibuja las aristas (segmentos) y los vértices de cada capa.
    """
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.set_title("Capas originales (un color por capa)", fontsize=14)
    ax.set_aspect('equal')
    ax.grid(True, linestyle=':', alpha=0.6)

    # Generar un color para cada capa
    colores = cm.get_cmap('tab10', len(listaLayers))
    capa_a_color = {layer: colores(i) for i, layer in enumerate(listaLayers)}

    # Para cada capa, extraer sus segmentos y dibujarlos
    for idx, layer in enumerate(listaLayers):
        # Recolectar todas las aristas de esta capa a partir de sus caras
        aristas_capa = set()
        for c in todas_las_caras_originales:
            if layer in c.nombre:   # porque el nombre de la cara incluye el layer
                # Recorrer todas las aristas de la cara (externas e internas)
                if c.aristasExternos:
                    actual = c.aristasExternos
                    inicio = actual
                    while True:
                        aristas_capa.add(actual)
                        actual = actual.siguiente
                        if actual == inicio or actual is None:
                            break
                for a_int in c.aristasInternos:
                    actual = a_int
                    inicio = actual
                    while True:
                        aristas_capa.add(actual)
                        actual = actual.siguiente
                        if actual == inicio or actual is None:
                            break

        # Dibujar las aristas de esta capa
        color = capa_a_color[layer]
        for a in aristas_capa:
            p1 = a.verticeOriginal.coordenadas
            p2 = a.pareja.verticeOriginal.coordenadas
            ax.plot([p1.x, p2.x], [p1.y, p2.y], color=color, linewidth=1.5, alpha=0.7)

        # Dibujar los vértices de esta capa (puntos)
        vertices_capa = set()
        for a in aristas_capa:
            vertices_capa.add(a.verticeOriginal)
            vertices_capa.add(a.pareja.verticeOriginal)
        for v in vertices_capa:
            ax.plot(v.coordenadas.x, v.coordenadas.y, 'o', color=color, markersize=3)

    # Crear leyenda manual
    patches = [plt.Line2D([0], [0], color=capa_a_color[layer], lw=2, label=layer) for layer in listaLayers]
    ax.legend(handles=patches, loc='upper right')

    plt.tight_layout()
    plt.show()


def visualizar_resultado_final(vertices, aristas, caras):
    """
    Muestra el resultado final del overlay: cada cara con un color diferente.
    Se dibujan las caras (relleno con transparencia) y sus bordes.
    """
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.set_title("Resultado final - Overlay (cada cara un color)", fontsize=14)
    ax.set_aspect('equal')
    ax.grid(True, linestyle=':', alpha=0.6)

    # Función para obtener los puntos de una cara (exterior)
    def obtener_puntos_cara(cara):
        if cara.aristasExternos is None:
            return []
        pts = []
        inicio = cara.aristasExternos
        actual = inicio
        visitadas = set()
        while actual and id(actual) not in visitadas:
            visitadas.add(id(actual))
            pts.append((actual.verticeOriginal.coordenadas.x, actual.verticeOriginal.coordenadas.y))
            actual = actual.siguiente
            if actual == inicio:
                break
        return pts

    # Asignar un color distinto a cada cara
    num_caras = len(caras)
    colores = cm.get_cmap('tab20', num_caras)

    for i, c in enumerate(caras):
        pts = obtener_puntos_cara(c)
        if len(pts) < 3:
            continue
        color = colores(i)
        # Dibujar el polígono relleno con cierta transparencia
        poly = Polygon(pts, closed=True, facecolor=color, edgecolor='black',
                       linewidth=1.5, alpha=0.6, label=c.nombre if i < 20 else None)
        ax.add_patch(poly)

    # Dibujar también los vértices para referencia (opcional)
    for v in vertices:
        ax.plot(v.coordenadas.x, v.coordenadas.y, 'ko', markersize=2)

    # Leyenda (solo mostrar las primeras 20 caras para no saturar)
    handles = [p for p in ax.patches if p.get_label()]
    ax.legend(handles=handles, loc='upper right', fontsize='small', ncol=2)

    plt.tight_layout()
    plt.show()


# ------------------------------------------------------------
# 1. CLASES GEOMÉTRICAS (sin cambios)
# ------------------------------------------------------------

# (Se mantienen las mismas clases Punto, SegmentoOverlay, NodoVertice, NodoArista, NodoCara)

@dataclass(frozen=True)
class Punto:
    x: float
    y: float
    def distancia(self, otro: "Punto") -> float:
        return math.hypot(self.x - otro.x, self.y - otro.y)

class SegmentoOverlay:
    def __init__(self, nombre, p1, p2, layer):
        self.nombre = nombre
        self.p1 = p1
        self.p2 = p2
        self.layer = layer
        self.intersecciones = []
    def __repr__(self):
        return f"Seg({self.nombre}, {self.layer})"

class NodoVertice:
    def __init__(self, nombre, coordenadas):
        self.nombre = nombre
        self.coordenadas = coordenadas
        self.aristaAdyacente = None

class NodoArista:
    def __init__(self, nombre):
        self.nombre = nombre
        self.verticeOriginal = None
        self.pareja = None
        self.cara = None
        self.siguiente = None
        self.anterior = None

class NodoCara:
    def __init__(self, nombre):
        self.nombre = nombre
        self.aristasInternos = []
        self.aristasExternos = None

# ------------------------------------------------------------
# 2. FUNCIONES GEOMÉTRICAS (sin cambios)
# ------------------------------------------------------------

EPS = 1e-6

def puntos_iguales(p1: Punto, p2: Punto) -> bool:
    return abs(p1.x - p2.x) < EPS and abs(p1.y - p2.y) < EPS

def parametro_segmento(seg: SegmentoOverlay, p: Punto) -> float:
    dx = seg.p2.x - seg.p1.x
    dy = seg.p2.y - seg.p1.y
    if abs(dx) > abs(dy):
        return (p.x - seg.p1.x) / dx if abs(dx) > EPS else 0
    return (p.y - seg.p1.y) / dy if abs(dy) > EPS else 0

def orient(a: Punto, b: Punto, c: Punto) -> float:
    return (b.x - a.x)*(c.y - a.y) - (b.y - a.y)*(c.x - a.x)

def punto_en_segmento(p: Punto, a: Punto, b: Punto) -> bool:
    """Devuelve True si p está sobre el segmento cerrado [a,b] (colinealidad asumida)."""
    return (min(a.x, b.x) - EPS <= p.x <= max(a.x, b.x) + EPS and
            min(a.y, b.y) - EPS <= p.y <= max(a.y, b.y) + EPS)

def interseccion_segmentos(s1: SegmentoOverlay, s2: SegmentoOverlay):
    """Retorna lista de puntos de intersección (0, 1 o 2)."""
    p1, p2 = s1.p1, s1.p2
    q1, q2 = s2.p1, s2.p2

    den = (p1.x - p2.x)*(q1.y - q2.y) - (p1.y - p2.y)*(q1.x - q2.x)
    
    if abs(den) < EPS:
        # Caso colineal: verificar si realmente son colineales
        if abs(orient(p1, p2, q1)) > EPS and abs(orient(p1, p2, q2)) > EPS:
            return []   # paralelos no colineales
        
        # Proyectar sobre el eje principal para ordenar
        def coord(pt):
            return pt.x if abs(p2.x - p1.x) > abs(p2.y - p1.y) else pt.y
        
        puntos = sorted([p1, p2, q1, q2], key=coord)
        a, b = puntos[1], puntos[2]   # posible zona de solapamiento
        
        if puntos_iguales(a, b):
            # Un solo punto de contacto
            if punto_en_segmento(a, p1, p2) and punto_en_segmento(a, q1, q2):
                return [a]
            return []
        
        # Verificar que ambos puntos pertenecen a ambos segmentos
        if (punto_en_segmento(a, p1, p2) and punto_en_segmento(a, q1, q2) and
            punto_en_segmento(b, p1, p2) and punto_en_segmento(b, q1, q2)):
            return [a, b]
        return []
    
    # Caso no colineal (cálculo de t y u)
    t = ((p1.x - q1.x)*(q1.y - q2.y) - (p1.y - q1.y)*(q1.x - q2.x)) / den
    u = ((p1.x - q1.x)*(p1.y - p2.y) - (p1.y - q1.y)*(p1.x - p2.x)) / den

    if 0 <= t <= 1 and 0 <= u <= 1:
        x = p1.x + t*(p2.x - p1.x)
        y = p1.y + t*(p2.y - p1.y)
        return [Punto(x, y)]
    return []

# ------------------------------------------------------------
# 3. LECTURA DE CAPAS (se añade debug)
# ------------------------------------------------------------

def cargar_layer(layer_name: str):
    vertices = []
    aristas = []
    caras = []
    activas = set()

    DEBUG_LOG.write(f"\n========== Cargando capa: {layer_name} ==========\n")

    # Vértices
    try:
        with open(f"{layer_name}.vertices", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("Nombre") or line.startswith("Archivo"):
                    continue
                partes = line.split()
                if len(partes) >= 4:
                    nombre, x, y, incidente = partes[0], partes[1], partes[2], partes[3]
                    v = NodoVertice(nombre + layer_name, Punto(float(x), float(y)))
                    v.aristaAdyacente = incidente + layer_name if incidente != "None" else None
                    vertices.append(v)
                    DEBUG_LOG.write(f"  Vértice leído: {v.nombre} ({v.coordenadas.x}, {v.coordenadas.y}) incidente={incidente}\n")
    except FileNotFoundError:
        DEBUG_LOG.write(f"  [AVISO] No se encontró {layer_name}.vertices\n")

    # Aristas
    try:
        with open(f"{layer_name}.aristas", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("Nombre") or line.startswith("Archivo"):
                    continue
                partes = line.split()
                if len(partes) >= 6:
                    nombre, origen, pareja, cara, sig, ant = partes[:6]
                    a = NodoArista(nombre + layer_name)
                    a.verticeOriginal = origen + layer_name if origen != "None" else None
                    a.pareja = pareja + layer_name if pareja != "None" else None
                    a.cara = cara + layer_name if cara != "None" else None
                    a.siguiente = sig + layer_name if sig != "None" else None
                    a.anterior = ant + layer_name if ant != "None" else None
                    aristas.append(a)
                    DEBUG_LOG.write(f"  Arista leída: {a.nombre} orig={origen} pareja={pareja} cara={cara} sig={sig} ant={ant}\n")
    except FileNotFoundError:
        DEBUG_LOG.write(f"  [AVISO] No se encontró {layer_name}.aristas\n")

    # Caras
    try:
        with open(f"{layer_name}.caras", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("Nombre") or line.startswith("Archivo"):
                    continue
                partes = line.split()
                if len(partes) >= 3:
                    nombre, interno, externo = partes[0], partes[1], partes[2]
                    c = NodoCara(nombre + layer_name)
                    if interno != "None":
                        interno_limpio = interno.strip("[]")
                        if interno_limpio:
                            c.aristasInternos = [x.strip() + layer_name for x in interno_limpio.split(",") if x.strip()]
                    if externo != "None":
                        c.aristasExternos = externo + layer_name
                    caras.append(c)
                    DEBUG_LOG.write(f"  Cara leída: {c.nombre} externo={externo} internos={interno}\n")
    except FileNotFoundError:
        DEBUG_LOG.write(f"  [AVISO] No se encontró {layer_name}.caras\n")

    # Activos
    try:
        with open(f"{layer_name}.activos", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and not line.startswith("Archivo") and not line.startswith("Caras"):
                    activas.add(line + layer_name)
                    DEBUG_LOG.write(f"  Activa leída: {line + layer_name}\n")
    except FileNotFoundError:
        DEBUG_LOG.write(f"  [AVISO] No se encontró {layer_name}.activos\n")

    # Resolver referencias cruzadas
    dict_vertices = {v.nombre: v for v in vertices}
    dict_aristas = {a.nombre: a for a in aristas}
    dict_caras = {c.nombre: c for c in caras}

    for a in aristas:
        if isinstance(a.verticeOriginal, str):
            a.verticeOriginal = dict_vertices.get(a.verticeOriginal)
        if isinstance(a.pareja, str):
            a.pareja = dict_aristas.get(a.pareja)
        if isinstance(a.cara, str):
            a.cara = dict_caras.get(a.cara)
        if isinstance(a.siguiente, str):
            a.siguiente = dict_aristas.get(a.siguiente)
        if isinstance(a.anterior, str):
            a.anterior = dict_aristas.get(a.anterior)
        DEBUG_LOG.write(f"  Resuelta arista {a.nombre}: vertOrig={a.verticeOriginal.nombre if a.verticeOriginal else 'None'} pareja={a.pareja.nombre if a.pareja else 'None'} cara={a.cara.nombre if a.cara else 'None'} sig={a.siguiente.nombre if a.siguiente else 'None'} ant={a.anterior.nombre if a.anterior else 'None'}\n")

    for v in vertices:
        if isinstance(v.aristaAdyacente, str):
            v.aristaAdyacente = dict_aristas.get(v.aristaAdyacente)
        DEBUG_LOG.write(f"  Vértice {v.nombre}: incidente={v.aristaAdyacente.nombre if v.aristaAdyacente else 'None'}\n")

    for c in caras:
        if isinstance(c.aristasExternos, str):
            c.aristasExternos = dict_aristas.get(c.aristasExternos)
        nuevos_internos = []
        for item in c.aristasInternos:
            if isinstance(item, str):
                a = dict_aristas.get(item)
                if a:
                    nuevos_internos.append(a)
        c.aristasInternos = nuevos_internos
        DEBUG_LOG.write(f"  Cara resuelta {c.nombre}: externo={c.aristasExternos.nombre if c.aristasExternos else 'None'} internos={[e.nombre for e in c.aristasInternos]}\n")

    DEBUG_LOG.write(f"  Capa {layer_name}: {len(vertices)} vértices, {len(aristas)} aristas, {len(caras)} caras, {len(activas)} activas\n")
    return vertices, aristas, caras, activas

# ------------------------------------------------------------
# 4. ALGORITMO DE OVERLAY (se añade debug)
# ------------------------------------------------------------

def extraer_segmentos(aristas, layer_id):
    segmentos = []
    visitadas = set()
    for a in aristas:
        if a.nombre in visitadas:
            continue
        p1 = a.verticeOriginal.coordenadas
        p2 = a.pareja.verticeOriginal.coordenadas
        seg = SegmentoOverlay(a.nombre, p1, p2, layer_id)
        segmentos.append(seg)
        visitadas.add(a.nombre)
        visitadas.add(a.pareja.nombre)
        DEBUG_LOG.write(f"  Segmento extraído: {seg.nombre} de {layer_id} ({p1.x},{p1.y})->({p2.x},{p2.y})\n")
    return segmentos

def detectar_intersecciones(segmentos):
    DEBUG_LOG.write("\n--- Detectando intersecciones ---\n")
    n = len(segmentos)
    for i in range(n):
        for j in range(i+1, n):
            inters = interseccion_segmentos(segmentos[i], segmentos[j])
            if inters:
                DEBUG_LOG.write(f"  Intersección entre {segmentos[i].nombre} y {segmentos[j].nombre}: {[(p.x,p.y) for p in inters]}\n")
            for p in inters:
                if not any(puntos_iguales(p, q) for q in segmentos[i].intersecciones):
                    segmentos[i].intersecciones.append(p)
                if not any(puntos_iguales(p, q) for q in segmentos[j].intersecciones):
                    segmentos[j].intersecciones.append(p)

def partir_segmentos(segmentos):
    DEBUG_LOG.write("\n--- Partiendo segmentos ---\n")
    nuevos = []
    contador = 0
    for s in segmentos:
        puntos = [s.p1]
        for p in s.intersecciones:
            if not puntos_iguales(p, s.p1) and not puntos_iguales(p, s.p2):
                puntos.append(p)
        puntos.append(s.p2)
        puntos.sort(key=lambda pt: parametro_segmento(s, pt))
        DEBUG_LOG.write(f"  Segmento {s.nombre} partido en {len(puntos)-1} subsegmentos: puntos={[(p.x,p.y) for p in puntos]}\n")
        for i in range(len(puntos)-1):
            a, b = puntos[i], puntos[i+1]
            if puntos_iguales(a, b):
                continue
            ns = SegmentoOverlay(f"g{contador}", a, b, s.layer)
            nuevos.append(ns)
            DEBUG_LOG.write(f"    Subsegmento {ns.nombre} ({a.x},{a.y})->({b.x},{b.y}) layer={ns.layer}\n")
            contador += 1
    return nuevos

def unificar_segmentos_colineales(segmentos):
    """Agrupa segmentos colineales y los fusiona SOLO donde realmente hay cobertura."""
    grupos = defaultdict(list)
    for seg in segmentos:
        dx = seg.p2.x - seg.p1.x
        dy = seg.p2.y - seg.p1.y
        # Normalizar dirección
        if dx < -EPS or (abs(dx) < EPS and dy < -EPS):
            dx, dy = -dx, -dy
        a = dy
        b = -dx
        c = -(a * seg.p1.x + b * seg.p1.y)
        norm = math.hypot(a, b)
        a /= norm
        b /= norm
        c /= norm
        # Hacer la representación única
        if a < -EPS or (abs(a) < EPS and b < -EPS):
            a, b, c = -a, -b, -c
        clave = (round(a, 10), round(b, 10), round(c, 10))
        grupos[clave].append(seg)

    nuevos = []
    contador = 0
    for clave, segs in grupos.items():
        # Elegir el eje para ordenar
        if abs(clave[0]) > abs(clave[1]):
            key_func = lambda p: (p.x, p.y)
        else:
            key_func = lambda p: (p.y, p.x)

        # Recopilar todos los puntos únicos (extremos e intersecciones)
        puntos_unicos = {}
        for seg in segs:
            for p in [seg.p1, seg.p2] + seg.intersecciones:
                k = (round(p.x, 8), round(p.y, 8))
                if k not in puntos_unicos:
                    puntos_unicos[k] = p
        puntos = list(puntos_unicos.values())
        puntos.sort(key=key_func)

        # Mapeo de punto a índice para calcular coberturas
        pt_to_idx = { (round(p.x,8), round(p.y,8)): i for i, p in enumerate(puntos) }

        # Inicializar cobertura a 0
        cobertura = [0] * (len(puntos) - 1)

        # Marcar cobertura basada en los segmentos originales
        for seg in segs:
            i1 = pt_to_idx[(round(seg.p1.x,8), round(seg.p1.y,8))]
            i2 = pt_to_idx[(round(seg.p2.x,8), round(seg.p2.y,8))]
            if i1 > i2:
                i1, i2 = i2, i1
            for idx in range(i1, i2):
                cobertura[idx] += 1

        # Crear segmentos solo para intervalos con cobertura > 0
        for i in range(len(puntos)-1):
            if cobertura[i] > 0:
                a, b = puntos[i], puntos[i+1]
                if puntos_iguales(a, b):
                    continue
                ns = SegmentoOverlay(f"g{contador}", a, b, "unified")
                nuevos.append(ns)
                contador += 1

    return nuevos

def crear_vertices(segmentos):
    DEBUG_LOG.write("\n--- Creando vértices a partir de nuevos segmentos ---\n")
    vertices = {}
    contador = 1
    def obtener_nombre(p):
        nonlocal contador
        for nombre, v in vertices.items():
            if puntos_iguales(v.coordenadas, p):
                return nombre
        nombre = f"p{contador}"
        contador += 1
        vertices[nombre] = NodoVertice(nombre, p)
        DEBUG_LOG.write(f"  Nuevo vértice: {nombre} ({p.x},{p.y})\n")
        return nombre
    for s in segmentos:
        obtener_nombre(s.p1)
        obtener_nombre(s.p2)
    return list(vertices.values())

def crear_aristas(segmentos, vertices):
    DEBUG_LOG.write("\n--- Creando half-edges ---\n")
    aristas = []
    contador = 1
    mapa = {}
    for v in vertices:
        mapa[(round(v.coordenadas.x, 6), round(v.coordenadas.y, 6))] = v
    for s in segmentos:
        p1 = mapa[(round(s.p1.x,6), round(s.p1.y,6))]
        p2 = mapa[(round(s.p2.x,6), round(s.p2.y,6))]
        e1 = NodoArista(f"s{contador}"); contador += 1
        e2 = NodoArista(f"s{contador}"); contador += 1
        e1.verticeOriginal = p1
        e2.verticeOriginal = p2
        e1.pareja = e2
        e2.pareja = e1
        aristas.append(e1)
        aristas.append(e2)
        DEBUG_LOG.write(f"  Half-edges: {e1.nombre} (de {p1.nombre} a {p2.nombre}) y {e2.nombre} (de {p2.nombre} a {p1.nombre})\n")
    return aristas

def angulo_arista(e: NodoArista) -> float:
    p1 = e.verticeOriginal.coordenadas
    p2 = e.pareja.verticeOriginal.coordenadas
    return math.atan2(p2.y - p1.y, p2.x - p1.x)

def conectar_aristas(vertices, aristas):
    DEBUG_LOG.write("\n--- Conectando half-edges (siguiente/anterior) ---\n")
    incidentes = defaultdict(list)
    for e in aristas:
        incidentes[e.verticeOriginal.nombre].append(e)
    for v_nombre, lista in incidentes.items():
        lista.sort(key=angulo_arista)
        DEBUG_LOG.write(f"  Vértice {v_nombre}: aristas incidentes ordenadas: {[e.nombre for e in lista]}\n")
    for v_nombre, lista in incidentes.items():
        n = len(lista)
        for i in range(n):
            e = lista[i]
            ant = lista[(i-1)%n]
            e.pareja.siguiente = ant
            ant.anterior = e.pareja
            DEBUG_LOG.write(f"    Enlace: {e.pareja.nombre}.siguiente = {ant.nombre}, {ant.nombre}.anterior = {e.pareja.nombre}\n")

def area_poligono(puntos):
    area = 0.0
    n = len(puntos)
    for i in range(n):
        x1, y1 = puntos[i]
        x2, y2 = puntos[(i+1)%n]
        area += x1*y2 - x2*y1
    return area / 2.0

def crear_caras(aristas):
    DEBUG_LOG.write("\n--- Formando caras (ciclos) ---\n")
    caras = {}
    contador = 1
    for e in aristas:
        if e.cara is not None:
            continue
        DEBUG_LOG.write(f"  Iniciando ciclo desde {e.nombre}\n")
        ciclo = []
        puntos = []
        actual = e
        while True:
            if actual is None or (actual.cara is not None and actual != e):
                DEBUG_LOG.write(f"    Ciclo abortado: actual es None o ya tiene cara.\n")
                ciclo = []
                break
            ciclo.append(actual)
            puntos.append([actual.verticeOriginal.coordenadas.x, actual.verticeOriginal.coordenadas.y])
            DEBUG_LOG.write(f"    Añadida {actual.nombre} ({actual.verticeOriginal.coordenadas.x},{actual.verticeOriginal.coordenadas.y}), siguiente={actual.siguiente.nombre if actual.siguiente else 'None'}\n")
            actual = actual.siguiente
            if actual == e:
                break
        if len(ciclo) < 3:
            DEBUG_LOG.write(f"  Ciclo de {len(ciclo)} aristas -> ignorado\n")
            continue
        area = area_poligono(puntos)
        DEBUG_LOG.write(f"  Ciclo cerrado con {len(ciclo)} aristas, área={area}\n")
        if area <= EPS:
            DEBUG_LOG.write(f"  Área <= 0 -> ignorado\n")
            continue
        c = NodoCara(f"f{contador}")
        contador += 1
        c.aristasExternos = ciclo[0]
        for ar in ciclo:
            ar.cara = c
        caras[c.nombre] = c
        DEBUG_LOG.write(f"  Cara creada: {c.nombre}\n")
    DEBUG_LOG.write(f"  Total de caras finitas creadas: {len(caras)}\n")
    return list(caras.values())

def crear_cara_infinita(aristas, caras):
    DEBUG_LOG.write("\n--- Creando cara infinita (f0) ---\n")
    f0 = NodoCara("f0")
    sin_cara = [e for e in aristas if e.cara is None]
    DEBUG_LOG.write(f"  Aristas sin cara: {[e.nombre for e in sin_cara]}\n")

    # Asignar f0 a todas ellas
    for e in sin_cara:
        e.cara = f0

    # Recorrer sin_cara para identificar los ciclos (huecos)
    visitados = set()
    representantes = []
    for e in sin_cara:
        if e.nombre in visitados:
            continue
        # Recorrer el ciclo completo
        ciclo = []
        actual = e
        while actual and actual.nombre not in visitados:
            visitados.add(actual.nombre)
            ciclo.append(actual)
            actual = actual.siguiente
            if actual == e:
                break
        if ciclo:
            # Guardar solo una arista como representante del hueco
            representantes.append(ciclo[0])
            DEBUG_LOG.write(f"    Hueco representado por {ciclo[0].nombre}, ciclo de {len(ciclo)} aristas\n")

    f0.aristasInternos = representantes
    caras.append(f0)
    DEBUG_LOG.write(f"  f0 tiene {len(representantes)} hueco(s) representados por: {[e.nombre for e in representantes]}\n")
# ------------------------------------------------------------
# 5. EXPORTAR (se añade volcado de debug final)
# ------------------------------------------------------------

def exportar_resultado(vertices, aristas, caras, caras_activas_nombres, base="resultado"):
    # (código de exportación sin cambios, no necesita debug extra)
    with open(base + ".vertices", "w", encoding="utf-8") as f:
        f.write("Archivo de vértices\n#################################\nNombre  x       y       Incidente\n#################################\n")
        for v in vertices:
            inc = v.aristaAdyacente.nombre if v.aristaAdyacente else "None"
            f.write(f"{v.nombre} {v.coordenadas.x:.6f} {v.coordenadas.y:.6f} {inc}\n")
    with open(base + ".aristas", "w", encoding="utf-8") as f:
        f.write("Archivo de aristas\n#############################################\nNombre  Origen  Pareja  Cara    Sigue   Antes\n#############################################\n")
        for a in aristas:
            origen = a.verticeOriginal.nombre if a.verticeOriginal else "None"
            pareja = a.pareja.nombre if a.pareja else "None"
            cara = a.cara.nombre if a.cara else "None"
            sig = a.siguiente.nombre if a.siguiente else "None"
            ant = a.anterior.nombre if a.anterior else "None"
            f.write(f"{a.nombre} {origen} {pareja} {cara} {sig} {ant}\n")
    with open(base + ".caras", "w", encoding="utf-8") as f:
        f.write("Archivo de caras\n#######################\nNombre  Interno Externo\n#######################\n")
        for c in caras:
            interno = "[" + ",".join([e.nombre for e in c.aristasInternos]) + "]"
            externo = c.aristasExternos.nombre if c.aristasExternos else "None"
            f.write(f"{c.nombre} {interno} {externo}\n")
    with open(base + ".activos", "w", encoding="utf-8") as f:
        f.write("Archivo de activos\n#######################\nCaras Activas\n#######################\n")
        for nombre in caras_activas_nombres:
            f.write(f"{nombre}\n")
    print(f"Exportado a {base}.*")

# ------------------------------------------------------------
# 6. VISUALIZACIONES (sin cambios, no se tocan para el debug)
# ------------------------------------------------------------

def visualizar_vertices_dcel(vertices):
    """Muestra todos los vértices de la DCEL (puntos de intersección y extremos)."""
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.set_aspect('equal')
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.set_title("Vértices de la DCEL (intersecciones y extremos)", fontsize=14)

    xs = [v.coordenadas.x for v in vertices]
    ys = [v.coordenadas.y for v in vertices]
    ax.scatter(xs, ys, c='red', s=30, zorder=5)

    # Etiquetas si no hay demasiados puntos
    if len(vertices) <= 50:
        for v in vertices:
            ax.annotate(v.nombre, (v.coordenadas.x, v.coordenadas.y),
                        textcoords="offset points", xytext=(5, 5), fontsize=8)

    plt.tight_layout()
    plt.show()


def visualizar_aristas_dcel(aristas):
    """Dibuja todas las half‑edges de la DCEL (una línea por par) con flechas de orientación."""
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.set_aspect('equal')
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.set_title("Aristas de la DCEL (half‑edges dirigidas)", fontsize=14)

    dibujadas = set()
    for a in aristas:
        # Para cada par de gemelas, dibujamos solo una línea, pero con flecha en ambos sentidos.
        # Usamos el nombre de la arista original para evitar duplicados.
        par = tuple(sorted([a.nombre, a.pareja.nombre]))
        if par in dibujadas:
            continue
        dibujadas.add(par)

        p1 = a.verticeOriginal.coordenadas
        p2 = a.pareja.verticeOriginal.coordenadas

        # Línea principal
        ax.plot([p1.x, p2.x], [p1.y, p2.y], color='black', linewidth=1.2)

        # Flecha en la dirección de la half‑edge actual
        mid_x = (p1.x + p2.x) / 2
        mid_y = (p1.y + p2.y) / 2
        dx = p2.x - p1.x
        dy = p2.y - p1.y
        ax.annotate('', xy=(mid_x + dx*0.01, mid_y + dy*0.01),
                    xytext=(mid_x - dx*0.01, mid_y - dy*0.01),
                    arrowprops=dict(arrowstyle='->', color='blue', lw=1.5))

        # Flecha opuesta (para la gemela)
        ax.annotate('', xy=(mid_x - dx*0.01, mid_y - dy*0.01),
                    xytext=(mid_x + dx*0.01, mid_y + dy*0.01),
                    arrowprops=dict(arrowstyle='->', color='red', lw=1.5))

    # Vértices de las aristas
    vertices_set = set()
    for a in aristas:
        vertices_set.add(a.verticeOriginal)
    for v in vertices_set:
        ax.plot(v.coordenadas.x, v.coordenadas.y, 'ko', markersize=3)

    plt.tight_layout()
    plt.show()

def visualizar_resultado_interactivo(vertices, aristas, caras, caras_activas_inicial):
    """
    Visualización interactiva del overlay con Matplotlib.
    - Cada cara (incluida f0) tiene un color único si está activa.
    - Caras inactivas: se dibujan en blanco puro.
    - Click sobre una cara → activa/desactiva.
    - Checkboxes para mostrar/ocultar:
        * Nombres de caras (centroide)
        * Nombres de vértices
        * Nombres de aristas (mitad de la half‑edge)
        * Flechas de dirección de los ciclos (desplazadas siempre a la izquierda):
            - Azul: borde exterior
            - Rojo: borde interior/hueco
    """
    import matplotlib.pyplot as plt
    from matplotlib.widgets import CheckButtons
    from matplotlib.patches import Polygon, Rectangle, FancyArrowPatch
    import numpy as np

    # --- Colores base por cara (tab20) ---
    num_caras = len(caras)
    cmap = plt.cm.get_cmap('tab20', num_caras)
    face_colors = {}
    for i, c in enumerate(caras):
        face_colors[c.nombre] = cmap(i)
    face_colors.setdefault("f0", (0.5, 0.5, 0.5))

    COLOR_BORDE = 'black'
    COLOR_VERTICE = 'white'

    # --- Preparar figura ---
    fig, ax = plt.subplots(figsize=(12, 9))
    plt.subplots_adjust(left=0.02, right=0.98, top=0.95, bottom=0.05)
    ax.set_aspect('equal')
    ax.grid(True, linestyle=':', alpha=0.4)
    ax.set_title("Resultado Overlay – Interactivo (clic para activar/desactivar)", fontsize=13)

    min_x = min(v.coordenadas.x for v in vertices)
    max_x = max(v.coordenadas.x for v in vertices)
    min_y = min(v.coordenadas.y for v in vertices)
    max_y = max(v.coordenadas.y for v in vertices)
    margin = 0.1 * max(max_x - min_x, max_y - min_y, 1.0)
    ax.set_xlim(min_x - margin, max_x + margin)
    ax.set_ylim(min_y - margin, max_y + margin)

    caras_activas = set(caras_activas_inicial)

    # --- Helpers ---
    def obtener_ciclo(cara):
        if cara.aristasExternos is None:
            return []
        pts = []
        inicio = cara.aristasExternos
        actual = inicio
        visitados = set()
        while actual and id(actual) not in visitados:
            visitados.add(id(actual))
            pts.append((actual.verticeOriginal.coordenadas.x, actual.verticeOriginal.coordenadas.y))
            actual = actual.siguiente
            if actual == inicio:
                break
        return pts

    def centroide(poly):
        if len(poly) < 3:
            return (0, 0)
        x = [p[0] for p in poly]
        y = [p[1] for p in poly]
        return (sum(x)/len(poly), sum(y)/len(poly))

    face_patches = {}
    face_centroids = {}

    def redraw():
        nonlocal face_patches, face_centroids
        ax.clear()
        ax.set_aspect('equal')
        ax.grid(True, linestyle=':', alpha=0.4)
        ax.set_xlim(min_x - margin, max_x + margin)
        ax.set_ylim(min_y - margin, max_y + margin)

        # Identificar aristas exteriores de cada cara
        exterior_edges = {}
        for c in caras:
            ext_set = set()
            if c.aristasExternos is not None:
                actual = c.aristasExternos
                inicio = actual
                while True:
                    ext_set.add(actual.nombre)
                    actual = actual.siguiente
                    if actual == inicio or actual is None:
                        break
            exterior_edges[c.nombre] = ext_set

        # --- Cara infinita (fondo) ---
        f0_activa = ("f0" in caras_activas)
        color_f0 = face_colors.get("f0", (0.5,0.5,0.5)) if f0_activa else 'white'
        alpha_f0 = 0.8 if f0_activa else 1.0
        fondo = Rectangle((min_x - margin, min_y - margin),
                          max_x - min_x + 2*margin,
                          max_y - min_y + 2*margin,
                          facecolor=color_f0, edgecolor='none',
                          alpha=alpha_f0, zorder=0)
        ax.add_patch(fondo)
        poly_f0 = Polygon([(min_x - margin, min_y - margin),
                           (max_x + margin, min_y - margin),
                           (max_x + margin, max_y + margin),
                           (min_x - margin, max_y + margin)],
                          facecolor='none', edgecolor='none', zorder=0, picker=True)
        ax.add_patch(poly_f0)
        face_patches["f0"] = poly_f0
        face_centroids["f0"] = ((min_x+max_x)/2, (min_y+max_y)/2)

        # --- Caras finitas ---
        for c in caras:
            if c.nombre == "f0":
                continue
            pts = obtener_ciclo(c)
            if len(pts) < 3:
                continue
            activa = (c.nombre in caras_activas)
            color_base = face_colors[c.nombre] if activa else 'white'
            alpha = 0.8 if activa else 1.0
            poly = Polygon(pts, closed=True, facecolor=color_base,
                           edgecolor=COLOR_BORDE, linewidth=1.2,
                           alpha=alpha, zorder=1, picker=True)
            ax.add_patch(poly)
            face_patches[c.nombre] = poly
            face_centroids[c.nombre] = centroide(pts)

        # --- Nombres de caras ---
        if chk_face_names.get_status()[0]:
            for nombre, (cx, cy) in face_centroids.items():
                ax.text(cx, cy, nombre, ha='center', va='center',
                        fontsize=8, color='white', fontweight='bold',
                        bbox=dict(facecolor='black', alpha=0.5, pad=1))

        # --- Vértices ---
        for v in vertices:
            ax.plot(v.coordenadas.x, v.coordenadas.y, 'o', color=COLOR_VERTICE,
                    markersize=4, markeredgecolor='black', zorder=3)
        if chk_vertex_names.get_status()[0]:
            for v in vertices:
                ax.text(v.coordenadas.x, v.coordenadas.y + 0.05,
                        v.nombre, fontsize=7, ha='center', color='yellow',
                        bbox=dict(facecolor='black', alpha=0.6, pad=0))

        # --- Aristas (líneas originales) ---
        dibujadas = set()
        for e in aristas:
            p1 = e.verticeOriginal.coordenadas
            p2 = e.pareja.verticeOriginal.coordenadas
            par = tuple(sorted([e.nombre, e.pareja.nombre]))
            if par not in dibujadas:
                dibujadas.add(par)
                ax.plot([p1.x, p2.x], [p1.y, p2.y], color='black', linewidth=1.0, zorder=2)

        # --- Flechas desplazadas (estilo debug) ---
        if chk_arrows.get_status()[0]:
            OFFSET = 0.15  # desplazamiento fijo
            for e in aristas:
                p1 = e.verticeOriginal.coordenadas
                p2 = e.pareja.verticeOriginal.coordenadas
                dx = p2.x - p1.x
                dy = p2.y - p1.y
                L = math.hypot(dx, dy)
                if L < 1e-9:
                    continue
                dx /= L
                dy /= L
                # Normal izquierda (rotación +90°)
                nx = -dy
                ny = dx
                # Puntos desplazados
                sx1 = p1.x + nx * OFFSET
                sy1 = p1.y + ny * OFFSET
                sx2 = p2.x + nx * OFFSET
                sy2 = p2.y + ny * OFFSET

                # Color según tipo
                es_exterior = (e.cara is not None and e.cara.nombre != "f0" 
                               and e.nombre in exterior_edges.get(e.cara.nombre, set()))
                color_flecha = 'blue' if es_exterior else 'red'

                # Dibujar flecha con FancyArrowPatch (más suave que ax.arrow)
                arrow = FancyArrowPatch((sx1, sy1), (sx2, sy2),
                                        arrowstyle='->', mutation_scale=10,
                                        color=color_flecha, alpha=0.85, lw=1.0,
                                        zorder=4)
                ax.add_patch(arrow)

        # --- Nombres de aristas y siguiente ---
        if chk_edge_names.get_status()[0]:
            dibujadas_nombres = set()
            for e in aristas:
                p1 = e.verticeOriginal.coordenadas
                p2 = e.pareja.verticeOriginal.coordenadas
                par = tuple(sorted([e.nombre, e.pareja.nombre]))
                if par in dibujadas_nombres:
                    continue
                dibujadas_nombres.add(par)
                mx, my = (p1.x + p2.x)/2, (p1.y + p2.y)/2
                ax.text(mx, my, e.nombre, fontsize=6, ha='center',
                        color='cyan', bbox=dict(facecolor='black', alpha=0.7, pad=0))
                if e.siguiente:
                    ax.text(mx, my - 0.15, f"→ {e.siguiente.nombre}",
                            fontsize=5, ha='center', color='green',
                            bbox=dict(facecolor='black', alpha=0.6, pad=0))

        fig.canvas.draw_idle()

    # --- Checkboxes ---
    rax = plt.axes([0.01, 0.90, 0.15, 0.08])
    chk_face_names = CheckButtons(rax, ['Nombres caras'], [False])
    rax2 = plt.axes([0.01, 0.82, 0.15, 0.08])
    chk_vertex_names = CheckButtons(rax2, ['Nombres vértices'], [False])
    rax3 = plt.axes([0.01, 0.74, 0.15, 0.08])
    chk_edge_names = CheckButtons(rax3, ['Nombres aristas'], [False])
    rax4 = plt.axes([0.01, 0.66, 0.15, 0.08])
    chk_arrows = CheckButtons(rax4, ['Flechas ciclos'], [False])

    def on_check(label):
        redraw()
    chk_face_names.on_clicked(on_check)
    chk_vertex_names.on_clicked(on_check)
    chk_edge_names.on_clicked(on_check)
    chk_arrows.on_clicked(on_check)

    # --- Clics sobre caras ---
    def on_click(event):
        if event.inaxes != ax:
            return
        caras_finitas = [c for c in caras if c.nombre != "f0"]
        def area_aprox(c):
            if c.nombre in face_patches:
                patch = face_patches[c.nombre]
                path = patch.get_path()
                if path is not None:
                    verts = path.vertices
                    if len(verts) >= 3:
                        area = 0.0
                        for i in range(len(verts)):
                            x1, y1 = verts[i]
                            x2, y2 = verts[(i+1)%len(verts)]
                            area += x1*y2 - x2*y1
                        return abs(area)/2.0
            return float('inf')
        caras_finitas.sort(key=area_aprox)

        clicked_cara = None
        for c in caras_finitas:
            patch = face_patches.get(c.nombre)
            if patch is not None and patch.contains(event)[0]:
                clicked_cara = c
                break
        if clicked_cara is None:
            patch_f0 = face_patches.get("f0")
            if patch_f0 is not None and patch_f0.contains(event)[0]:
                clicked_cara = next((c for c in caras if c.nombre == "f0"), None)

        if clicked_cara is not None:
            if clicked_cara.nombre in caras_activas:
                caras_activas.remove(clicked_cara.nombre)
            else:
                caras_activas.add(clicked_cara.nombre)
            print(f"Toggle cara {clicked_cara.nombre} -> activas: {sorted(caras_activas)}")
            redraw()

    fig.canvas.mpl_connect('button_press_event', on_click)
    redraw()
    plt.show()


# ------------------------------------------------------------
# 7. FUNCIÓN PRINCIPAL (con debug)
# ------------------------------------------------------------

# Variable global para el archivo de debug
DEBUG_LOG = None

def main():
    global DEBUG_LOG
    DEBUG_LOG = open("debug/debug_overlay.log", "w", encoding="utf-8")
    DEBUG_LOG.write("=== INICIO DEL PROCESO DE OVERLAY ===\n")

    #67
    #listaLayers = ["equipo67/layer01", "equipo67/layer02", "equipo67/layer03"]
    
    #alcaraz
    #listaLayers = ["equipoALCARAZ/layer01", "equipoALCARAZ/layer02", "equipoALCARAZ/layer03", "equipoALCARAZ/layer04", "equipoALCARAZ/layer05"]
    #listaLayers = ["equipoALCARAZ/layer01", "equipoALCARAZ/layer02"]
    #listaLayers = ["equipoALCARAZ/layer03", "equipoALCARAZ/layer04"]
    #listaLayers = ["equipoALCARAZ/layer03", "equipoALCARAZ/layer04", "equipoALCARAZ/layer05"]

    #arbol
    #listaLayers = ["equipoARBOL/layer01", "equipoARBOL/layer02", "equipoARBOL/layer03", "equipoARBOL/layer04", "equipoARBOL/layer05"]
   
    #arbusto
    #listaLayers = ["equipoARBUSTO/layerARBUSTO", "equipoARBUSTO/layerARBUSTO2"]
    
    #diego
    #listaLayers = ["equipoDIEGO/caso1_A", "equipoDIEGO/caso1_B"]
    #listaLayers = ["equipoDIEGO/caso2_A", "equipoDIEGO/caso2_B"]
    #listaLayers = ["equipoDIEGO/caso1_A", "equipoDIEGO/caso1_B", "equipoDIEGO/caso2_A", "equipoDIEGO/caso2_B"]
    
    #falacia del costo hundido
    #listaLayers = ["equipoFALACIADELCOSTOHUNDIDO/layer01", "equipoFALACIADELCOSTOHUNDIDO/layer02", "equipoFALACIADELCOSTOHUNDIDO/layer03"]
    
    #misticos
    #listaLayers = ["equipoMISTICOS/layer01", "equipoMISTICOS/layer02", "equipoMISTICOS/layer03", "equipoMISTICOS/layer04", "equipoMISTICOS/layer05", "equipoMISTICOS/layer06"]
    
    #morenos
    #listaLayers = ["equipoMORENOS/layer01", "equipoMORENOS/layer02", "equipoMORENOS/layer03", "equipoMORENOS/layer04"]
    
    #omar y dubin
    #listaLayers = ["equipoOMARYDUBIN/layer01", "equipoOMARYDUBIN/layer02", "equipoOMARYDUBIN/layer03", "equipoOMARYDUBIN/layer04", "equipoOMARYDUBIN/layer05", "equipoOMARYDUBIN/layer06"]
    
    #pythones
    #listaLayers = ["equipoPYTHONES/layer11", "equipoPYTHONES/layer12", "equipoPYTHONES/layer13", "equipoPYTHONES/layer14", "equipoPYTHONES/layer15"]
    
    #sia
    #listaLayers = ["equipoSIA/layer01SIA"]
    #listaLayers = ["equipoSIA/layer02SIA"]
    #listaLayers = ["equipoSIA/layer01SIA", "equipoSIA/layer02SIA"]
    
    #soto
    #listaLayers = ["equipoSOTO/layerSoto1", "equipoSOTO/layerSoto2", "equipoSOTO/layerSoto3"]



    todos_los_segmentos = []
    todas_las_caras_originales = []
    activas_originales = set()

    # Leer cada capa e ir detectando intersecciones incrementalmente
    for layer in listaLayers:
        print(f"Cargando {layer}...")
        _, aris, caras, activas = cargar_layer(layer)
        segs_nuevos = extraer_segmentos(aris, layer)

        # Cruzar los segmentos del layer recién cargado contra todos los anteriores
        DEBUG_LOG.write(f"\n--- Intersecciones incrementales: {layer} vs segmentos previos ({len(todos_los_segmentos)}) ---\n")
        for s_nuevo in segs_nuevos:
            for s_prev in todos_los_segmentos:
                inters = interseccion_segmentos(s_nuevo, s_prev)
                if inters:
                    DEBUG_LOG.write(
                        f"  {s_nuevo.nombre} ({layer}) ∩ {s_prev.nombre} ({s_prev.layer}): "
                        f"{[(round(p.x,6), round(p.y,6)) for p in inters]}\n"
                    )
                for p in inters:
                    if not any(puntos_iguales(p, q) for q in s_nuevo.intersecciones):
                        s_nuevo.intersecciones.append(p)
                    if not any(puntos_iguales(p, q) for q in s_prev.intersecciones):
                        s_prev.intersecciones.append(p)

        # También detectar intersecciones internas dentro del layer recién cargado
        DEBUG_LOG.write(f"\n--- Intersecciones internas: {layer} ({len(segs_nuevos)} segmentos) ---\n")
        n = len(segs_nuevos)
        for i in range(n):
            for j in range(i + 1, n):
                inters = interseccion_segmentos(segs_nuevos[i], segs_nuevos[j])
                if inters:
                    DEBUG_LOG.write(
                        f"  {segs_nuevos[i].nombre} ∩ {segs_nuevos[j].nombre}: "
                        f"{[(round(p.x,6), round(p.y,6)) for p in inters]}\n"
                    )
                for p in inters:
                    if not any(puntos_iguales(p, q) for q in segs_nuevos[i].intersecciones):
                        segs_nuevos[i].intersecciones.append(p)
                    if not any(puntos_iguales(p, q) for q in segs_nuevos[j].intersecciones):
                        segs_nuevos[j].intersecciones.append(p)

        todos_los_segmentos.extend(segs_nuevos)

        for c in caras:
            if c.nombre in activas:
                activas_originales.add(c.nombre)
            todas_las_caras_originales.append(c)

    DEBUG_LOG.write(f"\nTotal de segmentos originales: {len(todos_los_segmentos)}\n")

    # Visualización 1 (opcional)
    visualizar_capas_originales(listaLayers, todas_las_caras_originales)

    # 2. Partir segmentos  ← ya NO se llama detectar_intersecciones() aquí
    nuevos_segmentos = partir_segmentos(todos_los_segmentos)

    # *** NUEVO: Unificar segmentos colineales ***
    nuevos_segmentos = unificar_segmentos_colineales(nuevos_segmentos)

    # 3. Reconstruir DCEL
    vertices = crear_vertices(nuevos_segmentos)
    aristas = crear_aristas(nuevos_segmentos, vertices)
    conectar_aristas(vertices, aristas)

    for e in aristas:
        if e.verticeOriginal.aristaAdyacente is None:
            e.verticeOriginal.aristaAdyacente = e

# ---- NUEVAS VISUALIZACIONES ----
    visualizar_vertices_dcel(vertices)
    visualizar_aristas_dcel(aristas)


    # ---- Verificar aristas sin cara después de conectar ----
    for a in aristas:
        if a.siguiente is None or a.anterior is None:
            print(f"¡Arista {a.nombre} tiene siguiente o anterior None!")
    # 4. Crear caras finitas
    caras_finitas = crear_caras(aristas)
    # 5. Cara infinita
    crear_cara_infinita(aristas, caras_finitas)

    DEBUG_LOG.write(f"\n=== RESUMEN FINAL ===\n")
    DEBUG_LOG.write(f"Vértices totales: {len(vertices)}\n")
    DEBUG_LOG.write(f"Aristas totales (half‑edges): {len(aristas)}\n")
    DEBUG_LOG.write(f"Caras totales (incluyendo f0): {len(caras_finitas)}\n")
    for v in vertices:
        DEBUG_LOG.write(f"  Vértice {v.nombre}: ({v.coordenadas.x}, {v.coordenadas.y}) incidente={v.aristaAdyacente.nombre if v.aristaAdyacente else 'None'}\n")
    for a in aristas:
        DEBUG_LOG.write(f"  Arista {a.nombre}: orig={a.verticeOriginal.nombre if a.verticeOriginal else '?'} pareja={a.pareja.nombre if a.pareja else '?'} cara={a.cara.nombre if a.cara else '?'} sig={a.siguiente.nombre if a.siguiente else '?'} ant={a.anterior.nombre if a.anterior else '?'}\n")
    for c in caras_finitas:
        DEBUG_LOG.write(f"  Cara {c.nombre}: externo={c.aristasExternos.nombre if c.aristasExternos else 'None'} internos={[e.nombre for e in c.aristasInternos]}\n")

    # 6. Clasificar caras activas (se puede añadir debug si se desea)
    # (se mantiene la clasificación sin cambios)
    poligonos_activos = []
    for c in todas_las_caras_originales:
        if c.nombre not in activas_originales:
            continue
        # 1. Si tiene arista exterior, usamos ese ciclo
        if c.aristasExternos is not None:
            pts = []
            inicio = c.aristasExternos
            actual = inicio
            while actual:
                pts.append(actual.verticeOriginal.coordenadas)
                actual = actual.siguiente
                if actual == inicio or actual is None:
                    break
            if len(pts) >= 3:
                poligonos_activos.append(pts)
        # 2. Si no tiene exterior pero tiene ciclos internos (agujeros activos)
        else:
            for a_int in c.aristasInternos:
                pts = []
                inicio = a_int
                actual = inicio
                while actual:
                    pts.append(actual.verticeOriginal.coordenadas)
                    actual = actual.siguiente
                    if actual == inicio or actual is None:
                        break
                if len(pts) >= 3:
                    poligonos_activos.append(pts)

    def punto_en_poligono(pt, poly):
        x, y = pt.x, pt.y
        inside = False
        n = len(poly)
        for i in range(n):
            j = (i+1)%n
            xi, yi = poly[i].x, poly[i].y
            xj, yj = poly[j].x, poly[j].y
            intersect = ((yi > y) != (yj > y)) and (x < (xj-xi)*(y-yi)/(yj-yi+1e-9) + xi)
            if intersect:
                inside = not inside
        return inside

    def punto_prueba_cara(cara):
        if cara.aristasExternos is None:
            return None
        p1 = cara.aristasExternos.verticeOriginal.coordenadas
        p2 = cara.aristasExternos.siguiente.verticeOriginal.coordenadas
        medio = Punto((p1.x+p2.x)/2, (p1.y+p2.y)/2)
        dx = p2.x - p1.x
        dy = p2.y - p1.y
        nx = -dy
        ny = dx
        length = math.hypot(nx, ny)
        if length > 1e-9:
            nx /= length
            ny /= length
        eps = 1e-4
        return Punto(medio.x + nx*eps, medio.y + ny*eps)

    caras_activas = []
    for c in caras_finitas:
        if c.nombre == "f0":
            continue
        pt = punto_prueba_cara(c)
        if pt is None:
            continue
        activa = False
        for poly in poligonos_activos:
            if punto_en_poligono(pt, poly):
                activa = True
                break
        if activa:
            caras_activas.append(c.nombre)

    DEBUG_LOG.write(f"\nCaras activas finales: {caras_activas}\n")

    # 7. Exportar
    exportar_resultado(vertices, aristas, caras_finitas, caras_activas, "resultados/resultado")

    print("Proceso completado. Archivos exportados y debug escrito en debug/debug_overlay.log")

    DEBUG_LOG.close()   # Cerrar archivo de debug

    # Visualizaciones (se mantienen)
    visualizar_resultado_final(vertices, aristas, caras_finitas)
    # Sustituye la llamada a Pygame
    visualizar_resultado_interactivo(vertices, aristas, caras_finitas, caras_activas)

if __name__ == "__main__":
    main()