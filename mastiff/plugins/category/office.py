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
Microsoft Office File Category Plugin

File Type: Microsoft Office Documents
Purpose:
  This file contains the code for the category class "office", which
  allows plugins to be created to be run on Microsoft Office documents.

Output:
   None

__init__(): MANDATORY: Any initialization code the category requires. It must
            also call the __init__ for the MastiffPlugin class.
"""

__version__ = "$Id$"

import mastiff.plugins.category.categories as categories
import mastiff.filetype as FileType

class OfficeCat(categories.MastiffPlugin):
    """Category class for Microsoft Office files."""

    def __init__(self, name=None):
        """Initialize the category."""
        categories.MastiffPlugin.__init__(self, name)
        self.cat_name = 'Office'
        self.my_types = [ 'CDF V2 Document', # PPT, DOC, XLS
                         'Composite Document File V2',
                          'Microsoft Word',
                          'Microsoft Office Word',
                          'Microsoft Excel',
                          'Microsoft PowerPoint',
                          'Microsoft Office Document'
                          ]
        self.yara_filetype = """rule isOleDoc {
	    condition:
		    ( uint32(0x0) == 0xe011cfd0 and uint32(0x4) == 0xe11ab1a1 ) or
		    // some old beta versions have this signature
		    ( uint32(0x0) == 0x0dfc110e and uint32(0x4) == 0x0e11cfd0 )
        }"""

    def is_my_filetype(self, id_dict, file_name):
        """Determine if magic string is appropriate for this category."""

        try:
            if [ type_ for type_ in self.my_types if type_ in id_dict['magic']]:
                return self.cat_name
        except:
            return None

        # run Yara type check
        if FileType.yara_typecheck(file_name, self.yara_filetype) is True:
            return self.cat_name

        return None

