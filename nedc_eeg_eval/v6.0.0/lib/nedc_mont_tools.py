#!/usr/bin/env python

# files: $(NEDC_NFC)/class/python/.../nedc_mont_tools.py
#
# revision history:
#
# 20241228 (DH): added debuging prints/error checking code and added new methods
#                that load/give the montage and channel order
# 20230622 (AB): refactored code to new comment format
# 20220621 (PM): fixed get_subtrahends() to handle montages that only have one
#                part
# 20200708 (JP): code review
# 20200707 (TC): changed the interface
# 20200623 (TC): initial version
#
# This file contains a Python implementation of functions to manipulate
# montages.
#
#------------------------------------------------------------------------------

# import required system modules
#
import os
import sys
import re

# import numpy
#
import numpy as np

# import NEDC modules
#
import nedc_debug_tools as ndt
import nedc_file_tools as nft

#------------------------------------------------------------------------------
#
# global variables are listed here
#
#------------------------------------------------------------------------------

# set the filename using basename
#
__FILE__ = os.path.basename(__file__)

# define variables that delimit the parts of a line
#
DEF_DELIM_MONTAGE = "montage ="
DEF_DELIM_OPER = nft.DELIM_SPACE + nft.STRING_DASHDASH + nft.DELIM_SPACE

# define attribute key variables
#
ATTR_MONTAGE_D = "montage_d"
ATTR_CHAN_ORDER_D = "chan_order_d"
ATTR_MONT_ORDER_D = "mont_order_d"

#------------------------------------------------------------------------------
#
# classes are listed here
#
#------------------------------------------------------------------------------

class Montage:
    """
    Class: Montage

    arguments:
     none

    description:
     none
    """

    # define static variables for debug and verbosity
    #
    dbgl_d = ndt.Dbgl()
    vrbl_d = ndt.Vrbl()

    def __init__(self, fname = None):
        """
        method: constructor

        arguments:
         mfile: montage file

        return:
         none

        description:
         This simple method intializes a class
        """

        # set the class name
        #
        Montage.__CLASS_NAME__ = self.__class__.__name__

        # display debug information
        #
        if self.dbgl_d == ndt.FULL:
            print("%s (line: %s) %s::%s: contructing a montage (%s)" %
                  (__FILE__, ndt.__LINE__, Montage.__CLASS_NAME__,
                   ndt.__NAME__, fname))

        # opening the file
        #
        if fname is not None:
            self.montage_d = self.load(fname)
            if self.montage_d is None:
                print("Error: %s (line: %s) %s: %s (%s)" %
                      (__FILE__, ndt.__LINE__, Montage.__CLASS_NAME__,
                       "cannot load file", fname))
                sys.exit(os.EX_SOFTWARE)

        #
        # end of method

    def load(self, fname):
        """
        method: load

        arguments:
         fname: montage filename

        return:
         a montage as a dictionary

        description:
         This method loads (and parses) a montage file.
        """

        # display debug information
        #
        if self.dbgl_d > ndt.BRIEF:
            print("%s (line: %s) %s::%s: loading a montage (%s)" %
                  (__FILE__, ndt.__LINE__, Montage.__CLASS_NAME__,
                   ndt.__NAME__, fname))

        # open the montage file
        #
        fp = open(fname, nft.MODE_READ_TEXT)
        if fp is None:
            print("Error: %s (line: %s) %s::%s: %s (%s)" %
                  (__FILE__, ndt.__LINE__, Montage.__CLASS_NAME__,
                   ndt.__NAME__, "cannot open file", fname))
            raise Exception("cannot montage file")

        # define montage dict
        #
        self.montage_d = {}

        # parse the montage file
        #
        flag_pblock = False
        for line in fp:

            # check for a delimiter
            #
            if line.startswith(DEF_DELIM_MONTAGE):
                try:
                    # clean up the line
                    #
                    str = line\
                            .replace(nft.DELIM_NEWLINE, nft.DELIM_NULL) \
                            .replace(nft.DELIM_TAB, nft.DELIM_NULL) \
                                                .split(nft.DELIM_COMMA)

                    # separate the fields:
                    #  remove montage numbers
                    #
                    parts = str[1].split(nft.DELIM_COLON)

                    # slip double dash between minuend and subtrahend
                    #
                    parts[1] = parts[1].split(DEF_DELIM_OPER)

                    # remove any unnecessary space between items
                    #
                    parts[0] = parts[0].strip()
                    parts[1] = [channel.strip() for channel in parts[1]]

                    # append name and minuend/subtrahend to dict:
                    #  [('FP1-F7', ['EEG FP1-REF', 'EEG F7-REF']),
                    #   ('F7-T3', ['EEG F7-REF', 'EEG T3-REF']), ...]
                    #
                    self.montage_d.update({parts[0]:parts[1]})
                    flag_pblock = True

                except:

                    # return None when there is a syntax error
                    #
                    flag_pblock = False
                    print("Error: %s (line: %s) %s:: %s (%s)" %
                          (__FILE__, ndt.__LINE__, Montage.__CLASS_NAME__,
                           "cannot parse montage", fname))
                    break

        # close the file
        #
        fp.close()

        # load the montage order into memory
        #
        self.load_montages_order()

        # load the channel order into memory
        #
        self.load_channels_order()

        # make sure we found a montage block
        #
        if flag_pblock == False:
            fp.close()
            print("Error: %s (line: %s) %s::%s: invalid montage file (%s)" %
                  (__FILE__, ndt.__LINE__, Montage.__CLASS_NAME__,
                   ndt.__NAME__, fname))
            raise Exception("invalid montage file")

        # exit gracefully
        #
        return self.montage_d

    def check(self, isig, montage):
        """
        method: check

        arguments:
         isig: a dict of signal data
         montage: a montage dict

        return:
         a boolean value indicating status

        description:
         This method checks if a list of channel labels is consistent
         with the montage.
        """

        # display debug information
        #
        if self.dbgl_d > ndt.BRIEF:
            print("%s (line: %s) %s::%s: checking a montage" %
                  (__FILE__, ndt.__LINE__, Montage.__CLASS_NAME__,
                   ndt.__NAME__), montage)

        # ensure the montage instance has a channel
        # order varaible
        #
        if montage is None or isig is None:

            # if the if statement evaluates to true
            # throw an error message
            #
            print("%s (line: %s) %s::%s: signal/montage data not loaded(%s, %s)"
                  % (__FILE__, ndt.__LINE__, Montage.__CLASS_NAME__,
                     ndt.__NAME__, isig, montage))
            sys.exit(os.EX_SOFTWARE)

        # get a list of channels from input signal:
        #  use a fast technique:
        #   https://stackoverflow.com/questions/16819222/
        #    how-to-return-dictionary-keys-as-a-list-in-python
        #
        chan_labels = [*isig]

        # loop over a montage dict to find a missing channel
        #
        missing_channels = []

        for key in montage:

            # check minuend and subtrahend channels if it's not in
            # edf chan labels
            #
            for channel in montage[key]:
                if channel not in chan_labels:
                    missing_channels.append(channel)

        # check if there is a missing channel
        #
        if missing_channels:
            print("Error: %s (line: %s) %s::%s: missing channels" %
                  (__FILE__, ndt.__LINE__, Montage.__CLASS_NAME__,
                   ndt.__NAME__), missing_channels)
            return False

        # exit gracefully
        #
        return True

    def apply(self, isig, montage):
        """
        method: apply

        arguments:
         isig: signal data
         montage: a montage dict

        return:
         a new signal that is a result of the montage operation

        description:
         This method applies montage to a signal.
        """

        # display debug information
        #
        if self.dbgl_d > ndt.BRIEF:
            print("%s (line: %s) %s::%s: applying a montage" %
                  (__FILE__, ndt.__LINE__, Montage.__CLASS_NAME__,
                   ndt.__NAME__))

        # Save the montage dict in the instance variable.
        #
        self.montage_d = montage

        # Initialize the output signal dict.
        #
        out_sig = {}

        # Loop over each new channel key and its mapping in the montage.
        #
        for mont_key, mapping in self.montage_d.items():

            # Extract the expected minuend channel from the first mapping
            # element by splitting on '-' and stripping whitespace.
            #
            expected_minu = mapping[0].split(nft.DELIM_DASH)[0].strip()

            # If a second operand exists, extract the expected subtrahend in the
            # same way; otherwise, set it to None.
            #
            expected_subtra = (mapping[1].split(nft.DELIM_DASH)[0].strip()
                               if len(mapping) == 2 else None)

            # Initialize variables to hold the actual signal data.
            #
            actual_minu = None
            actual_subtra = None

            # Iterate over each channel key in the input signal dict.
            #
            for channel in isig:

                # Use extract_actual to get the candidate channel name.
                #
                candidate = \
                    channel.replace(nft.DELIM_DASH, nft.DELIM_SPACE).split()

                # If extraction fails, skip to the next channel.
                #
                if candidate is None:
                    continue

                # If the candidate matches the expected minuend and we have not
                # yet stored it, then store the corresponding signal.
                #
                if expected_minu in candidate and actual_minu is None:
                    actual_minu = isig[channel]
                    
                # If a subtrahend is expected and the candidate matches it and we
                # haven't stored it yet, then store that signal.
                #
                if (expected_subtra is not None and expected_subtra in candidate and
                    actual_subtra is None):
                    
                    actual_subtra = isig[channel]

            # If a subtrahend is expected, perform subtraction.
            #
            if expected_subtra is not None:

                # If both actual signals were found, subtract subtrahend from
                # minuend.
                #
                if actual_minu is not None and actual_subtra is not None:
                    out_sig[mont_key] = actual_minu - actual_subtra
                    
                else:

                    # If the expected minuend signal was not found, print an error.
                    #
                    if actual_minu is None:
                        print("%s (line: %s) %s::%s: no match for [%s]" %
                              (__FILE__, ndt.__LINE__, self.__CLASS_NAME__,
                               ndt.__NAME__, expected_minu))

                    # If the expected subtrahend signal was not found, print an error.
                    #
                    if actual_subtra is None:
                        print("%s (line: %s) %s::%s: no match for [%s]" %
                              (__FILE__, ndt.__LINE__, self.__CLASS_NAME__,
                               ndt.__NAME__, expected_subtra))
            else:

                # If no subtrahend is expected, simply copy the minuend signal.
                #
                if actual_minu is not None:
                    out_sig[mont_key] = actual_minu
                    
                    # Print an error if the expected minuend was not found.
                    #
                else:
                    print("%s (line: %s) %s::%s: no match for [%s]" %
                          (__FILE__, ndt.__LINE__, self.__CLASS_NAME__,
                           ndt.__NAME__, expected_minu))

        # exit gracefully
        # Return montage signal dict
        #
        return out_sig
    #
    # end of method

    def get_minuends(self):
        """
        method: get_minuends

        arguments:
         none

        return:
         a list of minuends from montage

        description:
         This method gets the minuends from a montage
        """

        # display debug information
        #
        if self.dbgl_d == ndt.FULL:
            print("%s (line: %s) %s::%s: fetching minuends" %
                  (__FILE__, ndt.__LINE__, Montage.__CLASS_NAME__,
                   ndt.__NAME__))

        # ensure the montage instance has a channel
        # order varaible
        #
        if not hasattr(self, ATTR_MONTAGE_D) or self.montage_d is None:

            # if the if statement evaluates to true
            # throw an error message
            #
            print("%s (line: %s) %s::%s: no montage loaded" %
                  (__FILE__, ndt.__LINE__, Montage.__CLASS_NAME__,
                   ndt.__NAME__))
            sys.exit(os.EX_SOFTWARE)

        # find the minuends
        #
        minuends = []
        for key in self.montage_d:
            minuends.append(self.montage_d[key][0])

        # exit gracefully
        #
        return minuends

    def get_subtrahends(self, null_fill = False):
        """
        method: get_subtrahends

        arguments:
         none

        return:
         a list of subtrahends from a montage

        description:
         This method gets the subtrahends from a montage.
        """

        # display debug information
        #
        if self.dbgl_d == ndt.FULL:
            print("%s (line: %s) %s::%s: fetching subtrahends" %
                  (__FILE__, ndt.__LINE__, Montage.__CLASS_NAME__,
                   ndt.__NAME__))

        # ensure the montage instance has a channel
        # order varaible
        #
        if not hasattr(self, ATTR_MONTAGE_D) or self.montage_d is None:

            # if the if statement evaluates to true
            # throw an error message
            #
            print("%s (line: %s) %s::%s: no montage loaded" %
                  (__FILE__, ndt.__LINE__, Montage.__CLASS_NAME__,
                   ndt.__NAME__))
            sys.exit(os.EX_SOFTWARE)

        # find the subtrahends
        #
        subtrahends = []
        for key in self.montage_d:

            # check if there's a label there
            #
            try:
                subtrahends.append(self.montage_d[key][1])

            # if no label then move on
            #
            except:

                if null_fill:
                    subtrahends.append(None)

        # exit gracefully
        #
        return subtrahends
    #
    # end of method

    def load_channels_order(self):

        """
        method: load_channels_order

        arguments:
         none

        return:
         boolean value indicating status

        description:
         This method loads the channel order
        """

        #display debug information
        #
        if self.dbgl_d == ndt.FULL:
            print("%s (line: %s) %s::%s: fetching subtrahends" %
                  (__FILE__, ndt.__LINE__, Montage.__CLASS_NAME__,
                   ndt.__NAME__))

        # ensure the montage instance has a channel
        # order varaible
        #
        if not hasattr(self, ATTR_MONTAGE_D) or self.montage_d is None:

            # if the if statement evaluates to true
            # throw an error message
            #
            print("%s (line: %s) %s::%s: no montage loaded" %
                  (__FILE__, ndt.__LINE__, Montage.__CLASS_NAME__,
                   ndt.__NAME__))
            return False

        # create channels_order list variable
        #
        channels_order = list()

        # fetch minudes
        #
        minudes = self.get_minuends()

        # fetch subtrahends
        #
        subtrahends = self.get_subtrahends(null_fill = True)

        # loop over all minudes and subtrahens
        #
        for minude, subtrahend in zip(minudes, subtrahends):


            # if a minude is not in channels_order
            # append minude to channels_order
            #
            if minude not in channels_order:

                # append minude to channels_order
                #
                channels_order.append(minude)

            # if a subtrahend is not in channels_order
            # append subtrahend to channels_order
            #
            if subtrahend is not None and subtrahend not in channels_order:

                # append subtrahend to channels order
                #
                channels_order.append(subtrahend)

        # store the channel order
        #
        self.chan_order_d = channels_order

        # exit gracefully
        #
        return True

    #
    # end of method

    def get_channels_order(self):
        """
        method: get_channels_order

        arguments:
         none

        return:
         a list representing the channel order

        description:
         This method fetches the channel order
        """

        # ensure the montage instance has a channel
        # order varaible
        #
        if not hasattr(self, ATTR_CHAN_ORDER_D) or self.chan_order_d is None:

            # if the if statement evaluates to true
            # throw an error message
            #
            print("%s (line: %s) %s::%s: no montage loaded" %
                  (__FILE__, ndt.__LINE__, Montage.__CLASS_NAME__,
                   ndt.__NAME__))
            sys.exit(os.EX_SOFTWARE)

        # exit gracefully
        #
        return self.chan_order_d
    #
    # end of method



    def load_montages_order(self):
        """
        method: load_montages_order

        arguments:
         none

        return:
         boolean value indicating status

        description:
         This method loads the montage order
        """

        #display debug information
        #
        if self.dbgl_d == ndt.FULL:
            print("%s (line: %s) %s::%s: fetching subtrahends" %
                  (__FILE__, ndt.__LINE__, Montage.__CLASS_NAME__,
                   ndt.__NAME__))

        # ensure the montage instance has a channel
        # order varaible
        #
        if not hasattr(self, ATTR_MONTAGE_D) or self.montage_d is None:

            # if the if statement evaluates to true
            # throw an error message
            #
            print("%s (line: %s) %s::%s: no montage loaded" %
                  (__FILE__, ndt.__LINE__, Montage.__CLASS_NAME__,
                   ndt.__NAME__))
            return False

        # store the montage order
        #
        self.mont_order_d = list(self.montage_d.keys())


        # exit gracefully
        #
        return True
    #
    # end of method

    def get_montage_order(self):
        """
        method: get_montage_order

        arguments:
         none

        return:
         a list representing the montage order

        description:
         This method fetches the montage order
        """

        # ensure the montage instance has a channel
        # order varaible
        #
        if not hasattr(self, ATTR_MONT_ORDER_D) or self.mont_order_d is None:

            # if the if statement evaluates to true
            # throw an error message
            #
            print("%s (line: %s) %s::%s: no montage loaded" %
                  (__FILE__, ndt.__LINE__, Montage.__CLASS_NAME__,
                ndt.__NAME__))
            sys.exit(os.EX_SOFTWARE)

        # check montage is loaded
        #
        if self.montage_d is None:
            print("%s (line: %s) %s::%s: no montage loaded" %
                  (__FILE__, ndt.__LINE__, Montage.__CLASS_NAME__,
                   ndt.__NAME__))
            return None

        # exit gracefully
        #
        return self.mont_order_d
     #
     # end of method

#
# end of class

#
# end of file

