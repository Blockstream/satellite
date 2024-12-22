import argparse
import os
import shutil
import textwrap
from unittest.mock import patch

from . import config, gqrx
from .test_helpers import TestEnv


class TestGqrx(TestEnv):

    def _assert_gqrx_config(self, gqrx_config, user_info):
        freq_hz = int(user_info['freqs']['dl'] * 1e6)
        default_gains = r'@Variant(\0\0\0\b\0\0\0\x2\0\0\0\x6\0L\0N\0\x41' + \
            r'\0\0\0\x2\0\0\x1\x92\0\0\0\x4\0I\0\x46\0\0\0\x2\0\0\0\xcc)'
        expected_config = textwrap.dedent(f"""
        [General]
        configversion=2

        [fft]
        averaging=80
        db_ranges_locked=true
        pandapter_min_db=-90
        waterfall_min_db=-90

        [input]
        bandwidth=1000000
        device="rtl=0"
        frequency={freq_hz}
        gains={default_gains}
        lnb_lo=10600000000
        sample_rate=2400000

        [receiver]
        demod=0
        """)

        self.assertEqual(gqrx_config, expected_config)

    def setUp(self):
        super().setUp()
        self.gqrx_dir = os.path.join(self.cfg_dir, "gqrx")
        self.gqrx_cfg = os.path.join(self.gqrx_dir, "default.conf")

        self.args = argparse.Namespace(cfg=self.cfg_name,
                                       cfg_dir=self.cfg_dir,
                                       path=self.gqrx_dir,
                                       yes=False)

        if not os.path.exists(self.cfg_dir):
            os.makedirs(self.cfg_dir)

    def tearDown(self):
        super().tearDown()
        shutil.rmtree(self.gqrx_dir, ignore_errors=True)

    @patch("blocksatcli.util.ask_yes_or_no")
    def test_gqrx_config(self, mock_ask_yes_or_no):
        mock_ask_yes_or_no.return_value = True  # Proceed? Yes

        # Create receiver cfg
        receiver_cfg = {"freqs": {"dl": 12016.4, "lo": 10600.0}}
        config.write_cfg_file(self.cfg_name, self.cfg_dir, receiver_cfg)

        # Run GQRX configuration
        gqrx.configure(self.args)
        with open(self.gqrx_cfg) as fd:
            gqrx_config = fd.read()

        self._assert_gqrx_config(gqrx_config, receiver_cfg)

    @patch("blocksatcli.util.ask_yes_or_no")
    def test_gqrx_config_abort(self, mock_ask_yes_or_no):
        # Create receiver cfg
        receiver_cfg = {"freqs": {"dl": 12016.4, "lo": 10600.0}}
        config.write_cfg_file(self.cfg_name, self.cfg_dir, receiver_cfg)

        # Run GQRX configuration but abort when asked to Proceed
        mock_ask_yes_or_no.return_value = False
        gqrx.configure(self.args)
        self.assertFalse(os.path.exists(self.gqrx_cfg))

    @patch("blocksatcli.util.ask_yes_or_no")
    def test_gqrx_config_overwrite(self, mock_ask_yes_or_no):
        mock_ask_yes_or_no.side_effect = [
            True,  # 1st config: Proceed? yes
            True,  # 2nd config: Proceed? Yes
            False,  # 2nd config: Overwrite? No
            True,  # 3rd config: Proceed? Yes
            True  # 3rd config: Overwrite? Yes
        ]

        receiver_cfg1 = {"freqs": {"dl": 12016.4, "lo": 10600.0}}
        receiver_cfg2 = {"freqs": {"dl": 12066.9, "lo": 10600.0}}

        # Create the first configuration
        config.write_cfg_file(self.cfg_name, self.cfg_dir, receiver_cfg1)
        gqrx.configure(self.args)
        with open(self.gqrx_cfg) as fd:
            gqrx_config = fd.read()
        self._assert_gqrx_config(gqrx_config, receiver_cfg1)

        # Change the CLI configuration and update the gqrx configuration but do
        # not accept the overwriting
        config.write_cfg_file(self.cfg_name, self.cfg_dir, receiver_cfg2)
        gqrx.configure(self.args)
        with open(self.gqrx_cfg) as fd:
            gqrx_config = fd.read()

        # The config file should still hold the first configuration
        self._assert_gqrx_config(gqrx_config, receiver_cfg1)

        # Update the config once again and, this time, accept the overwriting
        gqrx.configure(self.args)
        with open(self.gqrx_cfg) as fd:
            gqrx_config = fd.read()

        # The config file should now hold the second configuration
        self._assert_gqrx_config(gqrx_config, receiver_cfg2)

    @patch("blocksatcli.config.read_cfg_file")
    def test_gqrx_config_with_no_receiver_cfg(self, mock_read_cfg):
        """Test gqrx config with no receiver configuration
        """

        mock_read_cfg.return_value = None

        # Do not create a GQRX cfg if there is no receiver configuration
        gqrx.configure(self.args)
        self.assertFalse(os.path.exists(self.gqrx_cfg))
