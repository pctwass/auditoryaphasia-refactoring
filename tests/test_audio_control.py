from auditory_aphasia.audio_stimulation.audio_stimulation_controller import \
    AudioStimulationController


def test_fallback_to_system_audio():
    """
    Check that the default audio system if used if the config an unknown name
    """
    asc = AudioStimulationController(state_dict={})
    asc.system_config.audio_device_name = "UNKNOWN"

    # If the button box is not connected, this will raise an error -> still
    # pass as we are not concerned about this here
    try:
        asc.open()
    except Exception as e:
        if "No USB serial device connected" in str(e):
            pass
        else:
            raise

    pass
