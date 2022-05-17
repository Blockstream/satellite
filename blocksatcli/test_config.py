import os
import uuid
import shutil
from unittest import TestCase
from unittest.mock import patch

from . import config
from . import defs


class TestConfigDir(TestCase):

    def setUp(self):
        self.cfg_name = str(uuid.uuid4())
        self.cfg_dir = "/tmp/test-blocksat-cli-config"

        if not os.path.exists(self.cfg_dir):
            os.makedirs(self.cfg_dir)

    def tearDown(self):
        shutil.rmtree(self.cfg_dir, ignore_errors=True)

    @patch('blocksatcli.util.ask_yes_or_no')
    def test_read_write(self, mock_yes_or_no):
        mock_yes_or_no.return_value = False

        # At first, a config file does not exist
        user_info = config.read_cfg_file(self.cfg_name, self.cfg_dir)
        self.assertIsNone(user_info)

        # Create the config file
        test_info = {'test': 123}
        config.write_cfg_file(self.cfg_name, self.cfg_dir, test_info)

        # Check creation
        user_info = config.read_cfg_file(self.cfg_name, self.cfg_dir)
        self.assertEqual(user_info, test_info)

    @patch('blocksatcli.util.ask_yes_or_no')
    def test_cfg_patching(self, mock_yes_or_no):
        mock_yes_or_no.return_value = False

        # Configuration based on T11N AFR before the update on May 31st 2022:
        test_info = {
            "sat": {
                "name": "Telstar 11N Africa",
                "alias": "T11N AFR",
                "dl_freq": 11480.7,
                "band": "Ku",
                "pol": "H",
                "ip": "172.16.235.17"
            },
            "freqs": {
                "dl": 11480.7,
                "lo": 9750.0,
                "l_band": 1730.7
            }
        }
        config.write_cfg_file(self.cfg_name, self.cfg_dir, test_info)

        # Check patching
        user_info = config.read_cfg_file(self.cfg_name, self.cfg_dir)
        self.assertEqual(user_info['sat']['dl_freq'], 11452.1)
        self.assertEqual(user_info['freqs']['dl'], 11452.1)
        self.assertEqual(user_info['freqs']['l_band'], 1702.1)

        # Configuration based on T11N EU before the update on May 31st 2022:
        test_info = {
            "sat": {
                "name": "Telstar 11N Europe",
                "alias": "T11N EU",
                "dl_freq": 11484.3,
                "band": "Ku",
                "pol": "V",
                "ip": "172.16.235.25"
            },
            "freqs": {
                "dl": 11484.3,
                "lo": 9750.0,
                "l_band": 1734.3
            }
        }
        config.write_cfg_file(self.cfg_name, self.cfg_dir, test_info)

        # Check patching
        user_info = config.read_cfg_file(self.cfg_name, self.cfg_dir)
        self.assertEqual(user_info['sat']['dl_freq'], 11505.4)
        self.assertEqual(user_info['freqs']['dl'], 11505.4)
        self.assertEqual(user_info['freqs']['l_band'], 1755.4)

        # Configuration based on a satellite that is not patched
        test_info = {
            "sat": {
                "name": "Eutelsat 113",
                "alias": "E113",
                "dl_freq": 12066.9,
                "band": "Ku",
                "pol": "V",
                "ip": "172.16.235.9"
            },
            "freqs": {
                "dl": 12066.9,
                "lo": 10600.0,
                "l_band": 1466.9
            }
        }
        config.write_cfg_file(self.cfg_name, self.cfg_dir, test_info)

        # Check that patching yields no effect
        user_info = config.read_cfg_file(self.cfg_name, self.cfg_dir)
        self.assertEqual(user_info['sat']['dl_freq'],
                         test_info['sat']['dl_freq'])
        self.assertEqual(user_info['freqs']['dl'], test_info['freqs']['dl'])
        self.assertEqual(user_info['freqs']['l_band'],
                         test_info['freqs']['l_band'])

    @patch('blocksatcli.util.ask_yes_or_no')
    @patch('blocksatcli.defs.pids', defs.pids)
    def test_chan_conf(self, mock_yes_or_no):
        mock_yes_or_no.return_value = True
        defs.pids = [32]
        info = {'sat': defs.satellites[0], 'lnb': defs.lnbs[0]}
        chan_file = os.path.join(self.cfg_dir, self.cfg_name + "-channel.conf")

        # First conf file
        config._cfg_chan_conf(info, chan_file)
        conf = config._parse_chan_conf(chan_file)
        self.assertEqual(int(conf['FREQUENCY']), info['sat']['dl_freq'] * 1e3)
        self.assertEqual(conf['POLARIZATION'], 'HORIZONTAL')
        self.assertEqual(conf['VIDEO_PID'], '32')

        # Change PID definitions and try generating the conf file again
        defs.pids = [60, 61]

        # Generate a conf file but refuse to overwrite the pre-existing one
        mock_yes_or_no.return_value = False
        config._cfg_chan_conf(info, chan_file)
        conf = config._parse_chan_conf(chan_file)
        # Nothing should be changed
        self.assertEqual(conf['VIDEO_PID'], '32')

        # Overwrite the pre-existing conf file
        mock_yes_or_no.return_value = True
        config._cfg_chan_conf(info, chan_file)
        conf = config._parse_chan_conf(chan_file)
        # Now the new PID settings should be in the file
        self.assertEqual(conf['VIDEO_PID'], '60+61')

        # Add the v1-pointed flag to change the polarization
        info['lnb']['v1_pointed'] = True
        info['lnb']['v1_psu_voltage'] = 13
        config._cfg_chan_conf(info, chan_file)
        conf = config._parse_chan_conf(chan_file)
        self.assertEqual(conf['POLARIZATION'], 'VERTICAL')


class TestConfigHelpers(TestCase):

    def test_net_if(self):
        info = {}

        # Standalone
        info['setup'] = defs.demods[0]
        info['setup']['netdev'] = 'en0'
        self.assertEqual(config.get_net_if(info), 'en0')

        # USB types but adapter number not cached
        for demod in [1, 2]:
            info['setup'] = defs.demods[demod]
            self.assertEqual(config.get_net_if(info), 'dvb0_0')

            # USB type with adapter number cached
            info['setup']['adapter'] = 2
            self.assertEqual(config.get_net_if(info), 'dvb2_0')

        # SDR
        info['setup'] = defs.demods[3]
        self.assertEqual(config.get_net_if(info), 'lo')

        # Sat-IP
        info['setup'] = defs.demods[4]
        self.assertEqual(config.get_net_if(info), 'lo')

    def test_rx_model_and_marketing_name(self):
        info = {}

        info['setup'] = defs.demods[0]
        self.assertEqual(config.get_rx_model(info), 'Novra S400')
        self.assertEqual(config._get_rx_marketing_name(info['setup']),
                         'Novra S400 (pro kit)')

        info['setup'] = defs.demods[1]
        self.assertEqual(config.get_rx_model(info), 'TBS 5927')
        self.assertEqual(config._get_rx_marketing_name(info['setup']),
                         'TBS 5927 (basic kit)')

        info['setup'] = defs.demods[2]
        self.assertEqual(config.get_rx_model(info), 'TBS 5520SE')
        self.assertEqual(config._get_rx_marketing_name(info['setup']),
                         'TBS 5520SE')

        info['setup'] = defs.demods[3]
        self.assertEqual(config.get_rx_model(info), 'RTL-SDR')
        self.assertEqual(config._get_rx_marketing_name(info['setup']),
                         'RTL-SDR software-defined')

        info['setup'] = defs.demods[4]
        self.assertEqual(config.get_rx_model(info), 'Selfsat IP22')
        self.assertEqual(config._get_rx_marketing_name(info['setup']),
                         'Blockstream Base Station')

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
        info = {'setup': {'antenna': defs.antennas[-2]}}
        self.assertEqual(config.get_antenna_model(info), 'Selfsat-H50D')

        # Sat-IP
        info = {'setup': {'antenna': defs.antennas[-1]}}
        self.assertEqual(config.get_antenna_model(info), 'Selfsat>IP22')

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
