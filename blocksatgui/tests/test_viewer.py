from blocksatgui.components.viewer import GuiViewer
from blocksatgui.components.worker import start_job
from blocksatgui.qt import QApplication, QMessageBox, Qt, QThreadPool, QTimer
from blocksatgui.tests.conftest import pytestqt


@pytestqt
class TestGUIViewer():
    """Test the GUI viewer implementation

    The GUIViewer is used to interact with the user through a graphical
    interface when running a task in a separate thread. For example, when
    running a task that requires user input, the GUIViewer will be used to
    display a message box to the user and wait for the user to select an option
    before continuing the task execution in the background. This class tests
    the interaction between the main QT thread and the secondary thread that
    runs the task.

    """

    def test_yes_or_no_question(self, qtbot):
        self.thread_pool = QThreadPool()
        self.viewer = GuiViewer(None)

        def _check_messagebox(action):
            """Simulate the user clicking on the message box"""
            assert action in ['accept', 'reject', 'close']
            messagebox = QApplication.activeWindow()
            assert (isinstance(messagebox, QMessageBox))
            if action != 'close':
                bnt = (messagebox.button(QMessageBox.Ok) if action == 'accept'
                       else messagebox.button(QMessageBox.Cancel))
                qtbot.mouseClick(bnt, Qt.LeftButton)
            else:
                qtbot.keyClick(messagebox, Qt.Key_Escape)

        def _task(viewer):
            """Task that runs in a secondary thread"""
            return viewer.ask_yes_or_no(msg="Do you want to continue?")

        # Select yes
        QTimer.singleShot(100, lambda: _check_messagebox(action='accept'))
        task = start_job(func=_task,
                         args=(self.viewer.get_viewer(), ),
                         thread_pool=self.thread_pool)
        with qtbot.waitSignal(task.signals.sig_finished, timeout=1000):
            pass  # wait for the task to finish
        assert task.result is True

        # Select no
        QTimer.singleShot(100, lambda: _check_messagebox(action='reject'))
        task = start_job(func=_task,
                         args=(self.viewer.get_viewer(), ),
                         thread_pool=self.thread_pool)
        with qtbot.waitSignal(task.signals.sig_finished, timeout=1000):
            pass  # wait for the task to finish
        assert task.result is False

    def test_multiple_choice_question(self, qtbot):
        self.thread_pool = QThreadPool()
        self.viewer = GuiViewer(None)

        def _check_messagebox(action):
            """Simulate the user clicking on the message box"""
            messagebox = QApplication.activeWindow()
            assert (isinstance(messagebox, QMessageBox))
            bnts = messagebox.buttons()
            for bnt in bnts:
                if bnt.text() == action:
                    qtbot.mouseClick(bnt, Qt.LeftButton)
                    return

            # If the action is not in the buttons, close the window
            qtbot.keyClick(messagebox, Qt.Key_Escape)

        def _task(viewer):
            """Task that runs in a secondary thread"""
            return viewer.ask_multiple_choice(msg="Choose an option",
                                              vec=['option1', 'option2'],
                                              label="Options",
                                              to_str=lambda x: f'{x}',
                                              none_option=True,
                                              none_str='None of the above')

        # Select option1
        QTimer.singleShot(100, lambda: _check_messagebox(action='option1'))
        task = start_job(func=_task,
                         args=(self.viewer.get_viewer(), ),
                         thread_pool=self.thread_pool)
        with qtbot.waitSignal(task.signals.sig_finished, timeout=1000):
            pass  # wait for the task to finish
        assert task.result == 'option1'

        # Select option2
        QTimer.singleShot(100, lambda: _check_messagebox(action='option2'))
        task = start_job(func=_task,
                         args=(self.viewer.get_viewer(), ),
                         thread_pool=self.thread_pool)
        with qtbot.waitSignal(task.signals.sig_finished, timeout=1000):
            pass  # wait for the task to finish
        assert task.result == 'option2'

        # Select none
        QTimer.singleShot(
            100, lambda: _check_messagebox(action='None of the above'))
        task = start_job(func=_task,
                         args=(self.viewer.get_viewer(), ),
                         thread_pool=self.thread_pool)
        with qtbot.waitSignal(task.signals.sig_finished, timeout=1000):
            pass  # wait for the task to finish
        assert task.result is None
        assert task.error is None
