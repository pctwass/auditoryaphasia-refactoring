import sys
import os
import time
import pyscab

from pylsl import StreamOutlet

import src.config.config as config
import src.config.system_config as system_config
import config.temp_new_conf as temp_new_conf
import src.common.utils as utils
import src.condition_params as condition_params
import src.process_management.intermodule_communication as intermodule_comm

from src.main_processes.main_process_functions import *
from src.common.eyes_open_close import run_eyes_open_close
from src.common.oddball import run_oddball
from src.process_management.process_communication_enums import *
from src.plans.run_plan import generate_run_plan
from src.plans.trial_plan import generate_trial_plan
# from src.common.utils import *

# conf_system.set_logger(True, True, level_file = 'debug', level_stdout = 'info')
import logging
logger = logging.getLogger(__name__)


def main():
    # make directory to save files
    isExist = os.path.exists(os.path.join(system_config.data_dir, system_config.save_folder_name))
    if not isExist:
        os.makedirs(os.path.join(system_config.data_dir, system_config.save_folder_name))

    generate_meta_file(session_type='offline')

    sys.path.append(system_config.repository_dir_base)

    logger.debug("computer : %s" %system_config.computer_name)
    logger.debug("subject code : %s" %config.subject_code)

    #----------------------------------------------------------------------
    # start stimulation

    # set up intermodule communication LSL, subprocess modules, and open the audio device
    intermodule_comm_outlet = intermodule_comm.create_intermodule_communication_outlet('main', channel_count=4, source_id='auditory_aphasia_main')
    audio_stim_process, visual_fb_process, acquisition_process, live_barplot_process, audio_stim_state_dict, _, _ = create_and_start_subprocesses()
    open_audio_device(intermodule_comm_outlet, audio_stim_state_dict)

    # initiate recorder if managed locally
    if temp_new_conf.init_recorder_locally:
        logger.info("starting recorder")
        intermodule_comm.send_cmd_LSL(intermodule_comm_outlet, 'acq', 'init_recorder', {'session_type':'offline'})
    time.sleep(1)

    # eyes open close, pre
    user_input_play_eyes_open_close = input("Do you want to record eyes open closed? [y]/n : ")
    if user_input_play_eyes_open_close == "" or user_input_play_eyes_open_close.lower() == 'y':
        run_eyes_open_close(intermodule_comm_outlet, 'pre')

    # oddball
    user_input_play_oddball = input("Do you want to play oddball? [y]/n : ")
    if user_input_play_oddball == "" or user_input_play_oddball.lower() == 'y':
        run_oddball(intermodule_comm_outlet, audio_stim_state_dict, number_of_repetitions = config.oddball_n_reps)

    idx_run_offset = 0
    if config.initial_run_offline != 1:
        condition_plan = config.condition_offline[config.initial_run_offline-1:]
        idx_run_offset += config.initial_run_offline-1
    else:
        condition_plan = config.condition_offline

    # main loop
    execute_run_for_each_condition(
        condition_plan,
        idx_run_offset,
        intermodule_comm_outlet,
        audio_stim_state_dict
    )
    
    # eyes open close, post
    user_input_play_eyes_open_close = input("Do you want to record eyes open closed? [y]/n : ")
    if user_input_play_eyes_open_close == "" or user_input_play_eyes_open_close.lower() == 'y':
        run_eyes_open_close(intermodule_comm_outlet, 'post')

    # close audio device
    intermodule_comm.send_cmd_LSL(intermodule_comm_outlet, 'audio','close')
    time.sleep(3)

    # terminate subprocesses
    audio_stim_process.terminate()
    visual_fb_process.terminate()
    acquisition_process.terminate()
    live_barplot_process.terminate()

    logger.info("All procceses were terminated. Exit program.")


def execute_run_for_each_condition(
    condition_plan : enumerate[str],
    idx_run_offset : int,
    intermodule_comm_outlet : StreamOutlet,
    audio_stim_state_dict : dict[str,any]
):
    audio_files_dir_base = system_config.audio_files_dir_base
    number_of_words = system_config.number_of_words
    master_volume = config.master_volume
    words = config.words

    for idx_run, condition in enumerate(condition_plan):
        idx_run += idx_run_offset
        soa = config.soa_offline[idx_run]

        time.sleep(1)
        input("Press Any Key to Start a New Run, %s, SOA %sms" %(condition, soa))
        logger.debug("new run started, %d out of %d" %(idx_run+1, len(config.condition_offline)))
        logger.debug("condition of run : %s" %condition)
        
        plan_run = generate_run_plan(
            audio_files_dir_base,
            words,
            condition,
            condition_params.conditions[condition],
            master_volume
        )

        audio_info = plan_run['audio_info']
        audio_files = plan_run['audio_files']
        word_to_speak = plan_run['word_to_speak']
        target_plan = plan_run['targetplan']

        intermodule_comm.send_params_LSL(intermodule_comm_outlet, 'audio', 'audio_info', audio_info)
        intermodule_comm.send_params_LSL(intermodule_comm_outlet, 'audio', 'marker', True)
        
        f_name = gen_eeg_fname(os.path.join(system_config.data_dir, system_config.save_folder_name), config.callibration_file_name_prefix, condition, soa, idx_run, 'eeg', session_type = config.offline_session_type)
        
        if temp_new_conf.init_recorder_locally:
            intermodule_comm.send_cmd_LSL(intermodule_comm_outlet, 'acq','start_recording', f_name)

        execute_trial_for_each_word(
            intermodule_comm_outlet,
            audio_stim_state_dict,
            audio_files,
            word_to_speak,
            target_plan,
            condition,
            soa,
            number_of_words
        )

        if temp_new_conf.init_recorder_locally:
            intermodule_comm.send_cmd_LSL(intermodule_comm_outlet, 'acq', 'stop_recording')


def execute_trial_for_each_word(
    intermodule_comm_outlet : StreamOutlet,
    audio_stim_state_dict : dict[str,any],
    audio_files : pyscab.DataHandler,
    word_to_speak : str, # Typing is not entirely certain
    target_plan, # Type couldn't be determined
    condition : str,
    soa : float,
    number_of_words : int
):
    for word_idx in range(number_of_words):
        audio_stim_state_dict[0] = 0
        target = target_plan[word_idx]

        plan_trial = generate_trial_plan(audio_files,
                                                word_to_speak,
                                                target,
                                                condition,
                                                soa,
                                                config.number_of_repetitions,
                                                number_of_words,
                                                system_config.channel_speaker,
                                                system_config.channel_headphone,
                                                condition_params.conditions[condition],
                                                online=False)
        
        word = config.words[target-1]
        logger.debug("word : %s" %word)

        sentence_data = pyscab.DataHandler()
        sentence_data.load(0, os.path.join(system_config.repository_dir_base,
                                            'media',
                                            'audio',
                                            config.language,
                                            'sentences',
                                            condition,
                                            word,
                                            '1.wav'))
        sentence_duration = sentence_data.get_length_by_id(0)

        logger.info("plan_trial : %s" %str(plan_trial))
        play_plan = plan_trial['play_plan']
        intermodule_comm.send_cmd_LSL(intermodule_comm_outlet, 'audio', 'play', play_plan)

        marker = int(audio_stim_state_dict["trial_marker"])
        marker = 0

        # Provide visual feedback and wait until the audio has finished playing
        show_speaker_diagram = condition_params.conditions[condition]["show_speaker_diagram"]
        while True:
            if int(audio_stim_state_dict["trial_marker"]) != marker and show_speaker_diagram:
                marker = int(audio_stim_state_dict["trial_marker"])
                if marker in system_config.markers['new-trial']:  
                    intermodule_comm.send_cmd_LSL(intermodule_comm_outlet, 'visual', 'highlight_speaker', {'spk_num':word_to_speak[marker-200], 'duration':sentence_duration})
                elif marker == 210:
                    intermodule_comm.send_cmd_LSL(intermodule_comm_outlet, 'visual', 'show_speaker')

            if audio_stim_state_dict["audio_status"].value == AudioStatus.TERMINATED.value:
                audio_stim_state_dict["audio_status"] = AudioStatus.INITIAL
                break

            time.sleep(0.01)
            
        time.sleep(system_config.pause_between_trial)