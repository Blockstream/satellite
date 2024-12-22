import blocksatcli.instructions

from .components import cards, messagebox
from .qt import (QDialog, QDialogButtonBox, QFrame, QGridLayout, Qt,
                 QTextBrowser, QVBoxLayout, QWidget, Slot)

store_url = "https://store.blockstream.com/product-category/satellite_kits/"
github_satellite_url = "https://github.com/Blockstream/satellite"
online_doc_url = "https://blockstream.github.io/satellite/"
help_url = "https://help.blockstream.com/"
cov_map_url = "https://blockstream.com/satellite/#satellite_network-coverage"


class HelpPage(QWidget):

    help_cards_map = {
        "card_bs_store": {
            "title": "Buy a Satellite Kit",
            "desc": "Visit the Blockstream store and get a satellite kit",
            "bnt_text": "Blockstream store",
            "url": store_url,
            "icon": "blockstream_icon_white"
        },
        "card_satellite_github": {
            "title": "Github Project",
            "desc": "Access the source code of the project",
            "bnt_text": "Satellite project",
            "url": github_satellite_url,
            "icon": "github_icon"
        },
        "card_online_doc": {
            "title": "Documentation",
            "desc": "See the full documentation online",
            "bnt_text": "Go to documentation",
            "url": online_doc_url,
            "icon": "doc"
        },
        "card_offline_doc": {
            "title": "Instructions",
            "desc": "Open offline instructions to set up your receiver",
            "bnt_text": "Open instructions",
            "url": None,
            "icon": "instructions"
        },
        "card_bs_help": {
            "title": "Help",
            "desc": "Get help from the Satellite support team",
            "bnt_text": "Get support",
            "url": help_url,
            "icon": "help_icon"
        },
        "card_cov_map": {
            "title": "Coverage Map",
            "desc": "Check which satellite covers your location",
            "bnt_text": "Check coverage map",
            "url": cov_map_url,
            "icon": "globe_icon"
        }
    }

    def __init__(self):

        super().__init__()

        vbox = QVBoxLayout(self)
        wrapper = QFrame(self)
        vbox.addWidget(wrapper)

        self.grid = QGridLayout(wrapper)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setHorizontalSpacing(15)
        self.grid.setVerticalSpacing(15)
        self.grid.setAlignment(Qt.AlignHCenter)

        self._add_widgets()
        self._connect_signals()

        self.info = None

    def _add_widgets(self):

        cards_size = (250, 230)
        shadow_effect = False
        max_n_columns = 3

        n_row = -1
        n_col = 0
        for card_key, card_opts in self.help_cards_map.items():
            if n_col % max_n_columns == 0:
                n_row += 1
                n_col = 0

            component = cards.InfoCard(title=card_opts['title'],
                                       description=card_opts['desc'],
                                       bnt_text=card_opts['bnt_text'],
                                       obj_name=card_key,
                                       url=card_opts['url'],
                                       height=cards_size[0],
                                       width=cards_size[1],
                                       shadow=shadow_effect,
                                       icon=card_opts['icon'])

            self.grid.addWidget(component, n_row, n_col)
            n_col += 1

    def _connect_signals(self):
        # Connect the instructions card
        card = self.findChild(cards.InfoCard, "card_offline_doc")
        card.sig_clicked.connect(self.callback_open_instructions)

    @Slot()
    def callback_open_instructions(self):

        if self.info is not None:
            window = InstructionsDialog(self, self.info)
            window.show()
        else:
            messagebox.Message(
                parent=self,
                title="Receiver configuration not found",
                msg=("Please go to the Settings page and generate "
                     "a receiver configuration."),
                msg_type="info")

    def callback_get_receiver_info(self, rx_config):
        if not rx_config:
            self.info = None
            return
        self.info = rx_config['info']


class InstructionsDialog(QDialog):

    def __init__(self, parent=None, info=None):
        super().__init__(parent)

        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        self.setModal(False)
        self._add_widgets()

        self.info = info
        self.html = ""

        # Overwrite print function
        blocksatcli.instructions._print = self._to_html

        blocksatcli.instructions.print_rx_instructions(info, gui=True)
        blocksatcli.instructions.print_next_steps(gui=True)
        self.inst_text.setText(self.html)

        self.adjustSize()

    def _add_widgets(self):
        vbox = QVBoxLayout(self)
        vbox.setContentsMargins(20, 10, 20, 10)

        bnt = QDialogButtonBox()
        bnt.setStandardButtons(QDialogButtonBox.Ok)
        bnt.clicked.connect(self.accept)

        self.inst_text = QTextBrowser()
        self.inst_text.setOpenExternalLinks(True)

        vbox.addWidget(self.inst_text)
        vbox.addWidget(bnt)

    def _to_html(self, text, style='paragraph', end_prompt=False, **kwards):

        if style == "header":
            self.html += f"<h2 style='text-align': center;> {text} </h2>"
        elif style == "subheader":
            self.html += f"<h3> {text} </h3>"
        elif style == "item":
            self.html += f"<ul><li> {text} </li></ul>"
        elif style == "code":
            self.html += f"<pre> {text} </pre>"
        elif style == "url":
            self.html += (
                "<a href={0} style=\"color: #358de5\">{0}</a>\n".format(text))
        else:
            self.html += f"<p>{text} </p>"

        if end_prompt:
            self.html += "<hr>"
