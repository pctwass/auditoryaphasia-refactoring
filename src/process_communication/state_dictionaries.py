from process_communication.process_communication_enums import *


def init_audio_state_dict():
    audio_state_dict : dict = {
        "LSL_inlet_connected" : False ,
        "audio_status" : AudioStatus.INITIAL,
        "trial_marker" :  0,
    }
    return audio_state_dict


def init_visual_fb_state_dict():
    visual_fb_state_dict : dict = {
        "LSL_inlet_connected" : False 
    }
    return visual_fb_state_dict


def init_acquisition_state_dict():
    acquisition_state_dict : dict = {
        "LSL_inlet_connected" : False, 
        "active_trial" : False,
        "trial_classification_status" : TrialClassificationStatus.UNDECODED,
        "trial_label" : 0,
        "trial_stimulus_count" : 0,
        "acquire_trials" : False
    }
    return acquisition_state_dict