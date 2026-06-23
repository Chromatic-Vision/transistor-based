import math

import pygame

from OpenGL import GL

# import grid
import render

pygame.init()

PLANE = [
    (0, 0),
    (1, 0),
    (1, 1),
    (0, 0),
    (1, 1),
    (0, 1)
]

def render_plane(x: float, y: float, scale: float) -> None:
    GL.glPushMatrix()
    GL.glLoadIdentity()
    GL.glTranslatef(x, y, 0.0)
    GL.glScalef(scale, scale, scale)
    GL.glBegin(GL.GL_TRIANGLES)
    for tx, ty in PLANE:
        GL.glVertex3f(tx, ty, 0.0)
    GL.glEnd()
    GL.glPopMatrix()

COLOR_BACKGROUND = (0, 0, 0)
COLOR_GRID = (80, 15, 30)
COLOR_ACCENT = (176, 36, 58)
COLOR_FOREGROUND = (255, 255, 255)

# g = grid.Grid()
camera_x = 0.0
camera_y = 0.0
camera_scale = 1.0

FRAGMENT_SHADER = """
#version 330 core
out vec4 FragColor;

void main() {
    FragColor = vec4(1.0f, 0.5f, 0.2f, 1.0f);
}
"""

opengl_display = pygame.display.set_mode((800, 800), pygame.RESIZABLE | pygame.OPENGL | pygame.DOUBLEBUF)

fragment_shader = GL.glCreateShader(GL.GL_FRAGMENT_SHADER)
GL.glShaderSource(fragment_shader, FRAGMENT_SHADER)
GL.glCompileShader(fragment_shader)

grid_shader_program = GL.glCreateProgram()
GL.glAttachShader(grid_shader_program, fragment_shader)
GL.glLinkProgram(grid_shader_program)

CAMERA_SPEED = 1.0
ZOOM_RATE = 1.1

clock = pygame.time.Clock()
run = True
while run:
    clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        elif event.type == pygame.MULTIGESTURE:
            print(event)
    # screen.fill(COLOR_BACKGROUND)

    keys = pygame.key.get_pressed()
    if keys[pygame.K_a]:
        camera_x += CAMERA_SPEED / camera_scale
    if keys[pygame.K_d]:
        camera_x -= CAMERA_SPEED / camera_scale

    if keys[pygame.K_w]:
        camera_y += CAMERA_SPEED / camera_scale
    if keys[pygame.K_s]:
        camera_y -= CAMERA_SPEED / camera_scale

    # print(CAMERA_SPEED / scale, camera_x)

    if keys[pygame.K_DOWN]:
        camera_scale /= ZOOM_RATE
    if keys[pygame.K_UP]:
        camera_scale *= ZOOM_RATE

    # g.render(screen, (camera_x, camera_y), camera_scale)

    GL.glUseProgram(grid_shader_program)
    render_plane(camera_x, camera_x, camera_scale)

    pygame.display.flip()

# g.close()
