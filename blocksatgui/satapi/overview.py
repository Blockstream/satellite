from blocksatcli import config

from .. import qt, utils
from ..components import page
from .api import SatApi


class OverviewView(page.Page):

    def __init__(self):
        super().__init__(name="satapi-overview", topbar_enabled=False)

        self._layout.setContentsMargins(10, 5, 5, 10)
        self._layout.setAlignment(qt.Qt.AlignCenter)

        self.add_page(self._gen_main_page(), "overview")

    def _gen_main_page(self):
        frame, layout = page.get_widget('overview-tab')
        layout.addWidget(self._gen_icon(), alignment=qt.Qt.AlignCenter)
        layout.addWidget(self._gen_api_info_box(), alignment=qt.Qt.AlignCenter)
        return frame

    def _gen_icon(self):
        self.satapi_img = qt.QLabel()
        self.satapi_img.setFixedHeight(300)
        pixmap = utils.get_svg_pixmap("satapi", 0.5)
        self.satapi_img.setPixmap(pixmap)
        return self.satapi_img

    def _gen_api_info_box(self):
        frame = qt.QFrame(self)
        frame.setObjectName("info-box")
        frame.setSizePolicy(qt.QSizePolicy.Expanding, qt.QSizePolicy.Expanding)
        layout = qt.QFormLayout(frame)
        layout.setLabelAlignment(qt.Qt.AlignRight)
        layout.setFormAlignment(qt.Qt.AlignLeft)
        layout.setVerticalSpacing(10)
        layout.setContentsMargins(10, 0, 10, 0)
        self.receiver = qt.QLabel("No receiver selected")
        self.api = qt.QLabel("Disconnected")
        layout.addRow("Receiver:", self.receiver)
        layout.addRow("API status:", self.api)

        return frame

    def set_receiver(self, receiver):
        self.receiver.setText(receiver)

    def set_api_status(self, connected: bool):
        status = "Connected" if connected else "Disconnected"
        self.api.setText(status)


class Overview(qt.QObject):

    def __init__(self, sat_api: SatApi):
        self.view = OverviewView()
        self.sat_api = sat_api

        self._connect_signals()

    def _connect_signals(self):
        self.sat_api.config_manager.sig_is_api_server_valid.connect(
            self.view.set_api_status)

    def set_receiver(self, rx_info):
        if not rx_info:
            self.view.set_receiver("No receiver selected")
            return
        setup = rx_info["setup"]
        name = config._get_rx_marketing_name(setup)
        self.view.set_receiver(name)
