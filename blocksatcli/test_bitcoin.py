import unittest, argparse
from . import bitcoin, defs


class TestBitcoinConfGen(unittest.TestCase):
    def gen_text_dict(self):
        """Generate configurations in text and dictionary formats"""
        # Text version
        text = (
            "debug=udpnet\n"
            "debug=udpmulticast\n"
            "udpmulticastloginterval=60\n"
            "udpmulticast=dvb0_0,239.0.0.2:4434,172.16.235.9,1,blocksat-tbs-lowspeed\n"
            "udpmulticast=dvb0_1,239.0.0.2:4434,172.16.235.9,1,blocksat-tbs-highspeed\n"
        )
        # Corresponding dictionary version
        udpmcastlist = list()
        devices      = ["dvb0_0", "dvb0_1"]
        labels       = ["blocksat-tbs-lowspeed", "blocksat-tbs-highspeed"]
        for device,label in zip(devices, labels):
            udpmcastlist.append(
                bitcoin._udpmulticast(device,
                                      "172.16.235.9",
                                      dst_addr=defs.btc_dst_addr,
                                      trusted="1",
                                      label=label)
            )
        cfg = {
            'debug'                   : ["udpnet", "udpmulticast"],
            'udpmulticastloginterval' : "60",
            'udpmulticast'            : udpmcastlist
        }
        return text, cfg

    def test_cfg_to_text(self):
        """Test the conversion from dictionary to text"""
        expected_text, dct = self.gen_text_dict()
        # Create configuration object with the given configs
        cfg = bitcoin.Cfg(dct)
        # Export text version
        text = cfg.text()
        # See if text version matches the expected one
        self.assertEqual(text, expected_text)

    def test_text_to_cfg(self):
        """Test the conversion from text to dictionary"""
        text, expected_dct = self.gen_text_dict()
        # Create empty configuration object
        cfg = bitcoin.Cfg()
        # Load configurations from the expected text config
        cfg.load_text_cfg(text)
        # Check if dictionary version (loaded from text) is OK
        self.assertEqual(cfg.cfg, expected_dct)

    def test_concat(self):
        """Test the concatenation of a new option"""
        text, dct = self.gen_text_dict()
        # Create configuration object with the given configs
        cfg = bitcoin.Cfg(dct)
        # Add new option
        cfg.add_opt("udpmulticast",
                    bitcoin._udpmulticast("eth0",
                                          "172.16.235.9",
                                          dst_addr=defs.btc_dst_addr,
                                          trusted="1",
                                          label="blocksat-s400")
                    )
        # Add new option to expected text
        text += "udpmulticast=eth0,239.0.0.2:4434,172.16.235.9,1,blocksat-s400\n"
        # Check if exported text includes the new option
        self.assertEqual(text, cfg.text())

