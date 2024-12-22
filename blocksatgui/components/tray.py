from blocksatcli import cache

from .. import utils
from ..qt import QAction, QMenu, QSystemTrayIcon, Slot


class SystemTray(QSystemTrayIcon):
    """Manages the system tray icon.

    Args:
        window (QMainWindow): Main application window.

    """

    def __init__(self, app, window):
        super().__init__()

        self.app = app
        self.window = window

        self.cache = cache.Cache(utils.get_default_cfg_dir(), '.blocksatgui')

        self.is_available = self.isSystemTrayAvailable()
        if not self.is_available:
            return

        self._tray_default = "blocksat_tray"
        self._tray_active = "blocksat_tray_active"

        self._init_widget()
        self._connect_signals()

    def _init_widget(self):
        """Initiallize tray widget"""
        self._add_menu()
        self._set_icon(self._tray_default)
        self.setVisible(True)

    def _connect_signals(self):
        self.window.page_receiver.sig_started_thr_rx.connect(
            self.callback_receive_active)

        self.window.page_receiver.sig_stopped_thr_rx.connect(
            self.callback_receive_inactive)

        self.window.page_settings.sig_toggle_tray_icon.connect(
            self.callback_toggle_tray_icon)

    def _add_menu(self):
        """Add tray menu"""

        # Options
        open_opt = QAction("&Open", parent=self)
        quit_opt = QAction("&Quit", parent=self)

        # Menu
        menu = QMenu()
        menu.addAction(open_opt)
        menu.addAction(quit_opt)

        # Signals
        quit_opt.triggered.connect(self.callback_quit)
        open_opt.triggered.connect(self.callback_show)

        self.setContextMenu(menu)

    def _set_icon(self, icon_path):
        """Set tray icon"""
        self.setIcon(utils.get_svg_pixmap(icon_path))

    def enable(self):
        """Enable system tray icon"""

        if self.is_available:
            self.app.setQuitOnLastWindowClosed(False)
            self.show()

    def disable(self):
        """Disable system tray icon"""
        self.app.setQuitOnLastWindowClosed(True)
        self.hide()

    def set_tray(self):
        """Set icon on the system tray if enabled"""
        self.cache.load()
        tray_icon_status = self.cache.get('view.tray_icon')

        if tray_icon_status or tray_icon_status is None:
            self.enable()
        else:
            self.disable()

    @Slot()
    def callback_show(self):
        self.window.hide()
        self.window.show()

    @Slot()
    def callback_quit(self):
        self.app.exit()

    @Slot()
    def callback_receive_active(self):
        self._set_icon(self._tray_active)

    @Slot()
    def callback_receive_inactive(self):
        self._set_icon(self._tray_default)

    @Slot()
    def callback_toggle_tray_icon(self, state):
        if state:
            self.enable()
        else:
            self.disable()
