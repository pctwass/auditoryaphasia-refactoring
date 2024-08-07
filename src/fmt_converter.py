import numpy as np
import logging
logger = logging.getLogger(__name__)

#def n_ch_convert(n_ch):
#    n_ch = n_ch -1
#    return n_ch

def eeg_format_convert(data):
    # BrainVision RDA
    return np.transpose(data)

def marker_format_convert(data):
    # BrainVision RDA
    converted_data = np.empty(0)
    for marker in data:
        idx = marker[0].find('=')
        marker_num = marker[0][idx+2:]
        try:
            converted_data = np.append(converted_data, int(marker_num))
        except:
            return np.array(0)
    converted_data = converted_data.astype(np.int64)
    return converted_data