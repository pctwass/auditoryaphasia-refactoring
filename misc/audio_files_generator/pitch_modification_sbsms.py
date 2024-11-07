import os
import sys
import shutil

import librosa
import soundfile as sf
from src.common import pitch_shift

cmd = "dir"
returned_value = os.system(cmd)  # returns the exit code in unix
print('returned value:', returned_value)

home_dir = os.path.expanduser('~')

f_base = os.path.join(home_dir,
                      'git',
                      'auditory_aphasia_project',
                      'auditory_aphasia_audios',
                      'Dutch')

#convert_condition = ['6d', 'stereo']
convert_condition = ['stereo']
convert_suffix = '_pitch'
convert_cat = ['words', 'sentences']

words = ['Spiegel', 'Blender', 'Groente', 'Stropdas', 'Tractor', 'Knuffel']
pitchs = [1, 0, -1.5, -1.5, 0, 1]

n_spks = len(pitchs)

exec_dir = os.path.join('sbsms-convert','sbsms-convert.exe')

def check_dir(dir):
    isExist = os.path.exists(dir)
    if not isExist:
        os.makedirs(dir) 

for condition in convert_condition:
    for cat in convert_cat:
        for word in words:
            save_base = os.path.join(f_base, 'tmp', word)
            check_dir(save_base)
            f_list = os.listdir(os.path.join(f_base, cat, condition, word))
            n_files = len(f_list)
            if n_files == 1:
                for idx, pitch in enumerate(pitchs):
                    pitch_shift(os.path.join(f_base, cat, condition, word, '1.wav'),
                                os.path.join(save_base, '%d.wav' %(idx+1)),
                                pitch,
                                True)
            elif n_files == n_spks:
                for idx, pitch in enumerate(pitchs):
                    pitch_shift(os.path.join(f_base, cat, condition, word, '%d.wav' %(idx+1)),
                                os.path.join(save_base, '%d.wav' %(idx+1)),
                                pitch,
                                True)
            else:
                raise ValueError("number of files contained in folder is invalid.")

        for word in words:
            save_base = os.path.join(f_base, cat, condition+convert_suffix, word)
            check_dir(save_base)
            for idx, pitch in enumerate(pitchs):
                y, sr = librosa.load(os.path.join(f_base, 'tmp', word, '%d.wav' %(idx+1)), sr=None)
                sf.write(os.path.join(save_base, '%d.wav' %(idx+1)),
                         data=y,
                         samplerate=sr,
                         subtype='PCM_16')
        # delete temporary folder which contains output of sbsms
        shutil.rmtree(os.path.join(f_base, 'tmp'))