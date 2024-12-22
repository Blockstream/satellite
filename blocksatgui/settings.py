import os

import blocksatcli.config

from . import styles, update, utils
from .components import buttons, gpg, messagebox, optionbox, page
from .config import ConfigManager
from .qt import (QAction, QFormLayout, QFrame, QHBoxLayout, QLabel, QLineEdit,
                 QMenu, QMenuBar, QObject, QPushButton, QSizePolicy, Qt,
                 QTimer, QVBoxLayout, QWidget, Signal, Slot)
from .receiver import dependencies


class SettingsView(QWidget):

    def __init__(self):
        super().__init__()

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(10)
        self._layout.setAlignment(Qt.AlignTop)

        self._add_widgets()
        self.timer = QTimer()

    def _add_widgets(self):
        self.options = optionbox.OptionsBox(self, "Settings")
        self.options.add_widget(self._gen_settings_form())
        self._layout.addWidget(self._gen_settings_bar())
        self._layout.addWidget(self.options)

    def _gen_server_box(self):
        frame = QFrame()
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)

        self.server = QLineEdit()
        self.server_reload = buttons.TextButton('Restore default')
        self.server_reload.setToolTip("Set default server")

        layout.addWidget(self.server)
        layout.addWidget(self.server_reload)

        return frame

    def _gen_config_box(self):
        self.cfg_dir = QLineEdit()
        self.cfg_dir.setDisabled(True)
        self._cfg_dir_bnt = buttons.TextButton("Select Directory")
        frame, layout = page.get_widget('cfg-dir-box', 'frame', 'hbox', False)
        layout.setSpacing(5)
        layout.addWidget(self.cfg_dir, 3)
        layout.addWidget(self._cfg_dir_bnt)
        return frame

    def _gen_gpg_box(self):
        self.gpg_home = QLineEdit()
        self.gpg_home.setDisabled(True)
        self.gpg_home.setToolTip(
            "GPG home directory is relative to the configuration directory.")
        self._gpg_dir_bnt = buttons.TextButton("Select Directory")
        frame, layout = page.get_widget('gpg-home-box', 'frame', 'hbox', False)
        layout.setSpacing(5)
        layout.addWidget(self.gpg_home, 3)
        layout.addWidget(self._gpg_dir_bnt)
        return frame

    def _gen_settings_form(self):
        box = QFrame()
        layout = QFormLayout(box)

        self._satellite_api_url = self._gen_server_box()
        self._cfg_dir_box = self._gen_config_box()
        self._gpg_home_box = self._gen_gpg_box()
        self.message = self._gen_status_message()
        self.save_bnt = QPushButton("Save")

        layout.addRow('Satellite API URL: ', self._satellite_api_url)
        layout.addRow('Configuration directory: ', self._cfg_dir_box)
        layout.addRow('GPG home directory: ', self._gpg_home_box)
        layout.addWidget(self.save_bnt)
        layout.addWidget(self.message)

        return box

    def _gen_settings_bar(self):
        menu_bar = QMenuBar(self)
        menu_bar.setObjectName("settings-bar")
        menu_bar.setNativeMenuBar(False)
        menu_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        # GPG option
        gpg_opt = QMenu("&GPG", self)
        self.new_gpg_bnt = QAction("&Create GPG keyring", self)
        gpg_opt.addAction(self.new_gpg_bnt)

        # View option
        view_opt = QMenu("&View", self)
        self.tray_icon = QAction("&Tray icon", self)
        self.tray_icon.setCheckable(True)
        view_opt.addAction(self.tray_icon)

        # Check updates
        update_opts = QMenu("&Updates", self)
        self.update_bnt = QAction("&Check updates", self)
        self.upgrade_bnt = QAction("&Update dependencies", self)
        update_opts.addAction(self.update_bnt)
        update_opts.addAction(self.upgrade_bnt)

        # Add menus to menu bar
        menu_bar.addMenu(gpg_opt)
        menu_bar.addMenu(view_opt)
        menu_bar.addMenu(update_opts)

        return menu_bar

    def _gen_status_message(self):
        message = QLabel('')
        message.setVisible(False)

        return message

    def show_message(self, message, message_type="info"):
        if message_type == "info":
            self.message.setStyleSheet("color: {};".format(
                styles.colors['blocksat-blue-primary']))
        elif message_type == "error":
            self.message.setStyleSheet("color: {};".format(
                styles.colors['red']))

        self.message.setText(message)
        self.message.setVisible(True)
        self.timer.singleShot(5000, lambda: self.message.setVisible(False))

    def check_tray_icon(self, tray_icon_checked):
        self.tray_icon.setChecked(tray_icon_checked)

    def get_api_server(self):
        return self.server.text()

    def set_api_server(self, api_server):
        self.server.setText(api_server)

    def get_gpg_home(self):
        return self.gpg_home.text()

    def set_gpg_home(self, gpg_home):
        self.gpg_home.setText(gpg_home)

    def get_cfg_dir(self):
        return self.cfg_dir.text()

    def set_cfg_dir(self, cfg_dir):
        self.cfg_dir.setText(cfg_dir)


class Settings(QObject):
    """Settings page for global settings

    Signals:
        sig_toggle_tray_icon: Emitted to change tray icon visibility.

    """

    sig_toggle_tray_icon = Signal(bool)

    def __init__(self, cfg_manager: ConfigManager):
        super().__init__()

        self.cfg_manager = cfg_manager
        self.show_tray_icon = self.cfg_manager.gui_cache.get('view.tray_icon')

        self._cfg_dir = self.cfg_manager.cfg_dir
        self._gpg_home_dir = self.cfg_manager.gpg_home

        self.view = SettingsView()
        self.view.check_tray_icon(bool(self.show_tray_icon))
        self.view.set_cfg_dir(self._cfg_dir)
        self.view.set_gpg_home(self._gpg_home_dir)

        self._add_connections()
        self._load_settings()

    def _add_connections(self):
        self.view.new_gpg_bnt.triggered.connect(self.callback_gpg_new_keypair)
        self.view.tray_icon.triggered.connect(self.callback_toggle_tray_icon)
        self.view.update_bnt.triggered.connect(
            lambda: update.show_available_updates(self.view))
        self.view.upgrade_bnt.triggered.connect(self.upgrade_dependencies)
        self.view.save_bnt.clicked.connect(self._save_settings)
        self.view.server_reload.clicked.connect(
            self.cfg_manager.set_default_api_server)
        self.cfg_manager.sig_api_server.connect(self.view.set_api_server)

        self.view._cfg_dir_bnt.clicked.connect(
            lambda: self._select_directory_dialog('cfg'))
        self.view._gpg_dir_bnt.clicked.connect(
            lambda: self._select_directory_dialog('gpg'))

    def _select_directory_dialog(self, option):
        assert (option in ['cfg', 'gpg'])
        selected_dir = utils.select_file_dialog(
            parent=self.view,
            caption="Select directory",
            selection_mode='dir',
            default_dir=self.cfg_manager.cfg_dir,
            default_dir_only=option == 'gpg')

        if selected_dir:
            if option == 'cfg':
                self._cfg_dir = selected_dir
                self.view.set_cfg_dir(self._cfg_dir)
            else:
                self._gpg_home_dir = os.path.basename(selected_dir)
                self.view.set_gpg_home(self._gpg_home_dir)

    def _load_settings(self):
        self.view.set_api_server(self.cfg_manager.api_server)

    def _save_settings(self):
        # Set API server
        api_server = self.view.get_api_server()
        if not utils.validate_url(api_server):
            self.view.show_message("Invalid server URL!", "error")
            return
        self.cfg_manager.set_api_server(api_server)
        self.cfg_manager.set_cfg_dir(self._cfg_dir)
        self.cfg_manager.set_gpg_home(self._gpg_home_dir)
        self.view.show_message("Saved", "info")

    def upgrade_dependencies(self):
        if not hasattr(self, 'rx_info'):
            messagebox.Message(
                parent=self.view,
                title="Receiver Configuration not found",
                msg_type="warning",
                msg="Please select a receiver configuration file.")
            return

        target = blocksatcli.config.get_rx_label(self.rx_info)
        deps = dependencies.DepsDialog(parent=self.view,
                                       target=target,
                                       command="update")
        deps.exec_()

    def callback_get_receiver_info(self, rx_config):
        self.rx_info = rx_config['info'] if rx_config else None

    @Slot()
    def callback_gpg_new_keypair(self):
        gpg_dialog = gpg.GPGWizard(self.cfg_manager.gpg_dir)
        gpg_dialog.exec_()

    @Slot()
    def callback_toggle_tray_icon(self, checked):
        """Toggle tray icon visibility

        Emit signal to toggle tray icon visibility and save selected option to
        cache.

        """
        self.sig_toggle_tray_icon.emit(checked)
        self.cfg_manager.save_gui_cache('view.tray_icon', checked)
