# Running on Docker

There are two Docker images in this repository:

- `usb.docker`: for Linux USB receiver setups.
- `sdr.docker`: for SDR-based setups.

If using a USB demodulator, however, note the drivers need to be installed on
the Docker host (not the container). Please refer to the [USB demodulator
guide](tbs.md#tbs-5927-drivers).

Both images expect a source distribution tarball of the `blocksat-cli`
package. Hence, before proceeding, on the root directory, run:

```
python3 setup.py sdist
```

## Linux USB Container

Build the image with:

```
docker build -t blockstream/blocksat-usb -f usb.docker ..
```

Run the container while sharing the DVB network interfaces `dvb0_0` and `dvb0_1`
(rename as needed):

```
docker run --rm \
	--device=/dev/dvb0_0 \
	--device=/dev/dvb0_1 \
	--network=host \
	--cap-add=NET_ADMIN \
	--cap-add=SYS_ADMIN \
	-it blockstream/blocksat-usb \
	usb
```

After running, configure reverse path filters by running the following from the
host (not from the container):

```
blocksat-cli rp -i dvb0_0
blocksat-cli rp -i dvb0_1
```

## SDR Container

First, build the image:

```
docker build -t blockstream/blocksat-sdr -f sdr.docker ..
```

Next, run the container as follows:

```
docker run --rm \
	--privileged \
	-v /dev/bus/usb:/dev/bus/usb \
	-it blockstream/blocksat-sdr
```

Note **privileged mode** is used in order to allow the container to access the
RTL-SDR USB device of the host.

> On a Mac OSX host, you will need to set up a
> [docker-machine](https://docs.docker.com/machine/) in order share the SDR USB
> device. Once this docker-machine is active, you can share the USB device via
> the settings of the [machine
> driver](https://docs.docker.com/machine/drivers/). Then, run the above `docker
> run` command normally.

