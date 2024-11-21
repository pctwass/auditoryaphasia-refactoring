import logging
import os
import sys

from dareplane_utils.logging.logger import get_logger as get_dareplane_logger

from auditory_aphasia.config_builder import build_system_config

SYSTEM_CONFIG = build_system_config()

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

    level_default = get_log_level(SYSTEM_CONFIG.log_level_default)
    level_file = get_log_level(SYSTEM_CONFIG.log_level_file)
    level_stdout = get_log_level(SYSTEM_CONFIG.log_level_stdout)

    log_format = "%(asctime)s [%(levelname)s] [%(module)s.%(funcName)s] %(message)s"

    global logger
    logger = get_dareplane_logger(SYSTEM_CONFIG.logger_name)
    logger.setLevel(level_default)

    if SYSTEM_CONFIG.log_to_stdout:
        stdout_handler = logging.StreamHandler(stream=sys.stdout)
        stdout_handler.setFormatter(logging.Formatter(log_format))
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
        file_handler.setFormatter(logging.Formatter(log_format))
        file_handler.setLevel(level_file)
        logger.addHandler(file_handler)


def get_log_level(log_level_str: str):
    match log_level_str:
        case "debug":
            return logging.DEBUG
        case "info":
            return logging.INFO
        case "warning":
            return logging.WARNING
        case "critical":
            return logging.CRITICAL
        case _:
            return None

