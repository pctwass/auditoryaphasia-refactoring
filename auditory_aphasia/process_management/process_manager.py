import multiprocessing
import multiprocessing.process

from auditory_aphasia.acquisition.acquisition_interface import \
    run_acquisition_interface
from auditory_aphasia.audio_stimulation.audio_stimulation_interface import \
    run_audio_interface
from auditory_aphasia.barplot import run_barplot
from auditory_aphasia.process_management.state_dictionaries import (
    init_acquisition_state_dict, init_audio_state_dict,
    init_live_barplot_state_dict, init_visual_fb_state_dict)
from auditory_aphasia.visual_feedback.visual_feedback_interface import \
    run_visual_interface


class ProcessManager:
    def __init__(self) -> None:
        self._manager = multiprocessing.Manager()

    def create_audio_stim_process(
        self, kwargs: dict[str, any] = None
    ) -> tuple[multiprocessing.Process, dict[str, any]]:
        audio_stim_state_dict = init_audio_state_dict(self._manager)

        if kwargs is None:
            kwargs = dict(state_dict=audio_stim_state_dict)
        else:
            kwargs["state_dict"] = audio_stim_state_dict

        audio_process = multiprocessing.Process(
            target=run_audio_interface, kwargs=kwargs
        )
        return audio_process, audio_stim_state_dict

    def create_visual_fb_process(
        self, kwargs: dict[str, any] = None
    ) -> tuple[multiprocessing.Process, dict[str, any]]:
        visual_fb_state_dict = init_visual_fb_state_dict(self._manager)

        if kwargs is None:
            audio_state_dict = init_audio_state_dict(
                self._manager
            )  # the audio state dict was undefined before!
            kwargs = dict(state_dict=audio_state_dict)
        else:
            kwargs["state_dict"] = visual_fb_state_dict

        visual_fb_process = multiprocessing.Process(
            target=run_visual_interface, kwargs=kwargs
        )
        return visual_fb_process, visual_fb_state_dict

    def create_acquisition_process(
        self,
        num_classes: int,
        kwargs: dict[str, any] = None,
        kwargs_live_barplot: dict[str, any] = None,
    ) -> tuple[multiprocessing.Process, dict[str, any]]:
        live_barplot_process, live_barplot_state_dict = (
            self.create_live_barplot_process(num_classes, kwargs_live_barplot)
        )

        acquisition_state_dict = init_acquisition_state_dict(self._manager)
        if kwargs is None:
            kwargs = dict(
                state_dict=acquisition_state_dict,
                live_barplot_state_dict=live_barplot_state_dict,
            )
        else:
            kwargs["state_dict"] = acquisition_state_dict
            kwargs["live_barplot_state_dict"] = live_barplot_state_dict

        acquisition_process = multiprocessing.Process(
            target=run_acquisition_interface, kwargs=kwargs
        )
        return (
            acquisition_process,
            acquisition_state_dict,
        )

    def create_live_barplot_process(
        self, num_classes: int, kwargs_live_barplot: dict[str, any] = None
    ) -> tuple[multiprocessing.Process, dict[str, any]]:
        state_dict = init_live_barplot_state_dict(self._manager, num_classes)

        if kwargs_live_barplot is None:
            kwargs_live_barplot = dict(state_dict=state_dict)
        else:
            kwargs_live_barplot["state_dict"] = state_dict

        live_barplot_process = multiprocessing.Process(
            target=run_barplot, kwargs=kwargs_live_barplot
        )
        return live_barplot_process, state_dict
