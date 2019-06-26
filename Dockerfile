ARG distroseries=bionic
FROM ubuntu:$distroseries
MAINTAINER Blockstream

RUN apt-get update && apt-get install -y software-properties-common
RUN add-apt-repository -y ppa:blockstream/satellite
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y satellite

CMD ["bash"]
