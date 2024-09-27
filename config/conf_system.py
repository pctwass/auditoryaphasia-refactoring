import os
import sys
import datetime
import json # for loading conf variables
from psychopy import core, gui

import logging
logger = logging.getLogger(__name__)

import config.conf_selector
# exec("import %s as conf" % (conf_selector.conf_file_name))
# exec("import %s as conf_system" % (conf_selector.conf_system_file_name))
import config.conf as conf

import socket
computer_name = socket.gethostname().lower()

# ------------------------------------------------------------------------
# General

repository_dir_base = os.path.join('D:/','Users','aphasia','auditoryAphasia-python')
data_dir = os.path.join('D:/', 'home', 'bbci')

sys.path.append(repository_dir_base)

len_shared_memory = 8
datestr =  datetime.datetime.now().strftime("%y_%m_%d")
save_folder_name = conf.subject_code + "_" + datestr
log_file_name = datestr + ".log"

f_name_prefix = 'AuditoryAphasia'

number_of_words = len(conf.words)


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
# Marker

from markerbci import buttonbox
class Marker(object):
    def __init__(self, port=conf.port, marker_duration = 0.05):
        self.port = port
        self.marker_duration = marker_duration

    def open(self):
        self._bb = buttonbox.ButtonBoxBci(port=self.port)

    def close(self):
        self._bb.close()

    def sendMarker(self, val):
        self._bb.sendMarker(val=val)

# ------------------------------------------------------------------------
# LSL settings
enable_stream_inlet_recover = False

# ------------------------------------------------------------------------
# Audio

audio_files_dir_base = os.path.join(repository_dir_base,
                                    'media',
                                    'audio',
                                    conf.language)

n_ch = 8
device_name = 'X-AIR ASIO Driver'

format = "INT16"
frames_per_buffer = 512

correct_sw_latency = True
correct_hw_latency = 512

ch_speaker = [1,2,3,4,5,6]
ch_headphone = [7,8]

# ------------------------------------------------------------------------
# Visual
visual_images_dir_base = os.path.join(repository_dir_base,
                                    'media',
                                    'images')

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

rda_lsl_dir = os.path.join(repository_dir_base, 'lsl', 'BrainVisionRDA_x64', 'BrainVisionRDA.exe')
rda_lsl_config_dir = os.path.join(repository_dir_base, 'lsl', 'BrainVisionRDA_x64', 'brainvision_config.cfg')

marker_stream_keyword = 'RDA'

# Rec have to be global
Rec = None

def initialize_recorder(param):
    import subprocess
    try:
        import win32com.client as win32
        logger.debug("win32com.client was imported")
    except:
        logger.debug("Error : loading package pywin32 was failed, try these commands 'python Scripts/pywin32_postinstall.py -install'")
        print("Error : loading package pywin32 was failed, try these commands 'python Scripts/pywin32_postinstall.py -install'")

    global Rec
    Rec = win32.gencache.EnsureDispatch('VisionRecorder.Application')
    Rec.Acquisition.StopRecording()
    Rec.Acquisition.StopViewing()
    if param['session_type'] == 'online':
        #Rec.CurrentWorkspace.Load(os.path.join(repository_dir_base,"workspace",'9ch_selftest.rwksp'))
        Rec.CurrentWorkspace.Load(os.path.join(repository_dir_base,"lsl", 'config', 'BrainVisionRecorder',conf.recorder_config_offline))
        subprocess.Popen("%s -c %s" %(rda_lsl_dir, rda_lsl_config_dir))
    elif param['session_type'] == 'offline':
        #Rec.CurrentWorkspace.Load(os.path.join(repository_dir_base,"workspace",'9ch_selftest.rwksp'))
        Rec.CurrentWorkspace.Load(os.path.join(repository_dir_base, "lsl", 'config', 'BrainVisionRecorder', conf.recorder_config_online))
    Rec.Acquisition.ViewData()

def start_recording(f_dir):
    global Rec
    if f_dir[-4:] != '.eeg':
        f_dir += '.eeg'
    Rec.Acquisition.ViewData()
    Rec.Acquisition.StartRecording(f_dir)

def stop_recording():
    global Rec
    Rec.Acquisition.StopRecording()
    #Rec.Acquisition.StopViewing()


# ------------------------------------------------------------------------
# ERP Classification

# Plotting 
show_barplot = True

# load classifier configuration file
with open(os.path.join(repository_dir_base, 'config', 'conf_clf.json')) as f:
    conf_clf = json.load(f)
# load into local variables
locals().update(conf_clf) 

#eog_channels = ['EOGvu']
#misc_channels = ['x_EMGl', 'x_GSR', 'x_Respi', 'x_Pulse', 'x_Optic']

# TODO: grab these in new config loader script
n_channels = len(conf.channel_labels_online)
n_class = len(conf.words)
n_stimulus = n_class*conf.number_of_repetitions
markers_to_epoch = markers['target'] + markers['nontarget'] # loaded from conf_clf

def filter_mne(data, sos):
    # filter function which will be handed to mne.io.Raw.apply_function()
    #
    # USE THIS WITH channel_wise = False
    #

    # data has shape of (n_times,) if channel_wise=True and (len(picks), n_times) if False.
    # see details for mne documentation.

    from scipy import signal
    r = signal.sosfilt(sos, data, axis=1)

    return r

def get_calibration_data(params):
    import utils
    import mne
    from scipy import signal
    import numpy as np

    #mne.set_log_level(verbose=False)

    condition = params['condition']
    soa = params['soa']


    n_sessions = utils.get_n_sessions(data_dir, conf.subject_code, datestr)
    logger.info("n_sessions : %s" %str(n_sessions))

    files_for_calibration = utils.get_files_for_calibration(n_sessions = n_sessions,
                                                            data_dir = data_dir,
                                                            extension = 'vhdr',
                                                            soa_ms = int(soa*1000),
                                                            condition = condition,
                                                            f_name_prefix = conf.f_name_prefix,
                                                            th_soa_ms = 350)

    logger.info("files_for_calibration : %s" %str(files_for_calibration))

    myDlg = gui.Dlg(title="Calibration files")
    myDlg.addField("Found the following files for calibration:\n"+'\n'.join([' - '+str(f) for f in files_for_calibration])+'\n\nContinue?')
    ok_data = myDlg.show()  # show dialog and wait for OK or Cancel
    if not myDlg.OK:  # quit if the user pressed cancel
        core.quit()
    # not working because of Psychopy:
    # print("\nFound the following files for calibration:")
    # for f in files_for_calibration:
    #     print(' - '+str(f))
    # while True:
    #     try:
    #         answer = input("Do you want to continue? [y]/n : ")
    #         if answer == "" or answer.lower() == 'y':
    #             break 
    #         elif answer.lower() == 'n':
    #             exit('0')
    #         else:
    #             print('Invalid answer: '+str(answer))
    #     except EOFError:
    #         print('EOF')

    if len(files_for_calibration) == 0:
        logger.error("ERROR : data for subject %s was not found." %conf.subject_code)
        #print("ERROR : data for subject %s was not found." %subject_code)
    raws = list()
    for file in files_for_calibration:
        raw = mne.io.read_raw(file,
                              preload = True)
                              #eog = eog_channels,
                              #misc = misc_channels)
        sos = signal.butter(filter_order, np.array(filter_freq)/(raw.info['sfreq']/2), 'bandpass', output='sos')
        raw.apply_function(filter_mne, channel_wise=False, sos=sos)
        raws.append(raw)
    print(raws)
    raw = mne.concatenate_raws(raws)
    events, event_id = mne.events_from_annotations(raw)

    raw.pick_channels(ch_names = conf.channel_labels_online)
    #raw.pick_types(eeg=True)

    return mne.Epochs(raw, events, event_id=markers_to_epoch, tmin=tmin, tmax=tmax, baseline=baseline)

def set_logger(file=True, stdout=True, level_file = 'debug', level_stdout = 'info'):
    """
    level : 'debug' or 'info'
    """
    import logging

    if level_file.lower() == 'debug':
        level_file = logging.DEBUG
    elif level_file.lower() == 'info':
        level_file = logging.INFO

    if level_stdout.lower() == 'debug':
        level_stdout = logging.DEBUG
    elif level_stdout.lower() == 'info':
        level_stdout = logging.INFO

    log_format = '%(asctime)s [%(levelname)s] [%(module)s.%(funcName)s] %(message)s'

    root_logger = logging.getLogger(None)
    root_logger.setLevel(logging.DEBUG)

    if stdout:
        stdout_handler = logging.StreamHandler(stream=sys.stdout)
        stdout_handler.setFormatter(logging.Formatter(log_format))
        stdout_handler.setLevel(level_stdout)
        root_logger.addHandler(stdout_handler)

    if file:
        log_dir = os.path.join(os.getcwd(), "temp", "logging") #os.path.join(data_dir, save_folder_name)
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)
        file_handler = logging.FileHandler(os.path.join(log_dir, log_file_name))
        file_handler.setFormatter(logging.Formatter(log_format))
        file_handler.setLevel(level_file)
        root_logger.addHandler(file_handler)
