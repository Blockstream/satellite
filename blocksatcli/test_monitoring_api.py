import os
import shutil
import unittest
from unittest.mock import patch

from . import monitoring_api
from . import config
from .api.gpg import Gpg


class TestMonitoringApi(unittest.TestCase):

    def setUp(self):
        self.gpghome = "/tmp/.gnupg-test-monitoring-api"
        self.cfg_dir = "/tmp/.config-test-monitoring-api"
        self.cfg_name = "test-file"

        for directory in [self.cfg_dir, self.gpghome]:
            if not os.path.exists(directory):
                os.makedirs(directory)

    def tearDown(self):
        for directory in [self.cfg_dir, self.gpghome]:
            if os.path.exists(directory):
                shutil.rmtree(directory, ignore_errors=True)

    def create_receiver_cfg_file(self,
                                 registered=False,
                                 gen_gpg_key=False,
                                 has_password=False):
        self.test_info = {}

        # Add monitoring information if registered
        if registered:
            self.test_info['monitoring'] = {
                'registered': True,
                'uuid': 'test-uuid',
                'fingerprint': 'test-fingerprint',
                'has_password': has_password
            }

        # Create and update the uuid and fingerprint if using a real GPG key
        if gen_gpg_key:
            name = "Test"
            email = "test@test.com"
            comment = "comment"
            passphrase = "test"
            self.gpg = Gpg(self.gpghome)
            self.gpg.create_keys(name, email, comment, passphrase)
            self.fingerprint = self.gpg.get_default_public_key()['fingerprint']

            if registered:
                self.test_info['monitoring']['fingerprint'] = self.fingerprint

        config.write_cfg_file(self.cfg_name, self.cfg_dir, self.test_info)

    @patch('blocksatcli.util.prompt_for_enter')
    @patch('blocksatcli.monitoring_api.requests.post')
    def test_request_and_reset_monitoring_api_password(self, mock_api_post,
                                                       mock_prompt_for_enter):
        # Create a configuration file with monitoring.registered=True and
        # monitoring.has_password=False.
        self.create_receiver_cfg_file(registered=True, gen_gpg_key=True)
        user_info = config.read_cfg_file(self.cfg_name, self.cfg_dir)
        self.assertTrue('monitoring' in user_info)

        # Given that has_password=False, the BsMonitoring constructor should
        # request a new password from the Monitoring API.
        mock_api_post.return_value.status_code = 200
        mock_api_post.return_value.json.return_value = {
            'new_password': 'password1'
        }
        monitor_api = monitoring_api.BsMonitoring(self.cfg_name,
                                                  self.cfg_dir,
                                                  self.gpghome,
                                                  passphrase="test")

        # Check if the flag that indicates the password availability was set.
        self.assertTrue(monitor_api.user_info['monitoring']['has_password'])

        # Make sure the password is available in the monitoring object
        self.assertEqual(monitor_api.api_pwd, 'password1')

        # Test if the saved password can be loaded and decrypted correctly when
        # instantiating another BsMonitoring object
        monitor_api2 = monitoring_api.BsMonitoring(self.cfg_name,
                                                   self.cfg_dir,
                                                   self.gpghome,
                                                   passphrase="test")
        self.assertEqual(monitor_api2.api_pwd, 'password1')

        # Create a third BsMonitoring object requesting a password reset using
        # option 'reset_api_pwd'
        mock_api_post.return_value.status_code = 200
        mock_api_post.return_value.json.return_value = {
            'new_password': 'password2'
        }
        monitor_api3 = monitoring_api.BsMonitoring(self.cfg_name,
                                                   self.cfg_dir,
                                                   self.gpghome,
                                                   passphrase="test",
                                                   reset_api_pwd=True)
        self.assertEqual(monitor_api3.api_pwd, 'password2')

        # Any subsequent object should load the new password
        monitor_api4 = monitoring_api.BsMonitoring(self.cfg_name,
                                                   self.cfg_dir,
                                                   self.gpghome,
                                                   passphrase="test")
        self.assertEqual(monitor_api4.api_pwd, 'password2')
