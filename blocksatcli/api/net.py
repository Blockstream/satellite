"""Socket communication"""
import errno
import fcntl
import ipaddress
import logging
import socket
import struct

logger = logging.getLogger(__name__)
SIOCGIFINDEX = 0x8933  # Ioctl request for interface index
IP_MULTICAST_ALL = 49
MAX_READ = 2048


class UdpSock():
    def __init__(self, sock_addr, ifname, mcast_rx=True):
        """Instantiate UDP socket

        Args:
            sock_addr : Socket address string
            ifname    : Network interface name
            mcast_rx  : Use socket to receive multicast packets.

        Returns:
            Socket object

        """
        assert (":" in sock_addr), "Socket address must be in ip:port format"
        self.ip = sock_addr.split(":")[0]
        assert (ipaddress.ip_address(self.ip))  # parse address
        self.port = int(sock_addr.split(":")[1])
        self.ifindex = None

        assert (self.ip is not None), "UDP source IP is not defined"
        assert (self.port is not None), "UDP port is not defined"
        logger.debug("Connect with UDP socket %s:%s" % (self.ip, self.port))

        try:
            # Open and bind socket to Blocksat API port
            self.sock = sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

            # Allow reuse and bind
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('', self.port))

            # Get the network interface index
            self._get_ifindex(ifname)

            # Join multicast group if listening
            if (mcast_rx):
                self._join_mcast_group()

        except socket.error as e:
            if (e.errno == errno.EADDRNOTAVAIL):
                logger.error("Error on connection with UDP socket %s:%s" %
                             (self.ip, self.port))
                logger.info(
                    "Use argument `--sock-addr` to define the socket address.")
            raise

    def __del__(self):
        """Destructor"""
        if hasattr(self, 'sock'):
            self.sock.close()

    def _get_ifindex(self, ifname):
        """Get the index of a given interface name"""
        if (ifname is not None):
            ifreq = struct.pack('16si', ifname.encode(), 0)
            res = fcntl.ioctl(self.sock.fileno(), SIOCGIFINDEX, ifreq)
            self.ifindex = int(struct.unpack('16si', res)[1])
        else:
            self.ifindex = 0

    def _join_mcast_group(self):
        """Join multicast group on the chosen interface"""
        if (self.ifindex != 0):
            logger.debug("Join multicast group %s on network interface %d" %
                         (self.ip, self.ifindex))
        else:
            logger.debug("Join group %s with the default network interface" %
                         (self.ip))

        ip_mreqn = struct.pack('4s4si', socket.inet_aton(self.ip),
                               socket.inet_aton('0.0.0.0'), self.ifindex)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP,
                             ip_mreqn)

        # Make sure that this socket receives messages solely from the above
        # group that was explicitly joined above
        self.sock.setsockopt(socket.IPPROTO_IP, IP_MULTICAST_ALL, 0)

    def set_mcast_tx_opts(self, ttl=1, dscp=0):
        """Set options used for transmission of multicast-addressed packets

        Args:
            ttl  : Time-to-live
            dscp : Differentiated services code point (DSCP)

        """
        # Define the interface over which to send the multicast messages
        ip_mreqn = struct.pack('4s4si', socket.inet_aton(self.ip),
                               socket.inet_aton('0.0.0.0'), self.ifindex)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF,
                             ip_mreqn)

        # Set multicast TTL
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL,
                             struct.pack('b', ttl))

        # Set DSCP
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_TOS,
                             struct.pack('b', dscp))

        # Don't loop Tx messages back to us
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 0)

    def send(self, data):
        """Transmit UDP packet

        Args:
            data : data to transmit over the UDP payload

        """
        self.sock.sendto(data, (self.ip, self.port))

    def recv(self):
        """Blocking receive

        Returns:
            Received data.

        """
        return self.sock.recvfrom(MAX_READ)
