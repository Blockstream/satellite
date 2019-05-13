# DVB

## Dependencies

First install some required packages:

```
sudo apt apt update
sudo apt install python3 net-tools iptables dvb-apps dvb-tools
```

> NOTE: `net-tools` and `iptables` are used in order to ensure `ifconfig` and
> `iptables` tools are available.

## Run

Launch the DVB interface by running:

```
./launch.py
```

This script requires administration privileges for some commands. Thus, you may
need to run as root:

```
sudo ./launch.py
```

## Running on Docker Container

Build Docker image:

```
docker build -t blocksat/dvb .
```

Run container:

```
docker run --rm \
	--device=/dev/dvb \
	--network=host \
	--cap-add=NET_ADMIN \
	--cap-add=SYS_ADMIN -it blocksat/dvb
```

After runnning, configure reverse path filters from the host (not from the
container) by running:

```
sudo ./set_rp_filters.py -i dvb1_0
```

This script will run some `sysctl` configurations, which are not executed inside
the container.
