import os
from unittest.mock import patch, call

from requests.exceptions import ConnectionError

from . import monitoring
from .monitoring_api import metric_endpoint
from .test_helpers import create_test_setup, TestEnv


class TestReceiverReporter(TestEnv):

    def configure_reporter_setup(self,
                                 cfg_name="test_config",
                                 report_endpoint=metric_endpoint,
                                 gen_gpg_key=False,
                                 mon_api_registered=False,
                                 mon_api_gen_pwd=False,
                                 mon_api_reset_pwd=False):
        """Configure reporter setup

        This function creates a test setup with a complete receiver
        configuration file and the GPG keys. It also instantiates the
        monitoring.Reporter with the correct configuration for testing.

        """
        test_info = create_test_setup(cfg_name=cfg_name,
                                      cfg_dir=self.cfg_dir,
                                      gpghome=self.gpghome,
                                      gen_gpg_key=gen_gpg_key,
                                      mon_api_registered=mon_api_registered,
                                      mon_api_gen_password=mon_api_gen_pwd)

        reporter = monitoring.Reporter(cfg=cfg_name,
                                       cfg_dir=self.cfg_dir,
                                       dest_addr=report_endpoint,
                                       hostname='hostname-test',
                                       gnupghome=self.gpghome,
                                       passphrase='test',
                                       reset_api_pwd=mon_api_reset_pwd)

        return test_info, reporter

    @patch('blocksatcli.util.prompt_for_enter')
    @patch('blocksatcli.monitoring.requests.post')
    def test_reporter_with_bs_monitoring_api(self, mock_api_post,
                                             mock_prompt_for_enter):
        """Test reporter with Blockstream's Monitoring API

        When reporting to Blockstream's Monitoring API, the BsMonitoring
        handler will request a new password from the monitoring API if a
        password has not been generated yet. After that, the handler sends the
        receiver metrics using the password as its default authentication
        method. However, if there is any error in the password generation
        process (e.g., communication error with the API), the reporter should
        fall back to the GPG authentication method.

        """
        # Successfully respond to the password generation request
        mock_api_post.return_value.status_code = 200
        mock_api_post.return_value.json.return_value = {
            'new_password': 'generated-password'
        }
        _, reporter = self.configure_reporter_setup(mon_api_registered=True,
                                                    gen_gpg_key=True)

        reporter.send({'test': 'test'})

        # Given that the password was generated successfully, check if the
        # password is used for authentication:
        mock_api_post.assert_called_with(metric_endpoint,
                                         json={
                                             'test': 'test',
                                             'uuid': 'test-uuid',
                                             'password': 'generated-password',
                                         },
                                         cert=(None, None),
                                         timeout=5)

        # Error in the password generation process
        mock_api_post.return_value.status_code = 502
        _, reporter2 = self.configure_reporter_setup(mon_api_registered=True,
                                                     gen_gpg_key=True)

        reporter2.send({'test': 'test'})

        # The reporter should fall back to the GPG signature for authentication
        self.assertTrue('signature' in mock_api_post.call_args[1]['json'])

    @patch('blocksatcli.monitoring.requests.post')
    def test_reporter_with_generic_destination(self, mock_api_post):
        """Test reporter with a generic/custom HTTP server as the destination
        """
        mock_api_post.return_value.status_code = 200

        test_info, reporter = self.configure_reporter_setup(
            report_endpoint='http://custom.api.test')

        # The BsMonitoring handler should only be instantiated when reporting
        # to the Blockstream Monitoring API.
        self.assertIsNone(reporter.bs_monitoring)

        reporter.send({'test': 'test'})

        # When reporting to a generic destination, in addition to the metrics,
        # the request should include the satellite and hostname information.
        mock_api_post.assert_called_with('http://custom.api.test',
                                         json={
                                             'test': 'test',
                                             'satellite':
                                             test_info['sat']['alias'],
                                             'hostname': 'hostname-test',
                                         },
                                         cert=(None, None),
                                         timeout=5)

    @patch('blocksatcli.monitoring_api.BsMonitoring')
    @patch('blocksatcli.monitoring.requests.post')
    def test_reporter_with_receiver_not_registered(self, mock_api_post,
                                                   mock_bsmonitoring):
        """Test reporter with receiver not registered with the Monitoring API

        In the initial registration process with the Monitoring API, the
        reporter is responsible for indicating to the BsMonitoring handler when
        the receiver is locked. This is done through a threading event called
        rx_lock_event. The BsMonitoring handler cannot continue with the
        registration procedure before the receiver is locked.

        Also, while the receiver is not registered (i.e., while the initial
        registration process is not complete or if it has failed), the reporter
        functionality should remain disabled. In case of registration failure,
        every time reporter.send is called, the reporter prints a warning and
        does not report any metrics to the chosen destination.

        """
        _, reporter = self.configure_reporter_setup(mon_api_registered=False)
        self.assertIsNotNone(reporter.bs_monitoring)

        mock_bsmonitoring.return_value.registered = False
        mock_bsmonitoring.return_value.registration_failure = False

        reporter.send({'test': 'test', 'lock': False})

        # Receiver is not locked, so rx_lock_event was not set.
        self.assertFalse(
            call().rx_lock_event.set() in mock_bsmonitoring.mock_calls)

        reporter.send({'test': 'test', 'lock': True})

        # Receiver is locked, so rx_lock_event should be set.
        self.assertTrue(
            call().rx_lock_event.set() in mock_bsmonitoring.mock_calls)

        # Registration fails
        mock_bsmonitoring.return_value.registration_failure = True
        reporter.send({'test': 'test', 'lock': True})

        # Confirm that the metrics were not reported to the monitoring API
        # since the receiver is not properly registered and verified.
        self.assertFalse(mock_api_post.called)

    @patch('blocksatcli.monitoring.requests.post')
    def test_reporter_with_api_connection_error(self, mock_api_post):
        mock_api_post.side_effect = ConnectionError

        _, reporter = self.configure_reporter_setup(
            report_endpoint='addr-test')

        metrics = {'test': 'test'}

        # An error should be logged in case of connection error when reporting.
        with self.assertLogs(monitoring.logger, level='ERROR'):
            reporter.send(metrics)


class TestReceiverMonitor(TestEnv):

    def setUp(self):
        super().setUp()

        # Set stats with and without units
        self.stats = {
            'lock': (True, None),
            'level': (-50, "dBm"),
            'snr': (0, "dB"),
            'ber': (1e-5, None),
            'quality': (100, "%"),
            'pkt_err': (0, None)
        }

        self.stats_without_units = {
            'lock': True,
            'level': -50,
            'snr': 0,
            'ber': 1e-5,
            'quality': 100,
            'pkt_err': 0
        }

    def configure_monitor_setup(self, only_receiver_config=False):
        """Configure monitor setup

        This function creates a test setup with a complete receiver
        configuration file, the GPG keys, and a monitoring.Monitor instance.

        """
        create_test_setup(cfg_name="test_config",
                          cfg_dir=self.cfg_dir,
                          gpghome=self.gpghome,
                          mon_api_registered=True,
                          gen_gpg_key=True)

        if only_receiver_config:
            return

        monitor = monitoring.Monitor(self.cfg_dir,
                                     report=True,
                                     echo=True,
                                     min_interval=0,
                                     report_opts={
                                         'cfg': 'test_config',
                                         'cfg_dir': self.cfg_dir,
                                         'dest_addr': metric_endpoint,
                                         'gnupghome': self.gpghome,
                                         'passphrase': 'test'
                                     })

        return monitor

    def test_monitor_get_stats(self):
        monitor = self.configure_monitor_setup()
        monitor.stats = self.stats

        # Get stats with units
        res_with_units = monitor.get_stats(strip_unit=False)
        self.assertEqual(res_with_units, self.stats)

        # Get stats without units
        res_without_units = monitor.get_stats(strip_unit=True)
        self.assertEqual(res_without_units, self.stats_without_units)

    @patch('blocksatcli.monitoring.Reporter.send')
    def test_monitor_update_with_reporting_enabled(self, mock_send_report):
        monitor = self.configure_monitor_setup()

        monitor.update(self.stats)
        mock_send_report.assert_called_with(self.stats_without_units)

    @patch('time.strftime')
    def test_monitor_print_stats(self, mock_time):
        self.configure_monitor_setup(only_receiver_config=True)

        test_time = '2022-06-22 12:00:00'
        mock_time.return_value = test_time

        # Create a monitor instance UTC timezone
        monitor = monitoring.Monitor(self.cfg_dir, utc=True, min_interval=0)
        self.assertEqual(str(monitor), f"{test_time} ")

        # Create a monitor instance local timezone
        monitor = monitoring.Monitor(self.cfg_dir, utc=False, min_interval=0)
        self.assertEqual(str(monitor), f"{test_time} ")

        # Check monitor print with updated metrics
        monitor.update({'lock': (True, None)})
        self.assertEqual(str(monitor), f"{test_time}  Lock = True;")

        monitor.update({'level': (-50, "dBm")})
        self.assertEqual(str(monitor), f"{test_time}  Level = -50.00dBm;")

        monitor.update({'snr': (0, "dB")})
        self.assertEqual(str(monitor), f"{test_time}  SNR = 0.00dB;")

        monitor.update({'ber': (1e-5, None)})
        self.assertEqual(str(monitor), f"{test_time}  BER = 1.00e-05;")

        monitor.update({'quality': (100, "%")})
        self.assertEqual(str(monitor),
                         f"{test_time}  Signal Quality = 100.0%;")

        monitor.update({'pkt_err': (100, None)})
        self.assertEqual(str(monitor), f"{test_time}  Packet Errors = 100;")

        monitor.update({'snr': (0, "dB"), 'ber': (1e-5, None)})
        self.assertEqual(str(monitor),
                         f"{test_time}  SNR = 0.00dB; BER = 1.00e-05;")

    @patch('time.strftime')
    def test_monitor_logging_to_file(self, mock_time):
        self.configure_monitor_setup(only_receiver_config=True)

        test_time = '20220622-120000'
        mock_time.return_value = test_time

        # Create a monitor instance with logfile equal to true
        monitor = monitoring.Monitor(self.cfg_dir,
                                     logfile=True,
                                     min_interval=0)

        # Make sure the logs folder has been created
        log_dir = os.path.join(self.cfg_dir, 'logs')
        self.assertTrue(os.path.exists(log_dir))

        # Change time format
        test_time = '2022-06-22 12:00:00'
        mock_time.return_value = test_time

        # Check logging with updated metrics
        monitor.update({'lock': (True, None)})
        self.assertTrue(os.path.exists(monitor.logfile))
        with open(monitor.logfile, 'r') as f:
            log_file = f.readlines()

        self.assertEqual(log_file[0], f"{test_time}  Lock = True;\n")

        monitor.update({'snr': (0, "dB"), 'ber': (1e-5, None)})
        with open(monitor.logfile, 'r') as f:
            log_file = f.readlines()

        # The second monitor.update call should append a log line instead of
        # overwriting the first
        self.assertEqual(log_file[0], f"{test_time}  Lock = True;\n")
        self.assertEqual(log_file[1],
                         f"{test_time}  SNR = 0.00dB; BER = 1.00e-05;\n")

    def test_monitor_logging_interval(self):
        self.configure_monitor_setup(only_receiver_config=True)

        # Create a monitor instance with minimum interval equals to 10s
        monitor = monitoring.Monitor(self.cfg_dir,
                                     logfile=True,
                                     min_interval=10)

        # Update without waiting the minimum interval
        monitor.update({'lock': (True, None)})

        # The log file should not be created because the minimum interval
        # is not over yet
        self.assertFalse(os.path.exists(monitor.logfile))

        # Create a new instance with minimum interval equals to 0s
        monitor = monitoring.Monitor(self.cfg_dir,
                                     logfile=True,
                                     min_interval=0)
        monitor.update({'lock': (True, None)})

        # The log file should have been created with only the last update
        self.assertTrue(os.path.exists(monitor.logfile))
        with open(monitor.logfile, 'r') as f:
            log_file = f.readlines()
        self.assertTrue(len(log_file) == 1)

    @patch('builtins.print')
    @patch('blocksatcli.monitoring_api.BsMonitoring')
    def test_monitor_log_stats_to_console_with_registration_running(
            self, mock_bsmonitoring, mock_print):
        """Test monitor print to console with registration running

        If reporting to Blockstream's Monitoring API, wait util the
        registration is complete to log the status to the console.

        """
        mock_bsmonitoring.return_value.registered = False
        mock_bsmonitoring.return_value.registration_running = True

        monitor = self.configure_monitor_setup()
        monitor.update({'lock': (True, None)})

        mock_print.assert_called_with()
