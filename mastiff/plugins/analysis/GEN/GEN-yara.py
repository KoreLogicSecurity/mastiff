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
Yara Plugin

Plugin Type: Generic
Purpose:
  This plug-in allows the use of Yara plug-ins to be run on the file being
  analyzed. Yara rules are specified through a configuration option and all
  rules will be applied to the file.

Requirements:
  - Yara, libyara and yara-python must be installed.
    http://code.google.com/p/yara-project

Configuration Options:
[yara]
  yara_sigs = Base path to Yara signatures. This path will be recursed
              to find additional signatures. Files with ".yar" or ".yara" will
              be used.
              Leave blank to disable the plug-in.

Output:
   yara.txt - Output listing all matches found. This file will not be present
              if no matches were found.

Database:

  A new table named 'yara' will be created with the following fields:

    id INTEGER PRIMARY KEY = Primary key
    sid INTEGER DEFAULT NULL = ID of file being analyzed
    rule_name TEXT DEFAULT NULL = Name of the Yara rule matched
    meta TEXT DEFAULT NULL = Yara meta information
    tag TEXT DEFAULT NULL = Yara tag information
    rule_file TEXT DEFAULT NULL = Full path to rule file match is from
    file_offset INTEGER DEFAULT NULL = Offset in analyzed file match was found
    string_id TEXT DEFAULT NULL = ID of match variable from Yara rule
    data TEXT DEFAULT NULL = Data Yara rule matched on

  Only new information will be added to the database.
  The database is _NOT_ checked to see if old information is present.

NOTE:

  Since the Yara output can contain data that is in binary, any potential binary
  data is converted to hex. Within the string, the binary data will be
  represented as "backslash-xXX" with the XX being the hex equivalent.

  Please ensure all of your rules work in Yara before using them
  in mas.py.

"""

__version__ = "$Id$"

import logging
import os
import sqlite3

try:
    import yara
except ImportError, error:
    print "GenYara: Could not import yara: %s" % error

import mastiff.sqlite as DB
import mastiff.plugins.category.generic as gen
import mastiff.plugins as plugins

class GenYara(gen.GenericCat):
    """Yara signature plug-in."""

    def __init__(self):
        """Initialize the plugin."""
        gen.GenericCat.__init__(self)
        self.filename = ""

    def analyze(self, config, filename):
        """Analyze the file."""

        # sanity check to make sure we can run
        if self.is_activated == False:
            return False
        log = logging.getLogger('Mastiff.Plugins.' + self.name)
        log.info('Starting execution.')
        self.filename = filename

        # get my config options
        plug_opts = config.get_section(self.name)
        if plug_opts is None:
            log.error('Could not get %s options.', self.name)
            return False
        elif len(plug_opts['yara_sigs']) == 0:
            log.debug('No yara_sigs parameter. Disabling plug-in.')
            return False

        # find all yara signature files
        sig_files = self.get_sigs(plug_opts['yara_sigs'])
        if sig_files is None or len(sig_files) == 0:
            log.debug('No signature files detected. Exiting plug-in.')
            return True

        # create sig dict of all files found.
        # namespace is the file name of the rule
        sig_dict = dict()
        for files in sig_files:
            sig_dict[files] = files

        # compile rules and run against file
        try:
            rules = yara.compile(filepaths=sig_dict)
        except yara.SyntaxError, err:
            log.error('Rule error: %s', err)
            return False

        # generate matches        
        try:
            matches = rules.match(self.filename, callback=self._debug_print)
        except yara.Error, err:
            log.error('Yara error: %s', err)
            return False        

        if len(matches) > 0:
            self.output_file(config.get_var('Dir','log_dir'), matches)
            self.output_db(config, matches)

        return True

    def get_sigs(self, sig_dir):
        """
           Recurse through a directory for Yara signature files.
           Files should end in ".yar" or "yara".
           Returns a list of signature files, None on errors.
        """
        # sanity check the path
        log = logging.getLogger('Mastiff.Plugins.' + self.name + '.get_sigs')
        if not os.path.isdir(os.path.expanduser(sig_dir)) \
        or not os.path.exists(os.path.expanduser(sig_dir)):
            log.error('%s is not a directory or does not exist.' % sig_dir)
            return None

        sig_files = list()

        # walk the directory
        for items in os.walk(os.path.expanduser(sig_dir)):
            # find each yara sig file in the dir
            for files in items[2]:
                if files.endswith('.yar') or \
                files.endswith('.yara'):
                    sig_files.append(items[0] + os.sep + files)

        return sig_files

    def _debug_print(self, data):
        """ Debug printing of Yara matches."""
        log = logging.getLogger('Mastiff.Plugins.' + self.name + '.match')

        if data['matches'] == True:
            for match in data['strings']:
                log.debug('Match: %s: %s' % (data['rule'], plugins.bin2hex(match[2])))

        return yara.CALLBACK_CONTINUE


    def output_file(self, outdir, matches):
        """Prints any Yara matches to a file named yara.txt."""

        out_file = open(outdir + os.sep + 'yara.txt', 'w')
        if len(matches) == 0:
            out_file.write('No Yara matches.')
        else:
            out_file.write('Yara Matches for %s\n' % self.filename)
            for item in matches:
                out_file.write('\nRule Name: %s\n' % item.rule)
                out_file.write('Yara Meta: %s\n' % item.meta)
                out_file.write('Yara Tags: %s\n' % item.tags)
                out_file.write('Rule File: %s\n' % item.namespace)
                out_file.write('Match Info:\n')
                for y_match in item.strings:
                    out_file.write('\tFile Offset: %d\n' % y_match[0])
                    out_file.write('\tString ID: %s\n' % y_match[1])
                    out_file.write('\tData: %s\n\n' % plugins.bin2hex(y_match[2]))
                out_file.write('*'*79 + '\n')

        out_file.close()

        return True

    def output_db(self, config, matches):
        """ Output any matches to the database. """
        log = logging.getLogger('Mastiff.Plugins.' + self.name + '.output_db')

        db = DB.open_db_conf(config)
        if db is None:
            return False

        # add the table 'yara' if it doesn't exist
        if DB.check_table(db, 'yara') == False:
            fields = ['id INTEGER PRIMARY KEY',
                      'sid INTEGER DEFAULT NULL',
                      'rule_name TEXT DEFAULT NULL',
                      'meta TEXT DEFAULT NULL',
                      'tag TEXT DEFAULT NULL',
                      'rule_file TEXT DEFAULT NULL',
                      'file_offset INTEGER DEFAULT NULL',
                      'string_id TEXT DEFAULT NULL',
                      'data TEXT DEFAULT NULL' ]
            if not DB.add_table(db, 'yara', fields ):
                log.error('Unable to add "yara" database table.')
                return False

        sqlid = DB.get_id(db, config.get_var('Misc', 'hashes'))
        sel_query = 'SELECT count(*) FROM yara '
        sel_query += 'WHERE sid=? AND rule_name=? AND meta=? AND tag=? AND '
        sel_query += 'rule_file=? AND file_offset=? AND string_id=? AND data=? '
        query = 'INSERT INTO yara '
        query += '(sid, rule_name, meta, tag, rule_file, file_offset, string_id, data) '
        query += 'VALUES (?, ?, ?, ?, ?, ?, ?, ?)'

        cur = db.cursor()

        # go through all matches and insert into DB if needed
        try:
            for item in matches:
                for y_match in item.strings:
                    match_insert = ( sqlid, item.rule, str(item.meta), \
                                    str(item.tags), item.namespace, \
                                    y_match[0], y_match[1], plugins.bin2hex(y_match[2]), )
                    # check to see if its already in there
                    cur.execute(sel_query, match_insert)
                    if cur.fetchone()[0] == 0:
                        # not in the db already, add it in
                        log.debug('Adding %s match to database.' % (item.rule))
                        cur.execute(query, match_insert)
            db.commit()
        except sqlite3.Error, err:
            log.error('SQL error when adding item to DB: %s' % err)
            return False


        db.close()
        return True

