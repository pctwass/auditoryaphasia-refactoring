import pyaudio
import pyscab

from auditory_aphasia.audio_stimulation.pyscab_stimulation_controller import \
    PyscabStimulationController
from auditory_aphasia.clients.marker.button_box_bci_marker_client import \
    ButtonBoxBciMarkerClient as MarkerClient
from auditory_aphasia.config_builder import build_system_config
from auditory_aphasia.logging.logger import get_logger
from auditory_aphasia.process_management.process_communication_enums import \
    AudioStatus

logger = get_logger()


class AudioStimulationController(object):

    def __init__(self, state_dict):
        self.state_dict = state_dict
        self.marker = None
        self.audio_device_interface = None
        self.psycab_stim_controller = None
        self.system_config = build_system_config()

    def open(self):

        try:
            self.audio_device_interface = pyscab.AudioInterface(
                device_name=self.system_config.audio_device_name,
                n_ch=self.system_config.n_channels,
                format=self.system_config.format,
                frames_per_buffer=self.system_config.frames_per_buffer,
            )
        except KeyError as e:
            if self.system_config.audio_device_name not in str(e):
                raise
            else:
                # grab available devices
                device_name = (
                    pyaudio.PyAudio().get_default_output_device_info().get("name")
                )
                logger.info(
                    f"Could not find audio device with name {self.system_config.audio_device_name}, trying default device {device_name=}"
                )
                # try opening with default audio
                # https://pyscab.readthedocs.io/en/latest/_modules/pyscab/HardwareController.html#CallbackParams

                self.audio_device_interface = pyscab.AudioInterface(
                    device_name=device_name,
                    n_ch=self.system_config.n_channels,
                    format=self.system_config.format,
                    frames_per_buffer=self.system_config.frames_per_buffer,
                )

        self.marker = MarkerClient()
        self.marker.open()

        self.psycab_stim_controller = PyscabStimulationController(
            self.audio_device_interface,
            marker_send=self.marker.sendMarker,
            correct_latency=self.system_config.correct_sw_latency,
            correct_hardware_buffer=self.system_config.correct_hw_latency,
            state_dict=self.state_dict,
        )
        self.psycab_stim_controller.open()

        logger.info("Audio Device was opened")

    def close(self):
        self.psycab_stim_controller.close()
        self.audio_device_interface.terminate()

        logger.info("Audio Hardware Controller terminated.")

        if self.marker is not None:
            self.marker.close()  # close marker device

    def play(self, params: dict[str, any]):
        # self.p = Process(target=self.play_parallel, args=(params,self.state_dict, log_file, log_stdout))
        # self.p.start()

        # conf.set_logger(file=log_file, stdout=log_stdout)

        audio_infos = params["audio_info"]
        play_plan = params["play_plan"]

        audio_files = pyscab.DataHandler()
        for audio_info in audio_infos:
            audio_files.load(audio_info[0], audio_info[1], volume=audio_info[2])

        logger.debug("Stimulation Controller Opened and Start playing.")
        self.psycab_stim_controller.play(
            play_plan, audio_files, time_termination="auto", pause=0
        )

        # time.sleep(1) # for closing marker device properly, just in case.
        # logger.info("Marker Device closed")
        # logger.info("------------------------ Run ended ------------------------")
        self.state_dict["audio_status"] = AudioStatus.TERMINATED
        logger.debug("changed audio status to TERMINATED")
