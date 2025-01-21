from auditory_aphasia.process_management.process_manager import ProcessManager


def test_init_process_manager():
    pm = ProcessManager()


def test_creating_audio_stim_process():
    pm = ProcessManager()
    audio_stim_process, audio_stim_state_dict = pm.create_audio_stim_process()
    audio_stim_process.start()
    try:
        assert audio_stim_process.is_alive() is True 
    finally:
        audio_stim_process.terminate()


def test_creating_visual_fb_process():
    pm = ProcessManager()
    visual_fb_process, visual_fb_state_dict = pm.create_visual_fb_process()
    visual_fb_process.start()
    try:
        assert visual_fb_process.is_alive() is True
    finally:
        visual_fb_process.terminate()


def test_creating_acquisition_process():
    pm = ProcessManager()
    num_classes = 2
    acquisition_process, acquisition_state_dict = pm.create_acquisition_process(num_classes)
    acquisition_process.start()
    try:
        assert acquisition_process.is_alive() is True
    finally:
        acquisition_process.terminate()


def test_creating_live_barplot_process():
    pm = ProcessManager()
    num_classes = 2
    live_barplot_process, live_barplot_state_dict = pm.create_live_barplot_process(num_classes)
    live_barplot_process.start()
    try:
        assert live_barplot_process.is_alive() is True
    finally:
        live_barplot_process.terminate()
