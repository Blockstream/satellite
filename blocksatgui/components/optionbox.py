from ..qt import QFrame, QHBoxLayout, QLabel, QPushButton, Qt, QVBoxLayout


class OptionsBox(QFrame):

    def __init__(self, parent, title):
        super().__init__(parent=parent)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._layout.setAlignment(Qt.AlignTop)

        self._title = QLabel(title)
        self._title.setMinimumHeight(30)
        self._layout.addWidget(self._title)
        self._gen_box()

    def _gen_box(self):
        box = QFrame(self)
        box.setProperty("qssClass", "settings-box")
        self.box_layout = QVBoxLayout(box)
        self._layout.addWidget(box)

    def _gen_title_and_description(self, name, description):
        box = QFrame(self)
        layout = QVBoxLayout(box)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        name = QLabel(name)
        description = QLabel(description)
        description.setWordWrap(True)
        description.setProperty("qssClass", "text_normal__gray")
        layout.addWidget(name)
        layout.addWidget(description)
        return box

    def _gen_button(self, name):
        box = QFrame(self)
        layout = QVBoxLayout(box)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignRight)
        button = QPushButton(name)
        button.setFixedSize(300, 30)
        button.setObjectName(name.lower().replace(" ", "-"))
        layout.addWidget(button)
        return box, button

    def _gen_separator(self):
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("color: #444444")
        separator.setLineWidth(1)
        return separator

    def add_option(self, name, description, separator=False):
        """Add actionable option to the box

        Args:
            name (str): Name of the option
            description (str): Description of the option

        Returns:
            QPushButton: The button that was added to the box

        """
        box = QFrame(self)
        layout = QHBoxLayout(box)
        info = self._gen_title_and_description(name, description)
        button_box, button = self._gen_button(name)
        layout.addWidget(info, 2)
        layout.addWidget(button_box, 1)
        self.box_layout.addWidget(box)
        if separator:
            self.box_layout.addWidget(self._gen_separator())
        return button

    def add_widget(self, widget):
        self.box_layout.addWidget(widget)
