from .. import utils
from ..qt import (QFrame, QPushButton, QPlainTextEdit, QVBoxLayout, QIcon,
                  QTimer, QClipboard, Qt, QLabel)


class CopiableText(QFrame):

    def __init__(self, text, text_widget=QPlainTextEdit):
        assert (text_widget in [QPlainTextEdit, QLabel])
        super().__init__()

        self.setObjectName("copiable-widget")

        self._layout = QVBoxLayout(self)
        self._layout.setSpacing(0)
        self._layout.setContentsMargins(10, 10, 0, 10)

        self.timer = QTimer()

        self.text = text
        self.text_widget = text_widget(text)

        if text_widget == QPlainTextEdit:
            self.text_widget.setReadOnly(True)

        self.copy_bnt = QPushButton()
        self.copy_bnt.setFixedSize(60, 25)

        self._set_icon()
        self.copy_bnt.clicked.connect(lambda: self._copy_to_clipboard(text))
        self.copy_bnt.clicked.connect(self._copy_animation)

        self._layout.addWidget(self.copy_bnt, alignment=Qt.AlignRight)
        self._layout.addWidget(self.text_widget)

    def _set_icon(self):
        svg_icon = utils.get_svg_pixmap('copy_icon', scale=1)
        self.copy_bnt.setText('')
        self.copy_bnt.setIcon(svg_icon)

    def _copy_animation(self):
        self.copy_bnt.setIcon(QIcon())
        self.copy_bnt.setText("Copied!")
        self.timer.singleShot(1000, self._set_icon)

    def _copy_to_clipboard(self, text):
        """Copy text to system clipboard"""
        cb = QClipboard()
        cb.setText(text)
