import os
import sys

from pathlib import Path

import src.config.system_config as sytem_config


def set_logger(file=True, stdout=True, level_file = 'debug', level_stdout = 'info'):
    """
    level : 'debug' or 'info'
    """
    import logging

    if level_file.lower() == 'debug':
        level_file = logging.DEBUG
    elif level_file.lower() == 'info':
        level_file = logging.INFO

    if level_stdout.lower() == 'debug':
        level_stdout = logging.DEBUG
    elif level_stdout.lower() == 'info':
        level_stdout = logging.INFO

    log_format = '%(asctime)s [%(levelname)s] [%(module)s.%(funcName)s] %(message)s'

    root_logger = logging.getLogger(None)
    root_logger.setLevel(logging.DEBUG)

    if stdout:
        stdout_handler = logging.StreamHandler(stream=sys.stdout)
        stdout_handler.setFormatter(logging.Formatter(log_format))
        stdout_handler.setLevel(level_stdout)
        root_logger.addHandler(stdout_handler)

    if file:
        log_dir = os.path.join(sytem_config.repository_dir_base, "temp", "logging") #os.path.join(data_dir, save_folder_name)
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)
        file_handler = logging.FileHandler(os.path.join(log_dir, sytem_config.log_file_name))
        file_handler.setFormatter(logging.Formatter(log_format))
        file_handler.setLevel(level_file)
        root_logger.addHandler(file_handler)