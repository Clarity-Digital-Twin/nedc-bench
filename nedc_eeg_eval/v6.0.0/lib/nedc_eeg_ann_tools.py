#!/usr/bin/env python
#
# file: $NEDC_NFC/class/python/nedc_eeg_ann_tools/nedc_eeg_ann_tools.py
#
# revision history:
#
# 20250111 (DH): made csv/xml classes less reliant on montages
# 20241010 (DH): fixed csv/xml header duration precision bug
# 20240928 (DH): fixed bugs associated with montage paths
# 20240708 (DH): refactored code according to the new division of tools
# 20240518 (JP): split and renamed the ann tools
# 20220622 (AB): refactored code to new comment format
# 20220514 (JP): updated some things to fix bugs in the eeg scoring software
# 20220307 (PM): configured the CSV Class to support the new CSV format
# 20210201 (TC): added XML and CSV
# 20200610 (LV): refactored code
# 20200607 (JP): refactored code
# 20170728 (JP): added compare_durations and load_annotations
# 20170716 (JP): upgraded to use the new annotation tools
# 20170714 (NC): created new class structure
# 20170709 (JP): refactored the code
# 20170612 (NC): added parsing and displaying methods
# 20170610 (JP): initial version
#
# This class contains a collection of methods that provide
# the infrastructure for processing annotation-related data.
#
# These file types are supported: csv, lbl, tse, and xml. Each of these
# files has a specific header structure:
#
# CSV:
#  # version = csv_v1.0.0
#  # bname = file_name_value
#  # duration = duration_value secs
#  # montage_file = montage_file_value
#
#  ... data follows ...
#
# LBL:
#  version = lbl_v1.0.0
#
#  ... data follows ...
#
# TSE:
#  version = tse_v1.0.0
#
#  ... data follows ...
#
# XML:
#  <?xml version="1.0" ?>
#  <root>
#   <bname>file_name_value</bname>
#   <duration>duration_value secs</duration>
#   <montage_file>montage_file_value</montage_file>
#
#  ... data follows ...
#
#------------------------------------------------------------------------------

# import required system modules
#
import copy
import os
import re
import sys
import xml.etree.ElementTree as et

from collections import defaultdict
from lxml import etree
from operator import itemgetter
from pathlib import Path as path
from xml.dom import minidom as md

# import required NEDC modules
#
import nedc_debug_tools as ndt
import nedc_file_tools as nft

#------------------------------------------------------------------------------
#
# global variables are listed here
#
#------------------------------------------------------------------------------

# set the filename using base name
#
__FILE__ = os.path.basename(__file__)

# define numeric and symbolic constants
#
DEF_CHANNEL = int(-1)

# define symbols to use to create filler events:
#  a background symbol
#  a precision used to compare floats
#  a default probability (as a float)
#
DEF_BCKG = "bckg"
DEF_SEIZ = "seiz"
PRECISION = int(4)
PROBABILITY = float(1.0000)

# define the location of default files:
#  note these are version specific since the schema file will evolve
#  over time.
#
DEF_MAP_FNAME = "$NEDC_NFC/lib/nedc_eas_default_map.txt"
DEF_MONTAGE_FNAME = "$NEDC_NFC/lib/nedc_eas_default_montage.txt"
DEF_XML_FNAME = "$NEDC_NFC/lib/nedc_eeg_xml_schema_v00.xsd"

# define montage regex
#
DEF_REGEX_MONTAGE_FILE = \
    re.compile(r'(-?\d+(?=,)),(\w+(?:-?)+\w+(?=:))',
               re.IGNORECASE)

# define eas map regex
#
DEF_NEDC_EAS_MAP_REGEX = \
    re.compile("(.+?(?==))=\((\d+),(\d+),(\(\d+,\d+,\d+,\d+\))\)",
               re.IGNORECASE)

#******************************************************************************
#
# define the header structure for the supported file types
#
#------------------------------------------------------------------------------
# define the csv header format and other associated variables
#
DELIM_CSV_VERSION = nft.DEF_VERSION
DELIM_CSV_BNAME = nft.DEF_BNAME
DELIM_CSV_DURATION = nft.DEF_DURATION
DELIM_CSV_MONTAGE_FILE = nft.DEF_MONTAGE_FILE
DELIM_CSV_SECS = nft.FMT_SECS
DELIM_CSV_LABELS = nft.DELIM_CSV_LABELS
DELIM_CSV_MONTAGE = nft.DEF_MONTAGE

# define keys to access header information in dictionaries
#
CSV_KEY_VERSION = DELIM_CSV_VERSION
CSV_KEY_BNAME = DELIM_CSV_BNAME
CSV_KEY_DURATION = DELIM_CSV_DURATION
CSV_KEY_MONTAGE_FILE = DELIM_CSV_MONTAGE_FILE

#------------------------------------------------------------------------------
# define the lbl header format and other associated variables
#
DELIM_LBL_VERSION = nft.DEF_VERSION
DELIM_LBL_BNAME = nft.DEF_BNAME
DELIM_LBL_DURATION = nft.DEF_DURATION
DELIM_LBL_MONTAGE_FILE = nft.DEF_MONTAGE_FILE

# define keys to access header information in dictionaries
#
LBL_KEY_VERSION = DELIM_LBL_VERSION
LBL_KEY_BNAME = DELIM_LBL_BNAME
LBL_KEY_DURATION = DELIM_LBL_DURATION
LBL_KEY_MONTAGE_FILE = DELIM_LBL_MONTAGE_FILE

# define constants associated with the eeg lbl class
#
DELIM_LBL_MONTAGE = nft.DEF_MONTAGE
DELIM_LBL_NUM_LEVELS = nft.DEF_LBL_NUM_LEVELS
DELIM_LBL_LEVEL = nft.DEF_LBL_LEVEL
DELIM_LBL_SYMBOL = nft.DEF_LBL_SYMBOL
DELIM_LBL_LABEL = nft.DEF_LBL_LABEL
DELIM_LBL_VERSION = nft.DEF_VERSION

#------------------------------------------------------------------------------
# define the tse header format and other associated variables
#
DELIM_TSE_VERSION = nft.DEF_VERSION
DELIM_TSE_BNAME = nft.DEF_BNAME
DELIM_TSE_DURATION = nft.DEF_DURATION
DELIM_TSE_MONTAGE_FILE = nft.DEF_MONTAGE_FILE

# define keys to access header information in dictionaries
#
TSE_KEY_VERSION = DELIM_TSE_VERSION
TSE_KEY_BNAME = DELIM_TSE_BNAME
TSE_KEY_DURATION = DELIM_TSE_DURATION
TSE_KEY_MONTAGE_FILE = DELIM_TSE_MONTAGE_FILE

#------------------------------------------------------------------------------
# define the xml header format and other associated variables
#
DELIM_XML_VERSION = nft.DEF_VERSION
DELIM_XML_BNAME = nft.DEF_BNAME
DELIM_XML_DURATION = nft.DEF_DURATION
DELIM_XML_MONTAGE_FILE = nft.DEF_MONTAGE_FILE
DELIM_XML_MONTAGE = nft.DEF_MONTAGE

# define keys to access header information in dictionaries
#
XML_KEY_VERSION = DELIM_XML_VERSION
XML_KEY_BNAME = DELIM_XML_BNAME
XML_KEY_DURATION = DELIM_XML_DURATION
XML_KEY_MONTAGE_FILE = DELIM_XML_MONTAGE_FILE

# define constants for term based representation in the dictionary
#
DEF_TERM_BASED_IDENTIFIER = nft.DEF_TERM_BASED_IDENTIFIER

# define a constant to reference schema objects
#
DELIM_SCHEMA = nft.DEF_SCHEMA

# define a list of characters we need to parse out
#
REM_CHARS = [nft.DELIM_BOPEN, nft.DELIM_BCLOSE, nft.DELIM_NEWLINE,
             nft.DELIM_SPACE, nft.DELIM_QUOTE, nft.DELIM_SEMI,
             nft.DELIM_SQUOTE]

# define constants associated with the Xml class
#
XML_TAG_CHANNEL_PATH = nft.XML_TAG_CHANNEL_PATH
XML_TAG_EVENT = nft.XML_TAG_EVENT
XML_TAG_ROOT = nft.XML_TAG_ROOT
XML_TAG_BNAME = nft.DEF_BNAME
XML_TAG_DURATION = nft.DEF_DURATION
XML_TAG_LABEL = nft.XML_TAG_LABEL
XML_TAG_NAME = nft.XML_TAG_NAME
XML_TAG_PROBABILITY = nft.XML_TAG_PROBABILITY
XML_TAG_ENDPOINTS = nft.XML_TAG_ENDPOINTS
XML_TAG_CHANNEL = nft.XML_TAG_CHANNEL
XML_TAG_MONTAGE_CHANNELS = nft.XML_TAG_MONTAGE_CHANNELS
XML_TAG_ANNOTATION_LABEL_FILE = nft.XML_TAG_ANNOTATION_LABEL_FILE
XML_TAG_MONTAGE_FILE = nft.XML_TAG_MONTAGE_FILE
XML_TAG_MONTAGE_TAG = nft.XML_TAG_MONTAGE_TAG
XML_FMT_SECS = nft.FMT_SECS

# define types check
#
PARENT_TYPE = 'parent'
EVENT_TYPE = 'event'
LIST_TYPE = 'list'
DICT_TYPE = 'dict'

#------------------------------------------------------------------------------
#
# functions listed here
#
#------------------------------------------------------------------------------

# declare a global debug object so we can use it in functions
#
dbgl = ndt.Dbgl()

#------------------------------------------------------------------------------
# other supporting functions
#


def remap_labels(graph, label_map):
    """
    function: remap_labels

    Arguments:
      graph:  nested dict {level: {sublevel: {chan: [[start, stop, {label:prob}],…]}}}
      label_map: dict mapping target_label -> list of raw_labels to collapse, e.g.
                 { 'BCKG': ['bckg','background'], 'SEIZ': ['seiz','seizure'], … }

    Returns:
      new_graph: deep copied graph with every raw label replaced by its target.

    description:
     Walk a deep copy of an AnnGrEeg style graph and replace each region’s
     label according to label_map.

    """
    
    # build raw_label -> target_label lookup
    #
    raw2tgt = {
        raw: tgt
        for tgt, raws in label_map.items()
        for raw in raws
    }

    # deep‐copy so original isn’t touched
    #
    new_graph = copy.deepcopy(graph)
    
    # walk and remap each label in the graph
    #
    for lvl, subd in new_graph.items():

        # iterate through each sub‐dictionary of sublevels
        #
        for sub, chand in subd.items():

            # iterate through each channel’s list of events
            #
            for chan, ev_list in chand.items():

                # iterate over every event tuple in that channel
                #
                for ev in ev_list:

                    # unpack start time, stop time, and the symbol -> prob dict
                    #
                    start, stop, symdict = ev

                    # prepare a fresh dict to hold the remapped symbols
                    #
                    new_symdict = {}
                    
                    # for each raw label and its probability
                    #
                    for raw_label, prob in symdict.items():

                        # ensure raw in label list
                        #
                        if raw_label not in raw2tgt:
                            print("Error: %s (line: %s) %s: %s, %s (%s: %s, %s: %s)" %
                                  (__FILE__, ndt.__LINE__, ndt.__NAME__,
                                   "ann label not recognized",
                                   "redifine source to target label map",
                                   "unknow label", raw_label,
                                   "known labels", list(raw2tgt.keys())))
                            sys.exit(os.EX_SOFTWARE)

                        # map the raw label to its target, defaulting to itself
                        #
                        tgt = raw2tgt.get(raw_label, raw_label)
                        
                        # accumulate probability under the mapped label
                        #
                        new_symdict[tgt] = new_symdict.get(tgt, 0.0) + prob

                    # overwrite the old symbol dict with the remapped one
                    #
                    ev[2] = new_symdict

    # exit gracefully
    #  return remaped graph
    #
    return new_graph
#
# end of function

def get_unique_events(events):
    """
    function: get_unique_events

    arguments:
     events: events to aggregate

    return:
     a list of unique events

    description:
     This method combines events if they are of the same start/stop times.
    """

    # list to store unique events
    #
    unique_events = []

    # make sure events_a are sorted
    #
    events = sorted(events, key=lambda x: (x[0], x[1]))

    # loop until we have checked all events_a
    #
    while len(events) != 0:

        # reset flag
        #
        is_unique = True
        n_start = int(-1)
        n_stop = int(-1)

        # get this event's start/stop times
        #
        start = events[0][0]
        stop = events[0][1]

        # if we are not at the last event
        #
        if len(events) != 1:

            # get next event's start/stop times
            #
            n_start = events[1][0]
            n_stop = events[1][1]

        # if this event's start/stop times are the same as the next event's,
        #  (only do this if we are not at the last event)
        #
        if (n_start == start) and (n_stop == stop) and (len(events) != 1):

            # combine this event's dict with the next event's symbol dict
            #
            for symb in events[1][2]:

                # if the symb is not found in this event's dict
                #
                if symb not in events[0][2]:

                    # add symb to this event's dict
                    #
                    events[0][2][symb] = events[1][2][symb]

                # else if the symb in the next event has a higher prob
                #
                elif events[1][2][symb] > events[0][2][symb]:

                    # update this event's symb with prob from the next event
                    #
                    events[0][2][symb] = events[1][2][symb]
                #
                # end of if/elif
            #
            # end of for

            # delete the next event, it is not unique
            #
            del events[1]
        #
        # end of if

        # loop over unique events
        #
        for unique in unique_events:

            # if the start/stop times of this event is found in unique events
            #
            if (start == unique[0]) and (stop == unique[1]):

                # combine unique event's dict with this event's dict:
                #  iterate over symbs in this event's dict
                #
                for symb in events[0][2]:

                    # if the symb is not found in the unique event's dict
                    #
                    if symb not in unique[2]:

                        # add symb to the unique event's dict
                        #
                        unique[2][symb] = events[0][2][symb]

                    # else if the symb in this event has a higher prob
                    #
                    elif events[0][2][symb] > unique[2][symb]:

                        # update unique event's symb with prob from this event
                        #
                        unique[2][symb] = events[0][2][symb]
                    #
                    # end of if/elif
                #
                # end of for

                # delete this event, it is not unique
                #
                del events[0]
                is_unique = False
                break
            #
            # end of if
        #
        # end of for

        # if this event is still unique
        #
        if is_unique is True:

            # add this event to the unique events
            #
            unique_events.append(events[0])

            # delete this event, it is now stored as unique
            #
            del events[0]
        #
        # end of if
    #
    # end of while

    # exit gracefully
    #
    return unique_events
#
# end of function

def compare_durations(l1, l2):
    """
    function: compare_durations

    arguments:
     l1: the first list of files
     l2: the second list of files

    return:
     a boolean value indicating status

    description:
     This method goes through two lists of files and compares the durations
     of the annotations. If they don't match, it returns false.
    """

    # display an informational message
    #
    if dbgl > ndt.BRIEF:
        print("%s (line: %s) %s: comparing durations of annotations" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__))

    # create an annotation object
    #
    ann = AnnEeg()

    # check the length of the lists
    #
    if len(l1) != len(l2):
        return False

    # loop over the lists together
    #
    for l1_i, l2_i in zip(l1, l2):

        # load the annotations for l1
        #
        if ann.load(l1_i) == False:
            print("Error: %s (line: %s) %s: error loading annotation (%s)" %
                  (__FILE__, ndt.__LINE__, ndt.__NAME__, l1_i))
            return False

        # get the events for l1
        #
        events_l1 = ann.get()

        # sort the event
        #
        events_l1.sort(key = itemgetter(0))

        # fill in all the gap annotation with BCKG
        #
        events_l1 = augment_annotation(events_l1, ann.get_file_duration())

        # join all the BCKG events together
        #
        events_l1 = remove_repeated_events(events_l1)

        if events_l1 == None:
            print("Error: %s (line: %s) %s: error getting annotation ((%s)" %
                  (__FILE__, ndt.__LINE__, ndt.__NAME__, l1_i))
            return False

        # load the annotations for l2
        #
        if ann.load(l2_i) == False:
            print("Error: %s (line: %s) %s: error loading annotation (%s)" %
                  (__FILE__, ndt.__LINE__, ndt.__NAME__, l2_i))
            return False

        # get the events for l2
        #
        events_l2 = ann.get()

        # sort the event
        #
        events_l2.sort(key = itemgetter(0))

        # fill in all the gap annotation with BCKG
        #
        events_l2 = augment_annotation(events_l2, ann.get_file_duration())

        # join all the BCKG events together
        #
        events_l2 = remove_repeated_events(events_l2)

        if events_l2 == None:
            print("Error: %s (line: %s) %s: error getting annotation: (%s)" %
                  (__FILE__, ndt.__LINE__, ndt.__NAME__, l2_i))
            return False

        # check the durations
        #
        if round(events_l1[-1][1], ndt.MAX_PRECISION) != \
           round(events_l2[-1][1], ndt.MAX_PRECISION):
            print("Error: %s (line: %s) %s: durations do not match" %
                  (__FILE__, ndt.__LINE__, ndt.__NAME__))
            print("\t%s (%f)" % (l1_i, events_l1[-1][1]))
            print("\t%s (%f)" % (l2_i, events_l2[-1][1]))
            return False

    # exit gracefully
    #
    return True
#
# end of function

def load_annotations(flist, level=int(0), sublevel=int(0),
                     channel=DEF_CHANNEL):
    """
    function: load_annotations

    arguments:
     list: a list of filenames

    return:
     a list of lists containing all the annotations

    description:
     This method loops through a list and collects all the annotations.
    """

    # display an informational message
    #
    if dbgl > ndt.BRIEF:
        print("%s (line: %s) %s: loading annotations" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__))

    # create an annotation object
    #
    events = []
    ann = AnnEeg()

    # loop over the list
    #
    for fname in flist:

        # load the annotations
        #
        if ann.load(fname) == False:
            print("Error: %s (line: %s) %s: loading annotation for file (%s)" %
                  (__FILE__, ndt.__LINE__, ndt.__NAME__, fname))
            return None

        # get the events
        #
        events_tmp = ann.get(level, sublevel, channel)
        if events_tmp == None:
            print("Error: %s (line: %s) %s: error getting annotation (%s)" %
                  (__FILE__, ndt.__LINE__, ndt.__NAME__, fname))
            return None

        events_tmp.sort(key = itemgetter(0))

        # fill in all the gap annotation with BCKG
        #
        events_tmp = \
            augment_annotation(events_tmp, ann.get_file_duration())

        # join all the BCKG events together
        #
        events_tmp = remove_repeated_events(events_tmp)

        events.append(events_tmp)

    # exit gracefully
    #
    return events
#
# end of function

def augment_annotation(events, dur, sym = DEF_BCKG):
    """
    function: augment_annotation

    arguments:
     events: an event list
     dur: the duration of a file in seconds
     sym: the symbol to use for the annotation that fills in the gaps

    return:
     a new event list with the augmented annotation

    description:
     This method fills in gaps in an annotation with a user-supplied symbol.
    """

    # display informational message
    #
    if dbgl > ndt.BRIEF:
        print("%s (line: %s) %s: events (before)" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__))
        for ev in events:
            print(ev)

    # round the duration
    #
    dur = round(dur, ndt.MIN_PRECISION)

    # loop over the events
    #
    events_new = []
    curr_time = float(0.0)

    for ev in events:

        # if the current time equals the start time of the next event,
        # cop they event and advance time to the end of that event
        #
        start_time  = round(ev[0], ndt.MIN_PRECISION)
        end_time  = round(ev[1], ndt.MIN_PRECISION)

        if curr_time != start_time:

            # add a filler event
            #
            events_new.append([curr_time, start_time, {sym: PROBABILITY}])

        # append the event
        #
        events_new.append(ev)
        curr_time = end_time

    # add an end of file background event if necessary
    #
    if curr_time != dur:
        events_new.append([curr_time, dur, {sym: PROBABILITY}])

    # display informational message
    #
    if dbgl > ndt.BRIEF:
        print("%s (line: %s) %s: events (after)" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__))
        for ev in events_new:
            print(ev)

    # exit gracefully
    #
    return events_new
#
# end of function

def remove_repeated_events(events):
    """
    function: remove_repeated_events

    arguments:
     events: an event list

    return:
     a new event list with the merged annotations

    description:
     This method reduces consecutive repeated events, defined as events
     that share and end time and start time, to a single event.
     It is typically used to reduce multiple background events. Note that
     by convention we use the confidence of the first event in the sequence.
     You could use the average, but this is a bit complicated because gaps
     in annotations are filled in with a background event with a confidece of 1.0.
    """

    # display informational message
    #
    if dbgl > ndt.BRIEF:
        print("%s (line: %s) %s: events (before)" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__))
        for ev in events:
            print("before: ", ev)

    # initialize an output list
    #
    events_new = []

    # loop over all events
    #
    i = int(0)
    while i < len(events):

        # seek forward from the current event to the next dissimilar event
        #
        j = i
        cur_tag = list(events[j][2].keys())[0]
        while (j < (len(events) - 1)):
            nxt_tag = list(events[j+1][2].keys())[0]
            if cur_tag != nxt_tag:
                break;
            else:
                j += int(1)
                cur_tag = nxt_tag

        # append the new event list with the collapsed event:
        #  note we use the confidence from the first event rather than
        #  averaging across all events.
        #
        events_new.append([events[i][0], events[j][1], events[i][2]])
        i = j + 1

    # display informational message
    #
    if dbgl > ndt.BRIEF:
        print("%s (line: %s) %s: events (after)" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__))
        for ev in events_new:
            print("after: ", ev)

    # exit gracefully
    #
    return events_new

#
# end of function

def parse_nedc_eas_map_to_montage_defintion(map_file):
    """
    function: parse_nedc_eas_map_to_montage_defintion

    arguments:
     map_file: the nuked_eas map file configuration

    return:
     a dictionary to parse the map file

    description:
     note:
     ** NEDC_EAS MAP FILE CONFIGURATION **
     KEY   | MAPPING     PRIORITY    RGB_COLOR_SCHEME
     null = ( 0,          0,          (  0 ,  0,   0,  10))

     We want to extract only the KEY and MAPPING to build this dictionary:

     map_dictionary = { mapping: key}

     Ex: map_dictionary = { 'null' : 0 }
    """

    map_dictionary  = {}

    with open(map_file) as file:

        for ind, line in enumerate(file):

            line = line.strip().replace(nft.DELIM_SPACE, nft.DELIM_NULL)

            if len(line) == 0 or line.startswith(nft.DELIM_COMMENT) \
               or line.startswith(nft.DELIM_OPEN) or \
               line.startswith("symbols"):
                continue

            # pattern matching
            #
            result = re.findall(DEF_NEDC_EAS_MAP_REGEX, line)[0]

            if len(result) < 4:
                raise Exception(f"Map File Configuration invalid on line {ind + 1}")

            key, mapping, priority, rgb_val = \
                result[0], int(result[1]), int(result[2]), eval(result[3])

            map_dictionary[mapping] = key

    return map_dictionary
#
# end of function

def parse_nedc_eas_map_to_montage_definition_new(map_file):
    """
    function: parse_nedc_eas_map_to_montage_defintion_new

    arguments:
     map_file: the nedc_eas map file configuation

    return:
     a dictionary to parse the map file

    description:
     note:
     ** NEDC_EAS MAP FILE CONFIGURATION **
     symbols[0] = { 0: null, 1: spsw, 2: gped, ...}

     We want to extract only the KEY and MAPPING to build this dictionary:

     map_dictionary = { mapping: key}

     Ex: map_dictionary = { 'null' : 0 }
    """

    map_dictionary  = {}

    # fetch file contents and close conection
    #
    with open(map_file) as file:

        file_contents = file.readlines()

    file.close()

    # search through file_contents to see if symbols key is present
    # if so
    #
    for line in file_contents:

        # if the current line does not contain the key
        # symbols then continue to next line
        #
        if not line.startswith("symbols"):
            continue

        # clean up symbol data
        #
        symbol_line = line.split(nft.DELIM_EQUAL)[-1] \
                          .replace(nft.DELIM_BOPEN,nft.DELIM_NULL) \
                          .replace(nft.DELIM_BCLOSE,nft.DELIM_NULL)

        # store data in temporary list
        #
        symbols_list_temp = symbol_line.split(nft.DELIM_COMMA)

        # load data into map_dictionary
        #
        for symb in symbols_list_temp:
            map_dictionary[symb.split(nft.DELIM_COLON)[0]] = \
                symb.split(nft.DELIM_COLON)[1]

        # symbol data has been loaded
        # break from loop
        #
        break

    # exit gracefully
    #
    return map_dictionary

#
# end of function

#------------------------------------------------------------------------------
#
# + Classes are listed here:
#  There are six classes in this file arranged in this hierarchy
#   AnnGrEeg -> {Tse, Lbl, Csv, Xml} -> AnnEeg
#
# + Breakdown of Ann_EEG_Tools:
#
#   AnnGrEeg : The basic data structure that this whole library uses
#   Csv      : The class that deals with Csv files
#   Lbl      : The class that deals with Lbl files
#   Tse      : The class that deals with Tse files
#   Xml      : The class that deals with Xml files
#   AnnEeg   : This is a wrapper for all the other classes.
#              You would ONLY need to instantiate this class.
#
#   Between the four classes {Tse, Lbl, Csv, Xml}, each of the classes share
#   a common method that has the same name (it is important that their name is
#   is the same for AnnEeg to work).
#
#   Here are the common methods:
# *> add set and get header ???
#    + load()
#    + write()
#    + display()
#    + add()
#    + delete()
#    + get()
#    + get_graph()
#    + set_graph()
#
#   Nedc_ann_eeg_tools works by using the AnnEeg class to automatically call
#   correct method for the correct file type. So DO NOT REMOVE any of the
#   common method pointed out above.
#
# + Graphing Object Structure:
#
#   Below is the return Graphing Object Structure:
#
#    graph = { level { sublevel { channel_index : [[start_time, stop time, {'label': probability}],
#                                                      ...]}}}
#    level: int
#    sublevel: int
#    channel_index: int
#    start_time: float
#    stop_time:  float
#    label: string
#    probability: float
#
#   Ex:
#    graph = { 0 { 0 { 2 : [[55.1234, 60.0000, {'elec': 1.0}],
#                           [65.1234, 70.0000, {'chew': 1.0}]
#                                                            ]}}}
#
# + header object structure
#
#   Below is the returning header data dictionary
#
#    header = {bname : bname_value,
#              duration : duration_value,
#              montage_file : montage_file_value}
#
#------------------------------------------------------------------------------

# class: AnnGrEeg
#
# This class implements the main data structure used to hold an annotation.
#
class AnnGrEeg:
    """
    Class: AnnGrEeg

    arguments:
     none

    description:
     This class implements the main data structure used to hold an annotation.
    """

    def __init__(self):
        """
        method: constructor

        arguments:
         none

        return:
         none

        description:
         none
        """

        # set the class name
        #
        AnnGrEeg.__CLASS_NAME__ = self.__class__.__name__

        # declare a data structure to hold a graph
        #
        self.graph_d = {}

        self.header_d = {}
    #
    # end of method

    def create(self, lev, sub, chan, start, stop, symbols):
        """
        method: create

        arguments:
         lev: level of annotation
         sub: sublevel of annotation
         chan: channel of annotation
         start: start time of annotation
         stop: stop time of annotation
         symbols: dict of symbols/probabilities

        return:
         a boolean value indicating status

        description:
         This method create an annotation in the AG data structure
        """

        # display an informational message
        #
        if dbgl > ndt.BRIEF:
            print("%s (line: %s) %s: %s" %
                  (__FILE__, ndt.__LINE__, ndt.__NAME__,
                   "creating annotation in AG data structure"))

        # try to access sublevel dict at level
        #

        try:
            self.graph_d[lev]

            # try to access channel dict at level/sublevel
            #
            try:
                self.graph_d[lev][sub]

                # try to append values to channel key in dict
                #
                try:
                    self.graph_d[lev][sub][chan].append([start, stop, symbols])

                # if appending values failed, finish data structure
                #
                except:

                    # create empty list at chan key
                    #
                    self.graph_d[lev][sub][chan] = []

                    # append values
                    #
                    self.graph_d[lev][sub][chan].append([start, stop, symbols])

            # if accessing channel dict failed, finish data structure
            #
            except:

                # create dict at level/sublevel
                #
                self.graph_d[lev][sub] = {}

                # create empty list at chan
                #
                self.graph_d[lev][sub][chan] = []

                # append values
                #
                self.graph_d[lev][sub][chan].append([start, stop, symbols])

        # if accessing sublevel failed, finish data structure
        #
        except:

            # create dict at level
            #
            self.graph_d[lev] = {}

            # create dict at level/sublevel
            #
            self.graph_d[lev][sub] = {}

            # create empty list at level/sublevel/channel
            #
            self.graph_d[lev][sub][chan] = []

            # append values
            #
            self.graph_d[lev][sub][chan].append([start, stop, symbols])

        # exit gracefully
        #
        return True
    #
    # end of method

    def get(self, level, sublevel, channel):
        """
        method: get

        arguments:
         level: level of annotations
         sublevel: sublevel of annotations

        return:
         events by channel at level/sublevel

        description:
         This method returns the events stored at the level/sublevel argument
        """

        # display an informational message
        #
        if dbgl > ndt.BRIEF:
            print("%s (line: %s) %s: getting events stored at level/sublevel" %
                  (__FILE__, ndt.__LINE__, ndt.__NAME__))

        # declare local variables
        #
        events = []

        # try to access graph at level/sublevel/channel
        #
        try:
            events = self.graph_d[level][sublevel][channel]

            # exit gracefully
            #
            return events

        # exit (un)gracefully: if failed, return False
        #
        except:
            return False
    #
    # end of method

    def sort(self):
        """
        method: sort

        arguments:
         none

        return:
         a boolean value indicating status

        description:
         This method sorts annotations by level, sublevel,
         channel, start, and stop times
        """

        # display an informational message
        #
        if dbgl > ndt.BRIEF:
            print("%s (line: %s) %s: %s %s" %
                  (__FILE__, ndt.__LINE__, ndt.__NAME__,
                   "sorting annotations by",
                   "level, sublevel, channel, start and stop times"))

        # sort each level key by min value
        #
        self.graph_d = dict(sorted(self.graph_d.items()))

        # iterate over levels
        #
        for lev in self.graph_d:

            # sort each sublevel key by min value
            #
            self.graph_d[lev] = dict(sorted(self.graph_d[lev].items()))

            # iterate over sub levels
            #
            for sub in self.graph_d[lev]:

                # sort each channel key by min value
                #
                self.graph_d[lev][sub] = \
                    dict(sorted(self.graph_d[lev][sub].items()))

                # iterate over channels
                #
                for chan in self.graph_d[lev][sub]:

                    # sort each list of labels by start and stop times
                    #
                    self.graph_d[lev][sub][chan] = \
                        sorted(self.graph_d[lev][sub][chan],
                               key=lambda x: (x[0], x[1]))

        # exit gracefully
        #
        return True
    #
    # end of method

    def add(self, dur, sym, level, sublevel):
        """
        method: add

        arguments:
         dur: duration of events
         sym: symbol of events
         level: level of events
         sublevel: sublevel of events

        return:
         a boolean value indicating status

        description:
         This method adds events of type sym.
        """

        # display an informational message
        #
        if dbgl > ndt.BRIEF:
            print("%s (line: %s) %s: adding events of type sym" %
                  (__FILE__, ndt.__LINE__, ndt.__NAME__))

        # try to access level/sublevel
        #
        try:
            self.graph_d[level][sublevel]
        except:
            print("Error: %s (line: %s) %s::%s %s (%d/%d)" %
                  (__FILE__, ndt.__LINE__, AnnGrEeg.__CLASS_NAME__,
                   ndt.__NAME__, "level/sublevel not found", level, sublevel))
            return False

        # variable to store what time in the file we are at
        #
        mark = 0.0

        # make sure events are sorted
        #
        self.sort()

        # iterate over channels at level/sublevel
        #
        for chan in self.graph_d[level][sublevel]:

            # reset list to store events
            #
            events = []

            # iterate over events at each channel
            #
            for event in self.graph_d[level][sublevel][chan]:

                # ignore if the start or stop time is past the duration
                #
                if (event[0] > dur) or (event[1] > dur):
                    pass

                # ignore if the start time is bigger than the stop time
                #
                elif event[0] > event[1]:
                    pass

                # ignore if the start time equals the stop time
                #
                elif event[0] == event[1]:
                    pass

                # if the beginning of the event is not at the mark
                #
                elif event[0] != mark:

                    # create event from mark->start time
                    #
                    events.append([mark, event[0], {sym: 1.0}])

                    # add event after mark->start time
                    #
                    events.append(event)

                    # set mark to the stop time
                    #
                    mark = event[1]

                # if the beginning of the event is at the mark
                #
                else:

                    # store this event
                    #
                    events.append(event)

                    # set mark to the stop time
                    #
                    mark = event[1]
            #
            # end of for

            # after iterating through all events, if mark is not at dur
            #
            if mark != dur:

                # create event from mark->dur
                #
                events.append([mark, dur, {sym: 1.0}])

            # store events as the new events in self.graph_d
            #
            self.graph_d[level][sublevel][chan] = events
        #
        # end of for

        # exit gracefully
        #
        return True
    #
    # end of method

    def delete(self, sym, level, sublevel):
        """
        method: delete

        arguments:
         sym: symbol of events
         level: level of events
         sublevel: sublevel of events

        return:
         a boolean value indicating status

        description:
         This method deletes events of type sym
        """

        # display an informational message
        #
        if dbgl > ndt.BRIEF:
            print("%s (line: %s) %s: deleting events of type sym" %
                  (__FILE__, ndt.__LINE__, ndt.__NAME__))

        # try to access level/sublevel
        #
        try:
            self.graph_d[level][sublevel]
        except:
            print("Error: %s (line: %s) %s::%s %s (%d/%d)" %
                  (__FILE__, ndt.__LINE__, AnnGrEeg.__CLASS_NAME__,
                   ndt.__NAME__, "level/sublevel not found", level, sublevel))
            return False

        # iterate over channels at level/sublevel
        #
        for chan in self.graph_d[level][sublevel]:

            # get events at chan
            #
            events = self.graph_d[level][sublevel][chan]

            # keep only the events that do not contain sym
            #
            events = [e for e in events if sym not in e[2].keys()]

            # store events in self.graph_d
            #
            self.graph_d[level][sublevel][chan] = events
        #
        # end of for

        # exit gracefully
        #
        return True
    #
    # end of method

    def get_graph(self):
        """
        method: get_graph

        arguments:
         none

        return:
         entire graph data structure

        description:
         This method returns the entire graph, instead of a
         level/sublevel/channel.
        """

        return copy.deepcopy(self.graph_d)
    #
    # end of method

    def get_header(self):
        """
        method: get_graph

        arguments:
         none

        return:
         entire graph data structure

        description:
         This method returns the entire graph, instead of a
         level/sublevel/channel.
        """

        return copy.deepcopy(self.header_d)
    #
    # end of method

    def set_graph(self, graph):
        """
        method: set_graph

        arguments:
         graph: graph to set

        return:
         a boolean value indicating status

        description:
         This method sets the class data to graph.
        """

        self.graph_d = graph
        self.sort()
        return True
    #
    # end of method

    def set_header(self, header):
        """
        method: set_header

        arguments:
         graphs: header to set

        return:
         a Boolean value indicating status

        description:
         This method sets the class data to header.
        """

        self.header_d = header
        return True
    #
    # end of method

    def delete_graph(self):
        """
        method: delete_graph

        arguments:
         none

        return:
         none

        description:
         none
        """
        self.graph_d  = {}
        return True
#
# end of class

class Tse:
    """
    Class: Tse

    arguments:
     none

    description:
     This class contains methods to manipulate time-synchronous event files.
    """

    def __init__(self, montage_f = DEF_MONTAGE_FNAME, schema = None) -> None:
        """
        method: constructor

        arguments:
         montage_f: a montage file
         schema: a schema file

        return:
         none

        description:
         This method constructs Ag

        Note:
         montages and schema files are not used
         in the Lbl class, the constructor is only
         as such for convenience in AnnEeg
        """
        # set the class name
        #
        Tse.__CLASS_NAME__ = self.__class__.__name__

        # declare Graph object, to store annotations
        #
        self.data_d = AnnGrEeg()

        # Tse has no montage set to none
        #
        self.data_d.header_d[TSE_KEY_MONTAGE_FILE] = montage_f

        # set duration to default but has none
        #
        self.data_d.header_d[TSE_KEY_DURATION] = None
    #
    # end of method

    def load(self, fname):
        """
        method: load

        arguments:
         fname: annotation filename

        return:
         a boolean value indicating status

        description:
         This method loads an annotation from a file.
        """
        # display an informational message
        #
        if dbgl > ndt.BRIEF:
            print("%s (line: %s) %s: loading annotation from file" %
                  (__FILE__, ndt.__LINE__, ndt.__NAME__))

        # open file
        #
        with open(fname, nft.MODE_READ_TEXT) as fp:

            # get header data
            #

            # fetch bname information
            #
            self.data_d.header_d[TSE_KEY_BNAME] = \
                os.path.splitext(os.path.basename(fname))[0]

            # loop over lines in file
            #
            for line in fp:

                # clean up the line
                #
                line = line.replace(nft.DELIM_NEWLINE, nft.DELIM_NULL) \
                           .replace(nft.DELIM_CARRIAGE, nft.DELIM_NULL)
                check = line.replace(nft.DELIM_SPACE, nft.DELIM_NULL)

                # throw away commented, blank lines, version lines
                #
                if check.startswith(nft.DELIM_COMMENT) or \
                   check.startswith(nft.DEF_VERSION) or \
                   len(check) == 0:
                    continue

                # split the line
                #
                val = {}
                parts = line.split()

                try:
                    # loop over every part, starting after start/stop times
                    #
                    for i in range(2, len(parts), 2):

                        # create dict with label as key, prob as value
                        #
                        val[parts[i]] = float(parts[i+1])

                    # create annotation in AG
                    #
                    self.data_d.create(int(0), int(0), int(-1),
                                        float(parts[0]), float(parts[1]), val)
                except:
                    print("Error: %s (line: %s) %s::%s %s (%s)" %
                          (__FILE__, ndt.__LINE__, Tse.__CLASS_NAME__,
                           ndt.__NAME__, "invalid annotation", line))
                    return False

        # make sure graph is sorted after loading
        #
        self.data_d.sort()

        # exit gracefully
        #
        return True
    #
    # end of method

    def get(self, level, sublevel, channel):
        """
        method: get

        arguments:
         level: level of annotations to get
         sublevel: sublevel of annotations to get

        return:
         events at level/sublevel by channel

        description:
         This method gets the annotations stored in the AG at level/sublevel.
        """
        events = self.data_d.get(level, sublevel, channel)
        return events
    #
    # end of method

    def display(self, level, sublevel, fp = sys.stdout):
        """
        method: display

        arguments:
         level: level of events
         sublevel: sublevel of events
         fp: a file pointer

        return:
         a boolean value indicating status

        description:
         This method displays the events from a flat AG.
        """

        # display an informational message
        #
        if dbgl > ndt.BRIEF:
            print("%s (line: %s) %s: displaying events from flag AG" %
                  (__FILE__, ndt.__LINE__, ndt.__NAME__))

        # get graph
        #
        graph = self.get_graph()

        # try to access graph at level/sublevel
        #
        try:
            graph[level][sublevel]
        except:
            print("Error: %s (line: %s) %s::%s %s (%d/%d)" %
                  (__FILE__, ndt.__LINE__, Tse.__CLASS_NAME__, ndt.__NAME__,
                   "level/sublev not in graph", level, sublevel))
            return False

        # iterate over channels at level/sublevel
        #
        for chan in graph[level][sublevel]:

            # iterate over events for each channel
            #
            for event in graph[level][sublevel][chan]:
                start = event[0]
                stop = event[1]

                # create a string with all symb/prob pairs
                #
                pstr = nft.DELIM_NULL
                for symb in event[2]:
                    pstr += f" {symb:>8} {event[2][symb]:10.{PRECISION}f}"

                # display event
                #
                fp.write(f"{'ALL':>10}: {start:10.{PRECISION}f}" +
                         f" {stop:10.{PRECISION}f}{pstr}\n")

        # exit gracefully
        #
        return True
    #
    # end of method

    def write(self, ofile, level, sublevel):
        """
        method: write

        arguments:
         ofile: output file path to write to
         level: level of events
         sublevel: sublevel of events

        return:
         a boolean value indicating status

        description:
         This method writes the events to a .tse file
        """

        # display an informational message
        #
        if dbgl > ndt.BRIEF:
            print("%s (line: %s) %s: writing events to .tse file" %
                  (__FILE__, ndt.__LINE__, ndt.__NAME__))

        # make sure graph is sorted
        #
        self.data_d.sort()

        # get graph
        #
        graph = self.get_graph()

        # try to access the graph at level/sublevel
        #
        try:
            graph[level][sublevel]
        except:
            print("Error: %s (line: %s) %s::%s %s (%d/%d)" %
                  (__FILE__, ndt.__LINE__, Tse.__CLASS_NAME__,
                   ndt.__NAME__, "level/sublevel not in graph",
                   level, sublevel))
            return False

        # list to collect all events
        #
        events = []

        # iterate over channels at level/sublevel
        #
        for chan in graph[level][sublevel]:

            # iterate over events for each channel
            #
            for event in graph[level][sublevel][chan]:

                # store every channel's events in one list
                #
                events.append(event)

        # remove any events that are not unique
        #
        events = get_unique_events(events)

        # open file with write
        #
        with open(ofile, nft.MODE_WRITE_TEXT) as fp:

            # write version
            #
            fp.write("%s = %s\n" % (DELIM_TSE_VERSION, nft.TSE_VERSION))
            fp.write(nft.DELIM_NEWLINE)

            # iterate over events
            #
            for event in events:

                # create symb/prob string from dict
                #
                pstr = nft.DELIM_NULL
                for symb in event[2]:
                    pstr += f" {symb} {event[2][symb]:.{PRECISION}f}"

                # write event
                #
                fp.write(f"{event[0]:.{PRECISION}f}" +
                         f" {event[1]:.{PRECISION}f}{pstr}\n")

        # exit gracefully
        #
        return True
    #
    # end of method

    def add(self, dur, sym, level, sublevel):
        """
        method: add

        arguments:
         dur: duration of events
         sym: symbol of events
         level: level of events
         sublevel: sublevel of events

        return:
         a boolean value indicating status

        description:
         This method adds events of type sym.
        """

        return self.data_d.add(dur, sym, level, sublevel)
    #
    # end of method

    def delete(self, sym, level, sublevel):
        """
        method: delete

        arguments:
         sym: symbol of events
         level: level of events
         sublevel: sublevel of events

        return:
         a boolean value indicating status
         This method deletes events of type sym.

        description:
         none
        """

        return self.data_d.delete(sym, level, sublevel)
    #
    # end of method

    def get_graph(self):
        """
        method: get_graph

        arguments:
         none

        return:
         entire graph data structure

        description:
         This method accesses self.data_d.graph_d and returns
         the entire graph structure.
        """

        return self.data_d.get_graph()
    #
    # end of method

    def get_header(self):
        """
        method: get_header

        arguments:
         none

        return:
         entire graph data structure

        description:
         This method accesses self.data_d.header_d and returns
         header information
        """

        return self.data_d.header_d
    #
    # end of method

    def set_graph(self, graph):
        """
        method: set_graph

        arguments:
         graph: graph to set

        return:
         a boolean value indicating status

        description:
         This method sets the class data to graph.

        """

        return self.data_d.set_graph(graph)
    #
    # end of method

    def set_header(self, header):
        """
        method: set_header

        arguments:
         graph: graph to set

        return:
         a boolean value indicating status

        description:
         This method sets the class data to header
        """

        return self.data_d.set_header(header)
    #
    # end of method

    def set_file_duration(self,dur):
        """
        method: set_file_duration

        arguments:
         dur: duration of the file

        return:
         none

        description:
         This method allows us to set the file duration for the whole
         xml file
        """

        self.data_d.header_d[TSE_KEY_DURATION] = dur
        return
    #
    # end of method

    def get_file_duration(self):
        """
        method: get_file_duration

        arguments:
         none

        return:
         duration: the file duration (float)

        description:
         This method returns the file duration for the whole
         xml file
        """

        return float(self.data_d.header_d[TSE_KEY_DURATION])
    #
    # end of method
#
# end of class

class Lbl:
    """
    Class: Lbl

    arguments:
     none

    description:
     This class implements methods to manipulate label files.
    """

    def __init__(self, montage_f = None, schema = None) -> None:
        """
        method: constructor

        arguments:
         montage_f: a montage file
         schema: a schema file

        return:
         none

        description:
         This method constructs Ag

        Note:
         montages and schema files are not used
         in the Lbl class, the constructor is only
         as such for convenience in AnnEeg
        """

        # set the class name
        #
        Lbl.__CLASS_NAME__ = self.__class__.__name__

        # declare variables to store info parsed from lbl file
        #
        self.chan_map_d = {DEF_CHANNEL: DEF_TERM_BASED_IDENTIFIER}
        self.montage_lines_d = []
        self.symbol_map_d = {}
        self.num_levels_d = int(1)
        self.num_sublevels_d = {int(0): int(1)}

        # declare Graph object, to store annotations
        #
        self.data_d = AnnGrEeg()

        # set default duration but has none
        #
        self.data_d.header_d[LBL_KEY_DURATION] = None

        # set to default header information
        # will set montage file to lbl file in
        # load method
        #
        self.data_d.header_d[LBL_KEY_MONTAGE_FILE] = None
    #
    # end of method

    def load(self, fname):
        """
        method: load

        arguments:
         fname: annotation filename

        return:
         return: a boolean value indicating status

        description:
         This method loads an annotation from a file.
        """

        # display an informational message
        #
        if dbgl > ndt.BRIEF:
            print("%s (line: %s) %s: loading annotation from file" %
                  (__FILE__, ndt.__LINE__, ndt.__NAME__))

        # open file
        #
        fp = open(fname, nft.MODE_READ_TEXT)

        # fetch header information:
        # bname and pseudo montage file name
        #
        self.data_d.header_d[LBL_KEY_BNAME] = \
            os.path.splitext(os.path.basename(fname))[0]
        self.data_d.header_d[LBL_KEY_MONTAGE_FILE] = nft.get_fullpath(fname)

        # loop over lines in file
        #
        for line in fp:

            # clean up the line
            #
            line = line.replace(nft.DELIM_NEWLINE, nft.DELIM_NULL) \
                       .replace(nft.DELIM_CARRIAGE, nft.DELIM_NULL)

            # parse a single montage definition
            #
            if line.startswith(DELIM_LBL_MONTAGE):
                try:
                    chan_num, name, montage_line = \
                        self.parse_montage(line)
                    self.chan_map_d[chan_num] = name
                    self.montage_lines_d.append(montage_line)
                except:
                    print("Error: %s (line: %s) %s::%s: %s (%s)" %
                          (__FILE__, ndt.__LINE__, Lbl.__CLASS_NAME__,
                           ndt.__NAME__, "error parsing montage", line))
                    fp.close()
                    return False

            # parse the number of levels
            #
            elif line.startswith(DELIM_LBL_NUM_LEVELS):
                try:
                    self.num_levels_d = self.parse_numlevels(line)
                except:
                    print("Error: %s (line: %s) %s::%s: %s (%s)" %
                          (__FILE__, ndt.__LINE__, Lbl.__CLASS_NAME__,
                           ndt.__NAME__, "error parsing number of levels",
                           line))
                    fp.close()
                    return False

            # parse the number of sublevels at a level
            #
            elif line.startswith(DELIM_LBL_LEVEL):
                try:
                    level, sublevels = self.parse_numsublevels(line)
                    self.num_sublevels_d[level] = sublevels
                except:
                    print("Error: %s (line: %s) %s::%s: %s (%s)" %
                          (__FILE__, ndt.__LINE__, Lbl.__CLASS_NAME__,
                           ndt.__NAME__, "error parsing num of sublevels",
                           line))
                    fp.close()
                    return False

            # parse symbol definitions at a level
            #
            elif line.startswith(DELIM_LBL_SYMBOL):
                try:
                    level, mapping = self.parse_symboldef(line)
                    self.symbol_map_d[level] = mapping
                except:
                    print("Error: %s (line %s) %s::%s: %s (%s)" %
                          (__FILE__, ndt.__LINE__, Lbl.__CLASS_NAME__,
                           ndt.__NAME__, "error parsing symbols", line))
                    fp.close()
                    return False

            # parse a single label
            #
            elif line.startswith(DELIM_LBL_LABEL):
                try:
                    lev, sub, start, stop, chan, symbols = \
                        self.parse_label(line)
                except:
                    print("Error: %s (line %s) %s::%s: %s (%s)" %
                          (__FILE__, ndt.__LINE__, Lbl.__CLASS_NAME__,
                           ndt.__NAME__, "error parsing label", line))
                    fp.close()
                    return False

                # create annotation in AG
                #
                status = self.data_d.create(lev, sub, chan,
                                             start, stop, symbols)

        # close file
        #
        fp.close()

        # sort labels after loading
        #
        self.data_d.sort()

        # exit gracefully
        #
        return status
    #
    # end of method

    def get(self, level, sublevel, channel):
        """
        method: get

        arguments:
         level: level value
         sublevel: sublevel value

        return:
         events by channel from AnnGrEeg

        description:
         This method returns the events at level/sublevel
        """

        # get events from AG
        #
        events = self.data_d.get(level, sublevel, channel)

        # exit gracefully
        #
        return events
    #
    # end of method

    def display(self, level, sublevel, fp=sys.stdout):
        """
        method: display

        arguments:
         level: level of events
         sublevel: sublevel of events
         fp: a file pointer

        return:
         a boolean value indicating status

        description:
         This method displays the events from a flat AG
        """

        # display an informational message
        #
        if dbgl > ndt.BRIEF:
            print("%s (line: %s) %s: displaying events from flat AG" %
                  (__FILE__, ndt.__LINE__, ndt.__NAME__))

        # get graph
        #
        graph = self.get_graph()

        # try to access level/sublevel
        #
        try:
            graph[level][sublevel]
        except:
            sys.stdout.write("Error: %s (line: %s) %s::%s: %s (%d/%d)" %
                             (__FILE__, ndt.__LINE__, Lbl.__CLASS_NAME__,
                              ndt.__NAME__, "level/sublevel not found",
                              level, sublevel))
            return False

        # iterate over channels at level/sublevel
        #
        for chan in graph[level][sublevel]:

            # iterate over events at chan
            #
            for event in graph[level][sublevel][chan]:

                # find max probability
                #
                max_prob = max(event[2].values())

                # iterate over symbols in dictionary
                #
                for symb in event[2]:

                    # if the value of the symb equals the max prob
                    #
                    if event[2][symb] == max_prob:

                        # set max symb to this symbol
                        #
                        max_symb = symb
                        break


                # display event if chan_map_d is loaded.
                # chan_map_d will not be loaded in the event
                # of a conversion of file types
                #
                try:
                    fp.write(f"{self.chan_map_d[chan]:>10}: \
                                {event[0]:10.{PRECISION}f} \
                                {event[1]:10.{PRECISION}f} {max_symb:>8} \
                                {max_prob:10.{PRECISION}f}\n")
                except:
                    print("Error: %s (line: %s) %s::%s: %s " %
                          (__FILE__, ndt.__LINE__, Lbl.__CLASS_NAME__,
                           ndt.__NAME__, "chan_map_d is not loaded",))
                    return False


        # exit gracefully
        #
        return True
    #
    # end of method

    def write(self, ofile, level, sublevel):
        """
        method: write

        arguments:
         ofile: output file path to write to
         level: level of events
         sublevel: sublevel of events

        return:
         a boolean value indicating status

        description:
         This method writes events to a .lbl file.
        """

        # make sure graph is sorted
        #
        self.data_d.sort()

        # get graph
        #
        graph = self.get_graph()

        # try to access graph at level/sublevel
        #
        try:
            graph[level][sublevel]
        except:
            print("Error: %s (line: %s) %s: %s (%d/%d)" %
                  (__FILE__, ndt.__LINE__, ndt.__NAME__,
                   "level/sublevel not found", level, sublevel))
            return False

        # open file with write
        #
        with open(ofile, nft.MODE_WRITE_TEXT) as fp:

            # write version
            #
            fp.write(nft.DELIM_NEWLINE)
            fp.write("%s = %s\n" % (DELIM_LBL_VERSION, nft.LBL_VERSION))
            fp.write(nft.DELIM_NEWLINE)

            # variable to store the number of symbols
            #
            num_symbols = 0

            # ensure that symbol_map_d is loaded
            #
            if len(self.symbol_map_d.keys()) == 0:

                # create a dictionary at level 0 of symbol map
                #
                self.symbol_map_d[int(0)] = {}

                # if all channel exists we are converting from
                # tse to lbl. else we are converting from
                # xml or csv to lbl
                #
                if int(-1) in graph[level][sublevel]:

                    # iterate over all events stored in the 'all' channels
                    #
                    for event in graph[level][sublevel][int(-1)]:

                        # iterate over symbols in each event
                        #
                        for symbol in event[2]:

                            # if the symbol is not in the symbol map
                            #
                            if symbol not in self.symbol_map_d[0].values():

                                # map num_symbols integer to symbol
                                #
                                self.symbol_map_d[0][num_symbols] = symbol

                                # increment num_symbols
                                #
                                num_symbols += 1

                # file to convert is not of type tse so
                # the 'all' channel does not exist. iterate
                # through all events of all channels to
                # form symbol_map_d
                #
                else:

                    # iterate over all channels stored in all events
                    #
                    for channel in graph[level][sublevel]:

                        # iterate over all events stored in all channels
                        #
                        for event in graph[level][sublevel][channel]:

                            # iterate over symbols in each event
                            #
                            for symbol in event[2]:

                                # if the symbol is not in the symbol map
                                #
                                if symbol not in self.symbol_map_d[0].values():

                                    # map num_symbols integer to symbol
                                    #
                                    self.symbol_map_d[0][num_symbols] = symbol

                                    # increment num_symbols
                                    #
                                    num_symbols += 1

            # write montage to file
            #
            for line in self.montage_lines_d:
                fp.write("%s\n" % line)
            fp.write(nft.DELIM_NEWLINE)

            # write number of levels
            #
            fp.write("%s = %d\n" % (DELIM_LBL_NUM_LEVELS, self.num_levels_d))
            fp.write(nft.DELIM_NEWLINE)

            # write number of sublevels
            #
            for lev in self.num_sublevels_d:
                fp.write("%s[%d] = %d\n" %
                         (DELIM_LBL_LEVEL, lev, self.num_sublevels_d[lev]))
            fp.write(nft.DELIM_NEWLINE)

            # write symbol definitions
            #
            for lev in self.symbol_map_d:
                fp.write("%s[%d] = %s\n" %
                         (DELIM_LBL_SYMBOL, lev, str(self.symbol_map_d[lev])))
            fp.write(nft.DELIM_NEWLINE)

            # iterate over channels at level/sublevel
            #
            for chan in graph[level][sublevel]:

                # iterate over events in chan
                #
                for event in graph[level][sublevel][chan]:

                    # create string for probabilities
                    #
                    pstr = f"{nft.DELIM_OPEN}"

                    # iterate over symbol map
                    #
                    for symb in self.symbol_map_d[level].values():

                        # if the symbol is found in the event
                        #
                        if symb in event[2]:
                            pstr += (str(event[2][symb]) + nft.DELIM_COMMA +
                                     nft.DELIM_SPACE)
                        else:
                            pstr += '0.0' + nft.DELIM_COMMA + nft.DELIM_SPACE

                    # remove the ', ' from the end of pstr
                    #
                    pstr = pstr[:len(pstr) - 2] + f"{nft.DELIM_CLOSE}" + \
                        f"{nft.DELIM_BCLOSE}"

                    # write event
                    #
                    fp.write(f"label = {level}, {sublevel}," +
                             f" {event[0]:.{PRECISION}f},"+
                             f" {event[1]:.{PRECISION}f}, {chan}, {pstr}\n")

        # exit gracefully
        #
        return True
    #
    # end of method

    def add(self, dur, sym, level, sublevel):
        """
        method: add

        arguments:
         dur: duration of events
         sym: symbol of events
         level: level of events
         sublevel: sublevel of events

        return:
         a boolean value indicating status

        description:
         This method adds events of type sym
        """

        return self.data_d.add(dur, sym, level, sublevel)
    #
    # end of method

    def delete(self, sym, level, sublevel):
        """
        method: delete

        arguments:
         sym: symbol of events
         level: level of events
         sublevel: sublevel of events

        return:
         a boolean value indicating status

        description:
         This method deletes events of type sym
        """

        return self.data_d.delete(sym, level, sublevel)
    #
    # end of method

    def get_graph(self):
        """
        method: get_graph

        arguments:
         none

        return:
         entire graph data structure

        description:
         This method accesses self.graph_d and returns
         the entire graph structure.
        """

        return self.data_d.get_graph()
    #
    # end of method

    def get_header(self):
        """
        method: get_header

        arguments:
         none

        return:
         entire graph data structure

        description:
         This method accesses self.data_d.header_d and returns
         header information
        """

        return self.data_d.header_d
    #
    # end of method

    def set_graph(self, graph):
        """
        method: set_graph

        arguments:
         graph: graph to set

        return:
         a boolean value indicating status

        description:
         This method sets the class data to graph
        """

        return self.data_d.set_graph(graph)
    #
    # end of method

    def set_header(self, header):
        """
        method: set_header

        arguments:
         graph: graph to set

        return:
         a boolean value indicating status

        description:
         This method sets the class data to header
        """

        return self.data_d.set_header(header)
    #
    # end of method

    def set_file_duration(self,dur):
        """
        method: set_file_duration

        arguments:
         dur: duration of the file

        return:
         none

        description:
         This method allows us to set the file duration for the whole
         xml file
        """

        self.data_d.header_d[LBL_KEY_DURATION] = dur
        return

    def get_file_duration(self):
        """
        method: get_file_duration

        arguments:
         none

        return:
         duration: the file duration (float)

        description:
         This method returns the file duration for the whole
         xml file
        """

        return float(self.data_d.header_d[LBL_KEY_DURATION])

    def parse_montage(self, line):
        """
        method: parse_montage

        arguments:
         line: line from label file containing a montage channel definition
         none

        return:
         channel_number: an integer containing the channel map number
         channel_name: the channel name corresponding to channel_number
         montage_line: entire montage def line read from file

        description:
         This method parses a montage line into it's channel name and number.
         Splitting a line by two values easily allows us to get an exact
         value/string from a line of definitions
        """

        # display an informational message
        #
        if dbgl > ndt.BRIEF:
            print("%s (line: %s) %s: parsing montage by channel name, number" %
                  (__FILE__, ndt.__LINE__, ndt.__NAME__))

        # split between '=' and ',' to get channel number
        #
        channel_number = int(
            line.split(nft.DELIM_EQUAL)[1].split(nft.DELIM_COMMA)[0].strip())

        # split between ',' and ':' to get channel name
        #
        channel_name = line.split(
            nft.DELIM_COMMA)[1].split(nft.DELIM_COLON)[0].strip()

        # remove chars from montage line
        #
        montage_line = line.strip().strip(nft.DELIM_NEWLINE)

        # exit gracefully
        #
        return [channel_number, channel_name, montage_line]
    #
    # end of method

    def parse_numlevels(self, line):
        """
        method: parse_numlevels

        arguments:
         line: line from label file containing the number of levels

        return:
         an integer containing the number of levels defined in the file

        description:
         This method parses the number of levels in a file.
        """

        # split by '=' and remove extra characters
        #
        return int(line.split(nft.DELIM_EQUAL)[1].strip())
    #
    # end of method

    def parse_numsublevels(self, line):
        """
        method: parse_numsublevels

        arguments:
         line: line from label file containing number of sublevels in level

        return:
         level: level from which amount of sublevels are contained
         sublevels: amount of sublevels in particular level

        description:
         This method parses the number of sublevels per level in the file
        """

        # display an informational message
        #
        if dbgl > ndt.BRIEF:
            print("%s (line: %s) %s: parsing number of sublevels per level" %
                  (__FILE__, ndt.__LINE__, ndt.__NAME__))

        # split between '[' and ']' to get level
        #
        level = int(line.split(
            nft.DELIM_OPEN)[1].split(nft.DELIM_CLOSE)[0].strip())

        # split by '=' and remove extra characters
        #
        sublevels = int(line.split(nft.DELIM_EQUAL)[1].strip())

        # exit gracefully
        #
        return [level, sublevels]
    #
    # end of method

    def parse_symboldef(self, line):
        """
        method: parse_symboldef

        arguments:
         line: line from label file containing symbol definition for a level

        return:
         level: an integer containing the level of this symbol definition
         mappings: a dict containing the mapping of symbols for this level

        description:
         This method parses a symbol definition line into a specific level,
         the corresponding symbol mapping as a dictionary.
        """

        # split by '[' and ']' to get level of symbol map
        #
        level = int(line.split(nft.DELIM_OPEN)[1].split(nft.DELIM_CLOSE)[0])

        # remove all characters to remove, and split by ','
        #
        syms = nft.DELIM_NULL.join(c for c in line.split(nft.DELIM_EQUAL)[1]
                                   if c not in REM_CHARS)

        symbols = syms.split(nft.DELIM_COMMA)

        # create a dict from string, split by ':'
        #   e.g. '0: seiz' -> mappings[0] = 'seiz'
        #
        mappings = {}
        for s in symbols:
            mappings[int(s.split(nft.DELIM_COLON)[0])] = \
                s.split(nft.DELIM_COLON)[1]

        # exit gracefully
        #
        return [level, mappings]
    #
    # end of method

    def parse_label(self, line):
        """
        method: parse_label

        arguments:
         line: line from label file containing an annotation label

        return:
         all information read from .ag file

        description:
         this method parses a label definition into the values
         found in the label
        """

        # dict to store symbols/probabilities
        #
        symbols = {}

        # remove characters to remove, and split data by ','
        #
        lines = nft.DELIM_NULL.join(c for c in line.split(nft.DELIM_EQUAL)[1]
                                    if c not in REM_CHARS)

        data = lines.split(nft.DELIM_COMMA)

        # separate data into specific variables
        #
        level = int(data[0])
        sublevel = int(data[1])
        start = float(data[2])
        stop = float(data[3])

        # the channel value supports either 'all' or channel name
        #
        try:
            channel = int(data[4])
        except:
            channel = int(-1)

        # parse probabilities
        #
        probs = lines.split(
            nft.DELIM_OPEN)[1].strip(nft.DELIM_CLOSE).split(nft.DELIM_COMMA)

        # set every prob in probs to type float
        #
        probs = list(map(float, probs))

        # convert the symbol map values to a list
        #
        map_vals = list(self.symbol_map_d[level].values())

        # iterate over symbols
        #
        for i in range(len(self.symbol_map_d[level].keys())):

            if probs[i] > 0.0:

                # set each symbol equal to the corresponding probability
                #
                symbols[map_vals[i]] = probs[i]

        # exit gracefully
        #
        return [level, sublevel, start, stop, channel, symbols]
    #
    # end of method

    def update_montage(self, montage_file, from_nedc_eas = False):
        """
        method: update_montage

        arguments:
         montage_file: montage file

        return:
         a boolean value indicating status

        description:
         this method updates a montage file to class value
        """

        # fetch montage files full path
        #
        montage_file = nft.get_fullpath(montage_file)

        # ensure motnage path exists
        #
        if os.path.isfile(montage_file) == False:
            print("Error: %s (line: %s) %s: montage file doesn't exist (%s)" %
                (__FILE__, ndt.__LINE__, ndt.__NAME__, montage_file))
            sys.exit(os.EX_SOFTWARE)

        # update new montage file, if input montage file is None, update
        # with the default montage
        #

        if montage_file is None or montage_file == "None":
            self.data_d.header_d[LBL_KEY_MONTAGE_FILE] = \
                nft.get_fullpath(DEF_MONTAGE_FNAME)
        else:
            self.data_d.header_d[LBL_KEY_MONTAGE_FILE] = \
                nft.get_fullpath(montage_file)

        if from_nedc_eas:

            # fetch montage information if new map format is in use
            #
            map_dict = parse_nedc_eas_map_to_montage_definition_new(montage_file)

            # if map_dict is empty than fetch the montage from the map
            # utalizing the old map format
            #
            if not map_dict:
                map_dict = parse_nedc_eas_map_to_montage_defintion(montage_file)

            # format map_dict infromation for parsing
            #
            line = f"{DELIM_LBL_SYMBOL}[0] = {str(map_dict)}"

            line = line.replace(nft.DELIM_NEWLINE, nft.DELIM_NULL) \
                        .replace(nft.DELIM_CARRIAGE, nft.DELIM_NULL)

            # attempt to parse symbol data
            #
            try:
                level, mapping = self.parse_symboldef(line)
                self.symbol_map_d[level] = mapping
            except:
                print("Error: %s (line %s) %s::%s: %s (%s)" %
                    (__FILE__, ndt.__LINE__, Lbl.__CLASS_NAME__,
                    ndt.__NAME__, "error parsing montage", line))
                return False

        else:

            # fetch montage file path
            #
            montage_name = self.data_d.header_d[LBL_KEY_MONTAGE_FILE]
            montage_path = nft.get_fullpath(montage_name)

            # open file
            #
            montage_fp = open(montage_path, nft.MODE_READ_TEXT)
            # loop over lines in file
            #
            lines = montage_fp.readlines()

            for line in lines:
                # clean up the line
                #
                line = line.replace(nft.DELIM_NEWLINE, nft.DELIM_NULL) \
                        .replace(nft.DELIM_CARRIAGE, nft.DELIM_NULL)

                # parse a single montage definition
                #
                if line.startswith(DELIM_LBL_MONTAGE):
                    try:
                        chan_num, name, montage_line = \
                            self.parse_montage(line)
                        self.chan_map_d[chan_num] = name
                        # self.data_d.header_d[LBL_KEY_MONTAGE_FILE] \
                            #            .append(montage_line)
                    except:
                        print("Error: %s (line %s) %s::%s: %s (%s)" %
                            (__FILE__, ndt.__LINE__, Lbl.__CLASS_NAME__,
                            ndt.__NAME__, "error parsing montage", line))
                        montage_file.close()
                        return False

                # parse symbol definitions at a level
                #
                elif line.startswith(DELIM_LBL_SYMBOL):
                    try:
                        level, mapping = self.parse_symboldef(line)
                        self.symbol_map_d[level] = mapping
                    except:
                        print("Error: %s (line %s) %s::%s: %s (%s)" %
                            (__FILE__, ndt.__LINE__, Lbl.__CLASS_NAME__,
                            ndt.__NAME__, "error parsing symbols", line))
                        montage_fp.close()
                        return False
#
# end of class

class Csv:
    """
    Class: Csv

    arguments:
     none

    description:
     This class contains methods to manipulate comma separated value files.
    """

    def __init__(self, montage_f = DEF_MONTAGE_FNAME, schema = None) \
        -> None:
        """
        method: constructor

        arguments:
         none

        return:
         none

        description:
         none

        Note:
         schema is present only for convenient calls in AnnEeg
        """

        Csv.__CLASS_NAME__ = self.__class__.__name__

        # declare General object, to store annotations and header data
        #
        self.data_d = AnnGrEeg()

        # fill header montage file data
        #
        self.data_d.header_d[CSV_KEY_MONTAGE_FILE] = montage_f

        # fill header duration with default value
        #
        self.data_d.header_d[CSV_KEY_DURATION] = None

        # set the defualt channel map info
        #
        self.channel_map_label = {DEF_CHANNEL:DEF_TERM_BASED_IDENTIFIER}

        # if the motnage file exists attempt to load it
        #
        if montage_f is not None and \
           os.path.isfile(nft.get_fullpath(montage_f)) == True:

            # load the montage
            #
            self.parse_montage(montage_f)

    #
    # end of method

    def load(self, fname):
        """
        method: load

        arguments:
         fname: annotation filename

        return:
         a boolean value indicating status

        description:
         This method loads an annotation from a file.
        """

        # display an informational message
        #
        if dbgl > ndt.BRIEF:
            print("%s (line: %s) %s: loading annotation from file" %
                  (__FILE__, ndt.__LINE__, ndt.__NAME__))

        # create an incrementing index variable representing
        # the channel index
        #
        channel_idx = int(0)
        known_channels = [self.channel_map_label.values()]
        channel_map_label_temp = dict()
        
        with open(fname, nft.MODE_READ_TEXT) as fp:

            # fetch bname information
            #
            self.data_d.header_d[CSV_KEY_BNAME] = os.path.splitext(
                os.path.basename(fname))[0]

            # loop over all lines of the file and look for channles that
            # were not present in the montage for safteu
            #
            for line in fp:

                # ignore comments, blank line, csv header
                #
                if line.startswith(nft.DELIM_COMMENT) or \
                   DELIM_CSV_LABELS in line or \
                   len(line) == 0 :
                    continue

                # get the annotation label file for each line
                #
                channel = line.split(nft.DELIM_COMMA)[0]
                
                # if the channel map label still assumes a TERM based
                # approach load the montage information found by parsing
                # the csv instead
                #
                if channel not in known_channels:
                    
                    # append to the channel_map dictionary to create
                    # the corresponding channel number and name
                    #
                    channel_map_label_temp[int(channel_idx)] = channel
                    
                    # increment channel index
                    #
                    channel_idx += int(1)

                    known_channels.append(channel)

            # rewind pointer
            #
            fp.seek(0)
            
            # if no montage has been loaded except for the defualt TERM mapping
            # update the channel map.
            #
            if len(self.channel_map_label) == 1 and channel_map_label_temp:

                self.channel_map_label.update(channel_map_label_temp)
                
            for line_number, line in enumerate(fp):

                # remove space, "\n" and "\r" just case in it is written on a
                # a window operating machine
                #
                line = line.replace(nft.DELIM_NEWLINE, nft.DELIM_NULL) \
                           .replace(nft.DELIM_CARRIAGE, nft.DELIM_NULL) \
                           .replace(nft.DELIM_SPACE, nft.DELIM_NULL)

                # fetch montage path
                #
                montage_path = self.data_d.header_d[CSV_KEY_MONTAGE_FILE]

                # if montage path is DEFAULT check if fname has another
                # montage specified in header if so use fname's specified
                # montage file
                #
                if line.startswith(nft.DELIM_COMMENT + DELIM_CSV_MONTAGE_FILE) \
                   and montage_path == DEF_MONTAGE_FNAME:

                    # set header_d's montage attribute to montage
                    # file name found in fname
                    #
                    self.data_d.header_d[CSV_KEY_MONTAGE_FILE] = \
                        line.split(nft.DELIM_EQUAL)[int(-1)]

                # if we find the file duration
                #
                if line.startswith(nft.DELIM_COMMENT +  DELIM_CSV_DURATION):

                    # fetch and clean up duration info
                    #
                    self.data_d.header_d[CSV_KEY_DURATION] = line \
                               .replace(DELIM_CSV_SECS, nft.DELIM_NULL) \
                               .split(nft.DELIM_EQUAL)[int(-1)]

                # ignore comments, blank line, csv header
                #
                if line.startswith(nft.DELIM_COMMENT) or \
                    DELIM_CSV_LABELS in line or \
                    len(line) == 0 :
                    continue

                # get the annotation label file for each line
                #
                channel, start_time, stop_time, label, confidence = \
                    line.split(nft.DELIM_COMMA)

                # If the annotation is term base
                # then we should handle it
                #
                if channel == DEF_TERM_BASED_IDENTIFIER:

                    # uses the index of -1 if it is a term based event
                    #
                    self.data_d.create(int(0), int(0), int(-1),
                            float(start_time), float(stop_time),
                            {label:float(confidence)})

                # else assume tha channels are in the specified montage
                # order and create the graph
                #
                else:
    
                    # get the correct index for the channel
                    #
                    for ind, channel_lb in self.channel_map_label.items():
                        if channel_lb == channel:
                            channel_ind = ind

                    self.data_d.create(int(0), int(0), channel_ind,
                                float(start_time), float(stop_time),
                                {label:float(confidence)})


        self.data_d.sort()
        
        # exit gracefully
        #
        return True
    #
    # end of method

    def write(self, ofile, level, sublevel):
        """
        method: write

        arguments:
         ofile: output file path to write to
         level: level of events
         sublevel: sublevel of events

        return:
         a boolean value indicating status

        description:
         This method writes the events to a .csv file
        """

        # display an informational message
        #
        if dbgl > ndt.BRIEF:
            print("%s (line: %s) %s: writing events to .csv file" %
                  (__FILE__, ndt.__LINE__, ndt.__NAME__))

        # sort the graph
        # just in case it was set without using the load method
        #
        self.data_d.sort()

        # get the graph
        #
        graph = self.get_graph()

        # try to access the graph at level/sublevel
        #
        try:
            graph[level][sublevel]
        except:
            print("Error: %s (line: %s) %s::%s %s (%d/%d)" %
                  (__FILE__, ndt.__LINE__, Csv.__CLASS_NAME__,
                   ndt.__NAME__, "level/sublevel not in graph",
                   level, sublevel))
            return False

        # make the directory if a path is passed
        #
        if len(ofile.split(nft.DELIM_SLASH)) > 1:
            os.makedirs(os.path.dirname(ofile), exist_ok=True)

        # write the header data
        #
        self.write_header(ofile)

        # open file to write
        #
        with open(ofile, nft.MODE_APPEND_TEXT, newline=nft.DELIM_NEWLINE) as fp:

            # add all the event from the graphing object
            #
            for channel_ind, events in graph[level][sublevel].items():

                for event in events:
                    start_time, stop_time = event[0], event[1]

                    # takes the form {'label':confidence}
                    # then unzip it then cast it to the variable where it gets
                    # unzip again as the first unzip makes it turn into a tuple
                    #
                    [*label], [*confidence] = zip(*event[-1].items())

                    fp.write(f"{self.channel_map_label[channel_ind]},"
                             f"{start_time:.{PRECISION}f},"
                             f"{stop_time:.{PRECISION}f},"
                             f"{label[0]},"
                             f"{confidence[0]:.{PRECISION}f}\n")

        # exit gracefully
        #
        return True
    #
    # end of method

    def write_header(self, ofile):
        """
        method: write_header

        arguments:
         ofile: csv filename
         none

        return:
         a boolean value indicating status

        description:
         This method writes the header
        """

        # display an informational message
        #
        if dbgl > ndt.BRIEF:
            print("%s (line: %s) %s: writing header to .csv file" %
                  (__FILE__, ndt.__LINE__, ndt.__NAME__))

        # open file to write
        #
        with open(ofile, nft.MODE_WRITE_TEXT, newline=nft.DELIM_NEWLINE) as fp:

            # write version
            #
            fp.write(f"# {DELIM_CSV_VERSION} = {nft.CSV_VERSION}\n")

            # write the bname
            #
            fp.write("# %s = %s\n" %
                     (DELIM_CSV_BNAME,
                      ofile.split(nft.DELIM_SLASH)[-1].split('.')[0]))

            # fetch the duration
            #
            dur = float(self.data_d.header_d[CSV_KEY_DURATION])

            # write the duration
            #
            fp.write(f"# {DELIM_CSV_DURATION} = {dur:.4f} {DELIM_CSV_SECS}\n")

            # write the montage file
            #
            if self.data_d.header_d[CSV_KEY_MONTAGE_FILE] is not None:
                montage_path = self.data_d.header_d[CSV_KEY_MONTAGE_FILE]
                montage_fname = montage_path.split(nft.DELIM_SLASH)[-1]
            else:
                montage_fname = None
            fp.write(f"# {DELIM_CSV_MONTAGE_FILE} = {montage_fname}\n")
            fp.write(nft.DELIM_COMMENT)
            fp.write(nft.DELIM_NEWLINE)

            # write the csv header
            #
            fp.write(f"{DELIM_CSV_LABELS}\n")

        # exit gracefully
        #
        return True
    #
    # end of method

    def display(self, level, sublevel, fp=sys.stdout):
        """
        method: display

        arguments:
         level: level of events
         sublevel: sublevel of events
         fp: a file pointer

        return:
         a boolean value indicating status

        description:
         This method displays the events from a flat AG.
        """

        # display an informational message
        #
        if dbgl > ndt.BRIEF:
            print("%s (line: %s) %s: displaying events from flag AG" %
                  (__FILE__, ndt.__LINE__, ndt.__NAME__))

        # get graph
        #
        graph = self.get_graph()

        # try to access graph at level/sublevel
        #
        try:
            graph[level][sublevel]
        except:
            print("Error: %s (line: %s) %s::%s %s (%d/%d)" %
                  (__FILE__, ndt.__LINE__, Tse.__CLASS_NAME__, ndt.__NAME__,
                   "level/sublev not in graph", level, sublevel))
            return False

        # iterate over channels at level/sublevel
        #
        for chan in graph[level][sublevel]:

            # iterate over events for each channel
            #
            for event in graph[level][sublevel][chan]:

                # find max probability
                #
                max_prob = max(event[2].values())

                # iterate over symbols in dictionary
                #
                for symb in event[2]:

                    # if the value of the symb equals the max prob
                    #
                    if event[2][symb] == max_prob:

                        # set max symb to this symbol
                        #
                        max_symb = symb
                        break

                # display event
                #
                if max_prob is not None:
                    fp.write(f"{self.channel_map_label[chan]:>10}: \
                            {event[0]:10.{PRECISION}f} \
                            {event[1]:10.{PRECISION}f} \
                            {max_symb:>8} \
                            {max_prob:10.{PRECISION}f}\n")
                else:
                    fp.write(f"{self.channel_map_label[chan]:>10}: \
                                {event[0]:10.{PRECISION}f} \
                                {event[1]:10.{PRECISION}f} \
                                {max_symb:>8}\n")
        # exit gracefully
        #
        return True
    #
    # end of method

    def validate(self, fname):
        """
        method: validate

        arguments:
         fname: the file name

        return:
         a boolean value indicating status

        description:
         This method returns True if the metadata is a valid csv header.
        """

        # display debugging information
        #
        if dbgl > ndt.BRIEF:
            print("%s (line: %s) %s::%s: checking for csv (%s)" %
                  (__FILE__, ndt.__LINE__, AnnEeg.__CLASS_NAME__,
                   ndt.__NAME__, fname))
        # open the file
        #
        fp = open(fname, nft.MODE_READ_TEXT)
        if fp is None:
            print("Error: %s (line: %s) %s::%s: error opening file (%s)" %
                  (__FILE__, ndt.__LINE__, AnnEeg.__CLASS_NAME__,
                   ndt.__NAME__, fname))
            return False

        # read the first line in the file
        #
        header = fp.readline()
        if dbgl > ndt.BRIEF:
            print("%s (line: %s) %s::%s: header (%s)" %
                  (__FILE__, ndt.__LINE__, AnnEeg.__CLASS_NAME__,
                   ndt.__NAME__, header))
        fp.close()
        # exit gracefully:
        #
        if nft.CSV_VERSION in header.split(nft.DELIM_EQUAL)[-1].strip():
            return True
        else:
            if dbgl > ndt.BRIEF:
                print("Error: %s (line: %s) %s::%s: Not a valid CSV (%s)" %
                      (__FILE__, ndt.__LINE__, AnnEeg.__CLASS_NAME__,
                       ndt.__NAME__, fname))
            return False
    #
    # end of method

    def parse_montage(self, montage_f):
        """
        method: parse_montage

        arguments:
         montage_f: a montage file

        return:
         a boolean value indicating status

        description:
         This method updates the channel_map_label variable
         based on the inputted montage file

        Note:
         Please expand any environment variable before passing
         it into the function since the function does not expand
         it for you.
        """

        # fetch the montage files full path
        #
        montage_f = nft.get_fullpath(montage_f)

        # ensure parameter file exists
        #
        if os.path.isfile(montage_f) == False:
            print("ERROR: %s (line: %s) %s: montage file doesn't exist (%s)" %
                  (__FILE__, ndt.__LINE__, ndt.__NAME__, montage_f))
            return False

        # open the montage file
        #
        montage_fp = open(montage_f, nft.MODE_READ_TEXT)
        if montage_fp is None:
            print("Error: %s (line: %s) %s::%s: error opening file (%s)" %
                  (__FILE__, ndt.__LINE__, Csv.__CLASS_NAME__,
                   ndt.__NAME__, montage_f))
            return False

        # check if the dictionary has been populated once
        # this will be true when the dictionary is not-empty
        #
        if len(self.channel_map_label) > 1:
            self.channel_map_label.clear()

        for line in montage_fp:

            line = line.replace(nft.DELIM_NEWLINE, nft.DELIM_NULL) \
                        .replace(nft.DELIM_CARRIAGE, nft.DELIM_NULL) \
                        .replace(nft.DELIM_SPACE, nft.DELIM_NULL)

            # extract the information if present
            # or ignore the current line
            #
            if line.startswith(DELIM_CSV_MONTAGE):
                channel_number, channel_name = re.findall(
                    DEF_REGEX_MONTAGE_FILE, line).pop()
            else:
                continue

            # append to the channel_map dictionary to create
            # the corresponding channel number and name
            #
            self.channel_map_label[int(channel_number)] = channel_name

        # exit gracefully
        #
        return True
    #
    # end of method

    def set_file_duration(self, dur):
        """
        method: set_file_duration

        arguments:
         duration of the file

        return:
         none

        description:
         This method allows us to set the file duration for the whole
         csv file
        """

        self.data_d.header_d[CSV_KEY_DURATION] = dur
        return
    #
    # end of method

    def get_file_duration(self):
        """
        method: get_file_duration

        arguments:
         none

        return:
         duration: the file whole file duration (float)
         none

        description:
         This method returns the file duration for the whole
         csv file
        """

        return float(self.data_d.header_d[CSV_KEY_DURATION])

    def add(self, dur, sym, level, sublevel):
        """
        method: add

        arguments:
         dur: duration of events
         sym: symbol of events
         level: level of events
         sublevel: sublevel of events

        return:
         a boolean value indicating status

        description:
         This method adds events of type sym.
        """

        return self.data_d.add(dur, sym, level, sublevel)
    #
    # end of method

    def delete(self,sym, level, sublevel):
        """
        method: delete

        arguments:
         sym: symbol of events
         level: level of events
         sublevel: sublevel of events

        return:
         a boolean value indicating status

        description:
         This method deletes events of type sym.
        """

        return self.data_d.delete(sym, level, sublevel)
    #
    # end of method

    def get(self, level, sublevel, channel):
        """
        method: get

        arguments:
         level: level of events
         sublevel: sublevel of events
         channel: the channel

        return:
         none

        description:
         none
        """

        events = self.data_d.get(level, sublevel, channel)

        return events
    #
    # end of method

    def get_graph(self):
        """
        method: get_graph

        arguments:
         none

        return:
         entire graph data structure

        description:
         This method accesses self.data_d and returns
         the entire graph structure.
        """

        return self.data_d.get_graph()
    #
    # end of method

    def get_header(self):
        """
        method: get_header

        arguments:
         none

        return:
         entire graph data structure

        description:
         This method accesses self.data_d.header_d and returns
         header information
        """

        return self.data_d.header_d
    #
    # end of method

    def set_graph(self, graph):
        """
        method: set_graph

        arguments:
         graph: graph to set

        return:
         a boolean value indicating status

        description:
         This method sets the class data to graph.
        """

        return self.data_d.set_graph(graph)
    #
    # end of method

    def set_header(self, header):
        """
        method: set_header

        arguments:
         graph: graph to set

        return:
         a boolean value indicating status

        description:
         This method sets the class data to header
        """

        return self.data_d.set_header(header)
    #
    # end of method

# class: Xml
#
class Xml:
    """
    Class: Xml

    arguments:
     none

    description:
     none
    """

    def __init__(self, montage_f = DEF_MONTAGE_FNAME, schema = DEF_XML_FNAME) -> None:
        """
        method: constructor

        arguments:
         none

        return:
         none

        description:
         none
        """

        # set the class name
        #
        Xml.__CLASS_NAME__ = self.__class__.__name__

        # declare General object, to store annotations and header data
        #
        self.data_d = AnnGrEeg()

        # fill header montage file path
        #
        self.data_d.header_d[XML_KEY_MONTAGE_FILE] = montage_f

        # fill header duration with default value
        #
        self.data_d.header_d[XML_KEY_DURATION] = None

        # create schema, schema path, and channel storage variables
        #
        self.schema = schema
        self.channel_map_label = {DEF_CHANNEL:DEF_TERM_BASED_IDENTIFIER}

        # if the motnage file exists attempt to load it
        #
        if montage_f is not None and \
           os.path.isfile(nft.get_fullpath(montage_f)) == True:

            # load the montage
            #
            self.parse_montage(montage_f)

        # exit gracefully
        #
        return None
    #
    # end of method

    def load(self, fname):
        """
        method: load

        arguments:
         fname: annotation filename

        return:
         a boolean value indicating status

        description:
         This method loads an annotation from a file.
        """

        status = self.validate(fname)

        if not status:
            print("Error: %s (line: %s) %s: invalid xml file (%s)" %
                  (__FILE__, ndt.__LINE__, ndt.__NAME__, fname))
            return False
        else:

            # fetch root
            #
            root = et.parse(fname).getroot()

            # fetch montage information if present and if
            # a montage file was not specified in xml's __init__
            #
            file_montage = root.find(XML_TAG_MONTAGE_TAG).text
            user_montage = self.data_d.header_d[XML_KEY_MONTAGE_FILE]

            # if a montage file was not specified in xml's __init__
            # set new montage file
            #
            if root.find(XML_TAG_MONTAGE_TAG) is not None and \
               user_montage == DEF_MONTAGE_FNAME:

                # set fetched montage file
                #
                self.data_d.header_d[XML_KEY_MONTAGE_FILE] = str(file_montage)

            # fetch bname info
            #
            self.data_d.header_d[XML_KEY_BNAME] = \
                os.path.splitext(os.path.basename(fname))[0]

            # fetch duration info
            #
            duration = root.find(XML_TAG_DURATION).text

            # load duration info into header_d
            #
            self.data_d.header_d[XML_KEY_DURATION] = \
                duration.replace(XML_FMT_SECS, nft.DELIM_NULL)

            # fetch graph info
            #
            xml_dict = self.tree_to_dict(root)

            # note: This XML format assumes that we are doing annotations on
            #       0,0 level only. Chances are, we would need to revisit the
            #       XML if we want it to support multi-level annotations.
            #
            graph = {0: {0: dict(xml_dict)}}

            # set the graphing object to be the newly parsed XML
            #
            self.data_d.graph_d = graph

        # load the montage channel map if not done in __init__
        #
        channels = [channel.get('name') for channel in root.findall(".//channel")]

        if DEF_CHANNEL in list(self.channel_map_label.keys()) and \
           DEF_TERM_BASED_IDENTIFIER not in channels:

            # assume channels are in same order as the montage
            #
            for channel_idx, channel in enumerate(channels):

                # append to the channel_map dictionary to create
                # the corresponding channel number and name
                #
                self.channel_map_label[int(channel_idx)] = channel

        # exit gracefully
        #
        return True
    #
    # end of method

    def write(self, ofile, level, sublevel):
        """
        method: write

        arguments:
         ofile: output file path to write to
         level: level of events
         sublevel: sublevel of events

        return:
         a boolean value indicating status

        description:
         This method writes the events to a .xml file
        """

        # sort the graph
        #
        self.data_d.sort()

        # get graph
        #
        graph = self.get_graph()

        # local variables
        #
        file_start_time, file_end_time = float("inf"), float("-inf")
        channels = list()
        print("graph = %s" % graph)
        print("self.channel_map_labels = %s" % self.channel_map_label)
        # get the durations, end points and channels
        #
        for channel_index, data in graph[0][0].items():

            channels.append(self.channel_map_label[channel_index])

            for start, stop, _ in data:
                file_start_time = min(file_start_time, start)
                file_end_time = max(file_end_time, stop)

        # set up the root
        #
        root = et.Element(XML_TAG_ROOT)

        # add the bname
        #
        bname = et.SubElement(root, XML_TAG_BNAME)
        bname.text = path(ofile).stem

        # fetch the duration
        #
        dur = float(self.data_d.header_d[XML_KEY_DURATION])

        # add the duration
        #
        duration = et.SubElement(root, XML_TAG_DURATION)
        duration.text = f"{dur:.4f} {XML_FMT_SECS}"

        # add the montage file
        #
        montage_file = et.SubElement(root, XML_TAG_MONTAGE_FILE)
        montage_file_path = self.data_d.header_d[XML_KEY_MONTAGE_FILE]
        if montage_file_path is not None:
            montage_file.text = self.data_d.header_d[XML_KEY_MONTAGE_FILE] \
                                           .split(nft.DELIM_SLASH)[-1]
        else:
            montage_file.text = None

        # set up the label
        #
        label = et.SubElement(root, XML_TAG_LABEL, name= path(ofile).stem,
                              dtype=PARENT_TYPE)

        # add the endpoints
        #
        endpoints = et.SubElement(label, XML_TAG_ENDPOINTS,
                                  name=XML_TAG_ENDPOINTS, dtype= LIST_TYPE)
        endpoints.text = f"[{file_start_time:.{PRECISION}f}," + \
            f"{file_end_time:.{PRECISION}f}]"

        # add the montage_channels
        #
        montage_channels = et.SubElement(label, XML_TAG_MONTAGE_CHANNELS,
                                         name=XML_TAG_MONTAGE_CHANNELS,
                                         dtype=PARENT_TYPE)
        # add all the channels to the xml
        #
        for channel in channels:
            montage_channels.append(et.Element(XML_TAG_CHANNEL, name=channel,
                                               dtype="*"))

        # writes the start time and end time of each event under the correct
        # channels
        #
        for channel_index, data in graph[0][0].items():

            parent_channel = label.find('montage_channels/channel[@name=\'%s\']'
                                        % (self.channel_map_label[channel_index]))

            for start, stop, tag_probability in data:

                event_tag, event_probability = next(
                    iter(tag_probability.items()))

                tag = et.SubElement(parent_channel, XML_TAG_EVENT,
                                    name=str(event_tag), dtype=PARENT_TYPE)

                endpoint = et.SubElement(tag, XML_TAG_ENDPOINTS,
                                         name=XML_TAG_ENDPOINTS,
                                         dtype= LIST_TYPE)

                endpoint.text = f"[{start:.{PRECISION}f}, {stop:.{PRECISION}f}]"

                probability = et.SubElement(tag, XML_TAG_PROBABILITY,
                                            name=XML_TAG_PROBABILITY,
                                            dtype= LIST_TYPE)

                probability.text = f"[{float(event_probability):.{PRECISION}f}]"

        # convert the tree to a string
        #
        xmlstr = et.tostring(root, encoding=nft.DEF_CHAR_ENCODING)

        # convert the string to a pretty print
        #
        reparsed = md.parseString(
            xmlstr).toprettyxml(indent=nft.DELIM_SPACE)

        # open the output file to write
        #
        with open(ofile, nft.MODE_WRITE_TEXT) as writer:

            # write the xml file
            #
            writer.write(reparsed)

        # exit gracefully
        #
        return True
    #
    # end of method

    def display(self, level, sublevel, fp=sys.stdout):
        """
        method: display

        arguments:
         level: level of events
         sublevel: sublevel of events
         fp: a file pointer

        return:
         a boolean value indicating status

        description:
         This method displays the events from a flat AG.
        """

        # display an informational message
        #
        if dbgl > ndt.BRIEF:
            print("%s (line: %s) %s: displaying events from flag AG" %
                  (__FILE__, ndt.__LINE__, ndt.__NAME__))

        # ensure a montage was succesfully loaded
        #
        if self.montage_loaded == False:

            print("Error: %s (line: %s) %s: no montage loaded" %
                  (__FILE__, ndt.__LINE__, ndt.__NAME__))
            return False

        # get graph
        #
        graph = self.get_graph()

        # try to access graph at level/sublevel
        #
        try:
            graph[level][sublevel]
        except:
            print("Error: %s (line: %s) %s::%s %s (%d/%d)" %
                  (__FILE__, ndt.__LINE__, Xml.__CLASS_NAME__, ndt.__NAME__,
                   "level/sublev not in graph", level, sublevel))
            return False

        for chan in graph[level][sublevel]:
            # iterate over events for each channel
            #
            for event in graph[level][sublevel][chan]:
                start = event[0]
                stop = event[1]
                # create a string with all symb/prob pairs
                #
                pstr = nft.DELIM_NULL
                for symb in event[2]:

                    pstr += f" {symb:>8} {event[2][symb]:10.{PRECISION}f}"

                if chan != -1:
                    chan_a = chan
                else:
                    chan_a = -1
                # display event
                #
                fp.write(f"{self.channel_map_label[chan_a]:>10}: \
                            {start:10.{PRECISION}f} \
                            {stop:10.{PRECISION}f}{pstr}\n")
        # exit gracefully
        #
        return True
    #
    # end of method

    def tree_to_dict(self, root):
        """
        method: tree_to_dict

        arguments:
         root (xml.etree.ElementTree.root): root of the xml file

        return:
         treedict: dictionary equivalent of xml tree

        description:
         This method converts the given xml files into the graphing
         object format which allows us to set the graph directly
         using the return dictionary
        """

        # local variables
        #
        treedict = defaultdict(list)

        # access all the channel
        #
        for montage_channel in root.findall(XML_TAG_CHANNEL_PATH):

            # set the channel num so that we can use it to index
            # our dictionary with the corresponding channel number
            #
            for num, channel in self.channel_map_label.items():
                if channel == montage_channel.attrib[XML_TAG_NAME]:
                    channel_num = num

            # iterate through all the event in that channel
            #
            for event in montage_channel.findall(XML_TAG_EVENT):
                tag = event.attrib[XML_TAG_NAME]
                probability = event.find(XML_TAG_PROBABILITY) \
                                   .text.strip(nft.DELIM_OPEN) \
                                        .strip(nft.DELIM_CLOSE)
                start_time, end_time = \
                    event.find(XML_TAG_ENDPOINTS).text.strip(nft.DELIM_OPEN) \
                                                      .strip(nft.DELIM_CLOSE) \
                                                      .strip() \
                                                      .split(nft.DELIM_COMMA)
                # append to the correct channel index
                #
                treedict[channel_num].append([float(start_time),
                                              float(end_time),
                                              {tag: float(probability)}])

        # exit gracefully
        #
        return treedict
    #
    # end of method

    def validate(self, fname, xml_schema = DEF_XML_FNAME):
        """
        method: validate

        arguments:
         fname: filename to be validated

        return:
         a boolean value indicating status

        description:
         This method validates xml file with a schema
        """

        # parse an XML file
        #
        try:
            # turn a file to XML Schema validator
            #
            self.schema = etree.XMLSchema(file=nft.get_fullpath(xml_schema))
            xml_file = etree.parse(fname)

        # check for a syntax error
        #
        except etree.XMLSyntaxError:
            if dbgl > ndt.NONE:
                print("Error: %s (line: %s) %s: xml syntax error (%s)" %
                  (__FILE__, ndt.__LINE__, ndt.__NAME__, fname))
            return False

        # check if there was an OS error (e.g,, file doesn't exist)
        #
        except OSError:
            if dbgl > ndt.NONE:
                print("Error: %s (line: %s) %s: xml file doesn't exist (%s)" %
                  (__FILE__, ndt.__LINE__, ndt.__NAME__, fname))
            return False

        # validate the schema
        #
        status = self.schema.validate(xml_file)
        if status == False:
            try:
                self.schema.assertValid(xml_file)
            except etree.DocumentInvalid as errors:
                print("Error: %s (line: %s) %s: %s (%s)" %
                      (__FILE__, ndt.__LINE__, ndt.__NAME__, errors, fname))

        # exit gracefully
        #
        return status
    #
    # end of method

    def parse_montage(self, montage_f):
        """
        method: parse_montage

        arguments:
         montage_f: a montage file

        return:
         a boolean value indicating status

        description:
         This method updates the channel_map_label variable
         based on the inputted
         montage file

        Note:
         Please expand any environment variable before
         passing it into the function since the
         function does not expand it for you.
        """

        # fetch montages full path
        #
        montage_f = nft.get_fullpath(montage_f)

        # ensure parameter file exists
        #
        if os.path.isfile(montage_f) == False:
            print("ERROR: %s (line: %s) %s: montage file doesn't exist (%s)" %
                  (__FILE__, ndt.__LINE__, ndt.__NAME__, montage_f))
            return False

        # open montage file
        #
        montage_fp = open(montage_f, nft.MODE_READ_TEXT)
        if montage_fp is None:
            print("Error: %s (line: %s) %s::%s: error opening file (%s)" %
                  (__FILE__, ndt.__LINE__, Csv.__CLASS_NAME__,
                   ndt.__NAME__, montage_f))
            return False

        # check if the dictionary has been populated once
        # this will be true when the dictionary is not-empty
        #
        if len(self.channel_map_label) > 1:
            self.channel_map_label.clear()

        for line in montage_fp:

            line = line.replace(nft.DELIM_NEWLINE, nft.DELIM_NULL) \
                        .replace(nft.DELIM_CARRIAGE, nft.DELIM_NULL) \
                        .replace(nft.DELIM_SPACE, nft.DELIM_NULL)

            # extract the information if present or
            # continue until information is found
            #
            if line.startswith(DELIM_XML_MONTAGE):
                channel_number, channel_name = re.findall(
                    DEF_REGEX_MONTAGE_FILE, line).pop()
            else:
                continue

            # append to the channel_map dictionary to create
            # the corresponding channel number and name
            #
            self.channel_map_label[int(channel_number)] = channel_name

        # exit gracefully
        #
        return True
    #
    # end of method

    def set_file_duration(self,dur):
        """
        method: set_file_duration

        arguments:
         dur: duration of the file

        return:
         none

        description:
         This method allows us to set the file duration for the whole
         xml file
        """

        self.data_d.header_d[XML_KEY_DURATION] = dur
        return

    def get_file_duration(self):
        """
        method: get_file_duration

        arguments:
         none

        return:
         duration: the file duration (float)

        description:
         This method returns the file duration for the whole
         xml file
        """

        return float(self.data_d.header_d[XML_KEY_DURATION])

    # Note: commented out code may not be needed and may
    # just over complicate the add methods code
    #
    """
    # define a list of all xml events present
    # in all EEG montage file. Used for xml's
    # add method
    #
    xml_events_list = [ {"null_type": "null",
                         "bckg_type": "bckg",
                         "seiz_type": "seiz",
                         "artf_type": "artf"} ]
    """
    def add(self, dur, sym, level, sublevel):
        """
        method: add

        arguments:
         dur: duration of events
         sym: symbol of events
         level: level of events
         sublevel: sublevel of events

        return:
         a boolean value indicating status

        description:
         This method adds events of type sym.
        """

        # Note: commented out code may not be needed and may
        # just over complicate code
        #
        """
        # check that this is a valid add, by checking if
        # the sym specified is listed in one of the class mapping
        # list
        #
        class_mapping_list = self.get_valid_sub(self.schema_path)

        # initialize variables to hold child and parent values
        #
        child = None
        parent = None
        status = False

        # traverse all class mappings in the class
        # mapping list
        #
        for class_mapping in class_mapping_list:

            # traverse dictionary holding possible sym parent keys and
            # child values
            #
            for key in class_mapping:

                # if the sym specified is found to be a key
                #
                if (sym == key):

                    # store parent value
                    #
                    parent = key
                    status = True
                    break

                # get list of children for each parent sym
                #
                value_list = class_mapping.get(key)

                # iterate through list of children
                #
                for value in value_list:

                    # if sym is found in value list
                    #
                    if (sym == value):

                        # store child value
                        #
                        status = True
                        child = value
                        parent = key
                        break

        # if label is not valid
        #
        if status is False:
            print("Error: %s (line: %s) %s: invalid label (%s)" %
                  (__FILE__, ndt.__LINE__, ndt.__NAME__, sym))

        # if the sym to add is a child we make sure that the parent
        # label already exists in the duration provided
        #
        if (child != None):

            graph = self.get_graph()

            # obtain parent dictionary which is one sublevel below child
            #
            chan_dict = graph[level][sublevel-1]

            # check if parent sym exists at duration
            #
            add_parent = True

            for key in chan_dict:

                # list of events
                #
                value_list = chan_dict.get(key)

                # for each event
                # example of event: [0.0, 10.2787, {'bckg': 1.0}]
                #
                for event in value_list:

                    # get label of event for example ['bckg'] or ['seiz']
                    #
                    event_key = list(event[2].keys())

                    # if the parent event exists at duration
                    #
                    if ((event[1] == dur) and (parent == event_key[0])):

                        Add_parent = False

            # if parent label was not found at duration
            #
            if (add_parent == True):

                # add parent label
                #
                self.data_d.add(dur, parent, level, sublevel - 1)
        """

        return self.data_d.add(dur, sym, level, sublevel)

    #
    # end of method

    # Note: method may not need be implemented and
    # may have only over comlicated the add method
    #
    """
    def get_valid_sub(self, xml_schema):

        method: get_valid_sub

        arguments:
         xml_schema: valid xml schema file

        return:
         class_mapping_list: list of key/value pair dictionary

        description:
         This method returns a dictionary mapping of
         a parent class (i.e: SEIZ) and value is a list of
         valid sub elements i.e: spsw, gped, etc.

        # open the file to read
        #
        with open(xml_schema, nft.MODE_READ_TEXT) as fp:
            content = fp.read()

        # parse with BeautifulSoup
        #
        soup = bs(content, features="lxml-xml")

        # initialize mapping variables
        #
        class_mapping_list = []
        class_type_list = []

        # for all xml events in xml_events_list
        # fetch and append to appropriate
        # list the all xml events class mappings
        # and class types
        #
        for xml_events in xml_events_list:

            # initialize/reinitialize subsist/subsets
            # of the class mapping and type lists
            #
            class_mapping = {}
            class_type = []

            # fetch and load information from xml_events
            # into the respective temporary variables
            # class_mapping and class_type
            #
            for type_d, class_d in xml_events.items():
                if type_d not in class_type:
                    class_type.append(type_d)
                if class_d not in class_mapping:
                    class_mapping[class_d] = []

            # append fetched information to the list
            # of class mappings and the list of class
            # types
            #
            class_mapping_list.append(class_mapping)
            class_type_list.append(class_type)


        # loop through all complex Type in schema
        #
        for element in soup.find_all('xs:complexType'):

            # iterate over all class types in the list
            #
            for itr in range(len(class_type_list)):

                # if this has a name attribute and it is in
                # the classes type set
                #
                if  element.get(DEF_XML_NAME) in class_type_list[itr]:

                    # get the name of all valid sub elements
                    #
                    valid = [sub[DEF_XML_NAME] for sub
                             in element.find_all('xs:element')]

                    # get the def type of this class
                    #
                    def_type = xml_events_list[itr][element.get(DEF_XML_NAME)]

                    # extend to the array
                    #
                    class_mapping_list[itr][def_type].extend(valid)

        # exit gracefully
        #
        return class_mapping_list
    """

    def delete(self, sym, level, sublevel):
        """
        method: delete

        arguments:
         sym: symbol of events
         level: level of events
         sublevel: sublevel of events

        return:
         a boolean value indicating status

        description:
         This method deletes events of type sym.
        """

        return self.data_d.delete(sym, level, sublevel)
    #
    # end of method

    def get(self, level, sublevel, channel):
        events = self.data_d.get(level, sublevel, channel)
        """
        method: get

        arguments:
         level: level of annotations to get
         sublevel: sublevel of annotations to get

        return:
         events at level/sublevel by channel

        description:
         This method gets the annotations stored in the AG at level/sublevel.
        """

        return events
    #
    # end of method

    def get_graph(self):
        """
        method: get_graph

        arguments:
         none

        return:
         entire graph data structure

        description:
         This method accesses self.data_d.graph_d and returns
         the entire graph structure.
        """

        return self.data_d.get_graph()
    #
    # end of method

    def get_header(self):
        """
        method get_header

        arguments:
         none

        return:
         file header data

        description:
         This method accesses self.data_d.header_d and returns header info
        """

        return self.data_d.get_header()
    #
    # end of method

    def set_graph(self, graph):
        """
        method: set_graph

        arguments:
         graph: graph to set

        return:
         a boolean value indicating status

        description:
         This method sets the class data to graph
        """

        return self.data_d.set_graph(graph)
    #
    # end of method

    def set_header(self, header):
        """
        method: set_header

        arguments:
         header: header to set

        return:
         a boolean value indicating status

        description:
         This method sets the header data
        """

        return self.data_d.set_header(header)
    #
    # end of method

    def set_schema(self, schema):
        """
        method: set_schema

        arguments:
         schema: schema to set

        return:
         none

        description:
         This method sets the schema file
        """

        self.schema = schema

    #
    # end of method

#
# end of class

class AnnEeg:
    """
    Class: Ann

    arguments:
     none

    description:
     This class is the main class of this file. It contains methods to
     manipulate the set of supported annotation file formats including
     label (.lbl) and time-synchronous events (.tse) formats.
    """

    def __init__(self, schema = DEF_XML_FNAME, montage_f = DEF_MONTAGE_FNAME):
        """
        method: constructor

        arguments:
         schema: XML schema filename ($NEDC_NFC/lib/nedc_eeg_xml_schema_v00.xsd)
         montage_f: montage filename ($NEDC_NFC/lib/nedc_eas_default_montage.txt)

        return:
         none

        description:
         This method constructs AnnEeg
        """

        # set the class name
        #
        AnnEeg.__CLASS_NAME__ = self.__class__.__name__

        # instantiate FTYPES variable
        #
        self.ftype_obj_d = copy.deepcopy(FTYPE_OBJECTS)

        # initialize all sub classes with schema and montage
        #
        for type_name in self.ftype_obj_d.keys():
            self.ftype_obj_d[type_name][1].__init__(montage_f, schema)

        # declare variable to store type of annotations
        #
        self.type_d = None

    #
    # end of method

    def load(self, fname, schema=DEF_XML_FNAME, montage_f=DEF_MONTAGE_FNAME):
        """
        method: load

        arguments:
         fname: annotation filename
         schema: XML schema filename ($NEDC_NFC/lib/nedc_eeg_xml_schema_v00.xsd)
         montage_f: montage filename($NEDC_NFC/lib/nedc_eas_default_montage.txt)

        return:
         a boolean value indicating status

        description:
         This method loads an annotation from a file.
        """

        # display debugging information
        #
        if dbgl > ndt.BRIEF:
            print("%s (line: %s) %s::%s: loading file (%s, %s, %s)" %
                  (__FILE__, ndt.__LINE__, AnnEeg.__CLASS_NAME__,
                   ndt.__NAME__, fname, schema, montage_f))

        # re instantiate objects, this removes the previous loaded annotations
        #
        self.ftype_obj_d = copy.deepcopy(FTYPE_OBJECTS)

        # initialize all sub classes with schema and montage
        #
        for type_name in self.ftype_obj_d.keys():
            self.ftype_obj_d[type_name][1].__init__(montage_f, schema)

        # determine the file type
        #
        magic_str = nft.get_version(fname)
        self.type_d = self.check_version(magic_str)
        if self.type_d == None or self.type_d == False:
            if dbgl > ndt.BRIEF:
                print("Error: %s (line: %s) %s: unknown file type (%s: %s)" %
                    (__FILE__, ndt.__LINE__, ndt.__NAME__, fname, magic_str))
            return False

        # load the specific type
        #
        return self.ftype_obj_d[self.type_d][1].load(fname)
    #
    # end of method

    def get(self, level=int(0), sublevel=int(0), channel=int(-1)):
        """
        method: name

        arguments:
         level: the level value
         sublevel: the sublevel value

        return:
         events: a list of ntuples containing the start time, stop time,
         a label and a probability.

        description:
         This method returns a flat data structure containing a list of events.
        """

        # display debugging information
        #
        if dbgl > ndt.BRIEF:
            print("%s (line: %s) %s::%s: getting annotation (%s, %s, %s)" %
                  (__FILE__, ndt.__LINE__, AnnEeg.__CLASS_NAME__,
                   ndt.__NAME__, level, sublevel, channel))

        # attempting to get list of events
        #
        if self.type_d is not None:
            events = self.ftype_obj_d[self.type_d][1].data_d.get(level,
                                                                 sublevel,
                                                                 channel)
        else:
            print("Error: %s (line: %s) %s: no annotation loaded" %
                  (__FILE__, ndt.__LINE__, ndt.__NAME__))
            return False

        # exit gracefully
        #
        return events
    #
    # end of method

    def display(self, level=int(0), sublevel=int(0), fp=sys.stdout):
        """
        method: display

        arguments:
         level: level value
         sublevel: sublevel value
         fp: a file pointer (default = stdout)

        return:
         a boolean value indicating status

        description:
         This method displays the events at level/sublevel.
        """

        # display debugging information
        #
        if dbgl > ndt.BRIEF:
            print("%s (line: %s) %s::%s: displaying level/sublevel (%s, %s)" %
                  (__FILE__, ndt.__LINE__, AnnEeg.__CLASS_NAME__,
                   ndt.__NAME__, level, sublevel))

        # attempt to display events at level/sublevel
        #
        if self.type_d is not None:
            status = self.ftype_obj_d[self.type_d][1].display(level,
                                                              sublevel,
                                                              fp)
        else:
            print("Error: %s (line: %s) %s %s" %
                  (ndt.__NAME__, ndt.__LINE__, ndt.__NAME__,
                   "no annotations to display"))
            status = False

        # exit gracefully
        #
        return status
    #
    # end of method

    def write(self, ofile, level=int(0), sublevel=int(0)):
        """
        method: write

        arguments:
         ofile: output file path to write to
         level: level of annotation to write
         sublevel: sublevel of annotation to write

        return:
         a boolean value indicating status

        description:
         This method writes annotations to a specified file.
        """

        # display debugging information
        #
        if dbgl > ndt.BRIEF:
            print("%s (line: %s) %s::%s: writing to file (%s)" %
                  (__FILE__, ndt.__LINE__, AnnEeg.__CLASS_NAME__,
                   ndt.__NAME__, ofile))

        # attempt to write events at level/sublevel
        #
        if self.type_d is not None:
            status = self.ftype_obj_d[self.type_d][1].write(ofile,
                                                            level,
                                                            sublevel)
        else:
            print("Error: %s (line: %s) %s: %s" %
                  (__FILE__, ndt.__LINE__, ndt.__NAME__,
                   "no annotations to write"))
            status = False

        # exit gracefully
        #
        return status
    #
    # end of method

    def add(self, dur, sym, level, sublevel):
        """
        method: add

        arguments:
         dur: duration of file
         sym: symbol of event to be added
         level: level of events
         sublevel: sublevel of events

        return:
         a boolean value indicating status

        description:
         This method adds events to the current events based on args.
        """

        # display debugging information
        #
        if dbgl > ndt.BRIEF:
            print("%s (line: %s) %s::%s: addition to annotation " +
                  "(%s, %s, %s, %s)" %
                (__FILE__, ndt.__LINE__, AnnEeg.__CLASS_NAME__,
                 ndt.__NAME__, dur, sym, level, sublevel))

        # attempt to add labels to events at level/sublevel
        #
        if self.type_d is not None:
            status = self.ftype_obj_d[self.type_d][1].add(dur,
                                                          sym,
                                                          level,
                                                          sublevel)
        else:
            print("Error: %s (line: %s) %s: no annotations to add to" %
                  (__FILE__, ndt.__LINE__, ndt.__NAME__))
            status = False

        # exit gracefully
        #
        return status
    #
    # end of method

    def create(self, lev, sub, chan, start, stop, symbols):
        """
        method: create

        arguments:
         lev: level of the event
         sub: sublevel of the event
         chan: channel of the event
         start: start time of the event
         stop: stop time of the event
         sym: symbol of event to be deleted

        return:
         a boolean value indicating status

        description:
         This method create an events of type sym in the internal graph
        """

        # display debugging information
        #
        if dbgl > ndt.BRIEF:
            print("%s (line: %s) %s::%s: creating event " +
                  "(%s, %s, %s ,%s, %s, %s)" %
                  (__FILE__, ndt.__LINE__, AnnEeg.__CLASS_NAME__,
                   ndt.__NAME__, lev, sub, chan, start, stop, symbols ))

        # delete labels from events at level/sublevel
        #
        if self.type_d is not None:
            status = self.ftype_obj_d[self.type_d][1].data_d.create(lev,
                                                                    sub,
                                                                    chan,
                                                                    start,
                                                                    stop,
                                                                    symbols)
        else:
            print("Error: %s (line: %s) %s: no annotations to create" %
                 (__FILE__, ndt.__LINE__, ndt.__NAME__))
            status = False

        # exit gracefully
        #
        return status
    #
    # end of method

    def sort(self):
        """
        method: sort

        arguments:

        return:
         a boolean value indicating status

        description:
         This method sort the internal graph
        """

        # display debugging information
        #
        if dbgl > ndt.BRIEF:
            print("%s (line: %s) %s::%s: sorting" %
                  (__FILE__, ndt.__LINE__, AnnEeg.__CLASS_NAME__,
                   ndt.__NAME__))

        # attempting to sort
        #
        if self.type_d is not None:
            status = self.ftype_obj_d[self.type_d][1].data_d.sort()
        else:
            print("Error: %s (line: %s) %s: no annotations to sort" %
                (__FILE__, ndt.__LINE__, ndt.__NAME__))
            status = False

        # exit gracefully
        #
        return status
    #
    # end of method

    def delete(self, sym, level, sublevel):
        """
        method: delete

        arguments:
         sym: symbol of event to be deleted
         level: level of events
         sublevel: sublevel of events

        return:
         a boolean value indicating status

        description:
         This method deletes all events of type sym
        """

        # display debugging information
        #
        if dbgl > ndt.BRIEF:
            print("%s (line: %s) %s::%s: deleting (%s, %s, %s)" %
                  (__FILE__, ndt.__LINE__, AnnEeg.__CLASS_NAME__,
                   ndt.__NAME__, sym, level, sublevel))


        status = self.ftype_obj_d[self.type_d][1].delete(sym,
                                                         level,
                                                         sublevel)

        # exit gracefully
        #
        return status
    #
    # end of method

    def validate(self, fname, xml_schema = DEF_XML_FNAME):
        """
        method: validate

        arguments:
         fname: file to validate
         schema: a schema file

        return:
         a boolean value indicating status

        description:
         This method validate the file
        """

        # display debugging information
        #
        if dbgl > ndt.BRIEF:
            print("%s (line: %s) %s::%s: validating file (%s)" %
                  (__FILE__, ndt.__LINE__, AnnEeg.__CLASS_NAME__,
                   ndt.__NAME__, fname))

        # create status boolean variable
        #
        status = False

        # get type
        #
        magic_str = nft.get_version(fname)
        type_s = self.check_version(magic_str)

        # attempt to validate file
        #
        try:
            # if the current file type has a schema call its
            # validate function else call the validate function
            # without schema argument
            #
            if hasattr(self.ftype_obj_d[type_s][1], nft.DEF_SCHEMA):
                status = self.ftype_obj_d[type_s][1].validate(fname,
                                                              xml_schema)
            else:
                status = self.ftype_obj_d[type_s][1].validate(fname)
        except:
            if dbgl > ndt.BRIEF:
                print("Error: %s (line: %s) %s: cannot validate file type" %
                        (__FILE__, ndt.__LINE__, ndt.__NAME__))

        # exit gracefully
        #
        return status
    #
    # end of method

    def set_type(self, ann_type):
        """
        method: set_type

        arguments:
         type: the type of ann object to set

        return:
         a boolean value indicating status

        description:
         This method sets the type and graph in type from self.type_d
        """

        # display debugging information
        #
        if dbgl > ndt.BRIEF:
            print("%s (line: %s) %s::%s: setting file type" %
                  (__FILE__, ndt.__LINE__, AnnEeg.__CLASS_NAME__,
                   ndt.__NAME__))

        # attempt to set file type
        #
        if self.type_d is not None:

            # if annotation type is supported update ftype_obj_d and
            # change type_d
            #
            if ann_type in FTYPE_OBJECTS.keys():

                # update graph
                #
                graph_status = self.ftype_obj_d[ann_type][1] \
                                   .set_graph(self.ftype_obj_d \
                                              [self.type_d][1].get_graph())

                # update header
                #
                header_status = self.ftype_obj_d[ann_type][1] \
                                    .set_header(self.ftype_obj_d \
                                                [self.type_d][1].get_header())

                # update type_d
                #
                self.type_d = ann_type

            else:
                print("Error: %s (line: %s) %s: ann type not supported (%s)" %
                      (__FILE__, ndt.__LINE__, ndt.__NAME__, ann_type))

        # if file the AnnEeg objects file type is not
        # already set simply set the type
        #
        else:

            # update type_d
            #
            self.type_d = ann_type

        # exit gracefully
        #
        return True
    #
    # end of method

    def set_graph(self, graph):
        """
        method: set_graph

        arguments:
         type: type of ann object to set

        return:
         a boolean value indicating status

        description:
         This method sets the type and graph in type from self.type_d
        """

        # display debugging information
        #
        if dbgl > ndt.BRIEF:
            print("%s (line: %s) %s::%s: setting graph" %
                  (__FILE__, ndt.__LINE__, AnnEeg.__CLASS_NAME__,
                   ndt.__NAME__))

        # attempt to set graph
        #
        if self.type_d is not None:
            status = self.ftype_obj_d[self.type_d][1].set_graph(graph)
        else:
            print("Error: %s (line: %s) %s: no graph to set" %
                  (__FILE__, ndt.__LINE__, ndt.__NAME__))
            status = False

        # exit gracefully
        #
        return status
    #
    # end of method

    def set_header(self, header):
        """
        method: set_header

        arguments:
         type: type of ann object to set

        return:
         a boolean value indicating status

        description:
         This method sets the type and header in type from self.type_d
        """

        # display debugging information
        #
        if dbgl > ndt.BRIEF:
            print("%s (line: %s) %s::%s: setting header" %
                  (__FILE__, ndt.__LINE__, AnnEeg.__CLASS_NAME__,
                   ndt.__NAME__))

        # attempt to set header
        #
        if self.type_d is not None:
            status = self.ftype_obj_d[self.type_d][1].set_header(header)
        else:
            print("Error: %s (line: %s) %s: no header to set" %
                  (__FILE__, ndt.__LINE__, ndt.__NAME__))
            status = False

        # exit gracefully
        #
        return status
    #
    # end of method

    def set_file_duration(self,dur):
        """
        method: set_file_duration

        arguments:
         dur: duration of the file
         none

        return:
         none

        description:
         This method allows us to set the file duration for csv and xml
         files. TSE and LBL files does not have durations within them.
        """

        # display debugging information
        #
        if dbgl > ndt.BRIEF:
            print("%s (line: %s) %s::%s: setting file durations (%s)" %
                  (__FILE__, ndt.__LINE__, AnnEeg.__CLASS_NAME__,
                   ndt.__NAME__, dur))

        # attempt to set duration for all classes
        #
        for type_s in self.ftype_obj_d.keys():
            self.ftype_obj_d[type_s][1].set_file_duration(dur)

        # exit gracefully
        #
        return
    #
    # end of method

    def get_file_duration(self):
        """
        method: get_file_duration

        arguments:
         none

        return:
         none

        description:
         This method returns the file duration for csv and xml files.
         TSE and LBL files does not have durations within them.
        """

        # display debugging information
        #
        if dbgl > ndt.BRIEF:
            print("%s (line: %s) %s::%s: getting file durations" %
                  (__FILE__, ndt.__LINE__, AnnEeg.__CLASS_NAME__,
                   ndt.__NAME__))

        # attempt to get duration
        #
        if self.type_d is not None:
            duration = self.ftype_obj_d[self.type_d][1].get_file_duration()
        else:
            print("Error: %s (line: %s) %s: no duration to get" %
                  (__FILE__, ndt.__LINE__, ndt.__NAME__))

        # exit gracefully
        #
        return duration
    #
    # end of method

    def delete_graph(self):
        """
        method: delete_graph

        arguments:
         none

        return:
         none

        description:
         none
        """

        # display debugging information
        #
        if dbgl > ndt.BRIEF:
            print("%s (line: %s) %s::%s: deleting graph" %
                  (__FILE__, ndt.__LINE__, AnnEeg.__CLASS_NAME__,
                   ndt.__NAME__))

        # attempt to delete graph
        #
        status = self.ftype_obj_d[self.type_d][1].data_d.delete_graph()

        # exit gracefully
        #
        return True
    #
    # end of method

    def get_graph(self):
        """
        method: get_graph

        arguments:
         none

        return:
         the entire annotation graph

        description:
         This method returns the entire stored annotation graph
        """

        # display debugging information
        #
        if dbgl > ndt.BRIEF:
            print("%s (line: %s) %s::%s: getting graph" %
                  (__FILE__, ndt.__LINE__, AnnEeg.__CLASS_NAME__,
                   ndt.__NAME__))

        # attempt to get graph
        #
        if self.type_d is not None:
            graph = self.ftype_obj_d[self.type_d][1].get_graph()
        else:
            print("Error: %s (line: %s) %s: no graph to get" %
                  (__FILE__, ndt.__LINE__, ndt.__NAME__))
            graph = None

        # exit gracefully
        #
        return graph
    #
    # end of method

    def get_header(self):
        """
        method: get_header

        arguments:
         none

        return
         file header information

        description:
         This method returns the files header information
        """

        # display debugging information
        #
        if dbgl > ndt.BRIEF:
            print("%s (line: %s) %s::%s: getting header information" %
                  (__FILE__, ndt.__LINE__, AnnEeg.__CLASS_NAME__,
                   ndt.__NAME__))

        # attempt to get header information
        #
        if self.type_d is not None:
            header = self.ftype_obj_d[self.type_d][1].get_header()
        else:
            print("Error: %s (line: %s) %s: no header to get" %
                  (__FILE__, ndt.__LINE__, ndt.__NAME__))
            header = None

        # exit gracefully
        #
        return header
    #
    # end of method

    def check_version(self, magic):
        """
        method: check_version

        arguments:
         magic: a magic sequence

        return:
         a character string containing the name of the type

        description:
         none
        """

        # check for a match
        #
        for key in FTYPE_OBJECTS:
            if FTYPE_OBJECTS[key][0] == magic:
                return key

        # exit (un)gracefully:
        #  if we get this far, there was no match
        #
        return False
    #
    # end of method
#
# end of class

# -----------------------------------------------------------------------------
#
# Beginning of Most Important Section
#
#------------------------------------------------------------------------------

# define FTYPE_OBJECTS
#
FTYPE_OBJECTS = {nft.LBL_NAME : [nft.LBL_VERSION, Lbl()],
                 nft.TSE_NAME : [nft.TSE_VERSION, Tse()],
                 nft.CSV_NAME : [nft.CSV_VERSION, Csv(montage_f = None)],
                 nft.XML_NAME : [nft.XML_VERSION, Xml(montage_f = None)]}

# define a list of all file types versions
#
VERSIONS = [nft.LBL_VERSION, nft.TSE_VERSION, nft.CSV_VERSION, nft.XML_VERSION]

# define a list of all file type names
#
TYPE_NAMES = [nft.TSE_NAME, nft.LBL_NAME, nft.CSV_NAME, nft.XML_NAME]

#------------------------------------------------------------------------------
#
# End of Most Important Section
#
#------------------------------------------------------------------------------

#
# end of file
