class HPCStatsdb:

    def __init__(self, dbhostname, dbport, dbname, dbuser, dbpassword):
        """ This object is a singleton class, this means only one instance will be created """
        self.database = {
            'dbhostname': dbhostname,
            'dbport':     dbport,
            'dbname':     dbname,
            'dbuser':     dbuser,
            'dbpassword': dbpassword,
        }
        self.cur = False
        self.conn = False

    def infos(self):
        return self.database["dbhostname"], self.database["dbport"], self.database["dbname"],self.database["dbuser"], self.database["dbpassword"]

    def bind(self):
        """ Connection to the database """
        self.conn = psycopg2.connect("host = %(dbhostname)s dbname= %(dbname)s user= %(dbuser)s password= %(dbpassword)s" % self.database)
        self.cur = conn.cursor()
        return self.cur, self.conn


    def unbind(self):
        """ Disconnect from the database """
        self.conn.close()

