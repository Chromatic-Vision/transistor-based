from __future__ import annotations

import threading

import pygame

GRID_SIZE = 20


class Grid:
    def __init__(self):
        self._render_thread = threading.Thread(target=self._render_func, name='Grid._render_thread')

        self._render_surface: pygame.Surface | None = None
        self._last_scale: float | None = None
        self._last_camera_pos: tuple[float, float] = (0, 0)
        self._last_rect = None

        self._run = True

        self._render_thread.start()

    def _render_func(self):
        def world_to_surface(pos: tuple[float, float]) -> tuple[float, float]:
            return (
                (pos[0] + self._last_camera_pos[0]) * self._last_scale,
                (pos[1] + self._last_camera_pos[1]) * self._last_scale
            )

        clock = pygame.time.Clock()
        while self._run:
            if self._last_scale is not None and self._last_camera_pos is not None and self._render_surface is not None:
                rect = (*world_to_surface((10, 10)), 10 / self._last_scale, 10 / self._last_scale)
                # print(rect)
                pygame.draw.rect(self._render_surface, (255, 0, 0), rect)
            clock.tick(60)

    def render(self, screen: pygame.Surface, camera_pos: tuple[float, float], scale: float):
        # TODO: Make _render_thread render, project it into world space, and render it at the current scale and camera_pos

        def world_to_screen(pos: tuple[float, float]) -> tuple[float, float]:
            return (pos[0] - camera_pos[0]) * scale + screen.get_width() / 2, (pos[1] - camera_pos[1]) * scale + screen.get_height() / 2

        def screen_to_world(pos: tuple[float, float]) -> tuple[float, float]:
            return (
                (pos[0] - screen.get_width() / 2) / scale + camera_pos[0],
                (pos[1] - screen.get_height() / 2) / scale + camera_pos[1]
            )

        # assert screen_to_world(world_to_screen((0, 0))) == (0, 0), f'{world_to_screen((0, 0))}, {screen_to_world(world_to_screen((0, 0)))}'

        # In world coordinates
        rect = (
            *screen_to_world((0, 0)),
            screen.get_width() / scale,
            screen.get_height() / scale
        )
        # print(rect)

        print(camera_pos != self._last_camera_pos)
        if (
                self._last_scale != scale
                or self._render_surface is None
                or self._render_surface.get_size() != screen.get_size()
                or self._last_camera_pos != camera_pos
        ):
            s = self._render_surface
            self._render_surface = pygame.Surface(screen.get_size())
            if s is not None:
                if self._last_scale != scale:
                    scaled = pygame.transform.smoothscale_by(s, self._last_scale / scale)
                else:
                    scaled = s

                # if self._last_camera_pos is None:
                #     self._last_camera_pos = (screen.get_width() / 2, screen.get_height() / 2)

                self._render_surface.blit(scaled, ((camera_pos[0] - self._last_camera_pos[0]) * scale, (camera_pos[1] - self._last_camera_pos[1]) * scale))
            else:
                pygame.draw.rect(self._render_surface, (255, 0, 0), (10, 10, 10, 10))
            self._last_scale = scale
            self._last_camera_pos = camera_pos
        screen.blit(self._render_surface)

    def close(self):
        self._run = False
        print('Waiting for Grid._render_thread to join')
        self._render_thread.join(1)
        if self._render_thread.is_alive():
            print('\tThread is still alive')
        return
