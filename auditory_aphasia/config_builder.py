import datetime
import socket
from dataclasses import dataclass, field
from pathlib import Path

import yaml

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
    save_folder_name: str = "P100_" + ISO_DATE
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

    markers: dict = field(
        default_factory=lambda: {
            "target": [111, 112, 113, 114, 115, 116],
            "nontarget": [101, 102, 103, 104, 105, 106],
            "new-trial": [200, 201, 202, 203, 204, 205],
        }
    )
    format: str = "INT16"
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


@dataclass
class ClassifierConfig:
    classification_pipeline_name: str
    calibration_data_provider_name: str

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

    # here are dependent overwrites ... <- refactor how this is setup
    config = build_general_config()

    config_dict = yaml.safe_load(open(config_file_path, "r"))
    config_dict["save_folder_name"] = config.subject_code + ISO_DATE
    config_dict["number_of_words"] = len(config.words)

    system_config = SystemConfig(**config_dict)
    return system_config


def build_classifier_config(
    config_file_path: str = Path("./config/classifier_config.yaml"),
):

    config = build_general_config()
    config_dict = yaml.safe_load(open(config_file_path, "r"))

    config_dict["n_channels"] = len(config.channel_labels_online)
    config_dict["n_class"] = len(config.words)
    config_dict["n_stimulus"] = config.number_of_repetitions * config_dict["n_class"]

    classifier_config = ClassifierConfig(**config_dict)

    return classifier_config
