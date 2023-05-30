"""
@author: Kuro
"""
from fastapi.logger import logger

from app.shared.schemas.ExceptionSchema import SafeException, BaseResponse


def safe(function):
    """
    The safe function is a decorator that wraps the passed in function and returns
    a safe version of it. A safe version of a function does not raise any errors, but instead
    returns None if an error occurs.

    :param function: Used to Pass the function to be decorated.
    :return: A function that returns a dictionary of the arguments passed to it.
    """

    def run(*args, **kwargs) -> BaseResponse:
        """
        The run function is the main entry point for the wrapper
        It is responsible for parsing command line arguments and taking appropriate action.

        :param *args: Used to Pass a non-keyword, variable-length argument list to the function.
        :param **kwargs: Used to Pass a dictionary of keyword arguments to the function.
        :return: A dictionary of the arguments.
        """
        try:
            return function(*args, **kwargs)
        except Exception as e:
            logger.error(e)
            cls = args[0].__class__.__name__

            return SafeException(success=False, error=f"Caught Error: {e.args[0]}")

    return run
