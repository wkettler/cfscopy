#!/usr/bin/python

"""
power.py

Verify filesystem data integrity during power loss.

Copyright (C) 2013  William Kettler <william.p.kettler@gmail.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the 
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import os
import sys
from time import sleep

def w_srand(f, bs, fsync=False, osync=False):
    """
    Create a new file and fill it with pseudo random data.
    
    Inputs:
        f      (str): File
        bs     (int): Block size in KB
        fsync (bool): fsync after each IO is complete
        osync (bool): Open file with O_SYNC flag
    Outputs:
        NULL
    """
    buf = os.urandom(1024)
    i = 1
    
    if osync:
        print 'Using O_SYNC.'
        fh = os.open(f, os.O_CREAT | os.O_TRUNC | os.O_SYNC | os.O_RDWR)
    else:
        fh = os.open(f, os.O_CREAT | os.O_TRUNC | os.O_RDWR)
        
    if fsync:
        print 'Using fsync.'
    
    try:
        while True:
            os.write(fh, "\n%i\n\n" % i)
            os.write(fh, buf * bs)
            # Force write of fdst to disk.
            if fsync:
                os.fsync(fh)
             
            # Print current block count to screen.
            sys.stdout.write('\r%i' % i)
            sys.stdout.flush()
            i += 1
    except KeyboardInterrupt:
        print ''
        print 'Exiting.'
        os.close(fh)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Verify filesystem data integrity during power loss.')
    parser.add_argument('--fsync', action='store_true',
                       help='fsync after each IO is complete')
    parser.add_argument('--osync', action='store_true',
                       help='Open file with O_SYNC flag')
    args = parser.parse_args()
    
    f = 'power.out'
    w_srand(args.fsync, args.osync)