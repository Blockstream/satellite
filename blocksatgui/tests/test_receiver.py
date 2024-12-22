import os

import pytest

from blocksatcli import config, defs
from blocksatgui.components import cards
from blocksatgui.qt import QFrame, QPushButton
from blocksatgui.receiver import dashboard
from blocksatgui.receiver.settings import Settings
from blocksatgui.tests.conftest import pytestqt


@pytest.fixture
def rx_config(cfg_file):

    info = {'setup': defs.get_demod_def('Novra', 'S400')}

    rx_config = {
        'cfg': 'test',
        'cfg_dir': os.path.dirname(cfg_file),
        'info': info,
        'label': 'standalone'
    }

    return rx_config


@pytestqt
class TestReceiverPageComponents():

    def test_receiver_page_without_config_loaded(self, qtbot, cfg_manager):
        """Test default receiver page without any configuration loaded

        When there is no configuration loaded, the receiver page should be
        composed of only one button that emits a signal requesting for the
        configuration wizard.

        """
        rx_page = dashboard.ReceiverDashboard(cfg_manager)
        qtbot.addWidget(rx_page)
        rx_page.show()

        wrapper = rx_page.findChild(QFrame, 'default-config-wrapper')
        assert (wrapper is not None)

        button = wrapper.findChild(QPushButton, 'config-bnt')
        assert (button is not None)

        with qtbot.wait_signal(rx_page.sig_request_config_wizard):
            button.click()

    def test_receiver_page_with_config_loaded(self, qtbot, cfg_manager,
                                              rx_config):
        """Test receiver page with a configuration loaded

        When a configuration file is loaded, the receiver page should be
        updated to show all the components that compose the page.

        """
        rx_page = dashboard.ReceiverDashboard(cfg_manager)
        qtbot.addWidget(rx_page)

        # Default page should be displayed when no configuration is loaded
        assert (
            rx_page.current_page().objectName() == 'default-config-wrapper')

        with qtbot.wait_signal(rx_page.sig_rx_config):
            # Load the configuration file
            rx_page.callback_load_receiver_config(rx_config)

        # Return the control back to the event loop so the components in the
        # screen can be updated.
        qtbot.wait(5)

        # The receiver page should be displayed after the configuration is
        # loaded.
        assert (rx_page.current_page().objectName() == 'receiver-wrapper')

        # The receiver page components should be displayed
        receiver_page = rx_page.current_page()
        metric_cards = receiver_page.findChild(QFrame, 'metrics-box')
        assert (metric_cards is not None)

        rx_and_reporter_box = receiver_page.findChild(QFrame,
                                                      'rx-and-rep-wrapper')
        assert (rx_and_reporter_box is not None)

        run_rx_bnt = receiver_page.findChild(QPushButton, 'run-rx-bnt')
        assert (run_rx_bnt is not None)

    @pytest.mark.parametrize(
        'rx_info', [('Novra', 'S400'), ('Selfsat', 'IP22'), ('', 'RTL-SDR'),
                    ('TBS', '5520SE'), ('TBS', '5927')],
        ids=['standalone', 'sat-ip', 'sdr', 'tbs-5520', 'tbs-5927'])
    def test_metrics_cards(self, qtbot, cfg_manager, rx_config, rx_info):
        """Test metric card component for each receiver"""

        rx_page = dashboard.ReceiverDashboard(cfg_manager)
        qtbot.addWidget(rx_page)
        rx_page.show()

        rx_config['info']['setup'] = defs.get_demod_def(rx_info[0], rx_info[1])

        # Load the configuration file
        rx_page.callback_load_receiver_config(rx_config)

        # Return the control back to the event loop so the components in the
        # screen can be updated.
        qtbot.wait(5)

        wrapper = rx_page.findChild(QFrame, 'receiver-wrapper')

        # Make sure the metric cards is updated correctly
        metric_cards = wrapper.findChildren(cards.MetricCard)

        rx_info = rx_config['info']
        rx_label = config.get_rx_label(rx_info)
        expected_metrics = defs.supported_metrics_per_receiver[rx_label]
        if rx_info['setup']['type'] == defs.sdr_setup_type:
            sdr_impl = rx_config['cli_args']['run'].implementation
            expected_metrics = expected_metrics[sdr_impl]

        metrics = [
            metric.objectName().replace('card_', '') for metric in metric_cards
        ]
        assert (set(metrics) == set(expected_metrics))


@pytestqt
class TestReceiverSettingsPage():

    def test_settings_page_without_receiver_config(self, qtbot, cfg_manager):
        settings_page = Settings(cfg_manager)
        qtbot.addWidget(settings_page.view)

        assert (settings_page.view.content_page.current_page().objectName() ==
                'default-tab')

    def test_settings_page_with_receiver_config(self, qtbot, cfg_manager,
                                                cfg_file):
        settings_page = Settings(cfg_manager)
        qtbot.addWidget(settings_page.view)

        settings_page.load_rx_config(cfg_file)

        # Return the control back to the event loop so the components in the
        # screen can be updated.
        qtbot.wait(5)

        assert (settings_page.view.content_page.current_page().objectName() ==
                'settings-box')

    def test_load_configuration(self, qtbot, cfg_manager, cfg_file):
        """Verify the signal emitted after loading the receiver configuration

        There are many components connected to the signal emitted with the
        receiver configuration. Check if the emitted information is correct.

        """

        def check_emitted_config(config):
            assert (config['cfg'] == 'test')
            assert (isinstance(config['info'], dict))
            return True

        settings_page = Settings(cfg_manager)
        qtbot.addWidget(settings_page.view)

        with qtbot.wait_signal(settings_page.sig_config_loaded,
                               check_params_cb=check_emitted_config):
            settings_page.load_rx_config(cfg_file)
