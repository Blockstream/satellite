from ..qt import QFrame, QHBoxLayout, QSizePolicy, QStackedWidget, Qt, QWidget


class StackedPage(QFrame):

    def __init__(self) -> None:
        super().__init__()

        self.setObjectName("stacked-area")

        vbox = QHBoxLayout(self)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setAlignment(Qt.AlignCenter)
        vbox.setSpacing(0)

        self.stacked_area = QStackedWidget(self)
        self.stacked_area.setMaximumWidth(1080)
        self.stacked_area.setSizePolicy(
            QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))

        vbox.addWidget(self.stacked_area)

    def add_page(self, page):
        """Add page to stack"""
        assert (isinstance(page, QWidget))
        self.stacked_area.addWidget(page)

    def remove_page(self, page):
        """Remove page from stack"""
        assert (isinstance(page, QWidget))
        self.stacked_area.removeWidget(page)

    def set_active_page(self, page):
        """Set active widget on the stacked component"""
        self.stacked_area.setCurrentWidget(page)

    def get_current_page(self):
        """Returns the current active page"""
        return self.stacked_area.currentWidget()
