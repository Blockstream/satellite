import os
import zipfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch
from urllib.error import URLError

from .upnp import SSDPDevice
from . import satip


def _gen_ssdp_dev(addr, friendly_name):
    resp = ('HTTP/1.1 200 OK\r\n'
            'LOCATION: http://{}:8000/description.xml\r\n'
            'BOOTID.UPNP.ORG: 24\r\n').format(addr[0])
    ssdp_dev = SSDPDevice(addr, resp)
    ssdp_dev.friendly_name = friendly_name
    return ssdp_dev


def _mock_fw_upgrade(url, local_path, progress_callback):
    # Create a mock upgrade file
    with zipfile.ZipFile(local_path, 'w') as zip_ref:
        supg_file = os.path.join(os.path.dirname(local_path), 'upgrade.supg')
        Path(supg_file).touch()
        zip_ref.write(supg_file)


class MockResponse():
    """Mock requests response"""

    def __init__(self, text="", json={}):
        self.text = text
        self._json = json

    def raise_for_status(self):
        pass

    def json(self):
        return self._json


class TestApi(TestCase):

    @patch('urllib.request.urlopen')
    @patch('blocksatcli.util.ask_multiple_choice')
    @patch('blocksatcli.upnp.UPnP.discover')
    def test_discover(self, mock_upnp_discover, mock_ask_multi_choice,
                      mock_urllib_urlopen):
        """Test Sat-IP device discovery"""
        # Raise a mocked URLError instead of trying to open the URL to get the
        # description from the faked devices.
        mock_urllib_urlopen.side_effect = URLError('mocked method')

        addr1 = ('192.168.9.50', 33783)
        addr2 = ('192.168.9.51', 33781)
        wrong_ssdp_dev = _gen_ssdp_dev(addr1, 'Test-Dev')
        satip_ssdp_dev1 = _gen_ssdp_dev(addr1, 'SELFSAT-IP')
        satip_ssdp_dev2 = _gen_ssdp_dev(addr2, 'SELFSAT-IP')

        # UPnP does not discover any device
        mock_upnp_discover.return_value = []
        sat_ip = satip.SatIp()
        sat_ip.select_receiver()
        self.assertIsNone(sat_ip.host)

        # UPnP discovers a device, but not the Sat-IP receiver
        mock_upnp_discover.return_value = [wrong_ssdp_dev]
        sat_ip = satip.SatIp()
        sat_ip.select_receiver()
        self.assertIsNone(sat_ip.host)

        # UPnP discovers the Sat-IP receiver
        mock_upnp_discover.return_value = [satip_ssdp_dev1]
        sat_ip = satip.SatIp()
        sat_ip.select_receiver()
        self.assertEqual(sat_ip.host, addr1[0])

        # UPnP discovers multiple Sat-IP receivers in non-interactive mode
        mock_upnp_discover.return_value = [satip_ssdp_dev1, satip_ssdp_dev2]
        sat_ip = satip.SatIp()
        sat_ip.select_receiver(interactive=False)
        self.assertEqual(sat_ip.host, addr1[0])

        # UPnP discovers multiple Sat-IP receivers in interactive mode
        mock_ask_multi_choice.return_value = {
            'host': satip_ssdp_dev2.host,
            'base_url': satip_ssdp_dev2.base_url
        }
        sat_ip = satip.SatIp()
        sat_ip.select_receiver(interactive=True)
        self.assertEqual(sat_ip.host, addr2[0])

    @patch('requests.get')
    def test_fw_check(self, mock_get):
        """Test Sat-IP firmware validation"""

        # Old firmware version that does not satisfy the minimum
        mock_get.return_value = MockResponse("2.2.19")
        sat_ip = satip.SatIp()
        sat_ip.set_server_addr("192.168.100.2")
        self.assertFalse(sat_ip.check_fw_version())

        # Recent firmware version satisfying the minimum
        mock_get.return_value = MockResponse("3.1.18")
        sat_ip = satip.SatIp()
        sat_ip.set_server_addr("192.168.100.2")
        self.assertTrue(sat_ip.check_fw_version())

    @patch('requests.post')
    @patch('blocksatcli.util.urlretrieve')
    def test_fw_upgrade(self, mock_urlretrieve, mock_post):
        """Test Sat-IP firmware upgrade"""
        mock_post.return_value = MockResponse(
            json={
                'status': "0",
                'thisver': {
                    'sw_ver': "2.2.19"
                },
                'newver': {
                    'sw_ver': "3.1.18"
                }
            })
        mock_urlretrieve.side_effect = _mock_fw_upgrade
        sat_ip = satip.SatIp()
        sat_ip.set_server_addr("192.168.100.2")
        fw_upgrade_ok = sat_ip.upgrade_fw("/tmp/",
                                          interactive=False,
                                          no_wait=True)
        self.assertTrue(fw_upgrade_ok)
