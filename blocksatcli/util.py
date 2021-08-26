"""Utility functions"""
import copy
import os
import subprocess
import textwrap
import tempfile
from urllib.request import urlretrieve
from urllib.error import HTTPError


def fill_print(text):
    text = " ".join(text.replace("\n", "").split())
    print(textwrap.fill(text))
    print()


def typed_input(msg, hint=None, in_type=int, default=None):
    """Ask for user input of a specific type"""
    res = None
    while (res is None):
        try:
            if (default is not None):
                assert (isinstance(default, in_type))
                input_val = input(msg + ": [{}] ".format(default)) or default
            else:
                input_val = input(msg + ": ")
            res = in_type(input_val)
        except ValueError:
            if (hint is None):
                if (in_type == int):
                    print("Please enter an integer number")
                elif (in_type == float):
                    print("Please enter a number")
                else:
                    type_str = in_type.__name__
                    print("Please enter a {}".format(type_str))
            else:
                print(hint)
    assert (res is not None)
    assert (isinstance(res, in_type))
    return res


def string_input(msg, default=None):
    """Ask for a non-null string input with an optional default value"""
    res = ""
    while (len(res) == 0):
        if (default is not None):
            assert (isinstance(default, str))
            res = input(msg + ": [{}] ".format(default)) or default
        else:
            res = input(msg + ": ")
    return res


def _ask_yes_or_no(msg, default="y", help_msg=None):
    """Yes or no question

    Args:
        msg      : the message or question to ask the user
        default  : default response
        help_msg : Optional help message

    Returns:
        True if answer is yes, False otherwise.

    """
    response = None

    if (default == "y"):
        options = "[Y/n]"
    else:
        options = "[N/y]"

    while response not in {"y", "n"}:
        if (help_msg is None):
            question = msg + " " + options + " "
            raw_resp = input(question) or default
        else:
            print(textwrap.fill(msg))
            print()
            print(textwrap.fill(help_msg))
            print()
            raw_resp = input("Answer " + options + " ") or default

        response = raw_resp.lower()

        if (response not in ["y", "n"]):
            print("Please enter \"y\" or \"n\"")

    return (response == "y")


def _ask_multiple_choice(vec,
                         msg,
                         label,
                         to_str,
                         help_msg=None,
                         none_option=False,
                         none_str="None of the above"):
    """Multiple choice question

    Args:
        vec         : Vector with elements to choose from
        msg         : Msg to prompt user for choice
        label       : Description/label of what "vec" holdes
        to_str      : Function that prints information about elements
        help_msg    : Optional help message
        none_option : Whether to display a "none of the above" option
        none_str    : What do display as "none of the above" message

    Returns:
        Chosen element

    """
    if (none_option):
        assert (len(vec) > 0)
    else:
        assert (len(vec) > 1)

    print(msg)

    for i_elem, elem in enumerate(vec):
        elem_str = to_str(elem)
        print("[%2u] %s" % (i_elem, elem_str))

    if (none_option):
        print("[%2u] %s" % (len(vec), none_str))

    if (help_msg is not None):
        print()
        print(help_msg)

    resp = None
    while (not isinstance(resp, int)):
        try:
            resp = int(input("\n%s number: " % (label)))
        except ValueError:
            print("Please choose a number")
            continue

        max_resp = len(vec) + 1 if none_option else len(vec)
        if (resp >= max_resp):
            print("Please choose number from 0 to %u" % (max_resp - 1))
            resp = None
            continue

        if (none_option and resp == len(vec)):
            choice = None
            print(none_str)
        else:
            choice = copy.deepcopy(vec[resp])
            # NOTE: deep copy to prevent the caller from changing the original
            # element.
            print(to_str(choice))
        print()

        return choice


def _print_header(header, target_len=80):
    """Print section header"""

    prefix = ""
    suffix = ""
    header_len = len(header) + 2
    remaining = target_len - header_len
    prefix_len = int(remaining / 2)
    suffix_len = int(remaining / 2)

    if (remaining % 1 == 1):
        prefix_len += 1

    for i in range(0, prefix_len):
        prefix += "-"

    for i in range(0, suffix_len):
        suffix += "-"

    print("\n" + prefix + " " + header + " " + suffix)


def _print_sub_header(header, target_len=60):
    """Print sub-section header"""
    _print_header(header, target_len=target_len)


def prompt_for_enter():
    try:
        resp = input("\nPress Enter to continue...")
        if (resp == "q"):
            exit()
        os.system('clear')
    except KeyboardInterrupt:
        print("Aborting")
        exit()


def get_home_dir():
    """Get the user's home directory even if running with sudo"""
    sudo_user = os.environ.get('SUDO_USER')
    user = sudo_user if sudo_user is not None else ""
    return os.path.expanduser("~" + user)


class ProcessRunner():
    def __init__(self, logger=None, dry=False):
        self.logger = logger
        self.dry = dry
        self.last_cwd = None
        self.root = os.geteuid() == 0

    def _get_cmd_str(self, orig_cmd):
        """Generate string for command

        If any argument is supposed to be quoted (i.e., has spaces), add the
        quotes.

        """
        quoted_cmd = orig_cmd.copy()
        for i, elem in enumerate(quoted_cmd):
            if (" " in elem):
                quoted_cmd[i] = "\'{}\'".format(elem)
        return "> " + " ".join(quoted_cmd)

    def set_dry(self, dry=True):
        self.dry = dry

    def run(self,
            cmd,
            cwd=None,
            env=None,
            stdout=None,
            stderr=None,
            nocheck=False,
            root=False,
            nodry=False,
            capture_output=False):
        assert (isinstance(cmd, list))

        # Add sudo if necessary
        if (root and not self.root and cmd[0] != "sudo"):
            orig_cmd = cmd  # Keep the original list untouched
            cmd = orig_cmd.copy()
            cmd.insert(0, "sudo")

        # Handle capture_output for backwards compatibility with py3.6
        if (capture_output):
            assert (stdout is None)
            assert (stderr is None)
            stdout = subprocess.PIPE
            stderr = subprocess.PIPE

        if (self.dry and not nodry):
            if (cwd != self.last_cwd):
                print("> cd {}".format(cwd))
                self.last_cwd = cwd
            print(self._get_cmd_str(cmd))
            return

        if (self.logger is not None):
            self.logger.debug(self._get_cmd_str(cmd))

        try:
            res = subprocess.run(cmd,
                                 cwd=cwd,
                                 env=env,
                                 stdout=stdout,
                                 stderr=stderr,
                                 check=(not nocheck))
        except KeyboardInterrupt:
            print("Aborting")
            exit()

        return res

    def create_file(self, content, path, **kwargs):
        """Create file with given content on a specified path

        If the target path requires root privileges, this function can be
        executed with option root=True.

        """
        if (self.dry):
            # In dry-run mode, run an equivalent echo command.
            cmd = ["echo", "-e", repr(content), ">", path]
        else:
            tmp_file = tempfile.NamedTemporaryFile(mode="w", delete=False)
            with tmp_file as fd:
                fd.write(content)
            cmd = ["mv", tmp_file.name, path]
        self.run(cmd, **kwargs)
        if (not self.dry):
            self.logger.info("Created file {}".format(path))


class Pipe():
    """Unnamed pipe wrapper"""
    def __init__(self):
        """Create unnamed pipe"""
        r_fd, w_fd = os.pipe()

        self.r_fd = r_fd  # read file descriptor
        self.r_fo = os.fdopen(r_fd, "r")  # read file object

        self.w_fd = w_fd  # write file descriptor
        self.w_fo = os.fdopen(w_fd, "w")  # write file object

    def __del__(self):
        """Close pipe"""
        self.r_fo.close()
        self.w_fo.close()

    def readline(self):
        """Read line from pipe file"""
        return self.r_fo.readline()

    def write(self, data):
        """Write data to pipe file

        Args:
            data : The data to write into the pipe file

        """
        self.w_fo.write(data)


def _print_urlretrieve_progress(block_num, block_size, total_size):
    """Print progress on urlretrieve's reporthook"""
    downloaded = block_num * block_size
    progress = 100 * downloaded / total_size
    if (total_size > 0):
        print("Download progress: {:4.1f}%".format(progress), end='\r')
        if (progress >= 100):
            print("")


def download_file(url, destdir, dry_run, logger=None):
    """Download file from a given URL

    Args:
        url     : Download URL.
        destdir : Destination directory.
        dry_run : Dry-run mode.
        logger  : Optional logger to print messages.

    Returns:
        Path to downloaded file if the download is successful. None in
        dry-run mode or if the download fails.

    """
    filename = url.split('/')[-1]
    local_path = os.path.join(destdir, filename)

    if (dry_run):
        print("Download: {}".format(url))
        print("Save at: {}".format(destdir))
        return

    if (logger is not None):
        logger.debug("Download {} and save at {}".format(url, destdir))

    try:
        urlretrieve(url, local_path, _print_urlretrieve_progress)
    except HTTPError as e:
        logger.error(str(e))
        return

    return local_path
