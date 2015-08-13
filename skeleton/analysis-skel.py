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
Analysis plugin skeleton code

Plugin Type: Generic
Purpose:
  This file provides the skeleton code for a plugin that performs static
  analysis on any file given to the Mastiff framework. This is an example that
  shows all functions defined.

Output:
   None

__init__(): MANDATORY: Any initialization code the plugin requires. It must
            also call the __init__ for its category class.

activate(): OPTIONAL: Activation code called by Yapsy to activate the plugin.

deactivate(): OPTIONAL: Deactivated code called by Yapsy.

analyze(config, filename): MANDATORY: The main body of code that performs the
                           analysis on the file.

gen_output(outdir): Function that puts the data into self.page_data for the output
                             plug-ins.
"""

__version__ = "$Id$"

import logging

# Change the following line to import the category class you for the files
# you wish to perform analysis on
import mastiff.plugins.category.generic as gen

# Change the class name and the base class
class GenSkeleton(gen.GenericCat):
    """Skeleton generic plugin code."""

    def __init__(self):
        """Initialize the plugin."""
        gen.GenericCat.__init__(self)
        self.page_data.meta['filename'] = 'CHANGEME'

    def activate(self):
        """Activate the plugin."""
        gen.GenericCat.activate(self)

    def deactivate(self):
        """Deactivate the plugin."""
        gen.GenericCat.deactivate(self)

    def analyze(self, config, filename):
        """Analyze the file."""

        # sanity check to make sure we can run
        if self.is_activated == False:
            return False
        log = logging.getLogger('Mastiff.Plugins.' + self.name)
        log.info('Starting execution.')

        # Add analysis code here. Data can be added to tables or passed into gen_output

        self.gen_output()
        
        return self.page_data

    def gen_output(self):
        """Place the results into a Mastiff Output Page."""
        log = logging.getLogger('Mastiff.Plugins.' + self.name)

        # self.page_data was previously initialized
        # add a table to it
        new_table = self.page_data.addTable('ANALYSIS PLUGIN DESCRIPTION')

        # add header to table
        # example: new_table.addHeader([('Header 1', str), ('Header 2', int)])
        
        # add rows of data to table
        # example: new_table.addRow(['row1', 1])

        return True

