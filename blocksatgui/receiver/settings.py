import os

from blocksatcli import bitcoin, config

from .. import qt, utils
from ..components import messagebox, page
from ..config import ConfigManager
from . import configwizard, dependencies


class SettingsView(qt.QWidget):

    def __init__(self):
        super().__init__()

        self._layout = qt.QVBoxLayout(self)
        self.settings_bar = self._gen_settings_bar()
        self.content_page = page.Page(name="receiver-settings",
                                      topbar_enabled=False)
        self.content_page.add_page(self._gen_default_page(), "default")
        self.content_page.add_page(self._gen_settings_page(), "settings")
        self._layout.addWidget(self.settings_bar)
        self._layout.addWidget(self.content_page)

    def _gen_settings_bar(self):
        """Create settings menu bar"""
        menu_bar = qt.QMenuBar(self)
        menu_bar.setObjectName("settings-bar")
        menu_bar.setNativeMenuBar(False)
        menu_bar.setSizePolicy(qt.QSizePolicy.Expanding,
                               qt.QSizePolicy.Minimum)

        # Receiver option
        receiver_opt = qt.QMenu("&Configuration", self)
        receiver_opt.setObjectName("settings-bar__menu")
        self.new_cfg_bnt = qt.QAction("&Create", self)
        self.load_cfg_bnt = qt.QAction("&Load", self)
        receiver_opt.addAction(self.new_cfg_bnt)
        receiver_opt.addAction(self.load_cfg_bnt)

        # Bitcoin option
        bitcoin_opt = qt.QMenu("&Bitcoin", self)
        self.bitcoin_config_bnt = qt.QAction("&Create configuration file",
                                             self)
        self.bitcoin_install_bnt = qt.QAction("&Install Bitcoin Satellite",
                                              self)
        bitcoin_opt.addAction(self.bitcoin_config_bnt)
        bitcoin_opt.addAction(self.bitcoin_install_bnt)

        # Add options to the menu bar
        menu_bar.addMenu(receiver_opt)
        menu_bar.addMenu(bitcoin_opt)

        return menu_bar

    def _gen_default_page(self):
        """Generate default widgets to settings page"""
        rx_config = qt.QLabel("Configuration not found")
        rx_config.setFixedHeight(80)
        self.create_rx_bnt = qt.QPushButton("Create Receiver Configuration")
        self.create_rx_bnt.setFixedSize(300, 50)
        frame, layout = page.get_widget('default-tab')
        frame.setSizePolicy(qt.QSizePolicy.Expanding, qt.QSizePolicy.Expanding)
        layout.addWidget(rx_config, alignment=qt.Qt.AlignHCenter)
        layout.addWidget(self.create_rx_bnt)
        return frame

    def _gen_settings_page(self, info=None):
        frame, layout = page.get_widget('settings-tab', align_center=False)
        layout.setAlignment(qt.Qt.AlignTop)

        if info is None:
            return frame

        cfgs = config.get_readable_cfg(info)
        for category in cfgs:
            title = qt.QLabel(category.upper())
            title.setMinimumHeight(30)
            title.setProperty("qssClass", "settings-box__title")
            title.adjustSize()

            box = qt.QFrame()
            box.setProperty("qssClass", "settings-box")
            box_layout = qt.QFormLayout(box)
            box_layout.setFormAlignment(qt.Qt.AlignRight)
            box_layout.setLabelAlignment(qt.Qt.AlignLeft)
            box_layout.setVerticalSpacing(10)

            for key, cfg in cfgs[category].items():
                value = qt.QLabel(cfg)
                value.setAlignment(qt.Qt.AlignRight)
                box_layout.addRow(key, value)

                # Add a line to separate the items, except for the last one
                if key != list(cfgs[category].keys())[-1]:
                    separator = qt.QFrame()
                    separator.setFrameShape(qt.QFrame.HLine)
                    separator.setStyleSheet("color: #444444")
                    separator.setLineWidth(1)
                    box_layout.addRow(separator)

            layout.addWidget(title)
            layout.addWidget(box)

        scroll = qt.QScrollArea()
        scroll.setObjectName("settings-box")
        scroll.setVerticalScrollBarPolicy(qt.Qt.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(qt.Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(qt.QFrame.NoFrame)
        scroll.setWidgetResizable(True)
        scroll.setWidget(frame)

        return scroll

    def load_settings(self, info):
        self.content_page.switch_page("default")
        if info is None:
            return
        self.content_page.switch_page("default")
        self.content_page.remove_page("settings")
        self.content_page.add_page(self._gen_settings_page(info), "settings")
        self.content_page.switch_page("settings")


class Settings(qt.QObject):
    """Settings page

    Signals:
        sig_config_loaded: Emitted when a valid configuration is loaded.

    """

    sig_config_loaded = qt.Signal(dict)

    def __init__(self, cfg_manager: ConfigManager):

        super().__init__()

        self.cfg_manager = cfg_manager
        self.view = SettingsView()
        self.show_tray_icon = self.cfg_manager.gui_cache.get('view.tray_icon')
        self.rx_config = None

        self._add_connections()

    def _add_connections(self):
        self.view.create_rx_bnt.clicked.connect(self.open_config_wizard)
        self.view.new_cfg_bnt.triggered.connect(self.open_config_wizard)
        self.view.load_cfg_bnt.triggered.connect(self.open_select_file_dialog)

        self.view.bitcoin_config_bnt.triggered.connect(
            self.create_bitcoin_config)
        self.view.bitcoin_install_bnt.triggered.connect(self.install_bitcoin)

        self.cfg_manager.sig_cfg_dir.connect(lambda: self.load_rx_config())

    def set_rx_config(self, value):
        self.rx_config = value
        self.sig_config_loaded.emit(value)

        if value:
            # Save loaded config in cache
            self.cfg_manager.save_gui_cache('config.cfg', value['cfg'])

    @qt.Slot()
    def open_config_wizard(self):
        wizard_cfg = configwizard.ConfigWizard(
            cfg_dir=self.cfg_manager.cfg_dir)
        wizard_cfg.sig_finished.connect(self.load_rx_config)
        wizard_cfg.exec_()

    @qt.Slot()
    def open_select_file_dialog(self):
        selected_file = utils.select_file_dialog(
            parent=self.view,
            caption='Configuration files',
            selection_mode='file',
            default_dir=self.cfg_manager.cfg_dir,
            default_dir_only=True,
            filter="(*.json)")
        if selected_file is not None:
            self.cfg_path = selected_file
            self.load_rx_config(self.cfg_path)

    @qt.Slot()
    def load_rx_config(self, cfg_file=None):
        """Load receiver configuration file

        Args:
            cfg_file: Path to the configuration file

        """
        if cfg_file is None:
            # Try to load the last used configuration file saved in the cache.
            # If the file does not exist, try to load the default
            # configuration.
            for cfg in [(self.cfg_manager.gui_cache.get('config.cfg'),
                         self.cfg_manager.cfg_dir),
                        ("config", self.cfg_manager.cfg_dir)]:
                if cfg[0] is None or cfg[1] is None:
                    continue
                cfg_file = config._cfg_file_name(cfg[0], cfg[1])
                if os.path.isfile(cfg_file):
                    break

        info = config._read_cfg_file(cfg_file)

        rx_config = {}
        if info:
            rx_config['cfg'] = os.path.splitext(os.path.basename(cfg_file))[0]
            rx_config['info'] = info

        self.set_rx_config(rx_config)
        self.view.load_settings(info)

    @qt.Slot()
    def create_bitcoin_config(self):
        """Generate bitcoin configuration file"""
        if not self.rx_config:
            messagebox.Message(parent=self,
                               msg_type="info",
                               title="Missing receiver configuration",
                               msg=("Please create a receiver configuration "
                                    "and try again."))
            return

        home = os.path.expanduser("~")
        path = os.path.join(home, ".bitcoin")
        conf_file = "bitcoin.conf"
        abs_path = os.path.join(path, conf_file)
        info = self.rx_config['info']
        ifname = config.get_net_if(info)
        enable_concat = False

        if not os.path.exists(path):
            os.makedirs(path)

        if not os.path.exists(abs_path):
            title_txt = "Save Bitcon Config file"
            msg_txt = "Save {} at {}?".format(conf_file, path)
            bnt_write = "Save"
            enable_concat = False
        else:
            title_txt = "Bitcon Config Exists"
            msg_txt = (f"File {abs_path} already exists."
                       "How would you like to proceed?")
            bnt_write = "Overwrite"
            enable_concat = True

        msg_box = qt.QMessageBox(self.view)
        msg_box.setWindowTitle(title_txt)
        msg_box.setText(msg_txt)

        write_bnt = msg_box.addButton(bnt_write, qt.QMessageBox.ActionRole)

        if enable_concat:
            concat_bnt = msg_box.addButton("Concatenate",
                                           qt.QMessageBox.ActionRole)

        cancel_bnt = msg_box.addButton(qt.QMessageBox.Cancel)

        msg_box.setDefaultButton(cancel_bnt)
        msg_box.exec()

        clicked_button = msg_box.clickedButton()

        concat = False
        if clicked_button == write_bnt:
            concat = False
        elif enable_concat and clicked_button == concat_bnt:
            concat = True
        else:
            return

        bitcoin.create_config_file(abs_path,
                                   info,
                                   ifname,
                                   concat=concat,
                                   stdout=False)

    @qt.Slot()
    def install_bitcoin(self):
        """Install Bitcoin Satellite"""
        install_btc = dependencies.DepsDialog(parent=self.view,
                                              target=None,
                                              command="btc")
        install_btc.exec_()
