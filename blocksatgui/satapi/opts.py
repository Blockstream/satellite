import copy
from dataclasses import dataclass
from typing import Dict, Optional, Type, Union

from blocksatcli import defs
from blocksatcli.api.order import ApiChannel

from .. import qt, utils


@dataclass()
class WidgetOptions():
    widget: Type[qt.QWidget]
    label: str
    tip: str
    default: Optional[bool] = None
    placeholder: Optional[str] = None


GroupOptions = Dict[Union[str, int], WidgetOptions]
AdvancedOptions = Dict[str, GroupOptions]

# Advanced options to the send tab
opts_send: AdvancedOptions = {
    'regions': {
        r['region']:
        WidgetOptions(
            widget=qt.QCheckBox,
            label=r['alias'],
            tip=f"Send the message over {r['alias']}.",
            default=True,
        )
        for r in defs.satellites
    },
    'gpg': {
        "recipient":
        WidgetOptions(widget=qt.QComboBox,
                      label="Recipient: ",
                      tip="Public key fingerprint of the desired recipient.",
                      placeholder="Select a recipient"),
        "trust":
        WidgetOptions(
            widget=qt.QCheckBox,
            label="Trust Recipient: ",
            tip="Assume that the recipient\'s public key is fully trusted.",
            default=False),
        "sign":
        WidgetOptions(widget=qt.QCheckBox,
                      label="Sign: ",
                      tip="Sign message in addition to encrypting it.",
                      default=False),
        "sign_key":
        WidgetOptions(widget=qt.QComboBox,
                      label="Sign key: ",
                      tip=("Fingerprint of the private key to be used when "
                           "signing the message."),
                      placeholder="Select a private key"),
        "no_password":
        WidgetOptions(
            widget=qt.QCheckBox,
            label="No Password: ",
            tip="Whether to access the GPG keyring without a password.",
            default=False)
    },
    'format': {
        "send_raw":
        WidgetOptions(
            widget=qt.QCheckBox,
            label="Send raw: ",
            tip=("Send the raw file or text message, i.e., wihout the "
                 "data structure."),
            default=False,
        ),
        "plaintext":
        WidgetOptions(
            widget=qt.QCheckBox,
            label="Plain text: ",
            tip="Send data in plaintext format (no encryption).",
            default=False,
        ),
        "fec":
        WidgetOptions(
            widget=qt.QCheckBox,
            label="FEC: ",
            tip="Send data with forward error correction (FEC) encoding.",
            default=False,
        ),
    }
}

# Advanced options to the listen tab
channels = [
    (ApiChannel.USER.value, "User"),
    (ApiChannel.GOSSIP.value, "Gossip"),
    (ApiChannel.BTC_SRC.value, "Bitcoin"),
    (ApiChannel.ALL.value, "All"),
]
opts_listen: AdvancedOptions = {
    'channels': {
        i:
        WidgetOptions(
            widget=qt.QRadioButton,
            label=name,
            tip=f"Listen to {name} channel.",
            default=True if name == "User" else False,
        )
        for i, name in channels
    },
    'network': {
        "interface":
        WidgetOptions(widget=qt.QComboBox,
                      label="Network Interface: ",
                      tip="Network interface that receives API data.")
    },
    'format': {
        "plaintext":
        WidgetOptions(widget=qt.QCheckBox,
                      label="Plaintext: ",
                      tip=("Do not decrypt messages. Assumes messages are in "
                           "plaintext format."),
                      default=False),
        "save_raw":
        WidgetOptions(
            widget=qt.QCheckBox,
            label="Raw format: ",
            tip=("Save the raw decrypted data while ignoring the existence "
                 "of a data encapsulation structure."),
            default=False),
    },
    'gpg': {
        "sender":
        WidgetOptions(
            widget=qt.QComboBox,
            label="Sender: ",
            tip=("Public key fingerprint of a target sender used to "
                 "filter the incoming messages."),
            placeholder="Select sender",
        ),
        "no_password":
        WidgetOptions(
            widget=qt.QCheckBox,
            label="No Password: ",
            tip="Whether to access the GPG keyring without a password.",
            default=False)
    },
    'save': {
        "no_save":
        WidgetOptions(widget=qt.QCheckBox,
                      label="No Save: ",
                      tip=("Do not save the files decoded from the receiver "
                           "API messages."),
                      default=False),
    }
}


def get_send_opts():
    """Returns the send options"""
    return copy.deepcopy(opts_send)


def get_listen_opts():
    """Returns the listen options"""
    return copy.deepcopy(opts_listen)


def get_opt_widget(opts: WidgetOptions,
                   inline_label=True,
                   obj_name: Optional[str] = None) -> qt.QWidget:
    """Returns the QT widget based on the dictionary of options"""
    if opts.widget == qt.QComboBox or not inline_label:
        widget = opts.widget()
    else:
        widget = opts.widget(opts.label)

    if obj_name is not None:
        widget.setObjectName(obj_name)
    if opts.placeholder is not None and opts.widget == qt.QComboBox:
        widget.setPlaceholderText(opts.placeholder)
    if opts.tip:
        widget.setToolTip(opts.tip)
    if (opts.widget in [qt.QCheckBox, qt.QRadioButton]
            and opts.default is not None):
        widget.setChecked(opts.default)

    opts.widget = widget  # Save reference to the widget
    return widget


def get_group_box(parent,
                  name: str,
                  opts: GroupOptions,
                  layout='form',
                  inline_label=True,
                  obj_name: Optional[str] = None) -> qt.QGroupBox:
    """Returns the QT group box based on the dictionary of options"""
    group_box = qt.QGroupBox(name, parent)
    layout = utils.get_widget_layout(layout)
    group_layout = layout(group_box)
    if obj_name is not None:
        group_box.setObjectName(obj_name)
    for data in opts.values():
        widget = get_opt_widget(data, inline_label=inline_label)

        if layout == qt.QFormLayout:
            if inline_label:
                group_layout.addRow(widget)
            else:
                group_layout.addRow(data.label, widget)
        else:
            group_layout.addWidget(widget)
    return group_box


def get_selected_opts(opts: GroupOptions) -> Dict:
    """Returns the selected options"""
    res = {}
    for label, opt in opts.items():
        widget = opt.widget
        if isinstance(widget, qt.QCheckBox) or isinstance(
                widget, qt.QRadioButton):
            res[label] = widget.isChecked()
        elif isinstance(widget, qt.QComboBox):
            res[label] = widget.currentText() or None
        else:
            raise ValueError(f"Invalid widget type: {type(widget)}")
    return res
