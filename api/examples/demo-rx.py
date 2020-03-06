#!/usr/bin/env python3
"""
Read API data directly via internet and output to pipe
"""

import sys, argparse, textwrap, requests, struct, json, logging, time, socket, \
    errno, fcntl, datetime
import sseclient, urllib3, certifi


# Constants/definitions
HEADER_FORMAT = '!c3xI'  # first octet has MF bit and the type bit
TYPE_API_DATA = b'\x01'
MAX_SEQ_NUM   = 2 ** 31  # Maximum transmission sequence number
SIOCGIFINDEX  = 0x8933 # Ioctl request for interface index


def packetize(data, seq_num):
    """Place data into a Blocksat Packet

    Assumes fragmentation is not used, since it is not necessary over UDP.

    Args:
        data    : API message data buffer
        seq_num : API Tx sequence number (`tx_seq_num` field)

    Returns:
        Packet as bytes array

    """
    header = struct.pack(HEADER_FORMAT, TYPE_API_DATA, seq_num)
    pkt    = header + data

    return pkt


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


def open_sock(ifname, port, multiaddr):
    """Open socket

    Args:
        ifname    : Network interface name
        port      : Port that socket should be bound to
        multiaddr : Multicast group to which this application transmits

    """

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

    # Enable multicast loop
    #
    # NOTE: this will allow the API data reader application to receive the UDP
    # segments.
    multicast_loop_on = struct.pack('b', 1)
    sock.setsockopt(socket.IPPROTO_IP,
                    socket.IP_MULTICAST_LOOP,
                    multicast_loop_on)

    # Set multicast TTL
    ttl = struct.pack('b', 1)
    sock.setsockopt(socket.IPPROTO_IP,
                    socket.IP_MULTICAST_TTL,
                    ttl)

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
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('-d', '--dest', default="239.0.0.2:4433",
                        help='Destination address (ip:port) to which ' +
                        'API data will be sent (default: 239.0.0.2:4433)')

    parser.add_argument('-i', '--interface',
                        help="Network interface over which to send API data",
                        default=None)

    group = parser.add_mutually_exclusive_group()
    group.add_argument('--net', choices=['main', 'test'],
                       default=None,
                       help='Choose Mainnet (main) or Testnet (test) ' +
                       'Satellite API server (default: main)')
    group.add_argument('-s', '--server',
                       default='https://api.blockstream.space',
                       help='Satellite API server address (default: ' +
                       'https://api.blockstream.space)')

    parser.add_argument('-p', '--port', default=None,
                        help='Satellite API server port (default: None)')

    parser.add_argument('--debug', action='store_true',
                        help='Debug mode (default: false)')

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

    # Open socket
    sock = open_sock(args.interface, dest_port, dest_ip)

    # Always keep a record of the last received sequence number
    last_seq_num = None

    print("Connecting with Satellite API server...")
    while (True):
        try:
            # Server-sent Events (SSE) Client
            http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED',
                                       ca_certs=certifi.where())
            r = http.request('GET', server_addr + "/subscribe/transmissions",
                             preload_content=False)
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
                if (order["status"] == "sent"):
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
                        end_time  = order["ended_transmission_at"]
                        timestamp = datetime.datetime.strptime(end_time,
                                                               "%Y-%m-%dT%H:%M:%S.%fZ")

                        print("%s Message #%-5d\tSize: %d bytes\t" %(
                            timestamp.strftime('%b %d %Y %H:%M:%S'),
                            expected_seq_num, order["message_size"]))

                        # Get the data
                        data = fetch_api_data(server_addr, expected_seq_num)

                        if (data is not None):
                            # Put API data on a Blocksat packet
                            pkt_data = packetize(data, expected_seq_num)

                            # Send the packet
                            sock.sendto(pkt_data, (dest_ip, dest_port))
                            logging.debug("Send %d bytes to socket" %(
                                len(data)))

                        # Record the sequence number of the order that was received
                        last_seq_num = expected_seq_num

        except urllib3.exceptions.ProtocolError as e:
            logging.debug(e)
            print("Connection failed - trying again...")
            time.sleep(1)
            pass
        except urllib3.exceptions.MaxRetryError as e:
            logging.debug(e)
            print("ERROR: Maximum number of connection retries exceeded")
            exit()


if __name__ == '__main__':
    main()
