#!/usr/bin/env python
#
# file: $NEDC_NFC/class/python/nedc_sys_tools/nedc_file_tools.py
#
# revision history:
#
# 20250318 (JP): reviewed and refactored
# 20250316 (DH): added a class to deal with temp files
# 20240806 (DH): added new constants used in eeg/dpath ann tools
# 20240716 (JP): refactored after the rewrite of ann_tools
# 20240621 (JP): added other is methods from ann_tools
# 20240420 (JP): added is_raw
# 20230710 (SM): modified load_parameters to accept lists
# 20230621 (AB): refactored code to new comment style
# 20220225 (PM): added extract_comments function
# 20200623 (JP): reorganized
# 20200609 (JP): refactored the code and added atof and atoi
# 20170716 (JP): Upgraded to using the new annotation tools.
# 20170709 (JP): generalized some functions and abstracted more file I/O
# 20170706 (NC): refactored eval_tools into file_tools and display_tools
# 20170611 (JP): updated error handling
# 20170521 (JP): initial version
#
# usage:
#  import nedc_file_tools as nft
#
# This class contains a collection of functions that deal with file handling
#------------------------------------------------------------------------------
#
# imports are listed here
#
#------------------------------------------------------------------------------

# import system modules
#
import errno
import os
import re
import sys
try:
    import tomllib
except ImportError:
    import tomli as tomllib
import tempfile
import shutil
import atexit
import signal

# import NEDC modules
#
import nedc_debug_tools as ndt

#------------------------------------------------------------------------------
#
# global variables are listed here
#
#------------------------------------------------------------------------------

# set the filename using basename
#
__FILE__ = os.path.basename(__file__)

# set the default character encoding system
#
DEF_CHAR_ENCODING = "utf-8"

# file processing character constants
#
DELIM_BLANK = '\x00'
DELIM_BOPEN = '{'
DELIM_BCLOSE = '}'
DELIM_CARRIAGE = '\r'
DELIM_CLOSE = ']'
DELIM_COLON = ':'
DELIM_COMMA = ','
DELIM_COMMENT = '#'
DELIM_DASH = '-'
DELIM_DOT = '.'
DELIM_EQUAL = '='
DELIM_GREATTHAN = '>'
DELIM_LESSTHAN = '<'
DELIM_NEWLINE = '\n'
DELIM_NULL = ''
DELIM_OPEN = '['
DELIM_QUOTE = '"'
DELIM_SEMI = ';'
DELIM_SLASH = '/'
DELIM_SPACE = ' '
DELIM_SQUOTE = '\''
DELIM_TAB = '\t'
DELIM_USCORE = '_'

# define default file extensions
#
DEF_EXT_CSV = "csv"
DEF_EXT_CSVBI = "csv_bi"
DEF_EXT_DAT = "dat"
DEF_EXT_EDF = "edf"
DEF_EXT_HEA = "hea"
DEF_EXT_JPG = "jpg"
DEF_EXT_LBL = "lbl"
DEF_EXT_PNG = "png"
DEF_EXT_REC = "rec"
DEF_EXT_SVS = "svs"
DEF_EXT_TIF = "tif"
DEF_EXT_TXT = "txt"
DEF_EXT_XML = "xml"

# define common reference keys for EEG annotations
#
DEF_BNAME = "bname"
DEF_DURATION = "duration"
DEF_MONTAGE = 'montage'
DEF_MONTAGE_FILE = "montage_file"
DEF_SCHEMA = 'schema'
DEF_VERSION = "version"

# define common reference keys for DPATH annotations
#
DEF_REGION_ID = 'region_id'
DEF_TEXT = 'text'
DEF_COORDINATES = 'coordinates'
DEF_CONFIDENCE = 'confidence'
DEF_TISSUE_TYPE = 'tissue_type'
DEF_MICRON_LENGTH = 'LengthMicrons'
DEF_MICRON_AREA = 'AreaMicrons'
DEF_LENGTH = 'Length'
DEF_AREA = 'Area'
DEF_GEOM_PROPS = "geometric_properties"
DEF_TISSUE = 'tissue'
DEF_HEIGHT = 'height'
DEF_WIDTH = 'width'
DEF_MICRONS = 'MicronsPerPixel'

# file version constants
#
PFILE_VERSION = "param_v1.0.0"
CSV_VERSION = "csv_v1.0.0"
LBL_VERSION = 'lbl_v1.0.0'
TSE_VERSION = 'tse_v1.0.0'
XML_VERSION = '1.0'

# define file type names
#
CSV_NAME = "csv"
LBL_NAME = "lbl"
TSE_NAME = "tse"
XML_NAME = "xml"

# define constants for term based representation in eeg dictionaries
#
DEF_TERM_BASED_IDENTIFIER = "TERM"

# regular expression constants
#
DEF_REGEX_ASSIGN_COMMENT = '^%s([a-zA-Z:!?" _-]*)%s(.+?(?=\n))'

# file processing string constants
#
STRING_EMPTY = ""
STRING_DASHDASH = "--"

# file processing lists:
#  used to accelerate some functions
#
LIST_SPECIALS = [DELIM_SPACE, DELIM_BLANK]

# i/o constants
#
MODE_APPEND_TEXT = "a"
MODE_READ_TEXT = "r"
MODE_READ_BINARY = "rb"
MODE_READ_WRITE_BINARY = "rb+"
MODE_WRITE_TEXT = "w"
MODE_WRITE_BINARY = "wb"

# define constants for XML tags
#
DEF_XML_HEIGHT = "height"
DEF_XML_WIDTH = "width"
DEF_XML_CONFIDENCE = "confidence"
DEF_XML_COORDS = "coordinates"
DEF_XML_REGION_ID = "region_id"
DEF_XML_TEXT = "text"
DEF_XML_TISSUE_TYPE = "tissue_type"
DEF_XML_LABEL = "label"

# define a constant to identify seizure annotations
#
DEF_CLASS = "seiz"

# define constants associated with the eeg Csv class
#
DELIM_CSV_LABELS = "channel,start_time,stop_time,label,confidence"

# define constants associated with the eeg Xml class
#
XML_TAG_ANNOTATION_LABEL_FILE = "annotation_label_file"
XML_TAG_CHANNEL_PATH = "label/montage_channels/channel"
XML_TAG_CHANNEL = "channel"
XML_TAG_EVENT = "event"
XML_TAG_ENDPOINTS = "endpoints"
XML_TAG_LABEL = "label"
XML_TAG_MONTAGE_CHANNELS = "montage_channels"
XML_TAG_NAME = "name"
XML_TAG_PROBABILITY = "probability"
XML_TAG_MONTAGE_FILE = "montage_file"
XML_TAG_MONTAGE_TAG = "montage_tag"
XML_TAG_ROOT = "root"

# define constants associated with the eeg lbl class
#
DEF_LBL_NUM_LEVELS = 'number_of_levels'
DEF_LBL_LEVEL = 'level'
DEF_LBL_SYMBOL = 'symbols'
DEF_LBL_LABEL = 'label'

# define file format string for duration information
#
FMT_SECS = "secs"

# define the essential components of a CSV file
#
FMT_CSV_VERSION = "# version = %s"
FMT_CSV_BNAME = "# bname = %s"
FMT_CSV_DURATION = "# duration = %0.4f secs"
FMT_CSV_MONTAGE = "# montage_file = %s"

# define the essential components of an XML file:
#  note that this format is hardcoded into an XML file
#
FMT_XML_VERSION = "<?xml version="

# define number constants related to string processing
#
DEF_LWIDTH = int(79)

# define the number of bytes to read to check for a raw file
#
FLIST_BSIZE = int(32768)

# define the number of bytes to read to check for an edf file
#
EDF_VERS_BSIZE = int(8)
EDF_VERS = b"0       "

# define some important ml constants
#
ML_TRAIN = "train"
ML_DEV = "dev"
ML_EVAL = "eval"
DEVICE_TYPE_CPU = "cpu"
DEVICE_TYPE_GPU = "gpu"

# declare a global debug object so we can use it in functions
#
dbgl_g = ndt.Dbgl()

#------------------------------------------------------------------------------
#
# functions listed here: general string processing
#
#------------------------------------------------------------------------------

def trim_whitespace(istr):
    """
    function: trim_whitespace

    arguments:
     istr: input string

    return:
     an output string that has been trimmed

    description:
     This function removes leading and trailing whitespace.
     It is needed because text fields in Edf files have all
     sorts of junk in them.
    """

    # display informational message
    #
    if dbgl_g == ndt.FULL:
        print("%s (line: %s) %s: trimming (%s)" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__, istr))

    # declare local variables
    #
    last_index = len(istr)

    # find the first non-whitespace character
    #
    flag = False
    for i in range(last_index):
        if not istr[i].isspace():
            flag = True
            break

    # make sure the string is not all whitespace
    #
    if flag == False:
        return STRING_EMPTY

    # find the last non-whitespace character
    #
    for j in range(last_index - 1, -1, -1):
        if not istr[j].isspace():
            break

    # exit gracefully: return the trimmed string
    #
    return istr[i:j+1]
#
# end of function

def first_substring(strings, substring):
    """
    function: first_substring

    arguments:
     strings: list of strings (input)
     substring: the substring to be matched (input)

    return:
     the index of the match in strings
     none

    description:
     This function finds the index of the first string in strings that
     contains the substring. This is similar to running strstr on each
     element of the input list.
    """
    try:
        return next(i for i, string in enumerate(strings) if \
                    substring in string)
    except:
        return int(-1)
#
# end of function

def first_string(strings, tstring):
    """
    function: first_string

    arguments:
     strings: list of strings (input)
     substring: the string to be matched (input)

    return:
     the index of the match in strings
     none

    description:
     This function finds the index of the first string in strings that
     contains an exact match. This is similar to running strstr on each
     element of the input list.
    """
    try:
        return next(i for i, string in enumerate(strings) if \
                    tstring == string)
    except:
        return int(-1)
#
# end of function

# function: atoi
#
# arguments:
#  value: the value to be converted as a string
#
# return: an integer value
#
# This function emulates what C++ atoi does by replacing
# null characters with spaces before conversion. This allows
# Python's integer conversion function to work properly.
#
def atoi(value):
    """
    function: atoi

    arguments:
     none
     none

    return:
     none
     none

    description:
     none
     none
     none
    """
    # display informational message
    #
    if dbgl_g == ndt.FULL:
        print("%s (line: %s) %s: converting value (%s)" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__, value))

    # replace all the null's with spaces:
    #  this code is complicated but can be found here:
    #   https://stackoverflow.com/a/30020228
    #
    ind = (min(map(lambda x: (value.index(x)
                              if (x in value) else len(value)),
                   LIST_SPECIALS)))
    tstr = value[0:ind]

    # try to convert the input
    #
    try:
        ival = int(tstr)
    except:
        print("Error: %s (line: %s) %s: string conversion error [%s][%s])" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__, value, tstr))
        return None

    # exit gracefully
    #
    return ival
#
# end of function

def atof(value):
    """
    function: atof

    arguments:
     value: the value to be converted as a string

    return:
     an integer value

    description:
     This function emulates what C++ atof does by replacing
     null characters with spaces before conversion. This allows
     Python's integer conversion function to work properly.
    """

    # display informational message
    #
    if dbgl_g == ndt.FULL:
        print("%s (line: %s) %s: converting value (%s)" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__, value))

    # replace all the null's with spaces:
    #  this code is complicated but can be found here:
    #   https://stackoverflow.com/a/30020228
    #
    ind = (min(map(lambda x: (value.index(x)
                              if (x in value) else len(value)),
                   LIST_SPECIALS)))
    tstr = value[0:ind]

    # try to convert the input
    #
    try:
        fval = float(tstr)
    except:
        print("Error: %s (line: %s) %s: string conversion error [%s][%s])" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__, value, tstr))
        return None

    # exit gracefully
    #
    return fval
#
# end of function

#------------------------------------------------------------------------------
#
# functions listed here: manipulate filenames, lists and command line args
#
#------------------------------------------------------------------------------

def get_fullpath(path):
    """
    function: get_fullpath

    arguments:
     path: path to directory or file

    return:
     the full path to directory/file path argument

    description:
     This function returns the full pathname for a file. It expands
     environment variables.
    """

    # display informational message
    #
    if dbgl_g == ndt.FULL:
        print("%s (line: %s) %s: expanding name (%s)" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__, path))

    # exit gracefully
    #
    return os.path.abspath(os.path.expanduser(os.path.expandvars(path)))
#
# end of function

def create_filename(iname, odir, oext, rdir, cdir = False):
    """
    function: create_filename

    arguments:
     iname: input filename (string)
     odir: output directory (string)
     oext: output file extension (string)
     rdir: replace directory (string)
     cdir: create directory (boolean - true means create the directory)

    return:
     the output filename

    description:
     This function creates an output file name based on the input arguments. It
     is a Python version of Edf::create_filename().
    """

    # display informational message
    #
    if dbgl_g == ndt.FULL:
        print("%s (line: %s) %s: creating (%s)" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__, iname))

    # get absolute file name
    #
    abs_name = os.path.abspath(os.path.realpath(os.path.expanduser(iname)))

    # replace extension with ext
    #
    if oext is None:
        ofile = os.path.join(os.path.dirname(abs_name),
                             os.path.basename(abs_name))
    else:
        ofile = os.path.join(os.path.dirname(abs_name),
                             os.path.basename(abs_name).split(DELIM_DOT)[0]
                             + DELIM_DOT + oext)

    # get absolute path of odir:
    #  if odir is None, use the input file's path (strip the filename)
    #
    if odir is None:
        odir = os.path.dirname(iname)
    else:
        odir = os.path.abspath(os.path.realpath(os.path.expanduser(odir)))

    # if the replace directory is valid and specified
    #
    if rdir is not None and rdir in ofile:

        # get absolute path of rdir
        #
        rdir = os.path.abspath(os.path.realpath(
            os.path.expanduser(rdir)))

        # replace the replace directory portion of path with
        # the output directory
        #
        ofile = ofile.replace(rdir, odir)

    # if the replace directory is not valid or specified
    #
    else:

        # append basename of ofile to output directory
        #
        ofile = os.path.join(odir, os.path.basename(ofile))

    # create the directory if necessary
    #
    if cdir is True:
       if make_dir(odir) is False:
           print("Error: %s (line: %s) %s: make dir failed (%s)" %
                 (__FILE__, ndt.__LINE__, ndt.__NAME__, odir))
           sys.exit(os.EX_SOFTWARE)

    # exit gracefully
    #
    return ofile
#
# end of function

def concat_names(odir, fname):
    """
    function: concat_names

    arguments:
     odir: the output directory that will hold the file
     fname: the output filename

    return:
     fname: a filename that is a concatenation of odir and fname
     none

    description:
     none
     none
     none
    """

    # display informational message
    #
    if dbgl_g == ndt.FULL:
        print("%s (line: %s) %s: concatenating (%s %s)" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__, odir, fname))

    # strip any trailing slashes
    #
    str = odir
    if str[-1] == DELIM_SLASH:
        str = str[:-1]

    # ceate the full pathname
    #
    new_name = str + DELIM_SLASH + fname

    # exit gracefully
    #
    return new_name
#
# end of function

def get_flist(fname):
    """
    function: get_flist

    arguments:
     fname: full pathname of a filelist file

    return:
     flist: a list of filenames

    description:
     This function opens a file and reads filenames. It ignores comment
     lines and blank lines.
    """

    # display informational message
    #
    if dbgl_g == ndt.FULL:
        print("%s (line: %s) %s: opening (%s)" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__, fname))

    # declare local variables
    #
    flist = []

    # open the file
    #
    try:
        fp = open(fname, MODE_READ_TEXT)
    except IOError:
        print("Error: %s (line: %s) %s: file not found (%s)" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__, fname))
        return None

    # iterate over lines
    #
    try:
        for line in fp:

            # remove spaces and newline chars
            #
            line = line.replace(DELIM_SPACE, DELIM_NULL) \
                       .replace(DELIM_NEWLINE, DELIM_NULL) \
                       .replace(DELIM_TAB, DELIM_NULL)

            # check if the line starts with comments
            #
            if line.startswith(DELIM_COMMENT) or len(line) == 0:
                pass
            else:
                flist.append(line)
    except:
        flist = None

    # close the file
    #
    fp.close()

    # exit gracefully
    #
    return flist
#
# end of function

def make_fp(fname):
    """
    function: make_fp

    arguments:
     fname: the filename
     none

    return:
     fp: a file pointer
     none

    description:
     none
    """

    # display informational message
    #
    if dbgl_g == ndt.FULL:
        print("%s (line: %s) %s: creating (%s)" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__, fname))

    # open the file
    #
    try:
        fp = open(fname, MODE_WRITE_TEXT)
    except:
        print("Error: %s (line: %s) %s: error opening file (%s)" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__, fname))
        return None

    # exit gracefully
    #
    return fp
#
# end of function

#------------------------------------------------------------------------------
#
# functions listed here: general functions that determine file type
#
#------------------------------------------------------------------------------

def is_edf(fname):
    """
    method: is_edf

    arguments:
     fname: path to edf file

    return:
     True if file is an edf file

    description:
     This method looks at the beginning 8 bytes of the edf file, and decides
     if the file is an edf file.
    """

    # display debug information
    #
    if dbgl_g > ndt.BRIEF:
        print("%s (line: %s) %s: checking for an edf file (%s)" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__, fname))

    # open the file
    #
    fp = open(fname, MODE_READ_BINARY)
    if fp is None:
        print("Error: %s (line: %s) %s: error opening file (%s)" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__, fname))
        return False

    # make sure we are at the beginning of the file and read
    #
    fp.seek(0, os.SEEK_SET)
    barray = fp.read(EDF_VERS_BSIZE)

    # close the file and reset the pointer
    #
    fp.close()

    # exit gracefully:
    #  if the beginning of the file contains the magic sequence
    #  then it is an edf file
    #
    if barray == EDF_VERS:
        return True
    else:
        return False
#
# end of function

def is_raw(fname):
    """
    method: is_raw

    arguments:
     fname: path to a file

     return:
      True if file is a raw file

    description:
     This method looks at the beginning of the edf file, and decides
     if the file is a raw or text based on the values.
     """

    # display debug information
    #
    if dbgl_g > ndt.BRIEF:
        print("%s (line: %s) %s: checking for a raw file (%s)" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__, fname))

    # open the file
    #
    fp = open(fname, MODE_READ_BINARY)
    if fp is None:
        print("Error: %s (line: %s) %s::%s: error opening file (%s)" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__, fname))
        return False

    # make sure we are at the beginning of the file and read
    #
    fp.seek(0, os.SEEK_SET)
    barray = fp.read(FLIST_BSIZE)
    fp.close()

    # check if the decimal value is outside the range of [0, 127]
    #
    for val in barray:
        if int(val) < 0 or int(val) > 127:
            return True

    # exit gracefully - it is most likely a text file
    #
    return False
#
# end of function

def is_hea(hfile):
    """
    method: is_hea

    arguments:
     fname: the input header filename

    returns:
     a boolean value indicating status

    description:
     This method checks if a file is a header file.
     """

    # display debug message
    #
    if dbgl_g > ndt.BRIEF:
        print("%s (line: %s) %s: checking for a header file (%s)" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__, fname))

    # open the file
    #
    fp = open(hfile, MODE_READ_TEXT)
    if fp is None:
        print("Error: %s (line: %s) %s: error opening (%s)" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__, hname))
        return None

    # grab and the first line
    #
    parts = fp.readline().split()

    # grab the number of channels
    #
    try:
        num_channels = int(parts[1])
    except:
        fp.close()
        return False

    # count the number of remaining lines
    #
    nl = int(0)
    while fp.readline():
        nl += int(1)

    # close the file
    #
    fp.close()

    # display debug message
    #
    if dbgl_g > ndt.BRIEF:
        print("%s (line: %s) %s: done checking for a header file" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__))

    # exit gracefully
    #
    if nl != num_channels:
        return False
    else:
        return True
#
# end of function

# declare the file type checking functions
#
def is_ann(fname):
    """
    function: is_ann

    arguments:
     fname: an ann filename

    return:
     a boolean value indicating status

    description:
     This method checks if a file is a valid annotation file.
    """

    # display debug information
    #
    if dbgl_g > ndt.BRIEF:
        print("%s (line: %s) %s: checking for an ann file (%s)" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__, fname))

    # attempt to determine file type
    #
    try:

        # check the list of known types
        #
        if is_tse(fname):
            return True
        elif is_lbl(fname):
            return True
        elif is_csv(fname):
            return True
        elif is_xml(fname):
            return True

    # if an error occurs due to utf encoding
    # return false as all annotation files
    # are text files
    #
    except:

        return False

    # exit ungracefully: not a valid annotation file type
    #
    return False
#
# end of function

def is_tse(fname):
    """
    function: is_tse

    arguments:
     fname: an tse filename

    return:
     a boolean value indicating status

    description:
     This method checks if a file is a tse file.
    """

    # display debug information
    #
    if dbgl_g > ndt.BRIEF:
        print("%s (line: %s) %s: checking for a tse file (%s)" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__, fname))

    # get the magic sequence
    #
    magic_str = get_version(fname)

    # check the magic sequence
    #
    if magic_str != TSE_VERSION:
        return False

    # exit gracefully: it is a tse file
    #
    return True
#
# end of function

def is_lbl(fname):
    """
    function: is_lbl

    arguments:
     fname: an lbl filename

    return:
     a boolean value indicating status

    description:
     This method checks if a file is a lbl file.
    """

    # display debug information
    #
    if dbgl_g > ndt.BRIEF:
        print("%s (line: %s) %s: checking for an lbl file (%s)" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__, fname))

    # get the magic sequence
    #
    magic_str = get_version(fname)

    # if the fname's magic sequence
    # is not a lbl file's return false
    #
    if magic_str != LBL_VERSION:
        return False

    # exit gracefully: it is an lbl file
    #
    return True
#
# end of function

def is_csv(fname):
    """
    function: is_csv

    arguments:
     fname: an csv filename

    return:
     a boolean value indicating status

    description:
     This method checks if a file is a csv file.
    """

    # display debug information
    #
    if dbgl_g > ndt.BRIEF:
        print("%s (line: %s) %s: checking for an csv file (%s)" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__, fname))

    # get the magic sequence
    #
    magic_str = get_version(fname)

    # if the fname's magic sequence
    # is not a csv file's return false
    #
    if magic_str != CSV_VERSION:
        return False

    # exit gracefully: it is a csv file
    #
    return True
#
# end of function

def is_xml(fname, num_bytes_to_read = FLIST_BSIZE):
    """
    function: is_xml

    arguments:
     fname: an xml filename

    return:
     a boolean value indicating status

    description:
     This method checks if a file is a xml file.
    """

    # display debug information
    #
    if dbgl_g > ndt.BRIEF:
        print("%s (line: %s) %s: checking for an xml file (%s)" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__, fname))

    # declare status variables to determine
    # if a file is xml
    #
    status = False

    with open(fname, MODE_READ_BINARY) as fp:

        # read first n bytes
        #
        barray = fp.read(num_bytes_to_read)

        # create status helper variables
        #
        has_greator_than = False
        has_less_than = False
        has_less_than_slash = False
        has_slash_greator_than = False

        # determine if barray has a greater than symbol
        #
        if DELIM_GREATTHAN.encode() in barray:
            has_greator_than = True

        # determine if barray has a less than symbol
        #
        if DELIM_LESSTHAN.encode() in barray:
            has_less_than = True

        # determine if barray has a less than symbol followed by a slash
        #
        if (DELIM_LESSTHAN + DELIM_SLASH).encode() in barray:
            has_less_than_slash = True

        # determine if barray has a slash followed by a greator than symbol
        #
        if (DELIM_SLASH + DELIM_GREATTHAN).encode() in barray:
            has_slash_greator_than = True

        status = has_greator_than and has_less_than \
            and (has_less_than_slash or has_slash_greator_than)

    # exit gracefully
    #
    return status
#
# end of function

#------------------------------------------------------------------------------
#
# functions listed here: manipulate directories
#
#------------------------------------------------------------------------------

def make_dirs(dirlist):
    """
    function: make_dirs

    arguments:
     dirlist - the list of directories to create

    return:
     none

    description:
     This function creates all the directories in a given list
    """

    # display informational message
    #
    if dbgl_g > ndt.BRIEF:
        print("%s (line: %s) %s: creating (%s)" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__, dirlist))

    # loop over the list
    #
    for directory in dirlist:

        # make the directory
        #
        make_dir(directory)

    # exit gracefully
    #
    return True
#
# end of function

def make_dir(path):
    """
    function: make_dir

    arguments:
     path: new directory path (input)
     none

    return:
     a boolean value indicating status
     none

    description:
     This function emulates the Unix command "mkdir -p". It creates
     a directory tree, recursing through each level automatically.
     If the directory already exists, it continues past that level.
    """

    # display informational message
    #
    if dbgl_g == ndt.FULL:
        print("%s (line: %s) %s: creating (%s)" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__, path))

    # use a system call to make a directory
    #
    try:
        os.makedirs(path)

    # if the directory exists, and error is thrown (and caught)
    #
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise

    # exit gracefully
    #
    return True
#
# end of function

def get_dirs(flist, odir=DELIM_NULL, rdir=DELIM_NULL, oext=None):
    """
    function: get_dirs

    arguments:
     flist: list of files
     odir: output directory
     rdir: replace directory
     oext: output extension

    return:
     set of unique directory paths

    description:
     This function returns a set containing unique directory paths
     from a given file list. This is done by replacing the rdir
     with odir and adding the base directory of the fname to the set
    """

    # display informational message
    #
    if dbgl_g > ndt.BRIEF:
        print("%s (line: %s) %s: fetching (%s)" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__, flist))

    # generate a set of unique directory paths
    #
    unique_dirs = set()

    # for each file name in the list
    #
    for fname in flist:

        # generate the output file name
        #
        ofile = create_filename(fname, odir, oext, rdir)

        # append the base dir of the ofile to the set
        #
        unique_dirs.add(os.path.dirname(ofile))

    # exit gracefully
    #
    return unique_dirs
#
# end of function

#------------------------------------------------------------------------------
#
# functions listed here: manage and manipulate temporary files
#
#------------------------------------------------------------------------------

def make_tmpdir(dir_name):
    """
    function: make_tmpdir

    arguments:
     dir_name: a temporary directory name

    return:
     run_dir: the temporary directory 
    
    description:
     this funciton sets up an unique temporary directory
     where all temporary python files will be stored.

    note:
     a pid will be appended to the end of the dirname given
    """

    # fetch an available temporary file directory
    #
    base_tmp = tempfile.gettempdir()

    # Use ISIP_TMPDIR if available, otherwise use
    # the system temporary directory.
    #
    base_tmp = os.environ.get("ISIP_TMPDIR", tempfile.gettempdir())
    
    # Create a unique temporary directory using mkdtemp.
    # The prefix includes the basename and the current process's PID.
    #
    run_dir = tempfile.mkdtemp(
        prefix=f"{dir_name}_",
        suffix = f"_{os.getpid()}",
        dir=base_tmp
    )
    
    # set the environment
    #
    os.environ["TMPDIR"] = run_dir
    os.environ["TORCH_DISTRIBUTED_TMPDIR"] = run_dir
    os.environ["TORCH_DATASETS_CACHE"] = run_dir
    os.environ["TORCH_HOME"] = run_dir
    os.environ["TORCH_TEMP_DIR"] = run_dir
    os.environ["XDG_CACHE_HOME"] = run_dir
    os.environ["PYTHONPYCACHEPREFIX"] = run_dir

    # set tempfile's temp dir and gettempdir to
    # return run_dir (the temporary directory)
    #
    tempfile.tempdir = run_dir
    tempfile.gettempdir = lambda: run_dir

    # exit gracefully: temporary directory created
    #
    return run_dir
#
# end of function

def free_tmpdir(dir_path):
    """
    function: free_tmpdir

    arguments:
     dir_path: the path of the temporary directory to be removed

    return:
     None

    description:
     This function attempts to remove the specified temporary directory.
     If the directory does not exist, it simply returns without error.
    """

    # attempt to recursively remove temp dir
    #
    try:
        
        # Recursively remove the directory.
        #
        shutil.rmtree(dir_path)
        
        # display debug information
        #
        if dbgl_g > ndt.BRIEF:
            print("%s (line: %s) %s: %s (%s)" %
                  (__FILE__, ndt.__LINE__,
                   "deleted temporary directory",
                   ndt.__NAME__, dir_path))
            
    # if any exception occurs during recursive directory
    # removing print the exeption for debugging
    #
    except Exception as e:
        
        # display debug information
        #
        if dbgl_g > ndt.BRIEF:
            print("Error: %s (line: %s) %s: %s (%s)" %
                  (__FILE__, ndt.__LINE__,
                   "failed to delete temporary directory",
                   ndt.__NAME__, dir_path))
            
    # exit gracefully
    #
    return None
#
# end of function
                
#------------------------------------------------------------------------------
#
# functions listed here: manage parameter files
#
#------------------------------------------------------------------------------

def get_kv_pair(input_str):
    """
    function: get_kv_pair

    arguments:
     str: the input string to turn into a key:value pair

    return:
     key: the kay of the determined key:value pair
     value: the value of the determined key:value pair

    description:
     This function parses a parameter string (key = value) and turns it into a
     key:value pair value. This function supports key:single-value pairs and
     key:list pairs
    """

    # split the current key into key and value parts
    #
    parts = input_str.split(DELIM_EQUAL)

    # strip whitespace from the key
    #
    key = parts[0].strip()

    # strip whitespace from the key
    #
    parts[1] = parts[1].strip()

    # if the value is surrounded by quotes, determine it as a literal and
    # remove the surrounding quotes
    #
    if ((parts[1].startswith(DELIM_QUOTE) and
         parts[1].endswith(DELIM_QUOTE)) \
    or (parts[1].startswith(DELIM_SQUOTE) and
        parts[1].endswith(DELIM_SQUOTE))):

        value = parts[1].strip("'").strip('"')

    # if the value is not surrounded by quotes, determine the value as a list
    # or single string
    #
    else:

        # split the value using regex. this expression will split the
        # value string into lists if there are commas present. if the
        # commas are inside of parenthesis they will not be counted
        #
        parts[1] = re.split(r',\s*(?![^()]*\))', parts[1])

        # if there is only one string in the value list, it is not a list
        # and return the key value pair as strings
        #
        if len(parts[1]) <= 1:
            value = parts[1][0].strip()

        # if there is more than one string in the value list, return the key
        # value pair as a list of strings
        #
        else:
            value = [input_str.strip() for input_str in parts[1]]

    # exit gracefully
    #
    return key, value
#
# end of function

def load_parameters(pfile, keyword):
    """
    function: load_parameters

    arguments:
     pfile: path of a parameter file in TOML format
     keyword: a parameter that has a section or a single value

    return:
     values: a dict, containing the value/s of the specified parameter

    description:
     This function reads a specified parameter file and reads the specified
     parameter into a Python dictionary object.
    """

    # display informational message
    #
    if dbgl_g == ndt.FULL:
        print("%s (line: %s) %s: loading (%s %s)" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__, pfile, keyword))

        # display informational message
    #
    if dbgl_g == ndt.FULL:
        print("%s (line: %s) %s: loading (%s %s)" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__, pfile, keyword))

    try:
        with open(pfile, "rb") as f:
            values = tomllib.load(f)
    except FileNotFoundError:
        print("Error: %s (line: %s) %s: file not found (%s)" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__, pfile))
        return None

    if keyword not in values:
        print("Error: %s (line: %s) %s: keyword not found (%s)" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__, keyword))
        return None

    return values[keyword]

def generate_map(pblock):
    """
    function: generate_map

    arguments:
     pblock: a dictionary containing a parameter block

    return:
     pmap: a parameter file map

    description:
     This function converts a dictionary returned from load_parameters to
     a dictionary containing a parameter map. Note that is lowercases the
     map so that text is normalized.
    """

    # display informational message
    #
    if dbgl_g == ndt.FULL:
        print("%s (line: %s) %s: generating a map" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__))

    # declare local variables
    #
    pmap = {}

    # loop over the input, split the line and assign it to pmap
    #
    for key in pblock:
        lkey = key.lower()
        pmap[lkey] = pblock[key].split(DELIM_COMMA)
        pmap[lkey] = list(map(lambda x: x.lower(), pmap[lkey]))

    # exit gracefully
    #
    return pmap
#
# end of function

def permute_map(map):
    """
    function: permute_map

    arguments:
     map: the input map

    return:
     pmap: an inverted map

    description:
     this function permutes a map so symbol lookups can go fast.
    """

    # display informational message
    #
    if dbgl_g == ndt.FULL:
        print("%s (line: %s) %s: permuting map" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__))

    # declare local variables
    #
    pmap = {}

    # loop over the input map:
    #  note there is some redundancy here, but every event should
    #  have only one output symbol
    #
    for sym in map:
        for event in map[sym]:
            pmap[event] = sym

    # exit gracefully
    #
    return pmap
#
# end of function

def map_events(elist, pmap):
    """
    function: map_events

    arguments:
     elist: a list of events
     pmap: a permuted map (look up symbols to be converted)

    return:
     mlist: a list of mapped events

    description:
     this function maps event labels to mapped values.
    """

    # display informational message
    #
    if dbgl_g == ndt.FULL:
        print("%s (line: %s) %s: mapping events" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__))

    # loop over the input list
    #
    mlist = []
    i = int(0)
    for event in elist:

        # copy the event
        #
        mlist.append([event[0], event[1], {}]);

        # change the label
        #
        for key in event[2]:
            mlist[i][2][pmap[key]] = event[2][key]

        # increment the counter
        #
        i += int(1)

    # exit gracefully
    #
    return mlist
#
# end of function

def get_version(fname):
    """
    function: get_version

    arguments:
     fname: input filename

    return:
     a string containing the type

    description:
     this function opens a file, reads the magic sequence and returns
     the string.
    """

    # display informational message
    #
    if dbgl_g > ndt.BRIEF:
        print("%s (line: %s) %s: opening file (%s)" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__, fname))

    # open the file
    #
    try:
        fp = open(fname, MODE_READ_TEXT)
    except IOError:
        print("%s (line: %s) %s: file not found (%s)" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__, fname))
        return None
    
    # define version value
    #
    ver = None

    # attempt to catch encoding errors
    #
    try:
        # iterate over lines until we find the magic string
        #
        for line in fp:
            
            # set every character to be lowercase
            #
            line = line.lower()
            
            # check if string contains "version"
            #
            if line.startswith(DEF_VERSION) or line.startswith(FMT_XML_VERSION) \
               or line.startswith(DELIM_COMMENT + DELIM_SPACE + DEF_VERSION):
                
                # only get version value after "version"
                #  for example, xxx_v1.0.0
                #
                ver = line.split(DEF_VERSION, 1)[-1]
                ver = (ver.replace(DELIM_EQUAL, DELIM_NULL)).strip()
                ver = (ver.split())[0]
                
                #  remove "" if has
                #
                ver = ver.replace(DELIM_QUOTE, DELIM_NULL)
                
                # break after we find the version
                #
                break

    except UnicodeDecodeError:
        print("%s (line: %s) %s: unicode error (%s)" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__, fname))
        return None

    # close the file
    #
    fp.close()

    # substring "version" not found
    #
    if (ver is None):
        return None

    # exit gracefully
    #
    return ver
#
# end of function

#------------------------------------------------------------------------------
#
# functions listed here: manage and manipulate data files
#
#------------------------------------------------------------------------------

def extract_comments(fname, cdelim = "#", cassign = "="):
    """
    function: extract_comments

    arguments:
     fname : the filename
     cdelim: the character to check for the beginning of the comment
     cassign: the character used the assignment operator in name/value pairs

    return:
     a dict

    description:
     this function extract a key-value comments from a file and returns a
     dictionary

     dict_comments = { "header" : "value" }
     note: everything is a string literal
    """

    # create the regular expression pattern
    #
    regex_assign_comment = re.compile(DEF_REGEX_ASSIGN_COMMENT %
                                      (cdelim, cassign),
                                      re.IGNORECASE | re.MULTILINE)
    # local dictionaries
    #
    dict_comments = {}

    # display informational message
    #
    if dbgl_g > ndt.BRIEF:
        print("%s (line: %s) %s: opening file (%s)" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__, fname))

    # open the file
    #
    try:
        fp = open(fname, MODE_READ_TEXT)
    except IOError:
        print("%s (line: %s) %s: file not found (%s)" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__, fname))
        return None

    # loop through the file
    #
    for line in fp:

        # strip all the spaces within the line
        #
        line = line.replace(DELIM_CARRIAGE, DELIM_NULL)

        # skip all the line that is not a comment
        #
        if not line.startswith(cdelim):
            continue

        # extract all of the comments
        #
        assign_comment = re.findall(regex_assign_comment, line)

        # append it to the dictionary
        #
        if assign_comment:
            dict_comments[assign_comment[0][0].strip()] \
                            = assign_comment[0][1].strip()

    # close the file
    #
    fp.close()

    # exit gracefully
    #
    return dict_comments
#
# end of function

#------------------------------------------------------------------------------
#
# class are listed here
#
#------------------------------------------------------------------------------

class TempDirManager:
    """
    class: TempDirManager 

    description:
     The `TempDirManager` class manages the creation and cleanup of
     temporary directories in a structured way. It generates a unique
     directory using a specified base name and process ID, ensuring
     isolation for temporary files.  It configures environment
     variables like `TMPDIR` and integrates with the `tempfile` module
     to override default temporary storage locations. The class
     ensures cleanup by using `atexit`, handling signals (`SIGINT`,
     `SIGTERM`), and supporting context management. This prevents
     orphaned directories and enhances efficiency in applications
     requiring temporary storage.
    """

    def __init__(self, dir_name = "tmp"):
        """
        method: __init__

        arguments:
         dir_name (str): Base name for the temporary directory

        return:
         None

        description:
         Initializes the temporary directory manager, sets internal state,
         and registers cleanup handlers so that the temporary directory is
         removed at program exit or interruption.
        """
        
        # Store the base name for the temporary directory
        #
        self.dir_name = dir_name
        
        # Initialize the variable that will hold the temporary directory path
        #
        self.run_dir = None
        
        # Register free() to clean up the temp directory on exit
        #
        atexit.register(self.free)

        # Register signal handlers for SIGINT and SIGTERM
        #
        try:
            
            # Register SIGINT
            #
            signal.signal(signal.SIGINT, self._handle_signal) 

            # Register SIGTERM
            #
            signal.signal(signal.SIGTERM, self._handle_signal)

        # catch the exception if signal registration fails 
        #
        except Exception as e:

            # print error message
            #
            print("Error : %s (line: %s) %s: %s (%s)" %
                  (__FILE__, ndt.__LINE__, ndt.__NAME__,
                   "Failed to register signal handlers",str(e)))

        # print debug message
        #
        if dbgl_g > ndt.BRIEF:
            print("%s (line: %s) %s: Initialized TempDirManager" %
                  (__FILE__, ndt.__LINE__, ndt.__NAME__))
    #
    # end of method

    def create(self):
        """
        method: create

        arguments:
         none

        return:
         run_dir (str): the path to the created temporary directory

        description:
         Creates a unique temporary directory using a prefix and process ID
         suffix based on a base directory (from 'ISIP_TMPDIR' or system default).
         Sets several environment variables to point to this directory and
         overrides default settings in the tempfile module.
        """
        
        # Determine base temp directory using 'ISIP_TMPDIR' or system default
        #
        base_tmp = os.environ.get("ISIP_TMPDIR", tempfile.gettempdir())

        # print debug statement
        #
        if dbgl_g > ndt.BRIEF:
            print("%s (line: %s) %s: Using base temporary directory (%s)" %
                  (__FILE__, ndt.__LINE__, ndt.__NAME__, base_tmp))

        # Create a unique temporary directory with prefix and process ID suffix
        #
        self.run_dir = tempfile.mkdtemp(prefix=f"{self.dir_name}_",
                                        suffix=f"_{os.getpid()}",
                                        dir=base_tmp)

        # print debug statement
        #
        if dbgl_g > ndt.BRIEF:
            print("%s (line: %s) %s: Created temporary directory (%s)" %
                  (__FILE__, ndt.__LINE__, ndt.__NAME__, self.run_dir))

        # Set environment variables to direct apps to use the new temp directory
        #
        os.environ["TMPDIR"] = self.run_dir
        os.environ["TORCH_DISTRIBUTED_TMPDIR"] = self.run_dir
        os.environ["TORCH_DATASETS_CACHE"] = self.run_dir
        os.environ["TORCH_HOME"] = self.run_dir
        os.environ["TORCH_TEMP_DIR"] = self.run_dir
        os.environ["XDG_CACHE_HOME"] = self.run_dir
        os.environ["PYTHONPYCACHEPREFIX"] = self.run_dir

        # Override the default temp directory used by the tempfile module
        #
        tempfile.tempdir = self.run_dir
        tempfile.gettempdir = lambda: self.run_dir

        # exit gracefully
        #  return run dir
        #
        return self.run_dir

    #
    # end of method
    
    def free(self):
        """
        method: free

        arguments:
         none

        return:
         None

        description:
         Deletes the temporary directory recursively. If deletion fails,
         prints a debug error message. Resets run_dir to DELIM_NULL.
        """

        # if run_dir is defined and the path exists
        #
        if self.run_dir and os.path.exists(self.run_dir):

            # attempt to remove run_dir
            #
            try:

                # remove run_dir tree
                #
                shutil.rmtree(self.run_dir)

                # print debug statement
                #
                if dbgl_g > ndt.BRIEF:
                    print("%s (line: %s) %s: Deleted temporary directory (%s)" %
                          (__FILE__, ndt.__LINE__, ndt.__NAME__, self.run_dir))

            # catch any exception and print an error message
            #
            except Exception as e:

                # print an error message
                #
                print("Error: %s (line: %s) %s: Failed to delete temp dir (%s) "
                      "[%s]" % (__FILE__, ndt.__LINE__, ndt.__NAME__,
                                self.run_dir, str(e)))

            # ensure self.run_dir is set to null
            #
            finally:
                self.run_dir = DELIM_NULL

        # if run_dir is not defined or does not exist
        # notify user
        #
        else:
            
            print("Error : %s (line: %s) %s: No temporary directory to delete" %
                  (__FILE__, ndt.__LINE__, ndt.__NAME__))
    #
    # end of method
    
    def get_path(self):
        """
        method: get_path

        arguments:
         none

        return:
         run_dir (str): The current temporary directory path.

        description:
         Returns the path to the temporary directory currently managed.
        """

        # exit gracefully
        #  return run_dir
        #
        return self.run_dir

    #
    # end of method

    def _handle_signal(self, signum, frame):
        """
        method: _handle_signal

        arguments:
         signum (int): The received signal number.
         frame: The current stack frame (unused).

        return:
         None

        description:
         Handles termination signals by cleaning up the temporary directory,
         resetting the signal handler to default, and exiting using
         os.EX_SOFTWARE.
        """

        # print a debug statement
        #
        if dbgl_g > ndt.BRIEF:
            print("%s (line: %s) %s: Received signal (%s); cleaning up" %
                  (__FILE__, ndt.__LINE__, ndt.__NAME__, signum))

        # free the temporary directory created
        #
        self.free()

        # Reset the signal handler
        #
        signal.signal(signum, signal.SIG_DFL)

        # let the system exit
        #
        sys.exit(os.EX_SOFTWARE)

    #
    # end of method
    
    def __enter__(self):
        """
        method: __enter__

        arguments:
         none

        return:
         self (TempDirManager): The instance with the created temp directory.

        description:
         Supports usage of TempDirManager as a context manager by creating the
         temporary directory upon entering the 'with' block.
        """

        # print debug statement
        #
        if dbgl_g > ndt.BRIEF:
            print("%s (line: %s) %s: Entering context manager" %
                  (__FILE__, ndt.__LINE__, ndt.__NAME__))

        # create a temporary directory
        #
        self.create()

        # return the object instance
        #
        return self
    #
    # end of method

    def __exit__(self, exc_type, exc_value, traceback):
        """
        method: __exit__

        arguments:
         exc_type: Exception type (if an exception occurred).
         exc_value: Exception value (if an exception occurred).
         traceback: Traceback object (if an exception occurred).

        return:
         None

        description:
         Exits the context manager and ensures the temporary directory is
         cleaned up, regardless of whether an exception occurred.
        """

        # print debug statement
        #
        if dbgl_g > ndt.BRIEF:
            print("%s (line: %s) %s: Exiting context manager" %
                  (__FILE__, ndt.__LINE__, ndt.__NAME__))

        # free the temporary directory
        #
        self.free()
    #
    # end of method
#
# end of class

#
# end of file
