#! /usr/bin/env python
#
# cfscopy.py
#
# CFS directory copy utility.
#

__author__  = 'William Kettler <william_kettler@dell.com>'
__created__ = 'January 24, 2013'

import os
import errno
from argparse import ArgumentParser
import logging
import traceback
import sys
from time import sleep, gmtime, strftime
import re

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

if __name__ == '__main__':
    # Define CLI arguments.
    parser = ArgumentParser(description='CFS directory copy utility.')
    parser.add_argument('--retry', dest='retry', type=int, default=3,
        help='maximum number of retries')
    parser.add_argument('--retry-to', dest='retry_to', type=int, default=10,
        help='time in seconds between each retry')
    parser.add_argument('--resume', dest='log', type=str, default=None, metavar='LOG',
        help='resume previous copy')
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
    
    # Configure logging
    #logging.config.fileConfig('logging.conf')
    #logger = logging.getLogger()
    FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
    logging.basicConfig(filename=log,level=logging.INFO, format=FORMAT, filemode='w')
    print 'Logging to %s.' % log
    
    if os.path.normcase(os.path.abspath(src)) == os.path.normcase(os.path.abspath(dst)):
        raise ValueError("`%s` and `%s` are the same directory." % (src, dst))
    
    complete = []
    if resume_log:
        complete.extend(completed(resume_log))
    
    for root, dirs, files in os.walk(src):
        for d in dirs:
            orig = os.path.join(root, d)
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
                except Exception, err:
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
                    cp_sync(orig, new)
                    logging.info('File : %s' % new)
                    break
                except Exception, err:
                    logging.error('Attempt %i of %i failed.' % (r, retry))
                    logging.error(traceback.format_exc())
                    if r == retry:
                        logging.error('Maximum attempts succeeded!')
                        print 'Failed!'
                        sys.exit(1)
                    sleep(retry_to)
                finally:
                    r += 1