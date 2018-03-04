import sys
import time
import threading

# Definitions
MAX_SNR_DB = 20


class Logger(threading.Thread):
    """Logger Class

    Periodically calls an instance-defined print routine

    Attributes:
        block_obj : The flowgraph object to be passed to the print function
        period    : Interval between prints
        print_fcn : The specific print function to be used every period
        lock      : A mutex used to synchronize prints across instances
    """
    def __init__(self, block_obj, period, print_fcn, lock):
        ''' Init Logger '''

        # Init daemon thread
        threading.Thread.__init__(self)
        self.daemon = True

        self.block_obj = block_obj
        self.period    = period
        self.log       = print_fcn
        self.lock      = lock

    def run(self):

        next_print = time.time() + self.period

        while(True):
            # Schedule next print
            time.sleep((next_print - time.time()))
            next_print = time.time() + self.period

            # Call Print
            self.lock.acquire()
            try:
                self.log(self.block_obj)
            finally:
                self.lock.release()


def print_frame_sync(block_obj):

    # Get data from the frame synchronizer block
    state            = block_obj.get_state()
    timing_indicator = block_obj.get_timing_rec_indicator()

    # Print
    sys.stdout.write("----------------------------------------")
    sys.stdout.write("----------------------------------------\n")
    sys.stdout.write("[" + time.strftime("%Y-%m-%d %H:%M:%S") + "] ")
    sys.stdout.write("Frame Timing => ")

    if (state == 0):
        sys.stdout.write("SEARCHING")
    else:
        sys.stdout.write("LOCKED")

    sys.stdout.write("\t Timing Indicator: ");
    sys.stdout.write(str("{:3.4f}".format(timing_indicator)) + " %");
    sys.stdout.write("\r\n");
    sys.stdout.write("----------------------------------------")
    sys.stdout.write("----------------------------------------\n")
    sys.stdout.flush()


def print_snr(block_obj):

    # Get data from the SNR meter block
    snr_db = block_obj.get_snr()

    # Print SNR with a bar indicator
    # (each "=" indicates 0.5 dB)
    sys.stdout.write("[" + time.strftime("%Y-%m-%d %H:%M:%S") + "] ")
    sys.stdout.write("SNR [")

    bar_pos = round(2*snr_db)

    for i in range(0, 2*MAX_SNR_DB):
        if (i <= bar_pos):
            sys.stdout.write("=")
        else:
            sys.stdout.write(" ")

    sys.stdout.write("] ")
    sys.stdout.write(str("{:2.4f}".format(snr_db)))
    sys.stdout.write(" dB\r\n")
    sys.stdout.flush()


def print_ber(block_obj):

    # Get BER
    ber = block_obj.get_ber()

    # Print
    sys.stdout.write("----------------------------------------")
    sys.stdout.write("----------------------------------------\n")
    sys.stdout.write("[" + time.strftime("%Y-%m-%d %H:%M:%S") + "] ")
    sys.stdout.write("BER: ");
    sys.stdout.write(str("{:.2E}".format(ber)));
    sys.stdout.write("\r\n");
    sys.stdout.write("----------------------------------------")
    sys.stdout.write("----------------------------------------\n")
    sys.stdout.flush()


class rx_logger():
    """Rx Logger

    Initiates threads to log useful receiver metrics into the console.

    """

    def __init__(self, snr_meter_obj, snr_log_period, frame_synchronizer_obj,
                 frame_sync_log_period, decoder_obj, ber_log_period):

        # Use mutex to coordinate logs
        lock = threading.Lock()

        # Declare loggers
        snr_logger        = Logger(snr_meter_obj,
                                   snr_log_period,
                                   print_snr,
                                   lock)
        frame_sync_logger = Logger(frame_synchronizer_obj,
                                   frame_sync_log_period,
                                   print_frame_sync,
                                   lock)
        ber_logger        = Logger(decoder_obj,
                                   ber_log_period,
                                   print_ber,
                                   lock)

        # Start threads:
        snr_logger.start()
        frame_sync_logger.start()
        ber_logger.start()

