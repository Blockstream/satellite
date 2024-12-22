from enum import Enum, IntEnum, auto

import requests

from blocksatcli.cache import Cache
from blocksatcli.defs import user_guide_url
from blocksatcli.monitoring import ReportStatus
from blocksatcli.monitoring_api import DEFAULT_SERVER_URL, BsMonitoring

from ..components import messagebox
from ..components.defaultwizard import DefaultWizardPage
from ..components.gpg import AskGPGPassphrase, GPGInfoPage
from ..qt import (QCheckBox, QDialog, QFormLayout, QFrame, QGroupBox, QLabel,
                  QLineEdit, QObject, Qt, QVBoxLayout, QWizard, Signal, Slot)


class ReportStatusMsg(Enum):
    RUNNING = "Running Registration"
    NOT_REPORTING = "Not Reporting"
    FAILED = "Failed"
    REPORTING = "Reporting"


class RegistrationMsg(Enum):
    REGISTERED = "Receiver Registered"
    NOT_REGISTERED = "Not Registered"


class Reporter(QObject):
    """Reporter controller

    Signals:
        sig_status: Emitted when reporter status changes.
        sig_registered: Emitted when the registered attribute changes.
        sig_gpg_passphrase: Emitted when the gpg passphrase changes.

    """
    sig_status = Signal(str)
    sig_registered = Signal(bool)
    sig_gpg_passphrase = Signal(str)

    def __init__(self, parent, cfg_manager):
        super().__init__()

        self.view = ReporterViewer(parent)
        self.gui = parent
        self.cfg_manager = cfg_manager

        self._init_variables()
        self._connect_signals()

    def _init_variables(self):
        self.bs_monitor = None
        self.address = None
        self._registered = False
        self._gpg_passphrase = None

    @property
    def registered(self):
        return self._registered

    @registered.setter
    def registered(self, value):
        assert (isinstance(value, bool)), \
            f"Registered unsupported type {type(value)}"
        self._registered = value
        self.sig_registered.emit(value)

    @property
    def gpg_passphrase(self):
        return self._gpg_passphrase

    @gpg_passphrase.setter
    def gpg_passphrase(self, value):
        self._gpg_passphrase = value
        self.sig_gpg_passphrase.emit(value)

    def _connect_signals(self, viewer_only=False):
        """Connect signals"""
        self.view.checkbox.toggled.connect(self.save_report_option)
        self.view.checkbox.clicked.connect(self.callback_open_report_wizard)
        self.view.checkbox.clicked.connect(
            lambda: self.check_reporter_info(check_enabled=True))

        if viewer_only:
            return

        self.sig_gpg_passphrase.connect(self.callback_update_bs_monitor)
        self.sig_registered.connect(self.view.callback_update_registration)
        self.sig_status.connect(self.view.callback_update_status)
        self.sig_status.connect(self.callback_control_on_updated_status)

    def _get_bs_monitor(self):
        """Create an object of the BsMonitoring class"""
        return BsMonitoring(cfg=self.cfg,
                            cfg_dir=self.cfg_manager.cfg_dir,
                            server_url=self.report_url,
                            gnupghome=self.cfg_manager.gpg_home,
                            passphrase=self.gpg_passphrase,
                            interactive=False,
                            lazy=True)

    def disable_components(self, disable):
        """Disable components"""
        self.view.disable_widgets(disable)

    def save_report_option(self):
        """Save report option on user configuration"""
        if not hasattr(self, 'user_info'):
            return

        report = self.view.checkbox.isChecked()
        self.cfg_manager.save_gui_cache('reporter.status.' + self.cfg, report)

    def load_configuration(self, rx_config, report_url):
        """Load the receiver configuration to setup the reporter

        Args:
            rx_config (dict): Dictionary with receiver configuration.
            report_url (str): Remote server address.

        """
        self._init_variables()

        # Reset the widgets status before load a new configuration.
        # Before reseting the widgets, disconnect the viewer so there is no
        # side effect when resetings. After that, connect it again.
        self.view.checkbox.toggled.disconnect()
        self.view.checkbox.clicked.disconnect()
        self.view.reset_widgets()
        self._connect_signals(viewer_only=True)

        # Set information
        self.cfg = rx_config['cfg']
        self.user_info = rx_config['info']
        self.report_url = (report_url
                           if report_url is not None else DEFAULT_SERVER_URL)
        self.bs_monitor = self._get_bs_monitor()

        # Is reporter enabled and receiver registered?
        enable_report = self.cfg_manager.gui_cache.get('reporter.status.' +
                                                       self.cfg)
        self.registered = self.bs_monitor.registered
        if enable_report and self.registered:
            self.view.checkbox.setChecked(True)

        if self.registered:
            cache_cli = Cache(self.cfg_manager.cfg_dir)
            self.address = cache_cli.get(self.cfg + '.monitoring.location')

    @Slot()
    def callback_open_report_wizard(self):
        """Open report wizard if not registered"""
        if self.registered or not self.view.checkbox.isChecked():
            return

        reporter_wizard = ReporterWizard(self.cfg, self.cfg_manager.cfg_dir,
                                         self.cfg_manager.gpg_dir)
        reporter_wizard.exec_()
        if not reporter_wizard.complete:
            self.view.checkbox.setChecked(False)  # Disable reporting
            return

        self.address = reporter_wizard.address
        if reporter_wizard.gpg_passphrase is not None:
            self.gpg_passphrase = reporter_wizard.gpg_passphrase

    def check_reporter_info(self, check_enabled=False):
        """Check the receiver registration"""
        if check_enabled:
            if not self.view.checkbox.isChecked():
                return False

        if self.bs_monitor is None or self.bs_monitor.user_info is None:
            return False

        # Check the monitoring info in the receiver configuration file
        if ('monitoring' in self.bs_monitor.user_info
                and not self.bs_monitor.has_matching_keys()):
            fingerprint = self.bs_monitor.user_info['monitoring'][
                'fingerprint']
            self.registered = False
            self.bs_monitor.delete_credentials()
            self.view.checkbox.setChecked(False)
            messagebox.Message(
                parent=self.gui,
                title="GPG keypair not found",
                msg="Could not find key {} in the local keyring".format(
                    fingerprint),
                msg_type="warning")
            return False

        # Check GPG passphrase
        if self.gpg_passphrase is None:
            if not self.callback_ask_gpg_passphrase():
                if self.view.checkbox.isChecked():
                    messagebox.Message(parent=self.gui,
                                       title="GPG passphrase not found",
                                       msg="Disabling reporter option",
                                       msg_type="warning")
                    self.view.checkbox.setChecked(False)
                return False

        # Check non-GPG password
        if ('monitoring' in self.bs_monitor.user_info
                and self.gpg_passphrase is not None
                and self.bs_monitor.api_pwd is None):
            self.bs_monitor.load_api_password()
            if self.bs_monitor.api_pwd is None:
                msg = messagebox.Message(
                    parent=self.gui,
                    title="Password not found",
                    msg=("Unable to find the password for report "
                         "authentication. Generate new password?"),
                    msg_type="question",
                    lazy=True)

                if msg.exec_():
                    self.bs_monitor.gen_api_password()
                else:
                    return False

        return True

    @Slot()
    def callback_load_gpg_passphrase(self):
        """Load GPG passphrase"""
        # Open dialog window to ask GPG passphrase if None
        if self.gpg_passphrase is None:
            self.callback_ask_gpg_passphrase()

        return self.gpg_passphrase is None

    @Slot()
    def callback_update_bs_monitor(self, passphrase=None):
        gpg_passphrase = passphrase or self.gpg_passphrase

        self.bs_monitor = self._get_bs_monitor()
        if gpg_passphrase is not None:
            self.bs_monitor.gpg.set_passphrase(passphrase)

            if 'monitoring' in self.bs_monitor.user_info:
                self.bs_monitor.load_api_password()

    @Slot()
    def callback_ask_gpg_passphrase(self):
        """Ask GPG passphrase"""
        gpg_pass = AskGPGPassphrase(self.gui, self.cfg_manager.gpg_dir)
        if gpg_pass.exec_():
            self.gpg_passphrase = gpg_pass.get_passphrase()
            return True
        return False

    @Slot()
    def callback_update_report_status(self, status=None):
        """Update the reporter status

         Args:
            status (int): Report status.

        """
        if status is None or status == 0:
            status_msg = ReportStatusMsg.NOT_REPORTING.value
        elif status == requests.codes.ok:
            status_msg = ReportStatusMsg.REPORTING.value
        elif status == ReportStatus.REGISTRATION_RUNNING.value:
            status_msg = ReportStatusMsg.RUNNING.value
        elif status == 401:
            status_msg = ReportStatusMsg.FAILED.value + " (Not Authorized)"
        else:
            status_msg = ReportStatusMsg.FAILED.value + f"({status})"

        self.sig_status.emit(status_msg)

    @Slot()
    def callback_control_on_updated_status(self, status):
        """Control reporter component based on the reporter status"""
        if status == ReportStatusMsg.REPORTING.value:
            # Set registered status
            if not self.registered:
                self.registered = True

        elif status == ReportStatusMsg.RUNNING.value:
            self._enable_info_popup = True

        elif "Not Authorized" in status:
            self.gpg_passphrase = None


class ReporterViewer(QFrame):
    """Reporter viewer component
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.vbox = QFormLayout(self)
        self.vbox.setContentsMargins(20, 20, 20, 0)
        self.vbox.setSpacing(5)

        self.setObjectName('reporter')
        self._add_widgets()

    def _add_widgets(self):
        """Add widgets to the reporter component"""

        name = QLabel("RECEIVER MONITORING")
        name.setObjectName("card-title")

        info_box = QGroupBox("", self)
        info_layout = QFormLayout(info_box)

        self.checkbox = QCheckBox()
        self.registration = QLabel(RegistrationMsg.NOT_REGISTERED.value)
        self.status = QLabel(ReportStatusMsg.NOT_REPORTING.value)

        info_layout.addRow("Report: ", self.checkbox)
        info_layout.addRow("Register: ", self.registration)
        info_layout.addRow("Status: ", self.status)

        self.vbox.addWidget(name)
        self.vbox.addWidget(info_box)

    def reset_widgets(self):
        """Reset status components to the default value"""
        self.checkbox.setChecked(False)
        self.registration.setText(RegistrationMsg.NOT_REGISTERED.value)
        self.status.setText(ReportStatusMsg.NOT_REPORTING.value)

    def disable_widgets(self, disable=True):
        """Disable components"""
        self.checkbox.setDisabled(disable)

    @Slot()
    def callback_update_registration(self, registered):
        """Update the reporter registration status

        Args:
            registered (bool): Whether the receiver is registered.

        """
        registered_label = RegistrationMsg.REGISTERED.value \
            if registered \
            else RegistrationMsg.NOT_REGISTERED.value

        self.registration.setText(registered_label)

    @Slot()
    def callback_update_status(self, value: str):
        """Update reporter status

        Args:
            value (str): Reporter status message

        """
        self.status.setText(value)


class WizardPages(IntEnum):
    INITIAL_PAGE = auto()
    GPG_PAGE = auto()
    LOCATION_PAGE = auto()
    FINISH_PAGE = auto()


class ReporterWizard(QWizard):
    """Wizard for registering on the Blocksat monitoring server"""

    def __init__(self, cfg, cfg_dir, gpg_dir):
        super().__init__()

        self.cfg = cfg
        self.cfg_dir = cfg_dir
        self.gpg_dir = gpg_dir
        self.gpg_passphrase = None
        self.gpg_info = {}
        self.address = None
        self.complete = False

        # Wizard settings
        wizard_title = "Reporter registration"
        self.setFixedSize(640, 450)
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setWindowTitle(wizard_title)

        self.setOptions(QWizard.HaveHelpButton)

        # Wizard pages
        initial_page = InitialPage(self,
                                   title=wizard_title,
                                   subtitle="Overview")
        gpg_page = GPGInfoPage(self,
                               gpg_dir,
                               title=wizard_title,
                               subtitle="Create GPG Keyring",
                               individual_page=False)
        location_page = LocationPage(self,
                                     title=wizard_title,
                                     subtitle="Address Information")
        finish_page = FinishPage(self,
                                 title=wizard_title,
                                 subtitle="Next steps")

        self.setPage(WizardPages.INITIAL_PAGE, initial_page)
        self.setPage(WizardPages.GPG_PAGE, gpg_page)
        self.setPage(WizardPages.LOCATION_PAGE, location_page)
        self.setPage(WizardPages.FINISH_PAGE, finish_page)

        # Connect help button
        self.button(QWizard.HelpButton).clicked.connect(
            self.callback_open_help)

    def closeEvent(self, event):
        self.complete = False
        event.accept()

    def nextId(self):
        """Set the next wizard page"""
        current_id = self.currentId()

        if current_id == WizardPages.INITIAL_PAGE:
            return WizardPages.GPG_PAGE
        elif current_id == WizardPages.GPG_PAGE:
            return WizardPages.LOCATION_PAGE
        elif current_id == WizardPages.LOCATION_PAGE:
            return WizardPages.FINISH_PAGE
        else:
            # Set last page
            return -1

    @Slot()
    def callback_open_help(self):
        dialog_win = QDialog(self)
        layout = QVBoxLayout(dialog_win)

        msg_why = QLabel(
            "<h3>Why We Collect The Information</h3>"
            "<p>"
            "The location information (city, country, and state) "
            "collected on registration allows us to analyze the receiver "
            "performances worldwide and continuously improve the service. For "
            "example, it enables the identification of weak coverage spots. "
            "By reporting it, you will help us improve the Blockstream "
            "Satellite service. Besides, note we do not need the receiver's "
            "exact geolocation, only the coarse city/state coordinates."
            "</p"
            "<p>The public GPG key collected on registration is used for "
            "the initial registration procedure and, subsequently, for "
            "authenticating your requests to the monitoring API."
            "</p>")
        msg_why.setTextFormat(Qt.RichText)
        msg_why.setWordWrap(True)

        msg_url = QLabel("<p>"
                         "Please refer to further information at: "
                         "<br>"
                         "<a style='color: #358de5' "
                         f"href=\"{user_guide_url}doc/monitoring.html\"> "
                         "Monitoring User Guide"
                         "</a>"
                         "</p>")
        msg_url.setTextFormat(Qt.RichText)
        msg_url.setWordWrap(True)
        msg_url.setOpenExternalLinks(True)

        layout.addWidget(msg_why)
        layout.addWidget(msg_url)
        dialog_win.exec_()


class InitialPage(DefaultWizardPage):

    def __init__(self, wizard, title, subtitle):
        super().__init__(wizard, title, subtitle, watermark=None)

    def initializePage(self):
        super().initializePage()

        description = QLabel(
            "<h3> Report Receiver Data </h3>"
            "<p>"
            "Send periodic reports of your receiver performance metrics to "
            "Blockstream's monitoring server."
            "</p>"
            "<p>"
            "For registration, we require the following information:"
            "</p>"
            "<ul>"
            "<li>"
            "Your location (city, country, and state, if applicable)."
            "</li>"
            "<li>"
            "Your public GPG key, created and used by the Satellite API."
            "</li>"
            "</ul>")
        description.setTextFormat(Qt.RichText)
        description.setWordWrap(True)
        self.group_layout.addWidget(description)


class LocationPage(DefaultWizardPage):

    def __init__(self, wizard, title, subtitle):
        super().__init__(wizard, title, subtitle, watermark=None)

        self.wizard = wizard
        self.cache = Cache(self.wizard.cfg_dir)

    def initializePage(self):
        super().initializePage()

        address_box = QFrame()
        address_box.setObjectName("address_box")
        layout = QFormLayout(address_box)

        self.city = QLineEdit()
        self.state = QLineEdit()
        self.country = QLineEdit()

        layout.addRow("City:", self.city)
        layout.addRow("State (optional):", self.state)
        layout.addRow("Country:", self.country)
        layout.setVerticalSpacing(10)

        self.error = self.add_error_component("address_error")

        self.group_layout.addWidget(address_box)
        self.group_layout.addWidget(self.error)

        # Get cached address information
        cached_addr = self.cache.get(self.wizard.cfg + '.monitoring.location')
        if cached_addr:
            splitted_cached_addr = cached_addr.split(", ")
            self.city.setText(splitted_cached_addr[0])
            if len(splitted_cached_addr) >= 3:
                self.state.setText(splitted_cached_addr[1])
                self.country.setText(splitted_cached_addr[2])
            else:
                self.country.setText(splitted_cached_addr[1])

    def validate_inputs(self):
        city = self.city.text()
        state = self.state.text()
        country = self.country.text()

        city_valid = city != ""
        country_valid = country != ""

        self._display_error_message(city_valid, self.city, self.error,
                                    "Required field")
        self._display_error_message(country_valid, self.country, self.error,
                                    "Required field")

        valid = city_valid and country_valid

        if valid:
            if state != "":
                address = f"{city}, {state}, {country}"
            else:
                address = f"{city}, {country}"

            self.cache.set(self.wizard.cfg + '.monitoring.location', address)
            self.cache.save()
            self.wizard.address = address

        return valid


class FinishPage(DefaultWizardPage):

    def __init__(self, wizard, title, subtitle):
        super().__init__(wizard, title, subtitle, watermark=None)

    def initializePage(self):
        super().initializePage()

        info_msg = QLabel(
            "<h3>Next steps:</h3>"
            "<p>"
            "<ol>"
            "<li>"
            "The registration procedure will start as soon as the receiver "
            "is initialized."
            "</li>"
            "<li>"
            "A verification code will be sent to your receiver over "
            "satellite to finalize the authentication."
            "</li>"
            "</ol>"
            "\nFor more information, please refer to the "
            "<a style='color: #358de5' "
            f"href=\"{user_guide_url}doc/monitoring.html\"> "
            "Monitoring User Guide."
            "</p>")
        info_msg.setWordWrap(True)
        info_msg.setOpenExternalLinks(True)

        self.group_layout.addWidget(info_msg)
        self.wizard.complete = True
