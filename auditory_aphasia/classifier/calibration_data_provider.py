from logging import Logger

from auditory_aphasia.logging.logger import get_logger

logger = get_logger()

class CalibrationDataProvider:
    def __init__(
        self,
        logger: Logger = logger,
        n_sessions: int = 1,
        data_dir: str = './data',
        subject_code: str = 's1',
        channel_labels_online: list[str] = ['ch1', 'ch2'],
        file_name_prefix: str = 'prefix',
        filter_freq: list[float, float] = [1, 20],
        filter_order: int = 5,
        markers_to_epoch: list[int] = [1, 2],
        tmin: float = -1,
        tmax: float = 3,
        baseline: str = None,
    ):
        self.logger = logger
        self.n_sessions = n_sessions
        self.subject_code = subject_code
        self.channel_labels_online = channel_labels_online
        self.data_dir = data_dir
        self.file_name_prefix = file_name_prefix
        self.filter_freq = filter_freq
        self.filter_order = filter_order
        self.markers_to_epoch = markers_to_epoch
        self.tmin = tmin
        self.tmax = tmax
        self.baseline = baseline

    def get_calibration_data(self, params):
        import mne
        import numpy as np
        import src.common.utils as utils
        from scipy import signal

        # mne.set_log_level(verbose=False)

        condition = params["condition"]
        soa = params["soa"]

        self.logger.info("n_sessions : %s" % str(self.n_sessions))

        files_for_calibration = utils.get_files_for_calibration(
            n_sessions=self.n_sessions,
            data_dir=self.data_dir,
            extension="vhdr",
            soa_ms=int(soa * 1000),
            condition=condition,
            file_name_prefix=self.file_name_prefix,
            th_soa_ms=350,
        )

        self.logger.info("files_for_calibration : %s" % str(files_for_calibration))


        # TODO [ ] -> for now only have a CLI interface / think of a GUI
        #
        q = input("Found the following files for calibration:\n"
             + "\n".join([" - " + str(f) for f in files_for_calibration])
             + "\n\nContinue? [y/n] : ")
        if q != "y":
            raise ValueError("User aborted.")

        # ----------------- Old code
        # myDlg = gui.Dlg(title="Calibration files")
        # myDlg.addField(
        #     "Found the following files for calibration:\n"
        #     + "\n".join([" - " + str(f) for f in files_for_calibration])
        #     + "\n\nContinue?"
        # )
        # if not myDlg.OK:  # quit if the user pressed cancel
        #     core.quit()

        if len(files_for_calibration) == 0:
            self.logger.error(
                "ERROR : data for subject %s was not found." % self.subject_code
            )

        raws = list()
        for file in files_for_calibration:
            raw = mne.io.read_raw(file, preload=True)
            sos = signal.butter(
                self.filter_order,
                np.array(self.filter_freq) / (raw.info["sfreq"] / 2),
                "bandpass",
                output="sos",
            )
            raw.apply_function(self.filter_mne, channel_wise=False, sos=sos)
            raws.append(raw)
        raw = mne.concatenate_raws(raws)
        events, _ = mne.events_from_annotations(raw)

        raw.pick_channels(ch_names=self.channel_labels_online)

        return mne.Epochs(
            raw,
            events,
            event_id=self.markers_to_epoch,
            tmin=self.tmin,
            tmax=self.tmax,
            baseline=self.baseline,
        )
