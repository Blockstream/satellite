# Example Applications for Data Transmission via API

This directory contains example scripts for sending and receiving data through
the Blockstream Satellite API. The first example illustrates how a user can
create its own user/application-specific protocol for sending data through the
API. In particular, it illustrates a case in which data is transmitted alongside
user-defined metadata fields. The second example, in turn, illustrates the
transmission of a file to the Satellite API server. Lastly, the third example
illustrates how one can simulate the output of the Blockstream Satellite
receiver while fetching data directly from the Satellite API via the Internet,
rather than receiving data via the satellite link.

![Blockstream Satellite API Architecture](../../doc/img/api_architecture.png?raw=true "Blockstream Satellite API Architecture")

<!-- markdown-toc start - Don't edit this section. Run M-x markdown-toc-generate-toc again -->
## Contents

- [Environment](#environment)
- [Example 1: Sending data in a user-defined protocol](#example-1-sending-data-in-a-user-defined-protocol)
- [Example 2: Sending files directly](#example-2-sending-files-directly)
- [Example 3: Testing the API while receiving data directly via Internet](#example-3-testing-the-api-while-receiving-data-directly-via-internet)
- [Further Information](#further-information)
    - [Bump and delete API orders](#bump-and-delete-api-orders)
    - [Encryption and signature options](#encryption-and-signature-options)
        - [Choosing recipient](#choosing-recipient)
        - [Digital signature](#digital-signature)
        - [Password-protected GPG keyring](#password-protected-gpg-keyring)
    - [Text messages](#text-messages)

<!-- markdown-toc end -->

## Environment

The first step in order to use the examples that follow is to prepare the
environment.

For Python, create a virtual environment with the packages listed in the
`requirements.txt` file of this directory. For example, if using
*virtualenvwrapper*, run the following:

```
mkvirtualenv --python=`which python3` -r requirements.txt blocksat-api
```

Note this virtual environment will be required for all example scripts described
in this page. Hence, once you open a new terminal session in order to launch one
of the example applications, ensure to activate the environment again. For
example, assuming you are using `virtualenvwrapper`, run the following on every
new terminal session:

 ```
 workon blocksat-api
 ```

> NOTE: for a quick introduction to *virtualenvwrapper* visit their
> [introduction
> page](https://virtualenvwrapper.readthedocs.io/en/latest/index.html#introduction).
> Also, after installing *virtualenvwrapper*, make sure to follow the shell
> startup instructions on [their
> documentation](https://virtualenvwrapper.readthedocs.io/en/latest/install.html#shell-startup-file).

Next, generate a key pair for encryption (prior to transmission) and decryption
(on reception). You can do so by running the helper script below:

```
./generate_keys.py
```

Note that by default this will create the `.gnupg` directory in the local
(`examples`) directory. This `.gnupg` directory is where the GPG public and
secret keyrings are stored.

If you could not use the above helper script successfully, or if you prefer, you
can also generate keys on a local `.gnupg` directory with:

```
mkdir .gnupg
gpg --full-generate-key --homedir .gnupg
```

> NOTE: you may need to use an absolute path for the `--homedir` argument above.

Alternatively, you can use your own pre-existing GPG keys.

## Example 1: Sending data in a user-defined protocol

This example uses two scripts of the `examples` directory:

1. API data sender
2. API data reader

Also, it requires a running Blocksat receiver. If you don't have a real Blocksat
receiver setup, you can use the demo receiver explained in [Example
3](#example-3-receiving-data-from-the-api-sandbox).

The *API data sender* application by default places the user-specified file into
a data structure and then sends the structure to the API. The structure carries
the file name as a string and also contains a CRC32 checksum that can be used
for data integrity checking on the receiver side. The entire structure is first
encrypted using GnuPG and then posted via HTTPS to the Blockstream Satellite API
server, which in turn broadcasts the message over the satellite network.

Meanwhile, the *API data reader* application waits for data received by the
Blockstream Satellite receiver. It continuously listens for messages on the
specific multicast address that is used for API packets. Once an API message is
received, this application decrypts the message, validates the integrity of the
data and then saves the unpacked files. The integrity validation is done by
computing the CRC32 checksum of the received data and comparing the latter with
the checksum that is advertised on the header of the incoming data
structure. Ultimately, the incoming file is saved in the `downloads/` folder
with the name that is given in the header.

To get started, first ensure that you are using the correct Python virtual
environment. If using `virtualenvwrapper`, run:

```
workon blocksat-api
```

Then, launch the API data reader as follows:

```
./api_data_reader.py -i ifname
```

where `ifname` is the name of the network interface that is connected to your
Blockstream Satellite receiver.

> In case you are using a [USB receiver](../../doc/tbs.md), the interface
> will typically be named `dvb0_0` and `dvb0_1`, although the numbers may
> occasionally vary. Check `ifconfig` or `ip a`.
>
> In case you are using an [SDR-based receiver](../../sdr.md), the interface
> will be the loopback interface, typically named `lo` in the operating system.

Next, send some data. On another terminal session, activate the Python virtual
environment once again (e.g. with `workon blocksat-api`). Then, post a file of
your choice for transmission via Blockstream Satellite:

```
./api_data_sender.py -f filename
```

where `filename` is the path to the file you want to send.

>Note: the script will encrypt the data structure prior to posting to the API,
>so there is no need to encrypt the data before calling it.

Subsequently, get the *Lightning Invoice Number* that was printed by the API
data sender on the console and pay.

By default, the above command sends the transmission request to the API server
that handles live broadcasting via the Blockstream Satellite network. This
server operates in Mainnet and thus the payment requires actual
bitcoins. However, for developers/testers/experimenters, there is an alternative
API server that operates in Testnet. You can send the transmission request to
the Testnet server, using:

```
./api_data_sender.py --net test -f filename
```

Do note however that the Testnet server does not transmit data through the
satellite network. It only broadcasts the data to clients that are connected
directly to the server through the Internet. Hence, the way to receive Testnet
data is with the demo receiver that is explained in [Example
3](#example-3-receiving-data-from-the-api-sandbox)).

Once the API server effectively transmits your data and your satellite receiver
gets the transmission, the data is expected to appear at the API data reader
application. In the end, the received file will be saved in the `downloads`
folder.

For further understanding, you can compare the received file with the one that
was sent. For example, by running `md5sum` on both files. Also, you can test
what happens when trying to decrypt with wrong keys. For example, generate
another key pair by creating a second GnuPG home directory:

```
./generate_keys.py --gnupghome .gnupg-alt
```

Then, send the file using one GnuPG home and try to decrypt using another. For
example, send with the alternative GnuPG home:

```
./api_data_sender.py -f filename --gnupghome .gnupg-alt
```

Assuming the API data reader is still running with the default GnuPG home
directory, you should expect decryption to fail in this case.

Note that, the incoming data stream multiplexes transmissions from all users of
the Satellite API. Hence, the application is expected to fail decryption in most
cases, except when it finds a transmission that it is actually a recipient of.

## Example 2: Sending files directly

In this example, the goal is to send a file directly to the API, without placing
it on any user-specific protocol.

The same two scripts of [Example
1](#example-1-sending-data-in-a-user-defined-protocol) are used, except for
different command-line arguments:

1. API data sender
2. API data reader

In this case, launch the API data reader as follows:

```
./api_data_reader.py -i ifname --save-raw
```

where `ifname` is the name of the network interface that is connected to your
Blockstream Satellite receiver.

> In case you are using a [USB receiver](../../doc/tbs.md), the interface
> will typically be named `dvb0_0` and `dvb0_1`, although the numbers may
> occasionally vary. Check `ifconfig` or `ip a`.
>
> In case you are using an [SDR-based receiver](../../sdr.md), the interface
> will be the loopback interface, typically named `lo` in the operating system.

Next, send some data using:

```
./api_data_sender.py -f filename --send-raw
```

Note that the `--send-raw` flag means that the data is sent as it is, without
any additional protocol framing.

Again, to use the Testnet server instead, run:

```
./api_data_sender.py --net test -f filename --send-raw
```

> As mentioned earlier, when using the Testnet server, since the message is only
> sent over the Internet (and not over satellite), the demo receiver from
> [Example 3](#example-3-receiving-data-from-the-api-sandbox) must be used.

Once the satellite receiver interface receives the data, the API data reader app
will correspondingly receive it and retrieve the transmitted file.

Note that, just like in Example 1, this example also handles encryption
internally. That is, you can point to a non-encrypted file and the data sender
will encrypt it internally before posting to the API server. The reader will
then decrypt the data.

The command-line option `--save-raw` is also useful when sending a file directly
via the [form in the API web page](https://blockstream.com/satellite-queue/). In
this scenario, the file can be retrieved by running the API data reader as
above, with `--save-raw` flag. The only difference is that in this case you will
need to encrypt the file offline, before uploading to the form of the API web
page. This is because the web page does not encrypt your data before posting for
transmission, while the *API data reader* application does assume that the
incoming data is encrypted and correspondingly tries to decrypt it using the
keys that are available in the local GnupG home directory.

To encrypt a file offline, you can run for example:

```
gpg --encrypt --recipient pub_key_id_or_email filename
```

where `pub_key_id_or_email` can be either the public key ID or the e-mail
address of the target recipient.

> NOTE: In case the recipient information is located in the GnuPG home directory
> that was created using `./generate_keys.py`, add `--homedir .gnupg` to the
> above `gpg` command.

Alternatively, you can run the API data reader in "plaintext mode". This will
allow reception of plaintext files uploaded directly via the [API
website](https://blockstream.com/satellite-queue/), or any other plaintext
transmission broadcast via the satellite network. However, please **be aware**
that in this case **all** API transmissions will be saved to the `downloads`
folder, rather than solely the ones that can be decrypted with the GPG keys you
have. To run in this mode, execute:

```
./api_data_reader.py -i ifname --plaintext
```

## Example 3: Testing the API while receiving data directly via Internet

This example illustrates the scenario in which instead of receiving data with
the actual Blockstream Satellite receiver, you fetch data directly from the API
server through the Internet.

Now, you will need three scripts from the `examples` directory:

1. API data sender
2. API data reader
3. Demo receiver

You can choose to use the API data sender and API data reader either as in
[Example 1](#example-1-sending-data-in-a-user-defined-protocol) or as in
[Example 2](#example-2-sending-files). The important difference here is that the
API data reader will read data fed by the *demo receiver*, rather than the
actual Blockstream Satellite receiver.

Start by activating the `blocksat-api` Python virtual environment. Then, run the
demo receiver:

```
./demo-rx.py
```

This application will monitor [server-sent
events](../README.md#get-subscribechannels) that are generated by the API server
whenever a new message is sent by a user. Then it will post the data towards the
same multicast address and UDP port that the Blockstream Satellite receiver
normally would. By default, this is the address `239.0.0.2:4433`, which in turn
the API data reader listens to.

Next, assuming for the explanation that the approach of [Example
1](#example-1-sending-data-in-a-user-defined-protocol) is adopted, you can run
the API data reader with:

```
./api_data_reader.py --demo
```

> NOTE: the Demo Rx application will send the UDP datagrams containing API data
> over the loopback interface. When the API data reader is launched with option
> `--demo`, it will correspondingly listen to the loopback interface.

Finally, send a file with the API data sender application and wait until it pops
in the data reader.

```
./api_data_sender.py -f filename
```

If instead of sending to the Mainnet server, the goal is to send to the Testnet
server, run:

```
./api_data_sender.py --net test -f filename
```

In this case, the Demo receiver also needs to be listening to the Testnet
server. That is, it needs to be launched as follows:

```
./demo-rx.py --net test
```

## Further Information

### Encapsulation Format

User messages sent over the API are encapsulated over UDP/IPv4. The UDP
datagrams, in turn, are broadcast over the satellite network and received by the
Blockstream Satellite receivers.

The UDP datagrams are formatted as follows:

```
| UDP Header (8 bytes) | Blocksat Header (8 bytes) | User Message |
```

That is, within the UDP payload, there is an 8-byte header for auxiliary
Blocksat information, followed by the actual user message. The user message is
currently limited to 10 kB.

### Bump and delete API orders

The API data sender script also supports bumping and deletion of orders sent to
the API.

For bumping, you can run:

```
./api_data_sender.py --bump
```

To delete an order, run:

```
./api_data_sender.py --delete
```

Both of these commands will ask for the UUID and the authorization token of the
order. These were originally printed to the console by the API data sender, when
the latter was used to send the data to the API.

### Encryption and signature options

There are a few GPG options for the API data sender application that were not
explained above.

#### Choosing recipient

You can define the specific recipient of your encrypted API messages. To do so,
execute the sender app as follows:

```
./api_data_sender.py -f filename -r fingerprint
```

where fingerprint should be the public key fingerprint of the target recipient.

In case you want to skip validation of the recipient's public key and assume it
is fully trusted, you can run:

```
./api_data_sender.py -f filename -r fingerprint --trust
```

#### Digital signature

You can also digitally sign the transmitted messages. To do so, run the sender
app as follows:

```
./api_data_sender.py -f filename --sign
```

By default, messages will be signed using the default key from your keyring. You
can also define the specific key to use when signing, as follows:

```
./api_data_sender.py -f filename --sign --sign-key fingerprint
```

where fingerprint in this case is the fingerprint of the private key you wish to
use for signing.

#### Password-protected GPG keyring

By default it is assumed that the private key in your keyring is
password-protected. In case you want to use a private key that is **not**
password-protected for signing a transmission or decrypting incoming messages,
run the sender and reader apps with option `--no-password`, as follows:

```
./api_data_sender.py -f filename --sign --no-password
```

```
./api_data_reader.py --no-password
```

### Text messages

In addition to files, you can send text messages directly via command-line with
the sender app.

```
./api_data_sender.py --plaintext --send-raw -m "Hello world"
```


## Troubleshooting

1. **When running Example 3, messages are received by `demo-rx`, but not by
   `api_data_reader`.**

The `demo-rx` application fetches API messages from the API server and
subsequently transmits them through a network interface that is automatically
selected (typically your main network interface). While doing so, the `demo-rx`
configures the transmisssions such that they are looped back to the transmitting
interface/socket. The reader application, in turn, receives the messages that
are looped back.

You can inspect whether UDP segments for port 4433 (Blocksat API port) are being
transmitted by `demo-rx` succesfully. To do so, run:

```
sudo tcpdump -n -i any port 4433
```

If they are transmitted normally, it is possible that your firewall is blocking
the messages that are looped back. To overcome this, you can add a firewall rule
as follows:

```
sudo iptables -I INPUT -p udp -i ifname --match multiport --dports 4433,4434 -j ACCEPT
```

where `ifname` is the name of the network interface that `demo-rx` and
`api_data_reader` are using, which you should fill in.

Alternatively, configure firewall rules using the blocksat CLI:

```
blocksat-cli firewall -i ifname
```

You can also control the network interface that is used by `demo-rx` and
`api_data_reader`. To do so, execute the two applications as follows:

```
./demo-rx.py -i ifname
```

```
./api_data_reader.py -i ifname
```

>Note that instead of `--demo` on `api_data_reader.py`, in this case you specify
>the interface directly.
