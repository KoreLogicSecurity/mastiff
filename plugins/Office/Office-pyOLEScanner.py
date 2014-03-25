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
pyOLEScanner.py Plug-in

Plugin Type: Office
Purpose:
  This plugin runs Giuseppe 'Evilcry' Bonfa's pyOLEScanner.py script.
  pyOLEScanner.py examines an Office document and looks for
  specific instances of malicious code.

Pre-requisites:
   - pyOLEScanner.py must be downloaded. It can be found at:
   https://github.com/Evilcry/PythonScripts/raw/master/pyOLEScanner.zip

Output:
   office-analysis.txt - File containing output from scan.
   deflated_doc/ - If Office document is an Office 2007 or later document,
                   it will be deflated and extracted into this directory.

Configuration Options:
[Office Metadata]
exiftool = Path to exiftool program

NOTE:
- An Error such as "('An Error Occurred:', 'no such table: BWList')" in the
  output file is normal and can be ignored.
- For OfficeX files, an error:

     Starting Deflate Procedure
     An error occurred during deflating

  may occur when the script is unable to unzip the archive.

"""

__version__ = "$Id$"

import subprocess
import logging
import os
import sys

import mastiff.category.office as office

class OfficepyOLEScanner(office.OfficeCat):
    """
       Wrapper for Giuseppe 'Evilcry' Bonfa's pyOLEScanner.py office analysis
       plug-in.
    """

    def __init__(self):
        """Initialize the plugin."""
        office.OfficeCat.__init__(self)

    def analyze(self, config, filename):
        """
        Obtain the command and options from the config file and call the
        external program.
        """
        # make sure we are activated
        if self.is_activated == False:
            return False
        log = logging.getLogger('Mastiff.Plugins.' + self.name)
        log.info('Starting execution.')            

        # get my config options
        plug_opts = config.get_section(self.name)
        if plug_opts is None:
            log.error('Could not get %s options.', self.name)
            return False

        # verify external program exists and we can call it
        if not plug_opts['olecmd'] or \
           not os.path.isfile(plug_opts['olecmd']) or \
           not os.access(plug_opts['olecmd'], os.X_OK):
            log.error('%s is not accessible. Skipping.', plug_opts['olecmd'])
            return False

        # we need to change dir to log_dir as pyOLEScanner.py places files in
        # the directory we run in
        my_dir = os.getcwd()        
        if os.path.isabs(filename) is False:            
            # we need to update the filename to point to the right file
            filename = my_dir + os.sep + filename            
            
        os.chdir(config.get_var('Dir','log_dir'))

        run = subprocess.Popen([sys.executable] + [plug_opts['olecmd']] + \
                               [ filename ],
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               close_fds=True)
        (output, error) = run.communicate()
        if error is not None and len(error) > 0:
            log.error('Error running program: %s' % error)
            os.chdir(my_dir)
            return False

        # ole2.sqlite is created by pyOLEScanner.py, but is not usable to us
        # so lets delete it
        try:
            if os.path.isfile('ole2.sqlite'):
                os.remove('ole2.sqlite')
                log.debug('Deleted ole2.sqlite.')
        except OSError, err:
            log.error('Unable to delete ole2.sqlite: %s', err)            

        # change directories back
        os.chdir(my_dir)

        self.output_file(config.get_var('Dir','log_dir'), output)
        log.debug ('Successfully ran %s.', self.name)

        return True

    def output_file(self, outdir, data):
        """Place the data into a file."""
        log = logging.getLogger('Mastiff.Plugins.' + self.name)

        try:
            out_file = open(outdir + os.sep + "office-analysis.txt",'w')
        except IOError, err:
            log.error('Write error: %s', err)
            return False

        out_file.write(data)
        out_file.close()
        return True

