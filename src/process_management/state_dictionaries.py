import multiprocessing
from src.process_management.process_communication_enums import *


# There are reference to an index 3 of the below dict. This 4th (index 3) entry has not been implemented
# due to it not being used (only in commented-out code). 
def init_audio_state_dict(manager : multiprocessing.Manager = None) -> dict[str, any]:
    if manager is None:
        audio_state_dict : dict = {}
    else :
        audio_state_dict = manager.dict()

    audio_state_dict["LSL_inlet_connected"] = False
    audio_state_dict["audio_status"] = AudioStatus.INITIAL
    audio_state_dict["trial_marker"] = 0

    return audio_state_dict


def init_visual_fb_state_dict(manager : multiprocessing.Manager) -> dict[str, any]:
    if manager is None:
        visual_fb_state_dict : dict = {}
    else :
        visual_fb_state_dict = manager.dict()

    visual_fb_state_dict["LSL_inlet_connected"] = False

    return visual_fb_state_dict


def init_acquisition_state_dict(manager : multiprocessing.Manager) -> dict[str, any]:
    if manager is None:
        acquisition_state_dict : dict = {}
    else :
        acquisition_state_dict = manager.dict()

    acquisition_state_dict["LSL_inlet_connected"] = False
    acquisition_state_dict["trial_completed"] = True
    acquisition_state_dict["trial_classification_status"] = TrialClassificationStatus.UNDECODED
    acquisition_state_dict["trial_label"] = 0
    acquisition_state_dict["trial_stimulus_count"] = 0
    acquisition_state_dict["acquire_trials"] = False

    return acquisition_state_dict


def init_live_barplot_state_dict(manager : multiprocessing.Manager, num_classes : int) -> dict[str, any]:
    if manager is None:
        live_barplot_state_dict : dict = {}
    else :
        live_barplot_state_dict = manager.dict()
    
    live_barplot_state_dict["display_barplot"] = False
    live_barplot_state_dict["mean_classificaiton_values"] = multiprocessing.Array(
                "d", [0 for m in range(num_classes)])
    live_barplot_state_dict["index_best_class"] = None
            
    return live_barplot_state_dict