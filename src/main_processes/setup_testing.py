import pyscab
import os
import random

import src.config.config as config
import src.config.system_config as system_config

from src.plans.stimulation_plan import generate_stimulation_plan


def test_multi_ch(freq = 440,freq_1 = 440*1.2, duration = 0.5, volume = 1, num_rep = 3, soa = 0.7, ch = [1,2,3,4,5,6]):
    data = pyscab.DataHandler()

    sine = pyscab.generate_pcm(number_of_channels=1, frequency=freq, duration=0.5, format="INT16", volume=volume, window='linear')
    data.add_pcm(0, sine)

    sine_1 = pyscab.generate_pcm(number_of_channels=1, frequency=freq_1, duration=0.5, format="INT16", volume=volume, window='linear')
    data.add_pcm(1, sine_1)

    n_ch = len(ch)

    audio_plan = list()
    for m in range(0, n_ch*num_rep):
        ch = m%n_ch+1
        if ch == 1:
            id = 1
        else:
            id = 0
        audio_plan.append([m*soa, id, [ch], 1])

    return audio_plan, data

def test_stereo(volume = 1, num_rep = 20, ch = [7,8], soa = 1):
    data = pyscab.DataHandler()
    #data.load(1, "./left.wav")
    #data.load(2, "./right.wav")

    data.load(1, os.path.join(system_config.repository_dir_base, 'media', 'audio', 'misc', 'left.wav'))
    data.load(2, os.path.join(system_config.repository_dir_base, 'media', 'audio', 'misc', 'right.wav'))

    audio_plan = list()
    time = 0
    for m in range(0, num_rep):
        audio_plan.append([time, 1, [ch[0]], 1])
        time += soa
        audio_plan.append([time, 2, [ch[1]], 1])
        time += soa

    return audio_plan, data

def spk_volume_adjust(base_dir, words, volume = 1, num_rep = 10, soa = 0.35, condition = '6d',):
    data = pyscab.DataHandler()

    random.shuffle(words)

    for m in range(0,6):
        #word_dir = base_dir + "words" + "/" + str(m+1) + ".wav"
        word_dir = os.path.join(base_dir, 'words', condition, words[m], '%s.wav'%(str(1)))
        data.load(m+1, word_dir, volume = volume)

    for m in range(0,6):
        #sentence_dir =  base_dir + "sentences" + "/" + str(m+1) + ".wav"
        sentence_dir = os.path.join(base_dir, 'sentences', condition, words[m], '%s.wav'%(str(1)))
        data.load(m+1+10, sentence_dir, volume = volume)

    wordplan = generate_stimulation_plan(6, num_rep)
    word_to_speak_rnd = generate_stimulation_plan(6, num_rep)

    audio_plan = list()
    for m in range(0, len(wordplan)):
        audio_plan.append([m*soa, wordplan[m], [word_to_speak_rnd[m]], 1])
    
    ################# HACK DEMO #######################################################
    # t = 0
    # for s in range(2):
    #     audio_plan.append([t+2, s+13, [1,2,3,4,5,6], 1])
    #     t+=6
    #     for m in range(0, len(wordplan)):
    #         audio_plan.append([t, wordplan[m], [word_to_speak_rnd[m]], 1])
    #         t+=soa
    # print('audio', audio_plan)
    # print('data', data)
    ################# END HACK DEMO #######################################################
    
    return audio_plan, data
    

def sendMarker(val):
    pass
    
def main():

    #words = ['Spiegel', 'Blender', 'Groente', 'Stropdas', 'Tractor', 'Knuffel']

    words = config.words

    #home_dir = os.path.expanduser('~')
    #base_dir = "D:/Users/auditoryAphasia_stereo/auditoryAphasia_portable/auditoryAphasia/Feedbacks/media/online_paradigm/"
    base_dir = os.path.join(system_config.audio_files_dir_base)

    #DEVICE_NAME = 'X-AIR ASIO Driver'
    ahc = pyscab.AudioInterface(device_name = system_config.audio_device_name, n_ch = system_config.n_channels, format=system_config.format, frames_per_buffer = system_config.frames_per_buffer)
    stc = pyscab.StimulationController(ahc, marker_send=sendMarker)
    stc.open()


    isfamiliarizing = True

    MasterVolume = 0.25

    while isfamiliarizing:
        print('--------------------------------------------------------')
        print('Setup Test. You have the following choices:')
        print('1: 6D test (ch1-6)')
        print('2: stereo test (ch7-8)')
        print('3: Speakers Volume test')
        print('0: QUIT')
        print('------ Choose one now by inserting a number between [0-6] -------')
        selected_fam_stage = input()
        if int(selected_fam_stage) == 1:
            audio_plan, audio_data = test_multi_ch(volume=MasterVolume)
        elif int(selected_fam_stage) == 2:
            audio_plan, audio_data = test_stereo(volume=MasterVolume)
        elif int(selected_fam_stage) == 3:
            audio_plan, audio_data = spk_volume_adjust(base_dir, words, volume=MasterVolume)
        elif int(selected_fam_stage) == 0:
            break
        else:
            continue
        stc.play(audio_plan, audio_data, time_termination = 'auto')

    stc.close()

    #ahc.terminate()
