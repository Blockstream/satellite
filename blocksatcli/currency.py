import logging
import os
import sys
from datetime import datetime
from math import ceil
from typing import List, Tuple, Union

import requests

from .api.error import log_errors

CURRENCY_FORMATS = {"usd": ".2f", "satoshi": ".3f", "msatoshi": "d"}
CURRENCY_SHORT_LABELS = {"usd": "USD", "satoshi": "sat", "msatoshi": "msat"}
SUPPORTED_CLIENT_CURRENCIES = ["msatoshi", "satoshi", "usd"]  # used by the CLI
SUPPORTED_SERVER_CURRENCIES = ["msatoshi", "usd"]  # supported by the Sat API

assert all([k in SUPPORTED_CLIENT_CURRENCIES for k in CURRENCY_FORMATS.keys()])
assert all(
    [k in SUPPORTED_CLIENT_CURRENCIES for k in CURRENCY_SHORT_LABELS.keys()])

logger = logging.getLogger(__name__)


class CurrencyManager:

    def __init__(self, server, cache_timeout=60):
        self.server = server
        self.cache_timeout = cache_timeout  # rate cache timeout in seconds
        self.t_last_fetch = None  # timestamp of last rate fetch
        self.last_msat_per_usd = None  # last fetched rate

    def _get_msat_per_usd(self) -> int:
        now = datetime.utcnow()
        if self.t_last_fetch is not None and (
                now - self.t_last_fetch).total_seconds() < self.cache_timeout:
            return self.last_msat_per_usd

        try:
            res = requests.get(os.path.join(self.server, 'currency/rate'),
                               params={'base': 'usd'})
            if res.status_code != requests.codes.ok:
                log_errors(logger, res)
            res.raise_for_status()
        except requests.exceptions.RequestException:
            logger.error("Failed to fetch the BTCUSD exchange rate.")
            sys.exit(1)

        json_res = res.json()
        msat_per_usd = json_res['rates']['msatoshi']
        self.last_msat_per_usd = msat_per_usd
        self.t_last_fetch = now
        return msat_per_usd

    def sat_to_msat(self, sat_amount) -> int:
        return ceil(sat_amount * 1e3)

    def msat_to_sat(self, msat_amount) -> Union[int, float]:
        return round(msat_amount / 1e3, 3)

    def usd_to_satoshi(self, usd_amount) -> Union[int, float]:
        msat_per_usd = self._get_msat_per_usd()
        msat_amount = usd_amount * msat_per_usd
        return self.msat_to_sat(msat_amount)

    usd_to_sat = usd_to_satoshi  # alias

    def satoshi_to_usd(self, sat_amount) -> Union[int, float]:
        msat_per_usd = self._get_msat_per_usd()
        usd_amount = sat_amount * 1e3 / msat_per_usd
        return round(usd_amount, 2)

    sat_to_usd = satoshi_to_usd  # alias

    def msat_to_usd(self, msat_amount) -> Union[int, float]:
        sat_amount = self.msat_to_sat(msat_amount)
        return self.satoshi_to_usd(sat_amount)

    def usd_to_msat(self, usd_amount) -> int:
        sat_amount = self.usd_to_satoshi(usd_amount)
        return self.sat_to_msat(sat_amount)

    def convert_to_server_unit(self, amount,
                               currency) -> Tuple[Union[int, float], str]:
        """Convert amount in given currency to a server-supported currency unit

        The given amount can be specified in any supported client unit. This
        function converts it to the closest unit supported by the server. For
        instance, an amount specified in satoshi is converted to msatoshi
        because the server only supports msatoshi, not satoshi. Meanwhile, an
        amount in usd is returned as is because the server supports USD.

        Args:
            amount (int | float): Amount to convert.
            currency (str): Currency unit in which the amount is denominated.

        Returns:
            Tuple[Union[int, float], str]: Converted amount and
                server-supported currency.
        """
        if currency not in SUPPORTED_CLIENT_CURRENCIES:
            raise ValueError(f"Unsupported currency {currency}")

        if currency == "satoshi":
            server_currency = "msatoshi"
            converted_amount = self.sat_to_msat(amount)
        elif currency == "usd" or currency == "msatoshi":
            # No conversion needed for USD or msatoshi
            server_currency = currency
            converted_amount = amount

        assert server_currency in SUPPORTED_SERVER_CURRENCIES
        return converted_amount, server_currency

    def convert(self, amount: float, currency: str,
                target_currency: str) -> Union[int, float] | None:
        """Convert an amount in a given currency to another currency unit

        Args:
            amount (float): Amount in the given currency to convert.
            currency (str): Currency unit in which the amount is denominated.
            target_currency (str): Target currency unit.

        Returns:
            Union[int, float]: Amount in the target currency unit if
                successful, None otherwise.

        """
        assert currency in SUPPORTED_CLIENT_CURRENCIES
        assert target_currency in SUPPORTED_CLIENT_CURRENCIES

        if target_currency == currency:
            return amount
        elif target_currency in "usd":
            conversion_fn = (self.sat_to_usd
                             if currency == "satoshi" else self.msat_to_usd)
        elif target_currency == "satoshi":
            conversion_fn = (self.usd_to_sat
                             if currency == "usd" else self.msat_to_sat)
        elif target_currency == "msatoshi":
            conversion_fn = (self.usd_to_msat
                             if currency == "usd" else self.sat_to_msat)
        else:
            return None

        try:
            converted_amount = conversion_fn(amount)
        except SystemExit:
            converted_amount = None

        return converted_amount


def convert_currency_from_msat(server: str, records_list: List[dict],
                               field: str, currency: str) -> Tuple[str, str]:
    """Convert the msat amounts on a list of objects to a target currency

    Converts the amount field in each object of the records list from msat to a
    target unit in place. The target unit can be any supported by the client,
    with no restriction of being supported by the server. This function is
    intended primarily for formatting the output of client commands.

    Args:
        server (str): Server API from which the currency rate is fetched.
        records_list (List[dict]): List of dictionaries containing the records
            with amounts in millisatoshi to be converted to another target
            currency unit.
        field (str): Dictionary key whose value should be converted from msat
            to the chosen currency in each object of the records list. All
            objects in the list must have this key.
        currency (str): Target currency unit.

    Returns:
        Tuple[str,str]: Tuple with the currency label and format string to be
            used for printing the converted amounts.
    """
    currency_manager = CurrencyManager(server)
    currency_label = CURRENCY_SHORT_LABELS[currency]
    currency_format = CURRENCY_FORMATS[currency]
    for x in records_list:
        if currency == "satoshi":
            x[field] = currency_manager.msat_to_sat(x[field])
        elif currency == "usd":
            x[field] = currency_manager.msat_to_usd(x[field])
    return currency_label, currency_format


def convert_from_usd(server: str, usd_amount: float,
                     currency: str) -> Union[int, float]:
    """Convert a given amount in USD to another currency unit

    Args:
        server (str): Server API from which the currency rate is fetched.
        usd_amount (float): Amount in USD to convert.
        currency (str): Target currency unit.

    Returns:
        Union[int, float]: Amount in the target currency unit.
    """
    currency_manager = CurrencyManager(server)
    if currency == "satoshi":
        x = currency_manager.usd_to_sat(usd_amount)
    elif currency == "msatoshi":
        x = currency_manager.usd_to_msat(usd_amount)
    elif currency == "usd":
        x = usd_amount
    return x


def get_currency_label_and_format(currency):
    currency_label = CURRENCY_SHORT_LABELS[currency]
    currency_format = CURRENCY_FORMATS[currency]
    return currency_label, currency_format


def add_currency_opt_to_parser(parser):
    parser.add_argument(
        '--currency',
        choices=SUPPORTED_CLIENT_CURRENCIES,
        default="msatoshi",
        help="Currency unit in which the results are denominated")
