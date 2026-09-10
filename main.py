import os
import socket

import pygame

import world
import gui
import cursors
import net

address = ('localhost', 60_001)

set_videodriver = False
if 'SDL_VIDEODRIVER' not in os.environ:
    os.environ['SDL_VIDEODRIVER'] = 'x11'
    set_videodriver = True

pygame.init()
try:
    pygame.display.init()
except pygame.error:
    if set_videodriver:
        print('Not able to use x11')
        os.environ.pop('SDL_VIDEODRIVER')
        pygame.display.init()
    else:
        raise

print('Using video driver:', pygame.display.get_driver())

screen = pygame.display.set_mode((0, 0), pygame.RESIZABLE)

cursors.init()

CAMERA_SPEED = 20  # blocks/s
tick_rate = 20

if address is not None:
    s = socket.socket()
    s.connect(address)
    s.settimeout(0)
    client = net.NetClient(s)
else:
    client = None
level = world.Level(screen.get_size(), client=client)

clock = pygame.time.Clock()
run = True
try:
    while run:
        clock.tick(60)
        dt = clock.get_time() / 1_000
        gui.events = pygame.event.get()
        for event in gui.events:
            if event.type == pygame.QUIT:
                run = False
            elif event.type == pygame.MOUSEWHEEL:
                # TODO: Zoom into the middle of the screen instead of top-left
                if event.y > 0:
                    level.tile_size *= 1.1
                elif event.y < 0:
                    level.tile_size /= 1.1
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

        level.update_camera_and_render(screen, camera_dx * CAMERA_SPEED, camera_dy * CAMERA_SPEED, dt)

        pygame.display.update()
finally:
    level.stop()
