#!/usr/bin/env python
#
# file: $(NEDC_NFC)/util/python/nedc_eeg_eval/nedc_eeg_eval.py
#
# revision history:
#
# 20241003 (JP): added a timestamp log message
# 20240515 (BL): refactored code to match new naming, removed comp version
# 20220513 (JP): refactored the code to use the new ann tools library
# 20220418 (JP): updated I/O to support csv and xml using the new ann tools
# 20210202 (JP): obsoleted the NIST scoring software
# 20200730 (LV): merged research and competition versions, added NIST option
# 20170730 (JP): moved parameter file constants out of this driver
# 20170728 (JP): added error checking for duration
# 20170716 (JP): upgraded to using the new annotation tools.
# 20170527 (JP): added epoch-based scoring
# 20150520 (SZ): modularized the code
# 20170510 (VS): encapsulated the three scoring metrics 
# 20161230 (SL): revision for standards
# 20150619 (SZ): initial version
#------------------------------------------------------------------------------

# import system modules
#
import os
import sys
import time

# import NEDC support modules
#
import nedc_cmdl_parser as ncp
import nedc_debug_tools as ndt
import nedc_file_tools as nft

# import NEDC scoring modules
#
import nedc_eeg_eval_common as nec
import nedc_eeg_eval_dpalign as ndpalign
import nedc_eeg_eval_epoch as nepoch
import nedc_eeg_eval_ovlp as novlp
import nedc_eeg_eval_taes as ntaes
import nedc_eeg_eval_ira as nira

#------------------------------------------------------------------------------
#
# global variables are listed here
#
#------------------------------------------------------------------------------

# set the filename using basename                                              
#                                                                              
__FILE__ = os.path.basename(__file__)

# define the help file and usage message:
#  since this is released software, we use an src directory
#
HELP_FILE = "$NEDC_NFC/docs/help/nedc_eeg_eval.help"
USAGE_FILE = "$NEDC_NFC/docs/usage/nedc_eeg_eval.usage"

# define the program options:                                                  
#  note that you cannot separate them by spaces                                
#
ARG_ODIR = "--odir"
ARG_ABRV_ODIR = "-o"

ARG_PARM = "--parameters"
ARG_ABRV_PARM = "-p"


# define default values for arguments:
#  note we assume the parameter file is in the same
#  directory as the source code.
#
DEF_PFILE = "$NEDC_NFC/docs/params/nedc_eeg_eval_params_v00.toml"
DEF_ODIR = "./output"

# define the required number of arguments
#
NUM_ARGS = 2

# define the names of the output files
#
NEDC_SUMMARY_FILE = "summary.txt"
NEDC_DPALIGN_FILE = "summary_dpalign.txt"
NEDC_EPOCH_FILE = "summary_epoch.txt"
NEDC_OVLP_FILE = "summary_ovlp.txt"
NEDC_TAES_FILE = "summary_taes.txt"
NEDC_IRA_FILE = "summary_ira.txt"

# define formatting constants
#
NEDC_EVAL_SEP = nft.DELIM_EQUAL * 78
NEDC_VERSION = "v6.0.0"

# define class definitions:
#  this can be overridden by using a parameter file. multi-class
#  scoring can be done by making appropriate changes to the
#  parameter file.
#
SEIZ = "SEIZ"
BCKG = "BCKG"
CLASSES = [SEIZ, BCKG]

#------------------------------------------------------------------------------
#
# functions are listed here
#
#------------------------------------------------------------------------------

# declare a global debug object so we can use it in functions
#
dbgl = ndt.Dbgl()

# function: main
#
def main(argv):

    # create a command line parser                                        
    #                                                                          
    cmdl = ncp.Cmdl(USAGE_FILE, HELP_FILE)

    # define the command line arguments
    #
    cmdl.add_argument("files", type = str, nargs = '*')
    cmdl.add_argument(ARG_ABRV_ODIR, ARG_ODIR, type = str)
    cmdl.add_argument(ARG_ABRV_PARM, ARG_PARM, type = str)
    
    # parse the command line
    #
    args = cmdl.parse_args()
    
    # check if the proper number of lists has been provided
    #
    if len(args.files) != NUM_ARGS:
        cmdl.print_usage()
        sys.exit(os.EX_SOFTWARE)
            
    # set argument values
    #
    odir = nft.get_fullpath(DEF_ODIR)
    if args.odir is not None:
        odir = args.odir

    if args.parameters is not None:
        pfile = args.parameters

    if args.parameters is None:
        pfile = nft.get_fullpath(DEF_PFILE)
    
    # load parameters
    #
    nedc_dpalign = nft.load_parameters(pfile, ndpalign.NEDC_DPALIGN)
    nedc_epoch = nft.load_parameters(pfile, nepoch.NEDC_EPOCH)
    nedc_ovlp = nft.load_parameters(pfile, novlp.NEDC_OVLP)
    nedc_taes = nft.load_parameters(pfile, ntaes.NEDC_TAES)
    nedc_ira = nft.load_parameters(pfile, nira.NEDC_IRA)

    # load the scoring map
    #
    tmpmap = nft.load_parameters(pfile, nec.PARAM_MAP)
    if (tmpmap == None):
        print("Error: %s (line: %s) %s: %s (%s)" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__,
               "error loading the scoring map",  pfile))
        sys.exit(os.EX_SOFTWARE)

    # convert the map
    #
    scmap = nft.generate_map(tmpmap)
    if (scmap == None):
        print("Error: %s (line: %s) %s: error converting the map" % 
              (__FILE__, ndt.__LINE__, ndt.__NAME__))
        sys.exit(os.EX_SOFTWARE)

    if dbgl > ndt.BRIEF:
        print("%s (line: %s) %s: scoring map = " %
              (__FILE__, ndt.__LINE__, ndt.__NAME__), scmap)

    # set the input lists
    #
    fname_ref = args.files[0]
    fname_hyp = args.files[1]

    # parse the ref and hyp file lists 
    #
    reflist = nft.get_flist(fname_ref)
    hyplist = nft.get_flist(fname_hyp)

    # ensure file lists are valid
    #
    if None in reflist or len(reflist) == 0:
        print("Error: %s (line: %s) %s: invalid ref list" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__,
               ))
        sys.exit(os.EX_SOFTWARE)

    # ensure file lists are valid
    #
    if None in hyplist or len(hyplist) == 0:
        print("Error: %s (line: %s) %s: invalid hyp list" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__,
               ))
        sys.exit(os.EX_SOFTWARE)

    # fetch absolute paths for ref and hyp lists
    #
    reflist = [nft.get_fullpath(ref_file) for ref_file in reflist]
    hyplist = [nft.get_fullpath(hyp_file) for hyp_file in hyplist]

    if len(reflist) != len(hyplist):
        print("Error: %s (line: %s) %s: %s (ref: %s, hyp: %s)" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__,
               "ref and hyp list lengths dont match",
               len(reflist), len(hyplist)))
        sys.exit(os.EX_SOFTWARE)
        
    if dbgl > ndt.NONE:
        print("%s (line: %s) %s: ref list = " %
              (__FILE__, ndt.__LINE__, ndt.__NAME__), reflist)
        print("%s (line: %s) %s: hyp list = " %
              (__FILE__, ndt.__LINE__, ndt.__NAME__), hyplist)

    ref_anns = nec.parse_files(reflist, scmap)
    hyp_anns = nec.parse_files(hyplist, scmap)

    # ensure annotations were parsed correctly
    #
    if ref_anns == False:
        print("Error: %s (line: %s) %s: ref annotations failed to load" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__,
               ))
        sys.exit(os.EX_SOFTWARE)
    if hyp_anns == False:
        print("Error: %s (line: %s) %s: hyp annotations failed to load" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__,
               ))
        sys.exit(os.EX_SOFTWARE)

    
    if dbgl > ndt.NONE:
        print("%s (line: %s) %s: ref_anns = " %
              (__FILE__, ndt.__LINE__, ndt.__NAME__), ref_anns)
        print("%s (line: %s) %s: hyp_anns = " %
              (__FILE__, ndt.__LINE__, ndt.__NAME__), hyp_anns)
                
    # display debug information
    #
    if dbgl > ndt.NONE:
        print("command line arguments:")
        print(" output directory = %s" % (odir))
        print(" competition = %d" % (bool(args.competition)))
        print(" ref file  = %s" % (args.files[0]))
        print(" hyp file = %s" % (args.files[1]))
        print(" ref_anns = ", ref_anns)
        print(" hyp_anns = ", hyp_anns)
        print("")

    # check for mismatched file lists:
    #  note that we do this here so it is done only once, rather than
    #  in each scoring method
    #
    if (ref_anns == None) or (hyp_anns == None):
        print("Error: %s (line: %s) %s: %s (ref: %s) and (hyp: %s)" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__,
               "error loading filelists", fname_ref, fname_hyp))
        sys.exit(os.EX_SOFTWARE)
    elif len(ref_anns) != len(hyp_anns):
        print("Error: %s (line: %s) %s: (ref: %d) and (hyp: %d) %s" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__,
               len(ref_anns), len(hyp_anns), "have different lengths"))
        sys.exit(os.EX_SOFTWARE)

    # create the output directory and the output summary file
    #               
    print(" ... creating the output directory ...")
    if nft.make_dir(odir) == False:
        print("Error: %s (line: %s) %s: error creating output directory (%s)" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__, odir))
        sys.exit(os.EX_SOFTWARE)

    fname = nft.concat_names(odir, NEDC_SUMMARY_FILE)
    fp = nft.make_fp(fname)

    # print the log message
    #
    fp.write("%s" % (dbgl.log(__file__, NEDC_VERSION) + nft.DELIM_NEWLINE))

    # print the header of the summary file showing the relevant information
    #
    fp.write("%s" % (NEDC_EVAL_SEP + nft.DELIM_NEWLINE))
    fp.write("File: %s" % (fname + nft.DELIM_NEWLINE) )
    fp.write("Data:" + nft.DELIM_NEWLINE)
    fp.write(" Ref: %s" % (fname_ref + nft.DELIM_NEWLINE))
    fp.write(" Hyp: %s" % (fname_hyp + nft.DELIM_NEWLINE + nft.DELIM_NEWLINE))

    # execute dp alignment scoring
    #
    print(" ... executing NEDC DP Alignment scoring ...")
    fp.write("%s\n%s (%s):\n\n" % 
             (NEDC_EVAL_SEP,
              ("NEDC DP Alignment Scoring Summary").upper(),
              NEDC_VERSION))
    fname = nft.concat_names(odir, NEDC_DPALIGN_FILE)
    status = ndpalign.run(ref_anns, hyp_anns, scmap, nedc_dpalign,
                          odir, fname, fp)
    if status == False:
        print("Error: %s (line: %s) %s: error in DPALIGN scoring" % 
              (__FILE__, ndt.__LINE__, ndt.__NAME__))
        sys.exit(os.EX_SOFTWARE)
    
    # execute NEDC epoch-based scoring
    #
    print(" ... executing NEDC Epoch scoring ...")
    fp.write("%s\n%s (%s):\n\n" % 
             (NEDC_EVAL_SEP,
              ("NEDC Epoch Scoring Summary").upper(),
              NEDC_VERSION))
    fname = nft.concat_names(odir, NEDC_EPOCH_FILE)
    status = nepoch.run(ref_anns, hyp_anns, scmap, nedc_epoch,
                        odir, fname, fp)
    if status == False:
        print("Error: %s (line: %s) %s: error in EPOCH scoring" % 
              (__FILE__, ndt.__LINE__, ndt.__NAME__))
        sys.exit(os.EX_SOFTWARE)

    # execute overlap scoring
    #
    print(" ... executing NEDC Overlap scoring ...")
    fp.write("%s\n%s (%s):\n\n" % 
             (NEDC_EVAL_SEP,
              ("NEDC Overlap Scoring Summary").upper(),
              NEDC_VERSION))
    fname = nft.concat_names(odir, NEDC_OVLP_FILE)
    status = novlp.run(ref_anns, hyp_anns, scmap, nedc_ovlp,
                       odir, fname, fp)
    if status == False:
        print("Error: %s (line: %s) %s: error in OVLP scoring" % 
              (__FILE__, ndt.__LINE__, ndt.__NAME__))
        sys.exit(os.EX_SOFTWARE)
        
    # execute time-aligned event scoring
    #
    print(" ... executing NEDC Time-Aligned Event scoring ...")
    fp.write("%s\n%s (%s):\n\n" % 
             (NEDC_EVAL_SEP,
              ("NEDC TAES Scoring Summary").upper(),
              NEDC_VERSION))
    fname = nft.concat_names(odir, NEDC_TAES_FILE)
    status = ntaes.run(ref_anns, hyp_anns, scmap, nedc_taes,
                       odir, fname, fp)
    if status == False:
        print("Error: %s (line: %s) %s: error in TAES scoring" % 
              (__FILE__, ndt.__LINE__, ndt.__NAME__))
        sys.exit(os.EX_SOFTWARE)

    # execute ira scoring                  
    #                                                                       
    print(" ... executing NEDC IRA scoring ...")
    fp.write("%s\n%s (%s):\n\n" % 
             (NEDC_EVAL_SEP,
              ("NEDC Inter-Rater Agreement Summary").upper(),
              NEDC_VERSION))
    fname = nft.concat_names(odir, NEDC_IRA_FILE)
    status = nira.run(ref_anns, hyp_anns, scmap, nedc_ira, odir, fp)
    if status == False:
        print("Error: %s (line: %s) %s: error in IRA scoring" %
              (__FILE__, ndt.__LINE__, ndt.__NAME__))
        sys.exit(os.EX_SOFTWARE)

    # print the final message to the summary file, close it and exit
    #
    print(" ... done ...")
    fp.write("%s\nNEDC EEG Eval Successfully Completed on %s\n%s\n" \
             % (NEDC_EVAL_SEP, time.strftime("%c"), NEDC_EVAL_SEP))
    
    # close the output file
    #
    fp.close()

    # end of main
    #
    return True
    
#
# end of main

# begin gracefully
#
if __name__ == "__main__":
    main(sys.argv[0:])

#                                                                              
# end of file
