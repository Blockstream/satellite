import os
import signal
import sys

from . import utils
from .components import tray
from .qt import PYSIDE_VERSION, QApplication, QSplashScreen, QTimer


def create_app():
    """Create main QT Application"""
    app = QApplication([])
    app.setOrganizationName("Blockstream")
    app.setApplicationName("Blockstream Satellite")
    app.setWindowIcon(utils.get_svg_pixmap("blocksaticon"))
    app.setDesktopFileName("blocksatgui")
    app.setStyle("Fusion")

    return app


def init_app():
    """Initialize the main GUI application"""
    app = create_app()

    splash_pixmap = utils.get_svg_pixmap("satellite_logo", scale=0.4)
    if PYSIDE_VERSION == "pyside6":
        splash = QSplashScreen(app.primaryScreen(), splash_pixmap)
    else:
        splash = QSplashScreen(splash_pixmap)

    timer = QTimer()
    timer.singleShot(1, splash.show)

    # Lazy load to improve startup time. While showing the splash screen, load
    # the application.
    from . import mainwindow
    window = mainwindow.MainWindow(primary_screen=app.primaryScreen())
    timer.singleShot(500, lambda: splash.finish(window))
    timer.singleShot(500, window.show)

    sys_tray = tray.SystemTray(app, window)
    sys_tray.set_tray()

    with open(os.path.join(utils.get_static_path(), "style.qss"), 'r') as f:
        style = f.read()
        app.setStyleSheet(style)

    timer.singleShot(1000, window.run_initialization_checks)

    def sig_handler(signal=None, frame=None):
        app.quit()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    timer.start(500)
    timer.timeout.connect(lambda: None)

    exit_code = app.exec_()
    window.terminate()
    sys.exit(exit_code)
