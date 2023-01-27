import os
import shutil
import unittest
from unittest.mock import patch

from . import config
from . import monitoring
from .api.gpg import Gpg
from .monitoring_api import metric_endpoint

gpghome = "/tmp/.gnupg-test-monitoring"
cfg_dir = "/tmp/.config-test-monitoring"
cfg_name = "test-file"


def create_receiver_cfg_file(registered=False,
                             gen_gpg_key=False,
                             has_password=False):
    test_info = {"sat": {"name": "Galaxy 18", "alias": "G18"}}

    # Add monitoring information if registered
    if registered:
        test_info['monitoring'] = {
            'registered': True,
            'uuid': 'test-uuid',
            'fingerprint': 'test-fingerprint',
            'has_password': has_password
        }

    # Create and update the uuid and fingerprint if using real GPG key
    if gen_gpg_key:
        gpg = Gpg(gpghome)
        gpg.create_keys("Test", "test@test.com", "", "test")
        fingerprint = gpg.get_default_public_key()['fingerprint']

        if registered:
            test_info['monitoring']['fingerprint'] = fingerprint

    # Write configuration
    config.write_cfg_file(cfg_name, cfg_dir, test_info)

    return test_info


class TestReceiverReporter(unittest.TestCase):

    def setUp(self):
        # Create directories
        for directory in [cfg_dir, gpghome]:
            if not os.path.exists(directory):
                os.makedirs(directory)

    def tearDown(self):
        for directory in [cfg_dir, gpghome]:
            if os.path.exists(directory):
                shutil.rmtree(directory, ignore_errors=True)

    def create_reporter_instance_with_receiver_cfg(
            self,
            report_endpoint=metric_endpoint,
            rx_registered=False,
            gen_gpg_key=False,
            reset_api_pwd=False):

        # Create receiver configuration file
        self.test_info = create_receiver_cfg_file(registered=rx_registered,
                                                  gen_gpg_key=gen_gpg_key)

        # Create reporter instance
        return monitoring.Reporter(cfg=cfg_name,
                                   cfg_dir=cfg_dir,
                                   dest_addr=report_endpoint,
                                   hostname='hostname-test',
                                   gnupghome=gpghome,
                                   passphrase='test',
                                   reset_api_pwd=reset_api_pwd)

    @patch('blocksatcli.util.prompt_for_enter')
    @patch('blocksatcli.monitoring.requests.post')
    def test_sign_metrics_with_monitoring_password(self, mock_api_post,
                                                   mock_prompt_for_enter):
        mock_api_post.return_value.status_code = 200
        mock_api_post.return_value.json.return_value = {
            'new_password': 'generated-password'
        }

        reporter = self.create_reporter_instance_with_receiver_cfg(
            rx_registered=True, gen_gpg_key=True)

        # Send metrics
        metrics = {'test': 'test'}
        reporter.send(metrics)

        # Assert information sent to monitoring API
        mock_api_post.assert_called_with(metric_endpoint,
                                         json={
                                             'test': 'test',
                                             'uuid': 'test-uuid',
                                             'password': 'generated-password',
                                         },
                                         cert=(None, None))
