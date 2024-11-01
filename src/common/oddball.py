import os
import time
import pyscab

import config.conf as conf
import config.conf_system as conf_system
import utils

import logging
logger = logging.getLogger(__name__)

from src.process_management.process_communication_enums import AudioStatus


def run_oddball(
    outlet, 
    audio_state_dict, 
    number_of_repetitions = None
):
    if number_of_repetitions is None:
        number_of_repetitions = conf.oddball_n_reps

    while True:
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

        for i in range(number_of_repetitions):
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

        # ask the user if they want to repeat the procedure (default choice: 'yes')
        user_input_repeat_procedure = input("Do you want to play oddball again? [y]/n : ")
        if not user_input_repeat_procedure == "" or not user_input_repeat_procedure.lower() == 'y':
            break