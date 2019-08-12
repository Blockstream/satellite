ARG distroseries=bionic
FROM ubuntu:$distroseries
MAINTAINER Blockstream Satellite

RUN apt update && apt install -y python3 iproute2 iptables dvb-apps dvb-tools

RUN mkdir -p src/blocksat-rx/
COPY blocksat-cfg.py src/blocksat-rx/
COPY channels.conf src/blocksat-rx/

CMD ["/usr/bin/python3", "src/blocksat-rx/blocksat-cfg.py", "launch", "--skip-rp"]
