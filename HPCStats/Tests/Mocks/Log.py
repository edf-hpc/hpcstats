#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011-2018 EDF SA
# Contact:
#       CCN - HPC <dsp-cspit-ccn-hpc@edf.fr>
#       1, Avenue du General de Gaulle
#       92140 Clamart
#
# Authors: CCN - HPC <dsp-cspit-ccn-hpc@edf.fr>
#
# This file is part of HPCStats.
#
# HPCStats is free software: you can redistribute in and/or
# modify it under the terms of the GNU General Public License,
# version 2, as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public
# License along with HPCStats. If not, see
# <http://www.gnu.org/licenses/>.
#
# On Calibre systems, the complete text of the GNU General
# Public License can be found in `/usr/share/common-licenses/GPL'.

import logging

class MockLoggingHandler(logging.Handler):
    """Mock logging handler to check for expected logs. Messages are available
       from an instance's ``messages`` dict, in order, indexed by a lowercase
       log level string (e.g., 'debug', 'info', etc.).
    """

    def __init__(self, *args, **kwargs):

        # Unfortunately logging.Handler is an old-style class so we cannot use
        # modern inheritance super() function. Use old-style parent __init__()
        # then.
        #super(MockLoggingHandler, self).__init__(*args, **kwargs)
        logging.Handler.__init__(self, *args, **kwargs)

        self.messages = {'debug': [],
                         'info': [],
                         'warning': [],
                         'error': [],
                         'critical': []}

    def emit(self, record):
        """Store a message from ``record`` in the instance's ``messages`` dict.
        """
        self.acquire()
        try:
            self.messages[record.levelname.lower()].append(record.getMessage())
        finally:
            self.release()

    def reset(self):
        self.acquire()
        try:
            for message_list in self.messages.values():
                message_list[:] = []
        finally:
            self.release()
