import os
import shutil
import uuid
from unittest.mock import Mock

import pytest

from blocksatcli import config, defs, dependencies
from blocksatgui.config import ConfigManager
from blocksatgui.satapi.api import SatApi

skip_qt_test = not dependencies.check_python_packages(["pytest-qt"])
pytestqt = pytest.mark.skipif(skip_qt_test, reason="pytest-qt is required")

# Disable automatic reload on rxoptions.py. By default, the GUI automatically
# runs a worker thread to reload the widget that lists the detected devices
# (i.e., USB and Sat-IP). However, this behavior can produce undesired effects
# when testing high-level components, such as the component that composes the
# entire receive page. For instance, if the test runs faster than the discover
# function, an error can occur if the widget displaying the detected devices is
# removed. Therefore, it is helpful to disable this behavior when testing.
os.environ['BLOCKSAT_NO_AUTO_RELOAD'] = 'True'


@pytest.fixture
def cfg_dir():
    cfg_dir = f"/tmp/test-blocksat-{uuid.uuid4()}"

    if not os.path.exists(cfg_dir):
        os.makedirs(cfg_dir)

    yield cfg_dir

    shutil.rmtree(cfg_dir, ignore_errors=True)


@pytest.fixture
def user_info():
    test_config = {
        "sat": defs.get_satellite_def('G18'),
        "setup": defs.get_demod_def('Novra', 'S400'),
        "lnb": defs.get_lnb_def('GEOSATpro', 'UL1PLL'),
        "freqs": {
            "dl": 11913.4,
            "lo": 10600.0,
            "l_band": 1313.4
        }
    }
    test_config['setup']['netdev'] = 'lo'
    test_config['setup']['rx_ip'] = '192.168.1.2'
    test_config['setup']['antenna'] = defs.get_antenna_def('45cm')
    test_config['lnb']['v1_pointed'] = False

    return test_config


@pytest.fixture
def cfg_file(cfg_dir, user_info):
    cfg_name = "test"
    config.write_cfg_file(cfg_name, cfg_dir, user_info)

    return os.path.join(cfg_dir, cfg_name) + ".json"


@pytest.fixture
def cfg_manager(cfg_dir):
    config_manager = ConfigManager(cfg_dir)
    yield config_manager
    config_manager.deleteLater()


@pytest.fixture
def sat_api(cfg_dir):
    config_manager = ConfigManager(cfg_dir)
    sat_api = SatApi(config_manager)
    sat_api._start_job = Mock()
    yield sat_api
    sat_api.deleteLater()
