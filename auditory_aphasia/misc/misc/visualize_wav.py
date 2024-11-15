import os
import sys
import argparse

import librosa
import matplotlib.pyplot as plt

parser = argparse.ArgumentParser()

parser.add_argument('files', nargs='*')

args = parser.parse_args() 
files = args.files

N = len(files)

fig, axs = plt.subplots(N)

y = list()
sr = list()
for idx, file in enumerate(files):
    _y, _sr = librosa.load(file, sr=None)
    axs[idx].plot(_y)
    y.append(_y)
    sr.append(_sr)

plt.show()





#y, sr = librosa.load(, sr=None)