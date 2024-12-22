import os
from urllib.parse import urlparse

from blocksatcli import util

from . import qt

LAYOUT_OPTIONS = {
    "vbox": qt.QVBoxLayout,
    "hbox": qt.QHBoxLayout,
    "form": qt.QFormLayout,
    "grid": qt.QGridLayout,
}
VIEW_OPTIONS = {
    "widget": qt.QWidget,
    "frame": qt.QFrame,
}


def get_svg_widget(svg_name, height=None, width=None):
    """Generate a QSvgWidget from an SVG file

    Args:
        svg_name (str): Name of the SVG image.
        height (int): SVG height.
        width (int): SVG width.

    """
    if svg_name[0] == "/":  # Use full path
        svg_path = svg_name
    else:
        static_folder = get_static_path()
        svg_path = os.path.join(static_folder, f"{svg_name}.svg")

    if not os.path.exists(svg_path):
        return

    svg_widget = qt.QSvgWidget(svg_path)

    try:
        svg_widget.renderer().setAspectRatioMode(qt.Qt.KeepAspectRatio)
    except AttributeError:
        # Keep compatibility with old versions of pyside2.
        # In this case, the SVG widget can get the wrong aspect ratio.
        pass

    if height and width:
        svg_widget.setFixedSize(height, width)

    return svg_widget


def get_svg_pixmap(svg_name, scale=0.7):
    """Generate a QPixmap from SVG file

    Args:
        svg_name (str): Name of the SVG image.
        scale (int): Image scale.

    """
    static_folder = get_static_path()
    icon_svg_path = os.path.join(static_folder, f"{svg_name}.svg")
    svg_render = qt.QSvgRenderer(icon_svg_path)
    return qt.QIcon(icon_svg_path).pixmap(svg_render.defaultSize() * scale)


def set_dict(data, field, val, overwrite=True):
    """Set dict value using dot notation

    FIXME: Move the function from cache to util?
    """
    nested_keys = field.split('.')
    tmp = data
    for i, key in enumerate(nested_keys):
        if key not in tmp:
            tmp[key] = {}
        if i == len(nested_keys) - 1:
            if (key in tmp and not overwrite):
                return
            tmp[key] = val
        tmp = tmp[key]


def get_static_path():
    """Get the path to the folder with the static items"""
    this_file = os.path.realpath(__file__)
    root_path = os.path.dirname(this_file)
    return os.path.join(root_path, "static")


def get_default_cfg_dir():
    return os.path.join(util.get_home_dir(), ".blocksat")


def validate_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def get_widget_view(widget_type: str = 'widget'):
    """Get a widget view

    Args:
        widget_type (str): Widget type. Can be 'widget' or 'frame'.

    """
    assert widget_type in VIEW_OPTIONS.keys(), \
        f"Invalid widget type: {widget_type}"
    return VIEW_OPTIONS[widget_type]


def get_widget_layout(layout_type: str = 'vbox'):
    """Get a layout for a widget

    Args:
        layout_type (str): Layout type. Can be 'vbox', 'hbox', 'form' or
            'grid'.

    """
    assert layout_type in LAYOUT_OPTIONS.keys(), \
        f"Invalid layout type: {layout_type}"
    return LAYOUT_OPTIONS[layout_type]


def select_file_dialog(parent,
                       caption="Select Directory",
                       selection_mode='dir',
                       filter='',
                       default_dir='',
                       default_dir_only=False):
    """Select a file or a directory from user's filesystem

    Args:
        parent (QWidget): Parent widget.
        caption (str): Dialog caption.
        selection_mode (str): Selection mode. Can be 'dir' or 'file'. If
          'dir', the dialog will only allow to select a directory. If 'file',
          the dialog will only allow to select a file.
        default_dir (str): Default directory to open the dialog.
        default_dir_only (bool): If True, the user will not be able to select
          a file or directory outside the default directory.

    """

    def _set_topdir(dialog, topdir, currentdir):
        if topdir != currentdir.path():
            dialog.setDirectory(topdir)
            select_type = "directory" if selection_mode == 'dir' else "file"
            msg = f"Please select a {select_type} from {topdir}."
            qt.QMessageBox.warning(dialog, "Warning", msg)

    dialog = qt.QFileDialog(parent=parent,
                            caption=caption,
                            filter=filter,
                            directory=default_dir or '')
    dialog.setOption(qt.QFileDialog.DontUseNativeDialog, True)
    if selection_mode == 'dir':
        dialog.setFileMode(qt.QFileDialog.Directory)
    if default_dir_only:
        dialog.directoryEntered.connect(
            lambda: _set_topdir(dialog, default_dir, dialog.directory()))
    if dialog.exec_() == qt.QDialog.Accepted:
        return dialog.selectedFiles()[0]
