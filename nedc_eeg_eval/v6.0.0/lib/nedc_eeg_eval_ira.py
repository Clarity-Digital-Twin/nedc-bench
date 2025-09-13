#!/usr/bin/env python

# file: $NEDC_NFC/class/python/nedc_eeg_eval_tools/nedc_eeg_eval_ira.py
#
# revision history:
#
# 20240716 (JP): refactored after the rewrite of ann_tools
# 20230623 (AB): refactored code to use new comment style
# 20220514 (JP): refactored the code to use the new annotation tools library
# 20200813 (LV): updated for rehaul of nedc_eval_eeg
# 20180219 (VS): bug fixes, true negatives args are correctly passed
# 20170815 (JP): added another metric: prevalence
# 20170812 (JP): changed the divide by zero checks
# 20170716 (JP): upgraded to using the new annotation tools
# 20170702 (JP): added summary scoring; revamped the derived metrics
# 20170625 (JP): rewrote it based on our new specs
#
# usage:
#  import nedc_eeg_eval_ira as nira
#
# This file implements NEDC's inter-rater agreement scoring algorithm. This
# code essentially runs epoch-based scoring at a fine time resolution,
# and then evaluates the resulting confusion matrix using the Kappa
# statistic.
#------------------------------------------------------------------------------

# import required system modules
#
import os
import sys
import math

# import required NEDC modules
#
import nedc_debug_tools as ndt
import nedc_eeg_eval_common as nec
import nedc_file_tools as nft

#------------------------------------------------------------------------------
#
# define important constants
#
#------------------------------------------------------------------------------

# set the filename using basename
#
__FILE__ = os.path.basename(__file__)

# define paramter file constants
#
NEDC_IRA = "NEDC_IRA"

#------------------------------------------------------------------------------
#
# functions are listed here
#
#------------------------------------------------------------------------------

# declare a global debug object so we can use it in functions
#
dbgl = ndt.Dbgl()

def run(events_ref, events_hyp, mapping, nedc_ira, odir, fp):
    """
    function: run
    
    arguments:
     events_ref: a dictionary containining all ref events indexed by filenames
     events_hyp: a dictionary containining all hyp events indexed by filenames
     map: a mapping used to collapse classes during scoring
     nedc_ira: the NEDC IRA scoring algorithm parameters
     odir: the output directory
     fp: a pointer to the output summary file
 
    return: 
     a boolean value indicating status

    description: 
     This method runs the NEDC IRA scoring algorithm by:
     (1) loading the annotations
     (2) scoring them using an epoch-based approach
     (3) evaluating the resulting confusion matrix
     (4) displaying the results
    """
       
    # display an informational message
    #
    if dbgl > ndt.BRIEF:
        print("%s (line: %s) %s: running epoch scoring" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__))

    # define local variables
    #
    status = True
    nira = NedcIra(nedc_ira)

    # load the reference and hyp file lists into memory
    #
    num_files_ref = len(events_ref)
    num_files_hyp = len(events_hyp)

    if num_files_ref < 1 or num_files_hyp < 1 or \
       num_files_ref != num_files_hyp:
        print("Error: %s (line: %s):%s: file list error (%s %s)" %
              (__FILE__, ndt.__LINE__,ndt.__NAME__,
               events_ref, events_hyp))
        return False

    # run ira scoring
    #
    if dbgl > ndt.BRIEF:
        print("%s (line: %s) %s: scoring files" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__))

    status = nira.init_score(mapping)
    status = nira.score(events_ref, events_hyp, mapping)
    if status == False:
        print("Error: %s (line: %s):%s: error during scoring" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__))
        return False

    # compute agreement
    #
    if dbgl > ndt.BRIEF:
        print("%s (line: %s) %s: computing agreement" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__))

    cnf = nira.compute_agreement()
    if status == False:
        print("Error: %s (line: %s):%s: error computing agreement" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__))
        return False

    # collect information for scoring and display
    #
    if dbgl > ndt.BRIEF:
        print("%s (line: %s) %s: displaying results" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__))

    header, tbl = nec.create_table(cnf)
    status = nira.display_results("NEDC IRA Confusion Matrix",
                                  header, tbl, fp)
    if status == False:
        print("Error: %s (line: %s):%s: error displaying results" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__))
        return False

    # exit gracefully
    #
    return status
#
# end of function

#------------------------------------------------------------------------------
#
# classes are listed here
#
#------------------------------------------------------------------------------

class NedcIra():
    """
    Class: NedcIra
    
    arguments:
     none

    description: 
     This class contains methods that execute the ira-based scoring algorithm.
    """

    #--------------------------------------------------------------------------
    #
    # static data declarations
    #
    #--------------------------------------------------------------------------

    # define static variables for debug and verbosity
    #
    dbgl_d = ndt.Dbgl()
    vrbl_d = ndt.Vrbl()

    def __init__(self, params):
        """
        method: constructor
        
        arguments:
         none

        return: 
         none

        description: 
         none
        """
 
        # create class data
        #
        NedcIra.__CLASS_NAME__ = self.__class__.__name__
        
        # decode the parameters passed from the parameter file
        #
        self.epoch_dur_d = float(params['epoch_duration'])

        # declare a variable to hold a permuted map
        #
        self.pmap_d = {}

        # declare a duration parameter used to calculate the false alarm rate:
        #  we need to know the total duration of the data in secs
        #
        self.total_dur_d = float(0)

        # declare parameters to compute agreeement
        #
        self.sub_d = {}

        # additional derived data:
        #  we use class data to store a number of statistical measures
        #
        self.kappa_d = {}
        self.mkappa_d = float(0)

    #
    # end of method

    def init_score(self, score_map):
        """
        method: init_score
        
        arguments:
         score_map: a scoring map

        return: 
         a boolean value indicating status

        description: 
         This method initializes parameters used to track errors.
         We use dictionaries that are initialized in the order
         labels appear in the scoring map.
        """
 
        # display informational message
        #
        if self.dbgl_d > ndt.BRIEF:
            print("%s (line: %s) %s::%s: initializing score" %
                  (__FILE__, ndt.__LINE__, NedcIra.__CLASS_NAME__,
                   ndt.__NAME__))
            
        # initialize global counters
        #
        self.total_dur_d = float(0)

        # initialiaze parameters to compute agreement
        #  these are declared as dictionaries organized
        #  in the order of the scoring map
        #
        self.sub_d = {}
        self.kappa_d = {}
        self.mkappa_d = float(0)

        # establish the order of these dictionaries in terms of
        # the scoring map.
        #
        for key in score_map:
            self.sub_d[key] = {}
            for key2 in score_map:
                self.sub_d[key][key2] = int(0)

            self.kappa_d[key] = float(0)

        # permute the map: we need this in various places
        #
        self.pmap_d = nft.permute_map(score_map)

        # exit gracefully
        # 
        return True
    #
    # end of method

    def score(self, all_events_ref, all_events_hyp, score_map):
        """
        method: score
        
        arguments:
         all_events_ref: a dictionary of all reference events
         all_events_hyp: a dictionary of all hypothesis events
         score_map: a scoring map

        return: 
         a boolean value indicating status

        description: 
         This method computes a confusion matrix.
        """
 
        # display informational message
        #
        if self.dbgl_d > ndt.BRIEF:
            print("%s (line: %s) %s::%s: scoring files" %
                  (__FILE__, ndt.__LINE__, NedcIra.__CLASS_NAME__,
                   ndt.__NAME__))
            
        # declare local variables
        #
        status = True

        # loop over all files
        #
        i = int(0)
        for key_ref, key_hyp in zip(all_events_ref, all_events_hyp):

            events_ref = all_events_ref[key_ref]
            if events_ref == None:
                print("Error: %s (line: %s) %s: %s (%s)" %
                      (__FILE__, ndt.__LINE__, ndt.__NAME__,
                       "error getting annotations", fname))
                return False

            # get the hyp eventss                                            
            #                                                               
            events_hyp = all_events_hyp[key_hyp]
            if events_hyp == None:
                print("Error: %s (line: %s) %s: %s (%s)" %
                      (__FILE__, ndt.__LINE__, ndt.__NAME__,
                       "error getting annotations", fname))
                return False

            # update the total duration
            #
            self.total_dur_d += events_ref[-1][1]

            # map the annotations before scoring:
            #  only extract the first label and convert to a pure list
            #
            ann_ref = []
            for event in events_ref:
                key = next(iter(event[2]))
                ann_ref.append([event[0], event[1], \
                                self.pmap_d[key], event[2][key]])
                
            ann_hyp = []
            for event in events_hyp:
                key = next(iter(event[2]))
                ann_hyp.append([event[0], event[1], \
                                self.pmap_d[key], event[2][key]])

            # add this to the confusion matrix
            #
            status = self.compute(ann_ref, ann_hyp, self.epoch_dur_d)
            if status == False:
                print("Error: %s (line: %s) %s::%s: %s (%s)" %
                      (__FILE__, ndt.__LINE__, NedcIra.__CLASS_NAME__,
                       ndt.__NAME__, "error computing confusion matrix",
                       fname))
                return False

        # exit gracefully
        # 
        return True
    #
    # end of method

    def compute(self, ref, hyp, dur):
        """
        method: compute
        
        arguments:
         ref: reference annotation
         hyp: hypothesis annotation
         dur: the duration of time used to sample the annotations
        
        return:
         refo: the output aligned ref string
         hypo: the output aligned hyp string

        description: 
         this method iterates over the reference annotation, sampling it at
         times spaced by dur secs, and compares labels to the corresponding
         label in the hypothesis.
        """
 
        # check to make sure the annotations match:
        #  since these are floating point values for times, we
        #  do a simple sanity check to make sure the end times
        #  are close (within 1 microsecond)
        #
        if round(ref[-1][1], ndt.MIN_PRECISION) != \
           round(hyp[-1][1], ndt.MIN_PRECISION):
            return False

        # loop over the reference annotation starting at the middle
        # of the first interval.
        #
        dur_by_2 = dur / float(2.0)
        curr_time = dur / float(2.0)
        start_time = float(0)
        stop_time = ref[-1][1]
        i = 0

        while curr_time <= stop_time:

            # convert time to an index
            #
            j = self.time_to_index(curr_time, ref)
            k = self.time_to_index(curr_time, hyp)

            # increment the substitution matrix
            #
            self.sub_d[ref[j][2]][hyp[k][2]] += int(1)

            # increment time:
            #  do this using an integer counter to avoid roundoff error
            #
            i += 1
            curr_time = dur_by_2 + i * dur

        # exit gracefully
        #
        return True
    #
    # end of method

    def time_to_index(self, val, ann):
        """
        method: time_to_index
        
        arguments:
         val: a floating point value of time in secs
         ann: a list of annotation events

        return: 
         an integer index

        description: 
         This method finds the annotation corresponding to a value of time.
        """
 
        # loop over the annotation
        #
        counter = 0
        for entry in ann:
            if (val >= entry[0]) & (val <= entry[1]):
                return counter
            else:
                counter += 1

        # exit ungracefully:
        #  no match was found, which is a problem
        #
        return int(-1)
    #
    # end of method

    def compute_agreement(self):
        """
        method: compute_agreement
        
        arguments:
         none

        return: 
         cnf: a confusion matrix

        description: 
         This method computes Cohen's Kappa statistic for the confusion matrix.
         It iterates over each label and computes the label against all other
         classes. This is a classic Kappa statistic calculation described here:
        
         https://en.wikipedia.org/wiki/Cohen%27s_kappa#Example
        
         Other relevant references include:
        
         https://en.wikipedia.org/wiki/Confusion_matrix
         https://en.wikipedia.org/wiki/Precision_and_recall
         http://www.dataschool.io/simple-guide-to-confusion-matrix-terminology/
        
         Then it computes a Kappa statistic for the entire matrix following the
         procedure described here:
        
         https://www.harrisgeospatial.com/docs/CalculatingConfusionMatrices.html
        """
 
        # display informational message
        #
        if self.dbgl_d > ndt.BRIEF:
            print("%s (line: %s) %s::%s: computing Cohen's Kappa statistic" %
                  (__FILE__, ndt.__LINE__, NedcIra.__CLASS_NAME__,
                   ndt.__NAME__))
            
        # loop over all labels:
        #  note that the confusion matrix is square by definition,
        #  so loop counters can be interchanged.
        #
        for label in self.sub_d:

            # compute the elements of the "yes/no" matrix
            #
            a = float(self.sub_d[label][label])
            b = float(0)
            c = float(0)
            d = float(0)
            for label2 in self.sub_d[label]:
                if label != label2:
                    b += float(self.sub_d[label][label2])
                    c += float(self.sub_d[label2][label])
                    d += float(self.sub_d[label2][label2])

            # compute the intermediate probabilities
            #
            denom = a + b + c + d
            if denom == float(0):
                print("Error: %s (line: %s) %s::%s: %s (%s)" %
                      (__FILE__, ndt.__LINE__, NedcIra.__CLASS_NAME__,
                       ndt.__NAME__,
                       "error computing intermediate probabilities", label))
                p_o = float(0)
                p_yes = float(0)
                p_no = float(0)
                p_e = float(0)
            else:
                p_o   = (a + d) / (a + b + c + d)
                p_yes = (a + b) / (a + b + c + d) * (a + c) / (a + b + c + d)
                p_no  = (c + d) / (a + b + c + d) * (b + d) / (a + b + c + d)
                p_e   = p_yes + p_no

            # compute the final statistic
            #
            num = float(p_o - p_e)
            denom = float(1) - p_e
            if (denom == float(0)) and (num != float(0)):
                print("Error: %s (line: %s) %s::%s: %s (%s)" %
                      (__FILE__, ndt.__LINE__, NedcIra.__CLASS_NAME__,
                       ndt.__NAME__,
                       "error computing kappa statistic", label))
                self.kappa_d[label] = 0
            elif denom == float(0):
                self.kappa_d[label] = float(1.0)
            else:
                self.kappa_d[label] = float((p_o - p_e) / (1 - p_e))

        # compute a Kappa statistic over the entire matrix:
        #  (1) compute the sum of the rows and columns
        #  (2) sum of the diagonal
        #  (3) sum of the matrix
        #  (4) sum of the product of the rows and colums sums
        #
        sum_rows = {}
        for label1 in self.sub_d:
            sum_rows[label1] = int(0)
        sum_cols = {}
        flbl = next(iter(self.sub_d))
        for label1 in self.sub_d[flbl]:
            sum_cols[label1] = int(0)

        sum_M = int(0)
        for label1 in self.sub_d:
            sum_M += self.sub_d[label1][label1]
            for label2 in self.sub_d[label1]:
                sum_rows[label1] += self.sub_d[label1][label2]
                sum_cols[label2] += self.sub_d[label1][label2]

        sum_N = int(0)
        sum_gc = int(0)
        for label1 in self.sub_d:
            sum_N += sum_rows[label1]
            sum_gc += sum_rows[label1] * sum_cols[label1]

        # (5) compute multi-class Kappa statistic
        #
        num = sum_N * sum_M - sum_gc
        denom = sum_N * sum_N - sum_gc
        if (denom == int(0)) and (num == int(0)):
            self.mkappa_d = float(1)
        elif denom == int(0):
            print("Error: %s (line: %s) %s::%s: %s (%s %f %f)" %
                  (__FILE__, ndt.__LINE__, NedcIra.__CLASS_NAME__,
                   ndt.__NAME__,
                   "error computing the multi-class kappa statistic",
                   label, num, denom))
            self.mkappa_d = 0
        else:
            self.mkappa_d = float(num) / float(denom)

        # exit gracefully
        #
        return self.sub_d
    #
    # end of method

    def display_results(self, title, headers, tbl, fp):
        """
        method: display_results
        
        arguments:
         title: the title of the confusion table
         headers: the headers associated with the columns of the matrix
         tbl: the table to be printed
         fp: output file pointer

        return: 
         a boolean value indicating status

        description: 
         This method displays all the results in output report.
        """
 
        # display informational message
        #
        if self.dbgl_d > ndt.BRIEF:
            print("%s (line: %s) %s::%s: displaying results to output file" %
                  (__FILE__, ndt.__LINE__, NedcIra.__CLASS_NAME__,
                   ndt.__NAME__))
            
        # declare a format length:
        #  we use this variable to make sure the output lines up.
        #  it is the length of the fixed portion of the per label
        #  output format ("Label: " + "   " + "Kappa" = 15 characters
        #
        fmt_len = int(15)

        # print complete table in output file
        #
        nec.print_table(title, headers, tbl,
                                "%10s", "%12.2f", "%6.2f", fp)
        fp.write(nft.DELIM_NEWLINE)

        # write per label header
        #
        fp.write(("Per Label Results:" + nft.DELIM_NEWLINE).upper())

        # per label results: loop over all classes
        #
        max_lab_len = int(max(map(len, self.kappa_d)))
        for key in self.kappa_d:
            fp.write(" Label: %*s   Kappa: %12.4f" % \
                       (max_lab_len, key, self.kappa_d[key]) +
                     nft.DELIM_NEWLINE)
        fp.write(nft.DELIM_NEWLINE)

        # write the multi-class Kappa statistic
        #
        tot_len = max_lab_len + fmt_len
        fp.write(("Summary:" + nft.DELIM_NEWLINE).upper())
        fp.write(" %*s: %12.4f" % \
                   (tot_len, "Multi-Class Kappa", self.mkappa_d) +
                 nft.DELIM_NEWLINE)
        fp.write(nft.DELIM_NEWLINE)

        # exit gracefully
        #
        return True
    #
    # end of method

# end of file
#
