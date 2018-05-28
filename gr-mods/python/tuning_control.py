import sys
import os
import threading
import time
import datetime
import math
from numpy import arange

# Definitions
min_cfo_rec_alpha_scan_mode = 0.1
nco_update_rate_hz = 200
max_n_scan_attemps = 2

class tuning_control(threading.Thread):
  """Tuning Control

  Runtime control of the RF center frequency or RF frequency scanning helper.

  Attributes:
    scan_range        :  Range of frequencies to scan (0 disables scan mode)
    n_steps           :  Number iterations used to sweep the scan range
    cfo_poll_interval :  CFO polling interval in runtime control mode
    scan_interval     :  Interval between each scanned frequency in scan mode
    sps               :  Samples-per-symbol (used to reset the FLL)
    frame_sync_obj    :  Object of the top-level frame synchronizer module
    cfo_rec_obj       :  Object of the top-level frequency (CFO) recovery module
    nco_obj           :  Object of the top-level NCO module
    logger_obj        :  Object of the top-level Rx Logger module
    freq_label_obj    :  Object of the top-level GUI label (if any)
    fll_obj           :  Object of the top-level band-edge FLL
    rf_freq_getter    :  Getter for the top-level RF center frequency
    rf_freq_setter    :  Setter for the top-level RF center frequency
  """

  def __init__(self, samp_rate, sps, scan_range, n_steps, cfo_poll_interval,
               scan_interval, frame_sync_obj, cfo_rec_obj, nco_obj, logger_obj,
               freq_label_obj, fll_obj, rf_freq_getter, rf_freq_setter):

    self.samp_rate  = samp_rate
    self.sps        = sps
    self.scan_mode  = (scan_range != 0)
    self.scan_range = scan_range
    self.rf_freq    = rf_freq_getter()

    self.frame_sync_obj = frame_sync_obj
    self.cfo_rec_obj    = cfo_rec_obj
    self.nco_obj        = nco_obj
    self.fll_obj        = fll_obj
    self.rx_logger      = logger_obj

    # Interaction with the SDR
    self.get_hw_freq    = rf_freq_getter
    self.set_hw_freq    = rf_freq_setter

    self.cfo_poll_interval   = cfo_poll_interval
    self.scan_interval       = scan_interval
    self.nco_update_interval = 1.0/nco_update_rate_hz

    # Launch either the frequency scan or CFO control thread
    if (self.scan_mode):

      self.freq_step    = scan_range/n_steps
      self.curr_freq    = self.rf_freq
      self.freqs        = self.get_freq_scan_array(self.rf_freq,
                                                   scan_range,
                                                   n_steps)
      self.n_scan_steps = n_steps

      self.scan_thread = threading.Thread(target=self.freq_scanner,
                                          args=())
      self.scan_thread.daemon = True
      self.scan_thread.start()

    else:
      self.cfo_ctrl_thread = threading.Thread(target=self.cfo_controller,
                                         args=())
      self.cfo_ctrl_thread.daemon = True
      self.cfo_ctrl_thread.start()

    # And regardless of the operation mode, launch the NCO control
    # thread:
    if (self.nco_obj):
      self.nco_ctrl_thread = threading.Thread(target=self.nco_controller,
                                              args=())
      self.nco_ctrl_thread.daemon = True
      self.nco_ctrl_thread.start()

  def freq_scanner(self):
    """ Frequency scan mode """

    # A scan is only complete once one of the tested frequencies can acquire
    # frame lock:
    frame_lock_acquired = False
    # If scan finishes and the signal is not found, try again until a maximum
    # number of attempts:
    n_attempts = 0

    # Configure the frequency recovery to respond quick enough during the scan
    if (self.cfo_rec_obj is not None):
      start_freq_rec_alpha = self.cfo_rec_obj.get_alpha()

      if (start_freq_rec_alpha < min_cfo_rec_alpha_scan_mode):
        self.cfo_rec_obj.set_alpha(min_cfo_rec_alpha_scan_mode)
    else:
      start_freq_rec_alpha = 0

    # Sleep shortly just to allow the initialization logs to clear
    time.sleep(3)

    print("\n========================= Scan Mode =========================")
    print("Sweep from %f MHz to %f MHz, in steps of %.2f kHz" %(
      min(self.freqs)/1e6, max(self.freqs)/1e6, self.freq_step/1e3))
    self.print_scan_duration()

    # Change to the starting frequency
    self.set_scan_start_freq()

    # Start schedule of wake-ups
    next_work = time.time() + self.scan_interval

    while self.scan_mode:

      sys.stdout.write("[Scanning %6.3f MHz] " %(self.curr_freq/1e6))
      sys.stdout.flush()

      # Sleep and show progress until next scheduled work
      self.sleep_with_progress_dots(next_work, self.scan_interval)

      # Schedule next work
      next_work = time.time() + self.scan_interval

      # Each iteration evaluates the timing metric that can be
      # obtained with the chosen RF center frequency
      self.check_timing_metric()

      # Check if the current frequency could achieve frame lock:
      if (self.frame_sync_obj.get_state()):
        frame_lock_acquired = True

      # Stop when frame lock is achieved or all frequencies are scanned
      if (self.freq_idx == self.n_scan_steps or frame_lock_acquired):

        # Best frequency:
        max_idx     = self.metric.index(max(self.metric))
        best_freq   = self.freqs[max_idx]
        best_metric = self.metric[max_idx]

        self.print_scan_results(best_freq, best_metric, frame_lock_acquired)

        # Exit immediatelly if frame lock was achieved
        if (frame_lock_acquired):
          self.scan_mode = False
        else:
          print("Error: signal was not detected in any of the frequencies.")

          if (n_attempts == max_n_scan_attemps):
            print("Maximum number of scan attempts reached.")
            print("Check your hardware and/or try a wider scan range.")

            # Exit scan
            self.scan_mode = False

            print '\033[91m' + "ERROR:" + '\033[0m' + " Signal not found."

            os._exit(1)
          else:
            # Double the scan interval
            self.scan_interval = 2 * self.scan_interval

            # Go back to starting frequency
            self.set_scan_start_freq()

            if (n_attempts == 0):
              print("A second scan will be attempted.")
            elif (n_attempts == (max_n_scan_attemps - 1)):
              print("Scan will be attempted one last time.")
            else:
              print("Another scan round will be attempted.")

            print("Observation of each frequency will now take %.2f sec" %(
              self.scan_interval))
            self.print_scan_duration()

          n_attempts += 1

      if (self.scan_mode):
        # Proceed to analyze the next frequency:
        self.scan_next_freq()

    # ------- Scan exit routine -------

    # Then exit:
    self.exit_scan_mode(frame_lock_acquired, best_freq, start_freq_rec_alpha)

  def cfo_controller(self):
    """ Interaction with Runtime CFO controller """

    # CFO threshold
    sym_rate = self.samp_rate / self.sps
    rolloff  = self.fll_obj.rolloff()

    # The BE filter is centered at "(1 + rolloff) * (Rsym/2)". A frequency shift
    # of "(1 + rolloff) * (Rsym/2)" shifts the signal to the BE filter center,
    # but in this case half of the effective signal bandwidth is still
    # inside. Twice this amount shifts the extreme energy of the effective
    # bandwidth to the BE center frequency. Yet, the BE filter extends over
    # "rolloff * (Rsym/2)" from its center point, Thus, the maximum traceable
    # CFO is:
    #   (1 + rolloff)*(Rsym/2) +
    #   (1 + rolloff)*(Rsym/2) +
    #   rolloff * (Rsym/2)
    #   ------------------------
    #   = (1 + (3/2)*rolloff)*(Rsym/2)
    #
    # A slightly lower value is then used for the threshold
    self.abs_cfo_threshold = sym_rate * (1 + (1.4)*rolloff)

    next_work = time.time() + self.cfo_poll_interval

    while True:

      # Sleep until next scheduled work
      current_time = time.time()

      if (next_work > current_time):
        time.sleep(next_work - current_time)

      # Schedule next work
      next_work = time.time() + self.cfo_poll_interval

      # Check the current target RF center frequency according to the runtime
      # CFO controller module and the RF center frequency that is currently
      # being used in the SDR board
      current_cfo_est        = self.get_fll_cfo_estimation()
      current_rf_center_freq = self.get_hw_freq()

      # Also check whether the frame recovery algorithm is locked, to ensure a
      # frequency shift is only carried while the system is running already and
      # prevent shifts during the initialization.
      frame_sync_state = self.frame_sync_obj.get_state()

      # Update the radio RF center frequency if a new one is requested
      if (abs(current_cfo_est) > self.abs_cfo_threshold and
          frame_sync_state != 0):

        target_rf_center_freq = current_rf_center_freq + current_cfo_est

        print("\n--- Carrier Tracking Mechanism ---");
        print "[" + datetime.datetime.now().strftime(
          "%A, %d. %B %Y %I:%M%p" + "]")
        print("RF center frequency update");
        print("From:\t %d Hz (%6.2f MHz)" %(
          current_rf_center_freq, current_rf_center_freq/1e6));
        print("To:\t %d Hz (%6.2f MHz)" %(
          target_rf_center_freq, target_rf_center_freq/1e6));
        print("Frequency shifted by %.2f kHz" %(
          (target_rf_center_freq - current_rf_center_freq)/1e3
        ))
        print("----------------------------------\n");

        # Update the RF frequency
        self.set_freq(target_rf_center_freq)

  def nco_controller(self):
    """Interaction with the NCO module and the runtime CFO controller module"""

    next_work = time.time() + self.nco_update_interval

    while True:

      # Sleep until next scheduled work
      current_time = time.time()

      if (next_work > current_time):
        time.sleep(next_work - current_time)

      # Schedule next work
      next_work = time.time() + self.nco_update_interval

      # Update the frequency corrected by the NCO - make it equal to the
      # CFO that is currently estimated in the runtime CFO controller module
      current_cfo_est = self.cfo_rec_obj.get_cfo_estimate()
      self.nco_obj.set_freq(current_cfo_est)

  def check_timing_metric(self):

    # Get the timing metric from the frame synchronizer
    timing_metric = self.frame_sync_obj.get_avg_timing_metric()

    self.metric.append(timing_metric)

    sys.stdout.write(" Signal Strength: %.4f\n" %(timing_metric))
    sys.stdout.flush()

  def sleep_with_progress_dots(self, wake_up_time, sleep_interval):
    """Sleep and print progress in terms of dots

    Args:
        wake_up_time   : time scheduled for the task wake-up
        sleep_interval : target sleep interval
    """

    n_complete_dots  = 10
    printed_progress = 0
    current_time     = time.time()

    # Print dots until the wake-up time is reached
    while (wake_up_time > current_time):

      progress        = 1 - ((wake_up_time - current_time) / sleep_interval)
      n_progress_dots = int(round(progress * n_complete_dots))

      for i in range(printed_progress, n_progress_dots):
        sys.stdout.write('..')
        printed_progress = n_progress_dots
        sys.stdout.flush()

      time.sleep(1)
      current_time = time.time()

    # Make sure the number of printed dots is always the same
    missing_dots = n_complete_dots - printed_progress

    for i in range(0, missing_dots):
      sys.stdout.write('..')
      sys.stdout.flush()

  def exit_scan_mode(self, frame_lock, target_freq, freq_rec_alpha):
    """Routine for exiting the scan mode and turning into normal mode

    Args:
        frame_lock     : asserted when scan exits with frame lock
        target_freq    : the target RF center frequency obtained through scan
        freq_rec_alpha : the averaging alpha to be ser for the CFO recovery

    """

    # Set the RF center frequency in HW in case the scan has not exited with
    # frame lock:
    if (not frame_lock or not self.frame_sync_obj.get_state()):
      current_cfo_est = self.get_fll_cfo_estimation()
      self.set_freq(target_freq + current_cfo_est)
      # Changing frequency will lead to frame recovery loss, so it is better to
      # wait until the frame loss logs are printed
      time.sleep(3)

    # Set frequency recovery averaging length back to the starting value:
    if (self.cfo_rec_obj is not None):
      self.cfo_rec_obj.set_alpha(freq_rec_alpha)

    # Launch runtime control interaction thread:
    self.cfo_ctrl_thread = threading.Thread(target=self.cfo_controller,
                                            args=())
    self.cfo_ctrl_thread.daemon = True

    print("Starting receiver...")
    print("----------------------------------------")
    self.cfo_ctrl_thread.start()

    # Enable the logger module
    self.rx_logger.enable()

  def get_freq_scan_array(self, center_freq, scan_range, n_iter):
    """Prepare the array of frequencies to scan

    Returns the vector of frequencies sorted such that the first frequency to be
    scanned is the nominal center frequency and, then, the adjcent frequencies
    (w/ positive and negative offsets) are unfolded. This ensures that the
    extreme case of bigger offsets is tested later and the frequencies with
    lower error are tested first.

    Args:
        center_freq : The nominal RF center frequency (starting point)
        scan_range  : Range of frequencies to scan
        n_iter      : Number of scan iterations

    """

    freq_step  = scan_range/n_iter
    freq_array = []

    for i in range(0, n_iter + 1):

      i_abs_offset = i/2 + (i % 2)

      if (i % 2 == 0):
        freq = center_freq + (i_abs_offset * freq_step)
      else:
        freq = center_freq - (i_abs_offset * freq_step)

      freq_array.append(freq)

    return freq_array

  def set_scan_start_freq(self):
    """Set the starting point for the scan"""

    self.metric    = []
    self.freq_idx  = 0;
    self.curr_freq = self.freqs[0]
    self.set_freq(self.freqs[0])

  def scan_next_freq(self):

    # Move to a new frequency from the list
    self.freq_idx += 1;
    self.curr_freq = self.freqs[self.freq_idx]

    # Set it in the top-level variable (used by the RF board) and inform the CFO
    # controller:
    self.set_freq(self.curr_freq)

  def set_freq(self, freq):
    """Wrapper for setting the frequency in HW as int """

    self.reset_fll()

    self.set_hw_freq(int(round(freq)))

  def reset_fll(self):
    """Workaround to reset the FLL"""

    self.fll_obj.set_samples_per_symbol(self.sps)
    self.fll_obj.set_frequency(0)
    self.fll_obj.set_phase(0)

  def get_fll_cfo_estimation(self):
    """Get the CFO corresponding to the current freq. correction in the FLL"""

    norm_angular_freq = self.fll_obj.get_frequency()

    norm_freq = norm_angular_freq / (2.0 * math.pi)

    analog_freq = norm_freq * self.samp_rate

    return (-analog_freq)

  def print_scan_duration(self):
    """Compute and print the maximum duration expected for the complete scan """

    n_scan_steps  = self.n_scan_steps
    step_interval = self.scan_interval

    duration_sec  = step_interval * n_scan_steps
    d_min, d_sec  = divmod(duration_sec, 60)

    sys.stdout.write("The scan can take up to ")
    if (d_min > 0):
      sys.stdout.write("{:>d} min and {:2d} sec.\n\n".format(int(d_min),
                                                           int(d_sec)))
    else:
      sys.stdout.write("{:2d} sec.\n\n".format(int(d_sec)))

    sys.stdout.flush()

  def print_scan_results(self, best_freq, best_metric, sig_found):
    """Print Results"""

    delta_from_nominal = best_freq - self.rf_freq

    sorted_idx = [i[0] for i in sorted(enumerate(self.metric),
                                           key=lambda x:x[1],
                                           reverse=True)]

    print("============================================================")
    if (sig_found):
      print("Blockstream Satellite signal was found\n--")
    else:
      print("Frequency scan complete\n--")


    print("_%21s___%30s" %(
      "_____________________", "______________________________"))

    if (sig_found):
      print("| %21s | %-10d Hz (%6.2f MHz) |" %(
        "Frequency", best_freq, best_freq/1e6))
    else:
      print("| %21s | %-10d Hz (%6.2f MHz) |" %(
        "Best frequency", best_freq, best_freq/1e6))
    print("| %21s | %-7.4f %19s |" %(
      "Average timing metric", best_metric, ""))
    print("| %21s | %-27s |" %(
      "Offset from nominal", "%d Hz" %delta_from_nominal +
      "(%.2f kHz)" %(delta_from_nominal/1e3)))
    print("|%21s___%29s|" %(
      "_____________________", "_____________________________"))

    print("\nRanking of scanned frequencies (first is the best):\n")
    print("%-4s | %-27s | %-13s" %("Rank", "Frequency", "Timing Metric"))
    print("%-4s | %-27s | %-13s" %(
      "____", "___________________________", "_____________"))
    for i, metric_idx in enumerate(sorted_idx):
      print("%4d | %10d Hz (%6.2f MHz) | %-5.4f" %(
        i, self.freqs[metric_idx], self.freqs[metric_idx]/1e6,
        self.metric[metric_idx]))
    print("============================================================\n")

