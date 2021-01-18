import unittest
from unittest.mock import patch
from . import bidding


class TestBidding(unittest.TestCase):
    def test_suggested_bid(self):
        # The suggested bid should always respect the minimum bid per byte
        data_size = 1000
        bid = bidding.suggest_bid(data_size)
        expected_bid = bidding.MIN_BID_PER_BYTE * data_size
        self.assertEqual(bid, expected_bid)

        # It should never be below the global "min_bid"
        data_size = 10
        bid = bidding.suggest_bid(data_size)
        self.assertEqual(bid, bidding.MIN_BID)

        # It should always be an integer number of millisatoshis
        bidding.MIN_BID_PER_BYTE = 1.0005  # set a fractional minimum bid/byte
        data_size = 1000
        expected_bid = 1001
        bid = bidding.suggest_bid(data_size)
        self.assertEqual(bid, expected_bid)

    def test_bid_bump_suggestion(self):
        # Expect a suggested bid increase of at least 5% by default
        data_sizes = [10, 100, 1000, 10000]
        expected_bids = [11, 105, 1050, 10500]
        for data_size, expected_bid in zip(data_sizes, expected_bids):
            prev_bid = bidding.MIN_BID_PER_BYTE * data_size
            bid = bidding.suggest_bid(data_size, prev_bid)
            self.assertEqual(bid, expected_bid)

    @patch('blocksatcli.util.typed_input', return_value=1000)
    def test_bid_input(self, bid_input):
        data_size = 1000
        bid = bidding.ask_bid(data_size)
        self.assertEqual(bid, bid_input.return_value)

    def test_bid_validation(self):
        # Negative bid
        bid = -1
        self.assertFalse(bidding.validate_bid(bid))

        # Bumped bid below or equal to the original bid
        new_bid = 1000
        prev_bid = 1000
        self.assertFalse(bidding.validate_bid(new_bid, prev_bid))
        new_bid = 999
        prev_bid = 1000
        self.assertFalse(bidding.validate_bid(new_bid, prev_bid))

        # Valid bumped bid
        new_bid = 1001
        prev_bid = 1000
        self.assertTrue(bidding.validate_bid(new_bid, prev_bid))

        # Excessive bid
        self.assertFalse(bidding.validate_bid(2e7))
