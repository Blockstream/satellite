import os
import sys
import time
import traceback
from argparse import Namespace
from copy import copy
from ipaddress import ip_address

from blocksatcli import defs, satip, usb

from .. import styles
from ..components import buttons, messagebox
from ..qt import (QCheckBox, QComboBox, QDoubleValidator, QFormLayout, QFrame,
                  QGroupBox, QHBoxLayout, QIntValidator, QLabel, QLineEdit,
                  QObject, QThread, Signal)


class ReceiverOptions(QFrame):

    options_map = {
        defs.sdr_setup_type: {
            'gui': {
                'widget': QCheckBox,
                'label': 'GUI Mode',
                'tip': 'Enable GUI mode',
            },
            'gain': {
                'widget': QLineEdit,
                'label': 'Gain',
                'tip': 'RTL-SDR Rx gain',
                'type': float
            },
            'derotate': {
                'widget': QLineEdit,
                'label': 'Freq. Correction (kHz)',
                'tip': 'Frequency offset correction in kHz',
                'type': float
            },
            'rtl_idx': {
                'widget': QLineEdit,
                'label': 'RTL-SDR Index',
                'tip': 'RTL-SDR device index',
                'type': int
            }
        },
        defs.standalone_setup_type: {
            'address': {
                'widget': QLineEdit,
                'label': 'IP Address',
                'tip': "Standalone receiver's IP address",
                'type': ip_address,
                'config_key': 'rx_ip'
            },
            'freq_corr': {
                'widget': QLineEdit,
                'label': 'Freq. Correction (kHz)',
                'tip': 'Frequency offset correction in kHz',
                'type': float
            },
            'demod': {
                'widget': QComboBox,
                'label': 'Demodulator',
                'tip': 'Target demodulator within the S400',
                'choices': ["1", "2"],
                'type': str
            }
        },
        defs.sat_ip_setup_type: {
            'device': {
                'widget':
                QComboBox,
                'label':
                'Discover Sat-IP Device',
                'type':
                str,
                'tip':
                ('Sat-IP receiver discovered in the local network via UPnP '),
                'reload':
                True
            },
            'addr': {
                'widget': QLineEdit,
                'label': 'IP Address',
                'tip': 'Sat-IP antenna IP address',
                'type': ip_address,
                'config_key': 'ip_addr'
            },
            'freq_corr': {
                'widget': QLineEdit,
                'label': 'Freq. Correction (kHz)',
                'tip': 'Frequency offset correction in kHz',
                'type': float
            },
            'username': {
                'widget': QLineEdit,
                'label': 'Username',
                'tip': 'Sat-IP client username',
                'type': str
            },
            'password': {
                'widget': QLineEdit,
                'label': 'Password',
                'tip': 'Sat-IP client password',
                'type': str,
                'echo': QLineEdit.Password
            }
        },
        defs.linux_usb_setup_type: {
            'ip': {
                'widget': QLineEdit,
                'label': 'IP Address',
                'tip': 'IP address for the DVB-S2 net interface',
                'type': ip_address
            },
            'device': {
                'widget': QComboBox,
                'label': 'Device',
                'tip': 'Select the DVB adapter',
                'type': str,
                'reload': True
            }
        }
    }

    advanced_options_map = {
        defs.sdr_setup_type: {
            'implementation': {
                'widget': QComboBox,
                'type': str,
                'label': 'Implementation',
                'choices': ['leandvb', 'gr-dvbs2rx'],
                'tip': 'Software-defined demodulator implementation'
            }
        },
        defs.standalone_setup_type: {},
        defs.sat_ip_setup_type: {
            'ssdp_src_port': {
                'widget':
                QLineEdit,
                'label':
                'SSDP Source Port',
                'type':
                int,
                'tip': ('Source port set on SSDP packets used to discover '
                        'the Sat-IP server(s) in the network')
            },
            'ssdp_net_if': {
                'widget':
                QLineEdit,
                'label':
                'SSDP Network Interface',
                'type':
                str,
                'tip': ('Network interface over which to send SSDP packets '
                        'to discover the Sat-IP server(s) in the network')
            },
        },
        defs.linux_usb_setup_type: {}
    }

    validator_map = {'float': QDoubleValidator, 'int': QIntValidator}

    def __init__(self):
        super().__init__()

        self.setObjectName("rxoptions")

        name = QLabel("RECEIVER")
        name.setObjectName("card-title")

        layout = QFormLayout(self)
        layout.setContentsMargins(20, 20, 20, 0)
        layout.setSpacing(5)

        # Default object name for the group box widgets used on the options
        # component and on the status component.
        self.options_widget_name = "box"
        self.advanced_options_widget_name = "advanced-box"
        self.status_widget_name = "status"

        layout.addWidget(name)
        layout.addWidget(self._add_status())

        # Add an environment variable to disable the automatic reload behavior.
        # By default, this component will automatically run the reload function
        # associated with the reloadable widgets (i.e., discover USB
        # receivers).
        self._no_auto_reload = os.getenv('BLOCKSAT_NO_AUTO_RELOAD',
                                         'False').lower() in ('true', 1, 't')

        self._layout = layout

    def _add_status(self):
        """Add receiver status component"""
        status_box = QGroupBox("", self)
        status_box.setObjectName(self.status_widget_name)

        layout = QFormLayout(status_box)

        self.rx_model = QLabel("")
        self.rx_type = QLabel("")

        layout.addRow("Model: ", self.rx_model)
        layout.addRow("Type: ", self.rx_type)

        return status_box

    def _add_options(self, rx_config, args, options='default'):
        """Add receiver options component

        For each receiver option, create a widget and add it to the group box.

        Args:
            config (dict): Dictionary with receiver configuration.
            args (dict): Dictionary with CLI arguments.
            options (str): Select the options type ('default' or 'advanced')

        """
        assert (options in ['default', 'advanced'])
        assert (rx_config is not None)
        assert (args is not None)

        rx_info = rx_config['info']
        rx_type = rx_info['setup']['type']

        if options == 'advanced':
            box_name = "Advanced Options"
            obj_name = self.advanced_options_widget_name
            options_map = self.advanced_options_map
        else:
            box_name = "Options"
            obj_name = self.options_widget_name
            options_map = self.options_map

        if not options_map[rx_type]:
            # Do not add the option box if the dictionary if empty.
            return

        box = QGroupBox(box_name, self)
        box.setObjectName(obj_name)
        layout = QFormLayout(box)

        for widget_name, widget_opt in options_map[rx_type].items():
            widget = widget_opt['widget']()
            widget.setObjectName(widget_name)
            widget.setToolTip(widget_opt['tip'])

            # Get text from default argument value.
            value = None
            for field in ['run', 'config']:
                if widget_name in args[field]:
                    value = (args[field][widget_name]
                             if args[field][widget_name] is not None else "")
                    break

            # Load textfields
            if widget_opt['widget'] == QLineEdit:
                # Load text using default argument value.
                if value is not None:
                    widget.setText(str(value))

                # Load text with value available on the configuration file.
                if 'config_key' in widget_opt:
                    config_key = widget_opt['config_key']
                    value = rx_info['setup'][
                        config_key] if config_key in rx_info['setup'] else None
                    if value is not None:
                        widget.setText(str(value))

            # Set choices
            if widget_opt['widget'] == QComboBox:
                if 'choices' in widget_opt:
                    widget.addItems(widget_opt['choices'])
                    widget.setEditable(False)
                    # Set the default option based on default argument
                    if value is not None:
                        widget.setCurrentText(str(value))
                else:
                    widget.setPlaceholderText(f"No {widget_name} found")

            # Add validator
            if 'type' in widget_opt and widget_opt['type'] in [float, int]:
                if widget_opt['type'] == float:
                    validator = QDoubleValidator
                else:
                    validator = QIntValidator

                widget.setValidator(validator())

            # Change echo mode
            if 'echo' in widget_opt:
                widget.setEchoMode(widget_opt['echo'])

            # Add reload button
            if 'reload' in widget_opt:
                wrapper = QFrame()
                wrapper_layout = QHBoxLayout(wrapper)
                wrapper_layout.setSpacing(0)
                wrapper_layout.setContentsMargins(0, 0, 0, 0)
                reload_bnt = buttons.ReloadButton()
                reload_bnt.setFixedWidth(30)
                wrapper_layout.addWidget(widget)
                wrapper_layout.addWidget(reload_bnt)
                reload_widget = widget

                # Connect reload button
                if (rx_type == defs.linux_usb_setup_type
                        and widget_name == 'device'):
                    reload_bnt.clicked.connect(lambda: self._run_reload_worker(
                        reload_widget,
                        reload_bnt,
                        callback=self._process_usb_adapters,
                        func=usb.find_adapters))

                if (rx_type == defs.sat_ip_setup_type
                        and widget_name == 'device'):
                    cli_args = copy(args['run'])
                    reload_bnt.clicked.connect(lambda: self._run_reload_worker(
                        reload_widget,
                        reload_bnt,
                        callback=self._process_satip_devices,
                        func=satip.list_devices,
                        args=(Namespace(**cli_args), )))
                    widget.currentTextChanged.connect(
                        self._update_satip_addr_field)

                # Automatically run the reload action
                if not self._no_auto_reload:
                    reload_bnt.click()

                # Add wrapper to the layout: widget + reload button
                layout.addRow(f"{widget_opt['label']}:", wrapper)
                continue

            layout.addRow(f"{widget_opt['label']}:", widget)
        self._layout.addWidget(box)

    def _validate_field_from_widget(self, widget_name, widget_type,
                                    field_type):
        """Validate content type

        Get the input text from the widget and check against a specific type.
        If the input text is valid, return the validated text. Otherwise,
        change the widget border style to indicate an invalid field.

        Args:
            widget_name: Widget name.
            widget_type: Widget type (QLineEdit or QComboBox).
            field_type: Expected type from field content.

        Returns:
            A tuple containing a boolean (True if the content is valid or False
            otherwise) and a string (the validated text if valid or empty
            string otherwise).

        """
        assert (widget_type in [QLineEdit, QComboBox]), "Type not supported"

        is_valid = True
        input_valid = ""

        # Search for the widget in the default options and advanced options box
        for box_name in [
                self.options_widget_name, self.advanced_options_widget_name
        ]:
            box = self.findChild(QGroupBox, box_name)
            assert (box is not None), f"Box {box_name} not found"

            widget = box.findChild(widget_type, widget_name)
            if widget is not None:
                break

        assert (widget is not None), f"Component {widget_name} not found"

        if isinstance(widget, QLineEdit):
            widget_text = widget.text()
        else:
            widget_text = str(widget.currentText())

        if widget_text == "":
            return is_valid, input_valid

        try:
            input_valid = field_type(widget_text)
            widget.setStyleSheet(styles.border_style['normal'])
            # Only validate the ip address but return as string
            if field_type == ip_address:
                input_valid = widget_text
        except ValueError:
            widget.setStyleSheet(styles.border_style['error'])
            messagebox.Message(self, title="Invalid field", msg="")
            input_valid = ""
            is_valid = False

        return is_valid, input_valid

    def _get_options(self, rx_key, args):
        """Extract input data from widgets

        Args:
            rx_key (str): Receiver identification key
            args (dict): Dictionary with the default arguments for receiver
                         launch and configuration

        """
        all_options_valid = False

        all_options = self.options_map[rx_key]
        if self.advanced_options_map[rx_key]:
            # Add advanced options
            all_options.update(self.advanced_options_map[rx_key])

        for key, options in all_options.items():
            if options['widget'] in [QLineEdit, QComboBox]:
                is_valid, value = self._validate_field_from_widget(
                    widget_name=key,
                    widget_type=options['widget'],
                    field_type=options['type'])
            elif options['widget'] == QCheckBox:
                # Checkboxes can only have two states (checked or not
                # checked), and both are valid. So, we don't need to validate.
                is_valid = True
                component = self.findChild(QCheckBox, key)
                value = component.isChecked()
            else:
                raise ValueError(f"Widget {options['widget']} not supported \
                        in get options method")

            if not is_valid:
                # If one option is not valid, return early.
                return all_options_valid

            if value == "":
                continue

            # Special rule for USB receiver
            if rx_key == defs.linux_usb_setup_type:
                if key == "device":
                    adapter, frontend = self._parse_usb_adapters(value)
                    for field in ['run', 'config']:
                        args[field]['adapter'] = adapter
                        args[field]['frontend'] = frontend
                    continue

            if rx_key == defs.sat_ip_setup_type:
                if key == "device":
                    # Set the host ip on the addr field
                    args['run']['addr'] == value

            for field in ['run', 'config']:
                if key in args[field]:
                    args[field][key] = value

        # If it get here all options are valid.
        all_options_valid = True
        return all_options_valid

    def _convert_ns_to_dict(self, args):
        """Convert Namespace object to dictionary"""
        for k, v in args.items():
            args[k] = vars(v)

        return args

    def _convert_dict_to_ns(self, args):
        """Convert dictionary to Namespace object"""
        for k, v in args.items():
            args[k] = Namespace(**v)

        return args

    def _remove_options_box(self, box_name):
        rx_opt_box = self.findChild(QGroupBox, box_name)
        if rx_opt_box:
            rx_opt_box.deleteLater()

    def _parse_usb_adapters(self, value):
        """Parse the USB adapter and frontend number

        This function expects the following value pattern:

            vendor model: Adapter <N_ADAPTER>, Frontend <N_FRONTEND>

        """
        adapter_and_frontend = value.split(':')[-1]
        adapter_and_frontend_split = adapter_and_frontend.split(',')
        n_adapter = adapter_and_frontend_split[0].split()[1]
        n_frontend = adapter_and_frontend_split[1].split()[1]

        return n_adapter, n_frontend

    def _process_usb_adapters(self, res, error):
        box = self.findChild(QGroupBox, self.options_widget_name)
        assert (box is not None), "Box not found"
        widget = box.findChild(QComboBox, "device")
        assert (widget is not None), "Component device not found"

        widget.clear()  # Remove all itens
        widget.setPlaceholderText("No devices found")

        if error is not None:
            if error[1].code != 1:
                messagebox.Message(parent=self,
                                   title="TBS Adapters Error",
                                   msg=error[2],
                                   msg_type="warning")
            return

        labels = ["vendor", "model", "adapter", "frontend"]
        for device in res:
            # For each device, check if all information is present. If not,
            # mark the device as invalid and do not add it as an option to the
            # user.
            invalid_device = False
            for label in labels:
                if label not in device:
                    invalid_device = True
                    break

            if invalid_device:
                continue

            vendor = device["vendor"]
            model = device["model"]
            adapter = device["adapter"]
            frontend = device["frontend"]
            item = f"{vendor} {model}: Adapter {adapter}, Frontend {frontend}"

            widget.addItem(item)

        if widget.count() > 0:
            widget.setPlaceholderText('')

    def _process_satip_devices(self, res, error):
        box = self.findChild(QGroupBox, self.options_widget_name)
        assert (box is not None), "Box not found"
        widget = box.findChild(QComboBox, "device")
        assert (widget is not None), "Component device not found"

        widget.clear()  # Remove all itens
        widget.setPlaceholderText("No devices found")

        if res is None:
            return

        for device in res:
            widget.addItem(device['host'])

        if widget.count() > 0:
            widget.setPlaceholderText('')

    def _update_satip_addr_field(self, addr):
        box = self.findChild(QGroupBox, self.options_widget_name)
        assert (box is not None), "Box not found"
        widget = box.findChild(QLineEdit, "addr")
        assert (widget is not None), "Component device not found"

        if addr is not None:
            try:
                ip_address(addr)
            except ValueError:
                return

            widget.setText(str(addr))

    def _update_reload_widgets(self, widget, bnt):
        widget.setPlaceholderText('Searching...')
        widget.update()
        bnt.setDisabled(True)

    def _run_reload_worker(self, widget, button, callback, func, args=()):
        thread = QThread()
        worker = ReloadWorker(func=func, args=args)
        worker.moveToThread(thread)

        thread.started.connect(
            lambda: self._update_reload_widgets(widget, button))
        thread.started.connect(worker.run)
        worker.sig_finished.connect(callback)
        worker.sig_finished.connect(thread.quit)
        worker.sig_finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(lambda: button.setDisabled(False))

        self._thread = thread
        self._worker = worker

        thread.start()

    def add_rx_options(self, rx_config):
        """Add receiver options in the screen

        Add the correct receiver options based on the current receiver
        configuration loaded.

        Args:
            config (dict): Dictionary with receiver configuration.

        """
        # Remove the receiver options box if already exists
        self._remove_options_box(self.options_widget_name)
        self._remove_options_box(self.advanced_options_widget_name)

        args = rx_config['cli_args']

        args = self._convert_ns_to_dict(args)
        self._add_options(rx_config, args)
        self._add_options(rx_config, args, options='advanced')
        args = self._convert_dict_to_ns(args)

    def get_rx_options(self, rx_config):
        """Get receiver options from from layout components

        Get the options set by the user from the screen components. If the
        options are valid, set (in-place) into the args object.

        Args:
            rx_key (str): Receiver identification key
            args (Namespace): Namespace object with the default rx arguments

        """
        # Convert namespace to dictionary to facilitate manipulation. After
        # getting the user options, convert it back to namespace object.
        args = rx_config['cli_args']
        rx_type = rx_config['info']['setup']['type']
        args = self._convert_ns_to_dict(args)
        valid = self._get_options(rx_type, args)
        args = self._convert_dict_to_ns(args)

        return valid

    def update_rx_info(self, rx_config):
        assert (isinstance(rx_config, dict))
        info = rx_config['info']
        self.rx_model.setText(info["setup"]["model"])
        self.rx_type.setText(info["setup"]["type"])

    def disable_components(self, disable=True):
        self.setDisabled(disable)


class ReloadWorker(QObject):

    sig_finished = Signal(object, object)

    def __init__(self, func, args):
        super().__init__()

        self.args = args
        self.func = func

    def run(self):
        error = None
        res = None

        try:
            # Add a 1s delay to ensure the user can see the visual feedback
            time.sleep(1)
            res = self.func(*self.args)
        except:  # noqa: ignore=E722
            exctype, value = sys.exc_info()[:2]
            error = (exctype, value, traceback.format_exc())
        finally:
            self.sig_finished.emit(res, error)
