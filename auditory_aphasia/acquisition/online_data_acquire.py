import threading
import traceback
from logging import getLogger

import numpy as np
from dareplane_utils.signal_processing.filtering import FilterBank
from dareplane_utils.stream_watcher.lsl_stream_watcher import LSLStreamWatcher
from pylsl.pylsl import LostError
from scipy import signal

from auditory_aphasia.acquisition.epoch_container import EpochContainer

logger = getLogger(__name__)


class OnlineDataAcquire(object):
    def __init__(
        self,
        epoch_container: EpochContainer,
        eeg_sw: LSLStreamWatcher,
        marker_sw: LSLStreamWatcher,
        channels_to_acquire: list[list[int]],  # np.array[list[int]]
        n_eeg_channels: int,
        sample_freq_eeg: float,
        format_convert_eeg_func,
        format_convert_marker_func,
        filter_freq: float | None = None,
        filter_order: int | float | None = None,
        new_trial_markers: int | list[int] | None = None,
        end_markers: int | list[int] | None = None,
    ):

        self.epochs_container = epoch_container
        self.eeg_sw = eeg_sw
        self.eeg_time_correction = 0  # to track the lates correction value
        self.marker_time_correction = 0  # to track the lates correction value

        self.n_eeg_channels = n_eeg_channels
        self.sample_freq_eeg = sample_freq_eeg
        self.marker_sw = marker_sw
        self.filter_freq = filter_freq  # comes from classifier_config, set during init
        self.filter_order = filter_order

        # This will be from a formatting_client.eeg_format_convert,
        # with formatting_client = system_config.FormattingClient()
        self.format_convert_eeg_func = format_convert_eeg_func
        self.format_convert_marker_func = format_convert_marker_func

        self.channels_to_acquire = channels_to_acquire
        if isinstance(type(channels_to_acquire), list):
            self.channels_to_acquire = np.array(self.channels_to_acquire)

        self.new_trial_markers = new_trial_markers
        if isinstance(type(new_trial_markers), int):
            self.new_trial_markers = list(self.new_trial_markers)

        self.end_markers = end_markers
        if isinstance(type(self.end_markers), int):
            self.end_markers = list(self.end_markers)

        self.is_running = False

        self.new_trial_marker = None
        self.got_end_marker = False

        logger.info("Online Data Aquire module was initialized.")

    def start(self):
        logger.info("Online Data Acquire module was started.")
        self.thread = threading.Thread(target=self.main_thread)
        self.is_running = True
        self.thread.start()

    def stop(self):
        logger.info("Online Data Acquire module was stopped.")
        self.is_running = False

    def main_thread(self):

        # fail if these props are not set is ok
        assert self.filter_order is not None
        assert self.filter_freq is not None

        filter_bank = FilterBank(
            bands={"alpha": self.filter_freq},
            order=self.filter_order,
            output="signal",
            n_in_channels=self.eeg_sw.channel_count,
        )

        # ------------------------------------------------------------------------------------------------
        # MD: From here onwards, we can use the stream watcher and the FilterBank
        #     for markers and for EEG data respectively

        # ----------- We have the buffers in the StreamWachter instances already
        # eeg = LSLDataStruct()
        # eeg.data = np.empty((self.n_eeg_channels, 0))
        #
        # marker = LSLDataStruct()
        # marker.data = np.empty((0), dtype=np.int64)

        # Epoch = data_structure.Epoch(n_ch, fs_eeg, MARKERS_TO_EPOCH, EPOCH_RANGE, EPOCH_BASELINE)
        # 'epochs' is passed from parent

        logger.info("start receiving data.")
        try:
            while self.is_running:
                try:
                    self.eeg_sw.update()
                    self.marker_sw.update()
                    self.eeg.time_correction = self.eeg_sw.inlet.time_correction()
                    self.marker.time_correction = self.marker_sw.inlet.time_correction()
                except Exception as e:
                    if isinstance(type(e), LostError):
                        logger.error("Error : \n%s" % (traceback.format_exc()))
                        break

                # only process if a new marker (potentially for epoching arrives)
                if self.marker_sw.n_new > 0:
                    markers = self.marker_sw.unfold_buffer()[-self.marker_sw.n_new :]
                    if any([m in self.new_trial_markers for m in markers]):

                        # MD: Up to here, we could rather use the Dareplane utilities
                        eeg_ts = (
                            self.eeg_sw.unfold_buffer_t()[-self.eeg_sw.n_new :]
                            + self.eeg.time_correction
                        )
                        filter_bank.filter(
                            self.eeg_sw.unfold_buffer()[-self.eeg_sw.n_new :],
                            eeg_ts,
                        )
                        self.eeg_sw.n_new = 0

                        eeg_data = (filter_bank.get_data())[
                            :, :, 0
                        ]  # array (n_samples, n_channels, n_bands)

                        marker_ts = self.marker_sw.unfold_buffer_t()[
                            -self.marker_sw.n_new :
                        ]
                        self.marker_sw.n_new = 0

                        self.epochs_container.update(
                            eeg_data, eeg_ts, markers, marker_ts
                        )

                        if any([em in markers for em in self.end_markers]):
                            self.is_running = False

        except Exception as e:
            logger.error(f"Error : \n {traceback.format_exc()} - {e}")

        logger.info("stop receiving data.")

