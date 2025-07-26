import pygame, sys, pytmx
from colores import *
from entidades import *

ANCHO, ALTO, TILE = 800, 600, 32
pygame.init()
pantalla = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("juego")
clock = pygame.time.Clock()

tmx = pytmx.load_pygame("Nivel.tmx")
map_w, map_h = tmx.width * TILE, tmx.height * TILE

def rects(capa):
    return [pygame.Rect(x * TILE, y * TILE, TILE, TILE)
            for x, y, gid in tmx.get_layer_by_name(capa) if gid]

plataformas = rects("Plataformas")
lava = rects("Lava")

# spawnpoints
spawnpoints = []
spawn_actual = None

for obj in tmx.objects:
    if obj.type == "Spawnpoint":
        rect = pygame.Rect(obj.x, obj.y, obj.width, obj.height)
        spawnpoints.append((obj.id, rect))
        if obj.id == 2:
            spawn_actual = rect

if not spawnpoints:
    print("no hay spawnpoints")
    sys.exit()
if spawn_actual is None:
    print("id 2 no encontrado, usando primero")
    spawn_actual = spawnpoints[0][1]

jugador = Entity(spawn_actual.x, spawn_actual.y, 32, 32)
jugador.muerto = False
vel_y, gravedad, salto = 0, 900, -400
en_suelo, t_muerte = False, 0

# control de wallhop
wallhop_izq_hecho = False
wallhop_der_hecho = False

while True:
    dt = clock.tick(60) / 1000
    teclas = pygame.key.get_pressed()

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            pygame.quit(); sys.exit()
        if e.type == pygame.KEYDOWN and e.key == pygame.K_UP and not jugador.muerto:
            if en_suelo:
                vel_y = salto
                wallhop_izq_hecho = False
                wallhop_der_hecho = False
            elif izq and teclas[pygame.K_RIGHT] and not wallhop_izq_hecho:
                vel_y = salto
                jugador.posx += 10
                wallhop_izq_hecho = True
            elif der and teclas[pygame.K_LEFT] and not wallhop_der_hecho:
                vel_y = salto
                jugador.posx -= 10
                wallhop_der_hecho = True

    if jugador.muerto:
        if pygame.time.get_ticks() - t_muerte >= 2000:
            jugador.posx, jugador.posy = spawn_actual.x, spawn_actual.y
            jugador.muerto = False
            vel_y = 0
            en_suelo = False
            wallhop_izq_hecho = False
            wallhop_der_hecho = False
        else:
            continue

    movx = (-300 if teclas[pygame.K_LEFT] else 0) + (300 if teclas[pygame.K_RIGHT] else 0)
    jugador.posx += movx * dt

    rect = jugador.get_rect()
    for p in plataformas:
        if rect.colliderect(p):
            jugador.posx = p.left - jugador.ancho if movx > 0 else p.right
            break

    # contacto con pared
    izq = any(rect.move(-1, 0).colliderect(p) for p in plataformas)
    der = any(rect.move(1, 0).colliderect(p) for p in plataformas)

    # reiniciar wallhop si se despega
    if not izq:
        wallhop_izq_hecho = False
    if not der:
        wallhop_der_hecho = False

    vel_y += gravedad * dt
    if not en_suelo and (izq or der): vel_y = min(vel_y, 200)
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

    if any(rect.colliderect(l) for l in lava):
        jugador.muerto = True
        t_muerte = pygame.time.get_ticks()

    for _, s in spawnpoints:
        if rect.colliderect(s):
            spawn_actual = s

    jugador.posx = max(0, min(jugador.posx, map_w - jugador.ancho))
    jugador.posy = max(0, min(jugador.posy, map_h - jugador.alto))

    cam_x = max(0, min(rect.centerx - ANCHO // 2, map_w - ANCHO))
    cam_y = max(0, min(rect.centery - ALTO // 2, map_h - ALTO))

    pantalla.fill(color_azul_cielo)
    for layer in tmx.visible_layers:
        if isinstance(layer, pytmx.TiledTileLayer):
            for x, y, gid in layer:
                tile = tmx.get_tile_image_by_gid(gid)
                if tile:
                    pantalla.blit(tile, (x * TILE - cam_x, y * TILE - cam_y))

    if jugador.muerto:
        pantalla.fill(color_rojo)
        f = pygame.font.Font(None, 50)
        t1 = f.render("has muerto", True, color_blanco)
        t2 = f.render("reiniciando en 2 segundos...", True, color_blanco)
        pantalla.blit(t1, (ANCHO // 2 - t1.get_width() // 2, ALTO // 2 - 50))
        pantalla.blit(t2, (ANCHO // 2 - t2.get_width() // 2, ALTO // 2))
    else:
        jugador.dibujar(pantalla, (0, 0, 255), cam_x, cam_y)

    pygame.display.flip()
