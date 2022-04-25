#!/usr/bin/env python
"""
@author: Amber Herold
@contact: appion at scripps.edu
@license: You may use this software as allowed by Apache License 2.0: http://www.apache.org/licenses/LICENSE-2.0.

This StarFile class is responsible for anything that has to do with reading and writing STAR formated files.
The python star file tools avilable freely are somewhat bloated and did not work when tested with Relion output files.
This is not intended to be an all-purpose library for Star files, the goal is effieciency and ease of maintenance.
These are the rules we must follow:
    1. The file name must end in a ".star" extension. (But this class will allow the user to enforce that, just in case they want to change it.)
    2. Each file must have one or more data blocks. The start of a data block is defined by the keyword "data_" followed by an optional string
       for identification (e.g., "data_images").
    3. Multiple values associated with one or more labels in a data block can be arranged in a table using the keyword "loop_" followed
       by the list of labels and columns of values. The values are delimited by whitespace (i.e., blanks, tabs, end-of-lines and carriage returns).
       The loop must be followed by an empty line to indicate its end.
    4. Label names always starts with an underscore ("_"). Each label may only be used once within each data block.
    5. Data items or values can be numeric or strings of characters. A string is interpreted as a single item when it doesn't contain spaces
    6. Comments are strings which can occur in three places:
        File comments: All text before the first "data_" keyword
        Data block comments: Strings on their own lines starting with "#" or with ";" as the first character in the line.
        Item comments: Strings on the same line as and following tag-value items, also indicated by a leading "#".

So we define 4 classes in this file: The StarFile class, DataBlock class,  LoopBlock class and the Label class.

Example of reading an existing star file:
import starFile
star = starFile.StarFile("path/to/starfile")
star.read()
dataBlock = star.getDataBlock("dataBlockName")
loopDict  = dataBlock.getLoopDict() # returns a list with a dictionary for each line in the loop
labelDict = dataBlock.getLabelDict() # returns labels occuring outside a loop in a data block
header    = star.getHeader() # returns any header comments as a string

buildLoopFile() gives an example of creating a simple file with one datablock and one loop.
Similar things can be done to build more complex files.
Example of writing file:
import starFile
labels = ["_first", "_second"]
valueSets = [ "1 2", "3 4", "5 6" ]
star = starFile.StarFile("destination.star")
star.buildLoopFile( "data_mydata", labels, valueSets )
star.write()

The STAR (Self-defining Text Archiving and Retrieval) format (Hall, Allen and Brown, 1991) is for the storage
of label-value pairs for all kinds of input and output metadata. The STAR format is an alternative to XML,
but it is more readable and occupies less space. The STAR format has been adopted by the crystallographic community
in the form of CIF (Crystallographic Information Framework), and Bernard Heymann's BSOFT package was the first to
use STAR in the field of 3D-EM. Also Xmipp-3.0 now uses the STAR format.
"""

import os
import sys

# This is the default file comment that will be written to the top of any star file. It can be modified in the call to the StarFile
# constructor, or by calling StarFile.setFileComments( "new comments" ).
defaultFileComments = \
"""
##########################################################################
# STAR (Self-defining Text Archiving and Retrieval) format
# Generated by Appion for use with Relion and Xmipp programs
#
# Loop blocks begin with the names of columns, followed by data entries
#
##########################################################################
"""

class StarFile():

    def __init__(self, location, comments=defaultFileComments, msg=False):
        """
        @param location: This is a string which is the full path WITH file name for reading and writing
        @param comments: A string that is a comment block. This is used as is, so begin each line with #.
        """
        self.setLocation(location)
        self.dataBlocks = [] # Each file must have one or more data blocks.
        self.fileComments = comments
        self.msg = msg

    def buildLoopFile(self, dataBlockName, loopLabelList, valueSetList):
        """
        To build a simple star file with one data block containing one loop,
        @param dataBlockName: the name of the datablack as a string
        @param loopLabelList: a list containing all the labels as strings with leading underscores (_)
        @param valueSetList: a list of strings that correspond to the loop value entries.
        """
        labels = []
        for name in loopLabelList:
            labels.append(Label(name))

        loopBlock = LoopBlock()
        loopBlock.setLabels(labels)

        for values in valueSetList:
            loopBlock.addValueSet(values.split())

        dataBlock = DataBlock(dataBlockName)
        dataBlock.addLoopBlock(loopBlock)
        self.addDataBlock(dataBlock)

    def setHeader(self, comments=defaultFileComments):
        """
        @param comments: A string that is a comment block. This is used as is, so begin each line with #.
        """
        self.fileComments = comments

    def getHeader(self):
        return self.fileComments

    def setLocation(self, location):
        """
        @param location: This is a string which is the full path WITH file name for reading and writing
        """
        self.location = location

    def addDataBlock(self, dataBlock):
        """
        @param dataBlock: This should be a DataBlock object with any lables or loops already set.
        """
        if dataBlock:
            self.dataBlocks.append(dataBlock)

    def getDataBlock(self, dataBlockName):
        if self.msg is True:
            print("Looking for Data Block named %s..." % dataBlockName)
        for dataBlock in self.dataBlocks:
            if self.msg is True:
                print("\tFound Data Block: %s " % dataBlock.name)
            if dataBlock.name == dataBlockName:
                return dataBlock
        if self.msg is True:
            print("Failed to find Data Block named %s..." % dataBlockName)

    def read(self):
        if not os.path.isfile(self.location):
            raise Exception("Trying to read a star format file that does not exist: %s" % (self.location))
        if self.msg is True:
            print("Reading star format file: %s" % (self.location))

        f           = open(self.location, "r")
        indata      = False # are we inside a data block?
        inloop      = False # are we inside a loop block?
        dataBlock   = None # the current data block that we are reading
        header      = "" # collect any comment lines at the top of the file into this string

        for line in f:
            # remove any junk from the string
            line = line.strip()

            # Start of a comment or file Header
            if line.startswith("#") and not indata and not inloop:
                header += line

            # Start of a new Data Block
            elif line.startswith("data_"):
                # First add the current dataBlock to the File, then create a new one
                self.addDataBlock(dataBlock)
                dataBlock = DataBlock(line)
                indata = True

            # Start of Loop Block
            elif line.startswith("loop_"):
                loopBlock = LoopBlock()
                inloop = True

            # A Label in the current LoopBlock
            elif inloop and line.startswith("_"):
                label = Label(line)
                loopBlock.addLabel(label)

            # A Label in the current DataBlock (outside of any Loop Blocks)
            elif indata and line.startswith("_"):
                label = Label(line)
                dataBlock.addLabel(label)

            # End of Loop Block
            elif inloop and not line:
                dataBlock.addLoopBlock(loopBlock)
                inloop = False

            # Loop Block set of values
            elif inloop and line:
                sline = line.split()
                loopBlock.addValueSet(sline)

        if inloop: # End of file reached
            dataBlock.addLoopBlock(loopBlock)

        f.close()

        # Add the last (or only) data block to the star file
        self.addDataBlock(dataBlock)

        # Save any header comments
        self.setHeader(header)


    def write(self, location=""):
        """
        @param location: allows you to specify a location, overriding the objects own location variable
        """
        if location:
            outpath = location
        else:
            outpath = self.location

        f = open(outpath, 'w')
        f.write(self.fileComments)

        # add each data block that is defined for this file
        for dataBlock in self.dataBlocks:
            f.write(dataBlock.toString())

        f.close()



class DataBlock():
    """
    The start of a data block is defined by the keyword "data_" followed by an optional string for identification (e.g., "data_images")
    Next there can be a list of Labels and any number of Loop Blocks.
    """
    def __init__(self, name=""):
        self.setName(name)
        self.labels = [] # contains a list of all the Labels for this data block (each must be a Label object)
        self.loopBlocks = [] # an array of all the loop sections that make up this star file

    def setName(self, name):
        if not name.startswith("data_"):
            raise Exception("The name of a STAR file Data Block must begin with 'data_'.")
        self.name = name

    def setLoopBlocks(self, loopBlocks):
        self.loopBlocks = loopBlocks

    def addLoopBlock(self, loopBlock):
        self.loopBlocks.append(loopBlock)

    # Each label may only be used once within each data block.
    def addLabel(self, label):
        if label.name in (existingLabel.name for existingLabel in self.labels):
            raise Exception("Trying to add a duplicate Label to a STAR file data block: %s" % label.name)
        self.labels.append(label)

    def toString(self):
        # Start of data section
        outString = "\n" + self.name + "\n\n"

        # Add labels
        outString += '\n'.join(label.toString() for label in self.labels)
        outString += '\n'

        # Add loop blocks, converting each loop block to a string first with a generator expression
        outString += '\n'.join(loopBlock.toString() for loopBlock in self.loopBlocks)

        # End of Data Block section indicated by an empty line
        outString += '\n'
        return outString


    def getLoopDict(self, loopId=0):
        """
        Returns a list of dictionaries of the loop values like so:
        datadict = { [[label[0].name, valueSet[0][0]], [label[1].name, valueSet[0][1]], [label[2].name, valueSet[0][2]],...
                     [[label[0].name, valueSet[1][0]], [label[1].name, valueSet[1][1]], [label[2].name, valueSet[1][2]],...
                     [[label[0].name, valueSet[2][0]], [label[1].name, valueSet[2][1]], [label[2].name, valueSet[2][2]],...
                   }
        """
        if self.loopBlocks:
            dataDict =  self.loopBlocks[loopId].createDataDict()
        return dataDict

    def getLabelDict(self):
        """
        Returns a dictionary of key/value pairs where the labels listed in the data block (but not inside a loop block)
        are the keys. If there is a value on the same line as the label that is not a comment, it is saved as the value
        in this dictionary.
        """
        dataDict = {}
        if self.labels:
            for label in self.labels:
                dataDict[label.name] = label.value
        return dataDict



class LoopBlock():
    """
    Multiple values associated with one or more labels in a data block can be arranged in a table using the keyword "loop_" followed
           by the list of labels and columns of values. The values are delimited by whitespace (i.e., blanks, tabs, end-of-lines and carriage returns).
           The loop must be followed by an empty line to indicate its end.
    Label names always starts with an underscore ("_").
    """
    def __init__(self):
        self.labels = [] # contains a list of all the Labels for this loop section (each must be a Label object)
        self.valueSets = [] # contains an entry for each line of values in the loop block

    def setLabels(self, labels):
        for label in labels:
            self.addLabel(label)

    # Each label may only be used once within each data block.
    def addLabel(self, label):
        if label.name in (existingLabel.name for existingLabel in self.labels):
            raise Exception("Trying to add a duplicate Label to a STAR file loop block: %s" % label.name)
        self.labels.append(label)

    # add a list of value sets that correspond to the label list
    def addValueSet(self, values):
        self.valueSets.append(values)

    def toString(self):
        # start of loop section
        outString = "\n\nloop_\n"

        # Add labels
        outString += '\n'.join(label.toString() for label in self.labels)
        outString += '\n'

        # Add values
        for valueSet in self.valueSets:
            # separate by whitespace
            outString += '\t'.join(valueSet)
            outString += '\n'

        # End of loop section is indicated by an empty line
        outString += '\n\n'
        return outString

    def createDataDict(self):
        """
        This returns a list of dictionaries. Each value set is an entry in the list and is added as a dictionary.
        datadict = { [[label[0].name, valueSet[0][0]], [label[1].name, valueSet[0][1]], [label[2].name, valueSet[0][2]],...
                 [[label[0].name, valueSet[1][0]], [label[1].name, valueSet[1][1]], [label[2].name, valueSet[1][2]],...
                 [[label[0].name, valueSet[2][0]], [label[1].name, valueSet[2][1]], [label[2].name, valueSet[2][2]],...
               }

        The first label in the labels list corresponds to the first value in the valueSet. Second label to second value and so on.
        """
        dataTree = []

        # add a dictionary to the data tree for each value set entry
        for valueSet in self.valueSets:
            index = 0
            valueSetDict = {}
            for label in self.labels:
                valueSetDict[label.name] = valueSet[index]
                index = index + 1

            # Append the dict for this set of values to the tree
            dataTree.append(valueSetDict)

        return dataTree


class Label():
    """
    The Label class is basically a structure for the labels that belong to a Loop Block.
    Each label has a name, value and comment. The value and comment fields are optional.
    Comments are indicated by a leading "#".
    They show up when doing things like this:
    _rlnAngleRot #1
    _rlnAngleTilt #2
    _rlnTiltAngleLimit                       -91.000000
    _rlnPsiStep                               15.000000

    If the name parameter in the constructor is passed as a sting like this:
    _rlnTiltAngleLimit -91.000000 #1
    The name, value and comment will be parsed and set accordingly.
    Initialize a label with a string in the format _name value #comment
    """

    def __init__(self, labelLine):
        self.setName(labelLine)
        self.comment = ''
        self.value = ''

        # Parse the name to see if it includes a comment or value
        labelLine = labelLine.strip()
        slabelLine = labelLine.split()

        for item in slabelLine:
            if item.startswith("_"):
                self.name = item
            elif item.startswith('#'):
                self.comment = item
            else:
                self.value = item

    def setName(self, name):
        if not name.startswith("_"):
            raise Exception("Trying to add a label to a STAR file loop block that does not begin with and underscore. Labels must begin with underscore.")
        self.name = name

    def setValue(self, value):
        self.value = value

    def setComment(self, comment):
        self.comment = comment

    def toString(self):
        outString = self.name + "\t" + self.value + "\t" + self.comment
        return outString


#################################################################
#
# EXAMPLES
#
#################################################################
"""
Example of reading an existing star file:
import starFile
star = starFile.StarFile("path/to/starfile")
star.read()
dataBlock = star.getDataBlock("dataBlockName")
loopDict  = dataBlock.getLoopDict() # returns a list with a dictionary for each line in the loop
labelDict = dataBlock.getLabelDict() # returns labels occuring outside a loop in a data block
header    = star.getHeader() # returns any header comments as a string
"""


