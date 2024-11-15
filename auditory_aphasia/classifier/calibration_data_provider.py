from scipy import signal
from psychopy import core, gui

class CallibrationDataProvider():
    def __init__(
            self,
            logger,
            n_sessions : int,
            data_dir : str,
            subject_code : str,
            channel_labels_online : list[str],
            file_name_prefix : str,
            filter_freq : float,
            filter_order : int|float,
            markers_to_epoch : list[int],
            tmin : float,
            tmax : float,
            baseline : str = None
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
        import src.common.utils as utils
        import mne
        from scipy import signal
        import numpy as np

        #mne.set_log_level(verbose=False)

        condition = params['condition']
        soa = params['soa']


        self.logger.info("n_sessions : %s" %str(self.n_sessions))

        files_for_calibration = utils.get_files_for_calibration(n_sessions = self.n_sessions,
                                                                data_dir = self.data_dir,
                                                                extension = 'vhdr',
                                                                soa_ms = int(soa*1000),
                                                                condition = condition,
                                                                file_name_prefix = self.file_name_prefix,
                                                                th_soa_ms = 350)

        self.logger.info("files_for_calibration : %s" %str(files_for_calibration))

        myDlg = gui.Dlg(title="Calibration files")
        myDlg.addField("Found the following files for calibration:\n"+'\n'.join([' - '+str(f) for f in files_for_calibration])+'\n\nContinue?')
        ok_data = myDlg.show()  # show dialog and wait for OK or Cancel
        if not myDlg.OK:  # quit if the user pressed cancel
            core.quit()
        # not working because of Psychopy:
        # print("\nFound the following files for calibration:")
        # for f in files_for_calibration:
        #     print(' - '+str(f))
        # while True:
        #     try:
        #         answer = input("Do you want to continue? [y]/n : ")
        #         if answer == "" or answer.lower() == 'y':
        #             break 
        #         elif answer.lower() == 'n':
        #             exit('0')
        #         else:
        #             print('Invalid answer: '+str(answer))
        #     except EOFError:
        #         print('EOF')

        if len(files_for_calibration) == 0:
            self.logger.error("ERROR : data for subject %s was not found." %self.subject_code)
            #print("ERROR : data for subject %s was not found." %subject_code)
        raws = list()
        for file in files_for_calibration:
            raw = mne.io.read_raw(file,
                                preload = True)
                                #eog = eog_channels,
                                #misc = misc_channels)
            sos = signal.butter(self.filter_order, np.array(self.filter_freq)/(raw.info['sfreq']/2), 'bandpass', output='sos')
            raw.apply_function(self.filter_mne, channel_wise=False, sos=sos)
            raws.append(raw)
        print(raws)
        raw = mne.concatenate_raws(raws)
        events, _ = mne.events_from_annotations(raw)

        raw.pick_channels(ch_names = self.channel_labels_online)
        #raw.pick_types(eeg=True)

        return mne.Epochs(raw, events, event_id=self.markers_to_epoch, tmin=self.tmin, tmax=self.tmax, baseline=self.baseline)
    

    def _filter_mne(self, data, sos):
        # filter function which will be handed to mne.io.Raw.apply_function()
        #
        # USE THIS WITH channel_wise = False
        #

        # data has shape of (n_times,) if channel_wise=True and (len(picks), n_times) if False.
        # see details for mne documentation.
        
        r = signal.sosfilt(sos, data, axis=1)
        return r