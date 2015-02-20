#!/usr/bin/env python

__version__ = "$Id$"

import collections
from yapsy.IPlugin import IPlugin

BASEHEADER = collections.namedtuple('BASEHEADER', 'name type')
BASEROW = collections.namedtuple('BASEROW', 'ROWINDEX')

class TableError(Exception):
    """ Table Exception class """
    pass

class PageError(Exception):
    """ Page Exception class """
    pass

class table(object):
    """
        Base constructor for table of data.
        A table contains a header and rows of data.
        - The header is just a single row that contains the description of the data.
        - You may only add one row of data at a time
    """
    def __init__(self, header=None, data=None, title=None):
        """
            Initialize the table.
            self.header: List containing the column names in BASEHEADER named tuple type.
            self.rowdef: Named tuple based on BASEROW. Names are based on header def.
            self.title: String describing the contents of the table.
            self.rows: List of self.rowdef named tuples. Contains the table data.
            self.INDEX: Used for row order. Currently automatically generated.

            Input:
            - header: List containing the data definition.
            - data: List containing the initial row of data to initialize.
            - title: String containing the title for the table.
        """
        self.INDEX = 0
        self.header = None
        self.printHeader = True
        self.rowdef = None
        self.addheader(header)
        self.title = title
        self.rows = list()
        if data is not None:
            self.addrow(data)
        return

    def __str__(self):
        """ Return a string containing a quickly formatted view of the table. """
        outstring = ''
        if self.title is not None and self.title != '':
            outstring += self.title + '\n'
        if self.header is not None:
            for item in self.header:
                outstring += str(item.name) + '\t'
            outstring += '\n'
        if self.rows is not None and len(self.rows) > 0:
            for rows in sorted(self.rows, key=lambda x: x[0]):
                outstring += '\t'.join([ str(x) for x in rows[1:] ]) + '\n'

        return outstring

    def __repr__(self):
        return '<table [' + repr(self.header) + '], ' + repr(self.rows) + '>'

    def __iter__(self):
        """
            Generator to go through table rows.
            Returns the row tuple of the item.
        """
        for item in self.rows:
            yield item

    def addtitle(self, title=None):
        """ Add a title to the table. """
        if title is not None:
            self.title = title
        else:
            self.title = ''

    def addheader(self, header=None, printHeader=True):
        """ Add a header to the table.
            The header defines the format of the table and should be a list
            composed of the names of the fields in the table.

            After created, the header is used to construct the named tuple for
            all the rows in the table.
        """
        if header is not None:
            self.header = list()
            if isinstance(header, list):
                rowdef = tuple()
                for item in header:
                    self.header.append(BASEHEADER(item, 'str'))
                    rowdef = rowdef + (item, )
            else:
                raise TypeError('Headers must be of type list.')

            if printHeader is False:
                self.printHeader = False

            # if we have a rowdef, create the row def tuple
            if len(rowdef) > 0:
                self.rowdef = collections.namedtuple('ROWTUPLE', BASEROW._fields + (rowdef ))

    def addrow(self, row):
        """
            Add a row of data to the table.
            A header must be defined prior to adding any rows of data.
            Input:
                - row: Iterable containing row of data to add to the table. (best if list or tuple used)
                        Each item in the iterable will be placed into a separate column in the table.
        """

        # make sure we have a header defined
        if self.header is None:
            raise TableError('Header is needed before rows can be added.')

        if self.rows is None:
            self.rows = list()

        # go through the data and add to the table
        if row is not None:

        # The data should be an iterable.
         try:
            if len(row) != len(self.header):
                raise TableError('Row length ({0}) does not equal header length ({1}).'.format(len(row), len(self.header)))

            # Currently the index (row position in the table) is by the order the data is received
            # TODO: Take in an index
            rowlist = [self.INDEX]
            self.INDEX += 1

            for item in row:
                rowlist.append(item)

            # create and add named tuple into self.rows
            self.rows.append(self.rowdef._make(rowlist))
         except TypeError:
            raise TypeError('Invalid type given for data.')

class page(object):
    """
        A page is a container for multiple tables of data.
        Tables will be listed in the order they are added, unless an index is specified
        when the table is added.
    """
    def __init__(self):
        self.tables = dict()
        self.meta = dict()
        self.meta['filename'] = 'CHANGEME'
        self.counter = 0

    def __getitem__(self, title):
        """ Overload the getitem operator to return a specified table. """
        try:
            return self.tables[title]['table']
        except KeyError:
            raise KeyError('Table {} does not exist.'.format(title))

    def __iter__(self):
        """
            Generator to go through the list of tables, sorted by index.
            Yields a list of [ title, table, index ]
        """
        for title in self.tables:
            yield [ title, self.tables[title]['table'], self.tables[title]['index'] ]

    def __str__(self):
        outstring = ''
        for mytable in sorted(self.tables.iteritems(), key=lambda (k, v): v['index']):
            outstring += str(mytable[1]['table'])

        return outstring

    def __repr__(self):
        return '<page [' + repr(self.tables) + '] >'

    def addTable(self, title, header=None, index=None):
        if title is None or title == '':
            raise PageError('New tables must have a title.')

        if index is None:
            index = self.counter

        newTable = table(header=header, title=title)
        self.tables[title] = { 'table': newTable, 'index': index }
        self.counter += 1
        return newTable

class MastiffOutputPlugin(IPlugin):
    """The base plugin class every output plugin should inherit."""

    def __init__(self, name=None):
        """Initialize the Mastiff plugin class."""
        IPlugin.__init__(self)
        self.name = name

    def activate(self):
        """Power rings activate! Form of Mastiff Plugin!"""
        IPlugin.activate(self)

    def deactivate(self):
        """Deactivate plugin."""
        IPlugin.deactivate(self)

    def output(self, config, data):
        """ Output function. Should be overwritten by plugins. """
        return False

    def set_name(self, name=None):
        """
           Yapsy does not provide an easy way to get or set our own
           name, so here's a function to do so.
        """
        self.name = name
        return self.name


