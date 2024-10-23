import sys
import os
import time

import config.conf_selector
# exec("import %s as conf" % (conf_selector.conf_file_name))
# exec("import %s as conf_system" % (conf_selector.conf_system_file_name))
import config.conf as conf
import config.conf_system as conf_system
import src.utils as utils

import logging
logger = logging.getLogger(__name__)

from src.process_management.process_communication_enums import AudioStatus


def eyes_open_close(outlet, pre_or_post):
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
    time_rec = conf.eye_open_close_time # sec
    logger.debug("time eye open close set to %d" %time_rec)
    while True:
        eyes = input("Do you want to record eyes open closed? [y]/n : ")
        if eyes == "" or eyes.lower() == 'y':
            f_save_eye = os.path.join(conf_system.data_dir, conf_system.save_folder_name, folder)
            if not os.path.exists(f_save_eye):
                os.makedirs(f_save_eye)
            input("Press Any Key to Start Eyes Open Recording (%ds)" %time_rec)
            f_name = utils.check_file_exists(os.path.join(f_save_eye, 'eyes_open'), 'eeg')
            utils.send_cmd_LSL(outlet, 'acq','start_recording', f_name)
            time.sleep(time_rec)
            utils.send_cmd_LSL(outlet, 'acq', 'stop_recording')
            input("Press Any Key to Start Eyes Close Recording (%ds)" %time_rec)
            f_name = utils.check_file_exists(os.path.join(f_save_eye, 'eyes_close'), 'eeg')
            utils.send_cmd_LSL(outlet, 'acq','start_recording', f_name)
            time.sleep(time_rec)
            utils.send_cmd_LSL(outlet, 'acq', 'stop_recording')
            break
        elif eyes.lower() == 'n':
            break

def play_oddball(outlet, audio_state_dict, number_of_repetitions = 2):
    while True:
        val = input("Do you want to play oddball? [y]/n : ")
        if val == "" or val.lower() == 'y':
            import pyscab

            oddball_base = os.path.join(conf_system.repository_dir_base, 'media', 'audio', 'oddball')
            nT_id = 1
            T_id = 21

            audio_info = list()
            audio_files = pyscab.DataHandler()

            audio_info.append([nT_id, os.path.join(oddball_base, conf_system.oddball_non_target), conf.master_volume])
            audio_files.load(nT_id, os.path.join(oddball_base, conf_system.oddball_non_target), volume=conf.master_volume)
            logger.debug("oddball nT, id:%s, dir:%s, volume:%s", nT_id, os.path.join(oddball_base, conf_system.oddball_non_target), conf.master_volume)

            audio_info.append([T_id, os.path.join(oddball_base, conf_system.oddball_target), conf.master_volume])
            audio_files.load(T_id, os.path.join(oddball_base, conf_system.oddball_target), volume=conf.master_volume)
            logger.debug("oddball T, id:%s, dir:%s, volume:%s", T_id, os.path.join(oddball_base, conf_system.oddball_target), conf.master_volume)

            soa_oddball = conf.oddball_soa
            number_of_repetitions_oddball = conf.oddball_n_seqs # 50->5min
            logger.debug("oddball soa : %s", str(soa_oddball))
            logger.debug("oddball number of repetitions : %s", str(number_of_repetitions_oddball))

            play_plan = list()
            stimplan = utils.generate_stimulation_plan(6, number_of_repetitions_oddball)

            time_plan = 0
            for stim in stimplan:
                if stim == 1:
                    play_plan.append([time_plan, T_id, conf_system.oddball_channels, conf_system.oddball_marker['target']])
                else:
                    play_plan.append([time_plan, nT_id, conf_system.oddball_channels, conf_system.oddball_marker['nontarget']])
                time_plan += soa_oddball
            for m in range(conf.oddball_n_reps):
                oddball_run_idx = 0
                input("Press Any Key to Start New Oddball Run")
                while True:
                    oddball_run_idx += 1
                    f_dir = os.path.join(conf_system.data_dir, conf_system.save_folder_name, "Oddball_%d.eeg"%oddball_run_idx)
                    if os.path.exists(f_dir):
                        continue
                    else:
                        break
                logger.debug("oddball_%d will be saved in : %s" %(oddball_run_idx, str(f_dir)))
                utils.send_cmd_LSL(outlet, 'acq','start_recording', f_dir)
                utils.send_params_LSL(outlet, 'audio', 'audio_info', audio_info)
                #utils.send_params_LSL(outlet, 'audio', 'marker', True)
                utils.send_cmd_LSL(outlet, 'audio', 'play', play_plan)
                while audio_state_dict["audio_status"] != AudioStatus.TERMINATED:
                    time.sleep(1)
                audio_state_dict["audio_status"] = AudioStatus.INITIAL
                utils.send_cmd_LSL(outlet, 'acq', 'stop_recording')
        elif val.lower() == 'n':
            break