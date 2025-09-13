File: $NEDC_NFC/AAREADME.txt
Package: nedc_eeg_eval
Version: 6.0.0

-------------------------------------------------------------------------------
Change Log:

(20250807) (DH): updated for v6.0.0 release
(20240810) (JP): updated the tool for the new libraries
(20240528) (BL): removed the competition interface and changed name
(20220418) (JP): updated support for the ann tools library
(20200817) (LV): updated for new version of nedc_eeg_eval
(20200515) (JP): added check for duplicate and overlapping hypotheses
(20200417) (JP): made optional parameters work properly
(20200328) (JP): initial version
-------------------------------------------------------------------------------

-------------------------------------------------------------------------------
Summary:
-------------------------------------------------------------------------------

This package contains the standard version of our scoring
software. Starting with v5.0.0, we included support for csv and xml
files that contain annotation information. Note that starting with
v4.0.0, NIST integration was obsoleted as it became too difficult for
people to install and manage the NIST scoring software.

This software is designed to score system output from machine learning
systems that operate on sequential data. To learn more about the
theory behind how we score seizure detection systems, please refer to
this document:

 V. Shah, M. Golmohammadi, I. Obeid, and J. Picone, “Objective
 Evaluation Metrics for Automatic Classification of EEG Events,” in
 Signal Processing in Medicine and Biology: Emerging Trends in
 Research and Applications, 1st ed., I. Obeid, I. Selesnick, and
 J. Picone, Eds. New York City, New York, USA: Springer, 2021,
 pp. 1–26.
 URL: https://www.isip.piconepress.com/publications/unpublished/book_sections/2021/springer/metrics/

--------------------------------------------------------------------------------
INSTALLATION REQUIREMENTS
--------------------------------------------------------------------------------

Python code unfortunately often depends on a large number of add-ons, making
it very challenging to port code into new environments. This tool has been
tested extensively on Windows and Mac machines running Python v3.9.x.

Software tools required include:

 o Numpy (2.0.2): https://numpy.org/
 o SciPy (1.14.1): https://scipy.org/
 o lxml (5.3.0): https://lxml.de/
 o toml (0.10.2): https://pypi.org/project/toml/

There is a requirements.txt included in the release that helps you automate
the process of updating your environment.

C. USER'S GUIDE

C.1. WINDOWS USERS

For Window users, we recommend users install Anaconda in order to run
a bash emulator.

Through the Anaconda prompt, create a new environment and specify the proper
python version:

 $ conda create -n <my_environment_name> python=3.9

Install a bash emulator that will allow running the annotation tool:

 $ conda install m2-base

Install the required packages:

 $ conda install numpy
 $ conda install lxml
 $ conda install scipy
 $ conda install toml
 
Once the software has been installed, you need to do the following things if
you want to run this from any directory:

 - set the environment variable NEDC_NFC to the root directory
   of the installation:

   for WINDOWS CMD:
    $ set NEDC_NFC=<my_install_location>/nedc_eeg_eval/v6.0.0
   for WINDOWS POWERSHELL:
    $ $env:NEDC_NFC = "<my_install_location>/nedc_eeg_eval/v6.0.0"

 - put $NEDC_NFC\bin in your path:

   for WINDOWS CMD:
    $ set PATH=%NEDC_NFC%\bin;%PATH%
    $ set PATH=%NEDC_NFC%\lib;%PATH%

   for WINDOWS POWERSHELL:
    $ $env:PATH = "$env:NEDC_NFC\bin;$env:PATH"
    $ $env:PATH = "$env:NEDC_NFC\lib;$env:PATH"

Afterwards you must make the bin directory by changing your current working
directory to $NEDC_NFC/src, and then run the Makefile, i.e. "sh Makefile.sh".

You should be able to type:

 $ which nedc_eeg_eval
 
and see the command. Then you can simply type:

 $ nedc_eeg_eval

The easiest way to run this is to change your current working directory
to the root directory of the installation and execute the tool as follows:

 $ cd <my_install_location>
 $ ./bin/nedc_eeg_eval ./data/lists/ref.list ./data/lists/hyp.list

C.2. LINUX/MAC USERS

For Mac users, since Mac OS X 10.8 comes with Python 2.7, you may
need to utilize pip3 when attempting to install dependencies:

 pip3 install numpy
 pip3 install lxml
 pip3 install scipy
 pip3 install toml
 
Once the software has been installed, you need to do the following things if
you want to run this from any directory:

 - set the environment variable NEDC_NFC to the root directory
   of the installation:

   $ export NEDC_NFC='<my_install_location>/nedc_eeg_eval/v6.0.0'

 - put $NEDC_NFC/bin in your path:

   $ export PATH=$NEDC_NFC/bin:$PATH
   $ export PYTHONPATH=$NEDC_NFC/lib:$PYTHONPATH

Afterwards you must make the bin directory by changing your current working
directory to $NEDC_NFC/src, and then run sh on the Makefile, i.e. "sh Makefile.sh".

You should be able to type:

 $ which nedc_eeg_eval

and see the command. Then you can simply type:

 $ nedc_eeg_eval --help

------------------------------------------------------------------------------
Running NEDC EEG Eval:
------------------------------------------------------------------------------

The easiest way to run this is to change your current working directory
to the root directory of the installation and execute the tool as follows:

 cd <my_install_location>
 ./bin/nedc_eeg_eval ./data/lists/ref.list ./data/lists/hyp.list

The output scoring files will be located in a directory called output.

The file output/summary.txt contains an extremely detailed analysis of the
performance of your system. The output directory also contains per-file
output so you can better understand the performance on individual files.
All this is described in the above publication.

Other than a difference in some header information, these two files should
be identical. A typical output that you might see is:

 nedc_000_[1]: diff answers/summary.txt output/summary.txt 
 4,5c4,5
 <  File: answers/summary.txt
 <  Date: Mon Aug 17 13:14:48 2020
 ---
 >  File: output/summary.txt
 >  Date: Tue Aug 18 11:27:08 2020
 476c476
 < NEDC EEG Eval Successfully Completed on Mon Aug 17 13:14:49 2020
 ---
 > NEDC EEG Eval Successfully Completed on Tue Aug 18 11:27:13 2020

This means everything ran fine and the only differences are the date and
location of the file.

------------------------------------------------------------------------------
Input Files:
------------------------------------------------------------------------------

STANDARD VERSION:

 The file "ref.list" represents a list of reference annotation files. 
 The format for these files is straightforward:

 nedc_000_[1]: more data/ref/00000258_s001_t000.csv 
 # version = csv_v1.0.0
 # bname = 00000258_s001_t000
 # duration = 1750.0000 secs
 # map file: /data/isip/tools/master/nfc/lib/nedc_eas_default_montage.txt
 # annotation label file: /data/isip/tools/master/nfc/lib/default_map.txt
 #
 channel,start_time,stop_time,label,confidence
 TERM,0.0000,14.3320,bckg,1.0000
 TERM,14.3320,163.0320,seiz,1.0000
 TERM,163.0320,251.9720,bckg,1.0000
 TERM,251.9720,317.4720,seiz,1.0000
 TERM,317.4720,481.7640,bckg,1.0000
 TERM,481.7640,598.1640,seiz,1.0000
 TERM,598.1640,710.8280,bckg,1.0000
 TERM,710.8280,878.3280,seiz,1.0000
 TERM,878.3280,1077.0480,bckg,1.0000
 TERM,1077.0480,1315.0480,seiz,1.0000
 TERM,1315.0480,1590.5840,bckg,1.0000
 TERM,1590.5840,1679.8840,seiz,1.0000
 TERM,1679.8840,1750.0000,bckg,1.0000

 "TERM" can be ignored - it refers to the type of annotation (TERM means
 the annotation applies to all channels).

 The next two fields are the start and stop time in seconds of the event. The
 next field is the event label followed by a confidence.

 The hypothesis files listed in hyp.list have the same format, but the
 information contained in them should be generated by your system that you
 are evaluating.

 Note that starting with v5.0.0 you only need to provide
 non-background events. We fill in the gaps with an event designated
 as background.

DEMO VERSION:

 nedc_eeg_eval_demo runs nedc_eeg_eval on a list hypothesis and reference csv_bi
 annotation files found within the data directory. It then compares the output
 directory to archived results that comes with nedc_eeg_eval v6.0.0 to ensure
 there are no differences. The hypothesis and reference files the demo uses are
 located here:

  $NEDC_NFC/data/csv/hyp
  $NEDC_NFC/data/csv/hyp

 The hypothesis and reference file lists the demo uses as input is located here:

  $NEDC_NFC/data/lists/hyp.list
  $NEDC_NFC/data/lists/csv.list

 The hyp.list and csv.list files contents can be changed if necessary, but the
 paths of these list files can not change unless you edit the demo. To change
 the paths of the hypothesis and reference list files open the following file
 in a text editor:
 
  $NEDC_NFC/scr/nedc_eeg_eval_demo/nedc_eeg_eval_demo.sh
 
 And change the following variables to the new wanted path:

  # set ref and hyp list variables
  # 
  HYP_LIST="$LIST_DIR/hyp.list"
  REF_LIST="$LIST_DIR/ref.list"

 And make install to bin. Additionally, you can disable the output verification
 by commenting out all lines below line 61 by placing a "#" symbol at the begining
 of each line. And again make install to bin to see the changes.

OTHER IMPORTANT NOTES:

 This scoring software can be configured to do multiclass scoring. Instead of
 having only two events (bckg and seiz), you can edit the parameter file
 in the source directory (nedc_eeg_eval_params_v00.txt) to describe whatever
 classes you wish to score.

If you have any additional comments or questions about this software,
please direct them to help@nedcdata.org. We will do our best to answer
your questions promptly.

Best regards,

Joseph Picone
