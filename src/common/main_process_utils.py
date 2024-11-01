import multiprocessing
import os
import json
import time
import matplotlib
matplotlib.use('tkagg')

from pylsl import StreamOutlet

import config.conf as conf
import config.conf_system as conf_system
import utils

from process_management.process_manager import ProcessManager

conf_system.set_logger(True, True, level_file = 'debug', level_stdout = 'info')

import logging
logger = logging.getLogger(__name__)


def generate_meta_file(session_type:str):
    meta = dict()
    meta['session_type'] = session_type
    meta['words'] = conf.words
    with open(os.path.join(conf_system.data_dir, conf_system.save_folder_name, 'meta.json'), 'w') as f:
        json.dump(meta, f, indent=4)


def create_and_start_subprocesses() -> tuple[multiprocessing.Process, multiprocessing.Process, multiprocessing.Process, dict[str, any], dict[str, any], dict[str, any]]:
    # create process manager
    process_manager = ProcessManager()

    # open AudioStimulationController as a new Process
    audio_stim_process, audio_stim_state_dict = process_manager.create_audio_stim_process(kwargs=dict(name='audio', name_main_outlet='main'))
    audio_stim_process.start()
    while audio_stim_state_dict["LSL_inlet_connected"] is False:
        time.sleep(0.1) # wait until module is connected

    # open VisualFeedbackController as a new Process
    visual_fb_process, visual_fb_state_dict = process_manager.create_visual_fb_process(kwargs=dict(name='visual', name_main_outlet='main'))
    visual_fb_process.start()
    while visual_fb_state_dict["LSL_inlet_connected"] is False:
        time.sleep(0.1) # wait until module is connected

    # open AcquisitionSystemController as a new Process
    acquisition_process, acquisition_state_dict = process_manager.create_acquisition_process(args=['acq', 'main', False, False])
    acquisition_process.start()
    while acquisition_state_dict["LSL_inlet_connected"] is False:
        time.sleep(0.1) # wait until module is connected

    return audio_stim_process, visual_fb_process, acquisition_process, audio_stim_state_dict, visual_fb_state_dict, acquisition_state_dict


def open_audio_device(
        intermodule_comm_outlet : StreamOutlet, 
        audio_stim_state_dict : dict[str,any]
):
    logger.info("open audio device")
    audio_stim_state_dict["LSL_inlet_connected"] = False
    utils.send_cmd_LSL(intermodule_comm_outlet, 'audio', 'open')

    while audio_stim_state_dict["LSL_inlet_connected"] is False:
        time.sleep(0.1)


def launch_acquisition(
        intermodule_comm_outlet : StreamOutlet, 
        condition : str,
        soa : float
):
    utils.send_cmd_LSL(intermodule_comm_outlet, 'acq', 'init')
    utils.send_cmd_LSL(intermodule_comm_outlet, 'acq', 'connect_LSL')
    utils.send_cmd_LSL(intermodule_comm_outlet, 'acq', 'set')

    utils.send_params_LSL(intermodule_comm_outlet, 'acq', 'condition', condition)
    utils.send_params_LSL(intermodule_comm_outlet, 'acq', 'soa', soa)