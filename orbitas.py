import pygame
import math
import sys
import os
import random
import traceback

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"

# ============================================================
# CONFIGURACIÓN
# ============================================================
WIDTH, HEIGHT = 1100, 750
FPS = 60

NEGRO = (8, 8, 20)
AGUA = (40, 120, 200)
TIERRA_FIRME = (180, 140, 50)
PLAYA = (90, 180, 255)
TIERRA_BORDE = (90, 180, 255)

NAVE_VERDE = (60, 230, 90)
NAVE_AZUL = (90, 160, 255)
BLANCO = (240, 240, 240)
GRIS = (140, 140, 150)
AMARILLO = (255, 220, 80)
ROJO = (255, 80, 80)
AZUL_MAR = (80, 160, 255)
CIAN = (0, 255, 255)
AZUL_DESTACADO = (100, 200, 255)
NARANJA = (255, 140, 0)
GANCHO_AMARILLO = (255, 255, 0)

ATMOSFERA_COLOR = (200, 220, 240)
ATMOSFERA_GROSOR = 15

PRED_ELIPTICA = (255, 140, 0)    
PRED_CIRCULAR = (0, 255, 255)    

# ============================================================
# TEXTO INFORMATIVO (Pausa con I)
# ============================================================
TEXTO_INFO = [
    ("ÓRBITAS DE HOHMANN", "titulo"),
    ("", "normal"),
    ("Este juego pretende mostrar didácticamente lo que son las", "normal"),
    ("órbitas elípticas de Hohmann, las que permiten a una nave", "normal"),
    ("pasar de una órbita a otra. Esto incluye el viaje desde", "normal"),
    ("la órbita de un planeta como la Tierra a otra como la de", "normal"),
    ("Marte o, tal y como lo vemos aquí, desde la de una", "normal"),
    ("lanzadera a la de la ISS.", "normal"),
    ("", "normal"),
    ("Lo curioso de estas es que uno tiene que acelerar para", "normal"),
    ("'subir' a una órbita superior en la que irá más lento,", "normal"),
    ("es decir que", "normal"),
    ("¡tiene que acelerar para frenar!", "destacado"),
    ("", "normal"),
    ("De la misma manera, tendrá que frenar para bajar de", "normal"),
    ("órbita donde irá a una mayor velocidad.", "normal"),
    ("Es decir que, nuevamente,", "normal"),
    ("¡hay que frenar para acelerar!", "destacado"),
    ("", "normal"),
    ("", "normal"),
    ("mahler.gustave@gmail.com", "normal"),
]

# ============================================================
# ZONAS DE LA SUPERFICIE
# ============================================================
CONTINENTES_COLISION = [
    (0.5, 0.20),
    (2.2, 0.25),
    (3.8, 0.22),
    (5.2, 0.30),
]

def es_tierra(angulo):
    a = angulo % (2 * math.pi)
    for centro, radio in CONTINENTES_COLISION:
        diff = abs((a - centro + math.pi) % (2 * math.pi) - math.pi)
        if diff < radio:
            return True
    return False

# ============================================================
# ESCALA REAL
# ============================================================
R_PLANETA = 90.0
R_TIERRA_KM = 6371.0
ESCALA_KM_PX = R_TIERRA_KM / R_PLANETA

# ============================================================
# CONSTANTES ORBITALES
# ============================================================
R_VERDE = R_PLANETA + R_PLANETA / 2.0
R_AZUL  = R_PLANETA + R_PLANETA

_T_VERDE = 10.0 * 60.0 
MU = 4 * math.pi**2 * R_VERDE**3 / _T_VERDE**2

V_CIRC_VERDE = math.sqrt(MU / R_VERDE)
DV_TOQUE = V_CIRC_VERDE * 0.03

T_VERDE_REAL = 2 * math.pi * (R_VERDE * ESCALA_KM_PX) / math.sqrt(
    398600.4418 / (R_VERDE * ESCALA_KM_PX)
)
T_VERDE_JUEGO = 600.0
FACTOR_TIEMPO = T_VERDE_REAL / T_VERDE_JUEGO

DV_TOQUE_KM_S = DV_TOQUE * ESCALA_KM_PX / FACTOR_TIEMPO

DT_FISICO = 1.0  
SUBSTEPS = 4

R_ATMOSFERA = R_PLANETA + ATMOSFERA_GROSOR
DURACION_DESPEGUE = 120
DURACION_RESCATE = 90

# ============================================================
# SISTEMA DE PARTÍCULAS
# ============================================================
class Particula:
    def __init__(self, x, y, vx, vy, color, vida_max=25):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.vida = vida_max
        self.vida_max = vida_max
        self.tam = random.uniform(2.5, 4.5)
    
    def actualizar(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vx *= 0.94
        self.vy *= 0.94
        self.vida -= 1
        self.tam *= 0.92

    def dibujar(self, surf):
        if self.vida <= 0: return
        alpha = max(0, min(255, int(255 * (self.vida / self.vida_max))))
        radio = max(1, int(self.tam))
        temp = pygame.Surface((radio*2, radio*2), pygame.SRCALPHA)
        pygame.draw.circle(temp, (*self.color, alpha), (radio, radio), radio)
        surf.blit(temp, (int(self.x) - radio, int(self.y) - radio))

def emitir_estela(particulas, nave, cx, cy, tipo, cantidad=18):
    if nave.aterrizada or nave.estrellada or nave.perdida: return
    if nave.hundiendose and tipo != "despegue": return
    x, y = nave.posicion(cx, cy)
    
    ang_nave = nave.angulo + math.pi / 2
    
    if tipo == "fuego":
        ang_escape = ang_nave + math.pi
        offset = 10
    elif tipo == "despegue" or tipo == "rescate":
        ang_escape = ang_nave + math.pi
        offset = 12
    elif tipo == "friccion":
        ang_escape = random.uniform(0, 2 * math.pi)
        offset = 5
    else: # hielo
        ang_escape = ang_nave
        offset = 10
        
    origen_x = x + offset * math.cos(ang_escape)
    origen_y = y + offset * math.sin(ang_escape)
        
    for i in range(cantidad):
        ang_p = ang_escape + random.uniform(-0.45, 0.45)
        velocidad = random.uniform(1.5, 3.5)
        vx = velocidad * math.cos(ang_p)
        vy = velocidad * math.sin(ang_p)
        
        if tipo == "fuego":
            r = random.randint(220, 255); g = random.randint(80, 180); b = random.randint(0, 40)
        elif tipo == "friccion":
            c = random.randint(180, 220); r, g, b = c, c, c
        elif tipo == "despegue" or tipo == "rescate":
            r = 255; g = random.randint(150, 220); b = random.randint(0, 80)
        else:
            r = random.randint(80, 140); g = random.randint(180, 230); b = 255
            
        p = Particula(origen_x, origen_y, vx, vy, (r, g, b))
        particulas.append(p)

# ============================================================
# CLASE NAVE
# ============================================================
class Nave:
    def __init__(self, radio, color, angulo_inicial, nombre):
        self.radio_orbita = radio
        self.color = color
        self.angulo = angulo_inicial
        self.nombre = nombre
        self.radio_actual = radio
        self.vr = 0.0
        self.va = math.sqrt(MU / radio)
        self.dv_acumulado = 0.0
        self.aterrizada = False
        self.estrellada = False
        self.perdida = False
        self.acoplada = False
        
        self.fase_desacople = 0
        self.desacople_timer = 0
        
        self.en_atmosfera = False
        self.aterrizaje_automatico = False
        self.vel_vertical_aterrizaje_px = 0.0
        self.tiempo_proteccion = 0
        
        self.despegando = False
        self.despegue_timer = 0
        self.despegue_radio_inicial = 0
        self.despegue_angulo_inicial = 0
        self.rescatando = False
        
        self.amerizo = False
        
        self.hundiendose = False
        self.hundimiento_timer = 0
        self.hundimiento_angulo_original = 0
        self.hundimiento_fase = 1

    def posicion(self, cx, cy):
        return cx + self.radio_actual * math.cos(self.angulo), \
               cy + self.radio_actual * math.sin(self.angulo)

    def sincronizar_cartesiano(self, cx, cy):
        x, y = self.posicion(cx, cy)
        ux, uy = math.cos(self.angulo), math.sin(self.angulo)
        tx, ty = -uy, ux
        vx = self.va * tx + self.vr * ux
        vy = self.va * ty + self.vr * uy
        return x, y, vx, vy

    def iniciar_despegue(self):
        self.despegando = True
        self.despegue_timer = 0
        self.despegue_radio_inicial = self.radio_actual
        self.despegue_angulo_inicial = self.angulo
        self.aterrizada = False
        self.estrellada = False
        self.en_atmosfera = False
        self.aterrizaje_automatico = False
        self.vel_vertical_aterrizaje_px = 0.0
        self.tiempo_proteccion = 0
        self.va = 0.0
        self.vr = 0.0
        self.angulo = self.despegue_angulo_inicial

    def iniciar_rescate(self):
        self.rescatando = True
        self.hundiendose = False
        self.despegue_timer = 0
        self.despegue_radio_inicial = self.radio_actual
        self.despegue_angulo_inicial = self.angulo
        self.aterrizada = False
        self.estrellada = False
        self.en_atmosfera = False
        self.aterrizaje_automatico = False
        self.vel_vertical_aterrizaje_px = 0.0
        self.tiempo_proteccion = 0
        self.va = 0.0
        self.vr = 0.0
        self.angulo = self.despegue_angulo_inicial

    def actualizar_despegue(self, dt, particulas, cx, cy):
        if not self.despegando: return
        self.despegue_timer += 1
        t = min(1.0, self.despegue_timer / DURACION_DESPEGUE)
        
        curva = 1 - (1 - t)**2 
        
        self.radio_actual = self.despegue_radio_inicial + \
                            (self.radio_orbita - self.despegue_radio_inicial) * curva
        
        avance_angular = math.radians(30) * curva
        self.angulo = self.despegue_angulo_inicial + avance_angular
        
        if random.random() < 0.9 and t < 0.95:
            emitir_estela(particulas, self, cx, cy, "despegue", cantidad=3)
        
        if self.despegue_timer >= DURACION_DESPEGUE:
            self.despegando = False
            self.radio_actual = self.radio_orbita
            self.va = math.sqrt(MU / self.radio_orbita)
            self.vr = 0.0
            self.dv_acumulado = 0.0
            self.tiempo_proteccion = 30

    def actualizar_rescate(self, dt, particulas, cx, cy):
        if not self.rescatando: return
        self.despegue_timer += 1
        t = min(1.0, self.despegue_timer / DURACION_RESCATE)
        
        curva = 1 - (1 - t)**3 
        
        self.radio_actual = self.despegue_radio_inicial + \
                            (self.radio_orbita - self.despegue_radio_inicial) * curva
        
        if random.random() < 0.95 and t < 0.95:
            emitir_estela(particulas, self, cx, cy, "rescate", cantidad=4)
        
        if self.despegue_timer >= DURACION_RESCATE:
            self.rescatando = False
            self.radio_actual = self.radio_orbita
            self.va = math.sqrt(MU / self.radio_orbita)
            self.vr = 0.0
            self.dv_acumulado = 0.0
            self.tiempo_proteccion = 30
            self.aterrizada = False

# ============================================================
# FÍSICA
# ============================================================
def derivadas(x, y, vx, vy):
    r = math.hypot(x, y)
    if r < 1e-6: return vx, vy, 0.0, 0.0
    a = -MU / (r**3)
    return vx, vy, a * x, a * y

def paso_rk4(x, y, vx, vy, dt):
    k1x, k1y, k1vx, k1vy = derivadas(x, y, vx, vy)
    k2x, k2y, k2vx, k2vy = derivadas(x + 0.5*dt*k1x, y + 0.5*dt*k1y, vx + 0.5*dt*k1vx, vy + 0.5*dt*k1vy)
    k3x, k3y, k3vx, k3vy = derivadas(x + 0.5*dt*k2x, y + 0.5*dt*k2y, vx + 0.5*dt*k2vx, vy + 0.5*dt*k2vy)
    k4x, k4y, k4vx, k4vy = derivadas(x + dt*k3x, y + dt*k3y, vx + dt*k3vx, vy + dt*k3vy)
    x  += dt/6*(k1x  + 2*k2x  + 2*k3x  + k4x)
    y  += dt/6*(k1y  + 2*k2y  + 2*k3y  + k4y)
    vx += dt/6*(k1vx + 2*k2vx + 2*k3vx + k4vx)
    vy += dt/6*(k1vy + 2*k2vy + 2*k3vy + k4vy)
    return x, y, vx, vy

def calcular_elementos_orbitales(verde):
    if verde.en_atmosfera or verde.aterrizaje_automatico or verde.despegando or verde.hundiendose or verde.rescatando: return None
    _, _, vx, vy = verde.sincronizar_cartesiano(0, 0)
    r = verde.radio_actual
    if r < 1.0: return None
    v2 = vx**2 + vy**2
    epsilon = v2 / 2 - MU / r
    h = r * verde.va
    if epsilon >= 0: return None
    e_sq = 1 + (2 * epsilon * h**2) / MU**2
    e = math.sqrt(max(0, e_sq)) 
    a = -MU / (2 * epsilon)
    return {
        "e": e, "a": a,
        "r_apogeo": a * (1 + e), 
        "r_perigeo": a * (1 - e),
        "es_circular": e < 0.02
    }

def actualizar_nave_verde(nave, dt, cx, cy, iss, particulas):
    if nave.aterrizada or nave.estrellada or nave.perdida or nave.despegando or nave.hundiendose or nave.rescatando: return

    if nave.acoplada:
        nave.angulo = iss.angulo
        nave.radio_actual = iss.radio_actual
        nave.va = iss.va
        nave.vr = 0.0
        return

    if nave.en_atmosfera or nave.aterrizaje_automatico:
        if nave.tiempo_proteccion > 0:
            nave.tiempo_proteccion -= 1
        
        altitud_px = nave.radio_actual - R_PLANETA
        if altitud_px <= 0:
            if nave.aterrizaje_automatico and abs(nave.vel_vertical_aterrizaje_px) < 0.3:
                if es_tierra(nave.angulo):
                    nave.aterrizada = True
                else:
                    nave.estrellada = True
                    nave.amerizo = True
                    nave.hundiendose = True
                    nave.hundimiento_timer = 0
                    nave.hundimiento_angulo_original = nave.angulo
                    nave.hundimiento_fase = 1
            elif nave.tiempo_proteccion <= 0:
                nave.estrellada = True
                nave.amerizo = False
            return
        
        g_aterrizaje = MU / (R_PLANETA**2)
        nave.vel_vertical_aterrizaje_px -= g_aterrizaje * dt
        
        if not nave.aterrizaje_automatico:
            friccion_v = 0.03 * nave.vel_vertical_aterrizaje_px
            nave.vel_vertical_aterrizaje_px -= friccion_v * dt
            nave.va *= 0.995
        
        if nave.aterrizaje_automatico:
            if nave.vel_vertical_aterrizaje_px < -0.15:
                nave.vel_vertical_aterrizaje_px += (g_aterrizaje * 2.0) * dt
                if nave.vel_vertical_aterrizaje_px > 0:
                    nave.vel_vertical_aterrizaje_px = 0
            else:
                nave.vel_vertical_aterrizaje_px = -0.15
        
        nave.radio_actual += nave.vel_vertical_aterrizaje_px * dt
        nave.angulo += (nave.va / nave.radio_actual) * dt
        return

    if nave.fase_desacople == 1:
        nave.desacople_timer += 1
        t = nave.desacople_timer / 45.0
        angulo_retroceso = 30.0 / nave.radio_actual
        nave.radio_actual = iss.radio_actual + (t * 30.0)
        nave.angulo = iss.angulo + (t * angulo_retroceso)
        nave.va = iss.va - (t * (iss.va * 0.1))
        nave.vr = 0.0
        if nave.desacople_timer >= 45:
            nave.fase_desacople = 0
            nave.va = iss.va + (iss.va * 0.08) 
        return

    x, y, vx, vy = nave.sincronizar_cartesiano(cx, cy)
    rx, ry = x - cx, y - cy

    for _ in range(SUBSTEPS):
        rx, ry, vx, vy = paso_rk4(rx, ry, vx, vy, dt / SUBSTEPS)

    r = math.hypot(rx, ry)
    if r > 5000:
        nave.perdida = True
        return

    nave.radio_actual = r
    nave.angulo = math.atan2(ry, rx)

    ux, uy = rx / r, ry / r
    tx, ty = -uy, ux
    nave.vr = vx * ux + vy * uy
    nave.va = vx * tx + vy * ty

    if r <= R_ATMOSFERA and not nave.en_atmosfera:
        nave.en_atmosfera = True
        nave.vel_vertical_aterrizaje_px = nave.vr * 0.3
        nave.tiempo_proteccion = 60
        return

    if r <= R_PLANETA:
        if nave.tiempo_proteccion <= 0:
            nave.estrellada = True
            nave.amerizo = False
        nave.radio_actual = R_PLANETA

def aplicar_delta_v(nave, signo, iss, cx, cy):
    if nave.aterrizada or nave.estrellada or nave.perdida or nave.hundiendose or nave.rescatando: return
    if nave.en_atmosfera or nave.aterrizaje_automatico or nave.despegando: return
    
    if nave.acoplada:
        nave.acoplada = False 
        nave.fase_desacople = 1
        nave.desacople_timer = 0
        return

    nave.va += signo * DV_TOQUE
    nave.dv_acumulado += abs(DV_TOQUE)

def accionar_s(nave, cx, cy, particulas):
    if nave.aterrizada or nave.estrellada or nave.perdida or nave.acoplada or nave.despegando or nave.hundiendose or nave.rescatando: return
    
    if nave.en_atmosfera and not nave.aterrizaje_automatico:
        altitud_px = nave.radio_actual - R_PLANETA
        if altitud_px < 3:
            nave.estrellada = True
            nave.amerizo = not es_tierra(nave.angulo)
            if nave.amerizo:
                nave.hundiendose = True
                nave.hundimiento_timer = 0
                nave.hundimiento_angulo_original = nave.angulo
                nave.hundimiento_fase = 1
        else:
            nave.aterrizaje_automatico = True
    elif not nave.en_atmosfera:
        v_circ_local = math.sqrt(MU / nave.radio_actual)
        dv_cambio = abs(v_circ_local - nave.va) + abs(nave.vr)
        nave.va = v_circ_local
        nave.vr = 0.0
        nave.dv_acumulado += dv_cambio

def actualizar_orbita_circular(nave, dt):
    if nave.perdida: return
    v = math.sqrt(MU / nave.radio_orbita)
    nave.va = v
    nave.vr = 0.0
    nave.radio_actual = nave.radio_orbita
    nave.angulo += (v / nave.radio_orbita) * dt
    nave.dv_acumulado = 0.0

# ============================================================
# ACOPLAMIENTO Y COLISIONES
# ============================================================
def obtener_punto_gancho(iss, cx, cy):
    x, y = iss.posicion(cx, cy)
    ang_gancho = iss.angulo + math.pi / 2 + math.pi
    gancho_x = x + 20 * math.cos(ang_gancho)
    gancho_y = y + 20 * math.sin(ang_gancho)
    return gancho_x, gancho_y

def obtener_morro_nave(nave, cx, cy):
    x, y = nave.posicion(cx, cy)
    ang_morro = nave.angulo + math.pi / 2
    morro_x = x + 8 * math.cos(ang_morro)
    morro_y = y + 8 * math.sin(ang_morro)
    return morro_x, morro_y

def intentar_acoplamiento(verde, iss, cx, cy):
    if verde.acoplada or verde.aterrizada or verde.estrellada or verde.perdida or verde.fase_desacople > 0 or verde.en_atmosfera or verde.despegando or verde.hundiendose or verde.rescatando:
        return False
    mx, my = obtener_morro_nave(verde, cx, cy)
    gx, gy = obtener_punto_gancho(iss, cx, cy)
    dist = math.hypot(mx - gx, my - gy)
    dir_verde = verde.angulo + math.pi / 2
    dir_iss = iss.angulo + math.pi / 2
    diff_ang = (dir_verde - dir_iss + math.pi) % (2*math.pi) - math.pi
    _, _, vvx, vvy = verde.sincronizar_cartesiano(cx, cy)
    _, _, ivx, ivy = iss.sincronizar_cartesiano(cx, cy)
    vel_rel = math.hypot(vvx - ivx, vvy - ivy)
    if dist < 15 and abs(diff_ang) < 0.52 and vel_rel < 0.6:
        verde.acoplada = True
        return True
    return False

def comprobar_colision_iss(verde, iss, cx, cy):
    if verde.acoplada or verde.fase_desacople > 0 or verde.en_atmosfera or verde.despegando or verde.hundiendose or verde.rescatando: return False
    x, y = verde.posicion(cx, cy)
    ix, iy = iss.posicion(cx, cy)
    dist = math.hypot(x - ix, y - iy)
    if dist < 15:
        verde.estrellada = True
        return True
    return False

# ============================================================
# PREDICTOR POLAR
# ============================================================
def obtener_puntos_elipse(verde, cx, cy, pasos=360):
    if verde.aterrizada or verde.estrellada or verde.perdida or verde.acoplada or verde.fase_desacople > 0 or verde.en_atmosfera or verde.despegando or verde.hundiendose or verde.rescatando: return []
    datos = calcular_elementos_orbitales(verde)
    if datos and datos["es_circular"]:
        r = verde.radio_actual
        return [(cx + r * math.cos(2*math.pi*i/pasos), cy + r * math.sin(2*math.pi*i/pasos)) for i in range(pasos)]

    x, y = verde.posicion(cx, cy)
    rx, ry = x - cx, y - cy
    r_actual = math.hypot(rx, ry)
    if r_actual < 1.0: return []
    ux, uy = rx / r_actual, ry / r_actual
    _, _, vx, vy = verde.sincronizar_cartesiano(cx, cy)
    h = rx * vy - ry * vx
    ev_x = (vy * h) / MU - ux
    ev_y = (-vx * h) / MU - uy
    e = math.hypot(ev_x, ev_y)
    if e < 1e-3: return [] 
    v2 = vx**2 + vy**2
    epsilon = v2 / 2 - MU / r_actual
    if epsilon >= 0: return [] 
    p = h**2 / MU
    angulo_perigeo = math.atan2(ev_y, ev_x)
    puntos = []
    for i in range(pasos):
        theta = (2 * math.pi * i) / pasos
        den = 1 + e * math.cos(theta - angulo_perigeo)
        if den <= 0: continue
        r_theta = p / den
        px = cx + r_theta * math.cos(theta)
        py = cy + r_theta * math.sin(theta)
        if r_theta > R_PLANETA:
            puntos.append((px, py))
    return puntos

# ============================================================
# DIBUJO
# ============================================================
def dibujar_planeta(surf, cx, cy):
    pygame.draw.circle(surf, ATMOSFERA_COLOR, (int(cx), int(cy)), int(R_ATMOSFERA))
    pygame.draw.circle(surf, AGUA, (int(cx), int(cy)), int(R_PLANETA))
    
    tam = int(R_PLANETA * 2)
    surf_cont = pygame.Surface((tam, tam), pygame.SRCALPHA)
    
    for centro_ang, radio_ang in CONTINENTES_COLISION:
        cont_cx = R_PLANETA + R_PLANETA * math.cos(centro_ang)
        cont_cy = R_PLANETA + R_PLANETA * math.sin(centro_ang)
        cont_radio = R_PLANETA * radio_ang * 1.6
        
        pygame.draw.circle(surf_cont, TIERRA_FIRME, (int(cont_cx), int(cont_cy)), int(cont_radio))
        pygame.draw.circle(surf_cont, PLAYA, (int(cont_cx), int(cont_cy)), int(cont_radio), 2)
    
    mascara = pygame.Surface((tam, tam), pygame.SRCALPHA)
    pygame.draw.circle(mascara, (255, 255, 255, 255), (int(R_PLANETA), int(R_PLANETA)), int(R_PLANETA))
    surf_cont.blit(mascara, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    surf.blit(surf_cont, (int(cx - R_PLANETA), int(cy - R_PLANETA)))
    pygame.draw.circle(surf, TIERRA_BORDE, (int(cx), int(cy)), int(R_PLANETA), 2)

def dibujar_nave_verde(surf, nave, cx, cy):
    x, y = nave.posicion(cx, cy)
    if nave.perdida: return
    
    if nave.hundiendose:
        nave.hundimiento_timer += 1
        
        if nave.hundimiento_fase == 1:
            objetivo_radio = R_PLANETA - (R_PLANETA / 2) 
            
            if nave.radio_actual > objetivo_radio:
                nave.radio_actual -= 0.2 
                nave.angulo = nave.hundimiento_angulo_original
            else:
                nave.radio_actual = objetivo_radio
                nave.hundimiento_fase = 2
                nave.hundimiento_timer = 0
        else:
            offset_ang = math.sin(nave.hundimiento_timer * 0.03) * 0.08
            nave.angulo = nave.hundimiento_angulo_original + offset_ang
            
            objetivo_radio = R_PLANETA - (R_PLANETA / 2)
            offset_rad = math.cos(nave.hundimiento_timer * 0.03) * 2
            nave.radio_actual = objetivo_radio + offset_rad

        x, y = nave.posicion(cx, cy)
        ang = nave.angulo + math.pi / 2
        size = 10
        p1 = (x + size * math.cos(ang), y + size * math.sin(ang))
        p2 = (x + size*0.6 * math.cos(ang + 2.4), y + size*0.6 * math.sin(ang + 2.4))
        p3 = (x + size*0.6 * math.cos(ang - 2.4), y + size*0.6 * math.sin(ang - 2.4))
        
        temp = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.polygon(temp, (60, 180, 230, 100), [p1, p2, p3])
        pygame.draw.polygon(temp, (200, 255, 200, 100), [p1, p2, p3], 1)
        surf.blit(temp, (0,0))
        return

    if nave.aterrizada or nave.estrellada:
        color = NAVE_VERDE if nave.aterrizada else ROJO
        pygame.draw.circle(surf, color, (int(x), int(y)), 6)
        return
    ang = nave.angulo + math.pi / 2
    size = 10
    p1 = (x + size * math.cos(ang), y + size * math.sin(ang))
    p2 = (x + size*0.6 * math.cos(ang + 2.4), y + size*0.6 * math.sin(ang + 2.4))
    p3 = (x + size*0.6 * math.cos(ang - 2.4), y + size*0.6 * math.sin(ang - 2.4))
    pygame.draw.polygon(surf, NAVE_VERDE, [p1, p2, p3])
    pygame.draw.polygon(surf, (200, 255, 200), [p1, p2, p3], 1)

def dibujar_nave_azul(surf, nave, cx, cy, verde_acoplada):
    x, y = nave.posicion(cx, cy)
    ang = nave.angulo + math.pi / 2
    largo, ancho = 20, 4
    cos_a, sin_a = math.cos(ang), math.sin(ang)
    px, py = -sin_a, cos_a
    esquinas = [
        (x + largo*cos_a + ancho*px, y + largo*sin_a + ancho*py),
        (x + largo*cos_a - ancho*px, y + largo*sin_a - ancho*py),
        (x - largo*cos_a - ancho*px, y - largo*sin_a - ancho*py),
        (x - largo*cos_a + ancho*px, y - largo*sin_a + ancho*py),
    ]
    pygame.draw.polygon(surf, NAVE_AZUL, esquinas)
    pygame.draw.polygon(surf, (200, 220, 255), esquinas, 1)
    for s in (-1, 1):
        pygame.draw.circle(surf, (150, 200, 255), (int(x + s * largo * 0.6 * cos_a), int(y + s * largo * 0.6 * sin_a)), 3)
    gx, gy = obtener_punto_gancho(nave, cx, cy)
    pygame.draw.circle(surf, GANCHO_AMARILLO, (int(gx), int(gy)), 3)
    pygame.draw.circle(surf, BLANCO, (int(gx), int(gy)), 3, 1)

def dibujar_predictor(surf, puntos, color):
    for p in puntos:
        pygame.draw.circle(surf, color, (int(p[0]), int(p[1])), 1)

def dibujar_hud(surf, verde, azul, fuente, fuente_grande, datos_orbita, mensaje_error=""):
    altitud_px = verde.radio_actual - R_PLANETA if not verde.perdida else float('inf')
    altitud_km = altitud_px * ESCALA_KM_PX if altitud_px != float('inf') else 0
    
    if verde.despegando:
        lineas = [
            ("LANZADERA - DESPEGANDO", NAVE_VERDE, fuente_grande),
            (f"Altitud: {altitud_km:8.1f} km", BLANCO, fuente),
            ("Propulsores de despegue activos", AMARILLO, fuente),
            ("", BLANCO, fuente),
            ("Espera a llegar a la órbita inicial...", CIAN, fuente),
        ]
    elif verde.rescatando:
        lineas = [
            ("LANZADERA - RESCATANDO", NAVE_VERDE, fuente_grande),
            (f"Altitud: {altitud_km:8.1f} km", BLANCO, fuente),
            ("Motores de emergencia activos", NARANJA, fuente),
            ("", BLANCO, fuente),
            ("Saliendo del mar...", CIAN, fuente),
        ]
    elif verde.en_atmosfera or verde.aterrizaje_automatico or verde.hundiendose:
        if verde.aterrizada:
            altitud_m = 0
            vel_descenso_ms = 0.0
        elif verde.hundiendose:
            altitud_m = -15
            vel_descenso_ms = 0.0
        else:
            altitud_m = altitud_km * 1000
            vel_descenso_ms = abs(verde.vel_vertical_aterrizaje_px) * ESCALA_KM_PX * 1000
        
        lineas = [
            ("LANZADERA - ATMÓSFERA", NAVE_VERDE, fuente_grande),
            (f"Altitud: {altitud_m:8.0f} m", BLANCO, fuente),
            (f"Vel. descenso: {vel_descenso_ms:7.1f} m/s", 
             ROJO if vel_descenso_ms > 50 else NAVE_VERDE, fuente),
            ("", BLANCO, fuente),
        ]
        if verde.aterrizada:
            lineas.append(("ATERRIZAJE EXITOSO", NAVE_VERDE, fuente_grande))
            lineas.append(("Pulsa W para despegar", BLANCO, fuente))
        elif verde.hundiendose:
            lineas.append(("HUNDIDO EN EL MAR", AZUL_MAR, fuente_grande))
            lineas.append(("Pulsa W para rescatar o R para reiniciar", BLANCO, fuente))
        elif verde.aterrizaje_automatico:
            lineas.append(("ATERRIZAJE AUTOMÁTICO", CIAN, fuente_grande))
            lineas.append(("Retropropulsores activos", BLANCO, fuente))
        else:
            lineas.append(("Pulsa S para aterrizar", AMARILLO, fuente_grande))
            lineas.append(("(Si esperas demasiado, te estrellarás)", ROJO, fuente))
    else:
        velocidad_px_s = math.hypot(verde.va, verde.vr) if not verde.perdida else 0
        velocidad_km_s = velocidad_px_s * ESCALA_KM_PX / FACTOR_TIEMPO
        vr_km_s = verde.vr * ESCALA_KM_PX / FACTOR_TIEMPO if not verde.perdida else 0

        lineas = [
            ("LANZADERA", NAVE_VERDE, fuente_grande),
            (f"Altitud: {altitud_km:8.1f} km", BLANCO, fuente),
            (f"Velocidad: {velocidad_km_s:7.3f} km/s", BLANCO, fuente),
            (f"Vel. asc/desc: {vr_km_s:+7.3f} km/s", BLANCO, fuente),
            (f"Delta-v total: {verde.dv_acumulado * ESCALA_KM_PX / FACTOR_TIEMPO:6.2f} km/s", AMARILLO, fuente),
            (f"Δv por toque: {DV_TOQUE_KM_S*1000:.1f} m/s", GRIS, fuente),
            ("", BLANCO, fuente),
            ("S = Circularizar / Aterrizar", CIAN, fuente),
            ("A = Acelerar (Δv+)", NAVE_VERDE, fuente),
            ("D = Frenar (Δv-)", NAVE_VERDE, fuente),
            ("I = Ver información didáctica", CIAN, fuente),
            ("R = Reiniciar", GRIS, fuente),
        ]
        if datos_orbita:
            e = datos_orbita["e"]
            color_e = CIAN if datos_orbita["es_circular"] else PRED_ELIPTICA
            lineas.append(("", BLANCO, fuente))
            lineas.append((f"Excentricidad: {e:.3f}", color_e, fuente))
    
    for i, (texto, color, f) in enumerate(lineas):
        surf.blit(f.render(texto, True, color), (20, 20 + i * 26))

    y_msg = HEIGHT - 100
    if mensaje_error:
        msg = fuente_grande.render(mensaje_error, True, ROJO)
        surf.blit(msg, (WIDTH//2 - msg.get_width()//2, y_msg))
    elif verde.perdida:
        msg = fuente_grande.render("¡Lanzadera perdida! Pulsa R", True, AMARILLO)
        surf.blit(msg, (WIDTH//2 - msg.get_width()//2, y_msg))
    elif verde.aterrizada:
        msg = fuente_grande.render("¡ATERRIZAJE EXITOSO! Pulsa W para despegar", True, NAVE_VERDE)
        surf.blit(msg, (WIDTH//2 - msg.get_width()//2, y_msg))
    elif verde.hundiendose:
        msg = fuente_grande.render("¡HUNDIDO! Pulsa W para rescatar o R para reiniciar", True, AZUL_MAR)
        surf.blit(msg, (WIDTH//2 - msg.get_width()//2, y_msg))
    elif verde.rescatando:
        msg = fuente_grande.render("¡RESCATANDO LANZADERA!", True, NARANJA)
        surf.blit(msg, (WIDTH//2 - msg.get_width()//2, y_msg))
    elif verde.estrellada:
        if verde.amerizo:
            msg_text = "¡PERDIDO EN EL MAR! Pulsa R para reiniciar"
            color_msg = AZUL_MAR
        else:
            msg_text = "¡IMPACTO! Pulsa R para reiniciar"
            color_msg = ROJO
        msg = fuente_grande.render(msg_text, True, color_msg)
        surf.blit(msg, (WIDTH//2 - msg.get_width()//2, y_msg))
    elif verde.acoplada:
        msg = fuente_grande.render("¡ACOPLADO A LA ISS!", True, GANCHO_AMARILLO)
        surf.blit(msg, (WIDTH//2 - msg.get_width()//2, y_msg))
        msg2 = fuente.render("Pulsa A o D para desacoplar", True, BLANCO)
        surf.blit(msg2, (WIDTH//2 - msg2.get_width()//2, y_msg + 30))
    elif verde.fase_desacople > 0:
        msg = fuente_grande.render("Desacoplando...", True, NARANJA)
        surf.blit(msg, (WIDTH//2 - msg.get_width()//2, y_msg))
    elif datos_orbita and datos_orbita["es_circular"]:
        msg = fuente_grande.render("Órbita circular estabilizada", True, CIAN)
        surf.blit(msg, (WIDTH//2 - msg.get_width()//2, y_msg))

    altitud_azul_km = (azul.radio_actual - R_PLANETA) * ESCALA_KM_PX
    v_azul_km_s = azul.va * ESCALA_KM_PX / FACTOR_TIEMPO
    lineas_azul = [
        ("ISS", NAVE_AZUL, fuente_grande),
        (f"Altitud: {altitud_azul_km:.0f} km", BLANCO, fuente),
        (f"Vel: {v_azul_km_s:.2f} km/s", BLANCO, fuente),
    ]
    for i, (texto, color, f) in enumerate(lineas_azul):
        surf.blit(f.render(texto, True, color), (WIDTH - 280, 20 + i * 26))

def dibujar_pantalla_info(surf, fuente, fuente_grande):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 220))
    surf.blit(overlay, (0, 0))
    
    line_height = 26
    total_height = len(TEXTO_INFO) * line_height
    y_inicio = (HEIGHT - total_height) // 2 - 20
    
    for i, (texto, tipo) in enumerate(TEXTO_INFO):
        if tipo == "titulo":
            txt = fuente_grande.render(texto, True, AMARILLO)
            surf.blit(txt, (WIDTH//2 - txt.get_width()//2, y_inicio + i * line_height))
        elif tipo == "destacado":
            txt = fuente_grande.render(texto, True, AZUL_DESTACADO)
            surf.blit(txt, (WIDTH//2 - txt.get_width()//2, y_inicio + i * line_height))
        else:
            txt = fuente.render(texto, True, BLANCO)
            surf.blit(txt, (WIDTH//2 - txt.get_width()//2, y_inicio + i * line_height))
    
    msg_volver = fuente.render("[ Pulsa I para volver al juego ]", True, GRIS)
    surf.blit(msg_volver, (WIDTH//2 - msg_volver.get_width()//2, HEIGHT - 60))

# ============================================================
# BUCLE PRINCIPAL
# ============================================================
def main():
    pygame.init()
    pantalla = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Órbitas de Hohmann - Lanzadera reutilizable")
    reloj = pygame.time.Clock()

    fuente = pygame.font.SysFont("consolas", 18)
    fuente_grande = pygame.font.SysFont("consolas", 22, bold=True)

    cx, cy = WIDTH // 2, HEIGHT // 2

    verde = Nave(R_VERDE, NAVE_VERDE, 0.0, "Verde")
    azul  = Nave(R_AZUL, NAVE_AZUL, math.pi, "Azul")

    particulas = []
    mensaje_error = ""
    ejecutando = True
    
    game_over_timer = 0
    game_over_tipo = ""
    game_over_amerizo = False
    
    pausado = False

    while ejecutando:
        try:
            dt = DT_FISICO
            
            if not pausado:
                if game_over_timer > 0:
                    game_over_timer -= 1
                    if game_over_timer == 0:
                        verde = Nave(R_VERDE, NAVE_VERDE, 0.0, "Verde")
                        particulas.clear()
                        game_over_tipo = ""
                        game_over_amerizo = False
            
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    ejecutando = False
                elif evento.type == pygame.KEYDOWN:
                    if evento.key == pygame.K_i:
                        pausado = not pausado
                    elif pausado:
                        continue 
                    
                    elif evento.key == pygame.K_r:
                        verde = Nave(R_VERDE, NAVE_VERDE, 0.0, "Verde")
                        azul  = Nave(R_AZUL, NAVE_AZUL, math.pi, "Azul")
                        particulas.clear()
                        game_over_timer = 0
                        game_over_tipo = ""
                        game_over_amerizo = False
                        mensaje_error = ""
                    elif game_over_timer > 0:
                        continue
                    
                    elif evento.key == pygame.K_w:
                        if verde.aterrizada:
                            verde.iniciar_despegue()
                        elif verde.hundiendose:
                            verde.iniciar_rescate()
                    elif evento.key == pygame.K_a:
                        aplicar_delta_v(verde, +1, azul, cx, cy)
                        if not verde.en_atmosfera and not verde.despegando and not verde.hundiendose and not verde.rescatando:
                            emitir_estela(particulas, verde, cx, cy, "fuego", cantidad=20)
                    elif evento.key == pygame.K_d:
                        aplicar_delta_v(verde, -1, azul, cx, cy)
                        if not verde.en_atmosfera and not verde.despegando and not verde.hundiendose and not verde.rescatando:
                            emitir_estela(particulas, verde, cx, cy, "hielo", cantidad=20)
                    elif evento.key == pygame.K_s:
                        accionar_s(verde, cx, cy, particulas)
                        emitir_estela(particulas, verde, cx, cy, "hielo", cantidad=20)

            if not pausado and game_over_timer == 0:
                if verde.despegando:
                    verde.actualizar_despegue(dt, particulas, cx, cy)
                elif verde.rescatando:
                    verde.actualizar_rescate(dt, particulas, cx, cy)
                
                actualizar_nave_verde(verde, dt, cx, cy, azul, particulas)
                actualizar_orbita_circular(azul, dt)
                intentar_acoplamiento(verde, azul, cx, cy)
                colision = comprobar_colision_iss(verde, azul, cx, cy)
                
                if verde.en_atmosfera and not verde.aterrizaje_automatico:
                    if random.random() < 0.4:
                        emitir_estela(particulas, verde, cx, cy, "friccion", cantidad=1)

                if colision or (verde.estrellada and not verde.hundiendose):
                    game_over_timer = 90
                    game_over_tipo = "impacto"
                    game_over_amerizo = verde.amerizo
                    x, y = verde.posicion(cx, cy)
                    for _ in range(80):
                        ang = random.uniform(0, 2*math.pi)
                        vel = random.uniform(1, 6)
                        vx = vel * math.cos(ang)
                        vy = vel * math.sin(ang)
                        color_expl = (random.randint(200,255), random.randint(50,150), 0)
                        particulas.append(Particula(x, y, vx, vy, color_expl, vida_max=40))
                elif verde.perdida:
                    game_over_timer = 90
                    game_over_tipo = "perdida"
                
                for p in particulas:
                    p.actualizar(dt)
                particulas[:] = [p for p in particulas if p.vida > 0 and p.tam > 0.3]

            datos_orbita = calcular_elementos_orbitales(verde) if not (verde.perdida or verde.aterrizada or verde.estrellada or verde.despegando or verde.hundiendose or verde.rescatando) else None
            puntos_pred = obtener_puntos_elipse(verde, cx, cy)

            pantalla.fill(NEGRO)
            for i in range(60):
                sx = (i * 137 + 50) % WIDTH
                sy = (i * 89 + 30) % HEIGHT
                pygame.draw.circle(pantalla, (80, 80, 110), (sx, sy), 1)

            pygame.draw.circle(pantalla, (30, 40, 60), (cx, cy), int(R_VERDE), 1)
            pygame.draw.circle(pantalla, (30, 40, 70), (cx, cy), int(R_AZUL), 1)

            dibujar_planeta(pantalla, cx, cy)

            color_pred = PRED_CIRCULAR if (datos_orbita and datos_orbita["es_circular"]) else PRED_ELIPTICA
            dibujar_predictor(pantalla, puntos_pred, color_pred)

            for p in particulas:
                p.dibujar(pantalla)

            dibujar_nave_azul(pantalla, azul, cx, cy, verde.acoplada)
            dibujar_nave_verde(pantalla, verde, cx, cy)
            
            if game_over_timer > 0:
                if game_over_tipo == "impacto":
                    if game_over_amerizo:
                        msg = fuente_grande.render("¡PERDIDO EN EL MAR! Reiniciando...", True, AZUL_MAR)
                    else:
                        msg = fuente_grande.render("¡COLISIÓN! Reiniciando lanzadera...", True, ROJO)
                elif game_over_tipo == "perdida":
                    msg = fuente_grande.render("¡LANZADERA PERDIDA! Reiniciando...", True, AMARILLO)
                pantalla.blit(msg, (WIDTH//2 - msg.get_width()//2, HEIGHT//2))
            else:
                dibujar_hud(pantalla, verde, azul, fuente, fuente_grande, datos_orbita, mensaje_error)

            if pausado:
                dibujar_pantalla_info(pantalla, fuente, fuente_grande)

            pygame.display.flip()
            reloj.tick(FPS)

        except Exception as e:
            tb = traceback.format_exc()
            lineas_tb = tb.strip().split('\n')
            mensaje_error = lineas_tb[-1] if lineas_tb else str(e)
            pantalla.fill(NEGRO)
            for idx, linea in enumerate(lineas_tb[-4:]):
                surf_txt = fuente.render(linea, True, ROJO)
                pantalla.blit(surf_txt, (20, 100 + idx * 25))
            pygame.display.flip()
            reloj.tick(10)

    pygame.quit()

if __name__ == "__main__":
    main()