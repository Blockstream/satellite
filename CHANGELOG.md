# Changelog

## [2.3.1]

Release Date: 2021-03-16

### Fixed
- Potential unhandled crashing of the SDR app's monitoring thread due to invalid
  monitoring options.
- Network interface name used on the `api listen` command for USB receivers. Use
  the DVB-S2 adapter number cached the local JSON configuration file.
- Timestamps produced by the monitoring handler always based on UTC time despite
  the absence of option `--utc`.

## [2.3.0]

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
