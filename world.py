from __future__ import annotations

import abc
import enum
import json
import math
import threading
import typing

import pygame

import net
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

    def serialise(self) -> bytes:
        c = str(self.__class__.__name__).encode('utf-8')
        assert b' ' not in c
        return c + b' ' + self._serialise()

    @abc.abstractmethod
    def _serialise(self) -> bytes:
        pass

    @classmethod
    def _subclasses(cls) -> list[typing.Self]:
        out = []
        for s in cls.__subclasses__():
            out.append(s)
            out += s._subclasses()
        return out

    @classmethod
    def deserialise(cls, data: bytes) -> Tile:
        class_name, _, data = data.partition(b' ')
        class_name = class_name.decode('utf-8')
        assert class_name in Tile._subclasses()

        return globals()[class_name]._deserialise(data)

    @classmethod
    @abc.abstractmethod
    def _deserialise(cls, data: bytes) -> typing.Self:
        pass


class Activation(enum.Enum):
    FLOATING    = enum.auto(), False, (75,  90,  115)
    COMPETING   = enum.auto(), False, (156, 32,  6)
    OFF         = enum.auto(), False, (255, 255, 255)
    PULLED_DOWN = enum.auto(), False, (255, 255, 255)
    PULLED_UP   = enum.auto(), True,  (80,  150, 255)
    ON          = enum.auto(), True,  (80,  150, 255)

    def __new__(cls, value, activated: bool, color: tuple[int, int, int]) -> typing.Self:
        # https://softwareengineering.stackexchange.com/a/440441
        member = object.__new__(cls)
        member._value_ = value
        member.activated = activated
        member.color = color
        return member

    @classmethod
    def from_bool(cls, activated: bool) -> Activation:
        if activated:
            return cls.ON
        else:
            return cls.OFF


class TileWithActivation(Tile, abc.ABC):
    @abc.abstractmethod
    def get_activated(self) -> Activation:
        pass


class GateType(enum.StrEnum):
    AND = enum.auto()
    NAND = enum.auto()
    NOR = enum.auto()
    OR = enum.auto()
    XNOR = enum.auto()
    XOR = enum.auto()


_gate_cache: dict[tuple[GateType, int, tuple[int, int, int]], pygame.Surface] = {}


class Gate(TileWithActivation):
    def __init__(self, gate_type: GateType, input_a: TileWithActivation, input_b: TileWithActivation, rotation: int):
        self._gate_type = gate_type
        self._input_a = input_a
        self._input_b = input_b

        self._rotation = rotation

        self._activation: Activation = Activation.FLOATING
        self._new_activation: Activation = Activation.FLOATING

    def render(self, screen: pygame.Surface, x: int, y: int, size_: int) -> None:
        k = (self._gate_type, size_, self._activation.color)
        if k not in _gate_cache:
            s = pygame.Surface((size_, size_))
            s.set_colorkey((0, 0, 0))
            render.render(s, str(self._gate_type).upper(), self._activation.color, (0, 0), size_, self.line_width_from_size(size_))
            _gate_cache[k] = s
        s = _gate_cache[k]

        if self._rotation != 1:
            s = pygame.transform.rotate(s, (-self._rotation + 1) * 90)
        screen.blit(s, (x, y))

    def get_activated(self) -> Activation:
        return self._activation

    def latch_input(self):
        a: Activation = self._input_a.get_activated()
        b: Activation = self._input_b.get_activated()
        if a == Activation.COMPETING or b == Activation.COMPETING:
            self._new_activation = Activation.COMPETING
            return
        if a == Activation.FLOATING or b == Activation.FLOATING:
            self._new_activation = Activation.FLOATING

        a: bool = a.activated
        b: bool = b.activated
        if self._gate_type == GateType.AND:
            self._new_activation = Activation.from_bool(a and b)
        elif self._gate_type == GateType.NAND:
            self._new_activation = Activation.from_bool(not (a and b))
        elif self._gate_type == GateType.NOR:
            self._new_activation = Activation.from_bool(not (a or b))
        elif self._gate_type == GateType.OR:
            self._new_activation = Activation.from_bool(a or b)
        elif self._gate_type == GateType.XNOR:
            self._new_activation = Activation.from_bool(a is b)
        elif self._gate_type == GateType.XOR:
            self._new_activation = Activation.from_bool(a is not b)
        else:
            raise NotImplementedError(self._gate_type)

    def latch_output(self):
        self._activation = self._new_activation

    def _serialise(self) -> bytes:
        return json.dumps({
            'gate_type': self._gate_type,
            'rotation': self._rotation,

            'activation': self._activation.name,
            'new_activation': self._new_activation.name,
        }).encode('utf-8')

    @classmethod
    def _deserialise(cls, data: bytes) -> typing.Self:
        data = json.loads(json.loads(data.decode('utf-8')))
        tile = cls(GateType(data['gate_type']), NullGate(Activation.COMPETING), NullGate(Activation.COMPETING), data['rotation'])
        tile._activation = Activation.__members__[data['activation']]
        tile._new_activation = Activation.__members__[data['new_activation']]



class NullGate(TileWithActivation):
    def __init__(self, activated: Activation = Activation.OFF):
        self._activated = activated

    def render(self, screen: pygame.Surface, x: int, y: int, size_: int) -> None:
        pass

    def get_activated(self) -> Activation:
        return self._activated

    def _serialise(self) -> bytes:
        return self._activated.name.encode('utf-8')

    @classmethod
    def _deserialise(cls, data: bytes) -> typing.Self:
        return cls(Activation.__members__[data.decode('utf-8')])


class LogicalWire(TileWithActivation):
    def __init__(self, inputs: list[TileWithActivation]):
        self.inputs = inputs
        self._activation = Activation.FLOATING
        self._new_activation = Activation.FLOATING

    def get_activated(self) -> Activation:
        return self._activation

    def render(self, screen: pygame.Surface, x: int, y: int, size_: int) -> None:
        raise ValueError('LogicalWire cannot be rendered')

    def latch_input(self):
        activation = Activation.FLOATING
        for i in self.inputs:
            a = i.get_activated()
            match activation:
                case Activation.FLOATING:
                    activation = a
                case Activation.COMPETING:
                    pass
                case Activation.OFF:
                    if a == Activation.COMPETING or a == Activation.ON:
                        activation = Activation.COMPETING
                case Activation.PULLED_DOWN:
                    if a == Activation.COMPETING:
                        activation = Activation.COMPETING
                    elif a == Activation.OFF:
                        activation = Activation.OFF
                    elif a == Activation.ON:
                        activation = Activation.ON
                    elif a == Activation.PULLED_UP:
                        activation = Activation.COMPETING
                case Activation.PULLED_UP:
                    if a == Activation.COMPETING:
                        activation = Activation.COMPETING
                    elif a == Activation.OFF:
                        activation = Activation.OFF
                    elif a == Activation.ON:
                        activation = Activation.ON
                    elif a == Activation.PULLED_DOWN:
                        activation = Activation.COMPETING
                case Activation.ON:
                    if a == Activation.COMPETING or a == Activation.OFF:
                        activation = Activation.COMPETING

        self._new_activation = activation

    def latch_output(self):
        self._activation = self._new_activation

    def _serialise(self) -> bytes:
        raise ValueError('LogicalWire should not be saved')

    @classmethod
    def _deserialise(cls, data: bytes) -> typing.Self:
        raise ValueError('LogicalWire should not be saved')


class Button(TileWithActivation):
    def __init__(self, latching: bool):
        self._latching = latching
        self._state = False

    def render(self, screen: pygame.Surface, x: int, y: int, size_: int) -> None:
        c = Activation.from_bool(self._state).color
        pygame.draw.circle(screen, c, (x + size_ / 2, y + size_ / 2), size_ / 2, self.line_width_from_size(size_))
        if self._latching:
            pygame.draw.circle(screen, c, (x + size_ / 2, y + size_ / 2), self.line_width_from_size(size_))

    def set_latching(self, latching):
        self._latching = latching
        if not self._latching:
            self._state = False

    def get_activated(self) -> Activation:
        return Activation.from_bool(self._state)

    def mouse_press(self, pressed: bool, clicked: bool):
        if self._latching:
            if clicked:
                self._state = not self._state
        else:
            self._state = pressed

    def _serialise(self) -> bytes:
        return json.dumps({
            'latching': self._latching,
            'state': self._state
        }).encode('utf-8')

    @classmethod
    def _deserialise(cls, data: bytes) -> typing.Self:
        data = json.loads(data.decode('utf-8'))
        tile = cls(data['latching'])
        tile._state = data['state']
        return tile


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
        self.connections: dict[int, tuple[int, TileWithActivation]] = {}

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

            c = gate.get_activated().color

            a = _angle(from_, to)
            # print(f'{a=}, from=({from_x / size_}, {from_y / size_}), to=({to_x / size_}, {to_y / size_})')
            if a == 1 or a == 3:
                pygame.draw.line(screen, c, (from_x, from_y), (from_x, to_y), wire_width)
                pygame.draw.line(screen, c, (to_x, to_y), (from_x, to_y), wire_width)
                pygame.draw.circle(screen, c, (from_x, to_y), wire_width)

    def _serialise(self) -> bytes:
        return json.dumps(
            {from_: to for from_, (to, _) in self.connections.items()}
        ).encode('utf-8')

    @classmethod
    def _deserialise(cls, data: bytes) -> typing.Self:
        data = json.loads(data.decode('utf-8'))
        tile =  cls()
        tile.connections = {from_: (to, NullGate(Activation.COMPETING)) for from_, to in data}
        return tile


class Level:
    def __init__(self, screen_size: tuple[int, int]):
        self._level: dict[tuple[int, int], Tile] = {}
        self._logical_wires: list[LogicalWire] = []
        self._gates: list[Gate] = []
        self.camera_x = 0.0  # The top-left of the screen is at this position
        self.camera_y = 0.0
        self.tile_size: float = max(screen_size[0] / 40, screen_size[1] / 40)

        self._last_camera_pos = (self.camera_x, self.camera_y)
        self._renderer_to_server_queue: list[net.Packet] = []

        self._render_back_buffer = pygame.Surface(screen_size)
        self._render_front_buffer = pygame.Surface(screen_size)
        self._render_buffer_swap_lock = threading.Lock()

        self._run = True

        self._render_thread = threading.Thread(target=self._render_loop, name='render_thread')
        self._render_thread.start()

    def _update(self, packets: list[net.Packet]):
        for packet in packets:
            if isinstance(packet, net.PacketButtonActivate):
                if (t := self._level.get((packet.x, packet.y))) and isinstance(t, Button):
                    t.mouse_press(packet.press, packet.click)
            else:
                raise NotImplementedError(f'Handling packet of type {type(packet)} in Level._update')

        for (x, y), tile in self._level.items():
            if isinstance(tile, Gate):
                tile.latch_input()
        for logical_wire in self._logical_wires:
            logical_wire.latch_input()

        for (x, y), tile in self._level.items():
            if isinstance(tile, Gate):
                tile.latch_output()
        for logical_wire in self._logical_wires:
            logical_wire.latch_output()

    def _render_loop(self):
        b = Button(True)
        self._level[(-1, 0)] = b

        g = Gate(GateType.OR, b, NullGate(), 2)
        self._level[(0, 0)] = g

        w = Wires()
        w.connections[0] = (3, g)
        w.connections[1] = (4, b)
        w.connections[2] = (5, g)
        self._level[(-1, 1)] = w

        last = g
        for i in range(4):
            g = Gate(GateType.XNOR, last, NullGate(), i)
            self._level[(i, 6)] = g
            last = g

        clock = pygame.time.Clock()
        while self._run:
            clock.tick(20)  # 20

            packets, self._renderer_to_server_queue = self._renderer_to_server_queue, []
            self._update(packets)

            s: pygame.Surface = self._render_back_buffer
            s.fill((30, 0, 0))

            camera_x, camera_y = self.camera_x, self.camera_y
            self._render(s, camera_x, camera_y)

            with self._render_buffer_swap_lock:
                self._render_front_buffer, self._render_back_buffer = self._render_back_buffer, self._render_front_buffer
                self._last_camera_pos = (camera_x, camera_y)

    def _render(self, screen: pygame.Surface, camera_x: float, camera_y: float):
        # print('camera position:', self.camera_x, self.camera_y)
        for y_idx in range(-1, math.ceil(screen.get_height() / self.tile_size) + 1):
            y = y_idx * self.tile_size - camera_y % 1.0 * self.tile_size
            y_pos = y_idx + math.floor(camera_y)
            for x_idx in range(-1, math.ceil(screen.get_width() / self.tile_size) + 1):
                x = x_idx * self.tile_size - camera_x % 1.0 * self.tile_size
                x_pos = x_idx + math.floor(camera_x)

                # if self._level[()]
                if x_pos == -1 and y_pos == -1:
                    # pygame.draw.rect(screen, (255, 255, 255), (x, y, self.tile_size, self.tile_size))
                    pass
                elif (x_pos, y_pos) in self._level:
                    t = self._level[(x_pos, y_pos)]
                    t.render(screen, round(x), round(y), math.ceil(self.tile_size))

        # raise NotImplementedError('Level._render')

    def _screen_to_tile_pos(self, x: int, y: int) -> tuple[int, int]:
        x_idx = math.floor(self.camera_x + x / self.tile_size)
        y_idx = math.floor(self.camera_y + y / self.tile_size)
        return x_idx, y_idx

    def update_camera_and_render(self, screen: pygame.Surface, dx: float, dy: float, dt: float):
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

            packets: list[net.Packet] = []

            mouse_pos = pygame.mouse.get_pos(False)
            mouse_press = pygame.mouse.get_pressed(3)
            mouse_click = pygame.mouse.get_just_pressed()

            t_pos = self._screen_to_tile_pos(mouse_pos[0], mouse_pos[1])
            if t := self._level.get(t_pos):
                if isinstance(t, Button):
                    # TODO: The button does not get updated if the mouse press is held down and then the mouse cursor is moved off
                    packets.append(net.PacketButtonActivate(t_pos[0], t_pos[1], mouse_press[0], mouse_click[0]))

            self._renderer_to_server_queue.extend(packets)

    def stop(self):
        self._run = False
        print('Waiting for render_thread')
        self._render_thread.join()
