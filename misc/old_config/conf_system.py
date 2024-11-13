import os
import sys
import datetime
from pathlib import Path
import json # for loading conf variables

from src.logging.logger import get_logger
logger = get_logger()

import config.conf_selector
import config.conf_selector as conf_selector
import src.config.config as config

import socket
computer_name = socket.gethostname().lower()

# ------------------------------------------------------------------------
# General

repository_dir_base = Path(os.path.abspath(__file__)).parents[1]
data_dir = os.path.join('D:/', 'home', 'bbci')

sys.path.append(repository_dir_base)

len_shared_memory = 8
datestr =  datetime.datetime.now().strftime("%y_%m_%d")
save_folder_name = config.subject_code + "_" + datestr
log_file_name = datestr + ".log"

file_name_prefix = 'AuditoryAphasia'

number_of_words = len(config.words)


eye_open_close_time = 60

oddball_target = '1000.wav'
oddball_non_target = '500.wav'
oddball_marker = dict()
oddball_marker['target'] = 21
oddball_marker['nontarget'] = 1
oddball_channels = [1]

enable_pause_between_trial = False

pause_after_start_sound = 2
pause_between_sentence_and_subtrial = 3.5
pause_after_trial = 2
pause_between_trial = 5
pause_before_feedback = 1


# ------------------------------------------------------------------------
# Dareplane
dareplane_api_ip : str = "127.0.0.1"
dareplane_api_port : int = 8001 


# ------------------------------------------------------------------------
# Marker
from clients.marker.button_box_bci_marker_client import ButtonBoxBciMarkerClient
MarkerClient = ButtonBoxBciMarkerClient

markers = dict()
markers['target'] = [111,112,113,114,115,116]
markers['nontarget'] = [101,102,103,104,105,106]
markers['new-trial'] = [200,201,202,203,204,205]


# ------------------------------------------------------------------------
# LSL settings
enable_stream_inlet_recover = False

# ------------------------------------------------------------------------
# Audio
audio_files_dir_base = os.path.join('media', 'audio')

n_channels = 8
device_name = 'X-AIR ASIO Driver'

format = "INT16"
frames_per_buffer = 512

correct_sw_latency = True
correct_hw_latency = 512

channel_speaker = [1,2,3,4,5,6]
channel_headphone = [7,8]

# ------------------------------------------------------------------------
# Visual
visual_images_dir_base = os.path.join('media', 'images')

background_color = [-1, -1, -1]  # 0, 0, 0
foreground_color = [1, 1, 1]  # 255, 255, 255
highlight_color = [0.59375, -1, -1]  # 204, 0, 0

size_smiley = [0.5]
size_eye_open_close = [1.0]
size_dancing_gif = [0.7]
#size_barplot = [1.0]

enable_fullscreen = True

# ------------------------------------------------------------------------
# Acquisition
from clients.recorder.brain_vision_recorder_client import BrainVisionRecorderClient
RecorderClient = BrainVisionRecorderClient

from clients.formatting.brain_vision_formatting_client import BrainVisionFromattingClient
FormattingClient = BrainVisionFromattingClient

init_recorder_locally : bool = True

rda_lsl_dir = os.path.join('lsl', 'BrainVisionRDA_x64', 'BrainVisionRDA.exe')
rda_lsl_config_dir = os.path.join('lsl', 'BrainVisionRDA_x64', 'brainvision_config.cfg')

marker_stream_keyword = 'RDA'

eeg_acquisition_stream_name : str = "eeg_stream"
eeg_acquisition_stream_type : str = "eeg"
marker_acquisition_stream_name : str = "marker_stream"
marker_acquisition_stream_type : str = "markers"
marker_stream_await_timeout_ms : int|float = 1000 


# ------------------------------------------------------------------------
# ERP Classification

# Plotting 
show_live_classification_barplot = True

# load classifier configuration file
with open(os.path.join(repository_dir_base, 'config', conf_selector.conf_classifier_file_name+'.json')) as f:
    conf_clf = json.load(f)
# load into local variables
locals().update(conf_clf) 

#eog_channels = ['EOGvu']
#misc_channels = ['x_EMGl', 'x_GSR', 'x_Respi', 'x_Pulse', 'x_Optic']

# TODO: grab these in new config loader script
n_channels = len(config.channel_labels_online)
n_class = len(config.words)
n_stimulus = n_class*config.number_of_repetitions
markers_to_epoch = markers['target'] + markers['nontarget'] # loaded from conf_clf

from classifier.toeplitz_LDA_pipeline import ToeplitzLDAPipeline
ClassificationPipelineClass = ToeplitzLDAPipeline

from classifier.calibration_data_provider import CallibrationDataProvider
CallibrationDataProviderClass = CallibrationDataProvider
