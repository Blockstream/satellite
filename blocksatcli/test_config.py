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
        info['setup'] = {
            'type': defs.standalone_setup_type,
            'netdev': 'en0'
        }
        self.assertEqual(config.get_net_if(info), 'en0')

        info['setup'] = {
            'type': defs.linux_usb_setup_type,
        }
        self.assertEqual(config.get_net_if(info), 'dvb0_0')
        self.assertEqual(config.get_net_if(info, prefer_8psk=True), 'dvb0_1')

        info['setup'] = {
            'type': defs.sdr_setup_type,
        }
        self.assertEqual(config.get_net_if(info), 'lo')
