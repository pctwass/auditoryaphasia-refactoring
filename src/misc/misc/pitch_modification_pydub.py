#import librosa
#import soundfile as sf
import os
import numpy as np
from pydub import AudioSegment
from numpy.random import uniform
filename = '1.wav'
sound = AudioSegment.from_file(filename, format=filename[-3:])

octaves = 0.5
for octaves in np.linspace(-1,1,21):
    new_sample_rate = int(sound.frame_rate * (2.0 ** octaves))
    hipitch_sound = sound._spawn(sound.raw_data, overrides={'frame_rate': new_sample_rate})
    hipitch_sound = hipitch_sound.set_frame_rate(44100)
#export / save pitch changed sound
    hipitch_sound.export(f"octave_{octaves}.wav", format="wav")


import sys
sys.exit()
words = ['Spiegel', 'Blender', 'Groente', 'Stropdas', 'Tractor', 'Knuffel']
pitchs = [1, 0, -1.5, -1.5, 0, 1]

home_dir = os.path.expanduser('~')
f_base = os.path.join(home_dir, 'Music', 'DutchWords')

for idx, word in enumerate(words):
    f_name = "%d.wav" %(idx+1)
    f_dir = os.path.join(f_base, f_name)
    y, sr = librosa.load(f_dir, sr=None)
    for idx_pitch, pitch in enumerate(pitchs):
        y_shift = librosa.effects.pitch_shift(y=y, sr=sr, n_steps=pitch, bins_per_octave=12)
        sf.write(os.path.join(f_base, word, "%d.wav"%(idx_pitch+1)), data=y_shift, samplerate=sr, subtype='PCM_16')