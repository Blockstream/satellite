FROM debian:stretch

RUN apt-get update && apt-get install -y \
      gnuradio build-essential git cmake sudo vim \
      swig osmo-sdr gr-osmosdr usbutils \
      && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/Blockstream/satellite.git /opt/satellite

RUN cd /opt/satellite && ./install_gr_framers.sh && ./install_mods.sh \
  && ldconfig

COPY ./entrypoint.sh /
ENTRYPOINT ["/entrypoint.sh"]
