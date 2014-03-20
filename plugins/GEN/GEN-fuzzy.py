#!/usr/bin/env python
"""
  Copyright 2012-2013 The MASTIFF Project, All Rights Reserved.

  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.
"""

"""
Fuzzy Hashing plug-in

Plugin Type: Generic
Purpose:
  This plug-in generates the fuzzy hash of the given file.
  Also compares the fuzzy hashes against all of hashes already
  generated in the database.

Requirements:
  - ssdeep (http://ssdeep.sourceforge.net/)
  - pydeep (https://github.com/kbandla/pydeep)

Output:
   - fuzzy.txt - File listing the fuzzy hash of the file and any files that
     match.
   - The 'fuzzy' field will get added to the files table in the DB to store
     the fuzzy hash.

"""

__version__ = "$Id$"

import logging
import os

try:
    import pydeep
except ImportError, error:
    print('Gen-fuzzy: Could not import pydeep: %s' % error)

import mastiff.sqlite as DB
import sqlite3
import mastiff.category.generic as gen

class GenFuzzy(gen.GenericCat):
    """Fuzzy hashing plugin."""

    def __init__(self):
        """Initialize the plugin."""
        gen.GenericCat.__init__(self)

    def analyze(self, config, filename):
        """Analyze the file."""

        # sanity check to make sure we can run
        if self.is_activated == False:
            return False
        log = logging.getLogger('Mastiff.Plugins.' + self.name)
        log.info('Starting execution.')
        log.info('Generating fuzzy hash.')

        try:
            my_fuzzy = pydeep.hash_file(filename)
        except pydeep.error, err:
            log.error('Could not generate fuzzy hash: %s', err)
            return False

        if self.output_db(config, my_fuzzy) == False:
            return False

        self.compare_hashes(config, my_fuzzy)

        return True

    def compare_hashes(self, config, my_fuzzy):
        """
           Compare the current hash to all of the fuzzy
           hashes already collected.
        """
        log = logging.getLogger('Mastiff.Plugins.' + self.name + '.compare')
        db = DB.open_db_conf(config)
        conn = db.cursor()

        log.info('Comparing fuzzy hashes.')

        fuzz_results = list()
        my_md5 = config.get_var('Misc', 'hashes')[0]
        query = 'SELECT md5, fuzzy FROM mastiff WHERE fuzzy NOT NULL'
        try:
            # compare current hash for all fuzzy hashes
            for results in conn.execute(query):
                percent = pydeep.compare(my_fuzzy, results[1])
                if percent > 0 and my_md5 != results[0]:
                    fuzz_results.append([results[0], percent])
        except sqlite3.OperationalError, err:
            log.error('Could not grab other fuzzy hashes: %s', err)
            return False
        except pydeep.error, err:
            log.error('pydeep error: %s', err)

        # print out results
        my_file = open(config.get_var('Dir', 'log_dir') + os.sep + 'fuzzy.txt', 'w')
        my_file.write('Fuzzy Hash: %s\n\n' % my_fuzzy)
        if len(fuzz_results) > 0:
            my_file.write('This file is similar to the following files:\n\n')
            my_file.write('{0:35}\t{1:10}\n'.format('MD5', 'Percent'))
            for (md5,  percent) in fuzz_results:
                my_file.write('{0:35}\t{1:3}\n'.format(md5, percent))
        else:
            my_file.write('No other fuzzy hashes were related to this file.\n')

        my_file.close()
        return True

    def output_db(self, config, my_fuzzy):
        """ Add fuzzy hash to the DB."""
        log = logging.getLogger('Mastiff.Plugins.' + self.name + '.DB_output')

        # open up the DB and extend the mastiff table to include fuzzy hashes
        db = DB.open_db_conf(config)

        # there is a possibility the mastiff table is not available yet
        # check for that and add it
        if DB.check_table(db,  'files')  == False:
            log.debug('Adding table "files"')
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

        if not DB.add_column(db, 'mastiff', 'fuzzy TEXT DEFAULT NULL'):
            log.error('Unable to add column.')
            return False

        conn = db.cursor()
        # update our hash
        sqlid = DB.get_id(db, config.get_var('Misc', 'Hashes'))
        query = 'UPDATE mastiff SET fuzzy=? WHERE id=?'
        try:
            conn.execute(query, (my_fuzzy, sqlid, ))
            db.commit()
        except sqlite3.OperationalError, err:
            log.error('Unable to add fuzzy hash: %s', err)
            return False

        db.close()
        return True

