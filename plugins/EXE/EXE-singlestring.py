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
Single-byte string plug-in

Plugin Type: EXE
Purpose:

Attackers have begun to obfuscate embedded strings by moving a single byte
at a time into a character array. In assembler, it looks like:

mov mem, 0x68
mov mem+4, 0x69
mov mem+8, 0x21
...

Using a strings program, these strings will not be found. This script looks
for any strings embedded in this way and prints them out.  It does this by
looking through the file for C6 opcodes, which are the start of the
"mov mem/reg, imm" instruction.  It will then decode it, grab the value and
create a string from it.

Requirements:
- distorm3 (http://code.google.com/p/distorm/)

Output:
   None

"""

__version__ = "$Id$"

import logging
import re
import os

try:
    from distorm3 import Decode, Decode32Bits
except ImportError, err:
    print "EXE-SingleString: Could not import distorm3: %s" % error
    
import mastiff.category.exe as exe

# Change the class name and the base class
class SingleString(exe.EXECat):
    """Extract single-byte strings from an executable."""

    def __init__(self):
        """Initialize the plugin."""
        exe.EXECat.__init__(self)
        self.length = 3
        self.raw = False

    def activate(self):
        """Activate the plugin."""
        exe.EXECat.activate(self)

    def deactivate(self):
        """Deactivate the plugin."""
        exe.EXECat.deactivate(self)

    def findMov(self, filename):
        """ look through the file for any c6 opcode (mov reg/mem, imm)
        when it finds one, decode it and put it into a dictionary """
        #log = logging.getLogger('Mastiff.Plugins.' + self.name + '.findMov')

        f = open(filename,'rb')
        offset = 0        
        instructs = {}

        mybyte = f.read(1)

        while mybyte:
            if mybyte == "\xc6":
                # found a mov op - decode and record it
                f.seek(offset)
                mybyte = f.read(16)
                # p will come back as list of (offset, size, instruction, hexdump)
                p = Decode(offset, mybyte, Decode32Bits)

                # break up the mnemonic
                ma = re.match('(MOV) ([\S\s]+), ([x0-9a-fA-F]+)', p[0][2])
                if ma is not None:
                    instructs[offset] = [ma.group(1), ma.group(2), ma.group(3), p[0][1]] # mnemonic, size

                #log.debug( "MOV instructions detected: %x %s %d" % (offset,p[0][2],p[0][1]) )

                f.seek(offset+1)

            mybyte = f.read(1)
            offset = offset + 1

        f.close()
        return instructs

    def decodeBytes(self, instructs):
        """ Take in a dict of instructions - parse through each instruction and grab the strings """
        #log = logging.getLogger('Mastiff.Plugins.' + self.name + '.decodeBytes')

        curString = ""
        curOffset = 0
        strList = []
        usedBytes = []

        for off in sorted(instructs.keys()):

            if off not in usedBytes:
                # set up the new offset if needed
                if curOffset == 0:
                    curOffset = off

                while off in instructs:
                    usedBytes.append(off)
                    hexVal = int(instructs[off][2], 16)
                    opLen = instructs[off][3]

                    # is hexVal out of range?
                    if hexVal < 32 or hexVal > 126 and (hexVal != 10 or hexVal != 13 or hexVal != 9):
                        # end of string
                        #log.debug("%x non-string char - new string: %d: %s" % (curOffset, hexVal,curString))
                        strList.append([curOffset, curString])
                        curOffset = off + opLen
                        curString = ""
                    else:
                        #add to string
                        if not self.raw and hexVal == 10:
                            # line feed
                            curString = curString + "\\r"
                        elif not self.raw and hexVal == 13:
                            # return
                            curString = curString + "\\n"
                        elif not self.raw and hexVal == 9:
                            # tab
                            curString = curString + "\\t"
                        else:
                            curString = curString + chr(hexVal)

                    off = off + opLen

                strList.append([curOffset, curString])
                curOffset = 0
                curString = ""

            usedBytes.append(off)

        return strList

    def analyze(self, config, filename):
        """Analyze the file."""

        # sanity check to make sure we can run
        if self.is_activated == False:
            return False
        log = logging.getLogger('Mastiff.Plugins.' + self.name)
        log.info('Starting execution.')

        self.length = config.get_var(self.name, 'length')
        if self.length is None:
            self.length = 3

        self.raw = config.get_bvar(self.name, 'raw')

        # find the bytes in the file
        instructs = self.findMov(filename)

        # now lets get the strings
        strlist = self.decodeBytes(instructs)

        self.output_file(config.get_var('Dir','log_dir'), strlist)

        return True

    def output_file(self, outdir, strlist):
        """Print output from analysis to a file."""
        log = logging.getLogger('Mastiff.Plugins.' + self.name + '.output_file')

        # if the string is of the right len, print it
        outstr = ""
        for string in strlist:
            if len(string[1]) >= int(self.length):
                outstr = outstr + '0x%x: %s\n' % (string[0], string[1])

        if len(outstr) > 0:
            try:
                outfile = open(outdir + os.sep + 'single-string.txt', 'w')
            except IOError, err:
                log.debug("Cannot open single-string.txt: %s" % err)
                return False

            outfile.write(outstr)
            outfile.close()
        else:
            log.debug('No single-byte strings found.')

        return True

