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
sqlite.py

This file contains helper functions used to assist MASTIFF plug-ins in placing
data into a sqlite database.

"""

__version__ = "$Id$"

import logging
import os
import re

import sqlite3

def open_db(db_name):
    """ Return a sqlite3 Connection object for the given database name.
          If the file does not exist, it will attempt to create it.
    """

    log = logging.getLogger('Mastiff.DB.open')
    if not os.path.exists(db_name) or not os.path.isfile(db_name):
        log.warning('%s does not exist. Will attempt to create.',  db_name)

    try:
        db = sqlite3.connect(db_name)
    except sqlite3.OperationalError, err:
        log.error('Cannot access sqlite DB: %s.',  err)
        db  = None

    return db

def open_db_conf(config):
    """
       Read the DB information from a MASTIFF config file.
       Return a Sqlite Connection or None.
    """
    log = logging.getLogger('Mastiff.DB.open_db_conf')
    log_dir = config.get_var('Dir','base_dir')
    mastiff_db = config.get_var('Sqlite',  'db_file')

    if mastiff_db is None or log_dir is None or len(mastiff_db) == 0:
        log.error('Unable to open DB.')
        return None

    # db_file can be a full path - if it is, then use it
    dirname = os.path.expanduser(os.path.dirname(mastiff_db))
    if len(dirname) > 0 and os.path.exists(dirname) == True:
        return open_db(mastiff_db)

    return open_db(os.path.expanduser(log_dir) + os.sep + mastiff_db)

def sanitize(string):
    """
       Sanitize a string that cannot be sent correctly to sqlite3.
       Returns a string only containing letters, numbers, whitespace
       or underscore.
    """
    return re.sub(r'[^a-zA-Z0-9_\s]', '', string)

def check_table(db, table):
    """ Return True is a table exists, False otherwise"""
    conn = db.cursor()

    # sqlite3 won't let us use table names as variables, so we have to
    # use string substitution
    query = 'SELECT * FROM ' + sanitize(table)
    try:
        conn.execute(query)
        return True
    except sqlite3.OperationalError:
        # table doesn't exist
        return False

def add_table(db, table, fields):
    """
        Add a table to a database.
        Table is a string of the table name.
        fields is a list of columns in the form 'column_name column_type'
        Returns True if successful, False otherwise.
    """
    conn = db.cursor()

    if check_table(db, table):
        # Table already exists
        return True

    query = 'CREATE TABLE ' + sanitize(table) + '('
    for item in fields:
        query = query + sanitize(item) + ','
    query = query[:-1] + ')'

    try:
        conn.execute(query)
        db.commit()
    except sqlite3.OperationalError,  err:
        log = logging.getLogger('Mastiff.DB.add_table')
        log.error('Could not add table %s: %s',  table,  err)
        return False

    return True

def add_column(db, table, col_def):
    """
       Alter an existing table by adding a column to it.
       db is a sqlite3 db connection
       table is the table name
       col_def is the column definition
    """
    log = logging.getLogger('Mastiff.DB.add_column')
    if check_table(db, table) == False:
        log.error('Table %s does not exist.', table)
        return False

    conn = db.cursor()

    query = 'ALTER TABLE ' + table + ' ADD COLUMN ' + col_def
    try:
        conn.execute(query)
        db.commit()
    except sqlite3.OperationalError, err:
        # dup column name errors are fine
        if 'duplicate column name' not in str(err):
            log.error('Could not add column: %s', err)
            return False
    else:
        log.debug('Extended %s with column def "%s".', table, col_def)

    return True

def create_mastiff_tables(db):
    """
        Create the tables in the MASTIFF database to store
        the main analysis information.

        db is a sqlite3 db connection
    """
    if check_table(db, 'mastiff') == True:
        # table already exists, nothing to do
        return True

    fields = ['id INTEGER PRIMARY KEY',
              'md5 TEXT DEFAULT NULL',
              'sha1 TEXT DEFAULT NULL',
              'sha256 TEXT DEFAULT NULL',
              'type TEXT DEFAULT NULL']

    # if we were not successful, return None
    if add_table(db, 'mastiff',  fields) is None:
        return False
    db.commit()

    return True

def get_id(db,  hashes):
    """
       Return the db id number of the given tuple of hashes.
       Returns None if tuple does not exist.
    """

    log = logging.getLogger('Mastiff.DB.get_id')
    cur = db.cursor()
    try:
        cur.execute('SELECT id FROM mastiff WHERE (md5=? AND \
        sha1=? AND sha256=?)',
                    [ hashes[0],  hashes[1],  hashes[2], ])
    except sqlite3.OperationalError,  err:
        log.error('Could not execute query: %s',  err)
        return None

    sqlid = cur.fetchone()
    if sqlid is None:
        return sqlid
    else:
        return sqlid[0]

def insert_mastiff_item(db, hashes,  cat_list=None):
    """
       Insert info on analyzed file into database.
       hashes tuple  and cat_list will be inserted into mastiff table.
    """

    log = logging.getLogger('Mastiff.DB.Insert')

    # we'll create the tables just to be sure they exist
    create_mastiff_tables(db)

    cur = db.cursor()
    sqlid = get_id(db,  hashes)

    if sqlid is not None:
        # already in there, just send back the id
        log.debug('Hashes %s are already in the database.',  hashes)
    else:
        try:
            cur.execute('INSERT INTO mastiff (md5, sha1, sha256) \
            VALUES (?, ?, ?)',
                                    (hashes[0],  hashes[1],  hashes[2]))
            db.commit()
        except sqlite3.OperationalError,  err:
            log.error('Could not insert item into mastiff: %s',  err)
            return None
        sqlid = cur.lastrowid

    if cat_list is not None and sqlid is not None:
        try:
            log.info('Adding %s',  str(cat_list))
            cur.execute('UPDATE mastiff SET type=? WHERE id=?',
                        (str(cat_list), sqlid, ))
            db.commit()
        except sqlite3.OperationalError,  err:
            log.error('Could not update file type in DB: %s',  err)

    if sqlid is None:
        return sqlid

    return sqlid

# testing functions
if __name__ == '__main__':

    # configure logging for Mastiff module
    format_ = '[%(asctime)s] [%(levelname)s] [%(name)s] : %(message)s'
    logging.basicConfig(format=format_)
    log = logging.getLogger("Mastiff")
    log.setLevel(logging.DEBUG)

    mysql = open_db('/tmp/test.db')
    if mysql is None:
        print "Was not created"

    create_mastiff_tables(mysql)
    print "*** TEST: inserting items"
    insert_mastiff_item(mysql,  ('123', '345', '456'), 'filename')
    insert_mastiff_item(mysql,  ('135', '790', '246'), 'filename2')
    insert_mastiff_item(mysql,  ('111', '333', '555'), 'filename3')
    insert_mastiff_item(mysql,  ('444', '666', '888'), 'filename4')
    print "*** TEST: insert dup hashes"
    insert_mastiff_item(mysql,  ('111', '333', '555'), 'filename5')
    print "*** TEST: insert dup filename"
    insert_mastiff_item(mysql,  ('111', '333', '555'), 'filename3')
    print "*** TEST: add column"
    add_column(mysql, 'mastiff', 'test_col TEXT DEFAULT NULL')
    mysql.close()

