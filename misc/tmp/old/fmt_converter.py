import numpy

def n_ch_convert(n_ch):
    n_ch = n_ch -1
    return n_ch

def eeg_format_convert(data):
    # BrainVision RDA
    data = numpy.transpose(data)
    data = data[0:-1, :]
    return data

def marker_format_convert(data):
    # BrainVision RDA
    converted_data = numpy.empty(0)
    for marker in data:
        idx = marker[0].find('=')
        marker_num = marker[0][idx+2:]
        converted_data = numpy.append(converted_data, int(marker_num))
    converted_data = converted_data.astype(numpy.int64)
    #print(converted_data)
    return converted_data
