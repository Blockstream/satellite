"""Monitor the satellite receiver"""
import sys, os, time, logging, math
from . import defs
from datetime import datetime


logger = logging.getLogger(__name__)
sats   = [ x['alias'] for x in defs.satellites]


class Monitor():
    """Receiver Monitoring

    Collects receiver status metrics, prints to the console, saves to a log
    file, and reports to a server.

    """
    def __init__(self, cfg_dir, logfile=False, scroll=False):
        """Monitor Constructor

        Args:
            cfg_dir : Configuration directory where logs are saved
            logfile : Whether to dump logs into a file
            scroll  : Whether to print logs with scrolling or continuously
                      overwrite the same line

        """
        self.cfg_dir = cfg_dir
        self.logfile = None
        self.scroll  = scroll
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

    def __str__(self):
        """Return string containing the receiver stats"""
        t_now  = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
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
        logger.info("Saving logs on {}".format(self.logfile))

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

        # Print to console
        print_end = '\n' if self.scroll else '\r'
        if (not self.scroll):
            sys.stdout.write("\033[K")
        print(str(self), end=print_end)

        # Append metrics to log file
        if (self.logfile):
            with open(self.logfile, 'a') as fd:
                fd.write(str(self) + "\n")


