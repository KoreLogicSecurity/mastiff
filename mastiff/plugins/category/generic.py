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
Generic File Category Plugin

File Type: Any files
Purpose:
  This file contains the code for the category class "generic", which
  allows plugins to be created to be run on any file.

Output:
   None

__init__(): MANDATORY: Any initialization code the category requires. It must
            also call the __init__ for the MastiffPlugin class.

is_my_filetype(id_dict, file_name): MANDATORY: This function will return
            the cat_name if the given id_dict pertains to one of the
            file types this category can examine. The file_name is also given
            so additional tests can be performed, if required. None should be
            returned if it does not analyze this type.
"""

__version__ = "$Id$"

import mastiff.plugins.category.categories as categories

class GenericCat(categories.MastiffPlugin):
    """Category class for any file."""

    def __init__(self, name=None):
        """Initialize the category."""
        categories.MastiffPlugin.__init__(self, name)
        self.cat_name = 'Generic'
        self.my_types = []

    def is_my_filetype(self, id_dict, file_name):
        """Generic plugins are run against every file, so always return the
           cat_name."""
        return self.cat_name


if __name__ == '__main__':
    # testing code
    genclass = GenericCat()
    print genclass.cat_name

