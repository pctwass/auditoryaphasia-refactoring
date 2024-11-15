import datetime
import importlib
import json  # for loading conf variables
import os
import socket
from dataclasses import dataclass, field
from pathlib import Path

import config.conf_selector as config_selector
import git
import yaml
from clients.formatting.brain_vision_formatting_client import \
    BrainVisionFromattingClient
from clients.recorder.brain_vision_recorder_client import \
    BrainVisionRecorderClient

import auditory_aphasia.config.classifier_config as classifier_config
import auditory_aphasia.config.config as config
import auditory_aphasia.config.system_config as system_config

ISO_DATE = datetime.datetime.now().strftime("%Y-%m-%d")


# Using dataclass with a singleton instead of all global variables
# A singleton is used to maintain the import structure of the module at first
@dataclass
class GeneralConfig:
    language: str
    subject_code: str
    callibration_file_name_prefix: str
    words: list[str]  # stored in media/audio/<LANGUAGE>/words/<CONDITION>
    number_of_repetitions: (
        int  # (number_of_repetitions * number of words) stimuli will be presented
    )
    master_volume: float
    port: str  # port marker device
    screen_number: int  # screen for participant
    ## --- offline specific ---
    condition_offline: tuple[str]
    soa_offline: tuple[float]
    initial_run_offline: int  # index starts from 1
    offline_session_type: str  # either 'pre' or 'post'
    recorder_config_offline: str  # '64ch_eog_dcc.rwksp' for offline sessions / '32ch_DCC_standard.rwksp' for testing purposes only
    ## --- online specific ---
    condition_online: str  # '6d', '6d-pitch', 'stereo-pitch', 'mono'
    soa_online: float
    number_of_runs_online: int
    recorder_config_online: str  # '32ch_eog_dcc.rwksp' for online sessions / '32ch_DCC_standard.rwksp' for testing purposes only
    channel_labels_online: list[str]
    eye_open_close_time: int
    oddball_n_reps: int
    oddball_soa: float
    oddball_n_seqs: float  # (oddball_n_seps * 6) stimuli will be presented | e.g. 50 -> 5 mins, if soa = 1.0


@dataclass
class SystemConfig:
    repository_dir_base: str = "."
    computer_name: str = socket.gethostname().lower()
    datestr: str = ISO_DATE
    system_config.save_folder_name: str = "P100_" + ISO_DATE
    number_of_words: int = None
    log_file_name: str = ISO_DATE + ".log"

    # General
    data_dir: str = "./data"
    len_shared_memory: int = 8
    file_name_prefix: str = "AuditoryAphasia"
    eye_open_close_time: int = 60
    oddball_target: str = "1000.wav"
    oddball_non_target: str = "500.wav"
    oddball_marker: dict = field(
        default_factory=lambda: {
            "target": 21,
            "nontarget": 1,
        }
    )
    oddball_channels: list = field(default_factory=lambda: [1])
    enable_pause_between_trial: bool = False
    pause_after_start_sound: float = 2
    pause_between_sentence_and_subtrial: float = 3.5
    pause_after_trial: float = 2
    pause_between_trial: float = 5
    pause_before_feedback: float = 1
    show_live_classification_barplot: bool = True
    eog_channels: list = field(default_factory=lambda: ["EOGuv"])
    misc_channels: list = field(
        default_factory=lambda: ["x_EMGl", "x_GSR", "x_Respi", "x_Pulse", "x_Optic"]
    )

    # Dareplane
    dareplane_api_ip: str = "127.0.0.1"
    dareplane_api_port: int = 8001

    # Logging
    logger_name: str = ""
    log_level_default: int = 20
    log_to_stdout: bool = False
    log_level_stdout: int = 20
    log_to_file: bool = True
    log_level_file: int = 10

    # LSL settings
    enable_stream_inlet_recover: bool = False

    # Audio
    audio_files_dir_base: str = None
    n_channels: int = 8
    audio_device_name: str = "X-AIR ASIO Driver"
    audio_format: str = "INT16"
    frames_per_buffer: int = 512
    correct_sw_latency: bool = True  # why bool here and 512 for the next?
    correct_hw_latency: int = 512
    channel_speaker: list = field(default_factory=lambda: [1, 2, 3, 4, 5, 6])
    channel_headphone: list = field(default_factory=lambda: [7, 8])

    # Visual
    visual_images_dir_base: str = (
        "./media/images"  # this would be a resource of the module, why is this part of a config?
    )
    background_color: list = field(default_factory=lambda: [-1, -1, -1])
    foreground_color: list = field(default_factory=lambda: [1, 1, 1])
    highlight_color: list = field(default_factory=lambda: [0.59375, -1, -1])
    size_smiley: list = field(default_factory=lambda: [0.5])
    size_eye_open_close: list = field(default_factory=lambda: [1.0])
    size_dancing_gif: list = field(default_factory=lambda: [0.7])
    size_barplot: list = field(default_factory=lambda: [1.0])
    enable_fullscreen: bool = True

    # Acquisition
    init_recorder_locally: bool = True
    rda_lsl_dir: str = "./lsl/BrainVisionRDA_x64/BrainVisionRDA.exe"
    rda_lsl_config_dir: str = "./lsl/BrainVisionRDA_x64/brainvision_config.cfg"

    stream_await_timeout_ms: str = 1000
    eeg_acquisition_stream_name: str = "eeg_stream"
    eeg_acquisition_stream_type: str = "eeg"
    marker_acquisition_stream_name: str = "marker_stream"
    marker_acquisition_stream_type: str = "markers"
    marker_stream_name_keyword: str = "RDA"

    RecorderClient: BrainVisionRecorderClient = None
    FormattingClient: BrainVisionFromattingClient = None


@dataclass
class ClassifierConfig:
    ClassificationPipelineClass = None
    CallibrationDataProviderClass = None

    n_channels: int
    n_class: int
    n_stimulus: int

    ivals: list[tuple[float]]
    filter_order: int
    filter_freq: tuple[float]
    baseline: str | int | float
    tmin: float
    tmax: float

    dynamic_stopping: bool
    dynamic_stopping_params: dict[str, float | int]

    adaptation: bool
    adaptation_eta_cov: float
    adaptation_eta_mean: float
    labels_binary_classification: dict[str, int]


def build_general_config(config_file_path: str = Path("./config/general_config.yaml")):
    config_dict = yaml.safe_load(open(config_file_path, "r"))

    general_config = GeneralConfig(**config_dict)

    return general_config


def build_system_config(config_file_path: str = Path("./config/system_config.yaml")):

    repo = git.Repo(".", search_parent_directories=True)
    cwd = repo.working_tree_dir

    system_config.computer_name = socket.gethostname().lower()

    with open(config_file_path) as f:
        config_json_dict = json.load(f)

    config_dict = yaml.safe_load(open(config_file_path, "r"))

    if config.subject_code is not None and system_config.datestr is not None:
        system_config.save_folder_name = (
            config.subject_code + "_" + system_config.datestr
        )
    else:
        system_config.save_folder_name = None

    if config.words is not None:
        system_config.number_of_words = len(config.words)
    else:
        system_config.number_of_words = None

    if system_config.datestr is not None:
        system_config.log_file_name = system_config.datestr + ".log"
    else:
        system_config.log_file_name = None

    # General
    system_config.data_dir = config_json_dict.get("data_dir")
    system_config.len_shared_memory = config_json_dict.get("len_shared_memory")
    system_config.file_name_prefix = config_json_dict.get("file_name_prefix")
    system_config.eye_open_close_time = config_json_dict.get("eye_open_close_time")
    system_config.oddball_target = config_json_dict.get("oddball_target")
    system_config.oddball_non_target = config_json_dict.get("oddball_non_target")
    system_config.oddball_marker = config_json_dict.get("oddball_marker")
    system_config.oddball_channels = config_json_dict.get("oddball_channels")
    system_config.enable_pause_between_trial = config_json_dict.get(
        "enable_pause_between_trial"
    )
    system_config.pause_after_start_sound = config_json_dict.get(
        "pause_after_start_sound"
    )
    system_config.pause_between_sentence_and_subtrial = config_json_dict.get(
        "pause_between_sentence_and_subtrial"
    )
    system_config.pause_after_trial = config_json_dict.get("pause_after_trial")
    system_config.pause_between_trial = config_json_dict.get("pause_between_trial")
    system_config.pause_before_feedback = config_json_dict.get("pause_before_feedback")
    system_config.show_live_classification_barplot = config_json_dict.get(
        "show_live_classification_barplot"
    )
    system_config.eog_channels = config_json_dict.get("eog_channels")
    system_config.misc_channels = config_json_dict.get("misc_channels")

    # Dareplane
    system_config.dareplane_api_ip = config_json_dict.get("dareplane_api_ip")
    system_config.dareplane_api_port = config_json_dict.get("dareplane_api_port")

    # Logging
    system_config.logger_name = config_json_dict.get("logger_name")
    system_config.log_level_default = config_json_dict.get("log_level_default")
    system_config.log_to_stdout = config_json_dict.get("log_to_stdout")
    system_config.log_level_stdout = config_json_dict.get("log_level_stdout")
    system_config.log_to_file = config_json_dict.get("log_to_file")
    system_config.log_level_file = config_json_dict.get("log_level_file")

    # Marker
    system_config.MarkerClient = import_client_class(
        config_json_dict.get("marker_client_class")
    )
    system_config.markers = config_json_dict.get("markers")

    # LSL settings
    system_config.enable_stream_inlet_recover = config_json_dict.get(
        "enable_stream_inlet_recover"
    )

    # Audio
    if "audio_files_dir_base" in config_json_dict and config.language is not None:
        system_config.audio_files_dir_base = os.path.join(
            repository_dir_base,
            config_json_dict.get("audio_files_dir_base"),
            config.language,
        )
    else:
        system_config.audio_files_dir_base = None
    system_config.n_channels = config_json_dict.get("n_channels")
    system_config.audio_device_name = config_json_dict.get("audio_device_name")
    system_config.format = config_json_dict.get("format")
    system_config.frames_per_buffer = config_json_dict.get("frames_per_buffer")
    system_config.correct_sw_latency = config_json_dict.get("correct_sw_latency")
    system_config.correct_hw_latency = config_json_dict.get("correct_hw_latency")
    system_config.channel_speaker = config_json_dict.get("channel_speaker")
    system_config.channel_headphone = config_json_dict.get("channel_headphone")

    # Visual
    system_config.visual_images_dir_base = (
        os.path.join(
            repository_dir_base, config_json_dict.get("visual_images_dir_base")
        )
        if "visual_images_dir_base" in config_json_dict
        else None
    )
    system_config.background_color = config_json_dict.get("background_color")
    system_config.foreground_color = config_json_dict.get("foreground_color")
    system_config.highlight_color = config_json_dict.get("highlight_color")
    system_config.size_smiley = config_json_dict.get("size_smiley")
    system_config.size_eye_open_close = config_json_dict.get("size_eye_open_close")
    system_config.size_dancing_gif = config_json_dict.get("size_dancing_gif")
    system_config.size_barplot = config_json_dict.get("size_barplot")
    system_config.enable_fullscreen = config_json_dict.get("enable_fullscreen")

    # Acquisition
    system_config.init_recorder_locally = config_json_dict.get("init_recorder_locally")
    system_config.rda_lsl_dir = (
        os.path.join(repository_dir_base, config_json_dict.get("rda_lsl_dir"))
        if "rda_lsl_dir" in config_json_dict
        else None
    )
    system_config.rda_lsl_config_dir = (
        os.path.join(repository_dir_base, config_json_dict.get("rda_lsl_config_dir"))
        if "rda_lsl_config_dir" in config_json_dict
        else None
    )
    system_config.stream_await_timeout_ms = config_json_dict.get(
        "stream_await_timeout_ms"
    )

    system_config.eeg_acquisition_stream_name = config_json_dict.get(
        "eeg_acquisition_stream_name"
    )
    system_config.eeg_acquisition_stream_type = config_json_dict.get(
        "eeg_acquisition_stream_type"
    )
    system_config.marker_acquisition_stream_name = config_json_dict.get(
        "marker_acquisition_stream_name"
    )
    system_config.marker_acquisition_stream_type = config_json_dict.get(
        "marker_acquisition_stream_type"
    )
    system_config.marker_stream_name_keyword = config_json_dict.get(
        "marker_stream_name_keyword"
    )

    system_config.RecorderClient = import_client_class(
        config_json_dict.get("recorder_client_class")
    )
    system_config.FormattingClient = import_client_class(
        config_json_dict.get("formatting_client_class")
    )


def build_classifier_config(config_file_path: str):
    if config.channel_labels_online is not None:
        classifier_config.n_channels = len(config.channel_labels_online)
    else:
        classifier_config.n_channels = None
    if config.words is not None:
        classifier_config.n_class = len(config.words)
    else:
        classifier_config.n_class = None
    classifier_config.n_stimulus = (
        classifier_config.n_class * config.number_of_repetitions
    )

    with open(config_file_path) as f:
        config_json_dict = json.load(f)

    classifier_config.ivals = config_json_dict.get("ivals")
    classifier_config.filter_order = config_json_dict.get("filter_order")
    classifier_config.filter_freq = config_json_dict.get("filter_freq")
    classifier_config.baseline = config_json_dict.get("baseline")
    classifier_config.tmin = config_json_dict.get("tmin")
    classifier_config.tmax = config_json_dict.get("tmax")
    classifier_config.dynamic_stopping = config_json_dict.get("dynamic_stopping")
    classifier_config.dynamic_stopping_params = config_json_dict.get(
        "dynamic_stopping_params"
    )
    classifier_config.adaptation = config_json_dict.get("adaptation")
    classifier_config.adaptation_eta_cov = config_json_dict.get("adaptation_eta_cov")
    classifier_config.adaptation_eta_mean = config_json_dict.get("adaptation_eta_mean")
    classifier_config.labels_binary_classification = config_json_dict.get(
        "labels_binary_classification"
    )

    classifier_config.ClassificationPipelineClass = import_client_class(
        config_json_dict.get("classification_pipeline_class")
    )
    classifier_config.CallibrationDataProviderClass = import_client_class(
        config_json_dict.get("calibration_data_provider_class")
    )


def import_client_class(client_reference: str):
    if client_reference is None:
        return None

    client_reference_split = client_reference.split(":")
    client_module_path = client_reference_split[0]
    client_class_name = client_reference_split[1]

    client_module = importlib.import_module(client_module_path)
    client_class = getattr(client_module, client_class_name)
    return client_class
