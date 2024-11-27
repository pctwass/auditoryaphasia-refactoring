# Testing online functionality
import logging
import multiprocessing
import threading
import time
from pathlib import Path

import numpy as np
import pylsl
import pytest
from dareplane_utils.logging.logger import get_logger

from auditory_aphasia.acquisition.acquisition_system_controller import \
    AcquisitionSystemController
from auditory_aphasia.config_builder import (build_classifier_config,
                                             build_system_config)
from auditory_aphasia.factories import classification_pipeline_factory
from auditory_aphasia.process_management.process_manager import ProcessManager
from auditory_aphasia.process_management.state_dictionaries import \
    init_acquisition_state_dict

# Overwrite the logger to have a console handler for unit test
logger = get_logger("aphasia_testing", add_console_handler=True)
logger.setLevel(logging.DEBUG)


# system_config.eeg_acquisition_stream_name
# system_config.marker_acquisition_stream_name


def provide_eeg_lsl_stream(
    stop_event: threading.Event, srate: float = 100, nsamples: int = 1000
):

    system_config = build_system_config()

    # block print to stdout to suppress noise
    outlet = pylsl.StreamOutlet(
        pylsl.StreamInfo(
            system_config.eeg_acquisition_stream_name,
            "EEG",
            5,
            srate,
            "float32",
            "test_eeg_data_id",
        )
    )

    data = np.tile(np.linspace(0, 1, nsamples), (5, 1))
    data = data.T * np.arange(1, 6)  # 5 channels with linear increase
    data = data.astype(np.float32)

    isampl = 0
    nsent = 0
    tstart = time.time_ns()
    while not stop_event.is_set():
        dt = time.time_ns() - tstart
        req_samples = int((dt / 1e9) * srate) - nsent
        if req_samples > 0:
            outlet.push_chunk(data[isampl : isampl + req_samples, :].tolist())
            nsent += req_samples
            isampl = (isampl + req_samples) % data.shape[0]  # wrap around

        time.sleep(1 / srate)


def provide_marker_lsl_stream(
    stop_event: threading.Event, srate: float = 100, nsamples: int = 1000
):

    system_config = build_system_config()

    # block print to stdout to suppress noise
    outlet = pylsl.StreamOutlet(
        pylsl.StreamInfo(
            system_config.marker_acquisition_stream_name,
            "EEG",
            1,
            pylsl.IRREGULAR_RATE,
            "int64",
            "test_marker_data_id",
        )
    )

    data = np.tile(np.linspace(0, 1, nsamples), (5, 1))
    data = data.T * np.arange(1, 6)  # 5 channels with linear increase
    data = data.astype(np.float32)

    nsent = 0
    tstart = time.time_ns()
    while not stop_event.is_set():
        dt = time.time_ns() - tstart

        # Send markers every 1 sec for testing
        if dt > 1e9:
            tstart = time.time_ns()
            outlet.push_chunk([1])
            nsent += 1

        time.sleep(1 / srate)


@pytest.fixture(scope="session")  # only create once for all tests
def spawn_lsl_data_stream() -> threading.Event:

    stop_event = threading.Event()
    stop_event.clear()
    th_eeg = threading.Thread(target=provide_eeg_lsl_stream, args=(stop_event,))

    th_eeg.start()

    yield stop_event

    # teardown
    stop_event.set()
    th_eeg.join()


@pytest.fixture(scope="session")  # only create once for all tests
def provide_marker_stream() -> pylsl.StreamOutlet:

    system_config = build_system_config()

    outlet = pylsl.StreamOutlet(
        pylsl.StreamInfo(
            system_config.marker_acquisition_stream_name,
            "MISC",
            1,
            pylsl.IRREGULAR_RATE,
            "int64",
            "test_marker_data_id",
        )
    )

    return outlet


# # should not be on session scope, as tests should work on a new instance
# @pytest.fixture
# def provide_cvep_decoder(
#     provide_joblib_model: Path, provide_config_toml: Path
# ) -> OnlineDecoder:
#
#     online_decoder = online_decoder_factory(provide_config_toml)
#
#     return online_decoder


# @pytest.fixture
# def provide_running_decoder(
#     spawn_lsl_data_stream: threading.Event,
#     provide_cvep_decoder: OnlineDecoder,
#     provide_marker_stream: pylsl.StreamOutlet,
# ) -> tuple[OnlineDecoder, pylsl.StreamOutlet]:
#     cvd = provide_cvep_decoder
#     cvd.selected_channels = None  # select all channels for this use case
#     outlet = provide_marker_stream
#
#     cvd.init_all()
#     cvd.eval_after_s = 0.1
#
#     thread, stop_ev = cvd.run()
#
#     yield cvd, outlet
#
#     stop_ev.set()
#     thread.join()


def test_acquisition_controller_initiation(
    provide_marker_stream, spawn_lsl_data_stream
):
    marker_outlet = provide_marker_stream

    manager = multiprocessing.Manager()

    pm = ProcessManager()
    kwargs_live_barplot = dict()
    num_classes = 6

    live_barplot_process, live_barplot_state_dict = pm.create_live_barplot_process(
        num_classes, kwargs_live_barplot
    )

    state_dict = init_acquisition_state_dict(manager)

    classifier_config = build_classifier_config()
    system_config = build_system_config()

    classifier = classification_pipeline_factory(
        pipeline_name=classifier_config.classification_pipeline_name,
        n_channels=5,
    )

    # The __init__ is trying to connect the stream watches for eeg and markers
    #

    # system_config.eeg_acquisition_stream_name
    # system_config.marker_acquisition_stream_name

    acquisition_sys_controller = AcquisitionSystemController(
        state_dict=state_dict,
        live_barplot_state_dict=live_barplot_state_dict,
        clf=classifier,
        markers=system_config.markers,
        tmin=classifier_config.tmin,
        tmax=classifier_config.tmax,
        baseline=classifier_config.baseline,
        filter_freq=classifier_config.filter_freq,
        filter_order=classifier_config.filter_order,
        ivals=classifier_config.ivals,
        n_class=classifier_config.n_class,
        adaptation=classifier_config.adaptation,
        dynamic_stopping=classifier_config.dynamic_stopping,
        dynamic_stopping_params=classifier_config.dynamic_stopping_params,
        max_n_stims=classifier_config.n_stimulus,
    )
    assert acquisition_sys_controller is not None
