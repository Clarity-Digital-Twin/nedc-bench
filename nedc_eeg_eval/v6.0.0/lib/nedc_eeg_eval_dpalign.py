#!/usr/bin/env python

# file: $NEDC_NFC/class/python/nedc_eeg_eval_tools/nedc_eeg_eval_dpalign.py
#
# revision history:
#
# 20240716 (JP): refactored after the rewrite of ann_tools
# 20230623 (AB): refactored code to new comment format
# 20220514 (JP): refactored the code to use the new annotation tools library
# 20170815 (JP): added another metric: prevalence
# 20170812 (JP): changed the divide by zero checks
# 20170716 (JP): upgraded to using the new annotation tools
# 20170702 (JP): added summary scoring; revamped the derived metrics
# 20170617 (JP): initial version
#
# usage:
#  import nedc_eeg_eval_dpalign as nepoch
#
# This file implements NEDC's dynamic programming alignment scoring algorithm.
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
NEDC_DPALIGN = "NEDC_DPALIGN"

# define error types
#
DPALIGN_ETYPES_NULL = int(-1)
DPALIGN_ETYPES_DEL = int(0)
DPALIGN_ETYPES_INS = int(1)
DPALIGN_ETYPES_SUB = int(2)

#------------------------------------------------------------------------------
#
# functions are listed here
#
#------------------------------------------------------------------------------

# declare a global debug object so we can use it in functions
#
dbgl = ndt.Dbgl()

def run(events_ref, events_hyp, mapping, nedc_dpalign, odir, rfile, fp):
    """
    function: run
    
    arguments:
     events_ref: a dictionary containining all ref events indexed by filenames
     events_hyp: a dictionary containining all hyp events indexed by filenames
     mapping: a mapping used to collapse classes during scoring
     nedc_dpalign: the NEDC dp alignment scoring algorithm parameters
     odir: the output directory
     rfile: the results file (written in odir)
     fp: a pointer to the output summary file
 
    return: 
     a boolean value indicating status

    description: 
     This method runs the NEDC dp alignment scoring algorithm by:
     (1) loading the annotations
     (2) scoring them
     (3) displaying the results
    """
    
    # display an informational message
    #
    if dbgl > ndt.BRIEF:
        print("%s (line: %s) %s: running dpalign scoring" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__))

    # define local variables
    #
    status = True
    ndpalign = NedcDpalign(nedc_dpalign)

    # check the reference and hyp file lists
    #
    num_files_ref = len(events_ref)
    num_files_hyp = len(events_hyp)

    if num_files_ref < 1 or num_files_hyp < 1 or \
       num_files_ref != num_files_hyp:
        print("Error: %s (line: %s):%s: file list error (%s %s)" %
              (__FILE__, ndt.__LINE__,ndt.__NAME__,
               events_ref, events_hyp))
        return False

    # run dp alignment scoring
    #
    if dbgl > ndt.BRIEF:
        print("%s (line: %s) %s: scoring files" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__))

    status = ndpalign.init_score(mapping)
    status = ndpalign.score(events_ref, events_hyp, mapping, rfile)
    if status == False:
        print("Error: %s (line: %s):%s: error during scoring" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__))
        return False

    # compute performance
    #
    if dbgl > ndt.BRIEF:
        print("%s (line: %s) %s: computing performance" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__))

    cnf = ndpalign.compute_performance()
    if status == None:
        print("Error: %s (line: %s):%s: error computing performance" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__))
        return False

    # collect information for scoring and display
    #
    if dbgl > ndt.BRIEF:
        print("%s (line: %s) %s: displaying results" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__))

    header, tbl = nec.create_table(cnf)
    status = ndpalign.display_results("NEDC DPAlign Confusion Matrix",
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

class NedcDpalign():
    """
    Class: NedcDpalign
    
    arguments:
     none

    description: 
     This class contains methods that execute a dynamic programming based
     approach to scoring that was popularized in speech recognition.
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
        NedcDpalign.__CLASS_NAME__ = self.__class__.__name__

        # display informational message
        #
        if self.dbgl_d > ndt.BRIEF:
            print("%s (line: %s) %s::%s: scoring files" %
                  (__FILE__, ndt.__LINE__, NedcDpalign.__CLASS_NAME__,
                   ndt.__NAME__))
            
        # decode the parameters passed from the parameter file
        #
        self.penalty_del_d = float(params['penalty_del'])
        self.penalty_ins_d = float(params['penalty_ins'])
        self.penalty_sub_d = float(params['penalty_sub'])

        # declare a variable to hold a permuted map
        #
        self.pmap_d = {}

        # declare a duration parameter used to calculate the false alarm rate:
        #  we need to know the total duration of the data in secs
        #
        self.total_dur_d = float(0)

        # declare parameters to track errors:
        #  all algorithms should track the following per label:
        #   substitutions, deletions, insertions, hits, misses
        #   and false alarms.
        #
        self.tp_d = {}
        self.tn_d = {}
        self.fp_d = {}
        self.fn_d = {}

        self.tgt_d = {}
        self.hit_d = {}
        self.mis_d = {}
        self.fal_d = {}
        self.sub_d = {}
        self.ins_d = {}
        self.del_d = {}

        # additional derived data:
        #  we use class data to store a number of statistical measures
        #
        self.tpr_d = {}
        self.tnr_d = {}
        self.ppv_d = {}
        self.npv_d = {}
        self.fnr_d = {}
        self.fpr_d = {}
        self.fdr_d = {}
        self.for_d = {}
        self.acc_d = {}
        self.msr_d = {}
        self.prv_d = {}
        self.f1s_d = {}
        self.mcc_d = {}
        self.flr_d = {}

        # declare parameters to compute summaries
        #
        self.sum_tp_d = int(0)
        self.sum_tn_d = int(0)
        self.sum_fp_d = int(0)
        self.sum_fn_d = int(0)

        self.sum_tgt_d = int(0)
        self.sum_hit_d = int(0)
        self.sum_mis_d = int(0)
        self.sum_fal_d = int(0)
        self.sum_ins_d = int(0)
        self.sum_del_d = int(0)

        # additional derived data:
        #  we use class data to store a number of statistical measures
        #
        self.sum_tpr_d = float(0)
        self.sum_tnr_d = float(0)
        self.sum_ppv_d = float(0)
        self.sum_npv_d = float(0)
        self.sum_fnr_d = float(0)
        self.sum_fpr_d = float(0)
        self.sum_fdr_d = float(0)
        self.sum_for_d = float(0)
        self.sum_acc_d = float(0)
        self.sum_msr_d = float(0)
        self.sum_prv_d = float(0)
        self.sum_f1s_d = float(0)
        self.sum_mcc_d = float(0)
        self.sum_flr_d = float(0)

        # declare parameters to hold per file output
        #
        self.rfile_d = None
        self.refo_d = []
        self.hypo_d = []
        
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
                  (__FILE__, ndt.__LINE__, NedcDpalign.__CLASS_NAME__,
                   ndt.__NAME__))
            
        # initialize global counters
        #
        self.total_dur_d = float(0)

        # initialiaze parameters to track errors:
        #  these are declared as dictionaries organized
        #  in the order of the scoring map
        #
        self.tp_d = {}
        self.tn_d = {}
        self.fp_d = {}
        self.fn_d = {}

        self.tgt_d = {}
        self.hit_d = {}
        self.mis_d = {}
        self.fal_d = {}
        self.sub_d = {}
        self.ins_d = {}
        self.del_d = {}

        self.tpr_d = {}
        self.tnr_d = {}
        self.ppv_d = {}
        self.npv_d = {}
        self.fnr_d = {}
        self.fpr_d = {}
        self.fdr_d = {}
        self.for_d = {}
        self.acc_d = {}
        self.msr_d = {}
        self.prv_d = {}
        self.f1s_d = {}
        self.mcc_d = {}
        self.flr_d = {}

        # declare parameters to compute summaries
        #
        self.sum_tp_d = int(0)
        self.sum_tn_d = int(0)
        self.sum_fp_d = int(0)
        self.sum_fn_d = int(0)

        self.sum_tgt_d = int(0)
        self.sum_hit_d = int(0)
        self.sum_mis_d = int(0)
        self.sum_fal_d = int(0)
        self.sum_ins_d = int(0)
        self.sum_del_d = int(0)

        self.sum_tpr_d = float(0)
        self.sum_tnr_d = float(0)
        self.sum_ppv_d = float(0)
        self.sum_npv_d = float(0)
        self.sum_fnr_d = float(0)
        self.sum_fpr_d = float(0)
        self.sum_fdr_d = float(0)
        self.sum_for_d = float(0)
        self.sum_msr_d = float(0)
        self.sum_f1s_d = float(0)
        self.sum_mcc_d = float(0)
        self.sum_flr_d = float(0)

        # establish the order of these dictionaries in terms of
        # the scoring map.
        #
        for key in score_map:
            self.sub_d[key] = {}
            for key2 in score_map:
                self.sub_d[key][key2] = int(0)

            self.tp_d[key] = int(0)
            self.tn_d[key] = int(0)
            self.fp_d[key] = int(0)
            self.fn_d[key] = int(0)

            self.tgt_d[key] = int(0)
            self.hit_d[key] = int(0)
            self.mis_d[key] = int(0)
            self.fal_d[key] = int(0)
            self.ins_d[key] = int(0)
            self.del_d[key] = int(0)

            self.tpr_d[key] = float(0)
            self.tnr_d[key] = float(0)
            self.ppv_d[key] = float(0)
            self.npv_d[key] = float(0)
            self.fnr_d[key] = float(0)
            self.fpr_d[key] = float(0)
            self.fdr_d[key] = float(0)
            self.for_d[key] = float(0)
            self.acc_d[key] = float(0)
            self.msr_d[key] = float(0)
            self.prv_d[key] = float(0)
            self.f1s_d[key] = float(0)
            self.mcc_d[key] = float(0)
            self.flr_d[key] = float(0)

        # permute the map: we need this in various places
        #
        self.pmap_d = nft.permute_map(score_map)

        # exit gracefully
        # 
        return True
    #
    # end of method

    def score(self, all_events_ref, all_events_hyp, score_map, rfile):
        """
        method: score
        
        arguments:
         all_events_ref: a dictionary of all reference events
         all_events_hyp: a dictionary of all hypothesis events
         score_map: a scoring map
         rfile: a file that contains per file scoring results

        return: 
         a boolean value indicating status

        description: 
         This method computes a confusion matrix.
        """
 
        # display informational message
        #
        if self.dbgl_d > ndt.BRIEF:
            print("%s (line: %s) %s::%s: scoring files" %
                  (__FILE__, ndt.__LINE__, NedcDpalign.__CLASS_NAME__,
                   ndt.__NAME__))
            
        # declare local variables
        #
        status = True

        # create the results file
        #
        self.rfile_d = nft.make_fp(rfile)

        # loop over all files
        #
        i = int(0)
        for key_ref, key_hyp in zip(all_events_ref, all_events_hyp):

            # get the ref events
            #
            events_ref = all_events_ref[key_ref]
            if events_ref == None:
                print("Error: %s (line: %s) %s: %s (%s)" %
                      (__FILE__, ndt.__LINE__, ndt.__NAME__,
                       "error getting annotations", key_ref))
                return False

            # get the corresponding hyp events
            #                                                               
            events_hyp = all_events_hyp[key_hyp]
            if events_hyp == None:
                print("Error: %s (line: %s) %s: %s (%s)" %
                      (__FILE__, ndt.__LINE__, ndt.__NAME__,
                       "error getting annotations", key_hyp)) 
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
            refo, hypo = self.compute(ann_ref, ann_hyp)
            if refo == None:
                print("Error: %s (line: %s) %s::%s: %s (%s %s)" %
                      (__FILE__, ndt.__LINE__, NedcDpalign.__CLASS_NAME__,
                       ndt.__NAME__, "error computing confusion matrix",
                       events_ref[i], events_hyp[i]))
                return False

            # output the files to the per file results file
            #
            ref_fm, hyp_fm, hits, subs, inss, dels = \
	        nec.format_hyp(refo, hypo)
            
            self.rfile_d.write("%5d: %s" % (i, key_ref) + \
                               nft.DELIM_NEWLINE)
            self.rfile_d.write("%5s  %s" % (nft.STRING_EMPTY,
                                            key_hyp) +
                               nft.DELIM_NEWLINE)
            self.rfile_d.write("  Ref: %s" % ref_fm + nft.DELIM_NEWLINE)
            self.rfile_d.write("  Hyp: %s" % hyp_fm + nft.DELIM_NEWLINE)
            self.rfile_d.write("%7s (%s %d  %s %d  %s %d  %s %d  %s %d)" %
                               (nft.STRING_EMPTY, "Hit:", hits, "Sub:", subs,
                                "Ins:", inss, "Del:", dels,
                                "Total:", subs + inss + dels) +
                               nft.DELIM_NEWLINE)
            self.rfile_d.write(nft.DELIM_NEWLINE)

            # increment the counter
            #
            i += int(1)

        # close the file
        #
        self.rfile_d.close()

        # exit gracefully
        # 
        return True
    #
    # end of method

    def compute(self, ref, hyp):
        """
        method: compute
        
        arguments:
         ref: reference annotation
         hyp: hypothesis annotation

        return: 
         refo: the output aligned ref string
         hypo: the output aligned hyp string

        description: 
         this method measures similarity by performing a dynamic programming
         based string alignment.
        """
 
        # display informational message
        #
        if self.dbgl_d > ndt.BRIEF:
            print("%s (line: %s) %s::%s: computing errors" %
                  (__FILE__, ndt.__LINE__, NedcDpalign.__CLASS_NAME__,
                   ndt.__NAME__))
            
        # extract the labels from the input file record and extend the 
        #  inputs with a dummy symbol at the beginning and end:
        #  this makes the code a little simpler and more uniform
        #
        refi = [nec.NULL_CLASS]
        for value in ref:
            refi.append(value[2])
        refi.append(nec.NULL_CLASS)

        hypi = [nec.NULL_CLASS]
        for value in hyp:
            hypi.append(value[2])
        hypi.append(nec.NULL_CLASS)

        # compute the lengths and clear temp variables
        #
        m = len(refi)
        n = len(hypi)
        d = []
        etypes = []

        # zero out the cost matrix and initialize the edges with the
        # correct error types (backpointers)
        #
        for i in range(m):
            d.append([])
            etypes.append([])
            for j in range(n):
                d[i].append(float(0))
                etypes[i].append(DPALIGN_ETYPES_NULL)

        for i in range(1,n):
            d[0][i] = d[0][i-1] + self.penalty_ins_d
            etypes[0][i] = DPALIGN_ETYPES_INS

        for i in range(1,m):
            d[i][0] = d[i-1][0] + self.penalty_del_d
            etypes[i][0] = DPALIGN_ETYPES_DEL
        etypes[0][0] = DPALIGN_ETYPES_SUB

        # iterate over the interior nodes:
        #  cols (j) correspond to the reference. rows (i) correspond
        #  to the hypothesis. iterate over a column first (j), matching
        #  ref to a specific event in a hypothesis, and then over rows (i)
        #  next (iterating over events in the reference).
        #
        for j in range(1,n):
            for i in range(1,m):

                # compute the node penalties
                #
                d_del = d[i-1][j] + self.penalty_del_d
                d_ins = d[i][j-1] + self.penalty_ins_d
                d_sub = d[i-1][j-1]
                if refi[i] != hypi[j]:
                    d_sub += self.penalty_sub_d

                # update the best path and save the error type
                #
                min_dist = d_sub
                etypes[i][j] = DPALIGN_ETYPES_SUB
                if (d_ins < min_dist):
                    min_dist = d_ins
                    etypes[i][j] = DPALIGN_ETYPES_INS
                if (d_del < min_dist):
                    min_dist = d_del
                    etypes[i][j] = DPALIGN_ETYPES_DEL
                d[i][j] = min_dist

        # the last node (m-1, n-1) is where the best path terminates. backtrack
        # to get the best path. start at (m-1, n-1) and end at (0,0).
        #
        i = int(m - 1)
        j = int(n - 1)
        reft = []
        hypt = []

        while (True):
            if etypes[i][j] == DPALIGN_ETYPES_DEL:
                reft.append(refi[i])
                hypt.append(nec.NULL_CLASS)
                i -= 1
            elif etypes[i][j] == DPALIGN_ETYPES_INS:
                reft.append(nec.NULL_CLASS)
                hypt.append(hypi[j])
                j -= 1
            elif etypes[i][j] == DPALIGN_ETYPES_SUB:
                reft.append(refi[i])
                hypt.append(hypi[j])
                i -= 1
                j -= 1
            else:
                print("Error: %s (line: %s) %s::%s: %s (%s %s)" %
                      (__FILE__, ndt.__LINE__, NedcDpalign.__CLASS_NAME__,
                       ndt.__NAME__, "error doing dynamic programming",
                       events_ref[i], events_hyp[i]))
                return False

            # the best path must terminate on (0,0)
            #
            if (i < 0) and (j < 0):
                break

        # flip the arrays so the output is in the right order
        #
        refo = reft[::-1]
        hypo = hypt[::-1]

        # count errors - igtnore the first and last items since they are
        # due to the dummy nodes
        #
        for i in range(1, len(refo) - 1):
        
            # track no. of targets, del, ins and subs
            #
            if refo[i] == nec.NULL_CLASS:
                self.ins_d[hypo[i]] += int(1)
            elif hypo[i] == nec.NULL_CLASS:
                self.tgt_d[refo[i]] += 1            
                self.del_d[refo[i]] += int(1)
            else:
                self.tgt_d[refo[i]] += 1            
                self.sub_d[refo[i]][hypo[i]] += 1
                
            # track no. of hits, misses and false alarms
            #
            if refo[i] == nec.NULL_CLASS:
                self.fal_d[hypo[i]] += int(1)
            elif hypo[i] == nec.NULL_CLASS:
                self.mis_d[refo[i]] += int(1)
            elif refo[i] == hypo[i]:
                self.hit_d[refo[i]] += int(1)
            else:
                self.mis_d[refo[i]] += int(1)

        # exit gracefully
        #
        return [refo, hypo]

    def compute_performance(self):
        """
        method: compute_performance
        
        arguments:
         none

        return: 
         cnf: a confusion matrix

        description: 
         This method computes a number of standard measures of performance. The
         terminology follows these references closely:
        
         https://en.wikipedia.org/wiki/Confusion_matrix
         https://en.wikipedia.org/wiki/Precision_and_recall
         http://www.dataschool.io/simple-guide-to-confusion-matrix-terminology/
        
         The approach taken here for a multi-class problem is to convert the
         NxN matrix to a 2x2 for each label, and then do the necessary
         computations.
        """
 
        # display informational message
        #
        if self.dbgl_d > ndt.BRIEF:
            print("%s (line: %s) %s::%s: computing the performance" %
                  (__FILE__, ndt.__LINE__, NedcDpalign.__CLASS_NAME__,
                   ndt.__NAME__))
            
        # check for a zero count
        #
        num_total_ref_events = sum(self.tgt_d.values())
        if num_total_ref_events == 0:
            print("Error: %s (line: %s) %s::%s: %s (%d)" %
                  (__FILE__, ndt.__LINE__, NedcDpalign.__CLASS_NAME__,
                   ndt.__NAME__, "number of events is zero",
                   num_total_ref_events))    
            return None

        #----------------------------------------------------------------------
        # (1) The first block of parameters count events such as hits,
        #     missses and false alarms. These are directly computed
        #     from the output of the dp alignment.


        #----------------------------------------------------------------------
        # (2) The second block of computations are the derived measures
        #     such as sensitivity. These are computed using a two-step
        #     approach:
        #      (2.2) compute true positives, etc. (tp, tn, fp, fn)
        #      (2.3) compute the derived measures (e.g., sensitivity)
        #
        # loop over all labels
        #
        for key1 in self.sub_d:

            #------------------------------------------------------------------
            # (2.2) The dp algorithm outputs hits, misses and false alarms
            #       directly. These must be converted to (tp, tn, fp, fn).
            #
            # compute true positives (tp)
            #
            self.tp_d[key1] = self.hit_d[key1]

            # compute true negatives (tn)
            #  sum the submatrix formed when you exclude the row and column
            #  associated with key1
            #
            tn_sum = int(0)
            for key2 in self.sub_d:
                for key3 in self.sub_d:
                    if (key1 != key2) and (key1 != key3):
                        tn_sum += self.sub_d[key2][key3]
            self.tn_d[key1] = tn_sum

            # compute false positives (fp)
            #
            self.fp_d[key1] = self.ins_d[key1]

            # compute false negatives (fn)
            #
            self.fn_d[key1] = self.mis_d[key1]

            # check the health of the confusion matrix
            #
            tp = self.tp_d[key1]
            fp = self.fp_d[key1]
            tn = self.tn_d[key1]
            fn = self.fn_d[key1]
            tdur = self.total_dur_d

            if ((tp + fn) == 0) or ((fp + tn) == 0) or \
               ((tp + fp) == 0) or ((fn + tn) == 0):
                print("Warning: %s (line: %s) %s::%s: %s (%d %d %d %d)" %
                  (__FILE__, ndt.__LINE__, NedcDpalign.__CLASS_NAME__,
                   ndt.__NAME__, "divide by zero", tp, fp, tn, fn))    
            elif (round(tdur, ndt.MAX_PRECISION) == 0):
                print("Warning: %s (line: %s) %s::%s: %s (%f)" %
                  (__FILE__, ndt.__LINE__, NedcDpalign.__CLASS_NAME__,
                   ndt.__NAME__, "duration is zero",  tdur))    

            # (2.3) compute derived measures
            #
            if (tp + fn) != 0:
                self.tpr_d[key1] = float(self.tp_d[key1]) / float(tp + fn)
            else:
                self.tpr_d[key1] = float(0)

            if (tn + fp) != 0:
                self.tnr_d[key1] = float(self.tn_d[key1]) / float(tn + fp)
            else:
                self.tnr_d[key1] = float(0)

            if (tp + fp) != 0:
                self.ppv_d[key1] = float(self.tp_d[key1]) / float(tp + fp)
            else:
                self.ppv_d[key1] = float(0)

            if (tn + fn) != 0:
                self.npv_d[key1] = float(self.tn_d[key1]) / float(tn + fn)
            else:
                self.npv_d[key1] = float(0)

            self.fnr_d[key1] = 1 - float(self.tpr_d[key1])
            self.fpr_d[key1] = 1 - float(self.tnr_d[key1])
            self.fdr_d[key1] = 1 - float(self.ppv_d[key1])
            self.for_d[key1] = 1 - float(self.npv_d[key1])

            if (tp + tn + fp + fn) != 0:
                self.acc_d[key1] = float(self.tp_d[key1] + self.tn_d[key1]) / \
                                   (tp + tn + fp + fn)
                self.prv_d[key1] = float(self.tp_d[key1] + self.fn_d[key1]) / \
                                   (tp + tn + fp + fn)
            else:
                self.acc_d[key1] = float(0)
                self.prv_d[key1] = float(0)

            self.msr_d[key1] = 1 - self.acc_d[key1]

            # compute the f1 score:
            #  this has to be done after sensitivity and prec are computed
            #
            f1s_denom = float(self.ppv_d[key1] + self.tpr_d[key1])
            if round(f1s_denom, ndt.MAX_PRECISION) == 0:
                print("Warning: %s (line: %s) %s::%s: %s (%s)" %
                  (__FILE__, ndt.__LINE__, NedcDpalign.__CLASS_NAME__,
                   ndt.__NAME__, "f ratio divide by zero", key1))    
                self.f1s_d[key1] = float(0)
            else:
                self.f1s_d[key1] = 2.0 * self.ppv_d[key1] * \
                                    self.tpr_d[key1] / f1s_denom

            # compute the mcc score:
            #  this has to be done after sensitivity and prec are computed
            #
            mcc_denom = (tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)
            mcc_num = (tp * tn) - (fp * fn)
            if round(mcc_denom, ndt.MAX_PRECISION) == 0:
                print("Warning: %s (line: %s) %s::%s: %s (%s)" %
                  (__FILE__, ndt.__LINE__, NedcDpalign.__CLASS_NAME__,
                   ndt.__NAME__, "mcc ratio divide by zero",  key1))    
                self.mcc_d[key1] = float(0)
            else:
                self.mcc_d[key1] = mcc_num / math.sqrt(mcc_denom)

            # compute the false alarm rate
            #
            if (round(tdur, ndt.MAX_PRECISION) != 0):
                self.flr_d[key1] = float(fp) / tdur * (60 * 60 * 24)
        
        #----------------------------------------------------------------------
        # (3) the third block of parameters are the summary values
        #
        self.sum_tgt_d = sum(self.tgt_d.values())
        self.sum_hit_d = sum(self.hit_d.values())
        self.sum_mis_d = sum(self.mis_d.values())
        self.sum_fal_d = sum(self.fal_d.values())
        self.sum_ins_d = sum(self.ins_d.values())
        self.sum_del_d = sum(self.del_d.values())

        self.sum_tp_d = sum(self.tp_d.values())
        self.sum_tn_d = sum(self.tn_d.values())
        self.sum_fp_d = sum(self.fp_d.values())
        self.sum_fn_d = sum(self.fn_d.values())

        if (self.sum_tp_d + self.sum_fn_d) != 0:
            self.sum_tpr_d = float(self.sum_tp_d) / \
                             float(self.sum_tp_d + self.sum_fn_d)
        else:
            self.sum_tpr_d = float(0)

        if (self.sum_tn_d + self.sum_fp_d) != 0:
            self.sum_tnr_d = float(self.sum_tn_d) / \
                             float(self.sum_tn_d + self.sum_fp_d)
        else:
            self.sum_tnr_d = float(0)

        if (self.sum_tp_d + self.sum_fp_d) != 0:
            self.sum_ppv_d = float(self.sum_tp_d) / \
                             float(self.sum_tp_d + self.sum_fp_d)
        else:
            self.sum_ppv_d = float(0)

        if (self.sum_tn_d + self.sum_fn_d) != 0:
            self.sum_npv_d = float(self.sum_tn_d) / \
                             float(self.sum_tn_d + self.sum_fn_d)
        else:
            self.sum_npv_d = float(0)

        self.sum_fnr_d = 1 - float(self.sum_tpr_d)
        self.sum_fpr_d = 1 - float(self.sum_tnr_d)
        self.sum_fdr_d = 1 - float(self.sum_ppv_d)
        self.sum_for_d = 1 - float(self.sum_npv_d)

        if (self.sum_tp_d + self.sum_tn_d + \
            self.sum_fp_d + self.sum_fn_d) != 0:
            self.sum_acc_d = float(self.sum_tp_d + self.sum_tn_d) / \
                             (float(self.sum_tp_d + self.sum_tn_d + \
                                    self.sum_fp_d + self.sum_fn_d))
            self.sum_prv_d = float(self.sum_tp_d + self.sum_fn_d) / \
                             (float(self.sum_tp_d + self.sum_tn_d + \
                                    self.sum_fp_d + self.sum_fn_d))
        else:
            self.sum_acc_d = float(0)
            self.sum_prv_d = float(0)

        self.sum_msr_d = 1 - self.sum_acc_d

        if round(f1s_denom, ndt.MAX_PRECISION) == 0:
            print("Warning: %s (line: %s) %s::%s: %s (%s)" %
                  (__FILE__, ndt.__LINE__, NedcDpalign.__CLASS_NAME__,
                   ndt.__NAME__, "f ratio divide by zero", "summary"))    
            self.sum_f1s_d = float(0)
        else:
            self.sum_f1s_d = 2.0 * self.sum_ppv_d * self.sum_tpr_d / f1s_denom

        # compute the mcc score:
        #  this has to be done after sensitivity and prec are computed
        #
        sum_mcc_denom = (self.sum_tp_d + self.sum_fp_d) \
            * (self.sum_tp_d + self.sum_fn_d) \
            * (self.sum_tn_d + self.sum_fp_d) * (self.sum_tn_d + self.sum_fn_d)
        sum_mcc_num = (self.sum_tp_d * self.sum_tn_d) \
            - (self.sum_fp_d * self.sum_fn_d)
        if round(sum_mcc_denom, ndt.MAX_PRECISION) == 0:
            print("Warning: %s (line: %s) %s::%s: %s (%s)" %
                  (__FILE__, ndt.__LINE__, NedcDpalign.__CLASS_NAME__,
                   ndt.__NAME__, "mcc ratio divide by zero", "summary"))    
            self.sum_mcc_d = float(0)
        else:
            self.sum_mcc_d = sum_mcc_num / math.sqrt(sum_mcc_denom)
            
        # compute the false alarm rate
        #
        if round(self.total_dur_d, ndt.MAX_PRECISION) == 0:
            self.sum_flr_d = float(0)
        else:
            self.sum_flr_d = float(self.sum_fp_d) / self.total_dur_d * \
                (60 * 60 * 24)

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
                  (__FILE__, ndt.__LINE__, NedcDpalign.__CLASS_NAME__,
                   ndt.__NAME__))
            
        # print complete table in output file
        #
        nec.print_table(title, headers, tbl,
                        "%10s", "%12.2f", "%6.2f", fp)
        fp.write(nft.DELIM_NEWLINE)

        # write per label header
        #
        fp.write(("Per Label Results:" + nft.DELIM_NEWLINE).upper())
        fp.write(nft.DELIM_NEWLINE)

        # per label results: loop over all classes
        #
        for key in self.sub_d:
            fp.write((" Label: %s" % key + nft.DELIM_NEWLINE).upper())
            fp.write(nft.DELIM_NEWLINE)

            fp.write("   %30s: %12.0f" %
                     ("Targets", float(self.tgt_d[key])) + nft.DELIM_NEWLINE)
            fp.write("   %30s: %12.0f" %
                     ("Hits", float(self.hit_d[key])) + nft.DELIM_NEWLINE)
            fp.write("   %30s: %12.0f" %
                     ("Misses", float(self.mis_d[key])) + nft.DELIM_NEWLINE)
            fp.write("   %30s: %12.0f" %
                     ("False Alarms", float(self.fal_d[key])) +
                     nft.DELIM_NEWLINE)
            fp.write("   %30s: %12.0f   <**" %
                     ("Insertions", float(self.ins_d[key])) +
                     nft.DELIM_NEWLINE)
            fp.write("   %30s: %12.0f   <**" %
                     ("Deletions", float(self.del_d[key])) + nft.DELIM_NEWLINE)
            fp.write(nft.DELIM_NEWLINE)

            fp.write("   %30s: %12.0f" %
                     ("True Positives (TP)", float(self.tp_d[key])) +
                     nft.DELIM_NEWLINE)
            fp.write("   %30s: %12.0f" %
                     ("True Negatives (TN)", float(self.tn_d[key])) +
                     nft.DELIM_NEWLINE)
            fp.write("   %30s: %12.0f" %
                     ("False Positives (FP)", float(self.fp_d[key])) +
                     nft.DELIM_NEWLINE)
            fp.write("   %30s: %12.0f" %
                     ("False Negatives (FN)", float(self.fn_d[key])) +
                     nft.DELIM_NEWLINE)
            fp.write(nft.DELIM_NEWLINE)

            fp.write("   %30s: %12.4f%%" %
                     ("Sensitivity (TPR, Recall)", self.tpr_d[key] * 100.0) +
                     nft.DELIM_NEWLINE)
            fp.write("   %30s: %12.4f%%" %
                     ("Specificity (TNR)", self.tnr_d[key] * 100.0) +
                     nft.DELIM_NEWLINE)
            fp.write("   %30s: %12.4f%%" %
                     ("Precision (PPV)", self.ppv_d[key] * 100.0) +
                     nft.DELIM_NEWLINE)
            fp.write("   %30s: %12.4f%%" %
                     ("Negative Pred. Value (NPV)",
                        self.npv_d[key] * 100.0) + nft.DELIM_NEWLINE)
            fp.write("   %30s: %12.4f%%" %
                     ("Miss Rate (FNR)", self.fnr_d[key] * 100.0) +
                     nft.DELIM_NEWLINE)
            fp.write("   %30s: %12.4f%%" %
                     ("False Positive Rate (FPR)",
                        self.fpr_d[key] * 100.0) + nft.DELIM_NEWLINE)
            fp.write("   %30s: %12.4f%%" %
                     ("False Discovery Rate (FDR)",
                        self.fdr_d[key] * 100.0) + nft.DELIM_NEWLINE)
            fp.write("   %30s: %12.4f%%" %
                     ("False Omission Rate (FOR)",
                        self.for_d[key] * 100.0) + nft.DELIM_NEWLINE)
            fp.write("   %30s: %12.4f%%" %
                     ("Accuracy", self.acc_d[key] * 100.0) + nft.DELIM_NEWLINE)
            fp.write("   %30s: %12.4f%%" %
                     ("Misclassification Rate",
                        self.msr_d[key] * 100.0) + nft.DELIM_NEWLINE)
            fp.write("   %30s: %12.4f%%" %
                     ("Prevalence", self.prv_d[key] * 100.0) +
                     nft.DELIM_NEWLINE)
            fp.write("   %30s: %12.4f" %
                     ("F1 Score (F Ratio)", self.f1s_d[key]) +
                     nft.DELIM_NEWLINE)
            fp.write("   %30s: %12.4f" %
                     ("Matthews (MCC)", self.mcc_d[key]) + nft.DELIM_NEWLINE)
            fp.write("   %30s: %12.4f per 24 hours" %
                     ("False Alarm Rate", self.flr_d[key]) + nft.DELIM_NEWLINE)
            fp.write(nft.DELIM_NEWLINE)

        # display a summary of the results
        #
        fp.write(("Summary:" + nft.DELIM_NEWLINE).upper())
        fp.write(nft.DELIM_NEWLINE)

        # display the standard derived values
        #
        fp.write("   %30s: %12.0f" %
                 ("Total", float(self.sum_tgt_d)) + nft.DELIM_NEWLINE)
        fp.write("   %30s: %12.0f" %
                 ("Hits", float(self.sum_hit_d)) + nft.DELIM_NEWLINE)
        fp.write("   %30s: %12.0f" %
                 ("Misses", float(self.sum_mis_d)) + nft.DELIM_NEWLINE)
        fp.write("   %30s: %12.0f" %
                 ("False Alarms", float(self.sum_fal_d)) + nft.DELIM_NEWLINE)
        fp.write("   %30s: %12.0f   <**" %
                 ("Insertions", float(self.sum_ins_d)) + nft.DELIM_NEWLINE)
        fp.write("   %30s: %12.0f   <**" %
                 ("Deletions", float(self.sum_del_d)) + nft.DELIM_NEWLINE)
        fp.write(nft.DELIM_NEWLINE)

        fp.write("   %30s: %12.0f" %
                 ("True Positives(TP)", float(self.sum_tp_d)) +
                 nft.DELIM_NEWLINE)
        fp.write("   %30s: %12.0f" %
                 ("False Positives (FP)", float(self.sum_fp_d)) +
                 nft.DELIM_NEWLINE)
        fp.write(nft.DELIM_NEWLINE)

        fp.write("   %30s: %12.4f%%" %
                 ("Sensitivity (TPR, Recall)",
                    self.sum_tpr_d * 100.0) + nft.DELIM_NEWLINE)
        fp.write("   %30s: %12.4f%%" %
                 ("Miss Rate (FNR)", self.sum_fnr_d * 100.0) +
                 nft.DELIM_NEWLINE)
        fp.write("   %30s: %12.4f%%" %
                 ("Accuracy", self.sum_acc_d * 100.0) + nft.DELIM_NEWLINE)
        fp.write("   %30s: %12.4f%%" %
                 ("Misclassification Rate",
                    self.sum_msr_d * 100.0) + nft.DELIM_NEWLINE)
        fp.write("   %30s: %12.4f%%" %
                 ("Prevalence", self.sum_prv_d * 100.0) + nft.DELIM_NEWLINE)
        fp.write("   %30s: %12.4f" %
                 ("F1 Score", self.sum_f1s_d) + nft.DELIM_NEWLINE)
        fp.write("   %30s: %12.4f" %
                 ("Matthews (MCC)", self.sum_mcc_d) + nft.DELIM_NEWLINE)
        fp.write(nft.DELIM_NEWLINE)

        # display the overall false alarm rate
        #
        fp.write("   %30s: %12.4f secs" %
                 ("Total Duration", self.total_dur_d) + nft.DELIM_NEWLINE)
        fp.write("   %30s: %12.4f events" %
                 ("Total False Alarms", self.sum_fp_d) + nft.DELIM_NEWLINE)
        fp.write("   %30s: %12.4f per 24 hours" %
                 ("Total False Alarm Rate", self.sum_flr_d) +
                 nft.DELIM_NEWLINE)
        fp.write(nft.DELIM_NEWLINE)

        # exit gracefully
        #
        return True
    #
    # end of method

    def score_roc(self, events_ref, events_hyp):
        """
        method: score_roc
        
        arguments:
         events_ref: a reference list
         events_hyp: a hypothesis list

        return: 
         a boolean value indicating status

        description: 
         This method computes a confusion matrix for an roc/det curve.
        """
 
        # display informational message
        #
        if self.dbgl_d > ndt.BRIEF:
            print("%s (line: %s) %s::%s: computing an roc/det curve" %
                  (__FILE__, ndt.__LINE__, NedcDpalign.__CLASS_NAME__,
                   ndt.__NAME__))
            
        # declare local variables
        #
        status = True

        # loop over all event lists (corresponding to files)
        #
        for ann_ref, ann_hyp in zip(events_ref, events_hyp):

            # update the total duration
            #
            self.total_dur_d += ann_ref[-1][1]

            # add this to the confusion matrix
            #
            refo, hypo = self.compute(ann_ref, ann_hyp)
            if refo == None:
                print("Error: %s (line: %s) %s::%s: %s" %
                  (__FILE__, ndt.__LINE__, NedcDpalign.__CLASS_NAME__,
                   ndt.__NAME__), "error computing confusions")    
                return False

        # exit gracefully
        # 
        return True
    #
    # end of method

    def compute_performance_roc(self, key):
        """
        method: compute_performance_roc
        
        arguments:
         key: the class to be scored

        return: 
         a boolean value indicating status

        description: 
         This is a stripped down version of compute_performance that is
         focused on the data needed for an ROC or DET curve.
        
         Note that because of the way this method is used, error messages
         are suppressed.
        """
 
        # display informational message
        #
        if self.dbgl_d > ndt.BRIEF:
            print("%s (line: %s) %s::%s: computing performance for an ROC" %
                  (__FILE__, ndt.__LINE__, NedcDpalign.__CLASS_NAME__,
                   ndt.__NAME__))
            
        # check for a zero count
        #
        num_total_ref_events = sum(self.tgt_d.values())
        if num_total_ref_events == 0:
            print("Error: %s (line: %s) %s::%s: %s (%d)" %
                  (__FILE__, ndt.__LINE__, NedcDpalign.__CLASS_NAME__,
                   ndt.__NAME__, "number of events is zero",
                   num_total_ref_events))    
            return False

        #----------------------------------------------------------------------
        # (1) The first block of parameters count events such as hits,
        #     missses and false alarms. The overlap algorithm provides
        #     these directly.
        #
        for key1 in self.hit_d:
            self.ins_d[key1] = self.fal_d[key1]
            self.del_d[key1] = self.mis_d[key1]

        #----------------------------------------------------------------------
        # (2) The second block of computations are the derived measures
        #     such as sensitivity. These are computed using a two-step
        #     approach:
        #      (2.2) compute true positives, etc. (tp, tn, fp, fn)
        #      (2.3) compute the derived measures (e.g., sensitivity)
        #
        #------------------------------------------------------------------
        # (2.2) The overlap algorithm outputs hits, misses and false alarms
        #       directly. These must be converted to (tp, tn, fp, fn).
        #
        # compute true positives (tp)
        #
        self.tp_d[key] = self.hit_d[key]

        # compute true negatives (tn):
        #  sum the hits that are not the current label
        #
        tn_sum = int(0)
        for key2 in self.hit_d:
            if key != key2:
                tn_sum += self.hit_d[key2]
        self.tn_d[key] = tn_sum

        # compute false positives (fp): copy false alarms
        #
        self.fp_d[key] = self.fal_d[key]

        # compute false negatives (fn): copy misses
        #
        self.fn_d[key] = self.mis_d[key]

        # check the health of the confusion matrix
        #
        tp = self.tp_d[key]
        fp = self.fp_d[key]
        tn = self.tn_d[key]
        fn = self.fn_d[key]
        tdur = self.total_dur_d

        # (2.3) compute derived measures
        #
        if (tp + fn) != 0:
            self.tpr_d[key] = float(self.tp_d[key]) / float(tp + fn)
        else:
            self.tpr_d[key] = float(0)

        if (tn + fp) != 0:
            self.tnr_d[key] = float(self.tn_d[key]) / float(tn + fp)
        else:
            self.tnr_d[key] = float(0)

        self.fnr_d[key] = 1 - float(self.tpr_d[key])
        self.fpr_d[key] = 1 - float(self.tnr_d[key])

        # exit gracefully
        #
        return True
    #
    # end of method

    def get_roc(self, key):
        """
        method: get_roc
        
        arguments:
         key: the symbol for which the values are needed

        return: 
         a boolean value indicating status

        description: 
         This method simply returns the quanities needed for an roc curve:
         true positive rate (tpr) as a function of the false positive rate (fpr).
        """
         
        return self.fpr_d[key], self.tpr_d[key]

    def get_det(self, key):
        """
        method: get_det
        
        arguments:
         key: the symbol for which the values are needed

        return: 
         a boolean value indicating status

        description: 
         This method simply returns the quanities needed for a det curve:
         false negative rate (fnr) as a function of the false positive rate (fpr).
        """
         
        return self.fpr_d[key], self.fnr_d[key]

# end of file
#
