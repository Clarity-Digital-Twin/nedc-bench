#!/usr/bin/env python

# file: $(NEDC_NFC)/class/python/nedc_edf_tools/nedc_edf_tools.py
#
# revision history:
#
# 20241108 (DH): added resampling tools and refactored write_edf
# 20240524 (DB): added write_edf and put_header
# 20230621 (AB): refactor code to the comment format
# 20220107 (JP): cleaned up some standards issues
# 20210809 (JP): added get_header_from_file
# 20210809 (JP): fixed a bug with the cleanup method
# 20200607 (JP): started over using our own code because the open source
#                versions of this software were not adequately robust
# 20200219 (NS): updated to python3
# 20170622 (NC): refactored code into /class/ with more ISIP standards
# 20160511 (MT): refactored code to comply with ISIP standards and to allow
#                input from the command line
# 20141212 (MG): modified to support edf files with non-eeg channels
# 20141020 (MG): changed load_edf to read an edf file between two specified
#                times (t1,t2)
# 20140812 (MG): initial version
#
# This file contains a Python implementation of the C++ class Edf. It uses a
# dictionary to encapsulate metadata when this data is passed as an argument.
# The metadata dictionary should contain the following key-value pairs
# (default means that the field is optional and will be replaced with the
# default value if null):
#
#  'id_patient': patient ID (string, max 16 characters, default: 'X')
#  'sex': patient gender (string, max 16 characters, default: 'X')
#  'date_of_birth': patient's DOB (string, max 16 chars, default: 'X')
#  'full_name': patient's full name (string, max 16 characters, default: 'X')
#  'age': patient's age (string, max 16 characters, default: 'X')
#  'date_exam_1': start date of the recording, formatted as DD-MMM-YYYY
#                 (e.g. 01-JAN-2000) (string, max 16 characters, default: '')
#  'id_exam': EEG ID (string, max 16 characters, default: 'X')
#  'lrci_tech': technician (string, max 16 characters, default: '')
#  'lrci_machine': machine (string, max 16 characters, default: '')
#  'date_exam_2': start date of the recording, formatted as DD.MM.YY
#                 (e.g. 01.01.00) (string, max 8 characters, default: '')
#  'start_time': start time of the recording, formatted as HH.MM.SS
#                (e.g. 12.00.00) (string, max 8 characters, default: '')
#  'ghdi_file_type': file type (string, max 5 characters, default: '     ')
#  'ghdi_reserved': reserved field (string, max 39 characters,
#                   default: '                                       ')
#  'num_rec': number of data records (integer)
#  'rec_dur': duration of each data record in seconds (float)
#  'sample_frequency': Sampling frequency in Hz (float)
#  'chan_labels': list of channel labels (list of strings, max 16 characters
#                 each; number of channel labels is used as the number of
#                 channels, which is further used for calculating other
#                 values, it is important for this list to be correct)
#  'chan_trans_type': list of transducer types (list of strings,
#                     max 80 characters each, default: [''] * num_channels)
#  'chan_phys_dim': list of physical dimensions (list of strings,
#                   max 8 characters each, default: ['mV'] * num_channels)
#  'min_values': list of minimum physical values (list of floats,
#                default: [''] * num_channels)
#  'max_values': list of maximum physical values (list of floats,
#                default: [''] * num_channels)
#  'chan_dig_min': List of minimum digital values (list of strings,
#                  max 8 characters each,
#                  default: [str(-EDF_SIG_MAXVAL)] * num_channels)
#  'chan_dig_max': list of maximum digital values (list of strings,
#                  max 8 characters each,
#                  default: [str(EDF_SIG_MAXVAL)] * num_channels)
#  'chan_prefilt': list of prefiltering information (list of strings,
#                  max 80 characters each, default: [''] * num_channels)
#  'samples_per_channel': number of samples in each data record (integer)
#
# In an EDF file, the signal data is split into records of equal
# duration, specified by the 'rec_dur' field in the metadata
# dictionary. The number of records, specified by the 'num_rec' field,
# is calculated by dividing the total duration of the recording
# (total_samples / sample_frequency) by the record duration and
# rounding up to the nearest integer. Each record contains a fixed
# number of samples for each channel, determined by multiplying the
# record duration by the sampling frequency (rec_dur *
# sample_frequency).
#
# This signal dictionary is defined as follows:
#
#  the signal should be a 2D numpy array of integers
#  with dimensions [num_channels, total_samples], where:
#
#   num_channels is the number of channels in the recording
#   total_samples is the total number of samples per channel
#
# In the EDF format, the signal data is stored as unscaled integer
# values. The physical range of each channel is defined in the header by
# the 'phys_min' and 'phys_max' fields, while the corresponding digital
# range is defined by the 'dig_min' and 'dig_max' fields. When preparing
# the signal data for writing to an EDF file, you should ensure that the
# values in the 2D array are unscaled integers that fall within the
# digital range specified in the header.
#
# To convert the signal data from physical units (e.g., microvolts)
# to unscaled integer values, you can use the following formula:
#
#  DigVal = (PhysVal - PhysMin) * (DigMax - DigMin)
#                               / (PhysMax - PhysMin) + DigMin
#
# The code in this library must parallel the C++ version of this code.
#------------------------------------------------------------------------------

# import required system modules
#
import numpy as np
import os
from scipy.signal import resample_poly, decimate, kaiserord, firwin
import struct
import sys
import math
import copy
import re

# import NEDC modules
#
import nedc_debug_tools as ndt
import nedc_file_tools as nft
import nedc_mont_tools as nmt

#------------------------------------------------------------------------------
#
# global variables are listed here
#
#------------------------------------------------------------------------------

# set the filename using basename
#
__FILE__ = os.path.basename(__file__)

#------------------------------------------------------------------------------
#
# this special section defines an Edf header byte by byte
#
#------------------------------------------------------------------------------

# section (1): version information
#
EDF_VERS_NAME = "version"
EDF_VERS_BSIZE = int(8)
EDF_VERS = b"0       "

# section (2): patient information
#
EDF_LPTI_BSIZE = int(80)
EDF_LPTI_TSIZE = int(119)

EDF_LPTI_PATIENT_ID_NAME = "ltpi_patient_id"
EDF_LPTI_GENDER_NAME = "ltpi_gender"
EDF_LPTI_DOB_NAME = "ltpi_dob"
EDF_LPTI_FULL_NAME_NAME = "ltpi_full_name"
EDF_LPTI_AGE_NAME = "ltpi_age"

# section (3): local recording information
#
EDF_LRCI_BSIZE = int(80)
EDF_LRCI_TSIZE = EDF_LPTI_TSIZE
EDF_LRCI_RSIZE = EDF_LPTI_BSIZE

EDF_LRCI_START_DATE_LABEL = "lrci_start_date_label"
EDF_LRCI_START_DATE_LABEL_META = "Startdate"
EDF_LRCI_START_DATE = "lrci_start_date"
EDF_LRCI_EEG_ID = "lrci_eeg_id"
EDF_LRCI_TECH = "lrci_tech"
EDF_LRCI_MACHINE = "lrci_machine"

# section (4): general header information
#
EDF_GHDI_BSIZE = int(8 + 8 + 8 + 5 + 39 + 8 + 8 + 4)
EDF_GHDI_TSIZE = EDF_LPTI_TSIZE

EDF_GHDI_START_DATE = "ghdi_start_date"
EDF_GHDI_START_TIME = "ghdi_start_time"
EDF_GHDI_HSIZE = "ghdi_hsize"
EDF_GHDI_FILE_TYPE = "ghdi_file_type"
EDF_GHDI_RESERVED = "ghdi_reserved"
EDF_GHDI_NUM_RECS = "ghdi_num_recs"
EDF_GHDI_DUR_REC = "ghdi_dur_rec"
EDF_GHDI_NSIG_REC = "ghdi_nsig_rec"

# section (5): channel-specific information
#
EDF_LABL_BSIZE = int(16)
EDF_TRNT_BSIZE = int(80)
EDF_PDIM_BSIZE = int( 8)
EDF_PMIN_BSIZE = int( 8)
EDF_PMAX_BSIZE = int( 8)
EDF_DMIN_BSIZE = int( 8)
EDF_DMAX_BSIZE = int( 8)
EDF_PREF_BSIZE = EDF_TRNT_BSIZE
EDF_RECS_BSIZE = int( 8)

EDF_CHAN_LABELS = "chan_labels"
EDF_CHAN_TRANS_TYPE = "chan_trans_type"
EDF_CHAN_PHYS_DIM = "chan_phys_dim"
EDF_CHAN_PHYS_MIN = "chan_phys_min"
EDF_CHAN_PHYS_MAX = "chan_phys_max"
EDF_CHAN_DIG_MIN = "chan_dig_min"
EDF_CHAN_DIG_MAX = "chan_dig_max"
EDF_CHAN_PREFILT = "chan_prefilt"
EDF_CHAN_REC_SIZE = "chan_rec_size"

# section (6): derived values
#
EDF_SAMPLE_FREQUENCY = "sample_frequency"
EDF_NUM_CHANNELS_SIGNAL = "num_channel_signal"
EDF_NUM_CHANNELS_ANNOTATION = "num_channels_annotation"

# other important definitions
#
EDF_BSIZE = int(256)
EDF_ANNOTATION_KEY = "ANNOTATION"
EDF_FTYP_NAME = "ftype"
EDF_FTYP_BSIZE = int(5)
EDF_FTYP = "EDF  "
EDF_SIG_MAXVAL = int(32767)
EDF_SIZEOF_SHORT = int(2)

# define variables needed for conventional down sampling
#
DEF_EDFR_FTYPE = 'fir'
DEF_EDFR_FORDER = int(1024)

# define default values
#
EDF_DEF_CHAN = int(-1)
EDF_DEF_DBG_NF = int(10)

# define an regex to extract raw channel names
#
DEF_EDF_RAW_CHAN_REGEX = r'(?:.*\s+)?(?P<chan>[^ \-]+)-[^ \-]+\s*$'

#------------------------------------------------------------------------------
#
# functions are listed here
#
#------------------------------------------------------------------------------

def set_limits(f1, f2, fmax):
    """
    function: set_limits

    arguments:
     long f1: desired first index (input)
     long f2: desired number of items (input)
     long fmax: maximum number available (input)

    return: a boolean value indicating status
     long& n1: first index (output)
     long& n2: last_index (output)

    description:
     This method returns a range [n1, n2] that is clipped based
     on the inputs.
    """

    # initial the output to the max range
    #
    n1 = int(0)
    n2 = int(fmax)

    # clip n1
    #
    if f1 > int(0):
        n1 = min(f1, fmax - 1)

    # clip n2
    #
    if f2 == int(0):
        n2 = n1
        return(n1, n2)
    elif f2 > int(0):
        n2 = min(n1 + f2, n2)

    # exit gracefully
    #
    return(n1, n2)

#------------------------------------------------------------------------------
#
# classes are listed here
#
#------------------------------------------------------------------------------

# class: Edf
#
class Edf:
    """
    class: Edf

    arguments:
     none

    description:
     This is class is a Python implementation of the C++ class Edf.
     Its interface parallels that class.
    """
    # define static variables for debug and verbosity
    #
    dbgl_d = ndt.Dbgl()
    vrbl_d = ndt.Vrbl()

    #--------------------------------------------------------------------------
    #
    # constructors are listed here
    #
    #--------------------------------------------------------------------------
    def __init__(self):
        """
        method: constructor

        arguments:
         none

        return:
         none

        description:
         This simple method initializes the class
        """

        # set the class name
        #
        Edf.__CLASS_NAME__ = self.__class__.__name__

        # instantiate header holder object
        #
        self.h_d = {}

    #
    # end of method

    #--------------------------------------------------------------------------
    #
    # print methods are listed here
    #
    #--------------------------------------------------------------------------
    def print_header(self, fp, prefix = nft.DELIM_TAB):
        """
        method: print_header

        arguments:
         fp: stream to be used for printing
         prefix: a prefix character to use for printing

        return:
         a boolean value indicating status

        description:
         This method assumes the header has been loaded and prints it.
        """

        # display debug information
        #
        if self.dbgl_d > ndt.BRIEF:
            print("%s (line: %s) %s::%s: printing Edf header" %
                  (__FILE__, ndt.__LINE__, Edf.__CLASS_NAME__, ndt.__NAME__))

        # (1) version information
        #
        # note we conver this to a string to be compatible with the c++
        # version of this code
        #
        fp.write("%sBlock 1: Version Information\n" % (prefix))
        fp.write("%s version = [%s]\n\n" %
                 (prefix, str(self.h_d[EDF_VERS_NAME], nft.DEF_CHAR_ENCODING)))

        # (2) local patient information
        #
        fp.write("%sBlock 2: Local Patient Information\n" % (prefix))
        fp.write("%s lpti_patient_id = [%s]\n" %
                 (prefix, self.h_d[EDF_LPTI_PATIENT_ID_NAME]))
        fp.write("%s lpti_gender = [%s]\n" %
                 (prefix, self.h_d[EDF_LPTI_GENDER_NAME]))
        fp.write("%s lpti_dob = [%s]\n" %
                 (prefix, self.h_d[EDF_LPTI_DOB_NAME]))
        fp.write("%s lpti_full_name = [%s]\n" %
                 (prefix, self.h_d[EDF_LPTI_FULL_NAME_NAME]))
        fp.write("%s lpti_age = [%s]\n\n" %
                 (prefix, self.h_d[EDF_LPTI_AGE_NAME]))

        # (3) local recording information
        #
        fp.write("%sBlock 3: Local Recording Information\n" % (prefix))
        fp.write("%s lrci_start_date_label = [%s]\n" %
                 (prefix, self.h_d[EDF_LRCI_START_DATE_LABEL]))
        fp.write("%s lrci_start_date = [%s]\n" %
                 (prefix, self.h_d[EDF_LRCI_START_DATE]))
        fp.write("%s lrci_eeg_id = [%s]\n" %
                 (prefix, self.h_d[EDF_LRCI_EEG_ID]))
        fp.write("%s lrci_tech = [%s]\n" %
                 (prefix, self.h_d[EDF_LRCI_TECH]))
        fp.write("%s lrci_machine = [%s]\n\n" %
                 (prefix, self.h_d[EDF_LRCI_MACHINE]))

        # (4) general header information
        #
        fp.write("%sBlock 4: General Header Information\n" % (prefix))
        fp.write("%s ghdi_start_date = [%s]\n" %
                 (prefix, self.h_d[EDF_GHDI_START_DATE]))
        fp.write("%s ghdi_start_time = [%s]\n" %
                 (prefix, self.h_d[EDF_GHDI_START_TIME]))
        fp.write("%s ghdi_hsize = [%ld]\n" %
                 (prefix, self.h_d[EDF_GHDI_HSIZE]))
        fp.write("%s ghdi_file_type = [%s]\n" %
                 (prefix, self.h_d[EDF_GHDI_FILE_TYPE]))
        fp.write("%s ghdi_reserved = [%s]\n" %
                 (prefix, self.h_d[EDF_GHDI_RESERVED]))
        fp.write("%s ghdi_num_recs = [%ld]\n" %
                 (prefix, self.h_d[EDF_GHDI_NUM_RECS]))
        fp.write("%s ghdi_dur_rec = [%lf]\n" %
                 (prefix, self.h_d[EDF_GHDI_DUR_REC]))
        fp.write("%s ghdi_nsig_rec = [%ld]\n\n" %
                 (prefix, self.h_d[EDF_GHDI_NSIG_REC]))

        # (5) channel-specific information
        #
        fp.write("%sBlock 5: Channel-Specific Information\n" % (prefix))
        fp.write("%s chan_labels (%ld) = " %
                 (prefix, self.h_d[EDF_GHDI_NSIG_REC]))

        last_chan = self.h_d[EDF_GHDI_NSIG_REC] - 1
        for i in range(0, last_chan):
            fp.write("[%s], " % (self.h_d[EDF_CHAN_LABELS][i]))
        fp.write("[%s]\n" % ((self.h_d[EDF_CHAN_LABELS])[last_chan]))

        fp.write("%s chan_trans_type (%ld) = " %
                 (prefix, self.h_d[EDF_GHDI_NSIG_REC]))
        for i in range(0, last_chan):
                fp.write("[%s], " % (self.h_d[EDF_CHAN_TRANS_TYPE][i]))
        fp.write("[%s]\n" % (self.h_d[EDF_CHAN_TRANS_TYPE][last_chan]))

        fp.write("%s chan_phys_dim (%ld) = " %
                 (prefix, self.h_d[EDF_GHDI_NSIG_REC]))
        for i in range(0, last_chan):
            fp.write("[%s], " % (self.h_d[EDF_CHAN_PHYS_DIM][i]))
        fp.write("[%s]\n" % (self.h_d[EDF_CHAN_PHYS_DIM][last_chan]))

        fp.write("%s chan_phys_min (%ld) = " %
                 (prefix, self.h_d[EDF_GHDI_NSIG_REC]))
        for i in range(0, last_chan):
            fp.write("[%10.3f], " % (self.h_d[EDF_CHAN_PHYS_MIN][i]))
        fp.write("[%10.3f]\n" % (self.h_d[EDF_CHAN_PHYS_MIN][last_chan]))

        fp.write("%s chan_phys_max (%ld) = " %
                 (prefix, self.h_d[EDF_GHDI_NSIG_REC]))
        for i in range(0, last_chan):
            fp.write("[%10.3f], " % (self.h_d[EDF_CHAN_PHYS_MAX][i]))
        fp.write("[%10.3f]\n" % (self.h_d[EDF_CHAN_PHYS_MAX][last_chan]))

        fp.write("%s chan_dig_min (%ld) = " %
                 (prefix, self.h_d[EDF_GHDI_NSIG_REC]))
        for i in range(0, last_chan):
            fp.write("[%10ld], " % (self.h_d[EDF_CHAN_DIG_MIN][i]))
        fp.write("[%10ld]\n" % (self.h_d[EDF_CHAN_DIG_MIN][last_chan]))

        fp.write("%s chan_dig_max (%ld) = " %
                 (prefix, self.h_d[EDF_GHDI_NSIG_REC]))
        for i in range(0, last_chan):
            fp.write("[%10ld], " % (self.h_d[EDF_CHAN_DIG_MAX][i]))
        fp.write("[%10ld]\n" % (self.h_d[EDF_CHAN_DIG_MAX][last_chan]))

        fp.write("%s chan_prefilt (%ld) = " %
                 (prefix, self.h_d[EDF_GHDI_NSIG_REC]))
        for i in range(0, last_chan):
            fp.write("[%s], " % (self.h_d[EDF_CHAN_PREFILT][i]))
        fp.write("[%s]\n" % (self.h_d[EDF_CHAN_PREFILT][last_chan]))

        fp.write("%s chan_rec_size (%ld) = " %
                 (prefix, self.h_d[EDF_GHDI_NSIG_REC]))
        for i in range(0, last_chan):
            fp.write("[%10ld], " % (self.h_d[EDF_CHAN_REC_SIZE][i]))
        fp.write("[%10ld]\n" % (self.h_d[EDF_CHAN_REC_SIZE][last_chan]))

        fp.write("%s\n" % (prefix))

        # (6) derived values
        #
        fp.write("%sBlock 6: Derived Values\n" % (prefix))
        fp.write("%s hdr_sample_frequency = %10.1f\n" %
                 (prefix, self.h_d[EDF_SAMPLE_FREQUENCY]))
        fp.write("%s hdr_num_channels_signal = %10ld\n" %
                 (prefix, self.h_d[EDF_NUM_CHANNELS_SIGNAL]))
        fp.write("%s hdr_num_channels_annotation = %10ld\n" %
                 (prefix, self.h_d[EDF_NUM_CHANNELS_ANNOTATION]))
        fp.write("%s duration of recording (secs) = %10.1f\n" %
                 (prefix, (float)(self.h_d[EDF_GHDI_DUR_REC] *
                                  self.h_d[EDF_GHDI_NUM_RECS])))

        fp.write("%s per channel sample frequencies:\n" % (prefix))
        for i in range(0, self.h_d[EDF_GHDI_NSIG_REC]):
            fp.write("%s  channel[%4ld]: %10.1f Hz (%s)\n" %
                         (prefix, i,
                          self.get_sample_frequency(i),
                          self.h_d[EDF_CHAN_LABELS][i]))

        # exit gracefully
        #
        return True
    #
    #end of method

    def read_segment(
            self,
            fname,
            s_start,
            s_stop,
            chan_sel = None,
            scale = True
        ):
        """
        method: read_segment

        arguments:
         fname : path of the EDF file
         s_start : start sample index (inclusive, zero based)
         s_stop : stop  sample index (exclusive)
         chan_sel : list of channel labels to extract, or None for all
         scale : if True, convert digital values to physical units

        return:
         hdr_dict : the EDF header dictionary
         sig_dict : dictionary {channel_label: numpy_vector_of_samples}

        description:
         Read a given window of samples from an EDF file.  The window can start
         before the first sample or extend past the last sample; missing regions
         are zero padded.  Each call opens the EDF file, processes the request,
         and closes the file - no persistent cache is kept.
        """

        # open the EDF file in binary read mode
        #
        with open(fname, nft.MODE_READ_BINARY, buffering = 0) as fp_handle:

            # load the header into self.h_d so helper methods can use it
            #
            self.get_header(fp_handle)

            # cache constant header-derived values for this call
            #
            record_duration = self.h_d[EDF_GHDI_DUR_REC]
            samples_per_record = self.h_d[EDF_CHAN_REC_SIZE]
            num_channels_total = self.h_d[EDF_GHDI_NSIG_REC]
            bytes_per_record = 2 * sum(samples_per_record)
            chan_byte_offsets = (
                np.cumsum([0] + samples_per_record) * 2
            )

            # decide which channels to output and build index mappings
            #
            if chan_sel is None:
                selected_indices = list(range(num_channels_total))
                selected_labels = self.h_d[EDF_CHAN_LABELS]
            else:
                selected_labels = [lbl.upper() for lbl in chan_sel]
                selected_indices = [
                    self.h_d[EDF_CHAN_LABELS].index(lbl) for lbl in selected_labels
                ]

            # compute padding and clipping relative to the file limits
            #
            total_samples = self.get_num_samples(0)
            requested_length = int(max(0, s_stop - s_start))
            pad_left = max(0, -s_start)
            pad_right = max(0,  s_stop - total_samples)
            inside_start = max(0,  s_start)
            inside_stop = min(total_samples, s_stop)
            inside_length = max(0,  inside_stop - inside_start)

            # allocate an output frame initialized to zeros
            #
            frame_matrix = np.zeros(
                (len(selected_indices), requested_length), dtype = np.float64
            )

            # immediately return if no part of the window overlaps the file
            #
            if inside_length == 0:
                sig_dict = {
                    lbl: frame_matrix[i] for i, lbl in enumerate(selected_labels)
                }
                if scale:
                    self.dig_to_phys(sig_dict, self.h_d)
                return self.h_d, sig_dict

            # compute first and last record numbers that intersect the window
            #
            first_record = inside_start // samples_per_record[0]
            last_record  = (inside_stop - 1) // samples_per_record[0]

            # seek to the first relevant record within the EDF file
            #
            fp_handle.seek(
                self.h_d[EDF_GHDI_HSIZE] + first_record * bytes_per_record,
                os.SEEK_SET
            )

            # initialize write pointer skipping left padding
            #
            write_ptr = pad_left

            # calculate offset of inside_start within its record
            #
            offset_first = inside_start % samples_per_record[0]

            # iterate over each record that contributes samples
            #
            for record_idx in range(first_record, last_record + 1):

                # read the complete record into memory
                #
                record_buf = fp_handle.read(bytes_per_record)

                # determine slice boundaries inside this record
                #
                slice_start = offset_first if record_idx == first_record else 0
                slice_stop  = (
                    offset_first + inside_length
                    if record_idx == first_record and record_idx == last_record
                    else samples_per_record[0]
                    if record_idx  < last_record
                    else (inside_stop % samples_per_record[0] or
                          samples_per_record[0])
                )

                # compute number of samples to copy from this record
                #
                n_copy = slice_stop - slice_start
                if n_copy <= 0:
                    continue

                # extract the slice for each selected channel
                #
                for out_row, chan_idx in enumerate(selected_indices):

                    # byte offset where this channel begins within the record
                    #
                    byte_off = chan_byte_offsets[chan_idx]

                    # total samples for this channel within one record
                    #
                    samples_in_rec = samples_per_record[chan_idx]

                    # convert raw bytes to float64 values
                    #
                    chan_data = np.frombuffer(
                        record_buf,
                        dtype = "<i2",
                        count = samples_in_rec,
                        offset = byte_off
                    ).astype(np.float64)

                    # copy desired slice into the output matrix
                    #
                    frame_matrix[out_row,
                                 write_ptr : write_ptr + n_copy] = \
                        chan_data[slice_start : slice_stop]

                # advance write_ptr and reset offset_first for subsequent records
                #
                write_ptr += n_copy
                offset_first  = 0

        # build a dictionary mapping channel labels to numpy vectors
        #
        signal_dict = {
            lbl: frame_matrix[i] for i, lbl in enumerate(selected_labels)
        }

        # convert digital values to physical units if requested
        #
        if scale:
            self.dig_to_phys(signal_dict, self.h_d)

        # return header and signal dictionary
        #
        return self.h_d, signal_dict
    #
    # end of method

    def print_header_from_file(self, fname, fp, prefix = nft.DELIM_TAB):
        """
        method: print_header_from_file

        arguments:
         fname: input file
         fp: stream to be used for printing
         prefix: a prefix character to use for printing

        return:
         a boolean value indicating status

        description:
         This opens a file, reads the header, and pretty prints it.
        """

        # declare local variables
        #

        # display debug information
        #
        if self.dbgl_d > ndt.BRIEF:
            print("%s (line: %s) %s::%s: printing Edf header (%s)" %
                  (__FILE__, ndt.__LINE__, Edf.__CLASS_NAME__, ndt.__NAME__,
                   fname))

        # make sure this is an edf file
        #
        if nft.is_edf(fname) == False:
            print("Error: %s (line: %s) %s::%s: not an Edf file (%s)" %
                  (__FILE__, ndt.__LINE__, Edf.__CLASS_NAME__, ndt.__NAME__,
                   fname))
            return False

        # open the file
        #
        fp_edf = open(fname, "rb")
        if fp_edf == None:
            print("Error: %s (line: %s) %s::%s: error opening (%s)" %
                  (__FILE__, ndt.__LINE__, Edf.__CLASS_NAME__, ndt.__NAME__,
                   fname))

        # read the header from a file:
        #  note that we will ignore the signal data
        #
        if self.get_header(fp_edf) == False:
            print("Error: %s (line: %s) %s::%s: error opening (%s)" %
                  (__FILE__, ndt.__LINE__, Edf.__CLASS_NAME__, ndt.__NAME__,
                   fname))
            return False

        # print the header
        #
        self.print_header(fp, prefix)

        # exit gracefully
        #
        return True
    #
    # end of method

    #--------------------------------------------------------------------------
    #
    # get methods are listed here
    #
    #--------------------------------------------------------------------------
    def get_header_from_file(self, fname):
        """
        method: get_header_from_file

        arguments:
         fname: input filename

        return:
         a boolean value indicating status

        description:
         This method reads the header of an edf file given a filename.
        """

        # open the file
        #
        fp_edf = open(fname, "rb")
        if fp_edf == None:
            print("Error: %s (line: %s) %s::%s: error opening (%s)" %
                  (__FILE__, ndt.__LINE__, Edf.__CLASS_NAME__, ndt.__NAME__,
                   fname))
            return False

        # read the header from a file:
        #  note that we will ignore the signal data
        #
        if self.get_header(fp_edf) == False:
            print("Error: %s (line: %s) %s::%s: error opening (%s)" %
                  (__FILE__, ndt.__LINE__, Edf.__CLASS_NAME__, ndt.__NAME__,
                   fname))
            return False

        # exit gracefully
        #
        return True
    #
    # end of method

    def get_header(self, fp):
        """
        method: get_header

        arguments:
         fp: an open file pointer

        return:
         a logical value indicating the status of the get operation

        description:
         This method reads the header of an edf file.
        """

        # declare local variables
        #
        nbytes = int(0)
        num_items = int(0)

        # display debug information
        #
        if self.dbgl_d > ndt.BRIEF:
            print("%s (line: %s) %s::%s: fetching an Edf header" %
                  (__FILE__, ndt.__LINE__, Edf.__CLASS_NAME__, ndt.__NAME__))

        # rewind the file
        #
        fp.seek(0, os.SEEK_SET)

        # (1) version information
        #
        if self.dbgl_d > ndt.BRIEF:
            print("%s (line: %s) %s::%s: fetching (1)" %
                  (__FILE__, ndt.__LINE__, Edf.__CLASS_NAME__, ndt.__NAME__))

        self.h_d[EDF_VERS_NAME] = fp.read(EDF_VERS_BSIZE)
        if self.h_d[EDF_VERS_NAME] != EDF_VERS:
            return False

        # (2) local patient information
        #
        # unfortunately, some edf files don't contain all the information
        # they should. this often occurs because the deidentification
        # process overwrites this information. so we zero out the buffers
        # that won't be filled if the information is missing.
        #
        # note also that sometimes this field is blank, so split might
        # not return an adequate number of fields.
        #
        # finally, we want these stored as strings, not bytes
        #
        if self.dbgl_d > ndt.BRIEF:
            print("%s (line: %s) %s::%s: fetching (2)" %
                  (__FILE__, ndt.__LINE__, Edf.__CLASS_NAME__, ndt.__NAME__))

        fields = (fp.read(EDF_LPTI_BSIZE)).split()

        if len(fields) > int(0):
            self.h_d[EDF_LPTI_PATIENT_ID_NAME] = str(fields[0],
                                                     nft.DEF_CHAR_ENCODING)
        else:
            self.h_d[EDF_LPTI_PATIENT_ID_NAME] = nft.STRING_EMPTY
        if len(fields) > int(1):
            self.h_d[EDF_LPTI_GENDER_NAME] = str(fields[1],
                                                 nft.DEF_CHAR_ENCODING)
        else:
            self.h_d[EDF_LPTI_GENDER_NAME] = nft.STRING_EMPTY
        if len(fields) > int(2):
            self.h_d[EDF_LPTI_DOB_NAME] = str(fields[2],
                                              nft.DEF_CHAR_ENCODING)
        else:
            self.h_d[EDF_LPTI_DOB_NAME] = nft.STRING_EMPTY
        if len(fields) > int(3):
            self.h_d[EDF_LPTI_FULL_NAME_NAME] = str(fields[3],
                                                    nft.DEF_CHAR_ENCODING)
        else:
            self.h_d[EDF_LPTI_FULL_NAME_NAME] = nft.STRING_EMPTY
        if len(fields) > int(4):
            self.h_d[EDF_LPTI_AGE_NAME] = str(fields[4],
                                              nft.DEF_CHAR_ENCODING)
        else:
            self.h_d[EDF_LPTI_AGE_NAME] = nft.STRING_EMPTY

        # (3) local recording information
        #
        # unfortunately, some edf files don't contain all the information
        # they should. this often occurs because the deidentification
        # process overwrites this information. so we zero out the buffers
        # that won't be filled if the information is missing.
        #
        if self.dbgl_d > ndt.BRIEF:
            print("%s (line: %s) %s::%s: fetching (3)" %
                  (__FILE__, ndt.__LINE__, Edf.__CLASS_NAME__, ndt.__NAME__))

        fields = (fp.read(EDF_LRCI_BSIZE)).split()

        if len(fields) > int(0):
            self.h_d[EDF_LRCI_START_DATE_LABEL] = str(fields[0],
                                                      nft.DEF_CHAR_ENCODING)
        else:
            self.h_d[EDF_LRCI_START_DATE_LABEL] = nft.STRING_EMPTY
        if len(fields) > int(1):
            self.h_d[EDF_LRCI_START_DATE] = str(fields[1],
                                                nft.DEF_CHAR_ENCODING)
        else:
            self.h_d[EDF_LRCI_START_DATE] = nft.STRING_EMPTY
        if len(fields) > int(2):
            self.h_d[EDF_LRCI_EEG_ID] = str(fields[2],
                                            nft.DEF_CHAR_ENCODING)
        else:
            self.h_d[EDF_LRCI_EEG_ID] = nft.STRING_EMPTY
        if len(fields) > int(3):
            self.h_d[EDF_LRCI_TECH] = str(fields[3],
                                          nft.DEF_CHAR_ENCODING)
        else:
            self.h_d[EDF_LRCI_TECH] = nft.STRING_EMPTY
        if len(fields) > int(4):
            self.h_d[EDF_LRCI_MACHINE] = str(fields[4],
                                             nft.DEF_CHAR_ENCODING)
        else:
            self.h_d[EDF_LRCI_MACHINE] = nft.STRING_EMPTY

        # (4) general header information
        #
        # get the fourth block of data (non-local information)
        #
        if self.dbgl_d > ndt.BRIEF:
            print("%s (line: %s) %s::%s: fetching (4)" %
                  (__FILE__, ndt.__LINE__, Edf.__CLASS_NAME__, ndt.__NAME__))

        try:
            byte_buf = fp.read(EDF_GHDI_BSIZE)
            buf = str(byte_buf, nft.DEF_CHAR_ENCODING)
        except:
            print("Error: %s (line: %s) %s::%s: char encoding (%s)" %
                  (__FILE__, ndt.__LINE__, Edf.__CLASS_NAME__, ndt.__NAME__,
                   byte_buf))
            return False

        self.h_d[EDF_GHDI_START_DATE] = buf[0:8]
        self.h_d[EDF_GHDI_START_TIME] = buf[8:8+8]
        self.h_d[EDF_GHDI_HSIZE] = nft.atoi(buf[16:16+8])
        self.h_d[EDF_GHDI_FILE_TYPE] = buf[24:24+5]
        self.h_d[EDF_GHDI_RESERVED] = buf[29:29+39]
        self.h_d[EDF_GHDI_NUM_RECS] = nft.atoi(buf[68:68+8])
        self.h_d[EDF_GHDI_DUR_REC] = nft.atof(buf[76:76+8])
        self.h_d[EDF_GHDI_NSIG_REC] = nft.atoi(buf[84:84+4])

        # (5) channel-specific information
        #
        # get the fifth block of data (channel-specific information)
        #
        if self.dbgl_d > ndt.BRIEF:
            print("%s (line: %s) %s::%s: fetching (4)" %
                  (__FILE__, ndt.__LINE__, Edf.__CLASS_NAME__, ndt.__NAME__))

        # (5a) read channel labels
        #
        if self.dbgl_d > ndt.BRIEF:
            print("%s (line: %s) %s::%s: fetching (5a)" %
                  (__FILE__, ndt.__LINE__, Edf.__CLASS_NAME__, ndt.__NAME__))

        buf = fp.read(EDF_LABL_BSIZE * self.h_d[EDF_GHDI_NSIG_REC])

        self.h_d[EDF_NUM_CHANNELS_ANNOTATION] = int(0)
        self.h_d[EDF_CHAN_LABELS] = []
        for i in range(0, self.h_d[EDF_GHDI_NSIG_REC]):

            # grab the channel label
            #
            offset = EDF_LABL_BSIZE * i
            tstr = (str(buf[offset:offset+EDF_LABL_BSIZE],
                       nft.DEF_CHAR_ENCODING)).upper()
            self.h_d[EDF_CHAN_LABELS].append(nft.trim_whitespace(tstr))

            # look for the annotation labels:
            #  note that the label is already upper case
            #
            if EDF_ANNOTATION_KEY in self.h_d[EDF_CHAN_LABELS][i]:
                self.h_d[EDF_NUM_CHANNELS_ANNOTATION] += int(1)

        # (5b) read the transducer type
        #
        if self.dbgl_d > ndt.BRIEF:
            print("%s (line: %s) %s::%s: fetching (5b)" %
                  (__FILE__, ndt.__LINE__, Edf.__CLASS_NAME__, ndt.__NAME__))

        buf = fp.read(EDF_TRNT_BSIZE * self.h_d[EDF_GHDI_NSIG_REC])

        self.h_d[EDF_CHAN_TRANS_TYPE] = []
        for i in range(0, self.h_d[EDF_GHDI_NSIG_REC]):
            offset = EDF_LABL_BSIZE * i
            tstr = str(buf[offset:offset+EDF_TRNT_BSIZE],
                       nft.DEF_CHAR_ENCODING)
            self.h_d[EDF_CHAN_TRANS_TYPE].append(nft.trim_whitespace(tstr))

        # (5c) read the physical dimension
        #
        if self.dbgl_d > ndt.BRIEF:
            print("%s (line: %s) %s::%s: fetching (5c)" %
                  (__FILE__, ndt.__LINE__, Edf.__CLASS_NAME__, ndt.__NAME__))

        buf = fp.read(EDF_PDIM_BSIZE * self.h_d[EDF_GHDI_NSIG_REC])

        self.h_d[EDF_CHAN_PHYS_DIM] = []
        for i in range(0, self.h_d[EDF_GHDI_NSIG_REC]):
            offset = EDF_PDIM_BSIZE * i
            tstr = str(buf[offset:offset+EDF_PDIM_BSIZE],
                       nft.DEF_CHAR_ENCODING)
            self.h_d[EDF_CHAN_PHYS_DIM].append(nft.trim_whitespace(tstr))

        # (5d) read the physical minimum
        #
        if self.dbgl_d > ndt.BRIEF:
            print("%s (line: %s) %s::%s: fetching (5d)" %
                  (__FILE__, ndt.__LINE__, Edf.__CLASS_NAME__, ndt.__NAME__))

        buf = fp.read(EDF_PMIN_BSIZE * self.h_d[EDF_GHDI_NSIG_REC])

        self.h_d[EDF_CHAN_PHYS_MIN] = []
        for i in range(0, self.h_d[EDF_GHDI_NSIG_REC]):
            offset = EDF_PMIN_BSIZE * i
            tstr = str(buf[offset:offset+EDF_PMIN_BSIZE],
                       nft.DEF_CHAR_ENCODING)
            self.h_d[EDF_CHAN_PHYS_MIN].\
                append(nft.atof(nft.trim_whitespace(tstr)))

        # (5e) read the physical maximum
        #
        if self.dbgl_d > ndt.BRIEF:
            print("%s (line: %s) %s::%s: fetching (5e)" %
                  (__FILE__, ndt.__LINE__, Edf.__CLASS_NAME__, ndt.__NAME__))

        buf = fp.read(EDF_PMAX_BSIZE * self.h_d[EDF_GHDI_NSIG_REC])

        self.h_d[EDF_CHAN_PHYS_MAX] = []
        for i in range(0, self.h_d[EDF_GHDI_NSIG_REC]):
            offset = EDF_PMAX_BSIZE * i
            tstr = str(buf[offset:offset+EDF_PMAX_BSIZE],
                       nft.DEF_CHAR_ENCODING)
            self.h_d[EDF_CHAN_PHYS_MAX].\
                append(nft.atof(nft.trim_whitespace(tstr)))

        # (5f) read the digital minimum
        #
        if self.dbgl_d > ndt.BRIEF:
            print("%s (line: %s) %s::%s: fetching (5f)" %
                  (__FILE__, ndt.__LINE__, Edf.__CLASS_NAME__, ndt.__NAME__))

        buf = fp.read(EDF_DMIN_BSIZE * self.h_d[EDF_GHDI_NSIG_REC])

        self.h_d[EDF_CHAN_DIG_MIN] = []
        for i in range(0, self.h_d[EDF_GHDI_NSIG_REC]):
            offset = EDF_DMIN_BSIZE * i
            tstr = str(buf[offset:offset+EDF_DMIN_BSIZE],
                       nft.DEF_CHAR_ENCODING)
            self.h_d[EDF_CHAN_DIG_MIN].\
                append(nft.atoi(nft.trim_whitespace(tstr)))

        # (5g) read the digital maximum
        #
        if self.dbgl_d > ndt.BRIEF:
            print("%s (line: %s) %s::%s: fetching (5g)" %
                  (__FILE__, ndt.__LINE__, Edf.__CLASS_NAME__, ndt.__NAME__))

        buf = fp.read(EDF_DMAX_BSIZE * self.h_d[EDF_GHDI_NSIG_REC])

        self.h_d[EDF_CHAN_DIG_MAX] = []
        for i in range(0, self.h_d[EDF_GHDI_NSIG_REC]):
            offset = EDF_DMAX_BSIZE * i
            tstr = str(buf[offset:offset+EDF_DMAX_BSIZE],
                       nft.DEF_CHAR_ENCODING)
            self.h_d[EDF_CHAN_DIG_MAX].\
                append(nft.atoi(nft.trim_whitespace(tstr)))

        # (5h) read the prefilt labels
        #
        if self.dbgl_d > ndt.BRIEF:
            print("%s (line: %s) %s::%s: fetching (5h)" %
                  (__FILE__, ndt.__LINE__, Edf.__CLASS_NAME__, ndt.__NAME__))

        buf = fp.read(EDF_PREF_BSIZE * self.h_d[EDF_GHDI_NSIG_REC])

        self.h_d[EDF_CHAN_PREFILT] = []
        for i in range(0, self.h_d[EDF_GHDI_NSIG_REC]):
            offset = EDF_PREF_BSIZE * i
            tstr = str(buf[offset:offset+EDF_PREF_BSIZE],
                       nft.DEF_CHAR_ENCODING)
            self.h_d[EDF_CHAN_PREFILT].append(nft.trim_whitespace(tstr))

        # (5i) read the rec sizes
        #
        if self.dbgl_d > ndt.BRIEF:
            print("%s (line: %s) %s::%s: fetching (5i)" %
                  (__FILE__, ndt.__LINE__, Edf.__CLASS_NAME__, ndt.__NAME__))

        buf = fp.read(EDF_RECS_BSIZE * self.h_d[EDF_GHDI_NSIG_REC])

        self.h_d[EDF_CHAN_REC_SIZE] = []
        for i in range(0, self.h_d[EDF_GHDI_NSIG_REC]):
            offset = EDF_RECS_BSIZE * i
            tstr = str(buf[offset:offset+EDF_RECS_BSIZE],
                       nft.DEF_CHAR_ENCODING)
            self.h_d[EDF_CHAN_REC_SIZE].\
                append(nft.atoi(nft.trim_whitespace(tstr)))

        # (5j) the last chunk of the header is reserved space
        # that we don't need to read. however, we need to advance the
        # file pointer to be safe.
        #
        if self.dbgl_d > ndt.BRIEF:
            print("%s (line: %s) %s::%s: fetching (5j)" %
                  (__FILE__, ndt.__LINE__, Edf.__CLASS_NAME__, ndt.__NAME__))

        fp.seek(self.h_d[EDF_GHDI_HSIZE], os.SEEK_SET)

        # (6) compute some derived values
        #
        if self.dbgl_d > ndt.BRIEF:
            print("%s (line: %s) %s::%s: fetching (6)" %
                  (__FILE__, ndt.__LINE__, Edf.__CLASS_NAME__, ndt.__NAME__))

        self.h_d[EDF_SAMPLE_FREQUENCY] = \
            (float(self.h_d[EDF_CHAN_REC_SIZE][0]) /
             float(self.h_d[EDF_GHDI_DUR_REC]))
        self.h_d[EDF_NUM_CHANNELS_SIGNAL] = \
            int(self.h_d[EDF_GHDI_NSIG_REC] -
                self.h_d[EDF_NUM_CHANNELS_ANNOTATION])

        # exit gracefully
        #
        return True
    #
    # end of method

    def get_sample_frequency(self, chan = EDF_DEF_CHAN):
        """
        method: get_sample_frequency

        arguments:
         chan: the input channel index

        return:
         a floating point value containing the sample frequency

        description:
         none
        """
        if chan == EDF_DEF_CHAN:
           return self.h_d[EDF_SAMPLE_FREQUENCY]
        else:
            return (float(self.h_d[EDF_CHAN_REC_SIZE][chan]) /
                    float(self.h_d[EDF_GHDI_DUR_REC]))

    def get_num_samples(self, chan = EDF_DEF_CHAN):
        """
        method: get_num_samples

        arguments:
         chan: the input channel index

        return:
         an integer value containing the number of samples

        description:
         none
        """

        return int(self.h_d[EDF_CHAN_REC_SIZE][chan] *
                   self.h_d[EDF_GHDI_NUM_RECS])

    def get_duration(self):
        """
        method: get_duration

        arguments:
         none

        return:
         a float containing the duration in secs

        description:
         none
        """

        return (float(self.h_d[EDF_GHDI_DUR_REC] *
                      float(self.h_d[EDF_GHDI_NUM_RECS])))

    #--------------------------------------------------------------------------
    #
    # put methods are listed here
    #
    #--------------------------------------------------------------------------

    def put_header(self, ofile, metadata, num_chan):
        """
        method:put_header

        arguments:
         ofile: address of the output file
         metadata: dictionary with metadata
         num_chan: number of channels

        return:
         a boolean value indicating status

        description:
         This method writes the header from the metadata dictionary for edf
         file.
        """

        # display a debug message
        #
        if self.dbgl_d > ndt.BRIEF:
            print("%s (line: %s) %s: creating an Edf Header [%s]" %
                  (__FILE__, ndt.__LINE__, ndt.__NAME__, ofile))

        # open file for writing
        #
        with open(ofile, 'wb') as fp:

            # declare the bytearray
            #
            header = bytearray()

            # section (1): version information
            #
            # write version
            #
            header.extend(EDF_VERS)

            # section (2): patient information
            #
            # write lpti_patient_id
            #
            patient_info = list()
            patient_id = \
                metadata.get(EDF_LPTI_PATIENT_ID_NAME, 'X')
            patient_info.append(patient_id)

            # write lpti_gender
            #
            sex = metadata.get(EDF_LPTI_GENDER_NAME, 'X')
            patient_info.append(sex)

            # write lpti_dob
            #
            date_of_birth = metadata.get(EDF_LPTI_DOB_NAME, 'X')
            patient_info.append(date_of_birth)

            # write lpti_full_name
            #
            full_name = \
                metadata.get(EDF_LPTI_FULL_NAME_NAME, 'X')
            patient_info.append(full_name)

            # write lpti_age
            #
            age = metadata.get(EDF_LPTI_AGE_NAME, 'X')
            patient_info.append(age)

            header.extend(" ".join(patient_info).ljust(80).encode())

            # section (3): local recording information
            #
            # write lrci_start_date_label
            #
            record_info = list()
            record_info.append(EDF_LRCI_START_DATE_LABEL_META)

            # write lrci_start_date
            #
            lrci_start_date = metadata.get(EDF_LRCI_START_DATE, '')
            record_info.append(lrci_start_date)

            # write lrci_eeg_id
            #
            lrci_eeg_id = metadata.get(EDF_LRCI_EEG_ID, ' X')
            record_info.append(lrci_eeg_id)

            # write lrci_tech
            #
            lrci_tech = metadata.get(EDF_LRCI_TECH, '')
            record_info.append(lrci_tech)

            # write lrci_machine
            #
            lrci_machine = metadata.get(EDF_LRCI_MACHINE, '')
            record_info.append(lrci_machine)

            header.extend(" ".join(record_info).ljust(80).encode())

            # section (4): general header information
            #
            # write ghdi_start_date
            #
            ghdi_start_date = metadata.get(EDF_GHDI_START_DATE, '')
            header.extend(ghdi_start_date.ljust(8).encode())

            # write ghdi_start_time
            #
            ghdi_start_time = metadata.get(EDF_GHDI_START_TIME, '')
            header.extend(ghdi_start_time.ljust(8).encode())

            # write ghdi_hsize
            #
            hsize = num_chan * EDF_BSIZE + EDF_BSIZE
            header.extend(str(hsize).ljust(8).encode())

            # write ghdi_file_type
            #
            header.extend(metadata.get(EDF_GHDI_FILE_TYPE, '     ').\
                          ljust(5).encode())

            # write ghdi_reserved
            #                                          Startdate
            ghdi_reserved = \
                metadata.get(EDF_GHDI_RESERVED, \
                             '                                       ')

            header.extend(ghdi_reserved.ljust(39).encode())

            # write ghdi_num_recs
            #
            ghdi_num_recs = str(metadata.get(EDF_GHDI_NUM_RECS))

            header.extend(ghdi_num_recs.ljust(8).encode())

            # write ghdi_dur_rec
            #
            ghdi_dur_rec = str(metadata.get(EDF_GHDI_DUR_REC))
            header.extend(ghdi_dur_rec.ljust(8, '0').encode())

            # write ghdi_nsig_rec
            #
            header.extend(str(num_chan).ljust(4).encode())

            # section (5): channel-specific information
            #
            # write chan_labels
            #
            for label in metadata.get(EDF_CHAN_LABELS, [''] * num_chan):
                header.extend(label.ljust(16).encode())

            # write chan_trans_type
            #
            chan_trans_type = \
                metadata.get(EDF_CHAN_TRANS_TYPE, [''] * num_chan)

            for trans_type in chan_trans_type:
                header.extend(trans_type.ljust(80).encode())

            # write chan_phys_dim
            #
            chan_phys_dim = \
                metadata.get(EDF_CHAN_PHYS_DIM, ['mV'] * num_chan)

            for phys_dim in chan_phys_dim:
                header.extend(str(phys_dim).ljust(8).encode())

            # write chan_phys_min
            #
            chan_phys_min = \
                metadata.get(EDF_CHAN_PHYS_MIN, [''] * num_chan)

            for phys_min in chan_phys_min:
                if phys_min == '':
                    phys_min_str = ''.ljust(8)
                else:
                    try:
                        phys_min_float = float(phys_min)
                        phys_min_str = f"{phys_min_float:.6f}".rjust(8)[:8]
                    except ValueError:
                        phys_min_str = ''.ljust(8)
                header.extend(phys_min_str.encode())

            # write chan_phys_max
            #
            chan_phys_max = \
                metadata.get(EDF_CHAN_PHYS_MAX, [''] * num_chan)

            for phys_max in chan_phys_max:
                if phys_max == '':
                    phys_max_str = ''.ljust(8)
                else:
                    try:
                        phys_max_float = float(phys_max)
                        phys_max_str = f"{phys_max_float:.7f}"[:8].ljust(8)
                    except ValueError:
                        phys_max_str = ''.ljust(8)
                header.extend(phys_max_str.encode())

            # write chan_dig_min
            #
            chan_dig_min = \
                metadata.get(EDF_CHAN_DIG_MIN, [str(-EDF_SIG_MAXVAL)] * num_chan)

            for dig_min in chan_dig_min:
                header.extend(str(dig_min).ljust(8).encode())

            # write chan_dig_max
            #
            chan_dig_max = \
                metadata.get(EDF_CHAN_DIG_MAX, [str(EDF_SIG_MAXVAL)] * num_chan)

            for dig_max in chan_dig_max:
                header.extend(str(dig_max).ljust(8).encode())

            # write chan_prefilt
            #
            for prefilt in metadata.get(EDF_CHAN_PREFILT, [''] * num_chan):
                header.extend(prefilt.ljust(80).encode())

            # write chan_rec_size
            #
            rec_len_vals = metadata[EDF_CHAN_REC_SIZE]
            rec_len_strs = \
                [str(rec_len).ljust(8) for rec_len in rec_len_vals]

            for rec_len_str in rec_len_strs:
                header.extend(rec_len_str.encode())

            # write remainder of the header as spaces
            #
            needed_padding = metadata[EDF_GHDI_HSIZE] - len(header)

            extra = ' ' * needed_padding
            header.extend(extra.encode())

            with open(ofile, 'wb') as fp:
                fp.write(header)


            # display a debug message
            #
            if self.dbgl_d > ndt.BRIEF:
                print("%s (line: %s) %s::%s: done writing the edf header" %
                    (__FILE__, ndt.__LINE__, Edf.__CLASS_NAME__, ndt.__NAME__))

        # exit gracefully
        #
        return True

    #
    # end of method

    def put_signal(self, ofile, metadata, signal, num_chan):
        """
        method:put_signal

        arguments:
         ofile: address of output file
         metadata: dictionary with metadata
         signal: dictionary of arrays with signal samplings
         num_chan: number of channels

        return:
         a boolean value indicating status

        description:
         This method writes the signal from the 2D array for edf
         file.
        """

        # display a debug message
        #
        if self.dbgl_d > ndt.BRIEF:
            print("%s (line: %s) %s: writing the data to an Edf file [%s]" %
                  (__FILE__, ndt.__LINE__, ndt.__NAME__, ofile))

        # open the file and put file pointer at the end of the header
        #
        fp = open(ofile, nft.MODE_READ_WRITE_BINARY)
        lines = fp.readlines()
        header_offset = EDF_BSIZE + EDF_BSIZE * num_chan
        fp.seek(header_offset)
        lines = fp.readlines()

        # get number and length of records from metadata
        #
        num_rec = metadata[EDF_GHDI_NUM_RECS]
        chan_rsize = metadata[EDF_CHAN_REC_SIZE]
        value_prev = None

        # write the channel signals to the file
        #
        for record in range(num_rec):

            # iterate over all channels
            #
            for index, channel in enumerate(signal):

                # fetch needed channel indices
                #
                rec_len = round(chan_rsize[index])
                start_index = record * rec_len
                end_index = start_index + rec_len
                channel_data = signal[channel][int(start_index):int(end_index)]

                # write needed channel data values to the file
                #
                for counter, value in enumerate(channel_data):

                    # apply a cutoff filter
                    #
                    value = max(-EDF_SIG_MAXVAL, min(EDF_SIG_MAXVAL, value))

                    # write the signed integer to the file
                    #
                    fp.write(struct.pack('<h', int(value)))

                    value_prev = value

        fp.close()
        # display a debug message
        #
        if self.dbgl_d > ndt.BRIEF:
            print("%s (line: %s) %s: done writing the data to an Edf file" %
                  (__FILE__, ndt.__LINE__, ndt.__NAME__))

        # exit gracefully
        #
        return True
    #
    # end of method

    #--------------------------------------------------------------------------
    #
    # edf file methods are listed here
    #
    #--------------------------------------------------------------------------

    def read_edf(self, fname, scale, sflag = True):
        """
        method: read_edf

        arguments:
         fname: input filename
         scale: if true, scale the signal based on the header data
         sflag: if true, read the signal data

        return:
         the header and the signal data as dictionaries

        description:
         This method reads an edf file, and returns the raw signal data.
        """

        # declare local variables
        #
        sig = dict()

        # display debug information
        #
        if self.dbgl_d > ndt.BRIEF:
            print("%s (line: %s) %s::%s: opening an EDF file (%s)" %
                  (__FILE__, ndt.__LINE__, Edf.__CLASS_NAME__, ndt.__NAME__,
                   fname))

        # open the file
        #
        fp = open(fname, nft.MODE_READ_BINARY)
        if fp is None:
            print("Error: %s (line: %s) %s::%s: error opening file (%s)" %
                  (__FILE__, ndt.__LINE__, Edf.__CLASS_NAME__, ndt.__NAME__,
                   fname))
            return (None, None)

        # get the size of the file on disk
        #
        fp.seek(0, os.SEEK_END)
        file_size_in_bytes = fp.tell()
        fp.seek(0, os.SEEK_SET)
        if self.dbgl_d > ndt.BRIEF:
            print("%s (line: %s) %s::%s: file size = %ld bytes" %
                  (__FILE__, ndt.__LINE__, Edf.__CLASS_NAME__, ndt.__NAME__,
                   file_size_in_bytes))

        # load the header
        #
        if self.get_header(fp) == False:
            print("Error: %s (line: %s) %s::%s: error in get_header (%s)" %
                  (__FILE__, ndt.__LINE__, Edf.__CLASS_NAME__, ndt.__NAME__,
                   fname))
            return (None, None)

        # exit if necessary
        #
        if sflag == False:
            fp.close()
            return (self.h_d, None)

        # display debug information
        #
        if self.dbgl_d > ndt.BRIEF:
            self.print_header(sys.stdout)

        # position the file to the beginning of the data
        # using the header information
        #
        if self.dbgl_d > ndt.BRIEF:
            print("%s (line: %s) %s::%s: positioning file pointer" %
                  (__FILE__, ndt.__LINE__, Edf.__CLASS_NAME__, ndt.__NAME__))

        fp.seek(self.h_d[EDF_GHDI_HSIZE], os.SEEK_SET)

        # create space to hold the entire signal:
        #  in python, we only need to size the numpy arrays
        #
        for i in range(0, self.h_d[EDF_GHDI_NSIG_REC]):
            sz = int(self.h_d[EDF_GHDI_NUM_RECS] *
                     self.h_d[EDF_CHAN_REC_SIZE][i])
            sig[self.h_d[EDF_CHAN_LABELS][i]] = \
                np.empty(shape = sz, dtype = np.float64)

            if (self.dbgl_d == ndt.FULL) and (i < EDF_DEF_DBG_NF):
                print("%s (line: %s) %s::%s %s (%s: %ld row, %ld cols)" %
                      (__FILE__, ndt.__LINE__, Edf.__CLASS_NAME__,
                       ndt.__NAME__, "sig dimensions",
                       self.h_d[EDF_CHAN_LABELS][i], i,
                       sig[self.h_d[EDF_CHAN_LABELS][i]].shape[0]))

        if self.dbgl_d > ndt.BRIEF:
            print("%s (line: %s) %s::%s signal vector resized" %
                  (__FILE__, ndt.__LINE__, Edf.__CLASS_NAME__, ndt.__NAME__))

        # loop over all records
        #
        ns_read = np.zeros(shape = self.h_d[EDF_GHDI_NSIG_REC], dtype = int)
        for i in range(0, self.h_d[EDF_GHDI_NUM_RECS]):

            # loop over all channels
            #
            for j in range(0, self.h_d[EDF_GHDI_NSIG_REC]):

                # display debug message
                #
                if (self.dbgl_d == ndt.FULL) and (i < EDF_DEF_DBG_NF) and \
                   (j < EDF_DEF_DBG_NF):
                    print("%s (line: %s) %s::%s: %s [%ld %ld]" %
                          (__FILE__, ndt.__LINE__, Edf.__CLASS_NAME__,
                           ndt.__NAME__,
                           "reading record no.", i, j))

                # read the data:
                #  store the data after the last sample read
                #
                num_samps = self.h_d[EDF_CHAN_REC_SIZE][j]
                data = fp.read(num_samps * EDF_SIZEOF_SHORT)
                buf = np.frombuffer(data, dtype = "short", count = num_samps) \
                      .astype(np.float64)
                ns_read[j] += num_samps

                if num_samps != int(len(data) / EDF_SIZEOF_SHORT):
                    print("Error: %s (line: %s) %s::%s: %s [%d][%d]" %
                          (__FILE__, ndt.__LINE__, Edf.__CLASS_NAME__,
                           ndt.__NAME__, "read error",
                           num_samps, int(len(data)/EDF_SIZEOF_SHORT)))
                    return (None, None)


                # compute scale factors:
                #  this code is identical to the C++ version
                sum_n = float(self.h_d[EDF_CHAN_PHYS_MAX][j] - \
                              self.h_d[EDF_CHAN_PHYS_MIN][j])
                sum_d = float(self.h_d[EDF_CHAN_DIG_MAX][j] -
                              self.h_d[EDF_CHAN_DIG_MIN][j])

                if (self.dbgl_d == ndt.FULL) and (i < EDF_DEF_DBG_NF) and \
                   (j < EDF_DEF_DBG_NF):
                    print("%s (line: %s) %s::%s [%f %f]" %
                          (__FILE__, ndt.__LINE__, Edf.__CLASS_NAME__,
                           ndt.__NAME__, sum_n, sum_d))

                # save the record into its corresponding channel array
                # in the signal dictionary
                #
                offset = i * self.h_d[EDF_CHAN_REC_SIZE][j]
                sig[self.h_d[EDF_CHAN_LABELS][j]][offset:offset+num_samps] = \
                    buf

        # display debug information
        #
        if self.dbgl_d > ndt.BRIEF:
            print("%s (line: %s) %s::%s closing an EDF file" %
                  (__FILE__, ndt.__LINE__, Edf.__CLASS_NAME__, ndt.__NAME__))

        # close the file
        #
        fp.close()

        # scale the channel data if needed (convert from physical to digital)
        #
        if scale == True:

            # convert from digital to physical
            #
            self.dig_to_phys(sig, self.h_d)

        # display debug information
        #
        if self.dbgl_d > ndt.BRIEF:
            print("%s (line: %s) %s::%s: done closing an EDF file" %
                  (__FILE__, ndt.__LINE__, Edf.__CLASS_NAME__, ndt.__NAME__))

        # exit gracefully
        #
        return (self.h_d, sig)
    #
    # end of method

    def write_edf(self, ofile, metadata, signal):
        """
        method: write_edf

        arguments:
         ofile: output filename
         metadata: a dictionary containing the metadata for the header
         signal: the signal data (a vector of vectors)

        return:
         a boolean value indicating status

        description:
         This method writes an edf file from the metadata and the signal data.
        """

        # find number of channels
        #
        num_chan = len(metadata['chan_labels'])

        # write header
        #
        self.put_header(ofile, metadata, num_chan)

        # write signal
        #
        self.put_signal(ofile, metadata, signal, num_chan)

        # exit gracefully
        #
        return True
    #
    # end of method

    #--------------------------------------------------------------------------
    #
    # conversion methods listed here
    #
    #--------------------------------------------------------------------------

    def update_mont_hdr(self, hdr, monsig, mont_dict, scale):
        """
        method: update_mont_hdr

        arguments:
         hdr: The original header (e.g., read from the EDF file).
         monsig: Montage signals keyed by the new montage channel labels.
          Each value is a NumPy array containing the montage data.
         mont_dict: A dictionary mapping montage channel names to a list of
          component raw channel labels. If provided, this is used to select
          referene channel parameters.
         scale:
          If True, recompute the physical min/max values from the montage signal.

        Returns: A new header dictionary updated with montage channel information.

        description: this method returns a modified version of the original EDF
         header that is compatible with a montage signal
        """

        # Create new lists for the channel-specific header fields.
        #
        new_chan_labels      = []
        new_chan_trans_type  = []
        new_chan_phys_dim    = []
        new_chan_prefilt     = []
        new_chan_phys_min    = []
        new_chan_phys_max    = []
        new_chan_dig_min     = []
        new_chan_dig_max     = []
        new_chan_rec_size    = []

        # Loop over each montage channel in monsig.
        #
        for mont_label, signal in monsig.items():
            new_chan_labels.append(mont_label)

            # find reference index label if exists
            #
            ref_index = -1
            for raw_chan in hdr[EDF_CHAN_LABELS]:

                # Use extract_actual to get the candidate channel name.
                #
                candidate = \
                    raw_chan.replace(nft.DELIM_DASH, nft.DELIM_SPACE).split()

                # If extraction fails, skip to the next channel.
                #
                if candidate is None:
                    continue

                # check if the montage name is in the candidate
                #
                if mont_label.split(nft.DELIM_DASH)[0] in candidate:

                    # if they are equal set ref_index to the raw channel
                    # index
                    #
                    ref_index = hdr[EDF_CHAN_LABELS].index(raw_chan)

            # if the reference index was not found print and error
            #
            if ref_index == -1:
                print("Error: %s (line: %s) %s: %s (%s)" %
                      (__FILE__, ndt.__LINE__, ndt.__NAME__,
                       " montage channel names not found in raw channel list".
                       mont_label))
                sys.exit(os.EX_SOFTWARE)

            # Copy reference header information.
            #
            new_chan_trans_type.append(hdr['chan_trans_type'][ref_index])
            new_chan_phys_dim.append(hdr['chan_phys_dim'][ref_index])
            new_chan_prefilt.append(hdr['chan_prefilt'][ref_index])

            # append ref_index's value into montage header
            #
            new_chan_phys_min.append(hdr['chan_phys_min'][ref_index])
            new_chan_phys_max.append(hdr['chan_phys_max'][ref_index])

            # append ref_index's value into montage header
            #
            new_chan_dig_min.append(hdr['chan_dig_min'][ref_index])
            new_chan_dig_max.append(hdr['chan_dig_max'][ref_index])
            new_chan_rec_size.append(hdr['chan_rec_size'][ref_index])

        # Create a copy of the header and update channel-specific fields.
        #
        updated_hdr = hdr.copy()
        updated_hdr['chan_labels']      = new_chan_labels
        updated_hdr['chan_trans_type']  = new_chan_trans_type
        updated_hdr['chan_phys_dim']    = new_chan_phys_dim
        updated_hdr['chan_prefilt']     = new_chan_prefilt
        updated_hdr['chan_phys_min']    = new_chan_phys_min
        updated_hdr['chan_phys_max']    = new_chan_phys_max
        updated_hdr['chan_dig_min']     = new_chan_dig_min
        updated_hdr['chan_dig_max']     = new_chan_dig_max
        updated_hdr['chan_rec_size']    = new_chan_rec_size

        # Update the overall header fields for number of channels and header size.
        #
        num_new_channels = len(new_chan_labels)
        updated_hdr['ghdi_nsig_rec'] = num_new_channels
        updated_hdr['ghdi_hsize']    = EDF_BSIZE * num_new_channels + EDF_BSIZE
        updated_hdr['num_channel_signal'] = num_new_channels

        # exit gracefully
        #  return montage header
        #
        return updated_hdr
    #
    # end of method

    def resample(self, ofile, ifile, osf, mfile, scale = False):
        """
        method: resample

        arguments:
         ofile: output filename
         ifile: input filename
         osf: output sample frequency in Hz
         mfile: a montage filename
         scale: a boolean value to indicate whether we want to preform
          phys min/max scalling

        return: boolean value indicating status

        description:
         This method opens the files, extracts an Edf signal, and sends
         it to a resampling method.
         """

        # display debug information
        #
        if self.dbgl_d > ndt.NONE:
            print("%s (line: %s) %s::%s: resampling signal" %
                  (__FILE__, ndt.__LINE__, self.__CLASS_NAME__, ndt.__NAME__))

        # create a montage tool instance
        #
        mont_tool = nmt.Montage()

        # load the montage
        #
        mont_dict = mont_tool.load(mfile)

        # get the signal and header data
        #
        hdr, sig = self.read_edf(ifile, True, True)

        # ensure the edf was correctly loaded
        #
        if hdr is None:
            print("Error: %s (line: %s) %s::%s: error opening file (%s)" %
                  (__FILE__, ndt.__LINE__, self.__CLASS_NAME__,
                   ndt.__NAME__, ifile))
            return False

        # apply the montage to the signal data
        #
        monsig = mont_tool.apply(sig, mont_dict)

        # update montage header information to match montage signal
        # data
        #
        monhdr = self.update_mont_hdr(hdr, monsig, mont_dict, scale)


        # step one: resample the channels of interest
        #
        osig = self.resample_signal(monsig, osf, monhdr)

        # ensure that osig is not None (i.e. that resampling failed)
        #
        if osig is None:
            print("Error: %s (line: %s) %s::%s: error resampling (osf = %f)" %
                  (__FILE__, ndt.__LINE__, self.__CLASS_NAME__,
                   ndt.__NAME__, osf))
            return False

        # step two: update the new header to match the resampled signal data
        #
        # loop through each channel in osig to make needed updates
        # to edf header signal info
        #
        for channel in osig:

            # fetch the channel index in the physical maximum/minimum
            # and record size array
            #
            chan_index = monhdr[EDF_CHAN_LABELS].index(channel)

            # if the scale boolean was set to true scale phys min/max
            #
            if scale:

                # find the maximum/minimum of the resampled channel
                #
                phys_max = osig[channel].max()
                phys_min = osig[channel].min()

                phys_max_mag = max(np.abs(phys_max), np.abs(phys_min))

                # set the new minimum physical value
                #
                monhdr[EDF_CHAN_PHYS_MIN][chan_index] = float(-1 * phys_max_mag)

                # set the new maximum physical value
                #
                monhdr[EDF_CHAN_PHYS_MAX][chan_index] = float(phys_max_mag)

            # set the new channel record size
            #
            monhdr[EDF_CHAN_REC_SIZE][chan_index] = int(osf)

        monhdr[EDF_SAMPLE_FREQUENCY] = float(osf)

        # fetch the total number of samples of the first resampled channel
        # note: all resampled channels have the same new
        #  total number of samples
        #
        new_total_samples = len(list(osig.values())[0])

        # step three: update the record duration to one second
        # and number of records accordingly
        #
        # set the record duration for each record to one second
        #
        monhdr[EDF_GHDI_DUR_REC] = float(1.0)

        # Calculate new total recording duration
        #
        new_total_duration = float(new_total_samples) / osf

        # Calculate the new number of records
        #
        new_ghdi_num_recs = math.ceil(new_total_duration / monhdr[EDF_GHDI_DUR_REC])

        # Update the header with the new number of records
        #
        monhdr[EDF_GHDI_NUM_RECS] = new_ghdi_num_recs

        # step five: pad channels if the number of records was updated
        # (i.e. the record duration was something other than one)
        #
        # iterate over all channels
        #
        for chan_index, channel in enumerate(osig):

            # fetch the current length of the channel
            #
            current_length = len(osig[channel])

            # find the new length standard (due to changing ghdi_num_recs)
            #
            new_length = new_ghdi_num_recs * monhdr[EDF_CHAN_REC_SIZE][chan_index]

            # if the current length does not equal to the new length
            # append zero pad the matrix to the new length
            #
            if current_length != new_length:

                # create a numpy array of zeros
                #
                padding = np.zeros(new_length - current_length)

                # pad end of channel with zeros
                #
                osig[channel] = np.append(osig[channel], padding)

        # step six: convert osig from a physical dictionary
        # to a digital dictionary
        #
        if self.phys_to_dig(osig, monhdr) == False:
            print("Error: %s (line: %s) %s::%s: conversion error (%s, %s)" %
                  (__FILE__, ndt.__LINE__, self.__CLASS_NAME__,
                   ndt.__NAME__, osig, monhdr))
            return False


        # step seven: write to the updated header and resampled signal
        # to an edf file
        #
        if self.write_edf(ofile, monhdr, osig) == False:
            print("Error: %s (line: %s) %s::%s: error writing (%s)" %
                  (__FILE__, ndt.__LINE__, self.__CLASS_NAME__,
                   ndt.__NAME__, osf))
            return False

        # exit gracefully
        #
        return True
    #
    # end of method

    def phys_to_dig(self, phys_sig_dict, header):
        """
        method: phys_to_dig

        arguments:
         phys_sig_dict: dictionary containing the physical signals
         header: an edf header

        return: boolean value indicating status

        description:
         this method converts the physical signals found in the signal
         dictionary to their digital equivalents.

        Note:
         this method directly changes phys_sig_dict to save space
        """

        # display debug information
        #
        if self.dbgl_d > ndt.NONE:
            print("%s (line: %s) %s::%s: converting from physical to digital" %
                  (__FILE__, ndt.__LINE__, self.__CLASS_NAME__, ndt.__NAME__))

        # create a set of required keys to check that all keys are
        # present
        #
        required_keys = \
            {EDF_CHAN_LABELS, EDF_CHAN_DIG_MIN, EDF_CHAN_DIG_MAX,
             EDF_CHAN_PHYS_MAX, EDF_CHAN_PHYS_MIN}

        # Check if all needed header items are present
        #
        missing_keys = required_keys - header.keys()
        if missing_keys:
            print("Error: %s (line: %s) %s::%s: missing header info (%s)" %
              (__FILE__, ndt.__LINE__, self.__CLASS_NAME__,
               ndt.__NAME__, missing_keys))
            return False

        # fetch all needed header information
        #
        chan_labels = header[EDF_CHAN_LABELS]
        dig_min = header[EDF_CHAN_DIG_MIN]
        dig_max = header[EDF_CHAN_DIG_MAX]
        phys_max = header[EDF_CHAN_PHYS_MAX]
        phys_min = header[EDF_CHAN_PHYS_MIN]

        # instantiate a reference pointer to the signal dictionary
        # with a different name for clarity
        #
        dig_sig_dict = phys_sig_dict

        # Iterate over all channels in the signal dictionary
        #
        for channel in phys_sig_dict:

            # Fetch the corresponding channel index to obtain
            # correct min/max values for each channel
            #
            ch_index = chan_labels.index(channel)

            # calculate the digital range
            #
            dig_range = dig_max[ch_index] - dig_min[ch_index]

            # calculate the physical range
            #
            phys_range = phys_max[ch_index] - phys_min[ch_index]

            # calculate the physical values minus the physical minimums
            #
            val_pmin = phys_sig_dict[channel] - phys_min[ch_index]

            # calculate the new digital values
            #
            dig_values = (val_pmin * dig_range / phys_range) + dig_min[ch_index]

            # Round and convert to integer
            #
            dig_sig_dict[channel] = np.round(dig_values)

        # exit gracefully
        #
        return True
    #
    # end of method

    def dig_to_phys(self, dig_sig_dict, header):
        """
        method: dig_to_phys

        arguments:
         dig_sig_dict: dictionary containing the digital signals
         header: an edf header

        return: boolean value indicating status

        description:
         this method converts the digital signals found in the signal
         dictionary to their physical equivalents.

        Note:
         this method directly changes dig_sig_dict to save space
        """

        # display debug information
        #
        if self.dbgl_d > ndt.BRIEF:
            print("%s (line: %s) %s::%s: converting from digital to physical" %
                  (__FILE__, ndt.__LINE__, self.__CLASS_NAME__, ndt.__NAME__))

        # create a set of required keys to check that all keys are
        # present
        #
        required_keys = \
            {EDF_CHAN_LABELS, EDF_CHAN_DIG_MIN, EDF_CHAN_DIG_MAX,
             EDF_CHAN_PHYS_MAX, EDF_CHAN_PHYS_MIN}

        # Check if all needed header items are present
        #
        missing_keys = required_keys - header.keys()
        if missing_keys:
            print("Error: %s (line: %s) %s::%s: missing header info (%s)" %
                  (__FILE__, ndt.__LINE__, self.__CLASS_NAME__,
                   ndt.__NAME__, missing_keys))
            return False

        # fetch all needed header information
        #
        chan_labels = header[EDF_CHAN_LABELS]
        dig_min = header[EDF_CHAN_DIG_MIN]
        dig_max = header[EDF_CHAN_DIG_MAX]
        phys_max = header[EDF_CHAN_PHYS_MAX]
        phys_min = header[EDF_CHAN_PHYS_MIN]

        # instantiate a reference pointer to the dictionary
        # with a different name for clarity
        #
        phys_sig_dict = dig_sig_dict

        # Iterate over all channels in the signal dictionary
        #
        for channel in dig_sig_dict:

            # Fetch the corresponding channel index
            # to obtain the correct min/max values
            # for each channel
            #
            ch_index = chan_labels.index(channel)

            # calculate the digital range
            #
            dig_range = dig_max[ch_index] - dig_min[ch_index]

            # calculate the physical range
            #
            phys_range = phys_max[ch_index] - phys_min[ch_index]

            # calculate the digital values minus the digital minimums
            #
            val_dmin = dig_sig_dict[channel] - dig_min[ch_index]

            # Calculate new channel physical values
            #
            phys_values = \
                (val_dmin * phys_range / dig_range) + phys_min[ch_index]

            # Round and convert to integer and reassign
            # to phys_sig_dict (in memory same as dig_sig_dict)
            #
            phys_sig_dict[channel] = phys_values

        # exit gracefully
        #
        return True
    #
    # end of method

    def resample_signal(self, isig, osf, hdr, forder = DEF_EDFR_FORDER):
        """
        method: resample_signal

        arguments:
         isig: input signal dictionary
         osf: output sample frequency in Hz
         hdr: the edf's header data
         forder: the filtering order

        return:
         the resampled signal as a dictionary

        description:
         This method resamples a signal.
        """

        # display debug information
        #
        if self.dbgl_d > ndt.NONE:
            print("%s (line: %s) %s::%s: resampling a signal buffer" %
                  (__FILE__, ndt.__LINE__, self.__CLASS_NAME__, ndt.__NAME__))

        # fetch the record duration for determining isf in loop
        #
        rec_dur = hdr[EDF_GHDI_DUR_REC]

        # resample channel data by first up sampling and then
        # decimating
        #
        for channel in isig:

            # fetch the channels corresponding index
            #
            chan_idx = hdr[EDF_CHAN_LABELS].index(channel)

            # find the channels corresponding record size
            #
            chan_rec_size = hdr[EDF_CHAN_REC_SIZE][chan_idx]

            # calculate the channels corresponding sample
            # frequency (isf)
            #
            isf = float(chan_rec_size) / float(rec_dur)

            # find a ratio of integers that converts isf to osf
            #
            lcm = int(math.lcm(int(isf), int(osf)))
            up_rate = int(lcm/int(isf))
            down_rate = int(lcm/int(osf))

            # up sample using a polymorphic resampling
            #
            if up_rate > 1:

                # up sample the channel signal data
                #
                isig[channel] = resample_poly(
                    isig[channel], up_rate, 1,
                    padtype = 'line'
                )

            # if the down rate is greater than one decimate
            #
            if down_rate > 1:

                # down sample the channel signal data
                #
                isig[channel] = decimate(
                    isig[channel],
                    q = down_rate,
                    n = forder,
                    ftype = DEF_EDFR_FTYPE
                )

        # exit gracefully
        #  return isig
        #
        return isig
    #
    # end of method

    #--------------------------------------------------------------------------
    #
    # miscellaneous methods are listed here
    #
    #--------------------------------------------------------------------------
    def cleanup(self):
        """
        method: cleanup

        arguments:
         none

        return:
         a boolean value indicating status

        description:
         This method cleans up memory.
        """

        # display debug information
        #
        if self.dbgl_d > ndt.BRIEF:
            print("%s (line: %s) %s::%s: starting clean up of memory" %
                  (__FILE__, ndt.__LINE__, Edf.__CLASS_NAME__, ndt.__NAME__))

        # clear the header structure
        #
        if self.h_d != None:
            self.h_d = {}

        # display debug information
        #
        if self.dbgl_d > ndt.BRIEF:
            print("%s (line: %s) %s::%s: done cleaning up memory" %
                  (__FILE__, ndt.__LINE__, Edf.__CLASS_NAME__, ndt.__NAME__))

        # exit gracefully
        #
        return True

    def channels_data(self, edf_file, channels_order):
        """
        method: channels_data

        arguments:
         channels_order: a list of channel labels to be extracted. the channels
         will be extracted in this order.

        return:
         max_samp_rate: the sample rate of signals
         sigbufs: a 2D numpy matrix that contains the extracted signals
         as rows of the matrix

        description:
         This method extracts a set of channels from an Edf file. Channels_order
         is a list of channels to be extracted from edf file. We return
         the maximum sample rate of the channels and a numpy matrix containing
         the signal data.
        """

        # read the EDF file
        #
        header, signal = self.read_edf(edf_file, False)

        # find the appropriate sample rate
        #
        samp_rates = np.zeros((len(channels_order), ))
        num_samples = samp_rates.copy()
        for ch_counter, channel in enumerate(channels_order):

            # find the specified channel in all the channels in edf file.
            # if nothing found, something is wrong. stop the whole process to
            # find the reason.
            #
            found = False

            # loop through the return signal data where signal is an
            # OrderedDictionary:
            # Ex: {'EEG FP1-LE' : array([-118., ... , -88. ])
            #
            # If channel exist within the EDF file, we get its sample frequency
            # along its sample number
            #
            for sig_counter, signal_label in enumerate(signal):
                if (channel in signal_label):
                    samp_rates[ch_counter] = \
                        self.get_sample_frequency(sig_counter)
                    num_samples[ch_counter] = self.get_num_samples(sig_counter)
                    found = True
                    break

            # if we reach this, it means that we couldn't find the channel
            # in the EDF file
            #
            assert found, \
                (f"Error: {__FILE__} (line: {ndt.__LINE__}) \
                {ndt.__NAME__}: Channel {channel} wasn't found \
                in {edf_file}")

        max_samp_rate = int(samp_rates.max())
        nSamples = int(num_samples.max())

        # now sample rate and number of samples are found,
        # just fill the matrix.
        #
        sigbufs = np.zeros((len(channels_order), nSamples))
        for ch_counter, channel in enumerate(channels_order):

            # Find the index of channel
            #
            for sig_counter, signal_label in enumerate(signal):
                if (channel in signal_label):
                    step = int(nSamples / self.get_num_samples(ch_counter))
                    sigbufs[ch_counter, 0::step] = signal[channel]

        # exit gracefully
        #
        return max_samp_rate, sigbufs
    #
    # end of method

#
# end of Edf

# class: ApplyMontage
#
class ApplyMontage:
    """
    class: ApplyMontage

    arguments:
     none

    description:
     This is a simple class meant to compute the montage for edf signals.
    """

    #--------------------------------------------------------------------------
    #
    # constructors are listed here
    #
    #--------------------------------------------------------------------------
    def __init__(self, channel_order, montage_order):
        """
        method: constructor

        arguments:
         channel_order: the channels that occur in the signal
         montage_order: the montage to apply to the signal

        return:
         none

        description:
         This simple method initializes the class arguments
        """
        # set the class name
        #
        ApplyMontage.__CLASS_NAME__ = self.__class__.__name__

        # set the necessary values
        #
        self.ch_order = channel_order
        self.mon_order = montage_order

        # exit gracefully
        #
        return None

    #
    # end of method

    #--------------------------------------------------------------------------
    #
    # processing methods are listed here
    #
    #--------------------------------------------------------------------------

    # method: ApplyMontage::apply_montage
    #
    # arguments:
    #  sig: signal to apply the montage as a dictionary with channel names as
    #   keys and a list of data as the values:
    #   sig = {'channel1name': [data], 'channel2name': [data] ... }
    #
    # returns: the signal after applying the montage in the same form as the
    #  input signal: {'montage1name': [data], 'montage2name': [data] ... }
    #
    # This method is the main method of this class and will compute the montage
    #
    def apply_montage(self, sig):
        """
        method: apply_montage

        arguments:
         sig: signal to apply the montage as a dictionary with channel names as
         keys and a list of data as the values:
         sig = {'channel1name': [data], 'channel2name': [data] ... }

        return: the signal after applying the montage in the same form as the
         input signal: {'montage1name': [data], 'montage2name': [data] ...

        description:
         This method is the main method of this class and computes the montage.
        """
        # make sure mon_order exists
        #
        if self.mon_order is None:
            print("Error: %s (line: %s) %s::%s: montage order is none" %
                   (__FILE__, ndt.__LINE__, ApplyMontage.__CLASS_NAME__,
                   ndt.__NAME__))
            sys.exit(0)

        # set dictionary to hold montage signals
        #
        monsig = {}

        # iterate through each montage
        #
        for mcounter, montage in enumerate(self.mon_order):

            # set the raw channels needed and reset index values
            #
            rawch1, rawch2 = montage.split(nft.DELIM_DASH)
            index1, index2 = -1, -1
            monsig[montage] = []

            # go through all the channels
            #
            for ch_counter, channel in enumerate(self.ch_order):

                # set the indexes of the needed channels
                #
                if rawch1 in channel:
                    index1 = ch_counter
                if rawch2 in channel:
                    index2 = ch_counter

            # if the channels aren't found print an error message
            #
            assert not(index1 == -1 or index2 == -1 or index1 == index2),\
                (f"Error: {__FILE__} (line: {ndt.__LINE__}) \
                   {ndt.__NAME__}: channels({rawch1},{rawch2}) \
                   hasn't been found or the indices are incorrect")

            # apply the montage to all signal values in buff
            #
            for count in range(len(sig[channel])):
                monsig[montage].append(sig[self.ch_order[index1]][count] -
                                       sig[self.ch_order[index2]][count])

        # exit gracefully
        #
        return monsig
    #
    # end of method

#
# end of ApplyMontage

#
# end of file
