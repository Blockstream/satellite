import hashlib
import unittest
from . import order, pkt


class TestOrder(unittest.TestCase):
    def setUp(self):
        server = "https://api.blockstream.space/testnet"
        self.order = order.ApiOrder(server)

    def test_transmission(self):
        """Test API order transmission"""
        data = "Hello".encode()
        tx_len = pkt.calc_ota_msg_len(len(data))
        bid = tx_len * 50

        # Send
        res = self.order.send(data, bid)

        # Check response
        assert ('auth_token' in res)
        assert ('uuid' in res)
        assert ('lightning_invoice' in res)
        self.assertEqual(
            res['lightning_invoice']['metadata']['sha256_message_digest'],
            hashlib.sha256(data).hexdigest())
        self.assertEqual(res['lightning_invoice']['status'], 'unpaid')
        self.assertEqual(int(res['lightning_invoice']['msatoshi']), bid)

        # The uuid and auth token should be set on the order object too
        self.assertEqual(res['uuid'], self.order.uuid)
        self.assertEqual(res['auth_token'], self.order.auth_token)

        # The order should become available to be fetched
        self.order.get(res['uuid'], res['auth_token'])

        # Check the fetched info
        self.assertEqual(self.order.order['unpaid_bid'], bid)
        self.assertEqual(self.order.order['message_size'], len(data))
        self.assertEqual(self.order.order['status'], 'pending')

    def test_wait(self):
        """Test waiting for a transmission state"""
        data = "Hello".encode()
        tx_len = pkt.calc_ota_msg_len(len(data))
        bid = tx_len * 50

        # Send
        self.order.send(data, bid)

        # Because the order won't be paid, waiting for "paid" state should time
        # out and return False
        self.assertFalse(self.order.wait_state("paid", timeout=2))

    def test_bumping(self):
        """Test bumping of API order bid"""
        data = "Hello".encode()
        tx_len = pkt.calc_ota_msg_len(len(data))
        bid = tx_len * 50

        # Send first
        res = self.order.send(data, bid)
        self.assertEqual(int(res['lightning_invoice']['msatoshi']), bid)

        # Bump bid
        new_bid = int(1.05 * bid)
        res = self.order.bump(new_bid)

        # The new invoice should correspond to the difference between the new
        # and the old bid
        self.assertEqual(int(res['lightning_invoice']['msatoshi']),
                         (new_bid - bid))

    def test_delete(self):
        """Test bumping of API order bid"""
        data = "Hello".encode()
        tx_len = pkt.calc_ota_msg_len(len(data))
        bid = tx_len * 50

        # Send first
        res = self.order.send(data, bid)
        self.assertEqual(int(res['lightning_invoice']['msatoshi']), bid)

        # Delete order
        res = self.order.delete()
        self.assertEqual(res['message'], "order cancelled")

        # It should work to wait for state "cancelled"
        self.assertTrue(self.order.wait_state("cancelled", timeout=1))
