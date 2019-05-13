# DVB

## Docker

Build:

```
docker build -t blocksat/dvb .
```

Run:

```
docker run --rm \
	--device=/dev/dvb \
	--network=host \
	--cap-add=NET_ADMIN \
	--cap-add=SYS_ADMIN -it blocksat/dvb
```

After runnning, configure reverse path filters with:

```
sudo ./set_rp_filters.py -i dvb1_0
```

Note, this will run some `sysctl` configuration, which are not executed inside
the container.
