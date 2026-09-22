# -*- coding: utf-8 -*-
"""Read and write Minecraft NBT (gzipped or raw) with no third-party library.

Tags are represented as plain Python values wrapped only where the NBT type is ambiguous:

    Byte(1)  Short(1)  Int(1)  Long(1)  Float(1.0)  Double(1.0)
    str                              -> TAG_String
    dict                             -> TAG_Compound   (insertion order is kept)
    List(tag_type, [...])            -> TAG_List
    ByteArray / IntArray / LongArray -> the array tags

`read` keeps every value in its typed wrapper so that `write` reproduces the file byte for
byte apart from compression. Code that only wants to look uses `.value` or lets the wrappers
behave as their underlying int/float (they subclass int and float).
"""
import gzip
import struct

END, BYTE, SHORT, INT, LONG, FLOAT, DOUBLE, BYTE_ARRAY, STRING, LIST, COMPOUND, INT_ARRAY, LONG_ARRAY = range(13)


class Byte(int):
    tag = BYTE


class Short(int):
    tag = SHORT


class Int(int):
    tag = INT


class Long(int):
    tag = LONG


class Float(float):
    tag = FLOAT


class Double(float):
    tag = DOUBLE


class ByteArray(list):
    tag = BYTE_ARRAY


class IntArray(list):
    tag = INT_ARRAY


class LongArray(list):
    tag = LONG_ARRAY


class List(list):
    """A TAG_List. `elem` is the element tag type, needed when the list is empty."""
    tag = LIST

    def __init__(self, elem, items=()):
        super().__init__(items)
        self.elem = elem


def tag_of(v):
    if isinstance(v, str):
        return STRING
    if isinstance(v, dict):
        return COMPOUND
    t = getattr(v, 'tag', None)
    if t is None:
        raise TypeError('cannot infer NBT tag for %r; wrap it (Int, Byte, List...)' % (v,))
    return t


# ------------------------------------------------------------------------------- reading

class _Reader:
    def __init__(self, data):
        self.d = data
        self.i = 0

    def take(self, fmt):
        v = struct.unpack_from('>' + fmt, self.d, self.i)[0]
        self.i += struct.calcsize('>' + fmt)
        return v

    def string(self):
        n = self.take('H')
        s = self.d[self.i:self.i + n].decode('utf-8', 'replace')
        self.i += n
        return s

    def payload(self, t):
        if t == BYTE:
            return Byte(self.take('b'))
        if t == SHORT:
            return Short(self.take('h'))
        if t == INT:
            return Int(self.take('i'))
        if t == LONG:
            return Long(self.take('q'))
        if t == FLOAT:
            return Float(self.take('f'))
        if t == DOUBLE:
            return Double(self.take('d'))
        if t == BYTE_ARRAY:
            n = self.take('i')
            v = ByteArray(struct.unpack_from('>%db' % n, self.d, self.i))
            self.i += n
            return v
        if t == STRING:
            return self.string()
        if t == LIST:
            et = self.take('b')
            n = self.take('i')
            return List(et, [self.payload(et) for _ in range(n)])
        if t == COMPOUND:
            out = {}
            while True:
                tt = self.take('b')
                if tt == END:
                    return out
                name = self.string()
                out[name] = self.payload(tt)
        if t == INT_ARRAY:
            n = self.take('i')
            v = IntArray(struct.unpack_from('>%di' % n, self.d, self.i))
            self.i += 4 * n
            return v
        if t == LONG_ARRAY:
            n = self.take('i')
            v = LongArray(struct.unpack_from('>%dq' % n, self.d, self.i))
            self.i += 8 * n
            return v
        raise ValueError('unknown tag %d at %d' % (t, self.i))


def read(path):
    """The root compound of a .nbt file. Structure files have an unnamed root."""
    raw = open(path, 'rb').read()
    try:
        raw = gzip.decompress(raw)
    except OSError:
        pass
    r = _Reader(raw)
    t = r.take('b')
    if t != COMPOUND:
        raise ValueError('root is not a compound')
    r.string()  # root name, empty for structures
    return r.payload(COMPOUND)


# ------------------------------------------------------------------------------- writing

def _string(out, s):
    b = s.encode('utf-8')
    out.append(struct.pack('>H', len(b)))
    out.append(b)


def _payload(out, t, v):
    if t == BYTE:
        out.append(struct.pack('>b', v))
    elif t == SHORT:
        out.append(struct.pack('>h', v))
    elif t == INT:
        out.append(struct.pack('>i', v))
    elif t == LONG:
        out.append(struct.pack('>q', v))
    elif t == FLOAT:
        out.append(struct.pack('>f', v))
    elif t == DOUBLE:
        out.append(struct.pack('>d', v))
    elif t == BYTE_ARRAY:
        out.append(struct.pack('>i', len(v)))
        out.append(struct.pack('>%db' % len(v), *v))
    elif t == STRING:
        _string(out, v)
    elif t == LIST:
        et = v.elem if isinstance(v, List) else (tag_of(v[0]) if v else END)
        out.append(struct.pack('>bi', et, len(v)))
        for item in v:
            _payload(out, et, item)
    elif t == COMPOUND:
        for name, item in v.items():
            it = tag_of(item)
            out.append(struct.pack('>b', it))
            _string(out, name)
            _payload(out, it, item)
        out.append(b'\x00')
    elif t == INT_ARRAY:
        out.append(struct.pack('>i', len(v)))
        out.append(struct.pack('>%di' % len(v), *v))
    elif t == LONG_ARRAY:
        out.append(struct.pack('>i', len(v)))
        out.append(struct.pack('>%dq' % len(v), *v))
    else:
        raise ValueError('unknown tag %d' % t)


def dumps(root):
    """Uncompressed bytes of a compound as an unnamed root."""
    out = [struct.pack('>b', COMPOUND)]
    _string(out, '')
    _payload(out, COMPOUND, root)
    return b''.join(out)


def write(path, root, compress=True):
    data = dumps(root)
    if compress:
        # mtime=0, or the gzip header carries the clock and every regeneration rewrites all
        # 390 pieces with identical contents - a diff that hides the one piece that changed
        data = gzip.compress(data, mtime=0)
    with open(path, 'wb') as f:
        f.write(data)


# --------------------------------------------------------------------- structure helpers

def palette_name(entry):
    """Block id of a palette entry. 26.2 wrote `Name`/`Properties`; 26.3 writes `id`/`properties`."""
    return entry.get('id') or entry.get('Name')


def palette_props(entry):
    return entry.get('properties') or entry.get('Properties') or {}
