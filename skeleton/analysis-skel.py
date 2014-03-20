#!/usr/bin/env python
"""
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

output_file(outdir, data): MANDATORY: Function that puts the data received into
                           a given directory.
"""

__version__ = "$Id$"

import logging

# Change the following line to import the category class you for the files
# you wish to perform analysis on
import mastiff.category.generic as gen

# Change the class name and the base class
class GenSkeleton(gen.GenericCat):
    """Skeleton generic plugin code."""

    def __init__(self):
        """Initialize the plugin."""
        gen.GenericCat.__init__(self)

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

        # Add analysis code here. data var below would be changed.

        data = "\"Generic Plugin Example Skeleton data from %s\"" % filename
        self.output_file(config.get_var('Dir','log_dir'), data)
        return True

    def output_file(self, outdir, data):
        """Print output from analysis to a file."""

        # Code to log to file goes here

        return True

