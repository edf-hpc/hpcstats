class HPCStatsdb:

    def __init__(self, hostname, port, dbname, dbuser, dbpass):
        self._hostname = hostname
        self._port = port
        self._dbname = dbname
        self._dbuser = dbuser
        self._dbpass = dbpass

    def infos(self):
        return self._hostname, self._port, self._dbname, self._dbuser, self._dbpass
