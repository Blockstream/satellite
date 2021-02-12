import logging
import queue
import shlex
import subprocess

from . import net
from . import msg as api_msg
from .order import ApiOrder
from .pkt import BlocksatPkt, BlocksatPktHandler, ApiChannel

logger = logging.getLogger(__name__)


class ApiListener():
    """Infinite loop for listening to API messages"""
    def __init__(self, recv_once=False, recv_queue=None):
        """Constructor

        Args:
            recv_once : Receive a single message and stop
            recv_queue : Queue to mirror (store) the saved/serialized messages

        Note:
            The constructor options are useful for testing but are not
            necessary in production code.

        """
        self.enabled = True
        self.recv_once = recv_once
        assert (recv_queue is None or isinstance(recv_queue, queue.Queue))
        self.recv_queue = recv_queue

    def stop(self):
        logger.debug("Stopping API listener")
        self.enabled = False

    def run(self,
            gpg,
            download_dir,
            sock_addr,
            interface,
            channel,
            plaintext,
            save_raw,
            sender=None,
            stdout=False,
            no_save=False,
            echo=False,
            exec_cmd=None,
            gossip_opts=None,
            server_addr=None,
            tls_cert=None,
            tls_key=None,
            region=None):
        """Run loop

        Args:
            gpg          : Gnupg object
            download_dir : Directory where downloaded messages are saved
            sock_addr    : Multicast socket address to listen to
            interface    : Network interface to listen to
            channel      : Satellite API channel to listen to
            plaintext    : Receive messages in plaintext mode
            save_raw     : Save the raw message content without decapsulation
            sender       : Sender's GPG fingerprint for filtering of messages
            stdout       : Print messages to stdout instead of saving them
            no_save      : Don't save downloaded messages
            echo         : Echo text messages to stdout on reception
            exec_cmd     : Arbitrary shell command to run for each download
            gossip_opts  : Options for reception of Lightning gossip snapshots
            server_addr  : API server address for Rx confirmations
            tls_cert     : TLS client cert to authenticate on Rx confirmations
            tls_key      : TLS client key to authenticate on Rx confirmations
            region       : Satellite region to inform on Rx confirmations

        """
        logger.debug("Starting API listener")

        # Open UDP socket
        sock = net.UdpSock(sock_addr, interface)

        # Handler to collect groups of Blocksat packets that form an API
        # message
        pkt_handler = BlocksatPktHandler()

        # Set of decoded messages (to avoid repeated decoding)
        decoded_msgs = set()

        logger.info("Waiting for data...")
        while self.enabled:
            try:
                udp_payload, addr = sock.recv()
            except KeyboardInterrupt:
                break

            # Cast payload to BlocksatPkt object
            pkt = BlocksatPkt()
            pkt.unpack(udp_payload)

            # Filter API channel
            if (channel != ApiChannel.ALL.value and pkt.chan_num != channel):
                logger.debug("Packet discarded (channel {:d})".format(
                    pkt.chan_num))
                continue

            # Feed new packet into the packet handler
            all_frags_received = pkt_handler.append(pkt)

            # Decode each message only once
            seq_num = pkt.seq_num
            chan_seq_num = "{}-{}".format(pkt.chan_num, seq_num)
            if (chan_seq_num in decoded_msgs):
                logger.debug("Message {} from channel {} has already been "
                             "decoded".format(seq_num, pkt.chan_num))
                continue

            # Assume that the incoming message has forward error correction
            # (FEC) encoding. With FEC, the message may become decodable before
            # receiving all fragments (BlocksatPkts). For every packet, check
            # if the FEC data is decodable already and proceed with the
            # processing in the positive case. If the message is not actually
            # FEC-encoded, it will never assert the "fec_decodable" flag. In
            # this case, proceed with the processing only when all fragments
            # are received.
            msg = api_msg.ApiMsg(pkt_handler.concat(seq_num, force=True),
                                 msg_format="fec_encoded")
            fec_decodable = msg.is_fec_decodable()
            if (not fec_decodable and not all_frags_received):
                continue

            # API message is ready to be decoded
            if (channel == ApiChannel.ALL.value):
                logger.info("-------- API message {:d} (channel {:d})".format(
                    seq_num, pkt.chan_num))
            else:
                logger.info("-------- API message {:d}".format(seq_num))
            logger.debug("Message source: {}:{}".format(addr[0], addr[1]))
            logger.info("Fragments: {:d}".format(
                pkt_handler.get_n_frags(seq_num)))

            # Send confirmation of reception to API server
            order = ApiOrder(server_addr,
                             seq_num=seq_num,
                             tls_cert=tls_cert,
                             tls_key=tls_key)
            order.confirm_rx(region)

            # Decode the data from the available FEC chunks or from the
            # complete collection of Blocksat Packets
            if (fec_decodable):
                msg.fec_decode()
                data = msg.data['original']
            else:
                data = pkt_handler.concat(seq_num)

            # Mark as decoded
            decoded_msgs.add(chan_seq_num)

            # Delete message from the packet handler
            del pkt_handler.frag_map[seq_num]

            # Clean up old (timed-out) messages from the packet handler
            pkt_handler.clean()

            if (len(data) <= 0):
                logger.warning("Empty message")
                continue

            # The FEC-decoded data could be encrypted, signed, and/or
            # encapsulated. Decode it and obtain the original data.
            msg = api_msg.decode(data,
                                 plaintext=plaintext,
                                 decapsulate=(not save_raw),
                                 sender=sender,
                                 gpg=gpg)
            if (msg is None):
                continue

            # Finalize the processing of the decoded message
            if (stdout):
                msg.serialize()
            elif (not no_save):
                download_path = msg.save(download_dir)

            if (self.recv_queue is not None):
                self.recv_queue.put(msg.get_data(target='original'))

            if (echo):
                # Not all messages can be decoded in UTF-8 (binary files
                # cannot). Also, messages that were not sent in plaintext and
                # raw (non-encapsulated) format. Echo the results only when the
                # UTF-8 decoding works.
                try:
                    logger.info("Message:\n\n {} \n".format(
                        msg.data['original'].decode()))
                except UnicodeDecodeError:
                    logger.debug("Message not decodable in UFT-8")
            else:
                logger.debug("Message: {}".format(msg.data['original']))

            if (exec_cmd):
                cmd = shlex.split(
                    exec_cmd.replace("{}", shlex.quote(download_path)))
                logger.debug("Exec:\n> {}".format(" ".join(cmd)))
                subprocess.run(cmd)

            if (gossip_opts is not None):
                cmd = [
                    gossip_opts['cli'], 'snapshot', 'load',
                    shlex.quote(download_path)
                ]
                if (gossip_opts['dest'] is not None):
                    cmd.append(gossip_opts['dest'])

                logger.debug("Exec:\n> {}".format(" ".join(cmd)))
                subprocess.run(cmd)

            if (self.recv_once):
                self.stop()
