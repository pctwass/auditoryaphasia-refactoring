import os
import sys
import itertools
import random
import re

import numpy as np

import conf_selector
# exec("import %s as conf" % (conf_selector.conf_file_name))
# exec("import %s as conf_system" % (conf_selector.conf_system_file_name))
import conf as conf
import conf_system as conf_system

def getIntermoduleCommunicationInlet(target, timeout=None):
    from pylsl import StreamInlet, resolve_stream
    import time

    if timeout is None:
        timeout = float('inf')

    is_found = False
    start = time.time()
    while is_found is False:
        streams = resolve_stream('type', 'Markers')
        for stream in streams:
            if stream.name() == 'IntermoduleCommunication_' + target:
                inlet_intermodule = StreamInlet(stream)
                is_found = True
                return inlet_intermodule
        if time.time() - start > timeout:
            break

    if is_found is False:
        raise ValueError("Stream 'IntermoduleCommunication' was not found.")

def createIntermoduleCommunicationOutlet(name, type='Markers', channel_count=1, nominal_srate=0, channel_format='string', id=''):
    from pylsl import StreamInfo, StreamOutlet

    # StreamInfo(name, type, channel_count, nominal_srate, channel_format, source_id)
    # srate is set to IRREGULAR_RATE when nominal_srate = 0
    info = StreamInfo('IntermoduleCommunication_' + name, type, channel_count, nominal_srate, channel_format, id)
    outlet = StreamOutlet(info)

    return outlet

def send_cmd_LSL(outlet, target, cmd, params=None):
    if outlet.channel_count != 4:
        raise ValueError("channel_count of LSL outlet have to be 4.")
    
    import json
    params = json.dumps(params)
    outlet.push_sample([target, 'cmd', cmd, params])

def send_params_LSL(outlet, target, name_of_var, params=None):
    if outlet.channel_count != 4:
        raise ValueError("channel_count of LSL outlet have to be 4.")
    
    import json
    params = json.dumps(params)
    outlet.push_sample([target, 'params', name_of_var, params])

def _push_LSL(name, data, outlet):
    # not used
    if outlet.channel_count != 2:
        raise ValueError("channel_count of LSL outlet have to be 2.")

    import json
    outlet.push_sample("%s;"%name + json.dumps(data))

def _receive_LSL(val):
    # not used
    import json
    val = val.split(';')
    name = val[0]
    del(val[0])
    val = ';'.join(val)
    data = json.loads(val)

    return name, data

def atoi(text):
    return int(text) if text.isdigit() else text

def natural_keys(text):
    return [ atoi(c) for c in re.split(r'(\d+)', text) ]
    
def sort_list(data):
    return sorted(data, key=natural_keys)

class Sudoku(object):

    """
    This source code for generating sudoku matrix is based on one from scripts of old framework which is based on matlab.
    Modified by Simon Kojima to adopt to Python version 3.x
    """

    def __init__(self):
        pass

    def _create_filter_for_vector(self, vector):
        return (lambda permutation: not self._has_any_same_elements_on_same_positions(permutation, vector))

    def _has_any_same_elements_on_same_positions(self, v1, v2):
        # TODO : impliment in more efficient way
        res = list()
        for idx, x in enumerate(list(v1)):
            res.append(x == v2[idx])
        return any(res)

    def generate_matrix(self, rows, columns):

        """
        This method creates "sudoku" matrix:
        1. Creates a list of all permutations of a vector
        2. Randomly selects an element.
        3. Filters a list of possible vectors to remove conflicting

        Note : should be rows <= columns
        """

        column_values = range(1, columns + 1)
        column_permutations = list(itertools.permutations(column_values))

        random.seed()
        
        matrix = [None] * rows
        for i in range(rows):
            column_permutation = random.choice(column_permutations)
            matrix[i] = list(column_permutation)
            column_permutations = list(filter(self._create_filter_for_vector(column_permutation), column_permutations))
        return matrix


def get_minmax_stim_distance(sequence):
    stim_list = np.unique(sequence)
    distances = list()
    for stim in stim_list:
        idx = np.where(sequence == stim)
        distances.append(np.diff(idx))
    distances = np.hstack(distances)
    return np.min(distances), np.max(distances)

def generate_stimulation_plan(n_stim_types = 5, itrs = 10, min_stim_distance = 3):

    stim_list = np.arange(1, n_stim_types + 1)
    
    plan = stim_list.copy()

    np.random.seed()
    np.random.shuffle(plan)
    
    for itr in range(itrs-1):
        while True:
            cand = stim_list.copy()
            np.random.shuffle(cand)
            tmp = np.append(plan, cand)
            tmp_min_stim_distance = get_minmax_stim_distance(tmp)[0]
            if tmp_min_stim_distance >= min_stim_distance:
                plan = tmp
                break

    plan = plan.tolist()
    return plan

def generate_plan_run(audio_files_dir_base, words, condition, condition_params, master_volume = 1.0):

    number_of_words = len(words)

    #----------------------------------------------------------------------
    # generating stimulation plan

    sudoku = Sudoku()
    word2spk = sudoku.generate_matrix(1, number_of_words)[0]
    targetplan = sudoku.generate_matrix(1, number_of_words)[0]

    #----------------------------------------------------------------------
    # loading audio files


    # ids for each stimulus
    #
    # restart : 100
    # relax : 101
    #
    # word n (idx starts from 1) : n
    # sentence n (idx starts from 1) : 10+n
    #

    import pyscab
    audio_info = list()
    audio_files = pyscab.DataHandler()

    # load 'restart'
    audio_info.append([100, os.path.join(audio_files_dir_base, 'misc', 'restart.wav'), master_volume])
    audio_files.load(100, os.path.join(audio_files_dir_base, 'misc', 'restart.wav'), volume=master_volume)

    # load 'relax'
    audio_info.append([101, os.path.join(audio_files_dir_base, 'misc', 'relax.wav'), master_volume])
    audio_files.load(101, os.path.join(audio_files_dir_base, 'misc', 'relax.wav'), volume=master_volume)

    # load sentences
    for m in range(1, number_of_words+1):
        if condition_params['single_file']:
            dir = os.path.join(audio_files_dir_base,
                            'sentences',
                            condition,
                            words[m-1],
                            "1.wav")
        else:
            dir = os.path.join(audio_files_dir_base,
                            'sentences',
                            condition,
                            words[m-1],
                            "%d.wav" %word2spk[m-1])
        audio_files.load(10+m, dir, volume=master_volume)
        audio_info.append([10+m, dir, master_volume])

    # load words
    for m in range(1, number_of_words+1):
        if condition_params['single_file']:
            dir = os.path.join(audio_files_dir_base,
                            'words',
                            condition,
                            words[m-1],
                            "1.wav")
        else:
            dir = os.path.join(audio_files_dir_base,
                'words',
                condition,
                words[m-1],
                "%d.wav" %word2spk[m-1])
        audio_info.append([m, dir, master_volume])

    plan = dict()
    plan['audio_info'] = audio_info
    plan['audio_files'] = audio_files
    plan['word2spk'] = word2spk
    plan['targetplan'] = targetplan

    return plan

def generate_plan_trial(audio_files,
                        word2spk,
                        target,
                        condition,
                        soa,
                        number_of_repetitions,
                        number_of_words,
                        ch_speaker,
                        ch_headphone,
                        condition_params,
                        online = False):

    play_plan = list()
    word_plan = generate_stimulation_plan(number_of_words, number_of_repetitions)
    time_plan = 0 # you can add pause before trial.
    if condition_params['output'] == 'speaker':
        play_plan.append([time_plan, 100, [ch_speaker[0]], 210])
    elif condition_params['output'] == 'headphone':
        play_plan.append([time_plan, 100, ch_headphone, 210]) # play restart sound
    time_plan += audio_files.get_length_by_id(100)
    time_plan += conf_system.pause_after_start_sound

    # === About the marker of sentence ===
    # Sending 201 for word 1 is straight forward,
    # however, in original script, index for sentence is starting from 0.
    # i.e. word 1 : marker for word -> 101 or 111, marker for sentence -> 200
    #
    # for compatibility, python implementation is also follow this marker configuration.
    if condition_params['output'] == 'speaker':
        play_plan.append([time_plan, target+10, [ch_speaker[word2spk[target-1]-1]], 200+target-1])
    elif condition_params['output'] == 'headphone':
        play_plan.append([time_plan, target+10, ch_headphone, 200+target-1]) # play sentence

    # ====================================

    time_plan += conf_system.pause_between_sentence_and_subtrial
    time_plan += audio_files.get_length_by_id(target+10)
    for word_num in word_plan:
        time_plan += soa
        if condition_params['output'] == 'speaker':
            spk = [ch_speaker[word2spk[word_num-1]-1]]
        elif condition_params['output'] == 'headphone':
            spk = ch_headphone
        
        if word_num == target:
            marker = 110 + target
        else:
            marker = 100 + word_num

        play_plan.append([time_plan, word_num, spk, marker])
    
    if online is False:
        time_plan += conf_system.pause_after_trial
        if condition_params['output'] == 'speaker':
            play_plan.append([time_plan, 101, [ch_speaker[0]], 0])
        elif condition_params['output'] == 'heaphone':
            play_plan.append([time_plan, 101, ch_headphone, 0])

    plan = dict()
    plan['play_plan'] = play_plan
    plan['word_plan'] = word_plan

    return plan

def generate_plan_feedback(audio_files_dir_base, 
                            words,
                            word_num,
                            fb_type,
                            condition,
                            ch_speaker,
                            ch_headphone,
                            condition_params,
                            master_volume = 1.0):
    """
    word_num : index starts from 1
    fb_type : 0 (neutral), 1 (positive), 2 (very positive), 3 (exceptionally positive)
    """
    number_of_words = len(words)

    import pyscab
    audio_info = list()
    audio_files = pyscab.DataHandler()

    if fb_type == 0:
        fb_fname = 'neutral.wav'
    elif fb_type == 1:
        fb_fname = 'positive.wav'
    elif fb_type == 2:
        fb_fname = 'very_positive.wav'
    elif fb_type == 3:
        fb_fname = 'exceptionally_positive.wav'
    else:
        raise ValueError("Unkown feedback type %d" %fb_type)

    dir = os.path.join(audio_files_dir_base,
                        'misc',
                        'relax.wav')
    audio_info.append([0, dir, master_volume])
    audio_files.load(0, dir, volume=master_volume)

    word = words[int(word_num) - 1]
    dir = os.path.join(audio_files_dir_base,
                        'feedback',
                        fb_fname)
    audio_info.append([1, dir, master_volume])
    audio_files.load(1, dir, volume=master_volume)

    dir = os.path.join(audio_files_dir_base,
                    'words',
                    'slow',
                    '%s.wav' %word)
    audio_info.append([2, dir, master_volume])

    if condition_params['output'] == 'speaker':
        spk = [ch_speaker[0]]
    elif condition_params['output'] == 'headphone':
        spk = ch_headphone

    play_plan = list()
    time = 0
    #play_plan.append([time, 0, spk, 0]) # relax
    #time += audio_files.get_length_by_id(0)
    #time += 1
    play_plan.append([time, 1, spk, 0]) # feedback
    time += audio_files.get_length_by_id(1)

    if fb_type != 0:
        time += 1
        play_plan.append([time, 2, spk, 0]) # word

    plan = dict()
    plan['audio_info'] = audio_info
    plan['play_plan'] = play_plan

    return plan

def check_file_exists(f_dir, extension):
    """
    Parameters
    ----------

    f_dir : path-like
        don't include extension
    extension : str
        don't include .(dot)
    """
    f_name = f_dir + '.' + extension
    if os.path.exists(f_name):
        idx = 1
        while True:
            idx += 1
            f_name = f_dir + '_%d.%s' %(idx, extension)
            if not os.path.exists(f_name):
                break

    return f_name

def gen_eeg_fname(dir_base, f_name_prefix, condition, soa, idx_run, extension, session_type=None):
    """
    Parameters
    ==========
    session_type : str, 'pre' or 'post', Default = None
        specify presession or postsession if it's offline session
        None is corresponding to online session

    """
    if session_type is None:
        f_name = os.path.join(dir_base,
                            f_name_prefix + "_" + condition + "_" + str(int(soa*1000)) + "_" + str(idx_run+1).zfill(4))
    elif session_type == 'pre':
        f_name = os.path.join(dir_base,
                            f_name_prefix + "_pre_" + condition + "_" + str(int(soa*1000)) + "_" + str(idx_run+1).zfill(4))
    elif session_type == 'post':
        f_name = os.path.join(dir_base,
                            f_name_prefix + "_post_" + condition + "_" + str(int(soa*1000)) + "_" + str(idx_run+1).zfill(4))
    else:
        raise ValueError("Unknown session type : %s" %str(session))
    f_name = check_file_exists(f_name, extension)
    return f_name

def get_n_sessions(data_dir, subject_code, datestr):
    import json
    
    val = dict()
    val['n_offline'] = 0
    val['n_online'] = 0
    val['offline_sessions'] = list()
    val['online_sessions'] = list()

    sessions = list()
    folders = sort_list(os.listdir(data_dir))
    for folder in folders:
        if '_'.join(folder.split('_')[1:]) != datestr and folder.split('_')[0].lower() == subject_code.lower():
            sessions.append(folder)
            
    sessions = sort_list(sessions)

    for session in sessions:
        meta = json.load(open(os.path.join(data_dir, session, 'meta.json'), 'r'))
        if meta['session_type'] == 'offline':
            val['n_offline'] += 1
            val['offline_sessions'].append(session)
        elif meta['session_type'] == 'online':
            val['n_online'] += 1
            val['online_sessions'].append(session)
        else:
            raise ValueError("unkown session_type : %s" %(str(meta['session_type'])))
        
    return val

def get_files_for_calibration(n_sessions, data_dir, extension, soa_ms, condition, f_name_prefix, th_soa_ms = 350):

    files_for_calibration = list()

    if n_sessions['n_offline'] >= 2 and n_sessions['n_online'] == 0:
        # first online session
        # load data which has same (speaker) condition and soa from former 2 sessions
        for session in sort_list(n_sessions['offline_sessions']):
            files = os.listdir(os.path.join(data_dir, session))
            tmp = list()
            for file in files:
                if file.split('.')[-1] == extension:
                    tmp.append(file)
            files = tmp
            for file in files:
                if f_name_prefix in file:
                    condition_file = file.split('_')[-3]
                    soa_file = int(file.split('_')[-2])
                    if soa_ms >= th_soa_ms and soa_file >= th_soa_ms and condition_file == condition:
                        files_for_calibration.append(os.path.join(data_dir, session, file))
                    elif soa_ms < th_soa_ms and soa_file < th_soa_ms and condition_file == condition:
                        files_for_calibration.append(os.path.join(data_dir, session, file))

    elif n_sessions['n_offline'] >= 2 and n_sessions['n_online'] > 0:
        # load previous online session (even if speaker condition or soa was different)
        online_sessions = sort_list(n_sessions['online_sessions'])
        session = online_sessions[-1]
        files = os.listdir(os.path.join(data_dir, session))
        for file in files:
            if file.split('.')[-1] == extension:
                files_for_calibration.append(os.path.join(data_dir, session, file))
    elif n_sessions['n_offline'] < 2:
        # no offline session or one offline session
        pass

    return sort_list(files_for_calibration)

def get_ch_names_LSL(inlet):

    ch_names = list()

    info = inlet.info()
    ch = info.desc().child("channels").child("channel")
    for k in range(info.channel_count()):
        ch_names.append(ch.child_value('label'))
        ch = ch.next_sibling()
    
    return ch_names

def barplot(state_dict : dict[str, any], words):
    import time
    import matplotlib.pyplot as plt

    plt.ion()
    fig = plt.figure(1)
    n_classes = len(words)
    

    while True:
        #plt.figure(1)
        colors = ['tab:blue' for m in range(n_classes)]
        if state_dict["index_best_class"] is not None:
            colors[int(state_dict["index_best_class"])] = 'tab:green'
        val = state_dict["mean_classificaiton_values"][0:n_classes] # can probably remove '[0:n_classes]'
        fig.clear()
        plt.bar(words, val, color = colors)
        fig.canvas.draw()
        fig.canvas.flush_events()
        time.sleep(0.1)


class pandas_save(object):
    def __init__(self, file_dir):
        import pandas as pd
        
        f_name = file_dir.split('.')[0]
        _f_name = f_name
        idx = 1
        while True:
            if os.path.exists(f_name + '.pkl'):
                idx += 1
                f_name = _f_name + "_%d"%idx
            else:
                break
        self.file_dir = f_name + '.pkl'

        self.df = None

    def add(self, data, index = None, columns = None, html=False, csv=False):
        import pandas as pd
        if os.path.exists(self.file_dir):
            df = pd.read_pickle(self.file_dir)
            #if columns is not None:
            #    print("Warning (pylibs) : column value cannot overwrite, original culumns will be used.")
            columns = df.columns
            df_add = pd.DataFrame(data=data, columns=columns, index=index)
            df = pd.concat([df, df_add])
        else:
            df = pd.DataFrame(data=data, index=index, columns=columns)
            self.is_exists = True
        _ = df.to_pickle(self.file_dir)
        self.df = df
        if html:
            self.save_html()
        if csv:
            self.save_csv()
    
    def save_csv(self):
        self.df.to_csv(self.file_dir[:-4] + ".csv")

    def save_html(self):
        self.df.to_html(self.file_dir[:-4] + ".html")
    
    def print(self):
        import pandas as pd
        df = pd.read_pickle(self.file_dir)
        print(df)