from markerbci import buttonbox


class ButtonBoxBciMarkerClient(object):
    def __init__(self, port:str='', marker_duration:float=0.05):
        self.port = port
        self.marker_duration = marker_duration

    def open(self):
        self._buttonbox = buttonbox.ButtonBoxBci(port=self.port)

    def close(self):
        self._buttonbox.close()

    def sendMarker(self, val):
        self._buttonbox.sendMarker(val=val)