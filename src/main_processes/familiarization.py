import pyscab
import os
import sys
import time
import argparse

import src.config.config as config
import src.config.system_config as system_config
import src.process_management.intermodule_communication as intermodule_comm
import src.common.directory_navigator as dir_navigator
import src.condition_params as condition_params

from src.common.sudoku_matrix import SudokuMarix
from src.process_management.process_communication_enums import AudioStatus
from src.process_management.process_manager import ProcessManager
from src.process_management.state_dictionaries import init_audio_state_dict
from src.plans.audio_plan import generate_audio_plan
from src.plans.stimulation_plan import generate_stimulation_plan

from src.logging.logger import get_logger
logger = get_logger()


def gen_plan_play_oddball(
        soa : float = 1, 
        num_reps : int = 10,
        volume : float = 1
) -> tuple[list[any], pyscab.DataHandler]:
    oddball_base = os.path.join(system_config.repository_dir_base, 'media', 'audio', 'oddball')
    
    non_target_id = 1
    target_id = 21

    audio_files = pyscab.DataHandler()
    audio_files.load(non_target_id, os.path.join(oddball_base, system_config.oddball_non_target), volume=volume)
    audio_files.load(target_id, os.path.join(oddball_base, system_config.oddball_target), volume=volume)
    
    #soa_oddball = 1.0
    #number_of_repetitions_oddball = 1 # 50->5min

    play_plan = list()
    stim_plan = generate_stimulation_plan(6, num_reps)
    time_plan = 0
    for stim in stim_plan:
        if stim == 1:
            play_plan.append([time_plan, target_id, [1], 21])
        else:
            play_plan.append([time_plan, non_target_id, [1], 1])
        time_plan += soa

    return play_plan, audio_files


def gen_plan_play_word(
        word_idx_to_be_played : int, 
        repo_base_dir : str, 
        soa : float = 1.5, 
        channel : enumerate[int] = [1], 
        marker : int = None, 
        volume : float = 1
) -> tuple[list[any], pyscab.DataHandler]:
    data = pyscab.DataHandler()
    condition = '6d'
    words_to_speak = [config.words[word_idx_to_be_played-1]]

    load_audio_data(data, repo_base_dir, condition, words_to_speak, volume, load_sentences = False)

    plan = list()
    for m in range(number_of_repetitions):
        plan.append([m*soa, 1, channel, marker])
        
    return plan, data


def gen_plan_sentence_and_word(
        pyscab_audio_interface : pyscab.AudioInterface, 
        word_idx_to_be_played : int, 
        repo_base_dir : str, 
        channel : enumerate[int] = [1], 
        volume : float = 1
):
    data = pyscab.DataHandler()
    condition = '6d'
    words_to_speak = [config.words[word_idx_to_be_played-1]]

    load_audio_data(data, repo_base_dir, condition, words_to_speak, volume)
    
    word_data = data.get_data_by_id(1)
    sentence_data = data.get_data_by_id(11)
    
    # execute plan
    # --------------------------------------------------------------------------------
    pyscab_audio_interface.open()
    pyscab_audio_interface.play(sentence_data, channel)
    time.sleep(data.get_length_by_id(11))

    input("Press Any Key to Play Word : %s" %(config.words[word_idx_to_be_played-1]))
    pyscab_audio_interface.play(word_data, channel)
    time.sleep(data.get_length_by_id(1)*1.05)

    pyscab_audio_interface.close()


def gen_plan_spk_fam(
        repo_base_dir : str, 
        condition : str, 
        soa : float = 1, 
        volume : float = 1
) -> tuple[list[any], pyscab.DataHandler]:
    data = pyscab.DataHandler()

    sudoku = SudokuMarix()
    #words_to_speak = [1, 2, 3, 4, 5, 6]
    words_to_speak = sudoku.generate_matrix(1, 6)[0]

    load_audio_data(data, repo_base_dir, condition, words_to_speak, volume, load_restat=True, load_relax=True)
    audio_plan = generate_audio_plan(
        data,
        soa,
        words_to_speak,
        number_of_repetitions=number_of_repetitions,
        pause_between_trial = None
    )

    return audio_plan, data


def gen_plan_hp_fam(
        repo_base_dir : str, 
        condition : str, 
        soa : float = 1, 
        volume : float = 1,
        channel : enumerate[int] = [7,8], 
):
    data = pyscab.DataHandler()

    sudoku = SudokuMarix()
    #words_to_speak = [1, 2, 3, 4, 5, 6]
    words_to_speak = sudoku.generate_matrix(1, 6)[0]

    load_audio_data(data, repo_base_dir, condition, words_to_speak, volume, load_restat=True, load_relax=True)
    audio_plan = generate_audio_plan(
        data,
        soa,
        words_to_speak,
        number_of_repetitions=number_of_repetitions,
        start_sound_channel=channel,
        channel=channel
    )

    return audio_plan, data


def parse_familirization_arguments():
    familirization_parser = argparse.ArgumentParser()
    familirization_parser.add_argument('-n', '--n_reps', type=int, default=3)
    familirization_parser.add_argument('-v', '--visual', action='store_true')
    return familirization_parser.parse_args()
    

def set_globals(familirization_args):
    global is_visual
    global speaker_showed
    global number_of_repetitions
    global intermodule_comm_outlet

    is_visual = familirization_args.visual
    speaker_showed = False
    number_of_repetitions = familirization_args.n_reps

    if is_visual:
        intermodule_comm_outlet = intermodule_comm.create_intermodule_communication_outlet('main', channel_count=4, source_id='main')


def send_marker_visual(val : int):
    global is_visual
    if is_visual:
        global speaker_showed
        global intermodule_comm_outlet
        if val == 210:
            intermodule_comm.send_cmd_LSL(intermodule_comm_outlet, 'visual', 'show_speaker')
            speaker_showed = True
        
        if val >= 200 and val <= 205:
            speaker_showed = True
            spk_num = str(val)
            spk_num = int(spk_num[-1])+1
            intermodule_comm.send_cmd_LSL(intermodule_comm_outlet, 'visual', 'highlight_speaker', spk_num)

        if val >= 101 and val <= 116:
            if speaker_showed:
                intermodule_comm.send_cmd_LSL(intermodule_comm_outlet, 'visual', 'show_crosshair')
                speaker_showed = False


def load_audio_data(
        data : pyscab.DataHandler, 
        repo_base_dir : str, 
        condition : str, 
        words_to_speak : str, 
        volume : float, 
        load_sentences : bool = True, 
        load_restat : bool = False, 
        load_relax : bool = False
):
    for idx, word in enumerate(config.words):
        if condition_params.conditions[condition]['single_file']:
            file_name = '1.wav'
        else:
            file_name = f'{words_to_speak[idx]}.wav'

        word_file_path = dir_navigator.get_word_audio_file_path(repo_base_dir, condition, word, file_name)
        data.load(idx+1, word_file_path, volume = volume)
        
        if load_sentences:
            sentence_file_path = dir_navigator.get_sentence_audio_file_path(repo_base_dir, condition, word, file_name)
            data.load(idx+1+10, sentence_file_path, volume = volume)

    if load_restat:
        restart_file_path = dir_navigator.get_restart_audio_file_path(repo_base_dir)
        data.load(100, restart_file_path, volume = volume)
    
    if load_relax:
        relax_file_path = dir_navigator.get_relax_audio_file_path(repo_base_dir)
        data.load(101, relax_file_path, volume = volume)


def main():
    familirization_args = parse_familirization_arguments()
    set_globals(familirization_args)

    if familirization_args.visual:
        # create process manager
        process_manager = ProcessManager()
            
        # open VisualFeedbackController as a new Process
        visual_process, visual_fb_state_dict = process_manager.create_visual_fb_process(kwargs=dict(name='visual', name_main_outlet='main'))
        visual_process.start()
        while visual_fb_state_dict["LSL_inlet_connected"] is False:
            time.sleep(0.1) # wait until module is connected

    words_to_play = config.words
    master_volume = config.master_volume
    repo_base_dir = system_config.repository_dir_base

    audio_state_dict = init_audio_state_dict()

    pyscab_audio_interface = pyscab.AudioInterface(
        device_name = system_config.audio_device_name,
        n_ch = system_config.n_channels,
        format=system_config.format,
        frames_per_buffer = system_config.frames_per_buffer
    )
    
    pyscab_stim_controller = pyscab.StimulationController(
        pyscab_audio_interface, 
        marker_send=send_marker_visual, 
        state_dict=audio_state_dict
    )

    if os.environ['computername'].lower() == 'am4':
        hp_ch = [1,2]
    else:
        hp_ch = [7,8]

    is_familiarizing = True
    while is_familiarizing:
        try:
            print('--------------------------------------------------------')
            print('Familiarization begins. You have the following choices:')
            print('0: Quit familiarization')
            print('1: Oddball')
            print('2: Play Each word')
            print('3: Sentences and words from one speaker')
            print('4: 6D run with customizable SOA.')
            print('5: StereoPitch run with customizable SOA.')
            print('6: Mono run with customizable SOA.')
            print('------ Choose one now by inserting a number between [0-6] -------')
            selected_fam_stage = int(input())
            
            match selected_fam_stage:
                case 0:
                    sys.exit()
                
                # play oddball
                case 1:
                    audio_plan, audio_data = gen_plan_play_oddball()
                    
                # play each word
                case 2:
                    print('Stage  2: Select word to play. (The index starts from 1)')
                    print('Words : ' + str(words_to_play))
                    selected_word = input()
                    audio_plan, audio_data = gen_plan_play_word(int(selected_word), repo_base_dir, volume=master_volume) 

                # sentence and word
                case 3:
                    print('Stage 3: Select word to play. (The index starts from 1)')
                    print('Words : ' + str(words_to_play))
                    selected_word = input()
                    gen_plan_sentence_and_word(pyscab_audio_interface, int(selected_word), repo_base_dir, volume=master_volume)
                    continue
                
                # 6d
                case 4:
                    print('Stage 4: Specify SOA (in seconds) for the familiarization:')
                    selected_soa = input()
                    print('Do you want to play 6d-pitch? if so, type y')
                    en_pitch_shift = input()
                    if en_pitch_shift == 'y':
                        condition = '6d-pitch'
                    else:
                        condition = '6d'
                    audio_plan, audio_data = gen_plan_spk_fam(repo_base_dir, condition, soa=float(selected_soa), volume=master_volume)

                # stereo-pitch
                case 5:
                    print('Stage 5: Specify SOA (in seconds) for the familiarization:')
                    selected_soa = input()
                    audio_plan, audio_data = gen_plan_hp_fam(repo_base_dir, condition='stereo-pitch', soa=float(selected_soa), volume=master_volume, channel=hp_ch)

                # mono
                case 6:
                    print('Stage 6: Specify SOA (in seconds) for the familiarization:')
                    selected_soa = input()
                    audio_plan, audio_data = gen_plan_hp_fam(repo_base_dir, condition='mono', soa=float(selected_soa), volume=master_volume, channel=hp_ch)

                case _:
                    continue

            pyscab_stim_controller.open()
            pyscab_stim_controller.play(audio_plan, audio_data, time_termination = 'auto', pause=0)
            pyscab_stim_controller.close()

        except KeyboardInterrupt:
            audio_state_dict["audio_status"] = AudioStatus.FINISHED_PLAYING
            if familirization_args.visual:
                visual_process.terminate()
            return

        except ValueError:
            print("ERROR : input value was invailed.")
            main()

        except FileNotFoundError:
            print("ERROR : File was not found")
            main()
            
    audio_state_dict["audio_status"] = AudioStatus.FINISHED_PLAYING
    if familirization_args.visual:
        visual_process.terminate()
    
