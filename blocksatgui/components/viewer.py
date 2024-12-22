from abc import ABC, abstractmethod
from queue import Queue

from blocksatcli import util

from ..components import messagebox
from ..qt import QMessageBox, QObject, Signal


class BaseViewer(ABC):
    """Abstract base class for viewer implementation

    This class defines the metadata (methods and parameters) that should be
    implemented on a viewer class. The viewer is responsible for interacting
    with the user through a command-line interface or a graphical interface.
    Any class that inherits this abstract class should implement all the
    metadata defined here.

    """

    @abstractmethod
    def ask_yes_or_no(self, msg, default="y", help_msg=None, **kwargs) -> bool:
        pass

    @abstractmethod
    def ask_multiple_choice(self,
                            vec,
                            msg,
                            label,
                            to_str,
                            help_msg=None,
                            none_option=False,
                            none_str="None of the above",
                            **kwargs):
        pass


class CliViewer(BaseViewer):
    """Command-line interface viewer

    This class implements the methods defined in the BaseViewer abstract class
    to interact with the user through the command-line interface. It wraps
    around the utility functions defined in the blocksatcli.util module.

    """

    def ask_yes_or_no(self, msg, default="y", help_msg=None, **kwargs):
        return util.ask_yes_or_no(msg, default, help_msg)

    def ask_multiple_choice(self,
                            vec,
                            msg,
                            label,
                            to_str,
                            help_msg=None,
                            none_option=False,
                            none_str="None of the above",
                            **kwargs):
        return util.ask_multiple_choice(vec, msg, label, to_str, help_msg,
                                        none_option, none_str)


class GuiThreadViewer(QObject):
    """Graphical interface viewer to run in a secondary thread

    This class implements the methods defined in the BaseViewer abstract class
    to interact with the user through the graphical interface. Note that the
    real interaction with the user must be done through the main QT thread,
    so this class implements a signal to send the user question to the main
    thread and a queue to receive the user response.

    """

    sig_ask_user = Signal(dict)

    def __init__(self):
        super().__init__()
        self.resp_queue = Queue()  # Queue to receive user response

    def ask_yes_or_no(self, msg, default="y", help_msg=None, **kwargs):
        question = {
            'type': 'yes_or_no',
            'msg': msg,
            'default': default,
            'help_msg': help_msg,
            'title': kwargs.get('title', '')
        }
        self.sig_ask_user.emit(question)
        question = self.resp_queue.get()
        return question['res'] == 'y'

    def ask_multiple_choice(self,
                            vec,
                            msg,
                            label,
                            to_str,
                            help_msg=None,
                            none_option=False,
                            none_str="None of the above",
                            **kwargs):
        question = {
            'type': 'multiple_choice',
            'vec': vec,
            'msg': msg,
            'label': label,
            'to_str': to_str,
            'help_msg': help_msg,
            'none_option': none_option,
            'none_str': none_str,
            'title': kwargs.get('title', '')
        }
        self.sig_ask_user.emit(question)
        question = self.resp_queue.get()
        return question['res']


class GuiViewer(QObject):
    """Graphical interface viewer to run in the main thread"""

    def __init__(self, parent):
        super().__init__(parent)

        self.gui_parent = parent
        self._thread_viewer = GuiThreadViewer()
        self._thread_viewer.sig_ask_user.connect(
            lambda question: self._ask_user(question, self._thread_viewer.
                                            resp_queue))

    def _ask_user(self, question, resp_queue):
        """Create pop-up window with question to user"""
        if question['type'] == 'yes_or_no':
            window = messagebox.Message(parent=self.gui_parent,
                                        msg=question['msg'],
                                        title=question.get('title', ''),
                                        msg_type="question",
                                        lazy=True)
            question['res'] = 'y' if window.exec_() else 'n'
        else:
            msg_box = QMessageBox(self.gui_parent)
            msg_box.setText(question['msg'])
            msg_box.setWindowTitle(question.get('title', ''))

            for option in question['vec']:
                msg_box.addButton(question['to_str'](option),
                                  QMessageBox.ActionRole)
            # Add none option
            if question['none_option']:
                msg_box.addButton(question['none_str'], QMessageBox.ActionRole)

            msg_box.exec_()
            choice = msg_box.clickedButton().text()
            for option in question['vec']:
                if choice == question['to_str'](option):
                    question['res'] = choice
                    break
                elif choice == question['none_str']:
                    question['res'] = None
                    break

        resp_queue.put(question)

    def get_viewer(self) -> GuiThreadViewer:
        return self._thread_viewer
