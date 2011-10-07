

class DbJobs:

    def __init__(self, dbconnexion):
        self.dbconnexion = dbconnexion
    

    def insert(self, jobs):
        """
        Docstring for update
        """

        if not jobs:
            self.debug("> DEBUG : no job found")
        else:
            
            conn = Db(self.conf).supervision_connection()[1]
            cur = conn.cursor()
            for job in jobs:
                print "check", job
                self.debug(">         + insert %s @ %s" % (job.number, job.user))

                if not self.exists_user_of_job(job):
                    print "add user"
                    self.add_user_of_job(job)
                    
                print job.number, job.user, job.group, job.submission_datetime, job.running_datetime, job.end_datetime, job.nb_hosts, job.nb_procs    
                try:
                    job.number = (job.number).split('.')[0]
                    print "user exists"
                except:
                    pass
                    
                cur.execute('INSERT INTO jobs (number, username, groupname, submission_datetime, running_datetime, end_datetime, nb_nodes, nb_cpus) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)', (job.number, job.user, job.group, job.submission_datetime, job.running_datetime, job.end_datetime, job.nb_hosts, job.nb_procs))

            self.debug("> DEBUG : end transactions ")
            conn.commit()
            cur.close()
            self.debug("> DEBUG : close DB ")
            conn.close()
