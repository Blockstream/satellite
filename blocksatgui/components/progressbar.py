from ..qt import QProgressBar


class SimpleProgressBar(QProgressBar):

    def __init__(self, maximum, minimum):
        super().__init__()

        self.setMaximum(maximum)
        self.setMinimum(minimum)

    def update(self, value):
        """Update progress bar value"""
        self.setValue(value)
