#  currently (2023_02_09) available languages: Dutch, German
language : str
subject_code : str

callibration_file_name_prefix : str

# stored in media/audio/<LANGUAGE>/words/<CONDITION>
words : list[str]

# (number_of_repetitions * number of words) stimuli will be presented
number_of_repetitions : int

# master volume for audio
aster_volume : float

# port for marker device, i.e. button box in DCC labs
port :  str

# screen number which participant will be looking at
# depending on primary screen setting on operatin system
screen_number : int

## --- offline specific ---
condition_offline : tuple[str] 
soa_offline : tuple[float] 
initial_run_offline : int # index starts from 1
offline_session_type : str # either 'pre' or 'post'
recorder_config_offline :str  # '64ch_eog_dcc.rwksp' for offline sessions / '32ch_DCC_standard.rwksp' for testing purposes only

## --- online specific ---
condition_online : str # '6d', '6d-pitch', 'stereo-pitch', 'mono'
soa_online : float
number_of_runs_online : int
recorder_config_online :str # '32ch_eog_dcc.rwksp' for online sessions / '32ch_DCC_standard.rwksp' for testing purposes only
channel_labels_online : list[str]

eye_open_close_time : int

oddball_n_reps : int
oddball_soa : float
oddball_n_seqs : float # (oddball_n_seps * 6) stimuli will be presented | e.g. 50 -> 5 mins, if soa = 1.0