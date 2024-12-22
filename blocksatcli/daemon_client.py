import hashlib
import os
import subprocess
import time

try:
    import dbus
except ImportError:
    pass


class DaemonClient():
    service_name = "com.blockstream.satellite.runner"
    path_name = "/com/blockstream/satellite/runner"
    interface_name = "com.blockstream.satellite.runner"

    def __init__(self, user_home, logger=None):
        self.user_home = user_home
        self.logger = logger

        try:
            self.dbus = dbus.SystemBus()
        except NameError:
            self.dbus = None

        if self.dbus is None and self.logger is not None:
            self.logger.info("Dbus module not available. Unable to "
                             "comunicate with blocksat daemon application.")

    def _gen_token(self, pid):
        """Generate token for communication with blocksatd

        The token is the sha256 hash obtained from the concatenation of the
        secret (at ~/.blocksat/.secret) and the client (blocksat CLI or GUI)
        process identifier (PID).

        Args:
            pid (int): Client PID.

        Returns:
            str: Token as a hex string. None if the secret file does not exist.

        """
        cfg_dir = os.path.join(self.user_home, ".blocksat")
        cfg = os.path.join(cfg_dir, ".secret")
        if not os.path.exists(cfg):
            return

        with open(cfg, 'r') as f:
            secret = f.read()

        data = f"{secret}-{pid}".encode()
        token = hashlib.sha256(data).hexdigest()

        return token

    def send(self,
             cmd,
             cwd=None,
             env=None,
             stdout=None,
             stderr=None,
             check=False):
        """Send a command to be executed by Blocksat daemon

        Args:
            cmd (list): Command to be executed on Blocksat daemon.
            cwd (str): Working directory.
            env (dict): Environment variables.
            stdout (int): Stdout option.
            stderr (int): Stderr option.
            check (bool): Whether to check the process exit code.

        """
        if self.dbus is None:
            return

        service = self.dbus.get_object(self.service_name, self.path_name)
        proxy = dbus.Interface(service, dbus_interface=self.interface_name)
        pid = str(os.getpid())
        token = self._gen_token(pid)

        if token is None:
            if self.logger:
                self.logger.error(
                    "Daemon token is missing. Unable to "
                    "communicate with blocksat daemon application")
            return

        # Process the argument accordingly to D-Bus daemon
        cwd = '' if cwd is None else cwd
        stdout = 0 if stdout is None else stdout
        stderr = 0 if stderr is None else stderr
        env = {} if env is None else env

        req_id = int(proxy.run(token, cmd, cwd, env, stdout, stderr))

        while True:
            try:
                req_status = proxy.status(req_id)
            except dbus.exceptions.DBusException as e:
                req_status = ["Error", -1, '', e]

            req_message = str(req_status[0])
            if req_message != "Running":
                break

            time.sleep(2)

        res = subprocess.CompletedProcess(args=cmd,
                                          returncode=int(req_status[1]),
                                          stdout=str(req_status[2]).encode(),
                                          stderr=str(req_status[3]).encode())

        if check:
            res.check_returncode()

        return res

    def is_running(self):
        """Check if Blocksat daemon is running"""
        connected = False
        if self.dbus is None:
            return connected

        try:
            self.dbus.get_object(self.service_name, self.path_name)
            connected = True
        except dbus.exceptions.DBusException:
            pass

        return connected
