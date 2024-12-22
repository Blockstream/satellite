from unittest.mock import patch

from . import config, monitoring_api
from .test_helpers import TestEnv, create_test_setup


class TestMonitoringApi(TestEnv):

    def setUp(self):
        self.server_url = 'http://test-server'
        super().setUp()

    @patch('blocksatcli.util.prompt_for_enter')
    @patch('blocksatcli.monitoring_api.requests.post')
    def test_request_and_reset_monitoring_api_password(self, mock_api_post,
                                                       mock_prompt_for_enter):
        # Create a configuration file with monitoring.registered=True and
        # monitoring.has_password=False.
        user_info = create_test_setup(self.cfg_name,
                                      self.cfg_dir,
                                      self.gpghome,
                                      mon_api_registered=True,
                                      gen_gpg_key=True,
                                      mon_api_has_password=False)
        self.assertTrue('monitoring' in user_info)

        # Given that has_password=False, the BsMonitoring constructor should
        # request a new password from the Monitoring API.
        mock_api_post.return_value.status_code = 200
        mock_api_post.return_value.json.return_value = {
            'new_password': 'password1'
        }
        monitor_api = monitoring_api.BsMonitoring(self.cfg_name,
                                                  self.cfg_dir,
                                                  self.server_url,
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
                                                   self.server_url,
                                                   self.gpghome,
                                                   passphrase="test")
        self.assertEqual(monitor_api2.api_pwd, 'password1')

    @patch('blocksatcli.monitoring_api.BsMonitoring._register')
    def test_save_credentials(self, mock_register):
        """Test saving receiver credentials in the configuration file
        """
        # Create a configuration file with unregistered receiver
        user_info = create_test_setup(self.cfg_name,
                                      self.cfg_dir,
                                      self.gpghome,
                                      mon_api_registered=False,
                                      gen_gpg_key=False,
                                      mon_api_has_password=False)

        # The monitoring key is only placed in the configuration file once the
        # receiver is properly registered.
        self.assertFalse('monitoring' in user_info)

        # Since the receiver is not registered yet, the BsMonitoring handler
        # should run the registration function.
        monitor_api = monitoring_api.BsMonitoring(self.cfg_name,
                                                  self.cfg_dir,
                                                  self.server_url,
                                                  self.gpghome,
                                                  passphrase=None)
        self.assertTrue(mock_register.called)

        # The receiver credentials should be saved in the cfg file
        monitor_api._save_credentials('test-uuid', 'test-fingerprint')
        user_info = config.read_cfg_file(self.cfg_name, self.cfg_dir)
        self.assertTrue('monitoring' in user_info)
        self.assertTrue(user_info['monitoring']['registered'])
        self.assertEqual(user_info['monitoring']['uuid'], 'test-uuid')
        self.assertEqual(user_info['monitoring']['fingerprint'],
                         'test-fingerprint')
        self.assertFalse(user_info['monitoring']['has_password'])

    @patch('blocksatcli.monitoring_api.BsMonitoring._setup_registered')
    def test_delete_credentials(self, mock_setup_registered):
        """Test deleting receiver credentials from the configuration file
        """
        # Create a configuration file with receiver registered
        user_info = create_test_setup(self.cfg_name,
                                      self.cfg_dir,
                                      self.gpghome,
                                      mon_api_registered=True,
                                      gen_gpg_key=False,
                                      mon_api_has_password=False)
        self.assertTrue('monitoring' in user_info)

        # The receiver is registered (i.e., the 'monitoring' key is in the
        # configuration file), so the BsMonitoring handler should run the setup
        # function for registered receivers. Check:
        monitor_api = monitoring_api.BsMonitoring(self.cfg_name,
                                                  self.cfg_dir,
                                                  self.server_url,
                                                  self.gpghome,
                                                  passphrase=None)
        self.assertTrue(mock_setup_registered.called)

        # Delete the receiver credentials from the configuration file
        monitor_api.delete_credentials()
        user_info = config.read_cfg_file(self.cfg_name, self.cfg_dir)
        self.assertFalse('monitoring' in user_info)

    @patch('blocksatcli.monitoring_api.requests.post')
    @patch('blocksatcli.monitoring_api.BsMonitoring._setup_registered')
    def test_sign_request_with_gpg(self, mock_registered, mock_api_post):
        """Test sign requests with GPG
        """
        create_test_setup(self.cfg_name,
                          self.cfg_dir,
                          self.gpghome,
                          mon_api_registered=True,
                          gen_gpg_key=True,
                          mon_api_has_password=False)

        # Since the non-GPG password is not defined yet, the BsMonitoring
        # constructor will try to configure one. Pretend this step fails so
        # that the subsequent reports are authenticated with the GPG mechanism.
        mock_api_post.return_value.status_code = 400
        monitor_api = monitoring_api.BsMonitoring(self.cfg_name,
                                                  self.cfg_dir,
                                                  self.server_url,
                                                  self.gpghome,
                                                  passphrase="test")

        # Test sign request with GPG method
        report = {"test": "test"}
        monitor_api.sign_request(report, password_allowed=False)
        self.assertTrue("uuid" in report)
        self.assertTrue("signature" in report)

    def test_sign_request_with_password(self):
        """Test signing request with a password
        """
        create_test_setup(self.cfg_name,
                          self.cfg_dir,
                          self.gpghome,
                          mon_api_registered=True,
                          gen_gpg_key=True,
                          mon_api_gen_password=True)

        monitor_api = monitoring_api.BsMonitoring(self.cfg_name,
                                                  self.cfg_dir,
                                                  self.server_url,
                                                  self.gpghome,
                                                  passphrase="test")

        # Test sign request with password method
        report = {"test": "test"}
        monitor_api.sign_request(report, password_allowed=True)
        self.assertTrue("uuid" in report)
        self.assertTrue("password" in report)

    @patch('blocksatcli.monitoring_api.BsMonitoring._register_thread')
    @patch('builtins.input')
    @patch('blocksatcli.util.prompt_for_enter')
    def test_user_interaction_in_register_procedure(self,
                                                    mock_prompt_for_enter,
                                                    mock_user_input,
                                                    mock_register_thread):
        """Test user interaction in the register procedure
        """
        # Mock user input
        mock_user_input.side_effect = [
            'y',  # show explainer
            'City',
            'State',
            'Country',
            'y'  # confirm address
        ]

        # Create a configuration file with an unregistered receiver
        create_test_setup(self.cfg_name,
                          self.cfg_dir,
                          self.gpghome,
                          mon_api_registered=False,
                          gen_gpg_key=True,
                          mon_api_has_password=False)

        # The monitoring api will launch the registration function
        monitoring_api.BsMonitoring(self.cfg_name,
                                    self.cfg_dir,
                                    self.server_url,
                                    self.gpghome,
                                    passphrase="test")

        # Confirm the information sent to the register_thread function
        fingerprint = self.gpg.get_default_priv_key()['fingerprint']
        pubkey = self.gpg.gpg.export_keys(fingerprint)
        mock_register_thread.assert_called_with(
            # Fingerprint
            fingerprint,
            # Public Key
            pubkey,
            # Address
            'City, State, Country',
            # Satellite
            'G18',
            # Rx Type
            'Selfsat IP22',
            # Antenna
            'Selfsat>IP22',
            # LNB
            'Selfsat Integrated LNB')

    @patch('blocksatcli.monitoring_api.BsMonitoring.gen_api_password')
    @patch('blocksatcli.monitoring_api.requests.patch')
    @patch('blocksatcli.monitoring_api.queue.Queue')
    @patch('blocksatcli.monitoring_api.ApiListener')
    @patch('blocksatcli.monitoring_api.requests.post')
    @patch('blocksatcli.monitoring_api.BsMonitoring._register')
    def test_api_interaction_in_register_procedure(self, mock_register,
                                                   mock_api_post,
                                                   mock_listener, mock_queue,
                                                   mock_api_patch,
                                                   mock_gen_api_pwd):
        """Test interaction with the APIs in register procedure
        """
        # Create a configuration file with an unregistered receiver
        user_info = create_test_setup(self.cfg_name,
                                      self.cfg_dir,
                                      self.gpghome,
                                      mon_api_registered=False,
                                      gen_gpg_key=True)
        fingerprint = self.gpg.get_default_priv_key()['fingerprint']
        self.assertFalse('monitoring' in user_info)

        # For the initial registration, the BsMonitoring handler first signs up
        # with the Monitoring API via a POST request and gets the account UUID.
        # Then, it confirms the 2FA validation key via a PATCH request.
        mock_api_post.return_value.status_code = 200
        mock_api_post.return_value.json.return_value = {
            'uuid': 'test-uuid',
            'verified': False
        }
        mock_queue.return_value.get.return_value = b'validation-key'
        mock_api_patch.return_value.status_code = 200

        # For the initial registration, the BsMonitoring object calls the
        # _register_thread function on a thread.
        monitor_api = monitoring_api.BsMonitoring(self.cfg_name,
                                                  self.cfg_dir,
                                                  self.server_url,
                                                  self.gpghome,
                                                  passphrase="test")
        monitor_api.rx_lock_event.set()
        monitor_api._register_thread(fingerprint, "pubkey", "address",
                                     "satellite", "rx_type", "antenna", "lnb")

        # Check the arguments sent to API via post method to sign-up to
        # the monitoring server
        mock_api_post.assert_called_with(self.server_url + '/accounts',
                                         json={
                                             'fingerprint': fingerprint,
                                             'publickey': 'pubkey',
                                             'city': 'address',
                                             'satellite': 'satellite',
                                             'receiver_type': 'rx_type',
                                             'antenna': 'antenna',
                                             'lnb': 'lnb'
                                         })

        # Check arguments sent to the API via patch method
        mock_api_patch.assert_called_with(self.server_url + '/accounts',
                                          json={
                                              'uuid': 'test-uuid',
                                              'validation_key':
                                              'validation-key'
                                          })

        # After the 2FA procedure is done, the _register_thread function
        # generates a password for non-GPG authentication. Confirm:
        self.assertTrue(mock_gen_api_pwd.called)

        # Assert that the registration procedure has run successfully
        self.assertFalse(monitor_api.registration_running)
        self.assertFalse(monitor_api.registration_failure)

        # Check the configuration file
        user_info = config.read_cfg_file(self.cfg_name, self.cfg_dir)
        self.assertTrue('monitoring' in user_info)
        self.assertTrue(user_info['monitoring']['registered'])
        self.assertEqual(user_info['monitoring']['uuid'], 'test-uuid')
        self.assertEqual(user_info['monitoring']['fingerprint'], fingerprint)

    @patch('blocksatcli.monitoring_api.BsMonitoring._register')
    @patch('blocksatcli.util.ask_yes_or_no')
    def test_monitor_setup_with_registered_receiver_and_missing_gpg_key(
            self, mock_yes_or_no, mock_register):
        # Create a configuration file with a registered receiver
        user_info = create_test_setup(self.cfg_name,
                                      self.cfg_dir,
                                      self.gpghome,
                                      mon_api_registered=True,
                                      gen_gpg_key=True,
                                      mon_api_has_password=False)
        self.assertTrue('monitoring' in user_info)

        # Change path to the GPG home. This way the CLI will not find the
        # correct GPG key in the keyring
        self.gpghome = "/tmp/"

        # Assert logger error if key is not found in the local keyring
        with self.assertLogs(monitoring_api.logger, level='ERROR'):
            mock_yes_or_no.return_value = 'y'  # Reset credentials
            monitoring_api.BsMonitoring(self.cfg_name,
                                        self.cfg_dir,
                                        self.server_url,
                                        self.gpghome,
                                        passphrase="test")

        # Make sure that the old credentials were deleted and a new
        # registration was initiated by calling the _register function:
        user_info = config.read_cfg_file(self.cfg_name, self.cfg_dir)
        self.assertFalse('monitoring' in user_info)
        mock_register.assert_called()

    @patch('blocksatcli.monitoring_api.requests.patch')
    @patch('blocksatcli.monitoring_api.queue.Queue')
    @patch('blocksatcli.monitoring_api.ApiListener')
    @patch('blocksatcli.monitoring_api.requests.post')
    @patch('blocksatcli.monitoring_api.BsMonitoring._register')
    def test_failed_api_communication_in_registration_process(
            self, mock_register, mock_api_post, mock_listener, mock_queue,
            mock_api_patch):
        # Create a configuration file with an unregistered receiver
        user_info = create_test_setup(self.cfg_name,
                                      self.cfg_dir,
                                      self.gpghome,
                                      mon_api_registered=False,
                                      gen_gpg_key=True,
                                      mon_api_has_password=False)
        fingerprint = self.gpg.get_default_priv_key()['fingerprint']
        self.assertFalse('monitoring' in user_info)

        # Set status code different than 200
        mock_api_post.return_value.status_code = 502

        # Assert logger error
        with self.assertLogs(monitoring_api.logger, level='ERROR'):
            monitor_api = monitoring_api.BsMonitoring(self.cfg_name,
                                                      self.cfg_dir,
                                                      self.server_url,
                                                      self.gpghome,
                                                      passphrase="test")
            monitor_api.rx_lock_event.set()
            monitor_api._register_thread(fingerprint, "pubkey", "address",
                                         "satellite", "rx_type", "antenna",
                                         "lnb")

        # The registration failure flag should be set
        self.assertTrue(monitor_api.registration_failure)
