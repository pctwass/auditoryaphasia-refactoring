import os
import sys
import shutil

def pitch_shift(f_name, f_save, pitch, verbose=False):
    exec_dir = os.path.join('sbsms-convert','sbsms-convert.exe')
    cmd = str(exec_dir) + " " + str(f_name) + " " + str(f_save) + " 1 1 " + "%f %f" %(pitch, pitch)
    val = os.system(cmd)
    if verbose:
        print(cmd)
        print(val)

def generate_6d_mono(words, condition, base_dir, save_dir):
    files = os.listdir(os.path.join(base_dir, 'words'))
    for word in words:
        if not os.path.exists(os.path.join(save_dir, 'words', condition, word)):
            os.makedirs(os.path.join(save_dir, 'words', condition, word))
        if not os.path.exists(os.path.join(save_dir, 'sentences', condition, word)):
            os.makedirs(os.path.join(save_dir, 'sentences', condition, word))
        shutil.copyfile(os.path.join(base_dir, 'words', '%s.wav'%word), os.path.join(save_dir, 'words', condition, word, '1.wav'))
        shutil.copyfile(os.path.join(base_dir, 'sentences', '%s.wav'%word), os.path.join(save_dir, 'sentences', condition, word, '1.wav'))

def check_dir(dir):
    isExist = os.path.exists(dir)
    if not isExist:
        os.makedirs(dir) 

def pitch_shifter(condition,
                  source_condition,
                  source_single_file,
                  words,
                  pitchs,
                  base_dir,
                  save_dir,
                  convert_cat = ['words', 'sentences']):
    import librosa
    import soundfile as sf

    for cat in convert_cat:
        for word in words:
            check_dir(os.path.join(save_dir, 'tmp', word))
            if source_single_file:
                for idx, pitch in enumerate(pitchs):
                    pitch_shift(os.path.join(base_dir, cat, source_condition, word, '1.wav'),
                                os.path.join(save_dir, 'tmp', word, '%d.wav' %(idx+1)),
                                pitch,
                                True)
            else:
                for idx, pitch in enumerate(pitchs):
                    pitch_shift(os.path.join(base_dir, cat, source_condition, word, '%d.wav' %(idx+1)),
                                os.path.join(save_dir, 'tmp', 'word', '%d.wav' %(idx+1)),
                                pitch,
                                True)
            
            #save_base = os.path.join(save_dir, 'tmp', word)
            #check_dir(save_base)
            #print(base_dir)
            #f_list = os.listdir(os.path.join(base_dir, cat, condition, word))
            #n_files = len(f_list)
            #if n_files == 1:
            #elif n_files == n_spks:
            #    for idx, pitch in enumerate(pitchs):
            #        pitch_shift(os.path.join(base_dir, cat, condition, word, '%d.wav' %(idx+1)),
            #                    os.path.join(save_base, '%d.wav' %(idx+1)),
            #                    pitch,
            #                    True)
            #else:
            #    raise ValueError("number of files contained in folder is invalid.")

        for word in words:
            #save_base = os.path.join(base_dir, cat, condition+convert_suffix, word)
            check_dir(os.path.join(save_dir, cat, condition, word))
            for idx, pitch in enumerate(pitchs):
                y, sr = librosa.load(os.path.join(base_dir, 'tmp', word, '%d.wav' %(idx+1)), sr=None)
                sf.write(os.path.join(save_dir, cat, condition, word, '%d.wav' %(idx+1)),
                         data=y,
                         samplerate=sr,
                         subtype='PCM_16')
        # delete temporary folder which contains output of sbsms
        shutil.rmtree(os.path.join(base_dir, 'tmp'))