#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011-2015 EDF SA
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

"""
    This module is trick to mock builtin open() given in documentation of mock
    library version 0.8.0. It is useless with recent versions of mock library
    since it provides natively this function mock_open().
"""

from mock import inPy3k, MagicMock

if inPy3k:
    file_spec = ['_CHUNK_SIZE', '__enter__', '__eq__', '__exit__',
        '__format__', '__ge__', '__gt__', '__hash__', '__iter__', '__le__',
        '__lt__', '__ne__', '__next__', '__repr__', '__str__',
        '_checkClosed', '_checkReadable', '_checkSeekable',
        '_checkWritable', 'buffer', 'close', 'closed', 'detach',
        'encoding', 'errors', 'fileno', 'flush', 'isatty',
        'line_buffering', 'mode', 'name',
        'newlines', 'peek', 'raw', 'read', 'read1', 'readable',
        'readinto', 'readline', 'readlines', 'seek', 'seekable', 'tell',
        'truncate', 'writable', 'write', 'writelines']
else:
    file_spec = file

def mock_open(mock=None, data=None):

    if mock is None:
        mock = MagicMock(spec=file_spec)

    handle = MagicMock(spec=file_spec)
    handle.write.return_value = None
    if data is None:
        handle.__enter__.return_value = handle
    else:
        handle.__enter__.return_value = data
    mock.return_value = handle
    return mock
