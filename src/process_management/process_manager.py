import multiprocessing
import multiprocessing.process

import audio_stimulation.AudioStimulationInterface as AudioStimulationInterface
import src.visual_feedback.VisualFeedbackInterface as VisualFeedbackInterface
import src.acquisition.acquisition_interface as AcquisitionSystemInterface

from src.process_management.state_dictionaries import *
from src.barplot import barplot


class ProcessManager:
    def __init__(self) -> None:
        self._manager = multiprocessing.Manager()

    
    def create_subprocess(self, target, args : list = None) -> multiprocessing.Process:
        return multiprocessing.Process(target=target, args=args)


    def create_audio_stim_process(self, kwargs : dict[str,any] = None) -> tuple[multiprocessing.Process, dict[str, any]]:
        audio_stim_state_dict = init_audio_state_dict(self._manager)

        if kwargs is None:
            kwargs = dict(state_dict=audio_stim_state_dict)
        else:
            kwargs['state_dict'] = audio_stim_state_dict

        audio_process = multiprocessing.Process(target=AudioStimulationInterface.interface, kwargs=kwargs)
        return audio_process, audio_stim_state_dict


    def create_visual_fb_process(self, kwargs : dict[str,any] = None) -> tuple[multiprocessing.Process, dict[str, any]]:
        visual_fb_state_dict = init_visual_fb_state_dict(self._manager)

        if kwargs is None:
            kwargs = dict(state_dict=audio_state_dict)
        else:
            kwargs['state_dict'] = visual_fb_state_dict

        visual_fb_process = multiprocessing.Process(target=VisualFeedbackInterface.interface, kwargs=kwargs)
        return visual_fb_process, visual_fb_state_dict


    def create_acquisition_process(self, num_classes : int, kwargs : list = None) -> tuple[multiprocessing.Process, dict[str, any]]:
        live_barplot_process, live_barplot_state_dict = self.create_live_barplot_process(num_classes)

        acquisition_state_dict = init_acquisition_state_dict(self._manager)
        if kwargs is None:
            kwargs = dict(
                state_dict = acquisition_state_dict,
                live_barplot_state_dict = live_barplot_state_dict
            )
        else:
            kwargs['state_dict'] = acquisition_state_dict
            kwargs['live_barplot_state_dict'] = live_barplot_state_dict

        acquisition_process =  multiprocessing.Process(target=AcquisitionSystemInterface.interface, kwargs=kwargs)
        return acquisition_process, acquisition_state_dict, live_barplot_process


    def create_live_barplot_process(self, num_classes : int, args : list = None) -> tuple[multiprocessing.Process, dict[str, any]]:
        live_barplot_state_dict = init_live_barplot_state_dict(self._manager, num_classes)
        if args is None:
            args = [live_barplot_state_dict]
        else:
            args.append(live_barplot_state_dict)

        live_barplot_process =  multiprocessing.Process(target=barplot, args=args)
        return live_barplot_process, live_barplot_state_dict
