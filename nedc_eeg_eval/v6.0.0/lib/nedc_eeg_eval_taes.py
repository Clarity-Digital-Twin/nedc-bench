#!/usr/bin/env python

# file: $NEDC_NFC/class/python/nedc_eeg_eval_tools/nedc_eeg_eval_taes.py
#
# revision history:
#
# 20240716 (JP): refactored after the rewrite of ann_tools
# 20230705 (AB): refactored code to new comment format
# 20220514 (JP): refactored the code to use the new annotation tools library
# 20200813 (LV): updated for rehaul of nedc_eval_eeg
# 20180218 (VS): bug fixes, updated the metric according definition
# 20170815 (JP): added another metric: prevalence
# 20170812 (JP): changed the divide by zero checks
# 20170716 (JP): upgraded to using the new annotation tools
# 20170710 (JP): refactored code
# 20170702 (JP): added summary scoring; revamped the derived metrics
# 20170627 (VS): second optimized version
# 20170625 (VS): initial version
#
# usage:
#  import nedc_eeg_eval_taes as ntaes
#
# this file implements NEDC's time-aligned event scoring algorithm.
#------------------------------------------------------------------------------

# import required system modules
#
import os
import sys
import math

# import required nedc modules
#
import nedc_debug_tools as ndt
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
NEDC_TAES = "NEDC_TAES"

#------------------------------------------------------------------------------
#
# functions are listed here
#
#------------------------------------------------------------------------------

# declare a global debug object so we can use it in functions
#
dbgl = ndt.Dbgl()

def run(events_ref, events_hyp, mapping, nedc_taes, odir, rfile, fp):
    """
    function: run
    
    arguments:
     events_ref: a dictionary containining all ref events indexed by filenames
     events_hyp: a dictionary containining all hyp events indexed by filenames
     mapping: a mapping used to collapse classes during scoring
     nedc_epoch: the NEDC epoch scoring algorithm parameters
     odir: the output directory
     rfile: the results file (written in odir)
     fp: a pointer to the output summary file

    returns: 
     a boolean value indicating status

    description: 
     This method runs the NEDC time-aligned scoring algorithm by:
      (1) loading the annotations
      (2) scoring them
      (3) displaying the results
    """
     
    # display an informational message
    #
    if dbgl > ndt.BRIEF:
        print("%s (line: %s) %s: running taes scoring" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__))

    # define local variables
    #
    status = True
    ntaes = NedcTAES(nedc_taes)

    # load the reference and hyp file lists into memory
    #
    num_files_ref = len(events_ref)
    num_files_hyp = len(events_hyp)

    if num_files_ref < 1 or num_files_hyp < 1 or \
       num_files_ref != num_files_hyp:
        print("Error: %s (line: %s) %s: file list error (%s %s)" % 
            (__FILE__, ndt.__LINE__, ndt.__NAME__, events_ref, events_hyp))
        return False

    # run time-aligned scoring
    #
    if dbgl > ndt.BRIEF:
        print("%s (line: %s) %s: scoring files" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__))

    status = ntaes.init_score(mapping)
    status = ntaes.score(events_ref, events_hyp, mapping, rfile)
    if status == False:
        print("Error: %s (line: %s) %s: error during scoring" % 
            (__FILE__, ndt.__LINE__,ndt.__NAME__))
        return False

    # compute performance
    #
    if dbgl > ndt.BRIEF:
        print("%s (line: %s) %s: computing performance" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__))

    cnf = ntaes.compute_performance()
    if status == None:
        print("Error: %s (line: %s) %s: error computing performance" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__))
        return False

    # collect information for scoring and display
    #
    if dbgl > ndt.BRIEF:
        print("%s (line: %s) %s: displaying results" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__))

    status = ntaes.display_results(fp)
    if status == False:
        print("Error: %s (line: %s) %s: error displaying results" % 
            (__FILE__, ndt.__LINE__,ndt.__NAME__))
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

class NedcTAES():
    """
    Class: NedcTAES
    
    arguments:
     none

    description: 
     This class contains methods that execute the time-aligned event-based 
     scoring algorithm. This approach computes fractional counts of matches,
     providing more resolution than the overlap method.
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

        returns: 
         none

        description: 
         none
        """

        # create class data                                                    
        #                                                                      
        NedcTAES.__CLASS_NAME__ = self.__class__.__name__

        # display informational message                                        
        #                                                                      
        if self.dbgl_d > ndt.BRIEF:
            print("%s (line: %s) %s::%s: scoring files" %
                  (__FILE__, ndt.__LINE__, NedcTAES.__CLASS_NAME__,
                   ndt.__NAME__))
        # decode the parameters passed from the parameter file
        #

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

    #
    # end of method

    def init_score(self, score_map):
        """
        method: init_score
        
        arguments:
         score_map: a scoring map

        returns: 
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
                  (__FILE__, ndt.__LINE__, NedcTAES.__CLASS_NAME__,
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

        returns: 
         a boolean value indicating status

        description: 
         This method computes a confusion matrix.
        """

        # display informational message                                        
        #                                                                      
        if self.dbgl_d > ndt.BRIEF:
            print("%s (line: %s) %s::%s: scoring files" %
                  (__FILE__, ndt.__LINE__, NedcTAES.__CLASS_NAME__,
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

            events_ref = all_events_ref[key_ref]
            if events_ref == None:
                print("Error: %s (line: %s) %s: %s (%s)" %
                      (__FILE__, ndt.__LINE__, ndt.__NAME__,
                       "error getting annotations", fname))
                return False

            # get the hyp events
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
            refo, hypo, hit, mis, fal = self.compute(ann_ref, ann_hyp)
            if refo == None:
                ("Error: %s (line: %s) %s::%s %s (%s)" %
                    (__FILE__, ndt.__LINE__, Nedc_TAES.__CLASS_NAME__,
                     ndt.__NAME__, "error computing confusion matrix",
                     fname))
                return False

            # output the files to the per file results file
            #
            self.rfile_d.write("%5d: %s" % (i, key_ref) + \
                               nft.DELIM_NEWLINE)
            self.rfile_d.write("%5s  %s" % (nft.STRING_EMPTY,
                                            key_hyp) + nft.DELIM_NEWLINE)
            self.rfile_d.write("  Ref: %s" % nft.DELIM_SPACE.join(refo) +
                               nft.DELIM_NEWLINE)
            self.rfile_d.write("  Hyp: %s" % nft.DELIM_SPACE.join(hypo) +
                               nft.DELIM_NEWLINE)
            self.rfile_d.write("%6s (%s %.4f  %s %.4f  %s %.4f  %s %.4f)" %
                               (nft.STRING_EMPTY, "Hit:", hit,
                                "Miss:", mis, "False Alarms:", fal,
                                "Total:", mis + fal) + nft.DELIM_NEWLINE)
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
         hit: the number of hits
         mis: the number of misses
         fal: the number of false alarms

        description: 
         this method loops through reference and hypothesis annotations to 
         collect partial and absolute hit, miss and false alarms.
        """

        # check to make sure the annotations match:
        #  since these are floating point values for times, we
        #  do a simple sanity check to make sure the end times
        #  are close (within 1 microsecond)
        #
        if round(ref[-1][1], ndt.MIN_PRECISION) != \
           round(hyp[-1][1], ndt.MIN_PRECISION):
            return False

        # prime the output strings with null characters
        #
        refo = []
        hypo = []

        # initialize hmf variables to collect absolute and partial values
        #
        hit = float(0)
        mis = float(0)
        fal = float(0)

        # generate flags for hypothesis and reference values to indicate
        # whether an event is used once or not (for detection)
        #
        hflags = []
        rflags = []

        for i in range(len(hyp)):
            hflags.append(True)
        for i in range(len(ref)):
            rflags.append(True)

        # loop through ref events
        #
        for i in range(len(ref)):
            self.tgt_d[ref[i][2]] += 1
            tgt_event = ref[i][2]
            refo.append(ref[i][2])
            
            # collect hyp events which are in some overlap with ref event
            #
            labels, starts, stops \
                = self.get_events(ref[i][0], ref[i][1], hyp, hflags)

            # one event at a time, don't bother if ref/hyp labels don't overlap
            #
            if ref[i][2] in labels and rflags[i]:

                # loop through all hyp events and calculate partial HMF
                #
                for j in range(len(hyp)):

                    # compare hyp and ref event labels and hyp flags status;
                    #
                    if hyp[j][2] == ref[i][2] and hflags[j]:
                    
                        p_hit, p_miss, p_fa \
                            = self.compute_partial(ref, hyp, i, j, \
                                                   rflags, hflags, tgt_event)

                        # updat the HMF confusion matrix
                        #
                        hit += p_hit
                        mis += p_miss
                        fal += p_fa

                        self.hit_d[ref[i][2]] += p_hit
                        self.mis_d[ref[i][2]] += p_miss
                        self.fal_d[ref[i][2]] += p_fa

                    # update the hyp event index
                    #
                    j += 1
            
            # updated the ref event index
            #
            i += 1

        # update the absolute misses and false alarms from flags
        #
        if True in (rflags + hflags):
            mis += rflags.count(True)
            fal += hflags.count(True)
            self.update_abs_mf(ref, hyp, rflags, hflags)
        
        # exit gracefully
        #
        return (refo, hypo, hit, mis, fal)

    def update_abs_mf(self, ref, hyp, rflags, hflags):
        """
        method: update_abs_mf
        
        arguments:
         ref: reference label information as a list
         hyp: hypothesis label information as a list
         rflags: reference flags indicating the processed labels
         hflags: hypothesis flags indicating the processed labels

        returns: 
         none

        description: 
         This method updates the miss and fa class-variables by 
         collecting the ignored events which are not in partial
         overlap with same labels. (i.e. Absolute misses)
        """
          
        # loop through ref and hyp lists to update class variables
        # 
        for i in range(len(ref)):
            if rflags[i]:
                self.mis_d[ref[i][2]] += 1

        for i in range(len(hyp)):
            if hflags[i]:
                self.fal_d[hyp[i][2]] += 1

        # exit gracefully
        #
    #
    # end of method

    def ovlp_ref_seqs(self, ref, hyp, rind, hind,
                          refflag, hypflag, tgt):
        """
        method: ovlp_ref_seqs
        
        arguments:
         ref: reference label information as a list
         hyp: hypothesis label information as a list
         rind: ref index where ovlp is detected
         hind: hyp index where ovlp is detected
         refflag: reference flags indicating the processed labels
         hypflag: hypothesis flags indicating the processed labels
         tgt: label name for which ovlp is detected
        
        return:
         p_hit: detected partial hits
         p_miss: detected partial miss
         p_fa: detected partial FAs

        description: 
         This method calculates the HMF for overlapped events where
         hypothesis event stop time exceeds the reference event
         stop time.
        """

        # define variables
        #
        p_miss = float(0)

        # calculate the parameters for the current event
        #
        p_hit, p_fa = self.calc_hf(ref[rind], hyp[hind])
        p_miss += float(1) - p_hit
        
        # update flags for already detected events
        #
        hypflag[hind] = False
        refflag[rind] = False

        # update the index since there could be multiple ref events
        # overlapped with hyp event
        #
        #  <-->    <-->  <-->
        # <--------------------->
        #
        rind += 1
        
        # look for more ref events overlapping with hyp event
        #
        for i in range(rind, len(ref)):
            
            # update misses according to the TAES score definition
            #
            if ref[i][2] == hyp[hind][2] and \
               self.anyovlp(ref[i], hyp[hind]):

                # update the flags for processed events
                #
                refflag[i] = False
                p_miss += 1

            # move to next event index
            #
            i += 1

        # exit gracefully
        #
        return p_hit, p_miss, p_fa
    #
    # end of method
 
    def ovlp_hyp_seqs(self, ref, hyp, rind, hind,
                          refflag, hypflag, tgt_a):
        """
        method: ovlp_hyp_seqs
        
        arguments:
         ref: reference label information as a list
         hyp: hypothesis label information as a list
         rind: ref index where ovlp is detected
         hind: hyp index where ovlp is detected
         refflag: reference flags indicating the processed labels
         hypflag: hypothesis flags indicating the processed labels
         tgt_a: label name for which ovlp is detected
        
        return:
         p_hit: detected partial hits
         p_miss: detected partial miss
         p_fa: detected partial FAs

        description: 
         This method calculates the HMF for overlapped events where
         reference event stop time exceeds the hypothesis event
         stop time.
        """
        
        # define variables
        #
        p_miss = float(0)

        # calculate the parameters for the current event
        #
        p_hit, p_fa = self.calc_hf(ref[rind], hyp[hind])
        p_miss += float(1) - p_hit        

        # update flags for already detected events
        #
        refflag[rind] = False
        hypflag[hind] = False

        # update the index since there could be multiple hyp events
        # overlapped with hyp event
        #
        #  <----------------------->
        #   <---->  <-->   <-->
        #
        hind += 1
        
        # look for hyp events overlapping with hyp event
        #
        for i in range(hind, len(hyp)):
            
            # update HMF according to the TAES score definition
            #
            if hyp[i][2] == ref[rind][2] and \
               self.anyovlp(ref[rind], hyp[i]):

                # update the flags for processed events
                #
                hypflag[i] = False

                ovlp_hit, ovlp_fa \
                    = self.calc_hf(ref[rind], hyp[i])

                p_hit += ovlp_hit
                p_miss -= ovlp_hit
                p_fa += ovlp_fa

            # move to the next event index
            #
            i += 1

        # return gracefully
        #
        return p_hit, p_miss, p_fa
    # 
    # end of method

    def compute_partial(self, ref, hyp, rind, hind, \
                        rflags, hflags, tgt_event):
        """
        method: compute_partial
        
        arguments:
         start_r: start time of ref event
         stop_r: stop time of ref event
         start_h: start time of hyp event
         stop_h: stop time of hyp event
         flag: flag that suggests that event has previously used
         tstop_prev: previous stop time of a recent class
        
        return:
         hit: calculated fractional number of hits
         miss: calculated fractional number of misses
         fa: calculated fractional number of false alarms

        description: 
         This method calculates hits, misses and false alarms
         for detected hyp events by comparing it with duration
         of reference/hypothesis events and computing the amount
         of overlap between the two.
        """

        # check whether current reference event has any overlap
        # with the hyp event
        if not self.anyovlp(ref[rind], hyp[hind]):
            return (float(0), float(0), float(0))

        # check whether detected event stop time exceed the 
        # reference stop time.
        #
        elif float(hyp[hind][1]) >= float(ref[rind][1]):

            #   <---->
            #     <---->
            #
            #   <---->
            # <-------->
            #            
            # check whether multiple reference events are 
            # overlapped with hypothesis event
            #
            #  <-->    <-->  <-->
            # <--------------------->
            #
            p_hit, p_mis, p_fal \
                = self.ovlp_ref_seqs(ref, hyp, rind, hind, 
                                      rflags, hflags, tgt_event)

        # check whether reference event stop time exceed the 
        # detected stop time.
        #
        elif float(ref[rind][1]) > float(hyp[hind][1]):

            #   <------>
            # <----->
            #
            #   <------>
            #     <-->
            #
            # check whether multiple hypothesis events are 
            # overlapped with reference event
            #
            #  <----------------------->
            #   <---->  <-->   <-->
            #
            p_hit, p_mis, p_fal \
                = self.ovlp_hyp_seqs(ref, hyp, rind, hind,
                                     rflags, hflags, tgt_event)

        # return gracefully
        #
        return (p_hit, p_mis, p_fal)
    #
    # end of method

    def anyovlp(self, ref, hyp):
        """
        method: anyovlp
        
        arguments:
         ref: reference event
         hyp: hypothesis event
        
        return:
         boolean: True/False

        description: 
         This method looks for any sort of overlap between 
         two events passed as an argument and return a boolean
         value indicating the status.
        """
        
        # create set for the ref/hyp events
        #
        refset = set(range(int(ref[0]), int(ref[1]) + 1))
        hypset = set(range(int(hyp[0]), int(hyp[1]) + 1))
            
        if len(refset.intersection(hypset)) != 0:
            return True

        # return gracefully
        #
        return False
    #
    # end of method

    def calc_hf(self, ref, hyp):
        """
        method: calc_hf
        
        arguments:
         ref: reference event
         hyp: hypothesis event
        
        return:
         hit: detected hits
         fa: detected False Positives 

        description: 
         This method calculates hits and false alarms between the 
         events passed as an argument.
        """

        ## collect start and stop times from input arg events
        #
        start_r_a = ref[0]
        stop_r_a = ref[1]
        start_h_a = hyp[0]
        stop_h_a = hyp[1]

        # initialize local variables
        #
        ref_dur = stop_r_a - start_r_a
        hyp_dur = stop_h_a - start_h_a
        hit = float(0)
        fa = float(0)

        #----------------------------------------------------------------------
        # deal explicitly with the four types of overlaps that can occur
        #----------------------------------------------------------------------

        # (1) for pre-prediction event
        #     ref:         <--------------------->
        #     hyp:   <---------------->
        #
        if start_h_a <= start_r_a and stop_h_a <= stop_r_a:
            hit = (stop_h_a - start_r_a) / ref_dur
            if ((start_r_a - start_h_a) / ref_dur) < 1.0:
                fa = ((start_r_a - start_h_a) / ref_dur)
            else:
                fa = float(1)

        # (2) for post-prediction event
        #     ref:         <--------------------->
        #     hyp:                  <-------------------->
        #
        elif start_h_a >= start_r_a and stop_h_a >= stop_r_a:

            hit = (stop_r_a - start_h_a) / ref_dur                       
            if ((stop_h_a - stop_r_a) / ref_dur) < 1.0:
                fa = ((stop_h_a - stop_r_a) / ref_dur)
            else:
                fa = float(1)


        # (3) for over-prediction event
        #     ref:              <------->
        #     hyp:        <------------------->
        #
        elif start_h_a < start_r_a and stop_h_a > stop_r_a:
            
            hit = 1.0
            fa = ((stop_h_a - stop_r_a) + (start_r_a - start_h_a)) /\
                 ref_dur
            if fa > 1.0:
                fa = float(1)

        # (4) for under-prediction event
        #     ref:        <--------------------->
        #     hyp:            <------>
        #
        else:
            hit = (stop_h_a - start_h_a) / ref_dur

        # exit gracefully
        #
        return (hit, fa)
    #
    # end of method

    def get_events(self, start_a, stop_a, events_a, flags_a):
        """
        method: get_events
        
        arguments:
         start: start time
         stop: stop_time
         events: a list of events
         flags: event flags
        
        return:
         labels: the labels that overlap with the start and stop time
         starts: a list of start times
         stops: a list of stop times

        description: 
         this method returns a list of events that fall within a specified
         range of time of main event list (i.e. here events_a)
        """

        # declare output variables
        #
        labels = []
        starts = []
        stops = []
        flags = []
        ind = []

        # loop over all events
        #
        for i in range(len(events_a)):

            # if the event overlaps partially with the interval,
            # it is a match. this means:
            #              start               stop
            #   |------------|<---------------->|-------------|
            #          |---------- event -----|
            #
            if (events_a[i][1] > start_a) and (events_a[i][0] < stop_a):
                starts.append(events_a[i][0])
                stops.append(events_a[i][1])
                labels.append(events_a[i][2])
                ind.append(i)
                flags.append(flags_a[i])

        # exit gracefully
        #
        return [labels, starts, stops]
    #
    # end of method

    def compute_performance(self):
        """
        method: compute_performance
        
        arguments:
         none

        returns: 
         a boolean value indicating status

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
                  (__FILE__, ndt.__LINE__, NedcTAES.__CLASS_NAME__,
                   ndt.__NAME__))


        # check for a zero count
        #
        num_total_ref_events = sum(self.tgt_d.values())
        if num_total_ref_events == 0:            
            print("Error: %s (line: %s) %s::%s: %s (%d)" %
                  (__FILE__, ndt.__LINE__, NedcTAES.__CLASS_NAME__,
                   ndt.__NAME__, "number of events is zero",
                   num_total_ref_events))
            return None

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
        # loop over all labels
        #
        for key1 in self.hit_d:

            #------------------------------------------------------------------
            # (2.2) The overlap algorithm outputs hits, misses and false alarms
            #       directly. These must be converted to (tp, tn, fp, fn).
            #
            # compute true positives (tp)
            #
            self.tp_d[key1] = self.hit_d[key1]

            # compute true negatives (tn):
            #  sum the hits that are not the current label
            #
            tn_sum = int(0)
            for key2 in self.hit_d:
                if key1 != key2:
                    tn_sum += self.hit_d[key2]
            self.tn_d[key1] = tn_sum

            # compute false positives (fpos): copy false alarms
            #
            self.fp_d[key1] = self.fal_d[key1]

            # compute false negatives (fn): copy misses
            #
            self.fn_d[key1] = self.mis_d[key1]

            # check the health of the confusion matrix
            #
            tp = self.tp_d[key1]
            fpos = self.fp_d[key1]
            tn = self.tn_d[key1]
            fn = self.fn_d[key1]
            tdur = self.total_dur_d

            if ((tp + fn) == 0) or ((fpos + tn) == 0) or \
               ((tp + fpos) == 0) or ((fn + tn) == 0):
                print("Warning: %s (line: %s) %s::%s: %s (%d %d %d %d)" % 
                    (__FILE__, ndt.__LINE__, NedcTAES.__CLASS_NAME__,
                     ndt.__NAME__, "divide by zero", tp, fpos, tn, fn))
            elif (round(tdur, ndt.MAX_PRECISION) == 0):
                print("Warning: %s (line: %s) %s::%s: %s (%f)" % 
                    (__FILE__, ndt.__LINE__, NedcTAES.__CLASS_NAME__,
                     ndt.__NAME__, "duration is zero", tdur))

            # (2.3) compute derived measures
            #
            if (tp + fn) != 0:
                self.tpr_d[key1] = float(self.tp_d[key1]) / float(tp + fn)
            else:
                self.tpr_d[key1] = float(0)

            if (tn + fpos) != 0:
                self.tnr_d[key1] = float(self.tn_d[key1]) / float(tn + fpos)
            else:
                self.tnr_d[key1] = float(0)

            if (tp + fpos) != 0:
                self.ppv_d[key1] = float(self.tp_d[key1]) / float(tp + fpos)
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

            if (tp + tn + fpos + fn) != 0:
                self.acc_d[key1] = float(self.tp_d[key1] + self.tn_d[key1]) / \
                                   (tp + tn + fpos + fn)
                self.prv_d[key1] = float(self.tp_d[key1] + self.fn_d[key1]) / \
                                   (tp + tn + fpos + fn)
            else:
                self.acc_d[key1] = float(0)
                self.prv_d[key1] = float(0)

            self.msr_d[key1] = 1 - self.acc_d[key1]

            # compute the f1 score:
            #  this has to be done after sensitivity and prec are computed
            #
            f1s_denom = float(self.ppv_d[key1] + self.tpr_d[key1])
            if round(f1s_denom, ndt.MAX_PRECISION) == 0:
                print("Warning: %s (line %s) %s::%s %s (%s)" %
                (__FILE__, ndt.__LINE__, ndt.__NAME__,
                 ndt.__NAME__, "f ratio divide by zero", key1)) 
                self.f1s_d[key1] = float(0)
            else:
                self.f1s_d[key1] = 2.0 * self.ppv_d[key1] * \
                    self.tpr_d[key1] / f1s_denom

            # compute the mcc score:
            #  this has to be done after sensitivity and prec are computed
            #
            mcc_denom = (tp + fpos) * (tp + fn) * (tn + fpos) * (tn + fn)
            mcc_num = (tp * tn) - (fpos * fn)
            if round(mcc_denom, ndt.MAX_PRECISION) == 0:
                print("Warning: %s (line: %s) %s::%s: %s (%s)" % 
                    (__FILE__, ndt.__LINE__, NedcTAES.__CLASS_NAME__,
                     ndt.__NAME__, "mcc ratio divide by zero", key1))
                self.mcc_d[key1] = float(0)
            else:
                self.mcc_d[key1] = mcc_num / math.sqrt(mcc_denom)

            # compute the false alarm rate
            #
            if (round(tdur, ndt.MAX_PRECISION) == 0):
                print("Warning: %s (line: %s) %s::%s: %s (%s)" % 
                    (__FILE__, ndt.__LINE__, NedcTAES.__CLASS_NAME__,
                   ndt.__NAME__, "zero duration", key1))
                self.flr_d[key1] = float(0)
            else:
                self.flr_d[key1] = float(fpos) / tdur * (60 * 60 * 24)
        
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
                (__FILE__, ndt.__LINE__, NedcTAES.__CLASS_NAME__,
                   ndt.__NAME__, "f ratio divide by zero", "summary"))
            self.sum_f1s_d = float(0)
        else:
            self.sum_f1s_d = 2.0 * self.sum_ppv_d * self.sum_tpr_d / f1s_denom

        # compute the mcc score:
        #  this has to be done after sensitivity and prec are computed
        #
        sum_mcc_denom = (self.sum_tp_d + self.sum_fp_d) * \
            (self.sum_tp_d + self.sum_fn_d) * \
            (self.sum_tn_d + self.sum_fp_d) * (self.sum_tn_d + self.sum_fn_d)
        sum_mcc_num = (self.sum_tp_d * self.sum_tn_d) - \
            (self.sum_fp_d * self.sum_fn_d)
        if round(sum_mcc_denom, ndt.MAX_PRECISION) == 0:
            print("Warning: %s (line: %s) %s::%s: %s (%s)" % 
                   (__FILE__, ndt.__LINE__, NedcTAES.__CLASS_NAME__,
                    ndt.__NAME__, "mcc ratio divide by zero", "summary"))
            self.sum_mcc_d = float(0)
        else:
            self.sum_mcc_d = sum_mcc_num / math.sqrt(sum_mcc_denom)

        # compute the false alarm rate
        #
        if round(self.total_dur_d, ndt.MAX_PRECISION) == 0:
            print("Warning: %s (line: %s) %s::%s: %s (%s)" % 
                   (__FILE__, ndt.__LINE__, NedcTAES.__CLASS_NAME__,
                    ndt.__NAME__, "zero duration", "summary"))
            self.sum_flr_d = float(0)
        else:
            self.sum_flr_d = float(self.sum_fp_d) / self.total_dur_d * \
                             (60 * 60 * 24)

        # exit gracefully
        #
        return True
    #
    # end of method

    def display_results(self, fp):
        """
        method: display_results
        
        arguments:
         fp: output file pointer

        returns: 
         a boolean value indicating status

        description: 
         This method displays all the results in output report.
        """

        # display informational message                                        
        #
        if self.dbgl_d > ndt.BRIEF:
            print("%s (line: %s) %s::%s: displaying results to output file" %
                  (__FILE__, ndt.__LINE__, NedcTAES.__CLASS_NAME__,
                   ndt.__NAME__))
            
        # write per label header
        #
        fp.write(("Per Label Results:" + nft.DELIM_NEWLINE).upper())
        fp.write(nft.DELIM_NEWLINE)

        # per label results: loop over all classes
        #
        for key in self.hit_d:
            fp.write((" Label: %s" % key + nft.DELIM_NEWLINE).upper())
            fp.write(nft.DELIM_NEWLINE)

            fp.write("   %30s: %12.2f   <**" %
                     ("Targets", float(self.tgt_d[key])) + nft.DELIM_NEWLINE)
            fp.write("   %30s: %12.2f   <**" %
                     ("Hits", float(self.hit_d[key])) + nft.DELIM_NEWLINE)
            fp.write("   %30s: %12.2f   <**" %
                     ("Misses", float(self.mis_d[key])) + nft.DELIM_NEWLINE)
            fp.write("   %30s: %12.2f   <**" %
                     ("False Alarms", float(self.fal_d[key])) +
                     nft.DELIM_NEWLINE)
            fp.write("   %30s: %12.2f" %
                     ("Insertions", float(self.ins_d[key])) +
                     nft.DELIM_NEWLINE)
            fp.write("   %30s: %12.2f" %
                     ("Deletions", float(self.del_d[key])) + nft.DELIM_NEWLINE)
            fp.write(nft.DELIM_NEWLINE)

            fp.write("   %30s: %12.2f" %
                     ("True Positives (TP)", float(self.tp_d[key])) +
                     nft.DELIM_NEWLINE)
            fp.write("   %30s: %12.2f" %
                     ("True Negatives (TN)", float(self.tn_d[key])) +
                     nft.DELIM_NEWLINE)
            fp.write("   %30s: %12.2f" %
                     ("False Positives (FP)", float(self.fp_d[key])) +
                     nft.DELIM_NEWLINE)
            fp.write("   %30s: %12.2f" %
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
                     ("Negative Pred. Value (NPV)", self.npv_d[key] * 100.0) +
                     nft.DELIM_NEWLINE)
            fp.write("   %30s: %12.4f%%" %
                       ("Miss Rate (FNR)", self.fnr_d[key] * 100.0) +
                     nft.DELIM_NEWLINE)
            fp.write("   %30s: %12.4f%%" %
                     ("False Positive Rate (FPR)", self.fpr_d[key] * 100.0) +
                     nft.DELIM_NEWLINE)
            fp.write("   %30s: %12.4f%%" %
                     ("False Discovery Rate (FDR)", self.fdr_d[key] * 100.0) +
                     nft.DELIM_NEWLINE)
            fp.write("   %30s: %12.4f%%" %
                       ("False Omission Rate (FOR)", self.for_d[key] * 100.0) +
                     nft.DELIM_NEWLINE)
            fp.write("   %30s: %12.4f%%" %
                     ("Accuracy", self.acc_d[key] * 100.0) + nft.DELIM_NEWLINE)
            fp.write("   %30s: %12.4f%%" %
                     ("Misclassification Rate", self.msr_d[key] * 100.0) +
                     nft.DELIM_NEWLINE)
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
        fp.write("   %30s: %12.2f   <**" %
                 ("Total", float(self.sum_tgt_d)) + nft.DELIM_NEWLINE)
        fp.write("   %30s: %12.2f   <**" %
                 ("Hits", float(self.sum_hit_d)) + nft.DELIM_NEWLINE)
        fp.write("   %30s: %12.2f   <**" %
                 ("Misses", float(self.sum_mis_d)) + nft.DELIM_NEWLINE)
        fp.write("   %30s: %12.2f   <**" %
                 ("False Alarms", float(self.sum_fal_d)) + nft.DELIM_NEWLINE)
        fp.write("   %30s: %12.2f" %
                 ("Insertions", float(self.sum_ins_d)) + nft.DELIM_NEWLINE)
        fp.write("   %30s: %12.2f" %
                 ("Deletions", float(self.sum_del_d)) + nft.DELIM_NEWLINE)
        fp.write(nft.DELIM_NEWLINE)

        fp.write("   %30s: %12.2f" %
                 ("True Positives(TP)", float(self.sum_tp_d)) +
                 nft.DELIM_NEWLINE)
        fp.write("   %30s: %12.2f" %
                 ("False Positives (FP)", float(self.sum_fp_d)) +
                 nft.DELIM_NEWLINE)
        fp.write(nft.DELIM_NEWLINE)

        fp.write("   %30s: %12.4f%%" %
                 ("Sensitivity (TPR, Recall)", self.sum_tpr_d * 100.0) +
                 nft.DELIM_NEWLINE)
        fp.write("   %30s: %12.4f%%" %
                 ("Miss Rate (FNR)", self.sum_fnr_d * 100.0) +
                 nft.DELIM_NEWLINE)
        fp.write("   %30s: %12.4f%%" %
                 ("Accuracy", self.sum_acc_d * 100.0) + nft.DELIM_NEWLINE)
        fp.write("   %30s: %12.4f%%" %
                 ("Misclassification Rate", self.sum_msr_d * 100.0) +
                 nft.DELIM_NEWLINE)
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

        returns: 
         a boolean value indicating status

        description: 
         This method computes a confusion matrix for an roc/det curve.
        """

    # display informational message
    #
        if self.dbgl_d > ndt.BRIEF:
            print("%s (line: %s) %s::%s: computing an roc/det curve" %
                  (__FILE__, ndt.__LINE__, NedcTAES.__CLASS_NAME__,
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
            refo, hypo, hit, mis, fal = self.compute(ann_ref, ann_hyp)
            if refo == None:
                print("Error: %s (line: %s) %s::%s %s" %
                      (__FILE__, ndt.__LINE__, NedcTAES.__CLASS_NAME__,
                       ndt.__NAME__, "error computing confusions"))
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

        returns: 
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
                  (__FILE__, ndt.__LINE__, NedcTAES.__CLASS_NAME__,
                   ndt.__NAME__))
            
        # check for a zero count
        #
        num_total_ref_events = sum(self.tgt_d.values())
        if num_total_ref_events == 0:
            print("%Error: %s (line: %s) %s::%s: %s (%d)" % 
                (__FILE__, ndt.__LINE__, NedcTAES.__CLASS_NAME__,
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
        fpos = self.fp_d[key]
        tn = self.tn_d[key]
        fn = self.fn_d[key]
        tdur = self.total_dur_d

        # (2.3) compute derived measures
        #
        if (tp + fn) != 0:
            self.tpr_d[key] = float(self.tp_d[key]) / float(tp + fn)
        else:
            self.tpr_d[key] = float(0)

        if (tn + fpos) != 0:
            self.tnr_d[key] = float(self.tn_d[key]) / float(tn + fpos)
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

        returns: 
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

        returns: 
         a boolean value indicating status

        description: 
         This method simply returns the quanities needed for a det curve:
         false negative rate (fnr) as a function of the false positive rate (fpr).
        """

        return self.fpr_d[key], self.fnr_d[key]

# end of file
#
