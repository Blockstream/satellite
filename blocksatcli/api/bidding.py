import logging
from math import ceil

from .. import util

logger = logging.getLogger(__name__)
MIN_BID_PER_BYTE = 1
MIN_BID = 1000
DEFAULT_BUMP_FACTOR = 1.05
MAX_MSG_SIZE = 1050 * 1000  # maximum message size relayed by the satellite API
MAX_BID = 10 * MIN_BID_PER_BYTE * MAX_MSG_SIZE


def suggest_bid(data_size, prev_bid=None):
    """Suggest a valid bid for the given data transmission length

    Args:
        data_size : Size of the transmit data in bytes
        prev_bid  : Previous bid, if any

    Returns:
        Bid in millisatoshis

    """
    assert (isinstance(data_size, int))

    if (prev_bid is not None):
        # Suggest a 5% higher msat/byte ratio
        suggested_bid = ceil(DEFAULT_BUMP_FACTOR * prev_bid)
    else:
        suggested_bid = max(ceil(data_size * MIN_BID_PER_BYTE), MIN_BID)
    return suggested_bid


def validate_bid(bid, prev_bid=None):
    """Validate a given bid

    Args:
        bid      : New bid in msats
        prev_bid : Previous bid in msats, used if bumping

    Returns:
        Bool indicating whether the bid is valid.

    """
    if (bid <= 0):
        print("Please provide a positive bid in millisatoshis")
        return False

    if (prev_bid is not None and bid <= prev_bid):
        print("Please provide a bid higher than the previous bid")
        return False

    if (bid > MAX_BID):
        print("Bid too large. Are you sure you want to bid {:.2f} "
              "sats (satoshis)?".format(bid / 1e3))
        return False

    return True


def ask_bid(data_size, prev_bid=None):
    """Prompt user for a bid to transmit the given data size

    Args:
        data_size : Size of the transmit data in bytes
        prev_bid  : Previous bid, if any

    Returns:
        Bid in millisatoshis

    """
    suggested_bid = suggest_bid(data_size, prev_bid)

    print("")
    msg = "Your {}bid to transmit {:d} bytes (in millisatoshis)".format(
        ("new total " if prev_bid is not None else ""), data_size)

    while (True):
        bid = util.typed_input(msg, default=suggested_bid)
        if (validate_bid(bid, prev_bid)):
            break

    if (prev_bid is not None):
        logger.info("Bump bid by %d msat to a total of %d msat "
                    "(%.2f msat/byte)" %
                    (bid - prev_bid, bid, float(bid) / data_size))
    else:
        logger.info("Post data with bid of %d millisatoshis "
                    "(%.2f msat/byte)" % (bid, float(bid) / data_size))

    return bid
