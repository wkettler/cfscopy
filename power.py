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
        fh = open(f, 'wb', os.O_SYNC)
    else:
        fh = open(f, 'wb')
        
    if fsync:
        print 'Using fsync.'
    
    while True:
        fh.write("\n%i\n\n" % i)
        fh.write(buf * bs)
        # Force write of fdst to disk.
        if fsync:
            fh.flush()
            os.fsync(fh.fileno())
         
        # Print current block count to screen.
        sys.stdout.write('\r%i' % i)
        sys.stdout.flush()
        i += 1
        
            
def main(fsync, osync):
    """
        Write infinite amount of data to a file using O_SYNC and fsync.
        
        Inputs:
            fsync (bool): fsync after each IO is complete
            osync (bool): Open file with O_SYNC flag
        Outputs:
            NULL
    """
    f = "power.out"
    
    w_srand(f, 1, fsync=fsync, osync=osync)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Verify filesystem data integrity during power loss.')
    parser.add_argument('--fsync', action='store_true',
                       help='fsync after each IO is complete')
    parser.add_argument('--osync', action='store_true',
                       help='Open file with O_SYNC flag')
    args = parser.parse_args()
    
    main(args.fsync, args.osync)