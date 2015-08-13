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
The base category classes for each of the file types analyzed by
mastiff.
"""

__version__ = "$Id$"

from yapsy.IPlugin import IPlugin
import mastiff.plugins.output as output

class MastiffPlugin(IPlugin):
    """The base plugin class every category class should inherit."""

    def __init__(self, name=None):
        """Initialize the Mastiff plugin class."""
        IPlugin.__init__(self)
        self.name = name
        self.prereq = None
        self.yara_filetype = None
        self.page_data = output.page()
        self.page_data.meta['filename'] = 'CHANGEME'

    def activate(self):
        """Power rings activate! Form of Mastiff Plugin!"""
        IPlugin.activate(self)

    def analyze(self, config, filename, output=None):
        pass

    def deactivate(self):
        """Deactivate plugin."""
        IPlugin.deactivate(self)

    def set_name(self, name=None):
        """
           Yapsy does not provide an easy way to get or set our own
           name, so here's a function to do so.
        """
        self.name = name
        return self.name

