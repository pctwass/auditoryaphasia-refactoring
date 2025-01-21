import logging
import os
import sys

import src.config.system_config as system_config
from dareplane_utils.logging.logger import get_logger as get_dareplane_logger

# logger = get_dareplane_logger("bollinger_control", add_console_handler=True)

logger = None

LOGGING_LVL_MAP = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "critical": logging.CRITICAL,
}


def get_logger():
    global logger
    if logger is None:
        set_logger()
    return logger


def set_logger():
    """
    level : 'debug', 'info', 'warning', or 'critical'
    """

    level_default = LOGGING_LVL_MAP.get(system_config.log_level_default)
    level_file = LOGGING_LVL_MAP.get(system_config.log_level_file)
    level_stdout = LOGGING_LVL_MAP.get(system_config.log_level_stdout)

    global logger
    logger = get_dareplane_logger(system_config.logger_name, add_console_handler=True)
    logger.setLevel(level_default)

    if system_config.log_to_stdout:
        stdout_handler = logging.StreamHandler(stream=sys.stdout)
        stdout_handler.setLevel(level_stdout)
        logger.addHandler(stdout_handler)

    if system_config.log_to_file:
        log_dir = os.path.join(
            system_config.repository_dir_base, "temp", "logging"
        )  # os.path.join(data_dir, save_folder_name)
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)
        file_handler = logging.FileHandler(
            os.path.join(log_dir, system_config.log_file_name)
        )
        file_handler.setLevel(level_file)
        logger.addHandler(file_handler)

