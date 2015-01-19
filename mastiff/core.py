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
MASTIFF - MAlicious Static Inspection File Framework

This module implements the primary class for static analysis inspection.

Mastiff member variables:

cat_paths: List that contains the path to the category plug-ins.

plugin_paths: List that contains the paths to the analysis plug-ins.

filetype: Dictionary used to store the output from the file-type identification
functions.

file_name: full path to the file being analyzed.

hashes: Tuple of the MD5, SHA1 and SHA256 hashes of the file being analyzed.
This is also stored in the configuration file.

db: Sqlite3 Connection class to the database file.

cat_list: List that contains all of the category plug-ins to be used during
analysis.

activated_plugins: List that contains all of the plug-ins that have been
activated. This order of the plug-ins in this list is the order they will run.

cat_manager: Yapsy PluginManager class that manages the category plug-ins.

plugin_manager: Yapsy PluginManager class that manages the analysis plug-ins.

Mastiff member functions:

__init__(self, config_file=None, fname=None, loglevel=logging.INFO, override=None)
The initialization function of the class. This function will initialize all of the
member variables, set up logging, read in and store the configuration file, and
find and load all plug-ins.

init_file(self, fname)
This function validates the filename being analyzed
to ensure it exists and can be accessed, sets up the directory that all
output will be logged into, and adds initial file information into the
database.

set_filetype(self, fname=None, ftype=None)
Calls the file-type identification helper functions in mastiff/filetype.py,
and loops through all of the category plug-ins to determine which ones will
analyze the file.

validate(self, name, plugin)
Validates an analysis plug-in to ensure that it contains the correct functions.

activate_plugins(self, single_plugin=None)
Loops through all analysis plug-ins for category classes relevant to the file
type being examined and ensures they are valid. If validated, the analysis
plug-in is activated. This function also ensures that any pre-requisite plug-ins
have been activated.

analyze(self, fname=None, single_plugin=None)
Ensures the file type of the file is set up and loops through all activated
analysis plug-ins and calls their analyze() function.

list_plugins(self, type='analysis')
Helper function that loops through all available plug-ins and prints out their
name, path and description. The function can print out analysis or category
plug-in information.
"""

__version__ = "$Id$"

import sys
import os
import logging
import hashlib
from shutil import copyfile
from operator import attrgetter

if sys.version_info < (2, 6, 6):
    sys.stderr.write("Mastiff requires python version 2.6.6")
    sys.exit(1)

try:
    from yapsy.PluginManager import PluginManager
except ImportError, err:
    print "Yapsy not installed or accessible: %s" % err
    sys.exit(1)

import mastiff.conf as Conf
import mastiff.filetype as FileType
import mastiff.sqlite as DB
import mastiff.plugins.category.categories as Cats
import mastiff.plugins.analysis as analysis


class Mastiff:
    """Primary class for the static analysis inspection framework."""

    def __init__(self, config_file=None, fname=None, loglevel=logging.INFO, override=None):
        """Initialize variables."""

        # configure logging for Mastiff module
        format_ = '[%(asctime)s] [%(levelname)s] [%(name)s] : %(message)s'
        logging.basicConfig(format=format_)
        log = logging.getLogger("Mastiff")
        log.setLevel(loglevel)
        if log.handlers:
            log.handlers = []
                
        # read in config file
        self.config = Conf.Conf(config_file, override=override)

        # make sure base logging dir exists
        log_dir = self.config.get_var('Dir','log_dir')
        log_dir = os.path.abspath(os.path.expanduser(log_dir))        
        if not os.path.isdir(log_dir):
            try:
                os.makedirs(log_dir)
            except OSError, err:
                log.error('Could not make %s: %s. Exiting.', log_dir, err)
                sys.exit(1)
        self.config.set_var('Dir',  'base_dir',  log_dir)

        # set up file to log output to
        fh = logging.FileHandler(log_dir + os.sep + 'mastiff.log' )
        fh.setFormatter(logging.Formatter(format_))
        log.addHandler(fh)
        fh.setLevel(loglevel)

        # verbose logging set in the config and not command line?
        if self.config.get_bvar('Misc','verbose') == True and \
           loglevel != logging.ERROR:
            log.setLevel(logging.DEBUG)
            fh.setLevel(logging.DEBUG)

        # get path to category plugins
        self.cat_paths = [ os.path.dirname(Cats.__file__) ]

        # convert plugin paths to list
        self.plugin_paths = [ os.path.dirname(analysis.__file__)]
        # strip whitespace from dirs
        for tmp in str(self.config.get_var('Dir','plugin_dir')).split(','):
            if tmp:
                self.plugin_paths.append(os.path.expanduser(tmp.lstrip().rstrip()))

        self.filetype = dict()
        self.file_name = None
        self.hashes = None
        self.cat_list = list()
        self.activated_plugins = list()

        # Build the managers
        self.cat_manager = PluginManager()
        self.plugin_manager = PluginManager()

        # Find and load all category plugins
        cat_filter = dict()
        self.cat_manager.setPluginPlaces(self.cat_paths)
        self.cat_manager.collectPlugins()

        # Import all of the modules for the categories so we can access
        # their classes.
        for pluginInfo in self.cat_manager.getAllPlugins():

            log.debug('Found category: %s', pluginInfo.name)
            try:
                mod_name = "mastiff.plugins.category.%s" % \
                           os.path.basename(pluginInfo.path)
                cat_mod = __import__(mod_name,
                                   fromlist=["mastiff.plugins.category"])
            except ImportError, err:
                log.error("Unable to import category %s: %s",
                          pluginInfo.name,
                          err)
                self.cat_manager.deactivatePluginByName(pluginInfo.name)
                continue
            else:
                # We were able to import it, activate it
                self.cat_manager.activatePluginByName(pluginInfo.name)
                log.debug("Activated category: %s", pluginInfo.name)

            # Cat is imported, add class to the category filter
            # cat_filter will be a dict in the form:
            #     { cat_name: cat_class }
            # and contains all the category plugins that have been activated
            cat_class = getattr(cat_mod,
                                pluginInfo.plugin_object.__class__.__name__)
            cat_filter.update({pluginInfo.plugin_object.cat_name: cat_class})

        #log.debug("Category Filters: %s", cat_filter)

        # Now collect and load all analysis plugins
        self.plugin_manager.setPluginPlaces(self.plugin_paths)
        self.plugin_manager.setCategoriesFilter( cat_filter )
        self.plugin_manager.collectPlugins()

        # set up database
        self.db = DB.open_db_conf(self.config)
        DB.create_mastiff_tables(self.db)

        # init the filename if we have it
        if fname is not None:
            self.init_file(fname)
            
    def __del__(self):
        """
           Class destructor.
        """
        # Close down all logging file handles so we don't have any open file descriptors
        log = logging.getLogger("Mastiff")
        handles = list(log.handlers)
        for file_handle in handles:   
            log.removeHandler(file_handle)
            file_handle.close()
        
    def init_file(self, fname):
        """
           Validate the filename to ensure it can be accessed and set
           up class variables.

           This function is called when a filename is given or can be
           called directly.
        """
        log = logging.getLogger("Mastiff.Init_File")

        if fname is None:
            return None

        try:
            with open(fname, 'rb') as my_file:
                data = my_file.read()
        except IOError, err:
            log.error("Could not open file: %s", err)
            return None

        self.file_name = fname

        # create tuple of md5, sha1 and sha256 hashes
        self.hashes = hashlib.md5(data).hexdigest(), \
                      hashlib.sha1(data).hexdigest(), \
                      hashlib.sha256(data).hexdigest()
        self.config.set_var('Misc',  'hashes',  self.hashes)

        # update log_dir
        log_dir = os.path.abspath(os.path.expanduser(self.config.get_var('Dir','log_dir'))) + \
                  os.sep + \
                  self.hashes[0]
        self.config.set_var('Dir', 'log_dir', log_dir)

        # create log dir
        if not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir)
            except OSError, err:
                log.error('Could not make %s: %s. Exiting.', log_dir, err)
                sys.exit(1)

        # lets set up the individual log file
        # we may miss out on a couple prior logs, but thats OK
        log = logging.getLogger('Mastiff')
        fh = logging.FileHandler(log_dir + os.sep + 'mastiff.log' )
        format_ = '[%(asctime)s] [%(levelname)s] [%(name)s] : %(message)s'
        fh.setFormatter(logging.Formatter(format_))
        log.addHandler(fh)        
        fh.setLevel(logging.INFO)

        log = logging.getLogger("Mastiff.Init_File")        
        log.info('Analyzing %s.',  self.file_name)
        log.info("Log Directory: %s", log_dir)

        # copy file to the log directory
        if self.config.get_bvar('Misc', 'copy') is True:
            try:
                copyfile(self.file_name, log_dir + os.sep + os.path.basename(self.file_name) + '.VIR')
            except IOError, err:
                log.error('Unable to copy file: %s', err)
            log.debug('Copied file to log directory.')
        else:
            log.debug('Configuration set to not copy file.')

        # add entry to database if it exists
        if self.db is not None:
            log.debug('Adding entry to database.')
            DB.insert_mastiff_item(self.db,  self.hashes)

        return self.hashes

    def activate_plugins(self,  single_plugin=None):
        """
           Activate all plugins that are in the categories we selected.
           If single_plugin is given, only activate that plug-in.
        """

        has_prereq = list()

        for cats in self.cat_list:

            log = logging.getLogger('Mastiff.Plugins.Activate')
            log.debug('Activating plugins for category %s.', cats)

            for plugin in self.plugin_manager.getPluginsOfCategory(cats):

                if single_plugin is not None and single_plugin != plugin.name:
                    continue

                plugin.plugin_object.set_name(plugin.name)
                log.debug('Validating plugin "%s"', plugin.name)

                # if the plugin validates, try to activate it
                if self.validate(plugin.name, plugin.plugin_object) == True:
                    if plugin.plugin_object.prereq is not None:
                        # this plugin has a pre-req, can't activate yet
                        has_prereq.append([cats, plugin])
                    else:
                        log.debug('Activating "%s".', plugin.name)
                        self.plugin_manager.activatePluginByName(plugin.name, cats)
                        self.activated_plugins.append(plugin)
                else:
                    log.debug("Removing plugin %s %s.", plugin.name, cats)
                    self.plugin_manager.deactivatePluginByName(plugin.name,
                                                               cats)

        # now try to activate any plug-ins that have pre-reqs
        flag = True
        while flag is True:
            flag = False
            for plugins in has_prereq:
                # check to see if the pre-req in in the activated list
                inact = [p for p in self.activated_plugins if p.name == plugins[1].plugin_object.prereq]

                if len(inact) > 0:
                    # our pre-req has been activated, we can activate ourself
                    log.debug('Activating "%s". Pre-req fulfilled.', plugins[1].name)
                    self.plugin_manager.activatePluginByName(plugins[1].name, plugins[0])
                    self.activated_plugins.append(plugins[1])
                    has_prereq.remove(plugins)
                    flag = True

        # list out any plugins that were not activated due to missing pre-reqs
        for plugins in has_prereq:
            log.debug("Plugin %s not activated due to missing pre-req \"%s.\"" % \
                      (plugins[1].name, plugins[1].plugin_object.prereq ))

    def list_plugins(self, ctype='analysis'):
        """Print out a list of analysis or cat plugins."""

        if ctype == 'analysis':
            # analysis plug-ins
            print "Analysis Plug-in list:\n"
            print "%-25s\t%-15s\t%-25s\n%-50s" % \
                  ("Name", "Category", "Description", "Path")
            print '-' * 80

            for plugin in sorted(self.plugin_manager.getAllPlugins(),
                                  key=attrgetter('plugin_object.cat_name', 'name')):
                print "%-25s\t%-15s\t%-12s\n%-80s\n" % \
                (plugin.name, plugin.plugin_object.cat_name, \
                 plugin.description, plugin.path)

        elif ctype == 'cat':
            print "Category Plug-in list:\n"
            print "%-25s\t%-15s\t%-s" % ("Name", "FType", "Description")
            print '-' * 80
            # category plug-ins
            for plugin in sorted(self.cat_manager.getAllPlugins(),
                                 key=attrgetter('name')):
                print "%-25s\t%-15s\t%-s" % \
                      (plugin.name, plugin.plugin_object.cat_name,
                       plugin.description)

    def set_filetype(self, fname=None, ftype=None):
        """
        Calls the filetype functions and loops through the category
        plug-ins to see which ones will handle this file.
        """

        log = logging.getLogger('Mastiff.FileType')

        if fname is None and self.file_name is None:
            log.error("No file to analyze has been specified. Exiting.")
            sys.exit(1)
        elif fname is not None and self.file_name is None:
            if self.init_file(fname) is None:
                log.error("ERROR accessing file. Exiting.")
                sys.exit(1)

        if self.cat_list:
            # if self.cat_list is already set, assume that we've already
            # gone through this function
            return self.filetype

        if ftype is not None:
            # we are forcing a file type to run
            log.info('Forcing category plug-in "%s" to be added.', ftype)
            self.cat_list.append(ftype)

        # Grab the magic file type of the file. This is done here so as not
        # to do it in every category plug-in.
        self.filetype['magic'] = FileType.get_magic(self.file_name)

        # Grab the TrID type
        trid_opts = self.config.get_section('File ID')
        self.filetype['trid'] = FileType.get_trid(self.file_name,
                                                  trid_opts['trid'],
                                                  trid_opts['trid_db'])

        # Cycle through all of the categories and see if they should be added
        # to the list of categories to be run.
        for pluginInfo in self.cat_manager.getAllPlugins():
            cat_name = pluginInfo.plugin_object.is_my_filetype(self.filetype,
                                                               self.file_name)
            log.debug('Checking cat %s for filetype.', pluginInfo.name)
            if cat_name is not None:
                # cat_list contains analysis plugin categories to be used
                self.cat_list.append(cat_name)
                log.debug('Adding %s to plugin selection list.', cat_name)

        # add file type to the DB
        if self.db is not None:
            DB.insert_mastiff_item(self.db,  self.hashes, self.cat_list)

        return self.filetype

    def validate(self, name, plugin):
        """Return false if a plugin does not have the correct functions."""

        log = logging.getLogger('Mastiff.Plugins.Validate')

        try:
            callable(plugin.activate)
        except AttributeError:
            log.error("%s missing activate function.", name)
            return False

        try:
            callable(plugin.deactivate)
        except AttributeError:
            log.error("%s missing deactivate function.", name)
            return False

        try:
            callable(plugin.analyze)
        except AttributeError:
            log.error("%s missing analyze function.", name)
            return False

        return True

    def analyze(self, fname=None,  single_plugin=None):
        """Perform analysis on a given filename."""

        log = logging.getLogger('Mastiff.Analysis')

        if fname is None and self.file_name is None:
            log.error("No filename specified. Exiting.")
            sys.exit(1)
        elif fname is not None and self.file_name is None:
            # first time seeing the file, initialize it
            if self.init_file(fname) is None:
                log.error("ERROR accessing file. Exiting.")
                return False

        # set the file_type
        ftype = self.set_filetype()
        log.info('File categories are %s.', self.cat_list)

        if not self.filetype:
            log.error("The file type has not been set. Exiting.")
            sys.exit(1)

        # activate the plugins
        self.activate_plugins(single_plugin)

        for plugin in self.activated_plugins:
            # skip if plugin is not activated
            if plugin.is_activated == False:
                continue

            log.debug('Calling plugin "%s".', plugin.name)
            plugin.plugin_object.analyze(self.config, self.file_name)


        self.config.dump_config()
        log.info('Finished analysis for %s.', self.file_name)

# end class mastiff

