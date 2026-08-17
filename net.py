import abc
import json
import typing


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
