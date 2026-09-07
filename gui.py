import abc
import math
import typing

import pygame

import cursors
if typing.TYPE_CHECKING:
    import world


events: list[pygame.event.Event] = []  # Written by main.py


class Gui(abc.ABC):
    @abc.abstractmethod
    def __init__(self, screen_size: tuple[int, int]):
        pass

    @abc.abstractmethod
    def update_and_render(self, screen: pygame.Surface, level: world.Level):
        pass


class GuiPan(Gui):
    def __init__(self, screen_size: tuple[int, int]):
        self._drag_start: tuple[tuple[int, int], tuple[int, int]] | None = None

    def update_and_render(self, screen: pygame.Surface, level: world.Level):
        def screen_to_tile_pos(x: int, y: int) -> tuple[int, int]:
            x_idx = math.floor(level.camera_x + x / level.tile_size)
            y_idx = math.floor(level.camera_y + y / level.tile_size)
            return x_idx, y_idx


        mouse_pos = pygame.mouse.get_pos()
        mouse_click = pygame.mouse.get_just_pressed()
        mouse_press = pygame.mouse.get_pressed()

        import world

        gate_pos = screen_to_tile_pos(*mouse_pos)
        t = level.get_tile_at_pos(*gate_pos)
        if self._drag_start is None:
            if t is None:
                if mouse_click[0]:
                    self._drag_start = (mouse_pos, (level.camera_x, level.camera_y))
                if mouse_press[0]:
                    cursors.set_cursor()
                else:
                    cursors.set_cursor(cursors.CursorType.GRAB)

            elif isinstance(t, world.Button):
                cursors.set_cursor(cursors.CursorType.HAND)

            else:
                cursors.set_cursor()
        else:
            cursors.set_cursor(cursors.CursorType.GRABBING)

            level.camera_x = self._drag_start[1][0] + (self._drag_start[0][0] - mouse_pos[0]) / level.tile_size
            level.camera_y = self._drag_start[1][1] + (self._drag_start[0][1] - mouse_pos[1]) / level.tile_size

            if not mouse_press[0]:
                self._drag_start = None


class GuiSimpleWirePlacer(Gui):
    def __init__(self, screen_size: tuple[int, int]):
        self._screen_size = screen_size

        self._mouse_held: tuple[int, int] | None = None

    def update_and_render(self, screen: pygame.Surface, level: world.Level):
        # TODO: Right click to delete wires
        # TODO: Oscilloscope tool
        # TODO: If holding shift over a tile which the oscilloscope can be used on, change cursor to question mark

        def screen_to_tile_pos(x: int, y: int) -> tuple[int, int]:
            x_idx = math.floor(level.camera_x + x / level.tile_size)
            y_idx = math.floor(level.camera_y + y / level.tile_size)
            return x_idx, y_idx

        def wire_angle(a: int, b: int):
            a = a // 3
            b = b // 3

            delta = (b - a) % 4
            return delta

        import world

        mouse_pos = pygame.mouse.get_pos()
        mouse_press = pygame.mouse.get_pressed(3)
        focused = pygame.mouse.get_focused()

        if focused:
            grid_color = (60, 0, 0)
            mouse_tile_pos = screen_to_tile_pos(*mouse_pos)
            for x in range(-1, 2):
                for y in range(-1, 2):
                    draw_x = round((mouse_tile_pos[0] + x - level.camera_x) * level.tile_size)
                    draw_y = round((mouse_tile_pos[1] + y - level.camera_y) * level.tile_size)
                    pygame.draw.line(screen, grid_color,
                                     (draw_x, draw_y),
                                     (draw_x + level.tile_size, draw_y),
                                     world.Tile.line_width_from_size(round(level.tile_size))
                                     )
                    pygame.draw.line(screen, grid_color,
                                     (draw_x, draw_y),
                                     (draw_x, draw_y + level.tile_size),
                                     world.Tile.line_width_from_size(round(level.tile_size))
                                     )

        if not mouse_press[0]:
            self._mouse_held = None

        mouse_wire_pos_x = math.floor(level.camera_x * 6 + (mouse_pos[0] + level.tile_size / 12) * 6 / level.tile_size)
        if mouse_wire_pos_x % 6 == 1:
            mouse_wire_pos_x -= 1
        elif mouse_wire_pos_x % 6 == 5:
            mouse_wire_pos_x += 1
        mouse_wire_pos_y = math.floor(level.camera_y * 6 + (mouse_pos[1] + level.tile_size / 12) * 6 / level.tile_size)
        if mouse_wire_pos_y % 6 == 1:
            mouse_wire_pos_y -= 1
        elif mouse_wire_pos_y % 6 == 5:
            mouse_wire_pos_y += 1

        empty = (tile := level.get_tile_at_pos(mouse_wire_pos_x // 6, mouse_wire_pos_y // 6)) is None or isinstance(tile, world.Wires)
        if mouse_wire_pos_x % 6 == 0 or mouse_wire_pos_y % 6 == 0:
            empty = True

        if (
                not (mouse_wire_pos_x % 6 == 0 and mouse_wire_pos_y % 6 == 0)
                and focused
                and empty
        ):
            if mouse_press[0] and self._mouse_held is None:
                self._mouse_held = (mouse_wire_pos_x, mouse_wire_pos_y)

            if self._mouse_held is not None and (mouse_wire_pos_x % 6 == 0 or mouse_wire_pos_y % 6 == 0):
                def pos_to_angle(pos: tuple[int, int]) -> int:
                    pos_to_offset = {
                        0: -2,
                        2: -1,
                        3: 0,
                        4: 1,
                        6: 2
                    }
                    return world.WIRES_POSITIONS.index((
                        pos_to_offset[pos[0]],
                        pos_to_offset[pos[1]]
                    ))

                def mod_coords(from_: tuple[int, int], to: tuple[int, int]) -> tuple[tuple[int, int], tuple[int, int]]:
                    aa = []
                    ba = []
                    for i in range(2):
                        a = from_[i] % 6
                        b = to[i] % 6
                        if a == 0 and from_[i] > to[i]:
                            a = 6
                        if b == 0 and to[i] > from_[i]:
                            b = 6
                        aa.append(a)
                        ba.append(b)
                    return tuple(aa), tuple(ba)  # noqa

                from_, to = mod_coords(
                    (self._mouse_held[0], self._mouse_held[1]),
                    (mouse_wire_pos_x, mouse_wire_pos_y)
                )
                to_angle = pos_to_angle(to)
                try:
                    from_angle = pos_to_angle(from_)
                except ValueError:
                    from_angle = world.Wires.opposite_angle(to_angle)

                # print(f'{from_=} {from_angle=}, {to=} {to_angle=}')

                tile_pos = (
                    min(self._mouse_held[0], mouse_wire_pos_x) // 6,
                    min(self._mouse_held[1], mouse_wire_pos_y) // 6
                )

                a = wire_angle(from_angle, to_angle)
                is_parallel_if_should_be = not (a == 2 and from_angle % 3 + to_angle % 3 != 2)
                if a != 0 and is_parallel_if_should_be:
                    w = level.get_tile_at_pos(*tile_pos)
                    if w is None or not isinstance(w, world.Wires):
                        c = {}
                    else:
                        c = w.connections.copy()
                    del w

                    if from_angle in c and c[from_angle][0] not in c:
                        c[c[from_angle][0]] = (from_angle, c[from_angle][1])

                    if not (to_angle in c and c[to_angle][0] == from_angle):
                        if from_angle in c and to_angle not in c:
                            c[to_angle] = (from_angle, world.NullGate())
                        else:
                            c[from_angle] = (to_angle, world.NullGate())
                        w = world.Wires()
                        w.connections = c
                        level.place_tile_at_pos(tile_pos[0], tile_pos[1], w)
                        self._mouse_held = (mouse_wire_pos_x, mouse_wire_pos_y)

                        print(f'Made a connection: {from_=} {from_angle=}, {to=} {to_angle=}')

            # self._render_wires.connections[10] = (4, world.NullGate())
            # self._render_wires.render(screen, round((mouse_tile_x - camera_x) * tile_size), round((mouse_tile_y - camera_y) * tile_size), math.ceil(tile_size))

            pygame.draw.circle(
                screen, world.Activation.OFF.color,
                (
                    round((mouse_wire_pos_x / 6 - level.camera_x) * level.tile_size),
                    round((mouse_wire_pos_y / 6 - level.camera_y) * level.tile_size)
                ),
                world.Wires.line_width_from_size(round(level.tile_size))
            )


class GuiGatePlacer(Gui):
    def __init__(self, screen_size: tuple[int, int]):
        self._screen_size = screen_size

        import world
        self._gate_type: world.GateType | None = None

        self._rotation = 0
        self._gate_input = world.NullGate()
        # TODO: Support placing buttons
        self._render_gate = world.Gate(world.GateType.AND, self._gate_input, self._gate_input, self._rotation)

    def _set_render_tile_activation(self, gate_activation: world.Activation):
        self._gate_input._activated = gate_activation
        self._render_gate.latch_input()
        self._render_gate.latch_output()

    def update_and_render(self, screen: pygame.Surface, level: world.Level):
        import world

        q_pressed = False
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    if event.mod & pygame.KMOD_SHIFT:
                        self._rotation -= 1
                    else:
                        self._rotation += 1
                elif event.key == pygame.K_q:
                    q_pressed = True


        def screen_to_tile_pos(x: int, y: int) -> tuple[int, int]:
            x_idx = math.floor(level.camera_x + x / level.tile_size)
            y_idx = math.floor(level.camera_y + y / level.tile_size)
            return x_idx, y_idx


        mouse_pos = pygame.mouse.get_pos()
        mouse_click = pygame.mouse.get_just_pressed()

        gate_pos = screen_to_tile_pos(*mouse_pos)

        if q_pressed:
            t = level.get_tile_at_pos(*gate_pos)
            if t is not None and isinstance(t, world.Gate):
                self._render_gate._gate_type = t._gate_type
                self._rotation = t.rotation

        self._set_render_tile_activation(world.Activation.FLOATING)

        self._render_gate.rotation = self._rotation
        self._render_gate.render(
            screen,
            round((gate_pos[0] - level.camera_x) * level.tile_size),
            round((gate_pos[1] - level.camera_y) * level.tile_size),
            math.ceil(level.tile_size)
        )

        if mouse_click[0]:
            level.place_tile_at_pos(
                gate_pos[0], gate_pos[1],
                self._render_gate  # level makes a copy
            )
        elif mouse_click[2]:
            level.place_tile_at_pos(gate_pos[0], gate_pos[1], None)
