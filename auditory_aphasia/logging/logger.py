import logging
import os
import sys

from dareplane_utils.logging.logger import get_logger as get_dareplane_logger

from auditory_aphasia.config_builder import build_system_config

SYSTEM_CONFIG = build_system_config()
LOGGER_LVL_MAP = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "critical": logging.CRITICAL,
}

logger = None


def get_logger():
    global logger
    if logger is None:
        set_logger()
    return logger


def set_logger():
    """
    level : 'debug', 'info', 'warning', or 'critical'
    """

    level_default = LOGGER_LVL_MAP.get(SYSTEM_CONFIG.log_level_default)
    level_stdout = LOGGER_LVL_MAP.get(SYSTEM_CONFIG.log_level_stdout)

    global logger
    logger = get_dareplane_logger(SYSTEM_CONFIG.logger_name)
    logger.setLevel(level_default)

    if SYSTEM_CONFIG.log_to_stdout:
        stdout_handler = logging.StreamHandler(stream=sys.stdout)
        stdout_handler.setLevel(level_stdout)
        logger.addHandler(stdout_handler)

    if SYSTEM_CONFIG.log_to_file:
        log_dir = os.path.join(
            SYSTEM_CONFIG.repository_dir_base, "temp", "logging"
        )  # os.path.join(data_dir, save_folder_name)
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)
        file_handler = logging.FileHandler(
            os.path.join(log_dir, SYSTEM_CONFIG.log_file_name)
        )
        logger.addHandler(file_handler)
