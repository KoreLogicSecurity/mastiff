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
Windows Executable File Category Plugin

File Type: Windows Executable Programs
Purpose:
  This file contains the code for the category class "exe", which
  allows plugins to be created to be run on Windows executable files.

Output:
   None

__init__(): MANDATORY: Any initialization code the category requires. It must
            also call the __init__ for the MastiffPlugin class.

is_my_filetype(id_dict, file_name): MANDATORY: This function will return
            the cat_name if the given id_dict contains one of the
            file types this category can examine, or the yara rule matches the
            file type. The file_name is also given so additional tests can be
            performed, if required. None should be returned if it does not 
            analyze this type.
"""

__version__ = "$Id$"

import struct
import mastiff.plugins.category.categories as categories
import mastiff.filetype as FileType

class EXECat(categories.MastiffPlugin):
    """Category class for Windows executables."""

    def __init__(self, name=None):
        """Initialize the category."""
        categories.MastiffPlugin.__init__(self, name)
        self.cat_name = 'EXE'
        self.my_types = [ 'PE32 executable',
                          'MS-DOS executable',
                          'Win32 Executable',
                          'Win32 EXE'
                          ]
        self.yara_filetype = """rule isexe {
	    strings:
		    $MZ = "MZ"        
	    condition:
		    $MZ at 0 and uint32(uint32(0x3C)) == 0x00004550
        }"""	

    def is_exe(self, filename):
        """ Look to see if the filename has the header format we expect,"""

        with open(filename, 'rb') as exe_file:
            header = exe_file.read(2)
            if header != 'MZ':
                return False

            exe_file.seek(0x3c)
            offset =  struct.unpack('<i',  exe_file.read(4))
            if offset[0] > 1024:
                # seems a bit too far - we'll stop just in case
                return False

            exe_file.seek(offset[0])
            pe_header = exe_file.read(2)
            if pe_header != 'PE':
                return False

        return True

    def is_my_filetype(self, id_dict, file_name):
        """Determine if magic string is appropriate for this category."""

        # check magic string first
        if [ type_ for type_ in self.my_types if type_ in id_dict['magic']]:
            return self.cat_name

        # run Yara type check
        if FileType.yara_typecheck(file_name, self.yara_filetype) is True:
            return self.cat_name

        # perform a manual check
        if self.is_exe(file_name):
            return self.cat_name

        return None

