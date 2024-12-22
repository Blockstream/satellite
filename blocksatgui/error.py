import requests

from .components import messagebox, worker


def parse_api_error(error):
    """Parse API error message

    Args:
        error: API error message.

    Returns:
        tuple (str, dict): Tuple containing the error type and the error.

    """
    if isinstance(error, dict):
        if 'errors' in error:
            api_error = error['errors'][0]
            return 'error', {
                'title': api_error['title'],
                'code': api_error['code'],
                'detail': api_error['detail']
            }
        elif 'message' in error:
            return 'other', error['message']
        else:
            for key, val in error.items():
                error[key] = val[0]
            return 'validation', error
    elif isinstance(error, str):
        return 'other', error
    else:
        return 'unknown', error


def show_error_message(parent, title, error: worker.WorkerError):
    """Show a message box with the error message"""

    message = ""
    if error.type == requests.exceptions.ConnectionError:
        message = ("Failed to send request due to a connection "
                   "error. Please, make sure you are connected to "
                   "the internet.")
    elif error.type == SystemExit and not str(error.value).isnumeric():
        err_type, err = parse_api_error(error.value)
        if err_type == 'error':
            title = f"{err['title']} ({err['code']})"
            message = err['detail']
        elif err_type == 'validation':
            title = "Validation Error"
            message = "The following errors occurred:\n"
            for key, val in err.items():
                message += f"\n{key}: {val}"
        elif err_type == 'other':
            message = err

    if message == "":  # If no message was set, use the traceback
        message = error.traceback

    messagebox.Message(parent=parent, title=title, msg=message)
