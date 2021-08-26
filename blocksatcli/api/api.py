"""Blocksat API"""
import logging
import os
import shlex
import subprocess
import textwrap
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, \
    ArgumentTypeError
from shutil import which

import qrcode

from . import bidding, net
from . import msg as api_msg
from .. import config as blocksatcli_config
from .. import defs
from .demorx import DemoRx
from .gpg import Gpg, config_keyring
from .listen import ApiListener
from .order import ApiOrder
from .pkt import calc_ota_msg_len, ApiChannel

logger = logging.getLogger(__name__)
server_map = {
    'main': "https://api.blockstream.space",
    'test': "https://api.blockstream.space/testnet",
    'gossip': "https://api.blockstream.space/gossip",
    'btc-src': "https://api.blockstream.space/btc-src"
}


def _get_server_addr(net, server):
    if (net is None):
        return server
    else:
        return server_map[net]


def _warn_common_overrides(args):
    """Warn options overridden by arguments --gossip and --btc-src"""
    if (not (args.gossip or args.btc_src)):
        return

    opt = "--gossip" if args.gossip else "--btc-src"

    if (args.channel != ApiChannel.USER.value):
        logger.warning("Option {} overrides --channel".format(opt))

    if (args.server != server_map['main'] or args.net is not None):
        logger.warning("Option {} overrides --net and --server".format(opt))


def config(args):
    """API config command"""
    gnupghome = os.path.join(args.cfg_dir, args.gnupghome)
    gpg = Gpg(gnupghome, verbose=args.verbose, interactive=True)
    config_keyring(gpg, log_if_configured=True)


def send(args):
    """Send a message over satellite"""
    gnupghome = os.path.join(args.cfg_dir, args.gnupghome)
    server_addr = _get_server_addr(args.net, args.server)

    # Instantiate the GPG wrapper object if running with encryption or signing
    if (not args.plaintext or args.sign):
        gpg = Gpg(gnupghome, interactive=True)
        config_keyring(gpg)
    else:
        gpg = None

    # A passphrase is required if signing
    if (args.sign and (not args.no_password)):
        gpg.prompt_passphrase('Password to private key used for message '
                              'signing: ')

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

    # Put file or text within an API message
    msg = api_msg.generate(data,
                           filename=basename,
                           plaintext=args.plaintext,
                           encapsulate=(not args.send_raw),
                           sign=args.sign,
                           fec=args.fec,
                           gpg=gpg,
                           recipient=args.recipient,
                           trust=args.trust,
                           sign_key=args.sign_key,
                           fec_overhead=args.fec_overhead)

    # Actual number of bytes used for satellite transmission
    tx_len = calc_ota_msg_len(msg.get_length())
    logger.info("Satellite transmission will use %d bytes" % (tx_len))

    # Ask user for bid or take it from argument
    bid = args.bid if args.bid else bidding.ask_bid(tx_len)

    # API transmission order
    order = ApiOrder(server_addr, tls_cert=args.tls_cert, tls_key=args.tls_key)
    res = order.send(msg.get_data(), bid)
    print()

    # The API servers (except the gossip and btc-src instances) should return a
    # Lightning invoice for the transmission order
    if (server_addr != server_map['gossip']
            and server_addr != server_map['btc-src']):
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
        target_state = ['sent', 'cancelled']
        order.wait_state(target_state)
    except KeyboardInterrupt:
        pass


def listen(args):
    """Listen to API messages received over satellite"""
    gnupghome = os.path.join(args.cfg_dir, args.gnupghome)
    download_dir = os.path.join(args.cfg_dir, "api", "downloads")

    # Override some options based on the mutual exclusive --gossip and
    # --btc-src arguments, if present
    if (args.gossip):
        channel = ApiChannel.GOSSIP.value
        server_addr = server_map['gossip']
        args.plaintext = True
    elif (args.btc_src):
        channel = ApiChannel.BTC_SRC.value
        server_addr = server_map['btc-src']
        args.plaintext = True
    else:
        channel = args.channel
        server_addr = _get_server_addr(args.net, args.server)

    historian_cli = os.path.join(args.historian_path, 'historian-cli') \
        if (args.historian_path) else 'historian-cli'

    # Argument validation and special cases
    if (args.gossip):
        if (which(historian_cli) is None):
            logger.error("Option --gossip requires the historian-cli "
                         "application but could not find it")
            logger.info("Use option --historian-path to specify the path to "
                        "historian-cli")
            raise ValueError("Could not find the historian-cli application")

        if (args.stdout):
            raise ValueError("Argument --gossip is not allowed with argument "
                             "--stdout")
        elif (args.no_save):
            raise ValueError("Argument --gossip is not allowed with argument "
                             "--no-save")

        gossip_opts = {
            'cli': historian_cli,
            'dest': args.historian_destination
        }
    else:
        gossip_opts = None

    _warn_common_overrides(args)  # warn args overridden by --gossip/--btc-src

    if (args.exec):
        # Do not support the option in plaintext mode
        if (args.plaintext):
            raise ValueError("Option --exec is not allowed in plaintext mode")

        # Require either --sender or --insecure
        if (args.sender is None and not args.insecure):
            raise ValueError("Option --exec requires a specified --sender")

        # Warn about unsafe commands
        base_exec_cmd = shlex.split(args.exec)[0]
        unsafe_cmds = ["/bin/bash", "bash", "/bin/sh", "sh", "rm"]
        if (base_exec_cmd in unsafe_cmds):
            logger.warning("Running {} on --exec is considered unsafe".format(
                base_exec_cmd))

    # GPG wrapper object
    if (not args.plaintext or args.sender):
        gpg = Gpg(gnupghome, interactive=True)
        config_keyring(gpg)
    else:
        gpg = None

    # Define the interface used to listen for messages
    if (args.interface):
        interface = args.interface
    elif (args.demo):
        interface = "lo"
    else:
        # Infer the interface based on the user's setup
        user_info = blocksatcli_config.read_cfg_file(args.cfg, args.cfg_dir)
        interface = blocksatcli_config.get_net_if(user_info)
    logger.info("Listening on interface: {}".format(interface))
    logger.info("Downloads will be saved at: {}".format(download_dir))

    # A passphrase is required for decryption (but not for signature
    # verification)
    if (not args.plaintext and not args.no_password):
        gpg.prompt_passphrase('GPG keyring password for decryption: ')

    # Listen continuously
    listen_loop = ApiListener()
    listen_loop.run(gpg,
                    download_dir,
                    args.sock_addr,
                    interface,
                    channel,
                    args.plaintext,
                    args.save_raw,
                    sender=args.sender,
                    stdout=args.stdout,
                    no_save=args.no_save,
                    echo=args.echo,
                    exec_cmd=args.exec,
                    gossip_opts=gossip_opts,
                    server_addr=server_addr,
                    tls_cert=args.tls_cert,
                    tls_key=args.tls_key,
                    region=args.region)


def bump(args):
    """Bump the bid of an API order"""
    server_addr = _get_server_addr(args.net, args.server)

    # Fetch the ApiOrder
    order = ApiOrder(server_addr, tls_cert=args.tls_cert, tls_key=args.tls_key)
    order.get(args.uuid, args.auth_token)

    # Bump bid
    try:
        res = order.bump(args.bid)
    except ValueError as e:
        logger.error(e)
        return

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

    # Override some options based on the mutual exclusive --gossip and
    # --btc-src arguments, if present
    if (args.gossip):
        server_addr = server_map['gossip']
        channel = ApiChannel.GOSSIP.value
    elif (args.btc_src):
        server_addr = server_map['btc-src']
        channel = ApiChannel.BTC_SRC.value
    else:
        server_addr = _get_server_addr(args.net, args.server)
        channel = args.channel

    # Argument validation and special cases
    _warn_common_overrides(args)  # warn args overridden by --gossip/--btc-src

    # Open one socket for each interface:
    socks = list()
    for interface in args.interface:
        sock = net.UdpSock(args.dest, interface, mcast_rx=False)
        sock.set_mcast_tx_opts(args.ttl, args.dscp)
        socks.append(sock)

    rx = DemoRx(server_addr, socks, args.bitrate, args.event, channel,
                args.regions, args.tls_cert, args.tls_key)
    rx.run()


def subparser(subparsers):
    """Subparser for usb command"""
    def channel_number(value):
        ivalue = int(value)
        if ivalue < 0 or ivalue > 255:
            raise ArgumentTypeError(
                "Invalid API channel number {}. "
                "Choose number within [0, 256)".format(value))
        return ivalue

    p = subparsers.add_parser('api',
                              description="Blockstream Satellite API",
                              help='Blockstream Satellite API',
                              formatter_class=ArgumentDefaultsHelpFormatter)

    # Common API app arguments
    p.add_argument(
        '-g',
        '--gnupghome',
        default=".gnupg",
        help="GnuPG home directory, by default created inside the config "
        "directory specified via --cfg-dir option")
    server_addr = p.add_mutually_exclusive_group()
    server_addr.add_argument(
        '--net',
        choices=server_map.keys(),
        default=None,
        help="Choose between the Mainnet API server (main), the Testnet API \
        server (test), the receive-only server used for Lightning gossip \
        messages (gossip), or the receive-only server used for messages \
        carrying the Bitcoin source code (btc-src)")
    server_addr.add_argument('-s',
                             '--server',
                             default=server_map['main'],
                             help="Satellite API server address")
    p.add_argument(
        '--tls-cert',
        default=None,
        help="Certificate for client-side authentication with the API server")
    p.add_argument(
        '--tls-key',
        default=None,
        help="Private key for client-side authentication with the API server")
    p.set_defaults(func=print_help)

    subsubparsers = p.add_subparsers(title='subcommands',
                                     help='Target sub-command')

    # Config
    p1 = subsubparsers.add_parser(
        'config',
        aliases=['cfg'],
        description="Configure GPG keys",
        help="Configure GPG keys",
        formatter_class=ArgumentDefaultsHelpFormatter)
    p1.add_argument('-v',
                    '--verbose',
                    action='store_true',
                    default=False,
                    help="Verbose mode")
    p1.set_defaults(func=config)

    # Sender
    p2 = subsubparsers.add_parser(
        'send',
        aliases=['tx'],
        description=textwrap.dedent('''\

        Sends a file or a text message to the Satellite API for transmission
        via Blockstream Satellite. By default, runs the following sequence: 1)
        encapsulates the message into a structure containing the data checksum
        and the file name; 2) encrypts the entire structure using GnuPG; and 3)
        posts to the encrypted object to the API server for transmission.

        '''),
        help="Broadcast message through the Satellite API",
        formatter_class=ArgumentDefaultsHelpFormatter)
    msg_group = p2.add_mutually_exclusive_group()
    msg_group.add_argument('-f', '--file', help='File to send through the API')
    msg_group.add_argument('-m',
                           '--message',
                           help='Text message to send through the API')
    p2.add_argument('--bid',
                    default=None,
                    type=int,
                    help="Bid (in millisatoshis) for the message transmission")
    p2.add_argument(
        '-r',
        '--recipient',
        default=None,
        help="Public key fingerprint of the desired recipient. If not "
        "defined, the recipient will be automatically set to the first "
        "public key in the keyring")
    p2.add_argument(
        '--trust',
        default=False,
        action="store_true",
        help="Assume that the recipient\'s public key is fully trusted")
    p2.add_argument('--sign',
                    default=False,
                    action="store_true",
                    help="Sign message in addition to encrypting it")
    p2.add_argument(
        '--sign-key',
        default=None,
        help="Fingerprint of the private key to be used when signing the "
        "message. If not set, the default key from the keyring will be used")
    p2.add_argument(
        '--send-raw',
        default=False,
        action="store_true",
        help="Send the raw file or text message, i.e., without the data "
        "structure that includes the file name and checksum")
    p2.add_argument(
        '--plaintext',
        default=False,
        action="store_true",
        help="Send data in plaintext format, i.e., without encryption")
    p2.add_argument(
        '--fec',
        default=False,
        action="store_true",
        help="Send data with forward error correction (FEC) encoding")
    p2.add_argument(
        '--fec-overhead',
        default=0.1,
        type=float,
        help="Target ratio between the overhead FEC chunks and the original "
        "chunks. For example, 0.1 implies one overhead (redundant) chunk for "
        "every 10 original chunks")
    p2.add_argument(
        '--no-password',
        default=False,
        action="store_true",
        help="Whether to access the GPG keyring without a password")
    p2.add_argument(
        '--invoice-exec',
        help="Execute command with the Lightning invoice. Replaces the string "
        "\'{}\' with the Lightning bolt11 invoice string.")
    p2.add_argument(
        '--no-wait',
        default=False,
        action="store_true",
        help="Return immediately after submitting an API transmission order. "
        "Do not wait for the payment and transmission confirmations")
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
        formatter_class=ArgumentDefaultsHelpFormatter)
    p3.add_argument(
        '--sock-addr',
        default=defs.api_dst_addr,
        help="Multicast UDP address (ip:port) used to listen for API data")
    intf_arg = p3.add_mutually_exclusive_group()
    intf_arg.add_argument('-i',
                          '--interface',
                          default=None,
                          help="Network interface that receives API data")
    intf_arg.add_argument(
        '-d',
        '--demo',
        action="store_true",
        default=False,
        help="Use the same interface as the demo-rx tool, i.e., the loopback "
        "interface")
    p3.add_argument(
        '-c',
        '--channel',
        default=ApiChannel.USER.value,
        type=channel_number,
        help="Listen to a specific API transmission channel. If set to 0, "
        "listen to all channels. By default, listen to user transmissions, "
        "which are sent on channel 1")
    p3.add_argument(
        '--save-raw',
        default=False,
        action="store_true",
        help="Save the raw decrypted data into the download directory while "
        "ignoring the existence of a data encapsulation structure")
    p3.add_argument(
        '--plaintext',
        default=False,
        action="store_true",
        help="Do not try to decrypt the incoming messages. Instead, assume "
        "that the incoming messages are in plaintext format and save them as "
        "individual files named with timestamps in the download directory. "
        "Note this option saves all incoming messages, including those "
        "broadcast by other users. In contrast, the default mode (without "
        "this option) only saves the messages that are successfully decrypted."
    )
    p3.add_argument(
        '--sender',
        default=None,
        help="Public key fingerprint of a target sender used to filter the "
        "incoming messages. When specified, the application processes only "
        "the messages that are digitally signed by the selected sender, "
        "including clearsigned messages.")
    p3.add_argument('--no-password',
                    default=False,
                    action="store_true",
                    help="Set to access GPG keyring without a password")
    p3.add_argument(
        '--echo',
        default=False,
        action='store_true',
        help="Print the contents of all incoming text messages to the "
        "console, as long as these messages are decodable in UTF-8")
    stdout_exec_arg_group = p3.add_mutually_exclusive_group()
    stdout_exec_arg_group.add_argument(
        '--stdout',
        default=False,
        action='store_true',
        help="Serialize the received data to stdout instead of saving on a "
        "file")
    stdout_exec_arg_group.add_argument(
        '--no-save',
        default=False,
        action='store_true',
        help="Do not save the files decoded from the received API messages")
    stdout_exec_arg_group.add_argument(
        '--exec',
        help="Execute arbitrary shell command for each downloaded file. "
        "Use the magic string \'{}\' to represent the file path within the "
        "command. For instance, run \"--exec \'cat {}\'\" to print every "
        "incoming file to stdout. For security, this option must be used in "
        "conjunction with the --sender option to limit the execution of the "
        "specified command to digitally signed messages from a specified "
        "sender only. See option --insecure for an alternative.")
    p3.add_argument(
        '--insecure',
        default=False,
        action="store_true",
        help="Run the --exec option while receiving messages from any sender. "
        "In this case, any successfully decrypted message (i.e., any message) "
        "encrypted using your public key will trigger the --exec command, "
        "which is considered insecure. Use at your own risk and avoid unsafe "
        "commands.")
    btc_src_gossip_arg_group1 = p3.add_mutually_exclusive_group()
    btc_src_gossip_arg_group1.add_argument(
        '--gossip',
        default=False,
        action="store_true",
        help="Configure the application to receive Lightning gossip snapshots "
        "and load them using the historian-cli application. This argument "
        "overrides the following options: 1) --plaintext (enabled); 2) "
        "--channel (set to {}); and 3) --server/--net (set to {})".format(
            ApiChannel.GOSSIP.value, server_map['gossip']))
    btc_src_gossip_arg_group1.add_argument(
        '--btc-src',
        default=False,
        action="store_true",
        help="Configure the application to receive API messages carrying the "
        "Bitcoin Satellite and Bitcoin Core source codes. This argument "
        "overrides the following options: 1) --plaintext (enabled); 2) "
        "--channel (set to {}); and 3) --server/--net (set to {})".format(
            ApiChannel.BTC_SRC.value, server_map['btc-src']))
    p3.add_argument(
        '--historian-path',
        default=None,
        help="Path to the historian-cli application. If not set, look for "
        "historian-cli globally")
    p3.add_argument(
        '--historian-destination',
        default=None,
        help="Destination for gossip snapshots, formatted as "
        "[nodeid]@[ipaddress]:[port]. If not set, historian-cli attempts to "
        "discover the destination automatically. This parameter is provided "
        "as a positional argument of command \'historian-cli snapshot load\', "
        "which is called for each downloaded file in gossip mode (i.e., when "
        "argument --gossip is set).")
    p3.add_argument('-r',
                    '--region',
                    choices=range(0, 6),
                    type=int,
                    help="Coverage region for Rx confirmations")
    p3.set_defaults(func=listen)

    # Bump
    p4 = subsubparsers.add_parser(
        'bump',
        description="Bump bid of an API message order",
        help="Bump bid of an API message order",
        formatter_class=ArgumentDefaultsHelpFormatter)
    p4.add_argument(
        '--bid',
        default=None,
        type=int,
        help="New bid (in millisatoshis) for the message transmission")
    p4.add_argument('-u',
                    '--uuid',
                    default=None,
                    help="API order's universally unique identifier (UUID)")
    p4.add_argument('-a',
                    '--auth-token',
                    default=None,
                    help="API order's authentication token")
    p4.set_defaults(func=bump)

    # Delete
    p5 = subsubparsers.add_parser(
        'delete',
        aliases=['del'],
        description="Delete API message order",
        help="Delete API message order",
        formatter_class=ArgumentDefaultsHelpFormatter)
    p5.add_argument('-u',
                    '--uuid',
                    default=None,
                    help="API order's universally unique identifier (UUID)")
    p5.add_argument('-a',
                    '--auth-token',
                    default=None,
                    help="API order's authentication token")
    p5.set_defaults(func=delete)

    # Demo receiver
    p6 = subsubparsers.add_parser(
        'demo-rx',
        description=textwrap.dedent('''\

        Demo Blockstream Satellite Receiver, used to test the API data listener
        application without an actual satellite receiver. The satellite
        receiver receives UDP packets sent over satellite and relays these
        packets to a host PC, where the API data listener application runs.
        This application, in turn, produces equivalent UDP packets, just like
        the satellite receiver would. The difference is that it fetches the
        data through the internet, rather than receiving via satellite.

        '''),
        help='Run demo satellite receiver',
        formatter_class=ArgumentDefaultsHelpFormatter)
    p6.add_argument(
        '-d',
        '--dest',
        default=defs.api_dst_addr,
        help="Destination address (ip:port) to which API data will be sent")
    p6.add_argument(
        '-i',
        '--interface',
        nargs="+",
        help="Network interface(s) over which to send the API data. If \
        multiple interfaces are provided, the same packets are sent over all \
        interfaces.",
        default=["lo"])
    p6.add_argument('-c',
                    '--channel',
                    default=ApiChannel.USER.value,
                    type=channel_number,
                    help="Target API transmission channel")
    p6.add_argument('-r',
                    '--regions',
                    nargs="+",
                    choices=range(0, 6),
                    type=int,
                    help="Coverage region for Tx confirmations")
    p6.add_argument('--ttl',
                    type=int,
                    default=1,
                    help="Time-to-live to set on multicast packets")
    p6.add_argument(
        '--dscp',
        type=int,
        default=0,
        help="Differentiated services code point (DSCP) to set on the output \
        multicast IP packets")
    p6.add_argument(
        '--bitrate',
        type=float,
        default=1000,
        help="Maximum bit rate in kbps of the output packet stream")
    p6.add_argument('-e',
                    '--event',
                    choices=["transmitting", "sent"],
                    default="sent",
                    help='SSE event that should trigger packet transmissions')
    btc_src_gossip_arg_group2 = p6.add_mutually_exclusive_group()
    btc_src_gossip_arg_group2.add_argument(
        '--gossip',
        default=False,
        action="store_true",
        help="Configure the application to fetch and relay Lightning gossip "
        "messages. This argument overrides option --channel (set to {}) and "
        "options --server/--net (set to {})".format(ApiChannel.GOSSIP.value,
                                                    server_map['gossip']))
    btc_src_gossip_arg_group2.add_argument(
        '--btc-src',
        default=False,
        action="store_true",
        help="Configure the application to fetch and relay messages carrying "
        "the Bitcoin Satellite and Bitcoin Core source codes. This argument "
        "overrides option --channel (set to {}) and options --server/--net "
        "(set to {})".format(ApiChannel.BTC_SRC.value, server_map['btc-src']))
    p6.set_defaults(func=demo_rx)

    return p


def print_help(args):
    """Re-create argparse's help menu for the api command"""
    parser = ArgumentParser()
    subparsers = parser.add_subparsers(title='', help='')
    parser = subparser(subparsers)
    print(parser.format_help())
