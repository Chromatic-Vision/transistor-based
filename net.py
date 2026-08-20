import abc
import json
import typing

# Inspired by Factorio: https://www.factorio.com/blog/post/fff-147#:~:text=Clients%20receive%20merged%20package%20once%20per%20tick


class Packet(abc.ABC):
    @abc.abstractmethod
    def serialise(self) -> bytes:
        pass

    @classmethod
    @abc.abstractmethod
    def deserialise(cls, data: bytes) -> typing.Self:
        pass


class PacketButtonActivate(Packet):
    def __init__(self, x: int, y: int, press: bool, click: bool):
        self.x = x
        self.y = y
        self.press = press
        self.click = click

    def serialise(self) -> bytes:
        return json.dumps({
            'x': self.x,
            'y': self.y,
            'press': self.press,
            'click': self.click
        }).encode('ascii')

    def deserialise(cls, data: bytes) -> typing.Self:
        j = json.loads(data.decode('ascii'))
        return PacketButtonActivate(
            x=j['x'],
            y=j['y'],
            press=j['press'],
            click=j['click'],
        )


# Make a way for marking which packets were from a single frame,
# When changing a wire or a gate type, remove it and place a new one, all in a single frame.

if typing.TYPE_CHECKING:
    import world  # Would cause a recursive import


class PacketTilePlace(Packet):
    def __init__(self, x: int, y: int, tile: world.Tile):
        self.x = x
        self.y = y
        self.tile = tile

    def serialise(self) -> bytes:
        return json.dumps({
            'x': self.x,
            'y': self.y,
            'tile': self.tile.serialise()
        }).encode('utf-8')

    @classmethod
    def deserialise(cls, data: bytes) -> typing.Self:
        import world

        data = json.loads(data.decode('utf-8'))
        return cls(data['x'], data['y'], world.Tile.deserialise(data['tile']))


class PacketTileRemove(Packet):
    def __init__(self, x: int , y: int):
        self.x = x
        self.y = y

    def serialise(self) -> bytes:
        return json.dumps({
            'x': self.x,
            'y': self.y,
        }).encode('utf-8')

    @classmethod
    def deserialise(cls, data: bytes) -> typing.Self:
        data = json.loads(data.decode('utf-8'))
        return cls(data['x'], data['y'])
