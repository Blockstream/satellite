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

![Blockstream Satellite API Architecture](../doc/api_architecture.png?raw=true "Blockstream Satellite API Architecture")

<!-- markdown-toc start - Don't edit this section. Run M-x markdown-toc-generate-toc again -->
## Contents

- [Environment](#environment)
- [Example 1: Sending data in a user-defined protocol](#example-1-sending-data-in-a-user-defined-protocol)
- [Example 2: Sending files directly](#example-2-sending-files-directly)
- [Example 3: Testing the API while receiving data directly via Internet](#example-3-testing-the-api-while-receiving-data-directly-via-internet)
- [Further Information](#further-information)

<!-- markdown-toc end -->

## Environment

The first step in order to use the examples that follow is to prepare the
environment.

For Python, create a virtual environment with the packages listed in the
`requirements.txt` file of this directory. For example, if using
*virtualenvwrapper*, run the following:

```
mkvirtualenv --python=`which python2` -r requirements.txt blocksat-api
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
(`examples`) directory. This directory is where the GPG public and secret
keyrings are stored.

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

The *API data sender* by default places a user-specified file into a data
structure and then sends the entire structure to the API. The structure carries
the file name as a string and also contains a CRC32 checksum that can be used
for data integrity check on the receiver side. The entire structure is first
encrypted using GnuPG and then posted via HTTPS to the Blockstream Satellite
API.

Meanwhile, the *API data reader* application waits for data written by the
Blockstream Satellite receiver into the pipe file at `/tmp/blocksat/api`. It
continuously reads this named pipe, decrypts the incoming data, validates the
integrity of the data and then saves the unpacked files. The integrity
validation is done by computing the CRC32 checksum of the received data and
comparing it with the checksum that is advertised on the header of the incoming
data structure. Ultimately, the incoming file is saved in the `downloads/`
folder with the name that is given in the header.

In order to run the example, first ensure that the Blocksat receiver (or the
demo receiver of [Example 3](#example-3-receiving-data-from-the-api-sandbox))
is running. Next, ensure that you are using the correct Python virtual
environment. If using `virtualenvwrapper`, run:

```
workon blocksat-api
```

Then, launch the API data reader as follows:

```
./api_data_reader.py
```

The reader will wait for data to appear in the API named pipe (at
`/tmp/blocksat/api`).

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

Once the API server effectively transmits your data, the data is expected to pop
at the API data reader application. In the end, the received file will be saved
in the `downloads` folder.

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

Note that, in practice, data written by the Blocksat Receiver in the API named
pipe (at `/tmp/blocksat/api`) multiplexes transmissions from all users of the
Satellite API. Hence, the application is expected to fail decryption several
times until it finds the data for which it is actually a recipient of.

## Example 2: Sending files directly

In this example, the goal is to send a file directly to the API, without placing
it on any user-specific protocol.

The same two scripts of Example 1 are used, except for different command-line
arguments:

1. API data sender
2. API data reader

In this case, launch the API data reader as follows:

```
./api_data_reader.py --save-raw
```

Next, send some data using:

```
./api_data_sender.py -f filename --send-raw
```

Note that the `--send-raw` flag means that the data is sent as it is, without
any additional protocol framing.

Once the Blocksat receiver outputs your data into the API output pipe, the
reader will receive this data and retrieve the file.

Note that, just like in Example 1, this example also handles encryption
internally. That is, you can point to a non-encrypted file and the data sender
will encrypt it internally. The reader will then decrypt the data.

This use case is also useful when sending a file directly via the form in the
API web page. In this case, the file can be retrieved on the Blocksat receiver
side by running the API data reader as above. The only difference is that in
this case you will need to encrypt the file offline, before uploading to the
form in the API web page. This is because the *API data reader* application by
default assumes the incoming data is encrypted with the keys that are available
in the local GnupG home directory.

To encrypt a file offline, you can run for example:

```
gpg --encrypt --recipient pub_key_id_or_email filename
```

where `pub_key_id_or_email` can be either the public key ID of the target
recipient or its e-mail.

## Example 3: Testing the API while receiving data directly via Internet

This example illustrates the scenario in which instead of receiving data with
the actual Blockstream Satellite receiver (i.e. the `blocksat-rx` application),
you fetch data directly from the API through the Internet.

Now, you will need three scripts from the `examples` directory:

1. API data sender
2. API data reader
3. Demo receiver

You can choose to use the API data sender and API data reader either as in
[Example 1](#example-1-sending-data-in-a-user-defined-protocol) or as in
[Example 2](#example-2-sending-files). The important difference here is that the
API data reader will read data from a named pipe that is filled by the *demo
receiver*, rather than the actual Blockstream Satellite receiver.

Start by activating the `blocksat-api` Python virtual environment. Then, run the
demo receiver:

```
./demo-rx.py
```

This application will continuously wait for data broadcast directly by the API
and then it will output the data to the same named pipe that the Blockstream
Satellite receiver would use, namely the pipe file at `/tmp/blocksat/api`.

> NOTE: in case you want to concurrently run both the actual `blocksat-rx`
> receiver application and the demo receiver, you will need to use another named
> pipe for the demo receiver. Otherwise, the two applications would try to use
> the same named pipe. To do so, run `./demo-rx.py -f pipe_file`, where
> `pipe_file` is the name of the other named pipe file to be used for the demo
> receiver.

Next, assuming for the explanation that the approach of [Example
1](#example-1-sending-data-in-a-user-defined-protocol) is adopted, you can leave
the data reader running with:

```
./api_data_reader.py
```

Finally, send a file with the API data sender application and wait until it pops
in the data reader.

```
./api_data_sender.py -f filename
```

## Further Information

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
