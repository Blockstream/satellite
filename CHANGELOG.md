# Changelog

## Releases
- [2.5.1](#251)
- [2.5.0](#250)
- [0.4.7](#047)
- [0.4.6](#046)
- [0.4.5](#045)
- [0.4.4](#044)
- [0.4.3](#043)
- [0.4.2](#042)
- [0.4.1](#041)
- [0.4.0](#040)
- [0.3.2](#032)
- [0.3.1](#031)
- [0.3.0](#030)

## 2.5.1

Release Date: TBD

### Added
- Installation of gr-dvbs2rx on Debian Bookworm (12).
- User addition to video group when configuring a TBS USB receiver.

### Fixed
- Handling of pipe size verification with an SDR receiver using leandvb.
- Handling of TSDuck .lastcheck file creation failure.

## 2.5.0

Release Date: 2024-12-31

### Added
- Graphical user interface (GUI) application (`blocksat-gui`).
- Option to disable Linux media build backport on TBS driver installation.

### Changed
- Telstar 11N Africa and Europe downlink frequencies.
- Major version number from 0 to 2 for aligning with the source control tags.

### Fixed
- Compilation of SNMP MIB files when configuring or monitoring the Novra S400
  receiver.
- TBS driver installation failing due to disabling RC/IR support.
- Installation of copr dependencies with dnf5 on Fedora 41.

## 0.4.7

Release Date: 2024-07-18

### Added
- Support for the Mediastar A381 C-band LNB.

### Changed
- Telstar 18V C and Ku band downlink frequencies.
- Telstar 18V C band polarization.
- URL printing style on the instructions module.
- PySNMP package from the no longer maintained `pysnmp` to `pysnmplib`.

### Fixed
- `add-apt-repository` command on Debian 12 when installing dependencies.
- Usage of the deprecated `distutils.version` package.
- SNMP dependence on the `asyncore` package no longer available in Python 3.12.
- Installation of DVB apps formerly from the `v4l-utils` package on Fedora 40.

### Removed
- Support for the decommissioned Eutelsat 113 satellite.

## 0.4.6

Release Date: 2023-07-12

### Added
- Support for reporting to a custom Blockstream Monitoring server for testing.
- Environmental variable to disable the verification of TBS USB drivers.
- Generation of manpage and bash completion files via Makefile.
- Command `blocksat-cli sat-ip ls` to list the available Sat-IP receivers.
- Support for new Satellite API order queues on the `api list` command.
- Automatic patching and runtime verification of the channel configuration file
  used by USB receivers.
- Support for NetworkManager when configuring static IP addresses.

### Changed
- T18V C-band downlink frequency following the update on July 12, 2023.
- SSE client to custom implementation on the API demo Rx command.
- Verification of already configured components before attempting to configure
  the firewall, RP filters, SDR, S400, and USB receivers.
- Dependency on `zfec` made optional.
- Generate Gqrx configuration directly with the `blocksat-cli cfg` command for
  SDR receivers.

### Fixed
- Receiver reports not timing out when the connection hangs.
- GPG home directory not recursively created when setting up the directory.
- Dependency on GPG key importing order when setting up the GPG directory.
- GPG key creation not indicating an error for an empty passphrase.
- v4l LNB definition inferred for the C1-PLL LNB when using a USB receiver.
- TBS driver compilation with Linux kernel 6.0+ on Fedora 37 and 38.
- Fix Netplan configuration with NetworkManager renderer.
- Fix `firewall-cmd` output parsing when configuring the firewall.
- Fix parsing of TBS USB receiver logs breaking with unexpected metrics.

### Removed
- Dependency on `sseclient-py`.

## 0.4.5

Release Date: 2023-03-03

### Added
- Support for the gr-dvbs2rx SDR receiver implementation selected with the new
  `--impl` option on the `sdr` command and installed by the `deps install`
  command on Ubuntu 22.04+ and Fedora 36+.
- Support for password-based authentication with the Satellite Monitoring API,
  enabled automatically with the `--report` option.
- Command `reporting password` to set/reset the Monitoring API password.
- Command `reporting info` to show the Monitoring API registration info.
- Option `--disable` to disable selected Linux media modules when building the
  TBS drivers with the `deps tbs-drivers` command.
- Non-interactive modes for the `gqrx` and `sdr` commands.
- Option to return a JSON-formatted string with the `blocksat-cli cfg show`
  command.
- Option to save a static IP address associated with an IP22 and automatic
  usage of the address when launching the Sat-IP client.
- Explicit verification of the S400's reachability before attempting to
  configure or monitor the receiver.
- Validation of the frequency correction parameter passed to the S400 receiver.
- Verification of the TBS USB drivers before USB configuration or launching.
- Support for specification of channel number on the `api send` command.
- Support for sending Satellite API messages to non-paid channels.
- `api get` command to get information from a Satellite API transmission order.
- `api list` command to list the transmission orders on the Satellite API.
- Polling-based operation activated by option `--poll` on the API demo-rx app.
- Option `--if-by-region` on the demo-rx for 1:1 interface-to-region mapping.

### Changed
- Galaxy 18 downlink frequency.
- Explainer printed on initial registration with the monitoring API, with
  privacy and detailed registration info made optional.
- Information and organization of results on the `blocksat-cli cfg show`
  command.
- Improved efficiency of the `standalone cfg` command by reading the current
  configuration before attempting to apply a new one.
- Satellite API endpoints used when the TLS key/cert parameters are defined.
- Satellite API servers used for LN gossip and Bitcoin Source code messages.
- Satellite API SSE channel subscribed by the demo-rx application for LN
  gossip and Bitcoin Source code messages.

### Fixed
- Graceful exiting when interrupted at a prompt to create a GPG passphrase or
  keyring.
- TBS driver compilation failing on RPi OS Bullseye due to disabled SAA7146.
- Flat panel and Sat-IP antenna/receiver options on the configuration menu
  after C-band satellite selection.
- Standalone demodulator configuration not stopping on SNMP error.
- Error catching on POST HTTP requests reporting the receiver status.
- Pulling of media build repo on TBS driver build from a preexisting directory.

### Removed
- `--gossip` and `--btc-src` options from the `api demo-rx` application.

## 0.4.4

Release Date: 2022-05-31

### Added
- Option `--freq-corr` on the `sat-ip` and `standalone cfg` commands for tuning
  with a fixed frequency offset correction.

### Changed
- Downlink frequencies used in the T11N Africa and Europe regions.

## 0.4.3

Release Date: 2022-05-13

### Added
- Option to change the API listener download directory.
- Option to select the regions over which an API order is broadcast.

### Fixed
- Parsing of Novra S400 lock status and NaN metrics read via SNMP.

## 0.4.2

Release Date: 2022-01-06

### Added
- Support for the TBS 5520SE USB receiver.
- Support for the TBS drivers installation on Raspberry Pi OS.
- Fallback command for static IP configuration via `ip addr` in the absence of
  a supported system-specific network configuration utility.
- Definition of the starting RTL-SDR LNA and IF gains on the Gqrx configuration
  file.
- Verification of a matching receiver type on the local configuration file
  before launching receiver commands.
- Support for filtering of orders by region on the API demo-rx app.
- Support for non-rate-limited transmissions on the API demo-rx app.
- Support for the new Satellite API order state (confirming) on the sender app.

### Fixed
- Eventual blocking of Linux USB receiver due to a full stdout pipe.
- Non-root configuration of the /etc/network/interface file when the
  interfaces.d sources are not enabled.

## 0.4.1

Release Date: 2021-11-12

### Added
- Storage of the standalone receiver's IP address in the user's config file.
- Option `--ssdp-net-if` on the Sat-IP client to define the network interface
  for sending SSDP discovery packets.
- `make buildx-push` command to build Docker images for amd64 and arm64 using
  buildx.

### Changed
- Rename the Docker image from `blocksat-host` to `satellite`.

### Fixed
- Handling of empty Sat-IP frontend status responses.
- `snmpset` definitions printed by the `standalone cfg` command in dry run.
- Handling of invalid SSDP discovery replies received by the Sat-IP client.
- Reading of empty cache files such as the `.update` file with CLI update info.
- Handling of keyboard interrupts when waiting on user input.
- Catching of errors on the frontend status requests sent to the Sat-IP server.
- Success verification on the initial Sat-IP client login.

## 0.4.0

Release Date: 2021-09-10

### Added
- Support for the new Satellite Monitoring API, through which users can opt-in
  to report their receiver performance metrics using option `--report`.
- Support for the installation of software dependencies on Debian and Raspbian.
- Dry-run option (`--dry-run`) on the following subcommands: `firewall`, `rp`,
  `standalone config`, `usb config`, and `usb remove`.
- Option `--report-passphrase` to enable scripted runs while using option
  `--report`.
- Validation and automatic upgrade of the Sat-IP server firmware version on
  `sat-ip` startup.
- Option to disable the Sat-IP frontend monitoring for compatibility with old
  Sat-IP server firmware.
- Option to ignore errors on the tsp HTTP plugin used by the `sat-ip` command.

### Changed
- `sudo` requirement of subcommands `standalone config`, `usb config`, and `usb
  remove`. These can now be executed both by root and non-root users. Running
  them as a non-root user now applies the changes instead of performing a dry
  run.

### Fixed
- Permissions of the GPG home directory created via the `api config` command and
  other unnecessary warnings during the keyring creation process.
- API order state wait loop potentially stuck until timeout after an API message
  transmission.
- Incompatibility when parsing USB receiver logs on non-English terminal locale.
- TBS5927 driver installation giving up on Fedora upon a version mismatch
  between the kernel and the `kernel-headers` package obtained via the `dnf`.
- Logging of Sat-IP frontend metrics from other clients simultaneously connected
  to the same Sat-IP server.

## 0.3.2

Release Date: 2021-04-28

### Added
- Support for the Blockstream Satellite Base Station device and Sat-IP receivers
  in general.
- Option `--ts-file` to record MPEG TS file via the `sdr` or `sat-ip`
  applications.
- Option `--ts-dump` to dump the contents of MPEG TS packets received via the
  `sdr` or `sat-ip` applications.

### Changed
- Command-line options related to MPEG TS and the `tsp` application:
    - Options `--buffer-size-mb`, `--max-flushed-packets`, and
      `--max-input-packets` were prefixed with `--tsp`.
    - Option `--monitor-bitrate` was renamed to `--ts-monitor-bitrate`.
	- Option `--bitrate-period` was replaced by an optional argument of option
      `--ts-monitor-bitrate`.
	- Option `-a/--analyze` was renamed to `--ts-analysis`.
	- Option `--analyze-file` was replaced by an optional argument of option
      `--ts-analysis`.
	- Option `--monitor-ts` was renamed to `--ts-monitor-sequence`.

## 0.3.1

Release Date: 2021-03-16

### Added
- Configuration of the Novra S400 (pro kit receiver) via SNMP through command
  `blocksat-cli standalone cfg`.
- Command `blocksat-cli cfg show` to show the local configuration.
- Command `blocksat-cli cfg channel` to regenerate the channels configuration
  file used by Linux USB receivers.

### Changed
- CLI configuration and instructions to use DVB-S2 in CCM mode with the QPSK 3/5
  MODCOD instead of VCM mode with the QPSK 1/2 and 8PSK 2/3 MODCODs.
- Set of MPEG TS PIDs to 32 only instead of using two PIDs (32 and 33) for VCM.
- Option `-m/--modcod` on the SDR application, now defined explicitly (e.g., as
  *qpsk3/5*) instead of through the former "low/high" aliases.
- Default `udpmulticastloginterval` defined on the *bitcoin.conf* files
  generated by command `blocksat-cli btc`.

### Removed
- Option `-c/--channel` from the SDR application.

### Fixed
- Potential unhandled crashing of the SDR app's monitoring thread due to invalid
  monitoring options.
- Network interface name used on the `api listen` command for USB receivers. Use
  the DVB-S2 adapter number cached the local JSON configuration file.
- Timestamps produced by the monitoring handler always based on UTC time despite
  the absence of option `--utc`.
- USB receiver's dvbv5-zap monitoring mode that was not displaying results
  correctly.
- Unused `--chan-conf` option on the command `blocksat-cli cfg`.

## 0.3.0

Release Date: 2021-01-27

### Added
- Integrate API apps into the CLI. Support API message transmission, reception,
  and the demo-rx app directly from `blocksat-cli` commands (`api send`, `api
  listen`, and `api demo-rx`).
- Forward error correction (FEC) support on API apps. Apply FEC-encoding on API
  messages transmitted through the `api send` command and decode on the
  receiving end on command `api listen`. Detect a FEC-encoded message
  automatically on the API listener application.
- QR code for Lightning invoices displayed on API transmissions.
- Auto-cleaning of unfinished API messages on the API listener app.
- Parsing of user bid input on API send/bump applications.
- Option `--stdout` on the API listener app to serialize the received API
  messages to stdout.
- Option `--no-save` on the API listener app to disable the saving of decoded
  API messages into the download directory.
- Option `--exec` on the API listener app to execute an arbitrary command for
  every successfully decrypted API message.
- Option `--sender` on the API listener app to filter digitally signed messages
  from a selected sender.
- Option `--channel` on the API listener and demo-rx apps to support
  multiplexing and filtering of independent API packet streams.
- Support for clearsigning and verification of plaintext messages.
- Wait mechanism on the API sender app to wait until the API message is
  successfully transmitted over satellite, optionally disabled using
  command-line argument `--no-wait`.
- Option `--invoice-exec` on the API sender app to execute an arbitrary command
  with the Lightning invoice string.
- Handling of repeated downloads via the API listener app. Append number to file
  if the contents differ and avoid duplicate saving if the contents match.
- Local caching of CLI updates. Instead of checking Python `pip` every time,
  check once a day and cache the results on a file within the `.blocksat`
  directory.
- Universal logging format for all the supported types of receivers (USB,
  standalone, and SDR). Implement unique log parsing on each receiver module and
  feed the parsed results into a common monitoring class, which prints to the
  console in a standard format.
- Command `blocksat-cli standalone monitor` to monitor the Novra S400
  (standalone) receiver through SNMP.
- Monitoring of the SDR receiver status metrics using leandvb's `--fd-info`
  mechanism.
- Option `--monitoring-server`, which launches an HTTP server to respond the
  JSON-formatted receiver status to any remote requester.
- Option `--report` to proactively report the receiver status over HTTP to a
  specified destination server.
- Alternative option on the SDR app to define the logical channel that the
  receiver tunes to. The new option is named `--channel` and is mutually
  exclusive with the pre-existing `--modcod` option.
- Add option `--gossip` on the API listener and demo-rx apps to support the
  reception of Lightning gossip snapshots transported via the satellite API.
- Support specification of USB DVB-S2 adapter by model name on `blocksat-cli
  usb` command.
- Support for non-interactive dvbnet interface removal.
- Support for firewall configuration based on firewalld.


### Changed

- The procedure for creating the GPG keyring used for API transmission and
  reception. Create it on the `.blocksat` directory and import Blockstream
  Satellite's public key by default. Run this procedure manually through command
  `api config` or automatically from the `send`/`listen` commands.
- The mechanism to auto-discover CLI updates via pip. Instead of running only
  from the dependencies module (and associated commands), the new scheme runs
  from any CLI command.
- The log format adopted by the `blocksat-cli usb launch` and `blocksat-cli sdr`
  commands, now in the new standard format.
- The log analyzer (plotting) script for compatibility with the new standard
  logging format.
- Antenna pointing documentation in compliance with the new logging format.
- The bid suggested for API transmissions. Following the update on API pricing,
  the suggested bid is now 1 msat/byte.
- The global minimum bid for API orders, which is now of 1000 msats.


### Removed
- The example API applications formerly directory `api/`. They are now part of
  the CLI as a Python subpackage on directory `blocksatcli/api/`.

### Fixed
- Demo-rx application crashing on a rollback of the sequence number adopted by
  the API server, which was previously affecting primarily a local test
  environment.
- Reading of IQ file on the SDR app. It was previously failing due to option
  `--inpipe`.
- Excessively large `bufsize` used on `recvfrom` call to receive packets via UDP
  socket on the API listener app.
- Dependency on package `perl-File-Copy-Recursive`, which was missing for the
  TBS driver build on fc33.
