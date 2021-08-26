import math
import random
import string
import unittest
from . import fec, pkt


class TestFec(unittest.TestCase):
    def _rnd_string(self, n_bytes):
        """Generate a random string with the given number of bytes"""
        return ''.join(
            random.choice(string.ascii_letters + string.digits)
            for _ in range(n_bytes)).encode()

    def test_overhead(self):
        """Test the generated FEC overhead"""
        # Try several values of overhead
        n_overhead = 100
        max_overhead = 5

        # Random data to be encoded
        data = self._rnd_string(n_bytes=10000)
        n_chunks = math.ceil(len(data) / fec.CHUNK_SIZE)

        for i_overhead in range(n_overhead):
            # Target overhead
            overhead = max_overhead * i_overhead / n_overhead

            # Encoding
            fec_handler = fec.Fec(overhead)
            encoded_data = fec_handler.encode(data)

            # Expected number of FEC overhead chunks
            n_overhead_chunks = math.ceil(overhead * n_chunks)

            # Check that the encoder generates the expected number of chunks
            n_encoded_chunks = len(encoded_data) / fec.PKT_SIZE
            self.assertEqual(n_encoded_chunks, n_chunks + n_overhead_chunks)

            # Check the effective overhead
            effective_overhead = n_overhead_chunks / n_chunks
            self.assertGreaterEqual(effective_overhead, overhead)

    def test_encode_decode(self):
        """Test encoding and decoding of multiple message lengths"""
        for n_bytes in [100, 2**10, 2**20]:
            original_data = self._rnd_string(n_bytes)
            fec_handler = fec.Fec()
            encoded_data = fec_handler.encode(original_data)
            decoded_data = fec_handler.decode(encoded_data)
            self.assertEqual(original_data, decoded_data)

    def _drop_pkts(self, data, fraction):
        """Drop a fraction of the FEC packets"""
        n_pkts = len(data) // fec.PKT_SIZE
        n_drop = math.ceil(fraction * n_pkts)
        chunk_ids = set(range(n_pkts))
        drop_ids = set(random.sample(chunk_ids, n_drop))
        remaining_ids = chunk_ids - drop_ids

        res = b""
        for i_pkt in remaining_ids:
            s_byte = i_pkt * fec.PKT_SIZE  # starting byte
            e_byte = (i_pkt + 1) * fec.PKT_SIZE  # ending byte
            res += data[s_byte:e_byte]

        return res

    def test_erasure_recovery(self):
        """Test decoding of object containing erasures"""
        overhead = 0.1
        original_data = self._rnd_string(n_bytes=300000)
        fec_handler = fec.Fec(overhead)

        # Drop a fraction of packets corresponding to 90% of the overhead. The
        # data should remain recoverable, as the overhead exceeds the erasures.
        encoded_data = fec_handler.encode(original_data)
        erasure_data = self._drop_pkts(encoded_data, 0.9 * overhead)
        decoded_data = fec_handler.decode(erasure_data)
        self.assertEqual(original_data, decoded_data)

        # Drop 100% of the overhead. The object should become unrecoverable.
        encoded_data = fec_handler.encode(original_data)
        erasure_data = self._drop_pkts(encoded_data, overhead)
        decoder_res = fec_handler.decode(erasure_data)
        self.assertFalse(decoder_res)

    def test_blocksat_pkt_alignment(self):
        """Verify that the encoded FEC object splits evenly into BlocksatPkts

        The adopted FEC packet size is chosen so that each FEC packet fits
        exactly within the payload of a BlocksatPkt.

        """

        # Random FEC-encoded data
        original_data = self._rnd_string(n_bytes=2**20)
        fec_handler = fec.Fec()
        encoded_data = fec_handler.encode(original_data)
        n_pkts = len(encoded_data) // fec.PKT_SIZE

        # Distribute the FEC-encoded data into BlocksatPkts
        chan_num = 1
        seq_num = 1
        handler = pkt.BlocksatPktHandler()
        handler.split(encoded_data, seq_num, chan_num)

        # Each FEC packet should go in one BlocksatPkt (a.k.a. fragment)
        self.assertEqual(n_pkts, handler.get_n_frags(seq_num))

        # Check the payload of each BlocksatPkt
        frags = handler.get_frags(seq_num)
        for i_pkt in range(n_pkts):
            s_byte = i_pkt * fec.PKT_SIZE  # starting byte
            e_byte = (i_pkt + 1) * fec.PKT_SIZE  # ending byte
            self.assertEqual(encoded_data[s_byte:e_byte], frags[i_pkt].payload)
