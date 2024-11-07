import pyscab

from src.plans.stimulation_plan import generate_stimulation_plan
from src.common.sudoku_matrix import SudokuMarix


def generate_audio_plan(
        data_handler : pyscab.DataHandler,
        soa : float,
        words_to_speak : enumerate[str|int],
        number_of_repetitions : int = 1,
        channel : enumerate[int] = None,
        start_sound_channel : enumerate[int] = [1],
        pause_between_trial : float = 5,
        pause_after_start_sound : float = 2,
        pause_between_sentence_and_subtrial : float = 3.5,
        pause_before_trial_completion : float = 2,
        offset_start : float = 1
) -> list[any]:
    
    time_plan = 0
    time_plan += offset_start

    sudoku = SudokuMarix()
    target_plan = sudoku.generate_matrix(1, 6)[0]

    if channel is None:
        channel = [words_to_speak[stimulation_plan[m]-1]]
    
    audio_plan = list()
    for trial_idx in range(6):
        target = target_plan[trial_idx]
        stimulation_plan = generate_stimulation_plan(6, number_of_repetitions)

        audio_plan.append([time_plan, 100, start_sound_channel, 210])
        time_plan += data_handler.get_length_by_id(100)
        time_plan += pause_after_start_sound
        audio_plan.append([time_plan, target+10, channel, 200 + target])
        time_plan += data_handler.get_length_by_id(target+10)
        time_plan += pause_between_sentence_and_subtrial

        for m in range(0, len(stimulation_plan)):
            if stimulation_plan[m] == target:
                time_plan += soa
                audio_plan.append([time_plan, stimulation_plan[m], channel, 110 + target])
            else:
                time_plan += soa
                audio_plan.append([time_plan, stimulation_plan[m], channel, 100 + stimulation_plan[m]])

        time_plan += data_handler.get_length_by_id(stimulation_plan[m])
        time_plan += pause_before_trial_completion
        audio_plan.append([time_plan, 101, [1], 0])
        time_plan += data_handler.get_length_by_id(101)
        
        if pause_between_trial is not None:
            time_plan += pause_between_trial

    return audio_plan