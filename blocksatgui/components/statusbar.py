import os
from importlib import reload

from .. import __version__
from ..daemon import daemonstatus
from ..qt import QFrame, QHBoxLayout, QLabel, Qt


class StatusBar(QFrame):

    def __init__(self):
        super().__init__()

        self.setFixedHeight(30)
        self.hbox = QHBoxLayout(self)
        self.hbox.setContentsMargins(20, 0, 20, 0)
        self.setObjectName("status-bar")

        # Check if the GUI is running with root privileges
        self.is_root = os.geteuid() == 0

        self._add_widgets()

    def _add_widgets(self):
        if not self.is_root:
            # Only add the daemon status component to the screen if running as
            # a non-root user. If running with root privileges, the blocksatd
            # is not used. Therefore we do not need to show the status.
            self.daemon_status = daemonstatus.DaemonStatus()
            self.hbox.addWidget(self.daemon_status.view,
                                alignment=Qt.AlignLeft)

        version_label = QLabel(f"v.{__version__}")
        self.hbox.addWidget(version_label, alignment=Qt.AlignRight)

    def stop_threads(self):
        """Wrapper to stop all threads running on the status bar components"""
        if hasattr(self, "daemon_status"):
            self.daemon_status.stop_threads()

    def reload(self):
        # Reload dbus status component
        if hasattr(self, "daemon_status"):
            if not daemonstatus.DBUS_ENABLED:
                reload(daemonstatus)
                self.daemon_status.start_thread()
