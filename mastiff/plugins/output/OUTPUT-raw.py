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
Raw Output Plug-In

This output plug-in writes the output in its raw repr() state to a file.
"""

__version__ = "$Id$"

import logging
import mastiff.plugins.output as masOutput

class OUTPUTRaw(masOutput.MastiffOutputPlugin):
    """Raw output plugin.."""

    def __init__(self):
        """Initialize the plugin."""
        masOutput.MastiffOutputPlugin.__init__(self)

    def activate(self):
        """Activate the plugin."""
        masOutput.MastiffOutputPlugin.activate(self)

    def deactivate(self):
        """Deactivate the plugin."""
        masOutput.MastiffOutputPlugin.deactivate(self)

    def output(self, config, output):
        log = logging.getLogger('Mastiff.Plugins.Output.' + self.name)
        if config.get_bvar(self.name, 'enabled') is False:
            log.debug('Disabled. Exiting.')
            return True

        log.info('Writing raw output.')
        try:
            raw_file = open(config.get_var('Dir', 'log_dir')+'/output_raw.txt', 'w')
        except IOError, err:
            log.error('Could not open output_raw.txt file for writing: {}'.format(err))
            return False

        raw_file.write(repr(output))
        raw_file.close()
        return True
