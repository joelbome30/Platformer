import pygame
import sys
class Entity:
    def __init__(self, posx, posy, ancho=50, alto=50):
        self.posx = posx
        self.posy = posy
        self.ancho = ancho
        self.alto = alto

    def dibujar(self, superficie, color):
        pygame.draw.rect(superficie, color, (self.posx, self.posy, self.ancho, self.alto))

    def get_rect(self):
        return pygame.Rect(self.posx, self.posy, self.ancho, self.alto)

    @staticmethod
    def colisionan(ent1, ent2):
        return ent1.get_rect().colliderect(ent2.get_rect())

def wall_hop(jugador, plataformas, movx):
    wall_hop = False
    for p in plataformas:
        if jugador.colliderect(p):
            if movx > 0:
                jugador.right = p.left
                wall_hop = True
            elif movx < 0:
                jugador.left = p.right
                wall_hop = True
    return wall_hop
