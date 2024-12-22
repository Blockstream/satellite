from .. import qt
from ..components import page
from . import listen, overview, send, settings, transmissions
from .api import SatApi


class SatApiPage(qt.QObject):

    sig_rx_info = qt.Signal(dict)

    def __init__(self, sat_api: SatApi):
        super().__init__()

        self.sat_api = sat_api
        self.view = page.Page(name="satapi-page")

        # Add pages
        self._tabs = {
            'overview': {
                "page": overview.Overview(self.sat_api),
                "label": "Overview"
            },
            'send': {
                "page": send.Send(self.sat_api),
                "label": "Send"
            },
            'listen': {
                "page": listen.Listen(self.sat_api),
                "label": "Listen"
            },
            'tx': {
                "page": transmissions.Transmissions(self.sat_api),
                "label": "Transmissions"
            },
            'settings': {
                "page": settings.Settings(self.sat_api),
                "label": "Settings"
            }
        }
        for name, tab in self._tabs.items():
            self.view.add_tab(label=tab['label'],
                              page=tab['page'].view,
                              page_name=name,
                              set_active=(name == 'overview'))

        # Connect signals
        self.sig_rx_info.connect(self._get_page('listen').set_receiver)
        self.sig_rx_info.connect(self._get_page('overview').set_receiver)
        self.view.sig_page_changed.connect(self.update_pages)

        # Update pages every 5 seconds
        self.timer = qt.QTimer()
        self.timer.timeout.connect(self.update_pages)
        self.timer.start(5000)

    def _get_page(self, name):
        return self._tabs[name]['page']

    def callback_get_receiver_info(self, rx_config):
        self.sig_rx_info.emit(rx_config['info'] if rx_config else {})

    def update_pages(self):
        current_page = self.view.current_page().objectName()
        if current_page == 'satapi-transmissions':
            self._get_page('tx').update_page()

    def stop_threads(self):
        self.sat_api.stop_threads()
