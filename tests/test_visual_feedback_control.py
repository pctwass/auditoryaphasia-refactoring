# NOTE: these tests take about ~11s, 10s of which are for loading psychopy
import multiprocessing
import time

from auditory_aphasia.visual_feedback.visual_feedback_controller import \
    VisualFeedbackController
from auditory_aphasia.visual_feedback.visual_feedback_interface import \
    run_visual_interface


def test_visual_controller_init():
    asc = VisualFeedbackController()
    pass


def test_spawning_visual_fb_in_multiprocessing():
    kwargs = dict(
        name= 'test1',
        name_main_outlet = "main",
        state_dict= None             # how  can this be a string>>>???
    )

    visual_fb_process = multiprocessing.Process(
        target=run_visual_interface, kwargs=kwargs
    )
    visual_fb_process.start()
    time.sleep(1)

    try:
        assert visual_fb_process.is_alive() is True
    finally:
        visual_fb_process.terminate()
