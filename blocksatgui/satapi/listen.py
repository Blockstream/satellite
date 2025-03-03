from blocksatcli import config, util

from .. import qt
from ..components import buttons, page
from ..components.gpg import AskGPGPassphrase
from . import opts
from .api import SatApi


class ListenView(page.Page):

    sig_listen_start = qt.Signal()
    sig_listen_stop = qt.Signal()

    def __init__(self):
        super().__init__(name="satapi-listen", topbar_enabled=False)

        self._layout.setContentsMargins(10, 5, 5, 10)
        self.advanced_opts = opts.get_listen_opts()
        self.default_page = self._gen_default_page()
        self.listen_page = self._gen_listen_page()
        self.add_page(self.default_page, "default")
        self.add_page(self.listen_page, "listen")
        self.update_default_page()
        self.switch_page("default")

    def _gen_default_page(self):
        self._message = qt.QLabel("")
        self._message.setProperty("qssClass", "text_bold__gray")
        self._details = qt.QLabel("")
        self._details.setProperty("qssClass", "text_italic__gray")
        viewer, layout = page.get_widget('default-tab')
        layout.addWidget(self._message, alignment=qt.Qt.AlignCenter)
        layout.addWidget(self._details, alignment=qt.Qt.AlignCenter)
        return viewer

    def _gen_listen_page(self):
        title = qt.QLabel("Listen to satellite messages".upper())
        title.setProperty("qssClass", "metric-card__title")

        self.listen_output = qt.QPlainTextEdit()
        self.listen_output.setReadOnly(True)
        self.listen_output.setProperty("qssClass", "dialog__status")
        self.listen_options = self._add_listen_options()
        self.listen_bnt = buttons.MainButton("Listen")
        self.listen_bnt.setCheckable(True)
        self.listen_bnt.clicked.connect(self._emit_button_state_on_click)

        viewer, layout = page.get_widget('listen-tab')
        layout.setSpacing(5)
        layout.addWidget(title)
        layout.addWidget(self.listen_output, 2)
        layout.addWidget(self.listen_options, 1)
        layout.addWidget(self.listen_bnt, alignment=qt.Qt.AlignCenter)
        return viewer

    def _emit_button_state_on_click(self):
        if self.listen_bnt.isChecked():
            self.sig_listen_start.emit()
        else:
            self.sig_listen_stop.emit()

    def _add_listen_options(self):
        frame = qt.QFrame(self)
        frame.setObjectName("send-options")
        layout = qt.QVBoxLayout(frame)

        self.show_advanced_options = buttons.TextButton(
            "Show Advanced Options ►")
        self.show_advanced_options.setFixedHeight(30)

        self.advanced_options_box = qt.QGroupBox(self)
        self._layout_advanced_options = qt.QVBoxLayout(
            self.advanced_options_box)
        self.show_advanced_options.clicked.connect(
            self._toggle_advanced_options)

        # Add channels
        channels_box = opts.get_group_box(parent=self,
                                          name="Select Channels",
                                          opts=self.advanced_opts['channels'],
                                          layout='hbox')
        self._layout_advanced_options.addWidget(channels_box)

        # Network
        network_box = opts.get_group_box(parent=self,
                                         name="Network Options",
                                         opts=self.advanced_opts['network'],
                                         inline_label=False)
        self._layout_advanced_options.addWidget(network_box)

        # Message Format
        format_box = opts.get_group_box(parent=self,
                                        name="Message Format",
                                        opts=self.advanced_opts['format'],
                                        inline_label=False)
        self._layout_advanced_options.addWidget(format_box)

        # GPG
        gpg_box = opts.get_group_box(parent=self,
                                     name="GPG Options",
                                     opts=self.advanced_opts['gpg'],
                                     inline_label=False)
        self._layout_advanced_options.addWidget(gpg_box)

        # Save
        save_box = opts.get_group_box(parent=self,
                                      name="Save Options",
                                      opts=self.advanced_opts['save'],
                                      inline_label=False)
        self._layout_advanced_options.addWidget(save_box)

        self.advanced_options_box.setHidden(True)
        layout.addWidget(self.show_advanced_options, alignment=qt.Qt.AlignTop)
        layout.addWidget(self.advanced_options_box, 1)
        return frame

    def _toggle_advanced_options(self):
        show = True if self.advanced_options_box.isHidden() else False
        text = "Hide Advanced Options ▼" if show else "Show Advanced Options ►"
        self.show_advanced_options.setText(text)
        self.advanced_options_box.setHidden(not show)

    def set_network_interfaces(self, interfaces, default='lo'):
        widget = self.advanced_opts['network']['interface'].widget
        widget.clear()  # Clear previous items
        widget.addItems(interfaces)
        if default is not None:
            if default in interfaces:
                widget.setCurrentText(default)
            else:
                widget.setCurrentIndex(0)

    def append_output(self, text: str):
        text = text.strip()
        self.listen_output.appendPlainText(text)
        self.listen_output.centerCursor()
        self.listen_output.repaint()

    def clear_output(self):
        self.listen_output.clear()

    def set_senders(self, senders: list):
        self._senders = {}
        widget = self.advanced_opts['gpg']['sender'].widget
        widget.clear()
        for i, r in enumerate(senders):
            text = f"{r['uids']} ({r['fingerprint']})"
            widget.insertItem(i, text)
            self._senders[text] = r['fingerprint']

    def update_default_page(self, rx_loaded: bool = False):
        message, details = "", ""
        if not rx_loaded:
            message = "No receiver configuration loaded"
            details = "Please create or load a receiver configuration file "

        self._message.setText(message)
        self._details.setText(details)

    def set_listener_state(self, state: str):
        if state == 'stopping':
            text = "Stopping..."
            checked = False
            disabled = True
        elif state == 'stopped':
            text = "Listen"
            checked = False
            disabled = False
        else:
            text = "Stop"
            checked = True
            disabled = False

        self.listen_bnt.setText(text)
        self.listen_bnt.setChecked(checked)
        self.listen_bnt.setDisabled(disabled)
        self.advanced_options_box.setDisabled(state != 'stopped')

    def get_advanced_options(self):
        adv_opts = {}

        # Selected channel
        channels = opts.get_selected_opts(self.advanced_opts['channels'])
        selected_channel = [i for i, v in channels.items() if v][0]
        adv_opts['channel'] = selected_channel

        # Network options
        adv_opts.update(opts.get_selected_opts(self.advanced_opts['network']))

        # Format options
        adv_opts.update(opts.get_selected_opts(self.advanced_opts['format']))

        # Save options
        adv_opts.update(opts.get_selected_opts(self.advanced_opts['save']))

        # Gpg options
        gpg = opts.get_selected_opts(self.advanced_opts['gpg'])
        if gpg['sender']:
            if hasattr(self, '_senders'):
                try:
                    gpg['sender'] = self._senders[gpg['sender']]
                except KeyError:
                    gpg['sender'] = None
        adv_opts.update(gpg)

        return adv_opts


class Listen(qt.QObject):

    sig_listen_logs = qt.Signal(str)

    def __init__(self, sat_api: SatApi):
        super().__init__()
        self.view = ListenView()
        self.sat_api = sat_api

        self.sig_listen_logs.connect(self.view.append_output)
        self.sat_api.sig_listener_state.connect(self.view.set_listener_state)
        self.view.sig_listen_start.connect(self.start)
        self.view.sig_listen_stop.connect(self.stop)
        self.sat_api.sig_gpg_pubkeys.connect(self.view.set_senders)

    def switch_page(self, rx_config_loaded: bool):
        """Switch between the default page and the listen page"""
        self.view.switch_page("listen" if rx_config_loaded else "default")

    def set_network_interfaces(self, rx_config):
        """Set network interfaces"""
        interfaces = util.get_network_interfaces()
        default = config.get_net_if(rx_config)
        self.view.set_network_interfaces(interfaces, default)

    def set_receiver(self, rx_config):
        """Set receiver configuration"""
        if not rx_config:
            self.switch_page(False)
            self.view.update_default_page(False)
            return
        self.set_network_interfaces(rx_config)
        self.switch_page(True)

    def start(self):
        """Start listening to messages"""
        self.view.clear_output()
        opts = self.view.get_advanced_options()
        if self.sat_api.gpg.passphrase is None and (not opts['plaintext'] and
                                                    not opts['no_password']):
            gpg_dialog = AskGPGPassphrase(
                parent=self.view,
                gpg_dir=self.sat_api.config_manager.gpg_dir,
                gpg=self.sat_api.gpg)
            if not gpg_dialog.exec_():
                self.view.sig_listen_stop.emit()
                return
        self.sat_api.listen(output=self.sig_listen_logs, **opts)

    def stop(self):
        """Stop listening thread"""
        self.sig_listen_logs.emit("Stopping...")
        self.sat_api.stop_listener()
