#!/bin/bash
#
# file: $(NEDF_NFC)/src/Makefile.sh
#
# This file makes the python classes.
#

# important definitions
#
PROGRAM_NAME="Makefile.sh";

# make sure the environment is set properly
#
if (test -z "$NEDC_NFC") then
   echo "<$PROGRAM_NAME>:" "\$NEC_NFC is not properly set" "[$NEDC_NFC]";
   exit 1
fi

# build the stable libraries
#
cd nedc_eeg_eval; make install; cd ../
cd nedc_eeg_eval_demo; make install; cd ../

#
# end of file
