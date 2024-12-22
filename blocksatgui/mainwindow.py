from . import config, update
from .components import stacked, statusbar, topbar
from .daemon.config import DaemonInstallerGUI
from .help import HelpPage
from .overview import OverviewPage
from .qt import QFrame, QMainWindow, QSizePolicy, QTimer, QVBoxLayout
from .receiver import receiver
from .satapi import satapi
from .settings import Settings


class MainWindow(QMainWindow):
    """Main window of Blocksat GUI.

    Add all the components to a QMainWindow and connect the signals.

    """

    def __init__(self, primary_screen):
        super().__init__()

        screen_size = primary_screen.availableGeometry()
        screen_width, screen_height = screen_size.width(), screen_size.height()
        gui_width, gui_height = (1200, 900)

        if screen_width > gui_width and screen_height > gui_height:
            self.resize(gui_width, gui_height)
        else:
            self.resize(screen_width, screen_height)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(640, 480)

        self._set_window_layout()
        self._init_services()
        self._add_widgets()
        self._connect_signals()
        self._load_config()

        self.update_pages()

    def _set_window_layout(self):
        """Configure the main QHBoxLayout
        """
        central_frame = QFrame()
        self.setCentralWidget(central_frame)
        self.vbox = QVBoxLayout(central_frame)
        self.vbox.setContentsMargins(0, 0, 0, 0)
        self.vbox.setSpacing(0)

    def _init_services(self):
        """Initialize the services used by the GUI"""
        self.cfg_manager = config.ConfigManager()

    def _add_widgets(self):
        """Add widgets to the main window

        The main window has three main widgets, which are the topbar, the
        stacked area and the status bar.

        """
        self.stacked_page = stacked.StackedPage()
        self._add_pages_to_stack()

        self.statusbar = statusbar.StatusBar()
        self.topbar = self._topbar_widget()

        self.vbox.addWidget(self.topbar)
        self.vbox.addWidget(self.stacked_page)
        self.vbox.addWidget(self.statusbar)

    def _topbar_widget(self):
        """Generate topbar"""
        self.topbar_opts = {  # Topbar name and associated page
            "home": {
                "page": self.page_overview,
            },
            "receiver": {
                "page": self.page_receiver,
            },
            "api": {
                "page": self.page_sat_api.view,
            },
            "settings": {
                "page": self.page_settings.view,
            },
            "help": {
                "page": self.page_help,
            }
        }

        main_topbar = topbar.TopBar()
        for name, opts in self.topbar_opts.items():
            is_active = True if name == "home" else False
            capitalize = True if name != "api" else False
            bnt = main_topbar.add_button(
                name if name != "api" else name.upper(),
                self.stacked_page.set_active_page, is_active, capitalize,
                opts["page"])
            self.topbar_opts[name]['bnt'] = bnt  # Save button reference

        return main_topbar

    def _add_pages_to_stack(self):
        # Main page
        self.page_overview = OverviewPage()
        self.stacked_page.add_page(self.page_overview)

        # Receiver page
        self.page_receiver = receiver.ReceiverPage(self.cfg_manager)
        self.stacked_page.add_page(self.page_receiver)

        # Sat API page
        self.sat_api = satapi.SatApi(self.cfg_manager)
        self.page_sat_api = satapi.SatApiPage(self.sat_api)
        self.stacked_page.add_page(self.page_sat_api.view)

        # Settings page
        self.page_settings = Settings(cfg_manager=self.cfg_manager)
        self.stacked_page.add_page(self.page_settings.view)

        # Help page
        self.page_help = HelpPage()
        self.stacked_page.add_page(self.page_help)

    def _connect_signals(self):
        """Connect all the main window signals"""
        # Connections on the overview page
        self.page_overview.receiver_card.sig_clicked.connect(
            lambda: self.open_page("receiver"))
        self.page_overview.satapi_card.sig_clicked.connect(
            lambda: self.open_page("api"))
        self.page_overview.help_card.sig_clicked.connect(
            lambda: self.open_page("help"))

        # Connect pages to receive the receiver info
        self.page_receiver.sig_config_loaded.connect(
            self.page_help.callback_get_receiver_info)
        self.page_receiver.sig_config_loaded.connect(
            self.page_settings.callback_get_receiver_info)
        self.page_receiver.sig_config_loaded.connect(
            self.page_sat_api.callback_get_receiver_info)

    def _load_config(self):
        """Load configuration"""
        self.page_receiver.load_rx_config()

    def _update_states(self):
        """Update the states of the pages"""
        self.cfg_manager.update()

    def update_pages(self):
        """Set timer to update pages periodically"""
        timer = QTimer(self)
        timer.start(5000)
        timer.singleShot(1000, self._update_states)
        timer.timeout.connect(self._update_states)

    def open_page(self, tab_name):
        """Open the page associated with a specific top bar tab"""
        assert (tab_name in self.topbar_opts.keys())
        self.topbar.reset_icon_selection()
        self.topbar_opts[tab_name]['bnt'].set_active()
        self.stacked_page.set_active_page(self.topbar_opts[tab_name]['page'])

    def init_blocksat_daemon(self):
        """Initialize the Blocksat daemon"""
        daemon = DaemonInstallerGUI(self)
        daemon.start()
        self.statusbar.reload()

    def run_initialization_checks(self):
        self.init_blocksat_daemon()
        update.check_gui_updates()

    def terminate(self):
        """Gracefully terminate running threads"""
        self.statusbar.stop_threads()
        self.page_receiver.stop_threads()
        self.page_sat_api.stop_threads()
