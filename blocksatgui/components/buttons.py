from .. import utils
from ..qt import QCursor, QLabel, QPushButton, QSize, Qt, Signal


class ReloadButton(QPushButton):

    def __init__(self):
        super().__init__()

        reload_pixmap = utils.get_svg_pixmap("reload_icon")
        self.setIcon(reload_pixmap)


class MainButton(QPushButton):

    def __init__(self, name, obj_name="run-bnt", width=280, height=50):
        super().__init__(name)

        self.setObjectName(obj_name)
        self.setFixedSize(QSize(width, height))
        self.setCursor(QCursor(Qt.PointingHandCursor))

    def set_text(self, text):
        self.setText(text)

    def set_icon(self, icon_path):
        icon = utils.get_svg_pixmap(icon_path)
        self.setIcon(icon)
        self.setIconSize(QSize(25, 25))


class TextButton(QLabel):

    clicked = Signal()

    def __init__(self, name):
        super().__init__(name)

        self.setObjectName("clickable-text")
        self.setCursor(QCursor(Qt.PointingHandCursor))

    def mousePressEvent(self, event):
        self.clicked.emit()
