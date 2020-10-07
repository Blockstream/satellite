import logging
from math import ceil
from .. import util


logger = logging.getLogger(__name__)


def ask_bid(data_size, prev_bid=None):
    """Ask for user bid

    Args:
        data_size : Size of the transmit data in bytes
        prev_bid  : Previous bid, if any

    Returns:
        Bid in millisatoshis

    """

    if (prev_bid is not None):
        # Suggest a 5% higher msat/byte ratio
        prev_ratio      = float(prev_bid) / data_size
        suggested_ratio = 1.05 * prev_ratio
        min_bid         = int(ceil(data_size * suggested_ratio))
    else:
        min_bid = data_size * 50

    print("")
    msg = "Your {}bid to transmit {:d} bytes (in millisatoshis)".format(
        ("new total " if prev_bid is not None else ""), data_size, min_bid)

    bid = util.typed_input(msg, default=min_bid)
    print()

    if (prev_bid is not None):
        logger.info("Bump bid by %d msat to a total of %d msat "
                    "(%.2f msat/byte)" %(
                        bid - prev_bid, bid, float(bid) / data_size))
    else:
        logger.info("Post data with bid of %d millisatoshis "
                    "(%.2f msat/byte)" %(bid, float(bid) / data_size))

    return bid

