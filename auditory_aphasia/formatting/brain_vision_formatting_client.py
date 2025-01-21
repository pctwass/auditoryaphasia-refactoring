import numpy as np


class BrainVisionFromattingClient:
    def n_channels_convert(n_channels):
        n_channels = n_channels - 1
        return n_channels

    def eeg_format_convert(self, data):
        # BrainVision RDA
        return np.transpose(data)

    def marker_format_convert(self, data):
        # BrainVision RDA
        converted_data = np.empty(0)
        for marker in data:
            idx = marker[0].find("=")
            marker_num = marker[0][idx + 2 :]
            try:
                converted_data = np.append(converted_data, int(marker_num))
            except Exception as e:
                return np.array(0)

        converted_data = converted_data.astype(np.int64)
        return converted_data

