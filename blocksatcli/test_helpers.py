import os
import shutil
import unittest
import uuid

from . import config
from . import defs
from .api.gpg import Gpg, import_bs_pubkey


class TestEnv(unittest.TestCase):
    """Test Environment"""

    def setUp(self):
        self.cfg_name = str(uuid.uuid4())
        self.cfg_dir = os.path.join('/tmp', '.blocksat-test-' + self.cfg_name)

        if not os.path.exists(self.cfg_dir):
            os.makedirs(self.cfg_dir)

        self.gpghome = gpghome = os.path.join(self.cfg_dir, '.gnupg')
        self.gpg = Gpg(gpghome=gpghome)

    def tearDown(self):
        for directory in [self.cfg_dir, self.gpg.gpghome]:
            if os.path.exists(directory):
                shutil.rmtree(directory, ignore_errors=True)


def create_test_setup(cfg_name,
                      cfg_dir,
                      gpghome,
                      gen_gpg_key=False,
                      mon_api_registered=False,
                      mon_api_has_password=False,
                      mon_api_gen_password=False):
    """Create test setup with receiver configuration file and GPG keys

    This function creates a receiver configuration file and GPG keys for
    testing purposes. It can also generate the necessary information to mimic
    a receiver that has successfully passed the monitoring API registration
    (using the 'mon_api_registered') and password generation (using the
    'mon_api_gen_password') processes. For the password generation process, if
    the only necessary information is the monitoring API flag 'has_password',
    you can use the 'mon_api_has_password' option to set the flag instead of
    going into the complete process of generating a local file with the
    monitoring API password.

    Args:
        cfg_name (str): Name of the configuration file.
        cfg_dir (str): Directory to use for configuration files.
        gpghome (str): GnuPG home directory.
        gen_gpg_key (bool, optional): Whether to generate a GPG key pair.
            Defaults to False.
        mon_api_registered (bool, optional): Whether to flag that the receiver
            is already registered in the monitoring API on the configuration
            file. Defaults to False.
        mon_api_has_password (bool, optional): Whether to set the has_password
            flag into the configuration file. This flag indicates that a
            password is already set for reporting metrics to the Monitoring API
            using the non-GPG authentication method. Defaults to False.
        mon_api_gen_password (bool, optional): Whether to generate a local file
            with the monitoring API's encrypted password. Defaults to False.
    """
    test_info = {
        "sat": defs.get_satellite_def('G18'),
        "setup": defs.get_demod_def('Selfsat', 'IP22'),
        "lnb": defs.get_lnb_def('Selfsat', 'Integrated LNB')
    }
    test_info['setup']['antenna'] = defs.get_antenna_def('IP22')

    # Add monitoring information if registered
    if mon_api_registered:
        test_info['monitoring'] = {
            'registered': True,
            'uuid': 'test-uuid',
            'fingerprint': 'test-fingerprint',
            'has_password': mon_api_has_password
        }

    # Create and update the uuid and fingerprint if using real GPG key
    if gen_gpg_key:
        gpg = Gpg(gpghome)
        gpg.create_keys("Test", "test@test.com", "", "test")
        fingerprint = gpg.get_default_public_key()['fingerprint']
        # Some calls would fail on the _is_gpg_keyring_set assertion if the
        # Blockstream pubkey was not imported
        import_bs_pubkey(gpg)

        if mon_api_registered:
            test_info['monitoring']['fingerprint'] = fingerprint

    # Generate encrypted file with monitoring api password
    if mon_api_gen_password and gen_gpg_key:
        api_cfg_dir = os.path.join(cfg_dir, 'monitoring_api')
        if not os.path.exists(api_cfg_dir):
            os.mkdir(api_cfg_dir)

        enc_password = gpg.encrypt("test-password", fingerprint).data
        enc_pwd_file = os.path.join(api_cfg_dir,
                                    f'{fingerprint}_{cfg_name}_pwd.gpg')
        with open(enc_pwd_file, 'wb') as fd:
            fd.write(enc_password)

        test_info['monitoring']['has_password'] = True

    config.write_cfg_file(cfg_name, cfg_dir, test_info)

    return test_info
