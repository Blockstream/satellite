import random
import string
import struct
import time
import unittest
from . import pkt


class TestOrder(unittest.TestCase):
    def _rnd_string(self, n_bytes):
        """Generate random string with given number of bytes"""
        return ''.join(
            random.choice(string.ascii_letters + string.digits)
            for _ in range(n_bytes)).encode()

    def test_pack_unpack(self):
        """Test packing and unpacking to/from Blocksat Packet"""
        chan_num = pkt.ApiChannel.USER.value
        seq_num = 1
        frag_num = 10
        more_frags = False
        payload = "Hello".encode()

        # Packetize
        tx_packet = pkt.BlocksatPkt(seq_num, frag_num, chan_num, more_frags,
                                    payload)
        tx_serial_data = tx_packet.pack()

        self.assertEqual(len(tx_serial_data), pkt.HEADER_LEN + len(payload))

        # Unpack
        rx_packet = pkt.BlocksatPkt()
        rx_packet.unpack(tx_serial_data)

        # Check
        self.assertEqual(seq_num, rx_packet.seq_num)
        self.assertEqual(frag_num, rx_packet.frag_num)
        self.assertEqual(more_frags, rx_packet.more_frags)
        self.assertEqual(payload, rx_packet.payload)

    def test_handler(self):
        """Test extraction of API message from collection of Blockst Packets"""
        # Random data
        data = self._rnd_string(n_bytes=10000)

        # Distribute data into packets
        chan_num = 1
        seq_num = 1
        handler = pkt.BlocksatPktHandler()
        handler.split(data, seq_num, chan_num)

        # The random data should exceed the length of a single Blocksat Packet
        assert (handler.get_n_frags(seq_num) > 1)

        # All fragments but the last shall assert the "more fragments" bit
        packets = handler.get_frags(seq_num)
        for packet in packets[:-1]:
            self.assertTrue(packet.more_frags)
        self.assertFalse(packets[-1].more_frags)

        # Concatenate fragments back to form the original message
        decoded_data = handler.concat(seq_num)

        # Check
        self.assertEqual(data, decoded_data)

    def test_unordered_packet_handling(self):
        """Test decoding of API message from out-of-order Blocksat Packets"""
        # Random data
        data = self._rnd_string(n_bytes=10000)

        # Distribute data into packets
        chan_num = 1
        seq_num = 1
        tx_handler = pkt.BlocksatPktHandler()
        tx_handler.split(data, seq_num, chan_num)

        # Pass packets from the Tx handler to the Rx handler out-of-order.
        rx_handler = pkt.BlocksatPktHandler()
        packets = tx_handler.get_frags(seq_num)
        random.shuffle(packets)
        for packet in packets:
            data_ready = rx_handler.append(packet)
            if (data_ready):
                break

        # Concatenate fragments back to form the original message
        decoded_data = rx_handler.concat(seq_num)
        self.assertEqual(data, decoded_data)

    def test_packet_gap_handling(self):
        """Test decoding of API message with gap on Blocksat Packets"""
        # Random data
        data = self._rnd_string(n_bytes=10000)

        # Distribute data into packets
        chan_num = 1
        seq_num = 1
        tx_handler = pkt.BlocksatPktHandler()
        tx_handler.split(data, seq_num, chan_num)

        # Pass packets from the Tx handler to the Rx handler out-of-order and
        # drop a packet chosen randomly.
        rx_handler = pkt.BlocksatPktHandler()
        packets = tx_handler.get_frags(seq_num)
        random.shuffle(packets)
        i_drop = random.choice([p.frag_num for p in packets])
        data_ready = False
        for packet in packets:
            if (packet.frag_num == i_drop):
                continue

            data_ready = rx_handler.append(packet)
            if (data_ready):
                break

        # The data should not be ready to be decoded
        self.assertFalse(data_ready)

        # Method "concat" should only be called when the data is ready to be
        # decoded. Otherwise, it should throw an exception.
        with self.assertRaises(RuntimeError):
            rx_handler.concat(seq_num)

    def test_repeated_fragment(self):
        """Test processing of repeated fragment"""
        # Random data
        data = self._rnd_string(n_bytes=10000)

        # Distribute data into packets
        chan_num = 1
        seq_num = 1
        tx_handler = pkt.BlocksatPktHandler()
        tx_handler.split(data, seq_num, chan_num)

        # Feed the same fragment twice to the Rx handler
        rx_handler = pkt.BlocksatPktHandler()
        packets = tx_handler.get_frags(seq_num)

        # First time:
        data_ready1 = rx_handler.append(packets[0])
        concat1 = rx_handler.concat(seq_num, force=True)
        self.assertFalse(data_ready1)

        # Second time:
        data_ready2 = rx_handler.append(packets[0])
        concat2 = rx_handler.concat(seq_num, force=True)
        self.assertFalse(data_ready2)

        # The concatenated data should remain the same before and after feeding
        # the same packet for the second time.
        self.assertEqual(concat1, concat2)

        # Feed a different packet but whose fragment number is the same as the
        # one fed before. A warning should be printed in this case and the
        # fragment should not be processed.
        tampered_pkt = packets[1]
        tampered_pkt.frag_num = 0
        with self.assertLogs(level='WARNING'):
            data_ready3 = rx_handler.append(tampered_pkt)
        concat3 = rx_handler.concat(seq_num, force=True)
        self.assertFalse(data_ready3)
        self.assertEqual(concat1, concat3)

    def test_ota_msg_len(self):
        """Test over-the-air message length computation"""
        # Random data
        data = self._rnd_string(n_bytes=10000)

        # Expected number of bytes sent over-the-air
        expected_ota_len = pkt.calc_ota_msg_len(len(data))

        # Distribute data into packets
        chan_num = 1
        seq_num = 1
        tx_handler = pkt.BlocksatPktHandler()
        tx_handler.split(data, seq_num, chan_num)

        # Compute sum of transmitted payload lengths
        pkts = tx_handler.get_frags(seq_num)
        total_len = 0
        udp_ip_mpe_overhead = 8 + 20 + 16
        for packet in pkts:
            total_len += len(packet.pack()) + udp_ip_mpe_overhead

        # Check
        self.assertEqual(expected_ota_len, total_len)

    def test_fragment_clean_up(self):
        """Test automatic cleaning of old pending fragments"""
        # Random data
        data = self._rnd_string(n_bytes=10000)

        # Create a packet handler with a short timeout
        timeout = 0.5
        handler = pkt.BlocksatPktHandler(timeout=timeout)

        # Distribute data into packets
        chan_num = 1
        seq_num = 1
        handler.split(data, seq_num, chan_num)

        # Try to clean
        handler.clean()

        # It should not have cleaned anything (timeout interval has not
        # elapsed)
        assert (seq_num in handler.frag_map)

        # Wait enough to time out
        time.sleep(timeout)

        # Try to clean again
        handler.clean()

        # Now it should be clean
        assert (seq_num not in handler.frag_map)
        assert (handler.frag_map == {})

    def test_chan_number_backwards_compatibility(self):
        """Unpack the new header format using the previous unpacking format"""
        chan_num = pkt.ApiChannel.USER.value
        seq_num = 1
        frag_num = 10
        more_frags = True
        payload = "Hello".encode()

        # Packetize using the new implementation (new header format)
        tx_packet = pkt.BlocksatPkt(seq_num, frag_num, chan_num, more_frags,
                                    payload)
        tx_serial_data = tx_packet.pack()

        # Unpack using the previous header format
        rx_header = tx_serial_data[:pkt.HEADER_LEN]
        rx_payload = tx_serial_data[pkt.HEADER_LEN:]
        octet_0, rx_frag_num, rx_seq_num = struct.unpack('!cxHI', rx_header)
        rx_more_frags = bool(ord(octet_0) & ord(b'\x80'))

        self.assertEqual(seq_num, rx_seq_num)
        self.assertEqual(frag_num, rx_frag_num)
        self.assertEqual(more_frags, rx_more_frags)
        self.assertEqual(payload, rx_payload)
