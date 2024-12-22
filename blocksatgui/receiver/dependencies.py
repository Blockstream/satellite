import traceback
from typing import Optional

import blocksatcli.dependencies
import blocksatcli.main
import blocksatcli.util

from ..components import messagebox
from ..components.viewer import BaseViewer, GuiViewer
from ..qt import (QDialog, QDialogButtonBox, QFrame, QLabel, QObject,
                  QProgressBar, QPushButton, QTextEdit, QThread, QVBoxLayout,
                  Signal, Slot)

# Set pkexec as the default authorization manager
blocksatcli.util.ProcessRunner.set_auth_manager("pkexec")


class DepsDialog(QDialog):

    def __init__(self, parent, target, command="packages"):
        super().__init__(parent)
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        self._layout = QVBoxLayout(self)

        self.installer = DepsInstaller(parent,
                                       target,
                                       command,
                                       disable_install_bnt=True)

        bnt = QDialogButtonBox()
        bnt.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        self._layout.addWidget(self.installer)
        self._layout.addWidget(bnt)

        # Add connections
        ok_bnt = "Install" if command != "update" else "Update"
        bnt.button(QDialogButtonBox.Ok).setText(ok_bnt)
        bnt.button(QDialogButtonBox.Cancel).setText("Close")
        bnt.button(QDialogButtonBox.Ok).clicked.connect(
            lambda: self._callback_buttons_ctl(bnt, False))
        self.installer.sig_finished.connect(
            lambda: self._callback_buttons_ctl(bnt, True))
        bnt.accepted.connect(self._install)
        bnt.rejected.connect(self._cancel)

        self.adjustSize()

    def _callback_buttons_ctl(self, bnt, enabled=True):
        if not enabled:
            bnt.button(QDialogButtonBox.Ok).setText("Installing")
            bnt.button(QDialogButtonBox.Ok).setDisabled(True)
            bnt.button(QDialogButtonBox.Cancel).setDisabled(True)
        else:
            bnt.button(QDialogButtonBox.Ok).setText("Install")
            bnt.button(QDialogButtonBox.Cancel).setDisabled(False)

    def _install(self):
        self.installer.install()

    def _cancel(self):
        self.reject()


class DepsInstaller(QFrame):

    sig_running = Signal()
    sig_finished = Signal()
    sig_error = Signal()

    def __init__(self,
                 parent,
                 target=None,
                 command="packages",
                 disable_install_bnt=False):
        assert (command in ["packages", "drivers", "btc", "update"])

        super().__init__(parent)

        self.target = target
        self.command = command

        self.failed = False
        self.finished = False
        self.parser = blocksatcli.main.get_parser()
        self.gui_viewer = GuiViewer(self)

        self._add_components(disable_install_bnt)
        if not disable_install_bnt:
            # Do not connect the install function if the installation button is
            # disabled. We can reuse this installer in a QDialog, and connect
            # the install function with the dialog buttons instead.
            self._connect_signals(self.install_bnt)

    def _add_components(self, disable_install_bnt):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 0)

        if self.command == "packages":
            title_text = "Install Software Dependencies"
            text = "The following packages will be installed:\n"
            pkg_mapper = blocksatcli.dependencies.PkgMap()
            pkg_manager = blocksatcli.dependencies.get_pkg_manager()
            packages = pkg_mapper.get_packages(self.target, pkg_manager)
            for package in packages:
                text += f"- {package}\n"

        elif self.command == "drivers":
            title_text = "Install TBS Drivers"
            text = (
                "The device drivers required to use the TBS "
                "receiver will be installed. \n\n"
                "**Important**: The drivers are installed by "
                "rebuilding and rewriting the Linux Media drivers. Hence, "
                "if this machine is not dedicated to host the receiver, it "
                "would be safer and **recommended** to install the drivers on "
                "a virtual machine and use it to host the receiver. \n\n"
                "If you would like to review the installation process, first "
                "run the following command on the terminal:\n\n"
                "blocksat-cli deps tbs-drivers --dry-run\n\n"
                "Are you sure you want to continue?")
        elif self.command == "btc":
            title_text = "Install Bitcoin Satellite"
            text = ("Bitcoin Satellite will be installed in your OS. Proceed?")
        elif self.command == "update":
            title_text = "Update Software Dependencies"
            text = ("The software dependencies will be updated. Proceed?")

        # Components
        self.status = QLabel()
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 1)
        self.install_bnt = QPushButton("Install")

        msg = QTextEdit()
        msg.setReadOnly(True)
        msg.setMarkdown(text)
        title = QLabel(title_text)
        title.setProperty("qssClass", "dialog__title")

        layout.addWidget(title)
        layout.addWidget(msg)
        layout.addWidget(self.status)
        layout.addWidget(self.progress_bar)

        if not disable_install_bnt:
            layout.addWidget(self.install_bnt)

    def _connect_signals(self, bnt):
        bnt.clicked.connect(self.install)

    def _reset_states(self):
        self.failed = False
        self.finished = False

    def install(self):
        self._reset_states()

        if self.command == "packages":
            cmd = ["deps", "-y", "install"]
        elif self.command == "drivers":
            cmd = ["deps", "-y", "tbs-drivers"]
        elif self.command == "btc":
            cmd = ["deps", "-y", "install", "--btc"]
        elif self.command == "update":
            cmd = ["deps", "-y", "update"]

        # If the dependencies are already installed, do not proceed with the
        # installation
        if (self.command == "packages"
                and blocksatcli.dependencies.check_dependencies(self.target)):
            self.status.setText("Dependencies already installed.")
            self.finished = True
            self.install_bnt.setDisabled(True)
            self.sig_finished.emit()
            return

        args = self.parser.parse_args(cmd)
        if self.target:
            setattr(args, "target", self.target)

        worker = Worker(args,
                        command=self.command,
                        viewer=self.gui_viewer.get_viewer())
        thread = QThread()
        worker.moveToThread(thread)

        thread.started.connect(self.callback_status_msg)
        thread.started.connect(lambda: self.progress_bar.setRange(0, 0))
        thread.started.connect(lambda: self.install_bnt.setDisabled(True))
        thread.started.connect(
            lambda: self.install_bnt.setText("Installing..."))
        thread.started.connect(worker.run)
        thread.started.connect(lambda: self.sig_running.emit())
        worker.sig_finished.connect(thread.quit)
        worker.sig_finished.connect(self.callback_reboot_message)
        worker.sig_finished.connect(self.callback_finished)
        worker.sig_show_error.connect(self.callback_error_msg)
        worker.sig_show_error.connect(lambda: self.sig_error.emit())
        thread.finished.connect(lambda: self.progress_bar.setRange(0, 1))
        thread.finished.connect(lambda: self.sig_finished.emit())
        thread.finished.connect(lambda: self.install_bnt.setText("Install"))
        thread.finished.connect(self.callback_status_msg)
        worker.sig_finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.start()

        self._thread = thread
        self._worker = worker

    def callback_finished(self):
        self.finished = True

    @Slot()
    def callback_error_msg(self, error):
        self.failed = True
        messagebox.Message(self, title="Error", msg=error)

    @Slot()
    def callback_status_msg(self):
        if self._thread.isRunning():
            text = "Running... This may take a few minutes. Please wait."
        elif self.failed:
            text = "Installation failed."
        else:
            text = "Installation completed successfully."
            if self.command == "drivers":
                text += " Please reboot now."

        self.status.setText(text)

    @Slot()
    def callback_reboot_message(self):
        if not self.failed and self._worker.reboot_required():
            messagebox.Message(
                parent=self,
                msg=("Please reboot to load the new kernel and start the "
                     "installation process again."),
                title="TBS Drivers installation",
                msg_type="info")


class Worker(QObject):

    sig_finished = Signal()
    sig_show_error = Signal(str)

    def __init__(self, args, command, viewer=Optional[BaseViewer]):
        super().__init__()

        self.args = args

        if command == "drivers":
            assert (viewer is not None)
            blocksatcli.util.ask_yes_or_no = (
                lambda msg, default='y', help_msg=None: viewer.ask_yes_or_no(
                    msg=msg,
                    default=default,
                    help_msg=help_msg,
                    title="TBS Drivers installation"))

    @Slot()
    def run(self):
        try:
            self.args.func(self.args)
        except SystemExit:
            pass
        except:  # noqa: ignore=E722
            self.sig_show_error.emit(traceback.format_exc())
        finally:
            self.sig_finished.emit()

    def callback_asked_user(self, msg):
        """Save in cache if kernel update was requested"""
        if "Kernel update" in msg:
            self._reboot_required = True

    def reboot_required(self):
        """Check if reboot is required after installing dependencies"""
        if hasattr(self, "_reboot_required"):
            return self._reboot_required

        return False
