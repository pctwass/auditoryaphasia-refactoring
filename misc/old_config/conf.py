
#  currently (2023_02_09) available languages: Dutch, German
language = 'Dutch'
subject_code = 'VPpdfc'

callibration_file_name_prefix = 'AuditoryAphasia'

# stored in media/audio/<LANGUAGE>/words/<CONDITION>
words = ['Spiegel', 'Blender', 'Groente', 'Stropdas', 'Tractor', 'Knuffel']

# (number_of_repetitions * number of words) stimuli will be presented
number_of_repetitions = 15

# master volume for audio
master_volume = 0.3

# port for marker device, i.e. button box in DCC labs
port = 'COM3' # check for a match with the DeviceManager in Windows

# screen number which participant will be looking at
# depending on primary screen setting on operatin system
screen_number = 1

## --- offline specific ---

condition_offline = ['6d',
                     # 'mono',
                     '6d',
                     # 'mono'
                     ]

# give the order of conditions
soa_offline = [0.25,
               # 0.35,
               # 0.35,
               0.25
               ]

initial_run_offline = 1 # index starts from 1
offline_session_type = 'pre' # either 'pre' or 'post'
recorder_config_offline = "32ch_DCC_standard.rwksp" # for testing purposes only
# recorder_config_offline = '64ch_eog_dcc.rwksp' # for offline sessions


## --- offline specific end ---

## --- online specific ---

condition_online = '6d'
# '6d', '6d-pitch', 'stereo-pitch', 'mono'

# soa_online = 0.35 # start with slower SOA during first online set
soa_online = 0.25 # after discussing with Michael, possibly speed up.
number_of_runs_online = 15

recorder_config_online = "32ch_DCC_standard.rwksp" # for testing purposes only
# recorder_config_online = "32ch_eog_dcc.rwksp"  # true workspace for online training

# do not include channels other than EEG.
#channel_labels_online = ['Fp1', 'Fp2', 'F7', 'F3', 'Fz', 'F4', 'F8', 'FC5', 'FC1', 'FCz', 'FC2', 'FC6',
#                         'T7', 'C3', 'Cz', 'C4', 'T8', 'CP5', 'CP1', 'CP2', 'CP6', 'TP10', 'P7', 'P3',
#                         'Pz', 'P4', 'P8', 'PO9', 'PO10', 'O1', 'Oz', 'O2']
channel_labels_online = ['Fp2', 'F4', 'F8', 'FC6', 'C4', 'T8', 'CP2', 'CP6', 'TP10', 'P8', 'O2', 'PO10',
                         'P4', 'Cz', 'Pz', 'Oz', 'PO9', 'O1', 'P7', 'P3', 'CP5', 'CP1', 'T7', 'C3', 'FC1',
                         'FCz', 'FC2', 'Fz', 'FC5', 'F7', 'F3', 'Fp1']

## --- online specific end ---

eye_open_close_time = 60

# number of oddball runs
oddball_n_reps = 2 
oddball_soa = 1.0

# (oddball_n_seps * 6) stimuli will be presented
oddball_n_seqs = 50 # 50 -> 5 mins, if soa = 1.0

