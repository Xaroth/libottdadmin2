import unittest
import random

from libottdadmin2.packets import Packet
from .packet_data import PACKETS


class TestPacketReading(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.packets = PACKETS
        cls.parsed = {}

    def test_001_raw_read_write(self):
        types = ['byte', 'sshort', 'ushort', 'sint', 'uint', 'slong', 'ulong', 'longlong', 'ulonglong']

        for typ in types:
            pkt = Packet()
            writer = getattr(pkt, 'write_%s' % typ)
            reader = getattr(pkt, 'read_%s' % typ)

            for i in range(5, 10):
                with self.subTest(type=typ, i=i):
                    pkt.reset(clear=True)
                    val = [random.randint(0, 127) for _ in range(i)]
                    writer(*val)
                    self.assertIsNotNone(pkt.buffer, "Buffer is empty after writing")
                    pkt.reset(clear=False)
                    read = list(reader(i))
                    self.assertEqual(val, read, "Read data does not match written data")

    def test_002_parse_known(self):
        for name, buffer in self.packets.items():
            with self.subTest(name=name):
                pkt, data = Packet.from_name_and_buffer(name, buffer)
                self.assertIsNotNone(pkt, "Could not parse packet for packet %s" % name)
                self.assertIsNotNone(data, "Could not parse packet for packet %s" % name)
                self.parsed[pkt] = data

    def test_003_re_encode(self):
        for name, buffer in self.packets.items():
            with self.subTest(name=name):
                pkta, data = Packet.from_name_and_buffer(name, buffer)
                self.assertIsNotNone(pkta, "Could not parse packet for packet %s" % name)
                pktb = pkta.__class__.create(data)
                self.assertIsNotNone(pktb, "Could not assemble packet for packet %s" % name)
                self.assertEqual(pkta.buffer, pktb.buffer, "Buffers mismatch for packet %s" % name)
                self.assertEqual(pkta.header, pktb.header, "Headers mismatch for packet %s" % name)
                pktc = Packet.from_buffer(buffer=pkta.buffer, hdr=pkta.header)
                self.assertIsNotNone(pktc, "Could not assemble packet for packet %s" % name)
                self.assertEqual(pkta.buffer, pktc.buffer, "Buffers mismatch for packet %s" % name)
                self.assertEqual(pkta.header, pktc.header, "Headers mismatch for packet %s" % name)
                pktd = Packet.from_buffer(buffer=b''.join([pktb.header, pktb.buffer]))
                self.assertIsNotNone(pktc, "Could not re-assemble packet for packet %s" % name)
                self.assertEqual(pktd.buffer, pktc.buffer, "Buffers mismatch for packet %s" % name)
                self.assertEqual(pktd.header, pktc.header, "Headers mismatch for packet %s" % name)
