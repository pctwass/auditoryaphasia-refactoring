import multiprocessing
import multiprocessing.process
from src.process_management.state_dictionaries import *

import src.utils as utils
import src.audio.AudioController as AudioController
import src.visual_feedback.VisualFeedbackInterface as VisualFeedbackInterface
import src.acquisition.AcquisitionSystemController as AcquisitionSystemController


class ProcessManager:
    def __init__(self) -> None:
        self._manager = multiprocessing.Manager()

    
    def create_subprocess(self, target, args : list = None) -> multiprocessing.process:
        return multiprocessing.Process(target=target, args=args)


    def create_audio_process(self, args : list = None) -> tuple[multiprocessing.process, dict[str, any]]:
        command_array = self._manager.list()
        audio_state_dict = init_audio_state_dict(self._manager)
        if args is None:
            args = [audio_state_dict]
        args.append(audio_state_dict)

        audio_process = multiprocessing.Process(target=AudioController.interface, args=args)
        return audio_process, audio_state_dict


    def create_visual_fb_process(self, args : list = None) -> tuple[multiprocessing.process, dict[str, any]]:
        visual_fb_state_dict = init_visual_fb_state_dict(self._manager)
        if args is None:
            args = [visual_fb_state_dict]
        args.append(visual_fb_state_dict)

        visual_fb_process = multiprocessing.Process(target=VisualFeedbackInterface.interface, args=args)
        return visual_fb_process, visual_fb_state_dict


    def create_acquisition_process(self, args : list = None) -> tuple[multiprocessing.process, dict[str, any]]:
        acquisition_state_dict = init_acquisition_state_dict(self._manager)
        if args is None:
            args = [acquisition_state_dict]
        args.append(acquisition_state_dict)

        acquisition_process =  multiprocessing.Process(target=AcquisitionSystemController.interface, args=args)
        return acquisition_process, acquisition_state_dict


    def create_live_barplot_process(self, num_classes, args : list = None) -> tuple[multiprocessing.process, dict[str, any]]:
        live_barplot_state_dict = init_live_barplot_state_dict(self._manager, num_classes)
        if args is None:
            args = [live_barplot_state_dict]
        args.append(live_barplot_state_dict)

        live_barplot_process =  multiprocessing.Process(target=utils.barplot.interface, args=args)
        return live_barplot_process, live_barplot_state_dict
