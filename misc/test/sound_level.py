import utils
import pyscab
import os
import sys
import argparse

import conf_offline as conf

parser = argparse.ArgumentParser()

parser.add_argument('-n', '--n_reps', type=int, default=3)
parser.add_argument('-v', '--visual', action='store_true')

args = parser.parse_args()

NUMBER_OF_REPETITIONS = args.n_reps

condition = 'stereo-pitch'
soa = conf.soa
base_dir = conf.repository_dir_base

words = conf.words
MasterVolume = conf.master_volume

volume = dict()
volume['sentence'] = 0.51 # x1.7
volume['word'] = 0.51
volume['restart'] = 0.3
volume['relax'] = 0.3

data = pyscab.DataHandler()

for idx, word in enumerate(conf.words):

    if condition in conf.single_file_condition:
        f_name = '1.wav'
    else:
        f_name = '%d.wav' %(idx+1)

    word_dir = os.path.join(base_dir,
                            'media',
                            'audio',
                            conf.language,
                            'words',
                            condition,
                            word,
                            f_name)

    sentence_dir = os.path.join(base_dir,
                            'media',
                            'audio',
                            conf.language,
                            'sentences',
                            condition,
                            word,
                            f_name)

    data.load(idx+1, word_dir, volume = volume['word'])
    data.load(idx+1+10, sentence_dir, volume = volume['sentence'])

restart_dir = os.path.join(base_dir,
                        'media',
                        'audio',
                        conf.language,
                        'misc',
                        'restart.wav')
data.load(100, restart_dir, volume = volume['restart'])

relax_dir = os.path.join(base_dir,
                        'media',
                        'audio',
                        conf.language,
                        'misc',
                        'relax.wav')
data.load(101, relax_dir, volume = volume['relax'])

pause_between_trial = 5
pause_after_start_sound = 2
pause_between_sentence_and_subtrial = 3.5
pause_before_trial_completion = 2
number_of_repetitions = NUMBER_OF_REPETITIONS

sudoku = utils.Sudoku()
word2spk = sudoku.generate_matrix(1, 6)[0]
#word2spk = [1, 2, 3, 4, 5, 6]
targetplan = sudoku.generate_matrix(1, 6)[0]

offset_start = 1
audio_plan = list()

time_plan = 0
time_plan += offset_start
for trial_idx in range(6):
    target = targetplan[trial_idx]
    wordplan = utils.generate_stimulation_plan(6, number_of_repetitions)

    if condition == 'mono' or condition == 'stereo-pitch':
        audio_plan.append([time_plan, 100, [7,8], 210])
    else:
        audio_plan.append([time_plan, 100, [1], 210])
    time_plan += data.get_length_by_id(100)
    time_plan += pause_after_start_sound
    if condition == 'mono' or condition == 'stereo-pitch':
        audio_plan.append([time_plan, target+10, [7,8], 200 + target])
    else:
        audio_plan.append([time_plan, target+10, [word2spk[target-1]], 200 + target])
    time_plan += data.get_length_by_id(target+10)
    time_plan += pause_between_sentence_and_subtrial
    for m in range(0, len(wordplan)):
        if wordplan[m] == target:
            time_plan += soa
            if condition == 'mono' or condition == 'stereo-pitch':
                audio_plan.append([time_plan, wordplan[m], [7,8], 110 + target])
            else:
                audio_plan.append([time_plan, wordplan[m], [word2spk[wordplan[m]-1]], 110 + target])
        else:
            time_plan += soa
            if condition == 'mono' or condition == 'stereo-pitch':
                audio_plan.append([time_plan, wordplan[m], [7,8], 100 + wordplan[m]])
            else:
                audio_plan.append([time_plan, wordplan[m], [word2spk[wordplan[m]-1]], 100 + wordplan[m]])
    time_plan += data.get_length_by_id(wordplan[m])
    time_plan += pause_before_trial_completion
    if condition == 'mono' or condition == 'stereo-pitch':
        audio_plan.append([time_plan, 101, [7,8], 0])
    else:
        audio_plan.append([time_plan, 101, [1], 0])
    time_plan += data.get_length_by_id(101)
    time_plan += pause_between_trial

ahc = pyscab.AudioInterface(device_name = conf.device_name,
                            n_ch = conf.n_ch,
                            format=conf.format,
                            frames_per_buffer = conf.frames_per_buffer)
def sendMarker(val):
    pass
share = [0 for m in range(8)]
stc = pyscab.StimulationController(ahc, marker_send=sendMarker, share=share)

stc.play(audio_plan, data, time_termination = 'auto', pause=0)