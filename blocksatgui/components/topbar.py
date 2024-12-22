from .. import utils
from ..qt import QFrame, QHBoxLayout, QPushButton, Qt


class TopBar(QFrame):

    def __init__(self, add_icon=True, obj_name="top-bar"):
        super().__init__()

        self.setFixedHeight(50)
        self.hbox = QHBoxLayout(self)
        self.hbox.setContentsMargins(0, 0, 0, 0)
        self.hbox.setSpacing(0)
        self.hbox.setAlignment(Qt.AlignCenter)

        self.setObjectName(obj_name)

        if add_icon:
            blocksat_svg = utils.get_svg_widget("blocksaticon",
                                                height=30,
                                                width=30)
            self.hbox.addWidget(blocksat_svg)

    def _set_button_state(self, bnt):
        self.reset_icon_selection()
        bnt.set_active(True)

    def add_button(self,
                   name,
                   callback,
                   is_active=False,
                   capitalize=True,
                   *args):
        """Add button to the topbar and connect to the callback"""
        bnt = TopbarButton(text=name.capitalize() if capitalize else name,
                           is_active=is_active)
        bnt.clicked.connect(lambda: self._set_button_state(bnt))
        bnt.clicked.connect(lambda: callback(*args))
        self.hbox.addWidget(bnt)

        return bnt

    def reset_icon_selection(self):
        """Reset state of all tabs"""
        for bnt in self.findChildren(QPushButton):
            bnt.setChecked(False)


class TopbarButton(QPushButton):

    def __init__(self, text, bnt_height=50, is_active=False, object_name=None):
        super().__init__()

        if not object_name:
            self.setObjectName("top-bar__bnt")
        else:
            self.setObjectName(object_name)

        self.setText(text)
        self.setFixedHeight(bnt_height)
        self.setCheckable(True)
        self.set_active(is_active)

    def set_active(self, is_active=True):
        self.setChecked(is_active)
