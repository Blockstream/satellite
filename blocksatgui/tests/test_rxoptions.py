import blocksatcli.config
import blocksatcli.defs
import blocksatcli.main
from blocksatgui.qt import QFrame, QGroupBox, Qt, QVBoxLayout
from blocksatgui.receiver import rxconfig, rxoptions
from blocksatgui.tests.conftest import pytestqt


def setup_args(rx_label):
    parse = blocksatcli.main.get_parser()
    args = {}
    for k in ["config", "run"]:
        args[k] = parse.parse_args(rxconfig.receiver_map[rx_label]["args"][k])

    return args


def setup_rx_config(rx_type):
    return {
        'info': {
            'setup': {
                'type': rx_type
            }
        },
        'cli_args': setup_args(rx_type)
    }


@pytestqt
class TestRxOptionComponent():

    def test_rx_options(self, qtbot):
        rx_config = setup_rx_config(blocksatcli.defs.sdr_setup_type)

        rx_opt = rxoptions.ReceiverOptions()
        wrapper = QFrame()
        layout = QVBoxLayout(wrapper)
        layout.addWidget(rx_opt)
        qtbot.addWidget(wrapper)
        rx_opt_widget = wrapper.findChild(QFrame, "rxoptions")

        # Status widget is created from the beginning.
        status_widget = rx_opt_widget.findChild(QGroupBox,
                                                rx_opt.status_widget_name)
        assert (status_widget is not None)

        # At first, the "options" widget does not exist.
        options_widget = rx_opt_widget.findChild(QGroupBox,
                                                 rx_opt.options_widget_name)
        assert (options_widget is None)

        # Add options and make sure it is created correctly.
        rx_opt.add_rx_options(rx_config)
        options_widget = rx_opt_widget.findChild(QGroupBox,
                                                 rx_opt.options_widget_name)
        assert (options_widget is not None)

    def test_options_sdr(self, qtbot):
        rx_type = blocksatcli.defs.sdr_setup_type
        rx_config = setup_rx_config(rx_type)

        rx_opt = rxoptions.ReceiverOptions()
        wrapper = QFrame()
        layout = QVBoxLayout(wrapper)
        layout.addWidget(rx_opt)
        qtbot.addWidget(wrapper)

        rx_opt.add_rx_options(rx_config)
        rx_opt_widget = wrapper.findChild(QFrame, "rxoptions")
        options_widget = rx_opt_widget.findChild(QGroupBox,
                                                 rx_opt.options_widget_name)
        assert (options_widget is not None)

        advanced_options_widget = rx_opt_widget.findChild(
            QGroupBox, rx_opt.advanced_options_widget_name)
        assert (advanced_options_widget is not None)

        # Set options
        gui_widget = options_widget.findChild(
            rx_opt.options_map[rx_type]["gui"]["widget"], "gui")
        gui_widget.setCheckState(Qt.CheckState.Checked)
        assert (gui_widget.isChecked())

        gain_widget = options_widget.findChild(
            rx_opt.options_map[rx_type]["gain"]["widget"], "gain")
        gain_widget.setText("2.2")

        derotate_widget = options_widget.findChild(
            rx_opt.options_map[rx_type]["derotate"]["widget"], "derotate")
        derotate_widget.setText("3.4")

        rtl_idx_widget = options_widget.findChild(
            rx_opt.options_map[rx_type]["rtl_idx"]["widget"], "rtl_idx")
        rtl_idx_widget.setText("2")

        impl_widget = advanced_options_widget.findChild(
            rx_opt.advanced_options_map[rx_type]["implementation"]["widget"],
            "implementation")
        impl_widget.setCurrentText("gr-dvbs2rx")

        # Extract options from widgets
        rx_opt.get_rx_options(rx_config)

        cli_args = rx_config['cli_args']
        assert (cli_args["run"].gui is True)
        assert (cli_args["run"].gain == 2.2)
        assert (cli_args["run"].derotate == 3.4)
        assert (cli_args["run"].rtl_idx == 2)
        assert (cli_args["run"].implementation == "gr-dvbs2rx")

    def test_options_standalone(self, qtbot):
        rx_type = blocksatcli.defs.standalone_setup_type
        rx_config = setup_rx_config(rx_type)

        rx_opt = rxoptions.ReceiverOptions()
        wrapper = QFrame()
        layout = QVBoxLayout(wrapper)
        layout.addWidget(rx_opt)
        qtbot.addWidget(wrapper)

        rx_opt.add_rx_options(rx_config)
        rx_opt_widget = wrapper.findChild(QFrame, "rxoptions")
        options_widget = rx_opt_widget.findChild(QGroupBox,
                                                 rx_opt.options_widget_name)
        assert (options_widget is not None)

        # Set options
        address_widget = options_widget.findChild(
            rx_opt.options_map[rx_type]["address"]["widget"], "address")
        address_widget.setText("192.168.0.2")

        freq_corr_widget = options_widget.findChild(
            rx_opt.options_map[rx_type]["freq_corr"]["widget"], "freq_corr")
        freq_corr_widget.setText("100")

        demod_widget = options_widget.findChild(
            rx_opt.options_map[rx_type]["demod"]["widget"], "demod")
        demod_widget.setCurrentIndex(1)

        # Extract options from widgets
        rx_opt.get_rx_options(rx_config)

        cli_args = rx_config['cli_args']
        assert (cli_args["run"].address == "192.168.0.2")
        assert (cli_args["config"].freq_corr == 100)
        assert (cli_args["run"].demod == "2")

    def test_options_sat_ip(self, qtbot):
        rx_type = blocksatcli.defs.sat_ip_setup_type
        rx_config = setup_rx_config(rx_type)

        rx_opt = rxoptions.ReceiverOptions()
        wrapper = QFrame()
        layout = QVBoxLayout(wrapper)
        layout.addWidget(rx_opt)
        qtbot.addWidget(wrapper)

        rx_opt.add_rx_options(rx_config)
        rx_opt_widget = wrapper.findChild(QFrame, "rxoptions")

        options_widget = rx_opt_widget.findChild(QGroupBox,
                                                 rx_opt.options_widget_name)
        assert (options_widget is not None)

        advanced_options_widget = rx_opt_widget.findChild(
            QGroupBox, rx_opt.advanced_options_widget_name)
        assert (advanced_options_widget is not None)

        # Set options
        address_widget = options_widget.findChild(
            rx_opt.options_map[rx_type]["addr"]["widget"], "addr")
        address_widget.setText("192.168.0.2")

        freq_corr_widget = options_widget.findChild(
            rx_opt.options_map[rx_type]["freq_corr"]["widget"], "freq_corr")
        freq_corr_widget.setText("100")

        username_widget = options_widget.findChild(
            rx_opt.options_map[rx_type]["username"]["widget"], "username")
        username_widget.setText("username_test")

        password_widget = options_widget.findChild(
            rx_opt.options_map[rx_type]["password"]["widget"], "password")
        password_widget.setText("password_test")

        # Advanced port
        ssdp_port_widget = advanced_options_widget.findChild(
            rx_opt.advanced_options_map[rx_type]["ssdp_src_port"]["widget"],
            "ssdp_src_port")
        ssdp_port_widget.setText("3")

        ssdp_net_if_widget = advanced_options_widget.findChild(
            rx_opt.advanced_options_map[rx_type]["ssdp_net_if"]["widget"],
            "ssdp_net_if")
        ssdp_net_if_widget.setText("enp2")

        # Extract options from widgets
        rx_opt.get_rx_options(rx_config)

        cli_args = rx_config['cli_args']
        assert (cli_args["run"].addr == "192.168.0.2")
        assert (cli_args["run"].freq_corr == 100)
        assert (cli_args["run"].username == "username_test")
        assert (cli_args["run"].password == "password_test")
        assert (cli_args["run"].ssdp_src_port == 3)
        assert (cli_args["run"].ssdp_net_if == "enp2")

    def test_options_usb(self, qtbot):
        rx_type = blocksatcli.defs.linux_usb_setup_type
        rx_config = setup_rx_config(rx_type)

        rx_opt = rxoptions.ReceiverOptions()
        wrapper = QFrame()
        layout = QVBoxLayout(wrapper)
        layout.addWidget(rx_opt)
        qtbot.addWidget(wrapper)

        rx_opt.add_rx_options(rx_config)
        rx_opt_widget = wrapper.findChild(QFrame, "rxoptions")
        options_widget = rx_opt_widget.findChild(QGroupBox,
                                                 rx_opt.options_widget_name)
        assert (options_widget is not None)

        # Set options
        ip_widget = options_widget.findChild(
            rx_opt.options_map[rx_type]["ip"]["widget"], "ip")
        ip_widget.setText("192.168.0.2")

        # Extract options from widgets
        rx_opt.get_rx_options(rx_config)

        cli_args = rx_config['cli_args']
        assert (cli_args["config"].ip == "192.168.0.2")


@pytestqt
class TestRxList():
    """Test the widgets that display the list of discovered receivers

    This test suite only evaluates the processing flow after receiving the
    discovered device lists from the ReloadWorker thread. The objective is to
    assess if the GUI has correctly processed the received information

    """

    def test_list_usb_adapters(self, qtbot):

        rx_type = blocksatcli.defs.linux_usb_setup_type
        rx_config = setup_rx_config(rx_type)

        rx_opt = rxoptions.ReceiverOptions()
        wrapper = QFrame()
        layout = QVBoxLayout(wrapper)
        layout.addWidget(rx_opt)
        qtbot.addWidget(wrapper)

        rx_opt.add_rx_options(rx_config)
        rx_opt_widget = wrapper.findChild(QFrame, "rxoptions")
        options_widget = rx_opt_widget.findChild(QGroupBox,
                                                 rx_opt.options_widget_name)
        assert (options_widget is not None)

        usb_adapters = [{
            'adapter': '1',
            'frontend': '0',
            'vendor': 'TurboSight',
            'model': 'TBS 5927',
            'support': 'DVB-S/S2'
        }]
        rx_opt._process_usb_adapters(usb_adapters, error=None)

        # Extract options from widgets
        rx_opt.get_rx_options(rx_config)
        cli_args = rx_config['cli_args']

        for field in ["run", "config"]:
            assert (cli_args[field].adapter == usb_adapters[0]['adapter'])
            assert (cli_args[field].frontend == usb_adapters[0]['frontend'])

    def test_discover_sat_ip_receivers(self, qtbot):

        rx_type = blocksatcli.defs.sat_ip_setup_type
        rx_config = setup_rx_config(rx_type)

        rx_opt = rxoptions.ReceiverOptions()
        wrapper = QFrame()
        layout = QVBoxLayout(wrapper)
        layout.addWidget(rx_opt)
        qtbot.addWidget(wrapper)

        rx_opt.add_rx_options(rx_config)
        rx_opt_widget = wrapper.findChild(QFrame, "rxoptions")
        options_widget = rx_opt_widget.findChild(QGroupBox,
                                                 rx_opt.options_widget_name)
        assert (options_widget is not None)

        sat_ip_devices = [{
            'host': '192.168.0.5',
            'base_url': '',
        }]
        rx_opt._process_satip_devices(sat_ip_devices, error=None)

        # Extract options from widgets
        rx_opt.get_rx_options(rx_config)
        cli_args = rx_config['cli_args']

        assert (cli_args["run"].addr == sat_ip_devices[0]['host'])
