import librosa
import soundfile as sf
import os
import sys

words = ['Spiegel', 'Blender', 'Groente', 'Stropdas', 'Tractor', 'Knuffel']
pitchs = [1, 0, -1.5, -1.5, 0, 1]

for idx, word in enumerate(words):
    save_base = os.path.join("pitch-shifted-converted", word)
    isExist = os.path.exists(save_base)
    if not isExist:
        os.makedirs(save_base)    
    for idx_pitch, pitch in enumerate(pitchs):
        y, sr = librosa.load(os.path.join("pitch-shifted", word, "%d.wav"%(idx_pitch+1)), sr=None)
        sf.write(os.path.join(save_base, "%d.wav"%(idx_pitch+1)), data=y, samplerate=sr, subtype='PCM_16')