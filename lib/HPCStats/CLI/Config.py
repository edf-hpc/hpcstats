class Config:
    def __init__(self, filename):
        self._filename = filename

    def configurationfile(self):
        print self._filename

