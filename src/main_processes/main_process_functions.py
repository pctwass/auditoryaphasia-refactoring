import multiprocessing
import os
import json
import time
import matplotlib
matplotlib.use('tkagg')

from pylsl import StreamOutlet

import auditory_aphasia.config.config as config
import auditory_aphasia.config.system_config as system_config
import auditory_aphasia.config.classifier_config as classifier_config
import auditory_aphasia.common.utils as utils
import auditory_aphasia.process_management.intermodule_communication as intermodule_comm

from auditory_aphasia.process_management.process_manager import ProcessManager

from auditory_aphasia.logging.logger import get_logger
logger = get_logger()


def generate_meta_file(session_type:str):
    meta = dict()
    meta['session_type'] = session_type
    meta['words'] = config.words
    with open(os.path.join(system_config.data_dir, system_config.save_folder_name, 'meta.json'), 'w') as f:
        json.dump(meta, f, indent=4)


def create_and_start_subprocesses() -> tuple[multiprocessing.Process, multiprocessing.Process, multiprocessing.Process, multiprocessing.Process, dict[str, any], dict[str, any], dict[str, any], dict[str, any]]:
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
    kwargs_acquisition=dict(name='acq', name_main_outlet='main')
    kwargs_live_barplot=dict(words=config.words)
    acquisition_process, acquisition_state_dict, live_barplot_process, live_barplot_state_dict = process_manager.create_acquisition_process(num_classes=classifier_config.n_class, kwargs=kwargs_acquisition, kwargs_live_barplot=kwargs_live_barplot)
    acquisition_process.start()
    live_barplot_process.start()
    while acquisition_state_dict["LSL_inlet_connected"] is False:
        time.sleep(0.1) # wait until module is connected

    return audio_stim_process, visual_fb_process, acquisition_process, live_barplot_process, audio_stim_state_dict, visual_fb_state_dict, acquisition_state_dict, live_barplot_state_dict


def open_audio_device(
        intermodule_comm_outlet : StreamOutlet, 
        audio_stim_state_dict : dict[str,any]
):
    logger.info("open audio device")
    audio_stim_state_dict["LSL_inlet_connected"] = False
    intermodule_comm.send_cmd_LSL(intermodule_comm_outlet, 'audio', 'open')

    while audio_stim_state_dict["LSL_inlet_connected"] is False:
        time.sleep(0.1)


def launch_acquisition(
        intermodule_comm_outlet : StreamOutlet, 
        condition : str,
        soa : float
):
    intermodule_comm.send_cmd_LSL(intermodule_comm_outlet, 'acq', 'init')

    intermodule_comm.send_params_LSL(intermodule_comm_outlet, 'acq', 'condition', condition)
    intermodule_comm.send_params_LSL(intermodule_comm_outlet, 'acq', 'soa', soa)


def gen_eeg_fname(
        dir_base : str, 
        f_name_prefix : str, 
        condition : str, 
        soa : float, 
        idx_run : int, 
        extension : str, 
        session_type : str = None
):
    """
    Parameters
    ==========
    session_type : str, 'pre' or 'post', Default = None
        specify presession or postsession if it's offline session
        None is corresponding to online session

    """
    if session_type is None:
        f_name = os.path.join(dir_base,
                            f_name_prefix + "_" + condition + "_" + str(int(soa*1000)) + "_" + str(idx_run+1).zfill(4))
    elif session_type == 'pre':
        f_name = os.path.join(dir_base,
                            f_name_prefix + "_pre_" + condition + "_" + str(int(soa*1000)) + "_" + str(idx_run+1).zfill(4))
    elif session_type == 'post':
        f_name = os.path.join(dir_base,
                            f_name_prefix + "_post_" + condition + "_" + str(int(soa*1000)) + "_" + str(idx_run+1).zfill(4))
    else:
        raise ValueError("Unknown session type : %s" %str(session_type))
    
    f_name = utils.check_file_exists_on_extenstion(f_name, extension)
    return f_name