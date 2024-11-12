from markerbci import buttonbox


class ButtonBoxBciMarkerClient(object):
    def __init__(self, port:str='', marker_duration:float=0.05):
        return
        self.port = port
        self.marker_duration = marker_duration

    def open(self):
        return
        self._buttonbox = buttonbox.ButtonBoxBci(port=self.port)

    def close(self):
        return
        self._buttonbox.close()

    def sendMarker(self, val):
        return
        self._buttonbox.sendMarker(val=val)