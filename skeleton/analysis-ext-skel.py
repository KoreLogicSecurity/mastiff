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
Analysis Plugin using external program code

Plugin Type: Generic
Purpose:
  This file provides the skeleton code for a plugin that performs static
  analysis on any file given to the Mastiff framework using an external
  program. This is an example that shows all functions defined.

Output:
   None.

In the MASTIFF configuration file, the options for this particular plug-in
would be:

[GenSkel Ext Prog]
plugcmd = /path/to/my_prog
"""

__version__ = "$Id$"

import subprocess
import logging
import os

# Change the following line to import the category class you for the files
# you wish to perform analysis on
import mastiff.plugins.category.generic as gen

# Change the class name and the base class
class GenSkelExt(gen.GenericCat):
    """Skeleton generic plugin that calls external program."""

    def __init__(self):
        """Initialize the plugin."""
        gen.GenericCat.__init__(self)
        self.page_data.meta['filename'] = 'CHANGEME'

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

        # *** plug_opts['plugcmd'] SHOULD BE CHANGED TO THE PLUGIN SPECIFIC OPTIONS

        # verify external program exists and we can call it
        if not plug_opts['plugcmd'] or \
           not os.path.isfile(plug_opts['plugcmd']) or \
           not os.access(plug_opts['plugcmd'], os.X_OK):
            log.error('%s is not accessible. Skipping.', plug_opts['plugcmd'])
            return False

        # run your external program here
        run = subprocess.Popen([plug_opts['plugcmd']] + \
                               [ filename ],
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, 
                               close_fds=True)
        (output, error) = run.communicate()
        if error is not None and len(error) > 0:
            log.error('Error running program: %s' % error)
            return False

        self.gen_output(output)
        log.debug ('Successfully ran %s.', self.name)

        return True

    def gen_output(self, output):
        """Place the results into a Mastiff Output Page."""
        log = logging.getLogger('Mastiff.Plugins.' + self.name)

        # self.page_data was previously initialized
        # add a table to it
        new_table = self.page_data.addTable('ANALYSIS PLUGIN DESCRIPTION')

        # parse through data generated from output here
        
        # add header to table
        # example: new_table.addHeader([('Header 1', str), ('Header 2', int)])
        
        # add rows of data to table
        # example: new_table.addRow(['row1', 1])

        return True
