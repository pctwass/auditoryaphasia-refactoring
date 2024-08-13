# This configuration file is temporary. I just need a place to add new config settings.  Where they will go eventually we can determine once we restructure the config files

# Acquisition input streams
# -- Not sure if both stream name and type is needed
eeg_acquisition_stream_name : str = "eeg_stream"
eeg_acquisition_stream_type : str = "eeg"
marker_acquisition_stream_name : str = "marker_stream"
marker_acquisition_stream_type : str = "markers"
marker_stream_await_timeout_ms : int|float = 1000 

# Acquisition recorder suprocess
init_recorder_locally : bool = False