"""Encapsulation of API messages into Blocksat Packets"""
import logging, struct
from math import ceil


logger             = logging.getLogger(__name__)
HEADER_FORMAT      = '!cxHI'
# Header format:
# octet 0    : Type bit on LSB, MF bit on MSB
# octet 1    : Reserved
# octets 2-3 : Fragment number
# octets 4-7 : API message's sequence number
HEADER_LEN         = 8
TYPE_API_DATA      = b'\x01'
API_TYPE_LAST_FRAG = b'\x01' # Type=1 (API), MF=0
API_TYPE_MORE_FRAG = b'\x81' # Type=1 (API), MF=1
# Maximum Blocksat Packet payload in bytes to avoid fragmentation at IPv4 level:
#
# NOTE: The maximum Blocksat Packet payload considers the space occupied by the
# Blocksat Packet, UDP and IP headers. That is, 8 (blocksat header) + 8 (UDP
# header) + 20 (minimum IPv4 header), which add to 36 bytes. It also considers a
# layer-2 MTU of 1500 bytes. See the explanation on calc_ota_msg_len().
UDP_IP_HEADER      = 20 + 8
MAX_PAYLOAD        = 1500 - (UDP_IP_HEADER + HEADER_LEN)


class BlocksatPkt:
    """Blocksat Packet

    The Blocksat Packet is what goes on the payload of every UDP datagram sent
    over satellite for API traffic. It is responsible for transporting API
    messages (defined on msg.py). Because an API message can be larger than the
    payload capacity of a UDP datagram, multiple Blocksat Packets can be used to
    convey a message. In this case, each Blocksat Packet is referred to as a
    fragment of the API message.

    Each blocksat packet carries an 8-byte header and its payload, which is the
    fragment of the API Message. The header contains the fragment number and the
    corresponding API message sequence number. The latter can be used to
    aggregate Blocksat Packets corresponding to the same API message.

    This class implements the Blocksat Packet structure. It can generate a bytes
    array with the full concatenated packet (header + payload). It can also do
    the reverse, i.e., unpack the contents of a packet into header and payload.

    """
    def __init__(self, seq_num=None, frag_num=None, more_frags=None,
                 payload=None):
        self.seq_num    = seq_num
        self.frag_num   = frag_num
        self.more_frags = more_frags
        self.payload    = payload

    def pack(self):
        """Form Blocksat Packet
        """
        # Assert the "more fragments" (MF) bit if this isn't the last fragment
        octet_0 = API_TYPE_MORE_FRAG if self.more_frags else API_TYPE_LAST_FRAG
        header  = struct.pack(HEADER_FORMAT, octet_0, self.frag_num,
                              self.seq_num)
        return header + self.payload

    def unpack(self, udp_payload):
        """Unpack Blocksat Packet from UDP payload

        Args:
            udp_payload : UDP payload received via socket (bytes)

        Returns:
            Tuple with the Blocksat Packet's payload (bytes) and sequence number

        """
        assert(isinstance(udp_payload, bytes))
        assert(len(udp_payload) >= HEADER_LEN)

        # Separate header and payload
        header       = udp_payload[:HEADER_LEN]
        self.payload = udp_payload[HEADER_LEN:]

        # Parse header
        octet_0, self.frag_num, self.seq_num = struct.unpack(
            HEADER_FORMAT, header)

        # Sanity check
        assert(ord(octet_0) & 1), "Not an API packet"

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
    def __init__(self):
        self.frag_map = {}

    def _check_gaps(self, seq_num):
        """Check if there is any fragment number gap

        Returns:
            (bool) True when there are no gaps (everything is OK).

        """
        frag_idxs = sorted(self.frag_map[seq_num].keys())
        for i,x in enumerate(frag_idxs):
            if (i == 0 and x != 0):
                if (x > 1):
                    logger.warning("First {:d} fragments were lost".format(x))
                else:
                    logger.warning("First fragment was lost")
                return False
            elif (i > 0 and x - frag_idxs[i-1] != 1):
                logger.warning("Gap between fragment {:d} and fragment "
                               "{:d}".format(frag_idxs[i-1], x))
                return False
        return True

    def _check_ready(self, seq_num):
        """Check if the collection of Blocksat Packets is ready to be decoded

        Returns:
            (bool) True when ready to be decoded.

        """
        # Find the last fragment of the sequence
        i_last_frag = None
        for pkt in self.frag_map[seq_num].values():
            if (not pkt.more_frags):
                i_last_frag = pkt.frag_num
                break;

        # The message can only be ready when the last fragment is available:
        if (i_last_frag is None):
            return False

        # Because packets can be processed out of order, check that all packets
        # before the last fragment are also available:
        frags = self.frag_map[pkt.seq_num].keys()
        return all([i in frags for i in range(i_last_frag)])

    def append(self, pkt):
        """Append incoming BlocksatPkt

        Append the incoming Blocksat packet to the map of packets (fragments)
        pertaining to the same API message. Once the last fragment of a sequence
        comes, let the caller know that the API message is ready to be decoded.

        Returns:
            (bool) True if the underlying ApiMsg is ready to be extracted from
            the corresponding collection of packets.

        """
        assert(isinstance(pkt, BlocksatPkt))

        if (pkt.seq_num not in self.frag_map):
            self.frag_map[pkt.seq_num] = {}

        self.frag_map[pkt.seq_num][pkt.frag_num] = pkt

        logger.debug("BlocksatPktHandler: Append fragment {}, "
                     "Seq Num {}".format(pkt.frag_num, pkt.seq_num))

        return self._check_ready(pkt.seq_num)

    def get_frags(self, seq_num):
        """Get the Blocksat Packets sorted by fragment number"""
        return [x[1] for x in sorted(self.frag_map[seq_num].items())]

    def get_n_frags(self, seq_num):
        """Return the number of fragments corresponding to a sequence number"""
        return len(self.frag_map[seq_num].keys())

    def concat(self, seq_num):
        """Concatenate all Blocksat Packet payloads composing an API message"""
        assert(seq_num in self.frag_map)

        # The caller should call this function only when it's known that the
        # message can be decoded
        if (not self._check_gaps(seq_num)):
            raise RuntimeError("Gap found between message fragments")

        if (not self._check_ready(seq_num)):
            raise RuntimeError("Tried to decode while fragments are missing")

        api_msg = bytes()
        for i_frag in sorted(self.frag_map[seq_num]):
            assert(isinstance(self.frag_map[seq_num][i_frag].payload, bytes))
            api_msg += self.frag_map[seq_num][i_frag].payload
        return api_msg

    def split(self, data, seq_num):
        """Split data array into Blocksat Packet(s)

        An API message may be sent over multiple packet in case its length
        exceeds the maximum UDP payload. This function splits the message into
        packets and saves all the generated Blocksat Packets into the internal
        fragment map.

        Args:
            data    : Bytes object containing the API message data
            seq_num : API Tx sequence number (`tx_seq_num` field)

        """
        assert(isinstance(data, bytes))
        n_frags = ceil(len(data) / MAX_PAYLOAD)
        pkts    = list()

        logging.debug("Message size: {:d} bytes\tFragments: {:d}".format(
            len(data), n_frags))

        if (seq_num not in self.frag_map):
            self.frag_map[seq_num] = {}

        for i_frag in range(n_frags):
            # Is this the last_fragment?
            more_frags = (i_frag + 1) < n_frags

            # Byte range of the data to send on this Blocksat packet
            s_byte  = i_frag * MAX_PAYLOAD # starting byte
            e_byte  = (i_frag + 1) * MAX_PAYLOAD # ending byte

            # Packetize
            pkt = BlocksatPkt(seq_num, i_frag, more_frags, data[s_byte:e_byte])

            # Add to fragment map
            self.frag_map[seq_num][i_frag] = pkt


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

