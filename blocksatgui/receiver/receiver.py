from ..components import stacked, topbar
from ..qt import Qt, QVBoxLayout, QWidget, Signal
from . import dashboard, settings


class ReceiverPage(QWidget):

    sig_started_thr_rx = Signal()
    sig_stopped_thr_rx = Signal()
    sig_config_loaded = Signal(dict)

    def __init__(self, cfg_manager):
        super().__init__()

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._layout.setAlignment(Qt.AlignCenter)
        self._layout.setObjectName("receiver-page")
        self.cfg_manager = cfg_manager
        self._add_widgets()

    def _add_widgets(self):
        self.stacked_pages = stacked.StackedPage()
        self._add_pages_to_stack()

        self._layout.addWidget(self._topbar_widget())
        self._layout.addWidget(self.stacked_pages)

        self._add_connections()

    def _topbar_widget(self):
        self.topbar_opts = {
            "dashboard": {
                "page": self.page_dashboard,
            },
            "settings": {
                "page": self.page_settings.view,
            }
        }

        top_bar = topbar.TopBar(add_icon=False, obj_name="top-bar__inner")

        for name, opts in self.topbar_opts.items():
            # Set first page as active
            is_active = True if name == list(
                self.topbar_opts.keys())[0] else False
            capitalize = True
            bnt = top_bar.add_button(name, self.stacked_pages.set_active_page,
                                     is_active, capitalize, opts["page"])
            self.topbar_opts[name]["bnt"] = bnt

        return top_bar

    def _add_pages_to_stack(self):
        self.page_dashboard = dashboard.ReceiverDashboard(self.cfg_manager)
        self.page_settings = settings.Settings(self.cfg_manager)

        self.stacked_pages.add_page(self.page_dashboard)
        self.stacked_pages.add_page(self.page_settings.view)

    def _add_connections(self):
        self.page_dashboard.sig_started_thr_rx.connect(self.sig_started_thr_rx)
        self.page_dashboard.sig_stopped_thr_rx.connect(self.sig_stopped_thr_rx)
        self.page_settings.sig_config_loaded.connect(
            self.page_dashboard.callback_load_receiver_config)
        self.page_settings.sig_config_loaded.connect(
            self.sig_config_loaded.emit)
        self.page_dashboard.sig_request_config_wizard.connect(
            self.page_settings.open_config_wizard)

    def load_rx_config(self):
        """Load receiver configuration"""
        self.page_settings.load_rx_config()

    def stop_threads(self):
        self.page_dashboard.stop_threads()
