import librosa
import soundfile as sf
import os
import sys

cmd = "dir"

returned_value = os.system(cmd)  # returns the exit code in unix
print('returned value:', returned_value)

words = ['Spiegel', 'Blender', 'Groente', 'Stropdas', 'Tractor', 'Knuffel']
pitchs = [1, 0, -1.5, -1.5, 0, 1]

#home_dir = os.path.expanduser('~')
#f_base = os.path.join(home_dir, 'Music', 'DutchWords')
#f_base = "D:\\Users\\simon.kojima\\git\\auditoryAphasia-python\\src\\misc"

exe_dir = os.path.join('sbsms-convert','sbsms-convert.exe')

print(exe_dir)

for idx, word in enumerate(words):
    f_name = "%d.wav" %(idx+1)
    f_dir = os.path.join(f_name)
    save_base = os.path.join("pitch-shifted", word)
    isExist = os.path.exists(save_base)
    if not isExist:
        os.makedirs(save_base)    
    for idx_pitch, pitch in enumerate(pitchs):
        cmd = str(exe_dir) + " " + str(f_dir) + " " + str(os.path.join(save_base,"%d.wav"%(idx_pitch+1))) + " 1 1 " + "%f %f" %(pitch, pitch)
        print(cmd)
        val = os.system(cmd)
        print(val)