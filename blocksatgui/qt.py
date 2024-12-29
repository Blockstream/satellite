# Abstraction layer to provide support for PySide2 and PySide6
# flake8: noqa

try:
    PYSIDE_VERSION = "pyside6"

    # yapf: disable
    from PySide6.QtCore import (QAbstractTableModel, QObject,
                                QPersistentModelIndex, QPointF, QRunnable,
                                QSize, QThread, QThreadPool, QTimer, QUrl,
                                Signal, Slot)
    from PySide6.QtGui import (QAction, QClipboard, QCursor, QDesktopServices,
                               QDoubleValidator, QIcon, QIntValidator, Qt)
    from PySide6.QtSvg import QSvgRenderer
    from PySide6.QtSvgWidgets import QSvgWidget
    from PySide6.QtWidgets import (QAbstractItemView, QApplication,
                                   QButtonGroup, QCheckBox, QComboBox, QDialog,
                                   QDialogButtonBox, QDoubleSpinBox,
                                   QFileDialog, QFormLayout, QFrame,
                                   QGraphicsDropShadowEffect, QGridLayout,
                                   QGroupBox, QHBoxLayout, QHeaderView, QLabel,
                                   QLineEdit, QMainWindow, QMenu, QMenuBar,
                                   QMessageBox, QPlainTextEdit, QProgressBar,
                                   QPushButton, QRadioButton, QScrollArea,
                                   QSizePolicy, QSplashScreen, QStackedWidget,
                                   QStyledItemDelegate, QSystemTrayIcon,
                                   QTableView, QTableWidget, QTableWidgetItem,
                                   QTextBrowser, QTextEdit, QVBoxLayout,
                                   QWidget, QWizard, QWizardPage)

    # yapf: enable

except (ImportError, ModuleNotFoundError):

    PYSIDE_VERSION = "pyside2"

    # yapf: disable
    from PySide2.QtCore import (QAbstractTableModel, QObject,
                                QPersistentModelIndex, QPointF, QRunnable,
                                QSize, Qt, QThread, QThreadPool, QTimer, QUrl,
                                Signal, Slot)
    from PySide2.QtGui import (QClipboard, QCursor, QDesktopServices,
                               QDoubleValidator, QIcon, QIntValidator, QPixmap)
    from PySide2.QtSvg import QSvgRenderer, QSvgWidget
    from PySide2.QtWidgets import (QAbstractItemView, QAction, QApplication,
                                   QButtonGroup, QCheckBox, QComboBox, QDialog,
                                   QDialogButtonBox, QDoubleSpinBox,
                                   QFileDialog, QFormLayout, QFrame,
                                   QGraphicsDropShadowEffect, QGridLayout,
                                   QGroupBox, QHBoxLayout, QHeaderView, QLabel,
                                   QLineEdit, QMainWindow, QMenu, QMenuBar,
                                   QMessageBox, QPlainTextEdit, QProgressBar,
                                   QPushButton, QRadioButton, QScrollArea,
                                   QSizePolicy, QSplashScreen, QStackedWidget,
                                   QStyledItemDelegate, QSystemTrayIcon,
                                   QTableView, QTableWidget, QTableWidgetItem,
                                   QTextBrowser, QTextEdit, QVBoxLayout,
                                   QWidget, QWizard, QWizardPage)

    # yapf: enable
