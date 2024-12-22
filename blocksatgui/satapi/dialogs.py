from typing import Optional

from .. import error, qt
from ..components import copy, dialogs, page, stacked
from ..components.dialogs import (BaseDialog, LNInvoiceDialog, gen_error_label,
                                  set_error_message, toggle_error_style)
from ..satapi.api import SatApi


def calc_bid_per_byte(bid: int, payload_size: int) -> float:
    return round(bid / payload_size, 2)


class BidDialog(BaseDialog):

    def __init__(self,
                 gui,
                 suggested_bid: int,
                 payload_size: int,
                 prev_bid: Optional[int] = None):
        super().__init__(gui, title="Transmit Message")
        self.setObjectName("bid-dialog")

        self.suggested_bid = suggested_bid
        self.payload_size = payload_size
        self.prev_bid = prev_bid

        self._add_widgets()
        self._set_suggested_bid()
        self._set_payload_size()
        self._set_bid_per_byte()

        self.ok_bnt.setText("Submit")
        self.ok_bnt.clicked.connect(self._accept)
        self.cancel_bnt.clicked.connect(self.reject)
        self.add_buttons()

        self._bid.textChanged.connect(self._set_bid_per_byte)

    def _add_widgets(self):
        message = qt.QLabel("Enter your {} bid in msat: ".format(
            "updated " if self.prev_bid else ""))

        self._bid = qt.QLineEdit()
        self._bid_error = gen_error_label(self, 10)
        self._top_bid_bnt = qt.QPushButton("Top Bid")
        self._top_bid_bnt.clicked.connect(self._set_suggested_bid)
        bid_box, bid_layout = page.get_widget('bid-box', 'frame', 'hbox',
                                              False)
        bid_layout.setSpacing(2)
        bid_layout.addWidget(self._bid, 3)
        bid_layout.addWidget(self._top_bid_bnt, 1)

        self._payload_size = qt.QLabel()
        self._payload_size.setProperty("qssClass", "text_normal__gray")
        self._msats_per_byte = qt.QLabel()
        self._msats_per_byte.setProperty("qssClass", "text_normal__gray")
        text_box, text_layout = page.get_widget('text-box', 'frame', 'vbox',
                                                False)
        text_layout.setSpacing(1)
        text_layout.addWidget(self._payload_size)
        text_layout.addWidget(self._msats_per_byte)

        self._layout.addWidget(message)
        self._layout.addWidget(bid_box)
        self._layout.addWidget(self._bid_error)
        self._layout.addWidget(text_box)

    def _accept(self):
        if not self._validate_bid():
            return
        self.accept()

    def _set_suggested_bid(self):
        bid = self.suggested_bid if self.prev_bid is None else self.prev_bid
        self._bid.setText(str(bid))

    def _set_bid_per_byte(self):
        total = calc_bid_per_byte(self.get_bid(), self.payload_size)
        self._msats_per_byte.setText(f"{total} msat/byte")

    def _set_payload_size(self):
        self._payload_size.setText(f"Payload size: {self.payload_size} bytes")

    def _validate_bid(self):
        set_error_message(self._bid_error, "")
        toggle_error_style(self._bid, False)

        bid = self.get_bid()
        if bid <= 0:
            set_error_message(self._bid_error, "Bid must be greater than 0")
            toggle_error_style(self._bid, True)
            return False

        if self.prev_bid and bid <= self.prev_bid:
            set_error_message(self._bid_error,
                              "Bid must be greater than previous bid")
            toggle_error_style(self._bid, True)
            return False

        return True

    def get_bid(self):
        bid_str = self._bid.text()
        try:
            bid = int(bid_str)
        except ValueError:
            bid = 0
        return bid


class OrderInfoDialog(BaseDialog):

    def __init__(self, gui, uuid, auth_token):
        super().__init__(gui, title="Transmission Info")
        self.setObjectName("order-info-dialog")

        self.uuid = uuid
        self.auth_token = auth_token

        self.setMinimumWidth(360)
        self._add_widgets()

        self.ok_bnt.clicked.connect(self.accept)
        self.cancel_bnt.clicked.connect(self.reject)
        self.add_buttons()

    def _add_widgets(self):
        message = qt.QLabel(
            "Save this transmission ID and authentication token to delete "
            "or re-prioritize (bump) your transmission in the queue.")
        message.setWordWrap(True)

        self._uuid = copy.CopiableText(text=self.uuid)
        self._uuid.setMaximumHeight(100)
        self._auth_token = copy.CopiableText(text=self.auth_token)
        self._auth_token.setMaximumHeight(100)

        self._layout.addWidget(message)
        self._layout.addWidget(qt.QLabel("Transmission ID: "))
        self._layout.addWidget(self._uuid)
        self._layout.addWidget(qt.QLabel("Authorization Token: "))
        self._layout.addWidget(self._auth_token)


class SelectOrderView(qt.QWidget):

    def __init__(self, gui, tx_id=None, auth_token=None):
        super().__init__(gui)
        self.setObjectName("select-order")
        self._layout = qt.QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._layout.setAlignment(qt.Qt.AlignCenter)
        self._add_widgets(tx_id, auth_token)

    def _add_widgets(self, tx_id, auth_token):
        self.error = gen_error_label(self, 10)
        self.tx_id = qt.QLineEdit(tx_id)
        self.tx_id.setPlaceholderText("Enter transmission ID")
        self._tx_id_error = gen_error_label(self, 10)
        self.auth_token = qt.QLineEdit(auth_token)
        self.auth_token.setPlaceholderText("Enter authorization token")
        self._auth_token_error = gen_error_label(self, 10)

        frame, layout = page.get_widget('select-order', 'frame', 'form', False)
        layout.setSpacing(10)
        layout.addRow("Transmission ID: ", self.tx_id)
        layout.addRow("", self._tx_id_error)
        layout.addRow("Authorization Token: ", self.auth_token)
        layout.addRow("", self._auth_token_error)

        self._layout.addWidget(self.error)
        self._layout.addWidget(frame)

    def get_tx_id(self):
        return self.tx_id.text().strip() or None

    def get_auth_token(self):
        return self.auth_token.text().strip() or None

    def validate_fields(self):
        is_valid = True
        self._tx_id_error.hide()
        self._auth_token_error.hide()

        if not self.get_tx_id():
            self._tx_id_error.setText("Transmission ID is required")
            self._tx_id_error.setVisible(True)
            is_valid = False

        if not self.get_auth_token():
            self._auth_token_error.setText("Authorization token is required")
            self._auth_token_error.setVisible(True)
            is_valid = False

        return is_valid


class ManageOrderView(qt.QWidget):

    def __init__(self, gui, title=None):
        super().__init__(gui)
        self.setObjectName("manage-order")
        self._layout = qt.QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.title = title or "Manage Transmission"
        self.bid = 0
        self.message_size = 0
        self._add_widgets()

    def _add_widgets(self):
        frame, layout = page.get_widget('manage-order', 'frame', 'form', False)
        self.error = gen_error_label(self, 10)
        layout.addWidget(self.error)

        # Order information
        self._uuid = qt.QLabel()
        self._bid = qt.QLabel()
        self._bid_per_byte = qt.QLabel()
        self._message_size = qt.QLabel()
        self._status = qt.QLabel()
        layout.addRow("Transmission ID: ", self._uuid)
        layout.addRow("Bid: ", self._bid)
        layout.addRow("Message size: ", self._message_size)
        layout.addRow("Bid per byte: ", self._bid_per_byte)
        layout.addRow("Status: ", self._status)

        # Action: Bump, Delete or Pay
        self.actions_frame, actions_layout = page.get_widget(
            'actions-frame', 'widget', 'form', False)
        self.action = qt.QComboBox()
        self.action_label = qt.QLabel("Action: ")
        actions_layout.addRow(self.action_label, self.action)
        layout.addRow(self.actions_frame)
        self.actions_frame.setVisible(False)

        # Invoices list
        self.invoice_frame, invoice_layout = page.get_widget(
            'invoice-frame', 'widget', 'form', False)
        self.invoice_label = qt.QLabel("Invoice: ")
        self.invoices = qt.QComboBox()
        invoice_layout.addRow(self.invoice_label, self.invoices)
        layout.addRow(self.invoice_frame)
        self.invoice_frame.setVisible(False)

        self._layout.addWidget(frame)

    def set_order_info(self,
                       uuid,
                       bid,
                       status,
                       message_size,
                       bid_per_byte,
                       actions: list,
                       invoices: Optional[list] = None):
        self.bid = bid
        self.message_size = message_size
        self._uuid.setText(uuid)
        self._bid.setText(f"{bid} msat")
        self._bid_per_byte.setText(f"{bid_per_byte:.2f} msat/byte")
        self._status.setText(status.title())
        self._message_size.setText(f"{message_size} bytes")

        self.actions_frame.setVisible(bool(actions))
        if actions:
            self.action.addItems(actions)
            self.action.setCurrentIndex(0)

        if 'Pay' in actions and invoices:
            items = self._get_invoice_items(invoices)
            self.invoices.addItems(items)
            self.invoices.setCurrentIndex(0)
            self.action.currentTextChanged.connect(self._toggle_invoice_frame)

    def _toggle_invoice_frame(self, action):
        self.invoice_frame.setVisible(action.lower() == 'pay')

    def _get_invoice_items(self, invoices) -> list:
        self.ln_invoices = {}
        for invoice in invoices:
            key = f"LN {invoice['id']} ({invoice['msatoshi']} msat)"
            self.ln_invoices[key] = invoice
        return list(self.ln_invoices.keys())

    def get_selected_invoice(self):
        if not self.ln_invoices:
            return None
        key = self.invoices.currentText()
        return self.ln_invoices.get(key, None)

    def get_action(self):
        return self.action.currentText().lower()

    def get_bid(self):
        return self.bid

    def get_message_size(self):
        return self.message_size


class ManageOrderDialog(BaseDialog):

    def __init__(self,
                 gui,
                 api: SatApi,
                 tx_id: Optional[str] = None,
                 auth_token: Optional[str] = None,
                 ln_invoices: Optional[list] = None):
        super().__init__(gui, title="Manage Transmission")
        self.setObjectName("bump-order-dialog")
        self.resize(qt.QSize(400, 150))

        self.api = api
        self.stage = 'select'
        self.ln_invoices = ln_invoices

        self.stack = stacked.StackedPage()
        self.select_order = SelectOrderView(self,
                                            tx_id=tx_id,
                                            auth_token=auth_token)
        self.manage_order = ManageOrderView(self)
        self.success_page = self._gen_success_page()
        self.stack.add_page(self.select_order)
        self.stack.add_page(self.manage_order)
        self.stack.add_page(self.success_page)
        self._layout.addWidget(self.stack)

        self.ok_bnt.setText("Next")
        self.ok_bnt.clicked.connect(self._next)
        self.cancel_bnt.clicked.connect(self.reject)
        self._layout.addWidget(self.bnt_box)

    def _gen_success_page(self):
        viewer, layout = page.get_widget('success-page', align_center=False)
        message = qt.QLabel("Success")
        message.setWordWrap(True)
        self.success_message = message
        layout.addWidget(message)
        return viewer

    def _toggle_bnt_style(self, waiting, text=None):
        if waiting:
            self.ok_bnt.setText(text or "Submitting...")
            self.ok_bnt.setEnabled(False)
        else:
            self.ok_bnt.setText(text or "Next")
            self.ok_bnt.setEnabled(True)

    def _set_success_style(self, action):
        assert action in ['delete', 'bump']
        tx_id = self.select_order.get_tx_id()
        if action == 'delete':
            message = f"Transmission {tx_id} deleted successfully!"
        else:
            message = f"Transmission {tx_id} bumped successfully!"
        self.success_message.setText(message)

    def _next(self):
        if self.stage == 'select':
            if not self.select_order.validate_fields():
                return
            self._toggle_bnt_style(waiting=True)
            self.api.get_order(self.select_order.get_tx_id(),
                               self.select_order.get_auth_token(),
                               self._cb_get_order)
        elif self.stage == 'manage':
            action = self.manage_order.get_action()
            if action == 'delete':
                # Delete order
                self._toggle_bnt_style(waiting=True)
                self.api.delete_order(self.select_order.get_tx_id(),
                                      self.select_order.get_auth_token(),
                                      self._cb_delete_order)
                return
            elif action == 'pay':
                # Get selected lightning invoice
                invoice = self.manage_order.get_selected_invoice()
                # Show lightning invoice
                ln_dialog = dialogs.LNInvoiceDialog(gui=self, invoice=invoice)
                ln_dialog.exec_()
                return
            else:
                # Bump order
                bid_dialog = BidDialog(
                    gui=self,
                    suggested_bid=self.manage_order.get_bid(),
                    payload_size=self.manage_order.get_message_size(),
                    prev_bid=self.manage_order.get_bid())
                if not bid_dialog.exec_():
                    return
                self._toggle_bnt_style(waiting=True)
                self.api.bump_order(
                    bid=bid_dialog.get_bid(),
                    uuid=self.select_order.get_tx_id(),
                    auth_token=self.select_order.get_auth_token(),
                    callback=self._cb_bump_order)
        elif self.stage == 'success':
            self.accept()  # Close dialog

    def _set_stage(self, stage):
        assert stage in ['select', 'manage', 'success']
        self.stage = stage
        if stage == 'select':
            page = self.select_order
        elif stage == 'manage':
            page = self.manage_order
        else:
            page = self.success_page
        self.stack.set_active_page(page)

    def _cb_get_order(self, worker):
        """Callback for getting order info"""
        if worker.error is not None:
            self.select_order.error.setText("Error getting order info")
            return

        # Update order info at the manage order page before switching
        bid = worker.result['bid'] + worker.result['unpaid_bid']
        msg_size = self.api.calc_ota_msg_len(worker.result['message_size'])
        order_status = worker.result['status'].lower()
        unmanageable_states = ['sent', 'received', 'cancelled', 'expired']

        # Set the allowed actions
        actions = ['Bump', 'Delete']
        if order_status == 'pending' and self.ln_invoices:
            actions.append('Pay')
        elif order_status in unmanageable_states:
            actions = []

        self.manage_order.set_order_info(
            uuid=worker.result['uuid'],
            bid=bid,
            status=worker.result['status'],
            message_size=msg_size,
            bid_per_byte=worker.result['bid_per_byte'],
            actions=actions,
            invoices=self.ln_invoices)
        self._toggle_bnt_style(waiting=False)

        if order_status in unmanageable_states:
            self.ok_bnt.setDisabled(True)
            self.cancel_bnt.setText("Close")

        self._set_stage('manage')

    def _cb_delete_order(self, worker):
        """Callback for deleting order"""
        if worker.error is not None:
            err_type, err = error.parse_api_error(worker.error)
            message = ""
            if err_type == "error":
                message = err['detail']
            elif err_type == 'other':
                message = err
            else:
                message = worker.error.traceback
            self.manage_order.error.setText(message)
            return

        self._set_success_style(action="delete")
        self._toggle_bnt_style(waiting=False)
        self._set_stage('success')

    def _cb_bump_order(self, worker):
        """Callback for bumping order"""
        if worker.error is not None:
            err_type, err = error.parse_api_error(worker.error)
            message = ""
            if err_type == "error":
                message = err['detail']
            elif err_type == 'other':
                message = err
            else:
                message = worker.error.traceback
            self.manage_order.error.setText(message)
            return

        # Show lightning invoice
        invoice = worker.result['lightning_invoice']
        ln_dialog = LNInvoiceDialog(gui=self, invoice=invoice)
        ln_dialog.exec_()

        self._set_success_style(action="bump")
        self._toggle_bnt_style(waiting=False, text="Ok")
        self._set_stage('success')
