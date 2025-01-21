import os
import sys
import shutil

import librosa
import soundfile as sf
from sbsms import pitch_shift

import numpy as np

cmd = "dir"
returned_value = os.system(cmd)  # returns the exit code in unix
print('returned value:', returned_value)

#home_dir = os.path.expanduser('~')
home_dir = os.path.join("D:\\", 'Users', 'simon.kojima')

f_base = os.path.join(home_dir,
                      'git',
                      #'auditory_aphasia_project',
                      'auditory_aphasia_audios',
                      'Dutch')

convert_condition = ['stereo-pitch']
convert_cat = ['words', 'sentences']

words = ['Spiegel', 'Blender', 'Groente', 'Stropdas', 'Tractor', 'Knuffel']
n_files_per_word = 6

level_factor = 1.7

def check_dir(dir):
    isExist = os.path.exists(dir)
    if not isExist:
        os.makedirs(dir) 

for condition in convert_condition:
    for cat in convert_cat:
        for word in words:
            save_base = os.path.join(f_base, cat, condition+"_level_adjusted", word)
            check_dir(save_base)
            for idx in range(n_files_per_word):
                y, sr = librosa.load(os.path.join(f_base, cat, condition, word, '%d.wav' %(idx+1)), sr=None)
                if y.dtype == np.float32:
                    y = y*level_factor
                    if max(abs(y)) >= 1.0:
                        raise ValueError("Audio File will be clipped with this level factor.")
                    
                else:
                    raise ValueError("It's not support the type %s" %str(y.dtype))
                sf.write(os.path.join(save_base,'%d.wav' %(idx+1)),
                        data=y,
                        samplerate=sr,
                        subtype='PCM_16')