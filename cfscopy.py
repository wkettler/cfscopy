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
from time import sleep, gmtime, strftime
from lib.emailalerts import emailAlerts

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
    parser.add_argument('--email', dest='email', type=str, default=False,
        help='address to send email alerts')
    parser.add_argument('--src', dest='src', type=str, required=True,
        help='source directory')
    parser.add_argument('--dest', dest='dest', type=str, required=True,
        help='destination directory')
    args = parser.parse_args()
    
    # Load values.
    log = "_".join([strftime("%Y%m%d_%H%M%S", gmtime()), args.log])
    retry = args.retry
    retry_to = args.retry_to
    src = trim_slash(args.src)
    dest = trim_slash(args.dest)
    if args.email:
        email = args.email.split(',')
    else:
        email = args.email
    
    # Configure mailer.
    if email:
        mail = emailAlerts(sender='perf@automation.com', smtp='10.10.10.3', to=email)
    
    # Configure logging
    #logging.config.fileConfig('logging.conf')
    #logger = logging.getLogger()
    FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
    logging.basicConfig(filename=log,level=logging.INFO, format=FORMAT, filemode='w')
    print 'Logging to %s.' % log
    
    
    for root, dirs, files in os.walk(src):
        for d in dirs:
            orig = os.path.join(root, d)
            rel = os.path.relpath(os.path.join(root, d), src)
            new = os.path.join(dest, rel)
            
            logging.info('Creating directory %s' % new)
            
            # Create the directory at the destination.
            r = 1
            while r <= retry:
                try:
                    os.mkdir(new)
                    break
                except Exception, err:
                    logging.error('Attempt %i of %i failed.' % (r, retry))
                    logging.error(traceback.format_exc())
                    if r == retry:
                        logging.error('Maximum attempts succeeded!')
                        if email:
                            mail.send_msg('CFS Copy Exited', 'CFS copy has failed to create %s and has exited with the following exception.\n%s' % (new, traceback.format_exc()))
                        print 'Failed!'
                        sys.exit(1)
                    sleep(retry_to)
                finally:
                    r += 1
            
        for f in files:
            orig = os.path.join(root, f)
            rel = os.path.relpath(os.path.join(root, f), src)
            new = os.path.join(dest, rel)
            
            logging.info('Writing %s.' % new)
            
            # Copy the file to the destination.
            r = 1
            while r <= retry:
                try:
                    shutil.copy(orig, new)
                    break
                except Exception, err:
                    logging.error('Attempt %i of %i failed.' % (r, retry))
                    logging.error(traceback.format_exc())
                    if r == retry:
                        logging.error('Maximum attempts succeeded!')
                        if email:
                            mail.send_msg('CFS Copy Exited', 'CFS copy has failed to write %s and has exited with the following exception.\n%s' % (new, traceback.format_exc()))
                        print 'Failed!'
                        sys.exit(1)
                    sleep(retry_to)
                finally:
                    r += 1
                    
    mail.send_msg('CFS Copy Complete!')