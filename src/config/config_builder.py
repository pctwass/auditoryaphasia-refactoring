import importlib
import os
import sys
import datetime
import socket
import json # for loading conf variables

from pathlib import Path
from datetime import datetime

import config.conf_selector as config_selector
import src.config.config as config
import src.config.system_config as system_config
import src.config.classifier_config as classifier_config


repository_dir_base = Path(os.path.abspath(__file__)).parents[2]


def build_configs():
    sys.path.append(repository_dir_base)

    general_config_file_path = os.path.join(repository_dir_base, 'config', config_selector.conf_file_name) + '.json'
    system_config_file_path = os.path.join(repository_dir_base, 'config', config_selector.conf_system_file_name) + '.json'
    classifier_config_file_path = os.path.join(repository_dir_base, 'config', config_selector.conf_classifier_file_name) + '.json'
    
    build_general_config(general_config_file_path)
    build_system_config(system_config_file_path)
    build_classifier_config(classifier_config_file_path)


def build_general_config(config_file_path : str):
    with open(config_file_path) as f:
        config_json_dict = json.load(f)

    config.language = config_json_dict.get('language')
    config.subject_code = config_json_dict.get('subject_code')
    config.callibration_file_name_prefix = config_json_dict.get('callibration_file_name_prefix')
    config.words = config_json_dict.get('words')
    config.number_of_repetitions = config_json_dict.get('number_of_repetitions')
    config.master_volume = config_json_dict.get('master_volume')
    config.port =  config_json_dict.get('port')
    config.screen_number = config_json_dict.get('screen_number')

    ## --- offline specific ---
    config.condition_offline = config_json_dict.get('condition_offline')
    config.soa_offline = config_json_dict.get('soa_offline')
    config.initial_run_offline = config_json_dict.get('initial_run_offline')
    config.offline_session_type = config_json_dict.get('offline_session_type')
    config.recorder_config_offline = config_json_dict.get('recorder_config_offline')

    ## --- online specific ---
    config.condition_online = config_json_dict.get('condition_online')
    config.soa_online = config_json_dict.get('soa_online')
    config.number_of_runs_online = config_json_dict.get('number_of_runs_online')
    config.recorder_config_online = config_json_dict.get('recorder_config_online')
    config.channel_labels_online = config_json_dict.get('channel_labels_online')

    config.eye_open_close_time = config_json_dict.get('eye_open_close_time')
    config.oddball_n_reps = config_json_dict.get('oddball_n_reps')
    config.oddball_soa = config_json_dict.get('oddball_soa')
    config.oddball_n_seqs = config_json_dict.get('oddball_n_seqs')


def build_system_config(config_file_path : str):
    system_config.repository_dir_base = repository_dir_base
    system_config.computer_name = socket.gethostname().lower()

    with open(config_file_path) as f:
        config_json_dict = json.load(f)

    if 'datestr' in config_json_dict and not config_json_dict['datestr']:
        # ensure date is in correct format
        system_config.datestr = datetime.strptime(config_json_dict['datestr']).strftime("%y_%m_%d")
    else:
        system_config.datestr = datetime.now().strftime("%y_%m_%d")

    if config.subject_code is not None and system_config.datestr is not None :
        system_config.save_folder_name = config.subject_code + "_" + system_config.datestr
    else: system_config.save_folder_name = None

    if config.words is not None :
        system_config.number_of_words = len(config.words)
    else: system_config.number_of_words = None

    if system_config.datestr is not None :
        system_config.log_file_name = system_config.datestr + ".log"
    else: system_config.log_file_name = None

    # General
    system_config.data_dir = config_json_dict.get('data_dir')
    system_config.len_shared_memory = config_json_dict.get('len_shared_memory')
    system_config.file_name_prefix = config_json_dict.get('file_name_prefix')
    system_config.eye_open_close_time = config_json_dict.get('eye_open_close_time')
    system_config.oddball_target = config_json_dict.get('oddball_target')
    system_config.oddball_non_target = config_json_dict.get('oddball_non_target')
    system_config.oddball_marker = config_json_dict.get('oddball_marker')
    system_config.oddball_channels = config_json_dict.get('oddball_channels')
    system_config.enable_pause_between_trial = config_json_dict.get('enable_pause_between_trial')
    system_config.pause_after_start_sound = config_json_dict.get('pause_after_start_sound')
    system_config.pause_between_sentence_and_subtrial = config_json_dict.get('pause_between_sentence_and_subtrial')
    system_config.pause_after_trial = config_json_dict.get('pause_after_trial')
    system_config.pause_between_trial = config_json_dict.get('pause_between_trial')
    system_config.pause_before_feedback = config_json_dict.get('pause_before_feedback')
    system_config.show_live_classification_barplot = config_json_dict.get('show_live_classification_barplot')
    system_config.eog_channels = config_json_dict.get('eog_channels')
    system_config.misc_channels = config_json_dict.get('misc_channels')

    # Dareplane
    system_config.dareplane_api_ip = config_json_dict.get('dareplane_api_ip')
    system_config.dareplane_api_port = config_json_dict.get('dareplane_api_port')

    # Logging
    system_config.logger_name = config_json_dict.get('logger_name')
    system_config.log_level_default = config_json_dict.get('log_level_default')
    system_config.log_to_stdout = config_json_dict.get('log_to_stdout')
    system_config.log_level_stdout = config_json_dict.get('log_level_stdout')
    system_config.log_to_file = config_json_dict.get('log_to_file')
    system_config.log_level_file = config_json_dict.get('log_level_file')

    # Marker
    system_config.MarkerClient = import_client_class(config_json_dict.get('marker_client_class'))
    system_config.markers = config_json_dict.get('markers')

    # LSL settings
    system_config.enable_stream_inlet_recover = config_json_dict.get('enable_stream_inlet_recover')
    
    # Audio
    if 'audio_files_dir_base' in config_json_dict and config.language is not None:
        system_config.audio_files_dir_base = os.path.join(repository_dir_base, config_json_dict.get('audio_files_dir_base'), config.language)
    else: system_config.audio_files_dir_base = None
    system_config.n_channels = config_json_dict.get('n_channels')
    system_config.audio_device_name = config_json_dict.get('audio_device_name')
    system_config.format = config_json_dict.get('format')
    system_config.frames_per_buffer = config_json_dict.get('frames_per_buffer')
    system_config.correct_sw_latency = config_json_dict.get('correct_sw_latency')
    system_config.correct_hw_latency = config_json_dict.get('correct_hw_latency')
    system_config.channel_speaker = config_json_dict.get('channel_speaker')
    system_config.channel_headphone = config_json_dict.get('channel_headphone')
    
    # Visual
    system_config.visual_images_dir_base = os.path.join(repository_dir_base, config_json_dict.get('visual_images_dir_base')) if 'visual_images_dir_base' in config_json_dict else None
    system_config.background_color = config_json_dict.get('background_color')
    system_config.foreground_color = config_json_dict.get('foreground_color')
    system_config.highlight_color = config_json_dict.get('highlight_color')
    system_config.size_smiley = config_json_dict.get('size_smiley')
    system_config.size_eye_open_close = config_json_dict.get('size_eye_open_close')
    system_config.size_dancing_gif = config_json_dict.get('size_dancing_gif')
    system_config.size_barplot = config_json_dict.get('size_barplot')
    system_config.enable_fullscreen = config_json_dict.get('enable_fullscreen')
    
    # Acquisition
    system_config.init_recorder_locally = config_json_dict.get('init_recorder_locally')
    system_config.rda_lsl_dir = os.path.join(repository_dir_base, config_json_dict.get('rda_lsl_dir')) if 'rda_lsl_dir' in config_json_dict else None
    system_config.rda_lsl_config_dir = os.path.join(repository_dir_base, config_json_dict.get('rda_lsl_config_dir')) if 'rda_lsl_config_dir' in config_json_dict else None
    system_config.stream_await_timeout_ms = config_json_dict.get('stream_await_timeout_ms')
    
    system_config.eeg_acquisition_stream_name = config_json_dict.get('eeg_acquisition_stream_name')
    system_config.eeg_acquisition_stream_type = config_json_dict.get('eeg_acquisition_stream_type')
    system_config.marker_acquisition_stream_name = config_json_dict.get('marker_acquisition_stream_name')
    system_config.marker_acquisition_stream_type = config_json_dict.get('marker_acquisition_stream_type')
    system_config.marker_stream_name_keyword = config_json_dict.get('marker_stream_name_keyword')

    system_config.RecorderClient = import_client_class(config_json_dict.get('recorder_client_class'))
    system_config.FormattingClient = import_client_class(config_json_dict.get('formatting_client_class'))


def build_classifier_config(config_file_path : str):
    if config.channel_labels_online is not None:
        classifier_config.n_channels = len(config.channel_labels_online) 
    else: classifier_config.n_channels = None
    if config.words is not None:
        classifier_config.n_class = len(config.words)
    else: classifier_config.n_class = None
    classifier_config.n_stimulus = classifier_config.n_class * config.number_of_repetitions

    with open(config_file_path) as f:
        config_json_dict = json.load(f)

    classifier_config.ivals = config_json_dict.get('ivals')
    classifier_config.filter_order = config_json_dict.get('filter_order')
    classifier_config.filter_freq = config_json_dict.get('filter_freq')
    classifier_config.baseline = config_json_dict.get('baseline')
    classifier_config.tmin = config_json_dict.get('tmin')
    classifier_config.tmax = config_json_dict.get('tmax')
    classifier_config.dynamic_stopping = config_json_dict.get('dynamic_stopping')
    classifier_config.dynamic_stopping_params = config_json_dict.get('dynamic_stopping_params')
    classifier_config.adaptation = config_json_dict.get('adaptation')
    classifier_config.adaptation_eta_cov = config_json_dict.get('adaptation_eta_cov')
    classifier_config.adaptation_eta_mean = config_json_dict.get('adaptation_eta_mean')
    classifier_config.labels_binary_classification = config_json_dict.get('labels_binary_classification')

    classifier_config.ClassificationPipelineClass = import_client_class(config_json_dict.get("classification_pipeline_class"))
    classifier_config.CallibrationDataProviderClass = import_client_class(config_json_dict.get("calibration_data_provider_class"))


def import_client_class(client_reference : str):
    if client_reference is None:
        return None
    
    client_reference_split = client_reference.split(':')
    client_module_path = client_reference_split[0]
    client_class_name = client_reference_split[1]

    client_module = importlib.import_module(client_module_path)
    client_class = getattr(client_module, client_class_name)
    return client_class

