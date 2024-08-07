import librosa
import pyrubberband

import soundfile as sf
import os

y, sr = librosa.load("3.wav", sr=None)
#y_shift = pyrubberband.pyrb.pitch_shift(y, sr, -1.5)
y_shift = librosa.effects.pitch_shift(y=y, sr=sr, n_steps=-1.5, bins_per_octave=12, res_type = 'linear')
sf.write("out.wav", data=y_shift, samplerate=sr, subtype='PCM_16')

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