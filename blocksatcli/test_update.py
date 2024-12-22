import json
import os
from datetime import datetime
from unittest.mock import patch

from packaging.version import Version

from . import update
from .test_helpers import TestEnv


class TestUpdate(TestEnv):

    def test_cache_file(self):
        update_cache = update.UpdateCache(self.cfg_dir, "blocksat-cli")
        datetime_s = datetime.now()

        # At first, there should be no ".update" file to load. Hence, the cache
        # object should not have any data.
        self.assertFalse(update_cache.data)

        # Save the cache. This step should create the ".update" file.
        update_cache.save()
        self.assertTrue(os.path.exists(update_cache.path))

        # Now load the newly created ".update" file.
        update_cache2 = update.UpdateCache(self.cfg_dir, "blocksat-cli")

        # In this case, the data should be available already.
        self.assertTrue(update_cache2.data)

        # There shouldn't be any update
        self.assertFalse(update_cache2.has_update())

        # The last update check date should be set
        datetime_e = datetime.now()
        assert (update_cache2.last_check() > datetime_s)
        assert (update_cache2.last_check() < datetime_e)

    def test_cache_update_handler(self):
        data = {
            'blocksat-cli': {
                'update': None,
                'last_check': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
            },
            'blocksat-gui': {
                'update': ['2.3.0', '2.3.1'],
                'last_check': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
            }
        }
        temp_file = os.path.join(self.cfg_dir, ".update")
        with open(temp_file, 'w') as fd:
            json.dump(data, fd)

        update_cli = update.UpdateCache(self.cfg_dir, 'blocksat-cli')
        assert (update_cli.has_update() is None)

        update_gui = update.UpdateCache(self.cfg_dir, 'blocksat-gui')
        assert (update_gui.has_update() == ['2.3.0', '2.3.1'])
        assert (update_gui.new_version() == Version("2.3.1"))

        update_blocksat = update.UpdateCache(self.cfg_dir, 'blocksat')
        assert (update_blocksat.has_update() is None)
        self.assertRaises(TypeError, update_blocksat.new_version)

    def test_compatibility_with_old_update_version(self):
        # Backward compatibility: The new version reads the old format and
        # updates it to the new format while parsing the information correctly.
        data = {
            'cli_update': ['2.1.2', '2.4.4'],
            'last_check': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        }
        temp_file = os.path.join(self.cfg_dir, ".update")
        with open(temp_file, 'w') as fd:
            json.dump(data, fd)

        update_cli = update.UpdateCache(self.cfg_dir, 'blocksat-cli')
        cache_keys = list(update_cli.data.keys())
        assert update_cli.has_update() == ['2.1.2', '2.4.4']
        assert 'blocksat-cli' in cache_keys  # new format
        assert update_cli.data['blocksat-cli']['update'] == ['2.1.2', '2.4.4']

        # Forward compatibility: The old version reads the new format and
        # parses the CLI update information correctly.
        assert 'cli_update' in cache_keys  # old format
        assert 'last_check' in cache_keys  # old format
        assert update_cli.data['blocksat-cli']['update'] == update_cli.data[
            'cli_update']
        assert update_cli.data['blocksat-cli'][
            'last_check'] == update_cli.data['last_check']

    @patch('blocksatcli.dependencies.check_python_packages')
    @patch('blocksatcli.update.get_current_package_manager')
    def test_get_package_info(self, mock_manager, mock_python_packages):
        mock_manager.return_value = "pip"
        mock_python_packages.return_value = True
        pkg_info = update.get_package_info('blocksat-cli')
        assert (pkg_info == {'name': 'blocksat-cli', 'manager': 'pip'})

        mock_manager.return_value = "apt"
        mock_python_packages.return_value = True
        pkg_info = update.get_package_info('blocksat-cli')
        assert (pkg_info == {'name': 'blocksat', 'manager': 'apt'})

        mock_manager.return_value = None
        mock_python_packages.return_value = True
        pkg_info = update.get_package_info('blocksat-cli')
        assert (pkg_info is None)

    @patch('blocksatcli.dependencies.runner.run')
    @patch('blocksatcli.update.runner.run')
    def test_parse_upgradable_list_apt(self, mock_runner, mock_update):
        mock_runner.return_value.stdout = (
            'Listing...\n'
            'testpackage/jammy-updates 2:21.1.4-2ubuntu1.7~22.04.1 amd64 '
            '[upgradable from: 21.1.3-2ubuntu2.7]\n'
            'otherpackage/jammy 9.0.140-2ubuntu1.7~22.04.1 amd64 '
            '[upgradable from: 8.9.3-2ubuntu2.7]\n').encode()
        mock_runner.return_value.returncode = 0

        pkg = update.Package('testpackage', 'apt', '21.1.3')
        assert (pkg.is_upgradable())
        assert (pkg.new_version == "21.1.4")

        pkg = update.Package('otherpackage', 'apt', '8.9.3')
        assert (pkg.is_upgradable())
        assert (pkg.new_version == "9.0.140")

        pkg = update.Package('notupgradable', 'apt', '')
        assert (pkg.is_upgradable() is False)
        assert (pkg.new_version is None)

    @patch('blocksatcli.dependencies.runner.run')
    @patch('blocksatcli.update.runner.run')
    def test_parse_upgradable_list_dnf(self, mock_runner, mock_update):
        mock_runner.return_value.stdout = (
            'Last metadata expiration check: 0:48:41 ago on '
            'Fri 05 May 2023 04:45:01 PM -03.\n'
            'testpackage.noarch                    '
            '2:21.1.4-2.fc36                     '
            'updates\n'
            'otherpackage.x86_64                   '
            '9.0.140-1.fc36                    '
            'updates\n').encode()
        mock_runner.return_value.returncode = 0

        pkg = update.Package('testpackage', 'dnf', '21.1.1')
        assert (pkg.is_upgradable())
        assert (pkg.new_version == "21.1.4")

        pkg = update.Package('otherpackage', 'dnf', '9.0.0')
        assert (pkg.is_upgradable())
        assert (pkg.new_version == "9.0.140")

        pkg = update.Package('notupgradable', 'dnf', '8.7.0')
        assert (pkg.is_upgradable() is False)
        assert (pkg.new_version is None)
