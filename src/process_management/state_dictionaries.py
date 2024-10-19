import multiprocessing
from src.process_management.process_communication_enums import *


# There are reference to an index 3 of the below dict. This 4th (index 3) entry has not been implemented
# due to it not being used (only in commented-out code). 
def init_audio_state_dict(manager : multiprocessing.Manager = None) -> dict[str, any]:
    if manager is None:
        audio_state_dict : dict = {
            "LSL_inlet_connected" : False ,
            "audio_status" : AudioStatus.INITIAL,
            "trial_marker" :  0,
        }
    else:
        audio_state_dict : manager.dict = {
            "LSL_inlet_connected" : False ,
            "audio_status" : AudioStatus.INITIAL,
            "trial_marker" :  0,
        }
    return audio_state_dict


def init_visual_fb_state_dict(manager : multiprocessing.Manager) -> dict[str, any]:
    visual_fb_state_dict : manager.dict = {
        "LSL_inlet_connected" : False 
    }
    return visual_fb_state_dict


def init_acquisition_state_dict(manager : multiprocessing.Manager) -> dict[str, any]:
    acquisition_state_dict : manager.dict = {
        "LSL_inlet_connected" : False, 
        "trial_completed" : True,
        "trial_classification_status" : TrialClassificationStatus.UNDECODED,
        "trial_label" : 0,
        "trial_stimulus_count" : 0,
        "acquire_trials" : False
    }
    return acquisition_state_dict


def init_live_barplot_state_dict(manager : multiprocessing.Manager, num_classes : int) -> dict[str, any]:
    live_barplot_state_dict : manager.dict = {
        "mean_classificaiton_values" :  multiprocessing.Array(
                "d", [0 for m in range(num_classes)]
            ),
        "index_best_class" : None
    }
    return live_barplot_state_dict