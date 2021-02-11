import os
import queue
import random
import shutil
import string
import time
from unittest import TestCase, mock
from threading import Thread

from . import msg
from .gpg import Gpg
from .listen import ApiListener
from .net import UdpSock
from .pkt import BlocksatPktHandler, ApiChannel

gpghome = "/tmp/.gnupg-test"
gpgpassphrase = "test"


def rnd_string(n_bytes=1000):
    """Generate random string with a given number of bytes"""
    return ''.join(
        random.choice(string.ascii_letters + string.digits)
        for _ in range(n_bytes)).encode()


def gen_pkts(tx_msg, channel=1, seq_num=1):
    """Generate BlocksatPkts for a given API message"""
    assert (isinstance(tx_msg, msg.ApiMsg))
    tx_handler = BlocksatPktHandler()
    tx_handler.split(tx_msg.get_data(), seq_num, channel)
    return tx_handler.get_frags(seq_num)


def send_pkts(sock, pkts):
    """Send packets over a given UDP socket"""
    for pkt in pkts:
        sock.send(pkt.pack())


def setUpModule():
    """Create a test gpg directory with a keypair"""
    name = "Test"
    email = "test@test.com"
    comment = "comment"
    gpg = Gpg(gpghome)
    gpg.create_keys(name, email, comment, gpgpassphrase)


def tearDownModule():
    shutil.rmtree(gpghome, ignore_errors=True)


class TestApiListener(TestCase):
    def setUp(self):
        # Gpg
        self.gpg = Gpg(gpghome)
        self.gpg.set_passphrase(gpgpassphrase)

        # Listener parameters
        self.download_dir = "/tmp/test-download-dir"
        self.sock_addr = "239.0.0.254:4433"
        # NOTE: sock_addr does not use the default multicast IP (239.0.0.2) to
        # avoid conflicts with production apps
        self.channel = ApiChannel.USER.value

        # Tx socket
        self.net_if = "lo"
        self.sock = sock = UdpSock(self.sock_addr, self.net_if, mcast_rx=False)
        sock.set_mcast_tx_opts(ttl=1, dscp=0)

        # Listener loop in test mode (recv_once=True, with a reception queue)
        self.rx_queue = queue.Queue()
        self.listen_loop = ApiListener(recv_once=True,
                                       recv_queue=self.rx_queue)

    def tearDown(self):
        shutil.rmtree(self.download_dir, ignore_errors=True)

    def loopback_test(self,
                      filename=None,
                      channel=None,
                      plaintext=True,
                      raw=False,
                      no_save=False,
                      exec_cmd=None,
                      gossip_opts=None,
                      check_download=True):
        """Send an API message through the loopback interface and receive it

        Receive the message through the API listener loop.

        """
        # Tx message and the corresponding packets
        if (filename is None):
            filename = rnd_string(10).decode()
        tx_data = rnd_string()
        tx_msg = msg.generate(tx_data,
                              gpg=self.gpg,
                              filename=filename,
                              plaintext=plaintext,
                              encapsulate=(not raw))
        pkts = gen_pkts(tx_msg, self.channel)

        # Listener loop configuration
        channel = self.channel if channel is None else channel
        args = (self.gpg, self.download_dir, self.sock_addr, self.net_if,
                channel, plaintext, raw)
        kwargs = {
            'no_save': no_save,
            'exec_cmd': exec_cmd,
            'gossip_opts': gossip_opts
        }

        # Run the listener loop on a thread
        t = Thread(target=self.listen_loop.run,
                   daemon=True,
                   args=args,
                   kwargs=kwargs)
        t.start()
        time.sleep(0.2)  # wait for the loop initialization

        # Send the packets through the loopback interface
        send_pkts(self.sock, pkts)

        # The listener exits after successfully receiving a single message
        t.join(timeout=1)
        self.assertFalse(t.is_alive())

        # Confirm the message was decoded correctly
        rx_data = self.rx_queue.get()
        self.rx_queue.task_done()
        self.assertEqual(tx_data, rx_data)

        # Check download
        #
        # NOTE: in raw mode (sending and saving raw messages), the Rx end
        # defines a file name automatically (based on a timestamp). At this
        # level, we can't obtain this filename. Hence, check downloads only if
        # testing an encapsulated (i.e., non-raw) message.
        if ((not raw) and check_download):
            download_path = os.path.join(self.download_dir, tx_msg.filename)
            if (no_save):
                self.assertFalse(os.path.exists(download_path))
            else:
                self.assertTrue(os.path.exists(download_path))

    def test_raw_plaintext_msg(self):
        self.loopback_test(plaintext=True, raw=True)

    def test_encapsulated_plaintext_msg(self):
        self.loopback_test(plaintext=True, raw=False)

    def test_raw_encrypted_msg(self):
        self.loopback_test(plaintext=False, raw=True)

    def test_encapsulated_encrypted_msg(self):
        self.loopback_test(plaintext=False, raw=False)

    def test_no_save(self):
        """Test listener loop configured not to save downloaded messages"""
        self.loopback_test(no_save=True)

    def test_exec_cmd(self):
        """Test execution of an mv command on the downloaded file"""
        dest = os.path.join(self.download_dir, "moved_file")
        cmd = 'mv {{}} {}'.format(dest)
        # Run test but don't check the download, given that exec_cmd will move
        # the downloaded file to another path.
        self.loopback_test(exec_cmd=cmd, check_download=False)
        self.assertTrue(os.path.exists(dest))

    @mock.patch('subprocess.run')
    def test_gossip(self, mock_subproc_run):
        """Test Lightning gossip reception"""
        filename = 'snapshot.gsp'
        gossip_opts = {'cli': 'historian-cli', 'dest': None}
        self.loopback_test(filename=filename, gossip_opts=gossip_opts)
        expected_cmd = [
            'historian-cli', 'snapshot', 'load',
            os.path.join(self.download_dir, filename)
        ]
        self.assertTrue(mock_subproc_run.called_with(expected_cmd))

    @mock.patch('subprocess.run')
    def test_gossip_with_dest(self, mock_subproc_run):
        """Test Lightning gossip reception with a specified destination"""
        filename = 'snapshot.gsp'
        dest = '127.0.0.1'
        gossip_opts = {'cli': 'historian-cli', 'dest': dest}
        self.loopback_test(filename=filename, gossip_opts=gossip_opts)
        expected_cmd = [
            'historian-cli', 'snapshot', 'load',
            os.path.join(self.download_dir, filename), dest
        ]
        self.assertTrue(mock_subproc_run.called_with(expected_cmd))
