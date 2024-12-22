import time
import traceback

import blocksatcli.defs
import blocksatcli.satip
import blocksatcli.sdr
import blocksatcli.standalone
import blocksatcli.usb

from ..components import dialogs, threadlogger
from ..qt import QDialogButtonBox, QObject, QThread, QWidget, Signal, Slot

receiver_map = {
    blocksatcli.defs.sdr_setup_type: {
        "args": {
            "config": ["sdr"],
            "run": ["sdr"]
        },
        "module": blocksatcli.sdr,
    },
    blocksatcli.defs.standalone_setup_type: {
        "args": {
            "config": ["standalone", "cfg"],
            "run": ["standalone", "monitor"]
        },
        "module": blocksatcli.standalone,
    },
    blocksatcli.defs.linux_usb_setup_type: {
        "args": {
            "config": ["usb", "config"],
            "run": ["usb", "launch"]
        },
        "module": blocksatcli.usb,
    },
    blocksatcli.defs.sat_ip_setup_type: {
        "args": {
            "config": [],
            "run": ["sat-ip"]
        },
        "module": blocksatcli.satip,
    }
}

permissions_map = {
    blocksatcli.defs.sdr_setup_type:
    ("The next step will configure the maximum pipe size currently configured "
     "in your OS. Proceed?"),
    blocksatcli.defs.standalone_setup_type:
    ("The next step will configure the signal parameters on "
     "the S400 receiver and the network settings on the host. "
     "The changes to the host will be the following:\n\n"
     "- Configuration of Linux reverse path (RP) filtering rules "
     "to allow reception of one-way Blockstream Satellite traffic.\n"
     "- Configuration of firewall rules to accept the Blockstream "
     "Satellite traffic.\n"
     "\n If you would like to review the changes before applying them, "
     "run the following command on the terminal in dry-run mode:\n\n"
     "blocksat-cli standalone cfg --dry-run"),
    blocksatcli.defs.sat_ip_setup_type: (""),
    blocksatcli.defs.linux_usb_setup_type:
    ("The next step will create and configure a network interface to "
     "output the IP traffic received via the TBS receiver."
     "The changes to the host will be the following:\n\n"
     "- Creation of the DVB network interface.\n"
     "- Configuration of Linux reverse path (RP) filtering rules "
     "to allow reception of one-way Blockstream Satellite traffic.\n"
     "- Configuration of firewall rules to accept the Blockstream "
     "Satellite traffic.\n"
     "\n If you would like to review the changes before applying them, "
     "run the following command on the terminal in dry-run mode:\n\n"
     "blocksat-cli usb cfg --dry-run"),
}


def get_receiver_module(label):
    return receiver_map[label]["module"]


class RxConfig(QWidget):
    """Configure receiver

    Args:
        parent: Parent widget
        args (Namespace): Command-line arguments for receiver configuration
        label (str): Receiver label ("sdr", "standalone", "usb" or "sat-ip")

    Signals:
        sig_log: Emitted when the worker thread logs a message

    """
    sig_log = Signal(str)
    sig_run_config = Signal()
    sig_close_config = Signal()

    def __init__(self, parent, args, rx_type):
        assert (rx_type in receiver_map.keys())
        super().__init__(parent)

        self.parent = parent
        self.args = args
        self.module = get_receiver_module(rx_type)
        self.rx_type = rx_type

        self.configured = False

    def exec_(self):
        if self.rx_type == blocksatcli.defs.sat_ip_setup_type:
            return True

        dialog = dialogs.GenericDialog(parent=self.parent,
                                       title="Checking Configuration",
                                       message="",
                                       progress_bar=True,
                                       status_box=True)
        # Change buttons
        dialog.bnt.setStandardButtons(QDialogButtonBox.Close
                                      | QDialogButtonBox.Ok)
        dialog.bnt.setEnabled(False)
        dialog.bnt.button(QDialogButtonBox.Ok).setText("Configure")

        # Connect signals
        dialog.bnt.accepted.connect(lambda: self.sig_run_config.emit())
        dialog.bnt.rejected.connect(lambda: self.callback_cancel(dialog))
        dialog.connect_status_signal(self.sig_log)

        self.start_configuration_thread(dialog)
        dialog.exec_()

        return self.configured

    @Slot()
    def start_configuration_thread(self, dialog):
        # Get custom logger
        logger = threadlogger.set_logger_handler("ConfigWorker", self.sig_log)

        # Clean status box
        dialog.clean_status_box()
        dialog.running = True

        # Reset status
        self.failed = False
        self.configured = False

        worker = ConfigWorker(self.args, self.module, self.rx_type, logger)
        thread = QThread()
        worker.moveToThread(thread)

        dialog.connect_status_signal(worker.sig_traceback)

        thread.started.connect(lambda: dialog.enable_button(False))
        thread.started.connect(lambda: dialog.toggle_progress_bar(True))
        thread.started.connect(worker.verify)
        worker.sig_verify_finished.connect(
            lambda: dialog.toggle_progress_bar(False))
        worker.sig_verify_finished.connect(self.callback_check_config)
        worker.sig_verify_finished.connect(
            lambda: self.callback_set_configure_text(dialog))
        worker.sig_verify_finished.connect(lambda: dialog.enable_button(True))
        worker.sig_verify_finished.connect(
            lambda: dialog.toggle_close_event(False))

        self.sig_run_config.connect(lambda: dialog.toggle_close_event(True))
        self.sig_run_config.connect(worker.run)
        self.sig_run_config.connect(lambda: dialog.toggle_progress_bar(True))
        self.sig_run_config.connect(lambda: dialog.enable_button(False))
        self.sig_close_config.connect(thread.quit)
        self.sig_close_config.connect(worker.deleteLater)

        thread.finished.connect(lambda: dialog.toggle_progress_bar(False))
        worker.sig_finished.connect(thread.quit)
        worker.sig_error.connect(self.callback_status_failed)
        thread.finished.connect(lambda: self.callback_status_finished(dialog))
        worker.sig_finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(lambda: dialog.toggle_close_event(True))

        thread.start()

        # Prevent from the garbage collector
        self._thread = thread
        self._worker = worker

    @Slot()
    def callback_cancel(self, dialog):
        self.configured = False
        self.sig_close_config.emit()
        dialog.reject()

    @Slot()
    def callback_check_config(self, configured):
        """Check RX configuration"""
        if configured:
            self.sig_close_config.emit()
            return

        self.configured = configured

    @Slot()
    def callback_set_configure_text(self, dialog):
        if not self.configured:
            dialog.set_title_text("Configure Receiver")
            dialog.set_message_text(permissions_map[self.rx_type])

    def callback_status_failed(self):
        self.failed = True

    @Slot()
    def callback_status_finished(self, dialog):
        self.running = False
        if self.failed:
            self.sig_log.emit("\nConfiguration failed!")
            dialog.toggle_status_style(error=True)
            dialog.bnt.clear()
            dialog.bnt.setStandardButtons(QDialogButtonBox.Close)
            dialog.bnt.rejected.connect(lambda: self.callback_cancel(dialog))
            dialog.bnt.setEnabled(True)
        else:
            self.sig_log.emit("\n Receiver configured!")
            self.configured = True
            dialog.accept()  # Automatically close the window.


class ConfigWorker(QObject):

    sig_finished = Signal()
    sig_error = Signal()
    sig_traceback = Signal(str)
    sig_verify_finished = Signal(bool)

    def __init__(self, args, module, rx_type, logger):
        super().__init__()

        self.args = args
        self.module = module
        self.rx_type = rx_type
        self.config_list = None

        # Set new logger for receiver module
        self.module.logger = logger

    @Slot()
    def run(self):
        self.module.logger.info("Running configuration...")

        if hasattr(self.args, 'func'):
            try:
                if self.rx_type == blocksatcli.defs.sdr_setup_type:
                    self.module.configure(self.args)
                else:
                    self.args.func(self.args, self.config_list)
            except SystemExit:
                self.sig_error.emit()
            except:  # noqa: ignore=E722
                self.sig_error.emit()
                self.sig_traceback.emit(traceback.format_exc())
            finally:
                self.sig_finished.emit()

    @Slot()
    def verify(self):
        self.config_list = None

        try:
            self.config_list = self.module.verify(self.args)
            if isinstance(self.config_list, dict):
                rx_configured = all(
                    [r for r in self.config_list['config'].values()])
            else:
                rx_configured = bool(self.config_list)
                time.sleep(1)
        except SystemExit:
            rx_configured = False
        except:  # noqa: ignore=E722
            rx_configured = False
            self.sig_traceback.emit(traceback.format_exc())

        if not rx_configured:
            self.module.logger.info("Receiver not configured.")
        else:
            self.module.logger.info("Receiver already configured.")

        self.sig_verify_finished.emit(rx_configured)
