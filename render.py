from __future__ import annotations

import math

import pygame

try:
    import pygame.gfxdraw

    def _draw_filled_polygon(screen: pygame.Surface, color, points: list[tuple[int, int]]):
        pygame.gfxdraw.aapolygon(screen, points, color)
        pygame.gfxdraw.filled_polygon(screen, points, color)
except ImportError:
    def _draw_filled_polygon(screen: pygame.Surface, color, points: list[tuple[int, int]]):
        pygame.draw.polygon(screen, color, points)


def _parse_expression(expr: str) -> float:
    def n() -> str | None:
        nonlocal expr
        out = ''
        tokens = '/+-'
        while expr and expr[0] not in tokens:
            out += expr[0]
            expr = expr[1:]
        if not out and expr and expr[0] in tokens:
            c = expr[0]
            expr = expr[1:]
            return c
        return out or None

    tokens = []
    while c := n():
        tokens.append(c)

    def parse_add() -> float:
        nonlocal tokens
        lhs = parse_div()
        if tokens and tokens[0] == '+':
            tokens = tokens[1:]
            rhs = parse_div()
            return lhs + rhs
        if tokens and tokens[0] == '-':
            tokens = tokens[1:]
            rhs = parse_div()
            return lhs - rhs
        return lhs

    def parse_div() -> float:
        nonlocal tokens
        lhs = parse_int()
        if tokens and tokens[0] == '/':
            tokens = tokens[1:]
            rhs = parse_int()
            return lhs / rhs
        return lhs

    def parse_int() -> float:
        nonlocal tokens
        t = tokens[0]
        tokens = tokens[1:]
        return int(t)

    return parse_add()


def render_path(screen: pygame.Surface, path: str, color, pos, scale: float, stroke_width: int = 1):
    def screen_pos(p: tuple[float, float]) -> tuple[float, float]:
        return round(pos[0] + p[0] * scale), round(pos[1] + p[1] * scale)

    def render_capped_line(color, from_, to, width):
        if width <= 2:
            pygame.draw.aaline(screen, color, from_, to, width)
            return

        pygame.draw.circle(screen, color, from_, width // 2 - 1)
        pygame.draw.circle(screen, color, to, width // 2 - 1)

        angle = math.atan2(from_[0] - to[0], from_[1] - to[1])
        dx = math.cos(angle) * stroke_width / 2
        dy = -math.sin(angle) * stroke_width / 2

        _draw_filled_polygon(screen, color, [
            (from_[0] - dx, from_[1] - dy),
            (from_[0] + dx, from_[1] + dy),
            (to[0] + dx, to[1] + dy),
            (to[0] - dx, to[1] - dy),
        ])

    x = 0
    y = 0
    ox, oy = x, y
    for l in path.split('\n'):
        l, _, _ = l.partition('#')
        l = l.strip()
        if not l:
            continue
        if l == 'R':
            render_capped_line(color, screen_pos((x, y)), screen_pos((ox, oy)), stroke_width)
            x, y = ox, oy
            continue

        command, cx, cy = l.split(' ')
        cx = _parse_expression(cx)
        cy = _parse_expression(cy)

        if command == 'M':
            x = cx
            y = cy
            ox, oy = x, y
        elif command == 'L':
            render_capped_line(color, screen_pos((x, y)), screen_pos((cx, cy)), stroke_width)
            x = cx
            y = cy
        elif command == 'l':
            render_capped_line(color, screen_pos((x, y)), screen_pos((x + cx, y + cy)), stroke_width)
            x += cx
            y += cy


_render_file_cache: dict[str, str] = {}


def render(screen: pygame.Surface, name: str, color, pos, scale: float, stroke_width: int = 1) -> None:
    global _render_file_cache
    if name not in _render_file_cache:
        with open(f'./gates/{name}.txt') as file:
            _render_file_cache[name] = file.read()
    render_path(screen, _render_file_cache[name], color, pos, scale, stroke_width=stroke_width)


if __name__ == '__main__':
    assert abs(_parse_expression('1/3') - 0.3333333) < 0.01
    assert abs(_parse_expression('1/6') - 0.1666666) < 0.01
    assert abs(_parse_expression('1/2-1/12') - (1 / 2 - 1 / 12)) < 0.01

    pygame.init()
    screen = pygame.display.set_mode((800, 800))

    render(screen, 'NAND', (255, 255, 255), (0, 0), screen.get_width(), stroke_width=round(screen.get_width() / 13))

    # render_path(screen, '''
    # M 0 1/3
    # L 1/10 1/3

    # M 0 2/3
    # L 1/10 2/3

    # M 2/10 1/6
    # L 5/6 1/2
    # L 2/10 5/6
    # L 3/10 1/2
    # R

    # # X part
    # M 1/10 1/6
    # L 2/10 1/2
    # L 1/10 5/6

    # # # Not bubble
    # # M 5/6 1/2
    # # L 11/12 1/2-1/12
    # # L 1 1/2
    # # L 11/12 1/2+1/12
    # # R

    # M 5/6 1/2
    # l 1/6 0

    # # Square outline
    # M 0 0
    # L 1 0
    # L 1 1
    # L 0 1
    # R
    # ''', (255, 100, 100), (50, 50), 100)

    clock = pygame.time.Clock()
    while not pygame.event.get(pygame.QUIT):
        clock.tick(60)
        pygame.display.update()
    exit(0)

    import sys, os
    if len(sys.argv) != 5:
        raise ValueError(f'Expected four arguments ({sys.argv[0]} output.png size stroke_width border)')
    out_path = sys.argv[1]
    size = int(sys.argv[2])
    stroke_width = int(sys.argv[3])
    border = int(sys.argv[4])

    gate_files = os.listdir('gates/')
    s = pygame.Surface((size * len(gate_files) + 2 * len(gate_files) * border, size + 2 * border))

    for i, filename in enumerate(gate_files):
        render(s, filename.removesuffix('.txt'), (255, 255, 255), (i * size + border + 2 * border * i, border), size, stroke_width=stroke_width)

    pygame.image.save(s, out_path)

    pygame.quit()

