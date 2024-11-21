import os
import sys
import time

import config.temp_new_conf as temp_new_conf
import matplotlib
import numpy as np
import pyscab
from pylsl import StreamOutlet

import auditory_aphasia.condition_params as condition_params
import auditory_aphasia.process_management.intermodule_communication as intermodule_comm
from auditory_aphasia.common.eyes_open_close import run_eyes_open_close
from auditory_aphasia.common.oddball import run_oddball
from auditory_aphasia.config_builder import GeneralConfig, SystemConfig
from auditory_aphasia.logging.logger import get_logger
from auditory_aphasia.main_processes.main_process_functions import (
    classifier_config, create_and_start_subprocesses, generate_meta_file,
    launch_acquisition, open_audio_device)
from auditory_aphasia.plans.feedback_plan import generate_feedback_plan
from auditory_aphasia.plans.run_plan import generate_run_plan
from auditory_aphasia.plans.trial_plan import generate_trial_plan
from auditory_aphasia.process_management.process_communication_enums import (
    AudioStatus, TrialClassificationStatus)

matplotlib.use("tkagg")
logger = get_logger()


def run_main(config: GeneralConfig, system_config: SystemConfig):
    # make directory to save files
    isExist = os.path.exists(
        os.path.join(system_config.data_dir, system_config.save_folder_name)
    )
    if not isExist:
        os.makedirs(
            os.path.join(system_config.data_dir, system_config.save_folder_name)
        )

    generate_meta_file(session_type="online")

    sys.path.append(system_config.repository_dir_base)

    logger.debug("computer : %s" % system_config.computer_name)
    logger.debug("subject code : %s" % config.subject_code)

    condition = config.condition_online
    soa = config.soa_online

    # ----------------------------------------------------------------------
    # start stimulation

    # set up intermodule communication LSL, subprocess modules, and open the audio device
    intermodule_comm_outlet = intermodule_comm.create_intermodule_communication_outlet(
        "main", channel_count=4, source_id="auditory_aphasia_main"
    )
    (
        audio_stim_process,
        visual_fb_process,
        acquisition_process,
        live_barplot_process,
        audio_stim_state_dict,
        _,
        acquisition_state_dict,
        _,
    ) = create_and_start_subprocesses()
    open_audio_device(intermodule_comm_outlet, audio_stim_state_dict)

    if temp_new_conf.init_recorder_locally:
        logger.info("starting recorder")
        intermodule_comm.send_cmd_LSL(
            intermodule_comm_outlet, "acq", "init_recorder", {"session_type": "online"}
        )
    time.sleep(1)

    # eyes open close, pre
    user_input_play_eyes_open_close = input(
        "Do you want to record eyes open closed? [y]/n : "
    )
    if (
        user_input_play_eyes_open_close == ""
        or user_input_play_eyes_open_close.lower() == "y"
    ):
        run_eyes_open_close(intermodule_comm_outlet, "pre")

    # oddball
    user_input_play_oddball = input("Do you want to play oddball? [y]/n : ")
    if user_input_play_oddball == "" or user_input_play_oddball.lower() == "y":
        run_oddball(
            intermodule_comm_outlet,
            audio_stim_state_dict,
            number_of_repetitions=config.oddball_n_reps,
        )

    # initiate the acquisition system
    launch_acquisition(intermodule_comm_outlet, condition, soa)

    # run calibration
    intermodule_comm.send_cmd_LSL(intermodule_comm_outlet, "acq", "start_calibration")
    while acquisition_state_dict["trial_completed"] is False:
        time.sleep(0.1)

    # main loop
    execute_runs(
        config,
        system_config,
        intermodule_comm_outlet,
        audio_stim_state_dict,
        acquisition_state_dict,
        condition,
        soa,
    )

    # eyes open close, post
    user_input_play_eyes_open_close = input(
        "Do you want to record eyes open closed? [y]/n : "
    )
    if (
        user_input_play_eyes_open_close == ""
        or user_input_play_eyes_open_close.lower() == "y"
    ):
        run_eyes_open_close(intermodule_comm_outlet, "post")

    # close audio device
    intermodule_comm.send_cmd_LSL(intermodule_comm_outlet, "audio", "close")
    time.sleep(3)

    # terminate subprocesses
    audio_stim_process.terminate()
    visual_fb_process.terminate()
    acquisition_process.terminate()
    live_barplot_process.terminate()
    print("all trials ended, terminate process by main module")
    # sys.exit()


def execute_runs(
    config: GeneralConfig,
    system_config: SystemConfig,
    intermodule_comm_outlet: StreamOutlet,
    audio_stim_state_dict: dict[str, any],
    acquisition_state_dict: dict[str, any],
    condition: str,
    soa: float,
):
    audio_files_dir_base = system_config.audio_files_dir_base
    number_of_words = system_config.number_of_words
    master_volume = config.master_volume
    words = config.words

    for i in range(config.number_of_runs_online):
        plan_run = generate_run_plan(
            audio_files_dir_base,
            words,
            condition,
            condition_params.conditions[condition],
            master_volume,
        )

        audio_info = plan_run["audio_info"]
        audio_files = plan_run["audio_files"]
        word_to_speak = plan_run["word_to_speak"]
        target_plan = plan_run["targetplan"]

        n_runs = 1
        while True:
            # f_name = gen_eeg_fname(os.path.join(conf.data_dir, conf.save_folder_name), conf.f_name_prefix, condition, soa, idx_run)
            f_name = os.path.join(
                system_config.data_dir,
                system_config.save_folder_name,
                "%s_%s_%s_%s.%s"
                % (
                    config.callibration_file_name_prefix,
                    condition,
                    str(int(soa * 1000)),
                    str(n_runs).zfill(4),
                    "eeg",
                ),
            )
            print(f_name)
            if os.path.exists(f_name):
                n_runs += 1
            else:
                break

        time.sleep(1)
        val = input(
            "Press Any Key to Start A New Run (No.%d) or type 'n' to terminate : "
            % n_runs
        )
        if val.lower() == "n":
            break

        logger.info("plan_run : %s" % str(plan_run))

        # start acquisition for run
        if temp_new_conf.init_recorder_locally:
            intermodule_comm.send_cmd_LSL(
                intermodule_comm_outlet, "acq", "start_recording", f_name
            )
        intermodule_comm.send_cmd_LSL(intermodule_comm_outlet, "acq", "start")

        execute_trial_for_each_word(
            config,
            system_config,
            intermodule_comm_outlet,
            audio_stim_state_dict,
            acquisition_state_dict,
            audio_info,
            audio_files,
            word_to_speak,
            target_plan,
            condition,
            soa,
            audio_files_dir_base,
            number_of_words,
            master_volume,
            words,
        )

        # stop acquisition
        acquisition_state_dict["acquire_trials"] = False
        if temp_new_conf.init_recorder_locally:
            intermodule_comm.send_cmd_LSL(
                intermodule_comm_outlet, "acq", "stop_recording"
            )


def execute_trial_for_each_word(
    config: GeneralConfig,
    system_config: SystemConfig,
    intermodule_comm_outlet: StreamOutlet,
    audio_stim_state_dict: dict[str, any],
    acquisition_state_dict: dict[str, any],
    audio_info: list[tuple],
    audio_files: pyscab.DataHandler,
    word_to_speak: str,  # Typing is not entirely certain
    target_plan,  # Type couldn't be determined
    condition: str,
    soa: float,
    audio_files_dir_base: str,
    number_of_words: int,
    master_volume: float,
    words: list[str],
):
    number_of_words = system_config.number_of_words

    for idx, trial_num in enumerate(range(1, number_of_words + 1)):
        target = target_plan[idx]
        # time.sleep(2)

        plan_trial = generate_trial_plan(
            audio_files,
            word_to_speak,
            target,
            condition,
            soa,
            config.number_of_repetitions,
            system_config.number_of_words,
            system_config.channel_speaker,
            system_config.channel_headphone,
            condition_params.conditions[condition],
            online=True,
        )

        word = config.words[target - 1]
        logger.debug("word : %s" % word)
        sentence_data = pyscab.DataHandler()
        sentence_data.load(
            0,
            os.path.join(
                system_config.repository_dir_base,
                "media",
                "audio",
                config.language,
                "sentences",
                condition,
                word,
                "1.wav",
            ),
        )
        sentence_duration = sentence_data.get_length_by_id(0)

        logger.info("plan_trial : %s" % str(plan_trial))
        play_plan = plan_trial["play_plan"]
        intermodule_comm.send_params_LSL(
            intermodule_comm_outlet, "audio", "audio_info", audio_info
        )
        intermodule_comm.send_params_LSL(
            intermodule_comm_outlet, "audio", "marker", True
        )

        # intermodule_comm.send_cmd_LSL(outlet, 'acq','start_recording', os.path.join('D:/','data','test_2209'))
        intermodule_comm.send_cmd_LSL(
            intermodule_comm_outlet, "audio", "play", play_plan
        )
        acquisition_state_dict["trial_completed"] = False

        marker = int(audio_stim_state_dict["trial_marker"])

        # Provide visual feedback and wait until tiral is completed
        show_speaker_diagram = condition_params.conditions[condition][
            "show_speaker_diagram"
        ]
        while acquisition_state_dict["trial_completed"] is False:
            if (
                int(audio_stim_state_dict["trial_marker"]) != marker
                and show_speaker_diagram
            ):
                marker = int(audio_stim_state_dict["trial_marker"])
                if marker in system_config.markers["new-trial"]:
                    intermodule_comm.send_cmd_LSL(
                        intermodule_comm_outlet,
                        "visual",
                        "highlight_speaker",
                        {
                            "spk_num": word_to_speak[marker - 200],
                            "duration": sentence_duration,
                        },
                    )
                elif marker == 210:
                    intermodule_comm.send_cmd_LSL(
                        intermodule_comm_outlet, "visual", "show_speaker"
                    )
            time.sleep(0.01)

        if audio_stim_state_dict["audio_status"].value == AudioStatus.PLAYING.value:
            audio_stim_state_dict["audio_status"] = AudioStatus.FINISHED_PLAYING
        # intermodule_comm.send_cmd_LSL(outlet, 'audio', 'stop')

        # wait until the audio has finished playing
        while True:
            if (
                audio_stim_state_dict["audio_status"].value
                == AudioStatus.TERMINATED.value
            ):
                logger.info("status value is 99, terminate")
                break
            else:
                time.sleep(0.1)
                logger.info("wait for audio module is terminated")

        provide_audiovisual_feeback(
            system_config,
            intermodule_comm_outlet,
            audio_stim_state_dict,
            acquisition_state_dict,
            condition,
            audio_files_dir_base,
            master_volume,
            words,
        )

        logger.info("Trial ended, observed by main module")
        # intermodule_comm.send_cmd_LSL(outlet, 'acq', 'stop_recording')
        audio_stim_state_dict["audio_status"] = (
            AudioStatus.INITIAL
        )  # reinitialize status

        if system_config.enable_pause_between_trial:
            input("Press Any Key to Start A New Trial")
        else:
            time.sleep(system_config.pause_between_trial)


def provide_audiovisual_feeback(
    system_config: SystemConfig,
    intermodule_comm_outlet: StreamOutlet,
    audio_stim_state_dict: dict[str, any],
    acquisition_state_dict: dict[str, any],
    condition: str,
    audio_files_dir_base: str,
    master_volume: float,
    words: list[str],
):
    fb_type = acquisition_state_dict["trial_classification_status"]

    if fb_type == TrialClassificationStatus.UNDECODED:
        visual_fb = "neutral"
    elif fb_type == TrialClassificationStatus.DECODED:
        visual_fb = "positive"
    elif fb_type == TrialClassificationStatus.DECODED_EARLY:
        # TODO probably best to replace the first part of the below if statement by a unique classification state and do the check in the acquisition controller
        if (
            acquisition_state_dict["trial_stimulus_count"]
            == classifier_config.dynamic_stopping_params["min_n_stims"]
            and np.random.randint(5) == 0
        ):
            # 0.2 random chance
            visual_fb = "show_gif"
        else:
            visual_fb = "smiley"
    logger.info("feedback type ; %s" % visual_fb)

    fb_plan = generate_feedback_plan(
        audio_files_dir_base,
        words,
        acquisition_state_dict["trial_label"],
        fb_type,
        condition,
        system_config.channel_speaker,
        system_config.channel_headphone,
        condition_params.conditions[condition],
        master_volume,
    )

    intermodule_comm.send_params_LSL(
        intermodule_comm_outlet, "audio", "audio_info", fb_plan["audio_info"]
    )
    # utils.send_params_LSL(outlet, 'audio', 'marker', False)

    time.sleep(system_config.pause_before_feedback)

    if visual_fb == "show_gif":
        intermodule_comm.send_cmd_LSL(intermodule_comm_outlet, "visual", "show_gif")
    else:
        intermodule_comm.send_cmd_LSL(
            intermodule_comm_outlet, "visual", "show_" + visual_fb
        )

    intermodule_comm.send_cmd_LSL(
        intermodule_comm_outlet, "audio", "play", fb_plan["play_plan"]
    )
    audio_stim_state_dict["audio_status"] = AudioStatus.INITIAL

    while audio_stim_state_dict["audio_status"] != AudioStatus.TERMINATED:
        time.sleep(0.1)
    # time.sleep(3)
    if visual_fb != "show_gif":
        intermodule_comm.send_cmd_LSL(
            intermodule_comm_outlet, "visual", "hide_" + visual_fb
        )

