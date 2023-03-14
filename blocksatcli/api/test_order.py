import unittest
from http import HTTPStatus
from unittest.mock import Mock, patch
from uuid import uuid4

from . import order, pkt


def mock_get_api_resp(bid_msat, message_size, status='pending'):
    return Mock(status_code=HTTPStatus.OK,
                json=lambda: {
                    'bid': 0,
                    'unpaid_bid': bid_msat,
                    'bid_per_byte': 0,
                    'message_size': message_size,
                    'status': status
                })


def mock_post_api_resp(bid_msat):
    return Mock(status_code=HTTPStatus.OK,
                json=lambda: {
                    'uuid': str(uuid4()),
                    'auth_token': str(uuid4()),
                    'lightning_invoice': {
                        'payreq': 'payreq',
                        'msatoshi': bid_msat,
                    }
                })


def mock_del_api_resp():
    return Mock(status_code=HTTPStatus.OK,
                json=lambda: {'message': "order cancelled"})


class TestOrder(unittest.TestCase):

    def setUp(self):
        server = "mock-server"
        self.order = order.ApiOrder(server)

    @patch('blocksatcli.api.order.requests.get')
    @patch('blocksatcli.api.order.requests.post')
    def test_transmission(self, mock_post, mock_get):
        """Test API order transmission"""
        data = "Hello".encode()
        tx_len = pkt.calc_ota_msg_len(len(data))
        bid = tx_len * 50

        # Send
        mock_post.return_value = mock_post_api_resp(bid)
        res = self.order.send(data, bid)

        # Check response
        assert ('auth_token' in res)
        assert ('uuid' in res)
        assert ('lightning_invoice' in res)
        self.assertEqual(int(res['lightning_invoice']['msatoshi']), bid)

        # The uuid and auth token should be set on the order object
        self.assertIsNotNone(res['uuid'])
        self.assertIsNotNone(res['auth_token'])
        self.assertEqual(res['uuid'], self.order.uuid)
        self.assertEqual(res['auth_token'], self.order.auth_token)

        # The order should become available to be fetched
        mock_get.return_value = mock_get_api_resp(bid, len(data))
        self.order.get(res['uuid'], res['auth_token'])

        # Check the fetched info
        self.assertEqual(self.order.order['unpaid_bid'], bid)
        self.assertEqual(self.order.order['message_size'], len(data))
        self.assertEqual(self.order.order['status'], 'pending')

    @patch('blocksatcli.api.order.requests.get')
    @patch('blocksatcli.api.order.requests.post')
    def test_wait(self, mock_post, mock_get):
        """Test waiting for a transmission state"""
        data = "Hello".encode()
        tx_len = pkt.calc_ota_msg_len(len(data))
        bid = tx_len * 50

        # Send
        mock_post.return_value = mock_post_api_resp(bid)
        self.order.send(data, bid)

        # Waiting for "paid" state should time out and return False
        mock_get.return_value = mock_get_api_resp(bid, len(data))
        self.assertFalse(self.order.wait_state("paid", timeout=2))

        # Change the mock order to paid state and check the wait returns True
        # before timing out (state found)
        mock_get.return_value = mock_get_api_resp(bid,
                                                  len(data),
                                                  status='paid')
        self.assertTrue(self.order.wait_state("paid", timeout=2))

    @patch('blocksatcli.api.order.requests.get')
    @patch('blocksatcli.api.order.requests.post')
    def test_bumping(self, mock_post, mock_get):
        """Test bumping of API order bid"""
        data = "Hello".encode()
        tx_len = pkt.calc_ota_msg_len(len(data))
        bid = tx_len * 50

        # Send first
        mock_post.return_value = mock_post_api_resp(bid)
        res = self.order.send(data, bid)
        self.assertEqual(int(res['lightning_invoice']['msatoshi']), bid)

        # Bump bid
        new_bid = int(1.05 * bid)
        mock_get.return_value = mock_get_api_resp(bid, len(data))
        mock_post.return_value = mock_post_api_resp(new_bid - bid)
        res = self.order.bump(new_bid)

        # The new invoice should correspond to the difference between the new
        # and the old bid
        self.assertEqual(int(res['lightning_invoice']['msatoshi']),
                         (new_bid - bid))

    @patch('blocksatcli.api.order.requests.get')
    @patch('blocksatcli.api.order.requests.delete')
    @patch('blocksatcli.api.order.requests.post')
    def test_delete(self, mock_post, mock_del, mock_get):
        """Test bumping of API order bid"""
        data = "Hello".encode()
        tx_len = pkt.calc_ota_msg_len(len(data))
        bid = tx_len * 50

        # Send first
        mock_post.return_value = mock_post_api_resp(bid)
        res = self.order.send(data, bid)
        self.assertEqual(int(res['lightning_invoice']['msatoshi']), bid)

        # Delete order
        mock_get.return_value = mock_get_api_resp(bid, len(data))
        mock_del.return_value = mock_del_api_resp()
        res = self.order.delete()
        self.assertEqual(res['message'], "order cancelled")

        # It should work to wait for state "cancelled"
        mock_get.return_value = mock_get_api_resp(bid,
                                                  len(data),
                                                  status='cancelled')
        self.assertTrue(self.order.wait_state("cancelled", timeout=1))
