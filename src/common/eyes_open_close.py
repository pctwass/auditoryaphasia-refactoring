import os
import time

import auditory_aphasia.config.config as config
import auditory_aphasia.config.system_config as system_config
import auditory_aphasia.common.utils as utils
import auditory_aphasia.process_management.intermodule_communication as intermodule_comm

from auditory_aphasia.logging.logger import get_logger
logger = get_logger()


def run_eyes_open_close(outlet, pre_or_post):
    """
    Parameters
    ----------
    pre_or_post : 'pre' or 'post'
    """
    if pre_or_post == 'pre':
        folder = 'presession'
    elif pre_or_post == 'post':
        folder = 'postsession'
    else:
        raise ValueError("pre_or_post can only take 'pre' or 'post'")

    # eyes open close
    time_rec = config.eye_open_close_time # sec
    logger.debug("time eye open close set to %d" %time_rec)

    while True:
        f_save_eye = os.path.join(system_config.data_dir, system_config.save_folder_name, folder)
        if not os.path.exists(f_save_eye):
            os.makedirs(f_save_eye)
        input("Press Any Key to Start Eyes Open Recording (%ds)" %time_rec)
        f_name = utils.check_file_exists_on_extenstion(os.path.join(f_save_eye, 'eyes_open'), 'eeg')
        intermodule_comm.send_cmd_LSL(outlet, 'acq','start_recording', f_name)
        time.sleep(time_rec)
        intermodule_comm.send_cmd_LSL(outlet, 'acq', 'stop_recording')
        input("Press Any Key to Start Eyes Close Recording (%ds)" %time_rec)
        f_name = utils.check_file_exists_on_extenstion(os.path.join(f_save_eye, 'eyes_close'), 'eeg')
        intermodule_comm.send_cmd_LSL(outlet, 'acq','start_recording', f_name)
        time.sleep(time_rec)
        intermodule_comm.send_cmd_LSL(outlet, 'acq', 'stop_recording')

        # ask the user if they want to repeat the procedure (default choice: 'yes')
        user_input_repeat_procedure = input("Do you want to record eyes open closed again? [y]/n : ")
        if not user_input_repeat_procedure == "" or not user_input_repeat_procedure.lower() == 'y':
            break