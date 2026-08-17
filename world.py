import abc
import enum
import math
import threading

import pygame

import render


class Tile(abc.ABC):
    @abc.abstractmethod
    def render(self, screen: pygame.Surface, x: int, y: int, size_: int) -> None:
        pass

    @staticmethod
    def line_width_from_size(size_: int) -> int:
        w = math.ceil(size_ / (12 + 1))
        if w <= 0:
            return 1
        else:
            return w


class GateType(enum.StrEnum):
    AND = enum.auto()
    NAND = enum.auto()
    NOR = enum.auto()
    OR = enum.auto()
    XNOR = enum.auto()
    XOR = enum.auto()


_gate_cache: dict[tuple[GateType, int], pygame.Surface] = {}


class Gate(Tile):
    def __init__(self, gate_type: GateType, input_a: 'Gate', input_b: 'Gate'):
        self._gate_type = gate_type
        self._input_a = input_a
        self._input_b = input_b

    def render(self, screen: pygame.Surface, x: int, y: int, size_: int) -> None:
        k = (self._gate_type, size_)
        if k not in _gate_cache:
            s = pygame.Surface((size_, size_))
            s.set_colorkey((0, 0, 0))
            render.render(s, str(self._gate_type).upper(), (255, 255, 255), (0, 0), size_, self.line_width_from_size(size_))
            _gate_cache[k] = s
        s = _gate_cache[k]

        screen.blit(s, (x, y))

    def get_activated(self) -> bool:
        return True

    def latch_input(self):
        raise NotImplementedError('latch_input')

    def latch_output(self):
        raise NotImplementedError('latch_output')


class NullGate(Gate):
    def __init__(self, activated=False):
        self._activated = activated

    def render(self, screen: pygame.Surface, x: int, y: int, size_: int) -> None:
        pass

    def get_activated(self) -> bool:
        return self._activated

    def latch_input(self):
        pass

    def latch_output(self):
        pass


WIRES_POSITIONS = [
    (-1, -2), (0, -2), (1, -2),
    (2, -1), (2, 0), (2, 1),
    (1, 2), (0, 2), (-1, 2),
    (-2, 1), (-2, 0), (-2, -1),
]
WIRE_RENDER_POSITION = {
    -2: 0.0,
    -1: 1/3,
    0: 1/2,
    1: 2/3,
    2: 1.0
}


class Wires(Tile):
    def __init__(self):
        self.connections: dict[int, tuple[int, Gate]] = {}

    def render(self, screen: pygame.Surface, x: int, y: int, size_: int) -> None:
        def _angle(a: int, b: int):
            a = a // 3
            b = b // 3
            assert a != b

            delta = (b - a) % 4
            return delta

        wire_width = self.line_width_from_size(size_)

        for from_, (to, gate) in self.connections.items():
            from_x = x + WIRE_RENDER_POSITION[WIRES_POSITIONS[from_][0]] * size_
            from_y = y + WIRE_RENDER_POSITION[WIRES_POSITIONS[from_][1]] * size_
            to_x = x + WIRE_RENDER_POSITION[WIRES_POSITIONS[to][0]] * size_
            to_y = y + WIRE_RENDER_POSITION[WIRES_POSITIONS[to][1]] * size_

            if (from_ // 3) % 2 != 0:
                to_x, from_x = from_x, to_x
                to_y, from_y = from_y, to_y
            # from is now the vertical part,
            # to the horizontal

            if gate.get_activated():
                c = (80, 150, 255)
            else:
                c = (255, 255, 255)

            a = _angle(from_, to)
            print(f'{a=}, from=({from_x / size_}, {from_y / size_}), to=({to_x / size_}, {to_y / size_})')
            if a == 1 or a == 3:
                pygame.draw.line(screen, c, (from_x, from_y), (from_x, to_y), wire_width)
                pygame.draw.line(screen, c, (to_x, to_y), (from_x, to_y), wire_width)
                pygame.draw.circle(screen, c, (from_x, to_y), wire_width)


class Level:
    def __init__(self, screen_size: tuple[int, int]):
        self._level: dict[tuple[int, int], Tile] = {}
        self._gates: list[Gate] = []
        self.camera_x = 0.0  # The top-left of the screen is at this position
        self.camera_y = 0.0
        self.tile_size: float = max(screen_size[0] / 40, screen_size[1] / 40)

        self._last_camera_pos = (self.camera_x, self.camera_y)

        self._render_back_buffer = pygame.Surface(screen_size)
        self._render_front_buffer = pygame.Surface(screen_size)
        self._render_buffer_swap_lock = threading.Lock()

        self._run = True

        self._render_thread = threading.Thread(target=self._render_loop, name='render_thread')
        self._render_thread.start()

    def update(self):
        raise NotImplementedError('Level.update')

    def _render_loop(self):
        g = Gate(GateType.AND, NullGate(), NullGate())
        self._level[(0, 0)] = g

        w = Wires()
        w.connections[0] = (3, g)
        w.connections[1] = (4, g)
        w.connections[2] = (5, g)
        self._level[(1, 0)] = w

        clock = pygame.time.Clock()
        while self._run:
            clock.tick(4)  # 20

            s: pygame.Surface = self._render_back_buffer
            s.fill((30, 0, 0))

            self._render(s)

            with self._render_buffer_swap_lock:
                self._render_front_buffer, self._render_back_buffer = self._render_back_buffer, self._render_front_buffer
                self._last_camera_pos = (self.camera_x, self.camera_y)

    def _render(self, screen: pygame.Surface):
        print('camera position:', self.camera_x, self.camera_y)
        for y_idx in range(-1, math.ceil(screen.get_height() / self.tile_size) + 1):
            y = y_idx * self.tile_size - self.camera_y % 1.0 * self.tile_size
            y_pos = y_idx + math.floor(self.camera_y)
            for x_idx in range(-1, math.ceil(screen.get_width() / self.tile_size) + 1):
                x = x_idx * self.tile_size - self.camera_x % 1.0 * self.tile_size
                x_pos = x_idx + math.floor(self.camera_x)

                # if self._level[()]
                if x_pos == -1 and y_pos == -1:
                    pygame.draw.rect(screen, (255, 255, 255), (x, y, self.tile_size, self.tile_size))
                elif (x_pos, y_pos) in self._level:
                    t = self._level[(x_pos, y_pos)]
                    t.render(screen, round(x), round(y), math.ceil(self.tile_size))

        # raise NotImplementedError('Level._render')

    def update_camera(self, screen: pygame.Surface, dx: float, dy: float, dt: float):
        self.camera_x += dx * dt
        self.camera_y += dy * dt

        with self._render_buffer_swap_lock:
            screen.blit(self._render_front_buffer, (
                (self._last_camera_pos[0] - self.camera_x) * self.tile_size,
                (self._last_camera_pos[1] - self.camera_y) * self.tile_size
            ))
            # screen.blit(self._render_front_buffer,
            #             (self.camera_x - self._last_camera_pos[0], self.camera_y - self._last_camera_pos[1]))

            if screen.get_size() != self._render_front_buffer.get_size():
                self._render_front_buffer = pygame.Surface(screen.get_size())
                print(f'Resized front buffer to size {self._render_front_buffer.get_size()}')

    def stop(self):
        self._run = False
        print('Waiting for render_thread')
        self._render_thread.join()
