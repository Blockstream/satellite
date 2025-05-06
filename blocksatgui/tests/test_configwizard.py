from unittest.mock import patch

import pytest

from blocksatcli import defs
from blocksatgui.qt import QLabel, QLineEdit, QRadioButton, Qt, QWizard
from blocksatgui.receiver import configwizard
from blocksatgui.tests.conftest import pytestqt


def select_radio_button(widget, text, obj_name=None):
    options = widget.findChildren(QRadioButton, obj_name)
    selected_opt = None

    for option in options:
        if option.text() == text:
            selected_opt = option
            break

    assert (selected_opt is not None), f"Radio Button {obj_name} not found"
    selected_opt.click()


def input_text(widget, text, obj_name):
    text_box = widget.findChild(QLineEdit, obj_name)
    assert (text_box is not None), f"Text component {obj_name} not found"
    text_box.setText(text)


def get_error_message(widget, obj_name):
    error_widget = widget.findChild(QLabel, obj_name)
    assert (error_widget is not None), f"Error component {obj_name} not found"
    return error_widget.text()


@pytest.fixture
def cfg_wizard(cfg_dir):
    wizard = configwizard.ConfigWizard(cfg_dir)
    wizard.show_dependencies_page = False  # Do not show dependencies page
    wizard.show()

    return wizard


@pytestqt
class TestReceiversSetupConfig:

    @patch('os.listdir')
    @pytest.mark.parametrize("custom_ip", [False, True])
    def test_standalone_setup(self, mock_eth_interface, cfg_wizard, qtbot,
                              user_info, custom_ip):

        mock_eth_interface.return_value = ['lo', 'eth0']
        expected_config = user_info

        qtbot.addWidget(cfg_wizard)
        wizard_widget = cfg_wizard.children()[0]
        next_bnt = cfg_wizard.button(QWizard.NextButton)
        finish_bnt = cfg_wizard.button(QWizard.FinishButton)

        # Welcome page
        qtbot.mouseClick(next_bnt, Qt.LeftButton)

        # Satellite page
        select_radio_button(wizard_widget,
                            "Galaxy 18 (G18)",
                            obj_name="default_sat")
        qtbot.mouseClick(next_bnt, Qt.LeftButton)

        # Receiver page
        select_radio_button(wizard_widget,
                            "Novra S400 (pro kit) receiver",
                            obj_name="default_setup")
        qtbot.mouseClick(next_bnt, Qt.LeftButton)

        # Network Interface
        select_radio_button(wizard_widget, "lo", obj_name="net_interface")
        qtbot.mouseClick(next_bnt, Qt.LeftButton)

        if custom_ip:
            select_radio_button(wizard_widget, "Yes", obj_name="default_rx_ip")

            # Invalid ip input
            input_text(wizard_widget, "192.168.0", obj_name="ip_address")
            qtbot.mouseClick(next_bnt, Qt.LeftButton)
            error = get_error_message(wizard_widget,
                                      obj_name="ip_address_error")
            assert error == "Please enter a valid IPv4 address"

            # Valid ip input
            input_text(wizard_widget, "192.168.0.2", obj_name="ip_address")
            qtbot.mouseClick(next_bnt, Qt.LeftButton)

            expected_config["setup"]["rx_ip"] = "192.168.0.2"
        else:
            select_radio_button(wizard_widget, "No", obj_name="default_rx_ip")
            qtbot.mouseClick(next_bnt, Qt.LeftButton)

        # Antenna page
        select_radio_button(wizard_widget,
                            "Satellite Dish (45cm / 18in)",
                            obj_name="default_antenna")
        qtbot.mouseClick(next_bnt, Qt.LeftButton)

        # LNB
        select_radio_button(wizard_widget,
                            "GEOSATpro UL1PLL (Universal Ku band LNBF)",
                            obj_name="default_lnb")
        qtbot.mouseClick(next_bnt, Qt.LeftButton)

        # LNB Power supply
        select_radio_button(wizard_widget, "No", obj_name="default_vol")
        qtbot.mouseClick(next_bnt, Qt.LeftButton)

        qtbot.mouseClick(next_bnt, Qt.LeftButton)
        qtbot.mouseClick(finish_bnt, Qt.LeftButton)

        assert (cfg_wizard.config_options == expected_config)

    @pytest.mark.parametrize("static_ip", [False, True])
    def test_sat_ip_setup(self, cfg_wizard, qtbot, user_info, static_ip):
        expected_config = user_info

        qtbot.addWidget(cfg_wizard)
        wizard_widget = cfg_wizard.children()[0]
        next_bnt = cfg_wizard.button(QWizard.NextButton)
        finish_bnt = cfg_wizard.button(QWizard.FinishButton)

        # Welcome page
        qtbot.mouseClick(next_bnt, Qt.LeftButton)

        # Satellite page
        select_radio_button(wizard_widget,
                            "Galaxy 18 (G18)",
                            obj_name="default_sat")
        qtbot.mouseClick(next_bnt, Qt.LeftButton)

        # Receiver page
        select_radio_button(wizard_widget,
                            "Blockstream Base Station receiver",
                            obj_name="default_setup")
        qtbot.mouseClick(next_bnt, Qt.LeftButton)

        if static_ip:
            select_radio_button(wizard_widget, "Yes", obj_name="default_rx_ip")
            qtbot.mouseClick(next_bnt, Qt.LeftButton)

            # Invalid ip input
            input_text(wizard_widget, "192.168.0", obj_name="ip_address")
            qtbot.mouseClick(next_bnt, Qt.LeftButton)
            error = get_error_message(wizard_widget,
                                      obj_name="ip_address_error")
            assert error == "Please enter a valid IPv4 address"

            # Valid ip input
            input_text(wizard_widget, "192.168.0.2", obj_name="ip_address")
            qtbot.mouseClick(next_bnt, Qt.LeftButton)
        else:
            select_radio_button(wizard_widget, "No", obj_name="default_rx_ip")
            qtbot.mouseClick(next_bnt, Qt.LeftButton)

        qtbot.mouseClick(next_bnt, Qt.LeftButton)
        qtbot.mouseClick(finish_bnt, Qt.LeftButton)

        expected_config["setup"] = defs.get_demod_def('Selfsat', 'IP22')
        expected_config["setup"]["antenna"] = defs.get_antenna_def('IP22')
        expected_config["lnb"] = defs.get_lnb_def('Selfsat', 'Integrated LNB')
        expected_config['lnb']['v1_pointed'] = False

        if static_ip:
            expected_config["setup"]["ip_addr"] = "192.168.0.2"

        assert (cfg_wizard.config_options == expected_config)

    def test_tbs_5927_setup(self, cfg_wizard, qtbot, user_info):

        qtbot.addWidget(cfg_wizard)
        wizard_widget = cfg_wizard.children()[0]
        next_bnt = cfg_wizard.button(QWizard.NextButton)
        finish_bnt = cfg_wizard.button(QWizard.FinishButton)

        # Welcome page
        qtbot.mouseClick(next_bnt, Qt.LeftButton)

        # Satellite page
        select_radio_button(wizard_widget,
                            "Galaxy 18 (G18)",
                            obj_name="default_sat")
        qtbot.mouseClick(next_bnt, Qt.LeftButton)

        # Receiver page
        select_radio_button(wizard_widget,
                            "TBS 5927 (basic kit) receiver",
                            obj_name="default_setup")
        qtbot.mouseClick(next_bnt, Qt.LeftButton)

        # Antenna page
        select_radio_button(wizard_widget,
                            "Satellite Dish (45cm / 18in)",
                            obj_name="default_antenna")
        qtbot.mouseClick(next_bnt, Qt.LeftButton)

        # LNB
        select_radio_button(wizard_widget,
                            "GEOSATpro UL1PLL (Universal Ku band LNBF)",
                            obj_name="default_lnb")
        qtbot.mouseClick(next_bnt, Qt.LeftButton)

        # LNB Power supply
        select_radio_button(wizard_widget, "No", obj_name="default_vol")
        qtbot.mouseClick(next_bnt, Qt.LeftButton)

        qtbot.mouseClick(next_bnt, Qt.LeftButton)
        qtbot.mouseClick(finish_bnt, Qt.LeftButton)

        expected_config = user_info
        expected_config["setup"] = defs.get_demod_def('TBS', '5927')
        expected_config["setup"]["antenna"] = defs.get_antenna_def('45cm')
        expected_config["setup"][
            'channel'] = f"{cfg_wizard.cfg_dir}/config-channel.conf"

        assert (cfg_wizard.config_options == expected_config)

    def test_sdr_setup(self, cfg_wizard, qtbot, user_info):

        expected_config = user_info

        qtbot.addWidget(cfg_wizard)
        wizard_widget = cfg_wizard.children()[0]
        next_bnt = cfg_wizard.button(QWizard.NextButton)
        finish_bnt = cfg_wizard.button(QWizard.FinishButton)

        # Welcome page
        qtbot.mouseClick(next_bnt, Qt.LeftButton)

        # Satellite page
        select_radio_button(wizard_widget,
                            "Galaxy 18 (G18)",
                            obj_name="default_sat")
        qtbot.mouseClick(next_bnt, Qt.LeftButton)

        # Receiver page
        select_radio_button(wizard_widget,
                            "RTL-SDR software-defined receiver",
                            obj_name="default_setup")
        qtbot.mouseClick(next_bnt, Qt.LeftButton)

        # Antenna page
        select_radio_button(wizard_widget,
                            "Satellite Dish (45cm / 18in)",
                            obj_name="default_antenna")
        qtbot.mouseClick(next_bnt, Qt.LeftButton)

        # LNB
        select_radio_button(wizard_widget,
                            "GEOSATpro UL1PLL (Universal Ku band LNBF)",
                            obj_name="default_lnb")
        qtbot.mouseClick(next_bnt, Qt.LeftButton)

        # LNB Power supply
        select_radio_button(wizard_widget,
                            "Directv 21 Volt Power Inserter for SWM",
                            obj_name="default_vol")
        qtbot.mouseClick(next_bnt, Qt.LeftButton)

        qtbot.mouseClick(next_bnt, Qt.LeftButton)
        qtbot.mouseClick(finish_bnt, Qt.LeftButton)

        expected_config["setup"] = defs.get_demod_def('', 'RTL-SDR')
        expected_config["setup"]["antenna"] = defs.get_antenna_def('45cm')
        expected_config["lnb"].pop("v1_pointed")
        expected_config["lnb"]["psu_voltage"] = 21

        assert (cfg_wizard.config_options == expected_config)

    @pytest.mark.parametrize("lnb_universal", [False, True])
    def test_custom_ku_band_lnb(self, cfg_wizard, qtbot, user_info,
                                lnb_universal):

        expected_config = user_info

        qtbot.addWidget(cfg_wizard)
        wizard_widget = cfg_wizard.children()[0]
        next_bnt = cfg_wizard.button(QWizard.NextButton)
        finish_bnt = cfg_wizard.button(QWizard.FinishButton)

        # Welcome page
        qtbot.mouseClick(next_bnt, Qt.LeftButton)

        # Satellite page
        select_radio_button(wizard_widget,
                            "Galaxy 18 (G18)",
                            obj_name="default_sat")
        qtbot.mouseClick(next_bnt, Qt.LeftButton)

        # Receiver page
        select_radio_button(wizard_widget,
                            "Novra S400 (pro kit) receiver",
                            obj_name="default_setup")
        qtbot.mouseClick(next_bnt, Qt.LeftButton)

        # Network Interface
        select_radio_button(wizard_widget, "lo", obj_name="net_interface")
        qtbot.mouseClick(next_bnt, Qt.LeftButton)

        # Network IP
        select_radio_button(wizard_widget, "No", obj_name="default_rx_ip")
        qtbot.mouseClick(next_bnt, Qt.LeftButton)

        # Antenna page
        select_radio_button(wizard_widget,
                            "Satellite Dish (45cm / 18in)",
                            obj_name="default_antenna")
        qtbot.mouseClick(next_bnt, Qt.LeftButton)

        # LNB
        select_radio_button(wizard_widget, "Other", obj_name="default_lnb")
        qtbot.mouseClick(next_bnt, Qt.LeftButton)

        # LNB Universal
        # Try C
        select_radio_button(wizard_widget, "C", obj_name="lnb_freq_band")
        qtbot.mouseClick(next_bnt, Qt.LeftButton)
        error = get_error_message(wizard_widget,
                                  obj_name="lnb_freq_band_error")
        assert error == "You must use a Ku band LNB to receive from Galaxy 18"

        select_radio_button(wizard_widget, "Ku", obj_name="lnb_freq_band")

        if lnb_universal:
            select_radio_button(wizard_widget, "Yes", obj_name="univ_ku_band")
            qtbot.mouseClick(next_bnt, Qt.LeftButton)

            # LNB frequency range
            select_radio_button(wizard_widget,
                                "Yes",
                                obj_name="default_univ_ku_band")
            select_radio_button(wizard_widget,
                                "Yes",
                                obj_name="univ_ku_band_lo")
            qtbot.mouseClick(next_bnt, Qt.LeftButton)

            expected_config["lnb"] = {
                "in_range": [10700.0, 12750.0],
                "lo_freq": [9750.0, 10600.0],
                "universal": True
            }
        else:
            select_radio_button(wizard_widget, "No", obj_name="univ_ku_band")
            qtbot.mouseClick(next_bnt, Qt.LeftButton)

            input_text(wizard_widget, "10700", obj_name="freq_range_lowest")
            input_text(wizard_widget, "12750", obj_name="freq_range_highest")

            # Invalid LO frequency
            input_text(wizard_widget, "10", obj_name="lnb_lo_freq")
            qtbot.mouseClick(next_bnt, Qt.LeftButton)

            error = get_error_message(wizard_widget,
                                      obj_name="lnb_lo_freq_error")
            assert error == "Please, provide the frequencies in MHz."

            # Valid LO frequency
            input_text(wizard_widget, "10400", obj_name="lnb_lo_freq")
            qtbot.mouseClick(next_bnt, Qt.LeftButton)

            expected_config["lnb"] = {
                "in_range": [10700.0, 12750.0],
                "lo_freq": 10400.0,
                "universal": False
            }
            expected_config["freqs"] = {
                "dl": 11913.4,
                "lo": 10400.0,
                "l_band": 1513.4
            }

        # LNB polarization
        select_radio_button(wizard_widget,
                            "Horizontal",
                            obj_name="default_pol")

        qtbot.mouseClick(next_bnt, Qt.LeftButton)
        qtbot.mouseClick(finish_bnt, Qt.LeftButton)

        expected_config["lnb"]["vendor"] = ""
        expected_config["lnb"]["model"] = ""
        expected_config["lnb"]["band"] = "Ku"
        expected_config["lnb"]["pol"] = "H"

        assert (cfg_wizard.config_options == expected_config)

    @pytest.mark.parametrize("lnb_universal", [False, True])
    def test_custom_c_band_lnb(self, cfg_wizard, qtbot, user_info,
                               lnb_universal):

        expected_config = user_info

        qtbot.addWidget(cfg_wizard)
        wizard_widget = cfg_wizard.children()[0]
        next_bnt = cfg_wizard.button(QWizard.NextButton)
        finish_bnt = cfg_wizard.button(QWizard.FinishButton)

        # Welcome page
        qtbot.mouseClick(next_bnt, Qt.LeftButton)

        # Satellite page
        select_radio_button(wizard_widget,
                            "Telstar 18V C Band (T18V C)",
                            obj_name="default_sat")
        qtbot.mouseClick(next_bnt, Qt.LeftButton)

        # Receiver page
        select_radio_button(wizard_widget,
                            "Novra S400 (pro kit) receiver",
                            obj_name="default_setup")
        qtbot.mouseClick(next_bnt, Qt.LeftButton)

        # Network Interface
        select_radio_button(wizard_widget, "lo", obj_name="net_interface")
        qtbot.mouseClick(next_bnt, Qt.LeftButton)

        # Network IP
        select_radio_button(wizard_widget, "No", obj_name="default_rx_ip")
        qtbot.mouseClick(next_bnt, Qt.LeftButton)

        # Antenna page
        select_radio_button(wizard_widget,
                            "Satellite Dish (45cm / 18in)",
                            obj_name="default_antenna")
        qtbot.mouseClick(next_bnt, Qt.LeftButton)

        # LNB
        select_radio_button(wizard_widget, "Other", obj_name="default_lnb")
        qtbot.mouseClick(next_bnt, Qt.LeftButton)

        # LNB freq band
        select_radio_button(wizard_widget, "C", obj_name="lnb_freq_band")
        qtbot.mouseClick(next_bnt, Qt.LeftButton)

        # LNB freq range
        # Invalid LNB freq range
        input_text(wizard_widget, "10700", obj_name="freq_range_lowest")
        input_text(wizard_widget, "12750", obj_name="freq_range_highest")

        # Valid LO frequency
        input_text(wizard_widget, "5150", obj_name="lnb_lo_freq")
        qtbot.mouseClick(next_bnt, Qt.LeftButton)

        error = get_error_message(wizard_widget, obj_name="freq_range_error")
        assert error == ("Please, choose a frequency range covering the "
                         "Telstar 18V C Band downlink frequency of 4140.0 MHz")

        # Invalid LNB freq range
        input_text(wizard_widget, "4800", obj_name="freq_range_lowest")
        input_text(wizard_widget, "3400", obj_name="freq_range_highest")
        qtbot.mouseClick(next_bnt, Qt.LeftButton)

        error = get_error_message(wizard_widget, obj_name="freq_range_error")
        assert error == ("Please, provide the lowest frequency first, "
                         "followed by the highest.")

        # Invalid LNB freq range
        input_text(wizard_widget, "3400", obj_name="freq_range_lowest")
        input_text(wizard_widget, "4200", obj_name="freq_range_highest")
        qtbot.mouseClick(next_bnt, Qt.LeftButton)

        # LNB polarization
        select_radio_button(wizard_widget, "Vertical", obj_name="default_pol")

        qtbot.mouseClick(next_bnt, Qt.LeftButton)
        qtbot.mouseClick(finish_bnt, Qt.LeftButton)

        expected_config["sat"] = defs.get_satellite_def('T18V C')
        expected_config["lnb"] = {
            "vendor": "",
            "model": "",
            "in_range": [3400.0, 4200.0],
            "lo_freq": 5150.0,
            "universal": False,
            "band": "C",
            "pol": "V"
        }
        expected_config["freqs"] = {
            "dl": 4140.0,
            "lo": 5150.0,
            "l_band": 1010.0
        }
        assert (cfg_wizard.config_options == expected_config)
