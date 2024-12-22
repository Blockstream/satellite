import webbrowser

from .. import utils
from ..qt import (QFrame, QGraphicsDropShadowEffect, QLabel, QPointF,
                  QPushButton, Qt, QVBoxLayout, Signal, Slot)


class Card(QFrame):

    def __init__(self, name, object_name, height=130):
        """Generic card component

        Args:
            name (str): Card name displayed on the screen.
            object_name (str): Object identifier.
            height (int, optional): Card height. Defaults to 130.

        """
        super().__init__()

        self.setFixedHeight(height)
        self.setProperty("style", "card")
        self.setObjectName(object_name)
        frame_layout = QVBoxLayout(self)
        frame_layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel(name.upper())
        title.setFixedHeight(30)
        title.setProperty("qssClass", "card__title")
        title.adjustSize()

        self._box = QFrame()
        self._box.setObjectName(object_name)
        self._box.setProperty("qssClass", "card__box")
        self._layout = QVBoxLayout(self._box)
        self._layout.setSpacing(0)
        self._layout.setContentsMargins(0, 0, 0, 0)

        frame_layout.addWidget(title)
        frame_layout.addWidget(self._box)

    def set_body(self, component, alignment=Qt.AlignCenter):
        self._layout.addWidget(component, alignment=alignment)


class MetricCard(QFrame):

    sig_active_card = Signal(bool)

    def __init__(self, name, object_name):
        """Metric card component

        Args:
            name (str): Card name displayed on the screen.
            object_name (str): Object identifier.

        Signals:
            sig_active_card: Emitted to change card style.

        """
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.setObjectName(f"card_{object_name}")
        self.card = Card(name, object_name)
        self.value = QLabel("N/A")
        self.value.setObjectName("card__value")
        self.value.setProperty("color", "blocksat-blue")
        self.value.setAlignment(Qt.AlignCenter)
        self.card.set_body(self.value)

        layout.addWidget(self.card)

        self._active = False
        self.sig_active_card.connect(self.callback_card_style)

    @property
    def active(self):
        return self._active

    @active.setter
    def active(self, value):
        self._active = value
        self.sig_active_card.emit(value)

    @Slot()
    def callback_card_style(self, active=True, canceled=False):
        if active:
            self.setStyleSheet('''
                    QFrame[qssClass='card__box'] {
                        border: 1px solid #358de5;
                    }
                    QLabel#card__value {
                        color: #358de5;
                    }
            ''')
        elif canceled:
            self.setStyleSheet('''
                        QFrame[qssClass='card__box'] {
                            border: 1px solid #A70137;
                        }
                        QLabel#card__value {
                            color: #A70137;
                        }
                ''')
        else:
            self.setStyleSheet('''
                    QFrame[qssClass='card__box'] {
                        border: 1px solid #444444;
                    }
                    QLabel#card__value {
                        color: grey;
                    }
            ''')


class InfoCard(QFrame):

    sig_clicked = Signal()

    def __init__(self,
                 title,
                 description,
                 obj_name,
                 bnt_text=None,
                 url=None,
                 height=260,
                 width=230,
                 shadow=True,
                 clickable=False,
                 icon=None):

        super().__init__()

        self.setFixedHeight(height)
        self.setFixedWidth(width)
        self.setProperty("qssClass", "info-card")
        self.setObjectName(obj_name)

        if clickable:
            self.setProperty("qssClass", ["info-card-clickable"])
            self.mousePressEvent = self.mouse_event

        self.url = url
        self.card_layout = QVBoxLayout(self)
        self.card_layout.setContentsMargins(3, 0, 3, 0)

        if shadow:
            shadow_effect = QGraphicsDropShadowEffect(parent=self,
                                                      blurRadius=20.0,
                                                      color="#1F3A98",
                                                      offset=QPointF(0, 0))
            self.setGraphicsEffect(shadow_effect)

        if icon:
            icon_svg = utils.get_svg_widget(icon, height=35, width=35)
            self.card_layout.addWidget(icon_svg)

        box_title = QLabel(title)
        box_title.setFixedHeight(70)
        box_title.setProperty("qssClass", "info-card__title")

        box_description = QLabel(description)
        box_description.setWordWrap(True)
        box_description.setFixedWidth(width - 40)
        box_description.setProperty("qssClass", "info-card__desc")

        self.card_layout.addWidget(box_title, alignment=Qt.AlignLeft)
        self.card_layout.addWidget(box_description,
                                   alignment=Qt.AlignTop | Qt.AlignLeft)

        if bnt_text:
            bnt = QPushButton(bnt_text)
            bnt.setProperty("qssClass", "info-card__bnt")
            bnt.clicked.connect(lambda: self.sig_clicked.emit())
            if url:
                # Automatically connect button to open external link if url is
                # present
                bnt.clicked.connect(self.open_external_link)

            self.card_layout.addWidget(bnt, alignment=Qt.AlignLeft)

    @Slot()
    def open_external_link(self):
        assert (self.url is not None), "External link not defined"
        webbrowser.open(self.url)

    def mouse_event(self, event):
        self.sig_clicked.emit()
