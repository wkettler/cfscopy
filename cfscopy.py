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
import shutil
import logging
import traceback
import sys
import time

def trim_slash(d):
    """
    Trim trailing slash.
    """
    return d.rstrip(os.path.sep)

if __name__ == '__main__':
    # Define CLI arguments.
    parser = ArgumentParser(description='CFS directory copy utility.')
    parser.add_argument('--log', dest='log', type=str, default='cfscopy.log',
        help='log file')
    parser.add_argument('--retry', dest='retry', type=int, default=3,
        help='maximum number of retries')
    parser.add_argument('--retry-to', dest='retry_to', type=int, default=10,
        help='time in seconds between each retry')
    parser.add_argument('--src', dest='src', type=str, required=True,
        help='source directory')
    parser.add_argument('--dest', dest='dest', type=str, required=True,
        help='destination directory')
    args = parser.parse_args()
    
    # Load values.
    log = args.log
    retry = args.retry
    retry_to = args.retry_to
    src = trim_slash(args.src)
    dest = trim_slash(args.dest)
    
    # Configure logging
    #logging.config.fileConfig('logging.conf')
    #logger = logging.getLogger()
    FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
    logging.basicConfig(filename='cfscopy.log',level=logging.INFO, format=FORMAT, filemode='w')
    
    
    for root, dirs, files in os.walk(src):
        for d in dirs:
            orig = os.path.join(root, d)
            rel = os.path.relpath(os.path.join(root, d), src)
            new = os.path.join(dest, rel)
            
            logging.info('Creating directory %s' % new)
            
            # Create the directory at the destination.
            r = 0
            while r <= retry:
                try:
                    os.mkdir(new)
                    break
                except Exception, err:
                    logging.error('Attempt %i of %i failed.' % (r, retry))
                    logging.error(traceback.format_exc())
                    if r == retry:
                        logging.error('Maximum attempts succeeded!')
                        sys.exit(1)
                    time.sleep(retry_to)
                finally:
                    r += 1
            
        for f in files:
            orig = os.path.join(root, f)
            rel = os.path.relpath(os.path.join(root, f), src)
            new = os.path.join(dest, rel)
            
            logging.info('Writing %s.' % new)
            
            # Copy the file to the destination.
            r = 0
            while r <= retry:
                try:
                    shutil.copy(orig, new)
                    break
                except Exception, err:
                    logging.error('Attempt %i of %i failed.' % (r, retry))
                    logging.error(traceback.format_exc())
                    if r == retry:
                        logging.error('Maximum attempts succeeded!')
                        sys.exit(1)
                    time.sleep(retry_to)
                finally:
                    r += 1