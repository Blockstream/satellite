import qrcode

from ..util import format_sats


def print_invoice(invoice):
    print("--\nAmount Due:\n{}".format(
        format_sats(int(invoice["msatoshi"]) / 1e3)))
    print("--\nLightning Invoice Number:\n{}".format(invoice["payreq"]))

    qr = qrcode.QRCode()
    qr.add_data(invoice["payreq"])

    try:
        qr.print_ascii()
    except UnicodeError:
        qr.print_tty()
