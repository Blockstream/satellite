"""Blocksat API"""
import os, getpass, textwrap, logging, subprocess, shlex
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import qrcode
from .. import util, defs
from .. import config as blocksatcli_config
from .order import ApiOrder
from .msg import ApiMsg
from .pkt import BlocksatPkt, BlocksatPktHandler, calc_ota_msg_len
from .demorx import DemoRx
from . import bidding, net
from .gpg import Gpg


logger          = logging.getLogger(__name__)
blocksat_pubkey = '87D07253F69E4CD8629B0A21A94A007EC9D4458C'
server_map      = {
    'main'   : "https://api.blockstream.space",
    'test'   : "https://api.blockstream.space/testnet",
    'gossip' : "https://api.blockstream.space/gossip",
}


def _get_server_addr(net, server):
    if (net is None):
        return server
    else:
        return server_map[net]


def _is_gpg_keyring_set(gnupghome):
    if not os.path.exists(gnupghome):
        return False

    gpg = Gpg(gnupghome)

    return len(gpg.gpg.list_keys()) > 0


def config(args):
    """Generate GPG Keys"""
    gpghome = os.path.join(args.cfg_dir, args.gnupghome)

    logger.info("Generating a GPG keypair to encrypt and decrypt API messages")

    # Collect info for the new key
    name    = input("User name represented by the key: ")
    email   = input("E-mail address: ")
    comment = input("Comment to attach to the user ID: ")

    verbose = False if ('verbose' not in args) else args.verbose

    gpg = Gpg(gpghome, verbose, interactive=True)
    gpg.create_keys(name, email, comment)

    # Import Blockstream's public key
    key_server    = 'keys.openpgp.org'
    import_result = gpg.gpg.recv_keys(key_server, blocksat_pubkey)

    if (len(import_result.fingerprints) == 0):
        logger.warning("Failed to import key {}".format(blocksat_pubkey))
        return

    # Note: the order is important here. Add Blockstream's public key only after
    # adding the user's key. With that, the user's key becomes the first key,
    # which is used by default.
    logger.info("Imported key {} from {}".format(
        import_result.fingerprints[0], key_server
    ))

    gpg.gpg.trust_keys(blocksat_pubkey, 'TRUST_ULTIMATE')


def send(args):
    """Send a message over satellite"""
    gnupghome   = os.path.join(args.cfg_dir, args.gnupghome)
    server_addr = _get_server_addr(args.net, args.server)

    # Instantiate the GPG wrapper object if running with encryption
    if (not args.plaintext):
        if not _is_gpg_keyring_set(gnupghome):
            config(args)

        gpg = Gpg(gnupghome, interactive=True)

        if (args.sign and (not args.no_password)):
            gpg_password = getpass.getpass(prompt='Password to private key '
                                           'used for message signing: ')
            gpg.set_passphrase(gpg_password)

    # File or text message to send over satellite
    if (args.file is None):
        if (args.message is None):
            data = input("Type a message: ").encode()
            print()
        else:
            data = args.message.encode()
        basename = None
    else:
        basename = os.path.basename(args.file)
        with open(args.file, 'rb') as f:
            data = f.read()

    assert(len(data) > 0), \
        "Empty {}".format("file" if args.file else "message")

    msg = ApiMsg(data, filename=basename)

    # Pack data into structure (header + data), if enabled
    if (not args.send_raw):
        msg.encapsulate()

    # Encrypt, unless configured otherwise
    if (not args.plaintext):
        # Recipient public key. Use the first public key from keyring if
        # recipient is not defined.
        if (args.recipient is None):
            recipient = gpg.get_default_public_key()["fingerprint"]
            assert(recipient != blocksat_pubkey), \
                "Defaul public key is not the user's public key"
        else:
            # Make sure the key exists
            gpg.get_public_key(args.recipient)
            recipient = args.recipient

        # Digital signature. If configured to sign the message without a
        # specified key, use the default key.
        if (args.sign):
            if (args.sign_key):
                # Make sure the key exists
                gpg.get_priv_key(args.sign_key)
                sign_cfg = args.sign_key
            else:
                sign_cfg = gpg.get_default_priv_key()["fingerprint"]
        else:
            sign_cfg = False

        msg.encrypt(gpg, recipient, sign_cfg, args.trust)

    # Forward error correction encoding
    if (args.fec):
        msg.fec_encode(args.fec_overhead)

    # Actual number of bytes used for satellite transmission
    tx_len = calc_ota_msg_len(msg.get_length())
    logger.info("Satellite transmission will use %d bytes" %(tx_len))

    # Ask user for bid or take it from argument
    bid = args.bid if args.bid else bidding.ask_bid(tx_len)

    # API transmission order
    order = ApiOrder(server_addr, tls_cert=args.tls_cert, tls_key=args.tls_key)
    res   = order.send(msg.get_data(), bid)
    print()

    # The API servers (except the Gossip instance) return a Lightning invoice
    if (server_addr != server_map['gossip']):
        payreq = res["lightning_invoice"]["payreq"]

        # Print QR code
        try:
            qr = qrcode.QRCode()
            qr.add_data(payreq)
            qr.print_ascii()
        except UnicodeError:
            qr.print_tty()

        # Execute arbitrary command with the Lightning invoice
        if (args.invoice_exec):
            cmd = shlex.split(args.invoice_exec.replace("{}", payreq))
            logger.debug("Execute:\n> {}".format(" ".join(cmd)))
            subprocess.run(cmd)

    # Wait until the transmission completes (after the ground station confirms
    # reception). Stop if it is canceled.
    if (args.no_wait):
        return

    try:
        if (server_addr == server_map['main']):
            target_state = ['received', 'cancelled']
        else:
            target_state = ['sent', 'cancelled']
        order.wait_state(target_state)
    except KeyboardInterrupt:
        pass


def listen(args):
    """Listen to API messages received over satellite"""
    gnupghome    = os.path.join(args.cfg_dir, args.gnupghome)
    download_dir = os.path.join(args.cfg_dir, "api", "downloads")
    server_addr  = _get_server_addr(args.net, args.server)
    sock_addr    = defs.gossip_dst_addr if args.sock_addr == "gossip" \
                   else args.sock_addr

    # Argument validation
    if (args.exec):
        # Do not support the option in plaintext mode, except for the gossip
        # channel, where the `--exec` option is used in plaintext mode to load
        # the gossip snapshots using the historian-cli.
        if (args.plaintext and (sock_addr != defs.gossip_dst_addr)):
            raise ValueError("Option --exec is not allowed in plaintext mode")

        # Warn about unsafe commands
        base_exec_cmd = shlex.split(args.exec)[0]
        unsafe_cmds   = ["/bin/bash", "bash", "/bin/sh", "sh", "rm"]
        if (base_exec_cmd in unsafe_cmds):
            logger.warning("Running {} on --exec is considered unsafe".format(
                base_exec_cmd
            ))

    # Make sure that the GPG keyring is set if decrypting messages
    if (not args.plaintext and not _is_gpg_keyring_set(gnupghome)):
        config(args)

    # Define the interface used to listen for messages
    if (args.interface):
        interface = args.interface
    elif (args.demo):
        interface = "lo"
    else:
        # Infer the interface based on the user's setup
        user_info = blocksatcli_config.read_cfg_file(args.cfg, args.cfg_dir)
        if (user_info is None):
            return

        if (user_info['setup']['type'] == defs.sdr_setup_type):
            interface = "lo"
        elif (user_info['setup']['type'] == defs.linux_usb_setup_type):
            interface = "dvb0_0"
        elif (user_info['setup']['type'] == defs.standalone_setup_type):
            interface = user_info['setup']['netdev']
        else:
            raise ValueError("Unknown setup type")

    logger.info("Listening on interface: {}".format(interface))
    logger.info("Downloads will be saved at: {}".format(download_dir))

    # GPG wrapper object
    if (not args.plaintext):
        gpg = Gpg(gnupghome, interactive=True)

        if (not args.no_password):
            gpg_password = getpass.getpass(prompt='GPG keyring password for '
                                           'decryption: ')
            gpg.set_passphrase(gpg_password)

    # Open UDP socket
    sock = net.UdpSock(sock_addr, interface)

    # Handler to collect groups of Blocksat packets that form an API message
    pkt_handler = BlocksatPktHandler()

    # Set of decoded messages (to avoid repeated decoding)
    decoded_msgs = set()

    logger.info("Waiting for data...")
    while True:
        try:
            udp_payload, addr = sock.recv()
        except KeyboardInterrupt:
            break;

        # Cast payload to BlocksatPkt object
        pkt = BlocksatPkt()
        pkt.unpack(udp_payload)

        # Feed new packet into the packet handler
        all_frags_received = pkt_handler.append(pkt)

        # Decode each message only once
        seq_num = pkt.seq_num
        if (seq_num in decoded_msgs):
            logger.debug("Message {} has already been decoded".format(seq_num))
            continue

        # Assume that the incoming message has forward error correction (FEC)
        # encoding. With FEC, the message may become decodable before receiving
        # all fragments (BlocksatPkts). For every packet, check if the FEC data
        # is decodable already and proceed with the processing in the positive
        # case. If the message is not actually FEC-encoded, it will never assert
        # the "fec_decodable" flag. In this case, proceed with the processing
        # only when all fragments are received.
        msg = ApiMsg(pkt_handler.concat(seq_num, force=True),
                     msg_format="fec_encoded")
        fec_decodable = msg.is_fec_decodable()
        if (not fec_decodable and not all_frags_received):
            continue

        # API message is ready to be decoded
        logger.info("-------- API message {:d}".format(seq_num))
        logger.debug("Message source: {}:{}".format(addr[0], addr[1]))
        logger.info("Fragments: {:d}".format(pkt_handler.get_n_frags(seq_num)))

        # Send confirmation of reception to API server
        order = ApiOrder(server_addr, seq_num=seq_num, tls_cert=args.tls_cert,
                         tls_key=args.tls_key)
        order.confirm_rx(args.region)

        # Decode the data from the available FEC chunks or from the complete
        # collection of Blocksat Packets
        if (fec_decodable):
            msg.fec_decode()
            data = msg.data['original']
        else:
            data = pkt_handler.concat(seq_num)

        # Mark as decoded
        decoded_msgs.add(seq_num)

        # Delete message from the packet handler
        del pkt_handler.frag_map[seq_num]

        # Clean up old (timed-out) messages from the packet handler
        pkt_handler.clean()

        if (len(data) <= 0):
            logger.warning("Empty message")
            continue

        if (args.plaintext):
            if (args.save_raw):
                # Assume that the message is not encapsulated. This mode is
                # useful, e.g., for compatibility with transmissions triggered
                # from the browser at: https://blockstream.com/satellite-queue/.
                msg = ApiMsg(data, msg_format="original")
            else:
                # Encapsulated format, but no encryption
                msg = ApiMsg(data, msg_format="encapsulated")

                # Try to decapsulate it
                if (not msg.decapsulate()):
                    continue

            logger.info("Size: {:7d} bytes\tSaving in plaintext".format(
                msg.get_length()))
        else:
            # Cast data into ApiMsg object in encrypted form
            msg = ApiMsg(data, msg_format="encrypted")

            # Try to decrypt the data:
            if (not msg.decrypt(gpg)):
                continue

            # Try to decapsulate the application-layer structure if assuming it
            # is present (i.e., with "save-raw=False")
            if (not args.save_raw and not msg.decapsulate()):
                continue

        # Finalize the processing of the decoded message
        if (args.stdout):
            msg.serialize()
        elif (not args.no_save):
            download_path = msg.save(download_dir)

        if (args.echo):
            # Not all messages can be decoded in UTF-8 (binary files
            # cannot). Also, messages that were not sent in plaintext and raw
            # (non-encapsulated) format. Echo the results only when the UTF-8
            # decoding works.
            try:
                logger.info("Message:\n\n {} \n".format(
                    msg.data['original'].decode()))
            except UnicodeDecodeError:
                logger.debug("Message not decodable in UFT-8")
        else:
            logger.debug("Message: {}".format(msg.data['original']))

        if (args.exec):
            cmd = shlex.split(
                args.exec.replace("{}", shlex.quote(download_path))
            )
            logger.debug("Exec:\n> {}".format(" ".join(cmd)))
            subprocess.run(cmd)


def bump(args):
    """Bump the bid of an API order"""
    server_addr = _get_server_addr(args.net, args.server)

    # Fetch the ApiOrder
    order = ApiOrder(server_addr, tls_cert=args.tls_cert, tls_key=args.tls_key)
    order.get(args.uuid, args.auth_token)

    # Bump bid
    res = order.bump(args.bid)

    # Print QR code
    qr = qrcode.QRCode()
    qr.add_data(res["lightning_invoice"]["payreq"])
    qr.print_ascii()


def delete(args):
    """Cancel an API order"""
    server_addr = _get_server_addr(args.net, args.server)

    # Fetch the ApiOrder
    order = ApiOrder(server_addr, tls_cert=args.tls_cert, tls_key=args.tls_key)
    order.get(args.uuid, args.auth_token)

    # Delete it
    order.delete()


def demo_rx(args):
    """Demo satellite receiver"""
    server_addr = _get_server_addr(args.net, args.server)

    # Open one socket for each interface:
    socks = list()
    for interface in args.interface:
        sock = net.UdpSock(args.dest, interface, mcast_rx=False)
        sock.set_mcast_tx_opts(args.ttl, args.dscp)
        socks.append(sock)

    rx = DemoRx(server_addr, socks, args.bitrate, args.event, args.regions,
                args.tls_cert, args.tls_key)
    rx.run()


def subparser(subparsers):
    """Subparser for usb command"""
    p = subparsers.add_parser(
        'api',
        description="Blockstream Satellite API",
        help='Blockstream Satellite API',
        formatter_class=ArgumentDefaultsHelpFormatter
    )

    # Common API app arguments
    p.add_argument(
        '-g',
        '--gnupghome',
        default=".gnupg",
        help="GnuPG home directory, by default created inside the config "
        "directory specified via --cfg-dir option"
    )
    server_addr = p.add_mutually_exclusive_group()
    server_addr.add_argument(
        '--net',
        choices=['main', 'test', 'gossip'],
        default=None,
        help="Choose between the Mainnet Satellite API server (main), the \
        Testnet Satellite API server (test), or the receive-only server used \
        for Lightning gossip messages (gossip)"
    )
    server_addr.add_argument(
        '-s',
        '--server',
        default='https://api.blockstream.space',
        help="Satellite API server address"
    )
    p.add_argument(
        '--tls-cert',
        default=None,
        help="Certificate for client-side authentication with the API server"
    )
    p.add_argument(
        '--tls-key',
        default=None,
        help="Private key for client-side authentication with the API server"
    )
    p.set_defaults(func=print_help)

    subsubparsers = p.add_subparsers(
        title='subcommands',
        help='Target sub-command'
    )

    # Config
    p1 = subsubparsers.add_parser(
        'config',
        aliases=['cfg'],
        description="Configure GPG keys",
        help="Configure GPG keys",
        formatter_class=ArgumentDefaultsHelpFormatter
    )
    p1.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        default=False,
        help="Verbose mode"
    )
    p1.set_defaults(func=config)

    # Sender
    p2 = subsubparsers.add_parser(
        'send',
        aliases=['tx'],
        description=textwrap.dedent('''\

        Sends a file or a text message to the Satellite API for transmission via
        Blockstream Satellite. By default, runs the following sequence: 1)
        encapsulates the message into a structure containing the data checksum
        and the file name; 2) encrypts the entire structure using GnuPG; and 3)
        posts to the encrypted object to the API server for transmission.

        '''),
        help="Broadcast message through the Satellite API",
        formatter_class=ArgumentDefaultsHelpFormatter
    )
    msg_group = p2.add_mutually_exclusive_group()
    msg_group.add_argument(
        '-f',
        '--file',
        help='File to send through the API'
    )
    msg_group.add_argument(
        '-m',
        '--message',
        help='Text message to send through the API'
    )
    p2.add_argument(
        '--bid',
        default=None,
        type=int,
        help="Bid (in millisatoshis) for the message transmission"
    )
    p2.add_argument(
        '-r',
        '--recipient',
        default=None,
        help="Public key fingerprint of the desired recipient. If not defined, "
        "the recipient will be automatically set to the first public key in "
        "the keyring"
    )
    p2.add_argument(
        '--trust',
        default=False,
        action="store_true",
        help="Assume that the recipient\'s public key is fully trusted"
    )
    p2.add_argument(
        '--sign',
        default=False,
        action="store_true",
        help="Sign message in addition to encrypting it"
    )
    p2.add_argument(
        '--sign-key',
        default=None,
        help="Fingerprint of the private key to be used when signing the "
        "message. If not set, the default key from the keyring will be used"
    )
    p2.add_argument(
        '--send-raw',
        default=False,
        action="store_true",
        help="Send the raw file or text message, i.e., without the data "
        "structure that includes the file name and checksum"
    )
    p2.add_argument(
        '--plaintext',
        default=False,
        action="store_true",
        help="Send data in plaintext format, i.e., without encryption"
    )
    p2.add_argument(
        '--fec',
        default=False,
        action="store_true",
        help="Send data with forward error correction (FEC) encoding"
    )
    p2.add_argument(
        '--fec-overhead',
        default=0.1,
        type=float,
        help="Target ratio between the overhead FEC chunks and the original "
        "chunks. For example, 0.1 implies one overhead (redundant) chunk for "
        "every 10 original chunks"
    )
    p2.add_argument(
        '--no-password',
        default=False,
        action="store_true",
        help="Whether to access the GPG keyring without a password")
    p2.add_argument(
        '--invoice-exec',
        help="Execute command with the Lightning invoice. Replaces the string "
        "\'{}\' with the Lightning bolt11 invoice string."
    )
    p2.add_argument(
        '--no-wait',
        default=False,
        action="store_true",
        help="Return immediately after submitting an API transmission order. "
        "Do not wait for the payment, transmission, and reception confirmations"
    )
    p2.set_defaults(func=send)

    # Listen
    p3 = subsubparsers.add_parser(
        'listen',
        aliases=['rx'],
        description=textwrap.dedent('''\

        Receives data sent over the Blockstream Satellite network through the
        Satellite API. By default, assumes that the incoming messages are
        generated by the "send" command, which transmits encapsulated and
        encrypted messages. Thus, it first attempts to decrypt the data using a
        local GnuPG key. Then, on successful decryption, this application
        validates the integrity of the data. In the end, it saves the file into
        the download directory.

        '''),
        help="Listen to API messages",
        formatter_class=ArgumentDefaultsHelpFormatter
    )
    p3.add_argument(
        '--sock-addr',
        default=defs.api_dst_addr,
        help="Multicast UDP address (ip:port) used to listen for API data"
    )
    intf_arg = p3.add_mutually_exclusive_group()
    intf_arg.add_argument(
        '-i',
        '--interface',
        default=None,
        help="Network interface that receives API data"
    )
    intf_arg.add_argument(
        '-d',
        '--demo',
        action="store_true",
        default=False,
        help="Use the same interface as the demo-rx tool, i.e., the loopback "
        "interface"
    )
    p3.add_argument(
        '--save-raw',
        default=False,
        action="store_true",
        help="Save the raw decrypted data into the download directory while "
        "ignoring the existence of a data encapsulation structure"
    )
    p3.add_argument(
        '--plaintext',
        default=False,
        action="store_true",
        help="Do not try to decrypt the incoming messages. Instead, assume "
        "that the incoming messages are in plaintext format and save them as "
        "individual files named with timestamps in the download directory. "
        "Note this option saves all incoming messages, including those "
        "broadcast by other users. In contrast, the default mode (without this "
        "option) only saves the messages that are successfully decrypted."
    )
    p3.add_argument(
        '--no-password',
        default=False,
        action="store_true",
        help="Set to access GPG keyring without a password"
    )
    p3.add_argument(
        '--echo',
        default=False,
        action='store_true',
        help="Print the contents of all incoming text messages to the console, "
        "as long as these messages are decodable in UTF-8"
    )
    stdout_exec_arg = p3.add_mutually_exclusive_group()
    stdout_exec_arg.add_argument(
        '--stdout',
        default=False,
        action='store_true',
        help="Serialize the received data to stdout instead of saving on a file"
    )
    stdout_exec_arg.add_argument(
        '--no-save',
        default=False,
        action='store_true',
        help="Do not save the files decoded from the received API messages"
    )
    stdout_exec_arg.add_argument(
        '--exec',
        help="Execute command for each downloaded file. Replaces the string "
        "\'{}\' with the path to the downloaded file. Use at your own risk"
    )
    p3.add_argument(
        '-r',
        '--region',
        choices=range(0, 6),
        type=int,
        help="Coverage region for Rx confirmations"
    )
    p3.set_defaults(func=listen)

    # Bump
    p4 = subsubparsers.add_parser(
        'bump',
        description="Bump bid of an API message order",
        help="Bump bid of an API message order",
        formatter_class=ArgumentDefaultsHelpFormatter
    )
    p4.add_argument(
        '--bid',
        default=None,
        type=int,
        help="New bid (in millisatoshis) for the message transmission"
    )
    p4.add_argument(
        '--uuid',
        default=None,
        help="API order's universally unique identifier (UUID)"
    )
    p4.add_argument(
        '--auth-token',
        default=None,
        help="API order's authentication token"
    )
    p4.set_defaults(func=bump)

    # Delete
    p5 = subsubparsers.add_parser(
        'delete',
        aliases=['del'],
        description="Delete API message order",
        help="Delete API message order",
        formatter_class=ArgumentDefaultsHelpFormatter
    )
    p5.add_argument(
        '--uuid',
        default=None,
        help="API order's universally unique identifier (UUID)"
    )
    p5.add_argument(
        '--auth-token',
        default=None,
        help="API order's authentication token"
    )
    p5.set_defaults(func=delete)

    # Demo receiver
    p6 = subsubparsers.add_parser(
        'demo-rx',
        description=textwrap.dedent('''\

        Demo Blockstream Satellite Receiver, used to test the API data listener
        application without an actual satellite receiver. The satellite receiver
        receives UDP packets sent over satellite and relays these packets to a
        host PC, where the API data listener application runs. This application,
        in turn, produces equivalent UDP packets, just like the satellite
        receiver would. The difference is that it fetches the data through the
        internet, rather than receiving via satellite.

        '''),
        help='Run demo satellite receiver',
        formatter_class=ArgumentDefaultsHelpFormatter
    )
    p6.add_argument(
        '-d',
        '--dest',
        default=defs.api_dst_addr,
        help="Destination address (ip:port) to which API data will be sent"
    )
    p6.add_argument(
        '-i',
        '--interface',
        nargs="+",
        help="Network interface(s) over which to send the API data. If \
        multiple interfaces are provided, the same packets are sent over all \
        interfaces.",
        default=["lo"]
    )
    p6.add_argument(
        '-r',
        '--regions',
        nargs="+",
        choices=range(0, 6),
        type=int,
        help="Coverage region for Tx confirmations"
    )
    p6.add_argument(
        '--ttl',
        type=int,
        default=1,
        help="Time-to-live to set on multicast packets"
    )
    p6.add_argument(
        '--dscp',
        type=int,
        default=0,
        help="Differentiated services code point (DSCP) to set on the output \
        multicast IP packets"
    )
    p6.add_argument(
        '--bitrate',
        type=float,
        default=1000,
        help="Maximum bit rate in kbps of the output packet stream"
    )
    p6.add_argument(
        '-e',
        '--event',
        choices=["transmitting", "sent"],
        default="sent",
        help='SSE event that should trigger packet transmissions'
    )
    p6.set_defaults(func=demo_rx)

    return p


def print_help(args):
    """Re-create argparse's help menu for the api command"""
    parser     = ArgumentParser()
    subparsers = parser.add_subparsers(title='', help='')
    parser     = subparser(subparsers)
    print(parser.format_help())

