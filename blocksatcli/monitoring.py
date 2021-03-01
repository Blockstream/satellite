"""Monitor the satellite receiver"""
import sys, os, time, logging, math, requests, threading, json
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
from . import defs, config


logger = logging.getLogger(__name__)
sats   = [ x['alias'] for x in defs.satellites]


def get_report_opts(args):
    """Extract the parser fields needed to construct a Reporter object"""
    return {
        'cfg': args.cfg,
        'cfg_dir': args.cfg_dir,
        'dest_addr': args.report_dest,
        'hostname': args.report_hostname,
        'tls_cert': args.report_cert,
        'tls_key': args.report_key
    }


class Reporter():
    """Receiver Reporter

    Sends receiver metrics to a remote server.

    """
    def __init__(self, cfg, cfg_dir, dest_addr, hostname, tls_cert=None,
                 tls_key=None):
        """Reporter Constructor

        Args:
            cfg       : User configuration
            cfg_dir   : Configuration directory
            dest_addr : Remote server address
            hostname  : Hostname used to identify the reports
            tls_cert  : Optional client side certificate for TLS authentication
            tls_key   : Key associated with the client side certificate

        """
        info = config.read_cfg_file(cfg, cfg_dir)
        assert(info is not None)

        # Validate the satellite
        satellite = info['sat']['alias']
        assert(satellite is not None), "Reporting satellite undefined"
        assert(satellite in sats), "Invalid satellite"
        self.satellite = satellite

        # Destination address, hostname, and client side cert
        assert(dest_addr is not None), "Reporting destination address undefined"
        assert(hostname is not None), "Reporting hostname undefined"
        self.dest_addr = dest_addr
        self.hostname = hostname
        self.tls_cert = tls_cert
        self.tls_key  = tls_key

        logger.info("Reporting Rx status to {} "
                    "(hostname: {}, satellite: {})".format(
                        self.dest_addr,
                        self.hostname,
                        self.satellite))

    def send(self, metrics):
        """Save measurement on database

        Args:
            metrics : Dictionary with receiver metrics to send over the report
        """
        data = {
            "hostname"  : self.hostname,
            "satellite" : self.satellite,
        }
        data.update(metrics)

        logger.debug("Report {} to {}".format(
            data, self.dest_addr
        ))

        try:
            r = requests.post(self.dest_addr, json=data,
                              cert = (self.tls_cert, self.tls_key))
            if (r.status_code != requests.codes.ok):
                print(r.text)
        except requests.exceptions.ConnectionError as e:
            print(e)


class Server(BaseHTTPRequestHandler):
    """Server that replies the Rx stats requested via HTTP"""
    monitor = None # trick to access the Monitor object
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    def do_HEAD(self):
        self._set_headers()

    def do_GET(self):
        self._set_headers()
        self.wfile.write(
            json.dumps(self.monitor.get_stats()).encode()
        )


class Monitor():
    """Receiver Monitoring

    Collects receiver status metrics, prints to the console, saves to a log
    file, and reports to a server.

    """
    def __init__(self, cfg_dir, logfile=False, scroll=False, echo=True,
                 min_interval=1.0, server=False, port=defs.monitor_port,
                 report=False, report_opts={}, utc=True):
        """Monitor Constructor

        Args:
            cfg_dir      : Configuration directory where logs are saved
            logfile      : Whether to dump logs into a file
            scroll       : Whether to print logs with scrolling or continuously
                           overwrite the same line
            echo         : Whether to echo (print) every update to receiver
                           metrics to stdout.
            min_interval : Minimum interval in seconds between logs echoed or
                           saved.
            server       : Launch server to reply the receiver status via HTTP.
            port         : Server's HTTP port, if enabled.
            report       : Whether to report the receiver status over HTTP to
                           a remote address.
            report_opts  : Reporter options.
            utc          : Whether to print logs in UTC time.

        """
        self.cfg_dir      = cfg_dir
        self.logfile      = None
        self.scroll       = scroll
        self.echo         = echo
        self.min_interval = min_interval
        self.report       = report
        self.utc          = utc
        if (logfile):
            self._setup_logfile()

        # Supported receiver metrics, with their labels and printing formats
        self._metrics = {
            'lock'    : {
                'label'      : 'Lock',
                'format_str' : ''
            },
            'level'   : {
                'label'      : 'Level',
                'format_str' : '.2f'
            },
            'snr'     : {
                'label'      : 'SNR',
                'format_str' : '.2f'
            },
            'ber'     : {
                'label'      : 'BER',
                'format_str' : '.2e'
            },
            'pkt_err' : {
                'label'      : 'Packet Errors',
                'format_str' : 'd'
            }
        }
        self.stats    = {}

        # Reporter sessions
        if (report):
            self.reporter = Reporter(**report_opts)

        # State
        self.t_last_print = time.time()

        # Launch HTTP server on a daemon thread
        if (server):
            self.sever_thread = threading.Thread(
                target=self._run_server,
                args=(port,),
                daemon=True
            )
            self.sever_thread.start()

    def _run_server(self, port):
        """Run HTTP server with access to the Monitor object"""
        server_address = ('', port)
        Server.monitor = self
        self.httpd = HTTPServer(server_address, Server)
        self.httpd.serve_forever()

    def __str__(self):
        """Return string containing the receiver stats"""
        if (self.utc):
            timestamp = time.gmtime()
        else:
            timestamp = time.localtime()
        t_now = time.strftime("%Y-%m-%d %H:%M:%S", timestamp)

        string = "{} ".format(t_now)

        for key in self._metrics.keys():
            if key in self.stats:
                val = self.stats[key]
                # Label=Value
                string += " {} = {:{fmt_str}}".format(
                    self._metrics[key]['label'],
                    val[0],
                    fmt_str=self._metrics[key]['format_str'],
                )
                # Unit
                if (not math.isnan(val[0]) and val[1]):
                    string += val[1]

                string += ";"

        return string

    def _setup_logfile(self):
        """Setup directory and file for logs"""
        log_dir = os.path.join(self.cfg_dir, "logs")
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        name         = time.strftime("%Y%m%d-%H%M%S") + ".log"
        self.logfile = os.path.join(log_dir, name)
        logger.info("Saving logs at {}".format(self.logfile))

    def get_stats(self, strip_unit=True):
        """Get dictionary with the receiver stats

        Args:
            strip unit : Return the values directly, instead of tuples
                         containing the value and its unit.

        """
        if (not strip_unit):
            res = self.stats.copy()
        else:
            res = {}
            for key, val in self.stats.items():
                res[key] = val[0]

        return res

    def update(self, data):
        """Update the receiver stats kept internally

        Args:
            data : Dictionary of tuples corresponding to the receiver metrics.
                   Each tuple should consist of the value and its unit.

        """

        # The input should be a dictionary of tuples
        assert(isinstance(data, dict))
        assert(all([isinstance(x, tuple) for x in data.values()]))

        # All keys in the input dictionary must be supported receiver metrics
        assert(all([k in self._metrics for k in data.keys()]))

        # Copy all the data
        self.stats = data

        # Is it time to log a new line?
        t_now = time.time()
        if (t_now - self.t_last_print) < self.min_interval:
            return

        self.t_last_print = t_now

        # Print to console
        if (self.echo):
            print_end = '\n' if self.scroll else '\r'
            if (not self.scroll):
                sys.stdout.write("\033[K")
            print(str(self), end=print_end)

        # Append metrics to log file
        if (self.logfile):
            with open(self.logfile, 'a') as fd:
                fd.write(str(self) + "\n")

        # Report over HTTP to a remote address
        if (self.report):
            self.reporter.send(self.get_stats())


def add_to_parser(parser):
    """Add receiver monitoring options to parser"""
    m_p = parser.add_argument_group('receiver logging options')
    m_p.add_argument(
        '--log-scrolling',
        default=False,
        action='store_true',
        help='Print receiver logs line-by-line rather than repeatedly on the \
        same line'
    )
    m_p.add_argument(
        '--log-file',
        default=False,
        action='store_true',
        help='Save receiver logs on a file'
    )
    m_p.add_argument(
        '--log-interval',
        type=float,
        default=1.0,
        help="Logging interval in seconds"
    )

    ms_p = parser.add_argument_group('receiver monitoring server options')
    ms_p.add_argument(
        '--monitoring-server',
        default=False,
        action='store_true',
        help='Run HTTP server to monitor the receiver'
    )
    ms_p.add_argument(
        '--monitoring-port',
        default=defs.monitor_port,
        type=int,
        help='Monitoring server\'s port'
    )

    r_p = parser.add_argument_group('receiver reporting options')
    r_p.add_argument(
        '--report',
        default=False,
        action='store_true',
        help='Report receiver metrics to a remote HTTP server'
    )
    r_p.add_argument(
        '--report-dest',
        help='Destination address in http://ip:port format'
    )
    r_p.add_argument(
        '--report-hostname',
        help='Reporter\'s hostname'
    )
    r_p.add_argument(
        '--report-cert',
        default=None,
        help="Certificate for client-side authentication with the destination"
    )
    r_p.add_argument(
        '--report-key',
        default=None,
        help="Private key for client-side authentication with the destination"
    )


