import os
import pyscab

from auditory_aphasia.common.sudoku_matrix import SudokuMarix


def generate_run_plan(audio_files_dir_base, words, condition, condition_params, master_volume = 1.0):

    number_of_words = len(words)

    #----------------------------------------------------------------------
    # generating stimulation plan

    sudoku = SudokuMarix()
    word_to_speak = sudoku.generate_matrix(1, number_of_words)[0]
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
                            "%d.wav" %word_to_speak[m-1])
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
                "%d.wav" %word_to_speak[m-1])
        audio_info.append([m, dir, master_volume])

    plan = dict()
    plan['audio_info'] = audio_info
    plan['audio_files'] = audio_files
    plan['word_to_speak'] = word_to_speak
    plan['targetplan'] = targetplan

    return plan