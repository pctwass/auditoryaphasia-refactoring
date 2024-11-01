import os
import re
import json
import pylsl


def check_file_exists_on_extenstion(f_dir:str, extension:str) -> str:
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


# used only for calibration
def get_n_sessions(data_dir:str, subject_code:str, datestr:str) -> dict[str, int|list[str]]:
    sessions_info_dict = dict()
    sessions_info_dict['n_offline'] = 0
    sessions_info_dict['n_online'] = 0
    sessions_info_dict['offline_sessions'] = list()
    sessions_info_dict['online_sessions'] = list()

    sessions = list()
    folders = _sort_list(os.listdir(data_dir))
    for folder in folders:
        if '_'.join(folder.split('_')[1:]) != datestr and folder.split('_')[0].lower() == subject_code.lower():
            sessions.append(folder)
            
    sessions = _sort_list(sessions)

    for session in sessions:
        meta = json.load(open(os.path.join(data_dir, session, 'meta.json'), 'r'))
        if meta['session_type'] == 'offline':
            sessions_info_dict['n_offline'] += 1
            sessions_info_dict['offline_sessions'].append(session)
        elif meta['session_type'] == 'online':
            sessions_info_dict['n_online'] += 1
            sessions_info_dict['online_sessions'].append(session)
        else:
            raise ValueError("unkown session_type : %s" %(str(meta['session_type'])))
        
    return sessions_info_dict


# used only for calibration
def get_files_for_calibration(
        n_sessions : int, 
        data_dir : str, 
        extension : str, 
        soa_ms : float, 
        condition : str, 
        file_name_prefix : str, 
        th_soa_ms : float = 350
) -> enumerate[str]:
    files_for_calibration = list()

    if n_sessions['n_offline'] >= 2 and n_sessions['n_online'] == 0:
        # first online session
        # load data which has same (speaker) condition and soa from former 2 sessions
        for session in _sort_list(n_sessions['offline_sessions']):
            files = os.listdir(os.path.join(data_dir, session))
            tmp = list()
            for file in files:
                if file.split('.')[-1] == extension:
                    tmp.append(file)
            files = tmp
            for file in files:
                if file_name_prefix in file:
                    condition_file = file.split('_')[-3]
                    soa_file = int(file.split('_')[-2])
                    if soa_ms >= th_soa_ms and soa_file >= th_soa_ms and condition_file == condition:
                        files_for_calibration.append(os.path.join(data_dir, session, file))
                    elif soa_ms < th_soa_ms and soa_file < th_soa_ms and condition_file == condition:
                        files_for_calibration.append(os.path.join(data_dir, session, file))

    elif n_sessions['n_offline'] >= 2 and n_sessions['n_online'] > 0:
        # load previous online session (even if speaker condition or soa was different)
        online_sessions = _sort_list(n_sessions['online_sessions'])
        session = online_sessions[-1]
        files = os.listdir(os.path.join(data_dir, session))
        for file in files:
            if file.split('.')[-1] == extension:
                files_for_calibration.append(os.path.join(data_dir, session, file))
    elif n_sessions['n_offline'] < 2:
        # no offline session or one offline session
        pass

    return _sort_list(files_for_calibration)


# used only for acquisition
def get_channel_names_LSL(inlet : pylsl.StreamInlet) -> enumerate[str]:
    channel_names = list()

    info = inlet.info()
    ch = info.desc().child("channels").child("channel")
    for k in range(info.channel_count()):
        channel_names.append(ch.child_value('label'))
        ch = ch.next_sibling()
    
    return channel_names


def _sort_list(data : enumerate) -> enumerate|dict:
    return sorted(data, key=_natural_keys)

def _natural_keys(text : str) -> str:
    return [ _text_to_digit_if_digit(c) for c in re.split(r'(\d+)', text) ]

def _text_to_digit_if_digit(text : str) -> int|str:
    return int(text) if text.isdigit() else text
