import copy
from unittest.mock import ANY, patch

from pytest import mark

from blocksatcli import defs
from blocksatgui import qt
from blocksatgui.satapi import opts
from blocksatgui.satapi.api import SatApi
from blocksatgui.satapi.dialogs import BidDialog
from blocksatgui.satapi.listen import Listen
from blocksatgui.satapi.satapi import SatApiPage
from blocksatgui.satapi.send import Send
from blocksatgui.tests.conftest import pytestqt


@pytestqt
class TestSatApiMainPage:

    def test_pages_added_to_stack(self, qtbot, sat_api):
        """Test if all pages are added to the API tab"""
        satapi_page = SatApiPage(sat_api)
        qtbot.addWidget(satapi_page.view)
        pages = satapi_page.view.stack.stacked_area
        assert (pages.count() == 5)
        assert (pages.widget(0).objectName() == "satapi-overview")
        assert (pages.widget(1).objectName() == "satapi-send")
        assert (pages.widget(2).objectName() == "satapi-listen")
        assert (pages.widget(3).objectName() == "satapi-transmissions")
        assert (pages.widget(4).objectName() == "satapi-settings")


@pytestqt
class TestSapApiSendPage:

    expected_opts = {
        'regions': [0, 2, 3, 4, 5],
        'recipient': None,
        'trust': False,
        'sign': False,
        'sign_key': None,
        'no_password': False,
        'send_raw': False,
        'plaintext': False,
        'fec': False
    }

    def test_displayed_content(self, qtbot, sat_api):
        """Test displayed content based on emitted signals"""
        send_page = Send(sat_api)
        qtbot.addWidget(send_page.view)

        def get_current_page_name():
            return send_page.view.stack.get_current_page().objectName()

        assert (get_current_page_name() == "default-tab")

        # Manually switch to send page
        send_page.view.switch_page("send")
        assert (get_current_page_name() == "send-tab")

        # It should switch back to default page if no internet is available
        # or the API URL is invalid.
        sat_api.config_manager.set_on_internet(False)
        assert (get_current_page_name() == "default-tab")
        assert (send_page.view._message.text() == "Offline Mode")
        assert (send_page.view._details.text() == "Cannot send messages")

        sat_api.config_manager.set_on_internet(True)
        assert (get_current_page_name() == "default-tab")
        assert (send_page.view._message.text() == "Invalid API")
        assert (send_page.view._details.text() ==
                "Please, enter a valid API URL to send messages")

        # It should switch to the send page if internet is available and
        # the API URL is valid.
        sat_api.config_manager.set_api_valid(True)
        assert (get_current_page_name() == "send-tab")

    @patch.object(SatApi, 'send')
    @patch.object(BidDialog, 'get_bid')
    @patch.object(BidDialog, 'exec_')
    def test_send_plaintext_message(self, mock_dialog_exec, mock_get_bid,
                                    mock_satapi_send, qtbot, sat_api):
        """Test if send method is called correctly"""
        mock_get_bid.return_value = 1000
        mock_dialog_exec.return_value = True  # Accept bid

        send_page = Send(sat_api)
        qtbot.addWidget(send_page.view)

        send_page.view.message.setPlainText("message")
        plaintext = send_page.view.advanced_opts['format']['plaintext'].widget
        plaintext.setChecked(True)
        send_page.send_message()

        expected_opts = copy.deepcopy(self.expected_opts)
        expected_opts['plaintext'] = True
        mock_satapi_send.assert_called_once_with(data="message",
                                                 is_file=False,
                                                 bid=1000,
                                                 callback=ANY,
                                                 **expected_opts)

    @patch('blocksatgui.components.messagebox.Message')
    def test_send_message_fails_with_empty_message(self, mock_messagebox,
                                                   qtbot, sat_api):
        send_page = Send(sat_api)
        qtbot.addWidget(send_page.view)
        send_page.view.message.setPlainText("")  # Empty message
        send_page.send_message()
        mock_messagebox.assert_called_once_with(
            parent=send_page.view,
            title="No data to send",
            msg="Please, enter a message or select a file.",
            msg_type="info")

    def test_toggle_options_visibility(self, qtbot, sat_api):
        """Test if advanced options are shown/hidden correctly"""
        send_page = Send(sat_api)
        qtbot.addWidget(send_page.view)

        # Advanced options should be hidden by default
        assert (send_page.view.advanced_options_box.isHidden() is True)
        assert (send_page.view.show_advanced_options.text() ==
                "Show Advanced Options ►")

        # Click to show advanced options
        qtbot.mouseClick(send_page.view.show_advanced_options,
                         qt.Qt.LeftButton)
        assert (send_page.view.advanced_options_box.isHidden() is False)
        assert (send_page.view.show_advanced_options.text() ==
                "Hide Advanced Options ▼")

        # Click to hide advanced options
        qtbot.mouseClick(send_page.view.show_advanced_options,
                         qt.Qt.LeftButton)
        assert (send_page.view.advanced_options_box.isHidden() is True)
        assert (send_page.view.show_advanced_options.text() ==
                "Show Advanced Options ►")

    @mark.parametrize("region", [r["region"] for r in defs.satellites])
    def test_region_options(self, region, qtbot, sat_api):
        """Test if regions are selected correctly"""
        send_page = Send(sat_api)
        qtbot.addWidget(send_page.view)

        # All regions are selected by default
        expected_opt = copy.deepcopy(self.expected_opts['regions'])
        regions_opt = send_page.view.get_advanced_opts()['regions']
        assert (regions_opt == expected_opt)

        # Remove a region by unchecking it
        regions_box = send_page.view.advanced_opts['regions']
        region_widget = regions_box[region].widget
        region_widget.setChecked(False)
        expected_opt.remove(region)
        regions_opt = send_page.view.get_advanced_opts()['regions']
        assert (regions_opt == expected_opt)

    @mark.parametrize("option", ['send_raw', 'plaintext', 'fec'])
    def test_format_options(self, option, qtbot, sat_api):
        """Test if format options are selected correctly"""
        send_page = Send(sat_api)
        qtbot.addWidget(send_page.view)
        format_box = send_page.view.advanced_opts['format']

        # Default options
        assert (send_page.view.get_advanced_opts()[option] ==
                self.expected_opts[option])

        # Select it
        widget = format_box[option].widget
        widget.setChecked(True)
        assert (send_page.view.get_advanced_opts()[option] is True)

    def test_gpg_options(self, qtbot, sat_api):
        """Test if GPG options are selected correctly"""
        send_page = Send(sat_api)
        qtbot.addWidget(send_page.view)
        gpg_box = send_page.view.advanced_opts['gpg']

        for opt in ['trust', 'sign', 'no_password']:
            # Default options
            assert (send_page.view.get_advanced_opts()[opt] ==
                    self.expected_opts[opt])

            # Select it
            widget = gpg_box[opt].widget
            widget.setChecked(True)
            assert (send_page.view.get_advanced_opts()[opt] is True), opt

        # Test Sign key
        sat_api.sig_gpg_privkeys.emit([{
            'uids': 'uid1',
            'fingerprint': 'priv-fp1'
        }, {
            'uids': 'uid2',
            'fingerprint': 'priv-fp2'
        }])
        sign_key = gpg_box['sign_key'].widget
        assert (sign_key.count() == 2)
        sign_key.setCurrentIndex(0)  # Select first key
        assert (send_page.view.get_advanced_opts()['sign_key'] == 'priv-fp1')

        # Test Recipient
        sat_api.sig_gpg_pubkeys.emit([{
            'uids': 'uid1',
            'fingerprint': 'pub-fp1'
        }, {
            'uids': 'uid2',
            'fingerprint': 'pub-fp2'
        }])
        recipient = gpg_box['recipient'].widget
        assert (recipient.count() == 2)
        recipient.setCurrentIndex(1)  # Select second key
        assert (send_page.view.get_advanced_opts()['recipient'] == 'pub-fp2')


@pytestqt
class TestSapApiListenPage:

    expected_opts = {
        'channel': 1,
        'no_save': False,
        'plaintext': False,
        'save_raw': False,
        'no_password': False,
        'interface': None,
        'sender': None
    }

    def test_displayed_content(self, qtbot, sat_api):
        """Test displayed content based on emitted signals"""
        listen_page = Listen(sat_api)
        qtbot.addWidget(listen_page.view)

        def get_current_page_name():
            return listen_page.view.stack.get_current_page().objectName()

        # Listen page should be initialized with default page
        assert (get_current_page_name() == "default-tab")

        # Manually switch to listen page
        listen_page.view.switch_page("listen")
        assert (get_current_page_name() == "listen-tab")

    def test_toggle_advanced_options_visibility(self, qtbot, sat_api):
        """Test if advanced options are shown/hidden correctly"""
        listen_page = Listen(sat_api)
        qtbot.addWidget(listen_page.view)

        # Advanced options should be hidden by default
        assert (listen_page.view.advanced_options_box.isHidden() is True)
        assert (listen_page.view.show_advanced_options.text() ==
                "Show Advanced Options ►")

        # Click to show advanced options
        qtbot.mouseClick(listen_page.view.show_advanced_options,
                         qt.Qt.LeftButton)
        assert (listen_page.view.advanced_options_box.isHidden() is False)
        assert (listen_page.view.show_advanced_options.text() ==
                "Hide Advanced Options ▼")

        # Click to hide advanced options
        qtbot.mouseClick(listen_page.view.show_advanced_options,
                         qt.Qt.LeftButton)
        assert (listen_page.view.advanced_options_box.isHidden() is True)
        assert (listen_page.view.show_advanced_options.text() ==
                "Show Advanced Options ►")

    @mark.parametrize("channel", [i for i, _ in opts.channels])
    def test_channel_options(self, channel, qtbot, sat_api):
        """Test if channel options are selected correctly"""
        listen_page = Listen(sat_api)
        qtbot.addWidget(listen_page.view)

        # Default options: User channel
        user_channel = listen_page.view.advanced_opts['channels'][1].widget
        assert (user_channel.isChecked() is True)
        assert (listen_page.view.get_advanced_options()['channel'] ==
                self.expected_opts['channel'])

        # Select another channel
        widget = listen_page.view.advanced_opts['channels'][channel].widget
        widget.setChecked(True)
        assert (listen_page.view.get_advanced_options()['channel'] == channel)

        # Make sure that the user channel is not selected anymore, since
        # only one channel can be selected at a time.
        if channel != 1:
            assert (user_channel.isChecked() is False)

    def test_format_options(self, qtbot, sat_api):
        """Test if format options are selected correctly"""
        listen_page = Listen(sat_api)
        qtbot.addWidget(listen_page.view)
        format_box = listen_page.view.advanced_opts['format']

        for opt in ['plaintext', 'save_raw']:
            # Default options
            assert (listen_page.view.get_advanced_options()[opt] ==
                    self.expected_opts[opt])

            # Select it
            widget = format_box[opt].widget
            widget.setChecked(True)
            assert (listen_page.view.get_advanced_options()[opt] is True)

    def test_save_options(self, qtbot, sat_api):
        """Test if save options are selected correctly"""
        listen_page = Listen(sat_api)
        qtbot.addWidget(listen_page.view)
        save_box = listen_page.view.advanced_opts['save']

        # Default option
        assert (listen_page.view.get_advanced_options()['no_save'] ==
                self.expected_opts['no_save'])

        # Select: No save
        no_save = save_box['no_save'].widget
        no_save.setChecked(True)
        assert (listen_page.view.get_advanced_options()['no_save'] is True)

    def test_gpg_options(self, qtbot, sat_api):
        """Test if GPG options are selected correctly"""
        listen_page = Listen(sat_api)
        qtbot.addWidget(listen_page.view)
        gpg_box = listen_page.view.advanced_opts['gpg']

        # Select: No password
        assert (listen_page.view.get_advanced_options()['no_password'] ==
                self.expected_opts['no_password'])
        no_password = gpg_box['no_password'].widget
        no_password.setChecked(True)
        assert (listen_page.view.get_advanced_options()['no_password'] is True)

        # Select: Sender
        sat_api.sig_gpg_pubkeys.emit([{
            'uids': 'uid1',
            'fingerprint': 'pub-fp1'
        }, {
            'uids': 'uid2',
            'fingerprint': 'pub-fp2'
        }])
        sender = gpg_box['sender'].widget
        assert (sender.count() == 2)
        sender.setCurrentIndex(1)  # Select second key
        assert (listen_page.view.get_advanced_options()['sender'] == 'pub-fp2')

    def test_network_options(self, qtbot, sat_api):
        """Test if network options are selected correctly"""
        listen_page = Listen(sat_api)
        qtbot.addWidget(listen_page.view)

        # Default option
        assert (listen_page.view.get_advanced_options()['interface'] ==
                self.expected_opts['interface'])

        listen_page.view.set_network_interfaces(['eth0', 'wlan0', 'lo'], 'lo')
        assert (listen_page.view.get_advanced_options()['interface'] == 'lo')
