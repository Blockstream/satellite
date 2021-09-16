# Blockstream Satellite Host

## Overview

The Blockstream Satellite host image contains everything you need to interface
with the supported satellite receivers, including the Blockstream Satellite
command-line interface
([blocksat-cli](https://blockstream.github.io/satellite/doc/software.html)) and
the
[Bitcoin Satellite](https://blockstream.github.io/satellite/doc/bitcoin.html)
application. All you need to do is launch the `blockstream/satellite`
container while providing the appropriate resources to it.

For example, to interface with a Sat-IP receiver, run the container as follows:

```
docker run --rm -it \
    --network=host \
    -v blocksat-cfg:/root/.blocksat/ \
    blockstream/satellite
```

Please refer to the [user
guide](https://blockstream.github.io/satellite/doc/docker.html) for more
information, including the commands for other supported receiver types.

## Versions and Updates

The `satellite` image receives automatic updates whenever a new version of
the Blocksat CLI becomes available. Each version is tagged as
`satellite:x.y.z`, where `x.y.z` indicates the Blocksat CLI version
installed on the image.

Furthermore, the image is also updated when a new version of the Bitcoin
Satellite application becomes available. Thus, make sure to pull the latest
image version if you are running an outdated Bitcoin Satellite version and
would like to upgrade.

## Issues

If you experience any problem with this image, please get in touch by opening
an issue on [Github](https://github.com/Blockstream/satellite).
