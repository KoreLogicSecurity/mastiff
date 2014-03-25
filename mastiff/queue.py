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
   The queue module is used to add a job queue to MASTIFF. The MastiffQueue
   class uses the MASTIFF SQLite database to keep track of any files that are
   required to be analyzed. It works as a LIFO queue and has no priorities.

   This module was originally taken from Thiago Arruda's public domain Python
   job queue at http://flask.pocoo.org/snippets/88/ and has had some minor
   modifications made to make it in-line with MASTIFF.
"""

__version__ = "$Id"

import os, sqlite3,  os.path
import sys
from cPickle import loads, dumps
from time import sleep
try:
    from thread import get_ident
except ImportError:
    from dummy_thread import get_ident

import mastiff.conf as Conf
import logging

class MastiffQueue(object):
    """ Class to implement a LIFO job queue in a SQLite Database. """

    _create = (
            'CREATE TABLE IF NOT EXISTS queue '
            '('
            '  id INTEGER PRIMARY KEY AUTOINCREMENT,'
            '  file BLOB'
            ')'
            )
    _count = 'SELECT COUNT(*) FROM queue'
    _iterate = 'SELECT id, file FROM queue'
    _append = 'INSERT INTO queue (file) VALUES (?)'
    _write_lock = 'BEGIN IMMEDIATE'
    _popleft_get = (
            'SELECT id, file FROM queue '
            'ORDER BY id LIMIT 1'
            )
    _popleft_del = 'DELETE FROM queue WHERE id = ?'
    _peek = (
            'SELECT file FROM queue '
            'ORDER BY id LIMIT 1'
            )

    def __init__(self, config):
        """ Initialize the class. """

        #Read the config file and find where the DB is
        log = logging.getLogger('Mastiff.Queue.init')

        conf = Conf.Conf(config)
        self.path = os.path.abspath(conf.get_var('Dir', 'log_dir') + os.sep + conf.get_var('Sqlite', 'db_file'))
        log.debug('Setting up queue table at %s' % self.path)
        
        # create the dir if it doesn't exist
        if not os.path.isdir(os.path.dirname(self.path)):
            try:
                os.makedirs(os.path.dirname(self.path))
            except OSError, err:
                log.error('Could not make %s: %s. Exiting.', self.path, err)
                sys.exit(1)
        
        if not os.path.exists(self.path) or not os.path.isfile(self.path):
            # does not exist, create
            try:
                sqlite3.connect(self.path)
            except sqlite3.OperationalError, err:
                log.error('Cannot access sqlite DB: %s.',  err)

        self._connection_cache = {}
        with self._get_conn() as conn:
            # create the database if required
            conn.execute(self._create)

    def __len__(self):
        """ Allows len(queue) to return the number of items to be processed. """
        with self._get_conn() as conn:
            my_len = conn.execute(self._count).next()[0]
        return my_len

    def __iter__(self):
        """ Iterable object. """
        with self._get_conn() as conn:
            for my_id, obj_buffer in conn.execute(self._iterate):
                yield loads(str(obj_buffer))

    def _get_conn(self):
        """ Returns a connection to the database. """
        my_id = get_ident()
        if my_id not in self._connection_cache:
            self._connection_cache[my_id] = sqlite3.Connection(self.path, timeout=60)
        return self._connection_cache[my_id]

    def append(self, obj):
        """ Add a job to the queue. """
        obj_buffer = buffer(dumps(obj, 2))
        with self._get_conn() as conn:
            conn.execute(self._append, (obj_buffer,))

    def popleft(self, sleep_wait=False):
        """
           Pops a job off the queue and returns it. It will return the next item
           in the queue, or None is none exist. By default, the function will not
           wait if it cannot access the queue table or there is nothing.
        """
        keep_pooling = True
        wait = 0.1
        max_wait = 2
        tries = 0
        with self._get_conn() as conn:
            my_id = None
            while keep_pooling:
                conn.execute(self._write_lock)
                cursor = conn.execute(self._popleft_get)
                try:
                    my_id, obj_buffer = cursor.next()
                    keep_pooling = False
                except StopIteration:
                    conn.commit() # unlock the database
                    if not sleep_wait:
                        keep_pooling = False
                        continue
                    tries += 1
                    sleep(wait)
                    wait = min(max_wait, tries/10 + wait)
            if id:
                conn.execute(self._popleft_del, (my_id,))
                return loads(str(obj_buffer))
        return None

    def peek(self):
        """ Return the next item in the queue, but do not remove it. """
        with self._get_conn() as conn:
            cursor = conn.execute(self._peek)
            try:
                return loads(str(cursor.next()[0]))
            except StopIteration:
                return None
                
    def clear_queue(self):
        """ Clear the job queue. """
        while self.__len__() > 0:
            self.popleft(sleep_wait=False)            
