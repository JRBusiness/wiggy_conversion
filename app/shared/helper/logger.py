"""
@author: Kuro
"""
import logging
from settings import Config as settings

config = {
    "debug": settings.debug_log,
    "info": settings.info_log,
    "warning": settings.warning_log,
    "error": settings.error_log,
    "critical": settings.critical_log,
}


class StandardizedLogger:
    """
    This class is a standardized logger that can be used to log messages to a file.
    """

    def __init__(self, name):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        formatter = logging.Formatter(
            '{"@timestamp":"%(asctime)s", "level": "%(levelname)s", "name": "%(name)s", "user_id": "%(user_id)s", "message": "%(message)s"}'
        )

        for log_type, log_location in config.items():
            handler = logging.FileHandler(log_location)
            handler.setLevel(logging.getLevelName(log_type.upper()))
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def log(self, level, message, user_id=None):
        """
        If the user_id is not None, then add it to the extra dictionary, otherwise, just use an empty dictionary

        :param level: The log level. This is one of the constants defined in the logging module
        :param message: The message to log
        :param user_id: The user_id of the user who is making the request
        """
        extra = {"user_id": user_id} if user_id else {}
        self.logger.log(level, message, extra=extra)

    def debug(self, message, user_id=None):
        """
        The function takes in a message and a user_id, and then calls the log function with the logging.debug level and the message and user_id.

        :param message: The message to be logged
        :param user_id: The user_id of the user who is doing the action
        """
        self.log(logging.DEBUG, message, user_id)

    def info(self, message, user_id=None):
        """
        The function takes in a message and a user_id, and then calls the log function with the logging.INFO level and the message and user_id.

        :param message: The message to be logged
        :param user_id: The user_id of the user who is doing the action
        """
        self.log(logging.INFO, message, user_id)

    def warning(self, message, user_id=None):
        """
        It takes a message and a user_id, and logs the message at the WARNING level

        :param message: The message to be logged
        :param user_id: The user_id of the user who is doing the action
        """
        self.log(logging.WARNING, message, user_id)

    def error(self, message, user_id=None):
        """
        It logs the message at the ERROR level, and if the user_id is not None, it also logs the user_id at the DEBUG level

        :param message: The message to log
        :param user_id: The user_id of the user who is doing the action
        """
        self.log(logging.ERROR, message, user_id)

    def critical(self, message, user_id=None):
        """
        It logs a message with a severity level of CRITICAL

        :param message: The message to be logged
        :param user_id: The user_id of the user who is doing the action
        """
        self.log(logging.CRITICAL, message, user_id)
