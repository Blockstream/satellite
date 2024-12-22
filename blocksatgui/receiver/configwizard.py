import os
from enum import IntEnum, auto
from ipaddress import IPv4Address

from blocksatcli import config, defs, dependencies, gqrx, util

from .. import utils
from ..components.defaultwizard import DefaultWizardPage
from ..qt import (QButtonGroup, QDoubleValidator, QIntValidator, QLabel,
                  QLineEdit, QRadioButton, Qt, QWizard, Signal, Slot)
from ..receiver.dependencies import DepsInstaller


class Pages(IntEnum):
    WELCOME_PAGE = auto()
    SATELLITE_PAGE = auto()
    SETUP_DEMOD_PAGE = auto()
    SETUP_NET_INT_PAGE = auto()
    SETUP_NET_IP_PAGE = auto()
    SETUP_ANTENNA = auto()
    LNB_PAGE = auto()
    LNB_CUSTOM_PAGE = auto()
    LNB_CUSTOM_UNIV_FREQ_BAND_PAGE = auto()
    LNB_CUSTOM_FREQ_RANGE_AND_LO = auto()
    LNB_POLARIZATION = auto()
    LNB_PSU_VOLTAGE_NOT_SDR_PAGE = auto()
    LNB_PSU_VOLTAGE_SDR_PAGE = auto()
    SAVE_CFG_PAGE = auto()
    DEPENDENCIES_PAGE = auto()
    FINISH_PAGE = auto()


class ConfigWizard(QWizard):

    sig_finished = Signal(str)

    def __init__(self, cfg_dir):
        super().__init__()

        self.config_options = {}
        self.cfg_dir = cfg_dir

        self.show_dependencies_page = True

        # Wizard settings
        self.setFixedSize(840, 600)
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setOptions(QWizard.NoBackButtonOnLastPage)
        self.setWindowTitle("Configure DVB-S2 Receiver Setup")

        self.commit_bnt = self.button(QWizard.CommitButton)
        self.next_bnt = self.button(QWizard.NextButton)

        # Add pages
        self.setPage(Pages.WELCOME_PAGE, WelcomePage(self))
        self.setPage(Pages.SATELLITE_PAGE, SatellitePage(self))
        self.setPage(Pages.SETUP_DEMOD_PAGE, SetupDemodPage(self))
        self.setPage(Pages.SETUP_NET_INT_PAGE, SetupNetInterfacePage(self))
        self.setPage(Pages.SETUP_NET_IP_PAGE, SetupIpAddressPage(self))
        self.setPage(Pages.SETUP_ANTENNA, SetupAntennaPage(self))
        self.setPage(Pages.LNB_PAGE, LNBPage(self))
        self.setPage(Pages.LNB_CUSTOM_PAGE, LNBCustomPage(self))
        self.setPage(Pages.LNB_CUSTOM_UNIV_FREQ_BAND_PAGE,
                     LNBCustomUniversalKuPage(self))
        self.setPage(Pages.LNB_CUSTOM_FREQ_RANGE_AND_LO,
                     LNBCustomFreqRangeLOPage(self))
        self.setPage(Pages.LNB_POLARIZATION, LNBPolarizationPage(self))
        self.setPage(Pages.LNB_PSU_VOLTAGE_NOT_SDR_PAGE,
                     LNBPsuVoltageNotSDRPage(self))
        self.setPage(Pages.LNB_PSU_VOLTAGE_SDR_PAGE,
                     LNBPsuVoltageSDRPage(self))
        self.setPage(Pages.SAVE_CFG_PAGE, SaveCfgPage(self))
        self.setPage(Pages.DEPENDENCIES_PAGE, DependenciesPage(self))
        self.setPage(Pages.FINISH_PAGE, FinishPage(self))

        self.currentIdChanged.connect(self.callback_disable_back_button)

    def callback_disable_back_button(self, page_id):
        """Disable the back button by setting a commit page"""
        if page_id == Pages.SAVE_CFG_PAGE:
            self.currentPage().setCommitPage(True)
            self.commit_bnt.setText("Next")
        elif page_id == Pages.DEPENDENCIES_PAGE:
            self.currentPage().setCommitPage(True)
            self.commit_bnt.setText("Next")


class DefaultConfigPage(DefaultWizardPage):
    """Default functionality common to all config pages"""

    def __init__(self,
                 wizard,
                 title,
                 subtitle,
                 watermark,
                 options_key,
                 default_obj_name="default_obj"):
        super().__init__(wizard, title, subtitle, watermark)

        # Blocksat configuration options
        self.options = {}
        self.options_key = options_key

        # If object name is not specified when adding a new component to the
        # wizard page, the default name will be used.
        self.default_obj_name = default_obj_name

    def save_options(self, field, data):
        utils.set_dict(self.wizard.config_options, field, data)

    def get_selected_option_from_component(self, component):
        """Get selected configuration option from QT component

        This function gets the text (inserted by the user or from the radio
        buttons) and tries to map into the blocksat options list.

        Args:
            component (QWidget): QT component

        Returns:
            The selected option if list of options and filter is available,
            None otherwise.

        """
        assert (component is not None)

        if isinstance(component, QLineEdit):
            text = component.text()
            return text
        elif isinstance(component, QButtonGroup):
            selected_opt = component.checkedButton().text()
            obj_name = component.objectName()

            if selected_opt is None:
                return None

            options = self.options[obj_name]["options"]
            filter_label = self.options[obj_name]["filter"]

            if not options and not filter_label:
                return None

            for option in options:
                label = filter_label(option)
                if label == selected_opt:
                    return option

            return selected_opt

    def add_multiple_options_component(self,
                                       msg,
                                       vec,
                                       to_str,
                                       help_msg=None,
                                       default=0,
                                       none_option=False,
                                       none_str="Other",
                                       obj_name=None,
                                       visible=True,
                                       save_options=True,
                                       **kwargs):
        """Add component with the blocksat options list to the layout

        Args:
            msg (str): Message to be shown to the user.
            vec (list): Vector with elements to choose from.
            to_str (function): Function that convert elements information to
                               string.
            help_msg (str): Help message. Defaults to None.
            default (int): Index of the element to be checked by default.
                           Defaults to 0.
            none_option (bool): Whether to display an "Other" option. Defaults
                                to False.
            none_str (str): Message to be displayed as "Other" option. Defaults
                            to "Other".
            obj_name (str): Name of the QT widget object. Defaults to None.
            visible (bool): Whether to set the component as visible in the
                            layout. Defaults to True.
            save_options (bool): Whether to save the used options in the page
                                 object. Defaults to True.

        Returns:
            Qt component

        """
        obj_name = obj_name or self.default_obj_name

        if save_options:
            self.options[obj_name] = {}
            self.options[obj_name]["options"] = vec
            self.options[obj_name]["filter"] = to_str

        msg = QLabel(msg)
        msg.setWordWrap(True)
        msg.setObjectName(obj_name)
        self.group_layout.addWidget(msg)
        msg.setVisible(visible)

        if help_msg:
            help_msg = QLabel(help_msg)
            help_msg.setStyleSheet("font-size: 8pt;")
            help_msg.setWordWrap(True)
            help_msg.setTextFormat(Qt.RichText)
            help_msg.setTextInteractionFlags(Qt.TextBrowserInteraction)
            help_msg.setOpenExternalLinks(True)
            help_msg.setObjectName(obj_name)
            self.group_layout.addWidget(help_msg)
            help_msg.setVisible(visible)

        bnt_group = QButtonGroup(self.group)
        bnt_group.setObjectName(obj_name)

        # Add radio buttons
        for i, opt in enumerate(vec):
            opt_str = to_str(opt)
            bnt = QRadioButton(opt_str, self)
            bnt.setObjectName(obj_name)
            if i == default:
                # Set default option
                bnt.setChecked(True)
            bnt_group.addButton(bnt)
            self.group_layout.addWidget(bnt)
            bnt.setVisible(visible)

        if none_option:
            none_bnt = QRadioButton(none_str)
            none_bnt.setObjectName(obj_name)
            bnt_group.addButton(none_bnt)
            self.group_layout.addWidget(none_bnt)
            none_bnt.setVisible(visible)

        return bnt_group

    def add_text_input_component(self,
                                 question=None,
                                 placeholder=None,
                                 obj_name="default_input",
                                 input_type=None,
                                 visible=True):
        """Add component with a string and an input field

        Args:
            question (str): String question.
            placeholder (str): Short hint showed in the input component.
            obj_name (str): Name of the QT component.
            input_type (str): Validate the input type (supported types: "float"
                              and "int").
            visible (bool): Whether the component is visible.
        """

        self.options[obj_name] = []

        if question:
            question = QLabel(question)
            question.setWordWrap(True)
            question.setObjectName(obj_name)
            self.group_layout.addWidget(question)
            question.setVisible(visible)

        input = QLineEdit()
        input.setObjectName(obj_name)
        self.group_layout.addWidget(input)
        input.setVisible(visible)

        if input_type == "float":
            input.setValidator(QDoubleValidator())
        elif input_type == "int":
            input.setValidator(QIntValidator())

        if placeholder:
            input.setPlaceholderText(placeholder)

        return input

    def add_text_component(self, text, obj_name=None, visible=True):

        obj_name = obj_name or self.default_obj_name

        text = QLabel(text)
        text.setWordWrap(True)
        text.setObjectName(obj_name)
        self.group_layout.addWidget(text)
        text.setVisible(visible)

        return text


class WelcomePage(DefaultConfigPage):

    def __init__(self, wizard):
        super().__init__(wizard=wizard,
                         title="Configuration wizard",
                         subtitle=" ",
                         watermark="satellite",
                         options_key="",
                         default_obj_name="")

    def initializePage(self):
        super().initializePage()

        self.add_text_component("Welcome to the configuration wizard\n")
        self.add_text_component(
            "This wizard will generate a configuration file based on "
            "your setup.")

    def nextId(self):
        return Pages.SATELLITE_PAGE


class SatellitePage(DefaultConfigPage):

    def __init__(self, wizard):
        super().__init__(wizard=wizard,
                         title="Satellite",
                         subtitle="Satellite configuration",
                         watermark="satellite",
                         options_key="sat",
                         default_obj_name="default_sat")

    def initializePage(self):
        super().initializePage()

        config.cfg_satellite(gui_callback=self.add_multiple_options_component)
        self.satellite_grp = self.get_components_from_layout(
            self.default_obj_name, QButtonGroup, return_first=True)

    def validate_inputs(self):
        option = self.get_selected_option_from_component(self.satellite_grp)
        self.save_options(self.options_key, option)

        return True

    def set_next_page(self):
        self.next_page = Pages.SETUP_DEMOD_PAGE


class SetupDemodPage(DefaultConfigPage):

    def __init__(self, wizard):
        super().__init__(wizard=wizard,
                         title="Receiver",
                         subtitle="Receiver configuration",
                         watermark="satellite",
                         options_key="setup",
                         default_obj_name="default_setup")

    def initializePage(self):
        super().initializePage()

        config.ask_demod(self.wizard.config_options["sat"],
                         gui_callback=self.add_multiple_options_component)
        self.demod_grp = self.get_components_from_layout(self.default_obj_name,
                                                         QButtonGroup,
                                                         return_first=True)

    def validate_inputs(self):
        # Get option and save it.
        option = self.get_selected_option_from_component(self.demod_grp)
        self.save_options(self.options_key, option)

        # If sat-ip, also add the built-in antenna and lnb.
        setup = self.wizard.config_options["setup"]
        if setup["type"] == defs.sat_ip_setup_type:
            for antenna in defs.antennas:
                if antenna["type"] == "sat-ip":
                    utils.set_dict(self.wizard.config_options, "setup.antenna",
                                   antenna)
            for lnb in defs.lnbs:
                if lnb["vendor"] == "Selfsat":
                    select_lnb = defs.get_lnb_def(lnb["vendor"], lnb["model"])
                    select_lnb["v1_pointed"] = False
                    utils.set_dict(self.wizard.config_options, "lnb",
                                   select_lnb)

        return True

    def set_next_page(self):
        setup = self.wizard.config_options["setup"]
        if setup["type"] == defs.standalone_setup_type:
            self.next_page = Pages.SETUP_NET_INT_PAGE
        elif setup["type"] == defs.sat_ip_setup_type:
            self.next_page = Pages.SETUP_NET_IP_PAGE
        else:
            self.next_page = Pages.SETUP_ANTENNA


class SetupNetInterfacePage(DefaultConfigPage):

    def __init__(self, wizard):
        super().__init__(wizard=wizard,
                         title="Receiver",
                         subtitle="Network Interface",
                         watermark="satellite",
                         options_key="setup.netdev",
                         default_obj_name="net_interface")

    def initializePage(self):
        super().initializePage()

        self.devices = util.get_network_interfaces()
        question = "Which network interface is connected to the receiver?"
        if self.devices is None:
            self.net_interface_input = self.add_text_input_component(
                question=question)
            self.net_interface_input_error = self.add_error_component(
                self.default_obj_name)
        else:
            self.net_interface_grp = self.add_multiple_options_component(
                vec=self.devices,
                msg=question,
                to_str=lambda x: '{}'.format(x))

    def validate_inputs(self):
        is_valid = False

        if self.devices:
            net_int = self.get_selected_option_from_component(
                self.net_interface_grp)
            is_valid = True
        else:
            net_int = self.net_interface_input.text().strip()
            is_valid = net_int != ""
            self._display_error_message(
                is_valid, self.net_interface_input,
                self.net_interface_input_error,
                "Please enter a valid network interface name")

        if is_valid:
            self.save_options(self.options_key, net_int.strip())

        return is_valid

    def set_next_page(self):
        self.next_page = Pages.SETUP_NET_IP_PAGE


class SetupIpAddressPage(DefaultConfigPage):

    def __init__(self, wizard):
        super().__init__(wizard=wizard,
                         title="Receiver",
                         subtitle="IP Address",
                         watermark="satellite",
                         options_key="setup.rx_ip",
                         default_obj_name="default_rx_ip")

    def initializePage(self):
        super().initializePage()

        setup = self.wizard.config_options['setup']

        if setup['type'] == defs.sat_ip_setup_type:
            msg = ("Does the {} have a static IP address?".format(
                config._get_rx_marketing_name(setup)))
            self.options_key = "setup.ip_addr"
        else:
            msg = ("Have you manually assigned a custom "
                   "IP address to the receiver?")
            self.options_key = "setup.rx_ip"

        self.manual_ip_bnt_grp = self.add_multiple_options_component(
            vec=["Yes", "No"],
            msg=msg,
            to_str=lambda x: "{}".format(x),
            default=1)

        self.manual_ip_input = self.add_text_input_component(
            question="Which IPv4 address?",
            obj_name="ip_address",
            visible=False)
        self.manual_ip_input_error = self.add_error_component(
            "ip_address_error")

        self.set_callbacks()

    def validate_inputs(self):

        is_valid = False

        manual_ip = self.get_selected_option_from_component(
            self.manual_ip_bnt_grp)
        if manual_ip == "No":
            ip_address = defs.default_standalone_ip_addr
            is_valid = True
        else:
            ip_address_text = self.get_selected_option_from_component(
                self.manual_ip_input)
            ip_address = self._validate_type(
                ip_address_text, IPv4Address, self.manual_ip_input,
                self.manual_ip_input_error,
                "Please enter a valid IPv4 address")
            is_valid = bool(ip_address)

        if is_valid:
            self.save_options(self.options_key, str(ip_address))

        return is_valid

    def set_next_page(self):
        setup = self.wizard.config_options['setup']
        if setup['type'] == defs.sat_ip_setup_type:
            self.next_page = Pages.SAVE_CFG_PAGE
        else:
            self.next_page = Pages.SETUP_ANTENNA

    def set_callbacks(self):
        self.manual_ip_bnt_grp.buttonClicked.connect(self.callback_radio_bnt)

    def callback_radio_bnt(self):
        self._toggle_visibility(
            visible=self.manual_ip_bnt_grp.checkedButton().text() == "Yes",
            components=self.get_components_from_layout("ip_address"))


class SetupAntennaPage(DefaultConfigPage):

    def __init__(self, wizard):
        super().__init__(wizard=wizard,
                         title="Receiver",
                         subtitle="Antenna",
                         watermark="satellite",
                         options_key="setup.antenna",
                         default_obj_name="default_antenna")

    def initializePage(self):
        super().initializePage()

        config.ask_antenna(self.wizard.config_options["sat"],
                           gui_callback=self.add_multiple_options_component)
        self.antenna_grp = self.get_components_from_layout(
            self.default_obj_name, QButtonGroup, return_first=True)

        self.antenna_input = self.add_text_input_component(
            question="Enter size in cm: ",
            obj_name="custom_antenna",
            visible=False)
        self.antenna_input_error = self.add_error_component("custom_antenna")

        self.set_callbacks()

    def validate_inputs(self):
        is_valid = True
        antenna = self.get_selected_option_from_component(self.antenna_grp)

        if antenna == "Other":
            antenna_text = self.antenna_input.text()
            antenna_size = self._validate_type(
                antenna_text, int, self.antenna_input,
                self.antenna_input_error, "Please enter an integer number")
            antenna = {'label': "custom", 'type': 'dish', 'size': antenna_size}
            is_valid = bool(antenna_size)

        if is_valid:
            self.save_options(self.options_key, antenna)

            # For flat-panel and Sat-IP antennas, the LNB is the integrated one
            if antenna["type"] in ["flat", "sat-ip"]:
                for lnb in defs.lnbs:
                    if lnb["vendor"] == "Selfsat":
                        int_lnb = defs.get_lnb_def(lnb["vendor"], lnb["model"])
                        int_lnb["v1_pointed"] = False
                        self.save_options("lnb", int_lnb)

        return is_valid

    def set_next_page(self):
        antenna = self.wizard.config_options["setup"]["antenna"]
        if antenna["type"] in ["flat", "sat-ip"]:
            self.next_page = Pages.SAVE_CFG_PAGE
        else:
            self.next_page = Pages.LNB_PAGE

    def set_callbacks(self):

        self.antenna_grp.buttonClicked.connect(self.callback_radio_bnt)

    def callback_radio_bnt(self):
        self._toggle_visibility(
            visible=self.antenna_grp.checkedButton().text() == "Other",
            components=self.get_components_from_layout("custom_antenna"))


class LNBPage(DefaultConfigPage):

    def __init__(self, wizard):
        super().__init__(wizard=wizard,
                         title="LNB",
                         subtitle="LNB configuration",
                         watermark="satellite",
                         options_key="lnb",
                         default_obj_name="default_lnb")

    def initializePage(self):
        super().initializePage()

        config.ask_lnb(sat=self.wizard.config_options["sat"],
                       gui_callback=self.add_multiple_options_component)
        self.lnb_grp = self.get_components_from_layout(self.default_obj_name,
                                                       QButtonGroup,
                                                       return_first=True)
        self.lnb_grp_error = self.add_error_component(self.default_obj_name)

    def validate_inputs(self):
        lnb = self.get_selected_option_from_component(self.lnb_grp)

        if lnb == "Other":
            self.lnb_grp_error.setText("")
            return True

        sat = self.wizard.config_options["sat"]
        error_msg = ""

        valid_lnb_sat_freq = True if config._sat_freq_in_lnb_range(
            sat, lnb) else False
        if not valid_lnb_sat_freq:
            error_msg += ("Your LNB's input frequency range does not cover "
                          "the frequency of {} ({} MHz)\n".format(
                              sat["name"], sat["dl_freq"]))

        valid_lnb_sat_band = False if (sat['band'].lower()
                                       != lnb['band'].lower()) else True
        if not valid_lnb_sat_band:
            error_msg += ("The LNB you chose cannot operate "
                          "in {} band (band of satellite {})".format(
                              sat['band'], sat['alias']))

        is_valid = valid_lnb_sat_freq and valid_lnb_sat_band
        self._display_error_message(is_valid, self.lnb_grp, self.lnb_grp_error,
                                    error_msg)

        if is_valid:
            self.save_options(self.options_key, lnb)

        return is_valid

    def set_next_page(self):
        if self.lnb_grp.checkedButton().text() == "Other":
            self.next_page = Pages.LNB_CUSTOM_PAGE
        elif (self.wizard.config_options["lnb"]["pol"].lower() == "dual"
              and self.wizard.config_options["setup"]["type"]
              != defs.sdr_setup_type):
            self.next_page = Pages.LNB_PSU_VOLTAGE_NOT_SDR_PAGE
        elif (self.wizard.config_options["setup"]["type"] ==
              defs.sdr_setup_type):
            self.next_page = Pages.LNB_PSU_VOLTAGE_SDR_PAGE
        else:
            self.next_page = Pages.SAVE_CFG_PAGE


class LNBCustomPage(DefaultConfigPage):

    def __init__(self, wizard):
        super().__init__(wizard=wizard,
                         title="LNB",
                         subtitle="Inform the specifications of your LNB",
                         watermark="satellite",
                         options_key="lnb",
                         default_obj_name="lnb_freq_band")

    def initializePage(self):
        super().initializePage()

        text = QLabel("Please, inform the specifications of your LNB:")
        text.setWordWrap(True)
        self.group_layout.addWidget(text)

        self.lnb_freq_band_grp = self.add_multiple_options_component(
            msg="Frequency band:",
            vec=["C", "Ku"],
            to_str=lambda x: "{}".format(x))

        self.lnb_univ_ku_band_grp = self.add_multiple_options_component(
            msg="It is a Universal Ku band LNB",
            vec=["Yes", "No"],
            to_str=lambda x: "{}".format(x),
            obj_name="univ_ku_band",
            visible=False)

        self.lnb_freq_band_grp_error = self.add_error_component(
            "lnb_freq_band_error")
        self.lnb_univ_ku_band_grp_error = self.add_error_component(
            "univ_ku_band")

        self.set_callbacks()

    def validate_inputs(self):

        lnb_freq_band = self.get_selected_option_from_component(
            self.lnb_freq_band_grp)
        sat = self.wizard.config_options["sat"]
        is_lnb_freq_valid = sat["band"].lower() == lnb_freq_band.lower()
        self._display_error_message(
            condition=is_lnb_freq_valid,
            input_comp=self.lnb_freq_band_grp,
            error_comp=self.lnb_freq_band_grp_error,
            error_msg=("You must use a {} band LNB to receive "
                       "from {}".format(sat["band"], sat["name"])))

        if not is_lnb_freq_valid:
            return False

        if lnb_freq_band == "C":
            is_lnb_universal = False
        else:
            univ_ku_band = self.get_selected_option_from_component(
                self.lnb_univ_ku_band_grp)
            is_lnb_universal = univ_ku_band == "Yes"

        lnb = {
            "vendor": "",
            "model": "",
            "universal": is_lnb_universal,
            "band": lnb_freq_band
        }
        self.save_options(self.options_key, lnb)

        return True

    def set_next_page(self):
        if (self.lnb_freq_band_grp.checkedButton().text() == "Ku"
                and self.lnb_univ_ku_band_grp.checkedButton().text() == "Yes"):
            self.next_page = Pages.LNB_CUSTOM_UNIV_FREQ_BAND_PAGE
        else:
            self.next_page = Pages.LNB_CUSTOM_FREQ_RANGE_AND_LO

    def set_callbacks(self):
        self.lnb_freq_band_grp.buttonClicked.connect(self.callback_radio_bnt)

    def callback_radio_bnt(self):
        self._toggle_visibility(
            visible=self.lnb_freq_band_grp.checkedButton().text() == "Ku",
            components=self.get_components_from_layout("univ_ku_band"))


class LNBCustomUniversalKuPage(DefaultConfigPage):

    def __init__(self, wizard):
        super().__init__(wizard=wizard,
                         title="LNB",
                         subtitle="Inform the specifications of your LNB",
                         watermark="satellite",
                         options_key="lnb",
                         default_obj_name="default_univ_ku_band")

    def initializePage(self):
        super().initializePage()

        self.lnb_cover_inp_freq_grp = self.add_multiple_options_component(
            msg=("Does your LNB cover an input frequency from 10.7 "
                 "to 12.75 GHz?"),
            help_msg=("A Universal Ku band LNB typically covers this input "
                      "frequency range."),
            vec=["Yes", "No"],
            to_str=lambda x: "{}".format(x),
            visible=True)

        self.add_text_component(
            text=("Inform the two extreme frequencies "
                  "(in MHz) of your LNB's frequency range:"),
            obj_name="freq_range",
            visible=False)

        self.lnb_freq_low = self.add_text_input_component(
            placeholder="Lower frequency (MHz)",
            input_type="float",
            obj_name="freq_range_lowest",
            visible=False)

        self.lnb_freq_high = self.add_text_input_component(
            placeholder="Higher frequency (MHz)",
            input_type="float",
            obj_name="freq_range_highest",
            visible=False)

        self.lnb_cover_lo_grp = self.add_multiple_options_component(
            msg=("A Universal Ku band LNB has two LO (local "
                 "oscillator) frequencies. Does your LNB have LO "
                 "frequencies of 9750 MHz and 10600 MHz?"),
            help_msg=("Typically the two frequencies are 9750 MHz and "
                      "10600 MHz."),
            vec=["Yes", "No"],
            to_str=lambda x: "{}".format(x),
            obj_name="univ_ku_band_lo",
            visible=True)

        self.add_text_component(text="Inform the two LO frequencies in MHz:",
                                obj_name="lo",
                                visible=False)

        self.lnb_lo_low = self.add_text_input_component(
            placeholder="Lower frequency (MHz)",
            input_type="float",
            obj_name="lo_lowest",
            visible=False)

        self.lnb_lo_high = self.add_text_input_component(
            placeholder="Higher frequency (MHz)",
            input_type="float",
            obj_name="lo_highest",
            visible=False)

        self.lnb_freq_error = self.add_error_component("freq_range_lowest")
        self.lnb_lo_error = self.add_error_component("lo_lowest")

        self.set_callbacks()

    def _validate_lnb_freq_range(self):
        univ_freq_range = self.get_selected_option_from_component(
            self.lnb_cover_inp_freq_grp)
        lnb_in_range = []

        if univ_freq_range == "Yes":
            lnb_in_range = [10700.0, 12750.0]
            lnb_freq_range_valid = True

            return lnb_in_range

        try:
            lnb_in_range = [
                float(self.lnb_freq_low.text()),
                float(self.lnb_freq_high.text())
            ]
        except ValueError:
            lnb_freq_range_valid = False
            error_msg = "Please, provide a valid input."
        else:
            lnb_freq_range_valid, error_msg = config._validate_lnb_freq_range(
                lnb_in_range, self.wizard.config_options["sat"])

        self._display_error_message(
            condition=lnb_freq_range_valid,
            input_comp=[self.lnb_freq_low, self.lnb_freq_high],
            error_comp=self.lnb_freq_error,
            error_msg=error_msg)

        return lnb_in_range if lnb_freq_range_valid else None

    def _validate_lnb_lo(self):
        univ_lo_freq = self.get_selected_option_from_component(
            self.lnb_cover_lo_grp)
        lnb_lo_freq = []

        if univ_lo_freq == "Yes":
            lnb_lo_freq = [9750.0, 10600.0]
            lnb_lo_valid = True

            return lnb_lo_freq

        try:
            lnb_lo_freq = [
                float(self.lnb_lo_low.text()),
                float(self.lnb_lo_high.text())
            ]
        except ValueError:
            lnb_lo_valid = False
            error_msg = "Please, provide a valid input."
        else:
            lnb_lo_valid, error_msg = config._validate_lnb_lo_freq(lnb_lo_freq)

        self._display_error_message(
            condition=lnb_lo_valid,
            input_comp=[self.lnb_lo_low, self.lnb_lo_high],
            error_comp=self.lnb_lo_error,
            error_msg=error_msg)

        return lnb_lo_freq if lnb_lo_valid else None

    def validate_inputs(self):
        is_valid = False

        lnb_in_range = self._validate_lnb_freq_range()
        lnb_lo = self._validate_lnb_lo()

        if lnb_in_range and lnb_lo:
            is_valid = True
            self.save_options("lnb.in_range", lnb_in_range)
            self.save_options("lnb.lo_freq", lnb_lo)

        return is_valid

    def set_callbacks(self):

        self.lnb_cover_inp_freq_grp.buttonClicked.connect(
            self.callback_lnb_freq_range)

        self.lnb_cover_lo_grp.buttonClicked.connect(self.callback_lnb_lo)

    def callback_lnb_freq_range(self):
        lnb_cover_inp_freq_text = self.get_selected_option_from_component(
            self.lnb_cover_inp_freq_grp)

        text = self.get_components_from_layout(object_name="freq_range")
        high_freq = self.get_components_from_layout(
            object_name="freq_range_highest")
        low_freq = self.get_components_from_layout(
            object_name="freq_range_lowest")

        self._toggle_visibility(visible=lnb_cover_inp_freq_text == "No",
                                components=text + high_freq + low_freq)

    def callback_lnb_lo(self):
        lnb_cover_lo_text = self.get_selected_option_from_component(
            self.lnb_cover_lo_grp)

        text = self.get_components_from_layout(object_name="lo")
        high_freq = self.get_components_from_layout(object_name="lo_highest")
        low_freq = self.get_components_from_layout(object_name="lo_lowest")

        self._toggle_visibility(visible=lnb_cover_lo_text == "No",
                                components=text + high_freq + low_freq)

    def set_next_page(self):
        self.next_page = Pages.LNB_POLARIZATION


class LNBCustomFreqRangeLOPage(DefaultConfigPage):

    def __init__(self, wizard):
        super().__init__(wizard=wizard,
                         title="LNB",
                         subtitle="Inform the specifications of your LNB",
                         watermark="satellite",
                         options_key="lnb",
                         default_obj_name="default_custom_lo")

    def initializePage(self):
        super().initializePage()

        self.add_text_component(
            text=("Inform the two extreme frequencies "
                  "(in MHz) of your LNB's frequency range:"),
            obj_name="freq_range",
            visible=True)

        self.lnb_freq_low = self.add_text_input_component(
            placeholder="Lower frequency (MHz)",
            obj_name="freq_range_lowest",
            visible=True)

        self.lnb_freq_high = self.add_text_input_component(
            placeholder="Higher frequency (MHz)",
            obj_name="freq_range_highest",
            visible=True)

        self.lnb_lo_freq = self.add_text_input_component(
            question="Inform the LO frequency in MHz:",
            placeholder="LO frequency (MHz)",
            obj_name="lnb_lo_freq",
            visible=True)

        self.lnb_freq_error = self.add_error_component("freq_range_error")
        self.lnb_lo_freq_error = self.add_error_component("lnb_lo_freq_error")

    def _validate_lnb_freq_range(self):
        lnb_in_range = None

        try:
            lnb_in_range = [
                float(self.lnb_freq_low.text()),
                float(self.lnb_freq_high.text())
            ]
        except ValueError:
            lnb_freq_range_valid = False
            error_msg = "Please, provide a valid input."
        else:
            lnb_freq_range_valid, error_msg = config._validate_lnb_freq_range(
                lnb_in_range, self.wizard.config_options["sat"])

        self._display_error_message(
            condition=lnb_freq_range_valid,
            input_comp=[self.lnb_freq_low, self.lnb_freq_high],
            error_comp=self.lnb_freq_error,
            error_msg=error_msg)

        return lnb_in_range if lnb_freq_range_valid else None

    def _validate_lnb_lo(self):
        lnb_lo = None

        try:
            lnb_lo = float(self.lnb_lo_freq.text())
        except ValueError:
            lnb_lo_valid = False
            error_msg = "Please, provide a valid input."
        else:
            lnb_lo_valid, error_msg = config._validate_lnb_lo_freq(
                lnb_lo, single_lo=True)

        self._display_error_message(condition=lnb_lo_valid,
                                    input_comp=self.lnb_lo_freq,
                                    error_comp=self.lnb_lo_freq_error,
                                    error_msg=error_msg)

        return lnb_lo if lnb_lo_valid else None

    def validate_inputs(self):
        is_valid = False

        lnb_freq_range = self._validate_lnb_freq_range()
        lnb_lo = self._validate_lnb_lo()

        if lnb_freq_range and lnb_lo:
            self.save_options("lnb.in_range", lnb_freq_range)
            self.save_options("lnb.lo_freq", lnb_lo)
            is_valid = True

        return is_valid

    def set_next_page(self):
        self.next_page = Pages.LNB_POLARIZATION


class LNBPolarizationPage(DefaultConfigPage):

    def __init__(self, wizard):
        super().__init__(wizard=wizard,
                         title="LNB",
                         subtitle="Polarization",
                         watermark="satellite",
                         options_key="lnb.pol",
                         default_obj_name="default_pol")

    def initializePage(self):
        super().initializePage()

        config.ask_lnb_polarization(
            gui_callback=self.add_multiple_options_component)
        self.lnb_pol = self.get_components_from_layout(self.default_obj_name,
                                                       QButtonGroup,
                                                       return_first=True)

    def validate_inputs(self):

        pol = self.get_selected_option_from_component(self.lnb_pol)
        self.save_options(self.options_key, pol["id"])

        return True

    def set_next_page(self):
        if (self.wizard.config_options["lnb"]["pol"].lower() == "dual"
                and self.wizard.config_options["setup"]["type"]
                != defs.sdr_setup_type):
            self.next_page = Pages.LNB_PSU_VOLTAGE_NOT_SDR_PAGE
        elif (self.wizard.config_options["setup"]["type"] ==
              defs.sdr_setup_type):
            self.next_page = Pages.LNB_PSU_VOLTAGE_SDR_PAGE
        else:
            self.next_page = Pages.SAVE_CFG_PAGE


class LNBPsuVoltageNotSDRPage(DefaultConfigPage):

    def __init__(self, wizard):
        super().__init__(wizard=wizard,
                         title="LNB",
                         subtitle="Power Supply",
                         watermark="satellite",
                         options_key="lnb.psu_voltage",
                         default_obj_name="default_vol")

    def initializePage(self):
        super().initializePage()

        self.sdr_used_before_grp = self.add_multiple_options_component(
            msg=("Are you reusing an LNB that is already pointed "
                 "and that was used before by an SDR receiver? "),
            vec=["Yes", "No"],
            to_str=lambda x: "{}".format(x),
            default=1,
            help_msg=("This information is helpful to determine the "
                      "polarization required for the LNB"),
            visible=True)

        self.psu_ins_grp = self.add_multiple_options_component(
            msg=("In the pre-existing SDR setup, did you use one of "
                 "the LNB power inserters below? "),
            vec=defs.psus,
            to_str=lambda x: "{}".format(x['model']),
            none_option=True,
            none_str="No - another model",
            obj_name="psu_ins",
            visible=False)

        self.psu_voltage_input = self.add_text_input_component(
            question=("What is the voltage supplied to the LNB by "
                      "your power inserter?"),
            placeholder="Voltage",
            obj_name="psu_voltage",
            visible=False)

        self.psu_voltage_input_error = self.add_error_component("psu_voltage")

        self.set_callbacks()

    def validate_inputs(self):

        is_valid = False

        sdr_used_before_text = self.get_selected_option_from_component(
            self.sdr_used_before_grp)
        sdr_used_before = sdr_used_before_text == "Yes"
        self.save_options("lnb.v1_pointed", sdr_used_before)

        if not sdr_used_before:
            return True

        selected_psu_ins = self.get_selected_option_from_component(
            self.psu_ins_grp)
        if selected_psu_ins != "No - another model":
            psu_voltage = selected_psu_ins["voltage"]
            is_valid = True
        else:
            psu_voltage_text = self.psu_voltage_input.text()
            psu_voltage = self._validate_type(
                psu_voltage_text, int, self.psu_voltage_input,
                self.psu_voltage_input_error,
                "Please, provide a valid voltage")

        if psu_voltage:
            is_valid = True
            self.save_options("lnb.v1_psu_voltage", psu_voltage)

        return is_valid

    def set_next_page(self):
        self.next_page = Pages.SAVE_CFG_PAGE

    def set_callbacks(self):

        self.sdr_used_before_grp.buttonClicked.connect(self.callback_sdr_used)
        self.sdr_used_before_grp.buttonClicked.connect(
            self.callback_psu_voltage_input)
        self.psu_ins_grp.buttonClicked.connect(self.callback_psu_voltage_input)

    def callback_sdr_used(self):

        self._toggle_visibility(
            visible=(self.sdr_used_before_grp.checkedButton().text() == "Yes"),
            components=self.get_components_from_layout("psu_ins"))

    def callback_psu_voltage_input(self):
        condition = (
            self.psu_ins_grp.checkedButton().text() == "No - another model"
            and self.sdr_used_before_grp.checkedButton().text() == "Yes")

        self._toggle_visibility(
            visible=condition,
            components=self.get_components_from_layout("psu_voltage"))


class LNBPsuVoltageSDRPage(DefaultConfigPage):

    def __init__(self, wizard):
        super().__init__(wizard=wizard,
                         title="LNB",
                         subtitle="Power Supply",
                         watermark="satellite",
                         options_key="lnb.psu_voltage",
                         default_obj_name="default_vol")

    def initializePage(self):
        super().initializePage()

        self.psu_ins_grp = self.add_multiple_options_component(
            msg="Are you using one of the LNB power inserters below?",
            vec=defs.psus,
            to_str=lambda x: "{}".format(x['model']),
            none_option=True,
            none_str="No - another model",
            visible=True)

        self.psu_voltage_input = self.add_text_input_component(
            question=("What is the voltage supplied to the LNB by "
                      "your power inserter?"),
            placeholder="Voltage",
            obj_name="psu_voltage",
            visible=False)

        self.psu_voltage_input_error = self.add_error_component("psu_voltage")

        self.set_callbacks()

    def validate_inputs(self):
        is_valid = False

        selected_psu_ins = self.get_selected_option_from_component(
            self.psu_ins_grp)
        if selected_psu_ins != "No - another model":
            psu_voltage = selected_psu_ins["voltage"]
            is_valid = True
        else:
            psu_voltage_text = self.psu_voltage_input.text()
            psu_voltage = self._validate_type(
                psu_voltage_text, int, self.psu_voltage_input,
                self.psu_voltage_input_error,
                "Please, provide a valid voltage")
            is_valid = bool(psu_voltage)

        if is_valid:
            self.save_options(self.options_key, psu_voltage)

        return is_valid

    def set_next_page(self):
        self.next_page = Pages.SAVE_CFG_PAGE

    def set_callbacks(self):
        self.psu_ins_grp.buttonClicked.connect(self.callback_psu_voltage_input)

    def callback_psu_voltage_input(self):

        self._toggle_visibility(
            visible=(self.psu_ins_grp.checkedButton().text() ==
                     "No - another model"),
            components=self.get_components_from_layout("psu_voltage"))


class SaveCfgPage(DefaultConfigPage):

    def __init__(self, wizard):
        super().__init__(wizard=wizard,
                         title="Complete configuration",
                         subtitle=" ",
                         watermark="satellite",
                         options_key="",
                         default_obj_name="")

    def initializePage(self):
        super().initializePage()

        self.default_cfg_dir = self.wizard.cfg_dir
        options = self.wizard.config_options

        user_freq = config._cfg_frequencies(sat=options["sat"],
                                            lnb=options["lnb"],
                                            setup=options["setup"])
        self.save_options("freqs", user_freq)

        if not os.path.exists(self.default_cfg_dir):
            os.makedirs(self.default_cfg_dir)

        self.default_cfg_file = os.path.join(self.default_cfg_dir,
                                             "config.json")
        self.add_text_component("Receiver Configuration")
        self.add_text_component(
            "This step will generate a configuration file with the selected "
            "options. \n")

        if os.path.exists(self.default_cfg_file):
            self.rx_cfg_file = self.add_multiple_options_component(
                vec=["Yes", "No"],
                msg="Found previous {}. Remove and regenerate file?".format(
                    self.default_cfg_file),
                to_str=lambda x: "{}".format(x),
                default=1)
            self.new_rx_cfg_file = self.add_text_input_component(
                question="Enter the name for the new configuration file: ",
                obj_name="rx_cfg_name",
                visible=True)
            self.error_comp = self.add_error_component("rx_cfg_name")

        # Channel configuration file
        if (options["setup"]["type"] == defs.linux_usb_setup_type):
            self.add_text_component("\nChannel Configuration\n")
            self.add_text_component(
                "This step will generate the channel configuration file that "
                "is required when launching the USB receiver in Linux.\n")
            self.gen_chan_file = self.add_multiple_options_component(
                vec=["Yes", "No"],
                default=1,
                msg="Found previous {}. Remove and regenerate file?".format(
                    "channel file"),
                to_str=lambda x: "{}".format(x),
                visible=False,
                obj_name="chan_file_opt")

        # Gqrx configuration file
        if (options["setup"]["type"]) == defs.sdr_setup_type:
            self.add_text_component("\nGqrx Configuration")
            self.add_text_component(
                "This step will generate the configuration file that "
                "is needed for Gqrx.\n")
            home_dir = os.path.expanduser("~")
            cfg_path = os.path.join(home_dir, ".config", "gqrx")
            self.gqrx_file = os.path.join(cfg_path, "default.conf")
            if os.path.exists(self.gqrx_file):
                self.gen_gqrx_file = self.add_multiple_options_component(
                    vec=["Yes", "No"],
                    msg="Found previous {}. Remove and regenerate file?".
                    format(self.gqrx_file),
                    to_str=lambda x: "{}".format(x))

        self.set_callbacks()

    def validate_inputs(self):
        is_valid = False
        options = self.wizard.config_options

        if (not os.path.exists(self.default_cfg_file)
                or self.rx_cfg_file.checkedButton().text() == "Yes"):
            cfg_name = "config"
            is_valid = True
        else:
            cfg_name = self.new_rx_cfg_file.text()
            is_valid = cfg_name != ""
            self._display_error_message(condition=is_valid,
                                        input_comp=self.new_rx_cfg_file,
                                        error_comp=self.error_comp,
                                        error_msg="Invalid file name")

        if not is_valid:
            return False

        # Save channel file
        if (options["setup"]["type"] == defs.linux_usb_setup_type):
            chan_file = os.path.join(self.default_cfg_dir,
                                     cfg_name + "-channel.conf")
            if os.path.exists(chan_file):
                chan_file_comp = self.get_components_from_layout(
                    "chan_file_opt")
                if not chan_file_comp[0].isVisible():
                    # Ensure the group of components related to the channel
                    # file is visible on the screen. If it is invisible, make
                    # it visible and return an invalid state. This will cause
                    # the wizard to update the component's visibility but not
                    # go to the next page.
                    self._toggle_visibility(visible=True,
                                            components=chan_file_comp)
                    return False
            if (not os.path.exists(chan_file)
                    or self.gen_chan_file.checkedButton().text() == "Yes"):
                self._save_channel_cfg_file(self.default_cfg_dir, cfg_name,
                                            options)

        # Gqrx configuration file
        if (options["setup"]["type"] == defs.sdr_setup_type):
            if (not os.path.exists(self.gqrx_file)
                    or self.gen_gqrx_file.checkedButton().text() == "Yes"):
                self._save_gqrx_cfg_file(options)

        self._save_cfg_file(cfg_name, options)

        return True

    def set_callbacks(self):
        if hasattr(self, "rx_cfg_file"):
            self.rx_cfg_file.buttonClicked.connect(self.callback_rx_cfg_file)

    def _save_cfg_file(self, cfg_name, options):
        config_file = config._cfg_file_name(cfg_name, self.default_cfg_dir)
        config._write_cfg_file(config_file, options)
        self.wizard.cfg_file = config_file

    def _save_gqrx_cfg_file(self, options):
        gqrx.gqrx_config(self.gqrx_file, options, interactive=False)

    def _save_channel_cfg_file(self, cfg_dir, chan_cfg, options):
        chan_file = os.path.join(cfg_dir, chan_cfg + "-channel.conf")
        config.write_chan_conf(options, chan_file, yes=True)
        self.save_options("setup.channel", chan_file)

    def set_next_page(self):
        # Check if there are any dependencies to install.
        target = config.get_rx_label(self.wizard.config_options)
        if not dependencies.check_dependencies(
                target) and self.wizard.show_dependencies_page:
            self.next_page = Pages.DEPENDENCIES_PAGE
        else:
            self.next_page = Pages.FINISH_PAGE

    @Slot()
    def callback_rx_cfg_file(self):
        self._toggle_visibility(
            visible=self.rx_cfg_file.checkedButton().text() == "No",
            components=self.get_components_from_layout("rx_cfg_name"))


class DependenciesPage(DefaultConfigPage):

    def __init__(self, wizard):
        super().__init__(wizard=wizard,
                         title="Install Dependencies",
                         subtitle=" ",
                         watermark="satellite",
                         options_key="",
                         default_obj_name="")

    def initializePage(self):
        super().initializePage()

        target = config.get_rx_label(self.wizard.config_options)
        self.deps = DepsInstaller(self, target=target)
        if self.deps.finished:
            # The installer component checks if the dependencies are already
            # installed when instanciated.
            self.completeChanged.emit()
        else:
            self.deps.sig_finished.connect(lambda: self.completeChanged.emit())
        self.group_layout.addWidget(self.deps)

    def isComplete(self):
        return self.deps.finished

    def set_next_page(self):
        self.next_page = Pages.FINISH_PAGE


class FinishPage(DefaultConfigPage):

    def __init__(self, wizard):
        super().__init__(wizard=wizard,
                         title="Complete configuration",
                         subtitle=" ",
                         watermark="satellite",
                         options_key="",
                         default_obj_name="")

    def initializePage(self):
        super().initializePage()

        self.add_text_component("Configuration completed!\n")
        self.add_text_component(
            "The configuration file was saved at:\n{}".format(
                self.wizard.cfg_file))

        self.wizard.sig_finished.emit(self.wizard.cfg_file)

    def nextId(self):
        return -1
