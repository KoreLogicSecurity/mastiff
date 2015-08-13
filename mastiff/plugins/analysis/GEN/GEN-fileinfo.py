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
File Info plugin

Plugin Type: Generic
Purpose:
  This plug-in obtains the file information, such as the name and file size
  and stores it into the database.

Database:
  A new table named files will be added to the database. This table contains
  the following fields:

  id - Primary Key
  sid - The id # of the file in the mastiff table.
  filename - The filename, including path, of the file being analyzed.
  size - The file size in bytes.
  firstseen -  GMT date of when it was first seen (in UNIX timestamp).
  lastseen - GMT date of when it was last seen (in UNIX timestamp).
  times - Number of times this file has been analyzed.

Output:
   Data is only sent to the database. No files are created.

"""

__version__ = "$Id$"

import os
import time
import logging
import sqlite3

import mastiff.plugins.category.generic as gen
import mastiff.sqlite as DB

class GenFileInfo(gen.GenericCat):
    """File Information plugin code."""

    def __init__(self):
        """Initialize the plugin."""
        gen.GenericCat.__init__(self)
        self.page_data.meta['filename'] = 'file_info'

    def analyze(self, config, filename):
        """Analyze the file."""

        # sanity check to make sure we can run
        if self.is_activated == False:
            return False
        log = logging.getLogger('Mastiff.Plugins.' + self.name)
        log.info('Starting execution.')

        data = dict()
        data['filename'] = filename
        data['size'] = os.stat(filename).st_size
        data['time'] = time.time()
        data['hashes'] = config.get_var('Misc',  'hashes')

        self.gen_output(config, data)

        self.output_db(config, data)
        return self.page_data

    def gen_output(self, config, data):
        """ Add the output into the local page structure. """
        info_table = self.page_data.addTable('File Information')
        info_table.addheader([('name', str), ('info', str)], printHeader=False)

        info_table.addrow(['File Name', data['filename']])
        info_table.addrow(['Size', data['size']])
        info_table.addrow(['Time Analyzed', data['time']])

        hash_table = self.page_data.addTable('File Hashes')
        hash_table.addheader([('Algorithm', str), ('Hash', str)])
        hash_table.addrow(['MD5', data['hashes'][0]])
        hash_table.addrow(['SHA1', data['hashes'][1]])
        hash_table.addrow(['SHA256', data['hashes'][2]])

    def output_db(self, config, data):
        """Print output from analysis to a file."""
        log = logging.getLogger('Mastiff.Plugins.' + self.name)

        db = DB.open_db_conf(config)
        if db is None:
            return False
            
        db.text_factory = str

        # If the 'files' table does now exist, add it
        if DB.check_table(db,  'files')  == False:
            log.debug('Adding table files')
            fields = [ 'id INTEGER PRIMARY KEY',
                                   'sid INTEGER',
                                  'filename TEXT',
                                  'size INTEGER',
                                  'firstseen INTEGER',
                                  'lastseen INTEGER',
                                  'times INTEGER']
            if DB.add_table(db, 'files',  fields) is None:
                return False
            db.commit()

        cur = db.cursor()
        sqlid = DB.get_id(db,  data['hashes'])

        if sqlid is None:
            log.error('%s hashes do not exist in the database',  data['filename'])
            return False

        # see if the filename already exists in the db
        try:
            cur.execute('SELECT id, times FROM files WHERE filename=? AND sid=?',
                         (data['filename'], sqlid, ))
        except sqlite3.Error, err:
            log.error('Could not query filename table: %s',  err)
            return None
        results = cur.fetchone()
        if results is not None:
            # filename is already in there. just update the lastseen item
            log.debug('%s is already in the database for hashes. Updating times.',
                      data['filename'])
            try:
                cur.execute('UPDATE files SET lastseen=?, times=? WHERE id=?',
                                     (int(data['time']), results[1]+1, results[0], ))
                db.commit()
            except sqlite3.OperationalError, err:
                log.error('Could not update times: %s',  err)
                return False
            return True

        # file info is not in the database, add it
        try:
            cur.execute('INSERT INTO files (sid, filename, size, firstseen, lastseen, times) \
                                 VALUES (?, ?, ?, ?, ?, ?)',
                                    (sqlid,  data['filename'], data['size'],
                                    int(data['time']),  int(data['time']), 1,  ))
            db.commit()
        except sqlite3.Error,  err:
            log.error('Could not insert filename into files: %s',  err)
            return False

        return True

