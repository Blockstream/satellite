import logging

import distro

from .. import qt
from ..components import buttons, dialogs, messagebox, page
from ..components.gpg import AskGPGPassphrase
from ..error import show_error_message
from . import api, opts
from .dialogs import BidDialog, OrderInfoDialog

logger = logging.getLogger(__name__)


class SendView(page.Page):

    sig_file_selected = qt.Signal(object)

    def __init__(self):
        super().__init__(name="satapi-send", topbar_enabled=False)

        self._layout.setContentsMargins(10, 5, 5, 10)
        self.advanced_opts = opts.get_send_opts()
        self.default_page = self._gen_default_page()
        self.send_page = self._gen_send_page()
        self.add_page(self.default_page, "default")
        self.add_page(self.send_page, "send")
        self.update_default_page()
        self.switch_page("default")

        self.sig_file_selected.connect(
            lambda x: self._set_file_selected_style(bool(x)))

    def _gen_default_page(self):
        self._message = qt.QLabel("")
        self._message.setProperty("qssClass", "text_bold__gray")
        self._details = qt.QLabel("")
        self._details.setProperty("qssClass", "text_italic__gray")

        viewer, layout = page.get_widget('default-tab')
        layout.addWidget(self._message, alignment=qt.Qt.AlignCenter)
        layout.addWidget(self._details, alignment=qt.Qt.AlignCenter)
        return viewer

    def _gen_send_page(self):
        self.message_or_file = self._add_message_or_file()
        self.send_options = self._add_send_options()
        self.send_bnt = buttons.MainButton("Send")

        viewer, layout = page.get_widget('send-tab')
        layout.addWidget(self.message_or_file, 1)
        layout.addWidget(self.send_options, 1)
        layout.addWidget(self.send_bnt, alignment=qt.Qt.AlignCenter)
        return viewer

    def _add_message_or_file(self):
        self.message = qt.QPlainTextEdit()
        self.message.setObjectName("satapi-message")
        self._set_file_selected_style()
        self.upload_file_box = self._upload_file_box()

        viewer, layout = page.get_widget('send-tab', 'frame')
        layout.setSpacing(5)
        title = qt.QLabel("Send a message or file".upper())
        title.setProperty("qssClass", "metric-card__title")
        layout.addWidget(title)
        layout.addWidget(self.message)
        layout.addWidget(self.upload_file_box)
        return viewer

    def _upload_file_box(self):
        self.upload_file_btn = qt.QPushButton("Select file")
        self.upload_file_btn.setMaximumWidth(200)
        self.upload_file_btn.clicked.connect(self._select_file)
        self.sig_file_selected.connect(
            lambda x: self._toggle_upload_file(not bool(x)))

        self.file_selected = qt.QLabel("No file selected")
        self.sig_file_selected.connect(self._display_selected_file)

        self.remove_file_btn = buttons.TextButton("Remove")
        self.remove_file_btn.setHidden(True)
        self.sig_file_selected.connect(
            lambda x: self._toggle_remove_selected_file_bnt(bool(x)))
        self.remove_file_btn.clicked.connect(self._remove_selected_file)

        viewer, layout = page.get_widget('upload-file-box', 'frame', 'form')
        layout.addRow("Choose a file: ", self.upload_file_btn)
        layout.addRow('', self.file_selected)
        layout.addRow('', self.remove_file_btn)
        return viewer

    def _add_send_options(self):
        self.show_advanced_options = buttons.TextButton(
            "Show Advanced Options ►")
        self.show_advanced_options.setFixedHeight(30)

        self.advanced_options_box = qt.QGroupBox(self)
        self._layout_advanced_options = qt.QVBoxLayout(
            self.advanced_options_box)
        self.show_advanced_options.clicked.connect(
            self._toggle_advanced_options)

        # Add regions
        regions_box = opts.get_group_box(parent=self,
                                         name="Select Regions",
                                         opts=self.advanced_opts['regions'],
                                         layout='hbox')
        self._layout_advanced_options.addWidget(regions_box)

        # Add GPG options
        gpg_box = opts.get_group_box(parent=self,
                                     name="GPG Options",
                                     opts=self.advanced_opts['gpg'],
                                     inline_label=False)
        self._layout_advanced_options.addWidget(gpg_box)

        # Add format options
        format_box = opts.get_group_box(parent=self,
                                        name="Format Options",
                                        opts=self.advanced_opts['format'],
                                        inline_label=False)
        self._layout_advanced_options.addWidget(format_box)

        self.advanced_options_box.setHidden(True)
        viewer, layout = page.get_widget('send-options',
                                         'frame',
                                         align_center=False)
        layout.addWidget(self.show_advanced_options, alignment=qt.Qt.AlignTop)
        layout.addWidget(self.advanced_options_box, 1)
        return viewer

    def _select_file(self):
        dialog = qt.QFileDialog(parent=self, caption="Select a file")
        if qt.PYSIDE_VERSION == "pyside2" and distro.id() == "fedora":
            dialog.setOption(qt.QFileDialog.DontUseNativeDialog, True)
        if dialog.exec_():
            file_path = dialog.selectedFiles()[0]
            self.selected_file = file_path
            self.sig_file_selected.emit(file_path)

    def _remove_selected_file(self):
        self.selected_file = None
        self.sig_file_selected.emit(None)

    def _toggle_remove_selected_file_bnt(self, visible):
        self.remove_file_btn.setHidden(not visible)

    def _toggle_upload_file(self, enable):
        self.upload_file_btn.setEnabled(enable)

    def _toggle_advanced_options(self):
        show = True if self.advanced_options_box.isHidden() else False
        text = "Hide Advanced Options ▼" if show else "Show Advanced Options ►"
        self.show_advanced_options.setText(text)
        self.advanced_options_box.setHidden(not show)

    def _display_selected_file(self, file_path):
        if file_path is None:
            self.file_selected.setText("No file selected")
        else:
            self.file_selected.setText(file_path)

    def _set_file_selected_style(self, file_selected=False):
        if file_selected:
            self.message.setEnabled(False)
            self.message.setPlainText("")
            self.message.setPlaceholderText(
                "File selected. Message is disabled.")
        else:
            self.message.setEnabled(True)
            self.message.setPlaceholderText(
                "Enter your message here or select a file using the "
                "button below.")

    def get_message(self):
        return self.message.toPlainText() or None

    def get_file(self):
        text = self.file_selected.text()
        return text if text != "No file selected" else None

    def set_recipients(self, recipients):
        self._recipients = {}
        widget = self.advanced_opts['gpg']['recipient']['widget']
        widget.clear()
        for i, r in enumerate(recipients):
            text = f"{r['uids']} ({r['fingerprint']})"
            widget.insertItem(i, text)
            self._recipients[text] = r['fingerprint']

    def set_sign_keys(self, keys):
        self._sign_keys = {}
        widget = self.advanced_opts['gpg']['sign_key']['widget']
        widget.clear()
        for i, k in enumerate(keys):
            text = f"{k['uids']} ({k['fingerprint']})"
            widget.insertItem(i, text)
            self._sign_keys[text] = k['fingerprint']

    def update_default_page(self, on_internet=False, api_valid=False):
        message, details = "", ""
        if on_internet:
            if not api_valid:
                message = "Invalid API"
                details = "Please, enter a valid API URL to send messages"
        else:
            message = "Offline Mode"
            details = "Cannot send messages"

        self._message.setText(message)
        self._details.setText(details)

    def clear_data(self):
        if self.get_file():
            self._remove_selected_file()
        else:
            self.message.clear()

    def get_advanced_opts(self):
        adv_opts = {}

        # Selected regions
        regions = opts.get_selected_opts(self.advanced_opts['regions'])
        selected_regions = [r for r, v in regions.items() if v]
        adv_opts['regions'] = selected_regions

        # Selected GPG options
        gpg = opts.get_selected_opts(self.advanced_opts['gpg'])
        if gpg['recipient']:
            if hasattr(self, '_recipients'):
                try:
                    gpg['recipient'] = self._recipients[gpg['recipient']]
                except KeyError:
                    gpg['recipient'] = None

        if gpg['sign_key']:
            if hasattr(self, '_sign_keys'):
                try:
                    gpg['sign_key'] = self._sign_keys[gpg['sign_key']]
                except KeyError:
                    gpg['sign_key'] = None
        adv_opts.update(gpg)

        # Selected format options
        adv_opts.update(opts.get_selected_opts(self.advanced_opts['format']))

        return adv_opts


class Send(qt.QObject):

    sig_gpg_pubkeys = qt.Signal(list)
    sig_gpg_privkeys = qt.Signal(list)

    def __init__(self, sat_api: api.SatApi):
        super().__init__()

        self.view = SendView()
        self.sat_api = sat_api

        self._add_connections()
        self._get_gpg_keylist()

    def _add_connections(self):
        self.view.send_bnt.clicked.connect(self.send_message)
        self.sat_api.sig_gpg_pubkeys.connect(self.view.set_recipients)
        self.sat_api.sig_gpg_privkeys.connect(self.view.set_sign_keys)
        self.sat_api.config_manager.sig_is_api_server_valid.connect(
            lambda: self._update_default_page())
        self.sat_api.config_manager.sig_on_internet.connect(
            lambda: self._update_default_page())

    def _get_gpg_keylist(self):
        """Get public and private keys from GPG"""
        for private in [True, False]:
            self.sat_api.get_gpg_keylist(private)

    def _update_default_page(self):
        """Update content of the default page"""
        enable_default_page = (not self.sat_api.config_manager.on_internet
                               or not self.sat_api.config_manager.api_valid)
        self.view.update_default_page(
            on_internet=self.sat_api.config_manager.on_internet,
            api_valid=self.sat_api.config_manager.api_valid)
        self.view.switch_page("default" if enable_default_page else "send")

    def send_message(self):
        is_file = bool(self.view.get_file())
        data = self.view.get_file() if is_file else self.view.get_message()

        if not data:
            # No data to send
            messagebox.Message(parent=self.view,
                               title="No data to send",
                               msg="Please, enter a message or select a file.",
                               msg_type="info")
            return

        opts = self.view.get_advanced_opts()
        if self.sat_api.gpg.passphrase is None and opts['sign'] and (
                not opts['no_password']):
            gpg_dialog = AskGPGPassphrase(
                parent=self.view,
                gpg_dir=self.sat_api.config_manager.gpg_dir,
                gpg=self.sat_api.gpg)
            if not gpg_dialog.exec_():
                return

        if not self.sat_api.has_gpg_pubkey() and not opts['plaintext']:
            messagebox.Message(parent=self.view,
                               title="No GPG keyring found",
                               msg="Please, create a GPG keyring to send "
                               "encrypted messages or use plain text mode."
                               "\n\nYou can create a GPG keyring in the "
                               "Settings page > GPG Options tab.",
                               msg_type="critical")
            return

        data_size = self.sat_api.calc_tx_size(data,
                                              is_file,
                                              **opts,
                                              gpg=self.sat_api.gpg)
        suggested_bid = self.sat_api.suggest_bid(data_size)
        bid_dialog = BidDialog(gui=self.view,
                               suggested_bid=suggested_bid,
                               payload_size=data_size)
        if not bid_dialog.exec_():
            return  # User cancelled
        bid = bid_dialog.get_bid()

        def _callback(self, worker):
            if worker.error is not None:
                show_error_message(parent=self.view,
                                   title="Error",
                                   error=worker.error)
                return

            self.view.clear_data()

            # Show the transaction ID and authorization token
            uuid = worker.result['uuid']
            token = worker.result['auth_token']
            info = OrderInfoDialog(gui=self.view, uuid=uuid, auth_token=token)
            info.exec_()

            def _wait_tx_payment(api, uuid, token, dialog):
                """Wait for invoice payment and then close the dialog"""

                def _on_payment_confirmed(worker):
                    if worker.error is None and worker.result:
                        dialog.accept()

                api.wait_tx_payment(uuid,
                                    token,
                                    callback=_on_payment_confirmed)

            # Show lightning invoice
            invoice = worker.result['lightning_invoice']
            ln_dialog = dialogs.LNInvoiceDialog(gui=self.view, invoice=invoice)
            ln_dialog.sig_wait_payment.connect(
                lambda: _wait_tx_payment(self.sat_api, uuid, token, ln_dialog))
            ln_dialog.sig_stop_wait_payment.connect(
                self.sat_api.sig_stop_wait_tx_payment.emit)
            ln_dialog.exec_()

        self.sat_api.send(data=data,
                          is_file=is_file,
                          bid=bid,
                          callback=lambda worker: _callback(self, worker),
                          **opts)
