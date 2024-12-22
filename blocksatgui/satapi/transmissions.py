import logging

from blocksatcli import util

from .. import qt
from ..components import buttons, page, table
from ..satapi.dialogs import ManageOrderDialog, calc_bid_per_byte
from .api import SatApi

logger = logging.getLogger(__name__)

TX_TABLE_IDX = 5  # Transmission ID column


class ManageTxDelegate(qt.QStyledItemDelegate):

    sig_tx_selected = qt.Signal(bool)
    sig_manage_tx = qt.Signal(str)
    sig_unselect_tx = qt.Signal()

    def __init__(self, parent: table.Table, api: SatApi):
        super().__init__(parent)
        self._table = parent
        self.api = api
        self.api.tx_logs_cache.load()

    def paint(self, painter, option, index):
        self.parent().openPersistentEditor(index)
        super().paint(painter, option, index)

    def createEditor(self, parent, option, index):
        widget = qt.QWidget(parent)
        layout = qt.QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(qt.Qt.AlignCenter)
        check_box = qt.QRadioButton(widget)
        check_box.clicked.connect(
            lambda: self._select_row(check_box, index.row()))
        self.sig_unselect_tx.connect(lambda: check_box.setChecked(False))
        layout.addWidget(check_box)
        return widget

    def _select_row(self, check_box, row):
        if not check_box.isChecked():
            self._table.clearSelection()
            self.sig_tx_selected.emit(False)
            return
        self.sig_unselect_tx.emit()
        self._table.selectRow(row)
        check_box.setChecked(True)
        self.sig_manage_tx.emit(self._table.get_data(row, TX_TABLE_IDX))
        self.sig_tx_selected.emit(True)


class TransmissionsView(page.Page):

    def __init__(self):
        super().__init__(name="satapi-transmissions", topbar_enabled=False)

        self._layout.setContentsMargins(10, 5, 5, 10)
        self.default_page = self._gen_default_page()
        self.transmissions_page = self._gen_transmissions_page()
        self.add_page(self.default_page, "default")
        self.add_page(self.transmissions_page, "transmissions")
        self.update_default_page()
        self.switch_page("transmissions")
        self._data_uuid = []

    def _gen_default_page(self):
        self._message = qt.QLabel("Offline Mode")
        self._message.setProperty("qssClass", "text_bold__gray")
        self._details = qt.QLabel("Cannot manage transmissions")
        self._details.setProperty("qssClass", "text_italic__gray")

        viewer, layout = page.get_widget('default-tab')
        layout.addWidget(self._message, alignment=qt.Qt.AlignCenter)
        layout.addWidget(self._details, alignment=qt.Qt.AlignCenter)
        return viewer

    def _gen_transmissions_page(self):
        viewer, layout = page.get_widget('transmissions-tab')
        layout.addWidget(self._gen_options(), alignment=qt.Qt.AlignRight)
        layout.addWidget(self._gen_table())
        layout.addWidget(self._gen_buttons_box())
        return viewer

    def _gen_options(self):
        self.tx_options = qt.QComboBox()
        self.tx_options.addItems(["Queued", "Sent", "Pending Payment"])
        frame, layout = page.get_widget('options-box', 'frame', 'hbox', False)
        layout.addWidget(qt.QLabel("Show:"))
        layout.addWidget(self.tx_options)
        return frame

    def _gen_table(self):
        self.table_title = qt.QLabel("Queued Messages".upper())
        self.table_title.setProperty("qssClass", "metric-card__title")
        self.table = table.Table(
            behavior="fit",
            header=[
                "", "Created (UTC)", "Status", "Bid/Byte (msat)",
                "Message Size", "Transmission ID"
            ],
            alignment=[
                int(qt.Qt.AlignCenter),
                int(qt.Qt.AlignLeft | qt.Qt.AlignVCenter),
                int(qt.Qt.AlignLeft | qt.Qt.AlignVCenter),
                int(qt.Qt.AlignCenter),
                int(qt.Qt.AlignCenter),
                int(qt.Qt.AlignLeft | qt.Qt.AlignVCenter),
            ],
        )
        # Set the transmission ID column as stretchable. All other columns
        # will be resized to fit the table width.
        header = self.table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(TX_TABLE_IDX, qt.QHeaderView.Stretch)

        frame, layout = page.get_widget('table-box', 'frame', 'vbox', False)
        layout.addWidget(self.table_title)
        layout.addWidget(self.table)
        return frame

    def _gen_buttons_box(self):
        self.manage_tx_bnt = buttons.MainButton("Manage Transmission")
        frame, layout = page.get_widget('buttons-box', 'frame', 'hbox', False)
        layout.setAlignment(qt.Qt.AlignBottom | qt.Qt.AlignCenter)
        layout.addWidget(self.manage_tx_bnt)
        return frame

    def update_table_title(self, title):
        self.table_title.setText(title.upper())

    def update_table_data(self, data, force=False):
        uuids = [x[TX_TABLE_IDX] for x in data]
        if not force and self._data_uuid == uuids:
            return
        if not data:
            self.table.clear()
            self.table.reset_model()
            return
        self.table.set_items(data)
        self.table.sort_items(i_col=0, order="descending")
        self.table.reset_model()
        self._data_uuid = uuids

    def update_default_page(self, on_internet=False, api_valid=False):
        message, details = "", ""
        if on_internet:
            if not api_valid:
                message = "Invalid API"
                details = ("Please, enter a valid API URL to manage "
                           "transmissions")
        else:
            message = "Offline Mode"
            details = "Cannot manage transmissions"

        self._message.setText(message)
        self._details.setText(details)


class Transmissions(qt.QObject):

    def __init__(self, sat_api: SatApi):
        super().__init__()

        self.view = TransmissionsView()
        self.sat_api = sat_api
        self._selected_tx = None
        self._selected_option = None

        self._connect_signals()
        self._add_table_delegate()

    def _connect_signals(self):
        self.view.manage_tx_bnt.clicked.connect(
            lambda: self.manage_transmission())
        self.view.tx_options.currentTextChanged.connect(
            lambda x: self.view.update_table_title(x + " Messages"))
        self.view.tx_options.currentTextChanged.connect(
            lambda: self.view.table.clear())
        self.view.tx_options.currentTextChanged.connect(
            lambda x: self._update_transmissions(x.lower()))

    def _add_table_delegate(self):
        """Add a button to manage the transmission on the table"""
        manage_checkbox_idx = 0  # First column
        delegate = ManageTxDelegate(self.view.table, self.sat_api)
        delegate.sig_manage_tx.connect(self.manage_transmission)
        delegate.sig_tx_selected.connect(self._unset_selected_tx)
        self.view.table.setItemDelegateForColumn(manage_checkbox_idx, delegate)

    def _unset_selected_tx(self, selected):
        self._selected_tx = None if not selected else self._selected_tx

    def _update_transmissions(self, option):
        assert option in ["queued", "sent", "pending payment"]

        def _callback(self, worker):
            if worker.error:
                return

            queue_list = []
            self.sat_api.tx_logs_cache.load()
            for data in worker.result:
                # Skip the transmission if it's not in the cache
                if not self.sat_api.tx_logs_cache.get(data['uuid']):
                    continue
                bid = data['bid'] + data['unpaid_bid']
                ota_size = self.sat_api.calc_ota_msg_len(data['message_size'])
                bid_per_byte = (data['bid_per_byte']
                                or calc_bid_per_byte(bid, ota_size))
                queue_list.append([
                    "",
                    util.format_timestamp(data['created_at']),
                    data['status'].title(),
                    f"{bid_per_byte:.2f}",
                    data['message_size'],
                    data['uuid'],
                ])
            self.view.update_table_data(queue_list,
                                        force=self._selected_option != option)

        status, queue = None, "queued"
        if option == "queued":
            queue = "queued"
        elif option == "sent":
            queue = "sent"
            status = ["sent", "received"]
        elif option == "pending payment":
            queue = status = "pending"
        else:
            raise ValueError(f"Invalid option: {option}")
        self.sat_api.get_order_list(
            status=status,
            queue=queue,
            callback=lambda worker: _callback(self, worker))

    def update_page(self):
        self._selected_option = self.view.tx_options.currentText().lower()
        self._update_transmissions(self._selected_option)

    def manage_transmission(self, tx_id=None):
        tx_id = tx_id or self._selected_tx
        self._selected_tx = tx_id
        auth_token = None
        ln_invoices = []
        if tx_id:
            self.sat_api.tx_logs_cache.load()
            tx = self.sat_api.tx_logs_cache.get(tx_id)
            if tx and 'auth_token' in tx:
                auth_token = tx['auth_token']
            if tx and 'invoices' in tx:
                ln_invoices = tx['invoices']

        dialog = ManageOrderDialog(self.view,
                                   self.sat_api,
                                   tx_id=tx_id,
                                   auth_token=auth_token,
                                   ln_invoices=ln_invoices)
        if tx_id and auth_token:
            dialog._next()  # Skip the first page (order selection)
        dialog.exec_()

        # Update the table after closing the dialog
        self.update_page()
