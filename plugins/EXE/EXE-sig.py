#!/usr/bin/env python
"""
  Copyright 2012-2013 The MASTIFF Project, All Rights Reserved.

  This software, having been partly or wholly developed and/or
  sponsored by KoreLogic, Inc., is hereby released under the terms
  and conditions set forth in the project's "README.LICENSE" file.
  For a list of all contributors and sponsors, please refer to the
  project's "README.CREDITS" file.
"""

__doc__ = """
PE Digital Signature

Plugin Type: EXE
Purpose:
  This plug-in extracts any digital signatures from a PE executable and converts
  it to both DER and text format.

  Extraction is performed using the disitool.py tool from Didier Stevens. Many
  thanks to him for permission to use it.

  Conversion to text is performed using the openssl program.

  Validation of the signature is not yet done.

Pre-requisites:
   - pefile library (http://code.google.com/p/pefile/)
   - disitool.py (http://blog.didierstevens.com/programs/disitool/)
   - openssl binary (http://www.openssl.org/)

Configuration file:

[Digital Signatures]
# Options to extract the digital signatures
#
# disitool - path to disitool.py script.
# openssl - path to openssl binary
disitool = /usr/local/bin/disitool.py
openssl = /usr/bin/openssl

Output:
   sig.der - DER version of Authenticode signature.
   sig.txt - Text representation of signature.

TODO:
   - Validate the signature.

"""

__version__ = "$Id$"

import logging
import os
import subprocess
import sys
from cStringIO import StringIO

import pefile

# Change the following line to import the category class you for the files
# you wish to perform analysis on
import mastiff.category.exe as exe

class EXESig(exe.EXECat):
    """PE digital signature analysis plugin."""

    def __init__(self):
        """Initialize the plugin."""
        exe.EXECat.__init__(self)

    def activate(self):
        """Activate the plugin."""
        exe.EXECat.activate(self)

    def deactivate(self):
        """Deactivate the plugin."""
        exe.EXECat.deactivate(self)

    def dump_sig_to_text(self, log_dir, openssl):
        """ Convert a DER signature to its text format and writes it out."""

        log = logging.getLogger('Mastiff.Plugins.' + self.name + '.output_sig')
        der_file = log_dir + os.sep + 'sig.der'

        # check to see if file exists
        if os.path.exists(der_file) == False:
            log.error('Cannot find DER file: %s' % der_file)
            return False
        elif openssl is None or os.path.exists(openssl) is False:
            log.error('Cannot open openssl binary: %s' % openssl)
            return False

        cmd = [openssl, 'pkcs7', '-inform',  'DER',  '-print_certs',  '-text', '-in',  der_file]        

        run = subprocess.Popen(cmd,
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, 
                               close_fds=True)
        (output, error) = run.communicate()
        if error is not None and len(error) > 0:
            log.error('Error running openssl: %s' % error)
            return False

        if output is not None:
            with open(log_dir + os.sep + 'sig.txt', 'w') as out_file:
                log.debug('Signature converted to text.')
                out_file.write(output)
                out_file.close()

        return True

    def analyze(self, config, filename):
        """Analyze the file."""

        # sanity check to make sure we can run
        if self.is_activated == False:
            return False
        log = logging.getLogger('Mastiff.Plugins.' + self.name)
        log.info('Starting execution.')

        # get my config options
        sig_opts = config.get_section(self.name)

        # import disitool
        disitool_path = config.get_var(self.name, 'disitool')
        if disitool_path is None:
            log.error('disitool.py path is empty.')
            return False
        elif os.path.exists(disitool_path) == False:
            log.error('disitool.py does not exist: %s' % disitool_path)
            return False

        sys.path.append(os.path.dirname(disitool_path))
        try:
            try: 
                reload(disitool)
            except:
                import disitool
        except ImportError, err:
            log.error('Unable to import disitool: %s' % err)
            return False

        # extract sig
        # turn off stdout bc disitool.ExtractDigitalSignature is noisy
        try:
            old_stdout = sys.stdout
            sys.stdout = StringIO()
            sig = disitool.ExtractDigitalSignature(str(filename), \
                                           config.get_var('Dir','log_dir') + os.sep + 'sig.der')
            sys.stdout = old_stdout
        except pefile.PEFormatError, err:
            log.error('Unable to extract signature: %s' %err)
            return False

        if sig is None:
            log.info("No signature on the file.")
        else:
            log.info("Signature extracted.")
            if sig_opts['openssl'] is None:
                log.error('openssl binary not present. Not converting signature.')
            else:
                # convert the sig to text
                self.dump_sig_to_text(config.get_var('Dir','log_dir'),
                                      config.get_var(self.name, 'openssl'))
        return True

