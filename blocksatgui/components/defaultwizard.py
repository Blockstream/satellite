from .. import styles, utils
from ..qt import QGroupBox, QLabel, Qt, QVBoxLayout, QWizard, QWizardPage


class DefaultWizardPage(QWizardPage):
    """Default functionality common to all wizard pages

    Attributes:
        wizard (QWizard): Main QWizard.
        title (str): Page title.
        subtitle (str): Page subtitle.
        watermark (str): Watermark image name (stored in the static folder).

    """

    def __init__(self, wizard, title, subtitle, watermark):
        super().__init__(wizard)

        self.setTitle(title)
        self.title()
        self.setSubTitle(subtitle)

        if watermark:
            self.setPixmap(QWizard.WatermarkPixmap,
                           utils.get_svg_pixmap(watermark))

        self.wizard = wizard
        self.page_layout = QVBoxLayout(self)

        self.next_page = 0

    def initializePage(self):
        """Initialize wizard page

        Virtual Qt function. This function is called every time the user clicks
        on the wizard's Next button.

        """
        # Create a component to group all the components that will be added to
        # the page. This way, it easy to clean up if the user clicks the
        # wizard's Back button.
        self.group = QGroupBox(self)
        self.group.setObjectName("group")
        self.group_layout = QVBoxLayout(self.group)
        self.page_layout.addWidget(self.group)

    def validatePage(self):
        """Validate wizard page

        Virtual Qt function. This function validates the page when the user
        clicks Next or Finish. If the return if True, the next page will be
        called, otherwise continue in the same page.

        """
        is_valid = self.validate_inputs()
        if is_valid:
            self.set_next_page()

        return is_valid

    def cleanupPage(self):
        """Clean-up wizard page

        Virtual Qt function. This function resets the page's contents when the
        user clicks the wizard's Back button.

        """
        super().cleanupPage()

        # Remove wrapper component the holds all the page components.
        self.group.deleteLater()
        self.page_layout.removeWidget(self.group)

    def nextId(self):
        """Return the next page ID

        Virtual Qt function. This function returns the ID of the next page.

        """
        return self.next_page

    def validate_inputs(self):
        """Validate the pages inputs

        This method should be overwritten to implement validators.

        """
        return True

    def set_next_page(self):
        self.next_page = -1

    def add_error_component(self, object_name):
        """
        Generate and add the error component to the given layout

        Args:
            object_name: Object identifier

        Returns:
            QT component

        """
        error_msg = QLabel()
        error_msg.setAlignment(Qt.AlignBottom | Qt.AlignHCenter)
        error_msg.setStyleSheet("color: red")
        error_msg.setObjectName(object_name)
        error_msg.setWordWrap(True)

        if hasattr(self, "group_layout"):
            self.group_layout.addWidget(error_msg)
        else:
            self.page_layout.addWidget(error_msg)

        return error_msg

    def get_components_from_layout(self,
                                   object_name,
                                   object_type=None,
                                   return_first=False):
        """Get components in the layout based on the object name

        Args:
            object_name: Object identifier
            object_type: Object type
            return_first: Whether to return only the first item found

        Returns:
            List of the QT components found

        """
        components = list()

        for component in self.group.children():
            if component.objectName() == object_name:
                if object_type and not isinstance(component, object_type):
                    continue

                if return_first:
                    return component

                components.append(component)

        return components

    def _toggle_visibility(self, visible, components):
        """Toggle visibility from components in the layout based on a condition

        Args:
            visible: Whether the component should be visible
            components: List of components to change visibility

        """
        for component in components:
            try:
                component.setVisible(visible)
            except AttributeError:
                pass

    def _validate_type(self, text, in_type, input_comp, error_comp, error_msg):
        """Validate input type

        This function tries to validate the input based on the given type. If
        the input is invalid, add visual feedback in the screen.

        Args:
            text: Input text
            in_type: Desired input type
            input_comp: Input component
            error_comp: Error component
            error_msg: Error message to be displayed in case of invalid input

        Returns:
            Input with the correct type if valid, None otherwise.

        """
        valid_input = None
        msg = ""

        try:
            valid_input = in_type(text)
        except ValueError:
            msg = error_msg

        self._display_error_message(condition=valid_input,
                                    input_comp=input_comp,
                                    error_comp=error_comp,
                                    error_msg=msg)

        return valid_input

    def _display_error_message(self, condition, input_comp, error_comp,
                               error_msg):
        """Display error message in the screen

        Shows an error message and changes the border color from the component
        with the invalid input.

        Args:
            condition: Whether to show the error feedback.
            input_comp: Input component.
            error_comp: Error component.
            error_msg: Error message to be displayed in case of invalid input.

        Returns:
            Condition is True, None otherwise.

        """

        if condition:
            msg = ""
            style = styles.border_style["normal"]
        else:
            msg = error_msg
            style = styles.border_style["error"]

        error_comp.setText(msg)

        # Support a list of components
        if not isinstance(input_comp, list):
            input_comp_list = [input_comp]
        else:
            input_comp_list = input_comp

        try:
            for comp in input_comp_list:
                comp.setStyleSheet(style)
        except AttributeError:
            pass
