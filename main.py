import math

import pygame

# import grid
import render

pygame.init()

COLOR_BACKGROUND = (0, 0, 0)
COLOR_GRID = (80, 15, 30)
COLOR_ACCENT = (176, 36, 58)
COLOR_FOREGROUND = (255, 255, 255)

# g = grid.Grid()

screen = pygame.display.set_mode((800, 800), pygame.RESIZABLE)
clock = pygame.time.Clock()
run = True
while run:
    clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        elif event.type == pygame.MULTIGESTURE:
            print(event)
    screen.fill(COLOR_BACKGROUND)

    size = min(*screen.get_size()) / 8.0
    render.render(screen, 'XOR', COLOR_FOREGROUND, (screen.get_width() / 2 - size / 2, screen.get_height() / 2 - size / 2), size)

    pygame.display.update()
