#!/usr/bin/env python3

import hashlib
import logging
import os
import pwd
import signal
import subprocess
import sys

try:
    from PySide6.QtCore import QCoreApplication, QTimer
    APP_TYPE = "qt"
except (ImportError, ModuleNotFoundError):
    try:
        from PySide2.QtCore import QCoreApplication, QTimer
        APP_TYPE = "qt"
    except (ImportError, ModuleNotFoundError):
        from gi.repository import GLib
        APP_TYPE = "glib"

import dbus
import dbus.mainloop.glib
import dbus.service

POLKIT_SERVICE = "org.freedesktop.PolicyKit1"
POLKIT_PATH = "/org/freedesktop/PolicyKit1/Authority"
POLKIT_INTERFACE = "org.freedesktop.PolicyKit1.Authority"
BLOCKSATD_SERVICE = "com.blockstream.satellite.runner"
BLOCKSATD_PATH = "/com/blockstream/satellite/runner"

logger = logging.getLogger("blocksatd")
fmt = "%(asctime)s %(levelname)-8s %(name)s %(message)s"
logging.basicConfig(stream=sys.stdout, level=logging.INFO, format=fmt)
fh = logging.FileHandler("/var/log/blocksatd.log")
fh.setLevel(logging.INFO)
fh.setFormatter(logging.Formatter(fmt))
logger.addHandler(fh)

allowed_cmds = [
    "apt",
    "dnf",
    "yum",
    "sysctl",
    "systemctl",
    "nmcli",
    "ip",
    "netplan",
    "ifup",
    "rm",
    "echo",
    "grep",
    "dpkg",
    "git",
    "make"
    "sed",
    "tar",
    "iptables",
    "firewall-cmd",
    "dvbnet",
    "install",
    "mv",
    "mkdir",
]


class Runner(dbus.service.Object):

    def __init__(self, conn=None, object_path=None, bus_name=None):
        super().__init__(conn, object_path, bus_name)

        self.requests = {}
        self.polkit = PolicyKit(dbus=DBus('system'))

    def _get_sender_pid(self, sender, conn):
        dbus_info = dbus.Interface(
            conn.get_object("org.freedesktop.DBus",
                            "/org/freedesktop/DBus/Bus", False),
            "org.freedesktop.DBus")
        pid = dbus_info.GetConnectionUnixProcessID(sender)
        return int(pid)

    def _get_uid_from_pid(self, pid):
        """Get User ID based on the process ID"""
        p_status = f"/proc/{pid}/status"

        if not os.path.exists(p_status):
            return

        with open(p_status, 'r') as fd:
            status = fd.read()

        for line in status.splitlines():
            if "Uid" in line:
                uid = line.split()[1]
                try:
                    uid_int = int(uid)
                except ValueError:
                    uid_int = None

                return uid_int

    def _validate_token(self, pid, rec_token):
        """Validate received token"""
        user_id = self._get_uid_from_pid(pid)
        if user_id is None:
            logger.error("User ID not found.")
            return

        home = pwd.getpwuid(user_id).pw_dir
        cfg = os.path.join(home, '.blocksat', '.secret')

        if not os.path.exists(cfg):
            logger.error("Secret not found.")
            return False

        with open(cfg, 'r') as fd:
            secret = fd.read()

        valid_data = f"{secret}-{pid}".encode()
        valid_token = hashlib.sha256(valid_data).hexdigest()

        is_valid = valid_token == rec_token

        if not is_valid:
            logger.error("Received token does not match with expected token.")

        return is_valid

    def _convert_type(self, data):
        """Convert dbus data types to python native data types"""
        if isinstance(data, dbus.String):
            data = str(data)
        elif isinstance(data, dbus.Boolean):
            data = bool(data)
        elif isinstance(data, dbus.Int64):
            data = int(data)
        elif isinstance(data, dbus.Double):
            data = float(data)
        elif isinstance(data, dbus.Array):
            data = [self._convert_type(value) for value in data]
        elif isinstance(data, dbus.Dictionary):
            new_data = dict()
            for k, v in data.items():
                new_data[self._convert_type(k)] = self._convert_type(v)
            data = new_data

        return data

    def clean_request(self, pid):
        """Clean up process from requests list"""
        self.requests.pop(pid, None)

    @dbus.service.method(BLOCKSATD_SERVICE,
                         in_signature='sassa{ss}ii',
                         out_signature='i',
                         sender_keyword="sender",
                         connection_keyword="conn")
    def run(self, token, cmd, cwd, env, stdout, stderr, sender, conn):
        """Run requested command

        Args:
            token (str): Authorization token.
            cmd (list): Command to be executed on the child process.
            cwd (str): Working directory.
            env (dict): Environment variables.
            stdout (int): Stdout option from child process.
            stderr (int): Stderr option from child process.

        Returns:
            int: Child process identifier.

        """
        cmd = self._convert_type(cmd)
        if not isinstance(cmd, list) or cmd[0] not in allowed_cmds:
            cmd_str = " ".join(cmd) if isinstance(cmd, list) else cmd
            logger.error(f"Command not allowed: {cmd_str}")
            return -1

        cwd = self._convert_type(cwd)
        env = self._convert_type(env)
        stdout = self._convert_type(stdout)
        stderr = self._convert_type(stderr)

        cwd = None if not cwd else cwd
        env = None if not env else env
        stdout = subprocess.DEVNULL if stdout == 0 else stdout
        stderr = subprocess.DEVNULL if stderr == 0 else stderr

        sender_id = self._get_sender_pid(sender, conn)

        if (not self._validate_token(sender_id, token)) or (
                not self.polkit.check_authorization(sender_id)):
            logger.info(f"PID {sender_id} not authorized")
            return -2

        ps = subprocess.Popen(cmd,
                              cwd=cwd,
                              env=env,
                              stdout=stdout,
                              stderr=stderr)
        logger.info(f"Running PID {ps.pid}")
        logger.debug(f"Running [PID {ps.pid}]: > " + " ".join(cmd))

        # Save a reference for the requested process
        pid = ps.pid
        self.requests[pid] = ps

        return pid

    @dbus.service.method(BLOCKSATD_SERVICE,
                         in_signature='i',
                         out_signature='av')
    def status(self, request_id):
        """Return the status from runner request

        Args:
            request_id: Process ID from previous request.

        Returns:
            list: List with the status message (str), the process exit code
                (int), the captured stdout (str), and the captured stderr
                (str).

        """
        pid = int(request_id)

        if pid not in self.requests:
            logger.info(f"Process with PID {pid} not found.")
            return ["Process not found.", -1, '', '']

        ps = self.requests[pid]
        res = ps.poll()

        if res is None:
            logger.info(f"[PID {pid}] Running")
            return ["Running", 0, '', '']

        stdout = ps.stdout
        stdout = stdout.read().decode() if stdout else ''
        stderr = ps.stderr
        stderr = stderr.read().decode() if stderr else ''

        logger.info(f"[PID {pid}] Exit code: {res}")
        logger.debug(f"[PID {pid}] Stdout: {stdout}")

        if res != 0:
            cmd_str = " ".join(ps.args)
            logger.error(
                f"[PID {pid}] Command failed: {cmd_str} - Error: {stderr}")

        # Remove process from requests list
        self.clean_request(pid)

        stdout = stdout or ''
        stderr = stderr or ''

        return ["Finished", res, stdout, stderr]


class PolicyKit():

    def __init__(self, dbus) -> None:
        self.dbus = dbus

    def check_authorization(self, subject_pid) -> bool:
        """Check authorization using PolicyKit daemon

        subject_pid: ID from the subject process. The subject is the
            unprivileged process that requested the service.

        Returns:
            bool: Whether or not the subject it authorized.

        """
        proxy = self.dbus.proxy(POLKIT_SERVICE, POLKIT_PATH, POLKIT_INTERFACE)
        subject = ('unix-process', {
            'pid': dbus.UInt32(subject_pid, variant_level=1),
            'start-time': dbus.UInt64(0, variant_level=1)
        })
        action_id = BLOCKSATD_SERVICE
        details = {}
        flags = 1  # AllowUserInteraction flag
        cancellation_id = ''  # No cancellation id

        try:
            is_auth, _, details = proxy.CheckAuthorization(
                subject, action_id, details, flags, cancellation_id)
        except dbus.DBusException as e:
            logger.error(e)
            return False

        return bool(is_auth)


class DBus():

    def __init__(self, bus_type: str) -> None:
        assert (bus_type in ['system', 'session'])

    def proxy(self, service, path, interface):
        self.bus = dbus.SystemBus()

        service = self.bus.get_object(service, path)
        iface = dbus.Interface(service, dbus_interface=interface)
        return iface


def get_app():
    """Return the application object and start function"""
    if APP_TYPE == "qt":
        app = QCoreApplication([])
        return app, app.exec_
    elif APP_TYPE == "glib":
        loop = GLib.MainLoop()
        return loop, loop.run
    else:
        raise ValueError(f"Unknown {APP_TYPE} application.")


def main():
    app, app_start = get_app()
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    system_bus = dbus.SystemBus()
    dbus_service = dbus.service.BusName(BLOCKSATD_SERVICE, system_bus)
    logger.info(dbus_service.get_name())

    def sig_handler(signal=None, frame=None):
        app.quit()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    if APP_TYPE == "qt":
        timer = QTimer()
        timer.start(500)
        timer.timeout.connect(lambda: None)

    Runner(system_bus, BLOCKSATD_PATH)
    logger.info(
        f'Blocksatd: {BLOCKSATD_SERVICE} running (main-loop: {APP_TYPE}).')
    sys.exit(app_start())


if __name__ == "__main__":
    main()
