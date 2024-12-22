from . import utils
from .components import cards
from .qt import QFrame, QHBoxLayout, Qt, QVBoxLayout, QWidget, QLabel


class OverviewPage(QWidget):

    def __init__(self):

        super().__init__()

        self.vbox = QVBoxLayout(self)
        self.vbox.setContentsMargins(0, 10, 0, 0)
        self.vbox.setSpacing(0)
        self.vbox.setAlignment(Qt.AlignCenter)

        self.setObjectName("overview-page")

        self._add_widgets()

    def _add_widgets(self):

        blocksat_svg = QLabel()
        blocksat_svg.setFixedWidth(600)
        blocksat_svg.setFixedHeight(200)
        pixmap = utils.get_svg_pixmap("satellite_logo", 0.3)
        blocksat_svg.setPixmap(pixmap)

        info_box = QFrame(self)
        info_box.setFixedWidth(780)
        info_box.setFixedHeight(300)

        info_layout = QHBoxLayout(info_box)
        info_layout.setSpacing(0)
        info_layout.setContentsMargins(0, 0, 0, 0)

        self.receiver_card = cards.InfoCard(
            title="DVB-S2 Receiver",
            description="Set up and run your DVB-S2 receiver",
            obj_name="receiver-card",
            icon="antenna_icon_blue",
            clickable=True,
            width=230)
        self.satapi_card = cards.InfoCard(
            title="Satellite API",
            description="Send and receive satellite messages",
            obj_name="satapi-card",
            icon="message_icon",
            clickable=True,
            width=230)
        self.help_card = cards.InfoCard(
            title="Help",
            description="Visit the help page to learn more",
            obj_name="help-card",
            icon="help_icon_blue",
            clickable=True,
            width=230)

        info_layout.addWidget(self.receiver_card)
        info_layout.addWidget(self.satapi_card)
        info_layout.addWidget(self.help_card)

        self.vbox.addWidget(blocksat_svg, alignment=Qt.AlignCenter)
        self.vbox.addWidget(info_box)
