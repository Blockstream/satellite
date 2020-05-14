import unittest, hashlib
from . import order, pkt


class TestOrder(unittest.TestCase):
    def setUp(self):
        server     = "https://api.blockstream.space/testnet"
        self.order = order.ApiOrder(server)

    def test_transmission(self):
        """Test API order transmission"""
        data   = "Hello".encode()
        tx_len = pkt.calc_ota_msg_len(len(data))
        bid    = tx_len * 50

        # Send
        res = self.order.send(data, bid)

        # Check response
        assert('auth_token' in res)
        assert('uuid' in res)
        assert('lightning_invoice' in res)
        self.assertEqual(
            res['lightning_invoice']['metadata']['sha256_message_digest'],
            hashlib.sha256(data).hexdigest()
        )
        self.assertEqual(res['lightning_invoice']['status'], 'unpaid')
        self.assertEqual(int(res['lightning_invoice']['msatoshi']), bid)

    def test_bumping(self):
        """Test bumping of API order bid"""
        data   = "Hello".encode()
        tx_len = pkt.calc_ota_msg_len(len(data))
        bid    = tx_len * 50

        # Send first
        res = self.order.send(data, bid)
        self.assertEqual(int(res['lightning_invoice']['msatoshi']), bid)

        # Order identification:
        uuid       = res['uuid']
        auth_token = res['auth_token']

        # Bump bid
        new_bid = int(1.05 * bid)
        res = self.order.bump(new_bid, uuid, auth_token)

        # The new invoice should correspond to the difference between the new
        # and the old bid
        self.assertEqual(int(res['lightning_invoice']['msatoshi']),
                         (new_bid - bid))

    def test_delete(self):
        """Test bumping of API order bid"""
        data   = "Hello".encode()
        tx_len = pkt.calc_ota_msg_len(len(data))
        bid    = tx_len * 50

        # Send first
        res = self.order.send(data, bid)
        self.assertEqual(int(res['lightning_invoice']['msatoshi']), bid)

        # Order identification:
        uuid       = res['uuid']
        auth_token = res['auth_token']

        # Delete order
        res = self.order.delete(uuid, auth_token)
        self.assertEqual(res['message'], "order cancelled")

