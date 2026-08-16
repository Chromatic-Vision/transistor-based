import threading

import pygame

import world

pygame.init()

screen = pygame.display.set_mode((0, 0), pygame.RESIZABLE)

CAMERA_SPEED = 20  # blocks/s
tick_rate = 20

level = world.Level(screen.get_size())

clock = pygame.time.Clock()
run = True
while run:
    clock.tick(60)
    dt = clock.get_time() / 1_000
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
    screen.fill((0, 0, 0))

    keys = pygame.key.get_pressed()
    camera_dx = 0
    camera_dy = 0
    if keys[pygame.K_a] or keys[pygame.K_LEFT]:
        camera_dx += -1
    if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
        camera_dx += 1

    if keys[pygame.K_s] or keys[pygame.K_DOWN]:
        camera_dy += 1
    if keys[pygame.K_w] or keys[pygame.K_UP]:
        camera_dy += -1

    level.update_camera(screen, camera_dx * CAMERA_SPEED, camera_dy * CAMERA_SPEED, dt)

    pygame.display.update()

level.stop()
