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

def renderText(page_format, logdir, filename, datastring):
    """ Places the datastring previously created into the appropriate file or files. """

    log = logging.getLogger('Mastiff.Plugins.Output.OUTPUTtext.renderText')
    # print out the formatted text for the plug-in
    if page_format == 'single':
        # all data is on one page, open up one file for it
        out_filename = logdir + '/output_txt.txt'
        mode = 'a'
        # add a separater between plug-in output
        datastring += '*'*80 + '\n'
    elif page_format == 'multiple':
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

    txt_file.write(datastring.encode('utf-8', 'replace'))
    txt_file.close()

def _extend(data, length=0):
    """ Returns a unicode string that is left justified by the length given. """
    if data is None:
        return u""

    try:
        outstr = data.ljust(length)
    except AttributeError:
        outstr = str(data).ljust(length)
    except UnicodeEncodeError:        
        outstr = data.decode('utf-8').ljust(length)

    if isinstance(outstr, unicode):
        return outstr
    else:
        return unicode(outstr, 'utf-8', 'replace')

def processPage(plugin, page, page_format):
    """ Processes a page of data and puts it into the correct format. """

    txtstr = unicode('', 'utf-8')
    if page_format == 'single':
        txtstr += '\n{} Plug-in Results\n\n'.format(plugin)

    # loop through each table in the page
    for tabledata in sorted(page, key=lambda page: page[2]):
        (title, mytable, index) = tabledata

        # first we need to go through the table and find the max length for each column
        col_widths = [ len(getattr(col_name, 'name').replace(masOutput.SPACE, ' ')) for col_name in mytable.header ]

        # check to see if it should be printed like a horizontal or vertical table
        if mytable.printVertical is False:
            outlist = list()

            for row in mytable:
                # modify the col_widths to set a maximum length of each column to 60 characters
                row_lens = list()

                for col in row[1:]:
                    try:
                        row_lens.append(min(60, len(col)))
                    except TypeError:
                        # if this isn't a str or unicode value, explicitly convert it
                        row_lens.append(min(60, len(str(col))))

                col_widths = map(max, zip(col_widths, row_lens))

            # format the header
            if mytable.printHeader is not False:
                txtstr +=  "  ".join((getattr(val, 'name')).replace(masOutput.SPACE, ' ').ljust(length) for val, length in zip(mytable.header, col_widths)) + '\n'
                txtstr += '  '.join([ '-'*val for val in col_widths ])

            # format the data
            for row in mytable:
                # combine the row values together and extend them as needed
                # this may be a confusing statement, but its fast!
                #outlist.append("".join(map(lambda x: _extend(x[0], x[1]+2), zip(row[1:], col_widths))))
                outlist.append("".join([_extend(x[0], x[1]+2) for x in zip(row[1:], col_widths) ]))

            txtstr += '\n'
            txtstr += "\n".join(outlist)
            txtstr += '\n\n'

        else:
            outlist = list()

            # get max column width + 2
            max_col = max(col_widths) + 2

            # pre-justify header
            newheader = [ getattr(data,'name').replace(masOutput.SPACE, ' ').ljust(max_col) for data in mytable.header ]

            # this adds a slight speed increase for large output
            myappend = outlist.append

            # go through each row of data and join the header and values together
            for row in mytable:
                #myappend("\n".join(map(lambda x: x[0] + _extend(x[1], 0), zip(newheader, row[1:]))))
                myappend("\n".join([ x[0] + _extend(x[1], 0) for x in zip(newheader, row[1:])]))
                myappend("\n\n")

            txtstr += "".join(outlist)
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

        txtstr = unicode('', 'utf-8')
        page_format = config.get_var(self.name, 'format')

        # we need to output the File Information plugin first as it contains the
        # summary information on the analyzed file
        try:
            log.debug('Writing file information.')
            txtstr += processPage('File Information', data[data.keys()[0]]['Generic']['File Information'], page_format)
            renderText(page_format, config.get_var('Dir', 'log_dir'), data[data.keys()[0]]['Generic']['File Information'].meta['filename'], txtstr)
            txtstr = unicode('', 'utf-8')
        except KeyError:
            log.error('File Information plug-in data missing. Aborting.')
            return False

        # loop through category data
        for cats, catdata in data[data.keys()[0]].iteritems():
            if page_format == 'single':
                catstr = '{} Category Analysis Results'.format(cats)
                log.debug('Writing {} results.'.format(cats))
                txtstr += '{}\n'.format(catstr) + '-'*len(catstr) + '\n'

            # loop through plugin data and generate the output text
            for plugin, pages in catdata.iteritems():
                if cats == 'Generic' and plugin == 'File Information':
                    continue

                # process the page into its output string
                txtstr += processPage(plugin, pages, page_format)

                # render the text into the appropriate location
                renderText(page_format, config.get_var('Dir', 'log_dir'), pages.meta['filename'], txtstr)
                txtstr = ''

        return True
