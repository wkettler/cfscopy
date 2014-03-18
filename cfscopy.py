#!/usr/bin/env python

"""
cfscopy.py

Recursive directory copy utility for testing file system corruption.

Copyright (c) 2014  William Kettler <william.p.kettler@gmail.com>

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import os
from argparse import ArgumentParser
import logging
import traceback
import sys
from time import sleep, gmtime, strftime
import re
try:
    import win32file
    import win32con
except ImportError:
    pass


def trim_slash(d):
    """
    Trim trailing slash.
    """
    return d.rstrip(os.path.sep)


def completed(f):
    """
    Parse log for completed directories and files.
    """
    complete = []
    
    with open(f, 'rb') as fh:
        for l in fh:
            if re.search('INFO', l):
                i = l.split(':')[-1].strip()
                complete.append(i)
                
    return complete


def cp_sync(src, dst, bs=16):
    """
    Copy a file from source to destination.
    
    The destination may be a directory.
    
    Arguments:
    src -- source file
    dst -- destination file or directory
    bs -- block size in KB
    """
   
    bs *= 1024
    
    if os.path.isdir(dst):
        dst = os.path.join(dst, os.path.basename(src))

    # Write file and metadata.
    with open(src, 'rb') as fsrc:
        with open(dst, 'wb') as fdst:
            while True:
                buf = fsrc.read(bs)
                if not buf:
                    break
                fdst.write(buf)
            # Force write of fdst to disk.
            fdst.flush()
            os.fsync(fdst.fileno())
            

def cp_win32(src, dst, bs=16):
    """
    Copy a file from source to destination using win32 libraries.
    
    The destination may be a directory.
    
    Arguments:
    src -- source file
    dst -- destination file or directory
    bs -- block size in KB
    """
   
    bs *= 1024
    
    if os.path.isdir(dst):
        dst = os.path.join(dst, os.path.basename(src))
    
    # Open destination file using win32 API
    fdst = win32file.CreateFile(dst, win32file.GENERIC_WRITE, 0, None,
                                win32con.CREATE_ALWAYS,
                                win32file.FILE_FLAG_WRITE_THROUGH, None)

    # Write file and metadata.
    with open(src, 'rb') as fsrc:
        while True:
            buf = fsrc.read(bs)
            if not buf:
                break
            win32file.WriteFile(fdst, buf)
        
    # Flush and close dst
    win32file.FlushFileBuffers(fdst)
    fdst.close()


def main():
    # Define CLI arguments.
    parser = ArgumentParser(description='CFS directory copy utility.')
    parser.add_argument('--retry', dest='retry', type=int, default=3,
                        help='maximum number of retries')
    parser.add_argument('--retry-to', dest='retry_to', type=int, default=10,
                        help='time in seconds between each retry')
    parser.add_argument('--win32', dest='win32', action='store_true',
                        help='use win32 libraries')
    parser.add_argument('--resume', dest='log', type=str, default=None,
                        metavar='LOG', help='resume previous copy')
    parser.add_argument('--src', dest='src', type=str, required=True,
                        help='source directory')
    parser.add_argument('--dst', dest='dst', type=str, required=True,
                        help='destination directory')
    args = parser.parse_args()
    
    # Load values.
    log = "_".join([strftime("%Y%m%d_%H%M%S", gmtime()), 'cfscopy.log'])
    retry = args.retry
    retry_to = args.retry_to
    src = trim_slash(args.src)
    dst = trim_slash(args.dst)
    resume_log = args.log
    win32 = args.win32
    
    # Configure logging
    f = "%(asctime)s - %(levelname)s - %(message)s"
    logging.basicConfig(filename=log, level=logging.INFO, format=f,
                        filemode='w')
    print 'Logging to %s.' % log
    
    # Check if src and dst are the same directory
    if os.path.normcase(os.path.abspath(src)) == \
            os.path.normcase(os.path.abspath(dst)):
        raise ValueError("`%s` and `%s` are the same directory." % (src, dst))
    
    # Define cp function
    if win32:
        cp = lambda src, dst: cp_win32(src, dst)
        logging.info("Using win32 API")
    else:
        cp = lambda src, dst: cp_sync(src, dst)
        
    # Build completed files list if resume log is defined
    complete = []
    if resume_log:
        complete.extend(completed(resume_log))
    
    for root, dirs, files in os.walk(src):
        for d in dirs:
            rel = os.path.relpath(os.path.join(root, d), src)
            new = os.path.join(dst, rel)
                        
            # Create the directory at the destination.
            r = 1
            while r <= retry:
                if new in complete:
                    logging.info('Directory already exists : %s' % new)
                    break
                try:
                    os.mkdir(new)
                    logging.info('Directory : %s' % new)
                    break
                except Exception:
                    logging.error('Attempt %i of %i failed.' % (r, retry))
                    logging.error(traceback.format_exc())
                    if r == retry:
                        logging.error('Maximum attempts succeeded!')
                        print 'Failed!'
                        sys.exit(1)
                    sleep(retry_to)
                finally:
                    r += 1
            
        for f in files:
            orig = os.path.join(root, f)
            rel = os.path.relpath(os.path.join(root, f), src)
            new = os.path.join(dst, rel)
            
            # Copy the file to the destination.
            r = 1
            while r <= retry:
                if new in complete:
                    logging.info('File already exists : %s' % new)
                    break
                try:
                    cp(orig, new)
                    logging.info('File : %s' % new)
                    break
                except Exception:
                    logging.error('Attempt %i of %i failed.' % (r, retry))
                    logging.error(traceback.format_exc())
                    if r == retry:
                        logging.error('Maximum attempts succeeded!')
                        print 'Failed!'
                        sys.exit(1)
                    sleep(retry_to)
                finally:
                    r += 1
                    
    print 'Finished!'
                    

if __name__ == '__main__':
    main()