# DVB

## Dependencies

First install some required packages.

### Ubuntu/Debian:
```
sudo apt apt update
sudo apt install python3 iproute2 iptables dvb-apps dvb-tools
```

> NOTE: `iproute2` and `iptables` are used in order to ensure `ip` and
> `iptables` tools are available.

### Fedora:
```
sudo dnf update
sudo dnf install python3 iproute iptables dvb-apps v4l-utils
```

## Run

Launch the DVB interface by running:

```
sudo ./blocksat-cfg.py launch
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
sudo ./blocksat-cfg.py -i dvb1_0
```

This script will run some `sysctl` configurations, which are not executed inside
the container.

## Running with standalone DVB modem

```
sudo ./blocksat-cfg.py rp -i ifname
```

```
sudo ./blocksat-cfg.py firewall -i ifname --standalone
```
