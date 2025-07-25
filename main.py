import pygame
import sys
import pytmx
from colores import *
from entidades import *
# Configuración
ANCHO = 800
ALTO = 600
TILE_SIZE = 32

pygame.init()
pantalla = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("Juego")
clock = pygame.time.Clock()

# Cargar mapa
tmx_data = pytmx.load_pygame("Nivel.tmx")
map_width = tmx_data.width * TILE_SIZE
map_height = tmx_data.height * TILE_SIZE

# Función para obtener rectángulos desde capas
def obtener_rects(tmx, capa_nombre):
    lista = []
    for x, y, gid in tmx.get_layer_by_name(capa_nombre):
        if gid != 0:
            rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            lista.append(rect)
    return lista

# Jugador
jugador = pygame.Rect(100, 100, 32, 32)
color_jugador = (0, 0, 255)
vel_y = 0
gravedad = 900
fuerza_salto = -400
en_suelo = False

# Paredes
contacto_pared_izquierda = False
contacto_pared_derecha = False

# Capas
plataformas = obtener_rects(tmx_data, "Plataformas")
lava_tiles = obtener_rects(tmx_data, "Lava")

# Cámara
camera_x = 0
ultimo_tick = pygame.time.get_ticks()

# Bucle principal
while True:
    ahora = pygame.time.get_ticks()
    dt = (ahora - ultimo_tick) / 1000
    ultimo_tick = ahora

    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_UP:
                if en_suelo:
                    vel_y = fuerza_salto
                    en_suelo = False
                elif contacto_pared_izquierda:
                    vel_y = fuerza_salto
                    jugador.x += 10  # Rebota a la derecha
                elif contacto_pared_derecha:
                    vel_y = fuerza_salto
                    jugador.x -= 10  # Rebota a la izquierda

    # Movimiento lateral
    teclas = pygame.key.get_pressed()
    movx = 0
    if teclas[pygame.K_LEFT]:
        movx = -300 * dt
    if teclas[pygame.K_RIGHT]:
        movx = 300 * dt

    jugador.x += movx

    # Colisiones horizontales
    for p in plataformas:
        if jugador.colliderect(p):
            if movx > 0:
                jugador.right = p.left
            elif movx < 0:
                jugador.left = p.right

    # Detectar contacto con paredes
    contacto_pared_izquierda = False
    contacto_pared_derecha = False
    rect_izq = jugador.move(-1, 0)
    rect_der = jugador.move(1, 0)
    for p in plataformas:
        if rect_izq.colliderect(p):
            contacto_pared_izquierda = True
        if rect_der.colliderect(p):
            contacto_pared_derecha = True

    # Movimiento vertical con gravedad
    vel_y += gravedad * dt

    # Wall slide: si toca pared y no está en suelo
    if not en_suelo and (contacto_pared_izquierda or contacto_pared_derecha):
        vel_y = min(vel_y, 200)  # Caída lenta

    jugador.y += vel_y * dt

    # Colisiones verticales
    for p in plataformas:
        if jugador.colliderect(p):
            if vel_y > 0:
                jugador.bottom = p.top
                vel_y = 0
                en_suelo = True
            elif vel_y < 0:
                jugador.top = p.bottom
                vel_y = 0

    # Verificar si está sobre plataforma
    jugador_abajo = jugador.move(0, 1)
    en_suelo = False
    for p in plataformas:
        if jugador_abajo.colliderect(p):
            en_suelo = True
            break

    # Deteccion de lava
    for lava in lava_tiles:
        if jugador.colliderect(lava):
            fuente = pygame.font.SysFont(None, 80)
            texto = fuente.render("¡Perdiste!", True, (255, 0, 0))
            pygame.quit()
            sys.exit()

    # camara
    camera_x = jugador.centerx - ANCHO // 2
    camera_x = max(0, min(camera_x, map_width - ANCHO))

    # dibujar
    pantalla.fill((color_azul_cielo))

    for layer in tmx_data.visible_layers:
        if isinstance(layer, pytmx.TiledTileLayer):
            for x, y, gid in layer:
                tile = tmx_data.get_tile_image_by_gid(gid)
                if tile:
                    pantalla.blit(tile, (x * TILE_SIZE - camera_x, y * TILE_SIZE))

    pygame.draw.rect(pantalla, color_jugador, (jugador.x - camera_x, jugador.y, jugador.width, jugador.height))

    pygame.display.flip()
    clock.tick(60)

