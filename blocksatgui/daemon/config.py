import logging
import os
import subprocess
import sys
import tempfile
import time
import uuid
from argparse import Namespace
from shutil import which

from blocksatcli import util

from ..components import dialogs, messagebox, threadlogger
from ..components.viewer import BaseViewer, GuiViewer
from ..components.worker import start_job
from ..qt import QApplication, QDialogButtonBox, QObject, QThreadPool, Signal
from . import daemonstatus, dependencies

CONFIG_FILES = {
    "dbus": {
        "name": "D-Bus configuration file",
        "filename": "com.blockstream.satellite.conf",
        "path": "/usr/share/dbus-1/system.d/",
    },
    "polkit": {
        "name": "Polkit action file",
        "filename": "com.blockstream.satellite.policy",
        "path": "/usr/share/polkit-1/actions/",
    },
    "systemd": {
        "name": "Systemd unit file",
        "filename": "blockstream-satellite.service",
        "path": "/usr/lib/systemd/system/",
    }
}

BLOCKSATD = {
    "name": "com.blockstream.satellite.runner",
    "interface": "/com/blockstream/satellite/runner",
    "filename": "blocksatd.py",
}


class DaemonInstaller():

    def __init__(self,
                 viewer: BaseViewer,
                 runner: util.ProcessRunner,
                 logger=None,
                 interactive=True,
                 dry=False):
        self.viewer = viewer
        self.gui_path = self._get_gui_path()
        self.config_path = os.path.join(self.gui_path, "config")
        self.interactive = interactive
        self.runner = runner
        self.dry = dry
        self.runner.dry = dry
        self.logger = logger or logging.getLogger(__name__)

        if not os.path.exists(self.gui_path):
            raise RuntimeError("Could not find blocksat-gui installed on "
                               "the system.")

        # Generate new secret
        self.generate_secret()

    def _get_gui_path(self) -> str:
        """Get blocksat GUI path"""
        this_file = os.path.realpath(__file__)
        root_path = os.path.dirname(os.path.dirname(this_file))
        return os.path.join(root_path)

    def _get_config(self, name):
        """Get source and destination path to configuration file"""
        assert name in CONFIG_FILES.keys()
        source_config = os.path.join(self.config_path,
                                     CONFIG_FILES[name]["filename"])
        dest_config = os.path.join(CONFIG_FILES[name]["path"],
                                   CONFIG_FILES[name]["filename"])
        return (source_config, dest_config, CONFIG_FILES[name]["name"])

    def _install_file(self, source_file, dest_file, force=False) -> bool:
        """Install configuration file"""
        if not force and os.path.exists(dest_file):
            return True

        self.logger.debug(f"Install {source_file} at {dest_file}")
        res = self.runner.run(["install", "-m", "644", source_file, dest_file],
                              root=True,
                              nocheck=True)
        return res is not None and res.returncode == 0

    def _reload_systemd_unit(self, use_local_path=True):
        """Reload systemd unit file

        Args:
            use_local_path: Whether to use local blocksatd path

        """
        self.logger.info("Reloading systemd unit file")
        source, dest, _ = self._get_config("systemd")

        if use_local_path:
            blocksatd_path = os.path.join(self.gui_path, 'blocksatd.py')
            with open(source, "r") as fd:
                systemd_unit = fd.read()
                systemd_unit_mod = systemd_unit.replace(
                    "ExecStart=blocksatd",
                    f"ExecStart={sys.executable} {blocksatd_path}")

            temp_file = tempfile.NamedTemporaryFile(mode="w", delete=False)
            with temp_file as fd:
                temp_file.write(systemd_unit_mod)

            # Make the modified version the new source
            source = temp_file.name

        self._install_file(source, dest, force=True)
        self.runner.run(['systemctl', 'daemon-reload'], root=True)

    def is_blocksatd_running(self):
        """Check if blocksatd is running"""
        blocksatd_name = 'com.blockstream.satellite.runner'
        blocksatd_interface = '/com/blockstream/satellite/runner'

        try:
            import dbus
        except ImportError:
            self._install_dbus_python()

            # After install, try to re-import dbus
            import dbus

        dbus_client = dbus.SystemBus()
        try:
            dbus_client.get_object(blocksatd_name, blocksatd_interface)
            status = True
        except dbus.exceptions.DBusException:
            status = False

        return status

    def _install_dbus_python(self):
        if self.interactive and not self.viewer.ask_yes_or_no(
                msg=(
                    "Dbus module is missing. Would you like to install it now?"
                ),
                title="Required Dependency"):
            sys.exit()

        self.logger.info("Installing dbus module.")
        args = Namespace(dry_run=self.dry, yes=not self.interactive)
        dependencies.install(args)
        self.logger.info("Dbus module installed.")

    def _check_blocksatd_service(self):
        """Check if blocksatd service exists"""
        blocksat_systemd_unit = CONFIG_FILES["systemd"]["filename"]
        exists = self.runner.run(
            ["systemctl", "status", blocksat_systemd_unit],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            nocheck=True,
        )
        # status code 4 means the service does not exist
        return exists is not None and exists.returncode != 4

    def _start_blocksatd_service(self, enable=False):
        # Enable service
        blocksat_systemd_unit = CONFIG_FILES["systemd"]["filename"]
        if enable:
            is_enabled = self.runner.run(
                ["systemctl", "is-enabled", blocksat_systemd_unit],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                nocheck=True)

            if (is_enabled is None or is_enabled.returncode != 0):
                self.runner.run(["systemctl", "enable", blocksat_systemd_unit],
                                root=True)
            self.logger.info("Blocksat Daemon enabled.")

        # Start service
        self.runner.run(["systemctl", "start", blocksat_systemd_unit],
                        root=True)
        self.logger.info("Blocksat Daemon started.")

    def _run_blocksatd_standalone(self):
        """Run blocksatd as a standalone application"""
        self.logger.info("Running blocksatd in standalone mode.")

        blocksatd_path = os.path.join(self.gui_path, "blocksatd.py")

        cmd = [self.runner.auth_manager, sys.executable, blocksatd_path]

        if self.dry:
            print("> " + " ".join(cmd))
            return

        ps = subprocess.Popen(cmd, stdout=subprocess.DEVNULL)

        while not self.is_blocksatd_running():
            if ps.poll() is not None:
                sys.exit("An error occurred while running blocksatd in "
                         "standalone mode. Please try again.")
            time.sleep(2)

    def _run_blocksatd_service(self):
        """Start and enable blocksatd service"""
        self.logger.info("Running blocksatd as a systemd service.")
        self._start_blocksatd_service(enable=True)

    def is_blocksatd_installed_with_root(self) -> bool:
        """Check if blocksatd is installed with root privileges"""
        current_path = os.path.abspath(__file__)
        # If the current file is installed with root privileges, it will be
        # located under /usr. Thus, blocksatd should also be installed with
        # root privileges.
        if current_path.startswith("/usr"):
            return True
        return False

    def run_blocksatd(self, standalone=False) -> bool:
        """Launch blocksatd application

        Args:
            standalone: Whether to run blocksatd as a standalone application.

        Returns:
            bool: True if blocksatd is launched, False otherwise.
        """
        if self.is_blocksatd_running():
            return True

        if standalone:
            if self.interactive and not self.viewer.ask_yes_or_no(
                    msg=("Blocksat Daemon Application is not running. "
                         "Run it now?"),
                    title="Blocksatd Standalone Mode"):
                return False
            self._run_blocksatd_standalone()
            return True

        # Start the blocksatd service if already installed
        if self._check_blocksatd_service():
            self._start_blocksatd_service()
            return True

        self.logger.info("Blocksatd service not found.")

        # Ask user how to proceed
        if self.interactive:
            choice = self.viewer.ask_multiple_choice(
                vec=['Install', 'Run once', 'Cancel'],
                msg=("Blocksat Daemon Application is not running. "
                     "How would you like to proceed?"),
                label="Option",
                to_str=lambda x: '{}'.format(x),
                title="Run Blocksat Daemon")
        else:
            choice = "Install"

        if choice == "Install":
            if not self.install_config(include_service=True):
                return False
            self._run_blocksatd_service()
        elif choice == "Run once":
            self._run_blocksatd_standalone()
        else:
            return False

        return True

    def verify_config(self, include_service=False) -> list:
        """Check if all the configuration files is already in-place"""
        files = [  # D-Bus configuration files
            self._get_config("dbus"),
            self._get_config("polkit"),
        ]

        if include_service:
            service_file = self._get_config("systemd")
            files.append(service_file)

        config_missing = []
        for file in files:
            _, dest, name = file
            if not os.path.exists(dest):
                self.logger.info(f"{name} is missing.")
                config_missing.append(file)
        return config_missing

    def install_config(self, include_service=False) -> bool:
        """Install required configuration files to run blocksatd a service

        Args:
            include_service: Whether to install the systemd unit file to run
                blocksatd as a system service.

        Returns:
            bool: True if all the configuration files are installed, False
                otherwise.

        """
        config_list = self.verify_config(include_service)
        if not config_list:
            self.logger.info("Configuration files already installed")
            return True

        msg = ("The following configuration files are required to "
               "run Blocksat Daemon: \n" +
               "".join([f" - {x[2]}\n" for x in config_list]) +
               "\n Would you like to install them now?")

        if self.interactive and not self.viewer.ask_yes_or_no(
                msg=msg, default="y", title="Required Installation"):
            self.logger.info("Installation canceled.")
            return False

        for source, dest, name in config_list:
            self.logger.info(f"Installing {name}.")
            res = self._install_file(source_file=source, dest_file=dest)

            if self.dry:
                continue

            if not res:
                sys.exit(f"Error installing {name} at {dest}.")
            self.logger.info(f"{name} installed successfully.")

        return True

    def generate_secret(self):
        """Generate blocksatd secret"""
        id = uuid.uuid4().hex
        cfg_dir = os.path.join(util.get_home_dir(), ".blocksat")
        # Save at `~/.blocksat/` by default regardless of the user's cfg_dir so
        # that blocksatd can find the secret at this predefined location.
        if not os.path.exists(cfg_dir):
            os.makedirs(cfg_dir)

        cfg = os.path.join(cfg_dir, ".secret")
        with open(cfg, 'w') as fd:
            fd.write(id)


class DaemonInstallerGUI(QObject):
    """Assist the daemon installer with GUI operations"""

    sig_loggers = Signal(str)

    def __init__(self, gui):
        super().__init__(gui)
        self.gui = gui
        self.logger = threadlogger.set_logger_handler('daemon_installer',
                                                      self.sig_loggers)
        self.runner = util.ProcessRunner(self.logger)
        self.gui_viewer = GuiViewer(gui)
        self._thread_pool = QThreadPool()

    def _show_install_config_error(self, error):
        error_msg = ""
        if error[1] == SystemExit:
            error_msg = error[0].code
        error_msg = error_msg if isinstance(error_msg, str) else error[2]
        messagebox.Message(parent=self.gui, msg=error_msg)

    def _run_installation(self):
        """Run the installation process"""

        def _run_thread(self):
            start_job(func=install,
                      args=(
                          self.gui_viewer.get_viewer(),
                          self.runner,
                          self.logger,
                      ),
                      kwargs={
                          "dry": False,
                          "interactive": True
                      },
                      callback=lambda worker: _callback(worker, dialog),
                      thread_pool=self._thread_pool)

        def _callback(worker, dialog):
            if worker.error:
                print(worker.error.traceback)
            dialog.toggle_progress_bar(False)
            dialog.enable_button(True)
            dialog.accept()

        dialog = dialogs.GenericDialog(
            parent=self.gui,
            title="Install Blockstream Satellite Daemon",
            message=("Blockstream Satellite Daemon is required to improve "
                     "the GUI experience. Would you like to install it now?"),
            progress_bar=True,
            status_box=True)

        # Change buttons
        dialog.bnt.setStandardButtons(QDialogButtonBox.Close
                                      | QDialogButtonBox.Ok)
        dialog.bnt.setEnabled(True)
        dialog.bnt.button(QDialogButtonBox.Ok).setText("Continue")
        dialog.bnt.accepted.connect(lambda: _run_thread(self))
        dialog.bnt.rejected.connect(dialog.reject)
        dialog.bnt.accepted.connect(lambda: dialog.toggle_progress_bar(True))
        dialog.bnt.accepted.connect(lambda: dialog.enable_button(False))
        dialog.connect_status_signal(self.sig_loggers)
        self._dialog = dialog
        dialog.exec_()

    def _run_blocksatd(self, helper: DaemonInstaller):
        """Run blocksatd"""

        def _run_thread(self):
            standalone = not helper.is_blocksatd_installed_with_root()
            helper.interactive = False if standalone else True
            start_job(func=helper.run_blocksatd,
                      args=(standalone, ),
                      callback=lambda worker: _callback(worker, dialog),
                      thread_pool=self._thread_pool)

        def _callback(worker, dialog):
            if worker.error:
                msg = worker.error.traceback
                messagebox.Message(parent=self.gui,
                                   msg=msg,
                                   title="Error running blocksatd",
                                   msg_type="critical")
            dialog.accept()

        dialog = dialogs.GenericDialog(
            parent=self.gui,
            title="Run Blockstream Satellite Daemon",
            message="Blocksat Daemon is not running. Run it now? ",
            progress_bar=True,
            status_box=False)
        dialog.bnt.setStandardButtons(QDialogButtonBox.Close
                                      | QDialogButtonBox.Ok)
        dialog.bnt.setEnabled(True)
        dialog.bnt.button(QDialogButtonBox.Ok).setText("Start")
        dialog.bnt.accepted.connect(lambda: _run_thread(self))
        dialog.bnt.rejected.connect(dialog.reject)
        dialog.bnt.accepted.connect(lambda: dialog.toggle_progress_bar(True))
        dialog.bnt.accepted.connect(lambda: dialog.enable_button(False))
        dialog.exec_()

    def start(self):
        """Start Blockstream daemon service"""
        if os.geteuid() == 0:
            # No need for blocksatd when already running as root
            return

        if not which("pkexec"):
            messagebox.Message(
                parent=self.gui,
                title="Installation Error",
                msg=("The following packages are required to run the GUI. "
                     "Please make sure that it is installed: \n \"pkexec\"."))
            app = QApplication.instance()
            app.quit()  # Terminate the GUI
            return

        helper = DaemonInstaller(viewer=self.gui_viewer.get_viewer(),
                                 runner=self.runner,
                                 logger=self.logger,
                                 dry=False,
                                 interactive=True)
        helper.generate_secret()  # Generate new secret

        if daemonstatus.DBUS_ENABLED:
            dbus_client = daemonstatus.DbusClient()
            if dbus_client.is_blocksatd_recheable():
                return  # blocksatd is already running

        if dependencies.check_dependencies():
            missing_config = helper.verify_config()
            if not missing_config:
                self._run_blocksatd(helper)
                return

        self._run_installation()


def install(viewer: BaseViewer,
            runner: util.ProcessRunner,
            logger=None,
            dry=False,
            interactive=True):
    helper = DaemonInstaller(viewer=viewer,
                             runner=runner,
                             logger=logger,
                             dry=dry,
                             interactive=interactive)

    if helper.is_blocksatd_running():
        if logger:
            logger.info("Blocksat Daemon is already running.")
        return True

    # Install files required to run blocksatd as a dbus service
    if not helper.install_config(include_service=False):
        return

    standalone = False
    if not helper.is_blocksatd_installed_with_root():
        if logger:
            logger.info("Blocksat Daemon not found on system path.")
        standalone = True  # Run blocksatd as a standalone application
    helper.run_blocksatd(standalone=standalone)
