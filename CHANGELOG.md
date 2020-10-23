# Changelog

## [2.3.0] - 2020-10-26
### Added
- Integrate API apps into the CLI. Support API message transmission, reception,
  and the demo-rx app directly from `blocksat-cli` commands (`api send`, `api
  listen`, and `api demo-rx`).
- QR code for Lightning invoices displayed on API transmissions.
- Auto-cleaning of unfinished API messages on the API listener app.
- Parsing of user bid input on API send/bump applications.
- Option `--stdout` on the API listener app to serialize the received API
  messages to stdout.
- Option `--exec` on the API listener app to execute an arbitrary command for
  every received API message.
- Wait mechanism on API message transmission (`api send`) app to wait until the
  API message is successfully transmitted over satellite.
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
  receiver tunes to. The new option is named `--chanel` and is mutually
  exclusive with the pre-existing `--modcod` option.


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


### Removed
- The example API applications formerly directory `api/`. They are now part of
  the CLI as a Python subpackage on directory `blocksatcli/api/`.

### Fixed
- Demo-rx application crashing on a rollback of the sequence number adopted by
  the API server, which was previously affecting primarily a local test
  environment.
- Reading of IQ file on the SDR app. It was previously failing due to option
  `--inpipe`.
