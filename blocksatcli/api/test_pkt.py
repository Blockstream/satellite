import unittest, string, random
from . import pkt


class TestOrder(unittest.TestCase):
    def test_pack_unpack(self):
        """Test packing and unpacking to/from Blocksat Packet"""
        seq_num    = 1
        frag_num   = 10
        more_frags = False
        payload    = "Hello".encode()

        # Packetize
        tx_packet      = pkt.BlocksatPkt(seq_num, frag_num, more_frags, payload)
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
        n_bytes = 10000
        data    = ''.join(random.choice(string.ascii_letters + string.digits)\
                          for _ in range(n_bytes)).encode()

        # Distribute data into packets
        seq_num = 1
        handler = pkt.BlocksatPktHandler()
        handler.split(data, seq_num)

        # The random data should exceed the length of a single Blocksat Packet
        assert(handler.get_n_frags(seq_num) > 1)

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
        n_bytes = 10000
        data    = ''.join(random.choice(string.ascii_letters + string.digits)\
                          for _ in range(n_bytes)).encode()

        # Distribute data into packets
        seq_num    = 1
        tx_handler = pkt.BlocksatPktHandler()
        tx_handler.split(data, seq_num)

        # Pass packets from the Tx handler to the Rx handler out-of-order.
        rx_handler = pkt.BlocksatPktHandler()
        packets    = tx_handler.get_frags(seq_num)
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
        n_bytes = 10000
        data    = ''.join(random.choice(string.ascii_letters + string.digits) \
                          for _ in range(n_bytes)).encode()

        # Distribute data into packets
        seq_num    = 1
        tx_handler = pkt.BlocksatPktHandler()
        tx_handler.split(data, seq_num)

        # Pass packets from the Tx handler to the Rx handler out-of-order and
        # drop a packet chosen randomly.
        rx_handler = pkt.BlocksatPktHandler()
        packets    = tx_handler.get_frags(seq_num)
        random.shuffle(packets)
        i_drop     = random.choice([p.frag_num for p in packets])
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

    def test_ota_msg_len(self):
        """Test over-the-air message length computation"""
        # Random data
        n_bytes = 10000
        data    = ''.join(random.choice(string.ascii_letters + string.digits)\
                          for _ in range(n_bytes)).encode()

        # Expected number of bytes sent over-the-air
        expected_ota_len = pkt.calc_ota_msg_len(len(data))

        # Distribute data into packets
        seq_num    = 1
        tx_handler = pkt.BlocksatPktHandler()
        tx_handler.split(data, seq_num)

        # Compute sum of transmitted payload lengths
        pkts                = tx_handler.get_frags(seq_num)
        total_len           = 0
        udp_ip_mpe_overhead = 8 + 20 + 16
        for packet in pkts:
            total_len += len(packet.pack()) + udp_ip_mpe_overhead

        # Check
        self.assertEqual(expected_ota_len, total_len)

