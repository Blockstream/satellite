"""Utility functions"""
import os, textwrap, subprocess


def fill_print(text):
    text = " ".join(text.replace("\n", "").split())
    print(textwrap.fill(text))
    print()


def typed_input(msg, hint=None, in_type=int):
    """Ask for user input of a specific type"""
    res = None
    while (res is None):
        try:
            res = in_type(input(msg + ": "))
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
    assert(res is not None)
    assert(isinstance(res, in_type))
    return res


def _ask_yes_or_no(msg, default="y", help_msg = None):
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


def _ask_multiple_choice(vec, msg, label, to_str, help_msg = None,
                         none_option = False, none_str = "None of the above"):
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
    assert(len(vec) > 1)

    print(msg)

    for i_elem, elem in enumerate(vec):
        elem_str = to_str(elem)
        print("[%2u] %s" %(i_elem, elem_str))

    if (none_option):
        print("[%2u] %s" %(len(vec), none_str))

    if (help_msg is not None):
        print()
        print(help_msg)

    resp = None
    while (not isinstance(resp, int)):
        try:
            resp = int(input("\n%s number: " %(label)))
        except ValueError:
            print("Please choose a number")
            continue

        max_resp = len(vec) + 1 if none_option else len(vec)
        if (resp >= max_resp):
            print("Please choose number from 0 to %u" %(max_resp - 1))
            resp = None
            continue

        if (none_option and resp == len(vec)):
            choice = None
            print(none_str)
        else:
            choice = vec[resp]
            print(to_str(choice))
        print()

        return choice


def _print_header(header, target_len=80):
    """Print section header"""

    prefix      = ""
    suffix      = ""
    header_len  = len(header) + 2
    remaining   = target_len - header_len
    prefix_len  = int(remaining / 2)
    suffix_len  = int(remaining / 2)

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

def root_cmd(cmd):
    """Add sudo to cmd if non-root

    Args:
        cmd : Command as list

    """
    assert(isinstance(cmd, list))
    if (os.geteuid() != 0 and cmd[0] != "sudo"):
        cmd.insert(0, "sudo")
    return cmd


def run_or_print_root_cmd(cmd, logger=None):
    """Run root command

    Args:
        cmd : Command as list

    """
    assert(isinstance(cmd, list))
    assert(cmd[0] != "sudo")

    if (os.geteuid() == 0):
        if (logger is not None):
            logger.debug("> " + " ".join(cmd))
        return subprocess.check_output(cmd)
    else:
        print("> " + " ".join(cmd) + "\n")


def run_and_log(cmd, logger=None, cwd=None):
    assert(isinstance(cmd, list))
    if (logger is not None):
        logger.debug("> " + " ".join(cmd))
    subprocess.run(cmd, cwd=cwd)


