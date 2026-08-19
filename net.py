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
