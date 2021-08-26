"""Encapsulation of API messages into Blocksat Packets"""
import logging
import struct
import time
from enum import Enum
from math import ceil

logger = logging.getLogger(__name__)
HEADER_FORMAT = '!cBHI'
# Header format:
# octet 0    : Type bit on LSB, MF bit on MSB
# octet 1    : Channel number
# octets 2-3 : Fragment number
# octets 4-7 : Sequence number
HEADER_LEN = 8
TYPE_API_DATA = b'\x01'
API_TYPE_LAST_FRAG = b'\x01'  # Type=1 (API), MF=0
API_TYPE_MORE_FRAG = b'\x81'  # Type=1 (API), MF=1
# Maximum Blocksat Packet payload in bytes to avoid fragmentation at IPv4
# level:
#
# NOTE: The maximum Blocksat Packet payload considers the space occupied by the
# Blocksat Packet, UDP and IP headers. That is, 8 (blocksat header) + 8 (UDP
# header) + 20 (minimum IPv4 header), which add to 36 bytes. It also considers
# a layer-2 MTU of 1500 bytes. See the explanation on calc_ota_msg_len().
UDP_IP_HEADER = 20 + 8
MAX_PAYLOAD = 1500 - (UDP_IP_HEADER + HEADER_LEN)


class ApiChannel(Enum):
    ALL = 0
    USER = 1
    CTRL = 2
    AUTH = 3
    GOSSIP = 4
    BTC_SRC = 5


class BlocksatPkt:
    """Blocksat Packet

    The Blocksat Packet is what goes on the payload of every UDP datagram sent
    over satellite for API traffic. It is responsible for transporting API
    messages (defined on msg.py). Because an API message can be larger than the
    payload capacity of a UDP datagram, multiple Blocksat Packets can be used
    to convey a message. In this case, each Blocksat Packet is referred to as a
    fragment of the API message.

    Each blocksat packet carries an 8-byte header and its payload. The header
    contains the fragment number and the corresponding API message sequence
    number. The latter can be used to aggregate Blocksat Packets (i.e.,
    fragments) associated with the same API message. Furthermore, the header
    contains the so-called "channel number", which is used to support
    multiplexing and filtering of specific API packet streams (i.e., channels).

    This class implements the Blocksat Packet structure. It can serialize the
    packet contents into a bytes array with the full concatenated packet
    (header+payload). It can also execute the reverse, i.e., unpack/deserialize
    the contents of a packet into the corresponding header and payload fields.

    """
    def __init__(self,
                 seq_num=None,
                 frag_num=None,
                 chan_num=None,
                 more_frags=None,
                 payload=None):
        if (chan_num is not None):
            assert(chan_num >= 0 and chan_num < 256), \
                "Channel number must be >=0 && < 256"
        self.seq_num = seq_num
        self.frag_num = frag_num
        self.chan_num = chan_num
        self.more_frags = more_frags
        self.payload = payload

    def pack(self):
        """Form Blocksat Packet
        """
        # Assert the "more fragments" (MF) bit if this isn't the last fragment
        octet_0 = API_TYPE_MORE_FRAG if self.more_frags else API_TYPE_LAST_FRAG
        header = struct.pack(HEADER_FORMAT, octet_0, self.chan_num,
                             self.frag_num, self.seq_num)
        return header + self.payload

    def unpack(self, udp_payload):
        """Unpack Blocksat Packet from UDP payload

        Args:
            udp_payload : UDP payload received via socket (bytes)

        Returns:
            Tuple with the Blocksat Packet's payload (bytes) and sequence
            number.

        """
        assert (isinstance(udp_payload, bytes))
        assert (len(udp_payload) >= HEADER_LEN)

        # Separate header and payload
        header = udp_payload[:HEADER_LEN]
        self.payload = udp_payload[HEADER_LEN:]

        # Parse header
        octet_0, self.chan_num, self.frag_num, self.seq_num = struct.unpack(
            HEADER_FORMAT, header)

        # Sanity check
        assert (ord(octet_0) & 1), "Not an API packet"

        # Are there more fragments coming?
        self.more_frags = bool(ord(octet_0) & ord(b'\x80'))

        logger.debug("BlocksatPkt: Seq Num: {} / Frag Num: {} / MF: {}".format(
            self.seq_num, self.frag_num, self.more_frags))

    def __len__(self):
        return HEADER_LEN + len(self.payload)


class BlocksatPktHandler:
    """Blocksat Packet Handler

    The handler class is responsible for processing individual Blocksat Packets
    and aggregating them into multiple packets that convey an ApiMsg
    structure. It also handles the reverse operation, i.e., starting from an
    ApiMsg, it generates multiple Blocksat Packets.

    """
    def __init__(self, timeout=7200):
        """BlocksatPktHandler Constructor

        Args:
            timeout : Timeout in seconds to remove old pending fragments.

        """
        self.frag_map = {}
        self.timeout = timeout

    def _check_gaps(self, seq_num):
        """Check if there is any fragment number gap

        Returns:
            (bool) True when there are no gaps (everything is OK).

        """
        frag_idxs = sorted(self.frag_map[seq_num]['frags'].keys())
        for i, x in enumerate(frag_idxs):
            if (i == 0 and x != 0):
                if (x > 1):
                    logger.warning("First {:d} fragments were lost".format(x))
                else:
                    logger.warning("First fragment was lost")
                return False
            elif (i > 0 and x - frag_idxs[i - 1] != 1):
                logger.warning("Gap between fragment {:d} and fragment "
                               "{:d}".format(frag_idxs[i - 1], x))
                return False
        return True

    def _check_ready(self, seq_num):
        """Check if the collection of Blocksat Packets is ready to be decoded

        Returns:
            (bool) True when ready to be decoded.

        """
        # The message can only be ready when the last fragment is available:
        i_last_frag = self.frag_map[seq_num]['last_frag']
        if (i_last_frag is None):
            return False

        # Because packets can be processed out of order, check that all packets
        # before the last fragment are also available:
        frags = self.frag_map[seq_num]['frags'].keys()
        return all([i in frags for i in range(i_last_frag)])

    def _concat_pkt(self, pkt):
        """Concatenate a single BlocksatPkt within a concatenation cache"""
        seq_num = pkt.seq_num

        # If it's an out-of-order packet, re-compute the concatenated
        # version. Otherwise, just append directly to the cache.
        if (self.frag_map[seq_num]['high_frag'] is not None
                and pkt.frag_num < self.frag_map[seq_num]['high_frag']):

            concat_msg = bytearray()
            for i_frag, frag in sorted(
                    self.frag_map[seq_num]['frags'].items()):
                concat_msg += frag.payload

            self.frag_map[seq_num]['concat'] = concat_msg
        else:
            self.frag_map[seq_num]['concat'] += pkt.payload

    def append(self, pkt):
        """Append incoming BlocksatPkt

        Append the incoming Blocksat packet to the map of packets (fragments)
        pertaining to the same API message. Once the last fragment of a
        sequence comes, let the caller know that the API message is ready to be
        decoded.

        Args:
            pkt : Incoming BlocksatPkt

        Returns:
            (bool) True if the underlying ApiMsg is ready to be extracted from
            the corresponding collection of packets.

        """
        assert (isinstance(pkt, BlocksatPkt))

        if (pkt.seq_num not in self.frag_map):
            self.frag_map[pkt.seq_num] = {
                'high_frag': None,
                'last_frag': None,
                'concat': bytearray()
            }
            self.frag_map[pkt.seq_num]['frags'] = {}

        # Do not process a repeated fragment
        if (pkt.frag_num in self.frag_map[pkt.seq_num]['frags']):
            logger.debug("BlocksatPktHandler: fragment {} has already "
                         "been received".format(pkt.frag_num))
            # Check if the repeated fragment actually has the same contents
            pre_existing_pkt = self.frag_map[pkt.seq_num]['frags'][
                pkt.frag_num]
            if (pkt.payload != pre_existing_pkt.payload):
                logger.warning(
                    "Got the same fragment twice but with different contents "
                    "(frag_num: {}, seq_num: {})".format(
                        pkt.frag_num, pkt.seq_num))
            return self._check_ready(pkt.seq_num)

        self.frag_map[pkt.seq_num]['frags'][pkt.frag_num] = pkt

        # Timestamp the last fragment reception of this sequence number. Use
        # this timestamp to clean old fragments that were never decoded.
        self.frag_map[pkt.seq_num]['t_last'] = time.time()

        # Concatenate payload by payload instead of waiting to concatenate
        # everything in the end when the message is ready.
        self._concat_pkt(pkt)

        # Track the highest fragment number received so far. This information
        # is used to identify whether the concatenation cache needs to be
        # recomputed for out-of-order packets (see _concat_pkt()).
        if (self.frag_map[pkt.seq_num]['high_frag'] is None
                or pkt.frag_num > self.frag_map[pkt.seq_num]['high_frag']):
            self.frag_map[pkt.seq_num]['high_frag'] = pkt.frag_num

        # Track the last fragment of the sequence. This information is used to
        # more quickly verify whether the message is ready (see
        # _check_ready()).
        if (not pkt.more_frags):
            self.frag_map[pkt.seq_num]['last_frag'] = pkt.frag_num

        logger.debug("BlocksatPktHandler: Append fragment {}, "
                     "Seq Num {}".format(pkt.frag_num, pkt.seq_num))

        return self._check_ready(pkt.seq_num)

    def get_frags(self, seq_num):
        """Get the Blocksat Packets sorted by fragment number"""
        return [x[1] for x in sorted(self.frag_map[seq_num]['frags'].items())]

    def get_n_frags(self, seq_num):
        """Return the number of fragments corresponding to a sequence number"""
        return len(self.frag_map[seq_num]['frags'].keys())

    def concat(self, seq_num, force=False):
        """Concatenate all Blocksat Packet payloads composing an API message

        Args:
            seq_num : API message sequence number
            force   : Force concatenation even if there are fragment gaps

        Returns:
            Bytes array with the concatenated payloads

        """
        assert (seq_num in self.frag_map)

        # The caller should call this function only when it's known that the
        # message can be decoded
        if (not force and not self._check_gaps(seq_num)):
            raise RuntimeError("Gap found between message fragments")

        if (not force and not self._check_ready(seq_num)):
            raise RuntimeError("Tried to decode while fragments are missing")

        logger.debug("BlocksatPktHandler: Concatenated message with {} bytes "
                     "(force: {})".format(
                         len(self.frag_map[seq_num]['concat']), force))

        # Take the concatenated message directly from the cache
        return bytes(self.frag_map[seq_num]['concat'])

    def split(self, data, seq_num, chan_num):
        """Split data array into Blocksat Packet(s)

        An API message may be sent over multiple packet in case its length
        exceeds the maximum UDP payload. This function splits the message into
        packets and saves all the generated Blocksat Packets into the internal
        fragment map.

        Args:
            data     : Bytes object containing the API message data
            seq_num  : API Tx sequence number (`tx_seq_num` field)
            chan_num : API channel number

        """
        assert (isinstance(data, bytes))
        n_frags = ceil(len(data) / MAX_PAYLOAD)

        logger.debug("BlocksatPktHandler: Message size: {:d} bytes\t"
                     "Fragments: {:d}".format(len(data), n_frags))

        for i_frag in range(n_frags):
            # Is this the last_fragment?
            more_frags = (i_frag + 1) < n_frags

            # Byte range of the data to send on this Blocksat packet
            s_byte = i_frag * MAX_PAYLOAD  # starting byte
            e_byte = (i_frag + 1) * MAX_PAYLOAD  # ending byte

            # Packetize
            pkt = BlocksatPkt(seq_num, i_frag, chan_num, more_frags,
                              data[s_byte:e_byte])

            # Add to fragment map
            self.append(pkt)

    def clean(self):
        """Throw away old (timed-out) pending fragments
        """
        # Find the timed-out messages
        timed_out = []
        t_now = time.time()
        for seq_num in self.frag_map:
            if (t_now - self.frag_map[seq_num]['t_last'] > self.timeout):
                timed_out.append(seq_num)

        # Delete the timed-out messages
        for seq_num in timed_out:
            logger.debug("BlocksatPktHandler: Delete Seq Num {} from fragment "
                         "map".format(seq_num))
            del self.frag_map[seq_num]


def calc_ota_msg_len(msg_len):
    """Compute the number of bytes sent over-the-air (OTA) for an API message

    The API message is carried by Blocksat Packets, sent in the payload of UDP
    datagrams over IPv4, with a layer-2 MTU of 1500 bytes, and, ultimately,
    transported over MPE. If the message size is such that the UDP/IPv4 packet
    exceeds the layer-2 MTU, fragmentation is not handled at the IP level but
    instead at application layer, i.e., at the Blocksat Packet protocol level.

    Args:
        msg_len : Length of the API message to be transmitted

    """
    # Is it going to be fragmented?
    n_frags = ceil(msg_len / MAX_PAYLOAD)

    # Including all fragments, the total Blocksat + UDP + IPv4 overhead is:
    total_overhead = (UDP_IP_HEADER + HEADER_LEN) * n_frags

    # Total overhead at MPE layer:
    mpe_header = 16
    total_mpe_overhead = mpe_header * n_frags

    return total_mpe_overhead + total_overhead + msg_len
