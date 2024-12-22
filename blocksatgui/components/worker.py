import sys
import traceback

from ..qt import QObject, QRunnable, Signal, Slot


class WorkerError:
    """Worker error class"""

    def __init__(self, exc, type, traceback):
        self.exc = exc
        self.type = type
        self.value = exc.code if type == SystemExit else None
        self.traceback = traceback


class WorkerSignals(QObject):
    """Defines the signals available from a running worker thread.

    Signals:
        sig_started: Emitted when the worker starts.
        sig_finished: Emitted with the worker object when the job finishes.

    """
    sig_started = Signal()
    sig_finished = Signal(object)


class WorkerThread(QRunnable):
    """Run a given function on a separated thread

    This class can be used to run a given function in a separate thread and
    communicate with it using QT signals.

    Args:
        work (function): Function to run on this worker thread. The supplied
            args and kwargs will be passed through to the runner.
        args: Arguments to pass to the callback function.
        kwargs: Keywords to pass to the callback function.

    """

    def __init__(self, work, *args, **kwargs):
        super().__init__()

        self.work = work
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self._reset_worker_state()

    def _reset_worker_state(self):
        self.finished = False
        self.failed = False
        self.error = None
        self.result = None

    @Slot()
    def run(self):
        """Run the given function with the passed arguments"""
        self._reset_worker_state()

        error = None
        res = None

        try:
            res = self.work(*self.args, **self.kwargs)
        except:  # noqa: ignore=E722
            exctype, exc = sys.exc_info()[:2]
            error = WorkerError(exc, exctype, traceback.format_exc())
        finally:
            self.finished = True
            self.failed = True if error is not None else False
            self.result = res
            self.error = error
            self.signals.sig_finished.emit(self)


def start_job(func, thread_pool, args=(), kwargs={}, callback=None):
    """Start a job in a separate thread

    Args:
        func (function): Function to run in a separate thread.
        thread_pool (QThreadPool): Thread pool to use to run the job.
        args (tuple): Arguments to be passed to the function.
        kwargs (dict): Keyworded arguments to be passed to the function.
        callback (function, optional): Callback to be called with the
            response from the executed function.

    """
    worker_thread = WorkerThread(func, *args, **kwargs)
    if callback is not None:
        worker_thread.signals.sig_finished.connect(callback)
    thread_pool.start(worker_thread)
    return worker_thread
