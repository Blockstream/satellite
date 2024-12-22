import sys
import textwrap

import requests


def log_error(logger, error):
    """Print error returned by API server"""
    h = ("-----------------------------------------"
         "-----------------------------")
    if (isinstance(error, dict)):
        error_str = ""
        if ("title" in error):
            error_str += error["title"]
        if ("code" in error):
            error_str += " (code: {})".format(error["code"])
        logger.error(h)
        logger.error(textwrap.fill(error_str))
        if ("detail" in error):
            logger.error(textwrap.fill(error["detail"]))
        logger.error(h)
    else:
        logger.error(error)


def log_errors(logger, resp):
    """Log errors from a response"""
    if isinstance(resp, requests.Response):
        try:
            if "errors" in resp.json():
                for error in resp.json()["errors"]:
                    log_error(logger, error)
            else:
                logger.error(resp.json())
        except ValueError:
            logger.error(resp.text)
    elif isinstance(resp, str):
        logger.error(resp)


def get_json_or_text(r: requests.Response):
    """Get json response if possible, otherwise return text"""
    try:
        res = r.json()
    except ValueError:
        res = r.text
    return res


def log_error_and_exit(r, logger, sys_exit_out=False):
    """Log error and exit or exit with error

    Args:
        r (str or requests.Response): Error string or request response.
        sys_exit_out (bool, optional): Feed error message directly into
            sys.exit() so that a caller can capture this error using
            sys.exc_info(). Defaults to False.
    """
    if sys_exit_out:
        sys.exit(r if isinstance(r, str) else get_json_or_text(r))
    else:
        log_errors(logger, r)
        sys.exit(1)
