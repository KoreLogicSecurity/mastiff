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
Adobe PDF Category Plugin

File Type: Adobe PDF files
Purpose:
  This file contains the code for the category class "pdf", which
  allows plugins to be created to be run on any file.

Output:
   None

__init__(): MANDATORY: Any initialization code the category requires. It must
            also call the __init__ for the MastiffPlugin class.
"""

__version__ = "$Id$"

import mastiff.category.categories as categories

class PDFCat(categories.MastiffPlugin):
    """Category class for Adobe PDFs."""

    def __init__(self, name=None):
        """Initialize the category."""
        categories.MastiffPlugin.__init__(self, name)
        self.cat_name = 'PDF'
        self.my_types = [ 'PDF document',
                                    'Adobe Portable Document Format' ]

    def is_my_filetype(self, id_dict, file_name):
        """Determine if magic string is appropriate for this category."""

        # check the magic string for our file type
        if [ type_ for type_ in self.my_types if type_ in id_dict['magic'] ]:
            return self.cat_name

        # check TrID output
        for (percent, desc) in id_dict['trid']:
            for type_ in self.my_types:
                # make sure percent is high enough and trid string matches
                if type_ in desc and percent > 50:
                    return self.cat_name

        # the PDF header may be in the first 1024 bytes of the file
        # libmagic and TrID may not pick this up
        with open(file_name,  'r') as pdf_file:
            data = pdf_file.read(1024)

        if '%PDF-' in data:
            return self.cat_name

        return None

