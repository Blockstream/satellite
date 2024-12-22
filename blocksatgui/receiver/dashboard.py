import os
import time
import traceback

import blocksatcli.config
import blocksatcli.defs
import blocksatcli.dependencies
import blocksatcli.main
import blocksatcli.monitoring
import blocksatcli.util

from ..components import (buttons, cards, dialogs, messagebox, page,
                          threadlogger)
from ..qt import (QFrame, QHBoxLayout, QLabel, QObject, QScrollArea,
                  QSizePolicy, Qt, QThread, QVBoxLayout, Signal, Slot)
from . import dependencies, reporter, rxconfig, rxoptions

# Set pkexec as the default authorization manager
blocksatcli.util.ProcessRunner.set_auth_manager("pkexec")


class ReceiverDashboard(page.Page):
    """Receiver page

    Signals:
        sig_rx_config: Emitted when the receiver configuration is loaded.
        sig_start_rx: Emitted when "run receiver" is requested.
        sig_stop_rx: Emitted when "stop receiver" is requested.
        sig_started_thr_rx: Emitted when receiver thread starts.
        sig_stopped_thr_rx: Emitted when receiver thread stops.
        sig_log: Emitted when the receiver-related log is available.
        sig_request_config_wizard: Emitted when the config wizard is requested.
        sig_show_dependency_bnt: Emitted to change dependency bnt visibility.

    """
    sig_rx_config = Signal(dict)
    sig_start_rx = Signal()
    sig_stop_rx = Signal()
    sig_started_thr_rx = Signal()
    sig_stopped_thr_rx = Signal()
    sig_log = Signal(str)
    sig_request_config_wizard = Signal()
    sig_show_dependency_bnt = Signal(bool)

    def __init__(self, cfg_manager):
        super().__init__(name="receiver-page", topbar_enabled=False)

        self._rx_config = None
        self.cfg_manager = cfg_manager
        self.parser = blocksatcli.main.get_parser()

        # Maintain the receiver state
        self.rx_running = False
        self.rx_stop_req = False

        # Load the dashboard components
        self.default_page = self._gen_default_page()
        self.receiver_page = self._gen_receiver_page()
        self.add_page(self.default_page, "default")
        self.add_page(self.receiver_page, "receiver")
        self._connect_signals()

    @property
    def rx_config(self):
        return self._rx_config

    @rx_config.setter
    def rx_config(self, value):
        self._rx_config = value
        self.sig_rx_config.emit(value)

    def _gen_default_page(self):
        """Generate receiver default page

        When no valid configuration is loaded, the default page shows a
        "configuration not found" message and a button to open the
        configuration wizard.

        """
        msg_label = QLabel("Configuration not found")
        msg_label.setFixedHeight(80)
        bnt_config = buttons.MainButton(name="Create receiver configuration",
                                        obj_name='config-bnt',
                                        width=300)
        bnt_config.clicked.connect(
            lambda: self.sig_request_config_wizard.emit())
        frame, layout = page.get_widget('default-config-wrapper', 'frame')
        layout.addWidget(msg_label, alignment=Qt.AlignHCenter)
        layout.addWidget(bnt_config)
        return frame

    def _gen_receiver_page(self):
        """Generate receiver page

        The receiver page contains the receiver options, the reporter options,
        and the run/stop button.

        """
        frame, layout = page.get_widget('receiver-wrapper', 'frame')
        layout.addWidget(self._generate_metrics_component())
        layout.addWidget(self._generate_receiver_and_reporter_component())
        layout.addWidget(self._generate_bnts_component())
        return frame

    def _connect_signals(self):
        """Connect signals between components"""
        # Save the receiver state. Is the receiver thread running?
        self.sig_started_thr_rx.connect(
            lambda: self.callback_receiver_state(True))
        self.sig_stopped_thr_rx.connect(
            lambda: self.callback_receiver_state(False))

        self.rx_bnt.clicked.connect(self.callback_start_stop_receiver)
        self.sig_stop_rx.connect(self.callback_stop_receiver)

        # Change button style
        self.sig_started_thr_rx.connect(
            lambda: self.callback_set_bnt_style("running"))
        self.sig_stopped_thr_rx.connect(
            lambda: self.callback_set_bnt_style("default"))

        # Disable components
        self.sig_start_rx.connect(
            lambda: self.callback_disable_components(True))
        self.sig_start_rx.connect(self.callback_run_receiver)
        self.sig_stop_rx.connect(
            lambda: self.callback_disable_components(False))
        self.sig_stopped_thr_rx.connect(
            lambda: self.callback_disable_components(False))

    def _generate_bnts_component(self):
        """Generate component to hold the run/stop and dependency buttons

        Returns:
            Qt frame with buttons

        """
        wrapper = QFrame()
        layout = QHBoxLayout(wrapper)
        layout.setAlignment(Qt.AlignBottom | Qt.AlignCenter)

        layout.addWidget(self._generate_dependency_bnt(), 1)
        layout.addWidget(self._generate_start_stop_button_component(), 1)

        return wrapper

    def _generate_metrics_component(self):
        """Generate receiver metrics component

        Returns:
            Qt frame containing all the individual metrics components

        """
        self.metrics_box = QFrame()
        self.metrics_box.setObjectName("metrics-box")
        self.metrics_box.setFixedHeight(190)
        self.metrics_layout = QHBoxLayout(self.metrics_box)

        for key, metrics in blocksatcli.monitoring.rx_metrics.items():
            card = self._generate_metric_box(metrics["label"], key)
            self.metrics_layout.addWidget(card, 1)

        return self.metrics_box

    def _generate_metric_box(self, name, key):
        """Generate individual metric box

        Args:
            name (str): Metric name displayed on the screen
            key (str): Identifier metric key

        Returns:
            Qt frame for receiver metric

        """
        return cards.MetricCard(name.upper(), key)

    def _generate_dependency_bnt(self):
        """Generate dependency button

        Returns:
            Qt button to install dependencies

        """
        dep_bnt = buttons.MainButton(name="Install Dependencies",
                                     obj_name="dependency_bnt")
        dep_bnt.setProperty("qssClass", "focus-bnt__blue")
        dep_bnt.clicked.connect(self._install_dependencies)
        self.sig_show_dependency_bnt.connect(self.callback_show_dependency_bnt)
        return dep_bnt

    def _remove_metric_box(self, key):
        """Remove individual metric box from layout

        Args:
            key (str): Identifier metric key

        """
        component = self.metrics_box.findChild(cards.MetricCard, f"card_{key}")
        component.deleteLater()

    def _generate_receiver_and_reporter_component(self):
        """Wrapper component to hold the receiver and reporter components

        Returns:
            Qt frame with receiver and reporter options.

        """
        box = QFrame()
        box.setObjectName('rx-and-rep-wrapper')
        layout = QVBoxLayout(box)
        layout.setContentsMargins(10, 0, 10, 10)
        layout.setSpacing(10)

        self.receiver_comp = rxoptions.ReceiverOptions()
        self.reporter_comp = reporter.Reporter(self, self.cfg_manager)
        self.reporter_comp.view.setSizePolicy(QSizePolicy.Expanding,
                                              QSizePolicy.Expanding)

        layout.addWidget(self.receiver_comp)
        layout.addWidget(self.reporter_comp.view)

        scroll = QScrollArea()
        scroll.setObjectName('rx-and-rep-wrapper')
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidgetResizable(True)
        scroll.setWidget(box)

        return scroll

    def _generate_start_stop_button_component(self):
        """Component with a unique button to start and stop the receiver

        Returns:
            Qt button

        """
        self.rx_bnt = buttons.MainButton(name="Run Receiver",
                                         obj_name='run-rx-bnt')
        self.rx_bnt.setCheckable(True)

        return self.rx_bnt

    def _open_run_dialog(self):
        """Open dialog window with receiver status"""
        assert (isinstance(self.rx_config, dict))
        args = self.rx_config['cli_args']['run']
        rx_type = self.rx_config['info']['setup']['type']

        run_dialog = dialogs.GenericDialog(parent=self,
                                           title="Running Receiver",
                                           message="",
                                           progress_bar=True,
                                           status_box=True,
                                           button='close')
        run_dialog.connect_status_signal(self.sig_log)
        run_dialog.bnt.rejected.connect(run_dialog.reject)
        run_dialog.toggle_button(visible=False)
        run_dialog.toggle_progress_bar(running=True)
        run_dialog.show()

        # Automatically run receiver thread
        self._run_receiver(args, rx_type, run_dialog)

    def _hide_run_dialog(self, dialog):
        """Hide dialog with receiver status"""
        dialog.hide()
        dialog.toggle_progress_bar(False)

    def _error_run_dialog(self, dialog):
        """Show dialog with receiver status if any error occurs"""
        if self.rx_stop_req:
            dialog.accept()
            return

        dialog.toggle_progress_bar(False)
        dialog.toggle_status_style(error=True)
        dialog.toggle_button(visible=True)
        dialog.show()

    def _run_receiver(self, args, rx_type, dialog):
        """Create, run and add connections to the receiver worker thread"""
        logger = threadlogger.set_logger_handler("ReceiverWorker",
                                                 self.sig_log)

        # Set running status
        dialog.running = True

        # Create the receiver thread
        thread = QThread()
        worker = ReceiverWorker(args=args,
                                module=rxconfig.get_receiver_module(rx_type),
                                logger=logger,
                                target=rx_type)
        worker.moveToThread(thread)

        dialog.connect_status_signal(worker.sig_stderr)
        dialog.connect_status_signal(worker.sig_traceback)

        # Connect signals
        thread.started.connect(lambda: self.sig_started_thr_rx.emit())
        thread.started.connect(worker.run)
        worker.sig_rx_metrics.connect(self.callback_update_rx_metrics_values)
        worker.sig_rx_metrics.connect(lambda: self._hide_run_dialog(dialog))
        worker.sig_reporter_status.connect(
            self.reporter_comp.callback_update_report_status)
        worker.sig_finished.connect(
            self.reporter_comp.callback_update_report_status)
        worker.sig_finished.connect(self.callback_reset_rx_metrics_values)
        worker.sig_finished.connect(thread.quit)
        worker.sig_finished.connect(worker.deleteLater)
        worker.sig_finished.connect(lambda: self._error_run_dialog(dialog))
        worker.sig_finished.connect(lambda: self.sig_stop_rx.emit())
        thread.finished.connect(lambda: self.sig_stopped_thr_rx.emit())
        thread.finished.connect(thread.deleteLater)

        # Prevent from the garbage collector
        self._thread = thread
        self._worker = worker

        thread.start()

    def _open_config_dialog(self):
        """Open receiver configuration dialog"""
        assert (isinstance(self.rx_config, dict))
        args = self.rx_config['cli_args']['config']
        rx_type = self.rx_config['info']['setup']['type']

        rx_config = rxconfig.RxConfig(parent=self, args=args, rx_type=rx_type)
        return rx_config.exec_()

    def _get_cli_args(self, rx_config_file):
        """Get command-line arguments to configure and run the receiver

        Generate the CLI arguments to configure and run the receiver based on
        the currently loaded configuration file.

        Args:
            rx_config_file (dict): Dictionary with the receiver configuration.

        """
        rx_type = rx_config_file['info']['setup']['type']

        # Get the correct CLI commands to configure and run the receiver
        rx_config_run_opts = rxconfig.receiver_map[rx_type]

        args = {}
        for k in ["config", "run"]:
            args[k] = self.parser.parse_args(rx_config_run_opts["args"][k])

            # Set the configuration paths
            if hasattr(args[k], 'cfg'):
                args[k].cfg = rx_config_file['cfg']
            if hasattr(args[k], 'cfg_dir'):
                args[k].cfg_dir = self.cfg_manager.cfg_dir

            # Set non-interactive mode if available
            if hasattr(args[k], 'yes'):
                args[k].yes = True

        return args

    def _is_config_file_loaded(self):
        """Check if the receiver configuration file is loaded in memory"""
        if self.rx_config is None:
            messagebox.Message(
                self,
                title="Config not found",
                msg=("Receiver configuration not found. Please go to the "
                     "Settings tab and generate or load a receiver "
                     "configuration."))

            self.sig_stop_rx.emit()
            return False

        return True

    def _open_dependency_dialog(self, target, command):
        """Open dialog window to install the receiver dependencies

        Args:
            target: Target receiver ('sdr', 'standalone', 'usb' or 'sat-ip')
            command: Command to be executed ('package' to install package
                     dependencies or 'drivers' to install driver dependencies)

        """
        inst_dep = dependencies.DepsDialog(parent=self,
                                           target=target,
                                           command=command)
        inst_dep.exec_()
        return inst_dep.installer.finished and not inst_dep.installer.failed

    def _install_dependencies(self):
        """Install dependencies if not available

        Returns:
            True if the dependencies are installed successfully, or False
            otherwise.

        """
        assert (isinstance(self.rx_config, dict))
        target = blocksatcli.config.get_rx_label(self.rx_config['info'])

        status_pkgs = blocksatcli.dependencies.check_dependencies(target)
        if not status_pkgs:
            status_pkgs = self._open_dependency_dialog(target,
                                                       command="packages")

        status_drivers = (blocksatcli.dependencies.check_drivers()
                          if target == "usb" else True)
        if not status_drivers:
            # Proceed with the USB driver installation if the target is the USB
            # receiver and the dependencies were installed successfully.
            status_drivers = self._open_dependency_dialog(target,
                                                          command="drivers")

        status = status_pkgs and status_drivers
        if status:
            # If dependencies are installed correctly, hide the dependency
            # button.
            self.sig_show_dependency_bnt.emit(False)

        return status

    def _check_bs_reporter(self):
        """Check if the reporter is enabled, if yes, get the user info"""
        args = self.rx_config['cli_args']
        if self.reporter_comp.check_reporter_info(check_enabled=True):
            self.reporter_comp.callback_load_gpg_passphrase()

            passphrase = self.reporter_comp.gpg_passphrase
            address = self.reporter_comp.address

            if passphrase is None:
                return

            # Include the GPG passphrase in the args and also send it to
            # the reporter component.
            args['run'].report_passphrase = passphrase
            args['run'].report = True
            args['run'].report_address = address
        else:
            args['run'].report = False

        return args

    def _update_rx_metrics_boxes(self, rx_config):
        """Update the receiver metrics components in the layout
        """
        rx_info = rx_config['info']
        target = blocksatcli.config.get_rx_label(rx_info)
        rx_type = rx_info['setup']['type']
        rx_metrics = blocksatcli.defs.supported_metrics_per_receiver[target]

        if rx_type == blocksatcli.defs.sdr_setup_type:
            cli_args = rx_config['cli_args']
            rx_metrics = rx_metrics[cli_args['run'].implementation]

        metrics_in_layout = []
        for component in self.metrics_box.findChildren(cards.MetricCard):
            metric_name = component.objectName().replace('card_', '')
            metrics_in_layout.append(metric_name)

        add_boxes = [x for x in rx_metrics if x not in metrics_in_layout]
        rm_boxes = [x for x in metrics_in_layout if x not in rx_metrics]

        for metric in rm_boxes:
            self._remove_metric_box(metric)

        for metric in add_boxes:
            box = self._generate_metric_box(
                name=blocksatcli.monitoring.rx_metrics[metric]["label"],
                key=metric)
            self.metrics_layout.addWidget(box, 1)

    def _update_dependency_bnt_visibility(self, rx_config):
        """Set dependency button visibility

        Set the dependency button to be visible if dependencies are not
        satisfied. Otherwise, hide the dependency button.

        """
        target = blocksatcli.config.get_rx_label(rx_config['info'])
        dep_required = (not blocksatcli.dependencies.check_dependencies(target)
                        or (target == "usb"
                            and not blocksatcli.dependencies.check_drivers()))

        self.sig_show_dependency_bnt.emit(dep_required)

    @Slot()
    def callback_show_dependency_bnt(self, visibility):
        """Change dependency button visibility

        Args:
            visibility: Whether the dependency button should be visible

        """
        dep_bnt = self.findChild(buttons.MainButton, 'dependency_bnt')
        if dep_bnt:
            dep_bnt.setVisible(visibility)

    @Slot()
    def callback_receiver_state(self, state):
        self.rx_running = state

    @Slot()
    def callback_disable_components(self, state):
        """Disable components in the screen

        When the receiver is running, the user should not be able to interact
        with some components, i.e., change the enable/disable and reporter or
        change any of the receiver parameters.

        """
        self.reporter_comp.disable_components(disable=state)
        self.receiver_comp.disable_components(disable=state)

    @Slot()
    def callback_start_stop_receiver(self):
        if self.rx_bnt.isChecked():
            self.sig_start_rx.emit()
        else:
            self.sig_stop_rx.emit()

        # Disable the receiver button if the receiver thread is running,
        # enabled it otherwise.
        disable_bnt = True if self.rx_running else False
        self.rx_bnt.setDisabled(disable_bnt)

    @Slot()
    def callback_run_receiver(self):
        """Callback to run the receiver

        Make sure that all the dependencies are satisfied before running the
        receiver thread:

        1. If not reporting to BS:
            - Check if the software dependency is installed, and
            - Run receiver configuration.

        2. If reporting to BS:
            - Check the GPG keyring;
            - GPG passphrase;
            - Software dependency, and
            - Run receiver configuration.

        """
        self.rx_stop_req = False

        # Check if the receiver configuration file is loaded
        if not self._is_config_file_loaded():
            self.sig_stop_rx.emit()
            return

        # Get receiver options from layout components
        if not self.receiver_comp.get_rx_options(self.rx_config):
            messagebox.Message(self, title="Error", msg="Invalid options")
            self.sig_stop_rx.emit()
            return

        # Install dependencies if not available
        if not self._install_dependencies():
            self.sig_stop_rx.emit()
            return

        # Check if reporter is enabled
        self._check_bs_reporter()

        # Configure and launches the receiver
        if self._open_config_dialog():
            self._open_run_dialog()
        else:
            self.sig_stop_rx.emit()

    @Slot()
    def callback_set_bnt_style(self, status="default"):
        assert (status in ["default", "running", "stopping"])
        if status == "running":
            self.rx_bnt.setText("Stop Receiver")
            self.rx_bnt.setDisabled(False)
        elif status == "stopping":
            self.rx_bnt.setText("Stopping Receiver")
            self.rx_bnt.setDisabled(True)
            self.rx_bnt.setChecked(False)
        else:
            self.rx_bnt.setText("Run Receiver")
            self.rx_bnt.setDisabled(False)
            self.rx_bnt.setChecked(False)

    @Slot()
    def callback_stop_receiver(self):
        self.rx_stop_req = True
        self.sig_log.emit("\nStopping receiver. Please wait...")

        if hasattr(self, "_worker"):
            self._worker.monitor.stop()

        if self.rx_running:
            self.callback_set_bnt_style("stopping")
        else:
            self.callback_set_bnt_style("default")

    @Slot()
    def callback_load_receiver_config(self, rx_config):
        """Load the receiver information

        This function is connected to the signal emitted from the settings
        page when a new configuration is loaded. It is responsible for updating
        the required fields on the receiver page.

        1. Make the receiver configuration available as a class attribute.
        2. Re-generate the receiver arguments.
        3. Update the receiver components.
        4. Update the reporter component.
        5. Update dependency button visibility.
        6. Show the receiver page to the user.

        Args:
            rx_config_file (dict): Dictionary with the receiver configuration.

        """
        if not rx_config:
            self.switch_page("default")
            return

        self.rx_config = rx_config
        self.rx_config['cli_args'] = self._get_cli_args(rx_config)

        # Update screen with the receiver model, type, and options
        self.receiver_comp.update_rx_info(self.rx_config)
        self.receiver_comp.add_rx_options(self.rx_config)

        # Update metrics boxes
        self._update_rx_metrics_boxes(self.rx_config)

        # Load reporter config on the reporter component
        args = self.rx_config['cli_args']
        self.reporter_comp.load_configuration(
            rx_config=self.rx_config, report_url=args['run'].report_dest)

        # Hide/Show the dependency button
        self._update_dependency_bnt_visibility(self.rx_config)

        # Switch to the receiver page
        self.switch_page("receiver")

    @Slot()
    def callback_update_rx_metrics_values(self, metrics):
        """Update the receiver metrics value in the screen

        Args:
            stats (dict): Dictionary with the receiver metrics

        """
        if metrics is None:
            return

        for metric, value in metrics.items():
            format_str = blocksatcli.monitoring.rx_metrics[metric][
                "format_str"]
            component = self.metrics_box.findChild(cards.MetricCard,
                                                   f"card_{metric}")
            component.value.setText("{:{fmt_str}}".format(value,
                                                          fmt_str=format_str))
            if not component.active:
                component.active = True

    @Slot()
    def callback_reset_rx_metrics_values(self):
        metrics_in_layout = self.metrics_box.findChildren(cards.MetricCard)
        for metric in metrics_in_layout:
            metric.value.setText("N/A")
            metric.active = False

    def stop_threads(self):
        if not hasattr(self, "_worker"):
            return

        if not self.rx_running:
            return

        self.callback_stop_receiver()
        self._thread.quit()

        start_time = time.time()
        timeout = 60
        while time.time() < start_time + timeout:
            if not self._thread.isRunning():
                break
            time.sleep(2)


class ReceiverWorker(QObject):
    """Worker thread to launch and monitor the receiver

    This worker inherits from QObject so that we can use QT's signal/slots
    mechanism. It will be responsible for running and monitoring the receiver.

    Signals:
        sig_rx_metrics: Emitted when the receiver metrics change.
        sig_report_status: Emitted when the reporter status change.
        sig_finished: Emitted when run function finished.
        sig_traceback: Emitted with the traceback if any exception occurs.

    """
    sig_rx_metrics = Signal(dict)
    sig_reporter_status = Signal(int)
    sig_finished = Signal()
    sig_traceback = Signal(str)
    sig_stderr = Signal(str)

    def __init__(self, args, module, logger, target):
        super().__init__()

        self.args = args
        self.module = module
        self.target = target

        # Set new logger for receiver module
        self.module.logger = logger

        # Get the reporter options
        self.report_opts = blocksatcli.monitoring.get_report_opts(args)
        self.report_opts['interactive'] = False
        if self.args.report:
            self.report_opts['address'] = self.args.report_address

    @Slot()
    def run(self):
        """Run the configured receiver

        This function instantiates a monitor object with a GUI callback and
        launches the receiver.

        """
        # Crete custom monitor
        self.monitor = blocksatcli.monitoring.Monitor(
            self.args.cfg_dir,
            report=self.args.report,
            report_opts=self.report_opts,
            callback=self.callback_rx_metrics)
        self.monitor.disable_event.clear()

        # Pipe to get stderr
        pipe = blocksatcli.util.Pipe()

        params = {'args': self.args, 'monitor': self.monitor}
        if self.target == blocksatcli.defs.sdr_setup_type:
            params['stderr'] = pipe.w_fo

        # Start the receiver
        try:
            self.module.logger.info("Running receiver...")
            self.args.func(**params)
        except SystemExit:
            pass
        except:  # noqa: ignore=E722
            # Use bare exception so the graphical interface do not close if
            # some exception occurs.
            self.sig_traceback.emit(traceback.format_exc())
        finally:
            self.callback_thread_stderr(pipe)
            self.sig_finished.emit()

    def callback_rx_metrics(self, data, report):
        """Callback to get receiver stats and blocksat reporter status"""
        self.sig_rx_metrics.emit(data)
        self.sig_reporter_status.emit(report)

    def callback_thread_stderr(self, pipe):
        """Emit stderr signal"""
        os.set_blocking(pipe.r_fd, False)  # Set non-blocking mode
        error = pipe.r_fo.readlines()
        if error:
            self.sig_stderr.emit('\nError:')
            for line in error:
                self.sig_stderr.emit(line.replace('\n', ''))
