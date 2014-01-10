#!/usr/bin/env python
"""
  Copyright 2012-2013 The MASTIFF Project, All Rights Reserved.

  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.
"""

"""
pdfid.py Plug-in

Plugin Type: PDF
Purpose:
  Run Didier Stevens' pdfid.py script against a PDF and place the results into
  a file.

Output:
   pdfid.txt - Output of pdfid.py.

Requirements:
   The pdfid.py script must be installed.

Configuration Options:

   [pdfid]
   pdfid_cmd - Path to the pdfid.py script. Must be executable.
   pdfid_opts - Options to give to the script. Can be empty.

"""

__version__ = "$Id: PDF-pdfid.py,v 1.10 2013/02/11 19:55:23 thudak Exp $"

import subprocess
import logging
import os

import mastiff.category.pdf as pdf

class PDFid(pdf.PDFCat):
    """Run Didier Stevens pdfid.py"""

    def __init__(self):
        """Initialize the plugin."""
        pdf.PDFCat.__init__(self)

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
            log.error('Could not get %s options.',  self.name)
            return False

        # verify external program exists and we can call it
        if not plug_opts['pdfid_cmd'] or \
           not os.path.isfile(plug_opts['pdfid_cmd']) or \
           not os.access(plug_opts['pdfid_cmd'], os.X_OK):
            log.error('%s is not accessible. Skipping.',  plug_opts['pdfid_cmd'])
            return False
        elif len(plug_opts['pdfid_cmd']) == 0:
            log.debug('Plug-in disabled.')
            return False

        # options cannot be empty - at least have a blank option
        if 'pdfid_opts' not in plug_opts:
            plug_opts['pdfid_opts'] = ''
        elif len(plug_opts['pdfid_opts']) == 0:
            plug_opts['pdfid_opts'] = ''
        else:
            plug_opts['pdfid_opts'] = plug_opts['pdfid_opts'].split()

        # run pdfid.py here
        try:
            run = subprocess.Popen([plug_opts['pdfid_cmd']] + \
                               list(plug_opts['pdfid_opts']) + \
                               [ filename ],
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               close_fds=True)
            (output, error) = run.communicate()
        except:
            log.error('got error')
            return False
        if error is not None and len(error) > 0:
            log.error('Error running program: %s' % error)
            return False

        self.output_file(config.get_var('Dir','log_dir'), output)
        log.debug ('Successfully ran %s.', self.name)

        return True

    def output_file(self, outdir, data):
        """Place the data into a file."""
        log = logging.getLogger('Mastiff.Plugins.' + self.name)

        try:
            out_file = open(outdir + os.sep + "pdfid.txt",'w')
        except IOError, err:
            log.error('Write error: %s', err)
            return False

        out_file.write(data)
        out_file.close()
        return True

