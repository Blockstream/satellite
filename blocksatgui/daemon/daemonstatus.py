import time
from enum import Enum

try:
    import dbus
    DBUS_ENABLED = True
except ImportError:
    DBUS_ENABLED = False

from ..qt import (QHBoxLayout, QLabel, QObject, Qt, QThread, QWidget, Signal,
                  Slot)

SERVICE_NAME = 'com.blockstream.satellite.runner'
INTERFACE_NAME = '/com/blockstream/satellite/runner'


class Status(Enum):
    CONNECTED = "Connected"
    DISCONNECTED = "Disconnected"


class DaemonStatusView(QWidget):
    """Daemon status viewer

    Component that displays whether the blocksatd daemon is connected to dbus.

    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFixedHeight(30)

        self.hbox = QHBoxLayout(self)
        self.hbox.setAlignment(Qt.AlignCenter)
        self.hbox.setContentsMargins(0, 0, 0, 0)
        self.setObjectName("daemon-status")

        self.status_label = QLabel()
        self.hbox.addWidget(self.status_label)
        self.update_status(status=False)

    def update_status(self, status: bool):
        """Update the status text

        Args:
            status: Whether the blocksatd service is reachable via dbus.

        """
        new_status = (Status.CONNECTED.value
                      if status else Status.DISCONNECTED.value)
        status_text = f"Blocksatd: <b>{new_status}</b>"
        if not DBUS_ENABLED:
            # Add additional information to let the user know when the dbus
            # module is missing.
            status_text += " (dbus-python missing)"
        self.status_label.setText(status_text)


class DaemonStatus(QObject):
    """Daemon status controller

    Implements the logic to update the component on the screen.

    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.view = DaemonStatusView(parent)
        self.start_thread()

    def start_thread(self):
        if not DBUS_ENABLED:
            return

        # Initialize thread to watch the daemon state
        worker = DaemonStatusWorker()
        thread = QThread()
        worker.moveToThread(thread)
        worker.sig_status.connect(self.callback_update_status)
        thread.started.connect(worker.run)

        self._worker = worker
        self._thread = thread

        thread.start()

    def stop_threads(self):
        if not hasattr(self, "_worker"):
            return

        self._worker.stop()
        self._thread.quit()

        start_time = time.time()
        timeout = 60
        while time.time() < start_time + timeout:
            if not self._thread.isRunning():
                break
            time.sleep(2)

    @Slot()
    def callback_update_status(self, status):
        self.view.update_status(status)


class DaemonStatusWorker(QObject):
    """Thread to watch the status of the daemon every 3 seconds.

    Signals:
        sig_status (bool): Emitted with last checked status.

    """
    sig_status = Signal(bool)

    def __init__(self):
        super().__init__()

        self._terminate = False

    def run(self):
        self.dbus = DbusClient()

        while not self._terminate:
            status = self.dbus.is_blocksatd_recheable()
            self.sig_status.emit(status)
            time.sleep(3)

    def stop(self):
        self._terminate = True


class DbusClient():

    def __init__(self):
        self.bus = dbus.SystemBus()

    def is_blocksatd_recheable(self):
        try:
            self.bus.get_object(SERVICE_NAME, INTERFACE_NAME)
            status = True
        except dbus.exceptions.DBusException:
            status = False

        return status
