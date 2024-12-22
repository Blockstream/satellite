from ..qt import QMessageBox


class Message(QMessageBox):

    icon_map = {
        "critical": QMessageBox.Critical,
        "warning": QMessageBox.Warning,
        "info": QMessageBox.Information,
        "question": QMessageBox.Question
    }

    def __init__(self,
                 parent,
                 msg,
                 title="Error",
                 msg_type="critical",
                 lazy=False):
        super().__init__(parent)
        assert (msg_type
                in self.icon_map.keys()), f"Type {msg_type} is unknown"

        self.setIcon(self.icon_map[msg_type])
        self.setText(title)
        self.setWindowTitle(title)
        self.setInformativeText(msg)

        if msg_type == "question":
            self.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            self.setDefaultButton(QMessageBox.Ok)

        if not lazy:
            self.exec_()

    def exec_(self):
        status = super().exec_()
        if status == QMessageBox.Ok:
            return True
        else:
            return False
