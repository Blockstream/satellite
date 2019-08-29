# DVB

## Hardware

### USB DVB-S2 Receivers

This type of receiver connects to your host (Linux PC) directly via USB and
combines processing executed in the modem with some processing carried out by
the host. Hence, it requires specific drivers, which are described next.

1. **TBS5520SE Multi-standard Universal TV Tuner USB Box**
    - [User guide](https://www.tbsiptv.com/download/tbs5520se/tbs5520se_user_guide.pdf)
    - [Datasheet](https://www.tbsiptv.com/download/tbs5520se/tbs5520se_multi_standard_universal_tv_tuner_box_data_sheet.pdf)
2. **TBS5927 Professional DVB-S2 TV Tuner USB**
    - [User guide](https://www.tbsiptv.com/download/tbs5927/tbs5957_user_guide.pdf)
    - [Datasheet](https://www.tbsiptv.com/download/tbs5927/tbs5927_professtional_dvb-S2_TV_Tuner_USB_data_sheet.pdf)

To install the required drivers, run:

```
./tbsdriver.sh
```

Reboot after successful completion.

Further information can be found
[here](https://github.com/tbsdtv/linux_media/wiki).

### Standalone DVB-S2 Modems

This type of receiver handles the full DVB-S2 processing and unpacking of IP
packets from DVB-S2 frames, with no need for a host PC. It will typically
contain an Ethernet/LAN output interface, through which it will output the IP
traffic. To receive this traffic, the host PC will need to be on the same LAN as
the modem or directly connected to it via Ethernet.

## Software Dependencies

### Ubuntu/Debian:

```
sudo apt apt update
sudo apt install python3 iproute2 iptables dvb-apps dvb-tools
```

> NOTE 1: `iproute2` and `iptables` are used in order to ensure `ip` and
> `iptables` tools are available.
>
> NOTE 2: `dvb-apps` and `dvb-tools` are not required if using a standalone
> DVB-S2 modem. They are only required if using a USB modem.


### Fedora:
```
sudo dnf update
sudo dnf install python3 iproute iptables dvb-apps v4l-utils
```

> NOTE: `dvb-apps` and `v4l-utils` are not required if using a standalone DVB-S2
> modem. They are only required if using a USB modem.

## Running

### Running with a USB DVB-S2 modem:

Launch the DVB-S2 interface by running:

```
sudo ./blocksat-cfg.py launch
```

This script will set an arbitrary IP address to the network interface that is
created in Linux in order to handle the IP traffic received via the satellite
link. To define a specific IP instead, run the above with `--ip target_ip`
argument, where `target_ip` is the IP of interest.

### Running with a standalone DVB-S2 modem

As mentioned earlier, in standalone mode you will need a network interface on
your host connected to the same LAN as the DVB-S2 modem or directly to it via
Ethernet. In this case, in order to receive the traffic, you will only need some
networking configurations on your host. Such configurations are indicated and
executed by running:

```
sudo ./blocksat-cfg.py standalone -i ifname
```

where `ifname` is the name of the network interface that is connected (via
switches or directly) to the DVB-S2 modem.

## Docker

The Docker image that is available in this repository installs all software
dependencies and can be used to run the `blocksat-cfg` tool. Note, however, that
if using a USB modem, the modem's drivers are install required on the Docker
host (not the container).

First, build the image:

```
docker build -t blocksat/dvb .
```

Run the container:

```
docker run --rm \
	--device=/dev/dvb \
	--network=host \
	--cap-add=NET_ADMIN \
	--cap-add=SYS_ADMIN \
	-it blocksat/dvb \
	launch
```

If using a standalone modem, substitute `launch` on the above command with
`standalone`, according to the [run guidelines given above](#Running). Further
arguments such as `-i` can also be provided after the command (i.e. `launch` or
`standalone`) and will accordingly be processed by the `blocksat-cfg` tool
inside the container.

After running, configure reverse path filters by running the following from the
host (not from the container):

```
sudo ./blocksat-cfg.py rp -i dvb0_0
```

## Building dvb-apps from source

```
hg clone http://linuxtv.org/hg/dvb-apps
cd dvb-apps
make
sudo make install
```

For Kernel version greater than or equal to 4.14, [this
solution](https://gist.github.com/Kaeltis/d87dc76fc604f8b3373231dcd2d76568) can
be used to complete the compilation.

More information can be found
[here](https://www.linuxtv.org/wiki/index.php/LinuxTV_dvb-apps).
