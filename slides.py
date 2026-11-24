import os
import time

import pygame


# magick -density 400 ~/Downloads/PWS\ prezi.pdf images/%03d.png


class Slides:
    def __init__(self, filename: str = 'slides.txt'):
        def parse_pos(pos: str) -> tuple[int, int, int]:
            pos = pos.strip()
            pos = pos.split(' ')
            if len(pos) != 3:
                raise SyntaxError('Position should have 4 values')

            try:
                x = int(pos[0])
                y = int(pos[1])
                return x, y, int(pos[2])
            except ValueError:
                raise SyntaxError('Position values should be integers')


        start_time = time.time()

        self._image_dir = 'images'

        self._images: list[tuple[pygame.FRect, pygame.Surface]] = []
        self._slides: list[tuple[tuple[int, int, int], str]] = []
        with open(filename) as file:
            for line in file:
                line = line.strip()
                if not line:
                    continue

                if line.startswith('#'):
                    line = line.removeprefix('#').strip()
                    slide = True
                else:
                    slide = False

                pos, _, title = line.partition(':')
                pos = parse_pos(pos)
                title = title.strip()
                if slide:
                    self._slides.append((pos, title))
                else:
                    image = pygame.image.load(os.path.join(self._image_dir, title))
                    if image.get_size() == (4000, 2250):
                        height = (9 / 16) * pos[2]  # Hardcode 16/9 aspect ratio
                    else:
                        height = ((image.get_height() * pos[2]) / image.get_width())
                    # print(image.get_width() / image.get_height(), (pos[2] / height))
                    # assert abs((pos[2] / height) - (image.get_width() / image.get_height())) < 0.01
                    self._images.append((pygame.FRect(pos[0], pos[1], pos[2], height), image.convert()))

        self._slide_cache: dict[int, tuple[tuple[int, int], pygame.Surface]] = {}

        print(f'Loading slides took: {time.time() - start_time}s')

        self._first_render = True
        self._current_slide = 0
        self._previous_keys = (False, False)

    def render(self, screen: pygame.Surface, camera_x: float, camera_y: float, tile_size: float) -> tuple[float, float, float]:
        print(camera_x, camera_y, screen.get_width() / tile_size)

        def set_slide(i: int):
            nonlocal camera_x, camera_y, tile_size
            (x, y, width), title = self._slides[i]
            camera_x = x
            camera_y = y
            tile_size = screen.get_width() / width

            pygame.display.set_caption(title)


        if self._first_render:
            set_slide(0)
            self._first_render = False

        keys = pygame.key.get_pressed()
        if keys[pygame.K_RIGHT] and not self._previous_keys[1]:
            if self._current_slide + 1 < len(self._slides):
                self._current_slide += 1
                set_slide(self._current_slide)
        if keys[pygame.K_LEFT] and not self._previous_keys[0]:
            if self._current_slide > 0:
                self._current_slide -= 1
                set_slide(self._current_slide)
        self._previous_keys = (keys[pygame.K_LEFT], keys[pygame.K_RIGHT])

        for rect, image in self._images:
            r = pygame.Rect(
                (rect.x - camera_x) * tile_size,
                (rect.y - camera_y) * tile_size,
                rect.width * tile_size,
                rect.height * tile_size
            )
            # print(rect.w / rect.h, r.w / r.h)
            if r.colliderect(screen.get_rect()):
                i = id(image)
                if i not in self._slide_cache or self._slide_cache[i][0] != r.size:
                    self._slide_cache[i] = (r.size, pygame.transform.smoothscale(image, r.size))
                    print('Resized image')
                screen.blit(self._slide_cache[i][1], r.topleft)

        return camera_x, camera_y, tile_size
