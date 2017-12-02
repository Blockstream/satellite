from numpy import arange

class tuning_control():
  freqs = []
  metric = []

  def __init__(self, min_freq, max_freq, freq_step, top_block_obj):
    self.min_freq = min_freq;
    self.max_freq = max_freq;
    self.freq_step = freq_step;
    self.curr_freq = min_freq;
    self.last_freq = 0;
    self.finish = True;
    self.first = True;

    self.freq_range = arange(min_freq-freq_step,max_freq+2*freq_step,freq_step)
    self.freq_idx = 0;

    self.top = top_block_obj;

  def dump_timing_metric(self, file_name):
      f = open(file_name,'w')
      for i in range(len(self.freqs)):
        f.write(str(self.freqs[i])+', '+str(self.metric[i])+'\n')
      f.close()

  def get_next_freq(self, timing_metric):

    if(self.freq_idx < len(self.freq_range)):
        new_freq = self.freq_range[self.freq_idx]
    else:
        new_freq = 0;

    if(self.freq_idx == 0):
        # The first time the get_next_freq is called it will just
        # return the new frequency but will not store the timing metric
        print("First run, just return the first freq:", new_freq)

    	self.freq_idx += 1;
    if(self.freq_idx == len(self.freq_range)-1):
        # The last time the get_next_freq is clled it will get the last
        # information, them dump the metrics and stop the flow-graph

        self.freqs += [self.last_freq]
        self.metric += [timing_metric]

        print('Finished Freq Search, Stopping Flow-Graph')
        self.dump_timing_metric('/tmp/metric.csv')
    	self.freq_idx += 1;

        self.top.stop()
        self.top.wait()
	print("Enter to exit")
    if(self.freq_idx > len(self.freq_range)):
	# Just wait for the user to press enter
	return 0;
    else:
	fo_str = str(int(self.last_freq/1e3));
	tm_str = str(int(timing_metric*100));
	msg = "["+fo_str+" kHz] Signal Strength: "+tm_str+" %"
        print msg
	# print('Tunning control: got metric:', timing_metric, 'from freq', self.last_freq)
        # print("tuning control: new freq: ", new_freq)
        self.freqs += [self.last_freq]
        self.metric += [timing_metric]

    	self.freq_idx += 1;

    self.last_freq = new_freq;

    return new_freq;

  ## Update NCO Frequency
  # @param est_cfo Current carrier frequency offset (CFO) estimation
  # @param new_rf_center_freq New RF Center Frequency to be set
  # @param curr_rf_center_freq Current RF Center Frequency
  #
  # This function should be used to glue the current CFO estimate (a variable
  # that is internal to the freq. recovery module) into a parameter that is
  # expected to be passed to the NCO module for CFO correction. Additionally, it
  # eventually updates the RF center frequency configuration in the radio.
  def update_nco_freq(self, est_cfo, new_rf_center_freq, curr_rf_center_freq):
    # Update the radio RF center frequency if a new one is requested
    if (curr_rf_center_freq != new_rf_center_freq):
        self.top.set_freq(new_rf_center_freq)

    return est_cfo;
