import argparse
import os
from unittest import TestCase
from unittest.mock import patch

from . import config, defs
from .test_helpers import TestEnv


class TestConfigDir(TestEnv):

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

        changes = [
            (
                # T11N AFR frequency before May 31st 2022
                'T11N AFR',
                {
                    'old_freq': 11480.7,
                    'new_freq': 11470.3,
                },
            ),
            (
                # T11N AFR frequency before Dec 6, 2024
                'T11N AFR',
                {
                    'old_freq': 11452.1,
                    'new_freq': 11470.3,
                },
            ),
            (
                # T11N EU frequency before May 31st 2022
                'T11N EU',
                {
                    'old_freq': 11484.3,
                    'new_freq': 11494.51
                },
            ),
            (
                # T11N EU frequency before Dec 6, 2024
                'T11N EU',
                {
                    'old_freq': 11505.4,
                    'new_freq': 11494.51
                },
            ),
            (
                # G18 update on March 3, 2023
                'G18',
                {
                    'old_freq': 12016.4,
                    'new_freq': 11913.4
                },
            ),
            (
                'T18V C',
                {
                    'old_freq': 4053.83,  # frequency pre July 12, 2023
                    'new_freq': 4140.0,  # Update on May 9, 2025
                    'old_pol': 'H',  # Pre July 9, 2024
                    'new_pol': 'V'  # After July 9, 2024
                },
            ),
            (
                'T18V C',
                {
                    'old_freq': 4057.4,  # frequency after July 12, 2023
                    'new_freq': 4140.0,  # Update on May 9, 2025
                    'old_pol': 'H',  # Pre July 9, 2024
                    'new_pol': 'V'  # After July 9, 2024
                },
            ),
            (
                'T18V C',
                {
                    'old_freq': 4122.6,  # frequency after July 9, 2024
                    'new_freq': 4140.0,  # Update on May 9, 2025
                    'old_pol': 'H',  # Pre July 9, 2024
                    'new_pol': 'V'  # After July 9, 2024
                },
            ),
            (
                # T18V Ku update on July 9, 2024
                'T18V Ku',
                {
                    'old_freq': 11506.75,
                    'new_freq': 11507.9
                },
            )
        ]

        for satellite, change in changes:
            sat_def = defs.get_satellite_def(satellite)
            sat_def['dl_freq'] = change['old_freq']
            if 'old_pol' in change:
                sat_def['pol'] = change['old_pol']
            band = sat_def['band']
            example_lnb = "Titanium C1-PLL" if band == 'C' else \
                "GEOSATpro UL1PLL"
            lo_freq = 5150.0 if band == 'C' else (
                9750.0 if sat_def['dl_freq'] < 11700.0 else 10600.0)
            old_l_band = config._calc_if_freq(change['old_freq'], lo_freq,
                                              band)
            new_l_band = config._calc_if_freq(change['new_freq'], lo_freq,
                                              band)

            # Original configuration
            chan_conf = config.get_chan_file_path(self.cfg_dir, self.cfg_name)
            old_info = {
                "sat": sat_def,
                "freqs": {
                    "dl": change['old_freq'],
                    "lo": lo_freq,
                    "l_band": old_l_band
                },
                "lnb": defs.get_lnb_def(*example_lnb.split()),
                "setup": {
                    "type": defs.linux_usb_setup_type,
                    "channel": chan_conf
                }
            }
            new_info = {
                "sat": defs.get_satellite_def(satellite),
                "freqs": {
                    "dl": change['new_freq'],
                    "lo": lo_freq,
                    "l_band": new_l_band
                },
                "lnb": defs.get_lnb_def(*example_lnb.split()),
                "setup": {
                    "type": defs.linux_usb_setup_type,
                    "channel": chan_conf
                }
            }
            config.write_cfg_file(self.cfg_name, self.cfg_dir, old_info)
            config.write_chan_conf(old_info,
                                   chan_conf,
                                   yes=True,
                                   regeneration=True)

            # Before patching, the channel conf file should be inferred invalid
            self.assertFalse(config.verify_chan_conf(new_info))

            # Check patching
            user_info = config.read_cfg_file(self.cfg_name, self.cfg_dir)
            self.assertEqual(user_info, new_info)

            # After patching, the channel conf file should be inferred valid
            self.assertTrue(config.verify_chan_conf(new_info))

        # Configuration based on an up-to-date file
        test_info = {
            "sat": {
                "name": "Galaxy 18",
                "alias": "G18",
                "dl_freq": 11913.4,
                "band": "Ku",
                "pol": "H",
                "ip": "172.16.235.1"
            },
            "freqs": {
                "dl": 11913.4,
                "lo": 10600.0,
                "l_band": 1313.4
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
        info = {
            'sat': defs.get_satellite_def('G18'),
            'lnb': defs.get_lnb_def('GEOSATpro', 'UL1PLL')
        }
        chan_file = os.path.join(self.cfg_dir, self.cfg_name + "-channel.conf")

        # First conf file
        config.write_chan_conf(info, chan_file)
        conf = config._parse_chan_conf(chan_file)
        self.assertEqual(int(conf['FREQUENCY']), info['sat']['dl_freq'] * 1e3)
        self.assertEqual(conf['POLARIZATION'], 'HORIZONTAL')
        self.assertEqual(conf['VIDEO_PID'], '32')

        # Change PID definitions and try generating the conf file again
        defs.pids = [60, 61]

        # Generate a conf file but refuse to overwrite the pre-existing one
        mock_yes_or_no.return_value = False
        config.write_chan_conf(info, chan_file)
        conf = config._parse_chan_conf(chan_file)
        # Nothing should be changed
        self.assertEqual(conf['VIDEO_PID'], '32')

        # Overwrite the pre-existing conf file
        mock_yes_or_no.return_value = True
        config.write_chan_conf(info, chan_file)
        conf = config._parse_chan_conf(chan_file)
        # Now the new PID settings should be in the file
        self.assertEqual(conf['VIDEO_PID'], '60+61')

        # Add the v1-pointed flag to change the polarization
        info['lnb']['v1_pointed'] = True
        info['lnb']['v1_psu_voltage'] = 13
        config.write_chan_conf(info, chan_file)
        conf = config._parse_chan_conf(chan_file)
        self.assertEqual(conf['POLARIZATION'], 'VERTICAL')

    def test_verify_chan_config(self):
        chan_file = config.get_chan_file_path(self.cfg_dir, self.cfg_name)
        info = {
            'sat': defs.get_satellite_def('G18'),
            'lnb': defs.get_lnb_def('GEOSATpro', 'UL1PLL'),
            'setup': {
                'channel': chan_file
            }
        }

        # First, generate the channel config file
        config.write_chan_conf(info, chan_file)

        # The verify function should check if the channel config file matches
        # with the configuration expected for the user's satellite and setup
        self.assertTrue(config.verify_chan_conf(info))

        # Change the satellite to one that is not in the config file
        info['sat'] = defs.get_satellite_def('T11N EU')
        self.assertFalse(config.verify_chan_conf(info))

    @patch('blocksatcli.util.ask_yes_or_no')
    def test_cfg_resetting(self, mock_yes_or_no):
        # Create the config file
        test_info = {'test': 123}
        config.write_cfg_file(self.cfg_name, self.cfg_dir, test_info)

        # Check creation
        user_info = config.read_cfg_file(self.cfg_name, self.cfg_dir)
        self.assertEqual(user_info, test_info)

        # Reset config file
        mock_yes_or_no.return_value = True
        cfg_file_name = config._cfg_file_name(self.cfg_name, self.cfg_dir)
        config._rst_cfg_file(cfg_file_name)

        # Check reset
        mock_yes_or_no.return_value = False
        user_info = config.read_cfg_file(self.cfg_name, self.cfg_dir)
        self.assertIsNone(user_info)


class TestConfigHelpers(TestCase):

    def test_net_if(self):
        info = {}

        # Standalone
        info['setup'] = defs.get_demod_def('Novra', 'S400')
        info['setup']['netdev'] = 'en0'
        self.assertEqual(config.get_net_if(info), 'en0')

        # USB types but adapter number not cached
        for model in ['5927', '5520SE']:
            info['setup'] = defs.get_demod_def('TBS', model)
            self.assertEqual(config.get_net_if(info), 'dvb0_0')

            # USB type with adapter number cached
            info['setup']['adapter'] = 2
            self.assertEqual(config.get_net_if(info), 'dvb2_0')

        # SDR
        info['setup'] = defs.get_demod_def('', 'RTL-SDR')
        self.assertEqual(config.get_net_if(info), 'lo')

        # Sat-IP
        info['setup'] = defs.get_demod_def('Selfsat', 'IP22')
        self.assertEqual(config.get_net_if(info), 'lo')

    def test_rx_model_and_marketing_name(self):
        info = {}

        info['setup'] = defs.get_demod_def('Novra', 'S400')
        self.assertEqual(config.get_rx_model(info), 'Novra S400')
        self.assertEqual(config._get_rx_marketing_name(info['setup']),
                         'Novra S400 (pro kit)')

        info['setup'] = defs.get_demod_def('TBS', '5927')
        self.assertEqual(config.get_rx_model(info), 'TBS 5927')
        self.assertEqual(config._get_rx_marketing_name(info['setup']),
                         'TBS 5927 (basic kit)')

        info['setup'] = defs.get_demod_def('TBS', '5520SE')
        self.assertEqual(config.get_rx_model(info), 'TBS 5520SE')
        self.assertEqual(config._get_rx_marketing_name(info['setup']),
                         'TBS 5520SE')

        info['setup'] = defs.get_demod_def('', 'RTL-SDR')
        self.assertEqual(config.get_rx_model(info), 'RTL-SDR')
        self.assertEqual(config._get_rx_marketing_name(info['setup']),
                         'RTL-SDR software-defined')

        info['setup'] = defs.get_demod_def('Selfsat', 'IP22')
        self.assertEqual(config.get_rx_model(info), 'Selfsat IP22')
        self.assertEqual(config._get_rx_marketing_name(info['setup']),
                         'Blockstream Base Station')

    def test_antenna_model(self):
        # Dish antennas on cm and m range
        info = {'setup': {'antenna': defs.get_antenna_def('45cm')}}
        self.assertEqual(config.get_antenna_model(info), '45cm dish')
        info['setup']['antenna']['size'] = 100
        self.assertEqual(config.get_antenna_model(info), '1m dish')
        info['setup']['antenna']['size'] = 120
        self.assertEqual(config.get_antenna_model(info), '1.2m dish')

        # Backwards compatibility with "custom" antenna lacking a type field
        info = {'setup': {'antenna': {'label': 'custom', 'size': 282.5}}}
        self.assertEqual(config.get_antenna_model(info), '2.825m dish')

        # Flat-panel
        info = {'setup': {'antenna': defs.get_antenna_def('H50D')}}
        self.assertEqual(config.get_antenna_model(info), 'Selfsat-H50D')

        # Sat-IP
        info = {'setup': {'antenna': defs.get_antenna_def('IP22')}}
        self.assertEqual(config.get_antenna_model(info), 'Selfsat>IP22')

    def test_lnb_model(self):
        info = {}
        info['lnb'] = defs.get_lnb_def('GEOSATpro', 'UL1PLL')
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

    def test_rx_label(self):
        info = {'setup': {'type': 'Linux USB'}}
        self.assertEqual(config.get_rx_label(info), 'usb')

        info = {'setup': {'type': 'Software-defined'}}
        self.assertEqual(config.get_rx_label(info), 'sdr')

        info = {'setup': {'type': 'Standalone'}}
        self.assertEqual(config.get_rx_label(info), 'standalone')

        info = {'setup': {'type': 'Sat-IP'}}
        self.assertEqual(config.get_rx_label(info), 'sat-ip')


class TestReceiversSetupConfig(TestEnv):

    def setUp(self):
        super().setUp()
        self.args = argparse.Namespace(cfg=self.cfg_name, cfg_dir=self.cfg_dir)

        # Expected configuration
        self.expected_config = {
            "sat": defs.get_satellite_def('G18'),
            "setup": defs.get_demod_def('Novra', 'S400'),
            "lnb": defs.get_lnb_def('GEOSATpro', 'UL1PLL'),
            "freqs": {
                "dl": 11913.4,
                "lo": 10600.0,
                "l_band": 1313.4
            }
        }
        self.expected_config['setup']['netdev'] = 'lo'
        self.expected_config['setup']['rx_ip'] = '192.168.1.2'
        self.expected_config['setup']['antenna'] = defs.get_antenna_def('45cm')
        self.expected_config['lnb']['v1_pointed'] = False

    @patch('os.listdir')
    @patch('builtins.input')
    def test_standalone_setup(self, mock_user_input, mock_eth_interface):
        """Test the Pro Kit Setup (Standalone Receiver)
        """
        # User Input:
        mock_user_input.side_effect = [
            0,  # Satellite: G18
            0,  # DVB-S2 receiver: Novra S400 (pro kit)
            0,  # Eth interface: lo
            'N',  # Manual IP: No
            0,  # Antenna: Satellite Dish (45cm / 18in)
            0,  # LNB: GEOSATpro UL1PLL
            'N'  # Power Supply: Not used before
        ]
        mock_eth_interface.return_value = ['lo', 'eth0']

        config.configure(self.args)
        cfg_info = config.read_cfg_file(self.cfg_name, self.cfg_dir)
        self.assertEqual(cfg_info, self.expected_config)

    @patch('os.listdir')
    @patch('builtins.input')
    def test_standalone_setup_interface_not_found(self, mock_user_input,
                                                  mock_eth_interface):
        """Test Standalone Receiver without found the network interface

        In this situation, the CLI should prompt for the network interface name
        instead of listing options.
        """
        # User Input:
        mock_user_input.side_effect = [
            0,  # Satellite: G18
            0,  # DVB-S2 receiver: Novra S400 (pro kit)
            'lo',  # Eth interface: lo
            'N',  # Manual IP: Yes
            0,  # Antenna: Satellite Dish (45cm / 18in)
            0,  # LNB: GEOSATpro UL1PLL
            'N'  # Power Supply: Not used before
        ]
        mock_eth_interface.side_effect = FileNotFoundError

        config.configure(self.args)
        cfg_info = config.read_cfg_file(self.cfg_name, self.cfg_dir)
        self.assertEqual(cfg_info, self.expected_config)

    @patch('os.listdir')
    @patch('builtins.input')
    def test_standalone_setup_with_custom_ip(self, mock_user_input,
                                             mock_eth_interface):
        """Test Standalone Receiver manually assigned IP
        """
        # User Input:
        mock_user_input.side_effect = [
            0,  # Satellite: G18
            0,  # DVB-S2 receiver: Novra S400 (pro kit)
            0,  # Eth interface: lo
            'y',  # Manual IP: Yes
            '192.168.0',  # Custom IP address (not valid)
            '192.168.1.2',  # Custom IP address (valid)
            0,  # Antenna: Satellite Dish (45cm / 18in)
            0,  # LNB: GEOSATpro UL1PLL
            'N'  # Power Supply: Not used before
        ]
        mock_eth_interface.return_value = ['lo', 'eth0']

        config.configure(self.args)
        cfg_info = config.read_cfg_file(self.cfg_name, self.cfg_dir)
        self.assertEqual(cfg_info, self.expected_config)

    @patch('builtins.input')
    def test_sat_ip_setup(self, mock_user_input):
        """Test the Satellite Base Station Setup (Sat-IP Receiver)
        """
        # User Input:
        mock_user_input.side_effect = [
            0,  # Satellite: G18
            4,  # DVB-S2 receiver: Blockstream Base Station
            'N'  # No static IP
        ]

        self.expected_config["setup"] = defs.get_demod_def('Selfsat', 'IP22')
        self.expected_config['setup']['antenna'] = defs.get_antenna_def('IP22')
        self.expected_config["lnb"] = defs.get_lnb_def('Selfsat',
                                                       'Integrated LNB')
        self.expected_config['lnb']['v1_pointed'] = False

        config.configure(self.args)
        cfg_info = config.read_cfg_file(self.cfg_name, self.cfg_dir)
        self.assertEqual(cfg_info, self.expected_config)

    @patch('builtins.input')
    def test_sat_ip_setup_with_static_address(self, mock_user_input):
        """Test the Satellite Base Station Setup (Sat-IP Receiver)
        """
        # User Input:
        static_ip = '192.168.10.3'
        mock_user_input.side_effect = [
            0,  # Satellite: G18
            4,  # DVB-S2 receiver: Blockstream Base Station
            'Y',  # No static IP
            static_ip
        ]

        self.expected_config["setup"] = defs.get_demod_def('Selfsat', 'IP22')
        self.expected_config['setup']['antenna'] = defs.get_antenna_def('IP22')
        self.expected_config['setup']['ip_addr'] = static_ip
        self.expected_config["lnb"] = defs.get_lnb_def('Selfsat',
                                                       'Integrated LNB')
        self.expected_config['lnb']['v1_pointed'] = False

        config.configure(self.args)
        cfg_info = config.read_cfg_file(self.cfg_name, self.cfg_dir)
        self.assertEqual(cfg_info, self.expected_config)

    @patch('builtins.input')
    def test_tbs_5927_setup(self, mock_user_input):
        """Test Linux USB Setup with TBS 5927 Receiver
        """
        # User Input:
        mock_user_input.side_effect = [
            0,  # Satellite: G18
            1,  # DVB-S2 receiver: TBS 5927
            0,  # Antenna: Satellite Dish (45cm / 18in)
            0,  # LNB: GEOSATpro UL1PLL
            'N'  # Power Supply: Not used before
        ]
        self.expected_config["setup"] = defs.get_demod_def('TBS', '5927')
        self.expected_config['setup']['antenna'] = defs.get_antenna_def('45cm')
        self.expected_config["setup"][
            'channel'] = f"{self.cfg_dir}/{self.cfg_name}-channel.conf"

        config.configure(self.args)
        cfg_info = config.read_cfg_file(self.cfg_name, self.cfg_dir)
        self.assertEqual(cfg_info, self.expected_config)

    @patch('builtins.input')
    def test_tbs_5520SE_setup(self, mock_user_input):
        """Test Linux USB Setup with TBS 5520SE Receiver
        """
        # User Input:
        mock_user_input.side_effect = [
            0,  # Satellite: G18
            2,  # DVB-S2 receiver: TBS 5520SE
            0,  # Antenna: Satellite Dish (45cm / 18in)
            0,  # LNB: GEOSATpro UL1PLL
            'N'  # Power Supply: Not used before
        ]
        self.expected_config["setup"] = defs.get_demod_def('TBS', '5520SE')
        self.expected_config['setup']['antenna'] = defs.get_antenna_def('45cm')
        self.expected_config["setup"][
            'channel'] = f"{self.cfg_dir}/{self.cfg_name}-channel.conf"
        config.configure(self.args)
        cfg_info = config.read_cfg_file(self.cfg_name, self.cfg_dir)
        self.assertEqual(cfg_info, self.expected_config)

    @patch('builtins.input')
    @patch('blocksatcli.gqrx.os.path.expanduser')
    def test_sdr_setup(self, mock_user_home, mock_user_input):
        """Test Software-defined Radio (SDR) Setup
        """
        # User Input:
        mock_user_input.side_effect = [
            0,  # Satellite: G18
            3,  # DVB-S2 receiver: SDR
            0,  # Antenna: Satellite Dish (45cm / 18in)
            0,  # LNB: GEOSATpro UL1PLL
            0,  # Power Supply: Directv 21 Volt Power
            'y'  # Generate gqrx config file
        ]

        # Mock the user's home directory so that the gqrx conf is saved on the
        # temporary test directory
        mock_user_home.return_value = self.cfg_dir
        gqrx_path = os.path.join(self.cfg_dir, '.config', 'gqrx')
        gqrx_conf_file = os.path.join(gqrx_path, 'default.conf')

        self.expected_config["setup"] = defs.get_demod_def('', 'RTL-SDR')
        self.expected_config['setup']['antenna'] = defs.get_antenna_def('45cm')
        self.expected_config["lnb"].pop("v1_pointed")
        self.expected_config["lnb"]["psu_voltage"] = 21

        config.configure(self.args)
        cfg_info = config.read_cfg_file(self.cfg_name, self.cfg_dir)
        self.assertEqual(cfg_info, self.expected_config)
        self.assertTrue(os.path.exists(gqrx_conf_file))

    @patch('os.listdir')
    @patch('builtins.input')
    def test_setup_with_custom_ku_band_lnb(self, mock_user_input,
                                           mock_eth_interface):
        """Test setup with custom Ku band LNB
        """
        # User Input:
        mock_user_input.side_effect = [
            0,  # Satellite: G18
            0,  # DVB-S2 receiver: Novra S400 (pro kit)
            0,  # Eth interface: lo
            'N',  # Manual IP: No
            0,  # Antenna: Satellite Dish (45cm / 18in)
            3,  # LNB: Other
            1,  # LNB Frequency band: Ku
            'Y',  # LNB Universal Ku Band: Yes
            'Y',  # LNB Covers 10.7 to 12.75 GHz input range: Yes
            'Y',  # LNB LO frequencies of 9750 and 10600: Yes
            1  # LNB Polarization: Horizontal
        ]
        mock_eth_interface.return_value = ['lo', 'eth0']

        self.expected_config["lnb"] = {
            "vendor": "",
            "model": "",
            "in_range": [10700.0, 12750.0],
            "lo_freq": [9750.0, 10600.0],
            "universal": True,
            "band": "Ku",
            "pol": "H"
        }

        config.configure(self.args)
        cfg_info = config.read_cfg_file(self.cfg_name, self.cfg_dir)
        self.assertEqual(cfg_info, self.expected_config)

    @patch('os.listdir')
    @patch('builtins.input')
    def test_setup_with_custom_ku_band_lnb_with_different_freq_range(
            self, mock_user_input, mock_eth_interface):
        """Test setup with custom LNB with different frequency range
        """
        # User Input:
        mock_user_input.side_effect = [
            0,  # Satellite: G18
            0,  # DVB-S2 receiver: Novra S400 (pro kit)
            0,  # Eth interface: lo
            'N',  # Manual IP: No
            0,  # Antenna: Satellite Dish (45cm / 18in)
            3,  # LNB: Other
            1,  # LNB Frequency band: Ku
            'Y',  # LNB Universal Ku Band: Yes
            'n',  # LNB Covers 10.7 to 12.75 GHz input range: No
            'invalid input',  # LNB Frequency Range (invalid input)
            '10,12',  # LNB Frequency Range (invalid input)
            '12400,10600',  # LNB Frequency Range (wrong order)
            '10600,12400',  # LNB Frequency Range (valid input)
            'n',  # LNB LO frequency at specify range: No
            'invalid input',  # LNB two LO frequencies (invalid input)
            '9,10',  # LNB two LO frequencies (invalid input)
            '10600,9750',  # LNB two LO frequencies (wrong order)
            '9750,10600',  # LNB two LO frequencies (valid input)
            0,  # LNB Polarization: Dual
            0  # Power Supply: Directv 21 Volt
        ]
        mock_eth_interface.return_value = ['lo', 'eth0']

        self.expected_config["lnb"] = {
            "vendor": "",
            "model": "",
            "in_range": [10600.0, 12400.0],
            "lo_freq": [9750.0, 10600.0],
            "universal": True,
            "band": "Ku",
            "pol": "Dual",
            "v1_pointed": False
        }

        config.configure(self.args)
        cfg_info = config.read_cfg_file(self.cfg_name, self.cfg_dir)
        self.assertEqual(cfg_info, self.expected_config)

    @patch('os.listdir')
    @patch('builtins.input')
    def test_setup_with_custom_ku_band_lnb_not_universal(
            self, mock_user_input, mock_eth_interface):
        """Test setup with custom LNB not universal
        """
        # User Input:
        mock_user_input.side_effect = [
            0,  # Satellite: G18
            0,  # DVB-S2 receiver: Novra S400 (pro kit)
            0,  # Eth interface: lo
            'N',  # Manual IP: No
            0,  # Antenna: Satellite Dish (45cm / 18in)
            3,  # LNB: Other
            1,  # LNB Frequency band: Ku
            'N',  # LNB Universal Ku band: No
            '10700,12750',  # LNB Frequency Range
            10,  # LNB LO frequency (invalid input)
            10400,  # LNB LO frequency (valid input)
            2,  # LNB Polarization: Vertical
            0  # Power Supply: Directv 21 Volt
        ]
        mock_eth_interface.return_value = ['lo', 'eth0']
        self.maxDiff = None

        self.expected_config["lnb"] = {
            "vendor": "",
            "model": "",
            "in_range": [10700.0, 12750.0],
            "lo_freq": 10400.0,
            "universal": False,
            "band": "Ku",
            "pol": "V"
        }
        self.expected_config["freqs"] = {
            "dl": 11913.4,
            "lo": 10400.0,
            "l_band": 1513.4
        }

        config.configure(self.args)
        cfg_info = config.read_cfg_file(self.cfg_name, self.cfg_dir)
        self.assertEqual(cfg_info, self.expected_config)

    @patch('os.listdir')
    @patch('builtins.input')
    def test_setup_with_custom_c_band_lnb(self, mock_user_input,
                                          mock_eth_interface):
        """Test setup with custom C Band LNB
        """
        # User Input:
        mock_user_input.side_effect = [
            3,  # Satellite: T18V C
            0,  # DVB-S2 receiver: Novra S400 (pro kit)
            0,  # Eth interface: lo
            'N',  # Manual IP: No
            0,  # Antenna: Satellite Dish (45cm)
            1,  # LNB: Other
            0,  # LNB Frequency band: C
            '3400,4800',  # LNB Frequency Range
            5150,  # LNB LO frequency
            2  # LNB Polarization: Vertical
        ]
        mock_eth_interface.return_value = ['lo', 'eth0']
        self.maxDiff = None

        self.expected_config["sat"] = defs.get_satellite_def('T18V C')
        self.expected_config["setup"]["antenna"] = defs.get_antenna_def('45cm')
        self.expected_config["lnb"] = {
            "vendor": "",
            "model": "",
            "in_range": [3400.0, 4800.0],
            "lo_freq": 5150.0,
            "universal": False,
            "band": "C",
            "pol": "V"
        }
        self.expected_config["freqs"] = {
            "dl": 4140.0,
            "lo": 5150.0,
            "l_band": 1010.0
        }

        # Continue with invalid frequency range
        config.configure(self.args)
        cfg_info = config.read_cfg_file(self.cfg_name, self.cfg_dir)
        self.assertEqual(cfg_info, self.expected_config)

    @patch('os.listdir')
    @patch('builtins.input')
    def test_setup_with_custom_c_band_lnb_invalid_freq_range(
            self, mock_user_input, mock_eth_interface):
        """Test setup with custom C Band LNB with invalid frequency range
        """
        # User Input:
        mock_user_input.side_effect = [
            3,  # Satellite: T18V C
            0,  # DVB-S2 receiver: Novra S400 (pro kit)
            0,  # Eth interface: lo
            'N',  # Manual IP: No
            0,  # Antenna: Satellite Dish (45cm)
            1,  # LNB: Other
            0,  # LNB Frequency band: C
            '10700,12750',  # Invalid LNB frequency range
            '3400,4200',  # Valid LNB frequency range
            5150,  # LNB LO frequency
            2  # LNB Polarization: Vertical
        ]
        mock_eth_interface.return_value = ['lo', 'eth0']

        self.expected_config["sat"] = defs.get_satellite_def('T18V C')
        self.expected_config["setup"]["antenna"] = defs.get_antenna_def('45cm')
        self.expected_config["lnb"] = {
            "vendor": "",
            "model": "",
            "in_range": [3400.0, 4200.0],
            "lo_freq": 5150.0,
            "universal": False,
            "band": "C",
            "pol": "V"
        }
        self.expected_config["freqs"] = {
            "dl": 4140.0,
            "lo": 5150.0,
            "l_band": 1010.0
        }

        config.configure(self.args)
        cfg_info = config.read_cfg_file(self.cfg_name, self.cfg_dir)
        self.assertEqual(cfg_info, self.expected_config)

    @patch('builtins.input')
    def test_ku_band_satellite_with_c_band_lnb(self, mock_user_input):
        """Test KU band satellite with C band LNB
        """
        # User Input:
        mock_user_input.side_effect = [
            0,  # Satellite: G18
            3,  # DVB-S2 receiver: SDR
            0,  # Antenna: Satellite Dish (45cm / 18in)
            3,  # LNB: Other
            0  # LNB Frequency band: C
        ]
        with self.assertRaises(SystemExit):
            # Must use Ku band LNB to receive from G18
            config.configure(self.args)

    @patch('os.listdir')
    @patch('builtins.input')
    def test_standalone_setup_with_custom_antenna(self, mock_user_input,
                                                  mock_eth_interface):
        """Test Standalone Receiver with custom antenna
        """
        # User Input:
        mock_user_input.side_effect = [
            0,  # Satellite: G18
            0,  # DVB-S2 receiver: Novra S400 (pro kit)
            0,  # Eth interface: lo
            'N',  # Manual IP: No
            10,  # Antenna: Other
            60,  # Antenna size in cm
            0,  # LNB: GEOSATpro UL1PLL
            'N'  # LNB not pointed before
        ]
        mock_eth_interface.return_value = ['lo', 'eth0']

        self.expected_config["setup"]["antenna"] = {
            "label": "custom",
            "type": "dish",
            "size": 60
        }

        config.configure(self.args)
        cfg_info = config.read_cfg_file(self.cfg_name, self.cfg_dir)
        self.assertEqual(cfg_info, self.expected_config)
