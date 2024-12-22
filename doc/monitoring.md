---
nav_order: 11
---

# Monitoring Server

While running your receiver, you can choose to report your receiver performance metrics to a Blockstream-hosted server, referred to as the *satellite monitoring server*. To do so, you must explicitly enable the reporting functionality. Then, the interface application (GUI or CLI) will periodically send reports over the Internet. By doing so, you will be helping us better plan and improve the satellite communications service and worldwide coverage.

With the GUI, the reporting functionality can be enabled on the Receiver tab, as shown below:

![GUI Report Option](img/gui_report_opt.png?raw=true)

With the CLI, the `--report` option can be appended to all supported receiver types, as follows:

TBS 5927 or 5520SE USB receiver:

```
blocksat-cli usb launch --report
```

Novra S400 standalone receiver:

```
blocksat-cli standalone monitor --report
```

SDR receiver:

```
blocksat-cli sdr --report
```

Sat-IP receiver:

```
blocksat-cli sat-ip --report
```

When enabling this functionality for the first time, an initial registration procedure will be executed to confirm your satellite receiver is functional. The procedure involves a two-factor authentication mechanism over satellite, described next.

## Authentication over Satellite

The registration procedure is as illustrated below and involves the following steps:

![Two-factor authentication procedure](img/monitoring-api-authentication.png)

1. The interface application (CLI or GUI) sends a registration request over the internet to the monitoring server. The request includes the user's public [GPG key used for API apps](api.md#encryption-keys).
2. The monitoring server generates a random verification code, encrypts it using the user's public key, and sends the encrypted verification code to the [Satellite API](api.md) for transmission over satellite.
3. The satellite API relays the message over the satellite serving the user.
4. The interface application receives the encrypted verification code, decrypts it, and confirms the verification code back to the monitoring server.

In the end, this process confirms that the user owns the private key associated with the informed public key, as this is a prerequisite to decrypting the verification code. Furthermore, it verifies the user is running a functional satellite receiver, given that the encrypted verification code is sent exclusively over the satellite network.

## Authenticated Reports

After the initial registration, the periodic reporting of the receiver status becomes enabled. Then, for every reported metric set, a [detached GPG signature](https://www.gnupg.org/gph/en/manual/x135.html) is sent so that the monitoring server can validate its authenticity.

Since version 0.4.5, reports can also be authenticated using a lightweight password-based mechanism as an alternative to GPG detached signatures. The password is created automatically and saved in ciphertext (encrypted) on your local configuration directory (`~/.blocksat/` by default). From then on, the password is used every time you launch the receiver with reporting enabled.

Note that because the interface application (CLI or GUI) needs to decrypt the local password before starting to report, every time you launch the receiver with reporting enabled, the application will ask for the passphrase to your local private GPG key. This passphrase is not cached, so you must always provide it. Alternatively, with the CLI, you can specify it directly using the command-line option `--report-passphrase`.