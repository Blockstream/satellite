"""Dialog windows"""
import tempfile

import qrcode
import qrcode.image.svg

from blocksatcli import util

from .. import styles, utils
from ..components import copy
from ..qt import (QDialog, QDialogButtonBox, QFrame, QHBoxLayout, QLabel,
                  QPlainTextEdit, QProgressBar, QSize, QSizePolicy, Qt,
                  QVBoxLayout, Signal, Slot)

buttons_map = {
    'ok': QDialogButtonBox.Ok,
    'cancel': QDialogButtonBox.Cancel,
    'close': QDialogButtonBox.Close
}


def set_wait_response_style_button(button):
    """Set wait style for button"""
    button.setText("Sending...")
    button.setDisabled(True)


def gen_error_label(parent=None, font_size=None):
    """Generate a QLabel to display error messages"""
    error = QLabel(parent=parent)
    style = f"color: {styles.colors['red']};"
    if font_size:
        style += f" font-size: {font_size}px;"
    error.setStyleSheet(style)
    error.setHidden(True)
    return error


def set_error_message(error_component, text):
    """Set message and show the error component

    Args:
        error_component: Error component.
        text: Error message.

    """
    error_component.setText(text)
    error_component.setHidden(not bool(text))


def toggle_error_style(input_component, error=False):
    """Toggle error style for input component

    Args:
        input_component: Input component.
        error: Whether to show the error style.

    """
    style = (styles.border_style['error']
             if error else styles.border_style['normal'])

    input_component.setStyleSheet(style)


class BaseDialog(QDialog):

    def __init__(self, parent, title):
        super().__init__(parent)

        self.setObjectName("base-dialog")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(20, 10, 20, 10)
        self._layout.setSpacing(10)

        # Title
        self.title = QLabel(title)
        self.title.setProperty("qssClass", "title")
        self.title.setAlignment(Qt.AlignCenter)
        self._layout.addWidget(self.title)

        # Standard buttons
        self.bnt_box = QDialogButtonBox()
        self.bnt_box.setStandardButtons(QDialogButtonBox.Ok
                                        | QDialogButtonBox.Cancel)
        self.ok_bnt = self.bnt_box.button(QDialogButtonBox.Ok)
        self.cancel_bnt = self.bnt_box.button(QDialogButtonBox.Cancel)

    def add_buttons(self):
        self._layout.addWidget(self.bnt_box)


class GenericDialog(QDialog):

    def __init__(self,
                 parent,
                 title,
                 message,
                 button='close',
                 progress_bar=True,
                 status_box=True):
        """
        Args:
            parent: Parent window.
            title: Dialog window title.
            message: Fixed message to display on the dialog window.
            progress_bar: Whether to enable a progress bar.
            status_box: Whether to disable a status box.

        """
        super().__init__(parent)

        self.setMinimumWidth(600)
        self.vbox = QVBoxLayout(self)
        self.vbox.setContentsMargins(25, 25, 25, 25)

        self.accepted = False
        self.canceled = False
        self.running = False

        self.title_label = QLabel(title.upper())
        self.title_label.setProperty("qssClass", "dialog__title")
        self.title_label.setFixedHeight(40)
        self.vbox.addWidget(self.title_label)

        self.message_label = QLabel(message)
        self.message_label.setWordWrap(True)
        self.message_label.setSizePolicy(
            QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum))
        self.message_label.setWordWrap(True)
        self.message_label.adjustSize()
        self.vbox.addWidget(self.message_label)

        if status_box:
            self.status_box = QPlainTextEdit(self)
            self.status_box.setProperty("qssClass", "dialog__status")
            self.status_box.setReadOnly(True)
            self.vbox.addWidget(self.status_box)

        if progress_bar:
            self.progress_bar = QProgressBar(self)
            self.progress_bar.setRange(0, 1)
            self.vbox.addWidget(self.progress_bar)

        if button in buttons_map:
            self.bnt = QDialogButtonBox()
            self.bnt.setStandardButtons(buttons_map[button])
            self.vbox.addWidget(self.bnt)

        self.adjustSize()

    def closeEvent(self, event):
        self.canceled = True

        if self.running:
            event.ignore()
        else:
            event.accept()

    def _style_error_line(self, pattern, message):
        lines = message.splitlines()
        for i, line in enumerate(lines):
            if pattern in line:
                error_line = f"<p style = 'color: red'>{line}</p>"
                lines[i] = error_line
        return "".join(lines)

    @Slot()
    def append_status_message(self, status):
        if not isinstance(status, str):
            return

        status = status.strip()
        if "ERROR" in status:
            status = self._style_error_line(pattern="ERROR", message=status)
            self.status_box.appendHtml(status)
        else:
            self.status_box.appendPlainText(status)

        self.status_box.centerCursor()
        self.status_box.repaint()

    def clean_status_box(self):
        self.status_box.setPlainText("")
        self.toggle_status_style(error=False)

    def connect_status_signal(self, signal):
        signal.connect(self.append_status_message)

    def toggle_close_event(self, status):
        self.running = status

    def toggle_status_style(self, error=False):
        if not error:
            self.status_box.setStyleSheet("color: #358de5")
        else:
            self.status_box.setStyleSheet("color: red")

    def toggle_progress_bar(self, running):
        """Change the style from the progress bar"""
        if running:
            self.progress_bar.setRange(0, 0)
        else:
            self.progress_bar.setRange(0, 1)

    def toggle_button(self, visible):
        self.bnt.setVisible(visible)

    def enable_button(self, enable):
        self.bnt.setEnabled(enable)

    def set_button_name(self, button, new_name):
        if button in buttons_map:
            select_bnt = buttons_map[button]
            self.bnt.button(select_bnt).setText(new_name)

    def set_message_text(self, msg):
        self.message_label.setText(msg)
        self.adjustSize()

    def set_title_text(self, title):
        self.title_label.setText(title.upper())


class LNInvoiceDialog(QDialog):

    sig_wait_payment = Signal()
    sig_stop_wait_payment = Signal()

    def __init__(self, gui, invoice):
        super().__init__(gui)

        self.due_amount = invoice['msatoshi']
        self.payreq = invoice['payreq']
        self.id = invoice['id']

        self.resize(QSize(750, 400))
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(20, 20, 20, 20)

        self.bnt = QDialogButtonBox()
        self.bnt.setStandardButtons(QDialogButtonBox.Close)

        self._layout.addWidget(self._gen_invoice_page())
        self._layout.addWidget(self.bnt)

        self.bnt.button(QDialogButtonBox.Close).clicked.connect(self._reject)

    def _gen_invoice_page(self):
        """Generate invoice page with QR code"""

        title = QLabel("Pay Lightning Invoice")
        title.setProperty("qssClass", "title")

        amount = QLabel("Due amount: {}".format(
            util.format_sats(int(self.due_amount) / 1e3)))

        invoice_msg = copy.CopiableText(text=self.payreq)
        invoice_msg.text_widget.setObjectName("invoice-message")

        # Save the QR code as a SVG image in a temporary file
        qr = qrcode.QRCode()
        qr.add_data(self.payreq)
        qr_svg = qr.make_image(image_factory=qrcode.image.svg.SvgPathImage)
        temp_svg = tempfile.NamedTemporaryFile(delete=False)
        qr_svg.save(temp_svg.name)

        qr_widget = utils.get_svg_widget(temp_svg.name)
        qr_widget.setObjectName("invoice-qr")

        # Right side
        wrapper_r = QFrame(self)
        layout_r = QVBoxLayout(wrapper_r)
        layout_r.addWidget(title)
        layout_r.addWidget(amount)
        layout_r.addWidget(invoice_msg)

        # Left side
        wrapper_l = QFrame(self)
        wrapper_l.setMinimumWidth(200)
        layout_l = QVBoxLayout(wrapper_l)
        layout_l.addWidget(qr_widget)

        box = QFrame(self)
        box_layout = QHBoxLayout(box)
        box_layout.addWidget(wrapper_r)
        box_layout.addWidget(wrapper_l)

        return box

    def exec_(self):
        self.sig_wait_payment.emit()
        super().exec_()

    def _reject(self):
        self.sig_stop_wait_payment.emit()
        self.reject()

    def closeEvent(self, event):
        self.sig_stop_wait_payment.emit()
        event.accept()
