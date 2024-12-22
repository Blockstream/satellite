from typing import Optional

from blocksatgui import utils

from .. import qt
from . import stacked, topbar


class Page(qt.QWidget):

    sig_page_changed = qt.Signal(str)

    def __init__(self, name: str, layout=qt.QVBoxLayout, topbar_enabled=True):
        """Implements a page with a stacked area and optional topbar.

        Args:
            name (str): Name of the page (used for object name).
            layout (QBoxLayout): Main layout to use for the page.
            topbar_enabled (bool): Whether to include a topbar.

        """
        super().__init__()

        self.setObjectName(name)
        self.stack = stacked.StackedPage()
        self.stack.stacked_area.currentChanged.connect(
            self.sig_page_changed.emit)

        self._topbar_enabled = topbar_enabled
        if self._topbar_enabled:
            self.topbar = topbar.TopBar(add_icon=False,
                                        obj_name="top-bar__inner")

        self._add_widgets(layout)  # Add widgets to the page
        self._stacked_pages = {}  # Keeps track of the stacked pages

    def _add_widgets(self, layout):
        """Adds widgets to the page layout"""
        self._layout = layout(self)
        self._layout.setContentsMargins(0, 2, 0, 0)
        self._layout.setSpacing(0)
        if self._topbar_enabled:
            self._layout.addWidget(self.topbar)
        self._layout.addWidget(self.stack)

    def add_widget(self, widget: qt.QWidget):
        """Adds a widget to the page"""
        self._layout.addWidget(widget)

    def add_page(self, page: qt.QWidget, page_name: str):
        """Adds a page to the stacked area"""
        self._stacked_pages[page_name] = page
        self.stack.add_page(page)

    def add_tab(self,
                label: str,
                page: qt.QWidget,
                page_name: Optional[str] = None,
                set_active: bool = False):
        """Adds a tab to the page

        A tab is defined as the combination of a topbar button and a page with
        content. This method automatically creates a button on the top bar with
        the given label and adds the page to the content area. Also connects
        the top bar button to the page switching slot, i.e., the given page
        will be displayed when the user clicks on the top bar button.

        Args:
            label (str): Label for the top bar button.
            page (QWidget): Page to be added to the stacked area.
            page_name (str): Name of the page. If not provided, the label will
                be used as the name.

        """
        assert self._topbar_enabled, "Topbar should be enabled to add tabs"
        obj_name = page_name or label
        self.add_page(page=page, page_name=obj_name)
        self.topbar.add_button(name=label,
                               is_active=set_active,
                               callback=lambda: self.switch_page(obj_name))

    def current_page(self):
        """Returns the current page"""
        return self.stack.get_current_page()

    def switch_page(self, name: str):
        """Switches to the page with the given name"""
        assert name in self._stacked_pages, f"Page {name} not found"
        self.stack.set_active_page(self._stacked_pages[name])

    def remove_page(self, name: str):
        """Removes the page with the given name"""
        assert name in self._stacked_pages, f"Page {name} not found"
        self.stack.remove_page(self._stacked_pages[name])
        self._stacked_pages.pop(name)


def get_widget(obj_name: str,
               view_type='widget',
               layout_type='vbox',
               align_center=True):
    """Returns a simple widget with layout

    Args:
        obj_name (str): Object name for the frame.
        view_type (str): Type of widget. Valid options are: 'widget' and
            'frame'. Defaults to 'widget'.
        layout_type (str): Layout type for the frame. Valid options are:
            'hbox', 'vbox', 'grid', and 'form'. Defaults to 'vbox'.
        align_center (bool): Whether to align the layout to the center.
            Defaults to True.

    """
    view = utils.get_widget_view(view_type)
    layout = utils.get_widget_layout(layout_type)
    viewer = view()
    viewer.setObjectName(obj_name)
    layout = layout(viewer)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)
    if align_center:
        layout.setAlignment(qt.Qt.AlignCenter)
    return viewer, layout
