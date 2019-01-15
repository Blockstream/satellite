# Satellite API

Blockstream Satellite API provides developers with an easy-to-use RESTful API
that can be used to create applications that broadcast messages globally using
the Blockstream Satellite network.

As illustrated in the diagram below, data posted to the Satellite API server is
ultimately transported to the Blockstream Satellite Teleport and broadcast
globally. Subsequently, the Blockstream Satellite Receiver (`blocksat-rx`)
applications around the globe receive the data and output it to a named pipe.

![Blockstream Satellite API Architecture](../doc/api_architecture.png?raw=true "Blockstream Satellite API Architecture")

Example Python applications for interaction with the Satellite API are available
in the [`examples` directory](examples/).

**IMPORTANT** The Blockstream Satellite API is currently operating in developer
mode: utilizing Lightning Testnet for payment and without live satellite
transmissions. We will transition the API to mainnet and live satellite
broadcast on January 16th 2019.

<!-- markdown-toc start - Don't edit this section. Run M-x markdown-toc-generate-toc again -->
## Contents

- [REST API](#rest-api)
    - [POST /order](#post-order)
    - [POST /order/:uuid/bump](#post-orderuuidbump)
    - [GET /order/:uuid](#get-orderuuid)
    - [DELETE /order/:uuid](#delete-orderuuid)
    - [GET /orders/queued](#get-ordersqueued)
    - [GET /orders/sent](#get-orderssent)
    - [GET /info](#get-info)
    - [GET /subscribe/:channels](#get-subscribechannels)
- [Blockstream Satellite Receiver API Data Output](#blockstream-satellite-receiver-api-data-output)

<!-- markdown-toc end -->

## REST API

Each call to an API endpoint responds with a JSON object, whether the call is
successful or results in an error.

The code samples below assume that you've set `SATELLITE_API` in your shell to
`https://satellite.blockstream.com/api`, which is the public base URL of your
server. For example, run:

```
export SATELLITE_API=https://satellite.blockstream.com/api
```

### POST /order

Place an order for a message transmission. The body of the POST must provide a
`file` containing the message and a `bid` in millisatoshis. If the bid is below
an allowed minimum millisatoshis per byte, an error is returned.

For example, to place an order to transmit the file `hello_world.png` with an
initial bid of 10,000 millisatoshi, issue an HTTP POST request like this:

```bash
curl -F "bid=10000" -F "file=@/path/to/upload/file/hello_world.png" $SATELLITE_API/order
```

If successful, the response includes the JSON Lightning invoice as returned by
Lightning Charge's [POST
/invoice](https://github.com/ElementsProject/lightning-charge#post-invoice) and
an authentication token that can be used to modify the order. Within the
metadata of the Lightning invoice, metadata is included providing: the bid (in
millisatoshis), the SHA256 digest of the uploaded message file, and a UUID for
the order.

```bash
{
   "auth_token":"d784e322dad7ec2671086ce3ad94e05108f2501180d8228577fbec4115774750",
   "uuid":"409348bc-6af0-4999-b715-4136753979df",
   "lightning_invoice":{
      "id":"N0LOTYc9j0gWtQVjVW7pK",
      "msatoshi":"514200",
      "description":"BSS Test",
      "rhash":"5e5c9d111bc76ce4bf9b211f12ca2d9b66b81ae9839b4e530b16cedbef653a3a",
      "payreq":"lntb5142n1pd78922pp5tewf6ygmcakwf0umyy039j3dndntsxhfswd5u5ctzm8dhmm98gaqdqdgff4xgz5v4ehgxqzjccqp286gfgrcpvzl04sdg2f9sany7ptc5aracnd6kvr2nr0e0x5ajpmfhsjkqzw679ytqgnt6w4490jjrgcvuemz790salqyz9far68cpqtgq3q23el",
      "expires_at":1541642146,
      "created_at":1541641546,
      "metadata":{
         "msatoshis_per_byte":"200",
         "sha256_message_digest":"0e2bddf3bba1893b5eef660295ef12d6fc72870da539c328cf24e9e6dbb00f00",
         "uuid":"409348bc-6af0-4999-b715-4136753979df"
      },
      "status":"unpaid"
   }
}
```

### POST /order/:uuid/bump

Increase the bid for an order sitting in the transmission queue. The
`bid_increase` must be provided in the body of the POST. A Lightning invoice is
returned for it and, when it is paid, the increase is added to the current
bid. An `auth_token` must also be provided. For example, to increase the bid on
the order placed above by 100,000 millisatoshis, issue a POST like this:

```bash
curl -v -F "bid_increase=100000" -F "auth_token=d784e322dad7ec2671086ce3ad94e05108f2501180d8228577fbec4115774750" $SATELLITE_API/order/409348bc-6af0-4999-b715-4136753979df/bump
```

Response object is in the same format as for `POST /order`.

As shown below for DELETE, the `auth_token` may alternatively be provided using
the `X-Auth-Token` HTTP header.

### GET /order/:uuid

Retrieve an order by UUID. Must provide the corresponding auth token to prove
that it is yours.

```bash
curl -v -H "X-Auth-Token: 5248b13a722cd9b2e17ed3a2da8f7ac6bd9a8fe7130357615e074596e3d5872f" $SATELLITE_API/order/409348bc-6af0-4999-b715-4136753979df
```

### DELETE /order/:uuid

To cancel an order, issue an HTTP DELETE request to the API endpoint
`/order/:uuid/` providing the UUID of the order. An `auth_token` must also be
provided. For example, to cancel the order above, issue a request like this:

```bash
curl -v -X DELETE -F "auth_token=5248b13a722cd9b2e17ed3a2da8f7ac6bd9a8fe7130357615e074596e3d5872f" $SATELLITE_API/order/409348bc-6af0-4999-b715-4136753979df
```

The `auth_token` may be provided as a parameter in the DELETE body as above or
may be provided using the `X-Auth-Token` HTTP header, like this:

```bash
curl -v -X DELETE -H "X-Auth-Token: 5248b13a722cd9b2e17ed3a2da8f7ac6bd9a8fe7130357615e074596e3d5872f" $SATELLITE_API/order/409348bc-6af0-4999-b715-4136753979df
```

### GET /orders/queued  ###

Retrieve a list of paid, but unsent orders. Both pending orders and the order
currently being transmitted are returned. Optionally, accepts a parameter
specifying how many queued orders to return.

```bash
curl $SATELLITE_API/orders/queued
```

```bash
curl $SATELLITE_API/orders/queued?limit=18
```

The response is a JSON array of records (one for each queued message). The
revealed fields for each record include: `uuid`, `bid`, `bid_per_byte`,
`message_size`, `message_digest`, `status`, `created_at`,
`started_transmission_at`, and `ended_transmission_at`.

### GET /orders/sent  ###

Retrieves a list of up to 20 sent orders in reverse chronological
order. Optionally, accepts the parameter `before` (a timestamp in ISO 8601
format) specifying that only orders before the given time are to be returned.

```bash
curl $SATELLITE_API/orders/sent
```

```bash
curl $SATELLITE_API/orders/sent?limit=18
```

The response is a JSON array of records (one for each queued message). The
revealed fields for each record include: `uuid`, `bid`, `bid_per_byte`,
`message_size`, `message_digest`, `status`, `created_at`,
`started_transmission_at`, and `ended_transmission_at`.

### GET /info

Returns information about the c-lightning node where satellite API payments are
terminated.

```bash
curl $SATELLITE_API/info
```

The response is a JSON object consisting of the node ID, port, IP addresses, and
other information useful for opening payment channels. For example:

```bash
{
   "id":"032c6ba19a2141c5fee6ac8b6ff6cf24456fd4e8e206716a39af3300876c3a4835",
   "port":42259,
   "address":[],
   "version":"v0.5.2-2016-11-21-1937-ge97ee3d",
   "blockheight":434,
   "network":"regtest"
}
```


### GET /subscribe/:channels

Subscribe to one or more [server-side
events](https://en.wikipedia.org/wiki/Server-sent_events) channels. The
`channels` parameter is a comma-separated list of event channels. Currently,
only one channel is available: `transmissions`, to which an event is pushed each
time a message transmission begins and ends. Event data includes a JSON
representation of the order, including its current status.

```bash
curl $SATELLITE_API/subscribe/:channels
```


## Blockstream Satellite Receiver API Data Output

The blocksat receiver does not output the raw data payload sent to the Satellite
API directly as it is to the output named pipe. Instead, the blocksat receiver
embeds the data into a structure. The structure contains a delimiter and a field
with the data length. In the end, what appears in the output pipe is as
illustrated below:

![Output data structure used for API data](../doc/api_output_data_structure.png?raw=true "Output data structure used for API data")

This structure allows applications to distinguish the boundaries between
independent API transmissions. However, note that it does not guarantee data
integrity, since the length value in the header is simply the length of the
received data, rather than the length of the data that was actually
transmitted. Data integrity is left for the application-specific protocol to be
developed by users. See [Example 1 in the "examples"
directory](examples/#example-1-sending-data-in-a-user-defined-protocol) for one
such application-specific protocol that checks data integrity.

