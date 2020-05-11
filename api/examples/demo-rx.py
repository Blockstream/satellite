#!/usr/bin/env python3
"""
Read API data directly via internet and output to pipe
"""

import sys, argparse, textwrap, requests, struct, json, logging, time, socket, \
    errno, fcntl, datetime, math
import sseclient


# Constants/definitions
HEADER_FORMAT = '!cxHI'
# Header format:
# octet 0    : Type bit on LSB, MF bit on MSB
# octet 1    : Reserved
# octets 2-3 : Fragment number
# octets 4-7 : API message's sequence number
API_TYPE_LAST_FRAG = b'\x01' # Type=1 (API), MF=0
API_TYPE_MORE_FRAG = b'\x81' # Type=1 (API), MF=1
MAX_SEQ_NUM        = 2 ** 31  # Maximum transmission sequence number
SIOCGIFINDEX       = 0x8933 # Ioctl request for interface index
MAX_UDP_PLOAD      = 2**16 - 36 - 1 # maximum UDP payload size in bytes
# NOTE: the maximum payload includes the Blocksat, UDP and IP headers. That is,
# 8 (blocksat) + 8 (udp) + 20 (ip) = 36.


def packetize(data, seq_num):
    """Place data into Blocksat Packet(s)

    An API message may be sent over multiple packet in case its length exceeds
    the maximum UDP payload.

    Args:
        data    : Bytes object containing the API message data
        seq_num : API Tx sequence number (`tx_seq_num` field)

    Returns:
        List of Blocksat packets that will convey the given API message, each
        one being a Bytes object.

    """
    assert(isinstance(data, bytes))
    n_frags = math.ceil(len(data) / MAX_UDP_PLOAD)
    pkts    = list()

    logging.debug("Message size: %d bytes\tFragments: %d" %(len(data), n_frags))

    for i_frag in range(n_frags):
        # Assert more fragments (MF) bit if this isn't the last fragment
        octet_0 = API_TYPE_LAST_FRAG if ((i_frag + 1) == n_frags) else \
                  API_TYPE_MORE_FRAG
        header  = struct.pack(HEADER_FORMAT, octet_0, i_frag, seq_num)

        # Byte range of the data to send on this Blocksat packet
        s_byte  = i_frag * MAX_UDP_PLOAD # starting byte
        e_byte  = (i_frag + 1) * MAX_UDP_PLOAD # ending byte
        pkt     = header + data[s_byte:e_byte]
        pkts.append(pkt)

    return pkts


def send_pkts(socks, pkts, ip, port):
    """Send Blocksat packets corresponding to one API message

    Args:
        pkts : List of Blocksat packet structures to be sent
        ip   : Destination IP address
        port : Destination UDP port

    """
    assert(isinstance(pkts, list))
    assert(isinstance(socks, list))

    for i, pkt in enumerate(pkts):
        for sock in socks:
            sock.sendto(pkt, (ip, port))
            logging.debug("Send packet %d - %d bytes" %(
                i, len(pkt)))


def fetch_api_data(server_addr, seq_num):
    """Download a given message from the Satellite API

    Args:
        server_addr : Satellite API server address
        seq_num     : Message sequence number

    Returns:
        Message data as sequence of bytes

    """
    logging.debug("Fetch message #%s from API" %(seq_num))
    r = requests.get(server_addr + '/message/' + str(seq_num))

    r.raise_for_status()

    if (r.status_code == requests.codes.ok):
        data        = r.content
        return data


def confirm_tx(server_addr, seq_num, regions):
    """Confirm transmission

    Args:
        server_addr : Satellite API server address
        seq_num     : API's message sequence number
        regions     : Regions that were covered by the transmission

    """
    if regions is None:
        return

    assert(isinstance(regions, list))

    logging.info("Confirm transmission of message #%s on regions %s" %(
        seq_num, regions))
    r = requests.post(server_addr + '/order/tx/' + str(seq_num),
                      data = {
                          'regions': json.dumps(regions)
                      })
    if not r.ok:
        logging.error("Failed to confirm Tx of #%d [status code %d]" %(
            seq_num, r.status_code
        ))
    else:
        logging.info("Server response: " + r.json()['message'])


def open_sock(ifname, port, multiaddr, ttl=1, dscp=0):
    """Open socket

    Args:
        ifname    : Network interface name
        port      : Port that socket should be bound to
        multiaddr : Multicast group to which this application transmits

    """
    assert(ttl <= 255)
    logging.debug("Open socket to interface {}".format(ifname))

    # Open output socket
    sock = socket.socket(socket.AF_INET,
                         socket.SOCK_DGRAM)

    # Allow reuse and bind
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', port))

    # Get index of target interface
    if (ifname is not None):
        ifreq    = struct.pack('16si', ifname.encode(), 0)
        res      = fcntl.ioctl(sock.fileno(), SIOCGIFINDEX, ifreq)
        ifindex  = int(struct.unpack('16si', res)[1])
    else:
        ifindex  = 0

    # Define the interface over which to send the multicast messages
    ip_mreqn = struct.pack('4s4si',
                           socket.inet_aton(multiaddr),
                           socket.inet_aton('0.0.0.0'),
                           ifindex)
    sock.setsockopt(socket.IPPROTO_IP,
                    socket.IP_MULTICAST_IF,
                    ip_mreqn)

    # Set multicast TTL
    sock.setsockopt(socket.IPPROTO_IP,
                    socket.IP_MULTICAST_TTL,
                    struct.pack('b', ttl))

    # Set DSCP
    sock.setsockopt(socket.IPPROTO_IP,
                    socket.IP_TOS,
                    struct.pack('b', dscp))

    return sock


def main():
    parser = argparse.ArgumentParser(
        description=textwrap.dedent('''\
        Demo Blockstream Satellite Receiver

        Receives data from the Satellite API though the internet and sends the data to
        the multicast address that the API data reader listens to.

        This application can be used to test the API data reader in the absence of the
        real Blocksat receiver. The latter normally receives the multicast-addressed UDP
        segments that the API data reader waits for. This application, in turn, produces
        the multicast-addressed UDP segments after fetching the data through the
        internet, rather than receiving via satellite.

        '''),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument('-d', '--dest', default="239.0.0.2:4433",
                        help='Destination address (ip:port) to which ' +
                        'API data will be sent')

    parser.add_argument('-i', '--interface',
                        nargs="+",
                        help="Network interface(s) over which to send API \
                        data. If multiple interfaces are provided, the same \
                        packets are sent over the given interfaces.",
                        default=["lo"])

    parser.add_argument('-r', '--regions',
                        nargs="+",
                        choices=range(0, 5),
                        type=int,
                        help='Coverage region for Tx confirmations')

    group = parser.add_mutually_exclusive_group()
    group.add_argument('--net', choices=['main', 'test'],
                       default=None,
                       help='Choose Mainnet (main) or Testnet (test) ' +
                       'Satellite API server')
    group.add_argument('-s', '--server',
                       default='https://api.blockstream.space',
                       help='Satellite API server address')

    parser.add_argument('-p', '--port', default=None,
                        help='Satellite API server port')

    parser.add_argument('--ttl', type=int, default=1,
                        help='Time to live of multicast packets')

    parser.add_argument('--dscp', type=int, default=[0],
                        nargs="+",
                        help='Differentiated services code point (DSCP) of \
                        the output multicast IP packets. If multiple DSCPs are \
                        provided, the same packets are transmitted (repeated) \
                        over the given interface(s) with the given DSCPs.')

    parser.add_argument('-e', '--event', choices=["transmitting", "sent"],
                        default="sent",
                        help='SSE event that triggers packet transmissions')

    parser.add_argument('--debug', action='store_true',
                        help='Debug mode')

    args   = parser.parse_args()
    server = args.server
    net    = args.net

    # Switch debug level
    if (args.debug):
        logging.basicConfig(
            format='%(asctime)s %(levelname)-8s %(message)s',
            datefmt='%b %d %Y %H:%M:%S',
            level=logging.DEBUG)
        logging.debug('[Debug Mode]')
    else:
        logging.basicConfig(
            format='%(asctime)s %(levelname)-8s %(message)s',
            datefmt='%b %d %Y %H:%M:%S',
            level=logging.INFO)

    # Parse the server address
    if (net is not None and net == "main"):
        server = "https://api.blockstream.space"
    elif (net is not None and net == "test"):
        server = "https://api.blockstream.space/testnet"

    server_addr = server

    if (args.port is not None):
        server_addr = server + ":" + args.port

    if (server_addr == 'https://satellite.blockstream.com'):
        server_addr += '/api'

    # Parse UDP socket address
    dest_ip, dest_port_str = args.dest.split(":")
    dest_port              = int(dest_port_str)
    assert(dest_ip is not None), "UDP source IP is not defined"
    assert(dest_port is not None), "UDP port is not defined"
    logging.debug("Send Satellite API packets to %s:%s" %(dest_ip, dest_port))

    # Open sockets. Create one socket per interface and DSCP. For example, if
    # two DSCPs are specified, launch two sockets for each interface.
    socks = list()
    assert(isinstance(args.interface, list))
    assert(isinstance(args.dscp, list))
    for interface in args.interface:
        for dscp in args.dscp:
            socks.append(open_sock(interface, dest_port, dest_ip, args.ttl,
                                   dscp))

    # Always keep a record of the last received sequence number
    last_seq_num = None

    print("Connecting with Satellite API server...")
    while (True):
        try:
            # Server-sent Events (SSE) Client
            r = requests.get(server_addr + "/subscribe/transmissions",
                             stream=True)
            r.raise_for_status()
            client = sseclient.SSEClient(r)
            print("Connected. Waiting for events...\n")

            # Continuously wait for events
            for event in client.events():
                # Parse the order corresponding to the event
                order = json.loads(event.data)

                # Debug
                logging.debug("Order: " + json.dumps(order, indent=4,
                                                     sort_keys=True))

                # Download the message only if its order has "sent" state
                if (order["status"] == args.event):
                    # Sequence number
                    seq_num = order["tx_seq_num"]

                    rx_pending = True
                    while (rx_pending):
                        # Receive all messages until caught up
                        if (last_seq_num is None):
                            expected_seq_num = seq_num
                        else:
                            expected_seq_num = last_seq_num + 1

                        # Is this an interation to catch up with a sequence
                        # number gap or a normal transmission iteration?
                        if (seq_num == expected_seq_num):
                            rx_pending = False
                        else:
                            logging.info("Catch up with transmission %d" %(
                                expected_seq_num))

                        # Log
                        tstamp_field = "started_transmission_at" if \
                                       args.event == "transmitting" else \
                                       "ended_transmission_at"
                        timestamp = datetime.datetime.strptime(
                            order[tstamp_field], "%Y-%m-%dT%H:%M:%S.%fZ")

                        print("%s Message #%-5d\tSize: %d bytes\t" %(
                            timestamp.strftime('%b %d %Y %H:%M:%S'),
                            expected_seq_num, order["message_size"]))

                        # Get the data
                        data = fetch_api_data(server_addr, expected_seq_num)

                        if (data is not None):
                            # Put API data on Blocksat packet(s)
                            pkts = packetize(data, expected_seq_num)

                            # Send the packet(s)
                            send_pkts(socks, pkts, dest_ip, dest_port)

                            # Send transmission confirmation to the server
                            confirm_tx(server_addr, expected_seq_num,
                                       args.regions)

                        # Record the sequence number of the order that was received
                        last_seq_num = expected_seq_num

        except requests.exceptions.ChunkedEncodingError as e:
            logging.debug(e)
            pass

        except requests.exceptions.ConnectionError as e:
            logging.debug(e)
            time.sleep(2)
            pass

        except requests.exceptions.RequestException as e:
            logging.debug(e)
            time.sleep(2)
            pass

        except KeyboardInterrupt:
            exit()

        logging.info("Reconnecting...")


if __name__ == '__main__':
    main()
