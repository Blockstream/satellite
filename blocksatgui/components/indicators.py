from .. import styles
from ..qt import (QFrame, QGraphicsDropShadowEffect, QLabel, QPointF,
                  QVBoxLayout)


class StateIndicator():

    def __init__(self):

        self.wrapper = QFrame()
        self._layout = QVBoxLayout(self.wrapper)
        self._layout.setContentsMargins(0, 0, 0, 0)

        self.label = QLabel('')
        self.label.setFixedSize(15, 15)

        self.set_state(connected=False)
        self._layout.addWidget(self.label)

    def set_state(self, connected: bool):
        tip_msg = 'Connected' if connected else 'Disconnected'
        self.label.setToolTip(tip_msg)

        color = (styles.colors["green"] if connected else styles.colors["red"])
        style = (f"border: 1px solid {color}; border-radius: 7px; "
                 f"background: {color};")
        shadow = QGraphicsDropShadowEffect(parent=self.label,
                                           blurRadius=7.0,
                                           color=color,
                                           offset=QPointF(0, 0))
        self.label.setStyleSheet(style)
        self.label.setGraphicsEffect(shadow)
