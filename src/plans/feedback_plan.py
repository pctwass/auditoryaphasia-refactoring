import os


def generate_feedback_plan(audio_files_dir_base, 
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