#! /usr/bin/python
#
# emailalerts.py
#
# A class for sending email alerts.
#

__author__  = 'William Kettler <william_kettler@dell.com>'
__created__ = 'August 6, 2012'

import smtplib
from email.mime.text import MIMEText
import logging
import re

logger = logging.getLogger(__name__)

class emailAlerts():
    def __init__(self, **kwargs):
        # Initialize variables.
        self._sender    = None
        self._to        = []
        self._smtp      = None
        
        # Parse kwargs.
        for key in kwargs:
            if key   == 'smtp':
                self.set_smtp(kwargs[key])
            elif key == 'sender':
                self.set_sender(kwargs[key])
            elif key == 'to':
                self.add_to(kwargs[key])
            else:
                error_msg = 'Invalid argument.'
                logger.error(error_msg)
                raise RuntimeError(error_msg)
    
    def _valid_email(self, addr):
        #
        # Verifies email address is valid.
        #
        
        if not re.match(r"[^@]+@[^@]+\.[^@]+", addr):
            error_str = 'Invalid email address: %s' % addr
            logger.error(error_str)
            raise ValueError(error_str)
            
    def set_smtp(self, smtp):
        #
        # Sets the SMTP mail server IP/hostname.
        #
        
        self._smtp = smtp
        
    def get_smtp(self):
        #
        # Returns the SMTP mail server IP/hostname.
        #
        
        return self._smtp
    
    def add_to(self, addrs):
        #
        # Adds email address to the 'To' line.
        #
        
        # Argument must be a list.
        if not type(addrs) == list:
            raise TypeError('Expected list.')
        
        for addr in addrs:
            self._valid_email(addr)   
            self._to.append(addr)
        
    def getTo(self):
        return self._to
        
    def set_sender(self, addr):
        #
        # Sets the senders email address.
        #
        
        self._valid_email(addr)
        self._sender = addr
        
    def get_sender(self):
        #
        # Returns the senders email address.
        #
        
        return self._sender
        
    def send_msg(self, subject, msg):
        #
        # Sends email message.
        #
        
        if not type(subject) == str or not type(msg) == str:
            raise TypeError('Message and subject must be a string.')
        
        # Get parameters.
        smtp   = self.get_smtp()
        to     = self.getTo()
        sender = self.get_sender()

        # Verify all parameters are set.
        error_msg = None
        if not smtp:
            error_msg = 'SMTP server not set.'
        elif not to:
            error_msg = 'Receivers not set.'
        elif not sender:
            error_msg = 'Sender not set.'
        if error_msg:
            logger.error(error_msg)
            raise RuntimeError(error_msg)
            
        msg = MIMEText(msg, 'plain')
        msg['Subject'] = subject
        msg['From'   ] = sender
        msg['To'     ] = ', '.join(to)
        
        try:
            smtpObj = smtplib.SMTP(smtp)
            smtpObj.sendmail(sender, to, msg.as_string())
            logger.info('Successfully sent mail.')
        except Exception as e:
            logger.error('Unable to send email: %s' % e)
            raise e