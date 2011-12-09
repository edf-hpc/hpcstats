#!/usr/bin/python
# -*- coding: utf-8 -*-

class JobImporter:

    def __init__(self, db, conf):
        if ### Slurm
            return JobImporterSlurm(db, conf):
        elif ### Torque
            return JobImporterTorque(db, conf):
        else
            # Throw Exception
