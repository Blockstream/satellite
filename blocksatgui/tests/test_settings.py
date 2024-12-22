from blocksatgui.config import ConfigManager
from blocksatgui.settings import Settings
from blocksatgui.tests.conftest import pytestqt


@pytestqt
class TestTrayIconConfiguration():

    def test_enable_disable_tray_icon(self, qtbot, cfg_dir):
        """Test enabling/disabling of the system tray icon

        The settings page emits the signal requesting to enable or disable the
        tray icon and saves the selected option to cache.

        """

        def check_emitted_type(status):
            assert (status is not None)
            assert (isinstance(status, bool))
            return True

        config_manager = ConfigManager(cfg_dir=cfg_dir)
        settings_page = Settings(cfg_manager=config_manager)
        qtbot.addWidget(settings_page.view)

        # Click on the tray icon to enable it
        with qtbot.wait_signal(settings_page.sig_toggle_tray_icon,
                               check_params_cb=check_emitted_type):
            settings_page.view.tray_icon.trigger()
            assert (config_manager.gui_cache.get('view.tray_icon'))

        # Click to disable it
        with qtbot.wait_signal(settings_page.sig_toggle_tray_icon,
                               check_params_cb=check_emitted_type):
            settings_page.view.tray_icon.trigger()
            assert (not config_manager.gui_cache.get('view.tray_icon'))
