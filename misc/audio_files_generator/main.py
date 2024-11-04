import os
import sys
import shutil
import utils

home_dir = os.path.expanduser('~')

base_dir = os.path.join(home_dir, "Documents", "Audacity")

save_dir = os.path.join(home_dir, "Documents", "audio")

files = os.listdir(os.path.join(base_dir, 'words'))

words = list() 
for file in files:
    if file.split('.')[-1] == 'wav':
        words.append(file.split('.')[0])

# generate 6d and mono        
#utils.generate_6d_mono(words, '6d', base_dir, save_dir) 
#utils.generate_6d_mono(words, 'mono', base_dir, save_dir)

pitchs = [1, 0, -1.5, -1.5, 0, 1]

base_dir = os.path.join(home_dir, "Documents", "audio")
utils.pitch_shifter(condition = 'stereo-pitch',
                    source_condition = 'stereo',
                    source_single_file = True,
                    words = words,
                    pitchs = pitchs,
                    base_dir = base_dir,
                    save_dir = save_dir)