# Satellite API

The [Blockstream Satellite API](https://blockstream.com/satellite-api/) provides
developers with an easy-to-use RESTful API that can be used to broadcast
messages globally using the Blockstream Satellite network.

As illustrated in the diagram below, the process starts with a sender
application, which requests the transmission of a particular file or text
message. This transmission order gets queued up in the API server. Once the
order is paid with [Bitcoin
Lightning](https://github.com/ElementsProject/lightning), the API server sends
the message to the Blockstream Satellite Teleport (ground station). From there,
the message is broadcast globally through the Blockstream Satellite network.

![Blockstream Satellite API Architecture](../doc/img/api_architecture.png?raw=true "Blockstream Satellite API Architecture")

The `blocksat-cli` command-line interface (CLI) provides a range of commands for
the interaction with the Satellite API. This guide clarifies these commands.

> To install the CLI, please refer to [the installation
> instructions](quick-reference.md#1-cli-installation-and-upgrade).

> The API support on the CLI is available starting from version `0.3.0`. Please
> refer to instructions regarding [how to check and upgrade your CLI
> version](quick-reference.md#1-cli-installation-and-upgrade).

For details regarding the RESTful API, please refer to the [Satellite API's
repository](https://github.com/Blockstream/satellite-api).

<!-- markdown-toc start - Don't edit this section. Run M-x markdown-toc-generate-toc again -->
**Table of Contents**

- [Satellite API](#satellite-api)
    - [Encryption Keys](#encryption-keys)
    - [Satellite API Transmission](#satellite-api-transmission)
        - [Choosing the Recipient](#choosing-the-recipient)
        - [Signing the Messages](#signing-the-messages)
    - [Satellite API Reception](#satellite-api-reception)
    - [Demo Receiver](#demo-receiver)
    - [Further Information](#further-information)
        - [Lightning Wallets](#lightning-wallets)
        - [Plaintext Mode](#plaintext-mode)
        - [Receiving Messages Sent from the Browser](#receiving-messages-sent-from-the-browser)
        - [Reliable Transmissions](#reliable-transmissions)
        - [Running on Testnet](#running-on-testnet)
        - [Bump and delete API orders](#bump-and-delete-api-orders)
        - [Password-protected GPG keyring](#password-protected-gpg-keyring)

<!-- markdown-toc end -->


## Encryption Keys

To start, we recommend setting up a
[GPG](https://en.wikipedia.org/wiki/GNU_Privacy_Guard) key pair for the
encryption of messages sent through the satellite API. To do so, run:

```
blocksat-cli api cfg
```

After filling the requested information, this command will generate the key pair
(public and private keys) and create a new keyring, by default, located at the
`~/.blocksat/` directory.

## Satellite API Transmission

To send a text message over the Blockstream Satellite network, run:

```
blocksat-cli api send
```

Alternatively, you can send a file by running:

```
blocksat-cli api send -f [file]
```

where `[file]` should be replaced with the path to the file.

Subsequently, get the *Lightning Invoice Number* printed on the console or the
QR code and pay it using Bitcoin Lightning (refer to the list of [Lightning
wallet apps](#lightning-wallets)).

By default, the above commands encrypt your message or file using the GPG key
you set up [in the beginning](#encryption-keys). With that, only you (i.e., the
owner of the private key) can decrypt the message on reception (see [GPG's
manual](https://www.gnupg.org/gph/en/manual/x110.html) for further
information). Other users listening for messages broadcast over the Blockstream
Satellite network will still receive your encrypted message. However, they
**will not** be able to decrypt it.

### Choosing the Recipient

You can also define a specific recipient for your transmission. To do so, use
argument `-r`, as follows:

```
blocksat-cli api send -r [fingerprint]
```

where `[fingerprint]` is the [public key
fingerprint](https://en.wikipedia.org/wiki/Public_key_fingerprint) corresponding
to the target recipient. In other words, the *fingerprint* defines who is going
to be able to decrypt the message.

In case you want to skip the validation of the recipient's public key and assume
it is fully trusted, you can use argument `--trust`. For example:

```
blocksat-cli api send -r [fingerprint] --trust
```

These commands assume that the recipient's public key is available on the local
GPG keyring. Thus, you need to [import the public
key](https://www.gnupg.org/gph/en/manual/x56.html) into the keyring located at
`~/.blocksat/.gnupg`. Assuming the recipient has shared its *public key* with
you on a file named `recipient.gpg`, you can do so using:

```
gpg --import recipent.gpg --homedir $HOME/.blocksat/.gnupg
```

### Signing the Messages

You can also [digitally sign](https://www.gnupg.org/gph/en/manual/x135.html) a
message so that the recipient can verify that it was really generated by you and
that it was not altered in any way. To do so, use argument `--sign`. For
example:

```
blocksat-cli api send --sign
```

By default, messages will be signed using the default private key from your
keyring. You can also define the specific key to use when signing, as follows:

```
blocksat-cli api send --sign --sign-key [fingerprint]
```

where `[fingerprint]` is the fingerprint of the private key you wish to use for
signing.

## Satellite API Reception

To receive messages sent over satellite through the Satellite API, first of all,
you need to have [your satellite receiver](../README.md) running. If you do not
have a [real
receiver](https://store.blockstream.com/product-category/satellite_kits/), you
can experiment with the [demo receiver](#demo-receiver) explained in the sequel.

The satellite receiver continuously receives Bitcoin data and API messages
broadcast over satellite. To listen for the API messages, run:

```
blocksat-cli api listen
```

Once an API message is received, this application first tries to decrypt it. If
it succeeds, it then validates the integrity of the data and saves the final
result into the download directory (by default at `~/.blocksat/api/downloads/`).

Note that the incoming data stream multiplexes transmissions from all users of
the Satellite API. Hence, the application is expected to fail decryption in most
cases except when it finds a message it is supposed to receive.

Also, by default, this app saves both files and text messages into the download
directory. You can also configure it to print a received (successfully
decrypted) text message to the console by running with:

```
blocksat-cli api listen --echo
```

## Demo Receiver

The demo receiver application imitates the output of a real [Blockstream
Satellite
receiver](https://store.blockstream.com/product-category/satellite_kits/). It
outputs UDP packets containing the API messages, just like the regular receiver
does. The difference is that it fetches these messages directly through the
internet, rather than receiving via satellite.

You can run the demo receiver with:
```
blocksat-cli api demo-rx
```

Then, on another terminal session, you can listen for API messages coming from
the demo receiver by running:

```
blocksat-cli api listen --demo
```

> NOTE: the demo receiver sends packets with API data to the loopback
> interface. When the listener application is launched with option `--demo`, it
> will correspondingly listen to the loopback interface.

## Further Information

### Lightning Wallets

Here are some options of handy Lightning Wallets that can be used to pay for API
transmissions:

- [Bluewallet (iOS and Android)](https://bluewallet.io/lightning/)
- [Zap (iOS, Android, Windows, Mac, and Linux)](https://zaphq.io)
- [Breez (iOS and Android - in Beta)](https://breez.technology)

### Plaintext Mode

In addition to encrypted messages, you can also send and receive plaintext
messages, i.e., unencrypted messages. In this case, all users listening to
Satellite API messages will be able to see your message. Correspondingly, you
can receive all messages sent by other users in plaintext format.

To send a plaintext message, run:

```
blocksat-cli api send --plaintext
```

To receive plaintext messages, run:

```
blocksat-cli api listen --plaintext
```

In this case, please **be aware** that **all** API transmissions will be saved
to the download directory. In contrast, in normal mode (with encryption), the
listener application only saves the messages addressed to you (i.e., the
messages you can decrypt).

### Receiving Messages Sent from the Browser

If you want to receive a file uploaded directly on the [Satellite Queue
page](https://blockstream.com/satellite-queue/), from the browser, run the API
listener application as follows:

```
blocksat-cli api listen --plaintext --save-raw
```

The rationale is that files uploaded to the [Satellite
Queue](https://blockstream.com/satellite-queue/) are sent in plaintext (i.e.,
without encryption). Furthermore, the browser transmission tool does not
encapsulate the data in the same way as the CLI sender tool (i.e., command
`blocksat-cli api send`). Argument `--save-raw` accounts for this missing
encapsulation.

The CLI can also reproduce the message transmission format used by the
[Satellite Queue](https://blockstream.com/satellite-queue/) tool on the
browser. To do so, run the sender application as follows:

```
blocksat-cli api send --plaintext --send-raw
```

### Reliable Transmissions

The API messages sent over satellite are not guaranteed to be received by all
satellite receivers. Each receiver experiences a unique reception quality,
depending primarily on its location, weather conditions, and the adopted
receiver hardware. When the signal quality is low, it becomes more likely for
the receiver to fail on the reception of packets.

One way to increase the chances of successful reception is to use forward error
correction (FEC). In essence, FEC adds redundancy to the transmit data so that
receivers can recover the original message even if some parts are missing. This
is the mechanism that is used, for instance, in Bitcoin Satellite ([see further
details in the project's
Wiki](https://github.com/Blockstream/bitcoinsatellite/wiki#forward-error-correction-fec)).

To send an API message using FEC encoding, run:

```
blocksat-cli api send --fec
```

The `api listen` command detects and decodes FEC-encoded messages automatically.

In general, the higher the number of extra (redundant) pieces of data sent over
satellite, the better the protection to data loss over the satellite link.  The
user can tune this parameter using the command-line argument
`--fec-overhead`. By default, this argument is `0.1` (equivalent to 10%), such
that, for a message that originally occupies 10 packets, the application sends
one extra packet.

### Running on Testnet

The API commands described thus far interact with the API server that handles
live broadcasting via the Blockstream Satellite network. This server operates on
Bitcoin's Mainnet network and, therefore, the payment requires actual bitcoins.

Nevertheless, there is an alternative API server that operates on the Bitcoin
[Testnet network](https://en.bitcoin.it/wiki/Testnet). You can interact with
this Testnet server using argument `--net test`. For example:

```
blocksat-cli api --net test send
```

However, note that the Testnet server does not transmit data through the
satellite network. It only broadcasts the data to clients that are connected
directly to the server through the internet. Thus, you need to use the [demo
receiver](#demo-receiver) to receive API messages sent through the Testnet
server.

In this case, run the demo receiver as follows:

```
blocksat-cli api --net test demo-rx
```

### Bump and delete API orders

When users send messages to the Satellite API, these messages first go into the
[Satellite Queue](https://blockstream.com/satellite-queue/). From there, the
satellite transmitter serves the transmission orders with the highest bid (per
byte) first.

If your message is still waiting for transmission due to other messages with a
higher bid per byte, you can bump your bid by running:

```
blocksat-cli api bump
```

You can also delete (cancel) a transmission order by running:

```
blocksat-cli api del
```

Both of these commands will ask for the UUID and the authorization token of the
order. These were printed to the console when the message was first sent.

### Password-protected GPG keyring

By default, it is assumed that the private key in your keyring is
password-protected. In case you want to use a private key that is **not**
password-protected for signing a transmission or decrypting incoming messages,
run the apps with option `--no-password`, as follows:

```
blocksat-cli api send --sign --no-password
```

```
blocksat-cli api listen --no-password
```

