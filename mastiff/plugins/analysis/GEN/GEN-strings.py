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
Embedded Strings Extraction Plugin

Plugin Type: Generic
Purpose:
  Execute the 'strings' program and obtain embedded ASCII and UNICODE
  strings within the given filename.  These will be returned in a
  dictionary where the key is the decimal offset of the string
  within the file and the value is a list of string type (U or A)
  and the string itself.

Configuration Options:

  strcmd = Path to the strings binary

  DO NOT CHANGE THE FOLLOWING OPTIONS UNLESS YOU KNOW WHAT YOU ARE DOING.
  str_opts = Options to send to strings every time its called.
                   This should be set to "-a -t d" (without quotes).
  str_uni = Options to send to strings to obtain UNICODE strings.
                 This should be set to "-e l" (without quotes).

Output:
   Output will be put into a file given a directory and the strings
   dictionary.
"""

__version__ = "$Id$"

import subprocess
import re
import logging
import os

import mastiff.plugins.category.generic as gen

class GenStrings(gen.GenericCat):
    """Extract embedded strings."""

    def __init__(self):
        """Initialize the plugin."""
        gen.GenericCat.__init__(self)
        self.strings = {}
        self.page_data.meta['filename'] = 'strings'
        self.prereq = 'File Information'

    def _insert_strings(self, output, str_type):
        """Insert output from strings command into self.strings list."""

        for line in output.split('\n'):
            m = re.match('\s*([0-9]+)\s+(.*)', line)
            if m is not None and m.group(2):
                self.strings[int(m.group(1))] = [str_type, m.group(2)]

    def analyze(self, config, filename):
        """
        Run the strings command on the given filename and extract ASCII
        and UNICODE strings. The formatted output is stored in self.strings.
        """
        # make sure we are activated
        if self.is_activated == False:
            return None

        log = logging.getLogger('Mastiff.Plugins.' + self.name)
        log.info('Starting execution.')

        # get my config options
        str_opts = config.get_section(self.name)

        if not str_opts['strcmd'] or \
           not os.path.isfile(str_opts['strcmd']) or \
           not os.access(str_opts['strcmd'], os.X_OK):
            log.error('%s is not accessible. Skipping.')
            return None

        if not str_opts['str_opts'] or not str_opts['str_uni_opts']:
            log.error('Strings options do not exist. Please check config. Exiting.')
            return None

        # obtain ASCII strings
        run = subprocess.Popen([str_opts['strcmd']] + \
                               str_opts['str_opts'].split() + [ filename ],
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               close_fds=True)
        (output, error) = run.communicate()
        if error is not None and len(error) > 0:
            log.error('Error running program: %s' % error)
            return False

        self._insert_strings(output,'A')

        # obtain Unicode strings
        run = subprocess.Popen([str_opts['strcmd']] +
                               str_opts['str_opts'].split() + str_opts['str_uni_opts'].split() + [ filename ],
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               close_fds=True)
        (output, error) = run.communicate()
        if error is not None and len(error) > 0:
            log.error('Error running program: %s' % error)
            return False

        self._insert_strings(output,'U')

        #self.gen_output(config.get_var('Dir','log_dir'))
        self.gen_output()
        log.debug ('Successfully grabbed strings.')

        return self.page_data

    def gen_output(self):
        """Place the results into a Mastiff Output Page."""
        log = logging.getLogger('Mastiff.Plugins.' + self.name)

        # self.page_data was previously initialized
        # add a table to it
        str_table = self.page_data.addTable('Embedded Strings')

        if len(self.strings) == 0:
            log.warn("No embedded strings detected.")
            str_table.addheader([('Message', str)], printHeader=False)
            str_table.addrow(['No embedded strings detected.' ])
            return True

        str_table.addheader([('Offset', str), ('Type', str), ('String', str)])
        for k in sorted(self.strings.iterkeys()):
            str_table.addrow([ '{:0x}'.format(k), self.strings[k][0], self.strings[k][1] ])

        return True

