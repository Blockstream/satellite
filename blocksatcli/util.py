"""Utility functions"""

def _ask_yes_or_no(msg, default="y"):
    """Yes or no question

    Args:
        msg     : the message or question to ask the user
        default : default response

    Returns:
        True if answer is yes, False otherwise.

    """
    response = None

    if (default == "y"):
        options = "[Y/n]"
    else:
        options = "[N/y]"

    question = msg + " " + options + " "

    while response not in {"y", "n"}:
        raw_resp = input(question) or default
        response = raw_resp.lower()

        if (response not in {"y", "n"}):
            print("Please enter \"y\" or \"n\"")

    return (response == "y")


def _ask_multiple_choice(vec, msg, label, to_str, help_msg = None):
    """Multiple choice question

    Args:
        vec    : Vector with elements to choose from
        msg    : Msg to prompt user for choice
        label  : Description/label of what "vec" holdes
        to_str : Function that prints information about elements
        help_msg : Optional help message

    Returns:
        Chosen element

    """
    assert(len(vec) > 1)

    print(msg)

    for i_elem, elem in enumerate(vec):
        elem_str = to_str(elem)
        print("[%2u] %s" %(i_elem, elem_str))

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

        if (resp >= len(vec)):
            print("Please choose number from 0 to %u" %(len(vec) - 1))
            resp = None
            continue

        choice = vec[resp]
        print(to_str(choice))
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

