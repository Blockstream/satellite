from email.utils import parseaddr
from typing import Optional

from blocksatcli.api.gpg import Gpg, import_bs_pubkey, is_gpg_keyring_set

from ..components import messagebox
from ..qt import (QDialog, QDialogButtonBox, QFormLayout, QFrame, QLabel,
                  QLineEdit, Qt, QVBoxLayout, QWizard, Slot)
from .defaultwizard import DefaultWizardPage


class GPGWizard(QWizard):
    """Wizard for creating a GPG keyring"""

    def __init__(self, gpg_dir):
        super().__init__()

        # Wizard settings
        self.setFixedSize(640, 400)
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setOptions(QWizard.NoBackButtonOnLastPage)
        self.setWindowTitle("GPG Keyring")

        gpg_page = GPGInfoPage(self,
                               gpg_dir,
                               title="GPG Keyring",
                               subtitle="Create GPG Keyring",
                               individual_page=True)
        self.addPage(gpg_page)

        self.currentIdChanged.connect(self.callback_disable_buttons)

    def callback_disable_buttons(self):
        self.button(QWizard.NextButton).setVisible(False)
        self.button(QWizard.BackButton).setVisible(False)


class GPGInfoPage(DefaultWizardPage):

    def __init__(self,
                 wizard,
                 gpg_dir,
                 title,
                 subtitle,
                 individual_page=False):
        super().__init__(wizard, title, subtitle, watermark=None)

        self.wizard = wizard
        self.gpg = Gpg(gpg_dir)
        self.gpg_dir = gpg_dir
        self.individual_page = individual_page

        if individual_page:
            self.setFinalPage(True)

    def initializePage(self):
        super().initializePage()

        self.is_gpg_set = is_gpg_keyring_set(self.gpg_dir)

        if self.is_gpg_set:
            self._gpg_already_created_page()
        else:
            self._gpg_creation_key_page()

    def validate_inputs(self):
        if self.is_gpg_set:
            return True

        name = self.name.text()
        valid_name = name != ""

        email = self.email.text()
        valid_email = parseaddr(email)[1] != ""

        comment = self.comment.text()

        passphrase = self.passphrase.text()
        valid_passphrase = passphrase != ""

        self._display_error_message(condition=valid_name,
                                    input_comp=self.name,
                                    error_comp=self.error,
                                    error_msg="Invalid field")
        self._display_error_message(condition=valid_email,
                                    input_comp=self.email,
                                    error_comp=self.error,
                                    error_msg="Invalid field")
        self._display_error_message(condition=valid_passphrase,
                                    input_comp=self.passphrase,
                                    error_comp=self.error,
                                    error_msg="Invalid field")

        valid = all([valid_name, valid_email, valid_passphrase])

        if valid:
            self.group.setDisabled(True)
            self._create_keys(name, email, comment, passphrase)
            self.wizard.gpg_passphrase = passphrase

        return valid

    def _gpg_creation_key_page(self):
        gpg_info = QFrame(self)
        gpg_info.setObjectName("gpg_info_box")

        layout = QFormLayout(gpg_info)

        self.name = QLineEdit()
        self.email = QLineEdit()
        self.comment = QLineEdit()
        self.passphrase = QLineEdit()
        self.passphrase.setEchoMode(QLineEdit.Password)

        layout.addRow("Name:", self.name)
        layout.addRow("Email:", self.email)
        layout.addRow("Comment (optional):", self.comment)
        layout.addRow("Passphrase:", self.passphrase)
        layout.setVerticalSpacing(10)

        self.error = self.add_error_component("gpg_error")

        self.group_layout.addWidget(gpg_info)
        self.group_layout.addWidget(self.error)

    def _gpg_already_created_page(self):
        gpg_info = QFrame(self)
        layout = QFormLayout(gpg_info)

        key_info = self.gpg.get_default_public_key()
        uids = str(key_info['uids'][0])
        fingerprint = str(key_info['fingerprint'])

        msg = ("\nGPG keypair already created. No further action needed.")

        layout.addRow(QLabel("GPG Information:"))
        layout.addRow("Uids: ", QLabel(uids))
        layout.addRow("Fingerprint: ", QLabel(fingerprint))
        layout.addRow(QLabel(msg))

        self.group_layout.addWidget(gpg_info)

    def _create_keys(self, name, email, comment, passphrase):
        self.gpg.create_keys(name, email, comment, passphrase)
        import_bs_pubkey(self.gpg)


class AskGPGPassphrase(QDialog):
    """Dialog component to get GPG passphrase"""

    def __init__(self, parent, gpg_dir, gpg: Optional[Gpg] = None):
        super().__init__(parent)

        self.parent = parent
        if gpg is None:
            gpg = Gpg(gpg_dir, interactive=False)
        self.gpg = gpg

        self._add_widgets()

    def _add_widgets(self):
        self.setFixedSize(380, 200)
        vbox = QVBoxLayout(self)
        vbox.setAlignment(Qt.AlignCenter)
        vbox.setContentsMargins(25, 25, 25, 0)
        vbox.setSpacing(8)

        # Components
        self.bnt = QDialogButtonBox()
        self.bnt.setStandardButtons(QDialogButtonBox.Ok
                                    | QDialogButtonBox.Cancel)
        title = QLabel("Passphrase:")
        msg = QLabel("Please enter the passphrase to your GPG key")
        msg.setWordWrap(True)
        self.gpg_passphrase = QLineEdit()
        self.gpg_passphrase.setObjectName('password')
        self.gpg_passphrase.setEchoMode(QLineEdit.Password)
        self.gpg_passphrase.setAlignment(Qt.AlignBottom)

        self.error = QLabel()
        self.error.setAlignment(Qt.AlignBottom | Qt.AlignHCenter)
        self.error.setStyleSheet("color: red")
        self.error.setVisible(False)

        # Add to layout
        vbox.addWidget(title)
        vbox.addWidget(msg)
        vbox.addWidget(self.gpg_passphrase)
        vbox.addWidget(self.error)
        vbox.addWidget(self.bnt)

        # Connect signals
        self.bnt.accepted.connect(self._accept)
        self.bnt.rejected.connect(self._reject)

    def get_passphrase(self):
        passphrase = self.gpg_passphrase.text()
        return passphrase if passphrase != "" else None

    def display_error(self):
        self.error.setText("Passphrase is not correct. Please try again.")
        self.error.setVisible(True)

    @Slot()
    def _accept(self):
        self.error.setVisible(False)
        self.bnt.setDisabled(True)
        self.gpg_passphrase.setDisabled(True)

        priv_key = self.gpg.get_default_priv_key()
        if priv_key is None:
            messagebox.Message(
                parent=self.parent,
                title="GPG Error",
                msg="No GPG keypair found. Please create a GPG keypair.",
                msg_type="critical")
            self._reject()
            return

        fingerprint = priv_key['fingerprint']
        self.gpg.passphrase = self.get_passphrase()

        if not self.gpg.test_passphrase(fingerprint):
            self.display_error()
            self.gpg_passphrase.setDisabled(False)
            self.bnt.setDisabled(False)
            self.gpg_passphrase.clear()
            self.gpg_passphrase.setFocus()
            return

        self.accept()

    @Slot()
    def _reject(self):
        self.gpg_passphrase.clear()
        self.reject()

    def closeEvent(self, event):
        return self._reject()
