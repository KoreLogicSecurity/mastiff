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
Hex Dump plugin

Plugin Type: Generic
Purpose:
    This plug-in creates a hex view of the file being analyzed.
    
Output:
   hexdump.txt - Contents of the file displayed as hex and ASCII characters.

"""

__version__ = "$Id$"

import os
import logging

# Change the following line to import the category class you for the files
# you wish to perform analysis on
import mastiff.plugins.category.generic as gen

# Change the class name and the base class
class GEN_Hex(gen.GenericCat):
    """Hex Plug-in Code."""

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
        
        # make sure we are enabled
        if config.get_bvar(self.name, 'enabled') is False:
            log.info('Disabled. Exiting.')
            return True
        
        try:
            in_file = open(filename, 'rb')
        except IOError, err:
            log.error('Unable to open file.')
            return False
            
        offset = 0
        in_size = os.stat(filename).st_size
        out_string = ''
        
        while offset < in_size:
            try:
                chars = in_file.read(16)
            except IOError, err:
                log.error('Cannot read data from file: %s' % err)
                in_file.close()
                return False
                
            alpha_string = ''            
            out_string = out_string + '%08x: ' % offset
            
            for byte in chars:
                out_string = out_string + "%02x " % (ord(byte))
                alpha_string = alpha_string + self.is_ascii(byte)
                
            if len(chars) < 16:
                # we are at the end of the file - need to adjust so things line up                
                out_string = out_string + ' '*((16-len(chars))*3)                
            
            # add on the alpha version of the string
            out_string = out_string + ' |' + alpha_string + '|\n'
            offset += len(chars)                
        
        in_file.close()
        
        return self.output_file(config.get_var('Dir','log_dir'), out_string)
        #return True
        
    def is_ascii(self, letter):
        """ Returns the letter if it is a printable ascii character, period otherwise. """
        if 31 < ord(letter) < 127:
            return letter
        return '.'

    def output_file(self, outdir, data):
        """Print output from analysis to a file."""
        log = logging.getLogger('Mastiff.Plugins.' + self.name)
 
        try:            
            outfile = open(outdir + os.sep + 'hexdump.txt', 'w')
            outfile.write(data)
            outfile.close()
        except IOError, err:
            log.error('Could not open resources.txt: %s' % err)
            return False
            
        return True
