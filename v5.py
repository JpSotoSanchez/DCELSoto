# =============================================================================
# main_adaptado_con_pygame.py
# =============================================================================
# Versión que usa el algoritmo SIMPLE del código combinado (overlay_figuras)
# más visualización interactiva con Pygame (click para activar/desactivar caras)
# =============================================================================

import math
import random
import os
import sys
import heapq
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional, List, Set, Tuple

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.cm as cm
from matplotlib.patches import Polygon
import numpy as np
import pygame

# ------------------------------------------------
# 1. CLASES GEOMÉTRICAS Y DCEL (simplificadas)
# ------------------------------------------------

@dataclass(frozen=True)
class Punto:
    x: float
    y: float

    def distancia(self, otro: "Punto") -> float:
        return math.hypot(self.x - otro.x, self.y - otro.y)


class SegmentoOverlay:
    """Segmento auxiliar para overlay (similar al del código combinado)"""
    def __init__(self, nombre, p1, p2, layer):
        self.nombre = nombre
        self.p1 = p1
        self.p2 = p2
        self.layer = layer
        self.intersecciones = []   # lista de Puntos

    def __repr__(self):
        return f"Seg({self.nombre}, {self.layer})"


class NodoVertice:
    def __init__(self, nombre, coordenadas):
        self.nombre = nombre
        self.coordenadas = coordenadas
        self.aristaAdyacente = None   # arista incidente

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
        self.aristasInternos = []     # lista de aristas que inician huecos
        self.aristasExternos = None   # arista del borde exterior


# ------------------------------------------------
# 2. FUNCIONES GEOMÉTRICAS (iguales al combinado)
# ------------------------------------------------

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

def interseccion_segmentos(s1: SegmentoOverlay, s2: SegmentoOverlay):
    """Retorna lista de puntos de intersección (0, 1 o 2)"""
    p1, p2 = s1.p1, s1.p2
    q1, q2 = s2.p1, s2.p2

    # Usar la misma función que en overlay_figuras
    den = (p1.x - p2.x)*(q1.y - q2.y) - (p1.y - p2.y)*(q1.x - q2.x)
    if abs(den) < EPS:
        # Colineales -> posible solapamiento
        # Simplificación: solo consideramos intersecciones puntuales en extremos
        # Para el overlay completo se necesitaría manejar superposición, pero aquí asumimos segmentos de diferentes capas
        return []
    
    t = ((p1.x - q1.x)*(q1.y - q2.y) - (p1.y - q1.y)*(q1.x - q2.x)) / den
    u = ((p1.x - q1.x)*(p1.y - p2.y) - (p1.y - q1.y)*(p1.x - p2.x)) / den

    if 0 <= t <= 1 and 0 <= u <= 1:
        x = p1.x + t*(p2.x - p1.x)
        y = p1.y + t*(p2.y - p1.y)
        return [Punto(x, y)]
    return []


# ------------------------------------------------
# 3. LECTURA DE CAPAS (igual que en main.py original)
# ------------------------------------------------

def cargar_layer(layer_name: str):
    """Lee los archivos .vertices, .aristas, .caras, .activos de una capa"""
    vertices = []
    aristas = []
    caras = []
    activas = set()

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
    except FileNotFoundError:
        print(f"Advertencia: no se encontró {layer_name}.vertices")

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
                    a.verticeOriginal = origen + layer_name
                    a.pareja = pareja + layer_name
                    a.cara = cara + layer_name
                    a.siguiente = sig + layer_name
                    a.anterior = ant + layer_name
                    aristas.append(a)
    except FileNotFoundError:
        print(f"Advertencia: no se encontró {layer_name}.aristas")

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
                    # interno puede ser "[e1,e2]" o "None"
                    if interno != "None":
                        interno = interno.strip("[]")
                        if interno:
                            c.aristasInternos = [x.strip() + layer_name for x in interno.split(",") if x.strip()]
                    if externo != "None":
                        c.aristasExternos = externo + layer_name
                    caras.append(c)
    except FileNotFoundError:
        print(f"Advertencia: no se encontró {layer_name}.caras")

    # Activos
    try:
        with open(f"{layer_name}.activos", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and not line.startswith("Archivo") and not line.startswith("Caras"):
                    activas.add(line + layer_name)
    except FileNotFoundError:
        pass

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

    for v in vertices:
        if isinstance(v.aristaAdyacente, str):
            v.aristaAdyacente = dict_aristas.get(v.aristaAdyacente)

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

    return vertices, aristas, caras, activas


# ------------------------------------------------
# 4. ALGORITMO DE OVERLAY (copiado del combinado)
# ------------------------------------------------

def extraer_segmentos(aristas, layer_id):
    """Extrae segmentos de una lista de aristas DCEL"""
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
    return segmentos

def detectar_intersecciones(segmentos):
    """Fuerza bruta O(n²) - igual que el combinado"""
    n = len(segmentos)
    for i in range(n):
        for j in range(i+1, n):
            inters = interseccion_segmentos(segmentos[i], segmentos[j])
            for p in inters:
                if not any(puntos_iguales(p, q) for q in segmentos[i].intersecciones):
                    segmentos[i].intersecciones.append(p)
                if not any(puntos_iguales(p, q) for q in segmentos[j].intersecciones):
                    segmentos[j].intersecciones.append(p)

def partir_segmentos(segmentos):
    """Divide cada segmento por sus puntos de intersección"""
    nuevos = []
    contador = 0
    for s in segmentos:
        puntos = [s.p1]
        for p in s.intersecciones:
            if not puntos_iguales(p, s.p1) and not puntos_iguales(p, s.p2):
                puntos.append(p)
        puntos.append(s.p2)
        puntos.sort(key=lambda pt: parametro_segmento(s, pt))
        for i in range(len(puntos)-1):
            a, b = puntos[i], puntos[i+1]
            if puntos_iguales(a, b):
                continue
            ns = SegmentoOverlay(f"g{contador}", a, b, s.layer)
            nuevos.append(ns)
            contador += 1
    return nuevos

def crear_vertices(segmentos):
    """Crea NodoVertice a partir de los extremos de los segmentos"""
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
        return nombre
    for s in segmentos:
        obtener_nombre(s.p1)
        obtener_nombre(s.p2)
    return list(vertices.values())

def crear_aristas(segmentos, vertices):
    """Crea half-edges para cada segmento"""
    aristas = []
    contador = 1
    # Mapa de coordenadas a objeto vértice
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
    return aristas

def angulo_arista(e: NodoArista) -> float:
    p1 = e.verticeOriginal.coordenadas
    p2 = e.pareja.verticeOriginal.coordenadas
    return math.atan2(p2.y - p1.y, p2.x - p1.x)

def conectar_aristas(vertices, aristas):
    """Ordena las aristas incidentes por ángulo y enlaza siguiente/anterior"""
    incidentes = defaultdict(list)
    for e in aristas:
        incidentes[e.verticeOriginal.nombre].append(e)
    for lista in incidentes.values():
        lista.sort(key=angulo_arista)
    for lista in incidentes.values():
        n = len(lista)
        for i in range(n):
            e = lista[i]
            ant = lista[(i-1)%n]   # anterior en el orden angular
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
    """Recorre ciclos para formar caras"""
    caras = {}
    contador = 1
    for e in aristas:
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
            puntos.append([actual.verticeOriginal.coordenadas.x, actual.verticeOriginal.coordenadas.y])
            actual = actual.siguiente
            if actual == e:
                break
        if len(ciclo) < 3:
            continue
        area = area_poligono(puntos)
        if area <= EPS:
            continue
        c = NodoCara(f"f{contador}")
        contador += 1
        c.aristasExternos = ciclo[0]
        for ar in ciclo:
            ar.cara = c
        caras[c.nombre] = c
    return list(caras.values())

def crear_cara_infinita(aristas, caras):
    """Asigna la cara infinita (f0) a las aristas que no tienen cara"""
    f0 = NodoCara("f0")
    usadas = set()
    for e in aristas:
        if e.cara is None:
            e.cara = f0
            if e.nombre not in usadas:
                f0.aristasInternos.append(e)
                usadas.add(e.nombre)
    caras.append(f0)

def exportar_resultado(vertices, aristas, caras, caras_activas_nombres, base="resultado"):
    """Exporta archivos .vertices, .aristas, .caras, .activos"""
    # Vértices
    with open(base + ".vertices", "w", encoding="utf-8") as f:
        f.write("Archivo de vértices\n#################################\nNombre  x       y       Incidente\n#################################\n")
        for v in vertices:
            inc = v.aristaAdyacente.nombre if v.aristaAdyacente else "None"
            f.write(f"{v.nombre} {v.coordenadas.x:.6f} {v.coordenadas.y:.6f} {inc}\n")
    # Aristas
    with open(base + ".aristas", "w", encoding="utf-8") as f:
        f.write("Archivo de aristas\n#############################################\nNombre  Origen  Pareja  Cara    Sigue   Antes\n#############################################\n")
        for a in aristas:
            origen = a.verticeOriginal.nombre if a.verticeOriginal else "None"
            pareja = a.pareja.nombre if a.pareja else "None"
            cara = a.cara.nombre if a.cara else "None"
            sig = a.siguiente.nombre if a.siguiente else "None"
            ant = a.anterior.nombre if a.anterior else "None"
            f.write(f"{a.nombre} {origen} {pareja} {cara} {sig} {ant}\n")
    # Caras
    with open(base + ".caras", "w", encoding="utf-8") as f:
        f.write("Archivo de caras\n#######################\nNombre  Interno Externo\n#######################\n")
        for c in caras:
            interno = "[" + ",".join([e.nombre for e in c.aristasInternos]) + "]"
            externo = c.aristasExternos.nombre if c.aristasExternos else "None"
            f.write(f"{c.nombre} {interno} {externo}\n")
    # Activos
    with open(base + ".activos", "w", encoding="utf-8") as f:
        f.write("Archivo de activos\n#######################\nCaras Activas\n#######################\n")
        for nombre in caras_activas_nombres:
            f.write(f"{nombre}\n")
    print(f"Exportado a {base}.*")


# ------------------------------------------------
# 5. VISUALIZACIÓN CON PYGAME (adaptada del original)
# ------------------------------------------------

def visualizar_pygame(vertices, aristas, caras, caras_activas_inicial):
    """
    Muestra la DCEL resultante con Pygame.
    Permite clickear caras para activarlas/desactivarlas.
    """
    pygame.init()
    
    # Configuración de ventana
    WIDTH, HEIGHT = 1200, 800
    BACKGROUND = (25, 25, 25)
    COLOR_ARISTA = (220, 220, 220)
    COLOR_VERTICE = (255, 255, 255)
    COLOR_INTERSECCION = (255, 80, 80)   # no usado realmente aquí
    COLOR_CARA_ACTIVA = (30, 144, 255)    # azul
    COLOR_CARA_INACTIVA = (70, 70, 70)    # gris
    COLOR_INF_ACTIVA = (20, 60, 100)      # fondo azul oscuro (infinita)
    COLOR_INF_INACTIVA = (35, 35, 45)     # fondo gris oscuro
    
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("DCEL Interactiva - Overlay Simple")
    clock = pygame.time.Clock()
    
    # Calcular bounding box de todos los vértices
    all_x = [v.coordenadas.x for v in vertices]
    all_y = [v.coordenadas.y for v in vertices]
    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)
    padding = 50
    world_w = max_x - min_x
    world_h = max_y - min_y
    scale_x = (WIDTH - 2 * padding) / world_w if world_w != 0 else 1
    scale_y = (HEIGHT - 2 * padding) / world_h if world_h != 0 else 1
    scale = min(scale_x, scale_y)
    
    def world_to_screen(p: Punto):
        sx = (p.x - min_x) * scale + padding
        sy = HEIGHT - ((p.y - min_y) * scale + padding)
        return (int(sx), int(sy))
    
    # Obtener polígono de una cara (lista de puntos en pantalla)
    def face_polygon(cara):
        if cara.aristasExternos is None:
            return []
        pts = []
        inicio = cara.aristasExternos
        actual = inicio
        visitadas = set()
        while actual and id(actual) not in visitadas:
            visitadas.add(id(actual))
            pts.append(world_to_screen(actual.verticeOriginal.coordenadas))
            actual = actual.siguiente
            if actual == inicio:
                break
        return pts
    
    # Estado de caras activas (convertimos a set para búsqueda rápida)
    # Nota: caras_activas_inicial es una lista de nombres (strings)
    caras_activas = set(caras_activas_inicial)
    
    # Función para determinar si un punto de pantalla está dentro de un polígono (ray casting)
    def point_in_polygon(px, py, polygon):
        inside = False
        n = len(polygon)
        for i in range(n):
            x1, y1 = polygon[i]
            x2, y2 = polygon[(i+1) % n]
            # Chequeo de cruce horizontal
            if ((y1 > py) != (y2 > py)) and (px < (x2 - x1) * (py - y1) / (y2 - y1 + 1e-9) + x1):
                inside = not inside
        return inside
    
    # Loop principal
    running = True
    while running:
        clock.tick(60)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                # Buscar la cara más pequeña (para evitar que la infinita tape todo)
                # Ordenar caras por área aproximada (menor área primero)
                def area_cara_aprox(cara):
                    if cara.aristasExternos is None:
                        return float('inf')
                    pts = face_polygon(cara)
                    if len(pts) < 3:
                        return float('inf')
                    # Área en píxeles (aproximada)
                    area = 0.0
                    n = len(pts)
                    for i in range(n):
                        x1, y1 = pts[i]
                        x2, y2 = pts[(i+1)%n]
                        area += x1*y2 - x2*y1
                    return abs(area) / 2.0
                
                # Excluir la cara infinita (f0) de la selección
                caras_finitas = [c for c in caras if c.nombre != "f0"]
                caras_finitas.sort(key=area_cara_aprox)  # más pequeñas primero (para clicks precisos)
                
                clicked_cara = None
                for c in caras_finitas:
                    poly = face_polygon(c)
                    if len(poly) >= 3 and point_in_polygon(mx, my, poly):
                        clicked_cara = c
                        break
                
                if clicked_cara is not None:
                    if clicked_cara.nombre in caras_activas:
                        caras_activas.remove(clicked_cara.nombre)
                    else:
                        caras_activas.add(clicked_cara.nombre)
                    print(f"Toggle cara {clicked_cara.nombre} -> activas: {sorted(caras_activas)}")
        
        # Dibujar
        screen.fill(BACKGROUND)
        
        # 1. Dibujar la cara infinita (f0) como fondo
        cara_infinita = next((c for c in caras if c.nombre == "f0"), None)
        if cara_infinita:
            # La cara infinita se representa con el rectángulo que cubre toda la pantalla
            # pero también tiene agujeros (aristasInternos). Para simplificar, dibujamos un rectángulo
            # que cubra toda la pantalla y luego dibujamos las caras finitas encima.
            # En lugar de eso, podemos pintar el fondo según si f0 está "activa"? En el original se pintaba.
            # Aquí pintamos un rectángulo grande que cubra la vista, con un color que represente si la cara infinita está activa.
            # Como la cara infinita no se puede activar/desactivar realmente, usamos un color neutro.
            # Usaremos el color de fondo para las aristas, pero es más limpio dibujar un rectángulo.
            # Omitimos el relleno de la cara infinita, ya que las caras finitas la cubrirán.
            pass
        
        # 2. Dibujar caras finitas (de mayor área a menor para que las pequeñas estén encima si hay solapamiento)
        # Para que el click funcione bien, el orden de dibujo no afecta la detección.
        # Pero para que se vean bien, dibujamos primero las más grandes (normalmente la infinita).
        caras_finitas = [c for c in caras if c.nombre != "f0"]
        # Ordenar por área descendente para que las más grandes (como el fondo) se dibujen primero
        def area_cara_mundo(cara):
            if cara.aristasExternos is None:
                return 0.0
            pts = []
            inicio = cara.aristasExternos
            actual = inicio
            while actual:
                pts.append(actual.verticeOriginal.coordenadas)
                actual = actual.siguiente
                if actual == inicio:
                    break
            return abs(area_poligono([(p.x, p.y) for p in pts]))
        
        caras_finitas.sort(key=area_cara_mundo, reverse=True)
        
        for c in caras_finitas:
            poly = face_polygon(c)
            if len(poly) < 3:
                continue
            activa = c.nombre in caras_activas
            color = COLOR_CARA_ACTIVA if activa else COLOR_CARA_INACTIVA
            # Rellenar
            pygame.draw.polygon(screen, color, poly)
            # Borde
            pygame.draw.polygon(screen, COLOR_ARISTA, poly, width=2)
        
        # 3. Dibujar aristas (líneas)
        aristas_vistas = set()
        for a in aristas:
            if a.nombre in aristas_vistas:
                continue
            aristas_vistas.add(a.nombre)
            aristas_vistas.add(a.pareja.nombre)
            p1 = world_to_screen(a.verticeOriginal.coordenadas)
            p2 = world_to_screen(a.pareja.verticeOriginal.coordenadas)
            pygame.draw.line(screen, COLOR_ARISTA, p1, p2, 2)
        
        # 4. Dibujar vértices
        for v in vertices:
            p = world_to_screen(v.coordenadas)
            pygame.draw.circle(screen, COLOR_VERTICE, p, 4)
        
        pygame.display.flip()
    
    pygame.quit()


# ------------------------------------------------
# 6. FUNCIÓN PRINCIPAL
# ------------------------------------------------

def main():
    # Capas a cargar (igual que en el main original)
    listaLayers = ["layer03", "layer04", "layer05", "layer01", "layer02"]
    todos_los_segmentos = []
    todas_las_caras_originales = []   # para recordar qué caras estaban activas
    activas_originales = set()

    # Leer cada capa
    for layer in listaLayers:
        print(f"Cargando {layer}...")
        verts, aris, caras, activas = cargar_layer(layer)
        segs = extraer_segmentos(aris, layer)
        todos_los_segmentos.extend(segs)
        # Guardar qué caras estaban activas (para después clasificar)
        for c in caras:
            if c.nombre in activas:
                activas_originales.add(c.nombre)
            todas_las_caras_originales.append(c)

    print(f"Segmentos totales: {len(todos_los_segmentos)}")

    # 1. Detectar intersecciones (fuerza bruta)
    detectar_intersecciones(todos_los_segmentos)

    # 2. Partir segmentos
    nuevos_segmentos = partir_segmentos(todos_los_segmentos)
    print(f"Segmentos después de partir: {len(nuevos_segmentos)}")

    # 3. Reconstruir DCEL
    vertices = crear_vertices(nuevos_segmentos)
    aristas = crear_aristas(nuevos_segmentos, vertices)
    conectar_aristas(vertices, aristas)

    # Asignar arista incidente a cada vértice (cualquiera que salga)
    for e in aristas:
        if e.verticeOriginal.aristaAdyacente is None:
            e.verticeOriginal.aristaAdyacente = e

    # 4. Crear caras finitas
    caras_finitas = crear_caras(aristas)
    # 5. Crear cara infinita
    crear_cara_infinita(aristas, caras_finitas)

    print(f"Caras resultantes: {len(caras_finitas)}")

    # 6. Clasificar qué caras son activas (usando punto interior)
    # Recolectamos polígonos de las caras originales que estaban activas
    poligonos_activos = []
    for c in todas_las_caras_originales:
        if c.nombre not in activas_originales:
            continue
        if c.aristasExternos is None:
            continue
        # Obtener ciclo exterior
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

    def punto_en_poligono(pt, poly):
        """Ray casting"""
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
        """Genera un punto interior de la cara usando el punto medio de la primera arista"""
        if cara.aristasExternos is None:
            return None
        p1 = cara.aristasExternos.verticeOriginal.coordenadas
        p2 = cara.aristasExternos.siguiente.verticeOriginal.coordenadas
        medio = Punto((p1.x+p2.x)/2, (p1.y+p2.y)/2)
        # Vector interior: asumimos polígono CCW, interior a la izquierda
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

    # 7. Exportar resultados
    exportar_resultado(vertices, aristas, caras_finitas, caras_activas, "resultado_simple")

    print("Proceso completado. Archivos exportados.")

    # 8. Visualizar con Pygame
    visualizar_pygame(vertices, aristas, caras_finitas, caras_activas)


if __name__ == "__main__":
    main()