import pygame
import sys
import pytmx
from colores import *
from entidades import *

# Constants
ancho, alto, tamaño = 800, 600, 16
pygame.init()
pantalla = pygame.display.set_mode((ancho, alto))
pygame.display.set_caption("Juego")
reloj = pygame.time.Clock()

# Load map and assets
mapa = pytmx.load_pygame("Nivel.tmx")
fondo_img = pygame.image.load("Assets/Backgrounds/lev01_checkers/area01_parallax/area01_bkg1.png").convert()

# Find coin image
imagen_moneda = None
for objeto in mapa.objects:
    if getattr(objeto, "type", "") == "Coin" and hasattr(objeto, "gid"):
        imagen_moneda = mapa.get_tile_image_by_gid(objeto.gid)
        break

mapa_ancho, mapa_alto = mapa.width * tamaño, mapa.height * tamaño

def obtener_rects(nombre_capa):
    return [pygame.Rect(x * tamaño, y * tamaño, tamaño, tamaño)
            for x, y, gid in mapa.get_layer_by_name(nombre_capa) if gid]

plataformas = obtener_rects("Plataformas")
lava = obtener_rects("Lava")

# Collectibles
monedas_recolectadas = 0
monedas = []
for obj in mapa.objects:
    if getattr(obj, "type", "") == "Coin" and hasattr(obj, "gid"):
        imagen = mapa.get_tile_image_by_gid(obj.gid)
        rect = pygame.Rect(obj.x, obj.y - imagen.get_height(), imagen.get_width(), imagen.get_height())
        monedas.append({"rect": rect, "imagen": imagen})

# Find spawn point
punto_inicial = None
for objeto in mapa.objects:
    if getattr(objeto, "type", "") == "Spawnpoint" and objeto.name == "Inicio":
        punto_inicial = pygame.Rect(objeto.x, objeto.y, objeto.width, objeto.height)
        break

if punto_inicial is None:
    print("No se encontró un Spawnpoint llamado 'Inicio'")
    sys.exit()

# Player setup
jugador = Entity(punto_inicial.x, punto_inicial.y, 16, 16)
jugador.muerto = False

# Game variables
zoom = 1.25
velocidad = 200
vel_y = 0
gravedad = 900
salto = -300
en_suelo = False
tiempo_muerte = 0
wallhop_izq_hecho = False
wallhop_der_hecho = False
muertes = 0
fuente = pygame.font.Font(None, 30)

# Main game loop
while True:
    dt = reloj.tick(60) / 1000
    teclas = pygame.key.get_pressed()

    # Event handling
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_UP and not jugador.muerto:
                if en_suelo:
                    vel_y = salto
                    wallhop_izq_hecho = False
                    wallhop_der_hecho = False
                elif tocando_izquierda and teclas[pygame.K_RIGHT] and not wallhop_izq_hecho:
                    vel_y = salto
                    jugador.posx += 10
                    wallhop_izq_hecho = True
                elif tocando_derecha and teclas[pygame.K_LEFT] and not wallhop_der_hecho:
                    vel_y = salto
                    jugador.posx -= 10
                    wallhop_der_hecho = True

            elif evento.key in (pygame.K_EQUALS, pygame.K_PLUS):
                zoom = min(2.0, zoom + 0.1)
            elif evento.key == pygame.K_MINUS:
                zoom = max(0.5, zoom - 0.1)

    # Player death handling
    if jugador.muerto:
        if pygame.time.get_ticks() - tiempo_muerte >= 2000:
            jugador.posx, jugador.posy = punto_inicial.x, punto_inicial.y
            jugador.muerto = False
            vel_y = 0
            en_suelo = False
            wallhop_izq_hecho = False
            wallhop_der_hecho = False
        else:
            continue

    # Horizontal movement
    mov_horizontal = (-velocidad if teclas[pygame.K_LEFT] else 0) + (velocidad if teclas[pygame.K_RIGHT] else 0)
    jugador.posx += mov_horizontal * dt

    # Collision detection
    rect = jugador.get_rect()
    for p in plataformas:
        if rect.colliderect(p):
            jugador.posx = p.left - jugador.ancho if mov_horizontal > 0 else p.right
            break

    tocando_izquierda = any(rect.move(-1, 0).colliderect(p) for p in plataformas)
    tocando_derecha = any(rect.move(1, 0).colliderect(p) for p in plataformas)

    if not tocando_izquierda:
        wallhop_izq_hecho = False
    if not tocando_derecha:
        wallhop_der_hecho = False

    # Vertical movement and gravity
    vel_y += gravedad * dt
    if not en_suelo and (tocando_izquierda or tocando_derecha):
        vel_y = min(vel_y, 200)

    jugador.posy += vel_y * dt
    rect = jugador.get_rect()
    for p in plataformas:
        if rect.colliderect(p):
            if vel_y > 0:
                jugador.posy = p.top - jugador.alto
                en_suelo = True
            else:
                jugador.posy = p.bottom
            vel_y = 0
            break

    en_suelo = any(rect.move(0, 1).colliderect(p) for p in plataformas)

    # Lava collision
    if any(rect.colliderect(l) for l in lava):
        jugador.muerto = True
        tiempo_muerte = pygame.time.get_ticks()
        muertes += 1

    # Coin collection
    monedas = [m for m in monedas if not rect.colliderect(m["rect"])]
    monedas_recolectadas += len([m for m in monedas if rect.colliderect(m["rect"])])

    # Boundary checking
    jugador.posx = max(0, min(jugador.posx, mapa_ancho - jugador.ancho))
    jugador.posy = max(0, min(jugador.posy, mapa_alto - jugador.alto))

    # Camera setup
    cam_x = max(0, min(rect.centerx - ancho // (2 * zoom), mapa_ancho - ancho // zoom))
    cam_y = 0 if mapa_alto <= alto else max(0, min(rect.centery - alto // (2 * zoom), mapa_alto - alto // zoom))

    # Render zoomed surface
    pantalla_zoom = pygame.Surface((ancho // zoom, alto // zoom))

    # Draw background
    fondo_escalado = pygame.transform.scale(fondo_img, (mapa_ancho, mapa_alto))
    pantalla_zoom.blit(fondo_escalado, (-cam_x, -cam_y))

    # Draw map layers
    for capa in mapa.visible_layers:
        if isinstance(capa, pytmx.TiledTileLayer):
            for x, y, gid in capa:
                tile = mapa.get_tile_image_by_gid(gid)
                if tile:
                    pantalla_zoom.blit(tile, (x * tamaño - cam_x, y * tamaño - cam_y))

    # Draw coins
    for moneda in monedas:
        pantalla_zoom.blit(moneda["imagen"], (moneda["rect"].x - cam_x, moneda["rect"].y - cam_y))

    # Draw player or death screen
    if jugador.muerto:
        pantalla_zoom.fill(color_rojo)
    else:
        jugador.dibujar(pantalla_zoom, (0, 0, 255), cam_x, cam_y)

    # Draw HUD
    if imagen_moneda:
        pantalla_zoom.blit(imagen_moneda, (5, 5))
        texto = fuente.render(str(monedas_recolectadas), True, color_blanco)
        pantalla_zoom.blit(texto, (25, 7))

        texto2 = fuente.render(f"Muertes: {muertes}", True, color_blanco)
        pantalla_zoom.blit(texto2, (5, 28))

    # Final render
    pygame.transform.scale(pantalla_zoom, (ancho, alto), pantalla)
    pygame.display.flip()