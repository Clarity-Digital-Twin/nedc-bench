# file: $(NEDC_NFC)/src/nedc_eeg_eval_demo/Makefile
#
# revision history:
#
# 20250820 (DH): refactored
#
# This Makefile builds all the bash scripts in this directory and places
# them in $NEDC_NFC/bin.
#

# define source and object files
#
SRC = nedc_eeg_eval_demo.sh
EXE := $(basename $(SRC))

# define an installation target
#
install:
	rm -f $(NEDC_NFC)/bin/$(EXE)

	cp $(SRC) $(NEDC_NFC)/bin/$(EXE)
	cd $(NEDC_NFC)/bin/; chmod u+rwx,g+rwx,o+rx $(EXE)

#
# end of file
