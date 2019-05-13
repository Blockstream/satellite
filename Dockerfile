ARG distroseries=bionic
FROM ubuntu:$distroseries
MAINTAINER Blockstream Satellite

RUN apt update && apt install -y python3 net-tools iptables dvb-apps dvb-tools

RUN mkdir -p src/blocksat-rx/
COPY launch.py src/blocksat-rx/
COPY channels.conf src/blocksat-rx/

CMD ["/usr/bin/python3", "src/blocksat-rx/launch.py", "--skip-rp"]
