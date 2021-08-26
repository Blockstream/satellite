import unittest
from . import net


class TestApi(unittest.TestCase):
    def test_send_rcv(self):
        """Test transmission and reception of data"""
        ip = "239.0.0.2"
        port = 4444
        addr = ip + ":" + str(port)
        ifname = "lo"
        data = bytes([0, 1, 2, 3])

        # Tx socket
        tx_sock = net.UdpSock(addr, ifname, mcast_rx=False)
        tx_sock.set_mcast_tx_opts()

        self.assertEqual(tx_sock.ip, ip)
        self.assertEqual(tx_sock.port, port)

        # Rx socket
        rx_sock = net.UdpSock(addr, ifname)

        self.assertEqual(rx_sock.ip, ip)
        self.assertEqual(rx_sock.port, port)

        # Send data
        tx_sock.send(data)

        # Receive it
        rx_payload, rx_addr = rx_sock.recv()

        # Check
        self.assertEqual(data, rx_payload)
        self.assertEqual(rx_addr[1], port)
