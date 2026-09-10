from __future__ import annotations

import abc
import io
import json
import socket
import typing

# Inspired by Factorio: https://www.factorio.com/blog/post/fff-147#:~:text=Clients%20receive%20merged%20package%20once%20per%20tick


class Packet(abc.ABC):
    @abc.abstractmethod
    def _serialise(self) -> bytes:
        pass

    def serialise(self) -> bytes:
        c = str(self.__class__.__name__).encode('utf-8')
        assert b' ' not in c
        return c + b' ' + self._serialise()

    @classmethod
    def _subclasses(cls) -> list[typing.Self]:
        out = []
        for s in cls.__subclasses__():
            out.append(s)
            out += s._subclasses()
        return out

    @classmethod
    def deserialise(cls, data: bytes) -> Packet:
        class_name, _, data = data.partition(b' ')
        class_name = class_name.decode('utf-8')
        assert class_name in (c.__name__ for c in cls._subclasses()), cls._subclasses()

        return globals()[class_name]._deserialise(data)

    @classmethod
    @abc.abstractmethod
    def _deserialise(cls, data: bytes) -> typing.Self:
        pass


class PacketButtonActivate(Packet):
    def __init__(self, x: int, y: int, press: bool, click: bool):
        self.x = x
        self.y = y
        self.press = press
        self.click = click

    def _serialise(self) -> bytes:
        return json.dumps({
            'x': self.x,
            'y': self.y,
            'press': self.press,
            'click': self.click
        }).encode('ascii')

    @classmethod
    def _deserialise(cls, data: bytes) -> typing.Self:
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

    def _serialise(self) -> bytes:
        return json.dumps({
            'x': self.x,
            'y': self.y,
            'tile': self.tile.serialise().decode('utf-8')
        }).encode('utf-8')

    @classmethod
    def _deserialise(cls, data: bytes) -> typing.Self:
        import world

        data = json.loads(data.decode('utf-8'))
        return cls(data['x'], data['y'], world.Tile.deserialise(data['tile'].encode('utf-8')))


class PacketTileRemove(Packet):
    def __init__(self, x: int , y: int):
        self.x = x
        self.y = y

    def _serialise(self) -> bytes:
        return json.dumps({
            'x': self.x,
            'y': self.y,
        }).encode('utf-8')

    @classmethod
    def _deserialise(cls, data: bytes) -> typing.Self:
        data = json.loads(data.decode('utf-8'))
        return cls(data['x'], data['y'])


_CLIENT_HELLO = b'TransistorBasedClient'  # VERSION: u16 u16 u16
_SERVER_HELLO = b'TransistorBasedServer'


VERSION = (0, 0, 1)
_version = b''.join(v.to_bytes(2, 'big') for v in VERSION)


class NetServer:
    def __init__(self, hostname: str, port: int):
        self._server_socket = socket.create_server((hostname, port), reuse_port=True)
        # self._server_socket.setsockopt(socket.AF_INET, socket.SOCK_NONBLOCK, True)
        self._server_socket.settimeout(0)

        self._clients: list[NetServerClient] = []

    def update(self, new_packets: list[Packet]) -> list[Packet]:
        try:
            client_socket, client_address = self._server_socket.accept()
            client_socket.settimeout(0)
            print(f'Client connected from address: {client_address!r}')
            self._clients.append(NetServerClient(client_socket))
        except BlockingIOError:
            pass

        out = []
        i = 0
        while i < len(self._clients):
            c = self._clients[i]

            p = c.update(new_packets)
            if type(p) is str:
                self._clients.pop(i)
                print(f'Disconnecting client {c}, reason: {p}')
                c._s.close()
                continue

            out += p
            i += 1

        return out


class QueueBuffer:
    def __init__(self):
        self._buffer: list[bytes] = []
        self._length = 0

    def write_to_end(self, data: bytes) -> None:
        self._buffer.append(data)
        self._length += len(data)

    def write_to_start(self, data: bytes) -> None:
        self._buffer.insert(0, data)
        self._length += len(data)

    def try_read_from_start(self, length: int) -> bytes | None:
        if length > self._length:
            return None

        b = io.BytesIO()
        have = 0
        while self._buffer:
            if length - have < len(self._buffer[0]):
                b.write(self._buffer[0][:length - have])
                self._buffer[0] = self._buffer[0][length - have:]
                self._length -= length - have
                return b.getvalue()
            else:
                b.write(self._buffer[0])
                have += len(self._buffer[0])
                self._length -= len(self._buffer[0])
                self._buffer.pop(0)

        return b.getvalue()

    def read_from_start(self, length: int) -> bytes:
        if self._length == 0 or length == 0:
            return b''
        b = self.try_read_from_start(min(length, self._length))
        assert b is not None
        return b

    def __len__(self) -> int:
        return self._length


class PacketIO:
    def __init__(self, s: socket.socket, max_send_buffer_length: int = 65536):
        self._s = s

        self._buffer = QueueBuffer()
        self._new_packets: list[Packet] = []
        self._packets: list[Packet] = []
        self._length: int | None = None
        self._send_buffer = QueueBuffer()
        self._max_send_buffer_length = max_send_buffer_length

    def update(self, send_packets: list[Packet]) -> list[Packet] | str:
        try:
            while b := self._s.recv(2048):
                # print(f'Received {len(b)} bytes')
                self._buffer.write_to_end(b)
        except BlockingIOError:
            pass
        except ConnectionError as e:
            return f'Error while reading: {e!r}'

        while True:
            if self._length is None:
                self._length = self._buffer.try_read_from_start(4)
                if self._length is None:
                    break

            length = int.from_bytes(self._length, byteorder='big')
            # print(f'Packet size: {length}')
            if length == 0:
                self._packets.extend(self._new_packets)
                self._new_packets = []
                self._length = None

            else:
                packet = self._buffer.try_read_from_start(length)
                if packet is None:
                    break
                self._length = None
                self._new_packets.append(Packet.deserialise(packet))

        for packet in send_packets:
            s = packet.serialise()
            self._send_buffer.write_to_end(len(s).to_bytes(4, 'big') + s)
            if len(self._send_buffer) > self._max_send_buffer_length:
                return 'Send buffer overflow'
        self._send_buffer.write_to_end(b'\x00\x00\x00\x00')

        while p := self._send_buffer.read_from_start(4096):
            try:
                l = self._s.send(p)
                if l < len(p):
                    self._send_buffer.write_to_start(p[l:])
                    break
            except BlockingIOError:
                self._send_buffer.write_to_start(p)
                break
            except ConnectionError as e:
                return f'Error while sending: {e!r}'

        # if s and len(self._send_buffer) == 0:

        p = self._packets
        if send_packets or p:
            print(f'PacketIO: send_packets: {send_packets}, received: {p}')
        self._packets = []
        return p

class NetServerClient:
    def __init__(self, s: socket.socket):
        self._s = s
        self._state = 0
        self._buffer = bytes()

        self._packet_io = PacketIO(s)

    def update(self, send_packets: list[Packet]) -> list[Packet] | str:
        if self._state == 0:
            w = len(_CLIENT_HELLO) + len(_version)
            if len(self._buffer) < w:
                try:
                    self._buffer += self._s.recv(w - len(self._buffer))
                except BlockingIOError:
                    pass
                # TODO: Handle IO errors
            else:
                print('Server received client hello')
                if self._buffer != _CLIENT_HELLO + _version:
                    return f'Incorrect client hello {self._buffer!r}, expected: {_CLIENT_HELLO + _version}'
                self._state = 1
                self._buffer = _SERVER_HELLO + _version
        elif self._state == 1:
            try:
                sent = self._s.send(self._buffer)
            except BlockingIOError:
                sent = 0
            self._buffer = self._buffer[sent:]
            if len(self._buffer) == 0:
                self._state = 2

        elif self._state == 2:
            return self._packet_io.update(send_packets)

        else:
            raise NotImplementedError(self._state)

        return []


class NetClient:  # TODO: This class is basically the same as NetServerClient
    def __init__(self, s: socket.socket):
        self._s = s
        self._state = 0
        self._buffer = _CLIENT_HELLO + _version

        self._packet_io = PacketIO(s)

    def update(self, send_packets: list[Packet]) -> list[Packet] | str:
        if self._state == 0:
            try:
                sent = self._s.send(self._buffer)
            except BlockingIOError:
                sent = 0
            self._buffer = self._buffer[sent:]
            if len(self._buffer) == 0:
                self._state = 1

        elif self._state == 1:
            w = len(_SERVER_HELLO) + len(_version)
            if len(self._buffer) < w:
                try:
                    self._buffer += self._s.recv(w - len(self._buffer))
                except BlockingIOError:
                    pass
                # TODO: Handle IO errors
            else:
                print('Client received server hello')
                if self._buffer != _SERVER_HELLO + _version:
                    return f'Incorrect server hello {self._buffer!r}'
                self._state = 2

        elif self._state == 2:
            return self._packet_io.update(send_packets)

        else:
            raise NotImplementedError(self._state)

        return []


if __name__ == '__main__':
    b = QueueBuffer()
    for _ in range(10):
        b.write_to_end(b'a')
    assert len(b) == 10
    assert b.read_from_start(10) == b'a' * 10
