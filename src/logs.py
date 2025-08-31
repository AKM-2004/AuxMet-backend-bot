import logging
import os
from logging.handlers import TimedRotatingFileHandler


## functions to make create the logger when class is initializaed and then error, info, debug functions that will run in that perticular file


class ModuleLogger:
    def __init__(self, app_name: str, backup: int = 2):
        self.__app_name = app_name
        self.__backup = backup

        os.makedirs(f"./logs/{app_name}", exist_ok=True)

        self.__logger = logging.getLogger(app_name)
        self.__logger.setLevel(logging.DEBUG)
        self.__logger.propagate = False

        self.__formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # INFO handler (rotated daily)
        self.__info_handler = TimedRotatingFileHandler(
            filename=f"./logs/{app_name}/info.log",
            when="midnight",
            interval=1,
            backupCount=backup,
            encoding="utf-8",
        )
        self.__info_handler.setLevel(logging.INFO)
        self.__info_handler.setFormatter(self.__formatter)

        # ERROR handler
        self.__error_handler = TimedRotatingFileHandler(
            filename=f"./logs/{app_name}/error.log",
            when="midnight",
            interval=1,
            backupCount=backup,
            encoding="utf-8",
        )
        self.__error_handler.setLevel(logging.ERROR)
        self.__error_handler.setFormatter(self.__formatter)

        # DEBUG handler
        self.__debug_handler = TimedRotatingFileHandler(
            filename=f"./logs/{app_name}/debug.log",
            when="midnight",
            interval=1,
            backupCount=backup,
            encoding="utf-8",
        )
        self.__debug_handler.setLevel(logging.DEBUG)
        self.__debug_handler.setFormatter(self.__formatter)

        if not self.__logger.handlers:
            self.__logger.addHandler(self.__info_handler)
            self.__logger.addHandler(self.__error_handler)
            self.__logger.addHandler(self.__debug_handler)

    def ERROR(self, text):
        self.__logger.error(text)

    def DEBUG(self, text):
        self.__logger.debug(text)

    def INFO(self, text):
        self.__logger.info(text)
