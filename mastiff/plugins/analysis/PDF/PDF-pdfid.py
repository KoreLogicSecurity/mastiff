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

__version__ = "$Id$"

import subprocess
import logging
import os
import sys

import mastiff.plugins.category.pdf as pdf

class PDFid(pdf.PDFCat):
    """Run Didier Stevens pdfid.py"""

    def __init__(self):
        """Initialize the plugin."""
        pdf.PDFCat.__init__(self)
        self.page_data.meta['filename'] = 'pdf-id'

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
            log.error('Error executing pdfid.py: {}'.format(sys.exc_info()[0]))
            return False

        if error is not None and len(error) > 0:
            log.error('Error running program: {}'.format(error))
            return False

        # parse through output
        if 'PDF Header' in output.split('\n')[1]:
            # By default, pdfid.py displays the PDF header as the first. This is different enough from the
            # other data extracted it should be in its own table.
            header_table = self.page_data.addTable(title='PDF Header')
            header_table.addheader([('Name', str), ('Value', str)], printHeader=False)
            header_table.addrow(output.split('\n')[1].lstrip().split(': '))


        # grab the rest of the data
        if 'PDF Header' in output.split('\n')[1]:
            pdf_objects = [ x.lstrip().split() for x in output.split('\n')[2:] ]
        else:
            pdf_objects = [ x.lstrip().split() for x in output.split('\n')[1:] ]

        new_table = self.page_data.addTable(title='PDF Objects')
        new_table.addheader([('Object___Name', str), ('Count', int)])
        [ new_table.addrow([my_obj[0], my_obj[1]]) for my_obj in pdf_objects if my_obj ]

        log.debug ('Successfully ran %s.', self.name)

        return self.page_data


