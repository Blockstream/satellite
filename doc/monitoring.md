---
nav_order: 11
---

# Monitoring Server

As of version 0.3.2 of the Blocksat CLI, it is now possible to report receiver
performance metrics back to a Blockstream-hosted server, referred to as the
*satellite monitoring server*. To do so, you must explicitly enable the
reporting functionality, which activates periodic reports sent automatically by
the CLI over the internet to the monitoring server. Ultimately, the reported
data is used to better plan and improve the worldwide satellite communications
service and coverage.

If you would like to help us improve the service by reporting your receiver
performance, you can do so by appending the command-line option `--report` when
launching the receiver, as follows:

TBS 5927 USB receiver:
```
blocksat-cli usb launch --report
```

Novra S400 standalone receiver (see the [S400 monitoring instructions](s400.md#monitoring)):
```
blocksat-cli standalone monitor --report
```

SDR receiver:
```
blocksat-cli sdr --report
```

> Note option `--report` was added in blocksat-cli version v0.3.1. Refer to the
> [upgrade instructions](quick-reference.md#cli-installation-and-upgrade) if
> necessary.

When using this option for the first time, the CLI explains the reporting
process and runs an initial registration procedure to confirm you are running a
functional satellite receiver. The latter involves a two-factor authentication
mechanism over satellite, described next.

## Authentication over Satellite

The registration procedure is as illustrated below and involves the following
steps:

![Two-factor authentication procedure](img/monitoring-api-authentication.png)

1. The CLI (blocksat-cli) sends a registration request over the internet to the
   monitoring server. The request includes the user's public [GPG key used for
   API apps](api.md#encryption-keys).
2. The monitoring server generates a random verification code, encrypts it using
   the user's public key, and sends the encrypted verification code to the
   [Satellite API](api.md) for transmission over satellite.
3. The satellite API relays the message over the satellite links worldwide.
4. The CLI (blocksat-cli) receives the encrypted verification code, decrypts it,
   and confirms the verification code back to the monitoring server.

In the end, this process confirms that the user owns the private key associated
with the informed public key, as this is a pre-requisite to decrypt the
verification code. Furthermore, it verifies the user is running a functional
satellite receiver, given that the encrypted verification code is sent
exclusively over the satellite network.

## Signed Reports

After the initial registration, the CLI enables periodic reporting of the
receiver status. While doing so, it automatically appends a [detached GPG
signature](https://www.gnupg.org/gph/en/manual/x135.html) to every set of
metrics to be reported. With that, the monitoring server validates the
authenticity of each report.

Note that because reports are GPG-signed, every time you launch the receiver
with option `--report`, the CLI will ask for the passphrase to the private GPG
key required for signing. You can observe the underlying process in action by
running the CLI in debug mode. For example, with the USB receiver, you can
execute the following command:

```
blocksat-cli --debug usb launch --report --log-scrolling
```
