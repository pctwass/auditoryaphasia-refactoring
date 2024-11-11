# ------------------------------------------------------------------------
# General
repository_dir_base : str
computer_name : str

data_dir : str
datestr : str
save_folder_name : str
log_file_name : str
file_name_prefix : str

number_of_words : int

eye_open_close_time : int

oddball_target : str
oddball_non_target : str
oddball_marker : dict[str, int]
oddball_channels : int

enable_pause_between_trial : bool 
pause_after_start_sound : float
pause_between_sentence_and_subtrial : float 
pause_after_trial : int
pause_between_trial : int
pause_before_feedback : int

show_live_classification_barplot : bool 

eog_channels : list[str]
misc_channels : list[str]

# ------------------------------------------------------------------------
# Dareplane
dareplane_api_ip : str = "127.0.0.1"
dareplane_api_port : int = 8001 

# ------------------------------------------------------------------------
# Marker
markers : dict[str,list[str]]
MarkerClient = None

# ------------------------------------------------------------------------
# LSL settings
enable_stream_inlet_recover : bool

# ------------------------------------------------------------------------
# Audio
audio_files_dir_base : str

n_channels : int
device_name : str

format : str
frames_per_buffer : int

correct_sw_latency : bool
correct_hw_latency : int

channel_speaker : list[int]
channel_headphone : list[int]

# ------------------------------------------------------------------------
# Visual
visual_images_dir_base : str

background_color : str | tuple[int|float] # 3 entries, one for each rgb value
foreground_color : str | tuple[int|float] # 3 entries, one for each rgb value 
highlight_color : str | tuple[int|float]  # 3 entries, one for each rgb value

size_smiley : tuple[float]
size_eye_open_close : tuple[float]
size_dancing_gif : tuple[float]
#size_barplot : tuple[float]

enable_fullscreen : bool

# ------------------------------------------------------------------------
# Acquisition
init_recorder_locally : bool = True
RecorderClient = None
FormattingClient = None

rda_lsl_dir : str
rda_lsl_config_dir : str
marker_stream_keyword : str

eeg_acquisition_stream_name : str
eeg_acquisition_stream_type : str
marker_acquisition_stream_name : str 
marker_acquisition_stream_type : str 
marker_stream_await_timeout_ms : int|float  