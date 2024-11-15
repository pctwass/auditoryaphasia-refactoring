# This is a template for the callibration data provider
class CallibrationDataProviderTemplate():
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
        pass


    def get_calibration_data(self, params):
        pass
    

    def _filter_mne(self, data, sos):
        pass