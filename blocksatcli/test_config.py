import os
import uuid
from unittest import TestCase
from unittest.mock import patch

from . import config
from . import defs


class TestConfig(TestCase):
    @patch('blocksatcli.util._ask_yes_or_no')
    def test_read_write(self, mock_yes_or_no):
        mock_yes_or_no.return_value = False
        cfg_name = str(uuid.uuid4())
        cfg_dir = "/tmp"

        # At first, a config file does not exist
        user_info = config.read_cfg_file(cfg_name, cfg_dir)
        self.assertIsNone(user_info)

        # Create the config file
        test_info = {'test': 123}
        config.write_cfg_file(cfg_name, cfg_dir, test_info)

        # Check creation
        user_info = config.read_cfg_file(cfg_name, cfg_dir)
        self.assertEqual(user_info, test_info)

        # Remove file
        path = config._cfg_file_name(cfg_name, cfg_dir)
        self.assertTrue(os.path.exists(path))
        os.remove(path)
        self.assertFalse(os.path.exists(path))

    def test_net_if(self):
        info = {}

        # Standalone
        info['setup'] = defs.demods[0]
        info['setup']['netdev'] = 'en0'
        self.assertEqual(config.get_net_if(info), 'en0')

        # USB type but adapter number not cached
        info['setup'] = defs.demods[1]
        self.assertEqual(config.get_net_if(info), 'dvb0_0')
        self.assertEqual(config.get_net_if(info, prefer_8psk=True), 'dvb0_1')

        # USB type with adapter number cached
        info['setup']['adapter'] = 2
        self.assertEqual(config.get_net_if(info), 'dvb2_0')
        self.assertEqual(config.get_net_if(info, prefer_8psk=True), 'dvb2_1')

        # SDR
        info['setup'] = defs.demods[2]
        self.assertEqual(config.get_net_if(info), 'lo')

    def test_rx_model(self):
        info = {}

        info['setup'] = defs.demods[0]
        self.assertEqual(config.get_rx_model(info), 'Novra S400')

        info['setup'] = defs.demods[1]
        self.assertEqual(config.get_rx_model(info), 'TBS 5927')

        info['setup'] = defs.demods[2]
        self.assertEqual(config.get_rx_model(info), 'RTL-SDR')

    def test_antenna_model(self):
        # Dish antennas on cm and m range
        info = {'setup': {'antenna': defs.antennas[0]}}
        self.assertEqual(config.get_antenna_model(info), '45cm dish')
        info['setup']['antenna']['size'] = 100
        self.assertEqual(config.get_antenna_model(info), '1m dish')
        info['setup']['antenna']['size'] = 120
        self.assertEqual(config.get_antenna_model(info), '1.2m dish')

        # Backwards compatibility with "custom" antenna lacking a type field
        info = {'setup': {'antenna': {'label': 'custom', 'size': 282.5}}}
        self.assertEqual(config.get_antenna_model(info), '2.825m dish')

        # Flat-panel
        info = {'setup': {'antenna': defs.antennas[-1]}}
        self.assertEqual(config.get_antenna_model(info), 'Selfsat H50D')

    def test_lnb_model(self):
        info = {}
        info['lnb'] = defs.lnbs[0]
        self.assertEqual(config.get_lnb_model(info), 'GEOSATpro UL1PLL')

        # Custom LNBs
        info['lnb'] = {
            'vendor': "",
            'model': "",
            'universal': True,
            'band': "Ku"
        }
        self.assertEqual(config.get_lnb_model(info), 'Custom Universal LNB')
        info['lnb']['universal'] = False
        self.assertEqual(config.get_lnb_model(info), 'Custom Ku-band LNB')
        info['lnb']['band'] = "C"
        self.assertEqual(config.get_lnb_model(info), 'Custom C-band LNB')
