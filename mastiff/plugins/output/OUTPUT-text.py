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
Text Output Plug-In

This output plug-in writes the output to a text file.
"""

__version__ = "$Id$"

import logging
import mastiff.plugins.output as masOutput

def renderText(format, logdir, filename, datastring):

    log = logging.getLogger('Mastiff.Plugins.Output.OUTPUTtext.renderText')
    # print out the formatted text for the plug-in
    if format == 'single':
        # all data is on one page, open up one file for it
        out_filename = logdir + '/output_txt.txt'
        mode = 'a'
        # add a separater between plug-in output
        datastring += '*'*80 + '\n'
    elif format == 'multiple':
        # data should be broken up into individual files.
        # this will be set for each file
        out_filename = logdir + '/' + filename + '.txt'
        mode = 'w'
    else:
        log.error('Invalid format type for output plugin: {}'.format(format))
        return False

    try:
        txt_file = open(out_filename, mode)
    except IOError, err:
        log.error('Could not open {} file for writing: {}'.format(out_filename, err))
        return False

    txt_file.write(datastring)
    txt_file.close()

def processPage(plugin, page, format):
    txtstr = ''
    if format == 'single':
        txtstr += '\n{} Plug-in Results\n\n'.format(plugin)

    # loop through each table in the page
    for tabledata in sorted(page, key=lambda page: page[2]):
        (title, mytable, index) = tabledata

        # first we need to go through the table and find the max length for each column
        col_widths = [ len(getattr(col_name, 'name')) for col_name in mytable.header ]

        for row in mytable:
            # set a maximum length of each column to 60 characters
            col_widths = map(max, zip(col_widths, [ min(60, len(str(col))) for col in row[1:]]))
            #print col_widths

        # format the header
        if mytable.printHeader is not False:
            txtstr +=  "  ".join((getattr(val, 'name')).ljust(length) for val,  length in zip(mytable.header, col_widths)) + '\n'
            txtstr += '  '.join([ '-'*val for val in col_widths ]) + '\n'

        # format the data
        for row in mytable:
            txtstr += "  ".join(str(val).ljust(length) for val, length in zip(row[1:], col_widths) ) + '\n'

        txtstr += '\n'

    return txtstr

class OUTPUTtext(masOutput.MastiffOutputPlugin):
    """Text output plugin.."""

    def __init__(self):
        """Initialize the plugin."""
        masOutput.MastiffOutputPlugin.__init__(self)

    def activate(self):
        """Activate the plugin."""
        masOutput.MastiffOutputPlugin.activate(self)

    def deactivate(self):
        """Deactivate the plugin."""
        masOutput.MastiffOutputPlugin.deactivate(self)

    def output(self, config, data):
        log = logging.getLogger('Mastiff.Plugins.Output.' + self.name)
        if config.get_bvar(self.name, 'enabled') is False:
            log.debug('Disabled. Exiting.')
            return True

        log.info('Writing text output.')

        txtstr = ''
        format = config.get_var(self.name, 'format')

        # we need to output the File Information plugin first as it contains the
        # summary information on the analyzed file
        try:
            log.debug('Writing file information.')
            txtstr += processPage('File Information', data[data.keys()[0]]['Generic']['File Information'], format)
            renderText(format, config.get_var('Dir', 'log_dir'), data[data.keys()[0]]['Generic']['File Information'].meta['filename'], txtstr)
            txtstr = ''
        except KeyError, err:
            log.error('File Information plug-in data missing. Aborting.')
            return False

        # loop through category data
        for cats, catdata in data[data.keys()[0]].iteritems():
            if format == 'single':
                catstr = '{} Category Analysis Results'.format(cats)
                log.debug('Writing {} results.'.format(cats))
                txtstr += '{}\n'.format(catstr) + '-'*len(catstr) + '\n'

            # loop through plugin data and generate the output text
            for plugin, pages in catdata.iteritems():
                if cats == 'Generic' and plugin == 'File Information':
                    continue

                # process the page into its output string
                txtstr += processPage(plugin, pages, format)

                # render the text into the appropriate location
                renderText(format, config.get_var('Dir', 'log_dir'), pages.meta['filename'], txtstr)
                txtstr = ''

        return True
