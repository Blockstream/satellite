from distro import distro

from blocksatcli import defs

from .. import qt, styles
from ..components import buttons, optionbox, page
from .api import SatApi


class SettingsView(page.Page):

    def __init__(self):
        super().__init__(name="satapi-settings", topbar_enabled=False)

        self._layout.setContentsMargins(10, 5, 5, 10)
        self.add_page(self._gen_settings_page(), "settings")
        self.timer = qt.QTimer()

    def _gen_settings_page(self):
        viewer, layout = page.get_widget('settings-tab', align_center=False)
        self.options = optionbox.OptionsBox(self, "Settings")
        self.options.add_widget(self._gen_options())
        layout.addWidget(self.options)
        return viewer

    def _gen_options(self):
        self.btc_network = qt.QComboBox()
        self.btc_network.setPlaceholderText("Select Bitcoin Network")
        self.btc_network.addItems(list(defs.api_server_url.keys()))
        self.btc_network.addItem("None")
        self.btc_network.currentTextChanged.connect(
            self._clear_selected_network)
        save_dir = self._gen_save_dir()

        self.update_bnt = qt.QPushButton("Update")
        self.update_bnt.setFixedHeight(30)
        self._update_msg = qt.QLabel('Saved!')
        self._update_msg.setStyleSheet(
            f"color: {styles.colors['blocksat-blue-primary']}")
        self._update_msg.setVisible(False)
        self.update_bnt.clicked.connect(self._show_update_msg)

        frame, layout = page.get_widget('general-box', 'frame', 'form', False)
        layout.setSpacing(10)
        layout.addRow("Bitcoin Network: ", self.btc_network)
        layout.addRow("Download Directory: ", save_dir)
        layout.addWidget(self.update_bnt)
        layout.addWidget(self._update_msg)
        return frame

    def _gen_save_dir(self):
        self.save_dir = qt.QLineEdit()
        self.save_dir.setDisabled(True)
        self._save_dir_bnt = buttons.TextButton("Select Directory")
        self._save_dir_bnt.clicked.connect(self._select_directory)

        frame, layout = page.get_widget('save-box', 'frame', 'hbox', False)
        layout.setSpacing(5)
        layout.addWidget(self.save_dir, 3)
        layout.addWidget(self._save_dir_bnt)
        return frame

    def _select_directory(self):
        dialog = qt.QFileDialog(parent=self,
                                caption="Select Save Directory",
                                directory=self.get_save_dir() or '')
        dialog.setFileMode(qt.QFileDialog.Directory)
        if qt.PYSIDE_VERSION == "pyside2" and distro.id() == "fedora":
            dialog.setOption(qt.QFileDialog.DontUseNativeDialog, True)
        if dialog.exec_():
            self.save_dir.setText(dialog.selectedFiles()[0])

    def _clear_selected_network(self, network):
        if network == "None":
            self.btc_network.setCurrentIndex(-1)

    def _show_update_msg(self):
        self._update_msg.setVisible(True)
        self.timer.singleShot(2000, lambda: self._update_msg.setVisible(False))

    def set_save_dir(self, save_dir):
        self.save_dir.setText(save_dir)

    def set_bitcoin_net(self, bitcoin_net):
        if bitcoin_net is None:
            self.btc_network.setCurrentIndex(-1)
            return
        self.btc_network.setCurrentText(bitcoin_net)

    def get_save_dir(self):
        return self.save_dir.text() or ''


class Settings(qt.QObject):

    def __init__(self, sat_api: SatApi):
        self.view = SettingsView()
        self.sat_api = sat_api

        self._save_dir = self.sat_api.save_dir
        self._bitcoin_net = self.sat_api.bitcoin_net
        self.view.set_save_dir(self._save_dir)
        self.view.set_bitcoin_net(self._bitcoin_net)

        self.view.save_dir.textChanged.connect(self._update_save_dir)
        self.view.btc_network.currentTextChanged.connect(
            self._update_bitcoin_net)
        self.view.update_bnt.clicked.connect(self.apply_settings)

    def _update_save_dir(self, save_dir):
        """Update local save directory"""
        self._save_dir = save_dir

    def _update_bitcoin_net(self, bitcoin_net):
        """Update local bitcoin network"""
        self._bitcoin_net = bitcoin_net if bitcoin_net != "None" else None

    def apply_settings(self):
        """Apply settings update"""
        self.sat_api.set_save_dir(self._save_dir)
        self.sat_api.set_bitcoin_net(self._bitcoin_net)
