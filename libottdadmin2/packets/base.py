#
# This file is part of libottdadmin2
#
# License: http://creativecommons.org/licenses/by-nc-sa/3.0/
#

from functools import lru_cache, wraps
from itertools import chain

from libottdadmin2.exceptions import InvalidHeaderError, UnknownPacketError, InvalidPacketLengthError, \
    PacketExhaustedError
from libottdadmin2.util import ensure_binary, ensure_text

from struct import Struct

from typing import Tuple, Any, Union, Iterable, Optional, NamedTuple

STRUCT_FORMAT_PREFIXES = {'@', '=', '<', '>', '!'}


def new_struct(fmt):
    if fmt[0] in STRUCT_FORMAT_PREFIXES:  # pragma: no cover
        fmt = fmt[1:]
    fmt = '<%s' % fmt
    return _new_struct(fmt)


@lru_cache(maxsize=128)
def _new_struct(fmt):
    return Struct(fmt)


HEADER = new_struct("HB")


# Easy mapping for stream data.
# Since OpenTTD prefers unsigned variants for sending, we have a preference for those types as well.
TYPE_MAPPING = {
    int: 'I',
    bool: 'B',
    'bool': 'B',
    'byte': 'B',
    'sint': 'i',
    'uint': 'I',
    'short': 'h',
    'ushort': 'H',
    'long': 'l',
    'ulong': 'L',
    'long long': 'q',
    'ulong long': 'Q',
}


def int_validator(_min: Optional[int] = None, _max: Optional[int] = None, bits: Optional[int] = None,
                  signed: Optional[bool] = False):
    if bits:
        _min = 0 if not signed else -((2 ** bits) // 2)
        _max = (2 ** bits) if not signed else ((2 ** bits) // 2) - 1

    def _inner(func):
        @wraps(func)
        def __inner(self, *values):
            if _min is not None:
                if any(x < _min for x in values):  # pragma: no cover
                    raise ValueError("Value may not be smaller than %d" % _min)
            if _max is not None:
                if any(x > _max for x in values):  # pragma: no cover
                    raise ValueError("Value may not be greater than %d" % _max)
            return func(self, *values)
        return __inner
    return _inner


def check_length(value, max_length, name="Value", include_null=True):
    length = len(value) + (1 if include_null else 0)
    if length > max_length:  # pragma: no cover
        raise ValueError("%s may not be longer than %d characters (%d)" % (name, max_length, length))
    return value


def check_tuple_length(value, min_length=0, max_length=0, name="Value"):
    length = len(value)
    if length < min_length:
        raise ValueError("%s must be longer than %d items (%d)" % (name, min_length, length))
    elif length > max_length:
        raise ValueError("%s must be smaller than %d items (%d)" % (name, max_length, length))
    return value


class PacketData(NamedTuple):
    pass


class Packet:
    __slots__ = [
        '_index',
        '_header',
        '_buffer',
        '_fmt',
        '_val',
    ]
    packet_id = 0
    fields = []
    data = None

    _registry = {}

    def __init__(self, buffer=None, hdr=None):
        self._index = 0
        self._buffer = buffer or b''
        self._header = hdr
        self._fmt = []
        self._val = []

    def __str__(self):
        return self.__class__.__name__

    def __repr__(self):
        return "<%s (%d): %r>" % (
            str(self),
            self.packet_id,
            b''.join([self.header, self.buffer])
        )

    def reset(self, clear=False):
        self._index = 0
        if clear:
            self._buffer = b''

    @property
    def has_available_data(self):
        return self._index < len(self._buffer)

    @property
    def header(self):
        if not self._header:
            self._header = HEADER.pack(len(self.buffer) + HEADER.size, self.packet_id)
        return self._header

    @property
    def buffer(self):
        self._write_process()
        return self._buffer

    @staticmethod
    def register(klass):
        Packet._registry[klass.packet_id] = klass
        if not getattr(klass, 'data', None):
            fields = [(x, Any) if not (isinstance(x, (list, tuple)) and len(x) == 2) else x
                      for x in klass.fields]
            klass.data = NamedTuple(klass.__name__, fields)
        return klass

    @classmethod
    def create(cls, _out: Optional[Tuple[Any, ...]] = None, **kwargs):
        if _out and isinstance(_out, cls.data):
            # noinspection PyProtectedMember, PyUnresolvedReferences
            kwargs = dict(_out._asdict())
        obj = cls()
        obj.encode(**kwargs)
        return obj

    def write_to_buffer(self):
        return b''.join([self.header, self.buffer])

    @staticmethod
    def from_buffer(buffer=None, hdr=None, validate=True):
        if buffer is None:
            raise ValueError("Data must be passed")
        if not hdr:
            hdr = buffer[0:HEADER.size]
            buffer = buffer[HEADER.size:]
        if validate and len(hdr) != HEADER.size:
            raise InvalidHeaderError("Header length does not match expected length: %d / %d" % (
                len(hdr),
                HEADER.size
            ))
        length, pid = HEADER.unpack(hdr)
        if validate and length and length != (len(buffer) + HEADER.size):
            raise InvalidPacketLengthError("Invalid packet length: %d / %d" % (
                len(buffer) + HEADER.size,
                length
            ))
        if pid not in Packet._registry:
            raise UnknownPacketError("Unknown packet with packet id %d" % pid)
        klass = Packet._registry[pid]
        obj = klass(buffer, hdr)
        return obj

    @staticmethod
    def extract(buffer) -> Tuple[bool, int, Any]:
        if len(buffer) < HEADER.size:
            return False, 0, None
        hdr = buffer[0:HEADER.size]
        length, pid = HEADER.unpack(hdr)
        if len(buffer) < length:
            return False, 0, None
        if pid not in Packet._registry:
            return False, length, None
        klass = Packet._registry[pid]
        obj = klass(buffer[HEADER.size:length], hdr)
        return True, length, obj

    @staticmethod
    def from_name_and_buffer(name, buffer):
        for klass in Packet._registry.values():
            if klass.__name__ == name:
                obj = klass(buffer)
                return obj, obj.decode()
        return None, None

    def _write_add(self, fmt, *data):
        self._fmt.append(fmt)
        self._val.append(data)

    def _write_simple(self, fmt, *values):
        values = list(map(int, values))
        return self._write_add(fmt * len(values), *values)

    def _write_process(self):
        if not self._fmt:
            return
        fmt = ''.join(self._fmt)
        data = list(chain(*self._val))
        obj = new_struct(fmt)
        self._buffer += obj.pack(*data)
        self._index += obj.size
        self._fmt = []
        self._val = []

    @int_validator(_min=0, _max=1)
    def write_bool(self, *values: bool):
        self._write_simple('B', *values)

    @int_validator(bits=8, signed=False)
    def write_byte(self, *values: int):
        self._write_simple('B', *values)

    @int_validator(bits=16, signed=True)
    def write_sshort(self, *values: int):
        self._write_simple('h', *values)

    @int_validator(bits=16, signed=False)
    def write_ushort(self, *values: int):
        self._write_simple('H', *values)

    @int_validator(bits=32, signed=True)
    def write_sint(self, *values: int):
        self._write_simple('i', *values)

    @int_validator(bits=32, signed=False)
    def write_uint(self, *values: int):
        self._write_simple('I', *values)

    @int_validator(bits=32, signed=True)
    def write_slong(self, *values: int):
        self._write_simple('l', *values)

    @int_validator(bits=32, signed=False)
    def write_ulong(self, *values: int):
        self._write_simple('L', *values)

    @int_validator(bits=64, signed=True)
    def write_longlong(self, *values: int):
        self._write_simple('q', *values)

    @int_validator(bits=64, signed=False)
    def write_ulonglong(self, *values: int):
        self._write_simple('Q', *values)

    def write_str(self, *values: str):
        self._write_process()
        encoded = b'\x00'.join(map(ensure_binary, values)) + b'\x00'
        self._buffer += encoded
        self._index += len(encoded)

    def _read_batch(self, fmt) -> Tuple[Any, ...]:
        obj = new_struct(fmt)
        size_remaining = len(self._buffer) - self._index
        if obj.size > size_remaining:
            raise PacketExhaustedError("%d bytes requested, but only %d available" % (obj.size, size_remaining))
        new_index = self._index + obj.size
        ret = obj.unpack(self._buffer[self._index:new_index])
        self._index = new_index
        return ret

    def read_data(self, types: Iterable[Union[str, type]]) -> Iterable[Any]:
        batch = []
        ret = []
        for typ in types:
            if typ == str:
                if batch:
                    ret.extend(self._read_batch(''.join(batch)))
                    batch = []
                ind = self._buffer.index(b'\x00', self._index)
                ret.append(ensure_text(self._buffer[self._index:ind]))
                self._index = ind + 1
            else:
                batch.append(TYPE_MAPPING.get(typ, typ))
                continue
        if batch:
            ret.extend(self._read_batch(''.join(batch)))
        return ret

    def _read_simple(self, typ: Union[str, type], amount: int) -> Iterable[Any]:
        return self.read_data([typ] * amount)

    def read_bool(self, amount: int = 1) -> Iterable[bool]:
        return tuple(map(bool, self._read_simple('B', amount)))

    def read_byte(self, amount: int = 1) -> Iterable[int]:
        return self._read_simple('B', amount)

    def read_sshort(self, amount: int = 1) -> Iterable[int]:
        return self._read_simple('h', amount)

    def read_ushort(self, amount: int = 1) -> Iterable[int]:
        return self._read_simple('H', amount)

    def read_sint(self, amount: int = 1) -> Iterable[int]:
        return self._read_simple('i', amount)

    def read_uint(self, amount: int = 1) -> Iterable[int]:
        return self._read_simple('I', amount)

    def read_slong(self, amount: int = 1) -> Iterable[int]:
        return self._read_simple('l', amount)

    def read_ulong(self, amount: int = 1) -> Iterable[int]:
        return self._read_simple('L', amount)

    def read_longlong(self, amount: int = 1) -> Iterable[int]:
        return self._read_simple('q', amount)

    def read_ulonglong(self, amount: int = 1) -> Iterable[int]:
        return self._read_simple('Q', amount)

    def read_str(self, amount: int = 1) -> Iterable[str]:
        return self._read_simple(str, amount)

    def encode(self, **kwargs):
        pass

    def decode(self) -> PacketData:
        # noinspection PyCallingNonCallable
        return self.data()
